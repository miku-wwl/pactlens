"""Atomic public fact groups. No source envelope, labels, oracle or predictions."""

import json
from dataclasses import dataclass

from pactlens.evidence.inventory import Inventory

BUNDLE_VERSION = "pactlens-atomic-fact-bundles-v1-candidate"


@dataclass(frozen=True)
class FactBundle:
    key: str
    facts: tuple
    mandatory: bool
    priority: int
    tie: tuple


def fact_bundles(inventory):
    if type(inventory) is not Inventory:
        raise ValueError("PUBLIC_INVENTORY_REQUIRED")
    inventory.__post_init__()
    facts = inventory.facts
    data = {f.fact_id: json.loads(f.payload_json) for f in facts}
    result, used = [], set()

    def add(key, members, mandatory, priority, tie=()):
        members = tuple(sorted(members, key=lambda f: f.fact_id))
        if not members or any(f.fact_id in used for f in members):
            raise ValueError("ATOMIC_BUNDLE_PARTITION")
        used.update(f.fact_id for f in members)
        result.append(FactBundle(key, members, mandatory, priority, tuple(tie)))

    for kind in ("public_task", "communication_coverage", "execution", "execution_coverage"):
        rows = [f for f in facts if f.kind == kind]
        if len(rows) != 1:
            raise ValueError("MANDATORY_CORE_SHAPE")
        add(kind, rows, True, 0)
    for actor in ("Actor-1", "Actor-2", "Actor-3"):
        for round_number in (1, 2):
            rows = [
                f
                for f in facts
                if f.kind == "proposal_slot"
                and f.actor == actor
                and data[f.fact_id]["round"] == round_number
            ]
            if len(rows) != 1:
                raise ValueError("SIX_PROPOSAL_SLOTS_REQUIRED")
            add(f"proposal/{actor}/{round_number}", rows, True, 0)
            action = [
                f
                for f in facts
                if f.kind == "aig_action"
                and f.actor == actor
                and data[f.fact_id]["round"] == round_number
            ]
            receipt = [
                f
                for f in facts
                if f.kind == "consumer_receipt"
                and f.actor == actor
                and data[f.fact_id]["round"] == round_number
            ]
            if len(action) != 1 or len(receipt) != 1:
                raise ValueError("ACTION_RECEIPT_SLOT_REQUIRED")
            a, r = data[action[0].fact_id], data[receipt[0].fact_id]
            for key in ("action_id", "payload_digest", "proposal_digest", "round"):
                if a[key] != r[key]:
                    raise ValueError("ACTION_RECEIPT_CORRELATION")
            if r["receipt_status"] == "VERIFIED_COMMITTED" and (
                a["action_id"] is None or r["receipt_reference"] is None
            ):
                raise ValueError("RECEIPT_WITHOUT_ACTION")
            # Missing and every non-success state are retained, not made benign.
            mandatory = (
                a["action_state"] != "Succeeded" or r["receipt_status"] != "VERIFIED_COMMITTED"
            )
            add(
                f"integrity/{actor}/{round_number}",
                action + receipt,
                mandatory,
                10,
                (-round_number, actor),
            )

    def communication_identity(fact):
        if fact.kind not in ("message", "router_delivery"):
            return None
        body = data[fact.fact_id]
        if fact.kind == "router_delivery" and body["delivery_state"] != "DELIVERED":
            return None
        audience = body["recipients"] if fact.kind == "message" else body["delivered_recipients"]
        return body["sender"], body["round"], body["channel"], body["text"], tuple(sorted(audience))

    communications = []
    for f in sorted(
        facts, key=lambda f: (json.loads(f.ordering_json)["source_sequence"] or 0, f.fact_id)
    ):
        if f.kind not in ("message", "router_delivery") or f.fact_id in used:
            continue
        body = data[f.fact_id]
        identity = communication_identity(f)
        members = (
            [f] if identity is None else [m for m in facts if communication_identity(m) == identity]
        )
        # Ambiguous identical content is grouped atomically, without inventing linkage/order.
        related = {m.fact_id for m in members}
        if any(x & related for x in communications):
            raise ValueError("AMBIGUOUS_COMMUNICATION_BUNDLE")
        communications.append(related)
        sequence = json.loads(f.ordering_json)["source_sequence"] or 0
        failure = any(
            m.kind == "router_delivery" and data[m.fact_id]["delivery_state"] != "DELIVERED"
            for m in members
        )
        add(
            f"communication/{len(communications)}",
            members,
            failure,
            20,
            (body["round"], sequence, f.actor or ""),
        )

    for f in facts:
        if f.fact_id in used:
            continue
        if f.kind != "arena_event":
            raise ValueError("UNBUNDLED_FACT_KIND")
        p = data[f.fact_id]
        order = json.loads(f.ordering_json)
        mandatory = p["type"] in ("ROUND_OPENED", "ROUND_CLOSED", "FINAL_ALLOCATION_EXECUTED")
        add(
            "arena/" + str(order["source_sequence"]),
            (f,),
            mandatory,
            30,
            (p["round"], order["source_sequence"] or 0),
        )

    # At least one observed communication event and one successful integrity bundle
    # when available, in addition to all negative/unknown/missing observations.
    for prefix in ("communication/", "integrity/"):
        eligible = [b for b in result if b.key.startswith(prefix)]
        if eligible and not any(b.mandatory for b in eligible):
            chosen = min(eligible, key=lambda b: (b.priority, b.tie, b.key))
            result[result.index(chosen)] = FactBundle(
                chosen.key, chosen.facts, True, chosen.priority, chosen.tie
            )
    # Retain at least two distinct observed speakers when available.
    speech = [
        b
        for b in result
        if b.key.startswith("communication/") and any(f.kind == "message" for f in b.facts)
    ]
    speakers = sorted({f.actor for b in speech for f in b.facts if f.kind == "message"})
    for actor in speakers[:2]:
        chosen = min(
            (b for b in speech if any(f.kind == "message" and f.actor == actor for f in b.facts)),
            key=lambda b: (b.tie, b.key),
        )
        result[result.index(chosen)] = FactBundle(
            chosen.key, chosen.facts, True, chosen.priority, chosen.tie
        )
    assert used == {f.fact_id for f in facts}
    return tuple(sorted(result, key=lambda b: (not b.mandatory, b.priority, b.tie, b.key)))
