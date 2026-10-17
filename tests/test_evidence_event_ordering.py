import os
import subprocess
import sys
from dataclasses import replace

import pytest

from pactlens.arena.allocation import lawful_reference
from pactlens.arena.models import ArenaState, Proposal
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.evidence.projection import project_evidence
from pactlens.evidence.records import (
    Channel,
    EpisodeRecord,
    Message,
    capture_message,
    capture_outcome,
    capture_transition,
)
from pactlens.research.fixtures import load_specs, run_fixture

PUBLIC_ID = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"


def projected(record):
    return project_evidence(record, public_id=PUBLIC_ID).as_mapping()


@pytest.mark.parametrize("message_first", [True, False])
def test_capture_preserves_actual_interleaving(task, message_first):
    state = begin(ArenaState(task), expected_revision=0)
    journal = capture_transition(state)
    message = Message(1, 1, "a0", ("a1",), Channel.PUBLIC, "An observed agreement")
    if message_first:
        journal = capture_message(state, message, journal)
    state = submit_proposal(
        state,
        Proposal("a2", 1, task.task_hash, lawful_reference(task)),
        actor_id="a2",
        expected_revision=state.revision,
    )
    journal = capture_transition(state, journal)
    if not message_first:
        journal = capture_message(state, message, journal)
    data = projected(EpisodeRecord(state, (message,), event_journal=journal))
    events = {e["type"]: e for e in data["events"]}
    assert (
        events["MESSAGE"]["logical_position"] < events["PROPOSAL_ACCEPTED"]["logical_position"]
    ) == message_first
    assert data["event_ordering"]["status"] == "RECORDED_CROSS_STREAM"


def test_proposal_order_is_actual_acceptance_not_actor_sort(task):
    state = begin(ArenaState(task), expected_revision=0)
    journal = capture_transition(state)
    for actor in ("a2", "a0", "a1"):
        state = submit_proposal(
            state,
            Proposal(actor, 1, task.task_hash, lawful_reference(task)),
            actor_id=actor,
            expected_revision=state.revision,
        )
        journal = capture_transition(state, journal)
    events = projected(EpisodeRecord(state, event_journal=journal))["events"]
    proposals = [e for e in events if e["type"] == "PROPOSAL_ACCEPTED"]
    assert [e["actor"] for e in proposals] == ["Actor-3", "Actor-1", "Actor-2"]
    assert [e["logical_position"] for e in proposals] == [2, 3, 4]


def test_round_closure_final_execution_and_outcome_positions():
    data = projected(run_fixture("c_plus").record)
    events = data["events"]
    closure = next(e for e in events if e["type"] == "ROUND_CLOSED")
    final = next(e for e in events if e["type"] == "FINAL_ALLOCATION_EXECUTED")
    outcome = next(e for e in events if e["type"] == "PUBLIC_OUTCOME_OBSERVED")
    assert closure["payload"]["next_round"] == 2
    assert final["payload"]["round_closed"] is True
    assert closure["logical_position"] < final["logical_position"] < outcome["logical_position"]
    assert all(
        e["logical_position"] < final["logical_position"]
        for e in events
        if e["type"] == "PROPOSAL_ACCEPTED"
    )


def test_legacy_record_has_source_order_but_unknown_cross_stream_order():
    record = replace(run_fixture("c_plus").record, event_journal=None)
    data = projected(record)
    assert data["event_ordering"]["status"] == "SOURCE_LOCAL_ONLY"
    assert all(e["logical_position"] is None for e in data["events"])
    arena = [e["source_sequence"] for e in data["events"] if e["ordering_stream"] == "arena"]
    assert arena == list(range(1, 10))


def test_partial_capture_and_incomplete_observations_are_independent():
    record = run_fixture("incomplete_evidence").record
    partial = replace(record, event_journal=record.event_journal[:2])
    data = projected(partial)
    assert data["messages"]["status"] == "INCOMPLETE"
    assert data["event_ordering"]["status"] == "PARTIAL_CROSS_STREAM"
    assert sum(e["logical_position"] is not None for e in data["events"]) == 2
    assert len([e for e in data["events"] if e["type"] == "MESSAGE"]) == 1


def test_equal_cross_stream_positions_are_explicitly_unresolved(task):
    state = begin(ArenaState(task), expected_revision=0)
    message = Message(1, 1, "a0", ("a1",), Channel.PUBLIC, "Batch order unknown")
    journal = capture_message(state, message, capture_transition(state), logical_position=1)
    data = projected(EpisodeRecord(state, (message,), event_journal=journal))
    assert {e["logical_position"] for e in data["events"]} == {1}
    assert "EQUAL_IS_UNRESOLVED" in data["event_ordering"]["logical_positions"]


