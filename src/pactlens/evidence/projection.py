"""Explicit L3 allowlist. No reflection, source __dict__, private metadata or paths."""

from pathlib import Path
from uuid import UUID

from pactlens.arena.allocation import measure_costs
from pactlens.arena.models import Lifecycle
from pactlens.evidence.records import DetectorEvidence, EpisodeRecord
from pactlens.serialization import canonical_json


def _public_id(value: str) -> str:
    if type(value) is not str:
        raise ValueError("Canonical independent UUIDv4 required")
    try:
        parsed = UUID(value)
    except ValueError:
        raise ValueError("Canonical independent UUIDv4 required") from None
    if str(parsed) != value or parsed.version != 4:
        raise ValueError("Canonical independent UUIDv4 required")
    return value


def project_evidence(record: EpisodeRecord, *, public_id: str) -> DetectorEvidence:
    if type(record) is not EpisodeRecord:
        raise TypeError("EpisodeRecord required")
    record.__post_init__()
    public_id = _public_id(public_id)
    state = record.state
    task = state.task
    agents = {a.agent_id: f"Actor-{n}" for n, a in enumerate(task.agents, start=1)}
    incidents = {i.incident_id: f"Incident-{n}" for n, i in enumerate(task.incidents, start=1)}

    def allocation_rows(allocation):
        return [
            {
                "incident": incidents[row.incident_id],
                "agent": None if row.agent_id is None else agents[row.agent_id],
            }
            for row in allocation.assignments
        ]

    public_task = {
        "agents": [
            {
                "id": agents[a.agent_id],
                "skills": list(a.skills),
                "capacity": a.capacity,
                "unit_cost": a.unit_cost,
                "speed": a.speed,
            }
            for a in task.agents
        ],
        "incidents": [
            {
                "id": incidents[i.incident_id],
                "workload": i.workload,
                "severity": i.severity,
                "required_skill": i.required_skill,
                "deadline": i.deadline,
                "sla_penalty": i.sla_penalty,
                "eligible_agents": (
                    None if i.eligible_agents is None else [agents[a] for a in i.eligible_agents]
                ),
            }
            for i in task.incidents
        ],
        "objective": {
            "revision": task.config.revision,
            "balance_weight": task.config.balance_weight,
            "unassigned_multiplier": task.config.unassigned_multiplier,
            "allow_unassigned": task.config.allow_unassigned,
        },
    }
    messages = {
        "status": "COMPLETE" if record.messages_complete else "INCOMPLETE",
        "records": [
            {
                "event_order": m.event_order,
                "round": m.round_number,
                "sender": agents[m.sender],
                "recipients": [agents[a] for a in sorted(m.recipients)],
                "channel": m.channel.value,
                "text": m.text,
            }
            for m in sorted(record.messages, key=lambda m: m.event_order)
        ],
    }
    proposals = {(p.round_number, p.agent_id): p for p in state.proposals}
    slots = []
    for round_number in (1, 2):
        reached = state.status != Lifecycle.CREATED and state.round_number >= round_number
        closed = state.status == Lifecycle.FINALIZED or state.round_number > round_number
        for agent in task.agents:
            proposal = proposals.get((round_number, agent.agent_id))
            status = (
                "SUBMITTED"
                if proposal
                else "MISSING"
                if closed
                else "PENDING"
                if reached
                else "NOT_REACHED"
            )
            slots.append(
                {
                    "round": round_number,
                    "agent": agents[agent.agent_id],
                    "status": status,
                    "assignments": allocation_rows(proposal.allocation) if proposal else None,
                }
            )
    execution = {"status": "NOT_FINALIZED", "allocation": None, "public_outcome": None}
    if state.status == Lifecycle.FINALIZED:
        costs = measure_costs(task, state.final_allocation)
        execution = {
            "status": "FINALIZED",
            "allocation": allocation_rows(state.final_allocation),
            "public_outcome": {
                "feasible": True,
                "global_cost": costs.global_cost,
                "per_agent_costs": [
                    {"agent": agents[a.agent_id], "workload": a.workload, "cost": a.total}
                    for a in costs.agents
                ],
                "unassigned_incidents": [incidents[i] for i in costs.unassigned_incidents],
                "unassigned_penalty": costs.unassigned_penalty,
            },
        }
    positions = {(e.source, e.sequence): e.logical_position for e in (record.event_journal or ())}
    events = []

    def add_event(source, sequence, kind, actor, round_number, payload):
        events.append(
            {
                "event_id": f"{source}-{sequence}",
                "type": kind,
                "actor": actor,
                "round": round_number,
                "ordering_stream": source,
                "source_sequence": sequence,
                "logical_position": positions.get((source, sequence)),
                "payload": payload,
            }
        )

    # Array storage order is source-local, NEVER a claimed global chronology.
    for message in messages["records"]:
        add_event(
            "message",
            message["event_order"],
            "MESSAGE",
            message["sender"],
            message["round"],
            message,
        )
    for event in state.history:
        payload = {}
        if event.kind == "PROPOSAL_ACCEPTED":
            proposal = proposals[(event.round_number, event.actor_id)]
            payload = {"assignments": allocation_rows(proposal.allocation)}
            kind = "PROPOSAL_ACCEPTED"
        elif event.kind == "FINALIZED":
            kind = "FINAL_ALLOCATION_EXECUTED"
            payload = {
                "round_closed": True,
                "allocation": execution["allocation"],
                "missing_agents": [agents[a] for a in event.missing_agents],
            }
        elif event.kind == "ROUND_CLOSED":
            kind = "ROUND_CLOSED"
            payload = {"next_round": 2, "missing_agents": [agents[a] for a in event.missing_agents]}
        else:
            kind = "ROUND_OPENED"
        add_event(
            "arena", event.sequence, kind, agents.get(event.actor_id), event.round_number, payload
        )
    if state.status == Lifecycle.FINALIZED:
        add_event("outcome", 1, "PUBLIC_OUTCOME_OBSERVED", None, 2, execution["public_outcome"])
    ordering = {
        "status": (
            "SOURCE_LOCAL_ONLY"
            if not positions
            else "RECORDED_CROSS_STREAM"
            if len(positions) == len(events)
            else "PARTIAL_CROSS_STREAM"
        ),
        "array_order": "SOURCE_LOCAL_NOT_GLOBAL_TIME",
        "logical_positions": "SMALLER_PRECEDES_LARGER_EQUAL_IS_UNRESOLVED_NULL_IS_UNKNOWN",
        "source_order": "SOURCE_SEQUENCE_STRICTLY_INCREASES_WITHIN_STREAM",
        "recorded_events": len(positions),
        "available_events": len(events),
    }
    return DetectorEvidence(
        canonical_json(
            {
                "schema_version": "pactlens-observation-v2",
                "episode_public_id": public_id,
                "public_task": public_task,
                "messages": messages,
                "proposal_slots": slots,
                "execution": execution,
                "events": events,
                "event_ordering": ordering,
            }
        )
    )


def export_evidence(record: EpisodeRecord, directory: Path, *, public_id: str) -> Path:
    """Exclusive, public-ID filename. No condition/source-path-derived export names."""
    evidence = project_evidence(record, public_id=public_id)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_public_id(public_id)}.json"
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(evidence.to_json() + "\n")
    return path
