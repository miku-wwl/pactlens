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

As inspected in Phase 0.6, no arena, experimental dataset, measured findings or
detector implementation exists; `src/pactlens/__init__.py` remains marker-only.
Phase 0/0.5/0.6 checks and documentation are preparation. Future pre-sprint
implementation, if separately authorized, must also be disclosed as pre-sprint;
this observation must not be projected forward as a fabricated history.

## 2. Planned new work during the sprint (2026-10-23 onwards)

1. Synthetic Incident Allocation Arena (seeded generator, payoff function,
   capacity constraints, deterministic allocator, outcome evaluator).
2. Experimental conditions C+/N1/N2/N3/C−, episode manifests, and the
   evaluation dataset.
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
- Phase 0.6 is an **uncommitted documentation delta** over that HEAD.
  Preserve `34d3857` as the named original baseline; disclose all later
  preparation separately. The review ZIP carries SHA-256 file manifests to
  identify this uncommitted snapshot. It does not create a new Git baseline.

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
