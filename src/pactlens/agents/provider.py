"""Provider-neutral generation port. One attempt, no inference retries."""

from dataclasses import dataclass
from typing import Protocol

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
        if self.endpoint_type not in ("offline_fake", "ollama_loopback_openai"):
            raise ValueError("LOCAL_PROVIDER_ONLY")
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
