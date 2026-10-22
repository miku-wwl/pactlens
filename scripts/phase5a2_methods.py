"""Prospective policy comparisons and blocked Pilot candidate; no inference/effects."""

import json
from pathlib import Path

from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.inventory import Inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import BOUNDARY_TYPES, select_common
from pactlens.evidence.tight_views import render
from pactlens.evidence.views import View
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.reason_detector import envelope
from pactlens.research.study_launch import code_hash, freeze_candidate, schedule, verify_launch
from pactlens.research.sufficiency_v3 import eligibility
from pactlens.serialization import primitive

ROOT = Path(__file__).resolve().parents[1]
SAFE = ROOT / "review/phase5a2"


def main():
    comparisons = []
    for directory in sorted((SAFE / "packets").iterdir()):
        raw = json.loads((directory / "R.json").read_text(encoding="utf-8"))
        packet = CompactView(View.R, raw["text"], raw["manifest_json"], envelope())
        h, facts = packet.verify()
        inv = Inventory(h["episode"], ObservationPolicy(h["policy"]), facts)
        selected = select_common(inv, envelope=envelope(), renderer=render)
        minimal = {
            f.fact_id
            for f in facts
            if f.kind != "arena_event" or json.loads(f.payload_json)["type"] in BOUNDARY_TYPES
        }
        redundant = [render(inv, minimal, minimal, "0" * 64, v, envelope()) for v in View]
        assert verify_compact_parity(redundant[3], redundant[4])
        comparisons.append(
            {
                "case": directory.name,
                "complete_R_budget": primitive(packet.envelope.budget(packet.text)),
                "common_selector": [
                    {
                        "view": p.view.value,
                        "eligibility": eligibility(p),
                        "budget": primitive(p.envelope.budget(p.text)),
                    }
                    for p in selected.packets
                ],
                "only_redundant_chronology_removed": [
                    {
                        "view": p.view.value,
                        "eligibility": eligibility(p),
                        "budget": primitive(p.envelope.budget(p.text)),
                    }
                    for p in redundant
                ],
                "paid_campaign_policy_changed": False,
            }
        )
    comparison_path = SAFE / "policy-counterfactuals.json"
    comparison_body = {
        "scope": "OFFLINE_COVERAGE_ONLY_NO_COUNTERFACTUAL_MODEL_SCORES",
        "cases": comparisons,
        "inference_calls": 0,
        "formal_adoption": "PENDING",
    }
    if comparison_path.exists():
        assert json.loads(comparison_path.read_text(encoding="utf-8")) == comparison_body
    else:
        exclusive_json(comparison_path, comparison_body)
    dispatch = json.loads((SAFE / "live/predeclared-plan.json").read_text(encoding="utf-8"))
    assert code_hash(ROOT) == dispatch["source_hash_at_dispatch"]
    manifest = freeze_candidate(ROOT, profile="phase5a2")
    try:
        verify_launch(primitive(manifest), ROOT)
    except ValueError as error:
        denial = str(error)
    else:
        raise AssertionError("PENDING_CANDIDATE_MUST_NOT_LAUNCH")
    (ROOT / "research/phase5a2").mkdir(exist_ok=True)
    exclusive_json(ROOT / "research/phase5a2/freeze-candidate.json", manifest)
    exclusive_json(
        ROOT / "research/phase5a2/schedule.json", schedule(manifest["configuration_hash"])
    )
    exclusive_json(
        SAFE / "pilot-dry-check.json",
        {
            "status": "EXPECTED_DENIAL_PASS",
            "reason": denial,
            "formal_episodes": 0,
            "generation_calls": 0,
            "source_unchanged_since_dispatch": True,
            "pending_decisions": len(manifest["decisions"]),
            "exact_permission": "RUN_FORMAL_PILOT_20_EPISODES_ONLY",
            "no_owner_permission_inferred_from_engineering": True,
        },
    )
    print(json.dumps({"cases": len(comparisons), "pilot": denial, "formal_executions": 0}))


if __name__ == "__main__":
    main()
