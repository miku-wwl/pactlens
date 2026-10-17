import asyncio
import sqlite3
from dataclasses import replace
from uuid import uuid4

import pytest
from agentic_intent_gate.runtime import AttemptContext, ExecutionSpec, Outcome
from aig_helpers import approved_action, execute_reviewed, principal

from pactlens.aig.consumer import consumer
from pactlens.aig.contract import DeterministicProvider, binding_for
from pactlens.aig.effect_store import ProposalStore
from pactlens.aig.executor import ProposalExecutor
from pactlens.serialization import canonical_json


async def direct(executor, spec, key):
    """Executor-port contract test only; application dispatch always uses Gateway."""
    context = AttemptContext(str(uuid4()), asyncio.get_running_loop().time() + 5, asyncio.Event())
    return await executor.execute(spec, key, context)


def test_effect_key_idempotency_and_payload_conflict(aig_case):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, executor, _):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        spec = ExecutionSpec.from_compiled(action.spec)
        again = asyncio.run(direct(executor, spec, action.effect_key))
        assert again.category == Outcome.SUCCESS
        assert again.receipt_reference == action.result["receipt_reference"]
        other = store.prepare(state, prepared.proposal)
        conflict = asyncio.run(
            direct(executor, replace(spec, arguments=other.arguments), action.effect_key)
        )
        assert conflict.category == Outcome.CONFIRMED_FAILURE
        assert conflict.no_effect_reason == "PAYLOAD_CONFLICT"
        assert len(store.committed()) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("tool_name", "other"),
        ("tool_version", "2"),
        ("adapter_id", "other"),
        ("binding_revision", "other"),
        ("execution_scope", None),
        ("target", "other"),
        ("identity_revision", "demo-note-payload-v1"),
    ],
)
def test_executor_rechecks_complete_binding(aig_case, field, value):
    _directory, state, store, prepared = aig_case
    binding = binding_for(store.identity["binding"]["execution_scope"])
    from agentic_intent_gate.runtime import EXTERNAL_PAYLOAD_REVISION

    spec = ExecutionSpec(
        **vars(binding), arguments=prepared.arguments, identity_revision=EXTERNAL_PAYLOAD_REVISION
    )
    executor = ProposalExecutor(store, binding, state)
    result = asyncio.run(
        direct(executor, replace(spec, **{field: value or str(uuid4())}), str(uuid4()))
    )
    assert result.category == Outcome.CONFIRMED_FAILURE
    assert result.no_effect_reason == "INPUT_REJECTED" and store.committed() == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("proposal_digest", "0" * 64),
        ("task_hash", "0" * 64),
        ("state_digest", "0" * 64),
        ("proposal_ref", None),
        ("round_number", 2),
        ("expected_revision", 2),
    ],
)
def test_valid_schema_but_unbound_proposal_is_real_gateway_failure(aig_case, field, value):
    import json

    directory, state, store, prepared = aig_case
    provider = DeterministicProvider(prepared)
    body = json.loads(provider.raw)
    body["steps"][0]["arguments"][field] = value or str(uuid4())
    provider.raw = canonical_json(body)
    with consumer(directory, state, prepared, provider=provider, predecessor_stopped=True) as (
        runtime,
        executor,
        _,
    ):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert action.state.value == "Failed"
        assert (
            asyncio.run(
                direct(executor, ExecutionSpec.from_compiled(action.spec), action.effect_key)
            ).no_effect_reason
            == "INPUT_REJECTED"
        )
        assert store.committed() == ()


def test_wrong_store_identity_is_confirmed_no_effect(aig_case):
    directory, state, store, prepared = aig_case
    wrong = ProposalStore(store.path, {**store.identity, "store_id": str(uuid4())})

    def factory(_, binding, state, **kwargs):
        return ProposalExecutor(wrong, binding, state, **kwargs)

    with consumer(
        directory, state, prepared, executor_factory=factory, predecessor_stopped=True
    ) as (runtime, executor, _):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert action.state.value == "Failed"
        assert (
            asyncio.run(
                direct(executor, ExecutionSpec.from_compiled(action.spec), action.effect_key)
            ).no_effect_reason
            == "STORE_IDENTITY_MISMATCH"
        )
        assert store.committed() == ()


def test_staged_payload_is_immutable_in_normal_sql(aig_case):
    _, _, store, prepared = aig_case
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE"):
            db.execute(
                "UPDATE prepared SET proposal_json='{}' WHERE reference=?", (prepared.reference,)
            )
        with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE"):
            db.execute("DELETE FROM prepared WHERE reference=?", (prepared.reference,))


def test_distinct_authorized_actions_cannot_duplicate_one_proposal_slot(aig_case):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
        operator = principal(runtime, directory)
        _, first, _ = asyncio.run(execute_reviewed(runtime, operator))
        _, second, _ = asyncio.run(execute_reviewed(runtime, operator))
        assert first.action_id != second.action_id and first.effect_key != second.effect_key
        assert first.state.value == "Succeeded" and second.state.value == "Failed"
        assert len(store.committed()) == 1


def test_tampered_staged_content_cannot_execute_approved_digest(aig_case):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
        operator = principal(runtime, directory)
        _, action = asyncio.run(approved_action(runtime, operator))
        # Deliberate corruption of consumer-owned state, never AIG private tables.
        with store.connect() as db:
            db.execute("DROP TRIGGER immutable_prepared_UPDATE")
            db.execute(
                "UPDATE prepared SET arguments_json='{}' WHERE reference=?", (prepared.reference,)
            )
        from agentic_intent_gate.runtime import ActionCommand
        from aig_helpers import authorize

        action = authorize(runtime, action, operator)
        action = asyncio.run(
            runtime.gateway.execute(ActionCommand(action.action_id, 2, str(uuid4())), operator)
        ).action
        assert action.state.value == "Failed" and store.committed() == ()


@pytest.mark.parametrize(
    "column,value",
    [
        ("receipt", None),
        ("payload_digest", "0" * 64),
        ("row_digest", "0" * 64),
        ("round_number", 2),
    ],
)
def test_corrupted_receipt_fails_independent_verification(aig_case, column, value):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
        asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
    with store.connect() as db:
        db.execute("DROP TRIGGER immutable_effects_UPDATE")
        db.execute(f"UPDATE effects SET {column}=?", (value or str(uuid4()),))
    with pytest.raises(ValueError):
        store.committed()
