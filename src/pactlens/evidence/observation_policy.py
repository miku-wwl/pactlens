"""Observer rights differ from the private Router audit and actor inboxes."""

from enum import StrEnum

from pactlens.evidence.aig_adapter import project_aig_evidence
from pactlens.evidence.harness_adapter import project_harness
from pactlens.evidence.records import DetectorEvidence
from pactlens.serialization import canonical_json


class ObservationPolicy(StrEnum):
    DELIVERED = "delivered-intercept-v1"
    ROUTER_AUDIT = "router-audit-v1"


def project_observation(
    record,
    observations=(),
    deliveries=None,
    *,
    public_id,
    policy=ObservationPolicy.ROUTER_AUDIT,
    status="INCOMPLETE",
    shared_capture=False,
):
    if type(policy) is not ObservationPolicy:
        raise ValueError("EXPLICIT_OBSERVATION_POLICY_REQUIRED")
    if status not in (
        "COMPLETE",
        "INCOMPLETE",
        "STOPPED_UNKNOWN",
        "INTERRUPTED",
        "STOPPED_CONFLICT",
    ):
        raise ValueError("OBSERVABLE_CAPTURE_STATUS")
    if deliveries is None:
        data = project_aig_evidence(
            record, observations, public_id=public_id, shared_capture=shared_capture
        ).as_mapping()
        audit = {"status": "NOT_AVAILABLE", "records": []}
    else:
        data = project_harness(
            record,
            observations,
            deliveries,
            public_id=public_id,
            status=status,
            shared_capture=shared_capture,
        ).as_mapping()
        audit = {"status": "AVAILABLE", "records": data["harness"]["deliveries"]}
    # Observer-local message numbering never discloses missing Router-attempt IDs.
    renumber = {m["event_order"]: n for n, m in enumerate(data["messages"]["records"], 1)}
    messages = [
        {
            "event_order": renumber[m["event_order"]],
            "round": m["round"],
            "sender": m["sender"],
            "recipients": m["recipients"],
            "channel": m["channel"],
            "text": m["text"],
        }
        for m in data["messages"]["records"]
    ]
    events = []
    for e in data["events"]:
        if e["type"] == "MESSAGE":
            n = renumber[e["source_sequence"]]
            events.append(
                {
                    **e,
                    "event_id": f"message-{n}",
                    "source_sequence": n,
                    "ordering_stream": "intercepted-messages",
                    "payload": messages[n - 1],
                }
            )
        else:
            events.append(e)
    if policy == ObservationPolicy.DELIVERED:
        # The collector has no right to export rejected/failed private attempts.
        audit = {"status": "NOT_IN_POLICY", "records": []}
    return DetectorEvidence(
        canonical_json(
            {
                "schema_version": "pactlens-policy-observation-v1",
                "observation_policy": policy.value,
                "episode_public_id": data["episode_public_id"],
                "public_task": data["public_task"],
                "messages": {"status": data["messages"]["status"], "records": messages},
                "proposal_slots": data["proposal_slots"],
                "execution": data["execution"],
                "events": events,
                "event_ordering": data["event_ordering"],
                "aig_execution": data["aig_execution"],
                "communication_audit": audit,
                "capture_status": status,
            }
        )
    )
