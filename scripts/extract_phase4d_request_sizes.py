"""Read only fake-model protocol-test traces; export sizes, never prompts/outputs."""

import argparse
import hashlib
import json
from pathlib import Path

from pactlens.experiments.traces import read_trace
from pactlens.research.detector_runner import exclusive_json


def extract(root, output):
    reports = []
    for directory in sorted(root.glob("test_six_request_matrix*")):
        path = directory / "trace.jsonl"
        if not path.is_file() or directory.is_symlink():
            continue
        raw = path.read_bytes()
        rows = read_trace(path)
        config = rows[0]["payload"]
        assert config["config"]["group"] == "ENG-phase4d-offline"
        assert config["model"]["endpoint_type"] == "offline_fake"
        assert config["formal_episodes_executed"] == 0
        requests = [r["payload"]["request"] for r in rows if r["kind"] == "MODEL_REQUEST"]
        failures = [r["payload"] for r in rows if r["kind"] == "MODEL_FAILURE"]
        reports.append(
            {
                "synthetic_test_case": directory.name,
                "condition": config["config"]["condition"],
                "provenance": "FAKE_TRANSCRIPT_ENGINEERING_ONLY",
                "actual_model_calls": 0,
                "trace_sha256": hashlib.sha256(raw).hexdigest(),
                "requests": [
                    {
                        "actor": r["actor_id"],
                        "round": r["round_number"],
                        "complete_request_budget": r["token_budget"],
                    }
                    for r in requests
                ],
                "failures": [
                    {
                        "actor": f["actor_id"],
                        "round": f["round_number"],
                        "diagnostic": f["diagnostic"],
                        "complete_request_budget": f["token_budget"],
                    }
                    for f in failures
                ],
                "delivery_states": [
                    r["payload"]["delivery"]["status"] for r in rows if r["kind"] == "DELIVERY"
                ],
                "valid_declines": sum(
                    r["payload"]["status"] == "DECLINED"
                    for r in rows
                    if r["kind"] == "PROPOSAL_ATTEMPT"
                ),
            }
        )
        assert path.read_bytes() == raw
    assert len(reports) == 30, len(reports)
    exclusive_json(output, reports)
    print(
        json.dumps(
            {
                "synthetic_scenarios": len(reports),
                "actual_generation_calls": 0,
                "source_traces_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pytest_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    extract(args.pytest_directory, args.output)
