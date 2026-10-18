import asyncio
import json
from dataclasses import replace
from uuid import UUID, uuid5

import pytest
from harness_helpers import message, run_fake
from view_helpers import PUBLIC_ID

from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.parity import canonical_facts, verify_parity
from pactlens.evidence.renderers import RenderedView, render_view
from pactlens.evidence.views import View
from pactlens.research.fixtures import load_specs, run_fixture
from pactlens.serialization import canonical_json


@pytest.fixture(scope="module")
def aig_inventory(tmp_path_factory):
    from pactlens.research.fixtures import fixture_task

    run, _ = asyncio.run(
        run_fake(tmp_path_factory.mktemp("view-real-aig"), fixture_task(), transform=message)
    )
    inventory = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    return run, inventory


@pytest.mark.parametrize("case", [s.name for s in load_specs()])
@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_every_engineering_fixture_has_serialized_semantic_parity(case, policy):
    record = run_fixture(case).record
    inventory = build_inventory(record, public_id=PUBLIC_ID, policy=policy, shared_capture=True)
    r, mae = render_view(inventory, View.R), render_view(inventory, View.MAE)
    # Detached reconstruction of both actual serialized inputs and their manifests.
    reconstructed_r = RenderedView(
        View.R, r.text.encode().decode(), r.manifest_json.encode().decode()
    )
    reconstructed_mae = RenderedView(
        View.MAE, mae.text.encode().decode(), mae.manifest_json.encode().decode()
    )
    assert verify_parity(reconstructed_r, reconstructed_mae)
    assert canonical_facts(r) == canonical_facts(mae)


def test_real_aig_receipt_states_values_and_order_survive_both_renderings(aig_inventory):
    run, inventory = aig_inventory
    r, mae = render_view(inventory, View.R), render_view(inventory, View.MAE)
    assert verify_parity(r, mae)
    records = json.loads(canonical_facts(r))["facts"]
    actions = [f for f in records if f["kind"] == "aig_action"]
    receipts = [f for f in records if f["kind"] == "consumer_receipt"]
    assert len(actions) == len(receipts) == 6
    assert {f["payload"]["action_state"] for f in actions} == {"Succeeded"}
    assert all(f["payload"]["receipt_status"] == "VERIFIED_COMMITTED" for f in receipts)
    assert {f["payload"]["receipt_reference"] for f in receipts} == {
        o.receipt_reference for o in run.observations
    }
    assert all(f["ordering"]["cross_source_order"] == "RECORDED" for f in actions)


@pytest.mark.parametrize("field", ["fact_id", "actor", "payload", "completeness", "ordering"])
def test_parity_detects_semantic_drift_even_when_each_manifest_is_valid(aig_inventory, field):
    _, inventory = aig_inventory
    index = next(i for i, f in enumerate(inventory.facts) if f.kind == "aig_action")
    fact = inventory.facts[index]
    if field == "fact_id":
        changed = replace(fact, fact_id=str(uuid5(UUID(PUBLIC_ID), "different-public-fact")))
    elif field == "actor":
        changed = replace(fact, actor="Actor-3" if fact.actor != "Actor-3" else "Actor-1")
    elif field == "payload":
        payload = json.loads(fact.payload_json)
        payload["action_state"] = "Unknown"
        changed = replace(fact, payload_json=canonical_json(payload))
    elif field == "completeness":
        changed = replace(fact, completeness="INCOMPLETE")
    else:
        ordering = json.loads(fact.ordering_json)
        ordering["logical_position"] += 1
        changed = replace(fact, ordering_json=canonical_json(ordering))
    altered = replace(
        inventory, facts=(*inventory.facts[:index], changed, *inventory.facts[index + 1 :])
    )
    raw, structured = render_view(inventory, View.R), render_view(altered, View.MAE)
    raw.verify()
    structured.verify()
    with pytest.raises(ValueError, match="INFORMATION_MISMATCH"):
        verify_parity(raw, structured)


@pytest.mark.parametrize(
    "case",
    ["text", "manifest", "omitted_field", "extra_field", "duplicate_fact", "header", "budget"],
)
def test_render_manifest_binding_and_reconstruction_boundaries(aig_inventory, case):
    _, inventory = aig_inventory
    rendered = render_view(inventory, View.R)
    manifest = json.loads(rendered.manifest_json)
    lines = rendered.text.splitlines()
    if case == "text":
        lines[-1] = lines[-1].replace("INTEGRITY", "BEHAVIOR")
    elif case == "manifest":
        manifest["facts"] = manifest["facts"][:-1]
    elif case in ("omitted_field", "extra_field"):
        record = json.loads(lines[-1])
        if case == "omitted_field":
            record.pop("completeness")
        else:
            record["condition"] = "PRIVATE"
        lines[-1] = canonical_json(record)
    elif case == "duplicate_fact":
        lines.append(lines[-1])
    elif case == "budget":
        manifest["token_budget"]["fits"] = not manifest["token_budget"]["fits"]
    else:
        header = json.loads(lines[0])
        header["observation_policy"] = "PRIVATE_POLICY"
        lines[0] = canonical_json(header)
    changed = replace(rendered, text="\n".join(lines), manifest_json=canonical_json(manifest))
    with pytest.raises((ValueError, TypeError)):
        changed.verify()


def test_unknown_with_committed_receipt_stays_unknown_in_views(tmp_path, task):
    async def lost_ack(phase):
        if phase == "after_commit":
            raise RuntimeError("synthetic lost acknowledgment")

    run, _ = asyncio.run(run_fake(tmp_path, task, checkpoint=lost_ack))
    assert run.status == "STOPPED_UNKNOWN"
    inventory = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    r, mae = render_view(inventory, View.R), render_view(inventory, View.MAE)
    assert verify_parity(r, mae)
    facts = json.loads(canonical_facts(r))["facts"]
    present = [f for f in facts if f["kind"] == "aig_action" and f["completeness"] == "OBSERVED"]
    committed = [
        f for f in facts if f["kind"] == "consumer_receipt" and f["completeness"] == "OBSERVED"
    ]
    assert len(present) == len(committed) == 1
    assert present[0]["payload"]["action_state"] == "Unknown"
    assert committed[0]["payload"]["receipt_status"] == "VERIFIED_COMMITTED"
    assert not run.record.state.proposals
