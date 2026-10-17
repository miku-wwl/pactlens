# PactLens Provenance — Pre-Sprint Work vs. Sprint Contributions

Recorded 2026-10-17 (Phase 0; reviewed in Phases 0.5 and 0.6). Purpose: disclose, as
required by the competition's prior-work rules ("you must clearly identify
what is new work done during the sprint. Undisclosed prior work can lead to
disqualification." — official Guidelines tab, 2026-10-17), exactly what existed
before the sprint and what is planned as new work during it. This file is the
single source of truth for the report's prior-work disclosure section.

## 1. Pre-existing work (created before the sprint)

### 1.1 Third-party, pinned as an immutable dependency

| Item | Version / identity | Role in PactLens |
|---|---|---|
| Agentic Intent Gate | `0.2.0`, annotated tag `v0.2.0`, commit `7261fdd2f47d2b15fabe8faac527eeee37338eb1`, MIT | Shared Python runtime consumed via its public API (`agentic_intent_gate.runtime`) |

Already provided by AIG v0.2.0 (not PactLens contributions): strict Plan
validation; persistent Runs; exact Plan-to-Approval binding; independent Action
authorization; trusted single-tool `ToolExecutor` registration; single-step
`SIDE_EFFECT` lifecycle; SQLite-backed durable Action state, claim, audit
events and receipt references; CAS/concurrency controls; stable effect keys;
idempotent command handling; fail-closed recovery with terminal `Unknown`
outcomes; configurable trusted execution budgets (default 5 s, max 15 s).

PactLens uses the package **as installed**; no source copying, forking,
monkeypatching, or private-API dependency exists in this repository.

### 1.2 PactLens scaffolding and design completed before the sprint

- Root design blueprint (`PACTLENS_HACKATHON_DESIGN.md`): preserved original
  proposal. `docs/HACKATHON_DESIGN.md` is the maintained copy with explicit
  Phase 0.6 corrections; it is no longer an exact mirror.
- Root `AGENTS.md`: upstream consumer instructions + PactLens-specific
  addendum (appended 2026-10-17, upstream text preserved).
- Phase 0 scaffolding: `pyproject.toml` with the pinned Git dependency,
  `uv.lock` (31 packages, reproducible), `.python-version` (3.13), `LICENSE`
  (MIT), `.gitignore`, `.env.example` (no secrets), minimal
  `src/pactlens/__init__.py`.
- Phase 0 / 0.5 documentation: `docs/ARCHITECTURE.md`,
  `docs/EXPERIMENT_PLAN.md`, `docs/PROVENANCE.md` (this file),
  `docs/COMPETITION_REQUIREMENTS.md`, `docs/PHASE0_REPORT.md`,
  `docs/PHASE0_5_REVIEW.md`.
- Phase 0.6 protocol hardening and `docs/PHASE0_6_REVIEW.md`: exploratory
  allocation, truth/adjudication rules, abstention and information controls,
  official-rule conflicts, validation and Phase 1 plan. These are additional
  **pre-sprint preparation**, not sprint implementation or measured research.
- Phase 1 deterministic engineering on **2026-10-18 NZDT**, detailed in §4:
  arena source, synthetic test fixtures, manifest/review/projection contracts
  and automated tests. These also predate the official sprint.

As inspected in Phase 0.6, no arena, experimental dataset, measured findings or
detector implementation exists; `src/pactlens/__init__.py` remains marker-only.
Phase 0/0.5/0.6 checks and documentation are preparation. Future pre-sprint
implementation, if separately authorized, must also be disclosed as pre-sprint;
this observation must not be projected forward as a fabricated history.

## 2. Planned new work during the sprint (2026-10-23 onwards)

1. Arena engineering is now pre-sprint work (Phase 1, §4), not a future
   sprint-created contribution. Any genuinely new sprint extensions must be
   recorded separately.
2. Model-driven C+/N1/N2/N3/C− observations and evaluation dataset remain
   unimplemented/unrun. Engineering fixtures and planned-slot construction
   already exist before the sprint and are not that dataset.
3. Collusion detection monitors M / A / MA / R / MAE; additional ablations
   only under a prospective protocol amendment.
4. Thin AIG consumer adapter and evidence collector (Plan → Approval →
   Admission → Authorization → Execution → Receipt end-to-end), with
   synthetic-consent labelling for offline runs.
5. Controlled comparisons and ablation studies; pilot then frozen study.
6. Statistical analysis (metrics, intervals, case studies).
7. Research conclusions, figures, report writing, and submission.

This section is a **plan**, not completed work. Record actual dates and tree
identities as work lands; never backdate. No newly implemented sprint work is
claimed as of this review.

## 3. Verifiable pre-sprint baseline — how to establish it without silent commits/tags

Local Git verification in Phase 0.6 (no remote PactLens reachability or push
claim was independently checked):

