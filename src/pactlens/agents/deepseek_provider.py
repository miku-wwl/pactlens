"""Reviewed fixed-host Responses transport. No retries, tools, redirects or fallback.

Only synthetic engineering inputs are authorized by the Phase 4E campaign.
The ledger is consumer inference accounting, not an AIG execution mechanism.
"""

import asyncio
import hashlib
import http.client
import json
import os
import sqlite3
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from pactlens.agents.budgets import BudgetExceeded, require_budget, token_preflight
from pactlens.agents.models import Turn, closed_json
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.research.detector_contract import RESPONSE_SCHEMA
from pactlens.serialization import canonical_json, content_hash

HOST = "api.deepseek.com"
PRICING = {
    "date": "2026-10-22",
    "source": "https://api-docs.deepseek.com/quick_start/pricing/",
    "basis": "PEAK_CACHE_MISS_USD_PER_MILLION",
    "input": "0.30",
    "output": "1.20",
    "served_model_documented": "DeepSeek-V4.1-Flash-1017",
}
AGENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "actor_id",
        "round_number",
        "task_hash",
        "decision",
        "assignments",
        "message",
        "end_step",
    ],
    "properties": {
        "actor_id": {"type": "string"},
        "round_number": {"type": "integer", "enum": [1, 2]},
        "task_hash": {"type": "string"},
        "decision": {"enum": ["submit", "decline"]},
        "assignments": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["incident_id", "agent_id"],
                        "properties": {
                            "incident_id": {"type": "string"},
                            "agent_id": {"type": ["string", "null"]},
                        },
                    },
                },
            ]
        },
        "message": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["channel", "recipients", "text"],
                    "properties": {
                        "channel": {"enum": ["public", "private"]},
                        "recipients": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 2,
                            "items": {"type": "string"},
                        },
                        "text": {"type": "string", "minLength": 1, "maxLength": 256},
                    },
                },
            ]
        },
        "end_step": {"type": "boolean", "enum": [True]},
    },
}
PROFILE = {
    "endpoint": "https://api.deepseek.com/responses",
    "model": "deepseek-flash",
    "reasoning": {"effort": "none"},
    "temperature": 0,
    "max_output_tokens": 256,
    "stream": False,
    "seed": "UNSUPPORTED_NOT_SENT",
    "attempts": 1,
    "agent_schema_hash": content_hash(AGENT_SCHEMA),
    "detector_schema_hash": content_hash(RESPONSE_SCHEMA),
    "pricing": PRICING,
}


class ProviderFailure(OSError):
    def __init__(self, code, *, uncertain=False):
        self.code, self.uncertain = code, uncertain
        super().__init__(code)  # Never copy a remote error body or exception text.


def configured_key():
    value = os.environ.get("DEEPSEEK_API_KEY")
    if not value and os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
                value = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")[0]
        except (FileNotFoundError, OSError):
            pass
    if type(value) is not str or not value.strip() or "\r" in value or "\n" in value:
        raise ProviderFailure("CREDENTIAL_UNAVAILABLE")
    return value


def estimated_micro_usd(input_tokens, output_tokens):
    # ceil to a micro-dollar; peak/cache-miss even if the provider reports cache hits.
    return (input_tokens * 3 + output_tokens * 12 + 9) // 10


