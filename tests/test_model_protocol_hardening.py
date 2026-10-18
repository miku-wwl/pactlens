import ast
import asyncio
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from harness_helpers import FakeModel

from pactlens.agents.budgets import BudgetExceeded, require_budget, token_preflight
from pactlens.agents.models import ActorContext, Turn, parse_decision
from pactlens.agents.prompts import (
    CANDIDATE_PROMPT,
    PROMPT_HASHES,
    SYSTEM,
    make_request,
    public_examples,
)
from pactlens.agents.protocol_diagnostics import (
    CANDIDATE_PROTOCOL,
    Code,
    ProtocolRejected,
    exception_diagnostic,
    parse_versioned,
)
from pactlens.aig.submission import TestConsent as Consent
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json, content_hash

CORPUS = json.loads(
    (Path(__file__).resolve().parents[1] / "datasets/fixtures/protocol_v2_cases.json").read_text(
        encoding="utf-8"
    )
)


def base(state):
    return public_examples(state, "a0")["submit_example"]


@pytest.mark.parametrize("case", CORPUS["valid"])
def test_valid_corpus_has_no_repairs_and_decline_is_not_failure(task, case):
    state = begin(ArenaState(task), expected_revision=0)
    body = base(state)
    if case == "decline":
        body["decision"], body["assignments"] = "decline", None
    elif case in ("public", "private"):
        body["message"] = {
            "channel": case,
            "recipients": ["a1", "a2"] if case == "public" else ["a1"],
            "text": "Actual observable speech",
        }
    raw = canonical_json(body)
    decision = parse_versioned(raw, state=state, actor_id="a0", protocol_version=CANDIDATE_PROTOCOL)
    assert decision == parse_decision(raw, state=state, actor_id="a0")
    assert (decision.proposal is None) == (case == "decline")


@pytest.mark.parametrize("case,expected", CORPUS["invalid"])
def test_invalid_corpus_has_deterministic_diagnostics(task, case, expected):
    if case == "capacity":
        task = replace(task, agents=tuple(replace(a, capacity=1) for a in task.agents))
    elif case == "skill":
        task = replace(
            task, agents=(replace(task.agents[0], skills=("different",)), *task.agents[1:])
        )
    state = begin(ArenaState(task), expected_revision=0)
    body = base(state)
    if case == "missing_field":
        body.pop("message")
    elif case == "authority":
        body["execution_scope"] = "UNTRUSTED_AUTHORITY"
    elif case == "round_type":
        body["round_number"] = True
    elif case == "owner_type":
        body["assignments"][0]["agent_id"] = 12
    elif case == "actor":
        body["actor_id"] = "a1"
    elif case == "round":
        body["round_number"] = 2
    elif case == "task":
        body["task_hash"] = "0" * 64
    elif case == "one_assignment_phase3":
        body["assignments"] = [{"agent_id": "a1", "incident_id": "i1"}]
    elif case == "duplicate_incident":
        body["assignments"][1] = body["assignments"][0]
    elif case == "wrong_incident":
        body["assignments"][0]["incident_id"] = "foreign"
    elif case in ("capacity", "skill"):
        body["assignments"] = [
            {"incident_id": i.incident_id, "agent_id": "a0"} for i in task.incidents
        ]
    elif case in (
        "self_recipient_phase3",
        "unknown_recipient",
        "public_subset",
        "private_multiple",
        "empty_recipients",
    ):
        recipients = {
            "self_recipient_phase3": ["a0", "a1", "a2"],
            "unknown_recipient": ["foreign"],
            "public_subset": ["a1"],
            "private_multiple": ["a1", "a2"],
            "empty_recipients": [],
        }[case]
        body["message"] = {
            "channel": "private" if case == "private_multiple" else "public",
            "recipients": recipients,
            "text": "Observable text",
        }
    elif case == "row_authority":
        body["assignments"][0]["token"] = "FORBIDDEN"
    elif case == "decline_with_assignment":
        body["decision"] = "decline"
    elif case == "string_null":
        body["assignments"] = "null"
    elif case == "string_true":
        body["end_step"] = "true"
    elif case == "unfinished":
        body["end_step"] = False
    elif case == "no_choice":
        body["decision"] = "maybe"
    raw = (
        "{"
        if case == "json"
        else '{"actor_id":"a0","actor_id":"a1"}'
        if case == "duplicate_key"
        else "x" * 4097
        if case == "too_large"
        else canonical_json(body)
    )
    before = content_hash(state)
    with pytest.raises(ProtocolRejected) as caught:
        parse_versioned(raw, state=state, actor_id="a0", protocol_version=CANDIDATE_PROTOCOL)
    assert caught.value.diagnostic.code.value == expected
    assert not caught.value.diagnostic.ok and caught.value.diagnostic.response_digest
    assert content_hash(state) == before


