"""At most one fresh N3 v3-context local engineering episode. Never a study or detector.

The offline gate first runs the same configuration with a deterministic offline
transcript (no model, no network) through the real harness; any input-budget
failure there stops before inference. The live episode charges an exclusive
six-call ledger before each dispatch, never resumes, retries or replaces a step.
"""

import argparse
import asyncio
import os
from pathlib import Path

from pactlens.agents.context_v3 import V3_PROMPT, decode_request
from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.agents.reliability import response_observations
from pactlens.aig.submission import TestConsent
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-context-qualification-v1"
GROUP = "ENG-phase4c-context-v3"
CAP = 6


class SixCallLedger:
    """Charge before dispatch; a seventh or non-v3 request is refused, never retried."""

    def __init__(self, path):
        self.handle = Path(path).open("x", encoding="utf-8", newline="\n")  # noqa: SIM115 -- closed in qualify finally
        self.total = 0

    def charge(self, request):
        if request.prompt_version != V3_PROMPT or self.total >= CAP:
            raise ValueError("LOCAL_GENERATION_CAP_NO_RETRY")
        self.total += 1
        self.handle.write(
            canonical_json({"attempt": self.total, "request_hash": content_hash(request)}) + "\n"
        )
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        self.handle.close()


class Charged:
    def __init__(self, provider, ledger):
        self.provider, self.ledger, self.config = provider, ledger, provider.config

    async def generate(self, request):
        self.ledger.charge(request)
        return await self.provider.generate(request)


class OfflineTranscript:
    """Deterministic offline preflight transcript: the request's own syntax example."""

    config = ModelConfig(
        "offline-gate-transcript", "first-feasible-example", seed_support="FAKE_DETERMINISTIC"
    )

    def __init__(self):
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        examples = decode_request(request.turns)["examples"]
        body = examples["submit_example"] or examples["decline_example"]
        return ModelResponse(canonical_json(body), 1, None, None, "stop")


async def offline_gate(directory, task, config):
    """Six-step v3 path with the deterministic transcript; zero model or network calls."""
    transcript = OfflineTranscript()
    run = await run_episode(
        directory,
        task,
        config,
        transcript,
        consent=TestConsent(synthetic_consent=True),
        prompt_version=V3_PROMPT,
    )
    failures = [r["payload"] for r in read_trace(run.trace_path) if r["kind"] == "MODEL_FAILURE"]
    return {
        "status": run.status,
        "requests": len(transcript.requests),
        "input_budget_failures": sum(
            f["diagnostic"]["code"] == "INPUT_BUDGET_EXCEEDED" for f in failures
        ),
        "estimated_tokens": [r.token_budget.estimated_tokens for r in transcript.requests],
        "fits": run.status == "COMPLETE" and len(transcript.requests) == 6,
    }


async def qualify(directory, task, provider, *, allow_one_local_engineering_episode=False):
    if (
        allow_one_local_engineering_episode is not True
        or type(provider) is not OllamaProvider
        or provider.calls != 0
    ):
        raise ValueError("EXPLICIT_FRESH_LOCAL_QUALIFICATION_REQUIRED")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("FRESH_QUALIFICATION_DIRECTORY_NO_RESUME")
    config = EpisodeConfig(GROUP, Condition.N3)
    gate = await offline_gate(root / "offline-gate", task, config)
    summary = {
        "version": VERSION,
        "provenance": "PRE_SPRINT_ENGINEERING_NOT_FORMAL_OBSERVATION",
        "group": GROUP,
        "condition": "N3",
        "prompt_version": V3_PROMPT,
        "task_hash": task.task_hash,
        "offline_gate": gate,
        "synthetic_consent": True,
        "formal_episodes": 0,
        "detector_predictions": 0,
    }
    if not gate["fits"] or provider.calls != 0:
        summary["status"] = "BLOCKED_OFFLINE_GATE_NO_INFERENCE"
        summary["actual_generation_calls"] = provider.calls
        (root / "summary.json").write_text(canonical_json(summary), encoding="utf-8")
        return summary
    summary["identity"] = provider.readiness()
    summary["model_config"] = provider.config
    ledger = SixCallLedger(root / "generation-ledger.jsonl")
    try:
        run = await run_episode(
            root / "episode",
            task,
            config,
            Charged(provider, ledger),
            consent=TestConsent(synthetic_consent=True),
            prompt_version=V3_PROMPT,
        )
        replay = replay_trace(run.trace_path)
        measurements = response_observations(run)
        rows = read_trace(run.trace_path)
        summary.update(
            {
                "status": run.status,
                "public_id": run.public_id,
                "trace_sha256": content_hash(run.trace_path.read_text(encoding="utf-8")),
                "requests": [
                    {
                        "actor": r["payload"]["request"]["actor_id"],
                        "round": r["payload"]["request"]["round_number"],
                        "token_budget": r["payload"]["request"]["token_budget"],
                        "request_digest": r["payload"]["request_digest"],
                    }
                    for r in rows
                    if r["kind"] == "MODEL_REQUEST"
                ],
                "failures": [
                    {
                        k: r["payload"][k]
                        for k in ("actor_id", "round_number", "diagnostic", "token_budget")
                    }
                    for r in rows
                    if r["kind"] == "MODEL_FAILURE"
                ],
                "deliveries": [
                    {
                        "sender": d.sender,
                        "round": d.round_number,
                        "channel": d.channel.value,
                        "status": d.status,
                    }
                    for d in run.deliveries
                ],
                "measurements": measurements,
                "actions": len(run.observations),
                "receipts": sum(o.receipt_status == "VERIFIED_COMMITTED" for o in run.observations),
                "action_states": [o.action_state for o in run.observations],
                "finalized": run.record.state.status.value == "FINALIZED",
                "executor_calls": run.executor_calls,
                "pure_replay_equal": replay.evidence.to_json() == run.evidence().to_json(),
                "replay_model_calls": replay.model_calls,
                "replay_new_effects": replay.new_effects,
            }
        )
    finally:
        ledger.close()
        summary["actual_generation_calls"] = provider.calls
        summary["charged_attempts"] = ledger.total
        (root / "summary.json").write_text(canonical_json(summary), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-one-local-engineering-episode", action="store_true", required=True)
    args = parser.parse_args()
    result = asyncio.run(
        qualify(
            args.directory,
            fixture_task(),
            OllamaProvider.from_environment(),
            allow_one_local_engineering_episode=args.allow_one_local_engineering_episode,
        )
    )
    print(canonical_json(result))


if __name__ == "__main__":
    main()
