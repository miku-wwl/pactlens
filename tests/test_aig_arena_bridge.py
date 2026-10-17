import asyncio
from uuid import uuid4

import pytest

from pactlens.aig.workflow import run_synthetic_rounds
from pactlens.arena.outcomes import evaluate_outcome
from pactlens.integration.arena_bridge import apply_committed, reconstruct
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import canonical_json


@pytest.mark.parametrize("name", ["c_plus", "c_minus"])
def test_three_agents_two_rounds_real_aig_matches_original_fixture(tmp_path, name):
    original = run_fixture(name)
    run = asyncio.run(
        run_synthetic_rounds(
            tmp_path, original.state.task, original.state.proposals, synthetic_consent=True
        )
    )
    assert run.record.state == original.state
    assert (
        evaluate_outcome(original.state.task, run.record.state.final_allocation, ("a0", "a1"))
        == original.outcome
    )
    assert len(run.observations) == 6
    assert {o.action_state for o in run.observations} == {"Succeeded"}
    assert all(o.synthetic_consent for o in run.observations)
    assert [len(store.committed()) for store in run.stores] == [2, 2, 2]
    for key in ("store_id", "subject_id"):
        assert len({s.identity[key] for s in run.stores}) == 3
    assert len({s.identity["binding"]["execution_scope"] for s in run.stores}) == 3
    # Recovery of the derived Arena does not issue another AIG Action/effect.
    replayed = reconstruct(original.state.task, tuple(reversed(run.stores)), finalize=True)
    assert canonical_json(replayed) == canonical_json(run.record.state)
    assert [len(store.committed()) for store in run.stores] == [2, 2, 2]
    with pytest.raises(ValueError, match="Duplicate effect"):
        reconstruct(original.state.task, (*run.stores, run.stores[0]), finalize=True)


def test_bridge_requires_a_durable_effect_and_exact_arena_revision(aig_case):
    directory, state, store, prepared = aig_case
    with pytest.raises(ValueError, match="committed"):
        apply_committed(state, store, effect_key=str(uuid4()))
    from aig_helpers import execute_reviewed, principal

    from pactlens.aig.consumer import consumer

    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
    applied = apply_committed(state, store, effect_key=action.effect_key)
    with pytest.raises(ValueError, match="revision/state"):
        apply_committed(applied, store, effect_key=action.effect_key)
    assert len(applied.proposals) == 1


def test_harness_requires_explicit_synthetic_consent(tmp_path):
    fixture = run_fixture("c_plus")
    with pytest.raises(ValueError, match="synthetic_consent"):
        asyncio.run(run_synthetic_rounds(tmp_path, fixture.state.task, fixture.state.proposals))


def test_cross_store_conflicting_base_revisions_fail_reconstruction(tmp_path, task):
    from aig_helpers import execute_reviewed, principal

    from pactlens.aig.consumer import consumer, provision
    from pactlens.arena.allocation import lawful_reference
    from pactlens.arena.models import ArenaState, Proposal
    from pactlens.arena.transitions import begin

    state = begin(ArenaState(task), expected_revision=0)
    stores = []
    for actor in task.agents[:2]:
        directory = tmp_path / actor.agent_id
        store = provision(directory, task, actor.agent_id)
        prepared = store.prepare(
            state, Proposal(actor.agent_id, 1, task.task_hash, lawful_reference(task))
        )
        with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
            _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
            assert action.state.value == "Succeeded"
        stores.append(store)
    # Separate local commits do not provide distributed Arena serialization.
    with pytest.raises(ValueError, match="base revisions"):
        reconstruct(task, stores)
    assert [len(store.committed()) for store in stores] == [1, 1]
