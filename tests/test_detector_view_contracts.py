import asyncio
import json

import pytest
from harness_helpers import run_fake
from view_helpers import PUBLIC_ID, routed_record

from pactlens.agents.budgets import BudgetExceeded
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.parity import canonical_facts, verify_parity
from pactlens.evidence.renderers import extract_rendered, render_view
from pactlens.evidence.views import CATEGORIES, View, view_facts
from pactlens.research.fixtures import run_fixture
from pactlens.research.seeds import Condition


@pytest.mark.parametrize("policy", list(ObservationPolicy))
@pytest.mark.parametrize("view", list(View))
def test_five_view_fact_matrix_has_exact_declared_information(policy, view):
    record, router = routed_record(enabled=True, text="VISIBLE_MESSAGE_CONTENT")
    inventory = build_inventory(
        record, (), router.deliveries, public_id=PUBLIC_ID, policy=policy, shared_capture=True
    )
    rendered = render_view(inventory, view)
    header, facts = extract_rendered(rendered.text, view)
    assert {f.fact_id for f in facts} == {f.fact_id for f in view_facts(inventory, view)}
    assert all(f.category in CATEGORIES[view] for f in facts)
    assert header["observation_policy"] == policy.value
    assert rendered.verify()[1]
    if view == View.M:
        assert not any(
            f.kind
            in ("proposal_slot", "arena_event", "execution", "aig_action", "consumer_receipt")
            for f in facts
        )
    if view == View.A:
        assert "VISIBLE_MESSAGE_CONTENT" not in rendered.text
        assert not any(f.category in ("COMMUNICATION", "INTEGRITY") for f in facts)
    if view == View.MA:
        assert not any(f.category == "INTEGRITY" for f in facts)


def test_ma_is_union_and_r_adds_integrity_without_changing_ma_facts():
    inventory = build_inventory(
        run_fixture("c_plus").record, public_id=PUBLIC_ID, shared_capture=True
    )
    by_view = {v: {f.fact_id: f for f in view_facts(inventory, v)} for v in View}
    assert by_view[View.MA] == by_view[View.M] | by_view[View.A]
    assert all(by_view[View.R][key] == value for key, value in by_view[View.MA].items())
    assert {f.category for key, f in by_view[View.R].items() if key not in by_view[View.MA]} == {
        "INTEGRITY"
    }
    r, mae = render_view(inventory, View.R), render_view(inventory, View.MAE)
    assert r.text != mae.text and verify_parity(r, mae)
    assert canonical_facts(r) == canonical_facts(mae)


def test_monitor_budget_is_observable_and_blocks_without_silent_selection():
    inventory = build_inventory(
        run_fixture("c_plus").record, public_id=PUBLIC_ID, shared_capture=True
    )
    rendered = render_view(inventory, View.MAE)
    manifest = json.loads(rendered.manifest_json)
    assert manifest["bytes"] == len(rendered.text.encode())
    assert manifest["token_budget"]["exact_tokens"] is None
    assert manifest["selection_policy"] == "FULL_INVENTORY_OR_EXPLICIT_OVERFLOW_V1"
    before = rendered.text
    with pytest.raises(BudgetExceeded):
        rendered.conversation()
    assert rendered.text == before
    first = rendered.conversation(token_counter=lambda turns: 4096)  # synthetic boundary counter
    second = rendered.conversation(token_counter=lambda turns: 4096)
    assert first == second and first is not second and len(first) == 2
    with pytest.raises(BudgetExceeded):
        rendered.conversation(token_counter=lambda turns: 4097)


def test_n2_final_missingness_is_preserved_and_not_claimed_eliminated(tmp_path, task):
    run, _ = asyncio.run(run_fake(tmp_path, task, condition=Condition.N2))
    inventory = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    facts = view_facts(inventory, View.A)
    slots = [json.loads(f.payload_json) for f in facts if f.kind == "proposal_slot"]
    assert len([s for s in slots if s["round"] == 2 and s["status"] == "MISSING"]) == 3
    assert run.executor_calls == 3 and run.record.adjudication.behavior_class is None
