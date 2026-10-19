"""Deterministic offline transcripts for Phase 4C context tests; never model output."""

import json
import re

from harness_helpers import FakeModel

from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.arena.allocation import lawful_reference
from pactlens.arena.generator import generate_task
from pactlens.arena.models import ArenaConfig
from pactlens.research.fixtures import fixture_task
from pactlens.serialization import canonical_json

# Pre-edit HEAD digests of every v1/v2 request turn sequence (fake N3/C+ runs, group
# ENG-golden-v1, synthetic counter 500, public message transform), captured before
# Phase 4C edits. Equality proves historical prompt construction is unchanged.
GOLDEN_TURNS = {
    ("pactlens-agent-v1", "N3"): "c5e6b88f1a409954136fde159aa1f7a77929f5b74f263d918da32a54e8a63be8",
    ("pactlens-agent-v1", "C+"): "d4394d46dc0b29cfeb4b53c5f82e7310f57c6e455f24fa46306593535909c860",
    (
        "pactlens-agent-v2-candidate",
        "N3",
    ): "9a00455d9f6042ff962442640fb2f71d26a72babe70945a75df3aa2d05dbbddd",
    (
        "pactlens-agent-v2-candidate",
        "C+",
    ): "3ea193f088075cc61dd5b4050c4ac98c84b2830ed4ac5327f03fcf65e5df3d63",
}


def historical_text(task, actor, round_number=1):
    """Byte shape of the three Phase 4B v2 round-1 responses (lawful, no message).

    Validation scripts confirm the reconstructed digests equal the private trace's
    response digests; the private trace itself is never read by tests.
    """
    rows = ",\n".join(f'    {{"agent_id": "a{n}", "incident_id": "i{n}"}}' for n in range(3))
    return (
        "{\n"
        f'  "actor_id": "{actor}",\n'
        f'  "round_number": {round_number},\n'
        f'  "task_hash": "{task.task_hash}",\n'
        '  "decision": "submit",\n'
        '  "assignments": [\n' + rows + "\n  ],\n"
        '  "end_step": true,\n'
        '  "message": null\n'
        "}"
    )


class HistoricalTranscript:
    """Replays the historical response shape for every request; offline only."""

    config = ModelConfig(
        "offline-reconstruction", "phase4b-v2-shape", seed_support="FAKE_DETERMINISTIC"
    )

    def __init__(self, task):
        self.task = task
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return ModelResponse(
            historical_text(self.task, request.actor_id, request.round_number),
            1,
            None,
            None,
            "stop",
        )


class Counted(FakeModel):
    def count_input_tokens(self, turns):
        return 500  # synthetic counter seam only; lets v2 reach round 2 for comparison


def observation(request):
    return json.loads(request.turns[-1].content)


def private_peer(request):
    """Peer named in the actor's own private brief (C+/C−/N2 pair actors)."""
    found = re.search(r"coordinate with (\w+)", request.turns[0].content)
    return None if found is None else found.group(1)


def speaker(pattern, length=24, char="x"):
    """Scripted speech: pattern none|r1|pair|all; text exactly `length` characters."""

    def transform(body, request):
        peers = [a for a in ("a0", "a1", "a2") if a != request.actor_id]
        peer = private_peer(request)
        if (
            pattern == "none"
            or (pattern == "r1" and request.round_number != 1)
            or (pattern == "pair" and peer is None)
        ):
            return
        text = (f"{request.actor_id}-r{request.round_number}:" + char * length)[:length]
        body["message"] = (
            {"channel": "private", "recipients": [peer], "text": text}
            if peer is not None
            else {"channel": "public", "recipients": peers, "text": text}
        )

    return transform


def largest_generated_task(seeds=200):
    """Largest public 5-incident task among the first generator seeds (stress only)."""
    return max(
        (generate_task(s, ArenaConfig(incident_count=5)) for s in range(seeds)),
        key=lambda t: len(canonical_json(t)),
    )


def lawful_body(task, request):
    return {
        "actor_id": request.actor_id,
        "round_number": request.round_number,
        "task_hash": task.task_hash,
        "decision": "submit",
        "assignments": [
            {"incident_id": r.incident_id, "agent_id": r.agent_id}
            for r in lawful_reference(task).assignments
        ],
        "message": None,
        "end_step": True,
    }


__all__ = [
    "GOLDEN_TURNS",
    "Counted",
    "HistoricalTranscript",
    "fixture_task",
    "historical_text",
    "largest_generated_task",
    "lawful_body",
    "observation",
    "private_peer",
    "speaker",
]
