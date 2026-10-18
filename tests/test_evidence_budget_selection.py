import json
from dataclasses import replace

import pytest
from view_helpers import PUBLIC_ID

from pactlens.evidence.budget_selection import SelectionFailure, select_evidence
from pactlens.evidence.fact_bundles import fact_bundles
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.fixtures import load_specs, run_fixture


@pytest.mark.parametrize("name", [s.name for s in load_specs()])
@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_fixture_budget_core_and_atomic_common_selection(name, policy):
    inventory = build_inventory(
        run_fixture(name).record, public_id=PUBLIC_ID, policy=policy, shared_capture=True
    )
    result = select_evidence(inventory)
    manifest = json.loads(result.manifest_json)
    retained, omitted = set(manifest["retained_fact_ids"]), set(manifest["omitted_fact_ids"])
    assert retained | omitted == {f.fact_id for f in inventory.facts}
    assert not retained & omitted
    assert set(manifest["mandatory_fact_ids"]) <= retained
    assert (
        len([f for f in inventory.facts if f.fact_id in retained and f.kind == "proposal_slot"])
        == 6
    )
    for bundle in fact_bundles(inventory):
        membership = [f.fact_id in retained for f in bundle.facts]
        assert all(membership) or not any(membership)
        if bundle.mandatory:
            assert all(membership)
    for packet in result.packets:
        header, facts = packet.verify()
        packet.conversation()
        details = json.loads(packet.manifest_json)
        assert details["budget"]["estimated_tokens"] <= 4096
        assert details["budget"]["exact_tokens"] is None
        assert details["reserved_output_tokens"] == 256
        assert header["scope"] == (
            "SELECTED_SUBSET_NOT_COMPLETE_SOURCE" if details["omitted"] else "FULL_ELIGIBLE_SOURCE"
        )
        assert facts
    assert result.packet(View.R).envelope == result.packet(View.MAE).envelope


def test_deterministic_priority_ties_and_source_order_are_not_input_iteration_order():
    inv = build_inventory(run_fixture("c_plus").record, public_id=PUBLIC_ID, shared_capture=True)
    forward = select_evidence(inv)
    reverse = select_evidence(replace(inv, facts=tuple(reversed(inv.facts))))
    assert forward == reverse
    keys = [b.key for b in fact_bundles(inv)]
    assert keys == [b.key for b in fact_bundles(replace(inv, facts=tuple(reversed(inv.facts))))]


def test_mandatory_overflow_is_a_recorded_typed_failure_without_empty_success():
    inv = build_inventory(run_fixture("c_plus").record, public_id=PUBLIC_ID)
    with pytest.raises(SelectionFailure, match="INPUT_BUDGET_EXCEEDED") as failure:
        select_evidence(inv, envelope=DetectorEnvelope(input_limit=1024))
    report = json.loads(failure.value.diagnostics_json)
    assert report["error"] == "MANDATORY_CORE_OVERFLOW"
    assert report["mandatory_fact_ids"] and not report["prediction_generated"]
    assert report["views"]["MAE"]["budget"]["fits"] is False


def test_no_private_assignment_or_oracle_access_and_tampered_correlation_rejected():
    source = run_fixture("c_plus").record
    original = build_inventory(source, public_id=PUBLIC_ID)
    changed = build_inventory(
        replace(
            source,
            manifest=object(),
            private_metadata={"nested": {"seed": "L1_SEED", "truth": "L2_TRUTH"}},
            source_path="PRIVATE_GATE_PATH",
        ),
        public_id=PUBLIC_ID,
    )
    assert select_evidence(original) == select_evidence(changed)
    receipt = next(f for f in original.facts if f.kind == "consumer_receipt")
    payload = json.loads(receipt.payload_json)
    payload["proposal_digest"] = "a" * 64
    from pactlens.serialization import canonical_json

    bad = replace(receipt, payload_json=canonical_json(payload))
    with pytest.raises(ValueError, match="CORRELATION"):
        select_evidence(
            replace(original, facts=tuple(bad if f == receipt else f for f in original.facts))
        )


def test_critical_missing_evidence_does_not_get_dropped_to_preserve_success():
    inv = build_inventory(run_fixture("n2_talk_only").record, public_id=PUBLIC_ID)
    selected = {f.fact_id for f in select_evidence(inv).packet(View.R).verify()[1]}
    assert all(
        f.fact_id in selected
        for f in inv.facts
        if f.completeness in ("MISSING", "PENDING", "NOT_REACHED", "INCOMPLETE")
    )


def test_selection_manifest_cannot_add_private_fields_or_falsify_retention():
    from pactlens.serialization import canonical_json

    inv = build_inventory(run_fixture("c_plus").record, public_id=PUBLIC_ID)
    result = select_evidence(inv)
    m = json.loads(result.manifest_json)
    with pytest.raises(ValueError, match="MANIFEST_FIELDS"):
        replace(result, manifest_json=canonical_json({**m, "condition": "PRIVATE_MARKER"})).verify()
    m["retained_fact_ids"] = m["retained_fact_ids"][:-1]
    with pytest.raises(ValueError, match="MANIFEST_BINDING"):
        replace(result, manifest_json=canonical_json(m)).verify()


def test_identical_deliveries_stay_atomic_without_coalescing_two_observed_events(task):
    from pactlens.agents.models import MessageIntent
    from pactlens.arena.models import ArenaState
    from pactlens.arena.transitions import begin
    from pactlens.evidence.records import (
        Channel,
        EpisodeRecord,
        capture_message,
        capture_transition,
    )
    from pactlens.experiments.channels import Router

    state = begin(ArenaState(task), expected_revision=0)
    journal = capture_transition(state, logical_position=1)
    router = Router(("a0", "a1", "a2"), private_pair=("a0", "a1"), private_enabled=True)
    messages = []
    for position in (2, 4):
        d = router.route(
            MessageIntent(Channel.PRIVATE, ("a1",), "same observed speech"),
            actor="a0",
            round_number=1,
            attempt_position=position,
            delivery_position=position + 1,
        )
        messages.append(d.observed_message())
        journal = capture_message(state, messages[-1], journal, logical_position=position + 1)
    inv = build_inventory(
        EpisodeRecord(state, tuple(messages), event_journal=journal),
        (),
        router.deliveries,
        public_id=PUBLIC_ID,
        shared_capture=True,
    )
    groups = [b for b in fact_bundles(inv) if b.key.startswith("communication/")]
    assert len(groups) == 1 and len(groups[0].facts) == 4
    facts = select_evidence(inv).packet(View.R).verify()[1]
    assert len([f for f in facts if f.kind == "message"]) == 2
    assert len([f for f in facts if f.kind == "router_delivery"]) == 2
