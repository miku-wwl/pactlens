import asyncio

import pytest
from harness_helpers import message, observation, run_fake

from pactlens.aig.submission import TestConsent as Consent
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace


@pytest.mark.parametrize(
    "case", ["timeout", "invalid", "wrong_actor", "decline", "missing", "infeasible", "injection"]
)
def test_invalid_missing_and_timeout_retained_without_retry(tmp_path, task, case):
    def transform(body, request):
        if case == "timeout":
            return TimeoutError("synthetic pre-effect timeout")
        if case == "invalid":
            return "not-json"
        if case == "wrong_actor":
            body["actor_id"] = "foreign"
        elif case == "decline":
            body["decision"], body["assignments"] = "decline", None
        elif case == "missing":
            body["assignments"] = None
        elif case == "infeasible":
            body["assignments"][0]["agent_id"] = "foreign"
        elif case == "injection":
            body["execution_scope"] = "model-cannot-choose"

    run, model = asyncio.run(run_fake(tmp_path, task, transform=transform))
    assert len(model.requests) == 6 and run.executor_calls == 0
    assert run.status == ("COMPLETE" if case == "decline" else "INCOMPLETE")
    assert run.record.state.status.value == "FINALIZED"
    assert len(run.record.state.history[-1].missing_agents) == 3
    assert all(not s.committed() for s in run.stores)
    replay = replay_trace(run.trace_path)
    assert replay.status == run.status and replay.evidence.to_json() == run.evidence().to_json()


@pytest.mark.parametrize("phase,count", [("before_dispatch", 0), ("after_commit", 1)])
def test_unknown_stops_episode_after_one_attempt(tmp_path, task, phase, count):
    async def fault(at):
        if at == phase:
            raise RuntimeError("deterministic lost acknowledgment")

    run, model = asyncio.run(run_fake(tmp_path, task, checkpoint=fault))
    assert run.status == "STOPPED_UNKNOWN" and len(model.requests) == 1
    assert run.executor_calls == 1
    assert len(run.observations) == 1 and run.observations[0].action_state == "Unknown"
    assert sum(len(s.committed()) for s in run.stores) == count
    assert run.record.state.status.value == "ROUND_1" and run.record.state.proposals == ()
    assert replay_trace(run.trace_path).status == "STOPPED_UNKNOWN"
    assert sum(len(s.committed()) for s in run.stores) == count


@pytest.mark.parametrize("gate", ["approval", "authorization"])
def test_independent_consent_denials_no_effects(tmp_path, task, gate):
    run, _ = asyncio.run(
        run_fake(
            tmp_path,
            task,
            consent=Consent(True, approve=gate != "approval", authorize=gate != "authorization"),
        )
    )
    assert run.status == "INCOMPLETE" and run.executor_calls == 0
    assert sum(len(s.committed()) for s in run.stores) == 0
    assert len(run.observations) == (0 if gate == "approval" else 6)
    assert replay_trace(run.trace_path).evidence.to_json() == run.evidence().to_json()


def test_delivery_failure_not_in_any_recipient_context(tmp_path, task):
    run, model = asyncio.run(run_fake(tmp_path, task, transform=message, failed_deliveries=(1,)))
    assert run.status == "INCOMPLETE" and run.deliveries[0].status == "FAILED"
    missing_text = run.deliveries[0].text
    assert all(
        m["text"] != missing_text for r in model.requests for m in observation(r)["delivered_inbox"]
    )
    assert len(run.record.messages) == 5


def test_interruption_is_durable_and_never_resumed(tmp_path, task):
    def interrupted(body, request):
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(run_fake(tmp_path, task, transform=interrupted))
    rows = read_trace(tmp_path / "trace.jsonl")
    assert rows[-1]["payload"]["status"] == "INTERRUPTED"
    assert replay_trace(tmp_path / "trace.jsonl").status == "INTERRUPTED"


def test_arena_revision_conflict_preserves_committed_effect_without_reexecution(
    tmp_path, task, monkeypatch
):
    from pactlens.arena.models import ArenaError
    from pactlens.experiments import harness

    def conflict(*args, **kwargs):
        raise ArenaError("STALE_REVISION")

    monkeypatch.setattr(harness, "apply_committed", conflict)
    with pytest.raises(ArenaError, match="STALE_REVISION"):
        asyncio.run(run_fake(tmp_path, task))
    rows = read_trace(tmp_path / "trace.jsonl")
    assert len([r for r in rows if r["kind"] == "ACTION"]) == 1
    assert rows[-1]["payload"]["status"] == "STOPPED_CONFLICT"
    replay = replay_trace(tmp_path / "trace.jsonl")
    assert replay.status == "STOPPED_CONFLICT" and replay.record.state.proposals == ()
    assert replay.new_effects == 0


def test_actual_inference_deadline_cancels_one_call_and_continues_bounded_steps(tmp_path, task):
    from dataclasses import replace

    from harness_helpers import FakeModel

    from pactlens.experiments.conditions import EpisodeConfig
    from pactlens.experiments.harness import run_episode
    from pactlens.research.seeds import Condition

    class WaitingOnce(FakeModel):
        config = replace(FakeModel.config, timeout_seconds=1)

        async def generate(self, request):
            if not self.requests:
                self.requests.append(request)
                await asyncio.Event().wait()
            return await super().generate(request)

    model = WaitingOnce(task)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-deadline", Condition.N3),
            model,
            consent=Consent(True),
        )
    )
    assert len(model.requests) == 6 and run.status == "INCOMPLETE"
    assert run.executor_calls == 5
    failure = next(r for r in read_trace(run.trace_path) if r["kind"] == "MODEL_FAILURE")
    assert failure["payload"]["error_type"] == "TimeoutError"
    assert replay_trace(run.trace_path).status == "INCOMPLETE"


def test_cancellation_after_commit_records_unknown_and_one_receipt(tmp_path, task):
    from pactlens.aig.consumer import load_store

    async def cancelled(phase):
        if phase == "after_commit":
            raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(run_fake(tmp_path, task, checkpoint=cancelled))
    rows = read_trace(tmp_path / "trace.jsonl")
    actions = [r for r in rows if r["kind"] == "ACTION"]
    assert len(actions) == 1
    assert actions[0]["payload"]["observation"]["action_state"] == "Unknown"
    assert actions[0]["payload"]["observation"]["receipt_status"] == "VERIFIED_COMMITTED"
    assert rows[-1]["payload"]["status"] == "INTERRUPTED"
    assert rows[-1]["payload"]["executor_calls"] == 1
    stores = tuple(load_store(tmp_path / f"actor-{n}") for n in (1, 2, 3))
    assert sum(len(s.committed()) for s in stores) == 1
    assert replay_trace(tmp_path / "trace.jsonl").status == "INTERRUPTED"
    assert sum(len(s.committed()) for s in stores) == 1
