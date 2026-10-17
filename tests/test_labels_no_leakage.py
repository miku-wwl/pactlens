import json
from dataclasses import fields, replace

import pytest

from pactlens.arena.models import ArenaState
from pactlens.evidence.projection import export_evidence, project_evidence
from pactlens.evidence.records import EpisodeRecord
from pactlens.research.fixtures import load_specs, run_fixture
from pactlens.research.manifest import build_manifest
from pactlens.research.seeds import SeedMaterial
from pactlens.serialization import canonical_json

PUBLIC_ID = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"


def test_nested_private_markers_absent_in_all_public_representations_and_paths(tmp_path):
    run = run_fixture("c_plus")
    original = build_manifest().episodes[0]
    markers = [f"PRIVATE_MARKER_{i:02}" for i in range(22)]
    manifest = replace(
        original,
        episode_id=markers[0],
        group_id=markers[1],
        split=markers[2],
        condition=markers[3],
        pair_id=markers[4],
        twin_episode_id=markers[5],
        task_hash=markers[6],
        configuration_hash=markers[7],
        brief_revision=markers[8],
        source_revision=markers[9],
        environment=(("internal", markers[10]),),
        task_seed=SeedMaterial(markers[11], markers[12], 0),
        model_request_seeds=(SeedMaterial(markers[13], markers[14], 0),),
        evaluator_pair=(markers[20], markers[21]),
        assigned_coalition=(markers[20], markers[21]),
    )
    adjudication = replace(
        run.record.adjudication,
        notes=(markers[15], markers[16], markers[17]),
        instruction_origin=markers[18],
    )
    record = replace(
        run.record,
        manifest=manifest,
        adjudication=adjudication,
        private_metadata={"nested": [{"label": markers[19], "oracle": {"trace": markers}}]},
        source_path="/private/" + "/".join(markers) + "/C_PLUS.json",
    )
    evidence = project_evidence(record, public_id=PUBLIC_ID)
    exported = export_evidence(record, tmp_path, public_id=PUBLIC_ID)
    # Exercise the object adapter, its defensive mapping, actual exported bytes and filename.
    outputs = (
        evidence.to_json(),
        repr(evidence),
        repr(evidence.as_mapping()),
        canonical_json(evidence.as_mapping()),
        exported.read_text(encoding="utf-8"),
        exported.name,
        repr(record),
    )
    assert all(marker not in output for marker in markers for output in outputs)
    assert exported.name == PUBLIC_ID + ".json"
    assert set(evidence.as_mapping()) == {
        "schema_version",
        "episode_public_id",
        "public_task",
        "messages",
        "proposal_slots",
        "execution",
        "events",
        "event_ordering",
    }
    assert {f.name for f in fields(evidence)} == {"json_text"}
    assert evidence.as_mapping()["execution"]["public_outcome"]["global_cost"] == 12
    assert evidence.to_json() == project_evidence(run.record, public_id=PUBLIC_ID).to_json()


def test_projector_never_inspects_private_objects():
    class Poison:
        def __repr__(self):
            raise AssertionError("Private object was inspected")

        def __iter__(self):
            raise AssertionError("Private object was iterated")

    run = run_fixture("c_plus")
    record = replace(
        run.record,
        private_metadata=Poison(),
        manifest=Poison(),
        adjudication=None,
        source_path=Poison(),
    )
    assert (
        project_evidence(record, public_id=PUBLIC_ID).as_mapping()["execution"]["status"]
        == "FINALIZED"
    )


def test_legitimate_predictive_messages_actions_and_outcomes_are_preserved():
    run = run_fixture("c_plus")
    data = project_evidence(run.record, public_id=PUBLIC_ID).as_mapping()
    assert data["messages"]["records"][0]["text"] == run.record.messages[0].text
    assert data["messages"]["records"][1]["text"].startswith("Agreed")
    assert data["messages"]["records"][0]["channel"] == "private"
    assert data["execution"]["public_outcome"]["global_cost"] == 12
    assert all(row["agent"] == "Actor-3" for row in data["execution"]["allocation"])
    assert len(data["proposal_slots"]) == 6
    assert all(slot["status"] == "SUBMITTED" for slot in data["proposal_slots"])
    text = json.dumps(data)
    for forbidden in (
        "pair_benefit",
        "regret",
        "optimum_cost",
        "reference",
        "assignment",
        "twin_episode_id",
        "private_brief",
        "human_adjudicated",
        "receipt",
    ):
        assert '"' + forbidden + '"' not in text


def test_observed_text_is_not_blacklist_sanitized():
    run = run_fixture("n3_cooperation")
    message = replace(
        run.record.messages[0], text="KEEP_VISIBLE: discuss observed behavior, not a label."
    )
    record = replace(run.record, messages=(message,), event_journal=None)
    assert (
        project_evidence(record, public_id=PUBLIC_ID).as_mapping()["messages"]["records"][0]["text"]
        == message.text
    )


def test_schema_and_slot_keys_are_condition_independent():
    mappings = [
        project_evidence(run_fixture(spec).record, public_id=PUBLIC_ID).as_mapping()
        for spec in load_specs()
    ]
    keys = set(mappings[0])
    for data in mappings:
        assert set(data) == keys
        assert set(data["messages"]) == {"status", "records"}
        assert set(data["execution"]) == {"status", "allocation", "public_outcome"}
        assert len(data["proposal_slots"]) == 6
        assert all(
            set(slot) == {"round", "agent", "status", "assignments"}
            for slot in data["proposal_slots"]
        )
    missing = project_evidence(
        run_fixture("missing_proposal").record, public_id=PUBLIC_ID
    ).as_mapping()
    assert [s["status"] for s in missing["proposal_slots"]].count("MISSING") == 1
    incomplete = project_evidence(
        run_fixture("incomplete_evidence").record, public_id=PUBLIC_ID
    ).as_mapping()
    assert incomplete["messages"]["status"] == "INCOMPLETE"


def test_unexecuted_record_and_missing_values_are_explicit(task):
    data = project_evidence(EpisodeRecord(ArenaState(task)), public_id=PUBLIC_ID).as_mapping()
    assert data["execution"] == {
        "status": "NOT_FINALIZED",
        "allocation": None,
        "public_outcome": None,
    }
    assert all(
        row["status"] == "NOT_REACHED" and row["assignments"] is None
        for row in data["proposal_slots"]
    )


def test_adapters_return_defensive_copies_not_private_references():
    record = run_fixture("c_plus").record
    evidence = project_evidence(record, public_id=PUBLIC_ID)
    altered = evidence.as_mapping()
    altered["messages"]["records"][0]["text"] = "modified copy"
    assert evidence.as_mapping()["messages"]["records"][0]["text"] == record.messages[0].text


@pytest.mark.parametrize(
    "public_id", ["P001-C_PLUS", "../private", "00000000-0000-0000-0000-000000000000", 123]
)
def test_public_identifier_rejects_hidden_paths_and_non_uuid_ids(public_id):
    with pytest.raises(ValueError):
        project_evidence(run_fixture("c_plus").record, public_id=public_id)


def test_export_never_overwrites_existing_observation(tmp_path):
    record = run_fixture("c_plus").record
    path = export_evidence(record, tmp_path, public_id=PUBLIC_ID)
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        export_evidence(record, tmp_path, public_id=PUBLIC_ID)
    assert path.read_bytes() == original
