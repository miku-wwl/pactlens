import asyncio
import json
import os
import subprocess
import sys
from dataclasses import replace
from uuid import uuid4

import pytest
from agentic_intent_gate.runtime import ActionCommand
from aig_helpers import approved_action, authorize, execute_reviewed, principal

from pactlens.aig.consumer import consumer, observe_action
from pactlens.aig.executor import ProposalExecutor


@pytest.mark.parametrize(
    "phase,committed",
    [
        ("before_dispatch", False),
        ("before_commit", False),
        ("after_commit", True),
        ("before_ack", True),
    ],
)
def test_injected_errors_and_lost_ack_are_unknown_without_retry(aig_case, phase, committed):
    directory, state, store, prepared = aig_case

    async def fault(at):
        if at == phase:
            raise RuntimeError("Deterministic local fault")

    with consumer(directory, state, prepared, checkpoint=fault, predecessor_stopped=True) as (
        runtime,
        executor,
        _,
    ):
        _, action, command = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert action.state.value == "Unknown"
        assert len(store.committed()) == int(committed)
        again = asyncio.run(runtime.gateway.execute(command, principal(runtime, directory)))
        assert again.replayed and again.action.state.value == "Unknown" and executor.calls == 1
        observation = observe_action(
            runtime, store, action.action_id, principal(runtime, directory), synthetic_consent=True
        )
        assert observation.action_state == "Unknown"
        assert (observation.receipt_status == "VERIFIED_COMMITTED") == committed


def test_expired_gateway_deadline_claims_but_never_dispatches(aig_case):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, executor, _):
        operator = principal(runtime, directory)

        async def expired():
            _, action = await approved_action(runtime, operator)
            action = authorize(runtime, action, operator)
            return await runtime.gateway.execute(
                ActionCommand(action.action_id, 2, str(uuid4())),
                operator,
                deadline=asyncio.get_running_loop().time() - 1,
            )

        result = asyncio.run(expired())
        assert result.action.state.value == "Unknown" and executor.calls == 0
        assert store.committed() == ()


def test_executor_timeout_before_dispatch_has_no_effect(aig_case):
    directory, state, store, prepared = aig_case

    async def timeout(phase):
        if phase == "before_dispatch":
            raise TimeoutError("Deterministic pre-dispatch timeout")

    with consumer(directory, state, prepared, checkpoint=timeout, predecessor_stopped=True) as (
        runtime,
        executor,
        _,
    ):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert action.state.value == "Unknown" and executor.calls == 1
        assert store.committed() == ()


def test_gateway_cancellation_before_commit_rolls_back(aig_case):
    directory, state, store, prepared = aig_case
    reached = None

    async def barrier(phase):
        if phase == "before_commit":
            reached.set()
            await asyncio.Event().wait()

    with consumer(directory, state, prepared, checkpoint=barrier, predecessor_stopped=True) as (
        runtime,
        executor,
        _,
    ):
        operator = principal(runtime, directory)

        async def cancelled():
            nonlocal reached
            reached = asyncio.Event()
            _, action = await approved_action(runtime, operator)
            action = authorize(runtime, action, operator)
            command = ActionCommand(action.action_id, 2, str(uuid4()))
            task = asyncio.create_task(runtime.gateway.execute(command, operator))
            await reached.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            return runtime.gateway.get(action.action_id, operator)

        action = asyncio.run(cancelled())
        assert action.state.value == "Unknown" and executor.calls == 1
        assert store.committed() == ()


def test_concurrent_duplicate_command_has_one_dispatch(aig_case):
    directory, state, store, prepared = aig_case
    reached = None
    release = None

    async def barrier(phase):
        if phase == "before_dispatch":
            reached.set()
            await release.wait()

    with consumer(directory, state, prepared, checkpoint=barrier, predecessor_stopped=True) as (
        runtime,
        executor,
        _,
    ):
        operator = principal(runtime, directory)

        async def race():
            nonlocal reached, release
            reached, release = asyncio.Event(), asyncio.Event()
            _, action = await approved_action(runtime, operator)
            action = authorize(runtime, action, operator)
            command = ActionCommand(action.action_id, 2, str(uuid4()))
            first = asyncio.create_task(runtime.gateway.execute(command, operator))
            await reached.wait()
            duplicate = await runtime.gateway.execute(command, operator)
            assert duplicate.replayed and duplicate.action.state.value == "Executing"
            release.set()
            result = await first
            final = await runtime.gateway.execute(command, operator)
            return result, final

        first, duplicate = asyncio.run(race())
        assert first.action == duplicate.action and duplicate.replayed
        assert executor.calls == 1 and len(store.committed()) == 1


