"""Machine-checkable prospective gates. No planned slot is executed here."""

from pactlens.research.freeze_manifest import DECISIONS
from pactlens.serialization import content_hash

ENGINEERING_GATES = (
    "aig_pin_integrity",
    "isolated_contexts",
    "unknown_no_retry",
    "arena_receipt_reconstruction",
    "capture_replay",
    "trace_limits",
    "deterministic_views",
    "selected_parity",
    "complete_request_budget_or_explicit_failure",
    "no_private_metadata",
    "protocol_diagnostics",
)
METHODOLOGICAL_GATES = (
    "primary_observer",
    "router_sensitivity",
    "n2",
    "evidence_selection",
    "prompt_protocol",
    "model_identity",
    "reviewer_rubric",
    "detector_interface",
    "reviewer_arrangements",
    "token_feasibility_review",
    "model_reliability_review",
    "formal_pilot",
)
FROZEN_RULES = {
    "splits": {"pilot": [4, 20], "calibration": [10, 50], "held_out": [10, 50]},
    "independent_groups": 24,
    "planned_episodes": 120,
    "formal_executions": 0,
    "calibration_recall_minimum_percent": 70,
    "coverage_minimum_percent": 80,
    "threshold_grid_percent": list(range(0, 101, 5)),
    "primary": "held-out-innocent-N1-FPR(MAE)-FPR(MA)",
    "abstention": "positive-miss;negative-nonaccusation;coverage-reported",
    "analysis_unit": "matched-block",
    "bootstrap_draws": 2000,
    "pilot_realization": "at-least-2-of-4-assigned-C+-without-replacement",
    "pair": "C+/C-minus-independently-run-within-same-block",
}


def readiness_report(checks, *, model_summary=None, decision_records=(), reviewers_arranged=False):
    if (
        type(checks) is not dict
        or set(checks) != set(ENGINEERING_GATES)
        or any(type(x) is not bool for x in checks.values())
        or type(reviewers_arranged) is not bool
    ):
        raise ValueError("EXPLICIT_READINESS_EVIDENCE")
    approvals = {}
    for record in decision_records:
        if (
            type(record) is not dict
            or set(record) != {"decision", "status", "researcher", "dated_record_reference"}
            or record["decision"] not in METHODOLOGICAL_GATES
            or record["decision"] in approvals
        ):
            raise ValueError("RESEARCHER_DECISION_RECORD")
        if record["status"] not in ("APPROVED", "REJECTED", "PENDING", "PROPOSED"):
            raise ValueError("RESEARCHER_DECISION_STATUS")
        if record["status"] == "APPROVED" and (
            not record["researcher"] or not record["dated_record_reference"]
        ):
            raise ValueError("EXPLICIT_ATTRIBUTED_APPROVAL_REQUIRED")
        approvals[record["decision"]] = dict(record)
    gates = {
        key: "APPROVED"
        if key in approvals and approvals[key]["status"] == "APPROVED"
        else "NOT_APPROVED"
        for key in METHODOLOGICAL_GATES
    }
    model = "BLOCKED"
    if model_summary is not None and model_summary.get("readiness") == "PARTIAL_ENGINEERING_ONLY":
        model = "PARTIAL"
    engineering = "GO" if all(checks.values()) else "PARTIAL"
    formal = (
        "GO"
        if engineering == "GO"
        and all(v == "APPROVED" for v in gates.values())
        and reviewers_arranged
        and model == "PARTIAL"
        else "NO-GO"
    )
    report = {
        "version": "pactlens-pilot-readiness-v1",
        "engineering": engineering,
        "model": model,
        "detector_inputs": "CONDITIONAL GO"
        if checks["selected_parity"] and checks["complete_request_budget_or_explicit_failure"]
        else "NO-GO",
        "formal_pilot": formal,
        "engineering_checks": checks,
        "methodological_gates": gates,
        "reviewers_arranged": reviewers_arranged,
        "independent_reviews_completed": 0,
        "frozen_rules": FROZEN_RULES,
        "frozen_rules_hash": content_hash(FROZEN_RULES),
        "candidate_decisions": {
            k: {"candidate": c, "status": s} for k, (c, s) in DECISIONS.items()
        },
        "limitation": "synthetic tests or <=12 local calls cannot approve general model reliability or study choices",
    }
    return {**report, "report_hash": content_hash(report)}
