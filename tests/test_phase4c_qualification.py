"""Bounded v3 qualification runner, exercised only through an offline transport stub."""

import asyncio
import json

import pytest

from pactlens.agents.context_qualification import CAP, SixCallLedger, offline_gate, qualify
from pactlens.agents.context_v3 import V3_PROMPT, decode_request
from pactlens.agents.models import ActorContext, Turn
from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.prompts import CANDIDATE_PROMPT, make_request
from pactlens.agents.provider import ModelConfig
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json

MODEL, DIGEST = "offline-stub-not-real-model", "b" * 64


def stub(mode="example"):
    def transport(method, path, body=None):
        if path == "/api/version":
            return {"version": "OFFLINE-TEST-STUB"}
        if path == "/api/tags":
            return {"models": [{"name": MODEL, "digest": DIGEST}]}
        if path == "/api/show":
            return {"details": {}}
        assert path == "/v1/chat/completions" and method == "POST"
        turns = tuple(Turn(m["role"], m["content"]) for m in body["messages"])
        examples = decode_request(turns)["examples"]
        answer = dict(examples["submit_example"])
        if mode == "talk":
            peers = [a for a in ("a0", "a1", "a2") if a != answer["actor_id"]]
            answer["message"] = {"channel": "public", "recipients": peers, "text": "y" * 256}
        content = "{oops" if mode == "malformed" else canonical_json(answer)
        return {
            "model": MODEL,
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 120},
        }

    return OllamaProvider(
        "http://127.0.0.1:11434/v1",
        ModelConfig(MODEL, DIGEST, "ollama_loopback_openai"),
        transport=transport,
    )


def test_ledger_charges_before_dispatch_and_refuses_a_seventh_or_other_profile(tmp_path, task):
    state = begin(ArenaState(task), expected_revision=0)
    access = {"public": True, "private_peer": None}
    v3 = make_request(ActorContext("a0", "b"), state, (), 1, access, prompt_version=V3_PROMPT)
    v2 = make_request(
        ActorContext("a0", "b"), state, (), 1, access, prompt_version=CANDIDATE_PROMPT
    )
    ledger = SixCallLedger(tmp_path / "ledger.jsonl")
    try:
        with pytest.raises(ValueError, match="CAP_NO_RETRY"):
            ledger.charge(v2)
        for _ in range(CAP):
            ledger.charge(v3)
        with pytest.raises(ValueError, match="CAP_NO_RETRY"):
            ledger.charge(v3)
    finally:
        ledger.close()
    assert len((tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines()) == CAP
    with pytest.raises(FileExistsError):
        SixCallLedger(tmp_path / "ledger.jsonl")


def test_offline_gate_runs_six_steps_without_model_or_network(tmp_path, task):
    gate = asyncio.run(
        offline_gate(tmp_path / "gate", task, EpisodeConfig("ENG-gate", Condition.N3))
    )
    assert gate["fits"] and gate["requests"] == 6 and gate["input_budget_failures"] == 0
    assert max(gate["estimated_tokens"]) <= 2000


@pytest.mark.parametrize("mode", ["example", "talk", "malformed"])
def test_one_bounded_episode_records_outcomes_without_retry(tmp_path, task, mode):
    provider = stub(mode)
    summary = asyncio.run(
        qualify(tmp_path / "q", task, provider, allow_one_local_engineering_episode=True)
    )
    assert summary["offline_gate"]["fits"]
    assert summary["actual_generation_calls"] == summary["charged_attempts"] <= CAP
    assert summary["formal_episodes"] == summary["detector_predictions"] == 0
    assert summary["pure_replay_equal"] and summary["replay_new_effects"] == 0
    sent = len(summary["requests"])
    assert sent == summary["actual_generation_calls"]
    budget_failures = [
        f for f in summary["failures"] if f["diagnostic"]["code"] == "INPUT_BUDGET_EXCEEDED"
    ]
    assert sent + len(budget_failures) == 6
    if mode == "example":
        assert summary["status"] == "COMPLETE" and summary["receipts"] == 6
    elif mode == "talk":
        # Maximal speech exceeds the estimate later in the episode: recorded, never sent.
        assert budget_failures and summary["status"] == "INCOMPLETE"
        assert all(f["token_budget"]["fits"] is False for f in budget_failures)
    else:
        assert summary["actions"] == 0 and summary["status"] == "INCOMPLETE"
        assert all(m["validation"] in (None, "REJECTED") for m in summary["measurements"])
    stored = json.loads((tmp_path / "q/summary.json").read_text(encoding="utf-8"))
    assert stored["actual_generation_calls"] == summary["actual_generation_calls"]


def test_explicit_opt_in_and_fresh_directory_are_required(tmp_path, task):
    provider = stub()
    with pytest.raises(ValueError, match="EXPLICIT_FRESH_LOCAL"):
        asyncio.run(qualify(tmp_path / "never", task, provider))
    assert provider.calls == 0 and not (tmp_path / "never").exists()
    (tmp_path / "used").mkdir()
    (tmp_path / "used/existing").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="FRESH_QUALIFICATION_DIRECTORY"):
        asyncio.run(
            qualify(tmp_path / "used", task, provider, allow_one_local_engineering_episode=True)
        )
    assert provider.calls == 0
