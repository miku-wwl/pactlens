"""Manufactured approval fixtures only; no formal dispatch is performed."""

import asyncio
import hashlib
import json
from datetime import UTC, datetime

import pytest

from pactlens.research.json_types import content_hash
from pactlens.research.seeds import Condition
from pactlens.research.study_launch import (
    freeze_candidate,
    launch_verified,
    schedule,
    verify_launch,
)

NOW = datetime(2026, 10, 24, tzinfo=UTC)


def seal(body):
    body["manifest_hash"] = content_hash({k: v for k, v in body.items() if k != "manifest_hash"})
    return body


def approved_fixture(root):
    (root / "docs").mkdir()
    (root / "src").mkdir()
    (root / "docs/EXPERIMENT_PLAN.md").write_text(
        "MANUFACTURED APPROVAL TEST; NOT THE REAL PROTOCOL"
    )
    body = freeze_candidate(root)
    body["status"] = "APPROVED"
    for d in body["decisions"].values():
        d.update(
            status="APPROVED",
            researcher="UNIT_TEST_NOT_OWNER",
            timestamp="2026-10-24T00:00:00Z",
            record="SYNTHETIC_TEST_RECORD",
        )
    for name, q in body["qualifications"].items():
        path = root / (name + ".json")
        path.write_text(json.dumps({"status": "GO", "provenance": "MANUFACTURED_GUARD_TEST_ONLY"}))
        q.update(status="GO", path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    start = root / "start.txt"
    start.write_text("SYNTHETIC_START_EVIDENCE_NOT_OFFICIAL_VERIFICATION")
    body["official_start_verification"] = {
        "source": "https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25",
        "verified_by": "UNIT_TEST_NOT_RESEARCHER",
        "verified_at": "2026-10-23T01:00:00Z",
        "starts_at": "2026-10-23T00:00:00Z",
        "evidence_path": "start.txt",
        "evidence_sha256": hashlib.sha256(start.read_bytes()).hexdigest(),
    }
    body["owner_authorization"] = {
        "operation": "RUN_FORMAL_PILOT_20_EPISODES_ONLY",
        "owner": "UNIT_TEST_NOT_OWNER",
        "record": "SYNTHETIC_TEST_ONLY",
        "configuration_hash": body["configuration_hash"],
        "maximum_usd": 1,
        "maximum_generations": 220,
        "accept_synthetic_sandbox_consent": True,
    }
    return seal(body)


def test_full_membership_no_execution_and_pairing():
    body = schedule("0" * 64)
    assert body == schedule("0" * 64)
    rows = body["slots"]
    assert len(rows) == 120 and len({r["group"] for r in rows}) == 24
    assert {
        s: sum(r["split"] == s for r in rows) for s in ("pilot", "calibration", "held_out")
    } == {"pilot": 20, "calibration": 50, "held_out": 50}
    assert len({r["store"] for r in rows}) == len({r["scope_namespace"] for r in rows}) == 120
    for group in {r["group"] for r in rows}:
        pair = [
            r
            for r in rows
            if r["group"] == group
            and r["condition"] in (Condition.C_PLUS.value, Condition.C_MINUS.value)
        ]
        assert len(pair) == 2 and pair[0]["exogenous_hash"] == pair[1]["exogenous_hash"]
    assert (
        body["planned_total_calls"] == 1320
        and body["formal_slots_used"] == body["inference_calls"] == 0
    )


@pytest.mark.parametrize(
    "failure",
    [
        "pending",
        "researcher",
        "qualification",
        "qualification_file",
        "source",
        "start",
        "future_start",
        "owner",
        "owner_identity",
        "owner_cost",
        "split",
        "calibration",
        "held_out",
        "schedule",
        "hash",
    ],
)
def test_every_gate_fails_before_provider_or_files(tmp_path, failure):
    body = approved_fixture(tmp_path)
    if failure == "pending":
        body["status"] = "PENDING"
    elif failure == "researcher":
        next(iter(body["decisions"].values()))["researcher"] = None
    elif failure == "qualification":
        body["qualifications"]["agent"]["status"] = "BLOCKED"
    elif failure == "qualification_file":
        (tmp_path / "agent.json").write_text("changed")
    elif failure == "source":
        (tmp_path / "src/new.py").write_text("changed=1")
    elif failure == "start":
        body["official_start_verification"] = None
    elif failure == "future_start":
        body["official_start_verification"]["starts_at"] = "2026-10-25T00:00:00Z"
    elif failure == "owner":
        body["owner_authorization"] = None
    elif failure == "owner_identity":
        body["owner_authorization"]["configuration_hash"] = "1" * 64
    elif failure == "owner_cost":
        body["owner_authorization"]["maximum_usd"] = True
    elif failure == "split":
        body["target_split"] = "held_out"
    elif failure == "calibration":
        body["calibration_locked"] = False
    elif failure == "held_out":
        body["held_out_locked"] = False
    elif failure == "schedule":
        body["schedule_hash"] = "1" * 64
    if failure != "hash":
        seal(body)
    else:
        body["status"] = "CHANGED"
    calls = []
    with pytest.raises((ValueError, KeyError)):
        asyncio.run(
            launch_verified(
                body,
                tmp_path,
                tmp_path / "never-created",
                lambda *a: calls.append(a),
                lambda *a: calls.append(a),
                now=NOW,
            )
        )
    assert not calls and not (tmp_path / "never-created").exists()


def test_positive_guard_contract_only_never_launch(tmp_path):
    body = approved_fixture(tmp_path)
    assert verify_launch(body, tmp_path, now=NOW)
    assert not (tmp_path / "episodes").exists()


def test_pending_real_candidate_no_formal_ledger(tmp_path):
    from pathlib import Path

    from pactlens.agents.deepseek_provider import CampaignLedger

    root = Path(__file__).resolve().parents[1]
    body = freeze_candidate(root)
    assert body == freeze_candidate(root)
    with pytest.raises(ValueError):
        CampaignLedger.authorized_pilot(tmp_path / "never.sqlite3", body, root)
    assert not (tmp_path / "never.sqlite3").exists()


def test_unknown_stops_mocked_dispatch_wiring_without_running_a_formal_episode(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from pactlens.experiments import harness

    body = approved_fixture(tmp_path)
    dispatched = []
    detector = []

    async def fake_harness(directory, task, config, provider, **kwargs):
        # Mock only: no provisioning, model generation, Action or formal trace.
        dispatched.append(config.episode.episode_id)
        trace = tmp_path / "MOCK_NOT_AN_EPISODE.txt"
        trace.write_text("MOCK DISPATCH CONTRACT ONLY")
        assert config.episode.split.value == "pilot" and kwargs["formal_permit"]
        return SimpleNamespace(status="STOPPED_UNKNOWN", trace_path=trace)

    monkeypatch.setattr(harness, "run_episode", fake_harness)
    result = asyncio.run(
        launch_verified(
            body,
            tmp_path,
            tmp_path / "mock-wiring",
            lambda _: None,
            lambda *a: detector.append(a),
            now=NOW,
        )
    )
    assert len(result) == len(dispatched) == 1 and detector == []
    with pytest.raises(FileExistsError):
        asyncio.run(
            launch_verified(
                body,
                tmp_path,
                tmp_path / "mock-wiring",
                lambda _: None,
                lambda *a: detector.append(a),
                now=NOW,
            )
        )
    assert len(dispatched) == 1
