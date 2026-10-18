"""At most two fresh N3 local engineering episodes. Never a study or detector."""

import argparse
import asyncio
import os
from pathlib import Path

from pactlens.agents.budgets import BudgetExceeded, token_preflight
from pactlens.agents.models import ActorContext, MessageIntent, closed_json
from pactlens.agents.ollama_provider import OllamaProvider
from pactlens.agents.prompts import CANDIDATE_PROMPT, LEGACY_PROMPT, make_request
from pactlens.agents.protocol_diagnostics import FIELDS
from pactlens.aig.submission import TestConsent
from pactlens.arena.allocation import measure_costs
from pactlens.arena.models import ArenaState, Proposal
from pactlens.arena.transitions import begin
from pactlens.evidence.records import Channel
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-local-reliability-v1"
GROUP = "ENG-phase4b-reliability-v1"


class GenerationLedger:
    """Charge before dispatch, never resume/reset a comparison or replace failures."""

    def __init__(self, path):
        self.handle = Path(path).open("x", encoding="utf-8", newline="\n")  # noqa: SIM115 -- closed in comparison finally
        self.total = 0
        self.by_prompt = {}

    def charge(self, request):
        prompt = request.prompt_version
        if (
            prompt not in (LEGACY_PROMPT, CANDIDATE_PROMPT)
            or self.total >= 12
            or self.by_prompt.get(prompt, 0) >= 6
        ):
            raise ValueError("LOCAL_GENERATION_CAP_NO_RETRY")
        self.total += 1
        self.by_prompt[prompt] = self.by_prompt.get(prompt, 0) + 1
        self.handle.write(
            canonical_json(
                {
                    "attempt": self.total,
                    "prompt_version": prompt,
                    "request_hash": content_hash(request),
                }
            )
            + "\n"
        )
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        self.handle.close()


class BoundedProvider:
    def __init__(self, provider, ledger):
        self.provider, self.ledger, self.config = provider, ledger, provider.config

    async def generate(self, request):
        self.ledger.charge(request)
        return await self.provider.generate(request)


def initial_preflight(task, config, prompt_version):
    state = begin(ArenaState(task), expected_revision=0)
    result = []
    for actor in config.roles(task):
        try:
            request = make_request(
                ActorContext(actor, config.brief(actor, task)),
                state,
                (),
                config.seed(actor, 1, task).integer,
                {"public": True, "private_peer": None},
                prompt_version=prompt_version,
            )
            budget = token_preflight(request.turns, limit=2000)
        except BudgetExceeded as error:
            budget = error.report
        result.append({"actor": actor, "budget": budget})
    return result


