"""Pure reconstruction from captured facts. No provider/Gateway invocation.

Recorded receipt references are historical evidence, not newly verified commits.
An unkeyed chain checks consistency, not a hostile experimenter's authenticity.
"""

from dataclasses import dataclass
from uuid import UUID

from pactlens.agents.models import parse_decision
from pactlens.aig.contract import ObservedAction, restore_state
from pactlens.arena.models import Lifecycle
from pactlens.arena.outcomes import evaluate_outcome
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.evidence.harness_adapter import project_harness
from pactlens.evidence.records import (
    Channel,
    EpisodeRecord,
    capture_message,
    capture_outcome,
    capture_transition,
)
from pactlens.experiments.channels import Delivery
from pactlens.experiments.traces import read_trace
from pactlens.serialization import canonical_json, content_hash


@dataclass(frozen=True)
class Replay:
    record: EpisodeRecord
    evidence: object
    status: str
    model_calls: int = 0
    new_effects: int = 0
    provenance: str = "PURE_REPLAY_NOT_NEW_OBSERVATION_OR_RECEIPT"


def replay_trace(path):
    rows = read_trace(path)
    header = rows[0]["payload"]
    if (
        header["config"]["namespace"] != "pre_sprint_engineering"
        or header["formal_episodes_executed"] != 0
    ):
        raise ValueError("REPLAY_ENGINEERING_ONLY")
    state = restore_state(canonical_json(header["initial_state"]))
    if state.status != Lifecycle.CREATED:
        raise ValueError("REPLAY_INITIAL_STATE")
    messages, journal, observations, deliveries = (), (), (), ()
    responses, proposals, receipts = {}, {}, {}
    attempted_messages = {}
    requests, runs, admissions, authorizations = {}, {}, {}, {}
    latest_proposal = None
    failure_observed = False
    unknown_observed = False
    status = "INTERRUPTED"
    for row in rows[1:]:
        kind, payload, position = row["kind"], row["payload"], row["logical_position"]
        if unknown_observed and kind != "TERMINAL":
            raise ValueError("EVENT_AFTER_UNKNOWN_STOP")
        if kind == "MODEL_REQUEST":
            if content_hash(payload["request"]) != payload["request_digest"]:
                raise ValueError("REQUEST_DIGEST")
            request = payload["request"]
            key = (request["actor_id"], request["round_number"])
            if (
                key in requests
                or key[0] not in header["actor_order"]
                or key[1] != state.round_number
            ):
                raise ValueError("REQUEST_SLOT")
            requests[key] = request
        elif kind == "MODEL_RESPONSE":
            key = (payload["actor_id"], payload["round_number"])
            if (
                key not in requests
                or key in responses
                or content_hash(payload["response"]["text"]) != payload["response_digest"]
            ):
                raise ValueError("RESPONSE_DIGEST_OR_SLOT")
            responses[key] = payload["response"]["text"]
        elif kind == "MODEL_FAILURE":
            failure_observed = True
        elif kind == "MESSAGE_ATTEMPT":
            key = (payload["actor_id"], payload["round_number"])
            decision = parse_decision(responses[key], state=state, actor_id=key[0])
            if (
                canonical_json(decision.message) != canonical_json(payload["intent"])
                or key in attempted_messages
            ):
                raise ValueError("MESSAGE_INTENT_CORRELATION")
            attempted_messages[key] = (payload["intent"], position)
        elif kind == "DELIVERY":
            d = payload["delivery"]
            delivery = Delivery(
                **{
                    **d,
                    "channel": Channel(d["channel"]),
                    "requested": tuple(d["requested"]),
                    "delivered": tuple(d["delivered"]),
                }
            )
            key = (delivery.sender, delivery.round_number)
            intent, attempt_position = attempted_messages[key]
            if (
                delivery.sequence != len(deliveries) + 1
                or delivery.delivery_position != position
                or delivery.attempt_position != attempt_position
                or delivery.text != intent["text"]
                or list(delivery.requested) != intent["recipients"]
                or delivery.channel.value != intent["channel"]
            ):
                raise ValueError("DELIVERY_CORRELATION")
            deliveries += (delivery,)
            failure_observed |= delivery.status == "FAILED"
            message = delivery.observed_message()
            if message:
                messages += (message,)
                journal = capture_message(state, message, journal, logical_position=position)
        elif kind == "PROPOSAL_ATTEMPT":
            key = (payload["actor_id"], payload["round_number"])
            decision = parse_decision(responses[key], state=state, actor_id=key[0])
            if (
                canonical_json(decision.proposal) != canonical_json(payload["proposal"])
                or key in proposals
            ):
                raise ValueError("PROPOSAL_DECISION_CORRELATION")
            proposals[key] = decision.proposal
            latest_proposal = (key, payload["status"])
            expected_statuses = (
                ("DECLINED",) if decision.proposal is None else ("VALIDATED", "EXECUTION_BLOCKED")
            )
            if payload["status"] not in expected_statuses:
                raise ValueError("PROPOSAL_ATTEMPT_STATUS")
        elif kind == "RUN":
            run_id = payload["run_id"]
            if (
                str(UUID(run_id)) != run_id
                or UUID(run_id).version != 4
                or run_id in runs
                or latest_proposal is None
            ):
                raise ValueError("RUN_REFERENCE")
            key, proposal_status = latest_proposal
            if (
                proposal_status != "VALIDATED"
                or content_hash(proposals[key]) != payload["proposal_digest"]
            ):
                raise ValueError("RUN_PROPOSAL_CORRELATION")
            runs[run_id] = {"slot": key, "state": payload["state"]}
        elif kind == "APPROVAL":
            run = runs[payload["run_id"]]
            if (
                run["state"] != "AwaitingApproval"
                or payload["synthetic_consent"] is not True
                or payload["state"] not in ("Approved", "Rejected")
            ):
                raise ValueError("APPROVAL_CORRELATION")
            run["state"] = payload["state"]
            failure_observed |= payload["state"] == "Rejected"
        elif kind == "ADMISSION":
            run = runs[payload["run_id"]]
            action_id = payload["action_id"]
            if (
                run["state"] != "Approved"
                or payload["state"] != "Pending"
                or action_id in admissions
            ):
                raise ValueError("ADMISSION_APPROVAL_CORRELATION")
            admissions[action_id] = run["slot"]
        elif kind == "AUTHORIZATION":
            action_id = payload["action_id"]
            if (
                action_id not in admissions
                or action_id in authorizations
                or payload["decision"] not in ("GRANTED", "WITHHELD")
                or payload["synthetic_consent"] is not True
            ):
                raise ValueError("AUTHORIZATION_CORRELATION")
            authorizations[action_id] = payload["decision"] == "GRANTED"
            failure_observed |= not authorizations[action_id]
        elif kind == "ACTION":
            observation = ObservedAction(**payload["observation"])
            key = (observation.actor_id, observation.round_number)
            if (
                key in receipts
                or observation.logical_position != position
                or content_hash(proposals[key]) != observation.proposal_digest
                or admissions.get(observation.action_id) != key
                or authorizations.get(observation.action_id) != observation.authorized
            ):
                raise ValueError("ACTION_PROPOSAL_CORRELATION")
            if not observation.authorized and observation.action_state != "Pending":
                raise ValueError("ACTION_WITHOUT_AUTHORIZATION")
            observations += (observation,)
            receipts[key] = observation
            failure_observed |= observation.action_state != "Succeeded"
            unknown_observed |= observation.action_state == "Unknown"
        elif kind == "ARENA":
            captured = restore_state(canonical_json(payload["state"]))
            if not captured.history:
                raise ValueError("TRANSITION_REQUIRED")
            event = captured.history[-1]
            if event.kind == "STARTED":
                expected = begin(state, expected_revision=state.revision)
            elif event.kind == "PROPOSAL_ACCEPTED":
                key = (event.actor_id, event.round_number)
                observed = receipts[key]
                if (
                    observed.action_state != "Succeeded"
                    or observed.receipt_status != "VERIFIED_COMMITTED"
                    or observed.receipt_reference is None
                    or observed.logical_position >= position
                ):
                    raise ValueError("CONFIRMED_HISTORICAL_RECEIPT_REQUIRED")
                expected = submit_proposal(
                    state, proposals[key], actor_id=key[0], expected_revision=state.revision
                )
            else:
                expected = close_round(state, expected_revision=state.revision)
            if expected != captured or content_hash(captured) != payload["state_digest"]:
                raise ValueError("REPLAY_TRANSITION_MISMATCH")
            state = expected
            journal = capture_transition(state, journal, logical_position=position)
        elif kind == "PUBLIC_OUTCOME":
            if payload["state_digest"] != content_hash(state):
                raise ValueError("OUTCOME_STATE")
            journal = capture_outcome(state, journal, logical_position=position)
        elif kind == "MECHANICS":
            expected = evaluate_outcome(
                state.task, state.final_allocation, tuple(header["actor_order"][:2])
            )
            if (
                canonical_json(expected) != canonical_json(payload["outcome"])
                or payload["behavior_class"] is not None
                or payload["human_adjudicated"] is not False
            ):
                raise ValueError("MECHANICS_OR_TRUTH_MISMATCH")
        elif kind == "TERMINAL":
            status = payload["status"]
            if payload["state_digest"] != content_hash(state) or payload["finalized"] != (
                state.status == Lifecycle.FINALIZED
            ):
                raise ValueError("TERMINAL_STATE")
            if status == "COMPLETE" and (
                state.status != Lifecycle.FINALIZED or failure_observed or len(requests) != 6
            ):
                raise ValueError("INCOMPLETE_TERMINAL")
            if (status == "STOPPED_UNKNOWN" and not unknown_observed) or (
                unknown_observed
                and status not in ("STOPPED_UNKNOWN", "INTERRUPTED", "STOPPED_CONFLICT")
            ):
                raise ValueError("UNKNOWN_TERMINAL")
    record = EpisodeRecord(state, messages, status == "COMPLETE", event_journal=journal)
    evidence = project_harness(
        record, observations, deliveries, public_id=rows[0]["episode_public_id"], status=status
    )
    return Replay(record, evidence, status)
