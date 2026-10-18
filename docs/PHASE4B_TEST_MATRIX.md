# Phase 4B — Verification Matrix

Date: **2026-10-19 NZDT, pre-sprint engineering**. Baseline
`27c22f338d357a0f18850e86cd6cf9a297d7eeb8` was clean and verified locally,
against tracking and live HTTPS remote before work.

## 1. Final commands

| Check | Actual result |
|---|---|
| `uv sync --locked` with offline cache | PASS; 31 packages |
| `uv run pytest -q --junitxml=.runtime/phase4b-validation/pytest.xml` | **607 passed in 231.78s**, zero failure/error/skip |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS |
| `uv lock --check --offline` | PASS; 31 packages |
| Project-environment compileall of source/tests | PASS |
| Installed AIG version/pin/import/RECORD integrity | PASS; installed 0.2.0 at exact 7261fdd2 full pin; 57 hashes, five-second default |
| Actual local comparison | 2 N3 engineering episodes, **9 generation calls**, no replacements; model NOT READY |
| Offline selected-view audit | 34 source/policy sets: 33 fit estimate, one typed overflow; 165 safe exports; parity PASS for constructed matched inputs |
| Real stores/replay | Same durable Arena state, counts `[1,1,0]`/`[1,1,1]`, no verification writes/new effects/generation |

All original **480** cases remain passing and their test files are byte-identical.
The **127** new cases are:

| Module | Cases | Actual behavior covered |
|---|---:|---|
| `test_evidence_budget_selection.py` | 34 | 14 fixtures ×2 policies, mandatory/core preservation, shared atomic membership, source-order-independent priority/ties, typed mandatory overflow, private fields ignored, receipt mismatch rejection, honest missingness, tampered manifest and repeated-event atomic grouping |
| `test_budgeted_view_parity.py` | 21 | Exact reconstruction against source, MA union/subsets, integrity isolation, text/legend/group/value/null/order/manifest/budget tampering, task compression, complete envelope, exact/estimated seams, process determinism, real AIG Unknown+committed receipt and chronology |
| `test_observer_freeze_candidates.py` | 6 | Delivered/blocked/failed A/B rights, paired schema, actual N2 harness missing slots, nested L1/L2 marker isolation, deterministic unapproved model/prompt freeze candidate |
| `test_model_reliability_contract.py` | 4 | Exclusive pre-dispatch 12-total/6-profile ledger, fake-transport matched comparison, fresh contexts/stores and seed schedule, honest malformed/decline handling, preflight stop, explicit opt-in |
| `test_reviewer_packet_blinding.py` | 9 | Separate full A/B packets/forms, no L1/L4/private path/peer labels, detached nested data, labelled mechanical comparators, unattributed or malformed review rejection |
| `test_pilot_readiness.py` | 25 | Engineering does not imply pilot approval, each failed engineering/critical methodological gate blocks, attributed decisions required, frozen allocation/rules and deterministic report |
| `test_detector_prediction_contract.py` | 26 | Finite bounded scores/confidence, strict fields/types/bindings, duplicate keys, evidence references, NaN/infinity/bool/range rejection, error/insufficiency abstention and no thresholding |
| `test_reliability_measurements.py` | 2 | Schema structure versus JSON/feasibility/routing/actual acceptance measured separately; failed decisions never repaired or dispatched |
| **New total** | **127** | **480+127=607** |

## 2. Requirements 1–25 coverage

Shared selection/parity/mandatory/atomic/priority/process/MA subset/full-envelope/
overflow requirements (1–11) are exercised by the first two modules. Private
condition/oracle isolation, marker injection, chronology, policies and retained
N2/missing/Unknown distinctions (12–18) are covered across selection/parity/
observer tests and the unchanged harness regressions. Tamper/no-repair/no-new-
effect replay (19–21) have negative tests and actual read-only trace/store checks.
Freeze hashes, future response schema, historical compatibility and unchanged
AIG/Arena/harness behavior (22–25) are covered by freeze/prediction/readiness
tests and all original 480 cases.

The real local-model comparison is outside pytest and remains explicitly separate
from fake transport, synthetic planning and parser fixtures. Pytest blocks
application socket connections; fake Ollama transports perform no real inference.
The real AIG/SQLite paths use the actual pinned installed runtime with synthetic
consent. These tests authenticate no human and establish no collusion truth.

## 3. Intermediate failures and correction

An intermediate new-test run failed because a new test supplied recorded Router
positions without declaring shared capture. After correcting that test setup,
another assertion incorrectly treated the old hand-scripted N2 fixture as the
later harness's all-final-submission block. The assertion now runs the actual N2
harness with fake planning. Neither historical fixture nor condition mechanics
was changed. Final full-suite failures are **zero**; intermediate logs remain
available as engineering diagnostics, not research observations.

A separate strict-schema measurement audit corrects only a derived measurement
flag to include assignment/message structure. Original real responses, traces,
original summary and accept/reject decisions are unchanged; no model rerun or
prompt tuning followed. Safe audited per-response measurements are packaged.

## 4. Interpretation boundaries

The nine real calls show two incomplete episodes, not a winner or general
reliability rate. Near-limit detector estimates do not prove exact model fit.
Selected R/MAE parity is semantic, not token equality or presentation fairness.
One mandatory Router core overflows and some fitting subsets are insufficient
for complete episode-wide agreement/provenance audit; these limitations are
reported instead of changing the core or dropping cases.

Formal pilot/calibration/held-out execution **0**; detector inference/prediction/
scoring/calibration/statistical evaluation **0**; independent human review **0**;
paid/cloud inference **0**. No AIG upstream, Arena/fallback/condition, dependency,
frozen protocol/split/threshold or old report was modified. No commit, push,
tag, release, deployment, competition submission or Phase 4C occurred.
