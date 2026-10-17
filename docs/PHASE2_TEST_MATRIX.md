# Phase 2 — Integration Acceptance and Test Matrix

Execution: **2026-10-18 NZDT, pre-sprint engineering**. Final result:
**247 passed**, 0 failed/skipped/xfail. This retains all 164 Phase 1.1 cases
and adds 83 Phase 2 cases. Tests are not research observations or human review.
Actual JUnit, logs and detached integration evidence are included in the review.

## Executed cases

| Module | Cases | Scope |
|---|---:|---|
| test_aig_consumer_contract | 4 | Real installed lifecycle, verified receipt, default 5 seconds, exact command replay, required owner attestation, outbound-connection guard, bounded snapshot input |
| test_aig_approval_authorization | 21 | Missing/rejected/stale/other-Plan approval, immutable approved Plan, stale admission/Action, missing/cross-Action authorization, wrong token, seven real Plan validation failures, four startup/Gateway binding mismatches |
| test_aig_effect_store | 22 | Same-key same-payload receipt, conflicting payload, seven executor identity checks, six valid-schema registry/digest/revision failures through Gateway, wrong store, immutable stage, duplicate slot, changed approved snapshot, four corrupted receipt fields |
| test_aig_recovery | 19 | Four error/ack-loss checkpoints, expired caller deadline, executor timeout, cancellation before commit, concurrent duplicate command, five mismatched receipt correlations, six real process exit/restart boundaries |
| test_aig_three_agent_isolation | 3 | Independent compositions/principals/tokens, foreign-actor stage/ref rejection, persistent identity and incompatible store denial |
| test_aig_arena_bridge | 5 | Six real Actions for each C+/C− engineering fixture, costs 12/6, deterministic reconstruction, no duplicate application, durable-row/revision checks, explicit synthetic consent, cross-store conflicting base revisions |
| test_aig_evidence_projection | 9 | Explicit public allowlist/trust labels, shared vs unknown capture, real credential/private marker isolation, four contradictory correlation cases, missing evidence, round-boundary capture rejection |
| Existing arena determinism/outcomes/state integrity | 93 | Original 45 + 25 + 23 cases, unchanged mechanics |
| Existing event order/leakage/fixtures/splits | 71 | Original 22 + 12 + 26 + 11 cases |
| **Total** | **247** | **164 original + 83 new** |

## Acceptance evidence

| Requirement | Actual evidence / qualification |
|---|---|
| Immutable installed AIG dependency | version/source/site-packages checks; 57 RECORD hashes; config/lock unchanged |
| Validated Plan and persistent Run | real RunService reaches AwaitingApproval; malformed provider output produces PlanRejected / PLAN_VALIDATION_ERROR |
| Exact Plan Approval | other-reference Plan's approved Run cannot admit an unapproved Run; approved-Plan rewrite rejected by exposed repository; missing/rejected approval rejected |
| Independent Authorization | Pending Action execute rejected; foreign Action's authorization/key does not authorize another Pending Action |
| Durable Gateway claim and one dispatch | at an executor barrier, duplicate command returns durable Executing; only one executor call and one receipt |
| SQLite effect and correlated receipt | real commit/read verification; complete key/spec/identity/content correlation; unique receipt and round slot |
| Idempotency/conflict | same effect key returns exact original receipt; changed payload fails; distinct authorized Action cannot duplicate one slot |
| Wrong actor/tool/target/binding/scope/capability | core validation/composition/Gateway denials plus consumer registry/executor checks, zero effects |
| Default five-second budget | actual Gateway configuration equals 5; no extended binding/API argument |
| Timeout/cancellation/lost ack | deterministic fault seams and real SQLite rollback/commit; durable Unknown; no sleep-based race |
| Restart after success | fresh interpreter reads same Succeeded/receipt; command replay has zero executor calls |
| Restart interrupted execution | actual process exits before dispatch, before commit, after commit and after executor evidence; AIG recovery Unknown without executor |
| Before-claim restart | Authorized is preserved and observed without dispatch |
| Terminal no-retry | exact command replays state only; new execution command on terminal Action rejected as EXECUTION_ALREADY_STARTED |
| Three-agent isolation | distinct scope/store/subject/Gate/capability identities; cross-principal denied before dispatch |
| Arena integration | original functions only; exact base state/revision; known fixture final states/outcomes match; replay issues no AIG calls |
| No fabricated global order | legacy null positions, explicit UNKNOWN cross-source order, shared capture only with recorded Arena positions |
| L3/secret isolation | original 22 private markers plus new nested metadata/path/actual test-token exclusion; no raw AIG objects, scope/subject/grants/store ID or oracle values |
| No premature research/Phase 3 | fixed six-submission harness only; no model/network/orchestrator imports; formal slots still unexecuted |

## Test environment and development corrections

All required uv checks run with UV_OFFLINE=1. Application socket connections
remain blocked. On Windows, asyncio's standard-library socketpair creates its
internal local wakeup channel; the fixture permits that synchronous stdlib call,
then restores the outbound guard. A dedicated test still rejects connections to
Ollama's loopback port and an external destination. Subprocess tests execute
only deterministic installed consumer code; no model/client exists in it.

The source-import guard was updated for the authorized Phase 2 scope: only the
`aig/` package may import `agentic_intent_gate.runtime`; private/core imports and
network/model/orchestrator imports remain disallowed. Original Arena/evidence
files and all numerical expected fixture results remain unchanged.

Development uncovered missing owner attestation and the Windows asyncio IPC
interaction. Tests also initially assumed symbolic enum names instead of actual
wire values and expected detailed no-effect reason text in the public terminal
result. Assertions now follow the inspected installed API: PlanRejected,
RUN_NOT_ACTION_ELIGIBLE, ACTION_NOT_EXECUTABLE, and safe Failed classification.
Precise consumer reasons are tested at the ToolOutcome port; no core guard was
weakened or outcome fabricated. An intermediate full run passed 240 cases;
seven additional boundary cases and strengthened observation checks preceded the
final **247-pass** run. Lint/format issues were corrected in in-scope files.

All negative core enforcement tests call real installed public services. Direct
executor calls are separately labelled consumer-port contract tests; they do
not stand in for core approval/authorization rejection. Fault subclasses are
registered through the trusted executor registry, without AIG monkeypatching.

No production human authentication, distributed transaction/HA, malicious-host
isolation, cryptographic authenticity, model behavior, formal collusion outcome
or detector performance is verified by this matrix.
