"""Read-only engineering audit and existing exporter integration. Zero new inference."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from pactlens.agents.deepseek_provider import AGENT_SCHEMA_V34, request_budget
from pactlens.agents.models import Turn
from pactlens.aig.consumer import load_store
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.views import View
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.abstention import decision as historical_decision
from pactlens.research.detector_runner import exclusive_json, replay_prediction
from pactlens.research.reason_detector import ReasonPredictionRecord, envelope
from pactlens.research.reporting import export_engineering_results
from pactlens.research.sufficiency_v3 import eligibility
from pactlens.serialization import content_hash, primitive

ROOT = Path(__file__).resolve().parents[1]
SAFE = ROOT / "review/phase5a2"
PRIVATE = ROOT / ".runtime/phase5a2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = json.loads((SAFE / "live/campaign-summary.json").read_text(encoding="utf-8"))
    ledger = json.loads((SAFE / "live/usage-final.json").read_text(encoding="utf-8"))
    files = [p for p in PRIVATE.rglob("*") if p.is_file()]
    before = {str(p): sha(p) for p in files}
    scopes, stores, receipts = set(), set(), set()
    durable = []
    for parent in (PRIVATE / "controls", PRIVATE / "live"):
        for trace in sorted(parent.glob("*/trace.jsonl")):
            replay = replay_trace(trace)
            assert replay.model_calls == replay.new_effects == 0
            rows = read_trace(trace)
            observations = [r["payload"]["observation"] for r in rows if r["kind"] == "ACTION"]
            committed = []
            for directory in sorted(trace.parent.glob("actor-*")):
                if not directory.is_dir():
                    continue
                store = load_store(directory)
                identity = store.identity
                scope = identity["binding"]["execution_scope"]
                assert scope not in scopes and identity["store_id"] not in stores
                scopes.add(scope)
                stores.add(identity["store_id"])
                for effect in store.committed():
                    matches = [
                        o
                        for o in observations
                        if o["receipt_reference"] == effect.receipt_reference
                    ]
                    assert len(matches) == 1
                    observation = matches[0]
                    assert (
                        observation["action_state"] == "Succeeded"
                        and observation["authorized"]
                        and observation["receipt_status"] == "VERIFIED_COMMITTED"
                        and observation["payload_digest"] == effect.payload_digest
                        and observation["proposal_digest"] == content_hash(effect.prepared.proposal)
                        and effect.prepared.proposal.agent_id == identity["actor_id"]
                    )
                    assert effect.receipt_reference not in receipts
                    receipts.add(effect.receipt_reference)
                    committed.append(
                        {
                            "action_id": observation["action_id"],
                            "actor": observation["actor_id"],
                            "round": observation["round_number"],
                            "payload_digest": effect.payload_digest,
                            "proposal_digest": observation["proposal_digest"],
                            "receipt_reference": effect.receipt_reference,
                            "effect_key": effect.effect_key,
                            "scope_sha256": hashlib.sha256(scope.encode()).hexdigest(),
                            "store_id": identity["store_id"],
                            "authorized": True,
                            "state": "Succeeded",
                            "synthetic_consent": True,
                        }
                    )
            assert len(committed) == len(observations)
            native = []
            for row in rows:
                if row["kind"] == "MODEL_REQUEST":
                    r = row["payload"]["request"]
                    native.append(
                        {
                            "actor": r["actor_id"],
                            "round": r["round_number"],
                            "request_digest": row["payload"]["request_digest"],
                            "full_native_budget": primitive(
                                request_budget(
                                    tuple(Turn(**t) for t in r["turns"]),
                                    "agent",
                                    schema=AGENT_SCHEMA_V34,
                                    require=False,
                                )
                            ),
                        }
                    )
            durable.append(
                {
                    "case": trace.parent.name,
                    "trace_sha256": sha(trace),
                    "kind_counts": dict(Counter(r["kind"] for r in rows)),
                    "receipts": committed,
                    "native_agent_attempts": native,
                    "failures": [r["payload"] for r in rows if r["kind"] == "MODEL_FAILURE"],
                    "pure_replay": "PASS",
                    "replay_calls": 0,
                    "replay_new_effects": 0,
                }
            )
    assert before == {str(p): sha(p) for p in files}
    exclusive_json(
        SAFE / "aig-integrity.json",
        {
            "cases": durable,
            "distinct_scopes": len(scopes),
            "distinct_stores": len(stores),
            "verified_receipts": len(receipts),
            "private_bytes_unchanged": True,
            "core_seconds": 5,
            "new_calls": 0,
            "new_effects": 0,
            "public_replay_limit": "unkeyed consistency; no private durable stores in review ZIP",
        },
    )
    rows, details, parity = [], [], []
    for row in result["predictions"]:
        if row["status"] != "RECORDED":
            continue
        path = ROOT / row["artifact"]
        a = replay_prediction(path)
        p = a["packet"]
        packet = CompactView(View(p["view"]), p["text"], p["manifest_json"], envelope())
        response = a["prediction"]["response"]
        record = ReasonPredictionRecord(
            a["prediction"]["episode_public_id"],
            View(p["view"]),
            a["prediction"]["evidence_version"],
            a["prediction"]["prompt_hash"],
            None if response is None else json.dumps(response),
            a["prediction"]["error"],
        )
        historical = historical_decision(packet, record)
        details.append(
            {
                "case": row["case"],
                "view": row["view"],
                "artifact": row["artifact"],
                "model": a["config"]["model"],
                "prompt_hash": a["prediction"]["prompt_hash"],
                "schema_hash": a["prediction"]["schema_hash"],
                "budget": a["budget"],
                "usage": a["usage"],
                "response": response,
                "valid": a["prediction"]["error"] is None,
                "eligibility": eligibility(packet),
                "effective": a["decision"],
                "historical_policy_on_NEW_response": historical,
                "artifact_hash": a["artifact_hash"],
                "replay_calls": 0,
            }
        )
        rows.append(
            {
                "case": row["case"],
                "kind": row["kind"],
                "condition": row["condition"],
                "group": row["group"],
                "mechanical_harm": row["mechanical_harm"],
                "independent_truth": "PENDING_UNSIGNED",
                "artifact": row["artifact"],
            }
        )
    for name in dict.fromkeys(r["case"] for r in details):
        packets = {}
        for view in (View.R, View.MAE):
            raw = json.loads(
                (SAFE / "packets" / name / (view.value + ".json")).read_text(encoding="utf-8")
            )
            packets[view] = CompactView(view, raw["text"], raw["manifest_json"], envelope())
        assert verify_compact_parity(packets[View.R], packets[View.MAE])
        er, em = eligibility(packets[View.R]), eligibility(packets[View.MAE])
        assert er["eligible"] == em["eligible"]
        parity.append(
            {
                "case": name,
                "independent_parsed_parity": True,
                "eligibility_equal": True,
                "omitted_R": er["omitted"],
                "omitted_MAE": em["omitted"],
            }
        )
    export = export_engineering_results(rows, [r["artifact"] for r in rows], SAFE / "analysis")
    coverage = defaultdict(Counter)
    for row in details:
        for key in ("view:" + row["view"], "case:" + row["case"]):
            coverage[key]["attempted"] += 1
            coverage[key]["eligible"] += row["eligibility"]["eligible"]
            coverage[key]["sent"] += row["usage"] is not None
            coverage[key]["valid"] += row["valid"]
            coverage[key][row["effective"]["state"]] += 1
    assert ledger["agent_requests"] <= 60 and ledger["detector_requests"] <= 60
    assert ledger["reserved_or_charged_micro_usd"] <= ledger["ceiling_micro_usd"] <= 5000000
    assert len({r["identity"] for r in ledger["calls"]}) == len(ledger["calls"])
    assert all(r["status"] == "COMPLETED" for r in ledger["calls"])
    exclusive_json(
        SAFE / "detector-analysis.json",
        {
            "rows": details,
            "coverage": {k: dict(v) for k, v in coverage.items()},
            "parity": parity,
            "export": export,
            "ledger_integrity": "PASS",
            "new_model_calls": 0,
            "formal_episodes": 0,
            "thresholds_selected": 0,
            "historical_predictions_rewritten": 0,
        },
    )
    print(
        json.dumps(
            {
                "export": export,
                "coverage": {k: dict(v) for k, v in coverage.items() if k.startswith("view:")},
                "receipts": len(receipts),
                "calls": len(ledger["calls"]),
            }
        )
    )


if __name__ == "__main__":
    main()
