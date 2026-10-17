"""Synthetic consent helpers used only by offline engineering tests."""

from uuid import uuid4

from agentic_intent_gate.runtime import (
    ActionCommand,
    AdmissionCommand,
    ApprovalChoice,
    ApprovalDecisionRequest,
    Intent,
)


def principal(runtime, directory):
    return runtime.verifier.verify("Bearer " + (directory / "capability").read_text("ascii"))


async def approved_action(runtime, operator):
    run = await runtime.run_service.create(Intent("Record the reviewed synthetic proposal"))
    assert run.state.value == "AwaitingApproval"
    run = runtime.run_service.decide(
        run.run_id,
        ApprovalDecisionRequest(
            ApprovalChoice.APPROVE, run.version, "synthetic_consent=true; engineering test"
        ),
    )
    action = runtime.gateway.admit(
        AdmissionCommand(run.run_id, run.version, operator.subject_id, str(uuid4())),
        operator,
    ).action
    return run, action


def authorize(runtime, action, operator):
    return runtime.gateway.authorize(
        ActionCommand(action.action_id, action.version, str(uuid4())),
        operator,
    ).action


async def execute_reviewed(runtime, operator):
    run, action = await approved_action(runtime, operator)
    action = authorize(runtime, action, operator)
    command = ActionCommand(action.action_id, action.version, str(uuid4()))
    result = await runtime.gateway.execute(command, operator)
    return run, result.action, command
