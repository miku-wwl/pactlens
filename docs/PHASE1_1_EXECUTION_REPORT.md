# Phase 1.1 — State & Evidence Integrity Hardening

Implementation date: **2026-10-18 NZDT**. Overall status: **PASS** for this
pre-sprint engineering scope. No commit, push, tag, release, deployment, model
inference, formal research run or Phase 2 integration was performed.

## Findings and corrections

| Finding | Root cause | Correction |
|---|---|---|
| P1: substituted final allocation accepted | State validation checked lifecycle structure but not the deterministic consequence of ballots | Validate every accepted ballot and compare final allocation with the existing `execute_allocation` result at construction; recheck transition and L3 boundaries |
| P1: cross-event chronology absent | Message order and arena history were separate, while proposal slots sorted by actor were storage layout | Optional source-bound logical capture journal; observation-v2 explicit event allowlist and recorded/partial/source-local ordering contract |
| P2: provenance described earlier uncommitted Phase 1 | Documentation preceded the user-authorized commit/push | Additive provenance entry confirms local/tracking/live remote SHA, records all Phase 1.1 work as pre-sprint, and preserves historical reports |

## Files changed and scope

- New `arena/_domain.py`: primitive definitions extracted unchanged; `models`
  reexports existing public names. This keeps dependency direction acyclic:
  `models → allocation → _domain`. Allocation does not construct states.
- Modified `arena/models.py`, `transitions.py`, `outcomes.py`: state boundary
  validation and canonical stored-outcome comparison. `allocation.py` changes
  only its primitive-domain import; its executable rules are unchanged.
- Modified `evidence/records.py`, `projection.py`, `research/fixtures.py`:
  optional journal, fact-content binding, source validation, allowlisted events,
  and explicit capture calls in new scripted fixture playback.
- New `test_arena_state_integrity.py` (23 cases),
  `test_evidence_event_ordering.py` (22); adapted existing 12 leakage cases.
- Updated DATA_DICTIONARY, ARCHITECTURE, PHASE1_TEST_MATRIX, PROVENANCE;
  this report; narrow `.gitignore` pattern for future root review archives.

No dependency, fixture catalog, generator, allocation objective, ballot policy,
tie-break, missing-proposal fallback, adjudication rubric, experimental split,
sample allocation, statistical threshold or evaluation rule changed.

## Mechanical state consistency

A finalized state must have valid revision/history metadata, exactly the
accepted actor/round slots and feasible proposals for its public task. Its final
allocation must equal `execute_allocation(task, accepted_round_2_ballots)`.
Missing ballots still use the existing lawful-reference fallback; round-1
ballots never execute. A valid majority may still select J=12 instead of J*=6.
The invariant does **not** force the lawful optimum.

Reconstruction via `dataclasses.replace` rejects lawful-optimum substitution,
another feasible substituted allocation, changed ballots inconsistent with the
retained final allocation, incomplete or invalid history, and contradictory
revision/closure/status metadata. Round-1 reconstructed ballots also undergo
feasibility checks. Projection revalidates even objects deliberately mutated
after construction in negative tests. No restoration/deserialization API or
durable arena store exists in Phase 1; future restoration must use these checks.

Stored mechanical outcomes reside in `AdjudicationRecord`, not ArenaState.
`EpisodeRecord` construction and projection compare the complete stored outcome
with a fresh `evaluate_outcome` for the final allocation and declared evaluator
pair, including actual/reference costs, optimum, regret and burden/benefit
components. Missing adjudication is allowed; untyped supplied adjudication or
outcome on an unfinalized state is rejected. Reviewer notes/decisions remain
private and do not determine observations.

## Evidence ordering and supported claims

