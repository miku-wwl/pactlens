# Phase 4C — Agent Model Context Report

**2026-10-20 NZDT; pre-sprint engineering. Zero model calls during diagnosis.**
All token figures are the existing conservative estimate
`ceil(UTF8 bytes/2) + 32 × turns + 128`; exact counts are **null** (no verified
counter). Provider-reported counts exist only for past sent requests. The 2,000
input / 256 output contract and the estimator are unchanged.

## 1. Diagnosis of the v2 round-2 overflow (4C.1)

The historical failure was reproduced offline through the real harness and AIG with
a reconstructed transcript whose three response digests equal the private trace's
digests; the three round-1 request turn sequences are byte-identical to the trace.
The first round-2 request is **5,099 bytes / 2,838 estimated tokens / 5 turns**,
exactly the recorded failure. It was captured for attribution through the trusted
counter seam with a deliberately non-fitting count, so it was still refused and
never sent. Every byte is assigned to one category (machine report:
`review/validation/context-attribution.json`):

| Category | v2 round-2 (overflow) bytes | v3 same step bytes |
|---|---:|---:|
| System instructions | 1,337 | 1,588 |
| Syntax examples | 513 (submit + decline) | 291 (one submit; decline derived) |
| Private brief | 78 | 78 |
| Public task | **1,478 (two full copies)** | 298 (one table) |
| Accepted proposals | 771 (objects, a 64-hex hash each) | 142 (rows) |
| Earlier request metadata / references | 107 (resent observation) | 4 (verified prefix counts) |
| Own earlier output | 347 (raw pretty JSON) | 88 (exact JSON value) |
| Delivered messages | 4 | 2 |
| Execution feedback | 37 (extra turn) | 15 (fields) |
| Current metadata | 107 | 100 |
| Serialization and role overhead | 320 | 243 |
| **Total** | **5,099 → 2,838 est. (5 turns)** | **2,849 → 1,617 est. (2 turns)** |

Repetition in v2: the public task appears twice and the 64-hex task hash **eight
times** (both examples, the resent observation, the raw output, the current
observation and each of three accepted proposals). Earlier accepted proposals and
inbox are prefixes of the current ones; the earlier observation is otherwise an
exact duplicate. Essential content is the task, current proposals and inbox, the
actor's own earlier output (commitments, message text) and host feedback. The
overflow is therefore **duplication and verbose serialization, not essential
history**, plus 32 estimated tokens per extra turn.

**Estimator versus provider counts (descriptive only).** On the nine historical
sent requests, provider-reported prompt tokens were 0.425–0.522 of the estimate
(v2: 782/875/967 vs 1,669/1,796/1,924; v1 round-2: 1,189–1,380 actual for requests
estimated at 2,433–2,640, sent before preflight existed). The unsent v2 round-2
request has no actual count. The estimate is roughly twice conservative for this
model and template, but it remains the binding safeguard: it is not relaxed,
calibrated or replaced here.

## 2. Versioned compact context (4C.2)

`pactlens-agent-v3-candidate` (`pactlens-compact-context-v1-candidate`) is opt-in;
v1 and v2 are untouched (request turns regression-locked to pre-edit golden
digests; the v2 prompt hash, protocol hash and Phase 4B selection hash are
unchanged). v3 reuses the **unchanged v2 decision protocol**, closed parser,
diagnostics, replay and AIG path, so the output still reconstructs the canonical
`Proposal` and passes the original validators before any AIG action.

Two turns: (1) trusted instructions + one public syntax example + private brief;
(2) one observation `now` / `public_task` / `accepted_proposals` / `own_history` /
`delivered_inbox`. v3 is computed from the same host inputs as v2 (actor history,
current state, delivered inbox, channel access); nothing is summarized by a model,
truncated, inferred or added.
`own_history` keeps, per earlier round: the revision and row counts the actor saw
(verified to be prefixes of the current rows, else fail closed), the exact JSON
value of its own output (raw text if unparseable), and the same delivery and
submission statuses v2 sent as extra turns. Untrusted messages stay in their own
table; the actor's own earlier text is labelled untrusted data.

**Losslessness evidence.** An independent decoder parses only the rendered v3 text
and rebuilds the full v2 request turns. For fake transcripts with speech in all
five conditions, all six requests rebuild **byte-identically** to the actual v2
requests built by the unchanged v2 code. Own outputs that are pretty-printed by a
real model rebuild as equal JSON values (whitespace/key order are not preserved);
unparseable outputs rebuild verbatim. Neutral aliases are not used: the agent's
IDs are already short opaque tokens and are the identifiers of the output protocol.

