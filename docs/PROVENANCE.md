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

## 5. Phase 1 push confirmation and Phase 1.1 hardening — 2026-10-18 NZDT

Additive update: §4 and the original Phase 1 execution report describe the
earlier uncommitted development snapshot. They are preserved as historical
records; the subsequent user-authorized commit/push changes the current state.

Read-only verification during Phase 1.1 confirms:

- Starting tree clean on `main`; local HEAD and `origin/main` both
  `56470b3f888ca69377f5962a224d6687730b8463`.
- That commit exists locally with subject `Phase 1: add deterministic incident
  allocation arena`. Author/committer metadata records
  `2026-10-18T09:22:47+13:00`; Git metadata is not independent timing proof.
- The local `origin/main` reflog records `update by push` for that commit.
  A fresh `git ls-remote origin refs/heads/main` via per-command GitHub SSH-over-443
  configuration returned the same full SHA. This confirms the observed remote
  branch on the verification date, not its immutable future state. No permanent
  remote/SSH configuration was changed.
- Phase 1 engineering therefore was pushed before the sprint. Phase 1.1 remains
  an **uncommitted working-tree delta over that SHA**, with no new commit/push.

Phase 1.1 implemented on **2026-10-18 NZDT**, entirely pre-sprint:

- New `src/pactlens/arena/_domain.py`: unchanged primitive domain definitions
  extracted to avoid an allocation/state import cycle; public imports retained.
- Modified `arena/{models,allocation,transitions,outcomes}.py`: canonical final
  allocation checks and complete stored-outcome validation; allocation module
  changes only its domain import, preserving cost/voting/tie/fallback semantics.
- Modified `evidence/{records,projection}.py`, `research/fixtures.py`: optional
  source-bound logical capture journal, explicit observation-v2 event allowlist,
  legacy ordering uncertainty and new scripted-capture call positions.
- New `tests/test_arena_state_integrity.py`,
  `tests/test_evidence_event_ordering.py`; modified `test_labels_no_leakage.py`
  to retain valid mechanics while injecting private markers and cover v2 fields.
- Updated DATA_DICTIONARY, ARCHITECTURE, PHASE1_TEST_MATRIX and this provenance;
  new `docs/PHASE1_1_EXECUTION_REPORT.md`; narrow root review-ZIP ignore rule.

All original 14 fixture states, messages, outcomes, settings and rejected
attempts match the committed baseline under canonical serialization. Frozen
protocol, original reports, fixture catalog, dependency configuration and lock
remain unchanged. Full evidence and remaining limits are in the Phase 1.1 report.
Formal pilot/calibration/held-out episodes remain **0 executed / NOT RUN**;
120 planned slots across 24 blocks are unchanged. No model inference, detector,
independent human adjudication or AIG execution workflow ran.

Future review ZIPs belong outside the repository; root `.gitignore` now ignores
`/pactlens-phase*-review.zip`. The tracked `pactlens-phase1-review.zip` remains
tracked and byte-identical. Removing it from future versions (e.g. `git rm
--cached` in a separately reviewed commit) requires separate authorization;
no deletion, untracking or history rewrite was performed. Phase 1.1 review ZIP
is outside the repository and is not a new Git artifact.

## 6. Phase 1.1 pushed baseline and Phase 2 integration — 2026-10-18 NZDT

Additive current-state entry; prior reports/§5 retain their original development
snapshot statements. Before Phase 2 modifications, tree was clean on `main`.
Local HEAD, `origin/main` and a fresh HTTPS `ls-remote` confirmed
`6a879bb3fb19d47332ae2aa7376ead4d12b57d90`, subject `Phase 1.1: harden state
integrity and observable event ordering`. Phase 1.1's user-authorized HTTPS
push is thus confirmed; this SHA is the Phase 2 starting baseline.

Phase 2 implementation on **2026-10-18 NZDT** is pre-sprint engineering:

