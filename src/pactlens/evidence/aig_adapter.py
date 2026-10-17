"""Observation-v2 extension with explicitly different execution trust sources."""

import re

from pactlens.aig.contract import ObservedAction, uuid4_text
from pactlens.evidence.projection import project_evidence
from pactlens.evidence.records import DetectorEvidence
from pactlens.serialization import canonical_json, content_hash


def project_aig_evidence(record, observations, *, public_id, shared_capture=False):
    data = project_evidence(record, public_id=public_id).as_mapping()
    if type(shared_capture) is not bool:
        raise ValueError("Explicit shared capture assertion required")
    if shared_capture and data["event_ordering"]["status"] != "RECORDED_CROSS_STREAM":
        raise ValueError("Shared capture requires complete recorded Arena positions")
    if type(observations) is not tuple or len(observations) > 6:
        raise ValueError("At most six immutable Action observations required")
    aliases = {a.agent_id: f"Actor-{n}" for n, a in enumerate(record.state.task.agents, 1)}
    proposals = {(p.agent_id, p.round_number): p for p in record.state.proposals}
    records = []
    seen = set()
    for observation in observations:
        if type(observation) is not ObservedAction:
            raise ValueError("Detached bounded Action observation required")
        uuid4_text(observation.action_id)
        slot = (observation.actor_id, observation.round_number)
        if (
            observation.actor_id not in aliases
            or type(observation.round_number) is not int
            or observation.round_number not in (1, 2)
            or slot in seen
            or observation.action_state
            not in ("Pending", "Authorized", "Executing", "Succeeded", "Failed", "Unknown")
            or observation.approval_state != "Approved"
            or type(observation.action_version) is not int
            or not 1 <= observation.action_version <= 4
            or type(observation.authorized) is not bool
            or type(observation.synthetic_consent) is not bool
            or observation.receipt_status not in ("VERIFIED_COMMITTED", "MISSING")
        ):
            raise ValueError("Invalid public Action observation")
        seen.add(slot)
        expected_version = {"Pending": 1, "Authorized": 2, "Executing": 3}.get(
            observation.action_state, 4
        )
        if observation.action_version != expected_version or observation.authorized != (
            observation.action_state != "Pending"
        ):
            raise ValueError("Contradictory Action lifecycle observation")
        for digest in (observation.payload_digest, observation.proposal_digest):
            if type(digest) is not str or re.fullmatch("[a-f0-9]{64}", digest) is None:
                raise ValueError("Canonical public digest required")
        if observation.receipt_status == "VERIFIED_COMMITTED":
            uuid4_text(observation.receipt_reference)
        elif observation.receipt_reference is not None:
            raise ValueError("Unverified receipt reference")
        if (
            observation.action_state == "Succeeded"
            and observation.receipt_status != "VERIFIED_COMMITTED"
        ):
            raise ValueError("Success requires verified receipt")
        if slot in proposals and content_hash(proposals[slot]) != observation.proposal_digest:
            raise ValueError("Arena/Action proposal content mismatch")
        position = observation.logical_position
        if position is not None and (type(position) is not int or not 1 <= position <= 4096):
            raise ValueError("Bounded logical position required")
        if shared_capture:
            if position is None or record.event_journal is None:
                raise ValueError("Shared capture requires recorded positions")
            if any(
                e["ordering_stream"] == "arena"
                and (e["type"] == "ROUND_OPENED" or e["round"] < observation.round_number)
                and e["logical_position"] > position
                for e in data["events"]
            ):
                raise ValueError("Shared capture contradicts round boundary")
            applied = next(
                (
                    e
                    for e in data["events"]
                    if e["type"] == "PROPOSAL_ACCEPTED"
                    and (e["actor"], e["round"])
                    == (aliases[observation.actor_id], observation.round_number)
                ),
                None,
            )
            if applied and (
                applied["logical_position"] is None or applied["logical_position"] <= position
            ):
                raise ValueError("Shared capture contradicts Action-before-application")
        elif position is not None:
            raise ValueError("Unmatched capture clock; clear uncorrelated positions")
        records.append(
            {
                "action_id": observation.action_id,
                "actor": aliases[observation.actor_id],
                "round": observation.round_number,
                "action_state": observation.action_state,
                "approval_state": observation.approval_state,
                "authorized": observation.authorized,
                "payload_digest": observation.payload_digest,
                "proposal_digest": observation.proposal_digest,
                "receipt_reference": observation.receipt_reference,
                "receipt_status": observation.receipt_status,
                "synthetic_consent": observation.synthetic_consent,
                "ordering_stream": "aig-action-" + observation.action_id,
                "source_sequence": observation.action_version,
                "logical_position": position,
            }
        )
    data["aig_execution"] = {
        "contract_version": "pactlens-aig-observation-v1",
        "status": "COMPLETE" if len(records) == 6 else "INCOMPLETE",
        "cross_source_order": "RECORDED_SHARED_LOGICAL_CAPTURE" if shared_capture else "UNKNOWN",
        "records": records,
        "trust_sources": {
            "messages": "RESEARCH_OWNED_SYNTHETIC_OBSERVATIONS",
            "actions": "AIG_PUBLIC_API_LOCAL_CAPABILITY_NOT_PRODUCTION_AUTH",
            "receipts": "VERIFIED_CONSUMER_SQLITE_COMMIT_NOT_COLLUSION_PROOF",
            "arena_outcome": "DETERMINISTIC_SYNTHETIC_ARENA_ACCOUNTING",
        },
    }
    return DetectorEvidence(canonical_json(data))
