"""Lossless public tables v2: flat JSONL R versus grouped JSON MAE of the same facts.

Compared with v1 tables, rows cite the public UUIDv5 *name* of each fact instead of
its UUID (the UUID is recomputed from episode+key), repeated long values are listed
once and referenced, allocations are owner vectors and Action/receipt streams cite
their Action ID value. Text is independently parsed back to complete Fact records
and must re-render byte-identically. Presentation only: no fact is added, merged,
inferred or dropped, and both R and MAE use exactly the same encoding.
"""

import json
from dataclasses import dataclass
from uuid import UUID, uuid5

from pactlens.agents.budgets import TokenBudget
from pactlens.agents.models import closed_json
from pactlens.evidence.budgeted_views import (
    ACTOR_COLUMNS,
    INCIDENT_COLUMNS,
    compact_task,
    expand_task,
)
from pactlens.evidence.inventory import KIND_META, PAYLOAD_FIELDS, Fact
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.projection import _public_id
from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.views import CATEGORIES, View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-budgeted-facts-v2-candidate"
TABLE_VERSION = "pactlens-lossless-public-tables-v2-candidate"
MAX_BYTES = 262144
ROW_COLUMNS = ("key", "actor", "completeness", "order", "payload")
ORDER_COLUMNS = ("stream", "source_sequence", "logical_position", "cross_source_order")
CROSS = {"RECORDED": "R", "UNKNOWN": "U", "NOT_APPLICABLE": "N"}
STREAM_PREFIXES = ("aig-action-", "receipt-capture-")
EXACT_KEYS = {
    "public-task": "public_task",
    "communication-coverage": "communication_coverage",
    "execution": "execution",
    "execution-coverage": "execution_coverage",
}
PREFIX_KEYS = {
    "message/": "message",
    "router/": "router_delivery",
    "proposal/": "proposal_slot",
    "arena/": "arena_event",
    "action/": "aig_action",
    "receipt/": "consumer_receipt",
}
CODES = {
    "cross_source_order": {v: k for k, v in CROSS.items()},
    "owners": "item k=Incident-(k+1); n=Actor-n; null=unassigned",
    "value_ref": '{"@":n}=values[n]',
    "stream_ref": "[prefix,n]=prefix+values[n]",
    "fact_id": "UUIDv5(episode,key); cite keys",
}
MIN_STRING = 24
MIN_OBJECT = 48


def kind_of(key):
    if type(key) is not str:
        raise ValueError("FACT_KEY")
    if key in EXACT_KEYS:
        return EXACT_KEYS[key]
    prefix = key[: key.find("/") + 1] if "/" in key else None
    if prefix not in PREFIX_KEYS:
        raise ValueError("FACT_KEY_KIND")
    return PREFIX_KEYS[prefix]


def fact_key(fact, episode):
    """Recover the public logical key whose UUIDv5 is this fact's ID; never guess."""
    body = json.loads(fact.payload_json)
    order = json.loads(fact.ordering_json)
    key = {
        "public_task": lambda: "public-task",
        "communication_coverage": lambda: "communication-coverage",
        "execution": lambda: "execution",
        "execution_coverage": lambda: "execution-coverage",
        "message": lambda: f"message/{body['event_order']}",
        "router_delivery": lambda: f"router/{body['source_sequence']}",
        "proposal_slot": lambda: f"proposal/{body['agent']}/{body['round']}",
        "arena_event": lambda: f"arena/{order['stream']}-{order['source_sequence']}",
        "aig_action": lambda: f"action/{fact.actor}/{body['round']}",
        "consumer_receipt": lambda: f"receipt/{fact.actor}/{body['round']}",
    }[fact.kind]()
    if str(uuid5(UUID(episode), key)) != fact.fact_id or kind_of(key) != fact.kind:
        raise ValueError("FACT_KEY_DERIVATION")
    return key


def _dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _owners(value, expand=False):
    if value is None:
        return None
    if type(value) is not list or not 3 <= len(value) <= 5:
        raise ValueError("ALLOCATION_OWNERS")
    if expand:
        if any(x is not None and (type(x) is not int or not 1 <= x <= 3) for x in value):
            raise ValueError("ALLOCATION_OWNER_CODES")
        return [
            {"incident": f"Incident-{n}", "agent": None if x is None else f"Actor-{x}"}
            for n, x in enumerate(value, 1)
        ]
    result = []
    for n, row in enumerate(value, 1):
        if type(row) is not dict or set(row) != {"incident", "agent"}:
            raise ValueError("ALLOCATION_FIELDS")
        if row["incident"] != f"Incident-{n}" or (
            row["agent"] is not None and row["agent"] not in ("Actor-1", "Actor-2", "Actor-3")
        ):
            # Owner vectors require complete neutral incident order; never reorder values.
            raise ValueError("ALLOCATION_OWNER_ORDER")
        result.append(None if row["agent"] is None else int(row["agent"][-1]))
    return result