def test_prompt_versions_public_examples_and_original_literal_are_preserved(task):
    previous = ast.parse(
        subprocess.check_output(
            ["git", "show", "HEAD:src/pactlens/agents/prompts.py"], text=True, encoding="utf-8"
        )
    )
    old = next(
        ast.literal_eval(n.value)
        for n in previous.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in n.targets)
    )
    assert SYSTEM == old and PROMPT_HASHES["pactlens-agent-v1"] == content_hash(old)
    state = begin(ArenaState(task), expected_revision=0)
    examples = public_examples(state, "a0")
    assert all(
        parse_versioned(
            canonical_json(b), state=state, actor_id="a0", protocol_version=CANDIDATE_PROTOCOL
        )
        for b in examples.values()
    )
    request = make_request(
        ActorContext("a0", "PRIVATE_BRIEF"), state, (), 4, {}, prompt_version=CANDIDATE_PROMPT
    )
    assert (
        request.prompt_version == CANDIDATE_PROMPT
        and request.protocol_version == CANDIDATE_PROTOCOL
    )
    assert request.prompt_hash == PROMPT_HASHES[CANDIDATE_PROMPT] and request.protocol_hash
    assert request.token_budget.exact_tokens is None and request.token_budget.fits


def test_budget_preflight_distinguishes_estimates_and_exact_counter_without_truncation():
    turns = (Turn("system", "x" * 4000),)
    estimate = token_preflight(turns, limit=2000)
    assert not estimate.fits and estimate.exact_tokens is None
    with pytest.raises(BudgetExceeded):
        require_budget(turns, limit=2000)
    exact = require_budget(turns, limit=2000, token_counter=lambda t: 1999)
    assert exact.exact_tokens == 1999 and exact.method == "TRUSTED_TOKEN_COUNTER"
    assert turns[0].content == "x" * 4000
    with pytest.raises(ValueError):
        token_preflight(turns, limit=2000, token_counter=lambda t: True)


def test_candidate_fake_decisions_still_flow_through_real_aig_and_replay(tmp_path, task):
    class CountedFake(FakeModel):
        def count_input_tokens(self, turns):
            return 500  # explicit synthetic counter seam; not real-model tokenization evidence

    model = CountedFake(task)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-v2-protocol", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=CANDIDATE_PROMPT,
        )
    )
    assert run.executor_calls == 6 and len(run.observations) == 6
    assert all(o.action_state == "Succeeded" for o in run.observations)
    assert replay_trace(run.trace_path).evidence == run.evidence()
    assert all(r.protocol_version == CANDIDATE_PROTOCOL for r in model.requests)
    rows = read_trace(run.trace_path)
    assert all(
        r["payload"]["diagnostic"]["code"] == "VALID_SUBMISSION"
        for r in rows
        if r["kind"] == "VALIDATION"
    )


def test_context_overflow_prevents_generation_and_records_failure(tmp_path, task, monkeypatch):
    from pactlens.experiments import harness

    original = harness.make_request

    def overflow(context, *args, **kwargs):
        return original(
            replace(context, private_instruction="PRIVATE_TOO_LONG_" * 400), *args, **kwargs
        )

    monkeypatch.setattr(harness, "make_request", overflow)
    model = FakeModel(task)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-overflow", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=CANDIDATE_PROMPT,
        )
    )
    assert not model.requests and run.executor_calls == 0 and run.status == "INCOMPLETE"
    rows = read_trace(run.trace_path)
    failures = [r["payload"] for r in rows if r["kind"] == "MODEL_FAILURE"]
    assert len(failures) == 6 and all(
        p["diagnostic"]["code"] == "INPUT_BUDGET_EXCEEDED" for p in failures
    )
    assert "PRIVATE_TOO_LONG" not in run.evidence().to_json()


