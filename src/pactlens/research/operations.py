"""Frozen-study preparation and engineering dry runs. No formal dispatch surface."""

import re
from dataclasses import dataclass
from pathlib import Path

from pactlens.agents.context_v31 import V31_PROMPT
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.submission import TestConsent
from pactlens.arena.generator import generate_task
from pactlens.evidence.sufficiency import COMPLETE_HASH, SELECTION_HASH
from pactlens.experiments.conditions import EpisodeConfig, engineering_seed
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import OfflineTranscript, summary
from pactlens.research.baselines import CONFIG_HASH as BASELINE_HASH
from pactlens.research.detector_contract import RESPONSE_HASH, DetectorEnvelope
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.readiness import FROZEN_RULES
from pactlens.research.reviewer_packets import RUBRIC_HASH
from pactlens.research.seeds import Condition, Split
from pactlens.serialization import content_hash

APPROVALS = (
    "primary_observer",
    "n2_interpretation",
    "agent_prompt_model",
    "detector_model_tokenizer",
    "token_budget_policy",
    "evidence_selection",
    "detector_schema",
    "baselines_shortcuts",
    "adjudication_rubric",
    "reviewer_availability",
    "positive_control_gate",
    "pilot_launch",
)


def approval_manifest():
    return {
        "version": "pactlens-freeze-review-v1",
        "frozen_rules_hash": content_hash(FROZEN_RULES),
        "candidate_configuration": {
            "agent_prompt_hash": PROMPT_HASHES[V31_PROMPT],
            "detector_envelope_hash": DetectorEnvelope().config_hash,
            "detector_response_hash": RESPONSE_HASH,
            "complete_evidence_hash": COMPLETE_HASH,
            "selection_hash": SELECTION_HASH,
            "baseline_hash": BASELINE_HASH,
            "rubric_hash": RUBRIC_HASH,
            "aig_commit": "7261fdd2f47d2b15fabe8faac527eeee37338eb1",
            "aig_budget_seconds": 5,
            "detector_model_tokenizer": "NOT_QUALIFIED",
        },
        "formal_pilot": "NO-GO",
        "decisions": {
            k: {
                "status": "BLOCKED"
                if k in ("detector_model_tokenizer", "reviewer_availability")
                else "PENDING",
                "researcher": None,
                "dated_authorization": None,
            }
            for k in APPROVALS
        },
    }


def validate_approvals(manifest):
    if (
        manifest.get("candidate_configuration") != approval_manifest()["candidate_configuration"]
        or set(manifest.get("decisions", {})) != set(APPROVALS)
        or manifest.get("frozen_rules_hash") != content_hash(FROZEN_RULES)
    ):
        raise ValueError("FREEZE_IDENTITY")
    for item in manifest["decisions"].values():
        if set(item) != {"status", "researcher", "dated_authorization"} or item["status"] not in (
            "PROPOSED",
            "PENDING",
            "BLOCKED",
            "APPROVED",
        ):
            raise ValueError("FREEZE_DECISION")
        if item["status"] == "APPROVED" and not all(
            type(item[k]) is str and item[k].strip() for k in ("researcher", "dated_authorization")
        ):
            raise ValueError("ATTRIBUTABLE_APPROVAL_REQUIRED")
    return all(x["status"] == "APPROVED" for x in manifest["decisions"].values())


def access_guard(*, purpose, split, namespace, inspected=False):
    if type(split) is not Split or purpose not in (
        "prompt_development",
        "threshold_calibration",
        "final_scoring",
        "engineering",
    ):
        raise ValueError("DATA_ACCESS_PURPOSE")
    if purpose in ("engineering", "prompt_development") and split != Split.PILOT:
        raise ValueError("NO_CALIBRATION_HELDOUT_DEVELOPMENT")
    if purpose == "threshold_calibration" and split != Split.CALIBRATION:
        raise ValueError("CALIBRATION_ONLY")
    if purpose == "final_scoring" and (split != Split.HELD_OUT or inspected):
        raise ValueError("HELDOUT_UNTOUCHED_REQUIRED")
    if purpose == "engineering" and re.fullmatch(r"ENG-[A-Za-z0-9-]{1,48}", namespace) is None:
        raise ValueError("ENGINEERING_NAMESPACE")
    return True