def _allocations(value, expand=False):
    if type(value) is dict:
        return {
            k: _owners(v, expand) if k in ("assignments", "allocation") else _allocations(v, expand)
            for k, v in value.items()
        }
    if type(value) is list:
        return [_allocations(x, expand) for x in value]
    return value


def _payload(fact):
    body = json.loads(fact.payload_json)
    body = compact_task(body) if fact.kind == "public_task" else _allocations(body)
    return [body[c] for c in sorted(PAYLOAD_FIELDS[fact.kind])]


def _candidate(node):
    if type(node) is str:
        return len(node) >= MIN_STRING
    return type(node) is dict and len(_dump(node).encode("utf-8")) >= MIN_OBJECT


def _walk(node, chosen, uses, top=True):
    """Top-down replacement: a referenced subtree's interior is not visited."""
    if not top and _candidate(node) and _dump(node) in chosen:
        uses[_dump(node)] = uses.get(_dump(node), 0) + 1
        return
    if type(node) is list:
        for item in node:
            _walk(item, chosen, uses, False)
    elif type(node) is dict:
        for item in node.values():
            _walk(item, chosen, uses, False)


def _stream_value(stream):
    if type(stream) is str:
        for prefix in STREAM_PREFIXES:
            if stream.startswith(prefix) and len(stream) > len(prefix):
                return prefix, stream[len(prefix) :]
    return None


def _values(facts):
    """Deterministic fixpoint: values that are actually referenced at least twice."""
    payloads = [_payload(f) for f in facts]
    streams = [_stream_value(json.loads(f.ordering_json)["stream"]) for f in facts]
    counts = {}

    def count(node, top=True):
        if not top and _candidate(node):
            counts[_dump(node)] = counts.get(_dump(node), 0) + 1
        children = node if type(node) is list else node.values() if type(node) is dict else ()
        for child in children:
            count(child, False)

    for payload in payloads:
        count(payload)
    for item in streams:
        if item is not None:
            counts[_dump(item[1])] = counts.get(_dump(item[1]), 0) + 1
    chosen = {v for v, c in counts.items() if c >= 2}
    while True:
        uses = {}
        for payload in payloads:
            _walk(payload, chosen, uses)
        for item in streams:
            if item is not None and _dump(item[1]) in chosen:
                uses[_dump(item[1])] = uses.get(_dump(item[1]), 0) + 1
        kept = {v for v in chosen if uses.get(v, 0) >= 2}
        if kept == chosen:
            return sorted(chosen)
        chosen = kept


def _intern(node, index, top=True):
    if not top and _candidate(node) and _dump(node) in index:
        return {"@": index[_dump(node)]}
    if type(node) is list:
        return [_intern(x, index, False) for x in node]
    if type(node) is dict:
        return {k: _intern(v, index, False) for k, v in node.items()}
    return node


def _resolve(node, values, top=True):
    if type(node) is dict and set(node) == {"@"} and not top:
        n = node["@"]
        if type(n) is not int or not 0 <= n < len(values):
            raise ValueError("VALUE_REFERENCE")
        return values[n]
    if type(node) is list:
        return [_resolve(x, values, False) for x in node]
    if type(node) is dict:
        return {k: _resolve(v, values, False) for k, v in node.items()}
    return node


def _row(fact, episode, index):
    order = json.loads(fact.ordering_json)
    stream = order["stream"]
    split = _stream_value(stream)
    if split is not None and _dump(split[1]) in index:
        # Only a value that is also listed (used twice) becomes a reference.
        stream = [split[0], index[_dump(split[1])]]
    return [
        fact_key(fact, episode),
        fact.actor,
        fact.completeness,
        [
            stream,
            order["source_sequence"],
            order["logical_position"],
            CROSS[order["cross_source_order"]],
        ],
        _intern(_payload(fact), index),
    ]


