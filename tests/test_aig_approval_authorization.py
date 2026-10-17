import asyncio
import json
from dataclasses import replace
from uuid import uuid4

import pytest
from agentic_intent_gate.runtime import (
    ActionCommand,
    AdmissionCommand,
    ApprovalChoice,
    ApprovalDecisionRequest,
    BoundCapabilityAuthorization,
    CapabilityVerifier,
    ExecutableRegistry,
    Intent,
    ToolCapability,
    open_runtime,
)
from aig_helpers import approved_action, authorize, principal

from pactlens.aig.consumer import consumer
from pactlens.aig.contract import ARGUMENT_SCHEMA, DeterministicProvider


def code(error):
    assert type(error).__name__ in ("ActionError", "RunStoreError")
    return error.code.value


@pytest.mark.parametrize("mode", ["missing", "rejected", "stale", "different_plan", "plan_rewrite"])
def test_real_approval_and_admission_denials(aig_case, mode):
    directory, state, store, prepared = aig_case
    provider = DeterministicProvider(prepared)
    with consumer(directory, state, prepared, provider=provider, predecessor_stopped=True) as (
        runtime,
        _,
        _,
    ):
        operator = principal(runtime, directory)
        run = asyncio.run(runtime.run_service.create(Intent("Record reviewed proposal")))
        if mode == "stale":
            with pytest.raises(Exception) as caught:
                runtime.run_service.decide(
                    run.run_id, ApprovalDecisionRequest(ApprovalChoice.APPROVE, run.version - 1)
                )
            assert code(caught.value) == "STALE_RUN_VERSION"
        elif mode == "plan_rewrite":
            approved = runtime.run_service.decide(
                run.run_id, ApprovalDecisionRequest(ApprovalChoice.APPROVE, run.version)
            )
            other = asyncio.run(runtime.run_service.create(Intent("Another synthetic proposal")))
            with pytest.raises(Exception) as caught:
                runtime.runs.save_validated_plan(approved.run_id, approved.version, other.plan)
            assert code(caught.value) == "INVALID_RUN_TRANSITION"
        else:
            if mode == "rejected":
                run = runtime.run_service.decide(
                    run.run_id, ApprovalDecisionRequest(ApprovalChoice.REJECT, run.version)
                )
            if mode == "different_plan":
                other_prepared = store.prepare(state, prepared.proposal)
                provider.raw = DeterministicProvider(other_prepared).raw
                other_run, _ = asyncio.run(approved_action(runtime, operator))
                assert run.plan.to_dict() != other_run.plan.to_dict()
                # A real approval on another Run cannot admit this unapproved Plan.
            with pytest.raises(Exception) as caught:
                runtime.gateway.admit(
                    AdmissionCommand(run.run_id, run.version, operator.subject_id, str(uuid4())),
                    operator,
                )
            assert code(caught.value) == "RUN_NOT_ACTION_ELIGIBLE"
        assert store.committed() == ()


@pytest.mark.parametrize(
    "mode",
    [
        "missing_authorization",
        "stale_run",
        "stale_action",
        "wrong_capability",
        "reused_authorization",
    ],
)
def test_independent_authorization_uses_real_gateway(aig_case, mode):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, _, _):
        operator = principal(runtime, directory)
        run, action = asyncio.run(approved_action(runtime, operator))
        with pytest.raises(Exception) as caught:
            if mode == "missing_authorization":
                asyncio.run(
                    runtime.gateway.execute(
                        ActionCommand(action.action_id, action.version, str(uuid4())), operator
                    )
                )
            elif mode == "stale_run":
                runtime.gateway.admit(
                    AdmissionCommand(
                        run.run_id, run.version - 1, operator.subject_id, str(uuid4())
                    ),
                    operator,
                )
            elif mode == "wrong_capability":
                runtime.verifier.verify("Bearer " + "0" * 64)
            elif mode == "stale_action":
                authorize(runtime, action, operator)
                asyncio.run(
                    runtime.gateway.execute(
                        ActionCommand(action.action_id, 1, str(uuid4())), operator
                    )
                )
            else:
                # Reuse the exact authorization command key on a distinct Pending Action.
                key = str(uuid4())
                runtime.gateway.authorize(ActionCommand(action.action_id, 1, key), operator)
                _, other = asyncio.run(approved_action(runtime, operator))
                asyncio.run(
                    runtime.gateway.execute(ActionCommand(other.action_id, 1, key), operator)
                )
        assert code(caught.value) in {
            "ACTION_NOT_EXECUTABLE",
            "STALE_ACTION_VERSION",
            "STALE_RUN_VERSION",
            "AUTHENTICATION_REQUIRED",
        }
        assert store.committed() == ()


