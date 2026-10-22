"""Prospective offline matrix; synthetic planning, genuine local AIG, zero inference."""

import asyncio
from pathlib import Path

from pactlens.agents.context_v31 import identity
from pactlens.agents.context_v33 import V33_PROMPT, decode, encode
from pactlens.agents.deepseek_provider import request_budget
from pactlens.agents.models import Turn
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.aig.submission import TestConsent
from pactlens.arena.allocation import lawful_reference
from pactlens.arena.generator import generate_task
from pactlens.arena.models import ArenaConfig
from pactlens.evidence.compact_views import verify_compact_parity
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.tight_views import render
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import summary
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.fixtures import fixture_task
from pactlens.research.native_detector import envelope
from pactlens.research.seeds import Condition
from pactlens.research.sufficiency_v3 import eligibility
from pactlens.serialization import canonical_json, primitive

SAFE = Path("review/phase5a1")
ROOT = Path(".runtime/phase5a1-offline-v2")


class Witness:
    config = ModelConfig("fake-model", "phase5a1-offline-v1", seed_support="FAKE_DETERMINISTIC")

    def __init__(self, task, mode="submit", size=0):
        self.task, self.mode, self.size, self.requests = task, mode, size, []

    async def generate(self, r):
        self.requests.append(r)
        decoded = decode(r.turns[-1].content)
        assert encode(decoded) == r.turns[-1].content
        body = {
            **identity(r),
            "decision": self.mode,
            "assignments": None,
            "message": None,
            "end_step": True,
        }
        if self.mode == "submit":
            body["assignments"] = [
                {"incident_id": a.incident_id, "agent_id": a.agent_id}
                for a in lawful_reference(self.task).assignments
            ]
        if self.size:
            access = decoded["now"]["channel_access"]
            peers = [a.agent_id for a in self.task.agents if a.agent_id != r.actor_id]
            private = (
                [access["private_peer"]]
                if type(access) is dict and access.get("private_peer")
                else []
            )
            body["message"] = {
                "channel": "private" if private else "public",
                "recipients": private[:1] if private else peers,
                "text": ("Propose lawful allocation; confirm feasibility. " * 6)[: self.size],
            }
        return ModelResponse(canonical_json(body), 1, None, None, "stop")


async def make_case(path, task, condition, *, mode="submit", size=0, group="ENG-5a1-matched"):
    provider = Witness(task, mode, size)
    run = await run_episode(
        path,
        task,
        EpisodeConfig(group, condition),
        provider,
        consent=TestConsent(True),
        prompt_version=V33_PROMPT,
    )
    return run, provider


def export_packets(inv, name):
    selected = select_common(inv, envelope=envelope(), renderer=render)
    selected.verify()
    result = []
    for p in selected.packets:
        stem = SAFE / "packets" / (name + "-" + p.view.value)
        stem.parent.mkdir(exist_ok=True)
        stem.with_suffix(".txt").write_text(p.text, encoding="utf-8")
        exclusive_json(
            stem.with_suffix(".json"),
            {"view": p.view.value, "text": p.text, "manifest_json": p.manifest_json},
        )
        result.append(
            {
                "view": p.view.value,
                "budget": primitive(p.envelope.budget(p.text)),
                "eligibility": eligibility(p),
                "facts": len(p.verify()[1]),
                "source_facts": len(inv.facts),
            }
        )
    verify_compact_parity(selected.packet(View.R), selected.packet(View.MAE))
    assert (
        eligibility(selected.packet(View.R))["eligible"]
        == eligibility(selected.packet(View.MAE))["eligible"]
    )
    return result


