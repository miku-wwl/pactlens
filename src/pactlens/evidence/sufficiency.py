"""Episode-level evidence sufficiency on lossless v2 tables. No model or label input.

Two candidate policies share the v2 renderer and the unchanged atomic bundles:

- complete-or-infeasible: every eligible fact in all five views, or a typed
  EVIDENCE_BUDGET_INFEASIBLE failure with a measured bottleneck;
- common-bundles v2: the Phase 4B mandatory core, priority and fit rule, re-run
  only with v2 tables, so any change is attributable to representation.

`assess` reports mechanical coverage of the questions an auditor must answer. It
never inspects conditions, assignments, oracle values or predictions, and a fit
or a coverage label is not detector adequacy or behavioral truth.
"""

import json
from dataclasses import dataclass

from pactlens.agents.models import closed_json
from pactlens.evidence.budget_selection import SelectionFailure
from pactlens.evidence.compact_views import (
    TABLE_VERSION,
    CompactView,
    render_compact,
    verify_compact_parity,
)
from pactlens.evidence.fact_bundles import BUNDLE_VERSION, fact_bundles
from pactlens.evidence.inventory import Inventory
from pactlens.evidence.views import CATEGORIES, View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.serialization import canonical_json, content_hash

COMPLETE_VERSION = "pactlens-complete-evidence-v1-candidate"
SELECTION_VERSION = "pactlens-common-bundles-v2-candidate"
SUFFICIENCY_VERSION = "pactlens-evidence-sufficiency-v1-candidate"
COMPLETE_CONFIG = {
    "version": COMPLETE_VERSION,
    "tables": TABLE_VERSION,
    "rule": "all-eligible-facts-in-all-five-views-or-EVIDENCE_BUDGET_INFEASIBLE",
    "overflow": "typed-failure;measured-bottleneck;no-selection;no-retry;no-context-expansion",
    "approval": "PROPOSED_NOT_APPROVED",
}
SELECTION_CONFIG = {
    "version": SELECTION_VERSION,
    "bundles": BUNDLE_VERSION,
    "tables": TABLE_VERSION,
    "rules": "pactlens-common-bundles-v1-candidate-mandatory-priority-and-fit-unchanged",
    "approval": "PROPOSED_NOT_APPROVED",
}
COMPLETE_HASH = content_hash(COMPLETE_CONFIG)
SELECTION_HASH = content_hash(SELECTION_CONFIG)
BOUNDARY_TYPES = ("ROUND_OPENED", "ROUND_CLOSED", "FINAL_ALLOCATION_EXECUTED")
GROUPS = (
    "core_context",
    "proposal_slots",
    "integrity_pairs",
    "round_boundaries",
    "arena_chronology",
    "communication",
)


class EvidenceBudgetInfeasible(ValueError):
    code = "EVIDENCE_BUDGET_INFEASIBLE"

    def __init__(self, diagnostics):
        super().__init__(self.code)
        self.diagnostics_json = canonical_json(diagnostics)


def group_of(fact):
    """Public, condition-independent audit group of one fact."""
    if fact.kind in ("public_task", "communication_coverage", "execution", "execution_coverage"):
        return "core_context"
    if fact.kind == "proposal_slot":
        return "proposal_slots"
    if fact.kind in ("aig_action", "consumer_receipt"):
        return "integrity_pairs"
    if fact.kind in ("message", "router_delivery"):
        return "communication"
    if json.loads(fact.payload_json)["type"] in BOUNDARY_TYPES:
        return "round_boundaries"
    return "arena_chronology"


@dataclass(frozen=True)
class EvidencePackets:
    packets: tuple
    manifest_json: str

    def packet(self, view):
        return next(p for p in self.packets if p.view == view)

    def verify(self):
        if (
            type(self.packets) is not tuple
            or len(self.packets) != 5
            or {p.view for p in self.packets} != set(View)
            or any(type(p) is not CompactView for p in self.packets)
        ):
            raise ValueError("FIVE_COMPACT_VIEWS_REQUIRED")
        # Cross-view relations are checked on facts parsed from each actual text.
        ids = {p.view: {f.fact_id for f in p.verify()[1]} for p in self.packets}
        verify_compact_parity(self.packet(View.R), self.packet(View.MAE))
        if (
            ids[View.M] | ids[View.A] != ids[View.MA]
            or not ids[View.MA] <= ids[View.R]
            or ids[View.R] != ids[View.MAE]
        ):
            raise ValueError("CROSS_VIEW_FACT_RELATION")
        manifest = closed_json(self.manifest_json, 524288)
        if type(manifest) is not dict or manifest.get("retained_fact_ids") != sorted(ids[View.R]):
            raise ValueError("EVIDENCE_PACKET_MANIFEST")
        for packet in self.packets:
            body = json.loads(packet.manifest_json)
            if manifest["views"].get(packet.view.value) != {
                "selected_fact_count": len(body["facts"]),
                "omitted_fact_count": len(body["omitted"]),
                "bytes": len(packet.text.encode("utf-8")),
                "budget": body["budget"],
            }:
                raise ValueError("EVIDENCE_VIEW_BUDGET_BINDING")
        return True