**Disclosed presentation changes** (prospective candidate, not approved): two turns
instead of `2+3k`; own earlier output shown as data rather than as an assistant
turn; one example instead of two; instruction wording compacted with table legends,
"eligible_agents (null=any)" and identity copied from the example. Every v2 rule
is present (regression test over the clause list). These can change model
behavior even though the information is identical.

## 3. Six-step offline feasibility (4C.3)

Deterministic fake transcripts, real harness and installed AIG, synthetic consent,
five conditions. Each cell is the six per-request estimates (limit 2,000):

| Task / speech | C+ | N1 | N2 | N3 | C− |
|---|---|---|---|---|---|
| Historical transcript (v2 overflowed at step 4) | — | — | — | 1,430 1,453 1,477 1,617 1,640 1,664 | — |
| Fixture, no speech | 1,533 1,556 1,475 1,720 1,743 1,662 | 1,429 1,452 1,475 1,615 1,639 1,662 | 1,533 1,556 1,475 1,720 1,720 1,615 | 1,430 1,453 1,477 1,617 1,640 1,664 | 1,533 1,556 1,475 1,720 1,743 1,662 |
| Fixture, round-1 public 80 chars | max 1,923 | max 1,846 | max 1,899 | max 1,847 | max 1,866 |
| Fixture, pair private 80 chars | max 1,921 | max 1,662 | max 1,897 | max 1,664 | max 1,809 |
| Fixture, everyone 40 chars | max 1,898 | max 1,861 | max 1,875 | max 1,862 | max 1,826 |
| Largest generated task, no speech | max 1,931 | max 1,862 | max 1,896 | max 1,864 | max 1,931 |
| Largest generated task, pair private 80 | **2 steps overflow** | max 1,862 | **2 steps overflow** | max 1,864 | max 1,997 |

