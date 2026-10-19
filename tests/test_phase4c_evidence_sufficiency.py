"""Phase 4C episode-level evidence sufficiency; no labels, oracle or predictions."""

import asyncio
import inspect
import json
from dataclasses import replace

import pytest
from context_helpers import speaker
from harness_helpers import message, run_fake
from view_helpers import PUBLIC_ID

from pactlens.aig.submission import TestConsent as Consent
from pactlens.evidence.budget_selection import SelectionFailure, select_evidence
from pactlens.evidence.fact_bundles import fact_bundles
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import (
    GROUPS,
    EvidenceBudgetInfeasible,
    EvidencePackets,
    assess,
    group_of,
    select_common,
    select_complete,
)
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.fixtures import fixture_task, run_fixture
from pactlens.research.seeds import Condition


def inventory_of(run, policy):
    return build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        policy=policy,
        status=run.status,
        shared_capture=True,
    )


@pytest.fixture(scope="module")
def six_action(tmp_path_factory):
    run, _ = asyncio.run(
        run_fake(tmp_path_factory.mktemp("six"), fixture_task(), transform=message)
    )
    return {policy: inventory_of(run, policy) for policy in ObservationPolicy}


@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_complete_six_action_evidence_is_typed_infeasible_with_bottleneck(six_action, policy):
    inventory = six_action[policy]
    with pytest.raises(EvidenceBudgetInfeasible, match="EVIDENCE_BUDGET_INFEASIBLE") as caught:
        select_complete(inventory)
    report = json.loads(caught.value.diagnostics_json)
    assert report["prediction_generated"] is False
    neck = report["bottleneck"]
    assert neck["overflow_estimated_tokens"] > 0 and neck["exact_tokens"] is None
    assert neck["complete_fact_count"] == len(inventory.facts)
    attribution = neck["byte_attribution"]
    total = (
        attribution["detector_envelope_fixed"]
        + attribution["evidence_header_legends"]
        + attribution["evidence_value_table"]
        + sum(attribution["rows_by_group"].values())
    )
    # Header line, row bytes and envelope account for the whole request (newlines incl.).
    assert abs(total - neck["complete_request_bytes"]) <= 2
    assert set(attribution["rows_by_group"]) == set(GROUPS)
    diagnostic = neck["diagnostic_estimates_R"]
    # Even the six-action lifecycle core alone exceeds the estimated 4,096 input.
    assert diagnostic["lifecycle_core"] > 4096
    assert diagnostic["lifecycle_core_plus_all_communication"] > diagnostic["lifecycle_core"]


def test_complete_policy_returns_full_packets_when_the_episode_fits():
    # A small scripted source genuinely fits; no six-action source does.
    inventory = build_inventory(
        run_fixture("deterministic_tie").record, public_id=PUBLIC_ID, shared_capture=True
    )
    result = select_complete(inventory)
    assert result.verify()
    manifest = json.loads(result.manifest_json)
    assert manifest["original_evidence_complete"] and not manifest["omitted_fact_ids"]
    assert manifest["sufficiency"]["classification"] == "COMPLETE_EPISODE_EVIDENCE"
    for packet in result.packets:
        header, _ = packet.verify()
        assert header["scope"] == "FULL_ELIGIBLE_SOURCE"
        packet.conversation()


@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_v2_tables_retain_more_lifecycle_under_unchanged_rules(six_action, policy):
    inventory = six_action[policy]
    old = assess(
        inventory, json.loads(select_evidence(inventory).manifest_json)["retained_fact_ids"]
    )
    result = select_common(inventory)
    assert result.verify()
    new = json.loads(result.manifest_json)["sufficiency"]
    assert (
        new["groups"]["integrity_pairs"]["retained"] > old["groups"]["integrity_pairs"]["retained"]
    )
    assert json.loads(result.manifest_json)["retained_fact_ids"]
    mandatory = {f.fact_id for b in fact_bundles(inventory) if b.mandatory for f in b.facts}
    assert mandatory <= set(json.loads(result.manifest_json)["retained_fact_ids"])
    # Still not a complete episode audit: the packet must say so.
    assert new["classification"] == "LIFECYCLE_INCOMPLETE"
    assert new["episode_audit"] == "INSUFFICIENT_FOR_EPISODE_AUDIT"
    for packet in result.packets:
        assert json.loads(packet.manifest_json)["budget"]["fits"]


def test_classification_of_constructed_retained_sets(six_action):
    inventory = six_action[ObservationPolicy.DELIVERED]
    ids = {f.fact_id for f in inventory.facts}
    by_group = {g: {f.fact_id for f in inventory.facts if group_of(f) == g} for g in GROUPS}
    one_message = next(iter(by_group["communication"]))
    action = next(f for f in inventory.facts if f.kind == "aig_action")
    receipt = next(
        f
        for f in inventory.facts
        if f.kind == "consumer_receipt"
        and f.actor == action.actor
        and json.loads(f.payload_json)["round"] == json.loads(action.payload_json)["round"]
    )
    cases = {
        "COMPLETE_EPISODE_EVIDENCE": ids,
        "LIFECYCLE_AND_COMMUNICATION_COMPLETE": ids - by_group["arena_chronology"],
        "LIFECYCLE_COMPLETE_COMMUNICATION_PARTIAL": ids - {one_message},
        "LIFECYCLE_INCOMPLETE": ids - {action.fact_id, receipt.fact_id},
    }
    for label, retained in cases.items():
        assert assess(inventory, retained)["classification"] == label
    split = assess(inventory, ids - {receipt.fact_id})
    assert split["questions"]["action_receipt_correlation"] == "SPLIT"
    assert assess(inventory, ids)["questions"]["agreement_evidence"] == (
        "ALL_SOURCE_COMMUNICATION_RETAINED"
    )
    with pytest.raises(ValueError, match="RETAINED_FACTS_OUTSIDE_INVENTORY"):
        assess(inventory, {"not-a-fact"})


