"""Run remaining exact checks and bind a completed full test run to current source."""

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review/phase4d"


def main():
    tested = json.loads((REVIEW / "tested-source.json").read_text(encoding="utf-8"))
    current = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in ("src", "tests")
        for p in (ROOT / directory).rglob("*.py")
    }
    assert current == tested, "SOURCE_CHANGED_AFTER_TEST_START"
    suites = ET.parse(REVIEW / "logs/full-suite-verified.xml").getroot().iter("testsuite")
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.attrib.get(key, 0))
    assert totals == {"tests": 832, "failures": 0, "errors": 0, "skipped": 0}, totals
    assert (REVIEW / "logs/full-suite-verified-exit.txt").read_text().strip() == "0"
    commands = [
        ["uv", "sync", "--locked"],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "lock", "--check", "--offline"],
        ["uv", "run", "python", "-m", "compileall", "-q", "src", "tests", "scripts"],
        ["uv", "run", "python", "scripts/verify_phase4d_static.py"],
        ["git", "diff", "--check"],
    ]
    results = []
    for i, command in enumerate(commands, 1):
        result = subprocess.run(
            command,
            check=False,
            cwd=ROOT,
            env={**os.environ, "UV_OFFLINE": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        log = REVIEW / f"logs/verified-command-{i}.txt"
        log.write_bytes(
            ("COMMAND: " + " ".join(command) + "\n").encode()
            + result.stdout
            + f"\nEXIT_CODE: {result.returncode}\n".encode()
        )
        results.append(
            {
                "command": command,
                "exit_code": result.returncode,
                "log": log.relative_to(ROOT).as_posix(),
            }
        )
    all_passed = all(r["exit_code"] == 0 for r in results)
    report = {
        "version": "phase4d-final-verification-v1",
        "baseline": "af3146bd0b8dc4b7d106ce0d32fca38750e36626",
        "full_suite": totals,
        "baseline_tests": 724,
        "added_tests": 108,
        "commands": results,
        "source_hashes_verified": len(current),
        "all_required_passed": all_passed,
        "actual_agent_generations": 6,
        "actual_detector_generations": 2,
        "formal_study_executions": 0,
        "limitations": [
            "no qualified exact tokenizer",
            "real agent 1/6 valid",
            "both live detector outputs invalid",
            "complete six-action evidence infeasible",
            "no human adjudication or formal study",
        ],
    }
    (REVIEW / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
