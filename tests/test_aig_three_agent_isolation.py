import asyncio
import json
from contextlib import ExitStack
from uuid import uuid4

import pytest
from agentic_intent_gate.runtime import ActionCommand
from aig_helpers import approved_action, authorize, execute_reviewed, principal

from pactlens.aig.consumer import consumer, load_store, provision
from pactlens.aig.contract import DeterministicProvider
from pactlens.arena.allocation import lawful_reference
from pactlens.arena.models import ArenaState, Proposal
from pactlens.arena.transitions import begin


def test_cross_agent_principal_token_and_action_authorization_are_isolated(tmp_path, task):
    state = begin(ArenaState(task), expected_revision=0)
    with ExitStack() as contexts:
        combinations = []
        for index, actor in enumerate(task.agents):
            directory = tmp_path / str(index)
            store = provision(directory, task, actor.agent_id)
            prepared = store.prepare(
                state, Proposal(actor.agent_id, 1, task.task_hash, lawful_reference(task))
            )
            runtime, _, _ = contexts.enter_context(
                consumer(directory, state, prepared, predecessor_stopped=True)
            )
            operator = principal(runtime, directory)
            _, action = asyncio.run(approved_action(runtime, operator))
            combinations.append((runtime, operator, action, store, directory))
        a, ap, aa, _, ad = combinations[0]
        b, bp, ba, _, _ = combinations[1]
        aa = authorize(a, aa, ap)
        with pytest.raises(Exception) as caught:
            b.verifier.verify("Bearer " + (ad / "capability").read_text("ascii"))
        assert caught.value.code.value == "AUTHENTICATION_REQUIRED"
        for operation in (
            lambda: b.gateway.get(ba.action_id, ap),
            lambda: b.gateway.authorize(ActionCommand(ba.action_id, 1, str(uuid4())), ap),
            lambda: asyncio.run(
                b.gateway.execute(ActionCommand(ba.action_id, 1, str(uuid4())), ap)
            ),
        ):
            with pytest.raises(Exception) as caught:
                operation()
            assert caught.value.code.value == "ACTION_NOT_AUTHORIZED"
        with pytest.raises(Exception) as caught:
            asyncio.run(b.gateway.execute(ActionCommand(ba.action_id, 1, str(uuid4())), bp))
        assert caught.value.code.value == "ACTION_NOT_EXECUTABLE"
        assert all(store.committed() == () for _, _, _, store, _ in combinations)


def test_actor_cannot_stage_or_resolve_another_actors_proposal(tmp_path, task):
    state = begin(ArenaState(task), expected_revision=0)
    a_dir, b_dir = tmp_path / "a", tmp_path / "b"
    a = provision(a_dir, task, "a0")
    b = provision(b_dir, task, "a1")
    other = Proposal("a1", 1, task.task_hash, lawful_reference(task))
    with pytest.raises(ValueError, match="actor/task"):
        a.prepare(state, other)
    bp = b.prepare(state, other)
    ap = a.prepare(state, Proposal("a0", 1, task.task_hash, lawful_reference(task)))
    provider = DeterministicProvider(bp)
    with consumer(a_dir, state, ap, provider=provider, predecessor_stopped=True) as (runtime, _, _):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, a_dir)))
        assert action.state.value == "Failed"
        assert a.committed() == b.committed() == ()


def test_persisted_identity_cannot_be_regenerated_or_rebound(aig_case):
    directory, state, store, _ = aig_case
    original = store.identity
    assert load_store(directory).identity == original
    with pytest.raises(ValueError, match="empty"):
        provision(directory, state.task, "a0")
    identity_path = directory / "identity.json"
    changed = {**original, "store_id": str(uuid4())}
    identity_path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="STORE_IDENTITY_MISMATCH"):
        load_store(directory)
