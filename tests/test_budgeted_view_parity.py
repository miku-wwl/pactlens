import asyncio
import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
from harness_helpers import run_fake
from view_helpers import PUBLIC_ID

from pactlens.agents.budgets import BudgetExceeded
from pactlens.evidence.budget_selection import SelectionFailure, select_evidence
from pactlens.evidence.budgeted_views import (
    compact_task,
    expand_task,
    render_budgeted,
    verify_budgeted_parity,
)
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import canonical_json


@pytest.fixture(scope="module")
def budgeted():
    inv = build_inventory(run_fixture("c_plus").record, public_id=PUBLIC_ID, shared_capture=True)
    return inv, select_evidence(inv)


@pytest.mark.parametrize("view", list(View))
def test_actual_reconstructed_facts_and_cross_view_subsets(budgeted, view):
    inventory, result = budgeted
    packet = result.packet(view)
    _, facts = packet.verify()
    originals = {f.fact_id: f for f in inventory.facts}
    assert all(originals[f.fact_id] == f for f in facts)
    r_ids = {f.fact_id for f in result.packet(View.R).verify()[1]}
    assert {f.fact_id for f in facts} <= r_ids
    if view in (View.M, View.A, View.MA):
        assert not any(f.category == "INTEGRITY" for f in facts)
        assert "INTEGRITY" not in json.loads(packet.manifest_json)["header"]["omitted_by_category"]
    assert verify_budgeted_parity(result.packet(View.R), result.packet(View.MAE))
    m = {f.fact_id for f in result.packet(View.M).verify()[1]}
    a = {f.fact_id for f in result.packet(View.A).verify()[1]}
    ma = {f.fact_id for f in result.packet(View.MA).verify()[1]}
    assert m | a == ma and ma < r_ids


@pytest.mark.parametrize(
    "case",
    [
        "value",
        "missing",
        "extra",
        "order",
        "legend",
        "duplicate",
        "manifest",
        "budget",
        "envelope",
        "omission",
        "group",
    ],
)
def test_tampered_rendering_or_binding_is_rejected(budgeted, case):
    _, result = budgeted
    packet = result.packet(View.MAE if case == "group" else View.R)
    manifest = json.loads(packet.manifest_json)
    lines = packet.text.splitlines()
    if case == "group":
        body = json.loads(packet.text)
        body["groups"]["INTEGRITY"] = body["groups"]["INTEGRITY"][1:]
        text = canonical_json(body)
    elif case in ("manifest", "budget", "omission", "envelope"):
        if case == "manifest":
            manifest["facts"] = manifest["facts"][:-1]
        elif case == "budget":
            manifest["budget"]["estimated_tokens"] += 1
        elif case == "omission":
            manifest["omitted"] = []
        else:
            manifest["envelope_hash"] = "0" * 64
        text = packet.text
    else:
        header = json.loads(lines[0])
        row = json.loads(lines[1])
        if case == "value":
            row[2] = "Actor-1" if row[2] != "Actor-1" else "Actor-2"
        elif case == "missing":
            row.pop()
        elif case == "extra":
            row.append("PRIVATE_TRUTH")
        elif case == "order":
            row[-1] = True
        elif case == "legend":
            header["payload_columns"][row[1]].append("private_coalition")
        elif case == "duplicate":
            lines.append(lines[1])
        lines[0], lines[1] = canonical_json(header), canonical_json(row)
        text = "\n".join(lines)
    with pytest.raises((ValueError, TypeError)):
        replace(packet, text=text, manifest_json=canonical_json(manifest)).verify()


def test_compact_constraints_reconstruct_exactly_without_oracle_and_envelope_is_complete(budgeted):
    inv, result = budgeted
    task = next(f.as_mapping()["payload"] for f in inv.facts if f.kind == "public_task")
    assert expand_task(compact_task(task)) == task
    packet = result.packet(View.R)
    turns = packet.conversation()
    assert len(turns) == 3
    assert "RESPONSE_SCHEMA" in turns[-1].content and "risk_score" in turns[-1].content
    assert "EVIDENCE" in turns[1].content and packet.text in turns[1].content
    report = json.loads(packet.manifest_json)["budget"]
    assert report["utf8_bytes"] == sum(
        len(t.role.encode()) + len(t.content.encode()) for t in turns
    )
    assert report["utf8_bytes"] > len(packet.text.encode())
    with pytest.raises(BudgetExceeded):
        replace(packet, envelope=replace(packet.envelope, system="x" * 8000)).envelope.budget(
            packet.text, require=True
        )


