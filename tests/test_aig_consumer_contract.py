import asyncio
import socket

import pytest
from aig_helpers import execute_reviewed, principal

from pactlens.aig.consumer import consumer, provision
from pactlens.arena.allocation import lawful_reference
from pactlens.arena.models import ArenaState, Proposal
from pactlens.arena.transitions import begin


def test_real_installed_lifecycle_and_verified_receipt(tmp_path, task):
    state = begin(ArenaState(task), expected_revision=0)
    directory = tmp_path / "actor"
    store = provision(directory, task, "a0")
    prepared = store.prepare(state, Proposal("a0", 1, task.task_hash, lawful_reference(task)))
    with consumer(directory, state, prepared, predecessor_stopped=True) as (
        runtime,
        executor,
        store,
    ):
        run, action, command = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert run.state.value == "Approved"
        assert action.state.value == "Succeeded"
        assert runtime.gateway.tool_timeout_seconds == 5
        saved = store.committed()
        assert len(saved) == 1
        assert saved[0].effect_key == action.effect_key
        assert saved[0].receipt_reference == action.result["receipt_reference"]
        assert saved[0].prepared == prepared
        result = asyncio.run(runtime.gateway.execute(command, principal(runtime, directory)))
        assert result.replayed and result.action == action
        assert executor.calls == 1


def test_owner_attestation_is_required(aig_case):
    directory, state, store, prepared = aig_case
    with pytest.raises(Exception) as caught, consumer(directory, state, prepared):
        pytest.fail("AIG owner fence accepted missing attestation")
    assert caught.value.code.value == "ACTION_NOT_AUTHORIZED"
    assert store.committed() == ()


def test_offline_guard_still_blocks_application_connections():
    with socket.socket() as outbound, pytest.raises(AssertionError, match="forbidden"):
        outbound.connect(("127.0.0.1", 11434))
    with pytest.raises(AssertionError, match="forbidden"):
        socket.create_connection(("example.invalid", 443))


def test_consumer_bounds_snapshot_without_changing_arena_contract(tmp_path, task):
    from dataclasses import replace

    large_actor = replace(
        task.agents[0], skills=("ops", *(f"s{n:04d}" + "x" * 30 for n in range(2048)))
    )
    task = replace(task, agents=(large_actor, *task.agents[1:]))
    state = begin(ArenaState(task), expected_revision=0)
    store = provision(tmp_path / "bounded", task, "a0")
    with pytest.raises(ValueError, match="bounded storage"):
        store.prepare(state, Proposal("a0", 1, task.task_hash, lawful_reference(task)))
    assert store.committed() == ()
