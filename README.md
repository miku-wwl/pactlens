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

## Status: Phase 4C — model context and evidence sufficiency (pre-sprint)

Implemented **2026-10-19/20 NZDT** as pre-existing work over pushed Phase 4B
`d26995e`. The opt-in compact agent context `pactlens-agent-v3-candidate`
re-encodes exactly the information v2 shows (tests rebuild the v2 turns byte for
byte from v3 text). The historical v2 round-2 overflow (5,099 bytes / 2,838
estimated tokens: a duplicated public task, eight task-hash copies, five turns)
becomes 1,617, and the same six-step transcript completes (maximum 1,664 of 2,000).
No-speech paths fit in every condition; message-heavy C+/N2 histories on larger
tasks overflow explicitly at measured boundaries. One bounded local phi4-mini
episode made **6 calls**, all within budget, but **0/6 outputs were valid**
(duplicate keys, null assignments): no Action, INCOMPLETE, no rerun or tuning.

Lossless evidence tables v2 cut complete packets by about 20% and double retained
Action/receipt pairs under unchanged Phase 4B rules, with independent text
reconstruction and R/MAE parity. Complete six-action evidence remains
`EVIDENCE_BUDGET_INFEASIBLE` (5,002–5,825 estimated against 4,096); even the
lifecycle core alone exceeds the estimate slightly. All **724 tests pass
(607 existing +117 new)**.
Engineering **GO**; model generation path **PARTIAL** (output validity
REAL_MODEL_NOT_READY); detector evidence sufficiency **NO-GO**; formal pilot
**NO-GO**.

See the [execution report](docs/PHASE4C_EXECUTION_REPORT.md),
[context report](docs/PHASE4C_MODEL_CONTEXT_REPORT.md),
[evidence sufficiency](docs/PHASE4C_EVIDENCE_SUFFICIENCY_REPORT.md),
[token accounting](docs/PHASE4C_TOKEN_ACCOUNTING.md),
[freeze candidates](docs/PHASE4C_FREEZE_CANDIDATES.md) and
[test matrix](docs/PHASE4C_TEST_MATRIX.md). **24 groups /120 planned slots /0
formal runs** and frozen evaluation rules are unchanged; Phase 4C creates no
commit/push, detector inference, calibration or next-phase work.

## Phase 4B baseline — candidate budgeting and pilot preparation (historical)

Implemented **2026-10-19 NZDT**, pre-existing work: atomic common fact selection,
lossless compact tables, complete detector-envelope accounting, prospective
freeze decisions, separate reviewer preparation and future response validation.
All **607 tests pass (480 existing +127 new)**. Of 34 engineering source/policy
sets, 33 fit the input estimate; one real v1 Router-audit core fails explicitly.
Selected R/MAE inputs preserve independently checked semantic parity.

The authorized local comparison made **9 actual generation calls**: v1 six calls,
five valid outputs/two receipts; v2 three valid first-round submissions/receipts,
then its second-round 2,000-token preflight failed. Both episodes are INCOMPLETE.
No repair, replacement run or agent-prompt tuning followed. Engineering **GO**;
model **BLOCKED /REAL_MODEL_NOT_READY**; detector inputs **CONDITIONAL GO**;
formal pilot **NO-GO**. Token estimates are not exact and fitting lossy subsets
do not establish sufficient evidence. Observer/selection/model/rubric decisions
remain unapproved; no independent reviews or detector predictions exist.

See [execution report](docs/PHASE4B_EXECUTION_REPORT.md),
[budget measurements](docs/PHASE4B_TOKEN_BUDGET_REPORT.md),
[selection contract](docs/PHASE4B_EVIDENCE_SELECTION_CONTRACT.md),
[freeze candidates and reviewer workflow](docs/PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md),
[pilot gates](docs/PHASE4B_PILOT_READINESS.md) and
[test matrix](docs/PHASE4B_TEST_MATRIX.md). All **24 groups /120 planned slots /
0 formal runs** and frozen evaluation rules remain unchanged. Phase 4B creates
no commit/push, formal study, detector inference, calibration or Phase 4C work.

