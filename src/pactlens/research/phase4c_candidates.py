"""Phase 4C candidate record and separate readiness gates. Nothing here approves."""

from pactlens.agents.context_v3 import CONTEXT_VERSION, SYSTEM_V3, V3_PROMPT
from pactlens.agents.prompts import CANDIDATE_PROMPT, EXAMPLE_VERSION, PROMPT_HASHES
from pactlens.agents.protocol_diagnostics import CANDIDATE_PROTOCOL, PROTOCOL_HASH
from pactlens.evidence.compact_views import TABLE_VERSION
from pactlens.evidence.compact_views import VERSION as EVIDENCE_VERSION
from pactlens.evidence.sufficiency import (
    COMPLETE_CONFIG,
    COMPLETE_HASH,
    SELECTION_CONFIG,
    SELECTION_HASH,
    SUFFICIENCY_VERSION,
)
from pactlens.research.detector_contract import RESPONSE_HASH, DetectorEnvelope
from pactlens.research.readiness import FROZEN_RULES
from pactlens.serialization import content_hash

VERSION = "pactlens-phase4c-candidates-v1"
DECISIONS = {
    # One bounded live episode sent all six requests within budget but 0/6 were valid.
    "agent_context": (V3_PROMPT, "PROPOSED_NOT_MODEL_QUALIFIED"),
    "decision_protocol": (CANDIDATE_PROTOCOL, "UNCHANGED_FROM_PHASE4B_PENDING"),
    "example_policy": (
        "one-first-feasible-submit-example;decline-derived",
        "PROPOSED_REVIEW_REQUIRED_AFTER_LIVE_FAILURE",
    ),
    "evidence_tables": (TABLE_VERSION, "PROPOSED"),
    "complete_evidence_policy": (COMPLETE_CONFIG["version"], "PROPOSED"),
    "common_selection_on_v2_tables": (SELECTION_CONFIG["version"], "PROPOSED"),
    "sufficiency_rubric": (SUFFICIENCY_VERSION, "PROPOSED"),
    "primary_observer": ("delivered-intercept-v1", "PROPOSED_UNCHANGED"),
    "router_sensitivity": ("router-audit-v1", "PROPOSED_UNCHANGED"),
    "n2": ("retain-N2-A-all-round-2-block", "PROPOSED_UNCHANGED"),
    "token_feasibility": ("heuristic-not-relaxed;no-exact-counter", "UNRESOLVED"),
    "message_volume_coverage": ("explicit-overflow-beyond-measured-boundary", "UNRESOLVED"),
    "detector_budget_vs_complete_evidence": ("EVIDENCE_BUDGET_INFEASIBLE", "UNRESOLVED"),
    "formal_pilot": ("not-authorized", "NO-GO"),
}


def candidates():
    record = {
        "version": VERSION,
        "status": "CANDIDATES_NOT_APPROVED",
        "agent": {
            "prompt": V3_PROMPT,
            "prompt_hash": PROMPT_HASHES[V3_PROMPT],
            "system_sha256": content_hash(SYSTEM_V3),
            "context_version": CONTEXT_VERSION,
            "example_policy": EXAMPLE_VERSION,
            "protocol": CANDIDATE_PROTOCOL,
            "protocol_hash": PROTOCOL_HASH,
            "previous_candidate": {
                "prompt": CANDIDATE_PROMPT,
                "hash": PROMPT_HASHES[CANDIDATE_PROMPT],
            },
            "input_limit": 2000,
            "output_limit": 256,
            "token_method": "UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE;not-relaxed;exact-null",
        },
        "evidence": {
            "packet_version": EVIDENCE_VERSION,
            "tables": TABLE_VERSION,
            "complete_policy_hash": COMPLETE_HASH,
            "common_selection_hash": SELECTION_HASH,
            "sufficiency": SUFFICIENCY_VERSION,
            "envelope_hash": DetectorEnvelope().config_hash,
            "response_hash": RESPONSE_HASH,
            "input_limit": 4096,
            "reserved_output": 256,
        },
        "frozen_rules_hash": content_hash(FROZEN_RULES),
        "decisions": {k: {"candidate": c, "status": s} for k, (c, s) in sorted(DECISIONS.items())},
    }
    return {**record, "candidate_manifest_hash": content_hash(record)}


def readiness(*, engineering_checks, offline_six_step, live, evidence):
    """Separate gates from explicit measured inputs; not a composite success score."""
    if type(engineering_checks) is not dict or any(
        type(v) is not bool for v in engineering_checks.values()
    ):
        raise ValueError("EXPLICIT_ENGINEERING_CHECKS")
    engineering = "GO" if engineering_checks and all(engineering_checks.values()) else "PARTIAL"
    live_overflow = live.get("status") != "NOT_RUN" and live.get("input_budget_failures", 0) > 0
    # At most one local engineering episode can never qualify general reliability,
    # message-heavy conditions or exact tokenization, so GO is not reachable here.
    model = (
        "BLOCKED"
        if not offline_six_step.get("representative_paths_fit") or live_overflow
        else "PARTIAL"
    )
    if evidence.get("complete_six_action_fits"):
        detector = "GO"
    elif evidence.get("lifecycle_and_communication_fit"):
        detector = "CONDITIONAL GO"
    else:
        detector = "NO-GO"
    # Output validity is reported separately from path feasibility, never folded in.
    validity = (
        "NOT_ASSESSED"
        if live.get("status") == "NOT_RUN"
        else "REAL_MODEL_NOT_READY"
        if live.get("valid_outputs", 0) < live.get("actual_generation_calls", 6)
        or live.get("status") != "COMPLETE"
        else "SINGLE_EPISODE_VALID_NOT_QUALIFIED"
    )
    return {
        "version": "pactlens-phase4c-readiness-v1",
        "engineering": engineering,
        "model_generation_path": model,
        "model_output_validity": validity,
        "detector_evidence_sufficiency": detector,
        "formal_pilot": "NO-GO",
        "formal_pilot_reason": "unapproved candidates, unresolved token/evidence feasibility,"
        " no reviewers, no run authorization",
        "inputs": {
            "engineering_checks": engineering_checks,
            "offline_six_step": offline_six_step,
            "live": live,
            "evidence": evidence,
        },
        "frozen_rules": FROZEN_RULES,
    }
