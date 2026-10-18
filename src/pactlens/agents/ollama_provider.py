"""Only numeric loopback HTTP, no proxies, redirects, credentials or downloads.

Ollama can expose cloud models locally. Exact installed metadata is checked before
each call and cloud/remote model metadata is rejected. Host is trusted to run an
honest local Ollama server; loopback alone cannot prove its implementation.
"""

import asyncio
import http.client
import ipaddress
import json
import os
import re
import time
from urllib.parse import urlsplit

from pactlens.agents.models import closed_json
from pactlens.agents.provider import ModelConfig, ModelResponse


def local_address(url):
    if type(url) is not str:
        raise ValueError("EXPLICIT_LOCAL_URL_REQUIRED")
    parsed = urlsplit(url)
    try:
        numeric = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError:
        raise ValueError("NUMERIC_LOOPBACK_REQUIRED") from None
    if (
        parsed.scheme != "http"
        or not numeric.is_loopback
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/v1"
    ):
        raise ValueError("LOOPBACK_HTTP_V1_ONLY")
    return parsed.hostname, port


class OllamaProvider:
    def __init__(self, url, config, *, transport=None):
        self.address = local_address(url)
        if type(config) is not ModelConfig or config.endpoint_type != "ollama_loopback_openai":
            raise ValueError("OLLAMA_CONFIG_REQUIRED")
        if (
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", config.model) is None
            or "cloud" in config.model.lower()
        ):
            raise ValueError("LOCAL_MODEL_NAME_REQUIRED")
        self.config = config
        self._transport = transport or self._http
        self.calls = 0

    @classmethod
    def from_environment(cls):
        url = os.environ.get("PACTLENS_OLLAMA_BASE_URL")
        model = os.environ.get("PACTLENS_OLLAMA_MODEL")
        if not url or not model:
            raise ValueError("SET_PACTLENS_OLLAMA_BASE_URL_AND_MODEL")
        provisional = cls(url, ModelConfig(model, "UNCONFIRMED", "ollama_loopback_openai"))
        identity = provisional.readiness(require_revision=False)
        return cls(url, ModelConfig(model, identity["model_digest"], "ollama_loopback_openai"))

    def _http(self, method, path, body=None):
        connection = http.client.HTTPConnection(*self.address, timeout=self.config.timeout_seconds)
        try:
            connection.request(
                method,
                path,
                body=None if body is None else json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            result = connection.getresponse()
            raw = result.read(131073)
            if result.status != 200 or len(raw) > 131072:
                raise ValueError("LOCAL_HTTP_FAILURE_OR_BOUND")
            return closed_json(raw.decode("utf-8"), 131072)
        finally:
            connection.close()

    def readiness(self, *, require_revision=True):
        version = self._transport("GET", "/api/version")
        tags = self._transport("GET", "/api/tags")
        found = [m for m in tags.get("models", []) if m.get("name") == self.config.model]
        if len(found) != 1 or any(key in found[0] for key in ("remote_host", "remote_model")):
            raise ValueError("EXACT_INSTALLED_LOCAL_MODEL_REQUIRED")
        model = found[0]
        digest = model.get("digest")
        if type(digest) is not str or re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", digest) is None:
            raise ValueError("MODEL_DIGEST_REQUIRED")
        # /api/show catches remote metadata not consistently exposed by /api/tags.
        detail = self._transport("POST", "/api/show", {"model": self.config.model})
        if (
            any(k in detail for k in ("remote_host", "remote_model"))
            or "cloud" in str(model.get("details", {})).lower()
            or "cloud" in str(detail.get("details", {})).lower()
        ):
            raise ValueError("REMOTE_MODEL_FORBIDDEN")
        server_version = version.get("version")
        if type(server_version) is not str or len(server_version) > 128:
            raise ValueError("OLLAMA_VERSION_REQUIRED")
        if require_revision and digest != self.config.revision:
            raise ValueError("MODEL_REVISION_CHANGED")
        return {
            "endpoint_type": self.config.endpoint_type,
            "server_version": server_version,
            "model": self.config.model,
            "model_digest": digest,
            "seed_support": "REQUESTED_NOT_VERIFIED",
            "cloud_model": False,
        }

    async def generate(self, request):
        # to_thread waits for this bounded network operation; generation never dispatches tools.
        return await asyncio.to_thread(self._generate, request)

    def _generate(self, request):
        self.readiness()
        start = time.monotonic_ns()
        body = {
            "model": self.config.model,
            "messages": [{"role": t.role, "content": t.content} for t in request.turns],
            "stream": False,
            "temperature": self.config.temperature_milli / 1000,
            "max_tokens": self.config.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        if self.config.seed_support != "UNSUPPORTED":
            body["seed"] = request.seed
        self.calls += 1
        response = self._transport("POST", "/v1/chat/completions", body)
        if response.get("model") != self.config.model:
            raise ValueError("RESPONSE_MODEL_MISMATCH")
        choices = response.get("choices")
        if type(choices) is not list or len(choices) != 1:
            raise ValueError("ONE_COMPLETION_REQUIRED")
        usage = response.get("usage") or {}
        reason = choices[0].get("finish_reason", "unknown")
        return ModelResponse(
            choices[0]["message"]["content"],
            (time.monotonic_ns() - start) // 1000,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            reason,
        )
