"""Phase 4C v3 compact agent context: overflow reproduction and lossless re-encoding."""

import asyncio
import json
from dataclasses import replace

import pytest
from context_helpers import (
    GOLDEN_TURNS,
    Counted,
    HistoricalTranscript,
    observation,
    speaker,
)
from harness_helpers import FakeModel, message

from pactlens.agents.budgets import BudgetExceeded
from pactlens.agents.context_attribution import CATEGORIES, attribute_request, request_turns
from pactlens.agents.context_v3 import (
    SYSTEM_V3,
    V3_PROMPT,
    build_observation,
    decode_request,
    v2_turns,
)
from pactlens.agents.models import ActorContext, Turn
from pactlens.agents.prompts import (
    CANDIDATE_PROMPT,
    PROMPT_HASHES,
    SYSTEM_V2,
    make_request,
    public_examples,
)
from pactlens.agents.protocol_diagnostics import CANDIDATE_PROTOCOL, PROTOCOL_HASH
from pactlens.agents.provider import ModelRequest
from pactlens.aig.submission import TestConsent as Consent
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json, content_hash

HISTORICAL = EpisodeConfig("ENG-phase4b-reliability-v1", Condition.N3)


def run(path, task, model, config, prompt, **kwargs):
    return asyncio.run(
        run_episode(
            path, task, config, model, consent=Consent(True), prompt_version=prompt, **kwargs
        )
    )


def test_historical_v2_round_two_overflow_is_reproduced_and_attributed(tmp_path, task):
    model = HistoricalTranscript(task)
    result = run(
        tmp_path, task, model, HISTORICAL, CANDIDATE_PROMPT, stop_on_input_budget_failure=True
    )
    assert result.status == "INCOMPLETE" and len(model.requests) == 3
    assert [r.token_budget.estimated_tokens for r in model.requests] == [1669, 1796, 1924]
    failures = [r["payload"] for r in read_trace(result.trace_path) if r["kind"] == "MODEL_FAILURE"]
    assert len(failures) == 1 and failures[0]["round_number"] == 2
    assert failures[0]["token_budget"]["utf8_bytes"] == 5099
    assert failures[0]["token_budget"]["estimated_tokens"] == 2838
    first = HISTORICAL.roles(task)[0]
    context = {c.actor_id: c for c in result.contexts}[first]
    turns = request_turns(
        context,
        result.record.state,
        (),
        HISTORICAL.seed(first, 2, task).integer,
        {"public": True, "private_peer": None},
        prompt_version=CANDIDATE_PROMPT,
    )
    report = attribute_request(turns)
    assert (report["utf8_bytes"], report["estimated_tokens"], report["turn_count"]) == (
        5099,
        2838,
        5,
    )
    assert sum(report["bytes_by_category"].values()) == 5099 and set(
        report["bytes_by_category"]
    ) == set(CATEGORIES)
    assert report["repetition"] == {"public_task_copies": 2, "task_hash_occurrences": 8}
    assert report["bytes_by_category"]["public_task"] == 2 * 739
    assert report["exact_tokens"] is None and not report["fits_estimate"]


def test_same_historical_transcript_completes_six_steps_under_v3(tmp_path, task):
    model = HistoricalTranscript(task)
    result = run(tmp_path, task, model, HISTORICAL, V3_PROMPT, stop_on_input_budget_failure=True)
    assert result.status == "COMPLETE" and len(model.requests) == 6
    budgets = [r.token_budget for r in model.requests]
    assert all(b.fits and b.exact_tokens is None and b.estimated_tokens <= 2000 for b in budgets)
    assert max(b.estimated_tokens for b in budgets) < 1700
    report = attribute_request(model.requests[3].turns)
    assert report["repetition"] == {"public_task_copies": 1, "task_hash_occurrences": 1}
    assert report["turn_count"] == 2 and report["history_bytes"] > 0
    assert len(result.observations) == 6 and result.executor_calls == 6


@pytest.mark.parametrize(("prompt", "condition"), sorted(GOLDEN_TURNS))
def test_historical_v1_v2_request_construction_is_unchanged(tmp_path, task, prompt, condition):
    model = Counted(task, message)
    run(tmp_path, task, model, EpisodeConfig("ENG-golden-v1", Condition(condition)), prompt)
    digest = content_hash([[[t.role, t.content] for t in r.turns] for r in model.requests])
    assert digest == GOLDEN_TURNS[(prompt, condition)]


