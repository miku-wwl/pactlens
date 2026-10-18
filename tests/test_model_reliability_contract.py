import asyncio
import json

import pytest

from pactlens.agents.models import ActorContext
from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.prompts import CANDIDATE_PROMPT, LEGACY_PROMPT, make_request
from pactlens.agents.provider import ModelConfig
from pactlens.agents.reliability import GenerationLedger, compare_local
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.serialization import canonical_json


def fake_local_provider(*, malformed=False):
    model, digest = "offline-stub-not-real-model", "a" * 64

    def transport(method, path, body=None):
        if path == "/api/version":
            return {"version": "OFFLINE-TEST-STUB"}
        if path == "/api/tags":
            return {"models": [{"name": model, "digest": digest}]}
        if path == "/api/show":
            return {"details": {}}
        assert path == "/v1/chat/completions" and method == "POST"
        obs = json.loads(body["messages"][-1]["content"])
        response = {
            "actor_id": obs["actor_id"],
            "round_number": obs["round_number"],
            "task_hash": obs["task_hash"],
            "decision": "decline",
            "assignments": None,
            "message": None,
            "end_step": True,
        }
        return {
            "model": model,
            "choices": [
                {
                    "message": {"content": "{bad" if malformed else canonical_json(response)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 90},
        }

    return OllamaProvider(
        "http://127.0.0.1:11434/v1",
        ModelConfig(model, digest, "ollama_loopback_openai"),
        transport=transport,
    )


def test_generation_ledger_enforces_twelve_and_six_per_profile_without_reset(tmp_path, task):
    state = begin(ArenaState(task), expected_revision=0)
    ledger = GenerationLedger(tmp_path / "calls.jsonl")
    try:
        for prompt in (LEGACY_PROMPT, CANDIDATE_PROMPT):
            request = make_request(
                ActorContext("a0", "test"),
                state,
                (),
                1,
                {"public": True, "private_peer": None},
                prompt_version=prompt,
            )
            for _ in range(6):
                ledger.charge(request)
            with pytest.raises(ValueError, match="CAP_NO_RETRY"):
                ledger.charge(request)
        assert ledger.total == 12
    finally:
        ledger.close()
    assert len((tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()) == 12
    with pytest.raises(FileExistsError):
        GenerationLedger(tmp_path / "calls.jsonl")


@pytest.mark.parametrize("malformed", [False, True])
def test_offline_transport_comparison_is_bounded_fresh_and_retains_failures(
    tmp_path, task, malformed
):
    provider = fake_local_provider(malformed=malformed)
    summary = asyncio.run(
        compare_local(
            tmp_path / "comparison", task, provider, allow_two_local_engineering_episodes=True
        )
    )
    assert summary["actual_generation_calls"] == summary["charged_attempts"] <= 12
    assert summary["formal_episodes"] == summary["detector_predictions"] == 0
    assert summary["comparison_winner"] is None
    assert len(summary["episodes"]) == 2
    a, b = summary["episodes"]
    assert a["actual_generation_calls"] == 6
    assert b["actual_generation_calls"] <= 6
    assert a["public_id"] != b["public_id"]
    assert a["actions"] == b["actions"] == a["receipts"] == b["receipts"] == 0
    assert all(
        e["pure_replay_equal"] and e["replay_new_effects"] == e["replay_model_calls"] == 0
        for e in summary["episodes"]
    )
    for e in summary["episodes"]:
        if malformed:
            assert e["invalid_responses"] == e["actual_generation_calls"]
        else:
            assert e["valid_declines"] == e["valid_outputs"]
        assert all(
            x["latency_us"] is not None for x in e["measurements"] if x["response_hash"] is not None
        )
    # Both trace configurations have the same public task, group and seed schedule.
    from pactlens.experiments.traces import read_trace

    first = read_trace(tmp_path / "comparison/legacy-v1/trace.jsonl")[0]["payload"]
    second = read_trace(tmp_path / "comparison/candidate-v2/trace.jsonl")[0]["payload"]
    assert first["initial_state"] == second["initial_state"] and first["seeds"] == second["seeds"]
    with pytest.raises(ValueError, match="FRESH_LOCAL"):
        asyncio.run(
            compare_local(
                tmp_path / "comparison", task, provider, allow_two_local_engineering_episodes=True
            )
        )


def test_opt_in_required_and_no_implicit_model_selection(tmp_path, task):
    provider = fake_local_provider()
    with pytest.raises(ValueError, match="EXPLICIT_FRESH_LOCAL"):
        asyncio.run(compare_local(tmp_path / "never-created", task, provider))
    assert provider.calls == 0 and not (tmp_path / "never-created").exists()
