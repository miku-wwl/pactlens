import asyncio
import json
from dataclasses import replace

import pytest
from harness_helpers import message, run_fake

from pactlens.evidence.harness_adapter import project_harness
from pactlens.experiments.replay import replay_trace
from pactlens.experiments.traces import TraceWriter, read_trace
from pactlens.research.fixtures import fixture_task
from pactlens.serialization import canonical_json, content_hash


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    run, _ = asyncio.run(
        run_fake(tmp_path_factory.mktemp("integrity"), fixture_task(), transform=message)
    )
    return run


def rewrite(path, rows):
    previous = "0" * 64
    lines = []
    for n, row in enumerate(rows, 1):
        row = {k: v for k, v in row.items() if k != "digest"}
        row.update(sequence=n, logical_position=n, previous=previous)
        digest = content_hash(row)
        lines.append(canonical_json({**row, "digest": digest}))
        previous = digest
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "case",
    [
        "digest",
        "truncated_line",
        "duplicate",
        "reversed",
        "unknown",
        "oversized",
        "episode",
        "after_terminal",
    ],
)
def test_trace_storage_integrity_rejects_corruption(tmp_path, captured, case):
    path = tmp_path / "changed.jsonl"
    lines = captured.trace_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if case == "digest":
        lines[1] = lines[1].replace("ARENA", "MODEL_RESPONSE")
    elif case == "truncated_line":
        lines[-1] = lines[-1][:-2]
    elif case == "duplicate":
        lines.insert(2, lines[1])
    elif case == "reversed":
        lines[1:3] = reversed(lines[1:3])
    elif case == "unknown":
        row = json.loads(lines[1])
        row["extra"] = "not-allowed"
        lines[1] = canonical_json(row) + "\n"
    elif case == "oversized":
        lines[1] = "x" * 131073 + "\n"
    elif case == "episode":
        row = json.loads(lines[1])
        row["episode_public_id"] = "invalid"
        lines[1] = canonical_json(row) + "\n"
    else:
        lines.append(lines[-1])
    path.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(ValueError):
        read_trace(path)


@pytest.mark.parametrize(
    "case",
    ["proposal", "receipt", "mechanics", "terminal", "delivery", "authorization", "approval"],
)
def test_replay_semantic_consistency_even_if_chain_rewritten(tmp_path, captured, case):
    rows = list(read_trace(captured.trace_path))
    if case == "proposal":
        row = next(r for r in rows if r["kind"] == "PROPOSAL_ATTEMPT")
        row["payload"]["proposal"]["allocation"]["assignments"][0]["agent_id"] = "a2"
    elif case == "receipt":
        row = next(r for r in rows if r["kind"] == "ACTION")
        row["payload"]["observation"]["action_state"] = "Unknown"
    elif case == "mechanics":
        row = next(r for r in rows if r["kind"] == "MECHANICS")
        row["payload"]["outcome"]["regret"] = 10000
    elif case == "terminal":
        rows[-1]["payload"]["state_digest"] = "0" * 64
    elif case == "delivery":
        row = next(r for r in rows if r["kind"] == "DELIVERY")
        row["payload"]["delivery"]["delivered"] = ["a0"]
    elif case == "authorization":
        row = next(r for r in rows if r["kind"] == "AUTHORIZATION")
        row["payload"]["decision"] = "WITHHELD"
    else:
        row = next(r for r in rows if r["kind"] == "APPROVAL")
        row["payload"]["state"] = "Rejected"
    path = tmp_path / "semantic.jsonl"
    rewrite(path, rows)
    with pytest.raises((ValueError, KeyError)):
        replay_trace(path)


def test_missing_terminal_is_interrupted_not_complete(tmp_path, captured):
    path = tmp_path / "interrupted.jsonl"
    lines = captured.trace_path.read_bytes().splitlines(keepends=True)
    path.write_bytes(b"".join(lines[:-1]))
    replay = replay_trace(path)
    assert replay.status == "INTERRUPTED" and replay.record.state == captured.record.state
    assert replay.model_calls == replay.new_effects == 0
    assert replay.evidence.as_mapping()["harness"]["episode_status"] == "INTERRUPTED"


def test_writer_is_exclusive_and_terminal_closed(tmp_path):
    path = tmp_path / "trace.jsonl"
    writer = TraceWriter(path, "d6dd1a02-5135-4fd7-9844-2dd36366a68e")
    writer.append("CONFIG", {})
    writer.append("TERMINAL", {})
    with pytest.raises(ValueError):
        writer.append("MODEL_REQUEST", {})
    writer.close()
    with pytest.raises(FileExistsError):
        TraceWriter(path, writer.public_id)


def test_l1_l2_markers_and_real_tokens_excluded_from_l3(captured):
    marker = "PRIVATE_ASSIGNMENT_SEED_SPLIT_GROUP_BRIEF_ORACLE_TRUTH_MARKER"
    record = replace(
        captured.record,
        private_metadata={
            "condition": marker,
            "seed": marker,
            "nested": [{"private_briefs": marker}],
        },
        source_path=marker,
        manifest=object(),
        adjudication=replace(
            captured.record.adjudication, notes=(marker,), instruction_origin=marker
        ),
    )
    evidence = project_harness(
        record,
        captured.observations,
        captured.deliveries,
        public_id=captured.public_id,
        status=captured.status,
    )
    assert marker not in evidence.to_json()
    assert evidence.to_json() == captured.evidence().to_json()
    for store in captured.stores:
        for secret in (
            (store.path.parent / "capability").read_text("ascii"),
            store.identity["binding"]["execution_scope"],
            store.identity["subject_id"],
            str(store.path),
        ):
            assert secret not in evidence.to_json()
            assert secret not in captured.trace_path.read_text(encoding="utf-8")
    assert all(
        r["layer"] == "L1"
        for r in read_trace(captured.trace_path)
        if r["kind"] in ("CONFIG", "MODEL_REQUEST", "MODEL_RESPONSE")
    )
    assert '"private_briefs"' not in evidence.to_json()
    assert '"behavior_class"' not in evidence.to_json()


def test_independent_order_is_unknown_and_cannot_retain_shared_positions(captured):
    unknown_record = replace(captured.record, event_journal=None)
    unknown_actions = tuple(replace(o, logical_position=None) for o in captured.observations)
    unknown_deliveries = tuple(
        replace(d, attempt_position=None, delivery_position=None) for d in captured.deliveries
    )
    data = project_harness(
        unknown_record,
        unknown_actions,
        unknown_deliveries,
        public_id=captured.public_id,
        status=captured.status,
        shared_capture=False,
    ).as_mapping()
    assert data["event_ordering"]["status"] == "SOURCE_LOCAL_ONLY"
    assert data["harness"]["cross_source_order"] == "UNKNOWN"
    assert data["aig_execution"]["cross_source_order"] == "UNKNOWN"
    with pytest.raises(ValueError):
        project_harness(
            unknown_record,
            unknown_actions,
            captured.deliveries,
            public_id=captured.public_id,
            status=captured.status,
            shared_capture=False,
        )


def test_delivery_capture_rewrite_rejected(captured):
    deliveries = (
        replace(
            captured.deliveries[0], delivery_position=captured.deliveries[0].delivery_position + 1
        ),
        *captured.deliveries[1:],
    )
    with pytest.raises(ValueError, match="DELIVERY_CAPTURE"):
        project_harness(
            captured.record,
            captured.observations,
            deliveries,
            public_id=captured.public_id,
            status=captured.status,
        )
