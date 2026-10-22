"""Read-only qualification audit, descriptive exporter and pending freeze package."""

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from phase5a3_campaign import PRIVATE, SAFE, check_history, load_packet, sha

from pactlens.agents.budgets import CONTEXT_PROFILE, budget_hash
from pactlens.agents.deepseek_provider import AGENT_SCHEMA_V34
from pactlens.aig.consumer import load_store
from pactlens.arena.outcomes import evaluate_outcome
from pactlens.evidence.compact_views import verify_compact_parity
from pactlens.evidence.tight_views import citation_keys
from pactlens.evidence.views import View
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json, replay_prediction
from pactlens.research.reason_detector import schema_for
from pactlens.research.reporting import export_engineering_results
from pactlens.research.study_launch import code_hash, freeze_candidate, schedule, verify_launch
from pactlens.research.sufficiency_v3 import eligibility
from pactlens.serialization import canonical_json, content_hash, primitive


def main():
    check_history()
    result = json.loads((SAFE / "live/campaign-summary.json").read_text(encoding="utf-8"))
    usage = json.loads((SAFE / "live/usage-final.json").read_text(encoding="utf-8"))
    plan = json.loads((SAFE / "live/predeclared-plan.json").read_text(encoding="utf-8"))
    assert code_hash(Path.cwd()) == plan["source_hash_at_dispatch"]
    ledger = PRIVATE / "live/inference.sqlite3"
    with sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True) as db:
        actual = [
            {"call_id": n, **json.loads(meta), "retained_charge_micro_usd": charge}
            for n, meta, charge in db.execute("SELECT id,metadata,charge FROM calls ORDER BY id")
        ]
    assert actual == usage["calls"]
    assert usage["agent_requests"] <= 30 and usage["detector_requests"] <= 45
    assert (
        len(actual) <= 75
        and usage["reserved_or_charged_micro_usd"] <= usage["ceiling_micro_usd"] <= 2000000
    )
    assert len({r["identity"] for r in actual}) == len(actual)
    assert all(r["complete_request_budget"]["fits"] for r in actual)
    files = [p for p in PRIVATE.rglob("*") if p.is_file()]
    before = {str(p): sha(p) for p in files}
    scopes, receipts, durable = set(), set(), []
    for row in result["episodes"]:
        if "public_id" not in row:
            continue
        directory = PRIVATE / "live" / row["episode"]
        trace = directory / "trace.jsonl"
        rep = replay_trace(trace)
        rows = read_trace(trace)
        assert rep.model_calls == rep.new_effects == 0 and sha(trace) == row["trace_sha256"]
        observed = [r["payload"]["observation"] for r in rows if r["kind"] == "ACTION"]
        effects, proposals = [], []
        for actor in directory.glob("actor-*"):
            if not actor.is_dir():
                continue
            store = load_store(actor)
            scope = store.identity["binding"]["execution_scope"]
            assert scope not in scopes
            scopes.add(scope)
            for effect in store.committed():
                matches = [
                    o for o in observed if o["receipt_reference"] == effect.receipt_reference
                ]
                assert len(matches) == 1
                o = matches[0]
                assert (
                    o["authorized"]
                    and o["action_state"] == "Succeeded"
                    and o["receipt_status"] == "VERIFIED_COMMITTED"
                )
                assert o["payload_digest"] == effect.payload_digest and o[
                    "proposal_digest"
                ] == content_hash(effect.prepared.proposal)
                assert effect.receipt_reference not in receipts
                receipts.add(effect.receipt_reference)
                effects.append(
                    {
                        **o,
                        "effect_key": effect.effect_key,
                        "store_id": store.identity["store_id"],
                        "scope_sha256": content_hash(scope),
                    }
                )
                p = effect.prepared.proposal
                outcome = evaluate_outcome(
                    rep.record.state.task, p.allocation, tuple(row["roles"][:2])
                )
                proposals.append(
                    {
                        "actor": p.agent_id,
                        "round": p.round_number,
                        "would_be_harmful_if_realized": outcome.mechanical_harm,
                        "proposed_outcome": primitive(outcome),
                        "receipt": effect.receipt_reference,
                    }
                )
        assert len(effects) == len(observed) == row["receipts"]
        final = rep.record.state.final_allocation
        assert all(a.agent_id is not None for a in final.assignments)
        loads = Counter(a.agent_id for a in final.assignments if a.agent_id is not None)
        # This prospectively fixed task has three unit-work, unit-cost identical agents.
        independent = sum(n + n * n for n in loads.values())
        assert independent == row["mechanics"]["global_cost"]
        durable.append(
            {
                "case": row["episode"],
                "trace_sha256": sha(trace),
                "effects": effects,
                "committed_ballots": proposals,
                "independent_fixture_cost": independent,
                "failures": [r["payload"] for r in rows if r["kind"] == "MODEL_FAILURE"],
                "message_max_chars": max(
                    (
                        len(r["payload"]["delivery"]["text"])
                        for r in rows
                        if r["kind"] == "DELIVERY"
                    ),
                    default=0,
                ),
                "replay_calls": 0,
                "replay_effects": 0,
            }
        )
    assert before == {str(p): sha(p) for p in files}
    exclusive_json(
        SAFE / "aig-integrity.json",
        {
            "cases": durable,
            "verified_receipts": len(receipts),
            "distinct_scopes": len(scopes),
            "private_files_unchanged": True,
            "synthetic_consent_not_authenticated_human": True,
        },
    )
    rows, detail, coverage = [], [], defaultdict(Counter)
    lookup = {}
    for r in result["predictions"]:
        if r["status"] != "RECORDED":
            continue
        a = replay_prediction(r["artifact"])
        p = load_packet(r["case"], View(r["view"]))
        response = a["prediction"]["response"]
        detail.append(
            {
                **r,
                "model": a["config"]["model"],
                "budget_hash": a["config"]["budget_hash"],
                "schema_hash": a["prediction"]["schema_hash"],
                "envelope_hash": a["prediction"]["prompt_hash"],
                "response": response,
                "eligibility": eligibility(p),
                "new_semantic_prompt": False,
                "record_hash": a["record_hash"],
            }
        )
        rows.append(
            {
                "case": r["case"],
                "source_case": r["source_case"],
                "measurement_kind": r["kind"],
                "condition_operator_only": r["condition_operator_only"],
                "budget_profile": CONTEXT_PROFILE,
                "budget_hash": budget_hash(CONTEXT_PROFILE),
                "independent_truth": "PENDING_UNSIGNED",
                "artifact": r["artifact"],
            }
        )
        lookup[(r["case"], r["view"])] = a
        for key in (r["kind"] + "/" + r["view"], r["condition_operator_only"] + "/" + r["view"]):
            c = coverage[key]
            c["slots"] += 1
            c["eligible"] += eligibility(p)["eligible"]
            c["budget_fit"] += a["budget"]["fits"]
            c["dispatched"] += a["usage"] is not None
            c["contract_valid"] += a["prediction"]["error"] is None
            c[a["decision"]["state"]] += 1
            c["model_abstained"] += a["decision"]["model_abstained"]
            c["host_abstained"] += a["decision"]["host_mandated"]
    parity = []
    for case in dict.fromkeys(r["case"] for r in detail):
        r, m = load_packet(case, View.R), load_packet(case, View.MAE)
        assert verify_compact_parity(r, m)
        assert eligibility(r)["eligible"] == eligibility(m)["eligible"]
        parity.append(
            {
                "case": case,
                "equal_canonical_facts": True,
                "equal_eligibility": True,
                "retained_R_facts": len(r.verify()[1]),
                "retained_MAE_facts": len(m.verify()[1]),
                "omitted": 0,
            }
        )
    old = json.loads(Path("review/phase5a2/live/campaign-summary.json").read_text(encoding="utf-8"))
    paired = []
    for row in detail:
        if row["view"] != "MAE":
            continue
        if row["source_case"]:
            old_ma = next(
                x
                for x in old["predictions"]
                if x["case"] == row["source_case"] and x["view"] == "MA"
            )
            ma = replay_prediction(old_ma["artifact"])
            provenance = "CROSS_BUDGET_TIME_PAIR_TECHNICAL_ONLY_NOT_FORMAL"
        else:
            ma = lookup[(row["case"], "MA")]
            provenance = "SAME_NEW_PROFILE_MATCHED_ENGINEERING"
        mae = lookup[(row["case"], "MAE")]
        paired.append(
            {
                "case": row["case"],
                "provenance": provenance,
                "MA_score": ma["decision"]["effective_score"],
                "MAE_score": mae["decision"]["effective_score"],
                "joint_scored": ma["decision"]["state"] == mae["decision"]["state"] == "SCORED",
                "MA_usage": ma["usage"],
                "MAE_usage": mae["usage"],
                "MA_reason": (ma["prediction"]["response"] or {}).get("reason_code"),
                "MAE_reason": (mae["prediction"]["response"] or {}).get("reason_code"),
            }
        )
    export = export_engineering_results(rows, [r["artifact"] for r in rows], SAFE / "analysis")
    measurements = []
    for call in actual:
        role = call["role"]
        packet = None
        if role == "detector":
            case, view = call["context_id"].rsplit("-", 1)
            packet = load_packet(case, View(view))
            schema = schema_for(citation_keys(packet.text))
        else:
            schema = AGENT_SCHEMA_V34
        measurements.append(
            {
                "call_id": call["call_id"],
                "role": role,
                "context": call["context_id"],
                "complete_native_estimate": call["complete_request_budget"]["estimated_tokens"],
                "actual_input_tokens": call.get("input_tokens"),
                "actual_output_tokens": call.get("output_tokens"),
                "estimate_minus_actual": None
                if call.get("input_tokens") is None
                else call["complete_request_budget"]["estimated_tokens"] - call["input_tokens"],
                "native_wire_bytes": call["complete_request_budget"]["utf8_bytes"],
                "schema_utf8_bytes": len(canonical_json(schema).encode()),
                "latency_us": call.get("latency_us"),
                "estimated_micro_usd": call.get("estimated_actual_micro_usd"),
                "fits_previous_role_cap": call["complete_request_budget"]["estimated_tokens"]
                <= (2000 if role == "agent" else 4096),
                "new_role_cap": call["complete_request_budget"]["limit"],
            }
        )
        assert (call.get("input_tokens") or 0) <= call["complete_request_budget"]["limit"]
    exclusive_json(
        SAFE / "qualification-analysis.json",
        {
            "predictions": detail,
            "coverage": {k: dict(v) for k, v in coverage.items()},
            "parity": parity,
            "paired_MA_MAE": paired,
            "token_measurements": measurements,
            "export": export,
            "formal_statistics": False,
            "thresholds_selected": 0,
            "new_calls": 0,
        },
    )
    target = Path("research/phase5a3")
    target.mkdir(exist_ok=False)
    manifest = freeze_candidate(Path.cwd(), profile="phase5a3")
    exclusive_json(target / "freeze-candidate.json", manifest)
    exclusive_json(target / "schedule.json", schedule(manifest["configuration_hash"]))
    try:
        verify_launch(primitive(manifest), Path.cwd())
    except ValueError as error:
        assert str(error) == "FROZEN_APPROVALS_REQUIRED"
    else:
        raise AssertionError("PENDING_MANIFEST_MUST_FAIL_CLOSED")
    exclusive_json(
        SAFE / "pilot-dry-check.json",
        {
            "status": "EXPECTED_DENIAL_PASS",
            "reason": "FROZEN_APPROVALS_REQUIRED",
            "configuration_hash": manifest["configuration_hash"],
            "pending_decisions": 16,
            "formal_episodes": 0,
        },
    )
    check_history()
    print(
        json.dumps(
            {
                "calls": len(actual),
                "effective_scores": export["effective_scores"],
                "receipts": len(receipts),
                "parity_pairs": len(parity),
                "new_joint_MA_MAE": sum(
                    r["joint_scored"]
                    for r in paired
                    if r["provenance"] == "SAME_NEW_PROFILE_MATCHED_ENGINEERING"
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
