"""One trusted proposal append; uncertainty never becomes inferred success."""

import re
from contextlib import closing
from uuid import uuid4

from agentic_intent_gate.runtime import EXTERNAL_PAYLOAD_REVISION, Outcome, ToolOutcome

from pactlens.aig.contract import ARGUMENT_SCHEMA, uuid4_text
from pactlens.aig.effect_store import StoreRejected
from pactlens.serialization import canonical_json, content_hash


async def no_fault(phase):
    """Trusted test injection seam; production execution performs no injected work."""


class ProposalExecutor:
    def __init__(self, store, binding, state, *, checkpoint=no_fault):
        self.store, self.binding, self.state = store, binding, state
        self.checkpoint = checkpoint
        self.calls = 0

    async def execute(self, spec, effect_key, context):
        self.calls += 1

        def outcome(category, receipt=None, reason=None):
            return ToolOutcome(
                category,
                effect_key,
                spec.execution_scope,
                spec.target,
                spec.payload_digest(),
                receipt,
                reason,
            )

        unknown = ToolOutcome(Outcome.UNKNOWN_OUTCOME)
        commit_attempted = False
        try:
            uuid4_text(effect_key)
            uuid4_text(context.attempt_id)
            args = dict(spec.arguments)
            if (
                not self.binding.matches(spec)
                or spec.identity_revision != EXTERNAL_PAYLOAD_REVISION
            ):
                raise ValueError("Untrusted identity")
            if set(args) != set(ARGUMENT_SCHEMA["properties"]):
                raise ValueError("Closed arguments required")
            for key, rule in ARGUMENT_SCHEMA["properties"].items():
                value = args[key]
                if rule["type"] == "integer":
                    if type(value) is not int or not rule["minimum"] <= value <= rule["maximum"]:
                        raise ValueError("Integer rejected")
                elif (
                    type(value) is not str
                    or not rule["minLength"] <= len(value) <= rule["maxLength"]
                    or re.fullmatch(rule["pattern"], value) is None
                ):
                    raise ValueError("String rejected")
        except (ValueError, TypeError, AttributeError):
            return outcome(Outcome.CONFIRMED_FAILURE, reason="INPUT_REJECTED")
        try:
            if context.expired():
                return unknown
            await self.checkpoint("before_dispatch")
            if context.expired():
                return unknown
            with closing(self.store.connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                self.store.check_identity(db)
                # Effect-key conflict is checked before resolving a new reference.
                row = db.execute(
                    "SELECT * FROM effects WHERE effect_key=?", (effect_key,)
                ).fetchone()
                if row:
                    if row["payload_digest"] != spec.payload_digest():
                        raise StoreRejected("PAYLOAD_CONFLICT")
                    saved = self.store.verified_row(db, row)
                    return outcome(Outcome.SUCCESS, receipt=saved.receipt_reference)
                prepared = self.store.resolve(db, args)
                if canonical_json(prepared.state) != canonical_json(self.state):
                    raise StoreRejected("INPUT_REJECTED")
                if db.execute(
                    "SELECT 1 FROM effects WHERE round_number=?", (prepared.proposal.round_number,)
                ).fetchone():
                    raise StoreRejected("PAYLOAD_CONFLICT")
                receipt = str(uuid4())
                spec_json = canonical_json(self.store.spec_body(spec))
                db.execute(
                    "INSERT INTO effects(effect_key,receipt,proposal_ref,payload_digest,spec_json,row_digest,round_number) VALUES(?,?,?,?,?,?,?)",
                    (
                        effect_key,
                        receipt,
                        prepared.reference,
                        spec.payload_digest(),
                        spec_json,
                        content_hash(
                            self.store.row_body(
                                effect_key, receipt, spec.payload_digest(), spec_json
                            )
                        ),
                        prepared.proposal.round_number,
                    ),
                )
                await self.checkpoint("before_commit")
                if context.expired():
                    return unknown  # connection close rolls back
                commit_attempted = True
                db.commit()
                # Any exception/cancellation from this point retains the committed effect.
                await self.checkpoint("after_commit")
                if context.expired():
                    return unknown
            with closing(self.store.connect()) as db:
                row = db.execute(
                    "SELECT * FROM effects WHERE effect_key=?", (effect_key,)
                ).fetchone()
                saved = self.store.verified_row(db, row)
            await self.checkpoint("before_ack")
            if context.expired():
                return unknown
            return outcome(Outcome.SUCCESS, receipt=saved.receipt_reference)
        except StoreRejected as error:
            if commit_attempted:
                return unknown
            return outcome(Outcome.CONFIRMED_FAILURE, reason=str(error))
        except Exception:  # noqa: BLE001 -- Storage/ack uncertainty must fail closed as Unknown.
            return unknown
