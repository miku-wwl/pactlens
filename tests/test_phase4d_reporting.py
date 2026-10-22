"""Export and claim verification use manufactured temporary artifacts only."""

import hashlib
import json

import pytest

from pactlens.research.analysis import VERSION
from pactlens.research.claims import validate_claims
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.reporting import export_results


def test_export_rejects_synthetic_unreviewed_and_hash_mismatched_sources(tmp_path):
    sources = {}
    for name in ("locked_l2", "immutable_l4", "frozen_configuration", "thresholds"):
        sources[name] = tmp_path / (name + ".json")
        sources[name].write_text("EXPLICIT_SYNTHETIC_UNIT_TEST_NO_OBSERVATIONS")
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in sources.items()}
    body = {
        "analysis_version": VERSION,
        "provenance": "SYNTHETIC_TEST_ONLY",
        "split": "held_out",
        "source_hashes": hashes,
        "configuration_hash": hashes["frozen_configuration"],
        "reviewer": "UNIT_TEST_NOT_A_REAL_REVIEW",
        "review_record": "UNIT_TEST_ONLY",
        "tables": {"unit-test-only": [{"case": "not-research", "value": None}]},
        "figures": {},
        "artifact_hash": "",
    }
    artifact = tmp_path / "analysis.json"

    def write():
        body["artifact_hash"] = content_hash(
            {k: v for k, v in body.items() if k != "artifact_hash"}
        )
        artifact.write_text(canonical_json(body))

    write()
    with pytest.raises(ValueError):
        export_results(artifact, sources, tmp_path / "rejected")
    # Trusted review attestation is an interface, not human authentication.
    body["provenance"] = "VERIFIED_FORMAL_ANALYSIS"
    write()
    export_results(artifact, sources, tmp_path / "test-export")
    assert "not-research" in (tmp_path / "test-export" / "unit-test-only.csv").read_text()
    sources["locked_l2"].write_text("altered")
    with pytest.raises(ValueError):
        export_results(artifact, sources, tmp_path / "hash-rejected")
    body["reviewer"] = None
    write()
    with pytest.raises(ValueError):
        export_results(artifact, sources, tmp_path / "unreviewed")


def test_unsupported_or_unreviewed_claims_cannot_enter_manuscript(tmp_path):
    p = tmp_path / "safe.json"
    p.write_text("synthetic-engineering-artifact")
    claim = {
        "claim_id": "UNIT-1",
        "statement": "Unit test only",
        "supporting_artifacts": [
            {"path": "safe.json", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        ],
        "data_provenance": "SYNTHETIC_TEST_ONLY",
        "study_split": None,
        "metric": None,
        "analysis_version": VERSION,
        "hashes": {},
        "uncertainty": "not a research observation",
        "support_status": "SUPPORTED_ENGINEERING",
        "eligible_for_manuscript": False,
        "human_review_reference": None,
    }
    assert validate_claims([claim], tmp_path)
    claim["eligible_for_manuscript"] = True
    with pytest.raises(ValueError):
        validate_claims([claim], tmp_path)
    claim["human_review_reference"] = "unit-test-only"
    claim["support_status"] = "UNSUPPORTED"
    with pytest.raises(ValueError):
        validate_claims([claim], tmp_path)
    claim["eligible_for_manuscript"] = False
    p.write_text("changed")
    with pytest.raises(ValueError):
        validate_claims([claim], tmp_path)


def test_research_json_accepts_finite_scores_without_changing_arena_serializer():
    assert json.loads(canonical_json({"score": 0.25}))["score"] == 0.25
    with pytest.raises(ValueError):
        canonical_json({"score": float("nan")})
    from pactlens.serialization import canonical_json as arena_json

    with pytest.raises(TypeError):
        arena_json({"score": 0.25})
