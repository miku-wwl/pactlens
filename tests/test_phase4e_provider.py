"""Offline transport contracts, persistent hard caps and unchanged strict parsing."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal

import pytest

from pactlens.agents import deepseek_provider as ds
from pactlens.agents.budgets import BudgetExceeded
from pactlens.agents.models import Turn
from pactlens.agents.provider import ModelConfig, ModelRequest
from pactlens.research.detector_runner import DetectorRequest
from pactlens.serialization import canonical_json


def response(**changes):
    return {
        "id": "safe-response-1",
        "model": "deepseek-flash",
        "status": "completed",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "output_tokens_details": {"reasoning_tokens": 0},
        },
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": '{"synthetic":true}'}],
            }
        ],
        **changes,
    }


TURNS = (Turn("user", "Synthetic JSON test only."),)


def test_explicit_profile_and_complete_budget():
    assert ModelConfig("a", "b", "deepseek_responses").endpoint_type == "deepseek_responses"
    wire = ds.payload(TURNS, ds.AGENT_SCHEMA)
    assert wire["reasoning"] == {"effort": "none"} and wire["max_output_tokens"] == 256
    assert not {"tools", "seed", "top_p", "strict"} & set(wire)
    assert ds.request_budget(TURNS, "agent").exact_tokens is None
    with pytest.raises(BudgetExceeded):
        ds.request_budget((Turn("user", "x" * 9000),), "detector")


@pytest.mark.parametrize("role,cap", [("agent", 36), ("detector", 20)])
def test_caps_atomic_and_survive_restart(tmp_path, role, cap):
    ledger = ds.CampaignLedger(tmp_path / "budget.sqlite3")
    budget = ds.request_budget(TURNS, role)

    def reserve(n):
        try:
            return ledger.reserve(role, str(n), budget)
        except ds.ProviderFailure:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(x is not None for x in pool.map(reserve, range(cap + 5))) == cap
    restarted = ds.CampaignLedger(ledger.path)
    with pytest.raises(ds.ProviderFailure, match="CALL_CAP"):
        restarted.reserve(role, "new", budget)
    assert len(restarted.report()["calls"]) == cap


def test_spend_ceiling_reserves_ambiguous_and_duplicate(tmp_path):
    ledger = ds.CampaignLedger(tmp_path / "budget.sqlite3", ceiling_usd=Decimal(".001"))
    b = ds.request_budget(TURNS, "agent")
    n = ledger.reserve("agent", "first", b)
    with pytest.raises(ds.ProviderFailure):
        ledger.reserve("agent", "first", b)
    ledger.finish(n, {"status": "FAILED_OR_UNKNOWN", "uncertain": True})
    with pytest.raises(ds.ProviderFailure, match="SPEND_CAP"):
        ledger.reserve("agent", "second", b)
    assert ledger.report()["reserved_or_charged_micro_usd"] > 0
    with pytest.raises(ValueError, match="LEDGER_CONFIGURATION_CHANGED"):
        ds.CampaignLedger(ledger.path)


@pytest.mark.parametrize(
    "data,code",
    [
        (response(id=None), "MISSING_PROVIDER_REQUEST_ID"),
        (response(model="changed-model"), "MODEL_IDENTITY_CHANGED"),
        (response(usage=None), "MISSING_OR_INVALID_USAGE"),
        (response(status="incomplete"), "OUTPUT_SCHEMA_BUDGET_INFEASIBLE"),
        (response(status="failed"), "INCOMPLETE_OR_FAILED_GENERATION"),
        (response(output=[]), "EMPTY_OR_MULTIPART_OUTPUT"),
        (
            response(
                output=[{"type": "message", "role": "assistant", "content": [{"type": "refusal"}]}]
            ),
            "MODEL_REFUSAL",
        ),
        (response(output=[{"type": "reasoning"}]), "UNEXPECTED_REASONING_OUTPUT"),
        (response(output=[{"type": "function_call"}]), "UNEXPECTED_OUTPUT_TYPE"),
        (
            response(
                output=[
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "not JSON"}],
                    }
                ]
            ),
            "INVALID_MODEL_JSON",
        ),
    ],
)
def test_typed_responses(tmp_path, data, code):
    provider = ds.DeepSeekProvider(ds.CampaignLedger(tmp_path / "b.sqlite3"), "agent")
    with pytest.raises(ds.ProviderFailure, match=code):
        provider.decode(data, 1, {})


@pytest.mark.parametrize(
    "change,code",
    [
        ({"input_tokens": 2001, "total_tokens": 2051}, "ACTUAL_INPUT_BUDGET_EXCEEDED"),
        ({"output_tokens": 257, "total_tokens": 357}, "OUTPUT_SCHEMA_BUDGET_INFEASIBLE"),
        ({"total_tokens": 3}, "USAGE_INCONSISTENT"),
        ({"input_tokens": True}, "MISSING_OR_INVALID_USAGE"),
        ({"output_tokens_details": {"reasoning_tokens": 1}}, "UNEXPECTED_REASONING_TOKENS"),
    ],
)
def test_usage_is_not_a_preflight_tokenizer(tmp_path, change, code):
    provider = ds.DeepSeekProvider(ds.CampaignLedger(tmp_path / "b.sqlite3"), "agent")
    data = response()
    data["usage"].update(change)
    with pytest.raises(ds.ProviderFailure, match=code):
        provider.decode(data, 1, {})


def test_transport_failure_preserved_no_second_request(tmp_path, monkeypatch):
    ledger = ds.CampaignLedger(tmp_path / "b.sqlite3")
    provider = ds.DeepSeekProvider(ledger, "agent")
    calls = []

    def fail(*args):
        calls.append(1)
        raise ds.ProviderFailure("READ_TIMEOUT", uncertain=True)

    monkeypatch.setattr(ds, "_http", fail)
    r = replace(
        ModelRequest("a0", 1, TURNS, 0),
        prompt_version="pactlens-agent-v3.2-deepseek-candidate",
        protocol_version="pactlens-decision-v2-candidate",
        prompt_hash="0" * 64,
        protocol_hash="1" * 64,
        token_budget=ds.request_budget(TURNS, "agent"),
    )
    with pytest.raises(ds.ProviderFailure, match="READ_TIMEOUT"):
        asyncio.run(provider.generate(r))
    with pytest.raises(ds.ProviderFailure, match="PROFILE_STOPPED"):
        asyncio.run(provider.generate(r))
    assert len(calls) == 1 and ledger.report()["calls"][0]["uncertain"]


def test_success_usage_and_alias_change_persistence(tmp_path, monkeypatch):
    ledger = ds.CampaignLedger(tmp_path / "b.sqlite3")
    provider = ds.DeepSeekProvider(ledger, "detector")
    r = DetectorRequest(TURNS, 0, "0" * 64, "1" * 64)
    monkeypatch.setattr(ds, "_http", lambda *a: response())
    result = asyncio.run(provider.generate(r))
    assert result.output_tokens == 50 and result.finish_reason == "stop"
    assert ledger.report()["calls"][0]["estimated_actual_micro_usd"] == 90
    other = ds.DeepSeekProvider(ds.CampaignLedger(ledger.path), "detector")
    with pytest.raises(ds.ProviderFailure, match="MODEL_IDENTITY_CHANGED"):
        other.decode(response(model=ds.PRICING["served_model_documented"]), 1, {})
    assert "Authorization" not in canonical_json(ledger.report())


def test_closed_schema_and_nullability():
    assert ds.AGENT_SCHEMA["additionalProperties"] is False
    properties = ds.AGENT_SCHEMA["properties"]
    assert properties["assignments"]["anyOf"][1]["items"]["additionalProperties"] is False
    assert properties["message"]["anyOf"][1]["additionalProperties"] is False
    assert set(ds.AGENT_SCHEMA["required"]) == set(properties)


def test_pre_dispatch_budget_and_spend_exhaustion_stop_profile(tmp_path, monkeypatch):
    def forbidden_http(*args):
        raise AssertionError("NO_DISPATCH_ALLOWED")

    monkeypatch.setattr(ds, "_http", forbidden_http)
    for name, turns, ceiling in [
        ("input", (Turn("user", "x" * 9000),), Decimal(5)),
        ("spend", TURNS, Decimal(".000001")),
    ]:
        ledger = ds.CampaignLedger(tmp_path / (name + ".sqlite3"), ceiling_usd=ceiling)
        provider = ds.DeepSeekProvider(ledger, "agent")
        r = ModelRequest(
            "a0",
            1,
            turns,
            0,
            prompt_version="pactlens-agent-v3.2-deepseek-candidate",
            protocol_version="pactlens-decision-v2-candidate",
            prompt_hash="0" * 64,
            protocol_hash="1" * 64,
            token_budget=ds.request_budget(TURNS, "agent"),
        )
        with pytest.raises((BudgetExceeded, ds.ProviderFailure)):
            asyncio.run(provider.generate(r))
        assert provider.blocked and ledger.report()["agent_requests"] == 0
        with pytest.raises(ds.ProviderFailure, match="PROFILE_STOPPED"):
            asyncio.run(provider.generate(r))
