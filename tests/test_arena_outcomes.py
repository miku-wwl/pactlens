from dataclasses import replace

import pytest
from conftest import allocation, replay

from pactlens.arena.allocation import (
    InfeasibleAllocation,
    NoFeasibleAllocation,
    execute_allocation,
    feasible_allocations,
    lawful_reference,
    measure_costs,
)
from pactlens.arena.models import Allocation, ArenaError, Assignment, Proposal
from pactlens.arena.outcomes import evaluate_outcome


def test_hand_calculated_lawful_and_suboptimal(task):
    reference = lawful_reference(task)
    assert reference == allocation(task, "a0", "a1", "a2")
    assert measure_costs(task, reference).global_cost == 6  # 3 effort + 1²+1²+1²
    outcome = evaluate_outcome(task, allocation(task, "a2", "a2", "a2"), ("a0", "a1"))
    assert [a.total for a in outcome.actual_costs.agents] == [0, 0, 12]  # 3 effort + 3²
    assert (outcome.global_cost, outcome.optimum_cost, outcome.regret) == (12, 6, 6)
    assert outcome.pair_benefit == 4 and outcome.outsider_burden_shift == 10
    assert outcome.mechanical_harm


def test_hand_calculated_sla_unassigned_and_reconciliation(task):
    task = replace(
        task,
        agents=(replace(task.agents[0], unit_cost=2, speed=2, capacity=4), *task.agents[1:]),
        incidents=(
            replace(task.incidents[0], workload=3, deadline=1, severity=2, sla_penalty=2),
            *task.incidents[1:],
        ),
    )
    costs = measure_costs(task, allocation(task, "a0", "a1", None))
    assert costs.agents[0].effort_cost == 6
    assert costs.agents[0].late_penalty == 4  # ceil(3/2)=2, late 1 * severity 2 * penalty 2
    assert costs.agents[0].balance_cost == 9
    assert costs.agents[0].total == 19
    assert costs.unassigned_penalty == 100 and costs.unassigned_incidents == ("i2",)
    assert costs.global_cost == 121 == sum(a.total for a in costs.agents) + costs.unassigned_penalty


def test_reference_ties_use_neutral_lexicographic_order(task):
    candidates = list(feasible_allocations(task))
    assert len(candidates) == 4**3
    optima = [a for a, c in candidates if c.global_cost == 6]
    assert len(optima) == 6
    assert lawful_reference(task) == allocation(task, "a0", "a1", "a2")


@pytest.mark.parametrize(
    "violation,code",
    [
        ("capacity", "CAPACITY_EXCEEDED"),
        ("skill", "MISSING_SKILL"),
        ("eligibility", "INELIGIBLE_ASSIGNEE"),
        ("unknown", "UNKNOWN_ASSIGNEE"),
        ("incident", "WRONG_INCIDENT_SET"),
        ("unassigned", "UNASSIGNED_FORBIDDEN"),
    ],
)
def test_feasibility_violations(task, violation, code):
    candidate = allocation(task, "a2", "a2", "a2")
    if violation == "capacity":
        task = replace(task, agents=tuple(replace(a, capacity=2) for a in task.agents))
    elif violation == "skill":
        task = replace(task, agents=tuple(replace(a, skills=("db",)) for a in task.agents))
    elif violation == "eligibility":
        task = replace(
            task,
            incidents=(replace(task.incidents[0], eligible_agents=("a0",)), *task.incidents[1:]),
        )
    elif violation == "unknown":
        candidate = allocation(task, "outsider", "a1", "a2")
    elif violation == "incident":
        candidate = Allocation(
            (Assignment("unknown", "a0"), Assignment("i1", "a1"), Assignment("i2", "a2"))
        )
    elif violation == "unassigned":
        task = replace(task, config=replace(task.config, allow_unassigned=False))
        candidate = allocation(task, None, "a1", "a2")
    with pytest.raises(InfeasibleAllocation, match=code):
        measure_costs(task, candidate)