@pytest.mark.parametrize(
    "field", ["effect_key", "execution_scope", "target", "payload_digest", "receipt_reference"]
)
def test_real_gateway_rejects_mismatched_executor_evidence(aig_case, field):
    directory, state, store, prepared = aig_case

    class MismatchedEvidence(ProposalExecutor):
        async def execute(self, spec, key, context):
            outcome = await super().execute(spec, key, context)
            return replace(outcome, **{field: "invalid-correlation"})

    with consumer(
        directory, state, prepared, executor_factory=MismatchedEvidence, predecessor_stopped=True
    ) as (runtime, _, _):
        _, action, _ = asyncio.run(execute_reviewed(runtime, principal(runtime, directory)))
        assert action.state.value == "Unknown"
        assert len(store.committed()) == 1


# A new interpreter owns each real Gateway execution. No private AIG tables are read.
CHILD = r"""
import asyncio, json, os, sys
from pathlib import Path
from uuid import uuid4
from agentic_intent_gate.runtime import ActionCommand, AdmissionCommand, ApprovalChoice, ApprovalDecisionRequest, Intent
from pactlens.aig.consumer import consumer,load_store
from pactlens.aig.executor import ProposalExecutor
from pactlens.arena.transitions import begin
from pactlens.arena.models import ArenaState
from pactlens.research.fixtures import fixture_task
directory=Path(sys.argv[1]); mode=sys.argv[2]
store=load_store(directory)
with store.connect() as db:
 row=db.execute('SELECT arguments_json FROM prepared').fetchone()
 prepared=store.resolve(db,json.loads(row[0]))
state=prepared.state
async def checkpoint(phase):
 if phase==mode: os._exit(71)
class AfterAck(ProposalExecutor):
 async def execute(self,spec,key,context):
  result=await super().execute(spec,key,context)
  if mode=='after_ack': os._exit(72)
  return result
with consumer(directory,state,prepared,checkpoint=checkpoint,executor_factory=AfterAck,predecessor_stopped=True) as (runtime,executor,store):
 operator=runtime.verifier.verify('Bearer '+(directory/'capability').read_text('ascii'))
 async def run():
  run=await runtime.run_service.create(Intent('Record reviewed synthetic proposal'))
  run=runtime.run_service.decide(run.run_id,ApprovalDecisionRequest(ApprovalChoice.APPROVE,run.version,'synthetic_consent=true'))
  action=runtime.gateway.admit(AdmissionCommand(run.run_id,run.version,operator.subject_id,str(uuid4())),operator).action
  action=runtime.gateway.authorize(ActionCommand(action.action_id,1,str(uuid4())),operator).action
  command=ActionCommand(action.action_id,2,str(uuid4()))
  (directory/'test-command.json').write_text(json.dumps(vars(command)))
  if mode=='before_gateway': os._exit(73)
  result=await runtime.gateway.execute(command,operator)
  assert result.action.state.value=='Succeeded'
 asyncio.run(run())
"""


@pytest.mark.parametrize(
    "mode,count,expected",
    [
        ("success", 1, "Succeeded"),
        ("before_gateway", 0, "Authorized"),
        ("before_dispatch", 0, "Unknown"),
        ("before_commit", 0, "Unknown"),
        ("after_commit", 1, "Unknown"),
        ("after_ack", 1, "Unknown"),
    ],
)
def test_real_process_restart_preserves_receipts_and_never_replays(aig_case, mode, count, expected):
    directory, state, store, prepared = aig_case
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(directory), mode],
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == {"success": 0, "before_gateway": 73, "after_ack": 72}.get(
        mode, 71
    ), result.stderr
    receipts_before = tuple(e.receipt_reference for e in store.committed())
    assert len(receipts_before) == count
    command = ActionCommand(**json.loads((directory / "test-command.json").read_text()))
    with consumer(directory, state, prepared, predecessor_stopped=True) as (
        runtime,
        executor,
        reopened,
    ):
        operator = principal(runtime, directory)
        action = runtime.gateway.get(command.action_id, operator)
        assert action.state.value == expected
        assert executor.calls == 0
        if expected in ("Succeeded", "Unknown"):
            replay = asyncio.run(runtime.gateway.execute(command, operator))
            assert replay.replayed and replay.action.state.value == expected
            assert executor.calls == 0
            with pytest.raises(Exception) as caught:
                asyncio.run(
                    runtime.gateway.execute(
                        ActionCommand(action.action_id, action.version, str(uuid4())), operator
                    )
                )
            assert caught.value.code.value == "EXECUTION_ALREADY_STARTED"
        # The unclaimed Authorized case is observed only, not automatically dispatched.
        assert tuple(e.receipt_reference for e in reopened.committed()) == receipts_before
