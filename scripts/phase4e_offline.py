"""Six-step candidate preflight through real installed AIG; no external inference."""

import asyncio
import json
from pathlib import Path

from pactlens.agents.context_v32 import V32_PROMPT
from pactlens.agents.deepseek_provider import request_budget
from pactlens.aig.submission import TestConsent
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.experiments.phase4d_engineering import OfflineTranscript, summary
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.fixtures import fixture_task
from pactlens.research.seeds import Condition
from pactlens.serialization import primitive


async def main():
    root = Path(".runtime/phase4e5a-offline")
    root.mkdir(parents=True, exist_ok=False)
    task = fixture_task()
    model = OfflineTranscript(task)
    run = await run_episode(
        root / "six",
        task,
        EpisodeConfig("ENG-phase4e-offline", Condition.N3),
        model,
        consent=TestConsent(True),
        prompt_version=V32_PROMPT,
    )
    body = {
        **summary(run),
        "fake_requests": len(model.requests),
        "actual_inference": 0,
        "complete_wire_budgets": [
            primitive(request_budget(r.turns, "agent", require=False)) for r in model.requests
        ],
    }
    exclusive_json(Path("review/phase4e5a/offline.json"), body)
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
