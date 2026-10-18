"""Deterministic fake generation only; all effects use real installed AIG."""

import json

from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.aig.submission import TestConsent as Consent
from pactlens.arena.allocation import lawful_reference
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json


class FakeModel:
    config = ModelConfig("offline-fixture", "fake-v1", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, task, transform=None):
        self.task = task
        self.requests = []
        self.transform = transform

    async def generate(self, request):
        self.requests.append(request)
        body = {
            "actor_id": request.actor_id,
            "round_number": request.round_number,
            "task_hash": self.task.task_hash,
            "decision": "submit",
            "assignments": [
                {"incident_id": r.incident_id, "agent_id": r.agent_id}
                for r in lawful_reference(self.task).assignments
            ],
            "message": None,
            "end_step": True,
        }
        if self.transform:
            result = self.transform(body, request)
            if isinstance(result, Exception):
                raise result
            if isinstance(result, str):
                return ModelResponse(result, 1)
        return ModelResponse(canonical_json(body), 1, 100, 120, "stop")


async def run_fake(path, task, *, condition=Condition.N3, transform=None, **kwargs):
    provider = FakeModel(task, transform)
    result = await run_episode(
        path,
        task,
        EpisodeConfig("ENG-unit-v1", condition),
        provider,
        consent=kwargs.pop("consent", Consent(synthetic_consent=True)),
        **kwargs,
    )
    return result, provider


def message(body, request):
    body["message"] = {
        "channel": "public",
        "recipients": [a for a in ("a0", "a1", "a2") if a != request.actor_id],
        "text": f"observed-{request.actor_id}-{request.round_number}",
    }


def observation(request):
    return json.loads(request.turns[-1].content)
