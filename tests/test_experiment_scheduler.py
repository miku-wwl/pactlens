import asyncio
from dataclasses import replace

import pytest
from harness_helpers import FakeModel, message, observation, run_fake

from pactlens.aig.submission import TestConsent as Consent
from pactlens.experiments.conditions import EpisodeConfig, engineering_seed
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.integration.arena_bridge import reconstruct
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    task = fixture_task()
    return asyncio.run(run_fake(tmp_path_factory.mktemp("completed"), task, transform=message))


def test_three_independent_contexts_and_delivered_only(completed):
    run, model = completed
    assert len(run.contexts) == 3 and len(model.requests) == 6
    assert len({id(c) for c in run.contexts}) == 3
    for actor in ("a0", "a1", "a2"):
        requests = [r for r in model.requests if r.actor_id == actor]
        assert len(requests) == 2
        assert sum(t.role == "assistant" for t in requests[0].turns) == 0
        assert sum(t.role == "assistant" for t in requests[1].turns) == 1
        assert all(
            c.actor_id == actor for c in run.contexts if c.history[0] == requests[0].turns[-1]
        )
        inbox = observation(requests[1])["delivered_inbox"]
        assert all(actor in m["recipients"] for m in inbox)
        assert all(m["sender"] != actor for m in inbox)


def test_deterministic_order_current_committed_snapshot_and_real_gateway(completed):
    run, model = completed
    order = EpisodeConfig("ENG-unit-v1", Condition.N3).roles(run.record.state.task)
    assert [r.actor_id for r in model.requests] == list(order) * 2
    assert [observation(r)["revision"] for r in model.requests] == [1, 2, 3, 5, 6, 7]
    assert run.status == "COMPLETE" and run.record.state.revision == 9
    assert run.executor_calls == 6 and len(run.observations) == 6
    assert {o.action_state for o in run.observations} == {"Succeeded"}
    assert [len(s.committed()) for s in run.stores] == [2, 2, 2]
    assert reconstruct(run.record.state.task, run.stores, finalize=True) == run.record.state
    rows = read_trace(run.trace_path)
    assert len([r for r in rows if r["kind"] == "APPROVAL"]) == 6
    assert len([r for r in rows if r["kind"] == "AUTHORIZATION"]) == 6
    for store in run.stores:
        assert store.identity["binding"]["binding_revision"] == "proposal-v1"


def test_interleaving_is_captured_not_grouped_chronology(completed):
    run, _ = completed
    data = run.evidence().as_mapping()
    actions = data["aig_execution"]["records"]
    deliveries = data["harness"]["deliveries"]
    assert (
        deliveries[0]["delivery_position"]
        < actions[0]["logical_position"]
        < deliveries[1]["attempt_position"]
    )
    assert data["event_ordering"]["status"] == "RECORDED_CROSS_STREAM"
    assert data["event_ordering"]["array_order"] == "SOURCE_LOCAL_NOT_GLOBAL_TIME"


def test_exact_pure_replay_no_provider_or_gateway_calls(completed, monkeypatch):
    run, model = completed
    from pactlens.aig import consumer

    def forbidden(*args, **kwargs):
        pytest.fail("Replay invoked execution or inference")

    monkeypatch.setattr(model, "generate", forbidden)
    monkeypatch.setattr(consumer, "consumer", forbidden)
    before = tuple(tuple(s.committed()) for s in run.stores)
    replay = replay_trace(run.trace_path)
    assert replay.record.state == run.record.state
    assert replay.evidence.to_json() == run.evidence().to_json()
    assert replay.model_calls == replay.new_effects == 0
    assert tuple(tuple(s.committed()) for s in run.stores) == before
    assert replay_trace(run.trace_path).evidence == replay.evidence


def test_fresh_directory_and_explicit_consent_only(tmp_path, task):
    config = EpisodeConfig("ENG-test", Condition.N3)
    with pytest.raises(ValueError, match="CONSENT"):
        asyncio.run(run_episode(tmp_path, task, config, FakeModel(task)))
    (tmp_path / "existing").write_text("preserve")
    with pytest.raises(ValueError, match="FRESH_EPISODE"):
        asyncio.run(run_episode(tmp_path, task, config, FakeModel(task), consent=Consent(True)))


def test_engineering_namespace_cannot_consume_official_slots(task):
    for group in ("P001", "K001", "T001", "ENG-../hidden"):
        with pytest.raises(ValueError):
            engineering_seed(group, "task")
    plus = EpisodeConfig("ENG-unit-v1", Condition.C_PLUS)
    minus = replace(plus, condition=Condition.C_MINUS)
    assert plus.roles(task) == minus.roles(task)
    assert [plus.seed(a.agent_id, r, task) for a in task.agents for r in (1, 2)] == [
        minus.seed(a.agent_id, r, task) for a in task.agents for r in (1, 2)
    ]
