"""Phase 4C lossless v2 tables: independent text reconstruction and R/MAE parity."""

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
from harness_helpers import message, run_fake
from view_helpers import PUBLIC_ID

from pactlens.evidence.compact_views import (
    CompactView,
    extract_compact,
    fact_key,
    render_compact,
    verify_compact_parity,
)
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import CATEGORIES, View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.fixtures import fixture_task, load_specs, run_fixture
from pactlens.serialization import canonical_json

ENVELOPE = DetectorEnvelope()


def complete(inventory):
    ids = {f.fact_id for f in inventory.facts}
    return {view: render_compact(inventory, ids, set(), "0" * 64, view, ENVELOPE) for view in View}


@pytest.fixture(scope="module")
def six_action(tmp_path_factory):
    run, _ = asyncio.run(
        run_fake(tmp_path_factory.mktemp("six"), fixture_task(), transform=message)
    )
    assert run.status == "COMPLETE" and len(run.observations) == 6
    return {
        policy: build_inventory(
            run.record,
            run.observations,
            run.deliveries,
            public_id=run.public_id,
            policy=policy,
            status=run.status,
            shared_capture=True,
        )
        for policy in ObservationPolicy
    }


def check_exact(inventory, packets):
    originals = {f.fact_id: f for f in inventory.facts}
    ids = {}
    for view, packet in packets.items():
        header, facts = extract_compact(packet.text, view)
        assert all(originals[f.fact_id] == f for f in facts)
        assert {f.fact_id for f in facts} == {
            f.fact_id for f in inventory.facts if f.category in CATEGORIES[view]
        }
        assert header["scope"] == "FULL_ELIGIBLE_SOURCE"
        ids[view] = {f.fact_id for f in facts}
    assert ids[View.M] | ids[View.A] == ids[View.MA] and ids[View.MA] <= ids[View.R]
    assert ids[View.R] == ids[View.MAE]
    assert verify_compact_parity(packets[View.R], packets[View.MAE])


@pytest.mark.parametrize("name", [s.name for s in load_specs()])
@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_fixture_tables_reconstruct_every_original_fact(name, policy):
    inventory = build_inventory(
        run_fixture(name).record, public_id=PUBLIC_ID, policy=policy, shared_capture=True
    )
    check_exact(inventory, complete(inventory))


@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_six_action_real_aig_source_reconstructs_and_cites_by_key(six_action, policy):
    inventory = six_action[policy]
    packets = complete(inventory)
    check_exact(inventory, packets)
    r = packets[View.R]
    header, facts = r.verify()
    keys = [fact_key(f, header["episode"]) for f in facts if f.kind == "aig_action"]
    assert len(keys) == 6 and r.resolve_citations(keys) == [
        f.fact_id for f in facts if f.kind == "aig_action"
    ]
    with pytest.raises(ValueError, match="UNOBSERVED_EVIDENCE_CITATION"):
        packets[View.MA].resolve_citations(keys[:1])  # integrity is not in MA
    with pytest.raises(ValueError, match="DETECTOR_EVIDENCE_IDS"):
        r.resolve_citations(keys[:1] * 2)
    # Correlated identifiers are listed once and referenced, never re-derived.
    values = header["values"]
    for fact in facts:
        if fact.kind == "aig_action":
            body = json.loads(fact.payload_json)
            assert body["action_id"] in values and body["payload_digest"] in values


def tamper(packet, kind):
    if packet.view == View.MAE:
        body = json.loads(packet.text)
        if kind == "group":
            row = body["groups"]["INTEGRITY"].pop()
            body["groups"]["BEHAVIOR"].append(row)
        elif kind == "drop":
            body["groups"]["INTEGRITY"].pop()
        return json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    lines = packet.text.split("\n")
    header = json.loads(lines[0])
    row = json.loads(lines[1])
    if kind == "value":
        header["values"][0] = "0" * 64 if len(header["values"][0]) == 64 else "X"
    elif kind == "reference":
        row[4][0] = {"@": 999}
    elif kind == "order":
        row[3][2] = None
    elif kind == "completeness":
        row[2] = "MISSING" if row[2] != "MISSING" else "OBSERVED"
    elif kind == "actor":
        row[1] = "Actor-2" if row[1] != "Actor-2" else "Actor-3"
    elif kind == "key":
        row[0] = row[0].replace("Actor-1", "Actor-2")
    elif kind == "drop":
        lines.pop()
    elif kind == "duplicate":
        lines.append(lines[1])
    elif kind == "reorder":
        lines[1], lines[2] = lines[2], lines[1]
    elif kind == "legend":
        header["kind_metadata"][min(header["kind_metadata"])][2] = "TRUSTED_HUMAN"
    elif kind == "private_field":
        header["condition"] = "C+"
    elif kind == "false_complete":
        header["omitted_by_category"] = dict.fromkeys(header["omitted_by_category"], 1)
    elif kind == "whitespace":
        return packet.text.replace(",", ", ", 1)
    if kind not in ("drop", "duplicate", "reorder"):
        lines[0] = json.dumps(header, ensure_ascii=False, separators=(",", ":"))
        lines[1] = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
    return "\n".join(lines)


@pytest.mark.parametrize(
    "kind",
    [
        "value",
        "reference",
        "order",
        "completeness",
        "actor",
        "key",
        "drop",
        "duplicate",
        "reorder",
        "legend",
        "private_field",
        "false_complete",
        "whitespace",
    ],
)
def test_tampered_flat_text_is_rejected(six_action, kind):
    packet = complete(six_action[ObservationPolicy.ROUTER_AUDIT])[View.R]
    with pytest.raises((ValueError, TypeError, KeyError)):
        replace(packet, text=tamper(packet, kind)).verify()


