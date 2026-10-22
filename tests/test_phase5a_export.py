"""Source-bound synthetic exports are visibly separate from formal publication."""

import hashlib

import pytest

from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.reporting import TABLES, export_results, export_synthetic_results


def test_synthetic_export_lineage_and_formal_rejection(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("SYNTHETIC SOFTWARE TEST ONLY")
    body = {
        "provenance": "SYNTHETIC_SOFTWARE_VALIDATION_ONLY",
        "source_hashes": {"source": hashlib.sha256(source.read_bytes()).hexdigest()},
        "tables": {name: [{"value": None, "denominator": 0}] for name in TABLES},
    }
    body["artifact_hash"] = content_hash(body)
    artifact = tmp_path / "synthetic.json"
    artifact.write_text(canonical_json(body))
    export_synthetic_results(artifact, {"source": source}, tmp_path / "export")
    assert len(list((tmp_path / "export").glob("*.csv"))) == 9
    assert all(
        "SYNTHETIC_SOFTWARE_VALIDATION_ONLY" in p.read_text()
        for p in (tmp_path / "export").glob("*.csv")
    )
    with pytest.raises(ValueError):
        export_results(artifact, {"source": source}, tmp_path / "formal")
    source.write_text("changed")
    with pytest.raises(ValueError):
        export_synthetic_results(artifact, {"source": source}, tmp_path / "bad")
