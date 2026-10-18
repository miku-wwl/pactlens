"""One model-origin proposal through the existing Phase 2 public composition.

Consent choices are trusted scripted engineering controls, never model output
or authenticated human consent. AIG still owns all admission/authorization.
"""

from dataclasses import dataclass, replace
from uuid import uuid4

from agentic_intent_gate.runtime import (
    ActionCommand,
    AdmissionCommand,
    ApprovalChoice,
    ApprovalDecisionRequest,
    Intent,
)

from pactlens.aig.consumer import consumer, observe_action
from pactlens.aig.executor import no_fault
from pactlens.serialization import content_hash


@dataclass(frozen=True)
class TestConsent:
    synthetic_consent: bool = False
    approve: bool = True
    authorize: bool = True

    def __post_init__(self):
        if any(type(v) is not bool for v in (self.synthetic_consent, self.approve, self.authorize)):
            raise ValueError("EXACT_CONSENT_FLAGS")


@dataclass(frozen=True)
class Submission:
    observation: object | None
    effect_key: str | None
    executor_calls: int
    status: str


async def submit(directory, state, prepared, trace, *, consent, checkpoint=no_fault):
    if type(consent) is not TestConsent or consent.synthetic_consent is not True:
        raise ValueError("EXPLICIT_SYNTHETIC_CONSENT_REQUIRED")
    with consumer(directory, state, prepared, predecessor_stopped=True, checkpoint=checkpoint) as (
        runtime,
        executor,
        store,
    ):
        principal = runtime.verifier.verify(
            "Bearer " + (directory / "capability").read_text("ascii")
        )
        run = await runtime.run_service.create(
            Intent("Record one model-origin synthetic incident proposal")
        )
        trace.append(
            "RUN",
            {
                "run_id": run.run_id,
                "state": run.state.value,
                "plan_digest": None if run.plan is None else content_hash(run.plan.to_dict()),
                "proposal_digest": content_hash(prepared.proposal),
            },
        )
        if run.state.value != "AwaitingApproval":
            return Submission(None, None, executor.calls, "PLAN_REJECTED")
        run = runtime.run_service.decide(
            run.run_id,
            ApprovalDecisionRequest(
                ApprovalChoice.APPROVE if consent.approve else ApprovalChoice.REJECT,
                run.version,
                "synthetic_consent=true; pre-sprint engineering; model-origin proposal",
            ),
        )
        trace.append(
            "APPROVAL", {"run_id": run.run_id, "state": run.state.value, "synthetic_consent": True}
        )
        if not consent.approve:
            return Submission(None, None, executor.calls, "APPROVAL_DENIED")
        action = runtime.gateway.admit(
            AdmissionCommand(run.run_id, run.version, principal.subject_id, str(uuid4())), principal
        ).action
        trace.append(
            "ADMISSION",
            {"run_id": run.run_id, "action_id": action.action_id, "state": action.state.value},
        )
        if consent.authorize:
            action = runtime.gateway.authorize(
                ActionCommand(action.action_id, action.version, str(uuid4())), principal
            ).action
        trace.append(
            "AUTHORIZATION",
            {
                "action_id": action.action_id,
                "decision": "GRANTED" if consent.authorize else "WITHHELD",
                "synthetic_consent": True,
            },
        )
        try:
            if consent.authorize:
                action = (
                    await runtime.gateway.execute(
                        ActionCommand(action.action_id, action.version, str(uuid4())), principal
                    )
                ).action
        finally:
            # Gateway persists Unknown before propagating cancellation. Observe it
            # while the public composition is still owned; never dispatch again.
            observation = replace(
                observe_action(runtime, store, action.action_id, principal, synthetic_consent=True),
                logical_position=trace.next_position,
            )
            trace.append("ACTION", {"observation": observation, "executor_calls": executor.calls})
        return Submission(
            observation,
            action.effect_key,
            executor.calls,
            observation.action_state if consent.authorize else "AUTHORIZATION_DENIED",
        )