def response_observations(run):
    """Sanitized raw engineering measurements, not scores or inferred human truth."""
    rows = read_trace(run.trace_path)
    requests, responses, validations, failures = {}, {}, {}, {}
    for row in rows:
        p = row["payload"]
        if row["kind"] == "MODEL_REQUEST":
            r = p["request"]
            requests[(r["actor_id"], r["round_number"])] = p
        elif row["kind"] in ("MODEL_RESPONSE", "VALIDATION", "MODEL_FAILURE"):
            target = {
                "MODEL_RESPONSE": responses,
                "VALIDATION": validations,
                "MODEL_FAILURE": failures,
            }[row["kind"]]
            target[(p["actor_id"], p["round_number"])] = p
    measurements = []
    for actor in sorted(a.agent_id for a in run.record.state.task.agents):
        for round_number in (1, 2):
            key = (actor, round_number)
            request, response = requests.get(key), responses.get(key)
            validation, failure = validations.get(key), failures.get(key)
            body = None
            json_valid = schema_valid = message_valid = feasible = None
            if response is not None:
                try:
                    body = closed_json(response["response"]["text"])
                    json_valid = True
                except (ValueError, UnicodeError):
                    json_valid = False
                schema_valid = type(body) is dict and set(body) == FIELDS
                if schema_valid:
                    schema_valid = (
                        type(body["actor_id"]) is str
                        and body["actor_id"] == actor
                        and type(body["round_number"]) is int
                        and body["round_number"] == round_number
                        and body["task_hash"] == run.record.state.task.task_hash
                        and body["end_step"] is True
                        and body["decision"] in ("submit", "decline")
                    )
                    if body["decision"] == "submit":
                        assignments = body["assignments"]
                        schema_valid = schema_valid and (
                            type(assignments) is list
                            and 3 <= len(assignments) <= 5
                            and all(
                                type(row) is dict
                                and set(row) == {"incident_id", "agent_id"}
                                and type(row["incident_id"]) is str
                                and (row["agent_id"] is None or type(row["agent_id"]) is str)
                                for row in assignments
                            )
                        )
                        try:
                            proposal = Proposal.from_mapping(
                                {
                                    "agent_id": actor,
                                    "round_number": round_number,
                                    "task_hash": body["task_hash"],
                                    "assignments": body["assignments"],
                                }
                            )
                            measure_costs(run.record.state.task, proposal.allocation)
                            feasible = True
                        except (ValueError, TypeError):
                            feasible = False
                    elif body["assignments"] is not None:
                        schema_valid = False
                    message = body["message"]
                    if message is not None:
                        try:
                            if (
                                type(message) is not dict
                                or set(message) != {"channel", "recipients", "text"}
                                or type(message["recipients"]) is not list
                            ):
                                raise ValueError("MESSAGE_FIELDS")
                            MessageIntent(
                                Channel(message["channel"]),
                                tuple(message["recipients"]),
                                message["text"],
                            )
                            peers = {a.agent_id for a in run.record.state.task.agents} - {actor}
                            audience = set(message["recipients"])
                            message_valid = (
                                audience == peers
                                if message["channel"] == "public"
                                else len(audience) == 1 and audience <= peers
                            )
                        except (ValueError, TypeError):
                            message_valid = False
                            schema_valid = False
            valid = validation is not None and validation["status"] == "VALID"
            observation = next(
                (o for o in run.observations if (o.actor_id, o.round_number) == key), None
            )
            measurements.append(
                {
                    "actor": actor,
                    "round": round_number,
                    "protocol_version": rows[0]["payload"].get(
                        "protocol_version", "pactlens-decision-v1"
                    ),
                    "request_hash": None if request is None else request["request_digest"],
                    "response_hash": None if response is None else response["response_digest"],
                    "input_tokens": None
                    if response is None
                    else response["response"]["input_tokens"],
                    "output_tokens": None
                    if response is None
                    else response["response"]["output_tokens"],
                    "latency_us": None if response is None else response["response"]["latency_us"],
                    "json_valid": json_valid,
                    "schema_valid": schema_valid,
                    "assignment_feasible": feasible,
                    "message_valid": message_valid,
                    "valid_submit": valid and body["decision"] == "submit",
                    "valid_decline": valid and body["decision"] == "decline",
                    "validation": None if validation is None else validation["status"],
                    "failure": None if failure is None else failure["diagnostic"]["code"],
                    "aig_status": None if observation is None else observation.action_state,
                    "receipt_status": None if observation is None else observation.receipt_status,
                    "receipt_reference": None
                    if observation is None
                    else observation.receipt_reference,
                    "step": "NOT_REACHED"
                    if request is None and failure is None
                    else "PREFLIGHT_FAILED"
                    if request is None
                    else "ATTEMPTED",
                }
            )
    return measurements


