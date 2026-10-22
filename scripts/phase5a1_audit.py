"""Full retained evidence and native-envelope decomposition, zero calls/effects."""

import hashlib
import json
from pathlib import Path

from pactlens.agents.deepseek_provider import payload
from pactlens.aig.contract import ObservedAction
from pactlens.evidence.compact_views import verify_compact_parity
from pactlens.evidence.inventory import build_inventory
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.records import Channel
from pactlens.evidence.tight_views import citation_keys, render
from pactlens.evidence.views import View
from pactlens.experiments.channels import Delivery
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json
from pactlens.research.native_detector import envelope, schema_for
from pactlens.serialization import canonical_json, primitive


def main():
    trace = Path(".runtime/phase4d-six-action-communication/trace.jsonl")
    before = trace.read_bytes()
    replay = replay_trace(trace)
    rows = read_trace(trace)
    observations = tuple(
        ObservedAction(**r["payload"]["observation"]) for r in rows if r["kind"] == "ACTION"
    )
    deliveries = []
    for r in rows:
        if r["kind"] == "DELIVERY":
            d = r["payload"]["delivery"]
            deliveries.append(
                Delivery(
                    **{
                        **d,
                        "channel": Channel(d["channel"]),
                        "requested": tuple(d["requested"]),
                        "delivered": tuple(d["delivered"]),
                    }
                )
            )
    results = []
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
            render(inv, {f.fact_id for f in inv.facts}, set(), "0" * 64, v, envelope())
            for v in View
        ]
        verify_compact_parity(packets[3], packets[4])
        report = {
            "policy": policy.value,
            "source_facts": len(inv.facts),
            "parity": True,
            "new_model_calls": 0,
            "new_effects": 0,
            "views": {},
        }
        for p in packets:
            schema = schema_for(citation_keys(p.text))
            wire = payload(p.envelope.turns(p.text), schema)
            size = lambda x: len(canonical_json(x).encode("utf-8"))
            h = json.loads(p.text.split("\n")[0]) if p.view != View.MAE else json.loads(p.text)["h"]
            report["views"][p.view.value] = {
                "budget": primitive(p.envelope.budget(p.text)),
                "wire_bytes": size(wire),
                "system_bytes": len(p.envelope.system.encode()),
                "task_instruction_bytes": len(p.envelope.task.encode()),
                "output_instruction_bytes": len(p.envelope.output.encode()),
                "native_schema_bytes": size(schema),
                "native_format_bytes": size(wire["text"]),
                "evidence_bytes": len(p.text.encode()),
                "evidence_values_bytes": size(h["values"]),
                "provenance_legends_bytes": size(h["metadata"])
                + size(h["kinds"])
                + size(h["streams"]),
                "header_layout_bytes": size(h["layout"]),
                "input_json_escapes_and_framing_bytes": size(wire["input"])
                - sum(len(t.content.encode()) for t in p.envelope.turns(p.text)),
                "retained_identifiers": "all originals, interned; fact UUIDs deterministically reconstructed from original episode and logical keys",
                "omitted": 0,
            }
            stem = Path("review/phase5a1/full-audit") / (policy.name + "-" + p.view.value)
            stem.parent.mkdir(exist_ok=True)
            stem.with_suffix(".txt").write_text(p.text, encoding="utf-8")
            exclusive_json(stem.with_suffix(".json"), json.loads(p.manifest_json))
        results.append(report)
    assert trace.read_bytes() == before
    exclusive_json(
        Path("review/phase5a1/full-audit.json"),
        {
            "source_trace_sha256": hashlib.sha256(before).hexdigest(),
            "source_unchanged": True,
            "reports": results,
        },
    )
    print(
        json.dumps(
            [
                {
                    "policy": r["policy"],
                    "R": r["views"]["R"]["budget"]["estimated_tokens"],
                    "MAE": r["views"]["MAE"]["budget"]["estimated_tokens"],
                }
                for r in results
            ]
        )
    )


if __name__ == "__main__":
    main()
