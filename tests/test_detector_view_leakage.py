import json
from dataclasses import replace

import pytest
from view_helpers import PUBLIC_ID, routed_record

from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.parity import canonical_facts
from pactlens.evidence.renderers import export_view, render_view
from pactlens.evidence.views import View
from pactlens.research.fixtures import run_fixture


@pytest.mark.parametrize("view", list(View))
@pytest.mark.parametrize("policy", list(ObservationPolicy))
def test_all_private_marker_classes_absent_from_view_manifest_context_and_filename(
    tmp_path, view, policy
):
    source = run_fixture("c_plus").record
    kinds = (
        "CONDITION",
        "COALITION",
        "SPLIT",
        "GROUP",
        "SEED",
        "PRIVATE_INSTRUCTION",
        "SYSTEM_PROMPT",
        "SCENARIO",
        "ORACLE_REFERENCE",
        "GROUND_TRUTH",
        "ADJUDICATION",
        "TWIN_RESULT",
        "GATE_PATH",
        "CAPABILITY",
        "AUTHORIZATION_SECRET",
    )
    markers = ["HIDDEN_MARKER_" + kind for kind in kinds]
    record = replace(
        source,
        private_metadata={
            kind: {"nested": marker} for kind, marker in zip(kinds, markers, strict=True)
        },
        source_path="C:/private/" + markers[-3],
        manifest=object(),
        adjudication=replace(
            source.adjudication, notes=tuple(markers), instruction_origin=markers[5]
        ),
    )
    inventory = build_inventory(record, public_id=PUBLIC_ID, policy=policy, shared_capture=True)
    rendered = render_view(inventory, view)
    exported = export_view(rendered, tmp_path)
    # Synthetic counter only exposes the exact serialized packet to inspect leakage.
    context = rendered.conversation(token_counter=lambda turns: 500)
    outputs = (
        rendered.text,
        rendered.manifest_json,
        canonical_facts(rendered),
        exported.read_text(encoding="utf-8"),
        exported.name,
        repr(context),
        repr(inventory),
    )
    assert all(marker not in text for marker in markers for text in outputs)
    original = render_view(
        build_inventory(source, public_id=PUBLIC_ID, policy=policy, shared_capture=True), view
    )
    assert original == rendered
    assert exported.name == f"{PUBLIC_ID}.{view.value}.json"
    with pytest.raises(FileExistsError):
        export_view(rendered, tmp_path)


def test_private_objects_are_not_reflected_or_inspected_by_any_view():
    class Poison:
        def __repr__(self):
            raise AssertionError("Private object inspected")

        def __iter__(self):
            raise AssertionError("Private object inspected")

    record = replace(
        run_fixture("c_plus").record,
        private_metadata=Poison(),
        manifest=Poison(),
        source_path=Poison(),
        adjudication=None,
    )
    inventory = build_inventory(record, public_id=PUBLIC_ID, shared_capture=True)
    assert all(render_view(inventory, view).verify() for view in View)


def test_blocked_attempt_is_visible_only_when_the_observer_has_router_rights():
    record, router = routed_record(enabled=False, text="PREDICTIVE_ATTEMPT_SPEECH")
    inventories = {
        p: build_inventory(
            record, (), router.deliveries, public_id=PUBLIC_ID, policy=p, shared_capture=True
        )
        for p in ObservationPolicy
    }
    for view in View:
        delivered = render_view(inventories[ObservationPolicy.DELIVERED], view).text
        audit = render_view(inventories[ObservationPolicy.ROUTER_AUDIT], view).text
        assert "PREDICTIVE_ATTEMPT_SPEECH" not in delivered
        assert ("PREDICTIVE_ATTEMPT_SPEECH" in audit) == (view != View.A)
    assert "private_pair" not in json.dumps(
        [f.as_mapping() for f in inventories[ObservationPolicy.ROUTER_AUDIT].facts]
    )
