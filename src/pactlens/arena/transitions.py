"""Pure immutable transitions; actor/revision checks are domain validation, not auth."""

from dataclasses import replace

from pactlens.arena.allocation import execute_allocation, measure_costs
from pactlens.arena.models import (
    ArenaError,
    ArenaState,
    Lifecycle,
    Proposal,
    TransitionEvent,
    integer,
)


def _revision(state: ArenaState, expected_revision: int) -> None:
    if type(state) is not ArenaState:
        raise ArenaError("STATE_REQUIRED")
    integer(expected_revision, 0, 9)
    if expected_revision != state.revision:
        raise ArenaError("STALE_REVISION")


def begin(state: ArenaState, *, expected_revision: int) -> ArenaState:
    _revision(state, expected_revision)
    if state.status != Lifecycle.CREATED:
        raise ArenaError("ALREADY_STARTED")
    event = TransitionEvent(1, "STARTED", 1)
    return replace(state, status=Lifecycle.ROUND_1, revision=1, history=(event,))


def submit_proposal(
    state: ArenaState, proposal: Proposal, *, actor_id: str, expected_revision: int
) -> ArenaState:
    _revision(state, expected_revision)
    if state.status not in (Lifecycle.ROUND_1, Lifecycle.ROUND_2):
        raise ArenaError("ROUND_NOT_OPEN")
    if type(proposal) is not Proposal:
        raise ArenaError("PROPOSAL_REQUIRED")
    if proposal.agent_id != actor_id or actor_id not in {a.agent_id for a in state.task.agents}:
        raise ArenaError("WRONG_ACTOR")
    if proposal.round_number != state.round_number:
        raise ArenaError("WRONG_ROUND")
    if proposal.task_hash != state.task.task_hash:
        raise ArenaError("WRONG_TASK")
    if any(
        (p.agent_id, p.round_number) == (actor_id, proposal.round_number) for p in state.proposals
    ):
        raise ArenaError("DUPLICATE_PROPOSAL_SLOT")
    measure_costs(state.task, proposal.allocation)
    event = TransitionEvent(state.revision + 1, "PROPOSAL_ACCEPTED", state.round_number, actor_id)
    return replace(
        state,
        revision=state.revision + 1,
        proposals=state.proposals + (proposal,),
        history=state.history + (event,),
    )


def close_round(state: ArenaState, *, expected_revision: int) -> ArenaState:
    _revision(state, expected_revision)
    if state.status not in (Lifecycle.ROUND_1, Lifecycle.ROUND_2):
        raise ArenaError("ROUND_NOT_OPEN")
    present = {p.agent_id for p in state.proposals if p.round_number == state.round_number}
    missing = tuple(a.agent_id for a in state.task.agents if a.agent_id not in present)
    finalized = state.status == Lifecycle.ROUND_2
    allocation = (
        execute_allocation(state.task, tuple(p for p in state.proposals if p.round_number == 2))
        if finalized
        else None
    )
    event = TransitionEvent(
        state.revision + 1,
        "FINALIZED" if finalized else "ROUND_CLOSED",
        state.round_number,
        missing_agents=missing,
    )
    return replace(
        state,
        status=Lifecycle.FINALIZED if finalized else Lifecycle.ROUND_2,
        revision=state.revision + 1,
        history=state.history + (event,),
        final_allocation=allocation,
    )
