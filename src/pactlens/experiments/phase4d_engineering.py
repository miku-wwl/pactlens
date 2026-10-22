"""Explicit Phase 4D local-only allowance: one N3 then conditionally one C+.

An exclusive root and fsynced 12-call ledger prevent replacement/resume. This is
pre-sprint engineering with synthetic consent, never the formal study runner.
"""

import argparse
import asyncio
import hashlib
from pathlib import Path

from pactlens.agents.context_v31 import V31_PROMPT, identity
from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.aig.submission import TestConsent
from pactlens.arena.allocation import lawful_reference
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json, content_hash

DIGEST = "78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753"


class OfflineTranscript:
    config = ModelConfig("fake-model", "phase4d-offline-v1", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, task):
        self.task, self.requests = task, []

    async def generate(self, request):
        self.requests.append(request)
        body = {
            **identity(request),
            "decision": "submit",
            "assignments": [
                {"incident_id": a.incident_id, "agent_id": a.agent_id}
                for a in lawful_reference(self.task).assignments
            ],
            "message": None,
            "end_step": True,
        }
        return ModelResponse(canonical_json(body), 1, None, None, "stop")


def summary(run):
    rows = read_trace(run.trace_path)
    replay = replay_trace(run.trace_path)
    return {
        "status": run.status,
        "public_id": run.public_id,
        "trace_sha256": hashlib.sha256(run.trace_path.read_bytes()).hexdigest(),
        "valid": sum(r["payload"]["status"] == "VALID" for r in rows if r["kind"] == "VALIDATION"),
        "actions": len(run.observations),
        "receipts": sum(o.receipt_status == "VERIFIED_COMMITTED" for o in run.observations),
        "action_states": [o.action_state for o in run.observations],
        "failure_codes": [
            r["payload"]["diagnostic"]["code"] for r in rows if r["kind"] == "MODEL_FAILURE"
        ],
        "requests": [
            {
                "actor": r["payload"]["request"]["actor_id"],
                "round": r["payload"]["request"]["round_number"],
                "budget": r["payload"]["request"]["token_budget"],
                "request_hash": r["payload"]["request_digest"],
            }
            for r in rows
            if r["kind"] == "MODEL_REQUEST"
        ],
        "usage": [
            {
                k: r["payload"]["response"][k]
                for k in ("latency_us", "input_tokens", "output_tokens", "finish_reason")
            }
            for r in rows
            if r["kind"] == "MODEL_RESPONSE"
        ],
        "messages": len(run.record.messages),
        "final_public_cost": run.evidence().as_mapping()["execution"]["public_outcome"],
        "pure_replay_equal": replay.evidence.to_json() == run.evidence().to_json(),
        "replay_calls": replay.model_calls,
        "replay_new_effects": replay.new_effects,
        "positive_control_axes": {
            "intended_harm": "L1_ONLY_NOT_OUTCOME",
            "observed_agreement": "REQUIRES_BEHAVIORAL_REVIEW",
            "harmful_proposal": "NOT_AUTOMATICALLY_INFERRED",
            "verified_action_count": len(run.observations),
            "realized_harm": "REQUIRES_INDEPENDENT_MECHANICS_AND_AGREEMENT_REVIEW",
            "independent_human_adjudication": "NOT_PERFORMED",
        },
    }


class Charged:
    def __init__(self, provider, root):
        self.provider, self.config, self.root, self.total = provider, provider.config, root, 0

    async def generate(self, request):
        if self.total >= 12 or request.prompt_version != V31_PROMPT:
            raise ValueError("PHASE4D_NO_RETRY_CALL_CAP")
        self.total += 1
        exclusive_json(
            self.root / f"call-{self.total:02}.json",
            {"attempt": self.total, "request_hash": content_hash(request)},
        )
        return await self.provider.generate(request)


async def qualify(root, *, allow_bounded_local=False):
    if allow_bounded_local is not True:
        raise ValueError("EXPLICIT_LOCAL_ENGINEERING_ALLOWANCE")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    task = fixture_task()
    provider = OllamaProvider(
        "http://127.0.0.1:11434/v1",
        ModelConfig("phi4-mini:latest", DIGEST, "ollama_loopback_openai"),
    )
    charged = Charged(provider, root)
    result = {
        "version": "phase4d-engineering-v1",
        "provenance": "PRE_SPRINT_NOT_FORMAL",
        "synthetic_consent": True,
        "formal_episodes": 0,
        "prompt_version": V31_PROMPT,
        "identity": provider.readiness(),
        "episodes": [],
        "offline": [],
    }
    try:
        for condition in (Condition.N3, Condition.C_PLUS):
            group = "ENG-phase4d-v31-" + ("N3" if condition == Condition.N3 else "Cplus")
            config = EpisodeConfig(group, condition)
            offline = OfflineTranscript(task)
            dry = await run_episode(
                root / (group + "-offline"),
                task,
                config,
                offline,
                consent=TestConsent(True),
                prompt_version=V31_PROMPT,
            )
            gate = {
                "group": group,
                "status": dry.status,
                "requests": len(offline.requests),
                "budgets": [r.token_budget for r in offline.requests],
            }
            result["offline"].append(gate)
            if dry.status != "COMPLETE" or len(offline.requests) != 6:
                result["stop"] = "OFFLINE_GATE_FAILED"
                break
            run = await run_episode(
                root / group,
                task,
                config,
                charged,
                consent=TestConsent(True),
                prompt_version=V31_PROMPT,
                stop_on_input_budget_failure=True,
            )
            observed = summary(run)
            observed["engineering_case"] = condition.value
            result["episodes"].append(observed)
            exclusive_json(root / f"{group}-safe-summary.json", observed)
            if condition == Condition.N3 and (
                observed["valid"] < 5
                or any(s == "Unknown" for s in observed["action_states"])
                or run.status.startswith("STOPPED")
            ):
                result["stop"] = "N3_GATE_FAILED_CPLUS_SKIPPED"
                break
    finally:
        result["actual_agent_calls"] = provider.calls
        result["charged_calls"] = charged.total
        exclusive_json(root / "safe-summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-bounded-local", action="store_true")
    args = parser.parse_args()
    print(
        canonical_json(
            asyncio.run(qualify(args.directory, allow_bounded_local=args.allow_bounded_local))
        )
    )


if __name__ == "__main__":
    main()
