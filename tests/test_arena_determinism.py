import os
import random
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace

import pytest
from conftest import allocation, replay

from pactlens.arena.allocation import lawful_reference, measure_costs
from pactlens.arena.generator import generate_task
from pactlens.arena.models import ArenaConfig, ArenaError, ArenaState, Proposal, TransitionEvent
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.serialization import canonical_json, content_hash


@pytest.mark.parametrize("seed", [0, 1, 39, (1 << 64) - 1])
@pytest.mark.parametrize("count", [3, 4, 5])
def test_seeded_generation_and_replay(seed, count):
    task = generate_task(seed, ArenaConfig(incident_count=count))
    again = generate_task(seed, ArenaConfig(incident_count=count))
    assert task == again and task.task_hash == again.task_hash
    assert len(task.agents) == 3 and len(task.incidents) == count
    reference = lawful_reference(task)
    ballots = tuple((agent.agent_id, reference) for agent in task.agents)
    assert replay(task, ballots, ballots) == replay(again, ballots, ballots)
    assert not measure_costs(task, reference).unassigned_incidents


def test_local_rng_and_independent_task_content():
    before = random.getstate()
    tasks = [generate_task(seed) for seed in range(12)]
    assert random.getstate() == before
    assert len({task.task_hash for task in tasks}) == 12
    assert (
        len(
            {
                tuple((a.capacity, a.unit_cost, a.speed, a.skills) for a in task.agents)
                for task in tasks
            }
        )
        > 1
    )  # varied operational data, not renamed clones


def test_cross_process_reproduction_outside_checkout(tmp_path):
    program = """
from dataclasses import replace
from pactlens.arena.generator import generate_task
from pactlens.research.fixtures import run_fixture
from pactlens.research.manifest import build_manifest
from pactlens.serialization import canonical_json, content_hash
t = generate_task(173)
t = replace(t, agents=tuple(set(t.agents)), incidents=tuple(set(t.incidents)))
print(t.task_hash)
print(content_hash(build_manifest()))
print(canonical_json(run_fixture('c_plus').state))
"""
    outputs = []
    for seed in ("1", "987654"):
        environment = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONIOENCODING": "utf-8"}
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-I", "-c", program],
                cwd=tmp_path,
                env=environment,
                text=True,
                encoding="utf-8",
            )
        )
    # -I ignores PYTHONHASHSEED; the two processes still have independently randomized
    # string hashes. Explicit non-isolated hash-seed cases below verify fixed seeds too.
    assert outputs[0] == outputs[1]
    for seed in ("17", "23"):
        environment = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.check_output(
            [sys.executable, "-c", program],
            cwd=tmp_path,
            env=environment,
            text=True,
            encoding="utf-8",
        )
        assert result == outputs[0]


def test_unordered_inputs_are_canonical(task):
    reordered = replace(
        task, agents=tuple(reversed(task.agents)), incidents=tuple(reversed(task.incidents))
    )
    reference = lawful_reference(task)
    assert reordered == task
    assert content_hash(reordered) == task.task_hash
    assert replace(reference, assignments=tuple(reversed(reference.assignments))) == reference
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_state_is_deeply_immutable(task):
    state = ArenaState(task)
    with pytest.raises(FrozenInstanceError):
        state.revision = 1
    with pytest.raises(FrozenInstanceError):
        state.task.agents[0].capacity = 999
    with pytest.raises(TypeError):
        state.task.agents[0].skills[0] = "changed"


@pytest.mark.parametrize(
    "failure",
    [
        "created",
        "wrong_actor",
        "unknown_actor",
        "wrong_round",
        "wrong_task",
        "duplicate",
        "stale",
        "capacity",
        "finalized",
    ],
)
def test_invalid_transition_is_atomic(task, failure):
    reference = lawful_reference(task)
    state = begin(ArenaState(task), expected_revision=0)
    proposal = Proposal("a0", 1, task.task_hash, reference)
    actor = "a0"
    if failure == "created":
        state = ArenaState(task)
    elif failure == "wrong_actor":
        actor = "a1"
    elif failure == "unknown_actor":
        actor = "not_a_participant"
        proposal = replace(proposal, agent_id=actor)
    elif failure == "wrong_round":
        proposal = replace(proposal, round_number=2)
    elif failure == "wrong_task":
        proposal = replace(proposal, task_hash="0" * 64)
    elif failure in ("duplicate", "stale"):
        state = submit_proposal(state, proposal, actor_id=actor, expected_revision=state.revision)
    elif failure == "capacity":
        task = replace(task, agents=tuple(replace(a, capacity=1) for a in task.agents))
        state = begin(ArenaState(task), expected_revision=0)
        proposal = Proposal("a0", 1, task.task_hash, allocation(task, "a0", "a0", "a0"))
    elif failure == "finalized":
        state = close_round(state, expected_revision=state.revision)
        state = close_round(state, expected_revision=state.revision)
    before = canonical_json(state)
    with pytest.raises(ArenaError):
        submit_proposal(
            state, proposal, actor_id=actor, expected_revision=state.revision - (failure == "stale")
        )
    assert canonical_json(state) == before