def _render(
    inventory, ids, mandatory, selection_hash, envelope, token_counter, renderer=render_compact
):
    return tuple(
        renderer(
            inventory, ids, mandatory, selection_hash, view, envelope, token_counter=token_counter
        )
        for view in View
    )


def _fits(packets):
    return all(json.loads(p.manifest_json)["budget"]["fits"] for p in packets)


def _views(packets):
    return {
        p.view.value: {
            "selected_fact_count": len(json.loads(p.manifest_json)["facts"]),
            "omitted_fact_count": len(json.loads(p.manifest_json)["omitted"]),
            "bytes": len(p.text.encode("utf-8")),
            "budget": json.loads(p.manifest_json)["budget"],
        }
        for p in packets
    }


def _envelope(envelope):
    from pactlens.research.native_detector import NativeEnvelope
    from pactlens.research.reason_detector import ReasonEnvelope

    envelope = DetectorEnvelope() if envelope is None else envelope
    if type(envelope) not in (DetectorEnvelope, NativeEnvelope, ReasonEnvelope):
        raise ValueError("TRUSTED_DETECTOR_ENVELOPE")
    envelope.__post_init__()
    return envelope


def bottleneck(inventory, *, envelope=None, token_counter=None):
    """Measured cost of complete evidence; diagnostic renders are never packets."""
    envelope = _envelope(envelope)
    all_ids = {f.fact_id for f in inventory.facts}
    grouped = {g: {f.fact_id for f in inventory.facts if group_of(f) == g} for g in GROUPS}
    complete = render_compact(inventory, all_ids, set(), "0" * 64, View.R, envelope)
    budget = json.loads(complete.manifest_json)["budget"]
    lines = complete.text.split("\n")
    header = json.loads(lines[0])
    rows = {g: 0 for g in GROUPS}
    by_kind = {}
    facts = complete.verify()[1]
    order = sorted(facts, key=lambda f: (f.kind, f.actor or "", f.fact_id))
    for fact, line in zip(order, lines[1:], strict=True):
        size = len(line.encode("utf-8")) + 1
        rows[group_of(fact)] += size
        by_kind[fact.kind] = by_kind.get(fact.kind, 0) + size
    request = budget["utf8_bytes"]
    evidence = len(complete.text.encode("utf-8"))

    def estimate(ids):
        if not ids:
            return None
        packet = render_compact(
            inventory, ids, set(), "0" * 64, View.R, envelope, token_counter=token_counter
        )
        return json.loads(packet.manifest_json)["budget"]["estimated_tokens"]

    lifecycle = (
        grouped["core_context"]
        | grouped["proposal_slots"]
        | grouped["integrity_pairs"]
        | grouped["round_boundaries"]
    )
    return {
        "version": SUFFICIENCY_VERSION,
        "episode_public_id": inventory.episode_public_id,
        "observation_policy": inventory.observation_policy.value,
        "view": "R",
        "complete_fact_count": len(all_ids),
        "complete_request_bytes": request,
        "complete_estimated_tokens": budget["estimated_tokens"],
        "available_input_tokens": envelope.available_input,
        "overflow_estimated_tokens": max(0, budget["estimated_tokens"] - envelope.available_input),
        "exact_tokens": budget["exact_tokens"],
        "byte_attribution": {
            "detector_envelope_fixed": request - evidence,
            "evidence_header_legends": len(lines[0].encode("utf-8"))
            - len(canonical_json(header["values"]).encode("utf-8")),
            "evidence_value_table": len(canonical_json(header["values"]).encode("utf-8")),
            "rows_by_group": rows,
            "rows_by_kind": by_kind,
        },
        "source_facts_by_group": {g: len(grouped[g]) for g in GROUPS},
        "diagnostic_estimates_R": {
            "lifecycle_core": estimate(lifecycle),
            "lifecycle_core_plus_all_communication": estimate(lifecycle | grouped["communication"]),
            "all_except_arena_chronology": estimate(all_ids - grouped["arena_chronology"]),
            "all_except_communication": estimate(all_ids - grouped["communication"]),
        },
        "note": "diagnostic subset estimates are not selected packets or approved policies",
    }


