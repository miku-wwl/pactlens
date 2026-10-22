"""One-shot L3 -> provider -> immutable L4. Engineering only; no truth interface.

Uses the existing generation port and local adapter, without agent request identities.
An exclusive intent file fences a call before dispatch; interrupted attempts are
never resumed. Replay is read-only consistency checking, not fresh inference.
"""

import asyncio
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from pactlens.agents.budgets import BudgetExceeded
from pactlens.agents.models import closed_json
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.evidence.compact_views import VERSION as EVIDENCE_VERSION
from pactlens.evidence.compact_views import CompactView
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope, PredictionRecord
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.serialization import primitive

VERSION = "pactlens-detector-runner-v1-candidate"


@dataclass(frozen=True)
class DetectorRequest:
    turns: tuple
    seed: int
    prompt_hash: str
    evidence_hash: str


def exclusive_json(path, body):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(body) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _record(body, packet):
    header, facts = packet.verify()
    record = PredictionRecord(
        header["episode"],
        packet.view,
        EVIDENCE_VERSION,
        packet.envelope.config_hash,
        body,
        None,
    )
    record.verify_citations(facts)
    return record


async def predict(directory, packet, provider, *, engineering_id, seed=0):
    if (
        type(packet) is not CompactView
        or re.fullmatch(r"ENG-[A-Za-z0-9-]{1,48}", engineering_id) is None
    ):
        raise ValueError("ENGINEERING_L3_PACKET_REQUIRED_FORMAL_DISABLED")
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("DETECTOR_SEED")
    if type(provider.config) is not ModelConfig:
        raise ValueError("TRUSTED_MODEL_CONFIG")
    provider.config.__post_init__()
    if provider.config.max_output_tokens > packet.envelope.reserved_output_tokens:
        raise ValueError("OUTPUT_RESERVATION")
    header, facts = packet.verify()
    config = {
        "version": VERSION,
        "model": primitive(provider.config),
        "prompt_hash": packet.envelope.config_hash,
        "template_version": EVIDENCE_VERSION,
        "error_policy": "abstain-no-retry",
        "seed": seed,
        "engineering_id": engineering_id,
        "formal_execution_enabled": False,
    }
    identity = content_hash(
        {"config": config, "text": packet.text, "manifest": packet.manifest_json}
    )
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    exclusive_json(
        directory / (identity + ".intent.json"), {"identity": identity, "config": config}
    )
    error, raw_hash, usage, response_json = None, None, None, None
    budget = packet.envelope.budget(packet.text)
    record = None
    try:
        # Never accept a synthetic manifest's claimed exact count as provider qualification.
        turns = packet.conversation()
        request = DetectorRequest(
            turns, seed, packet.envelope.config_hash, content_hash(packet.text)
        )
        async with asyncio.timeout(provider.config.timeout_seconds):
            response = await provider.generate(request)
        if type(response) is not ModelResponse:
            raise ValueError("DETECTOR_RESPONSE_TYPE")
        response.__post_init__()
        raw_hash = content_hash(response.text)
        usage = {
            k: getattr(response, k)
            for k in ("input_tokens", "output_tokens", "latency_us", "finish_reason")
        }
        if response.input_tokens is not None and response.input_tokens > budget.limit:
            raise ValueError("ACTUAL_INPUT_BUDGET_EXCEEDED")
        if response.finish_reason == "length" or (
            response.output_tokens is not None
            and response.output_tokens > provider.config.max_output_tokens
        ):
            raise ValueError("OUTPUT_BUDGET_EXCEEDED")
        body = closed_json(response.text, 8192)
        if type(body) is not dict:
            raise ValueError("DETECTOR_OBJECT")
        # The v2 table legend explicitly asks for logical keys. Resolve exactly;
        # do not infer missing citations or repair malformed output.
        ids = body.get("evidence_ids")
        if type(ids) is list and all(type(x) is str for x in ids):
            allowed = {f.fact_id for f in facts}
            if not set(ids) <= allowed:
                body["evidence_ids"] = list(packet.resolve_citations(ids))
        response_json = canonical_json(body)
        record = _record(response_json, packet)
    except BudgetExceeded:
        error = "INPUT_BUDGET_EXCEEDED"
    except (ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        error = "INVALID_OUTPUT"
    except (OSError, TimeoutError, RuntimeError):
        error = "PROVIDER_ERROR"
    if error:
        response_json = None
        record = PredictionRecord(
            header["episode"],
            packet.view,
            EVIDENCE_VERSION,
            packet.envelope.config_hash,
            None,
            error,
        )
    prediction = json.loads(record.to_json())
    # Host-bound abstention retains an otherwise valid model response and its score.
    incomplete = bool(json.loads(packet.manifest_json)["omitted"]) or any(
        f.completeness != "OBSERVED" for f in facts
    )
    source_incomplete = any(
        f.kind.endswith("coverage")
        and any(
            v not in ("COMPLETE", "NOT_APPLICABLE") for v in json.loads(f.payload_json).values()
        )
        for f in facts
    )
    forced = incomplete or source_incomplete
    artifact = {
        "version": VERSION,
        "identity": identity,
        "config": config,
        "packet": {
            "view": packet.view.value,
            "text": packet.text,
            "manifest_json": packet.manifest_json,
            "envelope": primitive(packet.envelope),
        },
        "prediction": prediction,
        "record_hash": record.record_hash,
        "budget": primitive(budget),
        "usage": usage,
        "raw_response_hash": raw_hash,
        "source_coverage_insufficient": forced,
        "abstained": forced or record.verdict == "INSUFFICIENT_EVIDENCE",
        "provenance": "ENGINEERING_ONLY_NOT_RESEARCH_PREDICTION",
    }
    artifact["artifact_hash"] = content_hash(artifact)
    path = directory / (identity + ".prediction.json")
    exclusive_json(path, artifact)
    replay_prediction(path)
    return path


def replay_prediction(path):
    raw = Path(path).read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("PREDICTION_BOUND")
    body = closed_json(raw.decode("utf-8"), 2_000_000)
    digest = body.pop("artifact_hash")
    if content_hash(body) != digest or body["version"] != VERSION:
        raise ValueError("PREDICTION_INTEGRITY")
    p = body["packet"]
    packet = CompactView(
        View(p["view"]), p["text"], p["manifest_json"], DetectorEnvelope(**p["envelope"])
    )
    packet.verify()
    expected = content_hash(
        {"config": body["config"], "text": packet.text, "manifest": packet.manifest_json}
    )
    prediction = body["prediction"]
    record = PredictionRecord(
        prediction["episode_public_id"],
        View(prediction["view"]),
        prediction["evidence_version"],
        prediction["prompt_hash"],
        None if prediction["response"] is None else canonical_json(prediction["response"]),
        prediction["error"],
    )
    record.verify_citations(packet.verify()[1])
    if (
        expected != body["identity"]
        or record.record_hash != body["record_hash"]
        or json.loads(record.to_json()) != prediction
        or prediction["episode_public_id"] != packet.verify()[0]["episode"]
        or prediction["view"] != packet.view.value
        or prediction["prompt_hash"] != packet.envelope.config_hash
    ):
        raise ValueError("PREDICTION_BINDING")
    return {
        **body,
        "artifact_hash": digest,
        "replay_generation_calls": 0,
        "replay_new_effects": 0,
        "file_sha256": hashlib.sha256(raw).hexdigest(),
    }
