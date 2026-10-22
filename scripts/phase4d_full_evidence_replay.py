"""Full rendered-text parity/budget audit from an existing synthetic capture; zero effects."""

import argparse
import hashlib
import json
from pathlib import Path

from pactlens.aig.contract import ObservedAction
from pactlens.evidence.compact_views import render_compact
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.records import Channel
from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.views import View
from pactlens.experiments.channels import Delivery
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.json_types import canonical_json


def audit(trace, output):
    original = trace.read_bytes()
    replay = replay_trace(trace)
    rows = read_trace(trace)
    config = rows[0]["payload"]
    assert config["model"]["endpoint_type"] == "offline_fake"
    assert config["formal_episodes_executed"] == 0
    observations = tuple(
        ObservedAction(**r["payload"]["observation"]) for r in rows if r["kind"] == "ACTION"
    )
    deliveries = []
    for row in rows:
        if row["kind"] == "DELIVERY":
            body = row["payload"]["delivery"]
            deliveries.append(
                Delivery(
                    **{
                        **body,
                        "channel": Channel(body["channel"]),
                        "requested": tuple(body["requested"]),
                        "delivered": tuple(body["delivered"]),
                    }
                )
            )
    assert len(observations) == 6
    output.mkdir(parents=True, exist_ok=False)
    reports = []
    for policy in ObservationPolicy:
        inv = build_inventory(
            replay.record,
            observations,
            tuple(deliveries),
            public_id=replay.evidence.as_mapping()["episode_public_id"],
            policy=policy,
            status=replay.status,
            shared_capture=True,
        )
        packets = [
            render_compact(
                inv, {f.fact_id for f in inv.facts}, set(), "0" * 64, v, DetectorEnvelope()
            )
            for v in View
        ]
        facts = {
            p.view: {canonical_json(f) for f in canonical_fact_records(p.verify()[1])}
            for p in packets
        }
        assert facts[View.R] == facts[View.MAE]
        assert facts[View.M] | facts[View.A] == facts[View.MA]
        assert facts[View.MA] <= facts[View.R]
        reports.append(
            {
                "policy": policy.value,
                "full_source_fact_count": len(inv.facts),
                "canonical_R_equals_MAE": True,
                "M_union_A_equals_MA": True,
                "MA_subset_R": True,
                "views": {p.view.value: json.loads(p.manifest_json)["budget"] for p in packets},
                "omitted_facts": [],
                "use": "DIAGNOSTIC_ONLY_NOT_BUDGET_ELIGIBLE_MODEL_PACKETS",
            }
        )
        for packet in packets:
            stem = policy.name + "-" + packet.view.value
            (output / (stem + ".txt")).write_text(packet.text, encoding="utf-8")
            exclusive_json(output / (stem + ".manifest.json"), json.loads(packet.manifest_json))
    assert trace.read_bytes() == original
    exclusive_json(
        output / "verification.json",
        {
            "source_trace_sha256": hashlib.sha256(original).hexdigest(),
            "source_unchanged": True,
            "new_model_calls": 0,
            "new_effects": 0,
            "reports": reports,
        },
    )
    print(
        json.dumps(
            {
                "full_policy_sets": len(reports),
                "parity": "PASS",
                "new_model_calls": 0,
                "new_effects": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit(args.trace, args.output)