def _manifest(version, config_hash, inventory, chosen, mandatory, packets, bundles):
    omitted = sorted(f.fact_id for f in inventory.facts if f.fact_id not in chosen)
    return {
        "version": version,
        "selection_config_hash": config_hash,
        "approval": "PROPOSED_NOT_APPROVED",
        "episode_public_id": inventory.episode_public_id,
        "observation_policy": inventory.observation_policy.value,
        "retained_fact_ids": sorted(chosen),
        "omitted_fact_ids": omitted,
        "mandatory_fact_ids": sorted(mandatory),
        "retained_bundle_keys": bundles[0],
        "omitted_bundle_keys": bundles[1],
        "source_fact_count": len(inventory.facts),
        "selected_fact_count": len(chosen),
        "original_evidence_complete": not omitted,
        "views": _views(packets),
        "sufficiency": assess(inventory, chosen),
    }


def select_complete(inventory, *, envelope=None, token_counter=None):
    """All eligible facts in every view, or EVIDENCE_BUDGET_INFEASIBLE."""
    if type(inventory) is not Inventory:
        raise ValueError("PUBLIC_INVENTORY_REQUIRED")
    envelope = _envelope(envelope)
    fact_bundles(inventory)  # same atomic/correlation validation as every selector
    ids = {f.fact_id for f in inventory.facts}
    config_hash = content_hash({"complete": COMPLETE_HASH, "envelope": envelope.config_hash})
    packets = _render(inventory, ids, ids, config_hash, envelope, token_counter)
    if not _fits(packets):
        raise EvidenceBudgetInfeasible(
            {
                "error": EvidenceBudgetInfeasible.code,
                "version": COMPLETE_VERSION,
                "config_hash": config_hash,
                "prediction_generated": False,
                "views": _views(packets),
                "bottleneck": bottleneck(inventory, envelope=envelope, token_counter=token_counter),
            }
        )
    keys = [b.key for b in fact_bundles(inventory)]
    result = EvidencePackets(
        packets,
        canonical_json(
            _manifest(COMPLETE_VERSION, config_hash, inventory, ids, ids, packets, (keys, []))
        ),
    )
    result.verify()
    return result


def select_common(inventory, *, envelope=None, token_counter=None, renderer=render_compact):
    """Phase 4B common-bundle rules unchanged, rendered with lossless v2 tables."""
    if type(inventory) is not Inventory:
        raise ValueError("PUBLIC_INVENTORY_REQUIRED")
    envelope = _envelope(envelope)
    from pactlens.evidence.tight_views import render as tight_render
    from pactlens.research.native_detector import NativeEnvelope
    from pactlens.research.reason_detector import ReasonEnvelope

    if renderer not in (render_compact, tight_render) or (
        (renderer is tight_render) != (type(envelope) in (NativeEnvelope, ReasonEnvelope))
    ):
        raise ValueError("REVIEWED_RENDERER_ENVELOPE_REQUIRED")
    bundles = fact_bundles(inventory)
    mandatory = {f.fact_id for b in bundles if b.mandatory for f in b.facts}
    config_hash = content_hash({"selection": SELECTION_HASH, "envelope": envelope.config_hash})
    chosen = set(mandatory)
    packets = _render(inventory, chosen, mandatory, config_hash, envelope, token_counter, renderer)
    if not _fits(packets):
        raise SelectionFailure(
            {
                "version": SELECTION_VERSION,
                "config_hash": config_hash,
                "error": "MANDATORY_CORE_OVERFLOW",
                "mandatory_fact_ids": sorted(mandatory),
                "source_fact_count": len(inventory.facts),
                "attempted_selected_fact_count": len(chosen),
                "prediction_generated": False,
                "views": _views(packets),
            }
        )
    retained = [b.key for b in bundles if b.mandatory]
    for bundle in bundles:
        if bundle.mandatory:
            continue
        proposed = chosen | {f.fact_id for f in bundle.facts}
        candidate = _render(
            inventory, proposed, mandatory, config_hash, envelope, token_counter, renderer
        )
        # Same rule as Phase 4B: the larger matched views and all others must fit.
        if _fits(candidate):
            chosen, packets = proposed, candidate
            retained.append(bundle.key)
    omitted = [b.key for b in bundles if b.key not in retained]
    result = EvidencePackets(
        packets,
        canonical_json(
            _manifest(
                SELECTION_VERSION,
                config_hash,
                inventory,
                chosen,
                mandatory,
                packets,
                (retained, omitted),
            )
        ),
    )
    result.verify()
    return result


