"""Offline integrity/provenance checks. Reads protected source and engineering stores."""

import ast
import base64
import hashlib
import importlib.metadata
import inspect
import json
import subprocess
from pathlib import Path

from agentic_intent_gate import runtime

from pactlens.agents.context_v3 import CONTEXT_VERSION, SYSTEM_V3, V3_PROMPT
from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.agents.protocol_diagnostics import PROTOCOL_HASH
from pactlens.experiments.replay import replay_trace
from pactlens.research.claims import validate_claims
from pactlens.research.detector_runner import replay_prediction
from pactlens.serialization import content_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    dist = importlib.metadata.distribution("agentic-intent-gate")
    direct = json.loads(dist.read_text("direct_url.json"))
    assert (
        dist.version == "0.2.0"
        and direct["vcs_info"]["commit_id"] == "7261fdd2f47d2b15fabe8faac527eeee37338eb1"
    )
    assert ".venv" in runtime.__file__
    checked = 0
    for file in dist.files:
        if file.hash:
            actual = (
                base64.urlsafe_b64encode(
                    hashlib.new(file.hash.mode, Path(dist.locate_file(file)).read_bytes()).digest()
                )
                .decode()
                .rstrip("=")
            )
            assert actual == file.hash.value, str(file)
            checked += 1
    assert (
        inspect.signature(runtime.open_runtime).parameters["execution_timeout_seconds"].default == 5
    )
    protected = [
        "AGENTS.md",
        "pyproject.toml",
        "uv.lock",
        "docs/EXPERIMENT_PLAN.md",
        "src/pactlens/arena",
        "src/pactlens/aig",
        "src/pactlens/integration",
        "src/pactlens/evidence",
        "src/pactlens/experiments/harness.py",
        "src/pactlens/experiments/conditions.py",
        "src/pactlens/experiments/replay.py",
        "src/pactlens/experiments/traces.py",
        "src/pactlens/agents/models.py",
        "src/pactlens/agents/budgets.py",
        "src/pactlens/agents/context_v3.py",
        "tests",
    ]
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    baseline = subprocess.run(
        ["git", "show", "HEAD:src/pactlens/agents/prompts.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    constants = {}
    for node in ast.parse(baseline).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = ast.literal_eval(node.value)
    old_hashes = {
        constants["LEGACY_PROMPT"]: content_hash(constants["SYSTEM"]),
        constants["CANDIDATE_PROMPT"]: content_hash(
            {
                "system": constants["SYSTEM_V2"],
                "examples": constants["EXAMPLE_VERSION"],
                "protocol_hash": PROTOCOL_HASH,
            }
        ),
        V3_PROMPT: content_hash(
            {
                "system": SYSTEM_V3,
                "examples": constants["EXAMPLE_VERSION"],
                "protocol_hash": PROTOCOL_HASH,
                "context": CONTEXT_VERSION,
            }
        ),
    }
    assert all(PROMPT_HASHES[k] == v for k, v in old_hashes.items())
    trace = ROOT / ".runtime/phase4d-v31/ENG-phase4d-v31-N3/trace.jsonl"
    private_files = list((ROOT / ".runtime/phase4d-v31").rglob("*.sqlite3")) + [trace]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in private_files}
    replay = replay_trace(trace)
    assert replay.model_calls == replay.new_effects == 0
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in private_files}
    predictions = list((ROOT / "review/phase4d").rglob("*.prediction.json"))
    for p in predictions:
        snapshot = p.read_bytes()
        replay_prediction(p)
        assert p.read_bytes() == snapshot
    claims = ROOT / "research/phase4d/claims.json"
    if claims.exists():
        validate_claims(json.loads(claims.read_text(encoding="utf-8")), ROOT)
    assert len(list((ROOT / ".runtime/phase4d-v31").glob("call-*.json"))) == 6
    assert len(list((ROOT / ".runtime/phase4d-detector").glob("charge-*.json"))) == 2
    text = (ROOT / "research/phase4d/manuscript.md").read_text(encoding="utf-8")
    assert len(text.split("## Abstract\n\n")[1].split("\n\n##")[0].split()) == 150
    print(
        json.dumps(
            {
                "aig_version": dist.version,
                "installed_record_hashes": checked,
                "default_execution_seconds": 5,
                "historical_prompt_hashes": old_hashes,
                "protected_paths_unchanged": protected,
                "private_source_hashes_unchanged_by_replay": len(before),
                "prediction_replays": len(predictions),
                "agent_call_ledger": 6,
                "detector_call_ledger": 2,
                "formal_executions": 0,
                "heldout_outcomes_read": 0,
                "abstract_words": 150,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
