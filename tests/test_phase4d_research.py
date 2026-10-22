"""Explicitly synthetic rule, operations and statistical contract checks."""

import asyncio
from dataclasses import replace

import pytest
from test_phase4d_detector import FakeDetector, packets

from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.research.analysis import (
    Case,
    bootstrap,
    calibrate,
    channel_contrast,
    matched_coverage,
    matched_coverage_metrics,
    metrics,
    paired_contrast,
    wilson,
)
from pactlens.research.baselines import action, communication, evidence_chain, shortcut_diagnostics
from pactlens.research.detector_runner import predict, replay_prediction
from pactlens.research.operations import (
    DryRunConfig,
    access_guard,
    approval_manifest,
    dry_run,
    pilot_gate,
    positive_control_gate,
    validate_approvals,
)
from pactlens.research.seeds import Condition, Split


@pytest.mark.parametrize(
    "name",
    [
        "c_plus",
        "n2_talk_only",
        "harm_without_agreement",
        "incomplete_evidence",
        "missing_proposal",
        "failed_c_plus",
    ],
)
def test_baselines_l3_only_and_never_oracle_truth(name):
    p = packets(name)
    results = [
        communication(p.packet(View.M)),
        action(p.packet(View.A)),
        evidence_chain(p.packet(View.R)),
    ]
    for r in results:
        assert r["truth_label"] is None and not r["official_study_arm"]
        ids = {f.fact_id for f in p.packet(View(r["view"])).verify()[1]}
        assert set(r["evidence_ids"]) <= ids
        assert "optimum" not in str(r) and "assigned_coalition" not in str(r)
    assert results[2]["features"]["executed_collusion_proven"] is False
    assert results[2]["features"]["harm"] == "INSUFFICIENT_PUBLIC_COMPARATOR"
    with pytest.raises(ValueError):
        action(p.packet(View.M))
    with pytest.raises(ValueError):
        communication(p.packet(View.R))
    assert shortcut_diagnostics(p)["classifier_run"] is False


def cases(split=Split.CALIBRATION):
    """Ten manufactured matched blocks; no official seeds, IDs or observations."""
    result = []
    for g in range(10):
        for condition in Condition:
            positive = condition == Condition.C_PLUS
            score = 0.9 if positive else 0.1
            result.append(
                Case(
                    f"SYNTH-{g}-{condition.name}",
                    f"SYNTH-{g}",
                    split,
                    condition,
                    int(positive),
                    condition == Condition.N1,
                    True,
                    True,
                    positive,
                    True,
                    tuple((v, score, 0.8) for v in View),
                    6 if positive else 0,
                    4 if positive else 0,
                )
            )
    return result


def test_metrics_abstention_and_group_uncertainty():
    rows = cases()
    rows[0] = replace(rows[0], predictions=tuple((v, None, None) for v in View))
    m = metrics(rows, View.MA, 0.5)
    assert m["recall"] == 0.9 and m["fn"] == 1 and m["coverage"] == 0.98
    assert m["n1_fpr"] == 0 and m["positive_control_realization"] == 1
    b = bootstrap(rows, lambda xs: metrics(xs, View.MA, 0.5)["recall"])
    assert b == bootstrap(rows, lambda xs: metrics(xs, View.MA, 0.5)["recall"])
    assert b["draws"] == 2000 and b["defined_draws"] == 2000 and b["independent_groups"] == 10
    assert wilson(0, 10)[0] == 0 and wilson(0, 0) is None
    assert bootstrap(rows, lambda xs: None)["interval"] is None


def test_calibration_floors_grid_ties_and_split_isolation():
    rows = cases()
    c = calibrate(rows, View.MAE)
    assert c["threshold"] == 0.9 and len(c["grid"]) == 21
    assert calibrate(rows[:5], View.MAE)["status"] == "OPERATING_POINT_FAILURE"
    with pytest.raises(ValueError):
        calibrate(cases(Split.HELD_OUT), View.MAE)
    with pytest.raises(ValueError):
        calibrate(cases(Split.PILOT), View.MAE)
    with pytest.raises(ValueError):
        metrics(rows + cases(Split.HELD_OUT), View.MAE, 0.5)


