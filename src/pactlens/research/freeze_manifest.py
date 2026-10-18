"""Deterministic proposed configurations; engineering authorization is not approval."""

import re

from pactlens.agents.prompts import CANDIDATE_PROMPT, EXAMPLE_VERSION, LEGACY_PROMPT, PROMPT_HASHES
from pactlens.agents.protocol_diagnostics import CANDIDATE_PROTOCOL, LEGACY_PROTOCOL, PROTOCOL_HASH
from pactlens.evidence.budget_selection import CONFIG, CONFIG_HASH
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.research.detector_contract import RESPONSE_HASH, DetectorEnvelope
from pactlens.research.reviewer_packets import RUBRIC_HASH
from pactlens.serialization import content_hash, primitive

VERSION = "pactlens-freeze-candidates-v1"
DECISIONS = {
    "primary_observer": (ObservationPolicy.DELIVERED.value, "PROPOSED"),
    "router_sensitivity": (ObservationPolicy.ROUTER_AUDIT.value, "PROPOSED"),
    "n2": ("retain-N2-A-disclose-intervention-secondary", "PROPOSED"),
    "evidence_selection": (CONFIG["version"], "PROPOSED"),
    "prompt_protocol": (CANDIDATE_PROMPT, "PENDING"),
    "model_identity": ("verified-local-model-only", "PENDING"),
    "reviewer_rubric": ("pactlens-independent-review-v1-candidate", "PENDING"),
    "detector_interface": ("pactlens-detector-response-v1-candidate", "PENDING"),
    "formal_pilot": ("not-authorized", "NO-GO"),
}


def freeze_candidates(model_identity, model_config, *, trace_references=()):
    if type(model_identity) is not dict or set(model_identity) != {
        "endpoint_type",
        "server_version",
        "model",
        "model_digest",
        "seed_support",
        "cloud_model",
    }:
        raise ValueError("VERIFIED_LOCAL_IDENTITY_FIELDS")
    if (
        model_identity["endpoint_type"] != "ollama_loopback_openai"
        or model_identity["cloud_model"] is not False
        or re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", model_identity["model_digest"]) is None
    ):
        raise ValueError("IMMUTABLE_LOCAL_MODEL_REQUIRED")
    model_config.__post_init__()
    if (
        model_config.model != model_identity["model"]
        or model_config.revision != model_identity["model_digest"]
    ):
        raise ValueError("MODEL_CONFIG_IDENTITY_MISMATCH")
    references = []
    for ref in trace_references:
        if (
            type(ref) is not dict
            or set(ref) != {"profile", "trace_hash", "status", "actual_generation_calls"}
            or ref["profile"] not in ("legacy-v1", "candidate-v2")
            or re.fullmatch(r"[a-f0-9]{64}", ref["trace_hash"]) is None
        ):
            raise ValueError("SAFE_ENGINEERING_TRACE_REFERENCE")
        references.append(dict(ref))
    candidate = {
        "version": VERSION,
        "status": "CANDIDATES_NOT_APPROVED",
        "model": dict(model_identity),
        "model_config": primitive(model_config),
        "agent_input_limit": 2000,
        "agent_output_limit": 256,
        "seed_convention": "SHA256_ENGINEERING_COMMON_GROUP_UNSIGNED64_LOW63_V1",
        "seed_support": "REQUESTED_NOT_VERIFIED;no-fresh-inference-determinism-claim",
        "legacy": {
            "prompt": LEGACY_PROMPT,
            "hash": PROMPT_HASHES[LEGACY_PROMPT],
            "protocol": LEGACY_PROTOCOL,
        },
        "candidate": {
            "prompt": CANDIDATE_PROMPT,
            "hash": PROMPT_HASHES[CANDIDATE_PROMPT],
            "protocol": CANDIDATE_PROTOCOL,
            "protocol_hash": PROTOCOL_HASH,
            "example_policy": EXAMPLE_VERSION,
        },
        "condition_rules": "existing-EpisodeConfig-unchanged;no-repair;N2-round2-block;C-pair-channel-only",
        "token_method": "UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE;not-exact-or-guaranteed",
        "retry": "one-generation-attempt;Unknown-terminal-no-retry;no-replacement-episode",
        "errors": "invalid,error,overflow,missing-prediction=>abstention;valid-decline-not-failure",
        "selection_config": CONFIG,
        "selection_hash": CONFIG_HASH,
        "detector_envelope": primitive(DetectorEnvelope()),
        "detector_envelope_hash": DetectorEnvelope().config_hash,
        "detector_response_hash": RESPONSE_HASH,
        "reviewer_rubric_hash": RUBRIC_HASH,
        "trace_references": sorted(references, key=lambda x: x["profile"]),
        "decisions": {
            key: {"candidate": value, "status": status}
            for key, (value, status) in sorted(DECISIONS.items())
        },
        "freeze_gates": [
            "availability",
            "token-feasibility",
            "strict-protocol",
            "reviewed-examples",
            "transparent-outcomes",
            "stable-execution",
            "limitations",
            "independent-researcher-approval",
        ],
    }
    return {**candidate, "candidate_manifest_hash": content_hash(candidate)}
