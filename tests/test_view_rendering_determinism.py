import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
from view_helpers import PUBLIC_ID

from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.parity import canonical_facts, verify_parity
from pactlens.evidence.renderers import render_view
from pactlens.evidence.views import View
from pactlens.research.fixtures import run_fixture


def test_fresh_process_hash_seeds_and_serialization_are_deterministic(tmp_path):
    script = """
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.renderers import render_view
from pactlens.evidence.views import View
from pactlens.research.fixtures import run_fixture
from pactlens.serialization import canonical_json,content_hash
i=build_inventory(run_fixture('c_plus').record,public_id='d6dd1a02-5135-4fd7-9844-2dd36366a68e',shared_capture=True)
print(canonical_json({v.value:content_hash(render_view(i,v).text) for v in View}))
"""
    outputs = [
        subprocess.check_output(
            [sys.executable, "-c", script],
            cwd=tmp_path,
            env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONIOENCODING": "utf-8"},
            text=True,
            encoding="utf-8",
        )
        for seed in ("17", "991")
    ]
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("known", [True, False])
def test_render_order_never_claims_chronology_and_unknown_is_preserved(known):
    record = run_fixture("c_plus").record
    if not known:
        record = replace(record, event_journal=None)
    inventory = build_inventory(record, public_id=PUBLIC_ID, shared_capture=known)
    r, mae = render_view(inventory, View.R), render_view(inventory, View.MAE)
    assert verify_parity(r, mae)
    facts = json.loads(canonical_facts(r))["facts"]
    events = [f for f in facts if f["kind"] in ("message", "arena_event")]
    assert all(
        f["ordering"]["cross_source_order"] == ("RECORDED" if known else "UNKNOWN") for f in events
    )
    assert all((f["ordering"]["logical_position"] is not None) == known for f in events)
    assert (
        json.loads(r.text.splitlines()[0])["render_order"]
        == "SOURCE_FAMILIES_NOT_GLOBAL_CHRONOLOGY"
    )
    assert json.loads(mae.text)["render_order"] == "CATEGORY_ACTOR_KIND_NOT_CHRONOLOGY"
