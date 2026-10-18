"""Sequential three-actor/two-round protocol. No official-study entry point."""

import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from pactlens.agents.models import ActorContext, Turn
from pactlens.agents.prompts import CANDIDATE_PROMPT, LEGACY_PROMPT, make_request
from pactlens.agents.protocol_diagnostics import (
    CANDIDATE_PROTOCOL,
    LEGACY_PROTOCOL,
    Code,
    Diagnostic,
    exception_diagnostic,
    parse_versioned,
)
from pactlens.aig.consumer import provision
from pactlens.aig.executor import no_fault
from pactlens.aig.submission import TestConsent, submit
from pactlens.arena.models import ArenaState, Lifecycle
from pactlens.arena.outcomes import evaluate_outcome
from pactlens.arena.transitions import begin, close_round
from pactlens.evidence.harness_adapter import project_harness
from pactlens.evidence.records import (
    EpisodeRecord,
    capture_message,
    capture_outcome,
    capture_transition,
)
from pactlens.experiments.channels import Router
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.traces import TraceWriter
from pactlens.integration.arena_bridge import apply_committed
from pactlens.research.adjudication import prepare_adjudication
from pactlens.serialization import canonical_json, content_hash


@dataclass(frozen=True)
class HarnessRun:
    public_id: str
    status: str
    record: EpisodeRecord
    observations: tuple
    deliveries: tuple
    contexts: tuple
    stores: tuple
    trace_path: Path
    executor_calls: int

    def evidence(self):
        return project_harness(
            self.record,
            self.observations,
            self.deliveries,
            public_id=self.public_id,
            status=self.status,
        )


