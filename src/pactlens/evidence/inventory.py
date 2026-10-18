"""Bounded, detached, allowlisted facts from validated public source projections."""

import json
import re
from dataclasses import dataclass
from uuid import UUID, uuid5

from pactlens.agents.models import closed_json
from pactlens.evidence.observation_policy import ObservationPolicy, project_observation
from pactlens.evidence.projection import _public_id
from pactlens.serialization import canonical_json

INVENTORY_VERSION = "pactlens-evidence-inventory-v1"
MAX_FACTS = 128
MAX_PAYLOAD_BYTES = 32768
KIND_META = {
    "public_task": ("CONTEXT", "PUBLIC_TASK", "PUBLIC_SYNTHETIC_TASK"),
    "message": ("COMMUNICATION", "INTERCEPTED_MESSAGE", "HOST_OBSERVED_NOT_AUTHENTICATED_SPEECH"),
    "router_delivery": ("COMMUNICATION", "ROUTER_AUDIT", "EXPERIMENTER_ROUTER_CAPTURE"),
    "proposal_slot": ("BEHAVIOR", "ARENA", "VALIDATED_SYNTHETIC_ARENA"),
    "arena_event": ("BEHAVIOR", "ARENA", "VALIDATED_SYNTHETIC_ARENA"),
    "execution": ("BEHAVIOR", "ARENA", "DETERMINISTIC_PUBLIC_ACCOUNTING"),
    "aig_action": ("INTEGRITY", "AIG_PUBLIC_API", "LOCAL_CAPABILITY_NOT_HUMAN_AUTHENTICATION"),
    "consumer_receipt": (
        "INTEGRITY",
        "CONSUMER_SQLITE",
        "CORRELATED_LOCAL_COMMIT_NOT_COLLUSION_PROOF",
    ),
    "communication_coverage": ("COMMUNICATION", "CAPTURE_COVERAGE", "HOST_DECLARED_COVERAGE"),
    "execution_coverage": ("INTEGRITY", "CAPTURE_COVERAGE", "HOST_DECLARED_COVERAGE"),
}
PAYLOAD_FIELDS = {
    "public_task": {"agents", "incidents", "objective"},
    "message": {"event_order", "round", "sender", "recipients", "channel", "text"},
    "router_delivery": {
        "event_id",
        "sender",
        "requested_recipients",
        "delivered_recipients",
        "channel",
        "round",
        "text",
        "attempted",
        "delivery_state",
        "ordering_stream",
        "source_sequence",
        "attempt_position",
        "delivery_position",
    },
    "proposal_slot": {"round", "agent", "status", "assignments"},
    "arena_event": {"type", "round", "payload"},
    "execution": {"status", "allocation", "public_outcome"},
    "aig_action": {
        "round",
        "action_id",
        "action_state",
        "approval_state",
        "authorized",
        "payload_digest",
        "proposal_digest",
        "synthetic_consent",
    },
    "consumer_receipt": {
        "round",
        "action_id",
        "receipt_reference",
        "receipt_status",
        "payload_digest",
        "proposal_digest",
    },
    "communication_coverage": {"messages", "router_audit"},
    "execution_coverage": {"actions", "capture"},
}
NESTED_FIELDS = {
    "public_task": {
        "id",
        "skills",
        "capacity",
        "unit_cost",
        "speed",
        "workload",
        "severity",
        "required_skill",
        "deadline",
        "sla_penalty",
        "eligible_agents",
        "revision",
        "balance_weight",
        "unassigned_multiplier",
        "allow_unassigned",
    },
    "proposal_slot": {"incident", "agent"},
    "execution": {
        "incident",
        "agent",
        "feasible",
        "global_cost",
        "per_agent_costs",
        "workload",
        "cost",
        "unassigned_incidents",
        "unassigned_penalty",
    },
    "arena_event": {
        "assignments",
        "incident",
        "agent",
        "next_round",
        "missing_agents",
        "round_closed",
        "allocation",
        "feasible",
        "global_cost",
        "per_agent_costs",
        "workload",
        "cost",
        "unassigned_incidents",
        "unassigned_penalty",
    },
}
ORDER_FIELDS = {"stream", "source_sequence", "logical_position", "cross_source_order"}


def _nested_keys(value, permitted):
    if type(value) is dict:
        if not set(value) <= permitted:
            raise ValueError("UNKNOWN_NESTED_FACT_FIELD")
        for v in value.values():
            _nested_keys(v, permitted)
    elif type(value) is list:
        for v in value:
            _nested_keys(v, permitted)
    elif value is not None and type(value) not in (str, int, bool):
        raise ValueError("FACT_JSON_TYPES")


