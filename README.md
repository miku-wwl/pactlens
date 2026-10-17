# PactLens

**Evidence-Based Multi-Agent Collusion Detection** — a research project for the
Apart Research **AI Collusion Research Sprint** (2026-10-23 → 25), Track 2
(*Detection and Audit of Collusion*), research questions **2.2** and **2.3**:

> Can combining agent communication, executed actions, and verifiable execution
> evidence improve detection of harmful AI-agent collusion while reducing false
> accusations against innocent parallel behavior?

PactLens consumes the installed
[`agentic-intent-gate`](https://github.com/miku-wwl/agentic-intent-gate) runtime
(v0.2.0, pinned release commit
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`) through its public API only — it
does not fork, reimplement, or bypass the shared runtime. All orchestration,
experiments, detectors, and evaluation live in this repository (consumer side).

## Status: Phase 0.6 complete — exploratory protocol, no implementation yet

The authoritative protocol is [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md):
4 pilot + 10 calibration + 10 held-out blocks, five episodes per block,
120 planned episodes / 24 independent blocks. This is **exploratory**, not
confirmatory. MAE vs MA is the primary descriptive comparison; mandatory R
contains MAE's same facts in raw form to separate information from structure.
See [Phase 0.6 review](docs/PHASE0_6_REVIEW.md) for gates, checks and the
planning-only Phase 1 scope. No experiments were run.

**Not yet implemented** (planned, not built): the incident-allocation arena,
research experiment driver, agent runners, AIG consumer adapter, evidence
collector, monitors M/A/MA/R/MAE, evaluation pipeline, dashboard. There are no
experimental results in this repository. `src/pactlens/__init__.py` is a
package marker only.

## Intended architecture (three planes)

1. **Experiment plane** (this repo): scenario/seed/condition randomization,
   controlled messaging, model calls, measurement. Research metadata
   (condition, coalition assignment, ground truth) never reaches a detector.
2. **Execution plane**: one isolated AIG runtime per agent, each registering
   exactly one trusted `SIDE_EFFECT` tool (`submit_incident_proposal/1`) whose
   only effect is appending a row to a consumer-owned SQLite store, keyed by
   AIG's stable effect key with a durable receipt.
3. **Audit plane**: a versioned `EvidenceRecord` schema merges
   research-owned message logs with AIG's verifiable action records
   (approval, terminal state, payload digest, receipt) into leak-safe detector
   views (M / A / MA / R / MAE; extra ablations deferred).

See `docs/ARCHITECTURE.md` for the verified API contract and constraints.

## Installation and reproducibility

```bash
# Requires uv (https://docs.astral.sh/uv/) and Python 3.13
uv sync --locked          # installs from the reproducible uv.lock (31 packages)
uv lock --check --offline # verifies the lockfile is current and offline-usable
uv run ruff check .       # lint
```

- The runtime dependency is pinned to the immutable AIG release commit; the
  installed distribution must report `agentic-intent-gate==0.2.0` and resolve
  to that commit (verified in `docs/PHASE0_REPORT.md`).
- Reproducibility contract for the research phase (pre-registered in
  `docs/EXPERIMENT_PLAN.md`): frozen arena generator, seeds, models and
  prompts, calibrated-then-frozen detector thresholds, every run exported
  (including failures and `Unknown` actions), and all figures rebuilt from
  versioned manifests.
- Secrets: none in the repo. Copy `.env.example` to `.env` (gitignored) if
  provider credentials are ever needed for the optional LLM pilot.

## Repository layout

```text
AGENTS.md                          agent instructions (upstream AIG rules + PactLens invariants)
PACTLENS_HACKATHON_DESIGN.md      preserved original pre-sprint blueprint
LICENSE, .python-version, pyproject.toml, uv.lock
.env.example, .gitignore
src/pactlens/                     package marker only — no logic yet
docs/
  HACKATHON_DESIGN.md            maintained blueprint with Phase 0.6 corrections
  ARCHITECTURE.md                consumer contract, verified API surface, constraints
  EXPERIMENT_PLAN.md             pre-registration: hypotheses, conditions, metrics, failure paths
  PROVENANCE.md                  pre-sprint vs sprint work; baseline procedure
  COMPETITION_REQUIREMENTS.md    official sprint requirements (verified 2026-10-17)
  PHASE0_REPORT.md               Phase 0 validation (GO / PARTIAL)
  PHASE0_5_REVIEW.md             Phase 0.5 corrective review
  PHASE0_6_REVIEW.md             protocol hardening, validation, Phase 1 plan
```

## Competition constraints honored

PDF report on the official template, abstract ≤ 150 words, authors +
affiliations, a required "Limitations and Dual-Use / Ethical Considerations"
appendix, disclosure of prior work and AI assistance, and the submission
deadline 2026-10-25 23:59 AoE = 2026-10-27 00:59 NZDT
(`docs/COMPETITION_REQUIREMENTS.md`).

The linked template's 150–250-word advice conflicts with Guidelines: use
≤150 words. Submission availability is **UNRESOLVED**; registration controls
do not prove an open submission window. No registration/submission was performed.

## Boundaries

Sandbox-only synthetic effects; no real issue trackers or payments; no
third-party mutations; no external side effects; no commit/push/tag/deploy
without explicit user authorization.
