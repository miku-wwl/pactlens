"""Engineering candidates never replace historical policies or formal approvals."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from pactlens.agents.deepseek_provider import (
    CampaignLedger,
    ProviderFailure,
    payload,
    request_budget,
)
from pactlens.agents.models import Turn
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.views import View
from pactlens.research.abstention import decision as old_decision
from pactlens.research.detector_runner import analysis_prediction, predict, replay_prediction
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.native_detector import envelope
from pactlens.research.study_launch import DECISIONS_5A1, freeze_candidate, verify_launch
from pactlens.research.sufficiency_v3 import VERSION, eligibility

ROOT = Path(__file__).resolve().parents[1]


def packet(case, view):
    body = json.loads(
        (ROOT / "review/phase5a1/packets" / f"{case}-{view.value}.json").read_text(encoding="utf-8")
    )
    return CompactView(view, body["text"], body["manifest_json"], envelope())


class Fake:
    config = ModelConfig("fake-detector", "phase5a1", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, mode):
        self.mode, self.calls = mode, 0

    async def generate(self, r):
        self.calls += 1
        body = {
            "risk_score": 0.2,
            "confidence": 0.6,
            "evidence_ids": [r.citation_keys[0]],
            "rationale_short": "Engineering contract.",
            "adequacy": "ADEQUATE",
        }
        if self.mode == "insufficient":
            body["adequacy"] = "INSUFFICIENT_EVIDENCE"
        if self.mode == "citation":
            body["evidence_ids"] = ["f999"]
        if self.mode == "score":
            body["risk_score"] = True
        if self.mode == "rationale":
            body["rationale_short"] = "x" * 81
        return ModelResponse(
            canonical_json(body), 1, 100, 80, "length" if self.mode == "length" else "stop"
        )


@pytest.mark.parametrize("view", list(View))
@pytest.mark.parametrize(
    "mode", ["valid", "insufficient", "citation", "score", "rationale", "length"]
)
def test_one_shot_native_and_authoritative_policy(tmp_path, view, mode):
    p = packet("known-absence", view)
    fake = Fake(mode)
    path = asyncio.run(
        predict(tmp_path, p, fake, engineering_id="ENG-5a1-test", sufficiency_policy=VERSION)
    )
    before = path.read_bytes()
    out = replay_prediction(path)
    assert path.read_bytes() == before and fake.calls == 1
    assert out["replay_generation_calls"] == out["replay_new_effects"] == 0
    assert out["decision"]["host_mandated"] is False
    if mode == "valid":
        assert out["decision"]["state"] == "SCORED" and analysis_prediction(path)[1] == 0.2
    else:
        assert out["decision"]["state"] == "ABSTAINED" and analysis_prediction(path)[1] is None
    if mode in ("citation", "score", "rationale"):
        assert out["validation_diagnostic"]["field"] in (
            "risk_score",
            "evidence_ids",
            "rationale_short",
        )
    with pytest.raises(FileExistsError):
        asyncio.run(
            predict(tmp_path, p, fake, engineering_id="ENG-5a1-test", sufficiency_policy=VERSION)
        )


def test_selected_omission_is_not_blanket_permission(tmp_path):
    a = packet("executed-lawful", View.A)
    assert eligibility(a)["eligible"]
    path = asyncio.run(
        predict(
            tmp_path,
            a,
            Fake("valid"),
            engineering_id="ENG-5a1-selected",
            sufficiency_policy=VERSION,
        )
    )
    out = replay_prediction(path)
    assert out["decision"]["state"] == "SCORED"
    from pactlens.research.detector_contract import PredictionRecord

    r = out["prediction"]
    record = PredictionRecord(
        r["episode_public_id"],
        View.A,
        r["evidence_version"],
        r["prompt_hash"],
        canonical_json(r["response"]),
    )
    assert old_decision(a, record)["state"] == "ABSTAINED"
    assert not eligibility(packet("executed-lawful", View.MA))["eligible"]


@pytest.mark.parametrize("case", ["known-absence", "executed-lawful"])
def test_final_text_parity_and_evidence_eligibility(case):
    r, mae = packet(case, View.R), packet(case, View.MAE)
    assert verify_compact_parity(r, mae)
    assert eligibility(r)["eligible"] == eligibility(mae)["eligible"]
    assert eligibility(r)["reasons"] == eligibility(mae)["reasons"]
    assert len(r.resolve_citations(["f0"])) == 1
    with pytest.raises(ValueError):
        r.resolve_citations(["f999"])


def test_full_native_schema_is_accounted():
    turns = (Turn("system", "fixed"), Turn("user", "data"))
    complete = request_budget(turns, "agent", require=False)
    from pactlens.agents.budgets import token_preflight

    conversation = token_preflight(turns, limit=2000)
    assert complete.estimated_tokens > conversation.estimated_tokens + 400
    assert (
        complete.utf8_bytes
        == len(
            canonical_json(
                payload(
                    turns,
                    __import__(
                        "pactlens.agents.deepseek_provider", fromlist=["AGENT_SCHEMA"]
                    ).AGENT_SCHEMA,
                )
            ).encode("utf-8")
        )
        + 4
    )


def test_paid_context_and_total_caps(tmp_path):
    ledger = CampaignLedger.phase5a1(tmp_path / "campaign.sqlite3")
    b = request_budget((Turn("user", "offline"),), "agent")
    for i in range(6):
        ledger.reserve("agent", str(i), b, context_id="ENG-5a1-N3")
    with pytest.raises(ProviderFailure, match="EPISODE_CALL_CAP"):
        ledger.reserve("agent", "seventh", b, context_id="ENG-5a1-N3")
    with pytest.raises(ProviderFailure, match="UNDECLARED"):
        ledger.reserve("agent", "other", b, context_id="formal-pilot")
    for i in range(10):
        ledger.reserve("detector", "d" + str(i), b)
    with pytest.raises(ProviderFailure, match="CALL_CAP"):
        ledger.reserve("detector", "d11", b)
    for context in ("ENG-5a1-C_PLUS", "ENG-5a1-C_MINUS"):
        for i in range(6):
            ledger.reserve("agent", context + str(i), b, context_id=context)
    assert len(ledger.report()["calls"]) == 28
    with pytest.raises(ProviderFailure):
        ledger.reserve("agent", "twenty-ninth", b, context_id="ENG-5a1-C_PLUS")
    assert ledger.report()["reserved_or_charged_micro_usd"] <= 2000000


def test_new_freeze_candidate_requires_all_sixteen_attributable_choices():
    manifest = freeze_candidate(ROOT, profile="phase5a1")
    assert set(manifest["decisions"]) == set(DECISIONS_5A1) and len(DECISIONS_5A1) == 16
    assert not any(v["status"] == "APPROVED" for v in manifest["decisions"].values())
    with pytest.raises(ValueError, match="FROZEN_APPROVALS"):
        verify_launch(manifest, ROOT)
    changed = json.loads(json.dumps(manifest))
    changed["configuration"]["input_caps"]["detector"] = 8192
    changed["manifest_hash"] = content_hash(
        {k: v for k, v in changed.items() if k != "manifest_hash"}
    )
    with pytest.raises(ValueError, match="CONFIGURATION_CHANGED"):
        verify_launch(changed, ROOT)


def test_six_position_matrix_no_truncation_or_heldout():
    data = json.loads(
        (ROOT / "review/phase5a1/offline-agent-matrix.json").read_text(encoding="utf-8")
    )
    assert len(data["rows"]) == 20 and data["paid_calls"] == 0
    for row in data["rows"]:
        assert row["opportunities"] == 6 and row["pure_replay_equal"]
        if row["case"] in ("base", "communication", "decline"):
            assert all(b["fits"] for b in row["native_budgets"])
        if row["case"] == "long":
            assert any(not b["fits"] and b["round"] == 2 for b in row["native_budgets"])


def test_lower_user_ceiling_and_no_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv("PACTLENS_DEEPSEEK_MAX_USD", "0.0001")
    ledger = CampaignLedger.phase5a1(tmp_path / "lower.sqlite3")
    with pytest.raises(ProviderFailure, match="SPEND_CAP"):
        ledger.reserve(
            "agent", "x", request_budget((Turn("user", "x"),), "agent"), context_id="ENG-5a1-N3"
        )
    assert ledger.report()["calls"] == []


def test_protected_denominators_and_matched_groups_remain_original():
    from pactlens.research.analysis import Case, metrics
    from pactlens.research.seeds import Condition, Split

    case = Case(
        "synthetic-episode",
        "synthetic-matched-group",
        Split.HELD_OUT,
        Condition.N1,
        0,
        True,
        True,
        True,
        False,
        True,
        ((View.MA, 0.8, 0.9), (View.MAE, None, None)),
    )
    # Manufactured rows validate the frozen denominator; no held-out files/outcomes are opened.
    ma, mae = metrics([case], View.MA, 0.5), metrics([case], View.MAE, 0.5)
    assert ma["n1_fpr"] == 1 and mae["n1_fpr"] == 0
    assert ma["primary_n1"] == mae["primary_n1"] == 1


def test_unknown_missing_capture_and_communication_are_distinct():
    from pactlens.evidence.inventory import Inventory
    from pactlens.evidence.observation_policy import ObservationPolicy
    from pactlens.evidence.tight_views import render
    from pactlens.serialization import canonical_json as integer_json

    original = packet("known-absence", View.R)
    h, facts = original.verify()
    assert eligibility(original)["eligible"] and any(f.completeness == "MISSING" for f in facts)
    for mode in ("unknown", "capture", "omitted_message"):
        changed = []
        for f in facts:
            p = json.loads(f.payload_json)
            if (
                mode == "unknown"
                and f.kind == "aig_action"
                and f.actor == "Actor-1"
                and p["round"] == 1
            ):
                p["action_state"] = "Unknown"
                f = replace(f, payload_json=integer_json(p))
            if mode == "capture" and f.kind == "execution_coverage":
                p["capture"] = "INCOMPLETE"
                f = replace(f, payload_json=integer_json(p))
            changed.append(f)
        inv = Inventory(h["episode"], ObservationPolicy(h["policy"]), tuple(changed))
        ids = {f.fact_id for f in changed}
        if mode == "omitted_message":
            ids -= {f.fact_id for f in changed if f.kind == "communication_coverage"}
        p = render(inv, ids, set(), "0" * 64, View.R, envelope())
        assert not eligibility(p)["eligible"]


@pytest.mark.parametrize("malformed", [False, True])
def test_v33_assignments_use_unchanged_parser_and_real_aig(tmp_path, malformed):
    from harness_helpers import FakeModel

    from pactlens.agents.context_v33 import V33_PROMPT, decode, encode
    from pactlens.aig.submission import TestConsent as Consent
    from pactlens.experiments.conditions import EpisodeConfig
    from pactlens.experiments.harness import run_episode
    from pactlens.experiments.replay import replay_trace
    from pactlens.research.fixtures import fixture_task
    from pactlens.research.seeds import Condition

    def transform(body, r):
        decoded = decode(r.turns[-1].content)
        assert encode(decoded) == r.turns[-1].content
        if malformed:
            body["assignments"] = [[a["incident_id"], a["agent_id"]] for a in body["assignments"]]

    model = FakeModel(fixture_task(), transform)
    run = asyncio.run(
        run_episode(
            tmp_path,
            fixture_task(),
            EpisodeConfig("ENG-v33-parser", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=V33_PROMPT,
        )
    )
    assert len(model.requests) == 6
    assert len(run.observations) == (0 if malformed else 6)
    replay = replay_trace(run.trace_path)
    assert replay.model_calls == replay.new_effects == 0
    assert replay.evidence.to_json() == run.evidence().to_json()


def test_new_profile_manufactured_approvals_only_dry_check(tmp_path):
    from test_phase5a_launch import NOW, approved_fixture, seal

    old = approved_fixture(tmp_path)
    candidate = freeze_candidate(tmp_path, profile="phase5a1")
    candidate.update(
        status=old["status"],
        qualifications=old["qualifications"],
        official_start_verification=old["official_start_verification"],
        owner_authorization=old["owner_authorization"],
    )
    candidate["owner_authorization"]["configuration_hash"] = candidate["configuration_hash"]
    for d in candidate["decisions"].values():
        d.update(
            status="APPROVED",
            researcher="SYNTHETIC_UNIT_TEST_NOT_OWNER",
            timestamp="2026-10-24T00:00:00Z",
            record="MANUFACTURED_DRY_CHECK_ONLY",
        )
    seal(candidate)
    assert verify_launch(candidate, tmp_path, now=NOW)
    candidate["decisions"]["evidence_selection_sufficiency"]["status"] = "PROPOSED"
    seal(candidate)
    with pytest.raises(ValueError, match="ATTRIBUTABLE_METHOD"):
        verify_launch(candidate, tmp_path, now=NOW)


@pytest.mark.parametrize("configuration", [{"input_limit": 1000}, {"context_window_tokens": 1256}])
def test_native_envelope_honors_smaller_trusted_input_limits(configuration):
    from pactlens.agents.budgets import BudgetExceeded

    p = packet("known-absence", View.M)
    smaller = replace(p.envelope, **configuration)
    assert smaller.budget(p.text).limit == 1000 and not smaller.budget(p.text).fits
    with pytest.raises(BudgetExceeded):
        smaller.budget(p.text, require=True)
