"""Offline-only fixture tests: external socket connections are forbidden."""

import socket

import pytest

from pactlens.arena.models import Allocation, ArenaState, Assignment, Proposal
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.research.fixtures import fixture_task


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    original_connect = socket.socket.connect
    original_socketpair = socket.socketpair

    def local_socketpair(*args, **kwargs):
        # Windows asyncio uses the standard-library socketpair fallback for its
        # internal wakeup pipe. Permit only that synchronous stdlib operation;
        # user/API connects remain blocked once socketpair returns.
        with monkeypatch.context() as temporary:
            temporary.setattr(socket.socket, "connect", original_connect)
            return original_socketpair(*args, **kwargs)

    def denied(*args, **kwargs):
        raise AssertionError("Network access is forbidden in Phase 1 tests")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "socketpair", local_socketpair)


@pytest.fixture
def task():
    return fixture_task()


@pytest.fixture
def aig_case(tmp_path, task):
    from pactlens.aig.consumer import provision
    from pactlens.arena.allocation import lawful_reference

    state = begin(ArenaState(task), expected_revision=0)
    directory = tmp_path / "actor"
    store = provision(directory, task, "a0")
    prepared = store.prepare(state, Proposal("a0", 1, task.task_hash, lawful_reference(task)))
    return directory, state, store, prepared


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
