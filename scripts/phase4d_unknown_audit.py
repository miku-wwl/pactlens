"""Real local AIG fault injection; fake proposals, zero model calls, no retry."""

import argparse
import asyncio
from pathlib import Path

from pactlens.agents.context_v31 import V31_PROMPT
from pactlens.aig.submission import TestConsent
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.sufficiency import select_common
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import OfflineTranscript
from pactlens.experiments.replay import replay_trace
from pactlens.research.baselines import evidence_chain
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition


async def audit(output, private):
    private.mkdir(parents=True, exist_ok=False)
    rows = []
    for phase in ("before_dispatch", "after_commit"):

        async def fault(at, phase=phase):
            if at == phase:
                raise RuntimeError("synthetic lost acknowledgement")

        task = fixture_task()
        run = await run_episode(
            private / phase,
            task,
            EpisodeConfig("ENG-phase4d-unknown", Condition.N3),
            OfflineTranscript(task),
            consent=TestConsent(True),
            prompt_version=V31_PROMPT,
            checkpoint=fault,
        )
        assert run.status == "STOPPED_UNKNOWN" and run.executor_calls == 1
        assert len(run.observations) == 1 and run.observations[0].action_state == "Unknown"
        inv = build_inventory(
            run.record,
            run.observations,
            run.deliveries,
            public_id=run.public_id,
            policy=ObservationPolicy.DELIVERED,
            status=run.status,
            shared_capture=True,
        )
        packet = select_common(inv).packet(View.R)
        result = evidence_chain(packet)
        assert result["features"]["proposal_commit"] == "NOT_VERIFIED"
        assert not result["features"]["executed_collusion_proven"]
        count = sum(len(s.committed()) for s in run.stores)
        assert count == (1 if phase == "after_commit" else 0)
        replay = replay_trace(run.trace_path)
        assert replay.new_effects == replay.model_calls == 0
        assert count == sum(len(s.committed()) for s in run.stores)
        rows.append(
            {
                "engineering_fault_phase": phase,
                "action_state": "Unknown",
                "committed_effects": count,
                "arena_applied_proposals": len(run.record.state.proposals),
                "baseline": result,
                "packet_text": packet.text,
                "packet_manifest": packet.manifest_json,
                "replay_new_effects": 0,
                "actual_model_calls": 0,
            }
        )
    exclusive_json(output, rows)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("private", type=Path)
    args = p.parse_args()
    asyncio.run(audit(args.output, args.private))
