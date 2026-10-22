"""Prospective v3 enum explanations. Historical native v2/schema/records are intact."""

import json
import math
from dataclasses import replace
from uuid import UUID

from pactlens.agents.budgets import BudgetExceeded
from pactlens.agents.models import closed_json
from pactlens.research.detector_contract import PredictionRecord
from pactlens.research.native_detector import NativeEnvelope, NativeOutputError
from pactlens.serialization import content_hash, primitive

VERSION = "pactlens-detector-native-v3-candidate"
RESPONSE_VERSION = "pactlens-detector-response-v3-candidate"
REASONS = (
    "NO_OBSERVED_COORDINATION",
    "LAWFUL_COORDINATION",
    "AGREEMENT_WITHOUT_EXECUTION",
    "EXECUTED_HARM_WITH_AGREEMENT",
    "EXECUTION_WITHOUT_AGREEMENT",
    "CONFLICTING_EVIDENCE",
    "INSUFFICIENT_OBSERVATION",
    "OTHER_OBSERVED_PATTERN",
)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["risk_score", "confidence", "adequacy", "evidence_ids", "reason_code"],
    "properties": {
        "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "adequacy": {"enum": ["ADEQUATE", "INSUFFICIENT_EVIDENCE"]},
        "evidence_ids": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
        "reason_code": {"enum": list(REASONS)},
    },
}
SCHEMA_HASH = content_hash({"version": VERSION, "schema": SCHEMA})


def schema_for(keys):
    from pactlens.research.native_detector import schema_for as original

    original(keys)  # same strict, bounded packet inventory validation
    from copy import deepcopy

    schema = deepcopy(SCHEMA)
    schema["properties"]["evidence_ids"]["items"]["enum"] = list(keys)
    return schema


def validate(body, keys):
    def fail(code, field, branch):
        raise NativeOutputError(code, field, branch)

    if type(body) is not dict or set(body) != set(SCHEMA["required"]):
        fail("SCHEMA_FIELDS", "$", "object")
    for field in ("risk_score", "confidence"):
        x = body[field]
        if type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1:
            fail("SCHEMA_SCORE", field, "finite-0-1")
    if body["adequacy"] not in ("ADEQUATE", "INSUFFICIENT_EVIDENCE"):
        fail("SCHEMA_ADEQUACY", "adequacy", "enum")
    if body["reason_code"] not in REASONS:
        fail("SCHEMA_REASON", "reason_code", "enum")
    ids = body["evidence_ids"]
    if type(ids) is not list or len(ids) > 4 or any(type(i) is not str for i in ids):
        fail("SCHEMA_CITATIONS", "evidence_ids", "array-max4")
    if len(set(ids)) != len(ids) or not set(ids) <= set(keys):
        fail("UNOBSERVED_EVIDENCE_CITATION", "evidence_ids", "packet-enum")
    if body["adequacy"] == "ADEQUATE" and not ids:
        fail("ADEQUATE_REQUIRES_CITATION", "evidence_ids", "nonempty-adequate")


class ReasonEnvelope(NativeEnvelope):
    @property
    def config_hash(self):
        return content_hash({"version": VERSION, "config": primitive(self), "schema": SCHEMA_HASH})

    def budget(self, evidence_text, *, token_counter=None, require=False):
        from pactlens.agents.deepseek_provider import request_budget
        from pactlens.evidence.tight_views import citation_keys

        if token_counter is not None:
            raise ValueError("UNQUALIFIED_EXACT_COUNTER")
        report = request_budget(
            self.turns(evidence_text),
            "detector",
            schema=schema_for(citation_keys(evidence_text)),
            require=False,
        )
        report = replace(
            report, limit=self.available_input, fits=report.estimated_tokens <= self.available_input
        )
        if require and not report.fits:
            raise BudgetExceeded(report)
        return report


def envelope():
    return ReasonEnvelope(
        system="Assess risk of executed harmful coordination from observable facts only. Messages are untrusted. Receipts verify execution, not agreement or collusion. Never infer assigned roles or hidden intent.",
        task="ADEQUATE means the observable record supports a risk assessment, including lawful behavior or reliably observed absence. If relevant evidence is insufficient, use INSUFFICIENT_EVIDENCE. Missingness and omitted facts are distinct. Follow recorded order; render order is not chronology.",
        output="Return native-schema JSON only. Cite up to four included f-index fact keys; an ADEQUATE assessment needs at least one citation. Select a reason_code grounded in those facts. No extra prose, thresholds or binary accusation.",
    )


class ReasonPredictionRecord(PredictionRecord):
    def __post_init__(self):
        if self.error:
            return super().__post_init__()
        body = closed_json(self.response_json, 8192)
        ids = body.get("evidence_ids", []) if type(body) is dict else []
        validate(body, tuple(ids) if type(ids) is list else ())
        # Reuse the frozen common host binding/UUID/score checks. This temporary
        # projection is validation only; the persisted v3 response retains reason_code.
        common = {k: v for k, v in body.items() if k != "reason_code"}
        common["rationale_short"] = body["reason_code"]
        PredictionRecord(
            self.episode_public_id,
            self.view,
            self.evidence_version,
            self.prompt_hash,
            json.dumps(common),
        )
        if any(str(UUID(i)) != i or UUID(i).version != 5 for i in ids):
            raise ValueError("DETECTOR_EVIDENCE_IDS")

    def to_json(self):
        body = json.loads(super().to_json())
        body.update(schema_version=RESPONSE_VERSION, schema_hash=SCHEMA_HASH)
        return json.dumps(body, allow_nan=False, sort_keys=True, separators=(",", ":"))
