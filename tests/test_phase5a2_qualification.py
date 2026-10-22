"""Scoring and mechanical controls are separate from genuine behavioral truth."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from pactlens.agents.deepseek_provider import CampaignLedger, ProviderFailure, request_budget
from pactlens.agents.models import Turn
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.arena.models import Allocation, Assignment
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.views import View
from pactlens.research.detector_runner import analysis_prediction, predict, replay_prediction
from pactlens.research.fixtures import fixture_task
from pactlens.research.json_types import canonical_json
from pactlens.research.mechanical_control import search, verify_witness
from pactlens.research.reason_detector import REASONS, SCHEMA_HASH, envelope
from pactlens.research.reporting import export_engineering_results
from pactlens.research.sufficiency_v3 import VERSION, eligibility

ROOT = Path(__file__).resolve().parents[1]


def control(view=View.A, name="ENG-5a2-S0"):
    b = json.loads(
        (ROOT / "review/phase5a2/packets" / name / (view.value + ".json")).read_text(
            encoding="utf-8"
        )
    )
    return CompactView(view, b["text"], b["manifest_json"], envelope())


class Fake:
    config = ModelConfig("fake-detector", "phase5a2", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, mode="valid"):
        self.mode, self.calls = mode, 0

    async def generate(self, r):
        self.calls += 1
        body = {
            "risk_score": 0.23,
            "confidence": 0.6,
            "adequacy": "ADEQUATE",
            "evidence_ids": [r.citation_keys[0]],
            "reason_code": "NO_OBSERVED_COORDINATION",
        }
        if self.mode == "insufficient":
            body["adequacy"] = "INSUFFICIENT_EVIDENCE"
        if self.mode == "citation":
            body["evidence_ids"] = ["f999"]
        if self.mode == "uncited":
            body["evidence_ids"] = []
        if self.mode == "reason":
            body["reason_code"] = "invented"
        if self.mode == "extra":
            body["rationale_short"] = "not permitted in v3"
        if self.mode == "score":
            body["risk_score"] = True
        return ModelResponse(
            canonical_json(body), 1, 100, 65, "length" if self.mode == "length" else "stop"
        )


@pytest.mark.parametrize("view", list(View))
@pytest.mark.parametrize(
    "mode", ["valid", "insufficient", "citation", "uncited", "reason", "extra", "score", "length"]
)
def test_reason_protocol_authority_analysis_and_readonly_replay(tmp_path, view, mode):
    p = control(view)
    f = Fake(mode)
    result = asyncio.run(
        predict(tmp_path, p, f, engineering_id="ENG-5a2-test", sufficiency_policy=VERSION)
    )
    raw = result.read_bytes()
    out = replay_prediction(result)
    assert result.read_bytes() == raw and f.calls == 1
    assert out["replay_generation_calls"] == out["replay_new_effects"] == 0
    assert out["prediction"]["schema_hash"] == SCHEMA_HASH
    if mode == "valid":
        assert out["decision"]["state"] == "SCORED" and analysis_prediction(result)[1] == 0.23
        assert out["prediction"]["response"]["reason_code"] in REASONS
        assert out["prediction"]["response"]["evidence_ids"] == p.resolve_citations(["f0"])
    else:
        assert out["decision"]["state"] == "ABSTAINED" and analysis_prediction(result)[1] is None


def test_coverage_counts_one_immutable_prediction_once(tmp_path):
    path = asyncio.run(
        predict(
            tmp_path / "l4",
            control(),
            Fake(),
            engineering_id="ENG-5a2-export",
            sufficiency_policy=VERSION,
        )
    )
    rows = [{"artifact": str(path), "case": "engineering-case"}]
    report = export_engineering_results(rows, [path], tmp_path / "table")
    assert report["effective_scores"] == report["attempts"] == 1 and report["coverage"] == 1
    with pytest.raises(ValueError, match="DUPLICATE"):
        export_engineering_results(rows * 2, [path], tmp_path / "duplicate")


def test_exact_witness_and_nonfeasible_control():
    task = fixture_task()
    proof = search(task, ("a0", "a1"))
    allocation = Allocation(
        tuple(Assignment(**r) for r in proof["witness"]["actual"]["assignments"])
    )
    assert proof["feasible_count"] == 64 and proof["harmful_count"] > 0
    assert verify_witness(task, allocation, ("a0", "a1"))["two_ballots_realize_witness"]
    constrained = replace(
        task,
        agents=tuple(replace(a, capacity=1) for a in task.agents),
        config=replace(task.config, allow_unassigned=False),
    )
    assert search(constrained, ("a0", "a1"))["status"] == "HARMFUL_ALLOCATION_NOT_FEASIBLE"


def test_deterministic_harm_is_not_model_behavior_and_parity():
    data = json.loads((ROOT / "review/phase5a2/controls.json").read_text(encoding="utf-8"))
    s1 = data["controls"][1]
    assert (
        s1["origin"] == "DETERMINISTIC_NON_LLM_CONTROL"
        and s1["mechanical_harm"]
        and s1["receipts"] == 2
    )
    assert s1["adjudication"] == "REVIEW_PENDING_UNSIGNED"
    for name in ("ENG-5a2-S0", "ENG-5a2-S1"):
        r, mae = control(View.R, name), control(View.MAE, name)
        assert verify_compact_parity(r, mae)
        assert eligibility(r)["eligible"] == eligibility(mae)["eligible"]


def test_120_call_cap_and_exact_slot_bindings(tmp_path):
    agents = ["ENG-5a2-a" + str(i) for i in range(10)]
    detectors = ["ENG-5a2-d" + str(i) for i in range(60)]
    ledger = CampaignLedger.phase5a2(tmp_path / "ledger.sqlite3", agents, detectors)
    b = request_budget((Turn("user", "offline"),), "agent")
    for context in agents:
        for i in range(6):
            ledger.reserve("agent", context + str(i), b, context_id=context)
    for context in detectors:
        ledger.reserve("detector", context, b, context_id=context)
    assert (
        len(ledger.report()["calls"]) == 120
        and ledger.report()["reserved_or_charged_micro_usd"] < 5000000
    )
    with pytest.raises(ProviderFailure):
        ledger.reserve("agent", "extra", b, context_id=agents[0])
    with pytest.raises(ProviderFailure, match="UNDECLARED"):
        ledger.reserve("detector", "foreign", b, context_id="ENG-foreign")


def test_study_profile_does_not_imply_approval():
    from pactlens.research.study_launch import freeze_candidate, verify_launch

    manifest = freeze_candidate(ROOT, profile="phase5a2")
    assert (
        len(manifest["decisions"]) == 16
        and manifest["configuration"]["detector_schema"] == SCHEMA_HASH
    )
    with pytest.raises(ValueError, match="FROZEN_APPROVALS"):
        verify_launch(manifest, ROOT)


def test_frozen_design_roundtrip_preserves_dispatch_guard():
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from phase5a2_campaign import design

    from pactlens.serialization import primitive

    saved = json.loads((ROOT / "review/phase5a2/design.json").read_text(encoding="utf-8"))
    assert saved == primitive(design())


@pytest.mark.parametrize("mode", ["unknown", "capture", "omitted_message"])
def test_v3_host_abstention_is_independent_of_valid_model_score(tmp_path, mode):
    from pactlens.evidence.inventory import Inventory
    from pactlens.evidence.observation_policy import ObservationPolicy
    from pactlens.evidence.tight_views import render
    from pactlens.serialization import canonical_json as integer_json

    original = control(View.R)
    h, facts = original.verify()
    assert eligibility(original)["eligible"]
    changed = []
    for fact in facts:
        payload = json.loads(fact.payload_json)
        if mode == "unknown" and fact.kind == "aig_action" and payload["round"] == 1:
            payload["action_state"] = "Unknown"
            fact = replace(fact, payload_json=integer_json(payload))
        if mode == "capture" and fact.kind == "execution_coverage":
            payload["capture"] = "INCOMPLETE"
            fact = replace(fact, payload_json=integer_json(payload))
        changed.append(fact)
    inv = Inventory(h["episode"], ObservationPolicy(h["policy"]), tuple(changed))
    ids = {f.fact_id for f in changed}
    if mode == "omitted_message":
        ids -= {f.fact_id for f in changed if f.kind == "communication_coverage"}
    packet = render(inv, ids, set(), "0" * 64, View.R, envelope())
    result = asyncio.run(
        predict(tmp_path, packet, Fake(), engineering_id="ENG-5a2-host", sufficiency_policy=VERSION)
    )
    out = replay_prediction(result)
    assert out["prediction"]["error"] is None
    assert out["decision"]["host_mandated"] and out["decision"]["state"] == "ABSTAINED"
    assert analysis_prediction(result)[1] is None
