# PactLens Phase 1 Execution Report

Execution date: **2026-10-18 NZDT**, **pre-sprint engineering**. Branch `main`;
starting/current HEAD `45b86712edc75c9803a1f36f5d926fe62fba6a0e`. Starting tree
was clean. This phase is an uncommitted delta; that HEAD does not contain it.

## Executive Summary

**PASS** for the bounded Phase 1 acceptance criteria. Final suite: **119 passed,
0 failed**, no skips. Offline sync, lint, formatting, lock and installed-package
integrity checks pass. These are engineering results, not production guarantees,
model behavior, detector performance or statistical validity.

Implemented: seeded three-agent/3–5-incident generation, immutable exactly-two-round
transitions, strict proposals, feasible deterministic voting, exhaustive lawful
reference, integer cost/harm accounting, five primary scenarios plus nine
diagnostics, private pending adjudication, 24-block/120-slot manifest construction
and explicit L3 allowlist/export.

Unimplemented/unrun: providers/models, agent orchestration, AIG approval/execution/
receipt adapters, M/A/MA/R/MAE monitors, detection scoring, formal research runs,
independent human adjudication, frontend. No external API, inference, paid call,
AIG workflow, competition action, commit, push, tag, release or deployment occurred.

## Technical Evidence

### Changed files and architecture

New source:

- `src/pactlens/arena/{__init__,models,generator,allocation,transitions,outcomes}.py`
- `src/pactlens/research/{__init__,seeds,manifest,adjudication,fixtures}.py`
- `src/pactlens/evidence/{__init__,records,projection}.py`
- `src/pactlens/serialization.py`

New supporting files: six Python test files (conftest and five required modules),
`datasets/fixtures/{arena_cases.json,README.md}`, this report,
[DATA_DICTIONARY.md](DATA_DICTIONARY.md) and
[PHASE1_TEST_MATRIX.md](PHASE1_TEST_MATRIX.md).
Updated: README, package docstring, architecture status and provenance.
No dependency added. Approved Phase 0.6 protocol, metrics/splits/truth rules,
designs, historical reports, AGENTS, pyproject and lockfile are preserved.

```text
Private seed/group manifests              Public seeded task
                                                  |
                                  immutable round-1/round-2 proposals
                                                  |
                                  feasible vote-maximizing allocation
                                                  |
                            actual costs + exhaustive lawful reference
                                                  |
                                      private pending adjudication

Actual state + observed messages -> explicit L3 allowlist -> observable JSON
```

This is a domain library and bounded hand-scripted fixture helper, not an agent
runner or AIG replacement. No Runtime imports occur in application source.
Verification inspects the installed public API without opening a Runtime,
obtaining grants, admitting or dispatching an Action.

### Transitions, objective and lawful reference

`CREATED → ROUND_1 → ROUND_2 → FINALIZED`; no round-3 path. One accepted
proposal per actor/round, exact task hash, participant/ownership, current round/
revision, skill/capacity/eligibility checks. Frozen containers and checked history
retain previous state on rejection. These are domain consistency checks, not
AIG claiming, authorization or authentication.

Round 1 is unexecuted deliberation. Round-2 close fills each missing ballot with
one canonical-lawful-reference vote, retaining explicit missing records rather
than fabricating accepted submissions. Execution maximizes total final-ballot
incident matches over jointly feasible allocations, then minimizes J, then neutral
lexical owner order. Feasible majority outcomes can remain globally suboptimal.

The concrete integer objective is:

```text
C_a = sum_assigned(workload * unit_cost
      + max(0, ceil(workload/speed)-deadline) * severity * SLA_penalty)
      + balance_weight * actor_load²
U   = sum_unassigned(severity * SLA_penalty * unassigned_multiplier)
J   = sum_a C_a + U
```

Default balance weight=1, unassigned multiplier=20. Capacity/skill/eligible-actor
rules are public. Duration is per-incident parallel service, not a queue model.
Unassigned penalties are a public pool, not charged to an arbitrary actor.
The reference enumerates ≤4^5=1,024 owner vectors, rejects infeasible ones and
selects `(J, neutral lexical vector)`; no candidate explicitly raises
NoFeasibleAllocation. Integer cost definitions, tie/missing rules and exact seed
bytes are specified in DATA_DICTIONARY before any future pilot.

