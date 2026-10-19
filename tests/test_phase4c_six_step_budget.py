"""Phase 4C six-step v3 request budgeting with fake transcripts and real AIG."""

import asyncio
import json

import pytest
from context_helpers import largest_generated_task, speaker
from harness_helpers import FakeModel

from pactlens.agents.context_attribution import attribute_request
from pactlens.agents.context_v3 import V3_PROMPT
from pactlens.aig.submission import TestConsent as Consent
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.traces import read_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition

TASKS = {"fixture": fixture_task, "largest-generated-5": largest_generated_task}


def episode(path, task, condition, transform=None):
    model = FakeModel(task, transform)
    result = asyncio.run(
        run_episode(
            path,
            task,
            EpisodeConfig("ENG-six-step-v3", condition),
            model,
            consent=Consent(True),
            prompt_version=V3_PROMPT,
        )
    )
    return result, model


@pytest.mark.parametrize("condition", list(Condition))
@pytest.mark.parametrize("name", sorted(TASKS))
def test_all_six_decisions_fit_without_speech_in_every_condition(tmp_path, name, condition):
    task = TASKS[name]()
    result, model = episode(tmp_path, task, condition)
    assert result.status == "COMPLETE" and len(model.requests) == 6
    expected_actions = 3 if condition == Condition.N2 else 6
    assert len(result.observations) == result.executor_calls == expected_actions
    for request in model.requests:
        budget = request.token_budget
        assert request.prompt_version == V3_PROMPT and len(request.turns) == 2
        assert budget.limit == 2000 and budget.fits and budget.exact_tokens is None
        report = attribute_request(request.turns)
        assert report["utf8_bytes"] == budget.utf8_bytes
        assert report["estimated_tokens"] == budget.estimated_tokens
        assert report["public_task_bytes"] > 0
        assert (report["history_bytes"] > 0) == (request.round_number == 2)


def test_request_accounting_is_recorded_for_every_attempted_step(tmp_path):
    task = fixture_task()
    result, _ = episode(tmp_path, task, Condition.C_PLUS, speaker("all", 40))
    rows = read_trace(result.trace_path)
    recorded = [r["payload"]["request"] for r in rows if r["kind"] == "MODEL_REQUEST"]
    assert len(recorded) == 6
    for item in recorded:
        assert item["prompt_version"] == V3_PROMPT
        assert item["protocol_version"] == "pactlens-decision-v2-candidate"
        assert set(item["token_budget"]) == {
            "limit",
            "utf8_bytes",
            "estimated_tokens",
            "exact_tokens",
            "method",
            "fits",
        }
        assert item["token_budget"]["method"] == "UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE"


@pytest.mark.parametrize("char", ["x", "中"])
def test_maximal_speech_on_largest_task_is_an_explicit_overflow(tmp_path, char):
    task = largest_generated_task()
    result, model = episode(tmp_path, task, Condition.C_PLUS, speaker("all", 256, char))
    failures = [r["payload"] for r in read_trace(result.trace_path) if r["kind"] == "MODEL_FAILURE"]
    assert failures and {f["diagnostic"]["code"] for f in failures} == {"INPUT_BUDGET_EXCEEDED"}
    assert all(not f["token_budget"]["fits"] for f in failures)
    assert result.status == "INCOMPLETE" and len(model.requests) + len(failures) == 6
    # No candidate request is ever sent above the preflight estimate.
    assert all(r.token_budget.estimated_tokens <= 2000 for r in model.requests)


def test_round_one_never_carries_history_and_round_two_has_one_entry(tmp_path):
    task = fixture_task()
    _, model = episode(tmp_path, task, Condition.N3, speaker("r1", 60))
    for request in model.requests:
        report = attribute_request(request.turns)
        entries = json.loads(request.turns[-1].content)["own_history"]
        # History is one re-encoded entry per earlier round, never resent turns.
        assert len(entries) == request.round_number - 1
        assert (report["history_bytes"] == 0) == (request.round_number == 1)
        assert report["repetition"]["public_task_copies"] == 1 and report["turn_count"] == 2
