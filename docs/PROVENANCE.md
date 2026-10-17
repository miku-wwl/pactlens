# PactLens Provenance — Pre-Sprint Work vs. Sprint Contributions

Recorded 2026-10-17 (Phase 0; reviewed in Phase 0.5). Purpose: disclose, as
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

- Root design blueprint (`PACTLENS_HACKATHON_DESIGN.md`, mirrored to
  `docs/HACKATHON_DESIGN.md`): research framing, hypotheses, arena concept,
  monitor taxonomy, evaluation plan.
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

No experiments, datasets, measured results, or detector implementations
existed before the sprint. Phase 0 and 0.5 executed only environment,
dependency, API-surface, and official-requirements checks.

## 2. Planned new work during the sprint (2026-10-23 onwards)

1. Synthetic Incident Allocation Arena (seeded generator, payoff function,
   capacity constraints, deterministic allocator, outcome evaluator).
2. Experimental conditions C+/N1/N2/N3/C−, episode manifests, and the
   evaluation dataset.
3. Collusion detection monitors M / A / MA / MAE and ablations.
4. Thin AIG consumer adapter and evidence collector (Plan → Approval →
   Admission → Authorization → Execution → Receipt end-to-end), with
   synthetic-consent labelling for offline runs.
5. Controlled comparisons and ablation studies; pilot then frozen study.
6. Statistical analysis (metrics, intervals, case studies).
7. Research conclusions, figures, report writing, and submission.

This section is a **plan**, not a record of completed work. Everything
actually built must be checked off here with a timestamp as it lands.

## 3. Verifiable pre-sprint baseline — how to establish it without silent commits/tags

The pre-sprint state is already externally verifiable without creating any tag:

- Commit `34d3857` ("Phase 0: repository bootstrap, AIG v0.2.0 integration
  preflight, docs", 2026-10-17, pushed to `github.com:miku-wwl/pactlens`) is
  the last commit containing **no sprint-created code** — only scaffolding and
  pre-sprint docs. It is the natural `PRE_SPRINT_BASELINE` reference.
- Any Phase 0.5 documentation corrections made before the sprint are a second
  commit dated before 2026-10-23; both together define the baseline. Record the
  exact commit SHA(s) in the report's prior-work section.

Baseline procedure (to be executed only after user authorization — no commit,
tag, or push has been or will be performed without explicit approval):

1. Commit the Phase 0.5 review changes as a dated commit before the sprint
   starts; do not amend earlier commits (history stays auditable).
2. Create the baseline record as a **plain-text manifest** (not a tag):
   `git rev-parse HEAD`, file inventory with SHA-256 hashes, and the date —
   stored in `docs/` and committed.
3. Only if the user explicitly requests it: create an annotated lightweight
   marker (e.g. `git tag -a PRE_SPRINT_BASELINE`) and push it — never silently.
4. At sprint start (official date Friday 2026-10-23; no official start *time*
   is published), record the tree state at that point and list the first
   sprint-created files; from then on log every substantive change with date
   and purpose.

Reproduction rule: all manifests carry
`provenance = pre_sprint | created_during_sprint`, and pre-sprint scaffolding
is never presented as sprint results. Sprint deliverables derive only from the
frozen study protocol in `docs/EXPERIMENT_PLAN.md`.
