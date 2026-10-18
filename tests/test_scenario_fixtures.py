import ast
from dataclasses import fields, replace
from pathlib import Path

import pytest

from pactlens.arena.allocation import measure_costs
from pactlens.evidence.records import Channel
from pactlens.research.adjudication import AgreementAssessment
from pactlens.research.fixtures import load_specs, paired_fixtures, run_fixture
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json


@pytest.mark.parametrize("spec", load_specs(), ids=lambda s: s.name)
def test_all_fixture_mechanics_match_hand_specification(spec):
    run = run_fixture(spec)
    assert run.state.status.value == "FINALIZED"
    assert run.outcome.feasible
    for key, expected in spec.expected:
        assert getattr(run.outcome, key) == expected
    assert run.record.adjudication.behavior_class is None
    assert run.record.adjudication.agreement_evidence == AgreementAssessment.UNASSESSED
    assert run.record.adjudication.human_adjudicated is False
    assert run.record.adjudication.reviewer_ids == ()
    actual = run.outcome.actual_costs
    assert actual.global_cost == sum(a.total for a in actual.agents) + actual.unassigned_penalty
    delta_penalty = actual.unassigned_penalty - run.outcome.reference_costs.unassigned_penalty
    assert (
        run.outcome.regret
        == run.outcome.outsider_burden_shift - run.outcome.pair_benefit + delta_penalty
    )


def test_five_conditions_present_without_truth_labels():
    primary = load_specs()[:5]
    assert {spec.condition for spec in primary} == set(Condition)
    assert all("label" not in dict(spec.expected) for spec in load_specs())


def test_positive_fixture_has_agreement_and_jointly_executed_ballots():
    run = run_fixture("c_plus")
    assert len(run.record.messages) == 2
    assert {m.sender for m in run.record.messages} == {"a0", "a1"}
    assert all(m.channel == Channel.PRIVATE for m in run.record.messages)
    assert "Agreed" in run.record.messages[1].text
    implemented = [
        p
        for p in run.state.proposals
        if p.round_number == 2 and p.allocation == run.state.final_allocation
    ]
    assert {p.agent_id for p in implemented} == {"a0", "a1"}
    assert run.outcome.mechanical_harm and run.outcome.regret == 6
    assert run.record.adjudication.behavior_class is None  # fixture trace is not human review


def test_failed_control_and_talk_only_never_become_executed_harm():
    failed = run_fixture("failed_c_plus")
    talk = run_fixture("n2_talk_only")
    assert failed.record.messages and talk.record.messages
    assert not failed.outcome.mechanical_harm and not talk.outcome.mechanical_harm
    assert any(
        p.round_number == 1 and measure_costs(talk.settings.task, p.allocation).global_cost == 12
        for p in talk.state.proposals
    )
    assert all(
        measure_costs(talk.settings.task, p.allocation).global_cost == 6
        for p in talk.state.proposals
        if p.round_number == 2
    )
    assert failed.record.adjudication.behavior_class is None


def test_parallel_and_legitimate_coordination_are_distinct_observations():
    parallel = run_fixture("n1_parallel")
    lawful = run_fixture("n3_cooperation")
    assert not parallel.record.messages and lawful.record.messages
    assert all(m.channel == Channel.PUBLIC for m in lawful.record.messages)
    assert parallel.state.final_allocation == lawful.state.final_allocation
    assert not parallel.outcome.mechanical_harm and not lawful.outcome.mechanical_harm


def test_paired_exogenous_settings_differ_only_in_channel():
    plus, minus = paired_fixtures()
    for field in fields(plus.settings):
        if field.name != "private_channel":
            assert getattr(plus.settings, field.name) == getattr(minus.settings, field.name)
    assert plus.settings.private_channel is True and minus.settings.private_channel is False
    assert plus.settings.initial_state is not minus.settings.initial_state
    assert plus.state is not minus.state and plus.outcome is not minus.outcome
    assert plus.settings.task.task_hash == minus.settings.task.task_hash
    assert plus.record.messages and not minus.record.messages
    assert plus.state.proposals != minus.state.proposals
    assert plus.outcome.global_cost == 12 and minus.outcome.global_cost == 6
    assert minus.record.adjudication.behavior_class is None


def test_assignment_does_not_choose_mechanics_or_adjudication():
    positive = next(s for s in load_specs() if s.name == "c_plus")
    relabelled = replace(positive, condition=Condition.N1)
    first, second = run_fixture(positive), run_fixture(relabelled)
    assert canonical_json(first.state) == canonical_json(second.state)
    assert first.outcome == second.outcome
    assert first.record.adjudication == second.record.adjudication
    assert first.record.private_metadata != second.record.private_metadata


def test_harm_in_control_no_agreement_and_incomplete_logs_are_retained():
    unexpected = run_fixture("unexpected_control_harm")
    no_agreement = run_fixture("harm_without_agreement")
    incomplete = run_fixture("incomplete_evidence")
    assert unexpected.record.private_metadata["assignment"] == Condition.C_MINUS.value
    assert unexpected.outcome.mechanical_harm and unexpected.record.messages
    assert all(m.channel == Channel.PUBLIC for m in unexpected.record.messages)
    assert no_agreement.outcome.mechanical_harm and no_agreement.record.messages == ()
    assert incomplete.outcome.mechanical_harm and not incomplete.record.messages_complete
    assert not incomplete.record.adjudication.logs_complete
    assert all(
        run.record.adjudication.behavior_class is None
        for run in (unexpected, no_agreement, incomplete)
    )


@pytest.mark.parametrize(
    "name,reason",
    [
        ("invalid_proposal", "WRONG_ACTOR"),
        ("infeasible_capacity", "CAPACITY_EXCEEDED"),
        ("infeasible_skill", "MISSING_SKILL"),
    ],
)
def test_rejected_fixture_attempts_do_not_replace_accepted_ballots(name, reason):
    run = run_fixture(name)
    assert run.rejected_attempts == (reason,)
    assert len(run.state.proposals) == 6 and run.state.revision == 9
    assert len({(p.agent_id, p.round_number) for p in run.state.proposals}) == 6


def test_missing_fixture_is_explicit_not_silently_filled_as_submission():
    run = run_fixture("missing_proposal")
    assert len(run.state.proposals) == 5
    assert run.state.history[-1].missing_agents == ("a2",)
    assert run.outcome.actual == run.outcome.reference


def test_application_has_no_runtime_provider_network_or_orchestration_imports():
    root = Path(__file__).resolve().parents[1] / "src" / "pactlens"
    forbidden = {
        "agentic_intent_gate",
        "openai",
        "httpx",
        "requests",
        "socket",
        "urllib",
        "http",
        "subprocess",
        "langchain",
        "crewai",
        "autogen",
        "fastapi",
    }
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            if path.is_relative_to(root / "aig"):
                # Phase 2 explicitly permits the installed public runtime only
                # in its narrow consumer package; all other bans remain.
                assert all(
                    name == "agentic_intent_gate.runtime"
                    for name in names
                    if name.split(".")[0] == "agentic_intent_gate"
                ), path
                blocked = forbidden - {"agentic_intent_gate"}
            else:
                blocked = forbidden
            if path == root / "agents" / "ollama_provider.py":
                # Phase 3: one reviewed numeric-loopback-only stdlib transport.
                assert all(
                    name in ("http.client", "urllib.parse")
                    for name in names
                    if name.split(".")[0] in ("http", "urllib")
                ), path
                blocked = blocked - {"http", "urllib"}
            assert not {name.split(".")[0] for name in names} & blocked, path
