"""Versioned diagnostics around the original strict parser, without repairs."""

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from pactlens.agents.models import closed_json, parse_decision
from pactlens.arena.allocation import InfeasibleAllocation
from pactlens.evidence.records import Channel
from pactlens.serialization import content_hash

LEGACY_PROTOCOL = "pactlens-decision-v1"
CANDIDATE_PROTOCOL = "pactlens-decision-v2-candidate"
DIAGNOSTIC_VERSION = "pactlens-protocol-diagnostic-v1"
FIELDS = {"actor_id", "round_number", "task_hash", "decision", "assignments", "message", "end_step"}
PROTOCOL_HASH = content_hash(
    {
        "version": CANDIDATE_PROTOCOL,
        "fields": sorted(FIELDS),
        "response_bytes": 4096,
        "message_chars": 256,
        "routing": "known-other-actors-public-broadcast-private-single-intent",
    }
)


class Code(StrEnum):
    VALID = "VALID_SUBMISSION"
    DECLINE = "EXPLICIT_DECLINE"
    JSON = "INVALID_JSON"
    FIELDS = "FIELD_SET_MISMATCH"
    TYPE = "WRONG_FIELD_TYPE"
    ASSIGNMENTS = "INVALID_ASSIGNMENTS"
    INFEASIBLE = "INFEASIBLE_ASSIGNMENTS"
    ACTOR = "WRONG_ACTOR"
    ROUND = "WRONG_ROUND"
    TASK = "WRONG_TASK"
    ROUTING = "INVALID_MESSAGE_ROUTING"
    OUTPUT = "OUTPUT_BUDGET_EXCEEDED"
    INPUT = "INPUT_BUDGET_EXCEEDED"
    TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER = "PROVIDER_FAILURE"
    AIG = "AIG_SUBMISSION_FAILURE"
    INCOMPLETE = "INCOMPLETE_RESPONSE"


@dataclass(frozen=True)
class Diagnostic:
    code: Code
    protocol_version: str
    response_digest: str | None = None
    schema_version: str = DIAGNOSTIC_VERSION

    @property
    def ok(self):
        return self.code in (Code.VALID, Code.DECLINE)


class ProtocolRejected(ValueError):
    def __init__(self, diagnostic):
        super().__init__(diagnostic.code.value)
        self.diagnostic = diagnostic


def exception_diagnostic(error, *, protocol_version, response_digest=None, stage="MODEL"):
    if isinstance(error, ProtocolRejected):
        return error.diagnostic
    text = str(error)
    if stage == "AIG":
        code = Code.AIG
    elif isinstance(error, TimeoutError):
        code = Code.TIMEOUT
    elif isinstance(error, json.JSONDecodeError) or text == "DUPLICATE_KEY":
        code = Code.JSON
    elif text in ("RESPONSE_BOUND", "OUTPUT_BUDGET_EXCEEDED"):
        code = Code.OUTPUT
    elif text in ("INPUT_BUDGET_EXCEEDED", "ACTUAL_INPUT_BUDGET_EXCEEDED", "CONTEXT_OVERFLOW"):
        code = Code.INPUT
    elif isinstance(error, InfeasibleAllocation):
        code = (
            Code.ASSIGNMENTS
            if text in ("WRONG_INCIDENT_SET", "UNKNOWN_ASSIGNEE")
            else Code.INFEASIBLE
        )
    elif text.startswith(("MESSAGE", "'private'", "'public'")):
        code = Code.ROUTING
    elif "ASSIGNMENT" in text or text in ("INVALID_ALLOCATION_TYPE", "INVALID_IDENTIFIER"):
        code = Code.ASSIGNMENTS
    elif text == "DECISION_FIELDS":
        code = Code.FIELDS
    elif text == "DECISION_CONTEXT":
        code = Code.INCOMPLETE
    elif isinstance(error, (TypeError, UnicodeError)) or text == "INTEGER_OUT_OF_BOUNDS":
        code = Code.TYPE
    else:
        code = Code.PROVIDER
    return Diagnostic(code, protocol_version, response_digest)


def parse_versioned(raw, *, state, actor_id, protocol_version=LEGACY_PROTOCOL):
    if protocol_version == LEGACY_PROTOCOL:
        return parse_decision(raw, state=state, actor_id=actor_id)
    if protocol_version != CANDIDATE_PROTOCOL:
        raise ValueError("UNREVIEWED_PROTOCOL_VERSION")
    digest = hashlib.sha256(str(raw).encode("utf-8", errors="backslashreplace")).hexdigest()

    def reject(code):
        raise ProtocolRejected(Diagnostic(code, protocol_version, digest))

    if type(raw) is not str:
        reject(Code.TYPE)
    try:
        if len(raw.encode("utf-8")) > 4096:
            reject(Code.OUTPUT)
        body = closed_json(raw)
    except ProtocolRejected:
        raise
    except (ValueError, UnicodeError, RecursionError):
        reject(Code.JSON)
    if type(body) is not dict:
        reject(Code.TYPE)
    if set(body) != FIELDS:
        reject(Code.FIELDS)
    if (
        any(type(body[k]) is not str for k in ("actor_id", "task_hash", "decision"))
        or type(body["round_number"]) is not int
        or type(body["end_step"]) is not bool
    ):
        reject(Code.TYPE)
    if body["actor_id"] != actor_id:
        reject(Code.ACTOR)
    if body["round_number"] != state.round_number:
        reject(Code.ROUND)
    if body["task_hash"] != state.task.task_hash:
        reject(Code.TASK)
    if not body["end_step"] or body["decision"] not in ("submit", "decline"):
        reject(Code.INCOMPLETE)
    if body["decision"] == "decline" and body["assignments"] is not None:
        reject(Code.ASSIGNMENTS)
    if body["decision"] == "submit":
        rows = body["assignments"]
        if type(rows) is not list or not 3 <= len(rows) <= 5:
            reject(Code.ASSIGNMENTS)
        for row in rows:
            if type(row) is not dict:
                reject(Code.TYPE)
            if set(row) != {"incident_id", "agent_id"}:
                reject(Code.FIELDS)
            if type(row["incident_id"]) is not str or (
                row["agent_id"] is not None and type(row["agent_id"]) is not str
            ):
                reject(Code.TYPE)
    message = body["message"]
    if message is not None:
        if type(message) is not dict:
            reject(Code.TYPE)
        if set(message) != {"channel", "recipients", "text"}:
            reject(Code.FIELDS)
        if (
            type(message["recipients"]) is not list
            or any(type(a) is not str for a in message["recipients"])
            or type(message["text"]) is not str
            or type(message["channel"]) is not str
        ):
            reject(Code.TYPE)
        audience = set(message["recipients"])
        peers = {a.agent_id for a in state.task.agents} - {actor_id}
        if (
            not audience
            or len(audience) != len(message["recipients"])
            or not audience <= peers
            or message["channel"] not in (Channel.PUBLIC, Channel.PRIVATE)
            or (message["channel"] == Channel.PUBLIC and audience != peers)
            or (message["channel"] == Channel.PRIVATE and len(audience) != 1)
        ):
            reject(Code.ROUTING)
    try:
        return parse_decision(raw, state=state, actor_id=actor_id)
    except (ValueError, TypeError) as error:
        diagnostic = exception_diagnostic(
            error, protocol_version=protocol_version, response_digest=digest
        )
        if diagnostic.code == Code.PROVIDER:
            diagnostic = Diagnostic(Code.ASSIGNMENTS, protocol_version, digest)
        raise ProtocolRejected(diagnostic) from error
