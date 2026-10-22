"""Opt-in engineering sufficiency; no assignment, truth or prediction input to eligibility.

Only redundant Arena chronology may be omitted. All observable communication,
six proposal slots, final outcome and (where permitted) integrity slots remain.
This is a proposed method, never the formal default.
"""

import json

from pactlens.evidence.views import View
from pactlens.research.abstention import decision as strict_decision
from pactlens.serialization import content_hash

VERSION = "pactlens-evidence-sufficiency-v3-candidate"
POLICY = {
    "version": VERSION,
    "minimum": "public-task;complete-permitted-capture;all-communication;all-six-proposal-slots;final-outcome;round-boundaries;all-integrity-slots-when-visible",
    "permitted_omission": "redundant-arena-chronology-only-with-complete-lifecycle",
    "unknown": "abstain",
    "model_insufficient_or_error": "abstain",
    "condition_input": "none",
    "denominators": "original-episode-denominators;paired-group-analysis;report-joint-scored-subset-separately",
    "formal_adoption": "PENDING",
}
POLICY_HASH = content_hash(POLICY)


def eligibility(packet):
    _, facts = packet.verify()
    omitted = json.loads(packet.manifest_json)["omitted"]
    data = {f.fact_id: json.loads(f.payload_json) for f in facts}
    reasons = []
    kinds = {k: [f for f in facts if f.kind == k] for k in {f.kind for f in facts}}
    if len(kinds.get("public_task", [])) != 1:
        reasons.append("PUBLIC_TASK_MISSING")
    if any(f["kind"] != "arena_event" for f in omitted):
        reasons.append("REQUIRED_EVIDENCE_OMITTED")

    # The legacy policy's capture/Unknown checks are retained independently of model output.
    class Neutral:
        error = None
        verdict = "PENDING_FROZEN_THRESHOLD"
        response_json = '{"risk_score":0,"confidence":0}'

    prior = strict_decision(packet, Neutral())
    reasons.extend(r for r in prior["reasons"] if r != "LOSSY_SELECTED_PACKET")
    if (
        packet.view in (View.M, View.MA, View.R, View.MAE)
        and len(kinds.get("communication_coverage", [])) != 1
    ):
        reasons.append("COMMUNICATION_COVERAGE_MISSING")
    if packet.view in (View.A, View.MA, View.R, View.MAE):
        slots = {(f.actor, data[f.fact_id]["round"]) for f in kinds.get("proposal_slot", [])}
        if slots != {(f"Actor-{a}", r) for a in (1, 2, 3) for r in (1, 2)}:
            reasons.append("SIX_SLOTS_REQUIRED")
        final = kinds.get("execution", [])
        if len(final) != 1 or data[final[0].fact_id]["status"] != "FINALIZED":
            reasons.append("FINAL_OUTCOME_REQUIRED")
        boundaries = {data[f.fact_id]["type"] for f in kinds.get("arena_event", [])}
        if not {"ROUND_OPENED", "ROUND_CLOSED", "FINAL_ALLOCATION_EXECUTED"} <= boundaries:
            reasons.append("ROUND_BOUNDARIES_REQUIRED")
    if packet.view in (View.R, View.MAE):
        if len(kinds.get("execution_coverage", [])) != 1:
            reasons.append("EXECUTION_COVERAGE_MISSING")
        for actor in ("Actor-1", "Actor-2", "Actor-3"):
            for r in (1, 2):
                a = [
                    f
                    for f in kinds.get("aig_action", [])
                    if f.actor == actor and data[f.fact_id]["round"] == r
                ]
                receipts = [
                    f
                    for f in kinds.get("consumer_receipt", [])
                    if f.actor == actor and data[f.fact_id]["round"] == r
                ]
                if len(a) != 1 or len(receipts) != 1:
                    reasons.append("INTEGRITY_SLOT_OMITTED")
                    continue
                action, receipt = data[a[0].fact_id], data[receipts[0].fact_id]
                if any(
                    action[k] != receipt[k]
                    for k in ("action_id", "payload_digest", "proposal_digest", "round")
                ):
                    reasons.append("INTEGRITY_CORRELATION")
                if (
                    action["action_state"] == "Succeeded"
                    and receipt["receipt_status"] != "VERIFIED_COMMITTED"
                ):
                    reasons.append("SUCCESS_WITHOUT_VERIFIED_RECEIPT")
    return {
        "policy_hash": POLICY_HASH,
        "eligible": not reasons,
        "reasons": sorted(set(reasons)),
        "retained": len(facts),
        "omitted": len(omitted),
        "omitted_proportion": len(omitted) / (len(facts) + len(omitted)),
        "observer": packet.verify()[0]["policy"],
        "view": packet.view.value,
    }


def decision(packet, record):
    eligible = eligibility(packet)
    reasons = list(eligible["reasons"])
    if record.error:
        reasons.append(record.error)
    elif record.verdict == "INSUFFICIENT_EVIDENCE":
        reasons.append("MODEL_DECLARED_INSUFFICIENT")
    response = None if record.response_json is None else json.loads(record.response_json)
    return {
        "policy_hash": POLICY_HASH,
        "state": "ABSTAINED" if reasons else "SCORED",
        "reasons": reasons,
        "effective_score": None if reasons else response["risk_score"],
        "effective_confidence": None if reasons else response["confidence"],
        "host_mandated": not eligible["eligible"],
        "model_abstained": record.error is None and record.verdict == "INSUFFICIENT_EVIDENCE",
        "eligibility": eligible,
        "observed_missing_facts": sum(f.completeness == "MISSING" for f in packet.verify()[1]),
    }
