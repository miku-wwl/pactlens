from dataclasses import replace

import pytest

from pactlens.arena.allocation import lawful_reference
from pactlens.arena.models import ArenaError
from pactlens.evidence.projection import project_evidence
from pactlens.evidence.records import EpisodeRecord
from pactlens.research.fixtures import run_fixture

PUBLIC_ID = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"


def test_finalized_allocation_substitution_is_rejected():
    run = run_fixture("c_plus")
    with pytest.raises(ArenaError, match="FINAL_ALLOCATION_MISMATCH"):
        replace(run.state, final_allocation=lawful_reference(run.state.task))


def test_other_feasible_substitution_is_rejected():
    from conftest import allocation

    run = run_fixture("c_plus")
    with pytest.raises(ArenaError, match="FINAL_ALLOCATION_MISMATCH"):
        replace(run.state, final_allocation=allocation(run.state.task, "a0", "a0", "a0"))


def test_changed_ballots_cannot_preserve_contradictory_final_allocation():
    run = run_fixture("c_plus")
    lawful = lawful_reference(run.state.task)
    proposals = tuple(replace(p, allocation=lawful) for p in run.state.proposals)
    with pytest.raises(ArenaError, match="FINAL_ALLOCATION_MISMATCH"):
        replace(run.state, proposals=proposals)


@pytest.mark.parametrize(
    "field",
    [
        "global_cost",
        "optimum_cost",
        "regret",
        "pair_benefit",
        "outsider_burden_shift",
        "actual",
        "reference",
        "actual_costs",
        "reference_costs",
        "feasible",
    ],
)
def test_independently_changed_stored_mechanics_are_rejected(field):
    run = run_fixture("c_plus")
    outcome = run.outcome
    lawful = lawful_reference(run.state.task)
    changes = {
        "actual": lawful,
        "reference": outcome.actual,
        "actual_costs": outcome.reference_costs,
        "reference_costs": outcome.actual_costs,
        "feasible": 1,
    }
    changed = replace(outcome, **{field: changes.get(field, 777)})
    with pytest.raises(ArenaError, match="STORED_OUTCOME_MISMATCH"):
        replace(
            run.record, adjudication=replace(run.record.adjudication, mechanical_outcome=changed)
        )


@pytest.mark.parametrize(
    "mutation", ["revision", "missing_proposal", "missing_history", "closure", "status"]
)
def test_contradictory_finalization_metadata_is_rejected(mutation):
    from pactlens.arena.models import Lifecycle

    state = run_fixture("c_plus").state
    changes = {
        "revision": {"revision": state.revision - 1},
        "missing_proposal": {"proposals": state.proposals[:-1]},
        "missing_history": {"history": state.history[:-1], "revision": state.revision - 1},
        "closure": {
            "history": (*state.history[:-1], replace(state.history[-1], missing_agents=("a0",)))
        },
        "status": {"status": Lifecycle.ROUND_2},
    }
    with pytest.raises(ArenaError):
        replace(state, **changes[mutation])


def test_invalid_reconstructed_round_one_ballot_is_rejected():
    from conftest import allocation

    state = run_fixture("c_plus").state
    bad = replace(state.proposals[0], allocation=allocation(state.task, "unknown", "a0", "a1"))
    with pytest.raises(ArenaError):
        replace(state, proposals=(bad, *state.proposals[1:]))


@pytest.mark.parametrize("target", ["state", "outcome"])
def test_projection_rechecks_input_after_constructor_bypass(target):
    run = run_fixture("c_plus")
    if target == "state":
        object.__setattr__(run.state, "final_allocation", lawful_reference(run.state.task))
    else:
        object.__setattr__(run.outcome, "global_cost", -1)
    with pytest.raises(ArenaError):
        project_evidence(run.record, public_id=PUBLIC_ID)


def test_non_typed_stored_outcome_is_not_silently_ignored():
    with pytest.raises(ValueError, match="Typed adjudication"):
        replace(run_fixture("c_plus").record, adjudication=object())


def test_stored_outcome_requires_final_state(task):
    from pactlens.arena.models import ArenaState

    with pytest.raises(ValueError, match="requires finalized"):
        EpisodeRecord(ArenaState(task), adjudication=run_fixture("c_plus").record.adjudication)