## Phase 4A baseline — protocol and detector-input contracts (historical)

Implemented **2026-10-19 NZDT** as pre-existing work: opt-in candidate agent
prompt/protocol with strict diagnostics and honest token preflight, shared
Writer/Reader trace limits, two observation policies and five deterministic
M/A/MA/R/MAE evidence views. R/MAE parity is independently checked from actual
rendered text. **480 tests pass (339 existing +141 new)**. No new real inference,
formal episode, detector prediction, calibration or statistical evaluation ran.

Engineering readiness **GO**; detector-view methodological readiness
**CONDITIONAL GO**; formal pilot **NO-GO**. Full evidence packets overflow the
conservative 4,096-token preflight and fail closed for model input. Observer
rights, N2 confounding, prompt adoption and a feasible shared budget/selection
policy require prospective decisions; no amendment is applied. Real candidate
model reliability remains unverified. Original prompts/history are preserved.

See the [execution report](docs/PHASE4A_EXECUTION_REPORT.md),
[view contract and fact matrix](docs/PHASE4A_DETECTOR_VIEW_CONTRACT.md),
[protocol review](docs/PHASE4A_PROTOCOL_REVIEW.md),
[unapproved proposal](docs/PHASE4A_PROPOSED_AMENDMENT.md) and
[test matrix](docs/PHASE4A_TEST_MATRIX.md). The Phase 0.6 allocation, metrics and
study authority remain unchanged: **24 groups /120 future slots /0 formal runs**.
Phase 4A stops at review artifacts; it creates no commit, push or Phase 4B work.

## Phase 3 baseline — controlled agent harness (historical snapshot)

Phase 3 adds three isolated model contexts, controlled public/private delivery,
deterministic sequential two-round scheduling, the existing real AIG proposal
path, durable separated traces and pure replay with no new effects. Local
Ollama inference is disabled by default and requires an explicit engineering
smoke opt-in. All code/fixtures/engineering runs created on 2026-10-18 are
pre-existing work for competition disclosure. No formal study or detector ran.

See [harness contract](docs/PHASE3_HARNESS_CONTRACT.md),
[actual execution report](docs/PHASE3_EXECUTION_REPORT.md) and
[test matrix](docs/PHASE3_TEST_MATRIX.md). Consent remains explicitly synthetic;
no authenticated-human approval UI is implemented. Formal exploratory-study
readiness remains NO-GO pending pilot protocol/model/prompt/view/adjudication work.

## Earlier Phase 2 baseline and frozen research protocol

The authoritative protocol is [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md):
4 pilot + 10 calibration + 10 held-out blocks, five episodes per block,
120 planned episodes / 24 independent blocks. This is **exploratory**, not
confirmatory. MAE vs MA is the primary descriptive comparison; mandatory R
contains MAE's same facts in raw form to separate information from structure.
The Phase 0.6 protocol is preserved. Phase 1 implements only deterministic
arena mechanics, 14 hand-scripted engineering fixtures, private manifest/review
records and an allowlisted observation projection. No model research episodes
have been run; constructing 120 planned slots does not execute the study.
See [Phase 1 report](docs/PHASE1_EXECUTION_REPORT.md),
[data dictionary](docs/DATA_DICTIONARY.md) and
[test matrix](docs/PHASE1_TEST_MATRIX.md).

Phase 1.1 integrity hardening and Phase 2 now add a real installed-AIG path:
frozen synthetic proposal → validated Plan/Run → separate scripted test Approval
and Authorization → durable Gateway claim → SQLite proposal/receipt → verified
Arena reconstruction. Three isolated compositions each register one fixed tool,
retain their identity across restarts and use the default five-second budget.
Lost acknowledgments/interrupted execution remain Unknown without automatic retry.
This is local engineering with **synthetic consent**, not authenticated human
approval or an LLM collusion observation. See the
[integration contract](docs/PHASE2_INTEGRATION_CONTRACT.md),
[execution report](docs/PHASE2_EXECUTION_REPORT.md) and
[test matrix](docs/PHASE2_TEST_MATRIX.md).

