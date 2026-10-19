"""Phase 4C candidates stay unapproved; readiness gates stay separate."""

import pytest

from pactlens.agents.prompts import CANDIDATE_PROMPT, LEGACY_PROMPT, PROMPT_HASHES, SYSTEM
from pactlens.agents.protocol_diagnostics import PROTOCOL_HASH
from pactlens.evidence.budget_selection import CONFIG_HASH
from pactlens.research.phase4c_candidates import candidates, readiness
from pactlens.serialization import content_hash

# Phase 4B freeze-candidate values (docs/PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md).
PHASE4B_V2_PROMPT_HASH = "172bbe6f06dd39fb91cc8070b01baadb0dd84123037ae807519e2a4e709ec8da"
PHASE4B_PROTOCOL_HASH = "3f982b1c7b217e785c3d9416c1d47859ea4497367838cc3eb50903c72f7dc3b0"
PHASE4B_SELECTION_HASH = "ca0006424a181f7f96554eef167c8142267ea012fbcea816f8a158f0346e7032"


def test_historical_candidate_hashes_are_unchanged():
    assert PROMPT_HASHES[CANDIDATE_PROMPT] == PHASE4B_V2_PROMPT_HASH
    assert PROMPT_HASHES[LEGACY_PROMPT] == content_hash(SYSTEM)
    assert PROTOCOL_HASH == PHASE4B_PROTOCOL_HASH
    assert CONFIG_HASH == PHASE4B_SELECTION_HASH


def test_candidate_record_is_deterministic_and_never_approved():
    first, second = candidates(), candidates()
    assert first == second and first["status"] == "CANDIDATES_NOT_APPROVED"
    statuses = {d["status"] for d in first["decisions"].values()}
    assert not any(s == "APPROVED" for s in statuses)
    assert first["decisions"]["formal_pilot"]["status"] == "NO-GO"
    assert first["agent"]["input_limit"] == 2000 and first["evidence"]["input_limit"] == 4096


@pytest.mark.parametrize(
    ("offline", "live", "expected"),
    [
        ({"representative_paths_fit": False}, {"status": "NOT_RUN"}, "BLOCKED"),
        ({"representative_paths_fit": True}, {"status": "NOT_RUN"}, "PARTIAL"),
        (
            {"representative_paths_fit": True},
            {"status": "INCOMPLETE", "input_budget_failures": 1},
            "BLOCKED",
        ),
        (
            {"representative_paths_fit": True},
            {"status": "COMPLETE", "input_budget_failures": 0, "valid_outputs": 6},
            "PARTIAL",
        ),
    ],
)
def test_model_gate_never_reaches_go_from_engineering_evidence(offline, live, expected):
    report = readiness(
        engineering_checks={"tests": True},
        offline_six_step=offline,
        live=live,
        evidence={"complete_six_action_fits": True},
    )
    assert report["model_generation_path"] == expected
    assert report["formal_pilot"] == "NO-GO"


@pytest.mark.parametrize(
    ("live", "expected"),
    [
        ({"status": "NOT_RUN"}, "NOT_ASSESSED"),
        (
            {"status": "INCOMPLETE", "valid_outputs": 0, "actual_generation_calls": 6},
            "REAL_MODEL_NOT_READY",
        ),
        (
            {"status": "COMPLETE", "valid_outputs": 6, "actual_generation_calls": 6},
            "SINGLE_EPISODE_VALID_NOT_QUALIFIED",
        ),
    ],
)
def test_output_validity_is_reported_separately_from_path_feasibility(live, expected):
    report = readiness(
        engineering_checks={"tests": True},
        offline_six_step={"representative_paths_fit": True},
        live=live,
        evidence={"complete_six_action_fits": False},
    )
    assert report["model_output_validity"] == expected
    assert report["model_generation_path"] == "PARTIAL"


def test_evidence_gate_follows_measured_feasibility():
    def gate(evidence):
        return readiness(
            engineering_checks={"tests": True},
            offline_six_step={"representative_paths_fit": True},
            live={"status": "NOT_RUN"},
            evidence=evidence,
        )["detector_evidence_sufficiency"]

    assert gate({"complete_six_action_fits": True}) == "GO"
    assert gate({"complete_six_action_fits": False, "lifecycle_and_communication_fit": True}) == (
        "CONDITIONAL GO"
    )
    assert gate({"complete_six_action_fits": False}) == "NO-GO"
    with pytest.raises(ValueError):
        readiness(engineering_checks={"tests": 1}, offline_six_step={}, live={}, evidence={})