async def compare_local(directory, task, provider, *, allow_two_local_engineering_episodes=False):
    if (
        allow_two_local_engineering_episodes is not True
        or type(provider) is not OllamaProvider
        or provider.calls != 0
    ):
        raise ValueError("EXPLICIT_FRESH_LOCAL_COMPARISON_REQUIRED")
    identity = provider.readiness()
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("FRESH_COMPARISON_DIRECTORY_NO_RESUME")
    config = EpisodeConfig(GROUP, Condition.N3)
    preflight = initial_preflight(task, config, CANDIDATE_PROMPT)
    preflight_ok = all(x["budget"].fits for x in preflight)
    ledger = GenerationLedger(root / "generation-ledger.jsonl")
    summary = {
        "version": VERSION,
        "identity": identity,
        "provenance": "PRE_SPRINT_ENGINEERING_NOT_FORMAL_OBSERVATIONS",
        "group": GROUP,
        "task_hash": task.task_hash,
        "model_config": provider.config,
        "candidate_initial_preflight": preflight,
        "episodes": [],
        "formal_episodes": 0,
        "detector_predictions": 0,
        "synthetic_consent": True,
        "comparison_winner": None,
    }
    try:
        for name, prompt in (("legacy-v1", LEGACY_PROMPT), ("candidate-v2", CANDIDATE_PROMPT)):
            if prompt == CANDIDATE_PROMPT and not preflight_ok:
                summary["episodes"].append(
                    {
                        "profile": name,
                        "prompt_version": prompt,
                        "status": "NOT_RUN_INPUT_BUDGET_EXCEEDED",
                        "actual_generation_calls": 0,
                    }
                )
                continue
            provider.readiness()
            before = provider.calls
            run = await run_episode(
                root / name,
                task,
                config,
                BoundedProvider(provider, ledger),
                consent=TestConsent(synthetic_consent=True),
                prompt_version=prompt,
                stop_on_input_budget_failure=True,
            )
            replay = replay_trace(run.trace_path)
            measurements = response_observations(run)
            summary["episodes"].append(
                {
                    "profile": name,
                    "prompt_version": prompt,
                    "status": run.status,
                    "public_id": run.public_id,
                    "trace_hash": content_hash(run.trace_path.read_text(encoding="utf-8")),
                    "actual_generation_calls": provider.calls - before,
                    "valid_outputs": sum(x["validation"] == "VALID" for x in measurements),
                    "invalid_responses": sum(
                        x["response_hash"] is not None and x["validation"] != "VALID"
                        for x in measurements
                    ),
                    "valid_submissions": sum(x["valid_submit"] for x in measurements),
                    "valid_declines": sum(x["valid_decline"] for x in measurements),
                    "actions": len(run.observations),
                    "receipts": sum(
                        o.receipt_status == "VERIFIED_COMMITTED" for o in run.observations
                    ),
                    "finalized": run.record.state.status.value == "FINALIZED",
                    "pure_replay_equal": replay.evidence.to_json() == run.evidence().to_json(),
                    "replay_model_calls": replay.model_calls,
                    "replay_new_effects": replay.new_effects,
                    "measurements": measurements,
                }
            )
            (root / "summary.json").write_text(canonical_json(summary), encoding="utf-8")
            if run.status == "STOPPED_UNKNOWN":
                summary["stop"] = "UNKNOWN_NO_RETRY_OR_FURTHER_EPISODES"
                break
    finally:
        ledger.close()
        summary["actual_generation_calls"] = provider.calls
        summary["charged_attempts"] = ledger.total
        summary["readiness"] = (
            "PARTIAL_ENGINEERING_ONLY"
            if len(summary["episodes"]) == 2
            and all(x["status"] == "COMPLETE" for x in summary["episodes"])
            else "REAL_MODEL_NOT_READY"
        )
        (root / "summary.json").write_text(canonical_json(summary), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--allow-two-local-engineering-episodes", action="store_true", required=True
    )
    args = parser.parse_args()
    result = asyncio.run(
        compare_local(
            args.directory,
            fixture_task(),
            OllamaProvider.from_environment(),
            allow_two_local_engineering_episodes=args.allow_two_local_engineering_episodes,
        )
    )
    print(canonical_json(result))


if __name__ == "__main__":
    main()