class CampaignLedger:
    def __init__(self, path, *, ceiling_usd=Decimal(5)):
        self._initialize(
            path,
            ceiling_usd,
            {"agent": 36, "detector": 20, "total": 56, "purpose": "phase4e_engineering"},
        )

    @classmethod
    def phase5a1(cls, path):
        result = object.__new__(cls)
        result._initialize(
            path,
            Decimal(2),
            {
                "agent": 18,
                "detector": 10,
                "total": 28,
                "purpose": "phase5a1_engineering",
                "agent_contexts": ["ENG-5a1-N3", "ENG-5a1-C_PLUS", "ENG-5a1-C_MINUS"],
                "per_context": 6,
            },
            profile=profile_5a1(),
        )
        return result

    @classmethod
    def authorized_pilot(cls, path, manifest, root):
        from pactlens.research.study_launch import verify_launch

        verify_launch(manifest, root)
        result = object.__new__(cls)
        result._initialize(
            path,
            Decimal(str(manifest["owner_authorization"]["maximum_usd"])),
            {
                "agent": 120,
                "detector": 100,
                "total": 220,
                "purpose": "authorized_pilot",
                "manifest_hash": manifest["manifest_hash"],
            },
            profile=profile_5a1()
            if manifest["configuration"]["provider"].get("version") == "phase5a1-native-v1"
            else None,
        )
        return result

    def _initialize(self, path, ceiling_usd, limits, *, profile=None):
        self.profile = PROFILE if profile is None else profile
        self.limits = limits
        configured = os.environ.get("PACTLENS_DEEPSEEK_MAX_USD")
        ceiling = min(
            Decimal(5),
            Decimal(str(ceiling_usd)),
            Decimal(configured) if configured else Decimal(5),
        )
        if not ceiling.is_finite() or ceiling <= 0:
            raise ValueError("INVALID_SPEND_CEILING")
        self.ceiling = int(ceiling * 1_000_000)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, body TEXT NOT NULL)"
            )
            settings = canonical_json(
                {
                    "profile": self.profile,
                    "ceiling_micro_usd": self.ceiling,
                    "limits": limits,
                }
            )
            db.execute("INSERT OR IGNORE INTO settings VALUES (1, ?)", (settings,))
            if db.execute("SELECT body FROM settings WHERE id=1").fetchone()[0] != settings:
                raise ValueError("LEDGER_CONFIGURATION_CHANGED")
            db.execute(
                "CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, role TEXT NOT NULL, identity TEXT UNIQUE NOT NULL, reserve INTEGER NOT NULL, charge INTEGER NOT NULL, metadata TEXT NOT NULL)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def reserve(self, role, identity, budget, *, context_id=None):
        if role not in ("agent", "detector"):
            raise ValueError("INFERENCE_ROLE")
        reserve = estimated_micro_usd(2000 if role == "agent" else 4096, 256)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            total, charged = db.execute(
                "SELECT count(*), coalesce(sum(charge),0) FROM calls"
            ).fetchone()
            count = db.execute("SELECT count(*) FROM calls WHERE role=?", (role,)).fetchone()[0]
            if self.limits["purpose"] == "phase5a1_engineering" and role == "agent":
                if context_id not in self.limits["agent_contexts"]:
                    raise ProviderFailure("UNDECLARED_AGENT_CONTEXT")
                used = db.execute(
                    "SELECT count(*) FROM calls WHERE json_extract(metadata,'$.context_id')=?",
                    (context_id,),
                ).fetchone()[0]
                if used >= self.limits["per_context"]:
                    raise ProviderFailure("EPISODE_CALL_CAP")
            if total >= self.limits["total"] or count >= self.limits[role]:
                raise ProviderFailure("CALL_CAP")
            if charged + reserve > self.ceiling:
                raise ProviderFailure("SPEND_CAP")
            meta = {
                "status": "RESERVED_OUTCOME_UNKNOWN",
                "identity": identity,
                "role": role,
                "complete_request_budget": asdict(budget),
                "pricing": PRICING,
                "reserved_micro_usd": reserve,
                "estimated_actual_micro_usd": None,
            }
            if context_id is not None:
                meta["context_id"] = context_id
            try:
                call_id = db.execute(
                    "INSERT INTO calls(role,identity,reserve,charge,metadata) VALUES (?,?,?,?,?)",
                    (role, identity, reserve, reserve, canonical_json(meta)),
                ).lastrowid
            except sqlite3.IntegrityError:
                raise ProviderFailure("DUPLICATE_REQUEST_NO_RETRY") from None
        return call_id

    def finish(self, call_id, metadata):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            reserve, text = db.execute(
                "SELECT reserve,metadata FROM calls WHERE id=?", (call_id,)
            ).fetchone()
            body = json.loads(text)
            if body["status"] != "RESERVED_OUTCOME_UNKNOWN":
                raise ValueError("LEDGER_TERMINAL")
            body.update(metadata)
            charge = max(reserve, body.get("estimated_actual_micro_usd") or 0)
            db.execute(
                "UPDATE calls SET charge=?,metadata=? WHERE id=?",
                (charge, canonical_json(body), call_id),
            )

    def report(self):
        with self.connect() as db:
            rows = [
                {"call_id": n, **json.loads(meta), "retained_charge_micro_usd": charge}
                for n, meta, charge in db.execute(
                    "SELECT id,metadata,charge FROM calls ORDER BY id"
                )
            ]
        return {
            "profile": self.profile,
            "ceiling_micro_usd": self.ceiling,
            "calls": rows,
            "agent_requests": sum(x["role"] == "agent" for x in rows),
            "detector_requests": sum(x["role"] == "detector" for x in rows),
            "reserved_or_charged_micro_usd": sum(x["retained_charge_micro_usd"] for x in rows),
            "estimated_completed_micro_usd": sum(
                x.get("estimated_actual_micro_usd") or 0 for x in rows
            ),
        }


def payload(turns, schema):
    return {
        "model": "deepseek-flash",
        "input": [{"role": t.role, "content": t.content} for t in turns],
        "reasoning": {"effort": "none"},
        "temperature": 0,
        "max_output_tokens": 256,
        "stream": False,
        "text": {"format": {"type": "json_schema", "name": "pactlens_response", "schema": schema}},
    }


def request_budget(turns, role, *, require=True, schema=None):
    schema = (AGENT_SCHEMA if role == "agent" else RESPONSE_SCHEMA) if schema is None else schema
    # Same binding heuristic, applied conservatively to the complete serialized
    # request including native schema and generation controls. No exact-token claim.
    wire = canonical_json(payload(turns, schema))
    fn = require_budget if require else token_preflight
    return fn((Turn("user", wire),), limit=2000 if role == "agent" else 4096)


def _http(method, path, body, timeout):
    connection = http.client.HTTPSConnection(HOST, 443, timeout=timeout)
    dispatched = False
    try:
        connection.connect()
        dispatched = True  # Conservative: any write may have reached the provider.
        connection.request(
            method,
            path,
            body=body,
            headers={
                "Authorization": "Bearer " + configured_key(),
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        raw = response.read(262145)
        if len(raw) > 262144:
            raise ProviderFailure("PROVIDER_RESPONSE_BOUND", uncertain=True)
        if response.status != 200:
            code = {
                400: "UNSUPPORTED_SCHEMA_OR_REQUEST",
                401: "AUTHENTICATION_FAILURE",
                403: "PERMISSION_FAILURE",
                429: "RATE_LIMIT",
            }.get(
                response.status, "REDIRECT_DENIED" if 300 <= response.status < 400 else "HTTP_ERROR"
            )
            raise ProviderFailure(code, uncertain=response.status >= 500)
        try:
            data = closed_json(raw.decode("utf-8"), 262144)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise ProviderFailure("INVALID_PROVIDER_JSON", uncertain=True) from None
        return data
    except ProviderFailure:
        raise
    except TimeoutError:
        raise ProviderFailure(
            "READ_TIMEOUT" if dispatched else "CONNECT_TIMEOUT", uncertain=dispatched
        ) from None
    except (OSError, http.client.HTTPException):
        raise ProviderFailure(
            "UNCERTAIN_REQUEST_OUTCOME" if dispatched else "CONNECTION_FAILURE",
            uncertain=dispatched,
        ) from None
    finally:
        connection.close()


def available_models():
    body = _http("GET", "/models", None, 20)
    try:
        names = [x["id"] for x in body["data"]]
        if any(type(x) is not str or len(x) > 128 for x in names):
            raise ValueError
        return names
    except (KeyError, TypeError, ValueError):
        raise ProviderFailure("INVALID_MODELS_RESPONSE") from None


def profile_5a1():
    from pactlens.research.native_detector import SCHEMA_HASH

    return {
        **PROFILE,
        "version": "phase5a1-native-v1",
        "agent_prompt": "pactlens-agent-v3.3-candidate",
        "detector_schema_hash": SCHEMA_HASH,
        "citations": "packet-bound-f-index-max4",
        "rationale_max_characters": 80,
    }


class DeepSeekProvider:
    def __init__(self, ledger, role, *, context_id="engineering-default", profile="phase4e"):
        if type(ledger) is not CampaignLedger or role not in ("agent", "detector"):
            raise ValueError("TRUSTED_CAMPAIGN_REQUIRED")
        self.ledger, self.role, self.blocked = ledger, role, False
        if profile not in ("phase4e", "phase5a1"):
            raise ValueError("UNREVIEWED_PROVIDER_PROFILE")
        self.profile = PROFILE if profile == "phase4e" else profile_5a1()
        if self.profile != ledger.profile:
            raise ValueError("LEDGER_PROFILE_BINDING")
        if type(context_id) is not str or not 1 <= len(context_id) <= 128:
            raise ValueError("CONTEXT_ID")
        self.context_id = context_id
        self.config = ModelConfig(
            "deepseek-flash",
            "phase4e-responses-nonthinking-v1",
            "deepseek_responses",
            seed_support="UNSUPPORTED",
        )
        if profile == "phase5a1":
            from dataclasses import replace

            self.config = replace(self.config, revision="phase5a1-native-nonthinking-v1")
        self.returned_model = None

    async def generate(self, request):
        if self.blocked:
            raise ProviderFailure("PROFILE_STOPPED_NO_FALLBACK")
        if self.role == "agent" and getattr(request, "prompt_version", None) != self.profile.get(
            "agent_prompt", "pactlens-agent-v3.2-deepseek-candidate"
        ):
            raise ValueError("REVIEWED_DEEPSEEK_PROMPT_REQUIRED")
        schema = AGENT_SCHEMA if self.role == "agent" else RESPONSE_SCHEMA
        if self.role == "detector" and self.profile.get("version") == "phase5a1-native-v1":
            from pactlens.research.native_detector import schema_for

            schema = schema_for(request.citation_keys)
        try:
            budget = request_budget(request.turns, self.role, schema=schema)
        except BudgetExceeded:
            self.blocked = True
            raise
        body = canonical_json(payload(request.turns, schema)).encode("utf-8")
        identity = content_hash(
            {
                "request": request,
                "role": self.role,
                "profile": self.profile,
                "context_id": self.context_id,
            }
        )
        try:
            call_id = self.ledger.reserve(
                self.role,
                identity,
                budget,
                context_id=self.context_id if self.profile.get("version") else None,
            )
        except ProviderFailure:
            self.blocked = True
            raise
        started = time.monotonic_ns()
        metadata = {}
        metadata["request_sha256"] = hashlib.sha256(body).hexdigest()
        metadata["schema_hash"] = content_hash(schema)
        try:
            data = await asyncio.to_thread(
                _http, "POST", "/responses", body, self.config.timeout_seconds
            )
            try:
                response = self.decode(data, (time.monotonic_ns() - started) // 1000, metadata)
            except (KeyError, TypeError, AttributeError, ValueError):
                raise ProviderFailure("INVALID_RESPONSE_ENVELOPE", uncertain=True) from None
            self.ledger.finish(call_id, {**metadata, "status": "COMPLETED"})
            return response
        except ProviderFailure as error:
            self.blocked = True
            self.ledger.finish(
                call_id,
                {
                    **metadata,
                    "status": "FAILED_OR_UNKNOWN",
                    "error": error.code,
                    "uncertain": error.uncertain,
                    "latency_us": (time.monotonic_ns() - started) // 1000,
                },
            )
            raise
        except asyncio.CancelledError:
            # The thread may still finish remotely; reservation remains Unknown.
            self.blocked = True
            raise

    def decode(self, data, latency, metadata):
        if type(data) is not dict:
            raise ProviderFailure("INVALID_RESPONSE_ENVELOPE", uncertain=True)
        request_id, model, usage = data.get("id"), data.get("model"), data.get("usage")
        if type(request_id) is not str or not 1 <= len(request_id) <= 256:
            raise ProviderFailure("MISSING_PROVIDER_REQUEST_ID", uncertain=True)
        metadata["provider_request_id"] = request_id
        if type(model) is not str or len(model) > 128:
            raise ProviderFailure("MISSING_MODEL_IDENTITY", uncertain=True)
        metadata["returned_model"] = model
        with self.ledger.connect() as db:
            prior = {
                json.loads(x[0]).get("returned_model")
                for x in db.execute("SELECT metadata FROM calls")
            }
        prior.discard(None)
        if (prior and prior != {model}) or model not in (
            "deepseek-flash",
            PRICING["served_model_documented"],
        ):
            raise ProviderFailure("MODEL_IDENTITY_CHANGED", uncertain=True)
        self.returned_model = model
        if type(usage) is not dict or any(
            type(usage.get(k)) is not int or not 0 <= usage[k] <= 1_000_000
            for k in ("input_tokens", "output_tokens", "total_tokens")
        ):
            raise ProviderFailure("MISSING_OR_INVALID_USAGE", uncertain=True)
        if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
            raise ProviderFailure("USAGE_INCONSISTENT", uncertain=True)
        metadata.update(
            {
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "total_tokens": usage["total_tokens"],
                "estimated_actual_micro_usd": estimated_micro_usd(
                    usage["input_tokens"], usage["output_tokens"]
                ),
                "latency_us": latency,
            }
        )
        reasoning = usage.get("output_tokens_details", {}).get("reasoning_tokens")
        metadata["reasoning_tokens"] = reasoning
        # Bounded measurements survive incomplete output. No raw text is exported.
        visible = [
            p["text"]
            for o in data.get("output", [])
            if type(o) is dict
            for p in o.get("content", [])
            if type(p) is dict and p.get("type") == "output_text" and type(p.get("text")) is str
        ]
        if len(visible) == 1:
            metadata.update(
                output_characters=len(visible[0]),
                output_utf8_bytes=len(visible[0].encode("utf-8")),
                raw_response_hash=content_hash(visible[0]),
            )
        metadata["finish_reason"] = (
            "stop"
            if data.get("status") == "completed"
            else "length"
            if data.get("status") == "incomplete"
            else "unknown"
        )
        if reasoning not in (None, 0):
            raise ProviderFailure("UNEXPECTED_REASONING_TOKENS", uncertain=True)
        if usage["input_tokens"] > (2000 if self.role == "agent" else 4096):
            raise ProviderFailure("ACTUAL_INPUT_BUDGET_EXCEEDED", uncertain=True)
        if data.get("status") == "incomplete" or usage["output_tokens"] > 256:
            raise ProviderFailure("OUTPUT_SCHEMA_BUDGET_INFEASIBLE", uncertain=True)
        if data.get("status") != "completed":
            raise ProviderFailure("INCOMPLETE_OR_FAILED_GENERATION", uncertain=True)
        texts = []
        for output in data.get("output", []):
            if output.get("type") == "reasoning":
                raise ProviderFailure("UNEXPECTED_REASONING_OUTPUT", uncertain=True)
            if output.get("type") != "message" or output.get("role") != "assistant":
                raise ProviderFailure("UNEXPECTED_OUTPUT_TYPE", uncertain=True)
            for part in output.get("content", []):
                if part.get("type") == "refusal":
                    raise ProviderFailure("MODEL_REFUSAL")
                if part.get("type") != "output_text" or type(part.get("text")) is not str:
                    raise ProviderFailure("INVALID_OUTPUT_CONTENT", uncertain=True)
                texts.append(part["text"])
        if len(texts) != 1 or not texts[0].strip():
            raise ProviderFailure("EMPTY_OR_MULTIPART_OUTPUT", uncertain=True)
        metadata["output_characters"] = len(texts[0])
        metadata["output_utf8_bytes"] = len(texts[0].encode("utf-8"))
        metadata["raw_response_hash"] = content_hash(texts[0])
        metadata["finish_reason"] = "stop"
        try:
            closed_json(texts[0], 4096)
            return ModelResponse(
                texts[0], latency, usage["input_tokens"], usage["output_tokens"], "stop"
            )
        except (ValueError, TypeError, RecursionError):
            raise ProviderFailure("INVALID_MODEL_JSON", uncertain=False) from None