def test_trusted_exact_counter_seam_is_distinguished_from_heuristic_not_real_measurement(budgeted):
    inv, _ = budgeted
    calls = []

    def synthetic_counter(turns):
        calls.append(turns)
        return 2000

    result = select_evidence(inv, token_counter=synthetic_counter)
    assert calls and all(len(t) == 3 and "RESPONSE_SCHEMA" in t[-1].content for t in calls)
    manifest = json.loads(result.packet(View.MAE).manifest_json)
    assert manifest["budget"]["exact_tokens"] == 2000
    assert manifest["budget"]["method"] == "TRUSTED_TOKEN_COUNTER"
    result.packet(View.MAE).conversation(token_counter=synthetic_counter)
    with pytest.raises(ValueError):
        select_evidence(inv, token_counter=lambda turns: False)
    with pytest.raises(SelectionFailure):
        select_evidence(inv, envelope=DetectorEnvelope(context_window_tokens=1024))


def test_fresh_processes_are_deterministic_and_selected_order_is_not_chronology():
    code = """from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.budget_selection import select_evidence
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import content_hash
r=select_evidence(build_inventory(run_fixture('c_plus').record,public_id='d6dd1a02-5135-4fd7-9844-2dd36366a68e',shared_capture=True))
print(content_hash([r.manifest_json,*[p.text for p in r.packets]]))
"""
    outputs = [
        subprocess.check_output(
            [sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": str(seed)}, text=True
        )
        for seed in (1, 73)
    ]
    assert outputs[0] == outputs[1]


def test_real_aig_bundles_remain_atomic_and_unknown_receipt_is_not_success(tmp_path, task):
    async def lost_ack(phase):
        if phase == "after_commit":
            raise RuntimeError("offline test lost ack")

    run, model = asyncio.run(run_fake(tmp_path / "unknown", task, checkpoint=lost_ack))
    assert run.status == "STOPPED_UNKNOWN" and len(model.requests) == 1
    inv = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    try:
        result = select_evidence(inv)
        r, e = result.packet(View.R), result.packet(View.MAE)
    except SelectionFailure as failure:
        # A genuine mandatory overflow is preserved, never called a fitting input.
        report = json.loads(failure.diagnostics_json)
        assert all(
            f.fact_id in report["mandatory_fact_ids"]
            for f in inv.facts
            if f.kind in ("aig_action", "consumer_receipt")
        )
        ids = {f.fact_id for f in inv.facts}
        r = render_budgeted(
            inv, ids, ids, "0" * 64, View.R, DetectorEnvelope(), token_counter=lambda turns: 2000
        )
        e = render_budgeted(
            inv, ids, ids, "0" * 64, View.MAE, DetectorEnvelope(), token_counter=lambda turns: 2000
        )
    assert verify_budgeted_parity(r, e)
    facts = r.verify()[1]
    observed = [
        f.as_mapping() for f in facts if f.kind == "aig_action" and f.completeness == "OBSERVED"
    ]
    receipts = [
        f.as_mapping()
        for f in facts
        if f.kind == "consumer_receipt" and f.completeness == "OBSERVED"
    ]
    assert len(observed) == len(receipts) == 1
    assert observed[0]["payload"]["action_state"] == "Unknown"
    assert receipts[0]["payload"]["receipt_status"] == "VERIFIED_COMMITTED"
    assert observed[0]["payload"]["action_id"] == receipts[0]["payload"]["action_id"]


def test_known_and_unknown_source_clocks_survive_lossless_encoding():
    for known in (True, False):
        record = run_fixture("c_plus").record
        if not known:
            record = replace(record, event_journal=None)
        inv = build_inventory(record, public_id=PUBLIC_ID, shared_capture=known)
        result = select_evidence(inv)
        packet = result.packet(View.R)
        header, facts = packet.verify()
        assert header["render_order"] == "PRESENTATION_ORDER_NOT_CHRONOLOGY"
        original = {f.fact_id: f.ordering_json for f in inv.facts}
        assert all(f.ordering_json == original[f.fact_id] for f in facts)
