"""Exercise real L3/L4/replay and manufactured matched statistics, never formal data."""

import asyncio
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.research.analysis import Case, calibrate, metrics, paired_contrast
from pactlens.research.detector_runner import (
    analysis_prediction,
    exclusive_json,
    predict,
    replay_prediction,
)
from pactlens.research.fixtures import run_fixture
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.reporting import export_synthetic_results
from pactlens.research.reviewer_packets import prepare_reviewer_packets
from pactlens.research.seeds import Condition, Split


class FakeDetector:
    config = ModelConfig(
        "fake-detector", "synthetic-analysis-v1", seed_support="FAKE_DETERMINISTIC"
    )

    async def generate(self, request):
        return ModelResponse(
            canonical_json(
                {
                    "risk_score": 0.25,
                    "confidence": 0.8,
                    "adequacy": "ADEQUATE",
                    "evidence_ids": ["public-task"],
                    "rationale_short": "Manufactured software validation only.",
                }
            ),
            1,
            100,
            60,
            "stop",
        )


async def main():
    root = Path("review/phase4e5a/synthetic-analysis-complete")
    root.mkdir(parents=True, exist_ok=False)
    fixture = run_fixture("n3_cooperation")
    public_id = str(uuid4())
    selected = select_common(
        build_inventory(fixture.record, public_id=public_id, policy=ObservationPolicy.DELIVERED)
    )
    paths = []
    joined = []
    for view in View:
        path = await predict(
            root / "predictions",
            selected.packet(view),
            FakeDetector(),
            engineering_id="ENG-synthetic-analysis",
        )
        paths.append(path)
        joined.append(analysis_prediction(path))
        assert replay_prediction(path)["replay_new_effects"] == 0
    reviewers = prepare_reviewer_packets(fixture.record, public_id=public_id)
    exclusive_json(root / "blank-reviewers.json", reviewers)
    # This first join is the genuine software boundary; source capture/loss may
    # force abstention. Manufactured truth below is NEVER human adjudication.
    joined_case = Case(
        "SYNTH-boundary",
        "SYNTH-boundary",
        Split.CALIBRATION,
        Condition.N1,
        0,
        True,
        True,
        True,
        False,
        True,
        tuple(joined),
    )
    boundary = {v.value: metrics([joined_case], v, 0.5) for v in View}
    exclusive_json(root / "boundary-metrics.json", boundary)

    # Independent manufactured arrays exercise threshold selection and CI maths.
    # No official P/K/T ID, task, label or response is used in these arrays.
    def cases(split):
        return [
            Case(
                f"SYNTH-{split.value}-{g}-{c.name}",
                f"SYNTH-{g}",
                split,
                c,
                int(c == Condition.C_PLUS),
                c == Condition.N1,
                True,
                True,
                c == Condition.C_PLUS,
                True,
                tuple((v, 0.9 if c == Condition.C_PLUS else 0.1, 0.8) for v in View),
                6 if c == Condition.C_PLUS else 0,
                4 if c == Condition.C_PLUS else 0,
            )
            for g in range(10)
            for c in Condition
        ]

    calibration = cases(Split.CALIBRATION)
    heldout = cases(Split.HELD_OUT)
    thresholds = {v: calibrate(calibration, v)["threshold"] for v in View}
    assert all(x is not None for x in thresholds.values())
    heldout[0] = replace(heldout[0], predictions=tuple((v, None, None) for v in View))
    measurements = {v.value: metrics(heldout, v, thresholds[v]) for v in View}
    contrast = paired_contrast(heldout, View.MAE, View.MA, thresholds)
    assert measurements["MAE"]["coverage"] == 0.98 and measurements["MAE"]["recall"] == 0.9
    source = {
        "provenance": "SYNTHETIC_SOFTWARE_VALIDATION_ONLY",
        "boundary": boundary,
        "manufactured_thresholds": {v.value: t for v, t in thresholds.items()},
        "manufactured_metrics": measurements,
        "paired_contrast": contrast,
        "human_reviews": 0,
        "synthetic_adjudication_records": [
            {
                "episode": c.episode_id,
                "label": c.truth,
                "reviewer_A": "SYNTHETIC_FIXTURE_A",
                "reviewer_B": "SYNTHETIC_FIXTURE_B",
                "independent_human": False,
            }
            for c in heldout
        ],
        "boundary_prediction_files": [str(p) for p in paths],
    }
    exclusive_json(root / "sources.json", source)
    tables = {
        "condition-validity": [
            {"condition": c.value, "planned": 10, "executed": 10, "valid": 10} for c in Condition
        ],
        "positive-controls": [
            {"assigned": 10, "manufactured_positive": 10, "independent_human_positive": 0}
        ],
        "view-coverage": [
            {"view": v, "coverage": m["coverage"], "abstention": m["abstention_rate"]}
            for v, m in measurements.items()
        ],
        "fpr-recall": [
            {
                "view": v,
                "n1_fpr": m["n1_fpr"],
                "recall": m["recall"],
                "n1_denominator": m["primary_n1"],
            }
            for v, m in measurements.items()
        ],
        "ma-r-mae": [
            {
                "view": v,
                "n1_fpr": measurements[v]["n1_fpr"],
                "coverage": measurements[v]["coverage"],
            }
            for v in ("MA", "R", "MAE")
        ],
        "evidence-budget": [
            {
                "view": p.view.value,
                "estimated_tokens": json.loads(p.manifest_json)["budget"]["estimated_tokens"],
                "omitted": len(json.loads(p.manifest_json)["omitted"]),
            }
            for p in selected.packets
        ],
        "adjudicator-agreement": [
            {"manufactured_fixture_agreement": 1.0, "independent_human_reviews": 0, "kappa": None}
        ],
        "paired-confidence-intervals": [
            {
                "contrast": "N1 FPR MAE-MA",
                "difference": contrast["difference"],
                "interval": canonical_json(contrast["uncertainty"]),
                "unit": "matched_group",
            }
        ],
        "runtime-api-cost": [
            {
                "actual_api_calls": 0,
                "actual_api_usd": 0,
                "fake_latency_us": 1,
                "real_inference": False,
            }
        ],
    }
    source_path = root / "sources.json"
    body = {
        "provenance": "SYNTHETIC_SOFTWARE_VALIDATION_ONLY",
        "source_hashes": {"synthetic_source": hashlib.sha256(source_path.read_bytes()).hexdigest()},
        "tables": tables,
    }
    body["artifact_hash"] = content_hash(body)
    exclusive_json(root / "export.json", body)
    export_synthetic_results(
        root / "export.json", {"synthetic_source": source_path}, root / "tables"
    )
    print("SYNTHETIC_BOUNDARY_AND_STATISTICS_PASS_NO_RESEARCH_RESULTS")


if __name__ == "__main__":
    asyncio.run(main())
