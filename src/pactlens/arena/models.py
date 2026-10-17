"""Immutable state, with canonical allocation integrity at every construction."""

from dataclasses import dataclass
from enum import StrEnum

from pactlens.arena._domain import (
    Agent,
    Allocation,
    ArenaConfig,
    ArenaError,
    Assignment,
    Incident,
    Proposal,
    PublicTask,
    _tuple,
    identifier,
    integer,
)
from pactlens.arena.allocation import execute_allocation, measure_costs

__all__ = [
    "Agent",
    "Allocation",
    "ArenaConfig",
    "ArenaError",
    "ArenaState",
    "Assignment",
    "Incident",
    "Lifecycle",
    "Proposal",
    "PublicTask",
    "TransitionEvent",
    "identifier",
    "integer",
    "validate_state",
]


class Lifecycle(StrEnum):
    CREATED = "CREATED"
    ROUND_1 = "ROUND_1"
    ROUND_2 = "ROUND_2"
    FINALIZED = "FINALIZED"


@dataclass(frozen=True)
class TransitionEvent:
    sequence: int
    kind: str
    round_number: int
    actor_id: str | None = None
    missing_agents: tuple[str, ...] = ()

    def __post_init__(self):
        integer(self.sequence, 1, 9)
        integer(self.round_number, 1, 2)
        if self.kind not in ("STARTED", "PROPOSAL_ACCEPTED", "ROUND_CLOSED", "FINALIZED"):
            raise ArenaError("INVALID_EVENT_KIND")
        if self.actor_id is not None:
            identifier(self.actor_id)
        _tuple(self.missing_agents, str)
        for agent_id in self.missing_agents:
            identifier(agent_id)
        if len(set(self.missing_agents)) != len(self.missing_agents):
            raise ArenaError("DUPLICATE_MISSING_ACTOR")


@dataclass(frozen=True)
class ArenaState:
    task: PublicTask
    status: Lifecycle = Lifecycle.CREATED
    revision: int = 0
    proposals: tuple[Proposal, ...] = ()
    history: tuple[TransitionEvent, ...] = ()
    final_allocation: Allocation | None = None

    def __post_init__(self):
        if type(self.task) is not PublicTask or type(self.status) is not Lifecycle:
            raise ArenaError("INVALID_STATE_TYPE")
        integer(self.revision, 0, 9)
        _tuple(self.proposals, Proposal)
        _tuple(self.history, TransitionEvent)
        for proposal in self.proposals:
            proposal.__post_init__()
        for event in self.history:
            event.__post_init__()
        if self.revision != len(self.history):
            raise ArenaError("REVISION_HISTORY_MISMATCH")
        if tuple(event.sequence for event in self.history) != tuple(range(1, self.revision + 1)):
            raise ArenaError("INVALID_HISTORY_ORDER")
        slots = {(p.agent_id, p.round_number) for p in self.proposals}
        if len(slots) != len(self.proposals) or len(self.proposals) > 6:
            raise ArenaError("DUPLICATE_PROPOSAL_SLOT")
        if self.status == Lifecycle.CREATED and (self.revision or self.proposals):
            raise ArenaError("INVALID_CREATED_STATE")
        if (self.status == Lifecycle.FINALIZED) != (self.final_allocation is not None):
            raise ArenaError("FINALIZATION_STATE_MISMATCH")
        if self.final_allocation is not None and type(self.final_allocation) is not Allocation:
            raise ArenaError("INVALID_FINAL_ALLOCATION")
        if self.status == Lifecycle.CREATED:
            return
        if not self.history or self.history[0] != TransitionEvent(1, "STARTED", 1):
            raise ArenaError("MISSING_START_EVENT")
        known = {a.agent_id for a in self.task.agents}
        observed_slots = []
        current_round = 1
        finalized = False
        for event in self.history[1:]:
            if finalized or event.round_number != current_round:
                raise ArenaError("INVALID_HISTORY_LIFECYCLE")
            if event.kind == "PROPOSAL_ACCEPTED":
                slot = (event.actor_id, current_round)
                if event.actor_id not in known or slot in observed_slots or event.missing_agents:
                    raise ArenaError("INVALID_ACCEPTED_EVENT")
                observed_slots.append(slot)
            else:
                expected_kind = "ROUND_CLOSED" if current_round == 1 else "FINALIZED"
                missing = tuple(
                    a.agent_id
                    for a in self.task.agents
                    if (a.agent_id, current_round) not in observed_slots
                )
                if (
                    event.kind != expected_kind
                    or event.actor_id is not None
                    or event.missing_agents != missing
                ):
                    raise ArenaError("INVALID_CLOSE_EVENT")
                if current_round == 1:
                    current_round = 2
                else:
                    finalized = True
        expected_status = (
            Lifecycle.FINALIZED
            if finalized
            else Lifecycle.ROUND_1
            if current_round == 1
            else Lifecycle.ROUND_2
        )
        if self.status != expected_status:
            raise ArenaError("HISTORY_STATUS_MISMATCH")
        if observed_slots != [(p.agent_id, p.round_number) for p in self.proposals]:
            raise ArenaError("PROPOSAL_HISTORY_MISMATCH")
        if any(p.task_hash != self.task.task_hash for p in self.proposals):
            raise ArenaError("PROPOSAL_TASK_MISMATCH")
        for proposal in self.proposals:
            measure_costs(self.task, proposal.allocation)
        if self.final_allocation is not None:
            canonical = execute_allocation(
                self.task, tuple(p for p in self.proposals if p.round_number == 2)
            )
            if self.final_allocation != canonical:
                raise ArenaError("FINAL_ALLOCATION_MISMATCH")

    @property
    def round_number(self) -> int:
        return {
            Lifecycle.CREATED: 0,
            Lifecycle.ROUND_1: 1,
            Lifecycle.ROUND_2: 2,
            Lifecycle.FINALIZED: 2,
        }[self.status]


def validate_state(state: ArenaState) -> None:
    """Recheck boundary input; frozen values are not a hostile-host security barrier."""
    if type(state) is not ArenaState:
        raise ArenaError("INVALID_STATE_TYPE")
    state.__post_init__()
