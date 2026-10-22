"""Auditable claim provenance with explicit unsupported and human-review states."""

import hashlib
from pathlib import Path

REQUIRED = {
    "claim_id",
    "statement",
    "supporting_artifacts",
    "data_provenance",
    "study_split",
    "metric",
    "analysis_version",
    "hashes",
    "uncertainty",
    "support_status",
    "eligible_for_manuscript",
    "human_review_reference",
}


def validate_claims(claims, root):
    if type(claims) is not list or len({r.get("claim_id") for r in claims}) != len(claims):
        raise ValueError("UNIQUE_CLAIM_IDS")
    root = Path(root).resolve()
    for row in claims:
        if set(row) != REQUIRED or row["support_status"] not in (
            "UNSUPPORTED",
            "SUPPORTED_ENGINEERING",
            "SUPPORTED_RESEARCH",
            "PENDING_HUMAN_REVIEW",
        ):
            raise ValueError("CLAIM_CONTRACT")
        if row["eligible_for_manuscript"] and (
            row["support_status"] not in ("SUPPORTED_ENGINEERING", "SUPPORTED_RESEARCH")
            or not row["human_review_reference"]
        ):
            raise ValueError("NO_UNSUPPORTED_OR_UNREVIEWED_MANUSCRIPT_CLAIMS")
        if row["support_status"].startswith("SUPPORTED") and not row["supporting_artifacts"]:
            raise ValueError("CLAIM_SUPPORT_REQUIRED")
        for item in row["supporting_artifacts"]:
            path = (root / item["path"]).resolve()
            if (
                not path.is_relative_to(root)
                or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]
            ):
                raise ValueError("CLAIM_ARTIFACT_BINDING")
    return True
