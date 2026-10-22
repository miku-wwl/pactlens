"""One frozen 4096/8192 engineering qualification. No retries or formal slots."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from phase5a2_campaign import Scripted, run_summary

from pactlens.agents.budgets import CONTEXT_PROFILE, V35_PROMPT, budget_contract, budget_hash
from pactlens.agents.deepseek_provider import (
    AGENT_SCHEMA_V34,
    CampaignLedger,
    DeepSeekProvider,
    available_models,
    profile_5a3,
    request_budget,
)
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.submission import TestConsent
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.inventory import Inventory, build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.context_profile import envelope, full_packets
from pactlens.research.detector_runner import exclusive_json, predict, replay_prediction
from pactlens.research.fixtures import fixture_task
from pactlens.research.mechanical_control import search
from pactlens.research.reason_detector import envelope as legacy_envelope
from pactlens.research.reviewer_packets import prepare_reviewer_packets
from pactlens.research.seeds import Condition
from pactlens.research.study_launch import code_hash
from pactlens.research.sufficiency_v3 import VERSION, eligibility
from pactlens.serialization import content_hash, primitive

SAFE = Path("review/phase5a3")
PRIVATE = Path(".runtime/phase5a3")
GROUP = "ENG-5a3-block1"
ORDER = (Condition.N3, Condition.C_PLUS, Condition.N1, Condition.N2, Condition.C_MINUS)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name(condition):
    return GROUP + "-" + condition.name


def old_result():
    return json.loads(
        Path("review/phase5a2/live/campaign-summary.json").read_text(encoding="utf-8")
    )


def historical_name(old):
    return "ENG-5a3-hist-" + old.removeprefix("ENG-5a2-")


def design():
    task = fixture_task()
    config = EpisodeConfig(GROUP, Condition.C_PLUS)
    agents = [name(c) for c in ORDER]
    historical = [r["episode"] for r in old_result()["episodes"]]
    detectors = [historical_name(n) + "-" + v.value for n in historical for v in (View.R, View.MAE)]
    detectors += [n + "-" + v.value for n in agents for v in View]
    body = {
        "version": "phase5a3-engineering-design-v1",
        "group": GROUP,
        "task_hash": task.task_hash,
        "task_generation": "unchanged original fixture;fresh engineering context;not new task diversity",
        "roles": config.roles(task),
        "condition_order": [c.name for c in ORDER],
        "agent_contexts": agents,
        "detector_contexts": detectors,
        "historical_cases": historical,
        "seeds": {
            c.name: [
                EpisodeConfig(GROUP, c).seed(a, r, task) for r in (1, 2) for a in config.roles(task)
            ]
            for c in ORDER
        },
        "provider": profile_5a3(),
        "prompt_version": V35_PROMPT,
        "agent_prompt_hash": PROMPT_HASHES[V35_PROMPT],
        "detector_envelope_hash": envelope().config_hash,
        "budget_contract": budget_contract(CONTEXT_PROFILE),
        "budget_hash": budget_hash(CONTEXT_PROFILE),
        "selection": "all permitted source facts;no omissions;no truncation",
        "sufficiency": VERSION,
        "observer": ObservationPolicy.DELIVERED.value,
        "hypothesis": "budget-only change supports complete multi-round generation and full evidence;no semantic prompt tuning",
        "limits": {
            "agent": 30,
            "historical_detector": 20,
            "new_detector": 25,
            "optional_control": 0,
            "total": 75,
            "usd": 2,
        },
        "optional_control": "no new semantic protocol/hypothesis;S1 already fit old cap;offline replay only",
        "continuation": "fixed cases only;invalid output retained;no retry;provider integrity/Unknown stops affected role;ineligible source is unsent",
        "formal_episodes": 0,
        "human_approvals": 0,
    }
    return primitive({**body, "design_hash": content_hash(body)})


def persist_packets(case, inventory):
    packets = full_packets(inventory)
    assert verify_compact_parity(packets[3], packets[4])
    assert eligibility(packets[3])["eligible"] == eligibility(packets[4])["eligible"]
    directory = SAFE / "packets" / case
    directory.mkdir(parents=True, exist_ok=False)
    for p in packets:
        exclusive_json(
            directory / (p.view.value + ".json"), {"text": p.text, "manifest_json": p.manifest_json}
        )
    return packets


def load_packet(case, view):
    b = json.loads((SAFE / "packets" / case / (view.value + ".json")).read_text(encoding="utf-8"))
    return CompactView(view, b["text"], b["manifest_json"], envelope())


def check_history():
    b = json.loads((SAFE / "historical-source-verification.json").read_text(encoding="utf-8"))
    assert all(sha(Path(n)) == digest for n, digest in b["files_sha256"].items())


async def prepare():
    PRIVATE.mkdir(parents=True, exist_ok=False)
    saved = design()
    exclusive_json(SAFE / "design.json", saved)
    old = old_result()
    files = [
        p
        for base in (Path("review/phase5a2"), Path("research/phase5a2"))
        for p in base.rglob("*")
        if p.is_file()
    ]
    historical_rows = []
    for row in old["episodes"]:
        original = row["episode"]
        trace = Path(".runtime/phase5a2/live") / original / "trace.jsonl"
        if trace.exists():
            assert sha(trace) == row["trace_sha256"]
            assert replay_trace(trace).model_calls == 0
            files.append(trace)
        b = json.loads(
            (Path("review/phase5a2/packets") / original / "R.json").read_text(encoding="utf-8")
        )
        previous = CompactView(View.R, b["text"], b["manifest_json"], legacy_envelope())
        h, facts = previous.verify()
        inv = Inventory(h["episode"], ObservationPolicy(h["policy"]), facts)
        packets = persist_packets(historical_name(original), inv)
        assert packets[3].verify()[1] == facts
        historical_rows.append(
            {
                "source_case": original,
                "new_namespace": historical_name(original),
                "source_trace_sha256": row["trace_sha256"],
                "original_status": row["status"],
                "condition_operator_only": row["condition"],
                "views": [
                    {
                        "view": p.view.value,
                        "budget": primitive(p.envelope.budget(p.text)),
                        "eligibility": eligibility(p),
                    }
                    for p in packets
                    if p.view in (View.R, View.MAE)
                ],
            }
        )
    exclusive_json(
        SAFE / "historical-source-verification.json",
        {
            "files_sha256": {p.as_posix(): sha(p) for p in files},
            "cases": historical_rows,
            "new_agent_calls": 0,
            "inference_calls": 0,
        },
    )
    task = fixture_task()
    proof = search(task, EpisodeConfig(GROUP, Condition.C_PLUS).roles(task)[:2])
    assert proof["status"] == "HARMFUL_ALLOCATION_MECHANICALLY_FEASIBLE"
    exclusive_json(SAFE / "mechanical-feasibility.json", proof)
    offline = []
    for c in ORDER:
        config = EpisodeConfig(GROUP, c)
        model = Scripted(task, "witness", config, message_size=256)
        run = await run_episode(
            PRIVATE / "offline" / name(c),
            task,
            config,
            model,
            consent=TestConsent(True),
            prompt_version=V35_PROMPT,
        )
        assert run.status == "COMPLETE"
        budgets = [
            primitive(
                request_budget(
                    r.turns,
                    "agent",
                    schema=AGENT_SCHEMA_V34,
                    profile=CONTEXT_PROFILE,
                    require=False,
                )
            )
            for r in model.requests
        ]
        assert len(model.requests) == 6 and all(b["fits"] for b in budgets)
        offline.append(
            {"case": name(c), "origin": "DETERMINISTIC_OFFLINE_NOT_LLM", "budgets": budgets}
        )
    exclusive_json(
        SAFE / "offline-preflight.json",
        {"all_six_fit": True, "max_message_chars": 256, "cases": offline, "paid_calls": 0},
    )
    check_history()
    print("PREPARED_FIVE_CONDITIONS_AND_TEN_HISTORICAL_FULL_RECORDS", flush=True)


async def execute(allow):
    if allow != "phase5a3-max75-usd2":
        raise ValueError("EXPLICIT_ENGINEERING_ALLOWANCE_REQUIRED")
    saved = json.loads((SAFE / "design.json").read_text(encoding="utf-8"))
    assert saved == design()
    assert (SAFE / "logs/focused-tests-exit.txt").read_text().strip() == "0"
    check_history()
    live = PRIVATE / "live"
    live.mkdir(exist_ok=False)
    folder = SAFE / "live"
    folder.mkdir(exist_ok=False)
    plan = {
        **saved,
        "source_hash_at_dispatch": code_hash(Path.cwd()),
        "historical_packet_hashes": {
            p.relative_to(SAFE).as_posix(): sha(p) for p in (SAFE / "packets").rglob("*.json")
        },
    }
    plan["dispatch_hash"] = content_hash(plan)
    exclusive_json(folder / "predeclared-plan.json", plan)
    ledger = CampaignLedger.phase5a3(
        live / "inference.sqlite3", saved["agent_contexts"], saved["detector_contexts"]
    )
    result = {
        "episodes": [],
        "predictions": [],
        "formal_executions": 0,
        "independent_human_reviews": 0,
    }
    detector_stopped, agent_stopped = False, False

    async def detect(case, views, kind, condition=None, source=None):
        nonlocal detector_stopped
        for v in views:
            if detector_stopped:
                result["predictions"].append(
                    {"case": case, "view": v.value, "status": "NOT_RUN_PROVIDER_STOP"}
                )
                continue
            packet = load_packet(case, v)
            provider = DeepSeekProvider(
                ledger, "detector", context_id=case + "-" + v.value, profile="phase5a3"
            )
            path = await predict(
                folder / "predictions",
                packet,
                provider,
                engineering_id=case.replace("_", "-"),
                sufficiency_policy=VERSION,
            )
            body = replay_prediction(path)
            result["predictions"].append(
                {
                    "case": case,
                    "source_case": source,
                    "kind": kind,
                    "view": v.value,
                    "condition_operator_only": condition,
                    "artifact": path.as_posix(),
                    "status": "RECORDED",
                    "error": body["prediction"]["error"],
                    "decision": body["decision"],
                    "usage": body["usage"],
                    "budget": body["budget"],
                    "diagnostic": body["validation_diagnostic"],
                }
            )
            print(case, v.value, body["decision"]["state"], body["prediction"]["error"], flush=True)
            if provider.blocked and body["provider_error"] not in (
                None,
                "INVALID_MODEL_JSON",
                "OUTPUT_SCHEMA_BUDGET_INFEASIBLE",
            ):
                detector_stopped = True

    try:
        models = available_models()
        exclusive_json(
            folder / "metadata.json", {"metadata_GET": 1, "models": models, "paid_generations": 0}
        )
        assert "deepseek-flash" in models
        for old in old_result()["episodes"]:
            await detect(
                historical_name(old["episode"]),
                (View.R, View.MAE),
                "NEW_MEASUREMENT_OF_HISTORICAL_EPISODE_NOT_NEW_EPISODE",
                old["condition"],
                old["episode"],
            )
        task = fixture_task()
        for c in ORDER:
            case = name(c)
            if agent_stopped:
                result["episodes"].append({"episode": case, "status": "NOT_RUN_INTEGRITY_STOP"})
                continue
            provider = DeepSeekProvider(ledger, "agent", context_id=case, profile="phase5a3")
            config = EpisodeConfig(GROUP, c)
            run = await run_episode(
                live / case,
                task,
                config,
                provider,
                consent=TestConsent(True),
                prompt_version=V35_PROMPT,
            )
            row = {
                "episode": case,
                **run_summary(run, config, "REAL_DEEPSEEK_AGENT"),
                "budget_hash": budget_hash(CONTEXT_PROFILE),
            }
            result["episodes"].append(row)
            exclusive_json(folder / (case + ".json"), row)
            inv = build_inventory(
                run.record,
                run.observations,
                run.deliveries,
                public_id=run.public_id,
                policy=ObservationPolicy.DELIVERED,
                status=run.status,
                shared_capture=True,
            )
            persist_packets(case, inv)
            reviewers = prepare_reviewer_packets(
                run.record,
                run.observations,
                run.deliveries,
                public_id=run.public_id,
                status=run.status,
                shared_capture=True,
            )
            directory = folder / "reviewers" / run.public_id
            directory.mkdir(parents=True)
            for key in ("reviewer_A", "reviewer_B", "reconciliation"):
                exclusive_json(directory / (key + ".json"), reviewers[key])
            print(
                case,
                row["status"],
                row["valid"],
                row["receipts"],
                row["mechanical_harm"],
                flush=True,
            )
            await detect(case, tuple(View), "GENUINE_NEW_ENGINEERING_EPISODE", c.value)
            rows = read_trace(run.trace_path)
            agent_stopped = "Unknown" in row["action_states"] or any(
                r["payload"].get("submission_failures") for r in rows
            )
            if provider.blocked:
                last = next(
                    (x for x in reversed(ledger.report()["calls"]) if x.get("context_id") == case),
                    None,
                )
                if (
                    last
                    and last["status"] != "COMPLETED"
                    and last.get("error")
                    not in ("INVALID_MODEL_JSON", "OUTPUT_SCHEMA_BUDGET_INFEASIBLE")
                ):
                    agent_stopped = True
    finally:
        exclusive_json(folder / "usage-final.json", ledger.report())
        exclusive_json(folder / "campaign-summary.json", result)
        check_history()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--execute")
    args = parser.parse_args()
    asyncio.run(prepare() if args.prepare and args.execute is None else execute(args.execute))
