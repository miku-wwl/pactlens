"""Offline-only fixture tests: external socket connections are forbidden."""

import socket

import pytest

from pactlens.arena.models import Allocation, ArenaState, Assignment, Proposal
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.research.fixtures import fixture_task


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Network access is forbidden in Phase 1 tests")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture
def task():
    return fixture_task()


def allocation(task, *owners):
    return Allocation(
        tuple(Assignment(i.incident_id, a) for i, a in zip(task.incidents, owners, strict=True))
    )


def replay(task, round_1, round_2):
    state = begin(ArenaState(task), expected_revision=0)
    for number, ballots in ((1, round_1), (2, round_2)):
        for actor, ballot in ballots:
            state = submit_proposal(
                state,
                Proposal(actor, number, task.task_hash, ballot),
                actor_id=actor,
                expected_revision=state.revision,
            )
        state = close_round(state, expected_revision=state.revision)
    return state