- **VERIFIED locally:** `git rev-parse '34d3857^{commit}'` resolves to
  `34d38578ec36f7d69639c4f8c4ea572dd4b9e4d4`, the original Phase 0 baseline.
  It is an ancestor of HEAD. The commit object records 2026-10-17 +1300;
  this is Git metadata, not independent proof of development time.
- Phase 0.5 pre-sprint correction commit / starting HEAD:
  `7b710fe2f4f8c305897d6ff59820c6f1d3997f02`. It also records 2026-10-17 +1300.
  Thus Phase 0 commit is not the last pre-sprint preparation state.
- At the Phase 0.6 review, the delta was uncommitted over that HEAD; the user
  subsequently authorized its commit/push. Phase 1 locally confirms the resulting
  commit `45b86712edc75c9803a1f36f5d926fe62fba6a0e` as starting/current HEAD.
  Preserve `34d3857` as the original baseline and disclose later preparation
  separately. The earlier review ZIP identifies its then-uncommitted snapshot.

Future baseline procedure; recording read-only hashes needs no new permission,
but commit/tag/push still require explicit authorization:

1. Phase 0.5 is already committed locally. Record later preparation without
   amending earlier history; only commit if separately requested.
2. Create a **plain-text manifest** (not a tag):
   `git rev-parse HEAD`, file inventory with SHA-256 hashes, and the date —
   retained with the review artifacts; committing it is a separate action.
3. Only if explicitly requested: create an annotated tag and push it.
4. At sprint start (official date Friday 2026-10-23; no official start *time*
   is published), record the tree state at that point and list the first
   sprint-created files; from then on log every substantive change with date
   and purpose.

Reproduction rule: all manifests carry
`provenance = pre_sprint | created_during_sprint`, and pre-sprint scaffolding
is never presented as sprint results. Sprint deliverables derive only from the
frozen study protocol in `docs/EXPERIMENT_PLAN.md`.

## 4. Phase 1 pre-sprint engineering — 2026-10-18 NZDT

The user explicitly authorized the deterministic Arena on this date, before the
October 23 sprint. Starting tree: **clean**, branch `main`, HEAD
`45b86712edc75c9803a1f36f5d926fe62fba6a0e`. HEAD remains unchanged; this phase's
source/tests/docs are an **uncommitted delta**, not contained in that commit.
No commit, push, tag, release, deployment, registration or submission occurred.
Git metadata is not independent proof of wall-clock development time.

Files created:

- `src/pactlens/arena/{__init__,models,generator,transitions,allocation,outcomes}.py`:
  strict immutable two-round mechanics, integer costs and exhaustive reference.
- `src/pactlens/research/{__init__,seeds,manifest,adjudication,fixtures}.py`:
  frozen groups/seeds, 120 **unexecuted** slots, private pending reviews and
  bounded hand-scripted diagnostic fixtures.
- `src/pactlens/evidence/{__init__,records,projection}.py`,
  `src/pactlens/serialization.py`: explicit L3 allowlist and canonical JSON/hashes.
- `datasets/fixtures/{arena_cases.json,README.md}`: 14 related synthetic
  engineering cases, **not** independent research observations or model traces.
- `tests/conftest.py`, `tests/test_arena_determinism.py`,
  `tests/test_arena_outcomes.py`, `tests/test_scenario_fixtures.py`,
  `tests/test_split_groups.py`, `tests/test_labels_no_leakage.py`.
- `docs/DATA_DICTIONARY.md`, `docs/PHASE1_TEST_MATRIX.md`,
  `docs/PHASE1_EXECUTION_REPORT.md`.

Updated: this file, README, architecture status, package docstring. Frozen
EXPERIMENT_PLAN, Phase 0/0.5/0.6 reports, original/maintained design blueprints,
competition requirements, AGENTS, dependency config and lockfile are preserved
against Git-filtered HEAD blob identities. AIG remains installed 0.2.0 at
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`; all 57 distribution RECORD hashes
match. No source was copied from or modified in the shared Runtime.

Executed with `UV_OFFLINE=1`: `uv sync --locked`,
`uv run pytest -q --junitxml=.runtime/phase1-validation/pytest.xml` (**119 passed**),
`uv run ruff check .`, `uv run ruff format --check .`,
`uv lock --check --offline`. The test matrix records the corrected development
test/lint failures. The review ZIP includes actual logs, source/config and a
SHA-256 file manifest; hashes identify this working-tree snapshot without a tag.

Still absent: agent orchestration, model/provider integration, AIG consumer
approval/execution/receipt adapters, M/A/MA/R/MAE detectors, scoring, formal
pilot/calibration/held-out runs, independent human adjudication, research
findings and frontend. No synthetic approval is represented as human consent;
Phase 1 does not run an approval workflow at all.

This engineering work may support the sprint, but must **never** be described as
newly developed October 23–25. Actual future sprint-created implementation,
experiments and results must get their own contemporaneous provenance entries.
