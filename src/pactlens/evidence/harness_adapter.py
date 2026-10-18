"""Explicit observable inventory shared by future views, without constructing views."""

from pactlens.evidence.aig_adapter import project_aig_evidence
from pactlens.evidence.records import DetectorEvidence
from pactlens.experiments.channels import Delivery
from pactlens.serialization import canonical_json


def project_harness(record, observations, deliveries, *, public_id, status, shared_capture=True):
    if status not in (
        "COMPLETE",
        "INCOMPLETE",
        "STOPPED_UNKNOWN",
        "INTERRUPTED",
        "STOPPED_CONFLICT",
    ):
        raise ValueError("EPISODE_STATUS")
    data = project_aig_evidence(
        record, observations, public_id=public_id, shared_capture=shared_capture
    ).as_mapping()
    aliases = {a.agent_id: f"Actor-{n}" for n, a in enumerate(record.state.task.agents, 1)}
    rows = []
    delivered_messages = []
    previous_position = 0
    positions = {(e.source, e.sequence): e.logical_position for e in record.event_journal or ()}
    for d in deliveries:
        if type(d) is not Delivery:
            raise ValueError("TYPED_DELIVERY_REQUIRED")
        d.__post_init__()
        if d.sender not in aliases or not set(d.requested) <= set(aliases):
            # Unknown recipients are invalid intents, not legitimately observed actors.
            # They remain diagnostics in the private trace, never arbitrary L3 identifiers.
            requested = [aliases[a] for a in d.requested if a in aliases]
        else:
            requested = [aliases[a] for a in d.requested]
        if d.sender not in aliases:
            raise ValueError("DELIVERY_SENDER")
        if not shared_capture and (
            d.attempt_position is not None or d.delivery_position is not None
        ):
            raise ValueError("INDEPENDENT_DELIVERY_CLOCK")
        if d.observed_message() is not None:
            delivered_messages.append(d.observed_message())
            if shared_capture and positions.get(("message", d.sequence)) != d.delivery_position:
                raise ValueError("DELIVERY_CAPTURE_CORRELATION")
        if shared_capture:
            if (
                d.attempt_position is None
                or d.delivery_position is None
                or d.attempt_position <= previous_position
            ):
                raise ValueError("DELIVERY_CAPTURE_ORDER")
            previous_position = d.delivery_position
        rows.append(
            {
                "event_id": f"delivery-{d.sequence}",
                "sender": aliases[d.sender],
                "requested_recipients": requested,
                "delivered_recipients": [aliases[a] for a in d.delivered],
                "channel": d.channel.value,
                "round": d.round_number,
                "text": d.text,
                "attempted": True,
                "delivery_state": d.status,
                "ordering_stream": "router",
                "source_sequence": d.sequence,
                "attempt_position": d.attempt_position,
                "delivery_position": d.delivery_position,
            }
        )
    if tuple(delivered_messages) != record.messages:
        raise ValueError("DELIVERY_MESSAGE_CORRELATION")
    if [d.sequence for d in deliveries] != list(range(1, len(deliveries) + 1)):
        raise ValueError("DELIVERY_SEQUENCE")
    if status == "COMPLETE" and (
        not record.messages_complete or record.state.status.value != "FINALIZED"
    ):
        raise ValueError("COMPLETENESS_CONTRADICTION")
    data["harness"] = {
        "contract_version": "pactlens-harness-observation-v1",
        "episode_status": status,
        "provenance": "PRE_SPRINT_ENGINEERING_NOT_STUDY",
        "observation_policy": "ALL_ROUTER_ATTEMPTS_AND_CONFIRMED_DELIVERIES",
        "generation": "MODEL_OUTPUT_UNTRUSTED",
        "deliveries": rows,
        "cross_source_order": "SHARED_HOST_CAPTURE" if shared_capture else "UNKNOWN",
        "inventory": "CANONICAL_SHARED_SOURCE_FACTS_NO_DETECTOR_TRANSFORMS",
    }
    return DetectorEvidence(canonical_json(data))
