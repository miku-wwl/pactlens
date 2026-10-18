from uuid import uuid4

import pytest

from pactlens.experiments.traces import (
    KINDS,
    MAX_RECORD_BYTES,
    MAX_RECORDS,
    MAX_TRACE_BYTES,
    VERSION,
    TraceWriter,
    read_trace,
)
from pactlens.serialization import canonical_json, content_hash


def next_line(writer, kind, payload):
    body = {
        "schema_version": VERSION,
        "episode_public_id": writer.public_id,
        "sequence": writer.sequence + 1,
        "logical_position": writer.sequence + 1,
        "capture": "SHARED_HOST_OBSERVATION",
        "kind": kind,
        "layer": KINDS[kind],
        "trust": "EXPERIMENTER_OWNED_CAPTURE",
        "payload": payload,
        "previous": writer.previous,
    }
    return (canonical_json({**body, "digest": content_hash(body)}) + "\n").encode()


def fill_before_last(writer):
    while MAX_TRACE_BYTES - writer.bytes_written > 2 * MAX_RECORD_BYTES:
        overhead = len(next_line(writer, "MODEL_RESPONSE", {"padding": ""}))
        writer.append("MODEL_RESPONSE", {"padding": "x" * (MAX_RECORD_BYTES - overhead)})


def checkpoint(writer):
    return (
        writer.path.read_bytes(),
        writer.sequence,
        writer.previous,
        writer.terminal,
        writer.executor_calls,
        writer.bytes_written,
    )


def test_empty_trace_is_explicitly_incomplete_and_header_required(tmp_path):
    w = TraceWriter(tmp_path / "empty.jsonl", str(uuid4()))
    before = checkpoint(w)
    with pytest.raises(ValueError, match="TRACE_HEADER"):
        w.append("TERMINAL", {})
    assert checkpoint(w) == before
    w.close()
    with pytest.raises(ValueError, match="TRACE_HEADER"):
        read_trace(w.path)


def test_small_trace_hash_chain_and_cumulative_bytes(tmp_path):
    w = TraceWriter(tmp_path / "small.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    w.append("MODEL_RESPONSE", {"text": "\u6d4b\u8bd5"})
    w.append("TERMINAL", {})
    assert w.bytes_written == w.path.stat().st_size
    w.close()
    rows = read_trace(w.path)
    assert len(rows) == 3 and rows[-1]["kind"] == "TERMINAL"


@pytest.mark.parametrize("extra", [0, 1])
def test_exact_total_boundary_and_one_byte_over_are_atomic(tmp_path, extra):
    w = TraceWriter(tmp_path / "boundary.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    fill_before_last(w)
    # Split the remaining bytes so each independent line stays below its bound.
    overhead = len(next_line(w, "MODEL_RESPONSE", {"padding": ""}))
    w.append("MODEL_RESPONSE", {"padding": "x" * (MAX_RECORD_BYTES - overhead)})
    overhead = len(next_line(w, "TERMINAL", {"padding": ""}))
    padding = MAX_TRACE_BYTES - w.bytes_written - overhead
    before = checkpoint(w)
    if extra:
        with pytest.raises(ValueError, match="TRACE_TOTAL_BOUND"):
            w.append("TERMINAL", {"padding": "x" * (padding + 1)})
        assert checkpoint(w) == before
    w.append("TERMINAL", {"padding": "x" * padding})
    assert w.bytes_written == MAX_TRACE_BYTES
    w.close()
    assert read_trace(w.path)[-1]["kind"] == "TERMINAL"


def test_many_writer_appends_cannot_reproduce_old_8_point_6_mb_output(tmp_path):
    w = TraceWriter(tmp_path / "cumulative.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    while True:
        before = checkpoint(w)
        try:
            w.append("MODEL_RESPONSE", {"padding": "x" * 130000})
        except ValueError as error:
            assert str(error) == "TRACE_TOTAL_BOUND"
            assert checkpoint(w) == before
            break
    assert w.bytes_written <= MAX_TRACE_BYTES
    w.close()
    assert read_trace(w.path)[-1]["kind"] == "MODEL_RESPONSE"  # no manufactured terminal


def test_record_count_boundary_and_rejection_atomicity(tmp_path):
    w = TraceWriter(tmp_path / "records.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    for _ in range(MAX_RECORDS - 2):
        w.append("MODEL_RESPONSE", {})
    w.append("TERMINAL", {})
    before = checkpoint(w)
    with pytest.raises(ValueError, match="TRACE_STATE"):
        w.append("MODEL_RESPONSE", {})
    assert checkpoint(w) == before
    w.close()
    assert len(read_trace(w.path)) == MAX_RECORDS


def test_rejected_action_does_not_increment_accounting(tmp_path):
    w = TraceWriter(tmp_path / "action.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    before = checkpoint(w)
    with pytest.raises(ValueError, match="TRACE_RECORD_BOUND"):
        w.append("ACTION", {"executor_calls": 1, "padding": "x" * MAX_RECORD_BYTES})
    assert checkpoint(w) == before
    with pytest.raises(ValueError, match="TRACE_EXECUTOR_ACCOUNTING"):
        w.append("ACTION", {"executor_calls": True})
    assert checkpoint(w) == before
    w.close()


def test_reader_still_rejects_malformed_oversized_file(tmp_path):
    p = tmp_path / "hostile.jsonl"
    p.write_bytes(b"x" * (MAX_TRACE_BYTES + 1))
    with pytest.raises(ValueError, match="OVERSIZED"):
        read_trace(p)


def test_cumulative_action_overflow_leaves_accounting_and_terminal_space_intact(tmp_path):
    w = TraceWriter(tmp_path / "accounting-total.jsonl", str(uuid4()))
    w.append("CONFIG", {})
    fill_before_last(w)
    overhead = len(next_line(w, "MODEL_RESPONSE", {"padding": ""}))
    w.append("MODEL_RESPONSE", {"padding": "x" * (MAX_RECORD_BYTES - overhead)})
    overhead = len(next_line(w, "MODEL_RESPONSE", {"padding": ""}))
    w.append(
        "MODEL_RESPONSE", {"padding": "x" * (MAX_TRACE_BYTES - w.bytes_written - 500 - overhead)}
    )
    before = checkpoint(w)
    with pytest.raises(ValueError, match="TRACE_TOTAL_BOUND"):
        w.append("ACTION", {"executor_calls": 1, "padding": "x" * 1000})
    assert checkpoint(w) == before
    w.append("TERMINAL", {})
    w.close()
    assert read_trace(w.path)[-1]["kind"] == "TERMINAL"
