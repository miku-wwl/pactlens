"""Provider-neutral generation port. One attempt, no inference retries."""

from dataclasses import dataclass
from typing import Protocol

from pactlens.agents.budgets import TokenBudget
from pactlens.agents.models import Turn
from pactlens.arena.models import integer


@dataclass(frozen=True)
class ModelConfig:
    model: str
    revision: str
    endpoint_type: str = "offline_fake"
    temperature_milli: int = 0
    max_output_tokens: int = 256
    timeout_seconds: int = 60
    max_attempts: int = 1
    seed_support: str = "REQUESTED_NOT_VERIFIED"

    def __post_init__(self):
        for value in (self.model, self.revision):
            if type(value) is not str or not 1 <= len(value) <= 256:
                raise ValueError("MODEL_ID_REQUIRED")
        if self.endpoint_type not in (
            "offline_fake",
            "ollama_loopback_openai",
            "deepseek_responses",
        ):
            raise ValueError("EXPLICIT_PROVIDER_REQUIRED")
        integer(self.temperature_milli, 0, 1000)
        integer(self.max_output_tokens, 1, 256)
        integer(self.timeout_seconds, 1, 120)
        if type(self.max_attempts) is not int or self.max_attempts != 1:
            raise ValueError("NO_RETRIES_BUDGETED")
        if self.seed_support not in ("REQUESTED_NOT_VERIFIED", "UNSUPPORTED", "FAKE_DETERMINISTIC"):
            raise ValueError("SEED_SUPPORT")


@dataclass(frozen=True)
class ModelRequest:
    actor_id: str
    round_number: int
    turns: tuple[Turn, ...]
    seed: int
    prompt_version: str = "pactlens-agent-v1"
    derived_seed: int | None = None
    seed_mapping: str = "UNSIGNED64_LOW63_V1"
    protocol_version: str = "pactlens-decision-v1"
    prompt_hash: str | None = None
    protocol_hash: str | None = None
    token_budget: TokenBudget | None = None

    def __post_init__(self):
        integer(self.seed, 0, (1 << 63) - 1)
        if self.derived_seed is not None:
            integer(self.derived_seed, 0, (1 << 64) - 1)
            if self.seed != self.derived_seed & ((1 << 63) - 1):
                raise ValueError("SEED_MAPPING")
        if self.seed_mapping != "UNSIGNED64_LOW63_V1":
            raise ValueError("SEED_MAPPING")
        if type(self.turns) is not tuple or any(type(t) is not Turn for t in self.turns):
            raise ValueError("IMMUTABLE_TURNS")
        if self.protocol_version not in ("pactlens-decision-v1", "pactlens-decision-v2-candidate"):
            raise ValueError("PROTOCOL_VERSION")
        for digest in (self.prompt_hash, self.protocol_hash):
            if digest is not None and (
                type(digest) is not str
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("PROMPT_PROTOCOL_HASH")
        if self.token_budget is not None:
            if type(self.token_budget) is not TokenBudget:
                raise ValueError("TOKEN_BUDGET_TYPE")
            self.token_budget.__post_init__()
        if (
            self.prompt_version
            in (
                "pactlens-agent-v3-candidate",
                "pactlens-agent-v3.1-candidate",
                "pactlens-agent-v3.2-deepseek-candidate",
                "pactlens-agent-v3.3-candidate",
            )
            and self.protocol_version != "pactlens-decision-v2-candidate"
        ):
            # The v3 context candidate reuses the unchanged v2 decision protocol.
            raise ValueError("CANDIDATE_REQUEST_BINDING")
        if self.protocol_version == "pactlens-decision-v2-candidate" and (
            self.prompt_version
            not in (
                "pactlens-agent-v2-candidate",
                "pactlens-agent-v3-candidate",
                "pactlens-agent-v3.1-candidate",
                "pactlens-agent-v3.2-deepseek-candidate",
                "pactlens-agent-v3.3-candidate",
            )
            or self.prompt_hash is None
            or self.protocol_hash is None
            or self.token_budget is None
            or not self.token_budget.fits
        ):
            raise ValueError("CANDIDATE_REQUEST_BINDING")


@dataclass(frozen=True)
class ModelResponse:
    text: str
    latency_us: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str = "unknown"

    def __post_init__(self):
        if type(self.text) is not str or len(self.text.encode("utf-8")) > 4096:
            raise ValueError("RESPONSE_BOUND")
        integer(self.latency_us, 0, 1_000_000_000)
        for count in (self.input_tokens, self.output_tokens):
            if count is not None:
                integer(count, 0, 1_000_000)
        if self.finish_reason not in ("stop", "length", "unknown"):
            raise ValueError("FINISH_REASON")


class ModelProvider(Protocol):
    config: ModelConfig

    async def generate(self, request: ModelRequest) -> ModelResponse: ...
