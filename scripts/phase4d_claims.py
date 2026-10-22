"""Build a claim ledger from actual engineering artifacts; no research claims inferred."""

import hashlib
import json
from pathlib import Path

from pactlens.agents.context_v31 import V31_PROMPT
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.agents.protocol_diagnostics import PROTOCOL_HASH
from pactlens.research.analysis import VERSION
from pactlens.research.claims import validate_claims
from pactlens.research.detector_contract import RESPONSE_HASH, DetectorEnvelope
from pactlens.research.json_types import canonical_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    model = json.loads((ROOT / "review/phase4d/model-summary.json").read_text(encoding="utf-8"))
    detector = json.loads(
        (ROOT / "review/phase4d/local-detector/summary.json").read_text(encoding="utf-8")
    )
    dry = json.loads((ROOT / "review/phase4d/audit/pilot-dry-run.json").read_text(encoding="utf-8"))
    assert model["actual_agent_calls"] == 6 and model["episodes"][0]["valid"] == 1
    assert detector["actual_detector_calls"] == 2 and all(
        x["abstained"] for x in detector["results"]
    )
    assert len(dry["episodes"]) == 20 and dry["charged_fake_calls"] == 120
    specifications = [
        (
            "ENG-01",
            "The bounded v3.1 N3 engineering episode produced one valid decline in six calls, with no AIG Actions or receipts.",
            ["review/phase4d/model-summary.json", "review/phase4d/model-response-shapes.json"],
            "REAL_LOCAL_ENGINEERING",
            "valid outputs / dispatched calls",
            "SUPPORTED_ENGINEERING",
        ),
        (
            "ENG-02",
            "Both bounded local R/MAE detector smoke outputs failed strict validation and were recorded as abstentions.",
            ["review/phase4d/local-detector/summary.json"],
            "REAL_LOCAL_ENGINEERING",
            "valid outputs / smoke calls",
            "SUPPORTED_ENGINEERING",
        ),
        (
            "ENG-03",
            "Complete six-action public-speech evidence fails the binding heuristic 4096-token cap under both policies; selected facts preserve semantic R/MAE parity.",
            ["review/phase4d/audit/six-action-communication-audit.json"],
            "SYNTHETIC_ENGINEERING_REAL_LOCAL_AIG",
            "estimated full-request tokens; independent semantic relations",
            "SUPPORTED_ENGINEERING",
        ),
        (
            "ENG-04",
            "A four-group engineering dry run completed twenty fake-model episodes with 120 fake requests and 108 verified local receipts, using zero formal slots.",
            ["review/phase4d/audit/pilot-dry-run.json"],
            "SYNTHETIC_ENGINEERING_REAL_LOCAL_AIG",
            "engineering completion/receipt counts",
            "SUPPORTED_ENGINEERING",
        ),
        (
            "ENG-05",
            "A committed local proposal may coexist with terminal Unknown and zero Arena-applied proposals; read-only replay creates no second effect.",
            ["review/phase4d/audit/unknown-audit.json"],
            "DETERMINISTIC_FAULT_INJECTION_REAL_AIG",
            "effect/application counts",
            "SUPPORTED_ENGINEERING",
        ),
        (
            "RES-01",
            "Additional AIG execution evidence improves held-out detection beyond ordinary MA behavior logs.",
            [],
            "UNEXECUTED_FUTURE_RESEARCH",
            "paired held-out N1 FPR and recall/coverage",
            "UNSUPPORTED",
        ),
        (
            "RES-02",
            "At least two independently adjudicated C+ positive controls have been realized in the formal Pilot.",
            [],
            "UNEXECUTED_FUTURE_RESEARCH",
            "verified C+ / all assigned C+",
            "UNSUPPORTED",
        ),
    ]
    claims = []
    for identifier, statement, paths, provenance, metric, status in specifications:
        claims.append(
            {
                "claim_id": identifier,
                "statement": statement,
                "supporting_artifacts": [
                    {"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                    for p in paths
                ],
                "data_provenance": provenance,
                "study_split": None,
                "metric": metric,
                "analysis_version": VERSION,
                "hashes": {
                    "agent_prompt": PROMPT_HASHES[V31_PROMPT],
                    "agent_protocol": PROTOCOL_HASH,
                    "detector_prompt": DetectorEnvelope().config_hash,
                    "detector_response": RESPONSE_HASH,
                    "model_digest": model["identity"]["model_digest"],
                },
                "uncertainty": "Engineering observations only; small dependent cases; no formal outcomes or independent human review.",
                "support_status": status,
                "eligible_for_manuscript": False,
                "human_review_reference": None,
            }
        )
    validate_claims(claims, ROOT)
    (ROOT / "research/phase4d/claims.json").write_text(
        canonical_json(claims) + "\n", encoding="utf-8"
    )
    print(f"Validated {len(claims)} claims; all manuscript eligibility pending human review.")


if __name__ == "__main__":
    main()
