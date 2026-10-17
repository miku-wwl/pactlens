# PactLens Phase 2 — AIG Consumer Integration

Execution date: **2026-10-18 NZDT**, **pre-sprint engineering**.
Starting/current HEAD: `6a879bb3fb19d47332ae2aa7376ead4d12b57d90`, clean starting
tree on main, tracking/live HTTPS remote verified. Work is an uncommitted delta.

## Overall Status

**PASS** for the authorized local Phase 2 integration. Final **247 passed**
(164 existing + 83 new), no failures/skips/xfail. Real installed AIG services,
real SQLite effects and actual process interruption/recovery were exercised.
Planning and consent are synthetic engineering stand-ins. No claim of real LLM
collusion, authenticated human consent or production security is made.

No commit, push, tag, release, deployment, model inference, formal experiment,
detector, competition action or Phase 3 implementation was performed.

## Runtime Integration

Consumed installed `agentic-intent-gate==0.2.0` at immutable Git SHA
`7261fdd2f47d2b15fabe8faac527eeee37338eb1` through `agentic_intent_gate.runtime`
only. All **57** hashed RECORD files match; imports resolve inside this repo's
`.venv/Lib/site-packages`. Dependency config/lock and upstream source unchanged.
The [integration contract](PHASE2_INTEGRATION_CONTRACT.md) records inspected API
signatures/behavior and the upstream reference links.

Fixed ToolBinding: `submit_incident_proposal/1`, target `incident-sim`, adapter
`pactlens-sqlite-v1`, binding revision `proposal-v1`, fresh persisted actor-specific
UUIDv4 scope. Registry, capability, verifier, policy and store share this binding.
Each actor has independent Gate state, capability, subject and receipt-store
identity. Policy is `proposal-policy-v1`; default budget **5 seconds** is retained
by omitting the timeout argument. No extended profile exists.

The real ToolCapability uses six required flat bounded arguments: proposal_ref,
proposal_digest, task_hash, round_number, state_digest, expected_revision. Nested
allocations/extra authority fields are forbidden. Canonical immutable snapshots
are resolved locally; trusted host configuration chooses actor, task, scope,
executor and state view. A deterministic ModelProvider emits JSON, then the
actual AIG validator/risk gate validates and routes it.

New source: `aig/{__init__,contract,effect_store,executor,consumer,workflow}.py`,
`integration/{__init__,arena_bridge}.py`, `evidence/aig_adapter.py`. New tests:
seven `test_aig_*.py` modules and `aig_helpers.py`. Necessary conftest/source-guard
updates preserve offline tests and limit public AIG imports to the new package.
Updated README, ARCHITECTURE, DATA_DICTIONARY, PROVENANCE; three new Phase 2 docs.
All Arena mechanics and original evidence source remain byte-identical.

## Lifecycle Evidence

Actual path: Intent → real validated Plan → persistent AwaitingApproval Run →
explicit ApprovalDecisionRequest → Approved Run → AdmissionCommand/Pending
Action → separate ActionCommand Authorization → Authorized Action → durable
Gateway claim/Executing → consumer executor → verified SQLite receipt → Succeeded.
At a controlled executor barrier, a concurrent duplicate observes Executing;
only one executor call occurs. Identical completed commands replay durable state.

Missing/rejected/stale/other-Plan approval, mutation after approval, premature
admission, missing/stale/cross-Action authorization, wrong token/tool/target/
binding/scope and malformed arguments are rejected by real installed services,
not consumer-only mocked errors. Registry/actor/digest mismatches additionally
fail at the trusted consumer boundary. No private AIG database writes/reads or
monkeypatching were used. Safe Failed state omits detailed no-effect reason text;
the exact reason is independently asserted at the executor ToolOutcome port.

Current harness requires explicit `synthetic_consent=True`. Approval and
Authorization are separate real calls, but scripted test decisions. There is
no interactive approval UI, production login or implicit approval on composition.
Required predecessor-stop attestation is explicit and tested, not bypassed.

## Durability Evidence

Consumer-owned STRICT SQLite tables hold independent identity, immutable prepared
proposal/base-state snapshots and atomic effect/receipt rows. BEGIN IMMEDIATE,
unique effect keys/receipt UUIDs/actor-round slots, foreign keys and full sync
provide bounded local transaction behavior. Canonical AIG payload/spec, proposal,
base state, binding/store identity and receipt are recomputed and correlated.
Read verification precedes success acknowledgment. Normal updates/deletes fail;
deliberately corrupted receipt/snapshot fields fail verification.

- Same effect key + identical payload returns the original receipt, one effect.
- Different payload or duplicate committed actor/round slot fails without overwrite.
- Wrong store identity/input is proven no new effect; uncertainty returns Unknown.
- Before-commit cancellation rolls back the consumer row; Gateway records Unknown.
- Post-commit errors/lost acknowledgment leave one verified local row and Unknown.
- Actual subprocess exits cover before claim, before dispatch, before commit,
  after commit and after executor success evidence but before Gate finish.
- Success restart preserves Succeeded and receipt. Interrupted Executing becomes
  Unknown through AIG's recovery, without executor calls. Unclaimed Authorized
  remains Authorized and is not automatically dispatched.
- Original command replay on terminal state invokes no executor; a fresh execute
  command on terminal state is denied. No Unknown/Failed Action was reset.

Gate and consumer store are separate transactional domains, with no distributed
atomic commit. A receipt may independently be verified while the Action remains
Unknown; the collector preserves both facts. No row-existence-to-Action-success
reconciliation or automatic retry exists. Unkeyed hashes/triggers are consistency
checks, not cryptographic authenticity or malicious-host protection.

## Arena Integration