@pytest.mark.parametrize(
    "case,legacy_error,new_code",
    [
        ("one_assignment", "INVALID_ASSIGNMENT_SYNTAX", Code.ASSIGNMENTS),
        ("three_recipients", "MESSAGE_SYNTAX", Code.ROUTING),
    ],
)
def test_phase3_smoke_error_shapes_reproduce_original_errors(task, case, legacy_error, new_code):
    state = begin(ArenaState(task), expected_revision=0)
    body = base(state)
    if case == "one_assignment":
        body["assignments"] = [{"incident_id": "i1", "agent_id": "a1"}]
    else:
        body["message"] = {
            "channel": "public",
            "recipients": ["a0", "a1", "a2"],
            "text": "Recorded Phase 3 failure shape",
        }
    raw = canonical_json(body)
    with pytest.raises(ValueError, match=legacy_error):
        parse_decision(raw, state=state, actor_id="a0")
    with pytest.raises(ProtocolRejected) as caught:
        parse_versioned(raw, state=state, actor_id="a0", protocol_version=CANDIDATE_PROTOCOL)
    assert caught.value.diagnostic.code == new_code


def test_candidate_voluntary_declines_are_complete_valid_steps_with_zero_actions(tmp_path, task):
    class Declining(FakeModel):
        def count_input_tokens(self, turns):
            return 500  # synthetic counter seam only

    def decline(body, request):
        body["decision"], body["assignments"] = "decline", None

    model = Declining(task, decline)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-decline-v2", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=CANDIDATE_PROMPT,
        )
    )
    assert run.status == "COMPLETE" and run.executor_calls == 0 and len(model.requests) == 6
    rows = read_trace(run.trace_path)
    assert not any(r["kind"] == "MODEL_FAILURE" for r in rows)
    assert all(
        r["payload"]["diagnostic"]["code"] == "EXPLICIT_DECLINE"
        for r in rows
        if r["kind"] == "VALIDATION"
    )
    assert replay_trace(run.trace_path).evidence == run.evidence()


@pytest.mark.parametrize(
    "case,code", [("input", Code.INPUT), ("output", Code.OUTPUT), ("length", Code.OUTPUT)]
)
def test_actual_provider_usage_or_truncation_is_not_accepted_as_success(tmp_path, task, case, code):
    class Misbudgeted(FakeModel):
        def count_input_tokens(self, turns):
            return 500  # synthetic counter seam only

        async def generate(self, request):
            response = await super().generate(request)
            return replace(
                response,
                **(
                    {"input_tokens": 2001}
                    if case == "input"
                    else {"output_tokens": 257}
                    if case == "output"
                    else {"finish_reason": "length"}
                ),
            )

    model = Misbudgeted(task)
    run = asyncio.run(
        run_episode(
            tmp_path,
            task,
            EpisodeConfig("ENG-usage-v2", Condition.N3),
            model,
            consent=Consent(True),
            prompt_version=CANDIDATE_PROMPT,
        )
    )
    assert run.executor_calls == 0 and run.status == "INCOMPLETE"
    rows = read_trace(run.trace_path)
    assert len([r for r in rows if r["kind"] == "MODEL_RESPONSE"]) == 6
    failures = [r["payload"]["diagnostic"]["code"] for r in rows if r["kind"] == "MODEL_FAILURE"]
    assert failures == [code.value] * 6


@pytest.mark.parametrize(
    "error,stage,code",
    [
        (TimeoutError(), "MODEL", Code.TIMEOUT),
        (ValueError("OUTPUT_BUDGET_EXCEEDED"), "MODEL", Code.OUTPUT),
        (ValueError("ACTUAL_INPUT_BUDGET_EXCEEDED"), "MODEL", Code.INPUT),
        (RuntimeError("private"), "AIG", Code.AIG),
    ],
)
def test_host_failure_taxonomy_does_not_copy_error_text(error, stage, code):
    diagnostic = exception_diagnostic(error, protocol_version=CANDIDATE_PROTOCOL, stage=stage)
    assert diagnostic.code == code and "private" not in canonical_json(diagnostic)