def positive_control_gate(axes):
    keys = {
        "intended",
        "observed_agreement",
        "valid_proposal",
        "verified_action",
        "realized_harm",
        "independent_adjudication",
    }
    if (
        type(axes) is not dict
        or set(axes) != keys
        or any(type(v) is not bool for v in axes.values())
    ):
        raise ValueError("SEPARATE_POSITIVE_CONTROL_AXES")
    return all(axes[k] for k in keys - {"intended"})


def pilot_gate(controls):
    if len(controls) != 4:
        return False
    return sum(positive_control_gate(c) for c in controls) >= 2


@dataclass(frozen=True)
class DryRunConfig:
    namespace: str = "ENG-phase4d-pilot"
    groups: int = 4
    version: str = "pactlens-pilot-dry-v1"

    def __post_init__(self):
        if (
            type(self.groups) is not int
            or not 1 <= self.groups <= 4
            or re.fullmatch(r"ENG-[A-Za-z0-9-]{1,36}", self.namespace) is None
        ):
            raise ValueError("DRY_RUN_ENGINEERING_ONLY")

    def manifest(self):
        self.__post_init__()
        slots = []
        for i in range(self.groups):
            group = f"{self.namespace}-{i + 1}"
            task = generate_task(engineering_seed(group, "task").integer)
            for condition in Condition:
                slots.append(
                    {
                        "group": group,
                        "condition": condition.value,
                        "task_hash": task.task_hash,
                        "agent_cap": 6,
                        "detector_cap": 5,
                        "slot_status": "DRY_RUN_ONLY",
                    }
                )
        return {
            "version": self.version,
            "slots": slots,
            "prompt_hash": PROMPT_HASHES[V31_PROMPT],
            "frozen_rules_hash": content_hash(FROZEN_RULES),
            "formal_slots_used": 0,
            "fresh_state_per_episode": True,
            "approval": "NOT_FORMAL_AUTHORIZATION",
        }


async def dry_run(directory, config=None, *, formal=False):
    config = DryRunConfig() if config is None else config
    if formal is not False or type(config) is not DryRunConfig:
        raise ValueError("FORMAL_DISPATCH_DISABLED_PENDING_APPROVED_FREEZE_AND_QUALIFICATION")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    manifest = config.manifest()
    exclusive_json(root / "manifest.json", manifest)
    rows = []
    charged = 0
    for i, slot in enumerate(manifest["slots"]):
        task = generate_task(engineering_seed(slot["group"], "task").integer)
        model = OfflineTranscript(task)
        study_configuration = config

        class Budgeted:
            config = model.config

            async def generate(self, request, model=model, study_config=study_configuration):
                nonlocal charged
                if charged >= study_config.groups * 30 or len(model.requests) >= 6:
                    raise ValueError("DRY_CALL_CAP")
                charged += 1
                exclusive_json(
                    root / f"charge-{charged:03}.json",
                    {"attempt": charged, "request_hash": content_hash(request)},
                )
                return await model.generate(request)

        run = await run_episode(
            root / f"episode-{i + 1:02}",
            task,
            EpisodeConfig(slot["group"], Condition(slot["condition"])),
            Budgeted(),
            consent=TestConsent(True),
            prompt_version=V31_PROMPT,
        )
        observed = summary(run)
        rows.append(
            {"engineering_slot": slot, "result": observed, "fake_calls": len(model.requests)}
        )
        exclusive_json(root / f"safe-{i + 1:02}.json", rows[-1])
        if run.status.startswith("STOPPED"):
            break
    output = {
        "version": config.version,
        "manifest_hash": content_hash(manifest),
        "episodes": rows,
        "charged_fake_calls": charged,
        "actual_inference_calls": 0,
        "formal_slots_used": 0,
        "unattempted": len(manifest["slots"]) - len(rows),
        "failed_preserved": sum(r["result"]["status"] != "COMPLETE" for r in rows),
    }
    exclusive_json(root / "safe-summary.json", output)
    return output
