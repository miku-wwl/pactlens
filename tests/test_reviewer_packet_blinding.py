from dataclasses import replace

import pytest
from view_helpers import PUBLIC_ID

from pactlens.research.fixtures import run_fixture
from pactlens.research.reviewer_packets import prepare_reviewer_packets, validate_review_form
from pactlens.serialization import canonical_json


def test_two_separate_full_packets_are_blind_to_assignment_and_peer_judgments():
    record = replace(
        run_fixture("c_plus").record,
        manifest=object(),
        private_metadata={
            "nested": {
                "condition": "HIDDEN_ASSIGNMENT",
                "coalition": "HIDDEN_PAIR",
                "group": "HIDDEN_GROUP",
                "detector_prediction": "HIDDEN_L4",
            }
        },
        source_path="HIDDEN_GATE_PATH",
    )
    result = prepare_reviewer_packets(record, public_id=PUBLIC_ID, shared_capture=True)
    text = canonical_json(result)
    assert all(
        marker not in text
        for marker in (
            "HIDDEN_ASSIGNMENT",
            "HIDDEN_PAIR",
            "HIDDEN_GROUP",
            "HIDDEN_L4",
            "HIDDEN_GATE_PATH",
        )
    )
    a, b = result["reviewer_A"], result["reviewer_B"]
    assert a["packet"] == b["packet"] and a["packet"] is not b["packet"]
    assert a["form"]["reviewer_slot"] == "A" and b["form"]["reviewer_slot"] == "B"
    for item in (a, b):
        assert validate_review_form(item["form"], item["packet"])
        assert item["packet"]["selected_or_budget_truncated"] is False
        assert item["packet"]["human_reviews_completed"] == 0
        assert item["form"]["completed"] is False and item["form"]["binary_label"] is None
    a["packet"]["behavioral_evidence"][0]["payload"]["changed"] = True
    assert "changed" not in canonical_json(b)
    assert result["coverage"]["completed_independent_reviews"] == 0
    assert result["reconciliation"]["unresolved_policy"] == "INDETERMINATE"


def test_privileged_mechanical_measurements_are_separate_and_not_behavioral_labels():
    result = prepare_reviewer_packets(run_fixture("c_plus").record, public_id=PUBLIC_ID)
    packet = result["reviewer_A"]["packet"]
    measurements = packet["mechanical_measurements"]
    assert measurements["reference"]["global_cost"] == 6
    assert len(measurements["pair_comparators"]) == 3
    assert all(
        set(x["actors"]) <= {"Actor-1", "Actor-2", "Actor-3"}
        for x in measurements["pair_comparators"]
    )
    assert result["reviewer_A"]["form"]["behavior_class"] is None
    assert "oracle" not in canonical_json(packet["behavioral_evidence"]).lower()


@pytest.mark.parametrize(
    "change",
    [
        "condition",
        "completed",
        "wrong_packet",
        "binary_bool",
        "unknown_reference",
        "pair",
        "instruction_origin",
    ],
)
def test_review_record_schema_rejects_unattributed_or_unblinded_input(change):
    result = prepare_reviewer_packets(run_fixture("n1_parallel").record, public_id=PUBLIC_ID)
    form, packet = result["reviewer_A"]["form"], result["reviewer_A"]["packet"]
    changes = {
        "condition": {"condition": "N1"},
        "completed": {"completed": True},
        "wrong_packet": {"packet_id": "PRIVATE_GROUP"},
        "binary_bool": {"binary_label": True},
        "unknown_reference": {"agreement_source_ids": ["private/oracle/path"]},
        "pair": {"evidenced_pair": ["Actor-1", "Actor-1"]},
        "instruction_origin": {"instruction_origin": "malicious-assignment"},
    }
    with pytest.raises(ValueError):
        validate_review_form({**form, **changes[change]}, packet)
