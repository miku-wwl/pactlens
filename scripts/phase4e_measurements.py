"""Read-only engineering measurement, parity, failure-shape and feasibility report."""

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean

from pactlens.agents.deepseek_provider import request_budget
from pactlens.agents.models import Turn, closed_json
from pactlens.evidence.compact_views import CompactView
from pactlens.evidence.views import View
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.detector_runner import exclusive_json


def main():
    root = Path.cwd()
    safe = root / "review/phase4e5a"
    usage = json.loads((safe / "live/usage-final.json").read_text(encoding="utf-8"))
    campaign = json.loads((safe / "live/campaign-summary.json").read_text(encoding="utf-8"))
    calls = usage["calls"]

    def stats(role):
        rows = [c for c in calls if c["role"] == role]
        latency = sorted(c["latency_us"] / 1e6 for c in rows)
        return {
            "n": len(rows),
            "mean_seconds": mean(latency),
            "empirical_p95_seconds": latency[math.ceil(0.95 * len(latency)) - 1],
            "mean_input_tokens": mean(c["input_tokens"] for c in rows),
            "mean_output_tokens": mean(c["output_tokens"] for c in rows),
            "mean_estimated_usd": mean(c["estimated_actual_micro_usd"] for c in rows) / 1e6,
            "failure_or_unknown": sum(c["status"] != "COMPLETED" for c in rows),
        }

    roles = {r: stats(r) for r in ("agent", "detector")}
    full = []
    for policy in ("DELIVERED", "ROUTER_AUDIT"):
        for view in View:
            stem = safe / "full-six-action" / (policy + "-" + view.value)
            packet = CompactView(
                view,
                stem.with_suffix(".txt").read_text(encoding="utf-8"),
                stem.with_suffix(".manifest.json").read_text(encoding="utf-8"),
                DetectorEnvelope(),
            )
            _, facts = packet.verify()
            full.append(
                {
                    "policy": policy,
                    "view": view.value,
                    "fact_count": len(facts),
                    "legacy_envelope_estimate": packet.envelope.budget(
                        packet.text
                    ).estimated_tokens,
                    "complete_native_request_estimate": request_budget(
                        packet.envelope.turns(packet.text), "detector", require=False
                    ).estimated_tokens,
                    "exact_tokens": None,
                    "exact_tokenizer_qualified": False,
                    "all_source_facts_retained": True,
                }
            )
    source = root / ".runtime/phase4e5a-live/N3/trace.jsonl"
    budgets = []
    for row in read_trace(source):
        if row["kind"] == "MODEL_REQUEST":
            r = row["payload"]["request"]
            turns = tuple(Turn(**t) for t in r["turns"])
            b = request_budget(turns, "agent", require=False)
            budgets.append(
                {
                    "actor": r["actor_id"],
                    "round": r["round_number"],
                    "complete_request_estimate": b.estimated_tokens,
                    "fits": b.fits,
                    "legacy_turn_estimate": r["token_budget"]["estimated_tokens"],
                }
            )
    historical = []
    old = root / ".runtime/phase4d-v31/ENG-phase4d-v31-N3/trace.jsonl"
    for row in read_trace(old):
        if row["kind"] == "MODEL_RESPONSE":
            try:
                body = closed_json(row["payload"]["response"]["text"], 4096)
                assignments = body.get("assignments")
                shape = (
                    "null"
                    if assignments is None
                    else "pair-array"
                    if all(type(x) is list for x in assignments)
                    else "object-array"
                )
                historical.append({"decision": body.get("decision"), "assignment_shape": shape})
            except (ValueError, TypeError):
                historical.append({"shape": "INVALID_JSON"})
    report = {
        "provenance": "ENGINEERING_MEASUREMENTS_NOT_RESEARCH_RESULTS",
        "authenticated_metadata_requests": 1,
        "actual_generation_requests": len(calls),
        "actual_http_requests": len(calls) + 1,
        "role_statistics": roles,
        "actual_agent_request_budgets": budgets,
        "historical_v31_shapes": dict(Counter(json.dumps(x, sort_keys=True) for x in historical)),
        "full_evidence": full,
        "detector_attempted_packets": len(campaign["detector_predictions"]),
        "detector_errors": dict(
            Counter(
                x["prediction_error"] or "HOST_VALID_SCHEMA_AND_CITATIONS"
                for x in campaign["detector_predictions"]
            )
        ),
        "detector_scored": sum(
            x["decision"]["state"] == "SCORED" for x in campaign["detector_predictions"]
        ),
        "unused_predeclared_detector_packets": 15 - len(campaign["detector_predictions"]),
        "projected_full_study": {
            "agent_calls": 720,
            "detector_calls": 600,
            "total_calls": 1320,
            "input_cap_tokens": 3897600,
            "output_cap_tokens": 337920,
            "peak_cache_miss_token_cap_usd": 1.574784,
            "rounded_per_call_reservation_usd": 1.575360,
            "small_sample_mean_latency_minutes": (
                720 * roles["agent"]["mean_seconds"] + 600 * roles["detector"]["mean_seconds"]
            )
            / 60,
            "small_sample_p95_latency_minutes": (
                720 * roles["agent"]["empirical_p95_seconds"]
                + 600 * roles["detector"]["empirical_p95_seconds"]
            )
            / 60,
            "small_sample_mean_usage_usd": 720 * roles["agent"]["mean_estimated_usd"]
            + 600 * roles["detector"]["mean_estimated_usd"],
            "timeout_sensitivity_hours": 22,
            "maximum_authorized_model_hours_future": 8,
            "reviewer_person_hours_at_4_to_8_minutes_per_pass": [16, 32],
            "pilot_reviewer_person_hours": [40 * 4 / 60, 40 * 8 / 60],
            "feasibility": "NOT_QUALIFIED_BUDGET_FAILURES_AND_TINY_SAMPLE; NO_FORMAL_SPEND_AUTHORIZATION",
        },
        "estimated_usage_usd": usage["estimated_completed_micro_usd"] / 1e6,
        "retained_reservations_usd": usage["reserved_or_charged_micro_usd"] / 1e6,
    }
    exclusive_json(safe / "measurements.json", report)
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k
                in (
                    "actual_generation_requests",
                    "estimated_usage_usd",
                    "retained_reservations_usd",
                    "role_statistics",
                    "detector_errors",
                    "detector_scored",
                    "projected_full_study",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
