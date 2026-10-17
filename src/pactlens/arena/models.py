"""Strict immutable domain values for a bounded, two-round synthetic arena."""

import json
import re
from dataclasses import dataclass
from enum import StrEnum

from pactlens.serialization import content_hash


class ArenaError(ValueError):
    """Rejected domain input/transition. Messages deliberately omit raw input."""


def integer(value: int, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ArenaError("INTEGER_OUT_OF_BOUNDS")


def identifier(value: str) -> None:
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value) is None:
        raise ArenaError("INVALID_IDENTIFIER")


def _tuple(value: tuple, member_type: type) -> None:
    if type(value) is not tuple or any(type(item) is not member_type for item in value):
        raise ArenaError("IMMUTABLE_TYPED_TUPLE_REQUIRED")


@dataclass(frozen=True)
class ArenaConfig:
    incident_count: int | None = None
    balance_weight: int = 1
    unassigned_multiplier: int = 20
    allow_unassigned: bool = True
    revision: str = "incident-arena-v1"

    def __post_init__(self):
        if self.incident_count is not None:
            integer(self.incident_count, 3, 5)
        integer(self.balance_weight, 0, 10)
        integer(self.unassigned_multiplier, 1, 100)
        if type(self.allow_unassigned) is not bool or self.revision != "incident-arena-v1":
            raise ArenaError("INVALID_CONFIG")


@dataclass(frozen=True)
class Agent:
    agent_id: str
    skills: tuple[str, ...]
    capacity: int
    unit_cost: int = 1
    speed: int = 1

    def __post_init__(self):
        identifier(self.agent_id)
        _tuple(self.skills, str)
        if not self.skills or len(set(self.skills)) != len(self.skills):
            raise ArenaError("INVALID_SKILLS")
        for skill in self.skills:
            identifier(skill)
        object.__setattr__(self, "skills", tuple(sorted(self.skills)))
        integer(self.capacity, 0, 64)
        integer(self.unit_cost, 1, 16)
        integer(self.speed, 1, 16)


@dataclass(frozen=True)
class Incident:
    incident_id: str
    workload: int
    severity: int
    required_skill: str
    deadline: int
    sla_penalty: int
    eligible_agents: tuple[str, ...] | None = None

    def __post_init__(self):
        identifier(self.incident_id)
        identifier(self.required_skill)
        integer(self.workload, 1, 8)
        integer(self.severity, 1, 5)
        integer(self.deadline, 1, 16)
        integer(self.sla_penalty, 1, 100)
        if self.eligible_agents is not None:
            _tuple(self.eligible_agents, str)
            if len(set(self.eligible_agents)) != len(self.eligible_agents):
                raise ArenaError("DUPLICATE_ELIGIBLE_AGENT")
            for agent_id in self.eligible_agents:
                identifier(agent_id)
            object.__setattr__(self, "eligible_agents", tuple(sorted(self.eligible_agents)))


@dataclass(frozen=True)
class PublicTask:
    agents: tuple[Agent, ...]
    incidents: tuple[Incident, ...]
    config: ArenaConfig = ArenaConfig()

    def __post_init__(self):
        _tuple(self.agents, Agent)
        _tuple(self.incidents, Incident)
        if type(self.config) is not ArenaConfig or len(self.agents) != 3:
            raise ArenaError("EXACTLY_THREE_AGENTS_REQUIRED")
        if not 3 <= len(self.incidents) <= 5:
            raise ArenaError("THREE_TO_FIVE_INCIDENTS_REQUIRED")
        if len({a.agent_id for a in self.agents}) != 3:
            raise ArenaError("DUPLICATE_AGENT")
        if len({i.incident_id for i in self.incidents}) != len(self.incidents):
            raise ArenaError("DUPLICATE_INCIDENT")
        if self.config.incident_count not in (None, len(self.incidents)):
            raise ArenaError("INCIDENT_COUNT_CONFIG_MISMATCH")
        known = {agent.agent_id for agent in self.agents}
        if any(
            i.eligible_agents is not None and not set(i.eligible_agents) <= known
            for i in self.incidents
        ):
            raise ArenaError("UNKNOWN_ELIGIBLE_AGENT")
        object.__setattr__(self, "agents", tuple(sorted(self.agents, key=lambda a: a.agent_id)))
        object.__setattr__(
            self, "incidents", tuple(sorted(self.incidents, key=lambda i: i.incident_id))
        )

    @property
    def task_hash(self) -> str:
        return content_hash(self)


@dataclass(frozen=True)
class Assignment:
    incident_id: str
    agent_id: str | None

    def __post_init__(self):
        identifier(self.incident_id)
        if self.agent_id is not None:
            identifier(self.agent_id)


@dataclass(frozen=True)
class Allocation:
    assignments: tuple[Assignment, ...]

    def __post_init__(self):
        _tuple(self.assignments, Assignment)
        if not 3 <= len(self.assignments) <= 5:
            raise ArenaError("INVALID_ASSIGNMENT_COUNT")
        if len({a.incident_id for a in self.assignments}) != len(self.assignments):
            raise ArenaError("DUPLICATE_INCIDENT_ASSIGNMENT")
        object.__setattr__(
            self, "assignments", tuple(sorted(self.assignments, key=lambda a: a.incident_id))
        )


@dataclass(frozen=True)
class Proposal:
    agent_id: str
    round_number: int
    task_hash: str
    allocation: Allocation

    def __post_init__(self):
        identifier(self.agent_id)
        integer(self.round_number, 1, 2)
        if type(self.task_hash) is not str or re.fullmatch(r"[a-f0-9]{64}", self.task_hash) is None:
            raise ArenaError("INVALID_TASK_HASH")
        if type(self.allocation) is not Allocation:
            raise ArenaError("INVALID_ALLOCATION_TYPE")

    @classmethod
    def from_mapping(cls, payload: dict) -> "Proposal":
        required = {"agent_id", "round_number", "task_hash", "assignments"}
        if type(payload) is not dict or set(payload) != required:
            raise ArenaError("INVALID_PROPOSAL_FIELDS")
        rows = payload["assignments"]
        if type(rows) is not list or not 3 <= len(rows) <= 5:
            raise ArenaError("INVALID_ASSIGNMENT_SYNTAX")
        if any(type(row) is not dict or set(row) != {"incident_id", "agent_id"} for row in rows):
            raise ArenaError("INVALID_ASSIGNMENT_FIELDS")
        return cls(
            payload["agent_id"],
            payload["round_number"],
            payload["task_hash"],
            Allocation(tuple(Assignment(**row) for row in rows)),
        )

    @classmethod
    def from_json(cls, raw: str) -> "Proposal":
        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ArenaError("DUPLICATE_JSON_KEY")
                result[key] = value
            return result

        if type(raw) is not str:
            raise ArenaError("JSON_STRING_REQUIRED")
        try:
            if len(raw.encode("utf-8", errors="strict")) > 4096:
                raise ArenaError("PROPOSAL_TOO_LARGE")
            return cls.from_mapping(json.loads(raw, object_pairs_hook=unique_keys))
        except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
            raise ArenaError("INVALID_JSON") from error


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

    @property
    def round_number(self) -> int:
        return {
            Lifecycle.CREATED: 0,
            Lifecycle.ROUND_1: 1,
            Lifecycle.ROUND_2: 2,
            Lifecycle.FINALIZED: 2,
        }[self.status]
