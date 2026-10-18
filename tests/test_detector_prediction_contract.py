import json
from dataclasses import replace
from uuid import UUID, uuid5

import pytest
from view_helpers import PUBLIC_ID

from pactlens.evidence.budget_selection import select_evidence
from pactlens.evidence.budgeted_views import VERSION
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope, PredictionRecord
from pactlens.research.fixtures import run_fixture


def response():
    return {
        "risk_score": 0.35,
        "confidence": 0.7,
        "evidence_ids": [],
        "rationale_short": "SYNTHETIC CONTRACT TEST ONLY",
        "adequacy": "ADEQUATE",
    }


def record(body):
    return PredictionRecord(
        PUBLIC_ID, View.R, VERSION, DetectorEnvelope().config_hash, json.dumps(body)
    )


def test_finite_typed_serialization_has_no_threshold_or_binary_decision():
    r = record(response())
    assert r.verdict == "PENDING_FROZEN_THRESHOLD"
    assert json.loads(r.to_json())["response"]["risk_score"] == 0.35
    assert len(r.record_hash) == 64
    abstention = record({**response(), "adequacy": "INSUFFICIENT_EVIDENCE"})
    assert abstention.verdict == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize(
    "key,value",
    [
        ("risk_score", True),
        ("risk_score", float("nan")),
        ("risk_score", float("inf")),
        ("risk_score", -0.01),
        ("risk_score", 1.01),
        ("risk_score", "0.5"),
        ("confidence", False),
        ("confidence", None),
        ("adequacy", "SUSPICIOUS"),
        ("evidence_ids", ["PRIVATE_TRUTH"]),
        ("evidence_ids", "not-a-list"),
        ("rationale_short", "x" * 513),
    ],
)
def test_malformed_prediction_rejected_without_coercion(key, value):
    with pytest.raises((ValueError, TypeError)):
        record({**response(), key: value})


@pytest.mark.parametrize(
    "case",
    [
        "extra_authority",
        "condition",
        "duplicate_json",
        "missing",
        "opaque_id",
        "view",
        "evidence_version",
        "prompt_hash",
        "citation",
    ],
)
def test_identity_binding_fields_and_evidence_citations_are_closed(case):
    body = response()
    if case in ("extra_authority", "condition"):
        body["approval" if case == "extra_authority" else "condition"] = "PRIVATE"
    elif case == "missing":
        body.pop("confidence")
    if case in ("extra_authority", "condition", "missing"):
        with pytest.raises(ValueError):
            record(body)
        return
    r = record(body)
    changes = {
        "duplicate_json": {"response_json": '{"risk_score":0,"risk_score":1}'},
        "opaque_id": {"episode_public_id": "T001-N1"},
        "view": {"view": "MAE"},
        "evidence_version": {"evidence_version": "PRIVATE_GROUP"},
        "prompt_hash": {"prompt_hash": "PRIVATE_GATE_PATH"},
    }
    if case == "citation":
        inv = build_inventory(run_fixture("c_plus").record, public_id=PUBLIC_ID)
        facts = select_evidence(inv).packet(View.R).verify()[1]
        r = record({**body, "evidence_ids": [str(uuid5(UUID(PUBLIC_ID), "not-observed"))]})
        with pytest.raises(ValueError, match="UNOBSERVED"):
            r.verify_citations(facts)
    else:
        with pytest.raises(ValueError):
            replace(r, **changes[case])


@pytest.mark.parametrize(
    "error", ["INPUT_BUDGET_EXCEEDED", "INVALID_OUTPUT", "PROVIDER_ERROR", "MISSING_PREDICTION"]
)
def test_error_or_missing_output_is_abstention_not_a_fabricated_score(error):
    r = PredictionRecord(PUBLIC_ID, View.MAE, VERSION, DetectorEnvelope().config_hash, None, error)
    data = json.loads(r.to_json())
    assert data["verdict"] == "INSUFFICIENT_EVIDENCE" and data["response"] is None
