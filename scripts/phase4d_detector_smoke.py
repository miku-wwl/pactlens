"""Explicit at-most-two local engineering calls; never formal detector qualification."""

import argparse
import asyncio
from pathlib import Path

from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.provider import ModelConfig
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.experiments.phase4d_engineering import DIGEST
from pactlens.experiments.replay import replay_trace
from pactlens.research.detector_runner import exclusive_json, predict, replay_prediction
from pactlens.research.json_types import canonical_json, content_hash


async def smoke(root, trace, *, allow_two_local=False):
    if allow_two_local is not True:
        raise ValueError("EXPLICIT_TWO_CALL_ENGINEERING_ALLOWANCE")
    root.mkdir(parents=True, exist_ok=False)
    replay = replay_trace(trace)
    inv = build_inventory(
        replay.record,
        public_id=replay.evidence.as_mapping()["episode_public_id"],
        policy=ObservationPolicy.DELIVERED,
        status=replay.status,
    )
    packets = select_common(inv)
    packets.verify()
    provider = OllamaProvider(
        "http://127.0.0.1:11434/v1",
        ModelConfig("phi4-mini:latest", DIGEST, "ollama_loopback_openai"),
    )
    identity = provider.readiness()
    results = []
    for i, view in enumerate((View.R, View.MAE), 1):
        packet = packets.packet(view)
        packet.conversation()  # active complete-request estimate before charging
        if provider.calls >= 2:
            raise ValueError("DETECTOR_SMOKE_CAP")
        exclusive_json(
            root / f"charge-{i}.json", {"attempt": i, "request_hash": content_hash(packet.text)}
        )
        path = await predict(
            root / "predictions", packet, provider, engineering_id="ENG-phase4d-detector", seed=i
        )
        result = replay_prediction(path)
        results.append(
            {
                "view": view.value,
                "prediction": result["prediction"],
                "abstained": result["abstained"],
                "budget": result["budget"],
                "usage": result["usage"],
                "artifact_hash": result["artifact_hash"],
                "file_sha256": result["file_sha256"],
            }
        )
    output = {
        "purpose": "INTERFACE_ONLY_NOT_ACCURACY_OR_FORMAL_QUALIFICATION",
        "identity": identity,
        "actual_detector_calls": provider.calls,
        "formal_predictions": 0,
        "results": results,
    }
    exclusive_json(root / "safe-summary.json", output)
    print(canonical_json(output))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("trace", type=Path)
    p.add_argument("--allow-two-local", action="store_true")
    a = p.parse_args()
    asyncio.run(smoke(a.directory, a.trace, allow_two_local=a.allow_two_local))
