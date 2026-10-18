import json
from dataclasses import FrozenInstanceError, replace

import pytest
from harness_helpers import FakeModel

from pactlens.agents.models import ActorContext, Turn, parse_decision
from pactlens.agents.ollama_provider import OllamaProvider, local_address
from pactlens.agents.prompts import make_request
from pactlens.agents.provider import ModelConfig
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.serialization import canonical_json


@pytest.fixture
def valid(task):
    import asyncio

    state = begin(ArenaState(task), expected_revision=0)
    request = make_request(ActorContext("a0", "private"), state, (), 4, {})
    raw = asyncio.run(FakeModel(task).generate(request)).text
    return state, request, json.loads(raw)


def test_valid_protocol_and_closed_context(valid):
    state, request, body = valid
    decision = parse_decision(canonical_json(body), state=state, actor_id="a0")
    assert decision.proposal.agent_id == "a0" and decision.message is None
    with pytest.raises(FrozenInstanceError):
        request.actor_id = "a1"
    with pytest.raises(ValueError):
        ActorContext("a0", "private", [Turn("user", "mutable")])


@pytest.mark.parametrize(
    "mutation",
    [
        "actor",
        "round",
        "task",
        "authority",
        "scope",
        "tool",
        "boolean",
        "float",
        "infeasible",
        "missing",
        "end",
        "nested",
    ],
)
def test_invalid_or_injection_protocol(valid, mutation):
    state, _, body = valid
    if mutation in ("authority", "scope", "tool"):
        body[mutation] = "untrusted"
    elif mutation == "actor":
        body["actor_id"] = "a1"
    elif mutation == "round":
        body["round_number"] = 2
    elif mutation == "task":
        body["task_hash"] = "0" * 64
    elif mutation == "boolean":
        body["round_number"] = True
    elif mutation == "float":
        body["round_number"] = 1.0
    elif mutation == "infeasible":
        body["assignments"][0]["agent_id"] = "foreign"
    elif mutation == "missing":
        body.pop("message")
    elif mutation == "nested":
        body["assignments"][0]["scope"] = "bad"
    else:
        body["end_step"] = False
    with pytest.raises(ValueError):
        parse_decision(
            canonical_json(body) if mutation != "float" else json.dumps(body),
            state=state,
            actor_id="a0",
        )


@pytest.mark.parametrize(
    "raw", ["{}", "[]", "bad", "x" * 4097, '{"actor_id":"a0","actor_id":"a1"}', '"\\ud800"']
)
def test_malformed_and_duplicate_response(valid, raw):
    with pytest.raises((ValueError, UnicodeError)):
        parse_decision(raw, state=valid[0], actor_id="a0")


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:11434/v1",
        "http://localhost:11434/v1",
        "http://example.com/v1",
        "http://127.0.0.1/v1",
        "http://127.0.0.1:11434/v1?key=x",
        "http://u:p@127.0.0.1:11434/v1",
        "http://192.168.1.1:11434/v1",
        "http://127.0.0.1:11434/api",
    ],
)
def test_local_transport_configuration_rejects_remote_or_ambiguous(url):
    with pytest.raises(ValueError):
        local_address(url)


def test_provider_contract_with_offline_transport(valid):
    import asyncio

    requests = []
    digest = "a" * 64

    def transport(method, path, body=None):
        requests.append((method, path, body))
        return {
            "/api/version": {"version": "test-version"},
            "/api/tags": {"models": [{"name": "test:local", "digest": digest}]},
            "/api/show": {"details": {"family": "local"}},
            "/v1/chat/completions": {
                "model": "test:local",
                "choices": [
                    {"message": {"content": canonical_json(valid[2])}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 99, "completion_tokens": 120},
            },
        }[path]

    provider = OllamaProvider(
        "http://127.0.0.1:11434/v1",
        ModelConfig("test:local", digest, "ollama_loopback_openai"),
        transport=transport,
    )
    result = asyncio.run(provider.generate(valid[1]))
    assert result.input_tokens == 99 and provider.calls == 1
    sent = requests[-1][2]
    assert sent["seed"] == 4 and sent["max_tokens"] == 256 and sent["stream"] is False
    assert "Authorization" not in str(requests)


@pytest.mark.parametrize(
    "case", ["cloud_name", "remote_metadata", "changed_revision", "missing_model"]
)
def test_local_provider_fail_closed_model_identity(case):
    digest = "a" * 64

    def transport(method, path, body=None):
        if path == "/api/version":
            return {"version": "test"}
        if path == "/api/tags":
            return {
                "models": []
                if case == "missing_model"
                else [{"name": "test:local", "digest": digest}]
            }
        return {"remote_model": "x"} if case == "remote_metadata" else {}

    with pytest.raises(ValueError):
        provider = OllamaProvider(
            "http://127.0.0.1:11434/v1",
            ModelConfig(
                "test:cloud" if case == "cloud_name" else "test:local",
                "b" * 64 if case == "changed_revision" else digest,
                "ollama_loopback_openai",
            ),
            transport=transport,
        )
        provider.readiness()


def test_no_inference_by_default_or_retry_config(monkeypatch):
    monkeypatch.delenv("PACTLENS_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("PACTLENS_OLLAMA_MODEL", raising=False)
    with pytest.raises(ValueError, match="SET_PACTLENS"):
        OllamaProvider.from_environment()
    with pytest.raises(ValueError, match="NO_RETRIES"):
        replace(ModelConfig("x", "y"), max_attempts=2)


def test_unsigned_seed_preserved_with_explicit_transport_mapping(valid):
    state = valid[0]
    request = make_request(ActorContext("a0", "private"), state, (), (1 << 64) - 1, {})
    assert request.derived_seed == (1 << 64) - 1
    assert request.seed == (1 << 63) - 1
    assert request.seed_mapping == "UNSIGNED64_LOW63_V1"
    with pytest.raises(ValueError, match="SEED_MAPPING"):
        replace(request, seed=0)
