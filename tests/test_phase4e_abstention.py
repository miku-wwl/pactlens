"""L3 -> durable decision -> analysis coverage, including observed absences."""

import asyncio
import json

import pytest
from harness_helpers import FakeModel
from test_phase4d_detector import FakeDetector

from pactlens.agents.context_v32 import V32_PROMPT
from pactlens.aig.submission import TestConsent as Consent
from pactlens.evidence.compact_views import render_compact
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.views import View
from pactlens.experiments.conditions import EpisodeConfig
from pactlens.experiments.harness import run_episode
from pactlens.research.analysis import Case, metrics
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.detector_runner import analysis_prediction, predict, replay_prediction
from pactlens.research.fixtures import fixture_task
from pactlens.research.json_types import canonical_json, content_hash
from pactlens.research.seeds import Condition, Split


@pytest.mark.parametrize("condition", [Condition.N2, Condition.C_MINUS])
def test_observed_missing_and_blocked_do_not_alone_invalidate_packet(tmp_path, condition):
    task = fixture_task()

    def transform(body, request):
        if condition == Condition.C_MINUS:
            body.update(decision="decline", assignments=None)
        body["message"] = {
            "channel": "private",
            "recipients": [next(a.agent_id for a in task.agents if a.agent_id != request.actor_id)],
            "text": "Synthetic coordination attempt.",
        }

    # N2 submits all six decisions but blocks the three final Actions. C-minus
    # declines and attempts private messages that the router must block.
    run = asyncio.run(
        run_episode(
            tmp_path / "episode",
            task,
            EpisodeConfig("ENG-absence", condition),
            FakeModel(task, transform),
            consent=Consent(True),
            prompt_version=V32_PROMPT,
        )
    )
    assert len(run.observations) == (3 if condition == Condition.N2 else 0)
    inv = build_inventory(
        run.record,
        run.observations,
        run.deliveries,
        public_id=run.public_id,
        policy=ObservationPolicy.ROUTER_AUDIT,
        status=run.status,
        shared_capture=True,
    )
    for view in (View.M, View.A, View.R, View.MAE):
        packet = render_compact(
            inv, {f.fact_id for f in inv.facts}, set(), "0" * 64, view, DetectorEnvelope()
        )
        path = asyncio.run(
            predict(
                tmp_path / "predictions",
                packet,
                FakeDetector(),
                engineering_id="ENG-absence-detector",
            )
        )
        artifact = replay_prediction(path)
        reasons = artifact["decision"]["reasons"]
        assert "INCOMPLETE_SOURCE_CAPTURE" not in reasons
        assert "UNRESOLVED_OBSERVABLE_STATE" not in reasons
        prediction = analysis_prediction(path)
        case = Case(
            "SYNTH-case",
            "SYNTH-group",
            Split.PILOT,
            Condition.N1,
            0,
            True,
            True,
            True,
            False,
            True,
            (prediction,),
        )
        result = metrics([case], view, 0.5)
        assert result["coverage"] == int(not artifact["abstained"])
        assert result["executed"] == 1 and result["n1_fpr"] == 0
        # Latent score is diagnostic only, even after rehashing tampered flags.
        body = json.loads(path.read_text())
        body["abstained"] = not body["abstained"]
        body["artifact_hash"] = content_hash(
            {k: v for k, v in body.items() if k != "artifact_hash"}
        )
        path.write_text(canonical_json(body))
        with pytest.raises(ValueError, match="AUTHORITATIVE_ABSTENTION"):
            replay_prediction(path)


def test_host_abstention_cannot_feed_a_latent_score(tmp_path):
    from test_phase4d_detector import packets

    packet = packets("c_plus").packet(View.R)
    path = asyncio.run(predict(tmp_path, packet, FakeDetector(), engineering_id="ENG-host-forced"))
    body = replay_prediction(path)
    assert body["prediction"]["response"]["risk_score"] == 0.25
    assert body["decision"]["effective_score"] is None
    assert analysis_prediction(path) == (View.R, None, None)
    case = Case(
        "SYNTH-positive",
        "SYNTH-group",
        Split.CALIBRATION,
        Condition.C_PLUS,
        1,
        False,
        True,
        True,
        True,
        True,
        (analysis_prediction(path),),
    )
    m = metrics([case], View.R, 0.5)
    assert m["recall"] == 0 and m["coverage"] == 0 and m["abstention_rate"] == 1


def test_historical_v1_is_readable_but_not_implicitly_scored(tmp_path):
    from test_phase4d_detector import packets

    path = asyncio.run(
        predict(tmp_path, packets().packet(View.M), FakeDetector(), engineering_id="ENG-history")
    )
    body = json.loads(path.read_text())
    body["version"] = "pactlens-detector-runner-v1-candidate"
    body.pop("decision")
    body["artifact_hash"] = content_hash({k: v for k, v in body.items() if k != "artifact_hash"})
    path.write_text(canonical_json(body))
    replay_prediction(path)
    with pytest.raises(ValueError, match="LEGACY_PREDICTION"):
        analysis_prediction(path)