def _fact(row, episode, header):
    if type(row) is not list or len(row) != len(ROW_COLUMNS):
        raise ValueError("COMPACT_ROW_COLUMNS")
    key, actor, completeness, order, payload = row
    kind = kind_of(key)
    values = header["values"]
    if (
        type(order) is not list
        or len(order) != len(ORDER_COLUMNS)
        or order[3] not in CODES["cross_source_order"]
    ):
        raise ValueError("COMPACT_ORDER_COLUMNS")
    stream = order[0]
    if type(stream) is list:
        if (
            len(stream) != 2
            or stream[0] not in STREAM_PREFIXES
            or type(stream[1]) is not int
            or not 0 <= stream[1] < len(values)
            or type(values[stream[1]]) is not str
        ):
            raise ValueError("STREAM_REFERENCE")
        stream = stream[0] + values[stream[1]]
    payload = _resolve(payload, values)
    if type(payload) is not list or len(payload) != len(PAYLOAD_FIELDS[kind]):
        raise ValueError("PAYLOAD_COLUMNS")
    body = dict(zip(sorted(PAYLOAD_FIELDS[kind]), payload, strict=True))
    body = expand_task(body) if kind == "public_task" else _allocations(body, True)
    category, source, trust = KIND_META[kind]
    fact = Fact(
        str(uuid5(UUID(episode), key)),
        category,
        kind,
        actor,
        canonical_json(body),
        source,
        trust,
        completeness,
        canonical_json(
            {
                "stream": stream,
                "source_sequence": order[1],
                "logical_position": order[2],
                "cross_source_order": CODES["cross_source_order"][order[3]],
            }
        ),
    )
    if fact_key(fact, episode) != key:
        raise ValueError("FACT_KEY_DERIVATION")
    return fact


def _header(inventory, facts, view, selection_hash, counts, values):
    kinds = sorted({f.kind for f in facts})
    return {
        "version": VERSION,
        "episode": inventory.episode_public_id,
        "policy": inventory.observation_policy.value,
        "view": view.value,
        "selection_hash": selection_hash,
        "table_version": TABLE_VERSION,
        "row_columns": list(ROW_COLUMNS),
        "order_columns": list(ORDER_COLUMNS),
        "key_kinds": {
            **{k: v for k, v in EXACT_KEYS.items() if v in kinds},
            **{k: v for k, v in PREFIX_KEYS.items() if v in kinds},
        },
        "payload_columns": {k: sorted(PAYLOAD_FIELDS[k]) for k in kinds},
        "kind_metadata": {k: list(KIND_META[k]) for k in kinds},
        "kind_metadata_columns": ["category", "source", "trust"],
        "task_columns": {"agents": list(ACTOR_COLUMNS), "incidents": list(INCIDENT_COLUMNS)},
        "codes": CODES,
        "values": [json.loads(v) for v in values],
        "scope": "SELECTED_SUBSET_NOT_COMPLETE_SOURCE"
        if any(counts.values())
        else "FULL_ELIGIBLE_SOURCE",
        "omitted_by_category": counts,
        "render_order": "PRESENTATION_ORDER_NOT_CHRONOLOGY",
    }


def _text(inventory, facts, view, selection_hash, counts):
    values = _values(facts)
    index = {v: n for n, v in enumerate(values)}
    header = _header(inventory, facts, view, selection_hash, counts, values)
    episode = inventory.episode_public_id
    if view == View.MAE:
        groups = {
            category: [
                _row(f, episode, index)
                for f in sorted(facts, key=lambda f: (f.actor or "", f.kind, f.fact_id))
                if f.category == category
            ]
            for category in sorted(CATEGORIES[view])
        }
        return _dump({"header": header, "groups": groups})
    rows = sorted(facts, key=lambda f: (f.kind, f.actor or "", f.fact_id))
    return "\n".join((_dump(header), *(_dump(_row(f, episode, index)) for f in rows)))


class _Source:
    """Header-derived identity for byte-identical re-rendering of parsed facts."""

    def __init__(self, episode, policy):
        self.episode_public_id = episode
        self.observation_policy = ObservationPolicy(policy)