async def run_episode(
    directory,
    task,
    config,
    provider,
    *,
    consent=None,
    failed_deliveries=(),
    checkpoint=no_fault,
    prompt_version=LEGACY_PROMPT,
    stop_on_input_budget_failure=False,
):
    if (
        type(config) is not EpisodeConfig
        or type(consent) is not TestConsent
        or consent.synthetic_consent is not True
    ):
        raise ValueError("ENGINEERING_CONFIG_AND_SYNTHETIC_CONSENT_REQUIRED")
    config.__post_init__()
    if prompt_version not in (LEGACY_PROMPT, CANDIDATE_PROMPT):
        raise ValueError("UNREVIEWED_PROMPT_VERSION")
    if type(stop_on_input_budget_failure) is not bool:
        raise ValueError("TRUSTED_BUDGET_STOP_FLAG")
    protocol_version = CANDIDATE_PROTOCOL if prompt_version == CANDIDATE_PROMPT else LEGACY_PROTOCOL
    provider.config.__post_init__()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError("FRESH_EPISODE_DIRECTORY_REQUIRED_NO_RESUME")
    public_id = str(uuid4())
    trace = TraceWriter(directory / "trace.jsonl", public_id)
    state, journal, messages, observations = ArenaState(task), (), (), ()
    order = config.roles(task)
    router = Router(
        tuple(a.agent_id for a in task.agents),
        private_pair=order[:2],
        private_enabled=config.private_enabled,
        failed_sequences=failed_deliveries,
    )
    contexts = {
        a.agent_id: ActorContext(a.agent_id, config.brief(a.agent_id, task)) for a in task.agents
    }
    stores = {}
    status, executor_calls = "COMPLETE", 0
    submission_failures = ()
    budget_stopped = False
    trace.append(
        "CONFIG",
        {
            "config": config,
            "model": provider.config,
            "prompt_version": prompt_version,
            "protocol_version": protocol_version,
            "initial_state": state,
            "actor_order": order,
            "private_briefs": {a: c.private_instruction for a, c in contexts.items()},
            "seeds": [config.seed(a, r, task) for r in (1, 2) for a in order],
            "formal_episodes_executed": 0,
            "provenance": "PRE_SPRINT_ENGINEERING",
        },
    )

    def arena_capture():
        nonlocal journal
        position = trace.append("ARENA", {"state": state, "state_digest": content_hash(state)})
        journal = capture_transition(state, journal, logical_position=position)

    try:
        stores = {
            a.agent_id: provision(directory / f"actor-{n}", task, a.agent_id)
            for n, a in enumerate(task.agents, 1)
        }
        state = begin(state, expected_revision=0)
        arena_capture()
        for round_number in (1, 2):
            for actor in order:
                context = contexts[actor]
                try:
                    request = make_request(
                        context,
                        state,
                        router.inbox(actor),
                        config.seed(actor, round_number, task).integer,
                        {
                            "public": True,
                            "private_peer": next((a for a in order[:2] if a != actor), None)
                            if router.private_enabled and actor in order[:2]
                            else None,
                        },
                        prompt_version=prompt_version,
                        token_counter=getattr(provider, "count_input_tokens", None),
                    )
                    trace.append(
                        "MODEL_REQUEST",
                        {
                            "request": request,
                            "request_digest": content_hash(request),
                            "model": provider.config,
                        },
                    )
                    async with asyncio.timeout(provider.config.timeout_seconds):
                        response = await provider.generate(request)
                    response.__post_init__()
                    trace.append(
                        "MODEL_RESPONSE",
                        {
                            "actor_id": actor,
                            "round_number": round_number,
                            "response": response,
                            "response_digest": content_hash(response.text),
                        },
                    )
                    contexts[actor] = replace(
                        context,
                        history=(
                            *context.history,
                            request.turns[-1],
                            Turn("assistant", response.text),
                        ),
                    )
                    if prompt_version == CANDIDATE_PROMPT:
                        if response.input_tokens is not None and response.input_tokens > 2000:
                            raise ValueError("ACTUAL_INPUT_BUDGET_EXCEEDED")
                        if response.finish_reason == "length" or (
                            response.output_tokens is not None
                            and response.output_tokens > provider.config.max_output_tokens
                        ):
                            raise ValueError("OUTPUT_BUDGET_EXCEEDED")
                    decision = parse_versioned(
                        response.text,
                        state=state,
                        actor_id=actor,
                        protocol_version=protocol_version,
                    )
                except (ValueError, TypeError, TimeoutError, OSError, RecursionError) as error:
                    status = "INCOMPLETE"
                    trace.append(
                        "MODEL_FAILURE",
                        {
                            "actor_id": actor,
                            "round_number": round_number,
                            "classification": "GENERATION_OR_VALIDATION_FAILED_NO_RETRY",
                            "error_type": type(error).__name__,
                            "diagnostic": exception_diagnostic(
                                error, protocol_version=protocol_version
                            ),
                            "token_budget": getattr(error, "report", None),
                        },
                    )
                    trace.append(
                        "VALIDATION",
                        {"actor_id": actor, "round_number": round_number, "status": "REJECTED"},
                    )
                    if (
                        stop_on_input_budget_failure
                        and exception_diagnostic(error, protocol_version=protocol_version).code
                        == Code.INPUT
                    ):
                        budget_stopped = True
                        break
                    continue
                trace.append(
                    "VALIDATION",
                    {
                        "actor_id": actor,
                        "round_number": round_number,
                        "status": "VALID",
                        "diagnostic": Diagnostic(
                            Code.DECLINE if decision.proposal is None else Code.VALID,
                            protocol_version,
                        ),
                    },
                )
                if decision.message is not None:
                    attempt = trace.append(
                        "MESSAGE_ATTEMPT",
                        {
                            "actor_id": actor,
                            "round_number": round_number,
                            "intent": decision.message,
                        },
                    )
                    delivery = router.route(
                        decision.message,
                        actor=actor,
                        round_number=round_number,
                        attempt_position=attempt,
                        delivery_position=trace.next_position,
                    )
                    position = trace.append("DELIVERY", {"delivery": delivery})
                    message = delivery.observed_message()
                    if message is not None:
                        messages += (message,)
                        journal = capture_message(
                            state, message, journal, logical_position=position
                        )
                    if delivery.status == "FAILED":
                        status = "INCOMPLETE"
                    contexts[actor] = replace(
                        contexts[actor],
                        history=(
                            *contexts[actor].history,
                            Turn("user", canonical_json({"own_message_delivery": delivery.status})),
                        ),
                    )
                if decision.proposal is None:
                    trace.append(
                        "PROPOSAL_ATTEMPT",
                        {
                            "actor_id": actor,
                            "round_number": round_number,
                            "status": "DECLINED",
                            "proposal": None,
                        },
                    )
                    continue
                proposal = decision.proposal
                permitted = config.execution_permitted(round_number)
                trace.append(
                    "PROPOSAL_ATTEMPT",
                    {
                        "actor_id": actor,
                        "round_number": round_number,
                        "status": "VALIDATED" if permitted else "EXECUTION_BLOCKED",
                        "proposal": proposal,
                        "base_revision": state.revision,
                    },
                )
                if not permitted:
                    continue
                store = stores[actor]
                prepared = store.prepare(state, proposal)
                result = await submit(
                    store.path.parent,
                    state,
                    prepared,
                    trace,
                    consent=consent,
                    checkpoint=checkpoint,
                )
                executor_calls += result.executor_calls
                if result.status != "Succeeded":
                    submission_failures += (
                        {
                            "actor_id": actor,
                            "round_number": round_number,
                            "status": result.status,
                            "diagnostic": Diagnostic(Code.AIG, protocol_version),
                        },
                    )
                if result.observation is not None:
                    observations += (result.observation,)
                contexts[actor] = replace(
                    contexts[actor],
                    history=(
                        *contexts[actor].history,
                        Turn("user", canonical_json({"own_submission_status": result.status})),
                    ),
                )
                if result.status == "Unknown":
                    status = "STOPPED_UNKNOWN"
                    break
                if result.status != "Succeeded":
                    status = "INCOMPLETE"
                    continue
                state = apply_committed(state, store, effect_key=result.effect_key)
                arena_capture()
            if status == "STOPPED_UNKNOWN" or budget_stopped:
                break
            state = close_round(state, expected_revision=state.revision)
            arena_capture()
        if state.status == Lifecycle.FINALIZED:
            position = trace.append("PUBLIC_OUTCOME", {"state_digest": content_hash(state)})
            journal = capture_outcome(state, journal, logical_position=position)
            outcome = evaluate_outcome(task, state.final_allocation, order[:2])
            trace.append(
                "MECHANICS",
                {
                    "outcome": outcome,
                    "adjudication": "PENDING",
                    "behavior_class": None,
                    "human_adjudicated": False,
                },
            )
    except (KeyboardInterrupt, asyncio.CancelledError):
        status = "INTERRUPTED"
        raise
    except Exception:
        status = "STOPPED_CONFLICT"
        raise
    finally:
        try:
            trace.append(
                "TERMINAL",
                {
                    "status": status,
                    "state_digest": content_hash(state),
                    "finalized": state.status == Lifecycle.FINALIZED,
                    "executor_calls": trace.executor_calls,
                    "formal_episodes_executed": 0,
                    "submission_failures": submission_failures,
                },
            )
        finally:
            trace.close()
    adjudication = None
    if state.status == Lifecycle.FINALIZED:
        adjudication = prepare_adjudication(
            evaluate_outcome(task, state.final_allocation, order[:2]),
            logs_complete=status == "COMPLETE",
        )
    record = EpisodeRecord(
        state,
        messages,
        status == "COMPLETE",
        adjudication=adjudication,
        private_metadata={"config": config, "contexts": tuple(contexts.values())},
        event_journal=journal,
    )
    return HarnessRun(
        public_id,
        status,
        record,
        observations,
        router.deliveries,
        tuple(contexts.values()),
        tuple(stores.values()),
        trace.path,
        executor_calls,
    )
