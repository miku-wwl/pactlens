import asyncio
import json
from dataclasses import replace

import pytest
from harness_helpers import run_fake
from view_helpers import PUBLIC_ID, routed_record

from pactlens.agents.provider import ModelConfig
from pactlens.evidence.budget_selection import select_evidence
from pactlens.evidence.budgeted_views import verify_budgeted_parity
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import View
from pactlens.research.fixtures import run_fixture
from pactlens.research.freeze_manifest import freeze_candidates
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json


@pytest.mark.parametrize("enabled,failed", [(True, False), (False, False), (True, True)])
def test_budgeted_observer_rights_are_separate_from_private_audit(enabled, failed):
    text = "OBSERVABLE_ROUTER_EVENT"
    record, router = routed_record(enabled=enabled, failed=failed, text=text)
    packets = {}
    for policy in ObservationPolicy:
        inv = build_inventory(
            record, (), router.deliveries, public_id=PUBLIC_ID, policy=policy, shared_capture=True
        )
        result = select_evidence(inv)
        r, e = result.packet(View.R), result.packet(View.MAE)
        assert verify_budgeted_parity(r, e)
        packets[policy] = r
    delivered = enabled and not failed
    assert (text in packets[ObservationPolicy.DELIVERED].text) is delivered
    assert text in packets[ObservationPolicy.ROUTER_AUDIT].text
    assert len(router.deliveries) == 1
    if not delivered:
        assert (
            packets[ObservationPolicy.DELIVERED].text
            != packets[ObservationPolicy.ROUTER_AUDIT].text
        )


def test_pair_public_schema_and_n2_missingness_remain_honest(tmp_path, task):
    headers = []
    for enabled in (True, False):
        record, router = routed_record(enabled=enabled)
        inv = build_inventory(
            record, (), router.deliveries, public_id=PUBLIC_ID, shared_capture=True
        )
        headers.append(select_evidence(inv).packet(View.R).verify()[0])
    assert set(headers[0]) == set(headers[1])
    assert all(h["policy"] == ObservationPolicy.ROUTER_AUDIT.value for h in headers)
    run, _ = asyncio.run(run_fake(tmp_path / "n2-harness", task, condition=Condition.N2))
    n2 = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        status=run.status,
        shared_capture=True,
    )
    facts = select_evidence(n2).packet(View.R).verify()[1]
    slots = [
        f.as_mapping()["payload"]
        for f in facts
        if f.kind == "proposal_slot" and f.as_mapping()["payload"]["round"] == 2
    ]
    assert len(slots) == 3 and all(
        x["status"] == "MISSING" and x["assignments"] is None for x in slots
    )


def test_nested_private_markers_and_private_path_never_reach_any_budgeted_context():
    markers = [f"PRIVATE_L1_L2_MARKER_{i}" for i in range(15)]
    record = run_fixture("c_plus").record
    altered = replace(
        record,
        manifest=object(),
        private_metadata={
            "condition": markers[0],
            "coalition": markers[1],
            "split": markers[2],
            "group": markers[3],
            "seed": markers[4],
            "brief": markers[5],
            "model_prompt": markers[6],
            "hidden": {
                "oracle": markers[7],
                "truth": markers[8],
                "notes": markers[9],
                "twin": markers[10],
                "path": markers[11],
                "capability": markers[12],
                "grant": markers[13],
            },
        },
        source_path=markers[14],
    )
    inv = build_inventory(altered, public_id=PUBLIC_ID)
    result = select_evidence(inv)
    for packet in result.packets:
        combined = packet.text + packet.manifest_json + canonical_json(packet.conversation())
        assert all(marker not in combined for marker in markers)
        assert "PRIVATE_L1_L2" not in packet.verify()[0]["episode"]


def test_freeze_candidate_manifest_is_deterministic_and_never_approved():
    identity = {
        "endpoint_type": "ollama_loopback_openai",
        "server_version": "OFFLINE-STUB",
        "model": "local-test-model",
        "model_digest": "a" * 64,
        "seed_support": "REQUESTED_NOT_VERIFIED",
        "cloud_model": False,
    }
    config = ModelConfig("local-test-model", "a" * 64, "ollama_loopback_openai")
    first = freeze_candidates(identity, config)
    assert first == freeze_candidates(dict(reversed(list(identity.items()))), config)
    assert all(d["status"] in ("PROPOSED", "PENDING", "NO-GO") for d in first["decisions"].values())
    assert first["decisions"]["primary_observer"]["candidate"] == ObservationPolicy.DELIVERED.value
    assert first["decisions"]["formal_pilot"]["status"] == "NO-GO"
    assert first["agent_input_limit"] == 2000 and first["agent_output_limit"] == 256
    assert "Private brief" not in json.dumps(first)
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        freeze_candidates(identity, replace(config, revision="b" * 64))
    with pytest.raises(ValueError, match="IDENTITY_FIELDS"):
        freeze_candidates({**identity, "condition": "PRIVATE"}, config)
