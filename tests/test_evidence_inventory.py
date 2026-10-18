import json
from dataclasses import replace
from uuid import UUID

import pytest
from view_helpers import PUBLIC_ID

from pactlens.evidence.inventory import Fact, Inventory, build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import canonical_json


def test_fact_identity_aliases_provenance_completeness_and_defensive_copy():
    source = run_fixture("c_plus").record
    inventory = build_inventory(source, public_id=PUBLIC_ID, shared_capture=True)
    assert type(inventory.facts) is tuple
    assert len({f.fact_id for f in inventory.facts}) == len(inventory.facts)
    for fact in inventory.facts:
        assert UUID(fact.fact_id).version == 5
        assert fact.actor is None or fact.actor in ("Actor-1", "Actor-2", "Actor-3")
        assert Fact.from_mapping(fact.as_mapping()) == fact
        assert fact.source and fact.trust and fact.completeness
    message = next(f for f in inventory.facts if f.kind == "message")
    changed = message.as_mapping()
    changed["payload"]["text"] = "changed copy"
    assert changed != message.as_mapping()
    absent = [f for f in inventory.facts if f.kind == "aig_action"]
    assert len(absent) == 6 and all(f.completeness == "MISSING" for f in absent)
    assert all(json.loads(f.ordering_json)["cross_source_order"] == "UNKNOWN" for f in absent)


@pytest.mark.parametrize(
    "case", ["id", "actor", "source", "payload", "nested", "order", "category", "completeness"]
)
def test_fact_rejects_private_or_unrecognized_metadata(case):
    inventory = build_inventory(
        run_fixture("c_plus").record, public_id=PUBLIC_ID, shared_capture=True
    )
    fact = inventory.facts[0]
    changes = {
        "id": {"fact_id": "T001-C_PLUS"},
        "actor": {"actor": "PRIVATE_COALITION"},
        "source": {"source": "PRIVATE_GATE_PATH"},
        "payload": {"payload_json": canonical_json({"condition": "C+"})},
        "nested": {
            "payload_json": canonical_json(
                {"agents": [{"private_brief": "SECRET"}], "incidents": [], "objective": {}}
            )
        },
        "order": {
            "ordering_json": canonical_json(
                {
                    "stream": "x",
                    "source_sequence": 1,
                    "logical_position": 4,
                    "cross_source_order": "UNKNOWN",
                }
            )
        },
        "category": {"category": "PRIVATE_ASSIGNMENT"},
        "completeness": {"completeness": "N2"},
    }
    with pytest.raises(ValueError):
        replace(fact, **changes[case])


def test_inventory_ids_do_not_depend_on_private_assignment_or_seed():
    record = run_fixture("c_plus").record
    first = build_inventory(record, public_id=PUBLIC_ID, shared_capture=True)
    altered = replace(
        record,
        manifest=object(),
        private_metadata={
            "condition": "PRIVATE_CONDITION",
            "group": "PRIVATE_GROUP",
            "seed": "PRIVATE_SEED",
            "twin_result": "PRIVATE_TWIN",
        },
        source_path="PRIVATE_GATE_PATH",
    )
    second = build_inventory(altered, public_id=PUBLIC_ID, shared_capture=True)
    assert first == second
    with pytest.raises(ValueError):
        Inventory(PUBLIC_ID, ObservationPolicy.ROUTER_AUDIT, (first.facts[0], first.facts[0]))


def test_unknown_source_order_remains_unknown():
    record = replace(run_fixture("c_plus").record, event_journal=None)
    inventory = build_inventory(record, public_id=PUBLIC_ID)
    dynamic = [
        json.loads(f.ordering_json) for f in inventory.facts if f.kind in ("message", "arena_event")
    ]
    assert dynamic and all(
        o["logical_position"] is None and o["cross_source_order"] == "UNKNOWN" for o in dynamic
    )