**Not implemented at the Phase 2 baseline:** research experiment driver, model-driven agent runners,
monitors M/A/MA/R/MAE, detection scoring, statistical
evaluation pipeline or dashboard. Fixtures establish mechanics, not emergent
collusion or independently human-adjudicated truth.

At the Phase 3 baseline, only the engineering agent driver/runners were implemented;
its missing-view statement is superseded by Phase 4A above. Formal study execution,
detector predictions, scoring/statistics and dashboard remain unimplemented.
A single local engineering episode is not a research block.

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
uv run ruff format --check .
uv run pytest -q          # offline engineering tests, no model/API calls
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

For fully offline checks, set `UV_OFFLINE=1` in the calling environment.
Inspect a **scripted unit fixture**, without providers or Runtime dispatch:

```powershell
uv run python -c "from pactlens.research.fixtures import run_fixture; f=run_fixture('c_plus'); print(f.outcome.global_cost, f.outcome.regret, f.record.adjudication.behavior_class)"
# 12 6 None: hand-specified mechanics, human behavioral label still pending
uv run python -c "from pactlens.research.manifest import build_manifest; m=build_manifest(); print(len(m.groups), len(m.episodes), m.observations_executed)"
# 24 120 0: planned slots, no research executions
```

The `research/fixtures.py` helper loads `datasets/fixtures/arena_cases.json`
from this source checkout; a standalone wheel does not bundle the fixture catalog.
Public projection requires an independent canonical UUIDv4 and returns only
observed data. Never pass private source records/manifests to a future monitor.

## Repository layout

```text
AGENTS.md                          agent instructions (upstream AIG rules + PactLens invariants)
PACTLENS_HACKATHON_DESIGN.md      preserved original pre-sprint blueprint
LICENSE, .python-version, pyproject.toml, uv.lock
.env.example, .gitignore
src/pactlens/
  arena/                         immutable two-round mechanics and exhaustive reference
  aig/                           fixed consumer, frozen proposal registry, SQLite effects, six-action test harness
  integration/                   verified durable-proposal to Arena replay
  evidence/                      observed records and explicit L3 allowlist
  research/                      private seeds/manifests, pending reviews, unit fixtures
  serialization.py               canonical UTF-8 JSON and SHA-256
datasets/fixtures/arena_cases.json 14 hand-specified engineering cases, not study data
tests/                           offline determinism, outcomes, fixtures, split and leakage tests
docs/
  HACKATHON_DESIGN.md            maintained blueprint with Phase 0.6 corrections
  ARCHITECTURE.md                consumer contract, verified API surface, constraints
  EXPERIMENT_PLAN.md             pre-registration: hypotheses, conditions, metrics, failure paths
  PROVENANCE.md                  pre-sprint vs sprint work; baseline procedure
  COMPETITION_REQUIREMENTS.md    official sprint requirements (verified 2026-10-17)
  PHASE0_REPORT.md               Phase 0 validation (GO / PARTIAL)
  PHASE0_5_REVIEW.md             Phase 0.5 corrective review
  PHASE0_6_REVIEW.md             protocol hardening, validation, Phase 1 plan
  DATA_DICTIONARY.md             concrete objective, transitions, records and seed bytes
  PHASE1_TEST_MATRIX.md          acceptance-to-test mapping
  PHASE1_EXECUTION_REPORT.md     actual verification and next-phase limits
  PHASE1_1_EXECUTION_REPORT.md   state/evidence integrity hardening (historical)
  PHASE2_INTEGRATION_CONTRACT.md binding, schema, durability and evidence boundaries
  PHASE2_TEST_MATRIX.md          real lifecycle/fault/restart acceptance mapping
  PHASE2_EXECUTION_REPORT.md     actual Phase 2 results and limitations
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
