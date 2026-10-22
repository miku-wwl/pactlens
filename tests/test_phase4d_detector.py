"""Deterministic detectors exercise the real validated L3 and durable L4 boundary."""

import asyncio
import json
from dataclasses import replace

import pytest
from view_helpers import PUBLIC_ID

from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.evidence.compact_views import render_compact
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.detector_runner import predict, replay_prediction
from pactlens.research.fixtures import run_fixture
from pactlens.research.json_types import canonical_json


class FakeDetector:
    config = ModelConfig("fake-detector", "synthetic-v1", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, mode="valid"):
        self.mode, self.calls = mode, 0

    async def generate(self, request):
        self.calls += 1
        assert not any(
            x in canonical_json(request)
            for x in ("assigned_coalition", "private_brief", "adjudication", "condition")
        )
        if self.mode == "provider":
            raise OSError("synthetic provider failure")
        body = {
            "risk_score": 0.25,
            "confidence": 0.5,
            "evidence_ids": ["public-task"],
            "rationale_short": "Synthetic interface validation only.",
            "adequacy": "ADEQUATE",
        }
        if self.mode == "insufficient":
            body["adequacy"] = "INSUFFICIENT_EVIDENCE"
        if self.mode == "citation":
            body["evidence_ids"] = ["invented/fact"]
        if self.mode == "score":
            body["risk_score"] = True
        if self.mode == "extra":
            body["threshold"] = 0.5
        raw = "not JSON" if self.mode == "json" else canonical_json(body)
        if self.mode == "duplicate":
            raw = raw[:-1] + ',"risk_score":0.5}'
        return ModelResponse(raw, 1, 100, 80, "length" if self.mode == "length" else "stop")


def packets(name="n3_cooperation"):
    run = run_fixture(name)
    inv = build_inventory(run.record, public_id=PUBLIC_ID, policy=ObservationPolicy.DELIVERED)
    return select_common(inv)


@pytest.mark.parametrize("view", list(View))
@pytest.mark.parametrize(
    "mode",
    [
        "valid",
        "insufficient",
        "provider",
        "citation",
        "score",
        "json",
        "duplicate",
        "length",
        "extra",
    ],
)
def test_detector_contract_storage_replay(tmp_path, view, mode):
    packet = packets().packet(view)
    provider = FakeDetector(mode)
    path = asyncio.run(predict(tmp_path, packet, provider, engineering_id="ENG-detector-unit"))
    assert provider.calls == 1
    original = path.read_bytes()
    record = replay_prediction(path)
    assert original == path.read_bytes() and provider.calls == 1
    assert record["replay_generation_calls"] == record["replay_new_effects"] == 0
    if mode == "valid":
        assert record["prediction"]["response"]["risk_score"] == 0.25
        assert record["prediction"]["response"]["evidence_ids"] == [
            packet.resolve_citations(["public-task"])[0]
        ]
    elif mode == "insufficient":
        assert record["abstained"]
    else:
        assert record["abstained"] and record["prediction"]["error"] in (
            "PROVIDER_ERROR",
            "INVALID_OUTPUT",
        )
    with pytest.raises(FileExistsError):
        asyncio.run(predict(tmp_path, packet, provider, engineering_id="ENG-detector-unit"))
    assert provider.calls == 1
    damaged = json.loads(path.read_text())
    damaged["prediction"]["prompt_hash"] = "0" * 64
    path.write_text(canonical_json(damaged))
    with pytest.raises(ValueError):
        replay_prediction(path)


def test_budget_refuses_before_provider_and_records_abstention(tmp_path):
    packet = packets().packet(View.R)
    inv = build_inventory(
        run_fixture("n3_cooperation").record,
        public_id=PUBLIC_ID,
        policy=ObservationPolicy.DELIVERED,
    )
    packet = render_compact(
        inv,
        {f.fact_id for f in inv.facts},
        set(),
        "0" * 64,
        View.R,
        DetectorEnvelope(input_limit=100),
    )
    provider = FakeDetector()
    path = asyncio.run(predict(tmp_path, packet, provider, engineering_id="ENG-overflow"))
    assert provider.calls == 0
    assert replay_prediction(path)["prediction"]["error"] == "INPUT_BUDGET_EXCEEDED"


def test_formal_namespace_and_bad_manifest_rejected_without_call(tmp_path):
    packet = packets().packet(View.M)
    provider = FakeDetector()
    for namespace in ("P001", "T001", "K001"):
        with pytest.raises(ValueError):
            asyncio.run(predict(tmp_path, packet, provider, engineering_id=namespace))
    with pytest.raises(ValueError):
        asyncio.run(
            predict(
                tmp_path,
                replace(packet, text=packet.text + " "),
                provider,
                engineering_id="ENG-bad-manifest",
            )
        )
    assert provider.calls == 0


def test_selected_incomplete_packet_forces_abstention(tmp_path):
    packet = packets("c_plus").packet(View.R)
    assert json.loads(packet.manifest_json)["omitted"]
    path = asyncio.run(predict(tmp_path, packet, FakeDetector(), engineering_id="ENG-incomplete"))
    r = replay_prediction(path)
    assert r["source_coverage_insufficient"] and r["abstained"]