async def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    rows = []
    for label, task, size, mode in [
        ("base", fixture_task(), 0, "submit"),
        ("communication", fixture_task(), 48, "submit"),
        ("long", generate_task(503, ArenaConfig(incident_count=5)), 256, "submit"),
        ("decline", fixture_task(), 0, "decline"),
    ]:
        for condition in Condition:
            run, model = await make_case(
                ROOT / (label + "-" + condition.name), task, condition, mode=mode, size=size
            )
            trace = read_trace(run.trace_path)
            rows.append(
                {
                    "case": label,
                    "condition": condition.value,
                    **summary(run),
                    "native_budgets": [
                        {
                            "round": r.round_number,
                            "actor": r.actor_id,
                            **primitive(request_budget(r.turns, "agent", require=False)),
                        }
                        for r in model.requests
                    ],
                    "opportunities": sum(r["kind"] == "VALIDATION" for r in trace),
                    "fake_generation_count": len(model.requests),
                    "note": "hypothetical native-overflow witnesses still use fake provider only; paid provider rejects before dispatch",
                }
            )
            print(
                label,
                condition.name,
                [b["estimated_tokens"] for b in rows[-1]["native_budgets"]],
                flush=True,
            )
    exclusive_json(SAFE / "offline-agent-matrix.json", {"rows": rows, "paid_calls": 0})
    detector = []
    for name, mode, size in [("known-absence", "decline", 0), ("executed-lawful", "submit", 32)]:
        run, model = await make_case(
            ROOT / name, fixture_task(), Condition.N3, mode=mode, size=size
        )
        inv = build_inventory(
            run.record,
            run.observations,
            run.deliveries,
            public_id=run.public_id,
            policy=ObservationPolicy.DELIVERED,
            status=run.status,
            shared_capture=True,
        )
        detector.append({"name": name, "source": summary(run), "views": export_packets(inv, name)})
    exclusive_json(
        SAFE / "offline-detector-cases.json",
        {"cases": detector, "generation_calls": 0, "parity": True},
    )


async def private_supplement():
    rows = []
    for condition in (Condition.C_PLUS, Condition.N2):
        for size in (48, 256):
            run, model = await make_case(
                Path(".runtime/phase5a1-private-witness") / (condition.name + str(size)),
                fixture_task(),
                condition,
                size=size,
            )
            rows.append(
                {
                    "condition": condition.value,
                    "size": size,
                    **summary(run),
                    "native_budgets": [
                        primitive(request_budget(r.turns, "agent", require=False))
                        for r in model.requests
                    ],
                    "delivered_private_messages": sum(
                        d.channel.value == "private" and d.status == "DELIVERED"
                        for d in run.deliveries
                    ),
                }
            )
    exclusive_json(SAFE / "offline-private-supplement.json", {"rows": rows, "paid_calls": 0})


async def typed_overflow_supplement():
    class GuardedWitness(Witness):
        async def generate(self, r):
            request_budget(r.turns, "agent", require=True)
            return await super().generate(r)

    reports = []
    task = generate_task(503, ArenaConfig(incident_count=5))
    for condition in Condition:
        model = GuardedWitness(task, size=256)
        run = await run_episode(
            Path(".runtime/phase5a1-typed-overflow") / condition.name,
            task,
            EpisodeConfig("ENG-5a1-matched", condition),
            model,
            consent=TestConsent(True),
            prompt_version=V33_PROMPT,
        )
        row = {
            **summary(run),
            "condition": condition.value,
            "opportunities": sum(r["kind"] == "VALIDATION" for r in read_trace(run.trace_path)),
            "native_estimates": [
                primitive(
                    request_budget(
                        tuple(Turn(**t) for t in r["payload"]["request"]["turns"]),
                        "agent",
                        require=False,
                    )
                )
                for r in read_trace(run.trace_path)
                if r["kind"] == "MODEL_REQUEST"
            ],
        }
        assert row["opportunities"] == 6 and "INPUT_BUDGET_EXCEEDED" in row["failure_codes"]
        reports.append(row)
    exclusive_json(
        SAFE / "offline-typed-overflows.json",
        {
            "rows": reports,
            "paid_calls": 0,
            "guard": "same-full-native-require-budget-as-real-provider",
        },
    )


if __name__ == "__main__":
    import sys

    asyncio.run(
        typed_overflow_supplement()
        if "--typed-overflows" in sys.argv
        else private_supplement()
        if "--private-supplement" in sys.argv
        else main()
    )