def assess(inventory, retained_ids):
    """Mechanical audit coverage of one common retained set (all five views)."""
    if type(inventory) is not Inventory:
        raise ValueError("PUBLIC_INVENTORY_REQUIRED")
    inventory.__post_init__()
    retained = set(retained_ids)
    facts = inventory.facts
    if not retained <= {f.fact_id for f in facts}:
        raise ValueError("RETAINED_FACTS_OUTSIDE_INVENTORY")
    data = {f.fact_id: json.loads(f.payload_json) for f in facts}

    def coverage(selector):
        rows = [f for f in facts if selector(f)]
        return {"source": len(rows), "retained": sum(f.fact_id in retained for f in rows)}

    def complete(selector):
        value = coverage(selector)
        return value["source"] == value["retained"]

    groups = {g: coverage(lambda f, g=g: group_of(f) == g) for g in GROUPS}
    integrity = [f for f in facts if f.kind == "aig_action"]
    successful = [
        f
        for f in integrity
        if data[f.fact_id]["action_state"] == "Succeeded"
        and any(
            r.kind == "consumer_receipt"
            and r.actor == f.actor
            and data[r.fact_id]["round"] == data[f.fact_id]["round"]
            and data[r.fact_id]["receipt_status"] == "VERIFIED_COMMITTED"
            for r in facts
        )
    ]
    pairs_atomic = all(
        (f.fact_id in retained)
        == any(
            r.fact_id in retained
            for r in facts
            if r.kind == "consumer_receipt"
            and r.actor == f.actor
            and data[r.fact_id]["round"] == data[f.fact_id]["round"]
        )
        for f in integrity
    )
    negative = [
        f
        for f in facts
        if f.completeness != "OBSERVED"
        or (f.kind == "aig_action" and data[f.fact_id]["action_state"] != "Succeeded")
        or (f.kind == "router_delivery" and data[f.fact_id]["delivery_state"] != "DELIVERED")
    ]
    lifecycle = all(
        complete(lambda f, g=g: group_of(f) == g)
        for g in ("core_context", "proposal_slots", "integrity_pairs", "round_boundaries")
    )
    communication = complete(lambda f: group_of(f) == "communication")
    communication_source = groups["communication"]["source"]
    positioned = coverage(lambda f: json.loads(f.ordering_json)["logical_position"] is not None)
    if retained == {f.fact_id for f in facts}:
        classification = "COMPLETE_EPISODE_EVIDENCE"
    elif lifecycle and communication:
        classification = "LIFECYCLE_AND_COMMUNICATION_COMPLETE"
    elif lifecycle:
        classification = "LIFECYCLE_COMPLETE_COMMUNICATION_PARTIAL"
    else:
        classification = "LIFECYCLE_INCOMPLETE"
    return {
        "version": SUFFICIENCY_VERSION,
        "observation_policy": inventory.observation_policy.value,
        "source_fact_count": len(facts),
        "retained_fact_count": len(retained),
        "groups": groups,
        "categories": {
            c: coverage(lambda f, c=c: f.category == c) for c in sorted(CATEGORIES[View.R])
        },
        "questions": {
            "agreement_evidence": "NO_COMMUNICATION_IN_SOURCE"
            if communication_source == 0
            else "ALL_SOURCE_COMMUNICATION_RETAINED"
            if communication
            else "COMMUNICATION_PARTIALLY_OMITTED",
            "proposal_and_execution_observability": "ALL_SLOTS_AND_INTEGRITY_PAIRS_RETAINED"
            if lifecycle
            else "LIFECYCLE_PARTIALLY_OMITTED",
            "talk_only_versus_executed": "BOTH_SIDES_RETAINED"
            if lifecycle and communication
            else "NOT_FULLY_SUPPORTED_BY_PACKET",
            "missing_failed_unknown_distinction": "ALL_NEGATIVE_OR_MISSING_FACTS_RETAINED"
            if all(f.fact_id in retained for f in negative)
            else "NEGATIVE_OR_MISSING_FACTS_OMITTED",
            "final_allocation_and_public_costs": "RETAINED"
            if complete(lambda f: f.kind == "execution")
            else "OMITTED",
            "action_receipt_correlation": "ATOMIC" if pairs_atomic else "SPLIT",
            "successful_integrity_pairs": {
                "source": len(successful),
                "retained": sum(f.fact_id in retained for f in successful),
            },
            "observer_rights": inventory.observation_policy.value,
            "recorded_capture_positions": positioned,
        },
        "classification": classification,
        "episode_audit": "SUFFICIENT_MECHANICAL_COVERAGE"
        if classification == "COMPLETE_EPISODE_EVIDENCE"
        else "CONDITIONAL_ARENA_EVENTS_OMITTED"
        if classification == "LIFECYCLE_AND_COMMUNICATION_COMPLETE"
        else "INSUFFICIENT_FOR_EPISODE_AUDIT",
        "limits": "mechanical public coverage only; not detector adequacy, truth or approval",
    }
