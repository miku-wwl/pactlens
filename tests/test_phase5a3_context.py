"""Versioned caps across prompts, native wire, usage, ledger, harness, L4 and freeze."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from pactlens.agents import deepseek_provider as ds
from pactlens.agents.budgets import (
    CONTEXT_PROFILE,
    V35_PROMPT,
    BudgetExceeded,
    budget_hash,
    token_preflight,
)
from pactlens.agents.models import Turn
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.inventory import Inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import View
from pactlens.research.context_profile import full_packets
from pactlens.research.detector_runner import analysis_prediction, predict, replay_prediction
from pactlens.research.study_launch import freeze_candidate, verify_launch
from pactlens.research.sufficiency_v3 import VERSION, eligibility

ROOT = Path(__file__).resolve().parents[1]


def contexts():
    return ["ENG-5a3-a" + str(i) for i in range(5)], ["ENG-5a3-d" + str(i) for i in range(45)]


def packet(view=View.R, name="ENG-5a2-block1-N3"):
    b = json.loads((ROOT / "review/phase5a2/packets" / name / "R.json").read_text(encoding="utf-8"))
    from pactlens.research.reason_detector import envelope as old

    original = CompactView(View.R, b["text"], b["manifest_json"], old())
    h, facts = original.verify()
    inv = Inventory(h["episode"], ObservationPolicy(h["policy"]), facts)
    return next(p for p in full_packets(inv) if p.view == view)


@pytest.mark.parametrize("role,size", [("agent", 3300), ("detector", 8500)])
def test_role_specific_native_budget_transition_and_legacy_denial(role, size):
    turns = (Turn("user", "x" * size),)
    with pytest.raises(BudgetExceeded):
        ds.request_budget(turns, role)
    new = ds.request_budget(turns, role, profile=CONTEXT_PROFILE)
    assert new.fits and new.limit == (4096 if role == "agent" else 8192)
    with pytest.raises(ValueError):
        token_preflight(turns, limit=8192)
    with pytest.raises(BudgetExceeded):
        ds.request_budget((Turn("user", "x" * 18000),), role, profile=CONTEXT_PROFILE)


@pytest.mark.parametrize("role,cap", [("agent", 4096), ("detector", 8192)])
def test_native_reported_usage_ceiling_and_reservation(tmp_path, role, cap):
    from test_phase4e_provider import response

    a, d = contexts()
    ledger = ds.CampaignLedger.phase5a3(tmp_path / "new.sqlite3", a, d)
    provider = ds.DeepSeekProvider(ledger, role, profile="phase5a3")
    data = response()
    data["usage"].update(input_tokens=cap, total_tokens=cap + 50)
    assert provider.decode(data, 1, {}).input_tokens == cap
    data["usage"].update(input_tokens=cap + 1, total_tokens=cap + 51)
    with pytest.raises(ds.ProviderFailure, match="ACTUAL_INPUT_BUDGET_EXCEEDED"):
        provider.decode(data, 1, {})
    b = ds.request_budget((Turn("user", "x"),), role, profile=CONTEXT_PROFILE)
    ledger.reserve(role, "first", b, context_id=(a if role == "agent" else d)[0])
    assert ledger.report()["reserved_or_charged_micro_usd"] == ds.estimated_micro_usd(cap, 256)
    with pytest.raises(ds.ProviderFailure, match="BUDGET_PROFILE"):
        ledger.reserve(
            role,
            "wrong",
            ds.request_budget((Turn("user", "x"),), role),
            context_id=(a if role == "agent" else d)[0],
        )
    with pytest.raises(ValueError, match="LEDGER_PROFILE"):
        ds.DeepSeekProvider(ledger, role, profile="phase5a2")


@pytest.mark.parametrize("view", list(View))
def test_complete_new_views_real_history_fake_scoring_and_readonly_replay(tmp_path, view):
    from test_phase5a2_qualification import Fake

    p = packet(view)
    assert p.envelope.input_limit == 8192 and p.envelope.budget(p.text).fits
    assert eligibility(p)["eligible"] and not json.loads(p.manifest_json)["omitted"]
    f = Fake()
    result = asyncio.run(
        predict(tmp_path, p, f, engineering_id="ENG-5a3-test", sufficiency_policy=VERSION)
    )
    before = result.read_bytes()
    body = replay_prediction(result)
    assert result.read_bytes() == before and f.calls == 1
    assert analysis_prediction(result)[1] == 0.23
    assert body["config"]["budget_hash"] == budget_hash(CONTEXT_PROFILE)
    assert body["replay_generation_calls"] == 0
    assert verify_compact_parity(packet(View.R), packet(View.MAE))


def test_incomplete_historical_source_is_unsent_not_imputed(tmp_path):
    from test_phase5a2_qualification import Fake

    p = packet(name="ENG-5a2-block1-C_PLUS")
    assert not eligibility(p)["eligible"]
    f = Fake()
    path = asyncio.run(
        predict(tmp_path, p, f, engineering_id="ENG-5a3-ineligible", sufficiency_policy=VERSION)
    )
    out = replay_prediction(path)
    assert f.calls == 0 and out["decision"]["host_mandated"]
    assert out["validation_diagnostic"]["code"] == "INELIGIBLE_SOURCE_PREFLIGHT"
    assert analysis_prediction(path)[1] is None


def test_envelope_honors_lower_limit_and_unqualified_counter():
    p = packet()
    smaller = replace(p.envelope, input_limit=4096)
    assert not smaller.budget(p.text).fits
    with pytest.raises(BudgetExceeded):
        smaller.budget(p.text, require=True)
    with pytest.raises(ValueError, match="UNQUALIFIED"):
        p.envelope.budget(p.text, token_counter=lambda _: 1)


def test_new_freeze_does_not_approve_budget_or_change_original_design():
    m = freeze_candidate(ROOT, profile="phase5a3")
    assert m["configuration"]["input_caps"] == {"agent": 4096, "detector": 8192}
    assert m["configuration"]["agent_prompt"] == V35_PROMPT
    assert len(m["decisions"]) == 16 and all(
        d["status"] == "PENDING" for d in m["decisions"].values()
    )
    assert m["calibration_locked"] and m["held_out_locked"]
    with pytest.raises(ValueError, match="FROZEN_APPROVALS"):
        verify_launch(m, ROOT)
    assert freeze_candidate(ROOT, profile="phase5a2")["configuration"]["input_caps"] == {
        "agent": 2000,
        "detector": 4096,
    }


def test_harness_4096_usage_all_six_and_real_aig(tmp_path):
    from harness_helpers import FakeModel

    from pactlens.agents.provider import ModelResponse
    from pactlens.aig.submission import TestConsent as Consent
    from pactlens.experiments.conditions import EpisodeConfig
    from pactlens.experiments.harness import run_episode
    from pactlens.experiments.replay import replay_trace
    from pactlens.research.fixtures import fixture_task
    from pactlens.research.seeds import Condition

    class Usage(FakeModel):
        async def generate(self, r):
            x = await super().generate(r)
            assert r.token_budget.limit == 4096
            return ModelResponse(x.text, 1, 3000, 150, "stop")

    run = asyncio.run(
        run_episode(
            tmp_path,
            fixture_task(),
            EpisodeConfig("ENG-5a3-harness", Condition.N3),
            Usage(fixture_task()),
            consent=Consent(True),
            prompt_version=V35_PROMPT,
        )
    )
    assert run.status == "COMPLETE" and len(run.observations) == 6
    assert replay_trace(run.trace_path).model_calls == 0


def test_low_spend_cap_and_fixed_slots(tmp_path, monkeypatch):
    a, d = contexts()
    monkeypatch.setenv("PACTLENS_DEEPSEEK_MAX_USD", ".0001")
    ledger = ds.CampaignLedger.phase5a3(tmp_path / "low.sqlite3", a, d)
    with pytest.raises(ds.ProviderFailure, match="SPEND_CAP"):
        ledger.reserve(
            "agent",
            "x",
            ds.request_budget((Turn("user", "x"),), "agent", profile=CONTEXT_PROFILE),
            context_id=a[0],
        )
    assert not ledger.report()["calls"]