- New `src/pactlens/aig/{__init__,contract,effect_store,executor,consumer,workflow}.py`:
  reviewed fixed binding, deterministic provider, persisted proposal snapshots,
  independent SQLite effects/receipts, real installed-AIG composition and a fixed
  six-submission synthetic-consent engineering harness.
- New `src/pactlens/integration/{__init__,arena_bridge}.py` and
  `src/pactlens/evidence/aig_adapter.py`: verified effect replay through existing
  Arena transitions, plus the explicit Observation-v2 execution extension.
- Seven `tests/test_aig_*.py` modules and `tests/aig_helpers.py`. Existing conftest
  permits only stdlib socketpair IPC needed by Windows asyncio while blocking
  application connections; its new fixture provisions isolated synthetic stores.
  The existing source-import guard permits only public AIG imports inside the
  new consumer package, retaining network/model/orchestrator prohibitions.
- New Phase 2 integration contract, execution report and test matrix; updated
  README, ARCHITECTURE, DATA_DICTIONARY and this additive provenance entry.

All Arena mechanics and Phase 1.1 evidence source files remain byte-identical.
No research split, prompt, threshold, statistical rule or fixture catalog changed.
AIG remains installed 0.2.0 at the immutable 7261fdd2 pin; dependency config and
lock remain unchanged. Upstream references were inspected, never copied into
PactLens or modified. Core Run/approval/claim/recovery logic is reused, not owned
by this consumer. Test-only direct executor calls qualify the consumer port;
application/harness dispatch always goes through the actual Gateway.

These are genuine local SQLite/AIG lifecycle tests with deterministic planning
and **synthetic consent**, not LLM observations, human authentication or harmful
collusion findings. Formal pilot/calibration/held-out observations remain
**0 executed / NOT RUN**, with 120 planned slots across 24 blocks unchanged.
Phase 3 harness, model-driven agents, monitors, scoring and dashboard remain
unimplemented. No commit, push, tag, release, deployment or competition action
occurred during Phase 2; HEAD remains the starting baseline and the new work is
an uncommitted delta. Review archive is outside the repository; historical
tracked ZIP is preserved.

## 7. Pushed Phase 2 baseline and Phase 3 harness — 2026-10-18 NZDT

Additive entry: §6 and PHASE2_EXECUTION_REPORT retain the earlier uncommitted
snapshot. Phase 2 was subsequently committed/pushed on the user's instruction.
Fresh local HEAD, `origin/main` and live HTTPS remote verification all return
**`1aec45859c901994a08478800498b9925237dce8`**, subject `Phase 2: integrate AIG
consumer with durable proposal receipts`. Starting tree was clean. This is the
Phase 3 baseline; Phase 3 creates no commit, push, tag, release or deployment.

Phase 3 source, tests, fixtures, model prompt templates, dry runs, local-model
engineering trace and documentation were developed on **2026-10-18 NZDT**, before
October 23. They are **pre-existing work**, never sprint-created contributions:

- New `agents/{models,provider,prompts,ollama_provider}.py`: bounded output,
  independent contexts, provider metadata and numeric-loopback-only transport.
- New `experiments/{conditions,channels,harness,traces,replay,smoke}.py`:
  engineering-only configuration/seeds, controlled delivery, sequential two-round
  execution, durable traces and zero-effect replay. Package markers added.
- New `aig/submission.py` calls the existing consumer public composition, real
  Run/Approval/admission/Authorization/Gateway and existing receipt verification.
  Original Phase 2 AIG modules, Arena, bridge and base evidence files preserved.
- New `evidence/harness_adapter.py`: explicit observable communication inventory,
  completeness and temporal uncertainty, without private L1/L2 serialization.
- Six new test modules plus fake-generation helper; the existing import guard
  permits stdlib `http.client`/`urllib.parse` only in the reviewed local adapter.
- New Phase 3 contract/report/test matrix; additive architecture/data/provenance
  and README updates; local-only `.env.example`, with no credentials.

