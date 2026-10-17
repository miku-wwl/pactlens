"""Exactly six offline engineering submissions, with explicit synthetic consent.

No agent policy, conditions, inference, sampling, retry or general orchestration.
Interactive consent is not implemented by this deliberately test-only harness.
"""

from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from agentic_intent_gate.runtime import (
    ActionCommand,
    AdmissionCommand,
    ApprovalChoice,
    ApprovalDecisionRequest,
    Intent,
)

from pactlens.aig.consumer import consumer, observe_action, provision
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin, close_round
from pactlens.evidence.records import EpisodeRecord, capture_outcome, capture_transition
from pactlens.integration.arena_bridge import apply_committed


@dataclass(frozen=True)
class EngineeringRun:
    record: EpisodeRecord
    observations: tuple
    stores: tuple


async def run_synthetic_rounds(directory, task, proposals, *, synthetic_consent=False):
    if synthetic_consent is not True:
        raise ValueError("This harness requires explicit synthetic_consent=True")
    expected = {(a.agent_id, r) for a in task.agents for r in (1, 2)}
    if len(proposals) != 6 or {(p.agent_id, p.round_number) for p in proposals} != expected:
        raise ValueError("Exactly three actors and two rounds required")
    by_slot = {(p.agent_id, p.round_number): p for p in proposals}
    directory = Path(directory)
    stores = {
        a.agent_id: provision(directory / f"actor-{n}", task, a.agent_id)
        for n, a in enumerate(task.agents, start=1)
    }
    state = begin(ArenaState(task), expected_revision=0)
    journal = capture_transition(state)
    position = 1
    observations = []
    for round_number in (1, 2):
        for n, actor in enumerate(task.agents, start=1):
            path = directory / f"actor-{n}"
            store = stores[actor.agent_id]
            prepared = store.prepare(state, by_slot[(actor.agent_id, round_number)])
            # New private harness directories; previous contexts are stopped before reopen.
            with consumer(path, state, prepared, predecessor_stopped=True) as (runtime, _, store):
                principal = runtime.verifier.verify(
                    "Bearer " + (path / "capability").read_text("ascii")
                )
                run = await runtime.run_service.create(
                    Intent("Record one reviewed synthetic proposal")
                )
                run = runtime.run_service.decide(
                    run.run_id,
                    ApprovalDecisionRequest(
                        ApprovalChoice.APPROVE,
                        run.version,
                        "synthetic_consent=true; engineering test",
                    ),
                )
                action = runtime.gateway.admit(
                    AdmissionCommand(
                        run.run_id,
                        run.version,
                        principal.subject_id,
                        str(uuid4()),
                    ),
                    principal,
                ).action
                action = runtime.gateway.authorize(
                    ActionCommand(
                        action.action_id,
                        action.version,
                        str(uuid4()),
                    ),
                    principal,
                ).action
                action = (
                    await runtime.gateway.execute(
                        ActionCommand(
                            action.action_id,
                            action.version,
                            str(uuid4()),
                        ),
                        principal,
                    )
                ).action
                position += 1
                observation = observe_action(
                    runtime, store, action.action_id, principal, synthetic_consent=True
                )
                observations.append(replace(observation, logical_position=position))
                if observation.action_state != "Succeeded":
                    raise RuntimeError("Engineering submission stopped; no retry")
            effect = next(e for e in store.committed() if e.effect_key == action.effect_key)
            state = apply_committed(state, store, effect_key=effect.effect_key)
            position += 1
            journal = capture_transition(state, journal, logical_position=position)
        state = close_round(state, expected_revision=state.revision)
        position += 1
        journal = capture_transition(state, journal, logical_position=position)
    journal = capture_outcome(state, journal, logical_position=position + 1)
    return EngineeringRun(
        EpisodeRecord(state, event_journal=journal), tuple(observations), tuple(stores.values())
    )
