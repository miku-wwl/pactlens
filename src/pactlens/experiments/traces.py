"""Exclusive append-only, fsynced, bounded JSONL with unkeyed content chaining.

One trusted host captures positions explicitly. File ordering is not evidence of
unobserved provider/Gate transaction ordering. This is not authenticated history.
"""

import os
from pathlib import Path

from pactlens.agents.models import closed_json
from pactlens.evidence.projection import _public_id
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-research-trace-v1"
MAX_TRACE_BYTES = 8_000_000
MAX_RECORD_BYTES = 131_072
MAX_RECORDS = 256
KINDS = {
    "CONFIG": "L1",
    "MODEL_REQUEST": "L1",
    "MODEL_RESPONSE": "L1",
    "MODEL_FAILURE": "L1",
    "MESSAGE_ATTEMPT": "L3_SOURCE",
    "DELIVERY": "L3_SOURCE",
    "PROPOSAL_ATTEMPT": "L3_SOURCE",
    "VALIDATION": "L3_SOURCE",
    "RUN": "L3_SOURCE",
    "APPROVAL": "L3_SOURCE",
    "ADMISSION": "L3_SOURCE",
    "AUTHORIZATION": "L3_SOURCE",
    "ACTION": "L3_SOURCE",
    "ARENA": "L3_SOURCE",
    "PUBLIC_OUTCOME": "L3_SOURCE",
    "MECHANICS": "L2",
    "TERMINAL": "L3_SOURCE",
}


class TraceWriter:
    def __init__(self, path, public_id):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.public_id = _public_id(public_id)
        self.handle = self.path.open("xb")
        self.sequence = 0
        self.previous = "0" * 64
        self.terminal = False
        self.executor_calls = 0
        self.bytes_written = 0

    @property
    def next_position(self):
        return self.sequence + 1

    def append(self, kind, payload):
        if kind not in KINDS or self.terminal or self.sequence >= MAX_RECORDS:
            raise ValueError("TRACE_STATE")
        if self.sequence == 0 and kind != "CONFIG":
            raise ValueError("TRACE_HEADER")
        calls = 0
        if kind == "ACTION":
            if (
                type(payload) is not dict
                or type(payload.get("executor_calls")) is not int
                or not 0 <= payload["executor_calls"] <= 1
            ):
                raise ValueError("TRACE_EXECUTOR_ACCOUNTING")
            calls = payload["executor_calls"]
        body = {
            "schema_version": VERSION,
            "episode_public_id": self.public_id,
            "sequence": self.sequence + 1,
            "logical_position": self.next_position,
            "capture": "SHARED_HOST_OBSERVATION",
            "kind": kind,
            "layer": KINDS[kind],
            "trust": "EXPERIMENTER_OWNED_CAPTURE",
            "payload": payload,
            "previous": self.previous,
        }
        digest = content_hash(body)
        raw = (canonical_json({**body, "digest": digest}) + "\n").encode("utf-8")
        if len(raw) > MAX_RECORD_BYTES:
            raise ValueError("TRACE_RECORD_BOUND")
        if self.bytes_written + len(raw) > MAX_TRACE_BYTES:
            raise ValueError("TRACE_TOTAL_BOUND")
        self.handle.write(raw)
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.sequence += 1
        self.previous = digest
        self.bytes_written += len(raw)
        self.terminal = kind == "TERMINAL"
        self.executor_calls += calls
        return body["logical_position"]

    def close(self):
        self.handle.close()


def read_trace(path):
    rows = []
    previous = "0" * 64
    size = 0
    with Path(path).open("rb") as handle:
        while raw := handle.readline(MAX_RECORD_BYTES + 1):
            size += len(raw)
            if (
                len(raw) > MAX_RECORD_BYTES
                or not raw.endswith(b"\n")
                or size > MAX_TRACE_BYTES
                or len(rows) >= MAX_RECORDS
            ):
                raise ValueError("TRUNCATED_OR_OVERSIZED_TRACE")
            row = closed_json(raw.decode("utf-8"), MAX_RECORD_BYTES)
            if type(row) is not dict or set(row) != {
                "schema_version",
                "episode_public_id",
                "sequence",
                "logical_position",
                "capture",
                "kind",
                "layer",
                "trust",
                "payload",
                "previous",
                "digest",
            }:
                raise ValueError("TRACE_FIELDS")
            digest = row.pop("digest")
            if (
                row["schema_version"] != VERSION
                or row["sequence"] != len(rows) + 1
                or type(row["sequence"]) is not int
                or row["logical_position"] != row["sequence"]
                or type(row["logical_position"]) is not int
                or row["capture"] != "SHARED_HOST_OBSERVATION"
                or row["trust"] != "EXPERIMENTER_OWNED_CAPTURE"
                or row["kind"] not in KINDS
                or row["layer"] != KINDS[row["kind"]]
                or row["previous"] != previous
                or content_hash(row) != digest
                or canonical_json({**row, "digest": digest}).encode("utf-8") + b"\n" != raw
                or (rows and rows[-1]["kind"] == "TERMINAL")
            ):
                raise ValueError("TRACE_CHAIN")
            _public_id(row["episode_public_id"])
            if rows and row["episode_public_id"] != rows[0]["episode_public_id"]:
                raise ValueError("TRACE_EPISODE")
            previous = digest
            rows.append(row)
    if not rows or rows[0]["kind"] != "CONFIG":
        raise ValueError("TRACE_HEADER")
    return tuple(rows)
