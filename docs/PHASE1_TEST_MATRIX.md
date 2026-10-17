# Phase 1 Acceptance and Test Matrix

Execution date: **2026-10-18 NZDT**. Final full run: **119 passed, 0 failed**;
actual JUnit counts are packaged with the review. These are deterministic
engineering tests, not 119 research observations or human adjudications.

| Module | Passed cases | Evidence |
|---|---:|---|
| [test_arena_determinism.py](../tests/test_arena_determinism.py) | 45 | 3/4/5-incident generation, same-input replay, local RNG, four separate-process reproductions outside the checkout under isolated/randomized and explicit hash seeds, unordered input canonicalization, frozen nested state, stale/duplicate/wrong-actor/round/task/terminal rejection, strict closed JSON and history invariants |
| [test_arena_outcomes.py](../tests/test_arena_outcomes.py) | 25 | Hand-computed J*=6 / harmful J=12; separate SLA/unassigned J=121; six lawful ties; skill/capacity/eligibility and complete-task infeasibility; joint-feasibility voting; missing-final defaults; 0/1/−1 pair/outsider boundaries and evaluator-pair checks |
| [test_scenario_fixtures.py](../tests/test_scenario_fixtures.py) | 26 | All 14 hand-defined diagnostics, five intended conditions, agreement plus two jointly necessary ballots, failed C+, N2/N3 distinctions, independently finalized C+/C−, assignment invariance, unexpected control harm, incomplete logs, pending human labels, no forbidden application imports |
| [test_split_groups.py](../tests/test_split_groups.py) | 11 | Exact seed bytes/int convention, fixed group IDs, 24 blocks/120 unexecuted slots, shared twin settings/streams, 24 unique task hashes, pilot exclusion, deterministic pre-execution collision resolution/exhaustion |
| [test_labels_no_leakage.py](../tests/test_labels_no_leakage.py) | 12 | 22 hidden markers across private manifest/seed/coalition/nested metadata/L2 oracle fields/notes/paths; JSON, repr, adapter copies and actual files; poison private objects never inspected; preserve predictive text/actions/costs; uniform missing schemas, UUID-only filenames and exclusive export |
| **Total** | **119** | No skips, expected-failure cases or live model/provider tests |

## Acceptance mapping

| # | Required acceptance | Evidence / result |
|---|---|---|
| 1 | Deterministic generation and cross-process reproduction | `test_seeded_generation_and_replay`, `test_cross_process_reproduction_outside_checkout`: PASS |
| 2 | Validated immutable two-round transitions | `test_invalid_transition_is_atomic`, `test_lifecycle_exactly_two_rounds`, history/frozen-state tests: PASS |
| 3 | Deterministic execution and lawful optimum | Hand optimum/tie tests, conflicting ballots and infeasible per-incident-majority reconciliation: PASS |
| 4 | Independently checked integer costs | Hand J=6/12/121, component reconciliation and 0/1/negative boundary tests: PASS |
| 5 | Five distinct fixture mechanics | All-spec and parallel/talk-only/lawful/positive tests: PASS |
| 6 | C+/C− pairing integrity | Settings equality except channel, different state/proposal/outcome objects and independent evaluation; shared manifest seeds/settings: PASS |
| 7 | Truth not assignment-derived | Relabelled positive has identical execution/adjudication; every fixture class remains None: PASS |
| 8 | L1/L2 absent from L3 | Marker/poison-source tests and explicit public-field assertions: PASS |
| 9 | No accidental split/private-metadata leakage | Fixed group membership/task hash checks; nested/path/object/export tests: PASS for this boundary |
| 10 | 24-block/120-slot manifest | Per-split/per-condition counts and no-execution monkeypatch: PASS |
| 11 | No AIG copying/modification | Application AST has no Runtime/provider imports; installed AIG pin/site-packages path and 57 RECORD hashes verified separately: PASS |
| 12 | No premature Phase 2 | No adapters, ledgers, grants, receipts, Runtime dispatch or orchestration modules/imports: PASS for delivered scope |
| 13 | No model/API/external effects | Socket connections blocked in tests; no networking/model imports in application; uv checks forced offline: PASS for executed checks |

“No leakage” means no private input transfer through the explicit projection,
not no predictive information, adversarial text, arbitrary Python access or
filesystem compromise. Distinct seeds/hashes do not establish population-level
independence or statistical validity. Fixture labels are expectations, not final
human truth. Formal pilot/calibration/held-out scoring and genuine AIG integration
are **NOT RUN**.

## Development checks and corrected failures

- First 114-test suite passed. Initial Ruff found six issues: two function-call
  defaults, import ordering/unused import and an import alias; corrected only
  in in-scope code.
- After stronger history/ballot tests, one run had **1 failed, 118 passed**:
  a negative test expected MISSING_START_EVENT while the earlier revision/history
  guard correctly rejected it as REVISION_HISTORY_MISMATCH. The assertion was
  corrected and both rejection paths are tested; no guard was weakened.
- Final 119-test run passed, as did all required lint/format/lock checks.
- An auxiliary integrity script initially compared CRLF working bytes to LF
  Git blobs. It was corrected to compare Git-filtered blob identities; all
  14 preserved protocol/config/historical files match HEAD. Raw working-file
  SHA-256 values are separately recorded, without claiming byte-identical
  representations across Git line-ending conversion.
