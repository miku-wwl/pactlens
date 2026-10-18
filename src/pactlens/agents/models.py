"""Closed model protocol and immutable actor-local conversation values."""

import json
from dataclasses import dataclass

from pactlens.arena.models import Proposal, integer
from pactlens.arena.transitions import submit_proposal
from pactlens.evidence.records import Channel


def closed_json(raw, maximum=4096):
    def no_nonfinite(value):
        raise ValueError("NONFINITE_JSON")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_KEY")
            result[key] = value
        return result

    if type(raw) is not str or len(raw.encode("utf-8", errors="strict")) > maximum:
        raise ValueError("RESPONSE_BOUND")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=no_nonfinite)


@dataclass(frozen=True)
class MessageIntent:
    channel: Channel
    recipients: tuple[str, ...]
    text: str

    def __post_init__(self):
        if (
            type(self.channel) is not Channel
            or type(self.recipients) is not tuple
            or not 1 <= len(self.recipients) <= 2
            or any(type(a) is not str for a in self.recipients)
            or len(set(self.recipients)) != len(self.recipients)
            or type(self.text) is not str
            or not 1 <= len(self.text) <= 256
            or len(self.text.encode("utf-8", errors="strict")) > 1024
        ):
            raise ValueError("MESSAGE_SYNTAX")


@dataclass(frozen=True)
class Decision:
    proposal: Proposal | None
    message: MessageIntent | None


def parse_decision(raw, *, state, actor_id):
    body = closed_json(raw)
    if type(body) is not dict or set(body) != {
        "actor_id",
        "round_number",
        "task_hash",
        "decision",
        "assignments",
        "message",
        "end_step",
    }:
        raise ValueError("DECISION_FIELDS")
    integer(body["round_number"], 1, 2)
    if (
        body["actor_id"] != actor_id
        or body["round_number"] != state.round_number
        or body["task_hash"] != state.task.task_hash
        or body["end_step"] is not True
    ):
        raise ValueError("DECISION_CONTEXT")
    if body["decision"] == "submit":
        proposal = Proposal.from_mapping(
            {
                "agent_id": actor_id,
                "round_number": state.round_number,
                "task_hash": state.task.task_hash,
                "assignments": body["assignments"],
            }
        )
        # Dry validation, never apply a model proposal without a verified AIG receipt.
        submit_proposal(state, proposal, actor_id=actor_id, expected_revision=state.revision)
    elif body["decision"] == "decline" and body["assignments"] is None:
        proposal = None
    else:
        raise ValueError("DECISION_CHOICE")
    message = body["message"]
    if message is not None:
        if type(message) is not dict or set(message) != {"channel", "recipients", "text"}:
            raise ValueError("MESSAGE_FIELDS")
        if type(message["recipients"]) is not list:
            raise ValueError("MESSAGE_RECIPIENTS")
        message = MessageIntent(
            Channel(message["channel"]), tuple(message["recipients"]), message["text"]
        )
    return Decision(proposal, message)


@dataclass(frozen=True)
class Turn:
    role: str
    content: str


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    private_instruction: str
    history: tuple[Turn, ...] = ()

    def __post_init__(self):
        if type(self.history) is not tuple or any(type(t) is not Turn for t in self.history):
            raise ValueError("IMMUTABLE_HISTORY")