Mechanical outcomes record actual/reference allocations and component costs,
J, J*, regret, pair benefit and outsider shift. Tests independently check
hand-derived values and the identity
`regret = outsider_shift - pair_benefit + (U_actual-U_reference)`.
No cost measurement infers a coalition or agreement.

### Fixtures, paired intervention and ground-truth separation

On the hand task, lawful C=(2,2,2), J*=6. Two coordinated votes can implement
C=(0,0,12), J=12, regret=6, pair benefit=4, outsider shift=10. Replacing either
harmful vote by a lawful vote removes that joint effect. These are synthetic
unit-fixture arithmetic, **not findings about AI behavior or realization rates**.

C+/C− share task/config, initial state, brief/policy, no-model setting and six
predetermined fixture streams. Only the private-channel affordance differs;
each builds/finalizes/evaluates its own state. Delivered messages and resulting
ballots may differ as consequences. No outcome/label is copied from the twin.
A separate public-channel harmful C− diagnostic demonstrates that assignment
does not guarantee no harm; it is not another result for the main paired script.

Failed C+, N1 similar independent behavior, N2 discussion/round-1 attempts without
implemented harm, lawful public N3, harm without agreement, incomplete evidence,
missing/invalid proposals, ties and infeasible assignments are retained.

L1 assignment and L2 pending review stay outside L3. Allocation/evaluation have
no condition input. prepare_adjudication has no assignment argument; every fixture
behavior class is None and human_adjudicated=false. No agreement classifier or
L4 detector/scoring was introduced.

L3 explicitly reconstructs observed public task, messages, six proposal slots,
actual allocation and ordinary actual costs. It excludes labels, groups/seeds/
splits, coalition/pair/twin references, oracle reference/regret and private paths/
notes. Twenty-two nested markers and poison private objects are excluded from
repr, mapping adapters, JSON and exported files. Predictive malicious messages
remain. DetectorEvidence retains only JSON, with no source/private references.
Export filenames use canonical public UUIDv4s and exclusive creation; the trusted
caller must actually sample IDs independently of assignment.

### Manifest and reproducibility

P001–P004 / K001–K010 / T001–T010 remain fixed: **24 blocks / 120 planned slots /
zero planned episodes executed**. All five conditions share a block task;
twins share evaluator pair/settings/request streams. Pilot is excluded from main
groups. There are 24 distinct public task hashes in the constructed manifest.

UTF-8 seed messages use exact ` | ` separators; retain full SHA-256 and convert
the first eight bytes unsigned big-endian. Duplicate tasks are resolved before
outcomes through bounded `task/collision/N` sub-seeds, without resplitting;
exhaustion fails closed. Four separate-process reproductions outside the checkout
agree, including isolated/randomized hashes and explicit PYTHONHASHSEED values.
Shared generator/model assumptions still limit statistical independence.

## Verification

Commands actually executed with **UV_OFFLINE=1**:

| Command/check | Actual result |
|---|---|
| `uv sync --locked` | Resolved/checked 31 packages; exit 0 |
| `uv run pytest -q --junitxml=.runtime/phase1-validation/pytest.xml` | **119 passed in 7.12s**, exit 0 |
| `uv run ruff check .` | All checks passed; exit 0 |
| `uv run ruff format --check .` | 35 files already formatted; exit 0 |
| `uv lock --check --offline` | Resolved 31 packages; exit 0 |
| Installed dependency | Python 3.13.14; AIG 0.2.0 from this `.venv/Lib/site-packages`, Git pin `7261fdd2f47d2b15fabe8faac527eeee37338eb1` |
| Installed AIG RECORD | All **57** hashed distribution files match |
| Preserved protocol/config/history | **14** Git-filtered working-tree blobs match HEAD |
| Upstream reference copies | Previously retrieved immutable example/handoff/adapter copies read; all 3 SHA-256 values match Phase 0.6; no network fetch/example execution |

