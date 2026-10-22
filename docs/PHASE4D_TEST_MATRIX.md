# Phase 4D — Test and verification matrix

2026-10-22 NZDT. Tests block network connections; fake providers are explicit.
Real AIG integration effects are bounded synthetic SQLite writes with synthetic
consent. No test invokes a real model or consumes a formal study slot.

| Requirement | Exercised contract |
|---|---|
| Original baseline | Reproduced 724 tests before Phase 4D changes: 537.56 s. Focused existing protocol suite: 78 passed. |
| v3.1 | `test_phase4d_protocol.py`: 42 cases; five conditions, actor/round coverage, no/public/private/blocked speech, missing/decline/invalid output, overflow, strict duplicate keys/identity/array-object/message/authority checks |
| Detector | `test_phase4d_detector.py`: 48 cases; all five views, full request guard, strict bounded response/citations, provider/JSON/type/length errors, insufficiency, durable duplicate refusal, tamper rejection and zero-call replay |
| Scientific/operations | `test_phase4d_research.py`: 15 cases; L3 baseline rights/no oracle, incomplete evidence, paired synthetic metrics/bootstrap/calibration/strata, label-free selection, approval/split guards, real-AIG-to-fake-detector E2E/store immutability and engineering-only dry run |
| Reporting | `test_phase4d_reporting.py`: 3 cases; synthetic/unreviewed/source-mismatched exports rejected, claim/hash eligibility, finite numeric research JSON without relaxing Arena serialization |
| Historical compatibility | All existing tests retained; static verification reconstructs v1/v2/v3 hashes from HEAD literals and unchanged context source |
| Evidence sufficiency | 30 fixture/silent-six-action policy sets + 2 communicating-six-action sets; independent semantic M/A/MA/R/MAE relations, complete-or-infeasible, every omission recorded |
| Unknown | Existing recovery/failure tests plus real local before-dispatch/after-commit diagnostic; Unknown never becomes baseline success; replay performs no second effect |
| Pilot operations | Four ENG groups, five conditions, fresh state, 120 fake requests, 108 verified receipts, 20 equal replays; zero actual inference/formal slots |
| Live engineering ledger | Six agent plus two detector actual calls; C+ skipped; no retry/replacement/download/cloud/paid provider |

## Reproduction and actual logs

Final source-bound run: **832 passed in 560.26 s (9:20); 724 existing +108 new;
0 failed, 0 errors, 0 skipped.** All required command exits are 0. Ruff format
checked 183 Python files; static integrity reverified 57 installed AIG RECORD
hashes, five-second default, 122 tested source/test hashes, seven prediction
replays, unchanged trace/store bytes, and historical v1/v2/v3 prompt hashes.

```powershell
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv lock --check --offline
uv run python -m compileall -q src tests scripts
uv run python scripts/verify_phase4d_static.py
```

Full final test count/status and command exit codes are recorded in
`review/phase4d/logs/full-suite-verified.txt`, its JUnit XML and
`review/phase4d/verification.json`. These files, rather than prior reports,
are the final verification evidence. No chart export from formal data was run.

Development failures remain in logs: an incorrect fixture name, integer-only
Arena serializer used for fractional scores, same-value tamper-test edit,
UUIDv5 used where public UUIDv4 is required, reuse of an exclusive output path,
and a dry-run closure binding collision. These were corrected. An early full
test invocation was stopped after identifying the closure error; its partial
log is retained and is not counted as a passing suite. Completed fresh final
suite results are separate. These were offline implementation faults, not extra
live model runs or replacement research episodes.