@pytest.mark.parametrize(
    "change",
    [
        "message",
        "proposal",
        "missing_message",
        "digest",
        "unknown_reference",
        "duplicate",
        "round",
        "outcome",
    ],
)
def test_inconsistent_capture_is_rejected(change):
    run = run_fixture("c_plus")
    record = run.record
    journal = record.event_journal
    changes = {}
    if change == "message":
        changes["messages"] = (
            replace(record.messages[0], text="Reconstructed different text"),
            *record.messages[1:],
        )
    elif change == "proposal":
        # Round one does not affect final allocation: journal binding still detects rewriting it.
        proposals = (
            replace(run.state.proposals[0], allocation=run.state.final_allocation),
            *run.state.proposals[1:],
        )
        changes["state"] = replace(run.state, proposals=proposals)
    elif change == "missing_message":
        changes["messages"] = record.messages[:1]
    elif change == "digest":
        changes["event_journal"] = (replace(journal[0], source_digest="0" * 64), *journal[1:])
    elif change == "unknown_reference":
        changes["event_journal"] = (replace(journal[0], sequence=9), *journal[1:])
    elif change == "duplicate":
        changes["event_journal"] = (journal[0], *journal)
    elif change == "round":
        # Move round-one message after finalization while retaining its content binding.
        moved = replace(journal[1], logical_position=journal[-1].logical_position + 1)
        changes["event_journal"] = (*journal[:1], *journal[2:], moved)
    else:
        changes["event_journal"] = (replace(journal[-1], logical_position=1), *journal[:-1])
    with pytest.raises(ValueError):
        replace(record, **changes)


def test_no_capture_of_messages_after_round_closes(task):
    state = begin(ArenaState(task), expected_revision=0)
    state = close_round(state, expected_revision=state.revision)
    with pytest.raises(ValueError, match="open round"):
        capture_message(state, Message(1, 1, "a0", ("a1",), Channel.PUBLIC, "Too late"))
    with pytest.raises(ValueError, match="No final"):
        capture_outcome(state)


def test_source_local_order_cannot_be_reversed_or_equal():
    record = run_fixture("c_plus").record
    journal = record.event_journal
    with pytest.raises(ValueError, match="source-local"):
        replace(record, event_journal=(journal[0], replace(journal[3], logical_position=1)))


def test_round_constraints_hold_even_when_closure_capture_is_missing(task):
    state = begin(ArenaState(task), expected_revision=0)
    state = submit_proposal(
        state,
        Proposal("a0", 1, task.task_hash, lawful_reference(task)),
        actor_id="a0",
        expected_revision=state.revision,
    )
    proposal_journal = capture_transition(state, logical_position=2)
    state = close_round(state, expected_revision=state.revision)
    message = Message(1, 2, "a0", ("a1",), Channel.PUBLIC, "Round two")
    message_journal = capture_message(state, message, logical_position=1)
    with pytest.raises(ValueError, match="message round"):
        EpisodeRecord(state, (message,), event_journal=(*message_journal, *proposal_journal))


def test_missing_ballot_does_not_become_an_accepted_event():
    data = projected(run_fixture("missing_proposal").record)
    proposals = [e for e in data["events"] if e["type"] == "PROPOSAL_ACCEPTED"]
    assert len(proposals) == 5
    assert not any(e["actor"] == "Actor-3" and e["round"] == 2 for e in proposals)
    final = next(e for e in data["events"] if e["type"] == "FINAL_ALLOCATION_EXECUTED")
    assert final["payload"]["missing_agents"] == ["Actor-3"]


def test_projection_rechecks_capture_after_constructor_bypass():
    record = run_fixture("c_plus").record
    object.__setattr__(record.messages[0], "text", "Changed after capture")
    with pytest.raises(ValueError, match="Capture source mismatch"):
        projected(record)


def test_new_event_payloads_share_existing_observations_and_never_private_fields():
    for spec in load_specs():
        record = run_fixture(spec).record
        data = projected(record)
        for e in data["events"]:
            assert set(e) == {
                "event_id",
                "type",
                "actor",
                "round",
                "ordering_stream",
                "source_sequence",
                "logical_position",
                "payload",
            }
            assert "source_digest" not in str(e)
            if e["type"] == "MESSAGE":
                assert e["payload"] in data["messages"]["records"]
            if e["type"] == "PROPOSAL_ACCEPTED":
                slot = next(
                    s
                    for s in data["proposal_slots"]
                    if (s["round"], s["agent"]) == (e["round"], e["actor"])
                )
                assert e["payload"]["assignments"] == slot["assignments"]
        altered = replace(
            record,
            private_metadata={"condition": "PRIVATE_EVENT_MARKER", "pair": "PRIVATE_PAIR_MARKER"},
        )
        assert projected(altered) == data


def test_event_serialization_cross_process_and_import_order(tmp_path):
    program = """
import importlib
for name in MODULES:
    importlib.import_module('pactlens.' + name)
from pactlens.evidence.projection import project_evidence
from pactlens.research.fixtures import run_fixture
print(project_evidence(run_fixture('c_plus').record, public_id='d6dd1a02-5135-4fd7-9844-2dd36366a68e').to_json())
"""
    outputs = []
    orders = [
        ("arena.allocation", "arena.models", "evidence.records"),
        ("evidence.projection", "arena.outcomes", "arena.transitions"),
    ]
    for seed, modules in zip(("13", "947"), orders, strict=True):
        result = subprocess.check_output(
            [sys.executable, "-c", "MODULES=" + repr(modules) + program],
            cwd=tmp_path,
            env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONIOENCODING": "utf-8"},
            text=True,
            encoding="utf-8",
        )
        outputs.append(result)
    assert outputs[0] == outputs[1]
