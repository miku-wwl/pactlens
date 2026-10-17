import asyncio
from dataclasses import replace

import pytest

from pactlens.aig.workflow import run_synthetic_rounds
from pactlens.evidence.aig_adapter import project_aig_evidence
from pactlens.evidence.projection import project_evidence
from pactlens.research.fixtures import run_fixture

PUBLIC_ID = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"


@pytest.fixture
def integration_run(tmp_path):
    original = run_fixture("c_plus")
    return asyncio.run(
        run_synthetic_rounds(
            tmp_path, original.state.task, original.state.proposals, synthetic_consent=True
        )
    )


def test_known_capture_and_detached_public_allowlist(integration_run):
    run = integration_run
    evidence = project_aig_evidence(
        run.record, run.observations, public_id=PUBLIC_ID, shared_capture=True
    )
    data = evidence.as_mapping()
    existing = project_evidence(run.record, public_id=PUBLIC_ID).as_mapping()
    assert {key: data[key] for key in existing} == existing
    execution = data["aig_execution"]
    assert execution["status"] == "COMPLETE"
    assert execution["cross_source_order"] == "RECORDED_SHARED_LOGICAL_CAPTURE"
    assert len(execution["records"]) == 6
    for row in execution["records"]:
        assert set(row) == {
            "action_id",
            "actor",
            "round",
            "action_state",
            "approval_state",
            "authorized",
            "payload_digest",
            "proposal_digest",
            "receipt_reference",
            "receipt_status",
            "synthetic_consent",
            "ordering_stream",
            "source_sequence",
            "logical_position",
        }
        assert row["synthetic_consent"] and row["authorized"]
        assert row["receipt_status"] == "VERIFIED_COMMITTED"
        applied = next(
            e
            for e in data["events"]
            if e["type"] == "PROPOSAL_ACCEPTED"
            and (e["actor"], e["round"]) == (row["actor"], row["round"])
        )
        assert row["logical_position"] < applied["logical_position"]
    for forbidden in (
        "capability",
        "authorization_id",
        "subject_id",
        "execution_scope",
        "store_id",
        "plan_digest",
        "optimum_cost",
        "regret",
        "pair_benefit",
    ):
        assert '"' + forbidden + '"' not in evidence.to_json()


def test_legacy_and_independent_sources_do_not_gain_total_order(integration_run):
    run = integration_run
    record = replace(run.record, event_journal=None)
    observations = tuple(replace(o, logical_position=None) for o in run.observations)
    data = project_aig_evidence(record, observations, public_id=PUBLIC_ID).as_mapping()
    assert data["event_ordering"]["status"] == "SOURCE_LOCAL_ONLY"
    assert data["aig_execution"]["cross_source_order"] == "UNKNOWN"
    assert all(r["logical_position"] is None for r in data["aig_execution"]["records"])
    with pytest.raises(ValueError, match="clock"):
        project_aig_evidence(record, run.observations, public_id=PUBLIC_ID)


def test_private_marker_and_actual_credentials_never_enter_l3(integration_run):
    run = integration_run
    marker = "PRIVATE_CONDITION_COALITION_SEED_PAIR_ORACLE_MARKER"
    record = replace(
        run.record,
        private_metadata={"nested": [{"condition": marker, "brief": marker, "truth": marker}]},
        source_path=marker,
        manifest=object(),
    )
    data = project_aig_evidence(record, run.observations, public_id=PUBLIC_ID, shared_capture=True)
    assert marker not in data.to_json()
    for store in run.stores:
        token = (store.path.parent / "capability").read_text("ascii")
        assert token not in data.to_json()
        assert str(store.path) not in data.to_json()
        assert store.identity["binding"]["execution_scope"] not in data.to_json()
    assert (
        data.to_json()
        == project_aig_evidence(
            run.record, run.observations, public_id=PUBLIC_ID, shared_capture=True
        ).to_json()
    )


@pytest.mark.parametrize("mutation", ["digest", "receipt", "position", "duplicate"])
def test_contradictory_public_correlations_are_rejected(integration_run, mutation):
    run = integration_run
    first = run.observations[0]
    if mutation == "digest":
        first = replace(first, proposal_digest="0" * 64)
    elif mutation == "receipt":
        first = replace(first, receipt_reference="PRIVATE_RECEIPT_MARKER")
    elif mutation == "position":
        first = replace(first, logical_position=4096)
    observations = (first, *run.observations[1:])
    if mutation == "duplicate":
        observations = (first, first)
    with pytest.raises(ValueError):
        project_aig_evidence(run.record, observations, public_id=PUBLIC_ID, shared_capture=True)


def test_missing_execution_evidence_is_explicit(integration_run):
    data = project_aig_evidence(integration_run.record, (), public_id=PUBLIC_ID).as_mapping()
    assert data["aig_execution"]["status"] == "INCOMPLETE"
    assert data["aig_execution"]["records"] == []
    assert data["execution"]["public_outcome"]["global_cost"] == 12


def test_shared_capture_cannot_place_round_two_before_round_one_closure(integration_run):
    run = integration_run
    observations = tuple(
        replace(o, logical_position=2) if o.round_number == 2 and o.actor_id == "a0" else o
        for o in run.observations
    )
    with pytest.raises(ValueError, match="round boundary"):
        project_aig_evidence(run.record, observations, public_id=PUBLIC_ID, shared_capture=True)
