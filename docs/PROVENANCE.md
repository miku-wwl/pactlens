# PactLens Provenance — Pre-Sprint Work vs. Sprint Contributions

Recorded 2026-10-17 (Phase 0). Purpose: disclose, as required by the
competition's prior-work rules, exactly what existed before the sprint
(2026-10-23) and what is planned as new work during it. This file is the single
source of truth for the report's "Prior Work / Authorship Disclosure" section.

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

- This repository's root design blueprint (`PACTLENS_HACKATHON_DESIGN.md`,
  mirrored to `docs/HACKATHON_DESIGN.md`): research framing, hypotheses, arena
  concept, monitor taxonomy, evaluation plan.
- Root `AGENTS.md`: upstream consumer instructions + PactLens-specific
  addendum (appended 2026-10-17, upstream text preserved).
- Phase 0 scaffolding: `pyproject.toml` with the pinned Git dependency,
  `uv.lock` (31 packages, reproducible), `.python-version` (3.13), `LICENSE`
  (MIT), `.gitignore`, `.env.example` (no secrets), minimal
  `src/pactlens/__init__.py`.
- Phase 0 documentation: `docs/ARCHITECTURE.md`, `docs/EXPERIMENT_PLAN.md`,
  `docs/PROVENANCE.md` (this file), `docs/COMPETITION_REQUIREMENTS.md`,
  `docs/PHASE0_REPORT.md`.

No experiments, datasets, measured results, or detector implementations
existed before the sprint. The Phase 0 verification only executed environment,
dependency, and API-surface checks.

## 2. Planned new work during the sprint (2026-10-23 onwards)

1. Synthetic Incident Allocation Arena (seeded generator, payoff function,
   deterministic allocator, outcome evaluator).
2. Experimental conditions C+/N1/N2/N3/C−, episode manifests, and the
   evaluation dataset.
3. Collusion detection monitors M / A / MA / MAE and ablations.
4. Thin AIG consumer adapter and evidence collector (Plan → Approval →
   Admission → Authorization → Execution → Receipt end-to-end), with
   synthetic-consent labelling for offline runs.
5. Controlled comparisons and ablation studies; pilot then frozen study.
6. Statistical analysis (metrics, intervals, case studies).
7. Research conclusions, figures, report writing, and submission.

This section is a **plan**, not a record of completed work. Anything actually
built must be checked off here with a timestamp as it lands.

## 3. Pre-sprint baseline plan (authorization required)

- Baseline marker name (proposed): `PRE_SPRINT_BASELINE` at the Phase 0 tree
  state (this commit's content: scaffolding + Phase 0 docs, no code beyond the
  package marker).
- **Not yet created. No Git tag, push, commit of the working tree, release, or
  deployment has been made. Each requires explicit user authorization.**
- At sprint start (2026-10-23), record the Sprint start tree state and list the
  first sprint-created files; from then on, every substantive change is logged
  with date and purpose so the report's disclosure is factual.
- Reproduction rule: the report must distinguish
  `provenance = pre_sprint` vs `provenance = created_during_sprint` in
  manifests, and never present pre-sprint scaffolding as sprint results.
