"""New presentation retains six opportunities and strict parser on real AIG."""

import asyncio
from dataclasses import replace

import pytest
from harness_helpers import FakeModel

from pactlens.agents.context_v32 import V32_PROMPT
from pactlens.agents.deepseek_provider import request_budget
from pactlens.aig.submission import TestConsent as Consent
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition


@pytest.mark.parametrize(
    "mode", ["submit", "decline", "pair-array", "wrong-actor", "capacity", "public"]
)
def test_candidate_six_steps_and_no_parser_repair(tmp_path, mode):
    task = fixture_task()
    if mode == "capacity":
        task = replace(task, agents=tuple(replace(a, capacity=1) for a in task.agents))

    def transform(body, request):
        if mode == "decline":
            body.update(decision="decline", assignments=None)
        if mode == "pair-array":
            body["assignments"] = [[x["incident_id"], x["agent_id"]] for x in body["assignments"]]
        if mode == "wrong-actor":
            body["actor_id"] = "alien"
        if mode == "capacity":
            for row in body["assignments"]:
                row["agent_id"] = "a0"
        if mode == "public":
            body["message"] = {
                "channel": "public",
                "recipients": [a.agent_id for a in task.agents if a.agent_id != request.actor_id],
                "text": "Synthetic public discussion.",
            }

    model = FakeModel(task, transform)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-v32-contract", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=V32_PROMPT,
        )
    )
    assert len(model.requests) == 6
    replay = replay_trace(run.trace_path)
    assert (
        replay.evidence.to_json() == run.evidence().to_json()
        and replay.new_effects == replay.model_calls == 0
    )
    expected = 6 if mode in ("submit", "public") else 0
    assert len(run.observations) == expected
    if mode == "submit":
        assert all(request_budget(r.turns, "agent").fits for r in model.requests)
    assert len({(r.actor_id, r.round_number) for r in model.requests}) == 6
    assert len(run.contexts) == 3