@pytest.mark.parametrize(
    "mutation", ["tool", "target", "extra", "digest_type", "round_bool", "nested", "authority"]
)
def test_real_plan_validator_rejects_wrong_tool_target_or_arguments(aig_case, mutation):
    directory, state, store, prepared = aig_case
    provider = DeterministicProvider(prepared)
    plan = json.loads(provider.raw)
    args = plan["steps"][0]["arguments"]
    if mutation == "tool":
        plan["steps"][0]["tool_name"] = "other_tool"
    elif mutation == "target":
        plan["target"] = "real-tracker"
    elif mutation == "extra":
        args["extra"] = "unsupported"
    elif mutation == "digest_type":
        args["proposal_digest"] = 12
    elif mutation == "round_bool":
        args["round_number"] = True
    elif mutation == "nested":
        args["proposal_ref"] = {"payload": "nested"}
    else:
        args["execution_scope"] = str(uuid4())
    provider.raw = json.dumps(plan)
    with consumer(directory, state, prepared, provider=provider, predecessor_stopped=True) as (
        runtime,
        _,
        _,
    ):
        run = asyncio.run(runtime.run_service.create(Intent("Record reviewed proposal")))
        assert run.state.value == "PlanRejected" and run.error.code.value == "PLAN_VALIDATION_ERROR"
        assert runtime.gateway.list_for_run(run.run_id, principal(runtime, directory)) == ()
        assert store.committed() == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("binding_revision", "unreviewed-v2"),
        ("execution_scope", None),
        ("target", "other-target"),
        ("tool_name", "other_tool"),
    ],
)
def test_actual_gateway_denies_existing_action_under_wrong_binding(aig_case, field, value):
    directory, state, store, prepared = aig_case
    with consumer(directory, state, prepared, predecessor_stopped=True) as (runtime, executor, _):
        _, action = asyncio.run(approved_action(runtime, principal(runtime, directory)))
        binding = executor.binding
    wrong = replace(binding, **{field: value or str(uuid4())})
    token = (directory / "capability").read_text("ascii")
    verifier = CapabilityVerifier(
        token,
        subject_id=store.identity["subject_id"],
        binding=wrong,
        operations=("read", "admit", "authorize", "execute"),
    )
    # Deliberate trusted-host misconfiguration: real public composition, no core patch.
    with (
        pytest.raises(Exception) as caught,
        open_runtime(
            gate_path=directory / "gate.sqlite3",
            provider=DeterministicProvider(prepared),
            capability=ToolCapability(
                wrong, "Wrong reviewed identity negative test", ARGUMENT_SCHEMA
            ),
            registry=ExecutableRegistry(executor, binding=wrong),
            verifier=verifier,
            policy=BoundCapabilityAuthorization(verifier, policy_revision="proposal-policy-v1"),
            predecessor_stopped=True,
        ) as runtime,
    ):
        runtime.gateway.authorize(
            ActionCommand(action.action_id, 1, str(uuid4())), verifier.verify("Bearer " + token)
        )
    assert code(caught.value) in {"TOOL_NOT_BOUND", "ACTION_NOT_AUTHORIZED", "DATABASE_UNAVAILABLE"}
    assert store.committed() == ()
