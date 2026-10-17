"""Reviewed authority and immutable proposal snapshots owned by PactLens."""

import json
from dataclasses import dataclass
from uuid import UUID

from agentic_intent_gate.runtime import ToolBinding

from pactlens.arena.models import (
    Agent,
    Allocation,
    ArenaConfig,
    ArenaState,
    Assignment,
    Incident,
    Lifecycle,
    Proposal,
    PublicTask,
    TransitionEvent,
)
from pactlens.arena.transitions import submit_proposal
from pactlens.serialization import canonical_json, content_hash


def uuid4_text(value):
    if type(value) is not str or str(UUID(value)) != value or UUID(value).version != 4:
        raise ValueError("Canonical UUIDv4 required")
    return value


def binding_for(scope):
    return ToolBinding(
        "submit_incident_proposal",
        "1",
        "pactlens-sqlite-v1",
        "proposal-v1",
        "incident-sim",
        uuid4_text(scope),
    )


ARGUMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "proposal_ref",
        "proposal_digest",
        "task_hash",
        "round_number",
        "state_digest",
        "expected_revision",
    ],
    "properties": {
        "proposal_ref": {
            "type": "string",
            "minLength": 36,
            "maxLength": 36,
            "pattern": "^[a-f0-9-]{36}$",
        },
        **{
            key: {"type": "string", "minLength": 64, "maxLength": 64, "pattern": "^[a-f0-9]{64}$"}
            for key in ("proposal_digest", "task_hash", "state_digest")
        },
        "round_number": {"type": "integer", "minimum": 1, "maximum": 2},
        "expected_revision": {"type": "integer", "minimum": 1, "maximum": 8},
    },
}


def restore_state(raw):
    """Closed reconstruction through original validated domain constructors."""
    data = json.loads(raw)
    task = data["task"]
    state = ArenaState(
        PublicTask(
            tuple(Agent(**{**a, "skills": tuple(a["skills"])}) for a in task["agents"]),
            tuple(
                Incident(
                    **{
                        **i,
                        "eligible_agents": None
                        if i["eligible_agents"] is None
                        else tuple(i["eligible_agents"]),
                    }
                )
                for i in task["incidents"]
            ),
            ArenaConfig(**task["config"]),
        ),
        Lifecycle(data["status"]),
        data["revision"],
        tuple(_proposal(p) for p in data["proposals"]),
        tuple(
            TransitionEvent(**{**e, "missing_agents": tuple(e["missing_agents"])})
            for e in data["history"]
        ),
        None if data["final_allocation"] is None else _allocation(data["final_allocation"]),
    )
    if canonical_json(state) != raw:
        raise ValueError("Noncanonical or unknown snapshot fields")
    return state


def _allocation(value):
    if set(value) != {"assignments"}:
        raise ValueError("Closed allocation required")
    return Allocation(tuple(Assignment(**row) for row in value["assignments"]))


def _proposal(value):
    return Proposal(**{**value, "allocation": _allocation(value["allocation"])})


@dataclass(frozen=True)
class PreparedProposal:
    reference: str
    state: ArenaState
    proposal: Proposal

    def __post_init__(self):
        uuid4_text(self.reference)
        if (
            len(canonical_json(self.state).encode("utf-8")) > 65536
            or len(canonical_json(self.proposal).encode("utf-8")) > 4096
        ):
            raise ValueError("Consumer snapshot exceeds bounded storage input")
        # Dry validation only: the resulting immutable state is not applied here.
        submit_proposal(
            self.state,
            self.proposal,
            actor_id=self.proposal.agent_id,
            expected_revision=self.state.revision,
        )

    @property
    def arguments(self):
        return {
            "proposal_ref": self.reference,
            "proposal_digest": content_hash(self.proposal),
            "task_hash": self.state.task.task_hash,
            "round_number": self.proposal.round_number,
            "state_digest": content_hash(self.state),
            "expected_revision": self.state.revision,
        }


class DeterministicProvider:
    """Synthetic engineering stand-in; output still passes real AIG validation."""

    def __init__(self, prepared):
        self.raw = canonical_json(
            {
                "goal": "Record one reviewed synthetic incident proposal",
                "target": "incident-sim",
                "risk_class": "SIDE_EFFECT",
                "steps": [
                    {
                        "tool_name": "submit_incident_proposal",
                        "tool_version": "1",
                        "arguments": prepared.arguments,
                    }
                ],
            }
        )

    async def generate_plan(self, intent, **kwargs):
        return self.raw


@dataclass(frozen=True)
class ObservedAction:
    """Detached fields from public APIs, never an AIG domain-object serialization."""

    actor_id: str
    round_number: int
    action_id: str
    action_version: int
    action_state: str
    approval_state: str
    authorized: bool
    payload_digest: str
    proposal_digest: str
    receipt_reference: str | None
    receipt_status: str
    synthetic_consent: bool
    logical_position: int | None = None
