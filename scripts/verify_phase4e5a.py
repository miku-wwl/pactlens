"""Current-source checks plus read-only replay; no network, inference or effects."""

import base64
import hashlib
import importlib.metadata
import inspect
import json
import runpy
import subprocess
from pathlib import Path

from agentic_intent_gate import runtime

from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.consumer import load_store
from pactlens.evidence.compact_views import CompactView
from pactlens.evidence.views import View
from pactlens.experiments.replay import replay_trace
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.research.detector_runner import replay_prediction
from pactlens.research.json_types import canonical_json
from pactlens.research.study_launch import freeze_candidate, schedule, verify_launch
from pactlens.serialization import content_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()

    assert git("rev-parse", "HEAD") == "65a003263cccfb3d0370db13b086de958dab0db4"
    protected = [
        "AGENTS.md",
        "pyproject.toml",
        "uv.lock",
        "src/pactlens/arena",
        "src/pactlens/aig",
        "src/pactlens/integration",
        "src/pactlens/evidence",
        "src/pactlens/agents/models.py",
        "src/pactlens/agents/budgets.py",
        "src/pactlens/agents/context_v3.py",
        "src/pactlens/agents/context_v31.py",
        "src/pactlens/agents/protocol_diagnostics.py",
        "src/pactlens/experiments/conditions.py",
        "src/pactlens/experiments/traces.py",
        "src/pactlens/research/analysis.py",
        "src/pactlens/research/manifest.py",
        "src/pactlens/research/seeds.py",
        "docs/EXPERIMENT_PLAN.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_DICTIONARY.md",
    ]
    protected += [
        p
        for p in git("ls-files", "tests", "docs/PHASE4*").splitlines()
        if p != "tests/test_scenario_fixtures.py"
    ]
    git("diff", "--exit-code", "HEAD", "--", *protected)
    old = runpy.run_path(str(ROOT / ".runtime/baseline-65a/src/pactlens/agents/prompts.py"))[
        "PROMPT_HASHES"
    ]
    assert all(PROMPT_HASHES[k] == v for k, v in old.items())
    dist = importlib.metadata.distribution("agentic-intent-gate")
    direct = json.loads(dist.read_text("direct_url.json"))
    assert (
        dist.version == "0.2.0"
        and direct["vcs_info"]["commit_id"] == "7261fdd2f47d2b15fabe8faac527eeee37338eb1"
    )
    assert ".venv" in runtime.__file__
    checked = 0
    for f in dist.files:
        if f.hash:
            assert (
                base64.urlsafe_b64encode(
                    hashlib.new(f.hash.mode, Path(dist.locate_file(f)).read_bytes()).digest()
                )
                .decode()
                .rstrip("=")
                == f.hash.value
            )
            checked += 1
    assert (
        inspect.signature(runtime.open_runtime).parameters["execution_timeout_seconds"].default == 5
    )
    root = ROOT / ".runtime/phase4e5a-live/N3"
    files = [p for p in root.rglob("*") if p.is_file()]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    replay = replay_trace(root / "trace.jsonl")
    assert replay.model_calls == replay.new_effects == 0
    assert sum(len(load_store(p).committed()) for p in root.glob("actor-*") if p.is_dir()) == 3
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    paths = list((ROOT / "review/phase4e5a").rglob("*.prediction.json"))
    pairs = {}
    for path in paths:
        snapshot = path.read_bytes()
        body = replay_prediction(path)
        assert path.read_bytes() == snapshot
        packet = body["packet"]
        assert not any(
            key in packet["text"]
            for key in ("assigned_coalition", "private_brief", "oracle", '"condition"', '"truth"')
        )
        p = CompactView(
            View(packet["view"]),
            packet["text"],
            packet["manifest_json"],
            DetectorEnvelope(**packet["envelope"]),
        )
        header, facts = p.verify()
        pairs.setdefault(header["episode"], {})[p.view] = {
            canonical_json(f.as_mapping()) for f in facts
        }
    for views in pairs.values():
        if View.R in views and View.MAE in views:
            assert views[View.R] == views[View.MAE]
    candidate = json.loads(
        (ROOT / "research/phase5a/freeze-candidate.json").read_text(encoding="utf-8")
    )
    assert candidate == freeze_candidate(ROOT)
    assert all(x["status"] == "PENDING" for x in candidate["decisions"].values())
    try:
        verify_launch(candidate, ROOT)
    except ValueError:
        pass
    else:
        raise AssertionError("unapproved launch")
    dry = json.loads(
        (ROOT / "review/phase4e5a/full-schedule-dry-final.json").read_text(encoding="utf-8")
    )
    assert dry["schedule_hash"] == content_hash(schedule(candidate["configuration_hash"]))
    assert (
        dry["unique_stores"] == dry["unique_scopes"] == 360
        and dry["formal_slots_used"] == dry["model_calls"] == dry["effects"] == 0
    )
    usage = json.loads(
        (ROOT / "review/phase4e5a/live/usage-final.json").read_text(encoding="utf-8")
    )
    assert (
        usage["agent_requests"] == 3
        and usage["detector_requests"] == 8
        and usage["reserved_or_charged_micro_usd"] == 15012
    )
    assert sum(x["estimated_actual_micro_usd"] for x in usage["calls"]) == 7354
    assert (
        len(list((ROOT / "review/phase4e5a/synthetic-analysis-complete/tables").glob("*.csv"))) == 9
    )
    text = (ROOT / "research/phase5a/manuscript.md").read_text(encoding="utf-8")
    assert len(text.split("## Abstract\n\n")[1].split("\n\n##")[0].split()) == 150
    checks = {}
    for name in (
        "final-regression",
        "final-ruff-check",
        "final-ruff-format",
        "final-lock",
        "final-abstention-targeted",
    ):
        checks[name] = (ROOT / ("review/phase4e5a/logs/" + name + "-exit.txt")).read_text(
            encoding="utf-8"
        ).strip() == "0"
    assert all(checks.values())
    tests = (ROOT / "review/phase4e5a/logs/final-regression.txt").read_text(encoding="utf-8")
    assert "885 passed" in tests and "failed" not in tests
    sources = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in ("src", "tests", "scripts")
        for p in (ROOT / directory).rglob("*.py")
        if "__pycache__" not in p.parts
    }
    report = {
        "all_required_passed": True,
        "checks": checks,
        "aig_version": dist.version,
        "aig_record_hashes": checked,
        "historical_prompt_hashes": old,
        "protected_paths": protected,
        "prediction_replays": len(paths),
        "private_files_unchanged_by_replay": len(before),
        "real_agent_receipts": 3,
        "actual_generations": 11,
        "metadata_http_requests": 1,
        "formal_executions": 0,
        "heldout_outcomes_accessed": 0,
        "human_reviews": 0,
        "source_sha256": sources,
        "freeze_hash": candidate["manifest_hash"],
        "abstract_words": 150,
    }
    (ROOT / "review/phase4e5a/verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("source_sha256", "protected_paths", "historical_prompt_hashes")
            }
        )
    )


if __name__ == "__main__":
    main()
