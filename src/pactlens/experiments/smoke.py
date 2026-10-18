"""Explicit local opt-in, exactly one engineering episode, never a formal block."""

import argparse
import asyncio
from pathlib import Path

from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.aig.submission import TestConsent
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-one-local-engineering-episode", action="store_true", required=True)
    args = parser.parse_args()
    provider = OllamaProvider.from_environment()
    readiness = provider.readiness()
    result = asyncio.run(
        run_episode(
            args.directory,
            fixture_task(),
            EpisodeConfig("ENG-local-smoke-v1", Condition.N3),
            provider,
            consent=TestConsent(synthetic_consent=True),
        )
    )
    replay = replay_trace(result.trace_path)
    summary = {
        "status": result.status,
        "readiness": readiness,
        "actual_model_calls": provider.calls,
        "actions": len(result.observations),
        "verified_receipts": sum(
            o.receipt_status == "VERIFIED_COMMITTED" for o in result.observations
        ),
        "deliveries": len(result.deliveries),
        "delivered": sum(d.status == "DELIVERED" for d in result.deliveries),
        "finalized": result.record.state.status.value == "FINALIZED",
        "executor_calls": result.executor_calls,
        "pure_replay_equal": replay.evidence.to_json() == result.evidence().to_json(),
        "replay_model_calls": replay.model_calls,
        "replay_new_effects": replay.new_effects,
        "formal_episodes_executed": 0,
        "synthetic_consent": True,
    }
    (args.directory / "observation.json").write_text(result.evidence().to_json(), encoding="utf-8")
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
