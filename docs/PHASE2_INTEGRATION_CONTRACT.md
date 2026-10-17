# Phase 2 — Local AIG Consumer Contract

Implemented **2026-10-18 NZDT, pre-sprint engineering**. This is a fixed synthetic
incident-proposal integration with installed AIG 0.2.0, not a model-driven agent,
research experiment, generic execution framework or production authentication.

## External runtime and public API

Distribution `agentic-intent-gate==0.2.0`, Git source
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`, imported from installed site-packages.
No upstream source or private Gate tables are used as a consumer shortcut.
References inspected: [repository](https://github.com/miku-wwl/agentic-intent-gate),
[handoff](https://github.com/miku-wwl/agentic-intent-gate/blob/main/docs/V0.2.0-CONSUMER-HANDOFF.md),
[v0.2.0 adapter guide](https://github.com/miku-wwl/agentic-intent-gate/blob/v0.2.0/docs/ADAPTER_GUIDE.md),
[reference consumer](https://github.com/miku-wwl/agentic-intent-gate/blob/main/examples/consumer/app.py).
Installed signatures/behavior govern implementation rather than moving main.

Imports exclusively use `agentic_intent_gate.runtime`: ToolBinding,
ToolCapability, ExecutableRegistry, CapabilityVerifier, BoundCapabilityAuthorization,
open_runtime, provision_capability, Intent, ApprovalChoice,
ApprovalDecisionRequest, AdmissionCommand, ActionCommand, ExecutionSpec,
EXTERNAL_PAYLOAD_REVISION, Outcome and ToolOutcome. Tests also use AttemptContext
to qualify the executor port independently. Public Runtime services used are
`run_service.create/get/decide`, `gateway.admit/authorize/execute/get/list_for_run`.
The approved-Plan rewrite negative test calls the exposed Run repository's
`save_validated_plan`, which correctly rejects a write after approval.

## Frozen trusted binding and lifecycle

| Binding field | Value |
|---|---|
| tool_name / tool_version | `submit_incident_proposal` / `1` |
| target | `incident-sim` |
| adapter_id | `pactlens-sqlite-v1` (existing documented identity retained) |
| binding_revision | `proposal-v1` (first implemented reviewed revision) |
| execution_scope | fresh UUIDv4 on explicit provisioning; persisted for that actor/task/store |

Each composition registers exactly this one SIDE_EFFECT tool with the same
binding in capability, registry, verifier, authorization policy and consumer
store. Policy revision is `proposal-policy-v1`. Actor, task hash, subject ID,
scope and independent store UUID live in persisted host identity. Three actors
have distinct private Gate files, tokens, subjects, scopes and effect stores.
Changing actor/ref in Plan input cannot select another composition's authority.

`consumer()` omits execution_timeout_seconds and accepts no budget argument:
the AIG default **5 seconds** applies. No extended profile is created. AIG owns
Run validation, risk gate, exact approval binding, admission, authorization,
claims, command idempotency, terminal state, owner fence and recovery. No consumer
replacement is implemented. `predecessor_stopped=True` is required even for a
fresh isolated directory; it is an explicit trusted caller attestation, never a
process-stopping operation. The harness uses new directories and closes each
context before reopening that actor for round 2.

Sequence: prepare/freeze → deterministic provider JSON → actual AIG schema,
semantic and risk validation → persistent AwaitingApproval Run → explicit
ApprovalDecisionRequest → Approved Run → AdmissionCommand → Pending Action →
separate ActionCommand authorization → Authorized Action → Gateway execute →
durable Executing claim → trusted executor → verified SQLite effect/receipt →
Gateway terminal result. One Action records one proposal, never an entire round.

Current automated workflows require `synthetic_consent=True` and record that
fact. Scripted test Approval and Authorization are separate real AIG calls;
neither is authenticated human consent. No interactive UI/CLI consent workflow
or production login is supplied. Library composition alone approves nothing.

## Flat closed input schema and proposal preparation

All six fields required; additional properties, nested allocations and authority
fields forbidden. The schema is bounded and supplied to real ToolCapability:

| Argument | Bounds / binding |
|---|---|
| proposal_ref | canonical UUIDv4, length 36; immutable local registry row |
| proposal_digest | 64 lowercase SHA-256 hex characters of canonical full Proposal |
| task_hash | 64 lowercase SHA-256 hex characters, exact trusted public task |
| round_number | exact integer 1–2, no bool/coercion |
| state_digest | 64 lowercase SHA-256 hex characters of frozen public base ArenaState |
| expected_revision | exact integer 1–8, same frozen base state revision |

Consumer preparation caps canonical Proposal at 4,096 UTF-8 bytes and base-state
snapshot at 65,536 bytes, without changing Arena domain limits.

Preparing invokes the original `submit_proposal` as a dry validation and discards
the resulting state: actor/round/task, slot, feasibility and lifecycle must already
be valid. A new opaque proposal reference and canonical Proposal/base-state JSON
are persisted with canonical arguments. Snapshot UPDATE/DELETE is normally
blocked by SQLite triggers. Changing content requires a new reference/Plan and
fresh approval. The provider emits no credentials, binding, scope or executor
choice. It is not an LLM; AIG still validates its output and selects the risk gate.

The executor checks full binding/payload revision `tool-payload-v1`, all argument
types/bounds, effect/attempt UUIDs, store identity, complete snapshot reconstruction,
proposal digest, actor/task/round/base revision and Plan arguments. Snapshot
restore uses validated original domain constructors plus exact canonical roundtrip;
unknown fields or corrupted content are not silently accepted. For a new effect,
the prepared base state must equal the trusted host's current public state view.
An existing identical effect key is verified as an idempotent read even after
that view advances. No model/client input controls the trusted state view.

Snapshots survive restart in the independent proposal store; they are bounded
data, not serialized Python code or mutable authorization. Host configuration
and filesystem integrity remain trusted. Triggers/unkeyed digests are consistency
guards, not signatures or protection against a host rewriting all correlated data.

## Independent SQLite effects and receipt verification

The sole tool effect appends one immutable proposal effect in PactLens-owned
SQLite. `identity`, `prepared`, `effects` are STRICT tables. Identity is singleton;
effect key and receipt are unique UUIDv4 strings, proposal references are foreign
keys, round is constrained to 1/2 and unique per fixed actor/task composition.
Writes use BEGIN IMMEDIATE, foreign keys and synchronous=FULL. Runtime Gate and
consumer store are separate files and separate transactions.

An effects row atomically contains effect key, unique durable receipt, proposal
reference, AIG payload digest, complete canonical execution-spec JSON, local
sequence, round and a consistency digest bound to store identity. Verification
recomputes the AIG payload digest over all binding fields/arguments, restores
the exact prepared proposal/state, checks row/UUID/correlation fields and matches
the recorded receipt. Success is returned only after commit and read verification.
The local sequence orders that store's rows, not other actors' commits.

| Situation | Executor / Gateway behavior |
|---|---|
| Same effect key, identical payload | Verify original row and return original receipt; no new proposal |
| Same effect key, different payload | CONFIRMED_FAILURE / PAYLOAD_CONFLICT; no overwrite |
| Different Action for already committed actor/round slot | CONFIRMED_FAILURE / PAYLOAD_CONFLICT |
| Wrong expected store/binding identity | Deny before mutation; store mismatch uses STORE_IDENTITY_MISMATCH |
| Provably malformed/unbound input | CONFIRMED_FAILURE / INPUT_REJECTED |
| Timeout/cancellation/error/uncertain commit or acknowledgment | Unknown; no automatic retry/read-back-to-success |

AIG persists a safe Failed classification, not the executor's detailed no-effect
reason text. Tests verify the precise reason at the ToolOutcome port and the
actual durable Failed state through Gateway. Missing/corrupted receipts never
become verified L3 success. A public Succeeded Action must match its consumer
receipt. Unknown can independently have a VERIFIED_COMMITTED local receipt;
that observation never changes the AIG Action state.

## Failure and restart boundaries

| Failure point | Durable observation / recovery |
|---|---|
| After Authorization, before Gateway claim | Authorized remains; open does not dispatch it |
| After claim, before dispatch | Interrupted Executing recovers to Unknown, zero effects |
| During transaction, before commit | SQLite rolls back; AIG interrupted Action becomes Unknown |
| After consumer commit, before acknowledgment | Effect/receipt may exist; Action Unknown, no redispatch |
| After executor success evidence, before Gate finish | Separate Gate transaction can be interrupted; recovery Unknown with original receipt retained |
| After confirmed success, restart | Succeeded and receipt unchanged; identical command replays without executor |

No distributed atomic commit, universal exactly-once guarantee or consumer recovery
engine is claimed. AIG's existing open-time recovery handles its interrupted
Actions with predecessor-stop attestation. The executor performs no recovery
replay. Command keys, Action IDs, effect keys and receipt IDs are different
identities; a grant/idempotency key from another Action does not authorize it.
Deterministic checkpoints and actual subprocess exits test these windows without
sleep-based scheduling. Test executor subclasses are explicitly registered host
fault injection, never runtime monkeypatches or Plan-selected code.

## Arena bridge and evidence

`apply_committed` rereads/verifies the durable row and requires the exact base
state/revision before calling original `submit_proposal`. `reconstruct` reads
verified stores, orders application dependencies by recorded base revision,
uses `close_round` at the round boundary and optionally finalizes. This order is
logical dependency order, not invented cross-store commit chronology. Duplicate
effects, duplicate base revisions/slots and mismatched content fail closed.
The final allocation comes exclusively from unchanged Arena finalization.

Receipt commit, local Arena application, final allocation and mechanical outcome
are separate events. An Arena projection crash is repaired by replaying verified
local rows, never reissuing an AIG side effect. Unknown Actions remain Unknown
even where a local receipt independently supports a mechanical reconstruction;
this does not establish a verified formal research episode. Two independent
actors can commit against the same stale host view; reconstruction rejects their
conflicting base revisions. Phase 2 supplies no distributed global Arena lock.

The six-submission harness sequentially captures real Gateway completion/receipt,
then Arena application, closures and public costs in a shared logical counter.
The separate evidence adapter retains all base Observation-v2 fields and adds
one explicit execution extension; see [DATA_DICTIONARY.md](DATA_DICTIONARY.md).
Independent/legacy captures keep cross-source order unknown. Different trust
labels separate messages, AIG state, consumer receipts and Arena accounting.
R/MAE must later consume the same inventory; no monitor is implemented.

Local bearer credentials, trusted Python hosts, SQLite access and unkeyed hashes
are not production authentication, malicious-host isolation or cryptographic
authenticity. This is sandbox-only synthetic engineering. No real tracker,
payment, model inference, formal study, detector or Phase 3 is involved.
