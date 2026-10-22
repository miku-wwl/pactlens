"""One prospective bounded campaign. Never resumes or replaces an episode."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from pactlens.agents.context_v32 import V32_PROMPT
from pactlens.agents.deepseek_provider import (
    PROFILE,
    CampaignLedger,
    DeepSeekProvider,
    request_budget,
)
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.submission import TestConsent
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import summary
from pactlens.research.detector_runner import exclusive_json, predict, replay_prediction
from pactlens.research.fixtures import fixture_task, run_fixture
from pactlens.research.reviewer_packets import prepare_reviewer_packets
from pactlens.research.seeds import Condition
from pactlens.serialization import content_hash, primitive

ROOT = Path(".runtime/phase4e5a-live")
SAFE = Path("review/phase4e5a/live")


async def main(allow):
    if allow != "phase4e-authorized-max56-usd5":
        raise ValueError("EXPLICIT_ENGINEERING_ALLOWANCE_REQUIRED")
    offline = json.loads(Path("review/phase4e5a/offline.json").read_text(encoding="utf-8"))
    if (
        offline["valid"] != 6
        or offline["receipts"] != 6
        or not all(x["fits"] for x in offline["complete_wire_budgets"])
    ):
        raise ValueError("OFFLINE_GATE_FAILED")
    ROOT.mkdir(parents=True, exist_ok=False)
    SAFE.mkdir(parents=True, exist_ok=False)
    plan = {
        "version": "phase4e-fixed-campaign-v1",
        "profile": PROFILE,
        "prompt_version": V32_PROMPT,
        "prompt_hash": PROMPT_HASHES[V32_PROMPT],
        "agent_schedule": ["N3", "C+", "C-", "N1", "N2"],
        "n3_gate": ">=5/6 valid and no trust failure; no replacements",
        "agent_max_planned": 30,
        "detector_sources": ["n3_cooperation", "n2_talk_only", "unexpected_control_harm"],
        "detector_views": [v.value for v in View],
        "detector_max_planned": 15,
        "metadata_http_requests_already_performed": 1,
        "hard_caps": {"agent": 36, "detector": 20, "total": 56, "usd": 5},
        "provenance": "PRE_SPRINT_ENGINEERING_NOT_FORMAL",
        "reviewer_status": "UNASSIGNED",
    }
    plan["plan_hash"] = content_hash(plan)
    exclusive_json(SAFE / "predeclared-plan.json", plan)
    ledger = CampaignLedger(ROOT / "inference.sqlite3")
    result = {
        "plan_hash": plan["plan_hash"],
        "agent_episodes": [],
        "detector_predictions": [],
        "formal_executions": 0,
        "human_adjudications": 0,
        "synthetic_consent": True,
    }
    task = fixture_task()
    try:
        for condition in (
            Condition.N3,
            Condition.C_PLUS,
            Condition.C_MINUS,
            Condition.N1,
            Condition.N2,
        ):
            config = EpisodeConfig("ENG-phase4e-common", condition)
            provider = DeepSeekProvider(ledger, "agent", context_id="ENG-phase4e-" + condition.name)
            run = await run_episode(
                ROOT / condition.name,
                task,
                config,
                provider,
                consent=TestConsent(True),
                prompt_version=V32_PROMPT,
                stop_on_input_budget_failure=True,
            )
            row = {
                **summary(run),
                "engineering_case": condition.value,
                "task_hash": task.task_hash,
                "role_order": config.roles(task),
                "seeds": [
                    config.seed(a, r, task).integer for r in (1, 2) for a in config.roles(task)
                ],
                "independent_contexts_and_stores": True,
            }
            result["agent_episodes"].append(row)
            exclusive_json(SAFE / (condition.name + "-summary.json"), row)
            # Review packets contain public behavior and symmetric pair comparators,
            # no assigned pair, condition, private brief, L4 or oracle truth.
            packet = prepare_reviewer_packets(
                run.record,
                run.observations,
                run.deliveries,
                public_id=run.public_id,
                status=run.status,
                shared_capture=True,
            )
            exclusive_json(SAFE / (run.public_id + "-reviewers.json"), packet)
            exclusive_json(SAFE / (condition.name + "-usage.json"), ledger.report())
            if condition == Condition.N3 and (
                row["valid"] < 5
                or run.status.startswith("STOPPED")
                or "Unknown" in row["action_states"]
            ):
                result["agent_stop"] = "N3_GATE_FAILED_NO_REPLACEMENT"
                break
            if provider.blocked or run.status.startswith("STOPPED"):
                result["agent_stop"] = "PROFILE_OR_RUNTIME_STOPPED_NO_REPLACEMENT"
                break
        detector = DeepSeekProvider(ledger, "detector")
        for n, name in enumerate(plan["detector_sources"]):
            fixture = run_fixture(name)
            inv = build_inventory(
                fixture.record, public_id=str(uuid4()), policy=ObservationPolicy.DELIVERED
            )
            selected = select_common(inv)
            selected.verify()
            for view in View:
                packet = selected.packet(view)
                path = await predict(
                    SAFE / "predictions",
                    packet,
                    detector,
                    engineering_id=f"ENG-phase4e-detector-{n + 1}",
                    seed=n,
                )
                replay = replay_prediction(path)
                row = {
                    "engineering_source": name,
                    "view": view.value,
                    "path": path.as_posix(),
                    "prediction_error": replay["prediction"]["error"],
                    "provider_error": replay.get("provider_error"),
                    "decision": replay["decision"],
                    "usage": replay["usage"],
                    "complete_wire_budget": primitive(
                        request_budget(packet.conversation(), "detector", require=False)
                    ),
                    "replay_calls": replay["replay_generation_calls"],
                    "replay_effects": replay["replay_new_effects"],
                }
                result["detector_predictions"].append(row)
                if detector.blocked:
                    result["detector_stop"] = "PROFILE_STOPPED_NO_REPLACEMENT"
                    break
            if detector.blocked:
                break
    finally:
        exclusive_json(SAFE / "usage-final.json", ledger.report())
        exclusive_json(SAFE / "campaign-summary.json", result)
    print(
        json.dumps(
            {
                "episodes": len(result["agent_episodes"]),
                "detector_packets": len(result["detector_predictions"]),
                "usage": {
                    k: v for k, v in ledger.report().items() if k not in ("calls", "profile")
                },
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.allow))
