"""Offline decomposition of preserved inputs; no provider or effect invocation."""

import json
from pathlib import Path

from pactlens.agents.budgets import token_preflight
from pactlens.agents.deepseek_provider import AGENT_SCHEMA, payload, request_budget
from pactlens.agents.models import Turn
from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json, replay_prediction
from pactlens.serialization import canonical_json


def size(value):
    return len(canonical_json(value).encode("utf-8"))


def main():
    trace = Path(".runtime/phase4e5a-live/N3/trace.jsonl")
    rows = read_trace(trace)
    requests = [r["payload"]["request"] for r in rows if r["kind"] == "MODEL_REQUEST"]
    r = requests[-1]
    turns = tuple(Turn(**t) for t in r["turns"])
    wire = payload(turns, AGENT_SCHEMA)
    total = size(wire)
    body = json.loads(turns[1].content)
    values = {k: size(v) for k, v in wire.items()}
    content = {
        k: len(v.content.encode("utf-8"))
        for k, v in zip(("system_and_brief", "observation"), turns, strict=True)
    }
    instructions, brief = turns[0].content.split("Private brief: ", 1)
    schema_control_bytes = size(wire["text"])
    result = {
        "provenance": "OFFLINE_READ_ONLY_NO_CALLS",
        "historical_full_estimate": request_budget(turns, "agent", require=False).estimated_tokens,
        "historical_conversation_estimate": token_preflight(turns, limit=2000).estimated_tokens,
        "wire_utf8_bytes": total,
        "wire_value_bytes": values,
        "wire_key_separator_bytes": total - sum(values.values()),
        "system_instruction_bytes": len(instructions.encode()),
        "brief_bytes": len(brief.encode()),
        "content_utf8_bytes": content,
        "observation_field_value_bytes": {k: size(v) for k, v in body.items()},
        "observation_keys_separator_bytes": len(turns[1].content.encode())
        - sum(size(v) for v in body.values()),
        "native_schema_bytes": size(AGENT_SCHEMA),
        "native_text_format_bytes": schema_control_bytes,
        "input_json_framing_and_escape_bytes": size(wire["input"]) - sum(content.values()),
        "heuristic_role_and_margin_tokens": 162,
        "historical_sent_calls": [],
        "detector_historical": [],
        "new_model_calls": 0,
        "new_effects": 0,
    }
    assert (
        result["historical_full_estimate"] == 2132
        and result["historical_conversation_estimate"] == 1481
    )
    usage = json.loads(Path("review/phase4e5a/live/usage-final.json").read_text(encoding="utf-8"))
    for n, request in enumerate(requests[:3]):
        t = tuple(Turn(**v) for v in request["turns"])
        actual = usage["calls"][n]["input_tokens"]
        estimate = request_budget(t, "agent").estimated_tokens
        result["historical_sent_calls"].append(
            {
                "estimate": estimate,
                "provider_usage": actual,
                "absolute_error": abs(estimate - actual),
                "qualified_exact": False,
            }
        )
    for path in sorted(Path("review/phase4e5a/live/predictions").glob("*.prediction.json")):
        artifact = replay_prediction(path)
        result["detector_historical"].append(
            {
                "identity": artifact["identity"],
                "view": artifact["prediction"]["view"],
                "error": artifact["prediction"]["error"],
                "provider_error": artifact.get("provider_error"),
                "host_mandated": artifact["decision"]["host_mandated"],
                "reasons": artifact["decision"]["reasons"],
                "usage": artifact["usage"],
                "raw_response_available": False,
            }
        )
    exclusive_json(Path("review/phase5a1/diagnosis.json"), result)
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("detector_historical",)}, indent=2)
    )


if __name__ == "__main__":
    main()
