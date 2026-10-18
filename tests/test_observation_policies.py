import json

import pytest
from view_helpers import PUBLIC_ID, routed_record

from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy, project_observation
from pactlens.evidence.parity import verify_parity
from pactlens.evidence.renderers import render_view
from pactlens.evidence.views import View
from pactlens.serialization import canonical_json


@pytest.mark.parametrize("enabled,failed", [(True, False), (False, False), (True, True)])
def test_complete_private_audit_observer_access_and_actor_inbox_are_distinct(enabled, failed):
    record, router = routed_record(enabled=enabled, failed=failed, text="OBSERVED_ATTEMPT_TEXT")
    audit_before = canonical_json(router.deliveries)
    a = project_observation(
        record,
        (),
        router.deliveries,
        public_id=PUBLIC_ID,
        policy=ObservationPolicy.DELIVERED,
        shared_capture=True,
    ).as_mapping()
    b = project_observation(
        record,
        (),
        router.deliveries,
        public_id=PUBLIC_ID,
        policy=ObservationPolicy.ROUTER_AUDIT,
        shared_capture=True,
    ).as_mapping()
    delivered = enabled and not failed
    assert bool(router.inbox("a1")) == delivered
    assert bool(a["messages"]["records"]) == delivered
    assert a["communication_audit"] == {"status": "NOT_IN_POLICY", "records": []}
    assert len(b["communication_audit"]["records"]) == 1
    row = b["communication_audit"]["records"][0]
    assert row["delivery_state"] == (
        "DELIVERED" if delivered else "FAILED" if failed else "BLOCKED"
    )
    assert bool(row["delivered_recipients"]) == delivered
    assert canonical_json(router.deliveries) == audit_before
    if not delivered:
        assert "OBSERVED_ATTEMPT_TEXT" not in canonical_json(a)
        assert "OBSERVED_ATTEMPT_TEXT" in canonical_json(b)
    for policy in ObservationPolicy:
        inventory = build_inventory(
            record, (), router.deliveries, public_id=PUBLIC_ID, policy=policy, shared_capture=True
        )
        assert verify_parity(render_view(inventory, View.R), render_view(inventory, View.MAE))


@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_paired_visibility_schema_is_same_but_valid_observable_artifacts_remain(policy):
    packets = []
    for enabled in (True, False):
        record, router = routed_record(enabled=enabled)
        packets.append(
            project_observation(
                record,
                (),
                router.deliveries,
                public_id=PUBLIC_ID,
                policy=policy,
                shared_capture=True,
            ).as_mapping()
        )
    assert set(packets[0]) == set(packets[1])
    assert set(packets[0]["communication_audit"]) == set(packets[1]["communication_audit"])
    assert "C+" not in canonical_json(packets) and "C−" not in canonical_json(packets)
    if policy == ObservationPolicy.ROUTER_AUDIT:
        assert packets[0]["communication_audit"]["records"][0]["delivery_state"] == "DELIVERED"
        assert packets[1]["communication_audit"]["records"][0]["delivery_state"] == "BLOCKED"


def test_primary_compatibility_policy_is_router_audit_and_invalid_config_is_not_exported():
    record, router = routed_record(enabled=False)
    packet = project_observation(
        record, (), router.deliveries, public_id=PUBLIC_ID, shared_capture=True
    ).as_mapping()
    assert packet["observation_policy"] == ObservationPolicy.ROUTER_AUDIT.value
    assert "private_pair" not in json.dumps(packet)
    with pytest.raises(ValueError):
        project_observation(record, public_id=PUBLIC_ID, status="PRIVATE_CONDITION")
    with pytest.raises(ValueError):
        project_observation(record, public_id=PUBLIC_ID, policy="PRIVATE_CONDITION")