def extract_compact(text, view):
    if type(text) is str and text.startswith(
        ('{"v":"pactlens-facts-v3"', '{"h":{"v":"pactlens-facts-v3"')
    ):
        from pactlens.evidence.tight_views import extract

        return extract(text, view)
    if type(view) is not View or type(text) is not str or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("BOUNDED_COMPACT_TEXT")
    if view == View.MAE:
        body = closed_json(text, MAX_BYTES)
        if type(body) is not dict or list(body) != ["header", "groups"]:
            raise ValueError("GROUPED_COMPACT_FIELDS")
        header, groups = body["header"], body["groups"]
        if type(groups) is not dict or list(groups) != sorted(CATEGORIES[view]):
            raise ValueError("GROUPED_COMPACT_CATEGORIES")
        raw_rows = [
            (c, r) for c in groups for r in (groups[c] if type(groups[c]) is list else [None])
        ]
    else:
        lines = text.split("\n")
        if not 2 <= len(lines) <= 129:
            raise ValueError("FLAT_COMPACT_LINES")
        header = closed_json(lines[0], MAX_BYTES)
        raw_rows = [(None, closed_json(line, 40000)) for line in lines[1:]]
    if type(header) is not dict or list(header) != [
        "version",
        "episode",
        "policy",
        "view",
        "selection_hash",
        "table_version",
        "row_columns",
        "order_columns",
        "key_kinds",
        "payload_columns",
        "kind_metadata",
        "kind_metadata_columns",
        "task_columns",
        "codes",
        "values",
        "scope",
        "omitted_by_category",
        "render_order",
    ]:
        raise ValueError("COMPACT_HEADER_FIELDS")
    episode = _public_id(header["episode"])
    ObservationPolicy(header["policy"])
    if (
        header["version"] != VERSION
        or header["table_version"] != TABLE_VERSION
        or header["view"] != view.value
        or type(header["values"]) is not list
        or type(header["selection_hash"]) is not str
        or len(header["selection_hash"]) != 64
        or any(c not in "0123456789abcdef" for c in header["selection_hash"])
    ):
        raise ValueError("COMPACT_HEADER")
    facts = []
    for category, row in raw_rows:
        fact = _fact(row, episode, header)
        if category is not None and fact.category != category:
            raise ValueError("WRONG_COMPACT_GROUP")
        facts.append(fact)
    if (
        not facts
        or len(facts) > 128
        or len({f.fact_id for f in facts}) != len(facts)
        or any(f.category not in CATEGORIES[view] for f in facts)
    ):
        raise ValueError("COMPACT_FACT_SET")
    counts = header["omitted_by_category"]
    if (
        type(counts) is not dict
        or list(counts) != sorted(CATEGORIES[view])
        or any(type(x) is not int or not 0 <= x <= 128 for x in counts.values())
    ):
        raise ValueError("OMISSION_COVERAGE")
    # Canonical form: every legend, value table, reference and row order must be
    # exactly what the encoder produces for the parsed facts.
    expected = _text(
        _Source(episode, header["policy"]), tuple(facts), view, header["selection_hash"], counts
    )
    if expected != text:
        raise ValueError("NONCANONICAL_COMPACT_TEXT")
    return header, tuple(facts)


