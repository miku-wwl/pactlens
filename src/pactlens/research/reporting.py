"""Validated, source-bound future analysis export. No invented result generation."""

import csv
import hashlib
import json
import math
from pathlib import Path

from pactlens.agents.models import closed_json
from pactlens.research.analysis import VERSION
from pactlens.research.json_types import content_hash

FIGURES = (
    "episode-validity",
    "positive-control-realization",
    "five-view-coverage",
    "paired-n1-fpr",
    "execution-evidence-contribution",
    "shortcut-missingness",
)

TABLES = (
    "condition-validity",
    "positive-controls",
    "view-coverage",
    "fpr-recall",
    "ma-r-mae",
    "evidence-budget",
    "adjudicator-agreement",
    "paired-confidence-intervals",
    "runtime-api-cost",
)


def export_synthetic_results(artifact, sources, output):
    """Separate watermarked validation route; never passes the formal exporter."""
    import hashlib

    body = closed_json(Path(artifact).read_text(encoding="utf-8"), 2_000_000)
    if body.get("provenance") != "SYNTHETIC_SOFTWARE_VALIDATION_ONLY" or set(
        body.get("tables", {})
    ) != set(TABLES):
        raise ValueError("EXPLICIT_SYNTHETIC_TABLE_SET_REQUIRED")
    if body.get("artifact_hash") != content_hash(
        {k: v for k, v in body.items() if k != "artifact_hash"}
    ):
        raise ValueError("SYNTHETIC_EXPORT_INTEGRITY")
    if set(sources) != set(body["source_hashes"]) or any(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() != body["source_hashes"][k]
        for k, p in sources.items()
    ):
        raise ValueError("SYNTHETIC_SOURCE_BINDING")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in body["tables"].items():
        if not rows or any(set(r) != set(rows[0]) for r in rows):
            raise ValueError("RECTANGULAR_RESULTS_TABLE")
        with (output / (name + ".csv")).open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["provenance", *rows[0]])
            writer.writeheader()
            writer.writerows({"provenance": body["provenance"], **r} for r in rows)
    (output / "README.txt").write_text(
        "SYNTHETIC SOFTWARE VALIDATION ONLY. No research results or human reviews.\n"
        + body["artifact_hash"],
        encoding="utf-8",
    )
    return output


def verify_analysis_artifact(body, sources):
    required = {
        "analysis_version",
        "provenance",
        "split",
        "source_hashes",
        "configuration_hash",
        "reviewer",
        "review_record",
        "tables",
        "figures",
        "artifact_hash",
    }
    if type(body) is not dict or set(body) != required:
        raise ValueError("ANALYSIS_EXPORT_SCHEMA")
    if (
        body["analysis_version"] != VERSION
        or body["provenance"] != "VERIFIED_FORMAL_ANALYSIS"
        or body["split"] != "held_out"
    ):
        raise ValueError("NO_SYNTHETIC_OR_UNEXECUTED_MANUSCRIPT_RESULTS")
    if not body["reviewer"] or not body["review_record"]:
        raise ValueError("INDEPENDENT_REVIEW_REQUIRED")
    hashes = body["source_hashes"]
    if type(hashes) is not dict or set(hashes) != {
        "locked_l2",
        "immutable_l4",
        "frozen_configuration",
        "thresholds",
    }:
        raise ValueError("ANALYSIS_LINEAGE")
    if set(sources) != set(hashes):
        raise ValueError("SOURCE_FILES_REQUIRED")
    import hashlib

    if any(
        hashlib.sha256(Path(sources[k]).read_bytes()).hexdigest() != v for k, v in hashes.items()
    ):
        raise ValueError("ANALYSIS_SOURCE_HASH_MISMATCH")
    if body["configuration_hash"] != hashes["frozen_configuration"]:
        raise ValueError("ANALYSIS_CONFIGURATION")
    if body["artifact_hash"] != content_hash(
        {k: v for k, v in body.items() if k != "artifact_hash"}
    ):
        raise ValueError("ANALYSIS_EXPORT_HASH")
    if type(body["figures"]) is not dict or not set(body["figures"]) <= set(FIGURES):
        raise ValueError("FIGURE_CONTRACT")
    for name, rows in body["figures"].items():
        if type(rows) is not list:
            raise ValueError("FIGURE_ROWS")
        for r in rows:
            if set(r) != {"label", "value", "lower", "upper", "denominator"}:
                raise ValueError("FIGURE_ROW")
            if (
                type(r["label"]) is not str
                or type(r["denominator"]) is not int
                or r["denominator"] < 0
            ):
                raise ValueError("FIGURE_DENOMINATOR")
            for key in ("value", "lower", "upper"):
                if r[key] is not None and (
                    type(r[key]) not in (int, float) or not math.isfinite(r[key])
                ):
                    raise ValueError("FINITE_RESULT")
            if (r["lower"] is None) != (r["upper"] is None) or (
                r["lower"] is not None
                and (r["value"] is None or not r["lower"] <= r["value"] <= r["upper"])
            ):
                raise ValueError("RESULT_INTERVAL")
    for name, rows in body["tables"].items():
        if not rows or any(type(r) is not dict or set(r) != set(rows[0]) for r in rows):
            raise ValueError("RECTANGULAR_RESULTS_TABLE")
        if not name.replace("-", "").isalnum():
            raise ValueError("TABLE_NAME")
    return True


