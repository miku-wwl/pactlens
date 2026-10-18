# Phase 3 — Acceptance and Test Matrix

2026-10-18 NZDT, pre-sprint engineering. Final results are recorded in
[PHASE3_EXECUTION_REPORT.md](PHASE3_EXECUTION_REPORT.md). Tests use fake generation
and the **real installed AIG**. The separate opted-in local smoke is not pytest,
an official study episode, or authenticated human consent.

## Case inventory

| Module | Cases | Verified boundary |
|---|---:|---|
| test_agent_model_protocol | 34 | Valid/closed decisions, 12 invalid/injection cases, malformed/duplicate/oversized JSON, immutable history, local-only URL/transport, exact model/cloud/revision checks, no default inference/retries, explicit seed mapping |
| test_communication_router | 9 | Public/private delivery, disabled/wrong/self/unknown/subset recipients, injected failure, delivered-only inbox, immutable correlated facts |
| test_experiment_scheduler | 6 | Three contexts, two rounds/order, revisions 1/2/3/5/6/7, six actual Gateway effects, fresh dirs/consent, durable reconstruction, pure replay and chronology |
| test_condition_interventions | 7 | Independent C+/C− episodes and matching, blocked channel/inbox, failed positive retained, N2 discussion without final effect, five contracts without truth labels |
| test_harness_failure_modes | 16 | Timeout/invalid/wrong actor/decline/missing/infeasible/injection; pre/post-commit Unknown; independent approval/auth denials; delivery failure; generation interruption; bridge conflict; actual async deadline; post-commit cancellation |
| test_research_trace_integrity | 20 | Eight storage corruptions, seven semantic contradictions including approval/auth, interrupted missing terminal, exclusive/closed writer, marker/token isolation, unknown order and delivery/capture correlation |
| **Phase 3 new** | **92** | Engineering acceptance only |
| **Existing Phase 1.1/2** | **247** | Every original case retained; one narrow import-guard extension |
| **Total collected** | **339** | No official observations represented |

The original 247 comprise 83 AIG, 93 Arena/state and 71 evidence/fixture/split
cases; their historical matrices/reports are preserved. The network-blocking
pytest fixture remains active. Only stdlib socketpair IPC is permitted. Local
transport tests inject offline HTTP responses, never connect to Ollama/cloud.

## Required acceptance mapping

| Request case | Actual test evidence |
|---|---|
| 1 Three independent contexts | scheduler: separate immutable history, first/second request turns, actor inbox |
| 2–3 Permitted routing; blocked never received | router cases; paired minus requests have empty inbox; failed-message text absent from every inbox |
| 4–6 Valid/invalid/timeout | parser parameterization; harness invalid attempts; one real `asyncio.timeout` expiry then five bounded steps |
| 7 Prompt injection cannot select authority | extra authority/scope/tool fields rejected; harness injection has zero executor calls/rows; inherited actual AIG wrong-binding tests |
| 8–9 Order/current revision | actual actor request order and bases 1/2/3/5/6/7, six verified effects, original reconstruction |
| 10 Every effect via real Gateway | six real Run/Approval/admission/auth/execute records, detached API snapshots and independent SQLite receipt checks |
| 11 Wrong actor/unauthorized | wrong actor model protocol plus inherited cross-actor runtime tests; separate withheld Approval/auth produce zero effects |
| 12 Unknown never replayed | fault before dispatch/after commit yields one request/one dispatch; Unknown stop; original recovery/process tests retained |
| 13 Durable reconstruction | same final canonical Arena from verified stores; separate real-smoke reconstruction |
| 14–15 Matching/intervention | same private briefs/order/request seeds; independent Action IDs; actual delivered C+ versus blocked C− messages |
| 16–17 Failed control and no fabricated truth | C+ fake-model lawful outcome retained with regret zero and behavior_class null; N2 attempts not final execution |
| 18–20 Deterministic replay/zero effects | exact byte-identical L3 and same Arena; provider/composition forbidden in replay; store rows unchanged; replay counters zero |
| 21 Private marker isolation | nested L1/L2/path/brief/truth markers, real capability/scope/subject/path excluded from trace/L3 as appropriate; original 22-marker tests retained |
| 22 No false chronology | actual message/action/application interleaving; source-grouped array unchanged; independent clocks require nulls/UNKNOWN |
| 23 Failed/incomplete episodes | invalid outputs, model exceptions, actual timeout, delivery failure, cancellation and bridge failure retain terminal state; absent terminal → INTERRUPTED |
| 24 Original suite green | required final complete pytest run, retaining every original test identity |

Corruption tests rewrite the unkeyed chain to exercise additional semantic
checks; they do not claim resistance to a consistently rewritten hostile-host
history. Pure replay validates stored facts, not a new authenticated receipt.
Actual OS process-exit AIG recovery remains covered by inherited Phase 2 tests;
a power-loss test of the research JSONL filesystem is not claimed.

## Real generation is separate

One user-opted-in N3 engineering episode used local Ollama 0.35.1 and installed
`phi4-mini:latest`, digest
`78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753`.
Six actual generation calls produced six responses: four valid decisions
(one submission and three explicit declines), two rejected outputs, four routed
message attempts, one delivery and one verified AIG submission receipt. The
episode is **INCOMPLETE**, despite Arena finalization using missing-ballot
fallback. Real-model readiness is **PARTIAL**, not a passing complete-model
episode. No second real episode or retry was run.

The model's actual failures and usage/latency/digests are retained privately;
safe summaries and L3 observation are packaged. No behavioral ground truth,
positive-control realization rate or formal detector result follows from this
single engineering case. Formal exploratory study remains NO-GO.
