"""Separate observed behavior from private assignment and pending adjudication."""

import json
from dataclasses import dataclass, field
from enum import StrEnum

from pactlens.arena.models import ArenaState, identifier, integer
from pactlens.research.adjudication import AdjudicationRecord
from pactlens.research.manifest import EpisodeManifest


class Channel(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass(frozen=True)
class Message:
    event_order: int
    round_number: int
    sender: str
    recipients: tuple[str, ...]
    channel: Channel
    text: str

    def __post_init__(self):
        integer(self.event_order, 1, 1024)
        integer(self.round_number, 1, 2)
        identifier(self.sender)
        if (
            type(self.recipients) is not tuple
            or not self.recipients
            or any(type(a) is not str for a in self.recipients)
            or len(set(self.recipients)) != len(self.recipients)
            or type(self.channel) is not Channel
        ):
            raise ValueError("Invalid observed message routing")
        for recipient in self.recipients:
            identifier(recipient)
        if (
            type(self.text) is not str
            or not 1 <= len(self.text) <= 1024
            or len(self.text.encode("utf-8", errors="strict")) > 4096
        ):
            raise ValueError("Message text must be bounded observed text")


@dataclass(frozen=True)
class EpisodeRecord:
    state: ArenaState
    messages: tuple[Message, ...] = ()
    messages_complete: bool = True
    manifest: EpisodeManifest | None = field(default=None, repr=False)
    adjudication: AdjudicationRecord | None = field(default=None, repr=False)
    private_metadata: object = field(default=None, repr=False)
    source_path: str | None = field(default=None, repr=False)

    def __post_init__(self):
        if type(self.state) is not ArenaState or type(self.messages_complete) is not bool:
            raise ValueError("State and observation completeness required")
        if type(self.messages) is not tuple or any(type(m) is not Message for m in self.messages):
            raise ValueError("Immutable observed messages required")
        orders = [m.event_order for m in self.messages]
        if len(set(orders)) != len(orders):
            raise ValueError("Message event order must be unique")
        known = {a.agent_id for a in self.state.task.agents}
        if any(m.sender not in known or not set(m.recipients) <= known for m in self.messages):
            raise ValueError("Unknown observed message actor")


@dataclass(frozen=True)
class DetectorEvidence:
    """Owns only a JSON string; never retains a reference to private source objects."""

    json_text: str

    def to_json(self) -> str:
        return self.json_text

    def as_mapping(self) -> dict:
        return json.loads(self.json_text)  # defensive copy, not the source record