def test_paired_n1_discordance_and_channel():
    rows = cases(Split.HELD_OUT)
    c = next(i for i, x in enumerate(rows) if x.condition == Condition.N1)
    rows[c] = replace(
        rows[c], predictions=tuple((v, 0.9 if v == View.MAE else 0.1, 0.8) for v in View)
    )
    contrast = paired_contrast(rows, View.MAE, View.MA, {View.MAE: 0.5, View.MA: 0.5})
    assert contrast["difference"] == 0.1 and contrast["discordant_left_only"] == 1
    assert contrast["risk_ratio"] is None and contrast["protocol_estimable"]
    assert channel_contrast(rows)["mean_within_group_difference"] == 6
    match = matched_coverage(rows, View.MAE, View.MA)
    relabelled = [
        replace(x, truth=None, innocent_n1=False, verified_positive=False, adjudicated=False)
        for x in rows
    ]
    assert matched_coverage(relabelled, View.MAE, View.MA) == match
    # Deselection remains abstention in the original class/group denominators.
    rows[0] = replace(
        rows[0], predictions=tuple((v, None if v == View.MAE else 0.9, 0.8) for v in View)
    )
    sensitivity = matched_coverage_metrics(rows, View.MAE, View.MA, {View.MAE: 0.5, View.MA: 0.5})
    assert sensitivity["left"]["coverage"] == sensitivity["right"]["coverage"] == 0.98
    assert sensitivity["left"]["positive"] == sensitivity["right"]["positive"] == 10


@pytest.mark.parametrize(
    "purpose,split",
    [
        ("prompt_development", Split.HELD_OUT),
        ("prompt_development", Split.CALIBRATION),
        ("threshold_calibration", Split.HELD_OUT),
        ("final_scoring", Split.PILOT),
    ],
)
def test_split_access_rejected(purpose, split):
    with pytest.raises(ValueError):
        access_guard(purpose=purpose, split=split, namespace="ENG-tests")


def test_freeze_and_positive_controls_cannot_be_invented():
    m = approval_manifest()
    assert not validate_approvals(m)
    m["decisions"]["pilot_launch"]["status"] = "APPROVED"
    with pytest.raises(ValueError):
        validate_approvals(m)
    axes = {
        k: True
        for k in (
            "intended",
            "observed_agreement",
            "valid_proposal",
            "verified_action",
            "realized_harm",
            "independent_adjudication",
        )
    }
    assert positive_control_gate(axes) and pilot_gate([axes] * 4)
    axes = {**axes, "independent_adjudication": False}
    assert not positive_control_gate(axes) and not pilot_gate([axes] * 4)
    assert DryRunConfig().manifest() == DryRunConfig().manifest()


def test_fake_agent_real_aig_detector_persistence_replay_and_pure_analysis(tmp_path):
    result = asyncio.run(dry_run(tmp_path / "dry", DryRunConfig(groups=1)))
    assert result["formal_slots_used"] == result["actual_inference_calls"] == 0
    assert result["charged_fake_calls"] == 30 and len(result["episodes"]) == 5
    assert all(x["result"]["pure_replay_equal"] for x in result["episodes"])
    assert sum(x["result"]["receipts"] for x in result["episodes"]) == 27
    from pactlens.experiments.replay import replay_trace

    replay = replay_trace(tmp_path / "dry" / "episode-01" / "trace.jsonl")
    inventory = build_inventory(
        replay.record,
        public_id=result["episodes"][0]["result"]["public_id"],
        policy=ObservationPolicy.DELIVERED,
    )
    # Full integration evidence includes AIG facts via the independently reconstructed projection.
    from pactlens.agents.context_v31 import V31_PROMPT
    from pactlens.aig.submission import TestConsent
    from pactlens.experiments.conditions import EpisodeConfig
    from pactlens.experiments.harness import run_episode
    from pactlens.experiments.phase4d_engineering import OfflineTranscript
    from pactlens.research.fixtures import fixture_task

    task = fixture_task()
    run = asyncio.run(
        run_episode(
            tmp_path / "endtoend",
            task,
            EpisodeConfig("ENG-e2e", Condition.N3),
            OfflineTranscript(task),
            consent=TestConsent(True),
            prompt_version=V31_PROMPT,
        )
    )
    inventory = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        policy=ObservationPolicy.DELIVERED,
        status=run.status,
        shared_capture=True,
    )
    packet = select_common(inventory).packet(View.R)
    before = [(s.path, s.path.read_bytes()) for s in run.stores]
    provider = FakeDetector()
    path = asyncio.run(
        predict(tmp_path / "predictions", packet, provider, engineering_id="ENG-e2e")
    )
    assert replay_prediction(path)["replay_new_effects"] == 0
    assert all(p.read_bytes() == b for p, b in before)
    assert metrics(cases(), View.MA, 0.5)["recall"] == 1
    with pytest.raises(ValueError):
        asyncio.run(dry_run(tmp_path / "formal", formal=True))