def test_mandatory_overflow_is_typed_and_never_an_empty_success(six_action):
    with pytest.raises(SelectionFailure, match="INPUT_BUDGET_EXCEEDED") as caught:
        select_common(
            six_action[ObservationPolicy.ROUTER_AUDIT], envelope=DetectorEnvelope(input_limit=1500)
        )
    report = json.loads(caught.value.diagnostics_json)
    assert report["error"] == "MANDATORY_CORE_OVERFLOW" and not report["prediction_generated"]


def test_packet_bundle_detects_cross_view_and_manifest_tampering(six_action):
    inventory = six_action[ObservationPolicy.DELIVERED]
    result = select_common(inventory)
    other = select_common(six_action[ObservationPolicy.ROUTER_AUDIT])
    swapped = tuple(other.packet(View.MAE) if p.view == View.MAE else p for p in result.packets)
    with pytest.raises(ValueError):
        EvidencePackets(swapped, result.manifest_json).verify()
    manifest = json.loads(result.manifest_json)
    manifest["retained_fact_ids"] = manifest["retained_fact_ids"][1:]
    with pytest.raises(ValueError, match="EVIDENCE_PACKET_MANIFEST"):
        replace(result, manifest_json=json.dumps(manifest)).verify()


def test_selection_has_no_label_input_and_ignores_private_metadata():
    for function in (select_common, select_complete, assess):
        parameters = set(inspect.signature(function).parameters)
        assert not parameters & {"condition", "config", "assignment", "label", "truth", "score"}
    source = run_fixture("c_plus").record
    plain = build_inventory(source, public_id=PUBLIC_ID, shared_capture=True)
    marked = build_inventory(
        replace(source, private_metadata={"condition": "C+", "coalition": ("a0", "a1")}),
        public_id=PUBLIC_ID,
        shared_capture=True,
    )
    assert select_common(plain) == select_common(marked)


@pytest.mark.parametrize("condition", list(Condition))
def test_condition_differences_arise_only_from_observable_facts(tmp_path, task, condition):
    run, _ = asyncio.run(
        run_fake(tmp_path, task, condition=condition, transform=speaker("pair", 30))
    )
    for policy in ObservationPolicy:
        inventory = inventory_of(run, policy)
        try:
            manifest = json.loads(select_common(inventory).manifest_json)
        except SelectionFailure:
            continue
        retained = set(manifest["retained_fact_ids"])
        negative = [
            f
            for f in inventory.facts
            if f.completeness != "OBSERVED"
            or (
                f.kind == "router_delivery"
                and json.loads(f.payload_json)["delivery_state"] != "DELIVERED"
            )
        ]
        assert all(f.fact_id in retained for f in negative)
        blocked = [
            f
            for f in inventory.facts
            if f.kind == "router_delivery"
            and f.fact_id in retained
            and json.loads(f.payload_json)["delivery_state"] == "BLOCKED"
        ]
        if condition == Condition.C_MINUS and policy == ObservationPolicy.ROUTER_AUDIT:
            assert len(blocked) == 4  # blocked private attempts are audit-visible only under B
        else:
            assert not blocked
        if condition == Condition.N2:
            missing = [
                f for f in inventory.facts if f.kind == "aig_action" and f.completeness == "MISSING"
            ]
            assert len(missing) == 3 and all(f.fact_id in retained for f in missing)


def test_withheld_authorization_and_denied_approval_stay_explicit(tmp_path, task):
    for name, consent in (
        ("withheld", Consent(True, authorize=False)),
        ("denied", Consent(True, approve=False)),
    ):
        run, _ = asyncio.run(run_fake(tmp_path / name, task, consent=consent))
        inventory = inventory_of(run, ObservationPolicy.DELIVERED)
        integrity = [f for f in inventory.facts if f.kind in ("aig_action", "consumer_receipt")]
        try:
            result = select_common(inventory)
        except SelectionFailure as failure:
            # Non-success integrity is mandatory: overflow is reported, never dropped.
            mandatory = set(json.loads(failure.diagnostics_json)["mandatory_fact_ids"])
            assert {f.fact_id for f in integrity} <= mandatory
        else:
            facts = {f.fact_id for f in result.packet(View.R).verify()[1]}
            assert {f.fact_id for f in integrity} <= facts
        states = {
            json.loads(f.payload_json)["action_state"] for f in integrity if f.kind == "aig_action"
        }
        assert states == ({"Pending"} if name == "withheld" else {None})
        assert all(
            json.loads(f.payload_json)["receipt_status"] == "MISSING"
            for f in integrity
            if f.kind == "consumer_receipt"
        )