Two independently executed engineering examples use three isolated compositions
and six separately approved/authorized AIG Actions each. Verified durable effects
reproduce original Phase 1 fixtures exactly: **C+ J=12**, **C− J=6**. Each example
has six receipts, three distinct scopes and two committed proposals per actor.
Actual detached evidence is in `review/logs/integration-evidence.json`; these
names reference synthetic fixtures, not measured experimental conditions.

The bridge rereads verified rows and calls unchanged `submit_proposal` and
`close_round`. Exact prepared content, actor, round and base state/revision must
match. Final allocation always comes from Arena finalization. Reconstruction
from reversed store enumeration gives the same final state without another AIG
call. Receipt commit, Arena application, final allocation and cost computation
remain distinct events.

Logical dependency order comes from stored base revisions, not invented wall
clock order across SQLite stores. Duplicate identities/revisions or mismatched
snapshots stop reconstruction. Two agents can independently commit against the
same stale trusted view; a test confirms reconstruction rejects this conflict.
There is no distributed global Arena lock. An independently verified local effect
can support a mechanical projection while its AIG Action stays Unknown; this
does not establish a verified formal episode or authorize redispatch.

## Evidence Isolation

The separate adapter preserves all base Observation-v2 fields and adds explicit
`aig_execution` version `pactlens-aig-observation-v1`. Bounded detached records
allow neutral actor/round, real Action UUID/state/version, observed approval/
authorization status, payload/proposal digests, verified receipt reference/status,
synthetic-consent flag and supported ordering metadata. COMPLETE describes six
snapshots, not successful execution. Missing evidence remains explicit.

Research synthetic messages, AIG public state under local capabilities, verified
consumer commit and deterministic Arena costs carry different trust labels.
No capability token, raw authorization, subject/scope/store ID, private Gate
content/path, research condition/coalition/group/seed/split/brief, oracle optimum,
ground truth or adjudication enters L3. Existing 22-marker coverage remains;
new tests also check actual generated local tokens never appear.

The fixed harness captures Gateway completion/receipt before applying the
proposal and records both in a shared logical counter with Arena closures/costs.
Independent/legacy sources keep UNKNOWN cross-source order and null positions;
no retroactive AIG chronology is added to fixtures. R/MAE can later consume the
same observation inventory; no detector or privileged MAE-only record is built.
Detached snapshots/shared-clock claims remain trusted host inputs, not signatures.

## Testing

Python **3.13.14**. All commands below ran with **UV_OFFLINE=1**:

| Check | Actual result |
|---|---|
| `uv sync --locked` | PASS, 31 packages |
| `uv run pytest -q --junitxml=.runtime/phase2-validation/pytest.xml` | **247 passed in 105.78s**, zero failed/skipped/xfail |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS, 61 files already formatted |
| `uv lock --check --offline` | PASS, 31 packages |
| Source/test compilation | PASS |
| Installed AIG version/pin/import/RECORD | PASS, 0.2.0, exact SHA, site-packages, 57 hashes |
| Preserved starting files | PASS, 43 tracked files outside modification allowlist byte-identical |

[PHASE2_TEST_MATRIX.md](PHASE2_TEST_MATRIX.md) maps all 83 new cases and 164
retained cases to acceptance, including six real process boundaries. Windows
asyncio's stdlib socketpair IPC is permitted for event-loop wakeup; application
connections remain blocked and explicitly tested. Reference browsing was
read-only preflight, not a model/API execution. No model service or real third-
party mutation ran. Actual logs/JUnit are packaged; hostname/timestamp metadata
is removed from packaged JUnit, with results/durations unchanged.

Development failures from owner attestation, stdlib IPC, installed enum values
and safe terminal-result shape were corrected without weakening runtime gates.
An intermediate full suite passed 240 tests; the final suite includes seven more
boundary cases. No unresolved foundational failure or unavailable required
environment remains. Detailed development qualifications are in the test matrix.

## Remaining Risks and Next Phase

**GO for separately authorized Phase 3 — Controlled Multi-Agent Experimental
Harness.** Phase 3 was not started. Local integration passing does not verify
production human authentication, distributed serialization/HA, hostile-host
isolation, cryptographic history, external-provider effects, model behavior,
experimental feasibility or detector quality.

Current host state must be accurate; conflicting independent views fail closed
at replay rather than being globally serialized. Capabilities/filesystem access
are local trusted-host controls. Unknown remains terminal; manual inspection of
verified local receipts is not an automatic reconciliation engine. Core owner
attestation and default budget remain mandatory. No interactive human-consent
demo is claimed. The fixture catalog remains checkout-based rather than bundled
in the wheel. No distributed/durable cross-source capture log is implemented.

Formal pilot/calibration/held-out runs, model-driven agents, monitors, scoring,
independent human adjudication and dashboard remain **NOT RUN / unimplemented**.
The frozen 4/10/10 block allocation and 120 planned slots remain unchanged,
with **0 formal episodes executed**. All Phase 2 work is disclosed as prior work
before the October 23 sprint in additive PROVENANCE §6; historical reports remain.

## Review Artifact

`D:\workshop\oct\pactlens-phase2-review.zip`, outside the Git repository.
Contains source/tests, relevant docs, AGENTS/config/lock, actual verification
evidence, file SHA-256 manifest, snapshot verification receipt and standalone
archive verifier. CRC, all member checksums and source-byte consistency are
verified. A sibling final verification receipt records the final ZIP SHA-256;
the archive cannot contain its own self-referential hash.

No .git/.venv/.runtime directories, private SQLite files, capability credentials,
private research data, caches or previous review archives are included. The old
tracked Phase 1 ZIP remains untouched. Work stops after Phase 2.