@dataclass(frozen=True)
class CompactView:
    view: View
    text: str
    manifest_json: str
    envelope: DetectorEnvelope

    def verify(self):
        header, facts = extract_compact(self.text, self.view)
        manifest = closed_json(self.manifest_json, 2 * MAX_BYTES)
        if type(manifest) is not dict or set(manifest) != {
            "version",
            "header",
            "facts",
            "omitted",
            "mandatory_fact_ids",
            "render_hash",
            "envelope_hash",
            "budget",
            "reserved_output_tokens",
        }:
            raise ValueError("COMPACT_MANIFEST_FIELDS")
        budget = TokenBudget(**manifest["budget"])
        estimated = self.envelope.budget(self.text)
        if (budget.limit, budget.utf8_bytes, budget.estimated_tokens) != (
            estimated.limit,
            estimated.utf8_bytes,
            estimated.estimated_tokens,
        ):
            raise ValueError("COMPLETE_REQUEST_BUDGET_MISMATCH")
        omitted = manifest["omitted"]
        if type(omitted) is not list or any(
            type(x) is not dict
            or set(x) != {"fact_id", "category", "kind"}
            or x["kind"] not in KIND_META
            or x["category"] != KIND_META[x["kind"]][0]
            or x["category"] not in CATEGORIES[self.view]
            for x in omitted
        ):
            raise ValueError("OMITTED_MANIFEST")
        omitted_ids = {x["fact_id"] for x in omitted}
        if any(
            type(x) is not str or str(UUID(x)) != x or UUID(x).version != 5 for x in omitted_ids
        ):
            raise ValueError("OPAQUE_OMITTED_FACT_ID")
        selected = {f.fact_id for f in facts}
        if len(omitted_ids) != len(omitted) or omitted_ids & selected:
            raise ValueError("OMITTED_FACT_IDENTITY")
        counts = {
            k: sum(x["category"] == k for x in omitted) for k in sorted(CATEGORIES[self.view])
        }
        if (
            manifest["version"] != header["version"]
            or manifest["header"] != header
            or manifest["facts"] != canonical_fact_records(facts)
            or manifest["render_hash"] != content_hash(self.text)
            or manifest["envelope_hash"] != self.envelope.config_hash
            or manifest["reserved_output_tokens"] != self.envelope.reserved_output_tokens
            or counts != header["omitted_by_category"]
            or not set(manifest["mandatory_fact_ids"]) <= selected
        ):
            raise ValueError("COMPACT_MANIFEST_BINDING")
        return header, facts

    def conversation(self, *, token_counter=None):
        self.verify()
        self.envelope.budget(self.text, token_counter=token_counter, require=True)
        return self.envelope.turns(self.text)

    def resolve_citations(self, keys):
        """Host mapping of cited packet keys to canonical fact UUIDs; no guessing."""
        header, facts = self.verify()
        if header["version"] == "pactlens-budgeted-facts-v3-candidate":
            from pactlens.evidence.tight_views import resolve

            if type(keys) is not list or any(type(k) is not str for k in keys) or len(keys) > 16:
                raise ValueError("DETECTOR_EVIDENCE_IDS")
            return resolve(self.text, keys)
        if (
            type(keys) is not list
            or len(keys) > 16
            or len(set(keys)) != len(keys)
            or any(type(k) is not str for k in keys)
        ):
            raise ValueError("DETECTOR_EVIDENCE_IDS")
        known = {fact_key(f, header["episode"]): f.fact_id for f in facts}
        if not set(keys) <= set(known):
            raise ValueError("UNOBSERVED_EVIDENCE_CITATION")
        return [known[k] for k in keys]


def render_compact(
    inventory, selected_ids, mandatory_ids, selection_hash, view, envelope, *, token_counter=None
):
    inventory.__post_init__()
    eligible = [f for f in inventory.facts if f.category in CATEGORIES[view]]
    facts = tuple(f for f in eligible if f.fact_id in selected_ids)
    omitted = sorted(
        (
            {"fact_id": f.fact_id, "category": f.category, "kind": f.kind}
            for f in eligible
            if f.fact_id not in selected_ids
        ),
        key=lambda x: x["fact_id"],
    )
    counts = {k: sum(x["category"] == k for x in omitted) for k in sorted(CATEGORIES[view])}
    text = _text(inventory, facts, view, selection_hash, counts)
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("COMPACT_RENDER_BYTE_BOUND")
    manifest = {
        "version": VERSION,
        "header": extract_compact(text, view)[0],
        "facts": canonical_fact_records(facts),
        "omitted": omitted,
        "mandatory_fact_ids": sorted(set(mandatory_ids) & {f.fact_id for f in facts}),
        "render_hash": content_hash(text),
        "envelope_hash": envelope.config_hash,
        "budget": envelope.budget(text, token_counter=token_counter),
        "reserved_output_tokens": envelope.reserved_output_tokens,
    }
    rendered = CompactView(view, text, canonical_json(manifest), envelope)
    rendered.verify()
    return rendered


def verify_compact_parity(raw, grouped):
    if raw.view != View.R or grouped.view != View.MAE:
        raise ValueError("R_MAE_REQUIRED")
    rh, rf = raw.verify()
    gh, gf = grouped.verify()
    for key in ("episode", "policy", "selection_hash", "scope", "omitted_by_category", "values"):
        if rh[key] != gh[key]:
            raise ValueError("COMPACT_INFORMATION_MISMATCH")
    rm, gm = json.loads(raw.manifest_json), json.loads(grouped.manifest_json)
    if (
        canonical_fact_records(rf) != canonical_fact_records(gf)
        or rm["omitted"] != gm["omitted"]
        or rm["mandatory_fact_ids"] != gm["mandatory_fact_ids"]
        or raw.envelope != grouped.envelope
    ):
        raise ValueError("COMPACT_INFORMATION_MISMATCH")
    return True