def export_results(artifact, sources, output, *, charts=False):
    body = closed_json(Path(artifact).read_text(encoding="utf-8"), 2_000_000)
    verify_analysis_artifact(body, sources)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in body["tables"].items():
        with (output / (name + ".csv")).open("x", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    if charts:
        # Optional standard plotting tool, never installed or downloaded by this exporter.
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        for name, rows in body["figures"].items():
            valid = [r for r in rows if r["value"] is not None]
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar([r["label"] for r in valid], [r["value"] for r in valid], color="#255d81")
            for i, r in enumerate(valid):
                if r["lower"] is not None:
                    ax.errorbar(
                        i,
                        r["value"],
                        yerr=[[r["value"] - r["lower"]], [r["upper"] - r["value"]]],
                        fmt="none",
                        color="black",
                        capsize=4,
                    )
            ax.set_title(name.replace("-", " "))
            ax.set_ylabel("Verified analysis value")
            ax.tick_params(axis="x", labelrotation=20)
            fig.text(
                0.01,
                0.01,
                "Source "
                + body["artifact_hash"][:16]
                + "; undefined values omitted, never zero-filled",
                fontsize=7,
            )
            fig.tight_layout(rect=(0, 0.04, 1, 1))
            fig.savefig(output / (name + ".pdf"))
            fig.savefig(output / (name + ".svg"))
            plt.close(fig)
    (output / "provenance.json").write_text(
        json.dumps(
            {
                "source_analysis_hash": body["artifact_hash"],
                "sources": body["source_hashes"],
                "charts": charts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output


def export_engineering_results(rows, sources, output):
    """Descriptive real-engineering tables, without relaxing formal result guards."""
    from pactlens.research.detector_runner import analysis_prediction, replay_prediction

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    identities = set()
    table = []
    scored = 0
    for row in rows:
        artifact = replay_prediction(row["artifact"])
        if artifact["provenance"] != "ENGINEERING_ONLY_NOT_RESEARCH_PREDICTION":
            raise ValueError("ENGINEERING_L4_REQUIRED")
        if artifact["identity"] in identities:
            raise ValueError("DUPLICATE_ENGINEERING_PREDICTION")
        identities.add(artifact["identity"])
        view, score, confidence = analysis_prediction(row["artifact"])
        scored += score is not None
        table.append(
            {
                **row,
                "view": view.value,
                "effective_score": score,
                "effective_confidence": confidence,
                "state": artifact["decision"]["state"],
                "error": artifact["prediction"]["error"],
                "evidence_eligible": artifact["decision"].get("eligibility", {}).get("eligible"),
                "host_abstained": artifact["decision"]["host_mandated"],
                "model_abstained": artifact["decision"].get("model_abstained", False),
                "reason_codes": ";".join(artifact["decision"]["reasons"]),
            }
        )
    if table:
        with (output / "engineering-matrix.csv").open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(table[0]))
            writer.writeheader()
            writer.writerows(table)
    provenance = {
        "provenance": "REAL_ENGINEERING_DESCRIPTIVE_NOT_FORMAL",
        "attempts": len(table),
        "effective_scores": scored,
        "coverage": None if not table else scored / len(table),
        "threshold": "NOT_SELECTED",
        "formal_inference": False,
        "source_hashes": {
            str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources
        },
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return provenance
