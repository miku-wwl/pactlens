"""Independent current-source, installed-package and read-only durable-state audit."""

import base64
import hashlib
import importlib.metadata
import inspect
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from agentic_intent_gate import runtime

from pactlens.agents.deepseek_provider import AGENT_SCHEMA, PROFILE
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.consumer import load_store
from pactlens.evidence.compact_views import CompactView, verify_compact_parity
from pactlens.evidence.views import View
from pactlens.experiments.replay import replay_trace
from pactlens.research.abstention import POLICY_HASH
from pactlens.research.detector_contract import RESPONSE_HASH, DetectorEnvelope
from pactlens.research.detector_runner import replay_prediction
from pactlens.research.native_detector import envelope
from pactlens.research.study_launch import freeze_candidate, verify_launch

ROOT = Path(__file__).resolve().parents[1]
SAFE = ROOT / "review/phase5a1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()

    head = git("rev-parse", "HEAD")
    assert head == "54fd01b2bd4c3d4ac4d74cce93aeb4f731e5dcf2"
    protected = [
        "AGENTS.md",
        "pyproject.toml",
        "uv.lock",
        "src/pactlens/arena",
        "src/pactlens/aig",
        "src/pactlens/integration",
        "src/pactlens/agents/models.py",
        "src/pactlens/agents/budgets.py",
        "src/pactlens/agents/context_v3.py",
        "src/pactlens/agents/context_v31.py",
        "src/pactlens/agents/context_v32.py",
        "src/pactlens/agents/protocol_diagnostics.py",
        "src/pactlens/experiments",
        "src/pactlens/research/abstention.py",
        "src/pactlens/research/analysis.py",
        "src/pactlens/research/manifest.py",
        "src/pactlens/research/seeds.py",
        "docs/EXPERIMENT_PLAN.md",
    ]
    protected += git(
        "ls-files", "tests", "docs/PHASE4*", "docs/PHASE5A_*", "review/phase4d", "review/phase4e5a"
    ).splitlines()
    git("diff", "--exit-code", "HEAD", "--", *protected)
    code = """import json
import pactlens.agents.prompts as p
from pactlens.agents.deepseek_provider import AGENT_SCHEMA,PROFILE
from pactlens.research.abstention import POLICY_HASH
from pactlens.research.detector_contract import RESPONSE_HASH,DetectorEnvelope
print(json.dumps({'prompts':p.PROMPT_HASHES,'module':p.__file__,'agent_schema':AGENT_SCHEMA,'provider':PROFILE,'policy':POLICY_HASH,'response':RESPONSE_HASH,'envelope':DetectorEnvelope().config_hash}))
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / ".runtime/phase5a1-baseline/src")}
    old = json.loads(
        subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT / ".runtime/phase5a1-baseline",
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    assert "phase5a1-baseline" in old["module"] and len(old["prompts"]) == 5
    assert all(PROMPT_HASHES[k] == v for k, v in old["prompts"].items())
    assert (
        old["agent_schema"] == AGENT_SCHEMA
        and old["provider"] == PROFILE
        and old["policy"] == POLICY_HASH
        and old["response"] == RESPONSE_HASH
        and old["envelope"] == DetectorEnvelope().config_hash
    )
    dist = importlib.metadata.distribution("agentic-intent-gate")
    direct = json.loads(dist.read_text("direct_url.json"))
    assert (
        dist.version == "0.2.0"
        and direct["vcs_info"]["commit_id"] == "7261fdd2f47d2b15fabe8faac527eeee37338eb1"
    )
    assert (
        ".venv" in runtime.__file__
        and inspect.signature(runtime.open_runtime).parameters["execution_timeout_seconds"].default
        == 5
    )
    checked = 0
    for f in dist.files:
        if f.hash:
            actual = (
                base64.urlsafe_b64encode(
                    hashlib.new(f.hash.mode, Path(dist.locate_file(f)).read_bytes()).digest()
                )
                .decode()
                .rstrip("=")
            )
            assert actual == f.hash.value
            checked += 1
    private = ROOT / ".runtime/phase5a1-live"
    files = [p for p in private.rglob("*") if p.is_file()]
    before = {str(p): sha(p) for p in files}
    durable = []
    for name, expected in [("N3", 5), ("C_PLUS", 4)]:
        root = private / name
        replay = replay_trace(root / "trace.jsonl")
        assert replay.model_calls == replay.new_effects == 0
        commits = sum(len(load_store(p).committed()) for p in root.glob("actor-*") if p.is_dir())
        assert commits == expected
        core_states = {}
        authorizations = 0
        attempts = 0
        for database in root.rglob("gate.sqlite3"):
            with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
                for state, count in db.execute("SELECT state,count(*) FROM actions GROUP BY state"):
                    core_states[state] = core_states.get(state, 0) + count
                authorizations += db.execute(
                    "SELECT count(*) FROM action_authorizations"
                ).fetchone()[0]
                attempts += db.execute("SELECT count(*) FROM action_attempts").fetchone()[0]
        assert (
            core_states == {"Succeeded": expected}
            and authorizations == expected
            and attempts == expected
        )
        durable.append(
            {
                "case": name,
                "verified_committed_rows": commits,
                "core_action_states": core_states,
                "independent_authorization_rows": authorizations,
                "durable_claim_attempts": attempts,
                "replay_calls": 0,
                "replay_effects": 0,
            }
        )
    assert before == {str(p): sha(p) for p in files}
    paths = list((SAFE / "live/predictions").glob("*.prediction.json"))
    assert len(paths) == 10
    groups = {}
    for path in paths:
        b = path.read_bytes()
        out = replay_prediction(path)
        assert path.read_bytes() == b
        p = out["packet"]
        packet = CompactView(View(p["view"]), p["text"], p["manifest_json"], envelope())
        h, _ = packet.verify()
        groups.setdefault(h["episode"], {})[packet.view] = packet
        assert not any(
            marker in packet.text
            for marker in (
                "assigned_coalition",
                "private_brief",
                '"condition"',
                '"truth"',
                '"oracle"',
            )
        )
    for views in groups.values():
        assert verify_compact_parity(views[View.R], views[View.MAE])
    freeze_path = ROOT / "research/phase5a1/freeze-candidate.json"
    candidate = json.loads(freeze_path.read_text(encoding="utf-8"))
    assert (
        candidate == freeze_candidate(ROOT, profile="phase5a1")
        and len(candidate["decisions"]) == 16
    )
    try:
        verify_launch(candidate, ROOT)
    except ValueError as error:
        assert str(error) == "FROZEN_APPROVALS_REQUIRED"
    else:
        raise AssertionError("UNAPPROVED_FORMAL_LAUNCH")
    usage = json.loads((SAFE / "live/usage-final.json").read_text(encoding="utf-8"))
    assert (
        usage["agent_requests"] == 11
        and usage["detector_requests"] == 10
        and len(usage["calls"]) == 21
    )
    assert usage["reserved_or_charged_micro_usd"] == 25348 <= usage["ceiling_micro_usd"] <= 2000000
    assert sum(c["estimated_actual_micro_usd"] for c in usage["calls"]) == 11547
    assert all(c["reasoning_tokens"] == 0 and c["status"] == "COMPLETED" for c in usage["calls"])
    checks = {
        n: (SAFE / "logs" / (n + "-exit.txt")).read_text().strip() == "0"
        for n in (
            "final-sync",
            "final-regression",
            "final-ruff-check",
            "final-ruff-format",
            "final-lock",
            "baseline-retry",
        )
    }
    assert all(checks.values()), checks
    log = (SAFE / "logs/final-regression.txt").read_text(encoding="utf-8")
    passed_match = re.search(r"(\d+) passed", log)
    assert passed_match and int(passed_match[1]) >= 930 and "failed" not in log
    assert "885 passed" in (SAFE / "logs/baseline-retry-tests.txt").read_text(encoding="utf-8")
    sources = {
        p.relative_to(ROOT).as_posix(): sha(p)
        for d in ("src", "tests", "scripts")
        for p in (ROOT / d).rglob("*.py")
        if "__pycache__" not in p.parts
    }
    report = {
        "all_required_passed": True,
        "HEAD": head,
        "checks": checks,
        "tests_passed": int(passed_match[1]),
        "baseline_passed": 885,
        "aig_version": dist.version,
        "aig_record_hashes": checked,
        "aig_seconds": 5,
        "historical_prompt_hashes": old["prompts"],
        "historical_policy_hash": POLICY_HASH,
        "historical_response_hash": RESPONSE_HASH,
        "historical_envelope_hash": DetectorEnvelope().config_hash,
        "protected_paths": protected,
        "durable_rows": durable,
        "private_files_unchanged_by_replay": True,
        "prediction_replays": 10,
        "rendered_R_MAE_pairs": len(groups),
        "formal_executions": 0,
        "approval_status": "PENDING",
        "research_ready": False,
        "source_sha256": sources,
    }
    (SAFE / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("source_sha256", "protected_paths", "historical_prompt_hashes")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
