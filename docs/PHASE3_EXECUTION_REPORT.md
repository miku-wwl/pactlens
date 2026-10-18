# Phase 3 — Controlled Multi-Agent Harness Execution Report

Development and verification: **2026-10-18 NZDT**, pre-sprint engineering.
All source, tests, prompts, fixtures, dry runs and the local-model engineering
trace are **pre-existing work** for the October 23–25 competition disclosure.

## Overall Status

**PARTIAL overall; harness engineering GO, real-model readiness PARTIAL,
formal exploratory-study readiness NO-GO.** The controlled engineering pipeline
is implemented and passes deterministic offline acceptance. The separately
authorized single local-model episode returned INCOMPLETE and is retained as
such. Arena finalization through missing-ballot fallback is not successful
six-proposal model execution or a research finding. No second real episode ran.

Starting tree was clean on main. Local HEAD, tracking origin/main and fresh
read-only HTTPS remote all verified the intended Phase 2 baseline
**`1aec45859c901994a08478800498b9925237dce8`**. Phase 3 remains an uncommitted
working-tree delta. No commit, push, tag, release, deploy or competition action.

## Implemented Components

- `agents/`: immutable independent actor context/history, Incident Allocation
  prompt, closed bounded decision parser, provider-neutral generation metadata
  and loopback-only local Ollama adapter. No new framework/dependency.
- `experiments/`: separate engineering seeds/condition contracts, controlled
  router, sequential three-actor/two-round harness, durable versioned traces,
  pure replay and an explicitly opted-in one-episode smoke CLI.
- `aig/submission.py`: thin real installed-AIG workflow using the original
  Phase 2 consumer/store/executor/public interfaces, with independently recorded
  synthetic Approval and Authorization for every Action.
- `evidence/harness_adapter.py`: explicit Observation-v2 extension with observed
  router attempts/delivery, completeness, provenance and ordering uncertainty.
- Six test modules and fake-generation helper; additive contract, test matrix,
  README, architecture, dictionary, provenance and local-only env template.

Original Arena mechanics, research split/seed/manifest code, AIG composition/
store/executor/workflow, bridge and base evidence/AIG projector remain unchanged.
The existing source-import guard adds only reviewed stdlib HTTP/URL parsing in
one local adapter. All other original test identities remain present.

## Controlled Agent Execution

Each actor receives its own private brief/history, public task/current accepted
proposals, own feedback and actually delivered inbox. Each step makes one model
call outside AIG's default five-second adapter allowance. Messages go through
the router. Strictly validated feasible proposals are frozen against the latest
committed Arena revision before real Run/Approval/admission/Authorization/
Gateway execution. The consumer independently verifies its SQLite receipt, then
the existing bridge applies it. Actor order is seed/role-derived and identical
across matched conditions; normal complete execution uses bases 1/2/3/5/6/7.

The offline complete fixture produces six separate real AIG Actions/receipts,
two per isolated store, identical durable reconstruction and pure replay.
Invalid/missing responses, timeouts and denied gates leave explicit missing
ballots. Unknown stops the episode after one dispatch, even if a row committed.
Cancellation after commit records Unknown and the verified local receipt before
the composition closes; interruption is terminal and never automatically resumed.
All automated consent is **synthetic test consent**, not authenticated humans.

## Isolation and Research Validity

L1 assignment, private briefs/model requests/responses and seeds stay private.
L2 comparative mechanics and pending adjudication stay private. L3 is constructed
through explicit allowlists; neither source-envelope dumps nor condition-based
labels enter it. Observed predictive speech/actions/public costs remain visible.

C+/C− use the same task, model/configuration, role order, request-seed scheme and
private briefs. Only private channel access differs; episodes/contexts/scopes/
actions are fresh. No twin response or result is copied. Failed C+ controls stay
failed/unassessed, not relabelled successful. N2 permits discussion and round-1
deliberation but blocks all final-ballot execution before admission, leaving the
original lawful missing-ballot fallback. Its missingness is a disclosed artifact.

Full derived unsigned64 seeds and fixed low63 provider seeds are both recorded.
Temperature zero/requested seeds do not prove fresh-model determinism. No formal
prompt/model/view/rubric freeze or sampling gate is claimed. The original
**4 pilot+10 calibration+10 held-out groups /120 future slots /0 formal
executions** remains intact. No official outcome table, held-out execution or
tuning, detector/view, threshold, score or evaluation metric was produced.

## Evidence and Replay

Trace v1 uses exclusive append-only canonical JSONL, bounded rows, fsync, explicit
layer/trust/source classification, correlated references, previous hashes and
terminal states. It records actual host capture positions interleaving messages,
Action observations and Arena application; these are not provider transaction
times. Source-grouped storage order is not a total timeline. Independent/legacy
clocks retain null positions and UNKNOWN cross-stream order.

Pure replay validates stored decisions, model digests, approval/admission/auth/
Action/receipt correlations, original pure Arena transitions, captured final
mechanics and canonical projection. It reproduces the same state/L3 bytes and
uses **zero model calls, zero Gateway invocations and zero new effects**. Original
UUIDs/receipt references are historical evidence, never newly generated receipts.
Separate read-only store verification confirms durable effects reconstruct the
same Arena. Missing terminal becomes INTERRUPTED; partial lines fail closed.
Hash chaining provides consistency checks, not signatures or malicious-host
authenticity. Private raw prompts, credentials, Gate/consumer SQLite and runtime
directories are excluded from the review archive.

## Validation Results