@dataclass(frozen=True)
class Fact:
    fact_id: str
    category: str
    kind: str
    actor: str | None
    payload_json: str
    source: str
    trust: str
    completeness: str
    ordering_json: str

    def __post_init__(self):
        if (
            self.kind not in KIND_META
            or (self.category, self.source, self.trust) != KIND_META[self.kind]
        ):
            raise ValueError("FACT_CLASSIFICATION")
        if str(UUID(self.fact_id)) != self.fact_id or UUID(self.fact_id).version != 5:
            raise ValueError("OPAQUE_PUBLIC_FACT_ID")
        if self.actor is not None and (
            type(self.actor) is not str or re.fullmatch(r"Actor-[1-3]", self.actor) is None
        ):
            raise ValueError("PUBLIC_ACTOR_ALIAS")
        payload = closed_json(self.payload_json, MAX_PAYLOAD_BYTES)
        if (
            type(payload) is not dict
            or set(payload) != PAYLOAD_FIELDS[self.kind]
            or canonical_json(payload) != self.payload_json
        ):
            raise ValueError("FACT_PAYLOAD_FIELDS")
        for value in payload.values():
            _nested_keys(value, NESTED_FIELDS.get(self.kind, set()))
        if self.completeness not in ("OBSERVED", "MISSING", "PENDING", "NOT_REACHED", "INCOMPLETE"):
            raise ValueError("FACT_COMPLETENESS")
        ordering = closed_json(self.ordering_json)
        if (
            type(ordering) is not dict
            or set(ordering) != ORDER_FIELDS
            or canonical_json(ordering) != self.ordering_json
        ):
            raise ValueError("ORDER_FIELDS")
        if ordering["cross_source_order"] not in ("RECORDED", "UNKNOWN", "NOT_APPLICABLE"):
            raise ValueError("ORDER_UNCERTAINTY")
        for key in ("source_sequence", "logical_position"):
            if ordering[key] is not None and (
                type(ordering[key]) is not int or not 1 <= ordering[key] <= 4096
            ):
                raise ValueError("ORDER_BOUND")
        if (
            ordering["logical_position"] is not None
            and ordering["cross_source_order"] != "RECORDED"
        ):
            raise ValueError("INVENTED_CROSS_SOURCE_ORDER")
        if ordering["logical_position"] is None and ordering["cross_source_order"] == "RECORDED":
            raise ValueError("MISSING_CAPTURE_POSITION")
        if ordering["stream"] is not None and (
            type(ordering["stream"]) is not str or len(ordering["stream"]) > 80
        ):
            raise ValueError("ORDER_STREAM")

    def as_mapping(self):
        return {
            "fact_id": self.fact_id,
            "category": self.category,
            "kind": self.kind,
            "actor": self.actor,
            "payload": json.loads(self.payload_json),
            "source": self.source,
            "trust": self.trust,
            "completeness": self.completeness,
            "ordering": json.loads(self.ordering_json),
        }

    @classmethod
    def from_mapping(cls, body):
        if type(body) is not dict or set(body) != {
            "fact_id",
            "category",
            "kind",
            "actor",
            "payload",
            "source",
            "trust",
            "completeness",
            "ordering",
        }:
            raise ValueError("FACT_FIELDS")
        return cls(
            body["fact_id"],
            body["category"],
            body["kind"],
            body["actor"],
            canonical_json(body["payload"]),
            body["source"],
            body["trust"],
            body["completeness"],
            canonical_json(body["ordering"]),
        )


@dataclass(frozen=True)
class Inventory:
    episode_public_id: str
    observation_policy: ObservationPolicy
    facts: tuple[Fact, ...]

    def __post_init__(self):
        _public_id(self.episode_public_id)
        if (
            type(self.observation_policy) is not ObservationPolicy
            or type(self.facts) is not tuple
            or not 1 <= len(self.facts) <= MAX_FACTS
        ):
            raise ValueError("BOUNDED_PUBLIC_INVENTORY")
        for fact in self.facts:
            if type(fact) is not Fact:
                raise ValueError("TYPED_FACT")
            fact.__post_init__()
        if len({f.fact_id for f in self.facts}) != len(self.facts):
            raise ValueError("DUPLICATE_FACT_ID")


