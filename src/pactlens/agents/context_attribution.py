"""Offline byte/estimate attribution of actual agent request text. No model call.

Every UTF-8 byte of role+content is assigned to exactly one component, so the
components sum to the preflight byte count. Token shares are the heuristic's
ceil(bytes/2) view, not tokenizer measurements; exact counts stay null unless a
verified counter exists, and provider-reported usage is carried separately.
"""

import json
import re

from pactlens.agents.budgets import BudgetExceeded, token_preflight
from pactlens.agents.context_v3 import BRIEF_LABEL, EXAMPLE_LABEL, SYSTEM_V3, V2_EXAMPLES_LABEL
from pactlens.agents.models import closed_json
from pactlens.agents.prompts import LEGACY_PROMPT, SYSTEM, SYSTEM_V2, make_request
from pactlens.serialization import canonical_json

VERSION = "pactlens-context-attribution-v1"
TASK_HASH_FIELD = re.compile(r'"task_hash":\s*"([a-f0-9]{64})"')
CATEGORIES = (
    "system_prompt",
    "private_brief",
    "public_task",
    "examples",
    "accepted_proposals",
    "previous_requests",
    "previous_responses",
    "delivered_messages",
    "execution_feedback",
    "current_metadata",
    "serialization_and_role_overhead",
)
# v3 own_history entries: earlier-view reference, own earlier output, host feedback.
ENTRY_CATEGORY = {
    "round_number": "previous_requests",
    "seen_revision": "previous_requests",
    "seen_proposal_rows": "previous_requests",
    "seen_inbox_rows": "previous_requests",
    "output": "previous_responses",
    "message_delivery": "execution_feedback",
    "submission_status": "execution_feedback",
}
FIELD_CATEGORY = {
    "public_task": "public_task",
    "accepted_proposals": "accepted_proposals",
    "delivered_inbox": "delivered_messages",
    "actor_id": "current_metadata",
    "round_number": "current_metadata",
    "task_hash": "current_metadata",
    "revision": "current_metadata",
    "channel_access": "current_metadata",
    "now": "current_metadata",
}


def _size(text):
    return len(text.encode("utf-8"))


def request_turns(context, state, inbox, seed, channel_access, *, prompt_version):
    """Exact turns that preflight evaluates, even for a request that cannot be sent.

    The capturing counter deliberately reports a non-fitting count, so a candidate
    request is still refused; it never authorizes, sends or enlarges anything.
    """
    captured = []

    def capture(turns):
        captured.append(turns)
        return 1_000_000

    try:
        request = make_request(
            context,
            state,
            inbox,
            seed,
            channel_access,
            prompt_version=prompt_version,
            token_counter=capture,
        )
    except BudgetExceeded:
        return captured[-1]
    if prompt_version != LEGACY_PROMPT:
        raise ValueError("CANDIDATE_CAPTURE_MUST_NOT_FIT")
    return request.turns


def _system(content):
    """Split trusted system text into instructions, example syntax aid and brief."""
    for base, label in ((SYSTEM_V3, EXAMPLE_LABEL), (SYSTEM_V2, V2_EXAMPLES_LABEL)):
        if content.startswith(base + label):
            examples, _, brief = content[len(base) + len(label) :].partition(BRIEF_LABEL)
            return {
                "system_prompt": _size(base),
                "examples": _size(examples),
                "private_brief": _size(brief),
                "serialization_and_role_overhead": _size(label) + _size(BRIEF_LABEL),
            }
    if content.startswith(SYSTEM + BRIEF_LABEL):
        return {
            "system_prompt": _size(SYSTEM),
            "private_brief": _size(content) - _size(SYSTEM + BRIEF_LABEL),
            "serialization_and_role_overhead": _size(BRIEF_LABEL),
        }
    raise ValueError("UNREVIEWED_SYSTEM_TEXT")