The full field/payload contract is in
[DATA_DICTIONARY.md](DATA_DICTIONARY.md#phase-11-observable-event-ordering-contract).
Observation schema changes from v1 to **v2**, preserving existing six fields
and adding `events`/`event_ordering`. Consumers checking exact v1 schema keys
must opt into v2; no detector views exist to migrate yet.

Events cover observed messages, round opening, actual accepted proposals,
round-1 closure, atomic round-2 closure/final allocation and public outcome.
Every event has type, neutral actor or null, public round, bounded payload,
source sequence and optional logical position. IDs encode only source and local
sequence. No actor-sorted proposal-slot layout is treated as chronology.

Within each source stream, source sequence establishes order. Captured logical
positions establish cross-stream order when unequal; equal positions across
streams represent unresolved batching. Null means no captured position. Array
storage order groups sources and never asserts a total timeline. Round/lifecycle
rules provide only their actual causal bounds, including when a closure capture
is missing; they do not order same-round messages relative to proposals.

New fixture playback explicitly records STARTED, scripted messages, each
successful proposal/closure, then final public accounting. These are real
invocation positions of this scripted helper, not real-agent communications or
retroactive proof of old fixture chronology. Legacy journal-free records keep
source-local order and null cross-stream positions. Partial capture is explicit;
message completeness is a separate flag. Missing messages/proposals are never
fabricated. Final close and allocation share one transition; no sub-event order
is invented. Public outcome is deterministic synthetic arena accounting, not an
independently verified external-provider effect or receipt.

Both message-before-proposal and proposal-before-message are supported inside
an open round, without new turns. Multiple proposals preserve actual acceptance
order even for actors submitted in reverse identifier order. Message capture
after its round closes is unsupported and rejected. Future M/A/MA/R/MAE must
share this observation inventory and uncertainty; no monitor or privileged
MAE-only evidence was introduced.

## L3 isolation and evidence-record integrity

The projection explicitly constructs every field. It exports neutral public
task/actor/incident data, observed text and allocations, public actual costs and
ordering metadata. It exports no condition, coalition assignment, split/group/
seed, private pair/twin/fixture name, brief, adjudication, oracle reference,
optimum, regret or internal journal digest. The same 22 private markers remain
absent from JSON, repr, defensive mappings, exported bytes and filenames.

The prior leakage test's two markers in numeric mechanics were moved to private
notes/nested oracle metadata, because inconsistent stored mechanics are now
intentionally invalid. Ten new outcome-mutation cases test rejection separately.
Opaque private metadata/manifest/path objects remain uninspected; supplied
adjudication now has a typed mechanical-validation contract. A deliberately
edited observed message without capture metadata remains visible; changing
captured text or proposal content while retaining its journal fails closed.

Mechanical consistency, evidence-record integrity, malicious-host security and
cryptographic authenticity are different claims. Journal SHA-256 values are
unkeyed content bindings and are not signatures. They detect mismatched facts,
references and positions, but a malicious in-process host can rewrite both
source and digest, remove the optional journal or replace a consistently
rewritten history. A journal-free valid same-winner ballot rewrite cannot be
distinguished from an original history. No authenticated capture, durable log,
cryptographic authenticity, tamper-proof persistence or arbitrary-Python
isolation is implemented or claimed. Existing hostile-observable-text and public
fixture-lookup limitations also remain.

## Actual verification

Python **3.13.14**, installed AIG **0.2.0** from this repository's `.venv`
site-packages, immutable source SHA
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`. Lockfile/direct-url identity and
all **57** hashed distribution RECORD entries verified. No AIG source changed.

All required checks executed with `UV_OFFLINE=1`:

| Check | Actual result |
|---|---|
| `uv sync --locked` | PASS, 31 resolved/checked packages |
| `uv run pytest -q --junitxml=.runtime/phase1_1-validation/pytest.xml` | PASS, **164 passed**, 0 failed/skipped/xfail, 14.48 seconds |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS, 40 Python files already formatted |
| `uv lock --check --offline` | PASS, 31 packages |
| Source and test compilation | PASS |
| Cross-process evidence serialization / opposite module import orders | PASS, two processes with distinct explicit hash seeds, outside checkout |
| Existing state/manifest reproduction | PASS, four separate-process cases retained |
| Baseline comparison | PASS, all 14 fixture states/outcomes/messages/settings/rejections exactly match committed Phase 1 canonical bytes |
| Rule preservation | PASS, allocation non-import AST and extracted primitive definition AST unchanged |

The exact new substitution regression was run against original HEAD source in
an isolated local snapshot: **1 failed, DID NOT RAISE**, proving the original
bug. It passes current code. Intermediate development lint/format findings were
corrected; the final run above passes. Actual logs/JUnit and comparison evidence
are packaged in `review/logs/`. This expected baseline failure is not a failure
of the final suite. Tests are synthetic engineering checks, not 164 observations.

All 32 tracked files outside the declared modification allowlist retain their
starting raw working-file SHA-256, including AGENTS, frozen research documents,
original execution reports, fixture catalog, config/lock and prior tracked ZIP.
The original Phase 1 ZIP remains tracked and unchanged. Source/file checksums
identify the new uncommitted snapshot without pretending it has a Git commit.

## Git provenance and archive

Local HEAD, tracking `origin/main`, local push reflog and a fresh read-only
GitHub SSH-over-443 `ls-remote` confirm Phase 1 SHA
`56470b3f888ca69377f5962a224d6687730b8463`. Phase 1.1 creates no commit;
all work is pre-sprint, dated 2026-10-18 NZDT. Historical uncommitted-state
reports remain unchanged. See additive [PROVENANCE.md](PROVENANCE.md) §5.

Review archive: **`D:\workshop\oct\pactlens-phase1.1-review.zip`**, outside
the repository. Contains reviewable source/tests/docs/config/lock, actual logs
and a SHA-256 file manifest. Excludes Git/venv/runtime directories, old archives,
credentials, private datasets, caches and temporary files. Archive verification
checks CRC, every manifest checksum and exact current source-file bytes; the
external verification receipt records its resulting SHA-256. Raw JUnit is
retained locally; packaged JUnit removes only hostname/timestamp metadata.

The narrow ignore pattern prevents future root review ZIP additions. Removing
the historical tracked ZIP from future versions requires separate authorization;
no file was removed, untracked or history-rewritten in this pass.

## Remaining work and Phase 2 readiness

**GO for separately authorized Phase 2 planning/integration.** These Phase 1.1
integrity gates pass. This is not evidence that the AIG adapter, human approval,
independent authorization, durable effect/receipt path or recovery behavior
already works in PactLens; all remain unimplemented and require their own tests.

Formal pilot/calibration/held-out runs, inference, detectors, scoring and
independent human adjudication remain **NOT RUN**. Frozen allocation remains
4 pilot + 10 calibration + 10 held-out blocks, 120 planned episode slots,
0 formal episodes executed. No research findings or cryptographic guarantees
are inferred from engineering fixtures. Work stops at Phase 1.1.
