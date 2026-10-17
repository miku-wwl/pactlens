"""Condition-independent cost accounting, bounded enumeration and final voting."""

from dataclasses import dataclass
from itertools import product

from pactlens.arena.models import Allocation, ArenaError, Assignment, Proposal, PublicTask


class InfeasibleAllocation(ArenaError):
    pass


class NoFeasibleAllocation(ArenaError):
    pass


@dataclass(frozen=True)
class AgentCost:
    agent_id: str
    workload: int
    effort_cost: int
    late_penalty: int
    balance_cost: int

    @property
    def total(self) -> int:
        return self.effort_cost + self.late_penalty + self.balance_cost


@dataclass(frozen=True)
class CostBreakdown:
    agents: tuple[AgentCost, ...]
    unassigned_incidents: tuple[str, ...]
    unassigned_penalty: int

    @property
    def global_cost(self) -> int:
        return sum(a.total for a in self.agents) + self.unassigned_penalty


def measure_costs(task: PublicTask, allocation: Allocation) -> CostBreakdown:
    if type(task) is not PublicTask or type(allocation) is not Allocation:
        raise ArenaError("TASK_AND_ALLOCATION_REQUIRED")
    if tuple(row.incident_id for row in allocation.assignments) != tuple(
        incident.incident_id for incident in task.incidents
    ):
        raise InfeasibleAllocation("WRONG_INCIDENT_SET")
    agents = {a.agent_id: a for a in task.agents}
    incidents = {i.incident_id: i for i in task.incidents}
    loads = {a: 0 for a in agents}
    effort = dict(loads)
    late = dict(loads)
    unassigned = []
    penalty = 0
    for row in allocation.assignments:
        incident = incidents[row.incident_id]
        if row.agent_id is None:
            if not task.config.allow_unassigned:
                raise InfeasibleAllocation("UNASSIGNED_FORBIDDEN")
            unassigned.append(incident.incident_id)
            penalty += incident.severity * incident.sla_penalty * task.config.unassigned_multiplier
            continue
        if row.agent_id not in agents:
            raise InfeasibleAllocation("UNKNOWN_ASSIGNEE")
        agent = agents[row.agent_id]
        if incident.required_skill not in agent.skills:
            raise InfeasibleAllocation("MISSING_SKILL")
        if incident.eligible_agents is not None and agent.agent_id not in incident.eligible_agents:
            raise InfeasibleAllocation("INELIGIBLE_ASSIGNEE")
        loads[agent.agent_id] += incident.workload
        if loads[agent.agent_id] > agent.capacity:
            raise InfeasibleAllocation("CAPACITY_EXCEEDED")
        effort[agent.agent_id] += incident.workload * agent.unit_cost
        duration = (incident.workload + agent.speed - 1) // agent.speed
        late[agent.agent_id] += (
            max(0, duration - incident.deadline) * incident.severity * incident.sla_penalty
        )
    return CostBreakdown(
        tuple(
            AgentCost(
                a.agent_id,
                loads[a.agent_id],
                effort[a.agent_id],
                late[a.agent_id],
                task.config.balance_weight * loads[a.agent_id] ** 2,
            )
            for a in task.agents
        ),
        tuple(unassigned),
        penalty,
    )


def allocation_key(task: PublicTask, allocation: Allocation) -> tuple[int, ...]:
    order = {agent.agent_id: index for index, agent in enumerate(task.agents)}
    return tuple(
        3 if row.agent_id is None else order[row.agent_id] for row in allocation.assignments
    )


def feasible_allocations(task: PublicTask):
    """At most 4**5=1024 candidates; None sorts after the three neutral agents."""
    owners = tuple(a.agent_id for a in task.agents)
    if task.config.allow_unassigned:
        owners += (None,)
    for choices in product(owners, repeat=len(task.incidents)):
        candidate = Allocation(
            tuple(
                Assignment(i.incident_id, a) for i, a in zip(task.incidents, choices, strict=True)
            )
        )
        try:
            costs = measure_costs(task, candidate)
        except InfeasibleAllocation:
            continue
        yield candidate, costs


def lawful_reference(task: PublicTask) -> Allocation:
    best = min(
        feasible_allocations(task),
        key=lambda item: (item[1].global_cost, allocation_key(task, item[0])),
        default=None,
    )
    if best is None:
        raise NoFeasibleAllocation("NO_LAWFUL_ALLOCATION")
    return best[0]


def execute_allocation(task: PublicTask, final_proposals: tuple[Proposal, ...]) -> Allocation:
    """Maximize total final-round votes subject to feasibility, then cost, then lex.

    Each missing agent supplies one canonical-lawful-reference ballot. Round 1
    is deliberation only; it never silently replaces a missing round-2 ballot.
    """
    if type(final_proposals) is not tuple or any(type(p) is not Proposal for p in final_proposals):
        raise ArenaError("PROPOSAL_TUPLE_REQUIRED")
    known = {a.agent_id for a in task.agents}
    if len({p.agent_id for p in final_proposals}) != len(final_proposals):
        raise ArenaError("DUPLICATE_VOTER")
    for proposal in final_proposals:
        if (
            proposal.agent_id not in known
            or proposal.round_number != 2
            or proposal.task_hash != task.task_hash
        ):
            raise ArenaError("INVALID_FINAL_BALLOT")
        measure_costs(task, proposal.allocation)
    reference = lawful_reference(task)
    by_actor = {p.agent_id: p.allocation for p in final_proposals}
    ballots = tuple(by_actor.get(agent.agent_id, reference) for agent in task.agents)

    def rank(item):
        candidate, costs = item
        votes = sum(
            a.agent_id == b.agent_id
            for ballot in ballots
            for a, b in zip(ballot.assignments, candidate.assignments, strict=True)
        )
        return -votes, costs.global_cost, allocation_key(task, candidate)

    return min(feasible_allocations(task), key=rank)[0]
