# Phase 4A — Offline Verification Matrix

Date: **2026-10-19 NZDT**, pre-sprint. All results below are engineering checks,
not model-reliability measurements, detector results or formal observations.
Baseline: `6bf93a996476e6433eedc3fa11784703bf61a31a`.

## 1. Final checks

| Command/check | Actual result |
|---|---|
| `uv sync --locked` (offline cache) | PASS; installed environment synchronized, 31 packages |
| `uv run pytest -q --junitxml=.runtime/phase4a-validation/pytest.xml` | **480 passed in 170.32s**; 0 failures/errors/skips |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS |
| `uv lock --check --offline` | PASS; lock resolves 31 packages |
| `python -m compileall -q src tests` in the project environment | PASS |
| Installed AIG version/source/import and RECORD hashes | PASS; 0.2.0, pinned 7261fdd2 full revision, installed site-packages, 57 hashes |
| Historical private Phase 3 trace read-only replay | PASS; same INCOMPLETE status and L3, unchanged trace and receipt counts; zero new model/Gateway/effect calls |

Pytest's console elapsed time is 170.32 seconds; JUnit reports 170.12 seconds
for the suite itself. Logs and a sanitized JUnit document are in the review
package. The original **339** collected cases remain passing and their source
files are unchanged. The new **141** cases are:

| New module | Collected/passing cases | Requirement and negative evidence |
|---|---:|---|
| `test_model_protocol_hardening.py` | 44 | Closed/versioned parser, 4 valid forms, 26 invalid mutations, original two smoke-error shapes, genuine installed-AIG fake-model path, declines, preflight, actual usage/length rejection and host-failure categories |
| `test_trace_size_consistency.py` | 9 | Empty/header/small trace, exact 8,000,000-byte boundary, one byte over, cumulative/count limits, rejected append atomicity including executor count/terminal state, malformed oversize and chaining |
| `test_phase3_trace_compatibility.py` | 1 | Old request without new metadata replays under v1 with model/provider and new AIG composition forbidden |
| `test_evidence_inventory.py` | 11 | Opaque identity, aliases, defensive copying, allowlists, missingness, provenance and unknown cross-source order |
| `test_detector_view_contracts.py` | 13 | Five-view matrix under both policies, MA union, integrity exclusion from MA, explicit budget overflow and retained N2 all-final-slots missing signature |
| `test_observation_policies.py` | 6 | Enabled/blocked/failed routing, private experimenter audit versus detector rights versus actor inbox, paired schema, engineering compatibility default |
| `test_raw_structured_parity.py` | 42 | All 14 engineering fixtures under both policies, actual AIG/receipt snapshots, semantic drift despite individually valid manifests, text/manifest reconstruction and Unknown with committed receipt |
| `test_detector_view_leakage.py` | 12 | All five views under both policies, private marker classes through render/context/manifest/export filenames, no private-object reflection, blocked-attempt audience |
| `test_view_rendering_determinism.py` | 3 | Fresh-process hash-seed determinism, captured ordering and unknown order, rendering order explicitly not event chronology |
| **Total new** | **141** | **339 existing +141 new =480** |

## 2. Parser correctness is separate from model adherence

The deterministic corpus accepts **4/4 valid synthetic forms** (submission,
decline, public message and private message), and rejects **26/26 malformed or
invalid mutations** with their expected classifications. This is corpus coverage,
not an estimated real-model acceptance rate. The two recorded Phase 3 failure
shapes still reproduce the original `INVALID_ASSIGNMENT_SYNTAX` and
`MESSAGE_SYNTAX` failures; candidate classification adds detail without repair.

Candidate fake decisions pass through the real installed AIG path with separately
scripted Approval and Authorization. These tests prove execution integration,
not authenticated human consent. Unknown remains terminal and is not retried.
Valid declines require no Action and remain legitimate decisions.