def test_lifecycle_exactly_two_rounds(task):
    state = ArenaState(task)
    assert state.round_number == 0
    state = begin(state, expected_revision=0)
    assert state.round_number == 1
    state = close_round(state, expected_revision=1)
    assert state.round_number == 2
    final = close_round(state, expected_revision=2)
    assert final.status.value == "FINALIZED" and final.revision == 3
    assert len(final.history[-1].missing_agents) == 3
    with pytest.raises(ArenaError, match="ROUND_NOT_OPEN"):
        close_round(final, expected_revision=3)
    with pytest.raises(ArenaError, match="ALREADY_STARTED"):
        begin(final, expected_revision=3)
    for number in (0, 3, True, 1.0):
        with pytest.raises(ArenaError):
            Proposal("a0", number, task.task_hash, final.final_allocation)


def test_history_contract_rejects_inconsistent_or_mutable_state(task):
    state = begin(ArenaState(task), expected_revision=0)
    with pytest.raises(ArenaError, match="REVISION_HISTORY_MISMATCH"):
        replace(state, history=())
    with pytest.raises(ArenaError, match="MISSING_START_EVENT"):
        replace(state, revision=0, history=())
    with pytest.raises(ArenaError, match="MISSING_START_EVENT"):
        replace(state, history=(TransitionEvent(1, "PROPOSAL_ACCEPTED", 1, "a0"),))
    with pytest.raises(ArenaError, match="IMMUTABLE_TYPED_TUPLE_REQUIRED"):
        TransitionEvent(2, "ROUND_CLOSED", 1, missing_agents=["a0"])
    with pytest.raises(ArenaError, match="INVALID_CLOSE_EVENT"):
        replace(state, revision=2, history=state.history + (TransitionEvent(2, "ROUND_CLOSED", 1),))
    with pytest.raises(ArenaError, match="PROPOSAL_HISTORY_MISMATCH"):
        replace(state, proposals=(Proposal("a0", 1, task.task_hash, lawful_reference(task)),))


@pytest.mark.parametrize("seed", [-1, True, 1.5, "1", 1 << 64])
def test_seed_rejects_coercion(seed):
    with pytest.raises(ArenaError):
        generate_task(seed)


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        "[]",
        "null",
        '{"agent_id":"a0","agent_id":"a1"}',
        "x" * 4097,
        '"\\ud800"',
    ],
)
def test_strict_json_rejects_malformed_payload(raw):
    with pytest.raises(ArenaError):
        Proposal.from_json(raw)


@pytest.mark.parametrize(
    "mutation", ["extra", "float_round", "bool_round", "missing", "nested", "extra_row"]
)
def test_closed_proposal_syntax(task, mutation):
    data = {
        "agent_id": "a0",
        "round_number": 1,
        "task_hash": task.task_hash,
        "assignments": [{"incident_id": i.incident_id, "agent_id": "a0"} for i in task.incidents],
    }
    if mutation == "extra":
        data["authority"] = "MODEL_CANNOT_CHOOSE_AUTHORITY"
    elif mutation == "float_round":
        data["round_number"] = 1.0
    elif mutation == "bool_round":
        data["round_number"] = True
    elif mutation == "missing":
        del data["task_hash"]
    elif mutation == "nested":
        data["assignments"][0]["agent_id"] = {"id": "a0"}
    elif mutation == "extra_row":
        data["assignments"][0]["hidden"] = "forbidden"
    with pytest.raises(ArenaError):
        Proposal.from_mapping(data)


def test_valid_json_round_trip(task):
    raw = (
        '{"agent_id":"a0","round_number":1,"task_hash":"'
        + task.task_hash
        + '",'
        + (
            '"assignments":[{"incident_id":"i0","agent_id":"a0"},'
            '{"incident_id":"i1","agent_id":"a1"},{"incident_id":"i2","agent_id":"a2"}]}'
        )
    )
    parsed = Proposal.from_json(raw)
    assert parsed.allocation == lawful_reference(task)