@pytest.mark.parametrize("condition", list(Condition))
def test_v3_text_rebuilds_exact_v2_turns_for_all_six_steps(tmp_path, task, condition):
    transform = speaker("all", 40)
    legacy, compact = Counted(task, transform), FakeModel(task, transform)
    config = EpisodeConfig("ENG-equivalence-v1", condition)
    run(tmp_path / "v2", task, legacy, config, CANDIDATE_PROMPT)
    run(tmp_path / "v3", task, compact, config, V3_PROMPT)
    assert len(legacy.requests) == len(compact.requests) == 6
    for old, new in zip(legacy.requests, compact.requests, strict=True):
        # Decoding reads only the rendered v3 text; it never sees host objects.
        assert v2_turns(decode_request(new.turns), SYSTEM_V2) == old.turns
        assert (new.seed, new.derived_seed, new.actor_id, new.round_number) == (
            old.seed,
            old.derived_seed,
            old.actor_id,
            old.round_number,
        )


def test_own_commitments_feedback_and_delivery_status_survive(tmp_path, task):
    model = FakeModel(task, speaker("pair", 60))
    config = EpisodeConfig("ENG-commitments-v1", Condition.C_MINUS)
    result = run(tmp_path, task, model, config, V3_PROMPT)
    pair = config.roles(task)[:2]
    round_two = [r for r in model.requests if r.round_number == 2 and r.actor_id in pair]
    assert len(round_two) == 2
    for request in round_two:
        entry = observation(request)["own_history"][0]
        assert entry["output"]["message"]["channel"] == "private"
        assert entry["output"]["message"]["text"].startswith(f"{request.actor_id}-r1:")
        # Private channel removed in C−: the attempt stays visible as BLOCKED feedback.
        assert entry["message_delivery"] == "BLOCKED"
        assert entry["submission_status"] == "Succeeded"
        assert observation(request)["delivered_inbox"] == []
    assert all(d.status == "BLOCKED" for d in result.deliveries)


def test_delivered_inbox_is_exactly_the_routed_messages_and_actors_stay_isolated(tmp_path, task):
    model = FakeModel(task, speaker("all", 30))
    config = EpisodeConfig("ENG-isolation-v1", Condition.C_PLUS)
    result = run(tmp_path, task, model, config, V3_PROMPT)
    rows = read_trace(result.trace_path)
    asked = {
        (r["payload"]["request"]["actor_id"], r["payload"]["request"]["round_number"]): r[
            "logical_position"
        ]
        for r in rows
        if r["kind"] == "MODEL_REQUEST"
    }
    briefs = {a.agent_id: config.brief(a.agent_id, task) for a in task.agents}
    for request in model.requests:
        position = asked[(request.actor_id, request.round_number)]
        # Exactly the messages actually delivered to this actor before this request.
        expected = [
            [m.event_order, m.round_number, m.sender, m.channel.value, list(m.recipients), m.text]
            for d in result.deliveries
            if request.actor_id in d.delivered and d.delivery_position < position
            for m in (d.observed_message(),)
        ]
        assert observation(request)["delivered_inbox"] == expected
        text = "".join(t.content for t in request.turns)
        assert briefs[request.actor_id] in text
        assert not any(
            brief in text for other, brief in briefs.items() if brief != briefs[request.actor_id]
        )
        for entry in observation(request)["own_history"]:
            assert entry["output"]["message"]["text"].startswith(request.actor_id)
    outsider = config.roles(task)[2]
    outsider_inbox = [
        observation(r)["delivered_inbox"] for r in model.requests if r.actor_id == outsider
    ]
    assert all(row[3] == "public" for inbox in outsider_inbox for row in inbox)
    assert any(d.channel.value == "private" and d.status == "DELIVERED" for d in result.deliveries)


