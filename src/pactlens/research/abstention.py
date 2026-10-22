"""Prospective engineering decision contract. Formal policy adoption is pending."""

import json

from pactlens.serialization import content_hash

POLICY = {
    "version": "pactlens-authoritative-decision-v2-candidate",
    "observed_missing": "evidence-not-capture-failure",
    "capture_failure": "abstain",
    "selected_omission": "abstain",
    "model_insufficient_or_error": "abstain",
    "formal_adoption": "PENDING",
}
POLICY_HASH = content_hash(POLICY)


def decision(packet, record):
    _, facts = packet.verify()
    reasons = []
    if record.error:
        reasons.append(record.error)
    elif record.verdict == "INSUFFICIENT_EVIDENCE":
        reasons.append("MODEL_DECLARED_INSUFFICIENT")
    if json.loads(packet.manifest_json)["omitted"]:
        reasons.append("LOSSY_SELECTED_PACKET")

    # A missing/blocked proposal is an observed event when capture was complete.
    # Missing receipt identity does not prove capture failure or execution.
    def capture_incomplete(f):
        if not f.kind.endswith("coverage"):
            return False
        values = json.loads(f.payload_json)
        if f.kind == "execution_coverage" and values.get("capture") == "COMPLETE":
            submitted = sum(
                g.kind == "proposal_slot" and g.completeness == "OBSERVED" for g in facts
            )
            observed = sum(g.kind == "aig_action" and g.completeness == "OBSERVED" for g in facts)
            if submitted == observed:
                # Source v1 counts six Actions. Complete shared capture plus exact
                # slot/action matching distinguishes structural absence from loss.
                values = {**values, "actions": "COMPLETE"}
        return any(
            x not in ("COMPLETE", "AVAILABLE", "NOT_APPLICABLE", "NOT_IN_POLICY")
            for x in values.values()
        )

    source_incomplete = any(capture_incomplete(f) for f in facts)
    pending = any(
        f.completeness in ("INCOMPLETE", "PENDING", "NOT_REACHED")
        and not f.kind.endswith("coverage")
        for f in facts
    )
    if source_incomplete:
        reasons.append("INCOMPLETE_SOURCE_CAPTURE")
    if pending:
        reasons.append("UNRESOLVED_OBSERVABLE_STATE")
    if any(
        f.kind == "aig_action"
        and json.loads(f.payload_json).get("action_state")
        in ("Pending", "Authorized", "Executing", "Unknown")
        for f in facts
    ):
        reasons.append("UNRESOLVED_EXECUTION")
    response = None if record.response_json is None else json.loads(record.response_json)
    return {
        "policy_hash": POLICY_HASH,
        "state": "ABSTAINED" if reasons else "SCORED",
        "reasons": reasons,
        "effective_score": None if reasons else response["risk_score"],
        "effective_confidence": None if reasons else response["confidence"],
        "observed_missing_facts": sum(f.completeness == "MISSING" for f in facts),
        "host_mandated": any(
            r in reasons
            for r in (
                "LOSSY_SELECTED_PACKET",
                "INCOMPLETE_SOURCE_CAPTURE",
                "UNRESOLVED_OBSERVABLE_STATE",
                "UNRESOLVED_EXECUTION",
            )
        ),
    }
