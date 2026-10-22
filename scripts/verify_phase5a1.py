"""Current public-source verification; optional separate historical private audit.

No historical Git HEAD is asserted against today's checkout. A clean checkout
needs no private campaign databases. --historical explicitly requires receipts.
"""

import argparse
import base64
import hashlib
import importlib.metadata
import inspect
import json
import subprocess
from pathlib import Path

from agentic_intent_gate import runtime

from pactlens.agents.prompts import PROMPT_HASHES
from pactlens.aig.consumer import load_store
from pactlens.experiments.replay import replay_trace
from pactlens.research.detector_runner import replay_prediction

ROOT = Path(__file__).resolve().parents[1]


def current(root=ROOT):
    root = Path(root)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    dist = importlib.metadata.distribution("agentic-intent-gate")
    source = json.loads(dist.read_text("direct_url.json"))
    assert (
        dist.version == "0.2.0"
        and source["vcs_info"]["commit_id"] == "7261fdd2f47d2b15fabe8faac527eeee37338eb1"
    )
    assert (
        "site-packages" in runtime.__file__
        and inspect.signature(runtime.open_runtime).parameters["execution_timeout_seconds"].default
        == 5
    )
    count = 0
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
            count += 1
    frozen = json.loads((root / "review/phase5a1/verification.json").read_text(encoding="utf-8"))
    assert all(PROMPT_HASHES[k] == v for k, v in frozen["historical_prompt_hashes"].items())
    campaign = json.loads(
        (root / "review/phase5a1/live/predeclared-plan.json").read_text(encoding="utf-8")
    )
    assert PROMPT_HASHES[campaign["prompt_version"]] == campaign["prompt_hash"]
    predictions = list((root / "review/phase5a1/live/predictions").glob("*.prediction.json"))
    for p in predictions:
        replay_prediction(p)
    assert len(predictions) == 10
    return {
        "scope": "CURRENT_PUBLIC_SOURCE",
        "HEAD": head,
        "aig_version": dist.version,
        "RECORD_hashes": count,
        "seconds": 5,
        "public_prediction_replays": len(predictions),
        "requires_private_runtime": False,
        "historical_campaign_base": frozen["HEAD"],
        "new_model_calls": 0,
        "new_effects": 0,
        "status": "PASS",
    }


def historical(private_root=None, root=ROOT):
    root = Path(root)
    private = Path(private_root) if private_root else root / ".runtime/phase5a1-live"
    if not all((private / name / "trace.jsonl").is_file() for name in ("N3", "C_PLUS")):
        raise FileNotFoundError(
            "HISTORICAL_PRIVATE_RECEIPTS_REQUIRED;current-source-check-needs-no-runtime"
        )
    files = [p for p in private.rglob("*") if p.is_file()]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    outcomes = []
    for name, expected in (("N3", 5), ("C_PLUS", 4)):
        directory = private / name
        replay = replay_trace(directory / "trace.jsonl")
        assert replay.model_calls == replay.new_effects == 0
        actual = sum(
            len(load_store(p).committed()) for p in directory.glob("actor-*") if p.is_dir()
        )
        assert actual == expected
        outcomes.append({"case": name, "committed_rows": actual})
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return {
        "scope": "HISTORICAL_PHASE5A1_PRIVATE_AUDIT",
        "campaign_base": "54fd01b2bd4c3d4ac4d74cce93aeb4f731e5dcf2",
        "outcomes": outcomes,
        "files_unchanged": True,
        "new_model_calls": 0,
        "new_effects": 0,
        "status": "PASS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", action="store_true")
    parser.add_argument("--private-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(historical(args.private_root) if args.historical else current(), indent=2))
