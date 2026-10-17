"""Consumer SQLite domain, separate from the AIG Gate transaction and credentials."""

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from agentic_intent_gate.runtime import EXTERNAL_PAYLOAD_REVISION, ExecutionSpec

from pactlens.aig.contract import PreparedProposal, _proposal, restore_state, uuid4_text
from pactlens.serialization import canonical_json, content_hash


class StoreRejected(ValueError):
    """Proven no new effect, with an AIG-recognized safe reason."""


@dataclass(frozen=True)
class CommittedProposal:
    store_id: str
    sequence: int
    effect_key: str
    payload_digest: str
    receipt_reference: str
    prepared: PreparedProposal


class ProposalStore:
    def __init__(self, path, identity):
        self.path = Path(path)
        # Defensive immutable serialized copy; configuration contains no credential.
        self.identity_json = canonical_json(identity)

    @property
    def identity(self):
        return json.loads(self.identity_json)

    def connect(self):
        db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=rw", uri=True, timeout=0.2)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @staticmethod
    def provision(path, identity):
        Path(path).touch(exist_ok=False)
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""
                CREATE TABLE identity(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    body TEXT NOT NULL) STRICT;
                CREATE TABLE prepared(reference TEXT PRIMARY KEY NOT NULL CHECK(length(reference)=36),
                    proposal_json TEXT NOT NULL, state_json TEXT NOT NULL,
                    arguments_json TEXT NOT NULL) STRICT;
                CREATE TABLE effects(sequence INTEGER PRIMARY KEY,
                    effect_key TEXT UNIQUE NOT NULL CHECK(length(effect_key)=36),
                    receipt TEXT UNIQUE NOT NULL CHECK(length(receipt)=36),
                    proposal_ref TEXT NOT NULL REFERENCES prepared(reference),
                    payload_digest TEXT NOT NULL CHECK(length(payload_digest)=64),
                    spec_json TEXT NOT NULL, row_digest TEXT NOT NULL,
                    round_number INTEGER NOT NULL CHECK(round_number IN (1,2)),
                    UNIQUE(round_number)) STRICT;
            """)
            db.execute("INSERT INTO identity VALUES(1,?)", (canonical_json(identity),))
            for table in ("identity", "prepared", "effects"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(
                        f"CREATE TRIGGER immutable_{table}_{operation} BEFORE {operation} ON {table} "
                        "BEGIN SELECT RAISE(ABORT, 'IMMUTABLE'); END"
                    )
            db.commit()

    def check_identity(self, db):
        rows = db.execute("SELECT body FROM identity WHERE singleton=1").fetchall()
        if [row[0] for row in rows] != [self.identity_json]:
            raise StoreRejected("STORE_IDENTITY_MISMATCH")

    def prepare(self, state, proposal):
        identity = self.identity
        prepared = PreparedProposal(str(uuid4()), state, proposal)
        if proposal.agent_id != identity["actor_id"] or proposal.task_hash != identity["task_hash"]:
            raise ValueError("Proposal outside trusted actor/task")
        with closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self.check_identity(db)
            db.execute(
                "INSERT INTO prepared VALUES(?,?,?,?)",
                (
                    prepared.reference,
                    canonical_json(proposal),
                    canonical_json(state),
                    canonical_json(prepared.arguments),
                ),
            )
            db.commit()
        return prepared

    def resolve(self, db, arguments):
        reference = arguments["proposal_ref"]
        uuid4_text(reference)
        row = db.execute("SELECT * FROM prepared WHERE reference=?", (reference,)).fetchone()
        if row is None:
            raise StoreRejected("INPUT_REJECTED")
        state = restore_state(row["state_json"])
        proposal = _proposal(json.loads(row["proposal_json"]))
        prepared = PreparedProposal(reference, state, proposal)
        if (
            canonical_json(proposal) != row["proposal_json"]
            or canonical_json(prepared.arguments) != row["arguments_json"]
            or canonical_json(arguments) != row["arguments_json"]
            or proposal.agent_id != self.identity["actor_id"]
            or proposal.task_hash != self.identity["task_hash"]
        ):
            raise StoreRejected("INPUT_REJECTED")
        return prepared

    @staticmethod
    def spec_body(spec):
        return {
            "tool_name": spec.tool_name,
            "tool_version": spec.tool_version,
            "adapter_id": spec.adapter_id,
            "binding_revision": spec.binding_revision,
            "target": spec.target,
            "execution_scope": spec.execution_scope,
            "identity_revision": spec.identity_revision,
            "arguments": dict(spec.arguments),
        }

    def verified_row(self, db, row):
        self.check_identity(db)
        spec = ExecutionSpec(**json.loads(row["spec_json"]))
        from pactlens.aig.contract import binding_for

        binding = binding_for(self.identity["binding"]["execution_scope"])
        if (
            not binding.matches(spec)
            or self.identity["binding"] != vars(binding)
            or spec.identity_revision != EXTERNAL_PAYLOAD_REVISION
            or spec.payload_digest() != row["payload_digest"]
            or canonical_json(self.spec_body(spec)) != row["spec_json"]
        ):
            raise ValueError("Receipt correlation mismatch")
        prepared = self.resolve(db, dict(spec.arguments))
        uuid4_text(row["effect_key"])
        uuid4_text(row["receipt"])
        body = self.row_body(
            row["effect_key"], row["receipt"], row["payload_digest"], row["spec_json"]
        )
        if (
            row["row_digest"] != content_hash(body)
            or row["proposal_ref"] != prepared.reference
            or row["round_number"] != prepared.proposal.round_number
        ):
            raise ValueError("Receipt content mismatch")
        return CommittedProposal(
            self.identity["store_id"],
            row["sequence"],
            row["effect_key"],
            row["payload_digest"],
            row["receipt"],
            prepared,
        )

    def row_body(self, key, receipt, digest, spec_json):
        return {
            "store_id": self.identity["store_id"],
            "effect_key": key,
            "receipt": receipt,
            "payload_digest": digest,
            "spec_json": spec_json,
        }

    def committed(self):
        with closing(self.connect()) as db:
            self.check_identity(db)
            return tuple(
                self.verified_row(db, row)
                for row in db.execute("SELECT * FROM effects ORDER BY sequence")
            )