def _observation(content, *, previous):
    """Attribute one observation JSON by top-level field; syntax is the remainder.

    Fields of a resent earlier observation keep their semantic category so that
    duplicated public task/proposal/message bytes stay visible in the rollup.
    """
    body = closed_json(content, 24000)
    if type(body) is not dict:
        raise ValueError("OBSERVATION_FIELDS")
    parts = dict.fromkeys(CATEGORIES, 0)
    compact = content != canonical_json(body)  # v3 uses fixed insertion order
    own_history = 0
    for key, value in body.items():
        size = _size(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            if compact
            else canonical_json(value)
        )
        if key == "own_history":
            own_history = size if value else 0  # an empty list is syntax, not history
            for entry in value:
                for name, item in entry.items():
                    piece = _size(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
                    parts[ENTRY_CATEGORY[name]] += piece
                    size -= piece
            parts["serialization_and_role_overhead"] += size
            continue
        category = FIELD_CATEGORY.get(key)
        if category is None:
            raise ValueError("UNATTRIBUTED_OBSERVATION_FIELD")
        if previous and category == "current_metadata":
            category = "previous_requests"
        parts[category] += size
    parts["serialization_and_role_overhead"] += _size(content) - sum(parts.values())
    return parts, own_history


def attribute_request(turns, *, limit=2000, provider_input_tokens=None):
    """Partition one actual request; the final user turn is the current observation."""
    budget = token_preflight(turns, limit=limit)
    totals = dict.fromkeys(CATEGORIES, 0)
    rows = []
    history_bytes = 0
    for index, turn in enumerate(turns):
        parts = dict.fromkeys(CATEGORIES, 0)
        if index == 0:
            if turn.role != "system":
                raise ValueError("SYSTEM_TURN_REQUIRED")
            parts.update(_system(turn.content))
            kind = "system"
        elif turn.role == "assistant":
            parts["previous_responses"] = _size(turn.content)
            kind = "previous_response"
        else:
            body = closed_json(turn.content, 24000)
            feedback = type(body) is dict and len(body) == 1 and next(iter(body)).startswith("own_")
            if feedback:
                parts["execution_feedback"] = _size(turn.content)
                kind = "execution_feedback"
            else:
                current = index == len(turns) - 1
                observed, own_history = _observation(turn.content, previous=not current)
                parts.update(observed)
                history_bytes += own_history
                kind = "current_observation" if current else "previous_request"
        parts["serialization_and_role_overhead"] += _size(turn.role)
        if kind in ("previous_request", "previous_response", "execution_feedback"):
            history_bytes += _size(turn.role) + _size(turn.content)
        if sum(parts.values()) != _size(turn.role) + _size(turn.content):
            raise ValueError("ATTRIBUTION_PARTITION")
        for key, value in parts.items():
            totals[key] += value
        rows.append(
            {
                "turn": index,
                "role": turn.role,
                "kind": kind,
                "bytes": _size(turn.role) + _size(turn.content),
                "components": {k: v for k, v in parts.items() if v},
            }
        )
    if sum(totals.values()) != budget.utf8_bytes:
        raise ValueError("ATTRIBUTION_TOTAL")
    contents = [t.content for t in turns]
    return {
        "version": VERSION,
        "turn_count": len(turns),
        "utf8_bytes": budget.utf8_bytes,
        "estimated_tokens": budget.estimated_tokens,
        "limit": limit,
        "fits_estimate": budget.fits,
        "method": budget.method,
        "exact_tokens": None,
        "provider_reported_input_tokens": provider_input_tokens,
        "estimator": {
            "byte_tokens": (budget.utf8_bytes + 1) // 2,
            "per_turn_tokens": 32 * len(turns),
            "fixed_margin_tokens": 128,
        },
        "bytes_by_category": totals,
        "estimated_token_share_by_category": {k: (v + 1) // 2 for k, v in totals.items()},
        "public_task_bytes": totals["public_task"],
        # Resent earlier turns (v1/v2) or the re-encoded own_history field (v3).
        "history_bytes": history_bytes,
        "repetition": {
            "public_task_copies": sum(
                1 for c in contents if c.startswith("{") and ('"public_task":' in c)
            ),
            "task_hash_occurrences": _task_hash_occurrences(contents),
        },
        "turns": rows,
    }


def _task_hash_occurrences(contents):
    # The hash appears as a JSON field in examples, observations or earlier outputs.
    for content in contents:
        found = TASK_HASH_FIELD.search(content)
        if found is not None:
            return sum(c.count(found.group(1)) for c in contents)
    return None