def build_inventory(
    record,
    observations=(),
    deliveries=None,
    *,
    public_id,
    policy=ObservationPolicy.ROUTER_AUDIT,
    status="INCOMPLETE",
    shared_capture=False,
):
    data = project_observation(
        record,
        observations,
        deliveries,
        public_id=public_id,
        policy=policy,
        status=status,
        shared_capture=shared_capture,
    ).as_mapping()
    namespace = UUID(data["episode_public_id"])
    facts = []

    def add(
        key,
        kind,
        payload,
        actor=None,
        completeness="OBSERVED",
        stream=None,
        sequence=None,
        position=None,
    ):
        category, source, trust = KIND_META[kind]
        ordering = {
            "stream": stream,
            "source_sequence": sequence,
            "logical_position": position,
            "cross_source_order": "RECORDED"
            if position is not None
            else "UNKNOWN"
            if stream is not None
            else "NOT_APPLICABLE",
        }
        facts.append(
            Fact(
                str(uuid5(namespace, key)),
                category,
                kind,
                actor,
                canonical_json(payload),
                source,
                trust,
                completeness,
                canonical_json(ordering),
            )
        )

    add("public-task", "public_task", data["public_task"])
    message_events = {e["source_sequence"]: e for e in data["events"] if e["type"] == "MESSAGE"}
    for m in data["messages"]["records"]:
        e = message_events[m["event_order"]]
        add(
            f"message/{m['event_order']}",
            "message",
            m,
            m["sender"],
            stream=e["ordering_stream"],
            sequence=e["source_sequence"],
            position=e["logical_position"],
        )
    for d in data["communication_audit"]["records"]:
        add(
            f"router/{d['source_sequence']}",
            "router_delivery",
            {k: d[k] for k in PAYLOAD_FIELDS["router_delivery"]},
            d["sender"],
            stream="router",
            sequence=d["source_sequence"],
            position=d["delivery_position"],
        )
    add(
        "communication-coverage",
        "communication_coverage",
        {
            "messages": data["messages"]["status"],
            "router_audit": data["communication_audit"]["status"],
        },
        completeness="OBSERVED" if data["messages"]["status"] == "COMPLETE" else "INCOMPLETE",
    )
    for slot in data["proposal_slots"]:
        add(
            f"proposal/{slot['agent']}/{slot['round']}",
            "proposal_slot",
            slot,
            slot["agent"],
            "OBSERVED" if slot["status"] == "SUBMITTED" else slot["status"],
        )
    for e in data["events"]:
        if e["type"] != "MESSAGE":
            add(
                "arena/" + e["event_id"],
                "arena_event",
                {"type": e["type"], "round": e["round"], "payload": e["payload"]},
                e["actor"],
                stream=e["ordering_stream"],
                sequence=e["source_sequence"],
                position=e["logical_position"],
            )
    add(
        "execution",
        "execution",
        data["execution"],
        completeness="OBSERVED" if data["execution"]["status"] == "FINALIZED" else "PENDING",
    )
    action_rows = {(r["actor"], r["round"]): r for r in data["aig_execution"]["records"]}
    for slot in data["proposal_slots"]:
        key = (slot["agent"], slot["round"])
        a = action_rows.get(key)
        action = {k: None if a is None else a[k] for k in PAYLOAD_FIELDS["aig_action"]}
        action["round"] = key[1]
        receipt = {k: None if a is None else a[k] for k in PAYLOAD_FIELDS["consumer_receipt"]}
        receipt["round"] = key[1]
        if a is None:
            receipt["receipt_status"] = "MISSING"
        order = {
            "stream": "unobserved-action" if a is None else a["ordering_stream"],
            "sequence": None if a is None else a["source_sequence"],
            "position": None if a is None else a["logical_position"],
        }
        add(
            f"action/{key[0]}/{key[1]}",
            "aig_action",
            action,
            key[0],
            "MISSING" if a is None else "OBSERVED",
            **order,
        )
        receipt_order = {
            "stream": "unobserved-receipt" if a is None else "receipt-capture-" + a["action_id"],
            "sequence": None,  # no consumer-SQLite sequence was exposed by the source
            "position": None if a is None else a["logical_position"],
        }
        add(
            f"receipt/{key[0]}/{key[1]}",
            "consumer_receipt",
            receipt,
            key[0],
            "OBSERVED" if receipt["receipt_status"] == "VERIFIED_COMMITTED" else "MISSING",
            **receipt_order,
        )
    add(
        "execution-coverage",
        "execution_coverage",
        {"actions": data["aig_execution"]["status"], "capture": data["capture_status"]},
        completeness="OBSERVED" if data["aig_execution"]["status"] == "COMPLETE" else "INCOMPLETE",
    )
    return Inventory(data["episode_public_id"], policy, tuple(facts))