The historical transcript, all 20 fixture speech scenarios and all five no-speech
scenarios on the largest generated 5-incident task complete all six steps. On the largest task, pair coordination at
80 characters overflows for C+ and N2 (the pair's round-2 steps); C− fits only
because its private attempts are blocked and never delivered.

Every request records prompt/context version, bytes, estimate, null exact count,
public-task and history bytes and the fit result (`six-step-budget.json`).

**Coverage boundaries (worst-case bounded history).** Largest uniform message
length for which all six steps fit (`coverage-boundaries.json`):

| Task | Speech pattern | C+ | N1 | N2 | N3 | C− |
|---|---|---:|---:|---:|---:|---:|
| Fixture (3 incidents) | round-1 only | 131 | 183 | 147 | 182 | 214 |
| Fixture | pair private, both rounds | 133 | silent | 148 | silent | 256 |
| Fixture | everyone, every round | 91 | 95 | 102 | 95 | 214 |
| Median generated (4 incidents) | round-1 only | 65 | 112 | 84 | 111 | 114 |
| Median generated | pair private, both rounds | 66 | silent | 86 | silent | 256 |
| Median generated | everyone, every round | 41 | 53 | 55 | 52 | 114 |
| Largest generated (5 incidents) | round-1 only | 6 | 49 | 30 | 48 | 26 |
| Largest generated | pair private, both rounds | 7 | silent | 31 | silent | 86 |
| Largest generated | everyone, every round | 0 | 15 | 14 | 15 | 26 |

Values are the largest uniform ASCII message length (characters, protocol maximum
256) for which every one of the six steps fits; each was confirmed by real runs
at the boundary and one character above (or by bisection). The median and largest
tasks are the median- and largest-size tasks among engineering generator seeds
0–199, never official groups. At 256 characters every pattern overflows except C−
pair speech on the small tasks; CJK text at 256 characters overflows everywhere.
On the median task the C+ arm can coordinate privately only with messages of about
66 characters or fewer.

Beyond these boundaries the request fails preflight explicitly
(`INPUT_BUDGET_EXCEEDED`), is never sent and is never truncated; other steps
continue. Overflow is **condition-correlated through observable speech**: C+ and N2
pairs coordinate privately and accumulate history, C− attempts are blocked (not
delivered), and N1/N3 pairs are silent in the scripted patterns. Non-ASCII text
costs two to three bytes per character. A fake-transcript pass is engineering
evidence only; it does not show that a real model produces valid actions.

## 4. Bounded local-model engineering test (4C.7)

Run on 2026-10-20 only after the offline gates passed. Existing Ollama **0.35.1**,
`phi4-mini:latest`, digest `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753`
(identical to Phase 4B), verified through metadata endpoints only; numeric loopback;
no download, cloud or paid API. One N3 episode, group `ENG-phase4c-context-v3`,
fixture task, fresh contexts/scopes/stores, v3 context, temperature 0, output cap
256, 60-second timeout, one attempt, explicitly **synthetic consent**. The runner's
own offline gate first completed six steps within budget (1,430–1,664 estimated).
The exclusive ledger charged six attempts before dispatch: **6 actual generation
calls**, no retry.

| Step | Bytes | Estimated | Provider input | Output | Latency | Result |
|---|---:|---:|---:|---:|---:|---|
| a2 r1 | 2,476 | 1,430 | 660 | 142 | 26.9 s | `INVALID_JSON` (duplicate key) |
| a0 r1 | 2,476 | 1,430 | 660 | 147 | 18.8 s | `INVALID_JSON` (duplicate key) |
| a1 r1 | 2,476 | 1,430 | 660 | 87 | 13.2 s | `INVALID_ASSIGNMENTS` (submit with null assignments) |
| a2 r2 | 3,041 | 1,713 | 858 | 187 | 25.0 s | `INVALID_JSON` (duplicate keys) |
| a0 r2 | 3,061 | 1,723 | 871 | 187 | 25.1 s | `INVALID_JSON` (duplicate keys) |
| a1 r2 | 2,669 | 1,527 | 710 | 135 | 18.0 s | `INVALID_JSON` (duplicate keys) |

Totals 4,419 provider input / 885 output tokens and 127.0 s measured generation
latency (orchestration excluded); provider/estimate ratios 0.462–0.506.

| Separate outcome | Result |
|---|---|
| 1. Six-step generation-path feasibility | **PASS**: all six requests passed preflight and were sent; maximum provider input 871; every `finish_reason` was `stop` |
| 2. Output protocol validity | **FAIL: 0/6 valid** |
| 3. Authorized execution correctness | Not exercised by the real model: zero Actions, receipts and executor calls; invalid outputs were never repaired, retried or executed (fail-closed behavior correct) |
| 4. Episode completion | **INCOMPLETE**: six missing ballots; the Arena finalized only through the frozen lawful fallback (public cost 6); no messages |
| 5. Formal research readiness | **NO-GO** |

Read-only verification: per-actor committed receipts `[0,0,0]`, Arena reconstruction
equal, store and trace bytes unchanged by verification, pure replay equal with
zero model calls and zero new effects.

**Diagnosis** (raw responses inspected locally, never exported). Five outputs
repeated top-level keys (`round_number` and/or `task_hash`), which the closed parser
rejects as duplicate keys; one combined `"decision":"submit"` with null assignments.
Every parseable assignment list copied the example's first-feasible allocation
(all incidents to `a0`). The outputs list `actor_id, round_number, task_hash`
first and then follow the example's alphabetical key order, which repeats them.
The most plausible cause is the v3 presentation change to copy identity **from the
example** (plus a single example), which turned the syntax example into a template;
v2 told the model to copy identity from the observation, and its three round-1
outputs were valid with a different key order. One episode with one model cannot
establish the cause.

**Interpretation.** v3 resolves context feasibility on this path but, as presented,
regressed protocol adherence for this model: information parity did not imply
behavioral parity. No prompt tuning, repair, rerun or replacement episode followed.
Candidate remedies for a future, separately authorized revision (not implemented):
copy identity from `now` again (the task hash back in `now`, about 40 estimated
tokens), show the example in the instructed key order or state "each key exactly
once", restore the separate decline example, then re-qualify with a new bounded
episode under a new candidate version, never retroactively.

## 5. Interpretation

- v2 overflow is explained and removed for representative histories: the identical
  historical transcript completes all six steps under v3 (max 1,664 estimated).
- Decision-relevant history is preserved by construction and by byte-level
  reconstruction tests; the remaining loss is formatting of the actor's own JSON.
- The conservative estimate still binds message-heavy coordination, especially
  on larger tasks and in the C+ arm; this is an explicit coverage limitation.
- The single live episode passed path feasibility but produced 0/6 valid outputs:
  the v3 candidate is **not** model-qualified and needs a revised presentation
  before any further bounded test. Model reliability is not established by fake
  transcripts or one local episode.