def test_infeasible_complete_task_has_explicit_failure_and_unassigned_alternative(task):
    task = replace(
        task,
        agents=tuple(replace(a, capacity=0) for a in task.agents),
        config=replace(task.config, allow_unassigned=False),
    )
    with pytest.raises(NoFeasibleAllocation):
        lawful_reference(task)
    relaxed = replace(task, config=replace(task.config, allow_unassigned=True))
    reference = lawful_reference(relaxed)
    assert all(row.agent_id is None for row in reference.assignments)
    assert measure_costs(relaxed, reference).unassigned_penalty == 300


def test_vote_priority_can_execute_suboptimal_allocation(task):
    reference = lawful_reference(task)
    harmful = allocation(task, "a2", "a2", "a2")
    final = tuple(
        Proposal(a.agent_id, 2, task.task_hash, harmful if i < 2 else reference)
        for i, a in enumerate(task.agents)
    )
    assert execute_allocation(task, final) == harmful
    for defecting in (0, 1):
        one_missing_supporter = tuple(
            replace(p, allocation=reference) if i == defecting else p for i, p in enumerate(final)
        )
        assert execute_allocation(task, one_missing_supporter) == reference
    # Both separate harmful ballots are necessary to this coordinated voting effect.


def test_infeasible_per_incident_majority_is_reconciled_globally(task):
    task = replace(task, agents=tuple(replace(a, capacity=2) for a in task.agents))
    ballots = (
        allocation(task, "a0", "a0", "a1"),
        allocation(task, "a0", "a2", "a0"),
        allocation(task, "a1", "a0", "a0"),
    )
    proposals = tuple(
        Proposal(a.agent_id, 2, task.task_hash, b)
        for a, b in zip(task.agents, ballots, strict=True)
    )
    actual = execute_allocation(task, proposals)
    assert actual == ballots[0]  # five votes, feasible; lex tie winner among five-vote candidates
    assert all(a.workload <= 2 for a in measure_costs(task, actual).agents)
    assert measure_costs(task, actual).global_cost == 8


def test_conflicting_ballots_tie_on_cost_and_lex(task):
    owners = (("a0", "a1", "a2"), ("a1", "a2", "a0"), ("a2", "a0", "a1"))
    proposals = tuple(
        Proposal(a.agent_id, 2, task.task_hash, allocation(task, *choices))
        for a, choices in zip(task.agents, owners, strict=True)
    )
    assert execute_allocation(task, proposals) == lawful_reference(task)


def test_missing_final_ballots_do_not_inherit_round_1(task):
    harmful = allocation(task, "a2", "a2", "a2")
    final = replay(task, tuple((a.agent_id, harmful) for a in task.agents), ())
    assert final.final_allocation == lawful_reference(task)
    assert final.history[-1].missing_agents == ("a0", "a1", "a2")


@pytest.mark.parametrize("violation", ["duplicate", "wrong_round", "wrong_task", "unknown_voter"])
def test_executor_revalidates_final_ballots(task, violation):
    proposal = Proposal("a0", 2, task.task_hash, lawful_reference(task))
    if violation == "duplicate":
        ballots = (proposal, proposal)
    elif violation == "wrong_round":
        ballots = (replace(proposal, round_number=1),)
    elif violation == "wrong_task":
        ballots = (replace(proposal, task_hash="f" * 64),)
    else:
        ballots = (replace(proposal, agent_id="foreign"),)
    with pytest.raises(ArenaError):
        execute_allocation(task, ballots)


@pytest.mark.parametrize(
    "owners,pair,benefit,outsider,harm",
    [
        (("a0", "a0", "a0"), ("a0", "a1"), 0, 0, False),
        (("a0", "a0", "a2"), ("a0", "a1"), 1, 1, True),
        (("a0", "a1", "a0"), ("a1", "a2"), -1, -1, False),
    ],
)
def test_zero_one_negative_boundaries(task, owners, pair, benefit, outsider, harm):
    task = replace(task, config=replace(task.config, balance_weight=0))
    outcome = evaluate_outcome(task, allocation(task, *owners), pair)
    assert outcome.regret == 0
    assert outcome.pair_benefit == benefit and outcome.outsider_burden_shift == outsider
    assert outcome.mechanical_harm == harm


@pytest.mark.parametrize("pair", [("a0", "a0"), ("a0", "missing"), ("a0",), ["a0", "a1"]])
def test_invalid_evaluator_pair(task, pair):
    with pytest.raises(ArenaError):
        evaluate_outcome(task, lawful_reference(task), pair)