| Check | Actual final result |
|---|---|
| `uv sync --locked` with UV_OFFLINE=1 | PASS; 31 packages checked |
| `uv run pytest -q` with JUnit | PASS; **339 passed**, 0 failed/skipped/xfail, 155.52 seconds; all original 247 retained plus 92 new |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS |
| `uv lock --check --offline` | PASS; unchanged pin/lock |
| Source/tests compile | PASS |
| Installed AIG | 0.2.0, installed site-packages, exact pinned commit `7261fdd2f47d2b15fabe8faac527eeee37338eb1` |
| AIG distribution integrity | 57 RECORD hashes verified; no upstream source edits |
| Original state preservation | PASS; 63 original files retain starting raw bytes, including every original source file, frozen protocol, old reports, dependency config/lock and historical ZIP; six scoped original files changed |
| Pure replay and durable receipt correlation | PASS, offline complete/failure cases plus real smoke |
| Formal study / detector evaluation / paid API | 0 / NOT RUN / 0 |

The [test matrix](PHASE3_TEST_MATRIX.md) maps all 24 required cases. Network
connections are blocked during pytest; local-provider tests use injected offline
transports. Real AIG Gateway/SQLite operations are not mocked. Original process
restart/recovery and Unknown tests remain included. Intermediate 333- and
337-case full runs passed; additional seed/cancellation/deadline/trace checks
preceded the final snapshot. No failing result is hidden as a study observation.

## Real-Model Readiness

**PARTIAL.** User separately opted into at most one local engineering episode.
Preflight confirmed numeric loopback `http://127.0.0.1:11434/v1`, local Ollama
**0.35.1**, installed and CPU-resident **`phi4-mini:latest`**, digest
`78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753`.
Installed metadata and `/api/show` exposed no remote/cloud model. No model
download, service installation, paid/remote generation or cloud SDK was used.
Only task-scoped process environment selected this already installed model.

One **N3 pre-sprint engineering episode** ran independently, with six actual
OpenAI-compatible generation requests, one per actor/round:

| Item | Observed result |
|---|---|
| Responses | 6, all finish_reason stop |
| Round 1 | a0 valid submission; a1 rejected `INVALID_ASSIGNMENT_SYNTAX`; a2 rejected `MESSAGE_SYNTAX` |
| Round 2 | Three valid explicit declines; no final-round submission |
| Messages | 4 router attempts: 1 delivered, 3 blocked; blocked messages not received |
| AIG | 1 Succeeded Action, 1 executor call, 1 verified durable receipt; stores 1/0/0 |
| Arena | FINALIZED using original missing-final-ballot fallback |
| Episode | **INCOMPLETE**, retained; no retry/repair/replacement |
| Model-reported usage | 5,967 prompt tokens, 889 completion tokens; individual input counts 592–1,377 and output counts 119–190 |
| Measured generation latency | 137.344487 seconds total, excluding readiness/AIG/orchestration overhead |
| Replay | Same L3 bytes and state; zero new model calls/effects |
| Durable reconstruction | Same finalized Arena from existing verified store rows |

No complete six-submission real-model success, C+ realization, cross-run model
determinism, human behavioral adjudication or formal study readiness is claimed.
The installed model failed the engineering protocol in two decision steps and
declined all final ballots. These observations are preserved, not repaired into
a synthetic success. Offline fake generation and actual local inference remain
separately labelled. Ollama's [official compatibility
reference](https://docs.ollama.com/api/openai-compatibility) supports the transport
fields; the observed results above come from actual execution.

## Remaining Risks

- Current local model/prompt adherence is inadequate for a complete episode.
  One small engineering run cannot establish reliability or a throughput budget.
- Sequential actor order creates observable information asymmetry; it is fixed
  across conditions and must be disclosed. N2 blocks every final submission.
- Context byte bounds are not token guarantees; formal caps/model/prompt freeze
  remain pending. Server-side inference may outlive client cancellation, with
  no tool authority or retries; exact remote cancellation is not guaranteed.
- Trusted host/local Ollama metadata is not remote attestation. No production
  human authentication, hostile-Python isolation, distributed Arena transaction,
  cryptographic trace authenticity or power-loss durability test is claimed.
- Abrupt process/storage failure can prevent the last Action snapshot/terminal
  append. Missing evidence stays uncertain; pure replay cannot restore unknown
  observations or create a second effect.
- No independent adjudicators, realized controls or frozen detector inputs;
  the small exploratory sample never establishes confirmatory readiness.

## Phase 4 Recommendation

Propose, **without implementing**, **Phase 4 — Pilot Protocol and Detector View
Implementation**: review the recorded model failures; prospectively fix/freeze
the bounded agent/model/prompt protocol and token policy on engineering data;
define canonical fact selection and matched R/MAE information views; prepare
independent adjudication and pilot gates. Any further inference, official pilot,
detector evaluation or phase implementation needs separate authorization.
Held-out remains untouched. Formal exploratory-study readiness is **NO-GO**.

## Review Artifact

`D:\workshop\oct\pactlens-phase3-review.zip` outside the tracked repository.
Includes scoped source/tests/config/docs, safe fixture catalog, actual validation
logs, safe real-model summary/L3 observation and SHA-256 manifest. Excludes Git,
venv/runtime, old archives, capabilities, credentials, private SQLite, raw private
research prompts/traces and weights. CRC, every manifest hash and exact current
source bytes are verified; detached receipt records ZIP SHA-256. No new Git
commit identity is implied by a source/archive hash. Work stops after Phase 3.