Actual validation, permitted local inference and remaining limitations are
recorded in PHASE3_EXECUTION_REPORT. All automated AIG consent is synthetic,
not authenticated human consent. Raw private traces/SQLite/capabilities remain
outside source and the review package. Safe engineering templates and selected
validation summaries are included for reproducibility, not private research logs.

The official allocation remains **24 groups /120 future slots /0 formal
executions**. Frozen protocol, split membership, thresholds, old reports,
dependency configuration/lock, AGENTS and historical tracked ZIP remain intact.
No official outcome tables, held-out execution/tuning, detector or Phase 4 work
exists. Engineering replay is not a fresh observation or receipt. All behavioral
adjudication remains pending, including failed positive controls.

## 8. Pushed Phase 3 baseline and Phase 4A — 2026-10-19 NZDT

Additive current-state entry; all earlier reports/sections retain their original
snapshot dates and results. Phase 3 was subsequently committed and pushed on
the user's explicit instruction. Before Phase 4A, the working tree was clean;
local HEAD, `origin/main` and live HTTPS remote all confirmed
**`6bf93a996476e6433eedc3fa11784703bf61a31a`**, subject `Phase 3: add controlled
agent harness and replay traces`. This is the actual Phase 4A starting baseline.

Phase 4A work was developed on **2026-10-19 NZDT**, before October 23. It is
**pre-sprint engineering / pre-existing work**, never sprint-created contribution:

- New candidate public-task prompt/examples, protocol version/hash/diagnostics
  and token preflight; original v1 system prompt and historical trace meaning
  retained. Six existing agent/harness/replay/trace source files updated.
- New `agents/{budgets,protocol_diagnostics}.py` and
  `evidence/{observation_policy,inventory,views,renderers,parity}.py`; explicit
  observer rights, bounded immutable fact inventory, five input views and
  independently reconstructed R/MAE semantic parity. These are not detectors.
- Safe `protocol_v2_cases.json`, nine new regression modules and one helper;
  original tests unchanged. **339 existing +141 new =480 passing cases**.
- Phase 4A execution report, view contract, protocol review, test matrix and a
  **NOT APPROVED / NOT APPLIED** prospective-amendment proposal. Additive README,
  architecture, dictionary and provenance updates. Actual validation logs and
  safe synthetic exports packaged outside the repository.

One additional fake-model, six-step engineering audit exercised the real local
AIG proposal/receipt path and both view policies, with six verified local
receipts. It is synthetic response generation with scripted consent, **zero
actual LLM inference**, not a formal episode or authenticated human approval.
Unit tests likewise use deterministic/fake planning. No private trace, SQLite
store, capability or raw private model prompt enters the review archive.

The separate **2026-10-18 Phase 3 actual local-model observation** remains one
six-call Ollama engineering episode, one real proposal receipt, INCOMPLETE.
Phase 4A only read/replayed that trace: original bytes, L3 and stored counts
unchanged; no additional model/Gateway/effect call. No new actual inference was
authorized or performed and no model-reliability gain is claimed.

Formal pilot, calibration and held-out executions remain **0 / NOT RUN**, across
the unchanged **24 groups /120 future slots**. No detector prediction, score,
calibration, statistical evaluation or Phase 4B work exists. N2 blocking, C+/C−
pairing, Arena/fallback/objective, truth, thresholds, splits and abstention rules
remain unchanged. The frozen experiment plan, AIG consumer/store/receipt source,
dependency pin/lock, AGENTS, original test files, earlier reports and old review
archives are preserved. Installed AIG 0.2.0's 57 RECORD hashes were verified;
its full immutable pin and five-second budget remain unchanged.

Observer choice, candidate adoption, N2 alternatives and a feasible token/selection
policy require future prospective decisions. No alternative condition or lossy
selection is applied. Phase 4A remains uncommitted; no commit, push, tag, release,
deploy or submission was performed. HEAD remains the pushed Phase 3 baseline.
The external review ZIP and verification receipt describe this working snapshot.
