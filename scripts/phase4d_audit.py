"""Reproduce safe offline audit artifacts. No live provider, formal seed or truth read."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from pactlens.agents.context_v31 import V31_PROMPT
from pactlens.agents.provider import ModelConfig, ModelResponse
from pactlens.aig.submission import TestConsent
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.sufficiency import EvidenceBudgetInfeasible, select_common, select_complete
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import OfflineTranscript
from pactlens.research.baselines import (
    CONTRIBUTIONS,
    action,
    communication,
    evidence_chain,
    shortcut_diagnostics,
)
from pactlens.research.detector_runner import exclusive_json, predict, replay_prediction
from pactlens.research.fixtures import fixture_task, load_specs, run_fixture
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.operations import DryRunConfig, approval_manifest, dry_run
from pactlens.research.seeds import Condition


class ExampleDetector:
    config = ModelConfig(
        "deterministic-fake-detector", "phase4d-example", seed_support="FAKE_DETERMINISTIC"
    )

    async def generate(self, request):
        return ModelResponse(
            canonical_json(
                {
                    "risk_score": 0.25,
                    "confidence": 0.5,
                    "evidence_ids": ["public-task"],
                    "rationale_short": "Synthetic interface demonstration; no empirical research claim.",
                    "adequacy": "INSUFFICIENT_EVIDENCE",
                }
            ),
            1,
            None,
            None,
            "stop",
        )


class CommunicatingTranscript(OfflineTranscript):
    """Explicitly fake public speech for full six-Action evidence stress checks."""

    async def generate(self, request):
        response = await super().generate(request)
        body = json.loads(response.text)
        body["message"] = {
            "channel": "public",
            "recipients": [a for a in ("a0", "a1", "a2") if a != request.actor_id],
            "text": "Synthetic public coordination.",
        }
        return ModelResponse(canonical_json(body), 1, None, None, "stop")


async def main(output, private):
    output.mkdir(parents=True, exist_ok=False)
    private.mkdir(parents=True, exist_ok=False)
    task = fixture_task()
    # Six genuine synthetic SQLite receipts via installed AIG; planning/consent fake.
    run = await run_episode(
        private / "six-action",
        task,
        EpisodeConfig("ENG-phase4d-audit", Condition.N3),
        OfflineTranscript(task),
        consent=TestConsent(True),
        prompt_version=V31_PROMPT,
    )
    sources = [
        (
            "six-action",
            run.record,
            run.observations,
            run.deliveries,
            run.public_id,
            run.status,
            True,
        )
    ]
    for spec in load_specs():
        fixture = run_fixture(spec)
        sources.append((spec.name, fixture.record, (), None, str(uuid4()), "INCOMPLETE", False))
    audits = []
    cases = []
    for name, record, observations, deliveries, pid, status, shared in sources:
        for policy in ObservationPolicy:
            inv = build_inventory(
                record,
                observations,
                deliveries,
                public_id=pid,
                policy=policy,
                status=status,
                shared_capture=shared,
            )
            try:
                complete = select_complete(inv)
                full = {"status": "FIT_ESTIMATE", "manifest": json.loads(complete.manifest_json)}
            except EvidenceBudgetInfeasible as e:
                full = json.loads(e.diagnostics_json)
            selected = select_common(inv)
            selected.verify()
            facts = {
                p.view: {canonical_json(f) for f in canonical_fact_records(p.verify()[1])}
                for p in selected.packets
            }
            assert facts[View.R] == facts[View.MAE]
            assert facts[View.M] | facts[View.A] == facts[View.MA]
            assert facts[View.MA] <= facts[View.R]
            row = {
                "safe_fixture": name,
                "policy": policy.value,
                "complete": full,
                "selected": json.loads(selected.manifest_json),
                "independently_parsed_semantic_relations": True,
                "shortcuts": shortcut_diagnostics(selected),
            }
            audits.append(row)
            if policy == ObservationPolicy.DELIVERED:
                cases.append(
                    {
                        "safe_fixture": name,
                        "communication": communication(selected.packet(View.M)),
                        "action": action(selected.packet(View.A)),
                        "chain": evidence_chain(selected.packet(View.R)),
                    }
                )
            if name == "six-action":
                for packet in selected.packets:
                    stem = "six-action-" + policy.name + "-" + packet.view.value
                    (output / (stem + ".txt")).write_text(packet.text, encoding="utf-8")
                    exclusive_json(
                        output / (stem + ".manifest.json"), json.loads(packet.manifest_json)
                    )
            if name == "n3_cooperation" and policy == ObservationPolicy.DELIVERED:
                for view in View:
                    path = await predict(
                        output / "fake-predictions",
                        selected.packet(view),
                        ExampleDetector(),
                        engineering_id="ENG-detector-example",
                    )
                    replay_prediction(path)
    exclusive_json(output / "evidence-audit.json", audits)
    exclusive_json(output / "baseline-cases.json", cases)
    exclusive_json(output / "contribution-matrix.json", CONTRIBUTIONS)
    exclusive_json(output / "approval-manifest.json", approval_manifest())
    dry = await dry_run(private / "pilot-dry", DryRunConfig())
    exclusive_json(output / "pilot-dry-run.json", dry)
    exclusive_json(output / "pilot-deterministic-manifest.json", DryRunConfig().manifest())
    exclusive_json(
        output / "audit-receipt.json",
        {
            "audit_sets": len(audits),
            "synthetic_six_receipts": len(run.observations),
            "formal_executions": 0,
            "actual_inference_calls": 0,
            "evidence_audit_hash": content_hash(audits),
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("private", type=Path)
    a = p.parse_args()
    asyncio.run(main(a.output, a.private))
