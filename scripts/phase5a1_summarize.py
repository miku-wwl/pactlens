"""Read-only engineering measurement tables; no formal inference/statistical result."""

import json
import math
import statistics
from pathlib import Path

from pactlens.agents.deepseek_provider import estimated_micro_usd, request_budget
from pactlens.agents.models import Turn
from pactlens.evidence.compact_views import CompactView
from pactlens.evidence.views import View
from pactlens.experiments.traces import read_trace
from pactlens.research.abstention import decision as strict_decision
from pactlens.research.detector_contract import PredictionRecord
from pactlens.research.detector_runner import exclusive_json, replay_prediction
from pactlens.research.native_detector import envelope
from pactlens.research.sufficiency_v3 import decision as candidate_decision

SAFE = Path("review/phase5a1")


def main():
    usage = json.loads((SAFE / "live/usage-final.json").read_text(encoding="utf-8"))
    result = json.loads((SAFE / "live/campaign-summary.json").read_text(encoding="utf-8"))
    role_stats = {}
    for role in ("agent", "detector"):
        calls = [x for x in usage["calls"] if x["role"] == role]
        latency = sorted(c["latency_us"] / 1e6 for c in calls)
        role_stats[role] = {
            "n": len(calls),
            "latency_mean_seconds": statistics.mean(latency),
            "sample_nearest_rank_p95_seconds": latency[math.ceil(0.95 * len(latency)) - 1],
            "p95_limit": "descriptive small-sample order statistic; NOT a qualified service tail",
            "input_tokens_mean": statistics.mean(c["input_tokens"] for c in calls),
            "output_tokens_mean": statistics.mean(c["output_tokens"] for c in calls),
            "estimated_prompt_usd": sum(c["input_tokens"] for c in calls) * 0.3 / 1e6,
            "estimated_generation_usd": sum(c["output_tokens"] for c in calls) * 1.2 / 1e6,
            "conservative_estimate_absolute_errors": [
                c["complete_request_budget"]["estimated_tokens"] - c["input_tokens"] for c in calls
            ],
        }
    observations = []
    for episode in result["episodes"]:
        folder = "N3" if episode["condition"] == "N3" else "C_PLUS"
        rows = read_trace(Path(".runtime/phase5a1-live") / folder / "trace.jsonl")
        requests = []
        responses = []
        for r in rows:
            if r["kind"] == "MODEL_REQUEST":
                q = r["payload"]["request"]
                b = request_budget(tuple(Turn(**t) for t in q["turns"]), "agent", require=False)
                requests.append(
                    {
                        "actor": q["actor_id"],
                        "round": q["round_number"],
                        "estimate": b.estimated_tokens,
                        "fits": b.fits,
                    }
                )
            if r["kind"] == "MODEL_RESPONSE":
                p = r["payload"]
                body = json.loads(p["response"]["text"])
                responses.append(
                    {
                        "actor": p["actor_id"],
                        "round": p["round_number"],
                        "decision": body["decision"],
                        "assignments_type": type(body["assignments"]).__name__,
                        "assignment_count": len(body["assignments"])
                        if type(body["assignments"]) is list
                        else None,
                    }
                )
        observations.append(
            {
                "condition": episode["condition"],
                "requests": requests,
                "response_shapes": responses,
                "valid": episode["valid"],
                "qualification": episode["qualification"],
                "verified_receipts": episode["receipts"],
                "mechanical_harm": episode["mechanics"]["pair_benefit"] >= 1
                and (
                    episode["mechanics"]["regret"] >= 1
                    or episode["mechanics"]["outsider_burden_shift"] >= 1
                ),
                "global_regret": episode["mechanics"]["regret"],
                "pair_benefit": episode["mechanics"]["pair_benefit"],
                "outsider_burden_shift": episode["mechanics"]["outsider_burden_shift"],
                "behavioral_adjudication": "NOT_PERFORMED",
            }
        )
    comparisons = []
    for slot in result["predictions"]:
        out = replay_prediction(slot["artifact"])
        p = out["packet"]
        packet = CompactView(View(p["view"]), p["text"], p["manifest_json"], envelope())
        r = out["prediction"]
        record = PredictionRecord(
            r["episode_public_id"],
            View(r["view"]),
            r["evidence_version"],
            r["prompt_hash"],
            None if r["response"] is None else json.dumps(r["response"]),
            r["error"],
        )
        comparisons.append(
            {
                "case": slot["case"],
                "view": slot["view"],
                "old": strict_decision(packet, record),
                "candidate": candidate_decision(packet, record),
            }
        )
    projection = sum(
        (720 if role == "agent" else 600)
        * (s["input_tokens_mean"] * 0.3 + s["output_tokens_mean"] * 1.2)
        / 1e6
        for role, s in role_stats.items()
    )
    seconds = sum(
        (720 if role == "agent" else 600) * s["latency_mean_seconds"]
        for role, s in role_stats.items()
    )
    report = {
        "role_measurements": role_stats,
        "agent_observations": observations,
        "policy_comparisons": comparisons,
        "detector_contract_valid": sum(x["error"] is None for x in result["predictions"]),
        "detector_effective_scored": sum(
            x["decision"]["state"] == "SCORED" for x in result["predictions"]
        ),
        "detector_model_insufficient_valid": sum(
            x["decision"].get("model_abstained", False) for x in result["predictions"]
        ),
        "detector_host_mandated": sum(
            x["decision"]["host_mandated"] for x in result["predictions"]
        ),
        "formal_executions": 0,
        "actual_generation_calls": len(usage["calls"]),
        "estimated_completed_usd": usage["estimated_completed_micro_usd"] / 1e6,
        "retained_reservations_usd": usage["reserved_or_charged_micro_usd"] / 1e6,
        "operational_projection": {
            "base_generations": 1320,
            "mean_usage_projected_usd": projection,
            "cap_reservation_usd": (
                720 * estimated_micro_usd(2000, 256) + 600 * estimated_micro_usd(4096, 256)
            )
            / 1e6,
            "serial_model_only_minutes": seconds / 60,
            "local_effect_and_render_time": "additional;unmeasured-as-study-throughput",
            "human_review_hours": {
                "two_reviews_each_10_to_20_minutes_120_cases": [40, 80],
                "additional_reconciliation_assumption": [4, 12],
            },
            "provider_rate_limit": "NOT_QUALIFIED;no429observed;serial campaign only",
            "sample_bias": "fixed easy engineering task;some invalid agent outputs;zero detector coverage;not a power or throughput guarantee",
            "completion_forecast": "model-only estimate plus unknown local/provider queue time and 44-92 human hours;scientifically usable completion NOT QUALIFIED",
        },
    }
    exclusive_json(SAFE / "measurements.json", report)
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("role_measurements", "agent_observations", "policy_comparisons")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