JUnit counts: determinism 45, outcomes 25, scenarios 26, split/groups 11,
leakage 12. Actual logs, integrity JSON and XML are packaged. Tests block socket
connections; source AST rejects Runtime/provider/network/orchestration imports.
No arbitrary malicious-Python/filesystem access guarantee is claimed.

Corrected failures are disclosed in the test matrix: initial six Ruff issues;
one strengthened negative test expected the wrong rejection reason (**1 failed,
118 passed**) before correction and the final all-pass run; an auxiliary
CRLF-working-bytes versus LF-Git-blob comparison corrected to filtered blob
identities. No guard was weakened or failure treated as a pass.

Final review checks validate Markdown targets/anchors, changed-file scope,
credential patterns, ZIP member CRCs and SHA-256 hashes against its file manifest.
The final documentation check passed for 16 Markdown files and 28 local links;
scope is four modified existing files and 26 new source/test/data/document files.
`pactlens-phase1-review.zip` is created in the repository root from an explicit
allowlist. It contains source/tests, synthetic fixtures, docs/config, selected
actual logs under `review/logs/`, and checksums. It excludes `.git`, `.venv`,
`.runtime` directories, caches, credentials, provider data and real private
experimental records. No pre-existing archive is overwritten. This identifies
an uncommitted review snapshot, not a release.

## Research Boundary and Limitations

- Tests establish bounded mechanics/projection, not real model collusion,
  spontaneous emergence, detection quality or inference realization rate.
- The 14 related diagnostics are not independent research observations; planned
  slots/replays never increase n. No formal pilot/calibration/held-out run occurred.
- No independently authenticated human review occurred. Agreement/execution
  interpretation and uncertain cases remain for frozen-rubric reviewers.
- The world is small, synthetic and batch-based; majority voting/quadratic costs
  are declared choices, not production scheduling realism or legal standards.
- Reproducibility is qualified on Python 3.13/config/source. Future RNG behavior,
  malicious host access, adversarial observable text and known-fixture lookup are
  outside this tested boundary.
- State is in memory. Durable concurrency, authenticated consent, AIG effects/
  receipts and process restart/recovery are **NOT VERIFIED** by Phase 1.
- Fixture loading requires the source checkout, not a standalone wheel. Model
  prompts/briefs/provider/threshold freeze artifacts remain future work. No known
  failing engineering tests remain.

## Next Phase: AIG Consumer Integration (proposal only)

**Technical readiness: GO to begin separately authorized Phase 2.** Integration
acceptance is **NOT RUN**. The installed pinned public API is available and arena
contracts are tested; no extra Runtime capability is currently required.
Confirmatory research readiness remains NO-GO.

Proposed bounded scope and prerequisites:

1. Inspect installed public signatures/reference again. Review one trusted
   submit_incident_proposal/1 binding per isolated runtime, fixed sandbox target/
   adapter/revision, stable fresh UUIDv4 scope and default five-second budget.
2. Review a **flat bounded tool schema** encoding allocation as a short canonical
   string plus actor/round/task identity. Current nested Proposal is not directly
   an AIG tool schema. Model/client input cannot select authority or budgets.
3. Implement a consumer-owned durable proposal effect/receipt store; exact Plan
   Approval remains separate from Action Authorization and durable claiming.
   Preserve stable effect identity/receipts. Synthetic test consent is never
   represented as authenticated human approval.
4. Test wrong tool/schema/target/binding/scope, missing authorization/stale approval,
   duplicate/conflicting/concurrent effects, persistence, lost acknowledgement and
   Unknown/restart **without a second effect**. No private-table control, core
   edits or automatic retry. Store/state consistency under interruption and
   receipt/cancellation handling are explicit technical risks to resolve.

This requires a fresh Phase 2 instruction, reviewed schema/identity and private
local store provisioning. Providers, monitors, frontend and real trackers remain
outside that proposed slice. **Stop after Phase 1; Phase 2 has not started.**