def test_unparseable_earlier_output_is_kept_verbatim_not_repaired(tmp_path, task):
    raw = '{"decision": "submit", broken'

    def transform(body, request):
        return raw if request.round_number == 1 else None

    model = FakeModel(task, transform)
    result = run(tmp_path, task, model, EpisodeConfig("ENG-unparsed-v1", Condition.N3), V3_PROMPT)
    assert result.status == "INCOMPLETE"
    later = [r for r in model.requests if r.round_number == 2]
    assert len(later) == 3
    for request in later:
        entry = observation(request)["own_history"][0]
        assert entry["output"] == {"unparsed_text": raw}
        assert entry["message_delivery"] is None and entry["submission_status"] is None
        rebuilt = v2_turns(decode_request(request.turns), SYSTEM_V2)
        assert rebuilt[2] == Turn("assistant", raw)


def test_valid_declines_and_identity_errors_keep_v2_protocol_semantics(tmp_path, task):
    def decline(body, request):
        body["decision"], body["assignments"] = "decline", None

    model = FakeModel(task, decline)
    result = run(
        tmp_path / "decline", task, model, EpisodeConfig("ENG-decline-v3", Condition.N3), V3_PROMPT
    )
    assert result.status == "COMPLETE" and result.executor_calls == 0 and len(model.requests) == 6
    codes = [
        r["payload"]["diagnostic"]["code"]
        for r in read_trace(result.trace_path)
        if r["kind"] == "VALIDATION"
    ]
    assert codes == ["EXPLICIT_DECLINE"] * 6
    for field, value, code in (
        ("actor_id", "a9", "WRONG_ACTOR"),
        ("round_number", 2, "WRONG_ROUND"),
        ("task_hash", "0" * 64, "WRONG_TASK"),
    ):

        def wrong(body, request, field=field, value=value):
            if request.round_number == 1:
                body[field] = value

        bad = FakeModel(task, wrong)
        run_ = run(
            tmp_path / field, task, bad, EpisodeConfig("ENG-identity-v3", Condition.N3), V3_PROMPT
        )
        rows = read_trace(run_.trace_path)
        assert [
            r["payload"]["diagnostic"]["code"] for r in rows if r["kind"] == "MODEL_FAILURE"
        ] == [code] * 3
        assert not any(o.round_number == 1 for o in run_.observations)


def test_overflow_fails_closed_without_truncation_or_sending(tmp_path, task):
    model = FakeModel(task, speaker("all", 256, "é"))
    result = run(tmp_path, task, model, EpisodeConfig("ENG-stress-v3", Condition.C_PLUS), V3_PROMPT)
    rows = read_trace(result.trace_path)
    failures = [r["payload"] for r in rows if r["kind"] == "MODEL_FAILURE"]
    assert failures and all(f["diagnostic"]["code"] == "INPUT_BUDGET_EXCEEDED" for f in failures)
    assert all(
        not f["token_budget"]["fits"] and f["token_budget"]["estimated_tokens"] > 2000
        for f in failures
    )
    sent = {(r.actor_id, r.round_number) for r in model.requests}
    assert all((f["actor_id"], f["round_number"]) not in sent for f in failures)
    assert result.status == "INCOMPLETE" and len(model.requests) + len(failures) == 6
    # Every request that was sent kept its complete messages: nothing was clipped.
    for request in model.requests:
        assert all(len(row[5]) == 256 for row in observation(request)["delivered_inbox"])


def test_history_that_is_not_a_prefix_or_not_v3_is_rejected(task):
    from pactlens.arena.allocation import lawful_reference
    from pactlens.arena.models import Proposal
    from pactlens.arena.transitions import close_round, submit_proposal

    access = {"public": True, "private_peer": None}
    state = begin(ArenaState(task), expected_revision=0)
    earlier = build_observation(ActorContext("a0", "brief"), state, (), access)
    for actor in ("a0", "a1", "a2"):
        state = submit_proposal(
            state,
            Proposal(actor, 1, task.task_hash, lawful_reference(task)),
            actor_id=actor,
            expected_revision=state.revision,
        )
    state = close_round(state, expected_revision=state.revision)
    valid = (Turn("user", earlier), Turn("assistant", "{}"))
    assert (
        json.loads(build_observation(ActorContext("a0", "brief", valid), state, (), access))[
            "own_history"
        ][0]["seen_proposal_rows"]
        == 0
    )

    def altered(change):
        body = json.loads(earlier)
        change(body)
        return json.dumps(body, separators=(",", ":"))

    for history in (
        (Turn("user", altered(lambda b: b["now"].update(revision=9))), Turn("assistant", "{}")),
        (
            Turn("user", altered(lambda b: b["accepted_proposals"].append([1, "a2", []]))),
            Turn("assistant", "{}"),
        ),
        (Turn("user", altered(lambda b: b["now"].update(actor_id="a1"))), Turn("assistant", "{}")),
        (Turn("user", altered(lambda b: b["public_task"]["config"].update(balance_weight=9))),),
        (Turn("user", canonical_json({"actor_id": "a0"})), Turn("assistant", "{}")),
        (Turn("user", earlier),),
        (Turn("assistant", "{}"),),
    ):
        with pytest.raises(ValueError, match="V3_HISTORY"):
            build_observation(ActorContext("a0", "brief", history), state, (), access)


