"""Separate observed behavior from private assignment and pending adjudication."""

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise

from pactlens.arena.allocation import measure_costs
from pactlens.arena.models import ArenaState, Lifecycle, identifier, integer, validate_state
from pactlens.arena.outcomes import validate_outcome
from pactlens.research.adjudication import AdjudicationRecord
from pactlens.research.manifest import EpisodeManifest
from pactlens.serialization import content_hash


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
class CapturedEvent:
    """Host-recorded logical position bound to one observable source fact.

    The digest detects inconsistent reconstruction, not a malicious host rewriting
    both fact and journal. Equal positions across streams mean unresolved order.
    """

    source: str
    sequence: int
    logical_position: int
    source_digest: str

    def __post_init__(self):
        if self.source not in ("message", "arena", "outcome"):
            raise ValueError("Unknown observable event source")
        integer(self.sequence, 1, {"message": 1024, "arena": 9, "outcome": 1}[self.source])
        integer(self.logical_position, 1, 4096)
        if (
            type(self.source_digest) is not str
            or re.fullmatch("[a-f0-9]{64}", self.source_digest) is None
        ):
            raise ValueError("Invalid observable source digest")


def observable_facts(state: ArenaState, messages: tuple[Message, ...]) -> dict:
    """Internal bindings only; projection separately allowlists every public field."""
    facts = {("message", m.event_order): (m.round_number, content_hash(m)) for m in messages}
    proposals = {(p.round_number, p.agent_id): p for p in state.proposals}
    for event in state.history:
        payload = {"transition": event}
        if event.kind == "PROPOSAL_ACCEPTED":
            payload["proposal"] = proposals[(event.round_number, event.actor_id)]
        elif event.kind == "FINALIZED":
            payload["allocation"] = state.final_allocation
        facts[("arena", event.sequence)] = (event.round_number, content_hash(payload))
    if state.status == Lifecycle.FINALIZED:
        facts[("outcome", 1)] = (2, content_hash(measure_costs(state.task, state.final_allocation)))
    return facts


def _capture(journal, source, sequence, digest, logical_position):
    if type(journal) is not tuple or any(type(e) is not CapturedEvent for e in journal):
        raise ValueError("Immutable capture journal required")
    position = (
        logical_position
        if logical_position is not None
        else (journal[-1].logical_position + 1 if journal else 1)
    )
    event = CapturedEvent(source, sequence, position, digest)
    if any((e.source, e.sequence) == (source, sequence) for e in journal):
        raise ValueError("Duplicate captured event")
    if journal and position < journal[-1].logical_position:
        raise ValueError("Capture positions must be nondecreasing")
    return (*journal, event)


def capture_message(state, message, journal=(), *, logical_position=None):
    validate_state(state)
    if type(message) is not Message:
        raise ValueError("Observed Message required")
    message.__post_init__()
    known = {a.agent_id for a in state.task.agents}
    if (
        state.status not in (Lifecycle.ROUND_1, Lifecycle.ROUND_2)
        or message.round_number != state.round_number
        or message.sender not in known
        or not set(message.recipients) <= known
    ):
        raise ValueError("Message must be captured in its open round")
    return _capture(
        journal, "message", message.event_order, content_hash(message), logical_position
    )


def capture_transition(state, journal=(), *, logical_position=None):
    validate_state(state)
    if not state.history:
        raise ValueError("No transition to capture")
    sequence = state.history[-1].sequence
    digest = observable_facts(state, ())[("arena", sequence)][1]
    return _capture(journal, "arena", sequence, digest, logical_position)


def capture_outcome(state, journal=(), *, logical_position=None):
    validate_state(state)
    if state.status != Lifecycle.FINALIZED:
        raise ValueError("No final public outcome to capture")
    digest = observable_facts(state, ())[("outcome", 1)][1]
    return _capture(journal, "outcome", 1, digest, logical_position)


def validate_journal(state, messages, journal):
    if journal is None:
        return
    if type(journal) is not tuple or len(journal) > 1034:
        raise ValueError("Bounded immutable capture journal required")
    facts = observable_facts(state, messages)
    positions = {}
    previous = 0
    for event in journal:
        if type(event) is not CapturedEvent:
            raise ValueError("CapturedEvent required")
        event.__post_init__()
        key = (event.source, event.sequence)
        if key in positions or key not in facts or facts[key][1] != event.source_digest:
            raise ValueError("Capture source mismatch")
        if event.logical_position < previous:
            raise ValueError("Capture positions must be nondecreasing")
        positions[key] = previous = event.logical_position
    for source in ("message", "arena"):
        ordered = [positions[k] for k in sorted(positions) if k[0] == source]
        if any(a >= b for a, b in pairwise(ordered)):
            raise ValueError("Capture contradicts source-local order")
    for message in messages:
        position = positions.get(("message", message.event_order))
        if position is None:
            continue
        for event in state.history:
            anchor = positions.get(("arena", event.sequence))
            if anchor is None:
                continue
            before = event.kind == "STARTED" or event.round_number < message.round_number
            after = (
                event.kind == "FINALIZED"
                or event.round_number > message.round_number
                or (event.kind == "ROUND_CLOSED" and message.round_number == 1)
            )
            if (before and anchor > position) or (after and anchor < position):
                raise ValueError("Capture contradicts message round")
    outcome = positions.get(("outcome", 1))
    if outcome is not None and any(
        position > outcome for (source, _), position in positions.items() if source != "outcome"
    ):
        raise ValueError("Outcome precedes prerequisite observations")


@dataclass(frozen=True)
class EpisodeRecord:
    state: ArenaState
    messages: tuple[Message, ...] = ()
    messages_complete: bool = True
    manifest: EpisodeManifest | None = field(default=None, repr=False)
    adjudication: AdjudicationRecord | None = field(default=None, repr=False)
    private_metadata: object = field(default=None, repr=False)
    source_path: str | None = field(default=None, repr=False)
    event_journal: tuple[CapturedEvent, ...] | None = None

    def __post_init__(self):
        if type(self.state) is not ArenaState or type(self.messages_complete) is not bool:
            raise ValueError("State and observation completeness required")
        validate_state(self.state)
        if type(self.messages) is not tuple or any(type(m) is not Message for m in self.messages):
            raise ValueError("Immutable observed messages required")
        orders = [m.event_order for m in self.messages]
        if len(set(orders)) != len(orders):
            raise ValueError("Message event order must be unique")
        known = {a.agent_id for a in self.state.task.agents}
        if any(m.sender not in known or not set(m.recipients) <= known for m in self.messages):
            raise ValueError("Unknown observed message actor")
        for message in self.messages:
            message.__post_init__()
        rounds = [m.round_number for m in sorted(self.messages, key=lambda m: m.event_order)]
        if rounds != sorted(rounds) or any(r > self.state.round_number for r in rounds):
            raise ValueError("Messages contradict arena rounds")
        if self.adjudication is not None:
            if type(self.adjudication) is not AdjudicationRecord:
                raise ValueError("Typed adjudication record required")
            if self.state.status != Lifecycle.FINALIZED:
                raise ValueError("Stored outcome requires finalized state")
            validate_outcome(
                self.state.task, self.state.final_allocation, self.adjudication.mechanical_outcome
            )
        validate_journal(self.state, self.messages, self.event_journal)


@dataclass(frozen=True)
class DetectorEvidence:
    """Owns only a JSON string; never retains a reference to private source objects."""

    json_text: str

    def to_json(self) -> str:
        return self.json_text

    def as_mapping(self) -> dict:
        return json.loads(self.json_text)  # defensive copy, not the source record