@pytest.mark.parametrize("kind", ["group", "drop"])
def test_tampered_grouped_text_is_rejected(six_action, kind):
    packet = complete(six_action[ObservationPolicy.ROUTER_AUDIT])[View.MAE]
    with pytest.raises(ValueError):
        replace(packet, text=tamper(packet, kind)).verify()


def test_parity_rejects_unequal_information_between_r_and_mae(six_action):
    inventory = six_action[ObservationPolicy.DELIVERED]
    ids = {f.fact_id for f in inventory.facts}
    r = render_compact(inventory, ids, set(), "0" * 64, View.R, ENVELOPE)
    fewer = ids - {next(f.fact_id for f in inventory.facts if f.kind == "message")}
    mae = render_compact(inventory, fewer, set(), "0" * 64, View.MAE, ENVELOPE)
    with pytest.raises(ValueError, match="COMPACT_INFORMATION_MISMATCH"):
        verify_compact_parity(r, mae)
    other = render_compact(inventory, ids, set(), "1" * 64, View.MAE, ENVELOPE)
    with pytest.raises(ValueError, match="COMPACT_INFORMATION_MISMATCH"):
        verify_compact_parity(r, other)


def test_unknown_with_committed_receipt_stays_unknown_in_tables(tmp_path, task):
    async def lost_ack(phase):
        if phase == "after_commit":
            raise RuntimeError("offline lost acknowledgement")

    run, _ = asyncio.run(run_fake(tmp_path, task, checkpoint=lost_ack))
    inventory = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    packets = complete(inventory)
    check_exact(inventory, packets)
    facts = packets[View.MAE].verify()[1]
    action = next(f for f in facts if f.kind == "aig_action" and f.completeness == "OBSERVED")
    receipt = next(
        f for f in facts if f.kind == "consumer_receipt" and f.completeness == "OBSERVED"
    )
    assert json.loads(action.payload_json)["action_state"] == "Unknown"
    assert json.loads(receipt.payload_json)["receipt_status"] == "VERIFIED_COMMITTED"
    missing = [f for f in facts if f.kind == "aig_action" and f.completeness == "MISSING"]
    assert len(missing) == 5 and all(
        json.loads(f.payload_json)["action_id"] is None for f in missing
    )


def test_private_labels_never_reach_tables_and_do_not_change_text():
    source = run_fixture("c_plus").record
    plain = build_inventory(source, public_id=PUBLIC_ID, shared_capture=True)
    marked = build_inventory(
        replace(
            source,
            manifest=object(),
            private_metadata={"assignment": "L1_CONDITION_MARKER", "truth": "L2_TRUTH_MARKER"},
            source_path="PRIVATE_PATH_MARKER",
        ),
        public_id=PUBLIC_ID,
        shared_capture=True,
    )
    for view, packet in complete(plain).items():
        other = complete(marked)[view]
        assert packet.text == other.text
        for marker in ("MARKER", "C+", "c_plus", "coalition", "regret", "pair_benefit"):
            assert marker not in packet.text


def test_capture_positions_and_unknown_order_survive_without_invention():
    for known in (True, False):
        record = run_fixture("c_plus").record
        if not known:
            record = replace(record, event_journal=None)
        inventory = build_inventory(record, public_id=PUBLIC_ID, shared_capture=known)
        facts = complete(inventory)[View.R].verify()[1]
        original = {f.fact_id: f.ordering_json for f in inventory.facts}
        assert all(f.ordering_json == original[f.fact_id] for f in facts)
        positions = [json.loads(f.ordering_json)["logical_position"] for f in facts]
        assert any(p is not None for p in positions) == known


def test_owner_vectors_require_complete_neutral_order():
    from pactlens.evidence.compact_views import _owners

    rows = [{"incident": f"Incident-{n}", "agent": "Actor-1"} for n in (1, 2, 3)]
    assert _owners(_owners(rows), expand=True) == rows
    with pytest.raises(ValueError, match="ALLOCATION_OWNER_ORDER"):
        _owners([rows[1], rows[0], rows[2]])
    with pytest.raises(ValueError, match="ALLOCATION_OWNER_CODES"):
        _owners([1, 2, 4], expand=True)


def test_compact_view_requires_matching_manifest_and_budget(six_action):
    packet = complete(six_action[ObservationPolicy.DELIVERED])[View.MA]
    manifest = json.loads(packet.manifest_json)
    for change in (
        lambda m: m["budget"].update(estimated_tokens=1),
        lambda m: m.update(
            omitted=[
                {"fact_id": m["facts"][0]["fact_id"], "category": "CONTEXT", "kind": "public_task"}
            ]
        ),
        lambda m: m.update(render_hash="0" * 64),
        lambda m: m["facts"].pop(),
    ):
        broken = json.loads(packet.manifest_json)
        change(broken)
        with pytest.raises((ValueError, TypeError)):
            CompactView(packet.view, packet.text, canonical_json(broken), packet.envelope).verify()
    assert manifest["budget"]["exact_tokens"] is None


def test_fresh_processes_render_identical_tables():
    code = """from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.sufficiency import select_common
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import content_hash
r=select_common(build_inventory(run_fixture('c_plus').record,public_id='d6dd1a02-5135-4fd7-9844-2dd36366a68e',shared_capture=True))
print(content_hash([r.manifest_json,*[p.text for p in r.packets]]))
"""
    outputs = {
        subprocess.check_output(
            [sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": str(seed)}, text=True
        )
        for seed in (2, 91)
    }
    assert len(outputs) == 1
