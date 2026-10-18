import pytest

from pactlens.research.readiness import ENGINEERING_GATES, METHODOLOGICAL_GATES, readiness_report


def test_engineering_pass_does_not_approve_formal_pilot_or_research_choices():
    checks = dict.fromkeys(ENGINEERING_GATES, True)
    report = readiness_report(checks)
    assert report["engineering"] == "GO"
    assert report["formal_pilot"] == "NO-GO" and report["model"] == "BLOCKED"
    assert all(x == "NOT_APPROVED" for x in report["methodological_gates"].values())
    assert report["frozen_rules"]["planned_episodes"] == 120
    assert report["frozen_rules"]["independent_groups"] == 24
    assert report["frozen_rules"]["formal_executions"] == 0
    assert report["frozen_rules"]["threshold_grid_percent"] == list(range(0, 101, 5))


@pytest.mark.parametrize("gate", ENGINEERING_GATES)
def test_failed_engineering_gate_remains_no_go(gate):
    checks = dict.fromkeys(ENGINEERING_GATES, True)
    checks[gate] = False
    report = readiness_report(checks)
    assert report["engineering"] == "PARTIAL" and report["formal_pilot"] == "NO-GO"


@pytest.mark.parametrize("gate", METHODOLOGICAL_GATES)
def test_one_unapproved_critical_decision_is_not_silently_satisfied(gate):
    approvals = [
        {
            "decision": name,
            "status": "APPROVED",
            "researcher": "SYNTHETIC_UNIT_TEST_ID",
            "dated_record_reference": "SYNTHETIC_TEST_ONLY",
        }
        for name in METHODOLOGICAL_GATES
        if name != gate
    ]
    report = readiness_report(
        dict.fromkeys(ENGINEERING_GATES, True),
        model_summary={"readiness": "PARTIAL_ENGINEERING_ONLY"},
        decision_records=approvals,
        reviewers_arranged=True,
    )
    assert report["formal_pilot"] == "NO-GO"
    assert report["methodological_gates"][gate] == "NOT_APPROVED"


def test_blank_approval_cannot_be_fabricated_and_reports_are_deterministic():
    checks = dict.fromkeys(ENGINEERING_GATES, True)
    with pytest.raises(ValueError, match="ATTRIBUTED_APPROVAL"):
        readiness_report(
            checks,
            decision_records=[
                {
                    "decision": "primary_observer",
                    "status": "APPROVED",
                    "researcher": None,
                    "dated_record_reference": None,
                }
            ],
        )
    assert readiness_report(checks) == readiness_report(dict(reversed(list(checks.items()))))
