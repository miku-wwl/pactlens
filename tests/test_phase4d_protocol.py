"""v3.1 strict protocol regressions and six-request offline validation."""

import asyncio
import json

import pytest
from context_helpers import largest_generated_task, speaker
from harness_helpers import FakeModel

from pactlens.agents.context_v31 import SYSTEM_V31, V31_PROMPT
from pactlens.agents.models import ActorContext
from pactlens.agents.prompts import make_request
from pactlens.agents.protocol_diagnostics import CANDIDATE_PROTOCOL, parse_versioned
from pactlens.aig.submission import TestConsent as Consent
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.traces import read_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json


@pytest.mark.parametrize("condition", list(Condition))
@pytest.mark.parametrize("mode", ["none", "public", "private", "decline", "invalid", "long"])
def test_six_request_matrix(tmp_path, condition, mode):
    def transform(body, request):
        if mode in ("public", "private", "long"):
            speaker("all" if mode != "private" else "pair", 256 if mode == "long" else 24)(
                body, request
            )
        if mode == "decline":
            body.update(decision="decline", assignments=None)
        if mode == "invalid" and request.round_number == 1:
            body.update(assignments=None)

    task = largest_generated_task() if mode == "long" else fixture_task()
    model = FakeModel(task, transform)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-phase4d-offline", condition),
            model,
            consent=Consent(True),
            prompt_version=V31_PROMPT,
        )
    )
    rows = read_trace(run.trace_path)
    failures = [r for r in rows if r["kind"] == "MODEL_FAILURE"]
    if mode == "long":
        assert failures and len(model.requests) < 6
        assert all(r["payload"]["diagnostic"]["code"] == "INPUT_BUDGET_EXCEEDED" for r in failures)
    else:
        assert len(model.requests) == 6
        assert len({(r.actor_id, r.round_number) for r in model.requests}) == 6
        assert len(failures) == (3 if mode == "invalid" else 0)
    for request in model.requests:
        assert request.token_budget.fits and request.token_budget.limit == 2000
        body = json.loads(request.turns[-1].content)
        assert body["now"]["task_hash"] == task.task_hash
        assert body["now"]["actor_id"] == request.actor_id
        assert task.task_hash not in request.turns[0].content
        assert len(body["own_history"]) == request.round_number - 1
    assert all(o.action_state != "Unknown" for o in run.observations)


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate-round",
        "duplicate-hash",
        "submit-null",
        "wrong-actor",
        "wrong-task",
        "wrong-round",
        "partial",
        "message-self",
        "end-false",
        "extra-authority",
        "pair-arrays",
    ],
)
def test_failures_remain_strict(damage):
    task = fixture_task()
    state = begin(ArenaState(task), expected_revision=0)
    body = {
        "actor_id": "a0",
        "round_number": 1,
        "task_hash": task.task_hash,
        "decision": "decline",
        "assignments": None,
        "message": None,
        "end_step": True,
    }
    if damage.startswith("duplicate"):
        key = "round_number" if damage.endswith("round") else "task_hash"
        raw = canonical_json(body)[:-1] + "," + json.dumps(key) + ":" + json.dumps(body[key]) + "}"
    else:
        if damage == "submit-null":
            body["decision"] = "submit"
        if damage == "wrong-actor":
            body["actor_id"] = "a1"
        if damage == "wrong-task":
            body["task_hash"] = "0" * 64
        if damage == "wrong-round":
            body["round_number"] = 2
        if damage == "partial":
            body.update(decision="submit", assignments=[])
        if damage == "pair-arrays":
            body.update(decision="submit", assignments=[["i0", "a0"], ["i1", "a1"], ["i2", "a2"]])
        if damage == "message-self":
            body["message"] = {"channel": "private", "recipients": ["a0"], "text": "agree"}
        if damage == "end-false":
            body["end_step"] = False
        if damage == "extra-authority":
            body["approval"] = True
        raw = canonical_json(body)
    with pytest.raises(ValueError):
        parse_versioned(raw, state=state, actor_id="a0", protocol_version=CANDIDATE_PROTOCOL)


def test_one_identity_source_and_schema_demonstration():
    task = fixture_task()
    r = make_request(
        ActorContext("a0", "private-a0"),
        begin(ArenaState(task), expected_revision=0),
        (),
        0,
        {"public": True, "private_peer": None},
        prompt_version=V31_PROMPT,
    )
    assert r.turns[0].content.startswith(SYSTEM_V31)
    assert "private-a0" in r.turns[0].content and "private-a1" not in canonical_json(r)
    assert "copy" not in SYSTEM_V31.lower()
    assert SYSTEM_V31.count('"actor_id":') == 1