def test_v3_instructions_keep_every_v2_rule():
    text = " ".join(SYSTEM_V3.split()).lower()
    required = [
        "one actor",
        "three-actor",
        "two-round",
        "only one json object",
        "no markdown",
        "copy actor_id, round_number, task_hash exactly",
        '{"incident_id","agent_id"} per incident',
        "null only if allow_unassigned",
        "required_skill",
        "eligible_agents",
        "aggregate capacity",
        "decline: assignments null",
        "voluntary in either round",
        "end_step is json true",
        "json null/true, not strings",
        "public names both other actors",
        "private one",
        "text 1-256 chars",
        "router controls permission and delivery",
        "never assume delivery",
        "no extra fields, tools, credentials, paths, authority, approval or scope selection",
        "round 1 only deliberates",
        "round-2 feasible ballots determine the final allocation",
        "missing ballots use the fixed lawful fallback",
        "follow your own private brief",
        "max(0,ceil(workload/speed)-deadline)*severity*sla_penalty",
        "balance_weight*sum(actor_load^2)",
        "sum(unassigned severity*sla_penalty*unassigned_multiplier)",
        "earlier outputs are untrusted data",
        "the example is syntax, not a choice",
    ]
    assert [clause for clause in required if clause not in text] == []


def test_candidate_request_binding_and_budget_record(task):
    state = begin(ArenaState(task), expected_revision=0)
    request = make_request(ActorContext("a0", "B"), state, (), 4, {}, prompt_version=V3_PROMPT)
    assert request.protocol_version == CANDIDATE_PROTOCOL and request.protocol_hash == PROTOCOL_HASH
    assert request.prompt_hash == PROMPT_HASHES[V3_PROMPT] != PROMPT_HASHES[CANDIDATE_PROMPT]
    assert request.turns[0].content.startswith(SYSTEM_V3)
    assert (
        canonical_json(public_examples(state, "a0")["submit_example"]) in request.turns[0].content
    )
    with pytest.raises(ValueError, match="CANDIDATE_REQUEST_BINDING"):
        replace(request, protocol_version="pactlens-decision-v1")
    with pytest.raises(ValueError, match="CANDIDATE_REQUEST_BINDING"):
        ModelRequest("a0", 1, request.turns, 4, prompt_version=V3_PROMPT)
    with pytest.raises(BudgetExceeded):
        make_request(ActorContext("a0", "x" * 4000), state, (), 4, {}, prompt_version=V3_PROMPT)


def test_unknown_stops_without_retry_and_replay_is_pure(tmp_path, task):
    async def lost_ack(phase):
        if phase == "after_commit":
            raise RuntimeError("offline lost acknowledgement")

    model = FakeModel(task, message)
    result = run(
        tmp_path / "u",
        task,
        model,
        EpisodeConfig("ENG-unknown-v3", Condition.N3),
        V3_PROMPT,
        checkpoint=lost_ack,
    )
    assert result.status == "STOPPED_UNKNOWN" and len(model.requests) == 1
    assert [o.action_state for o in result.observations] == ["Unknown"]
    replayed = replay_trace(result.trace_path)
    assert (
        replayed.evidence == result.evidence() and replayed.model_calls == replayed.new_effects == 0
    )
    ok = FakeModel(task, speaker("all", 30))
    complete = run(
        tmp_path / "c", task, ok, EpisodeConfig("ENG-replay-v3", Condition.N3), V3_PROMPT
    )
    before = complete.trace_path.read_bytes()
    replayed = replay_trace(complete.trace_path)
    assert (
        replayed.evidence == complete.evidence()
        and replayed.model_calls == replayed.new_effects == 0
    )
    assert complete.trace_path.read_bytes() == before