**Actual candidate model reliability: NOT RUN / NOT VERIFIED.** No new Ollama or
other real inference occurred. The old six-call v1 engineering episode is retained
as history, not rerun or reinterpreted under v2.

## 3. Trace regression evidence

Before the fix, the old Writer produced **8,609,987 bytes** through valid appends;
the existing Reader rejected it with `TRUNCATED_OR_OVERSIZED_TRACE`. The updated
Writer/Reader share 8,000,000 total bytes, 131,072 bytes per record and 256 records.
Tests verify exact limits and unchanged file/state on rejected appends. If a
terminal cannot fit, replay reports the valid prefix as INTERRUPTED; no terminal
or effect is invented. Filesystem failures remain outside the size guarantee.

The actual 2026-10-18 private engineering trace was separately read without
generation or dispatch: trace hash unchanged, L3 equal, status INCOMPLETE,
per-actor stored proposal counts still `[1, 0, 0]`. The raw trace and private
stores are excluded from the review ZIP; only the safe verification summary is
included.

## 4. Rendered information, leakage and ordering

R and MAE are parsed independently from actual JSONL/grouped-JSON renderings.
Canonical comparison includes every fact ID/value/null, actor, provenance/trust,
receipt linkage, completeness and known/unknown order. Hash/manifest consistency
checks bind actual text. Tests change values, IDs, actors, missingness and order,
including changes with a newly consistent individual manifest: semantic parity
still detects differing facts. This is stronger than comparing a shared object.

Markers cover condition, coalition, split/group/seed, private brief, model system
prompt, hidden settings, oracle allocation, ground truth, adjudication, paired
outcome, private Gate path, capability and authorization secret. None appears in
the tested views, metadata, contexts or export names. This establishes direct
projection isolation, **not** absence of statistical condition shortcuts.

N2 all-missing final slots and Policy B blocked attempts are deliberately still
observable where authorized. Tests assert their truthful presence, not their
elimination. Unknown cross-source clocks remain unknown. Known shared capture
positions are preserved and are not promoted into transaction timestamps.

## 5. Measured rendering budget audit

One additional **synthetic engineering audit**, not a model episode, used six
fake response steps through six real AIG Actions/verified local receipts.
No real inference, formal episode or detector prediction occurred. Both policies
passed R/MAE semantic parity. Bytes below measure rendered text only; estimated
tokens additionally account for the common system context and chat margin.

| Policy | View | Facts | UTF-8 bytes | Estimated input tokens | 4,096 preflight |
|---|---|---:|---:|---:|---|
| A delivered | M | 8 | 4,541 | 2,581 | fits estimate |
| A delivered | A | 18 | 10,019 | 5,320 | overflow |
| A delivered | MA | 25 | 13,238 | 6,929 | overflow |
| A delivered | R | 38 | 22,125 | 11,373 | overflow |
| A delivered | MAE | 38 | 38,265 | 19,443 | overflow |
| B Router | M | 14 | 8,422 | 4,521 | overflow |
| B Router | A | 18 | 10,012 | 5,316 | overflow |
| B Router | MA | 31 | 17,118 | 8,869 | overflow |
| B Router | R | 44 | 26,005 | 13,313 | overflow |
| B Router | MAE | 44 | 44,977 | 22,799 | overflow |

These are explicitly **heuristic estimates, not exact tokenizer measurements or
guaranteed upper bounds**. All exact-token fields are null. Complete contexts are
retained for audit; overflowing model conversations fail closed. Synthetic exact
counter tests do not establish actual model token fit. A prospective selection/
token-accounting decision is documented, not activated.

## 6. Intentionally not run

New actual model calls **0**; formal pilot/calibration/held-out executions **0**;
detector predictions/scoring **0**. No calibration, statistics, learning,
competition submission, deployment, commit or push occurred. Passing engineering
tests does not resolve observer selection, N2 confounding, prompt reliability,
token feasibility or formal-pilot readiness.
