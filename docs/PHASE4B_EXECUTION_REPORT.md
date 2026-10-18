# Phase 4B — Execution Report

**2026-10-19 NZDT. Pre-sprint engineering / pre-existing work.**

## 1. Overall status

**PARTIAL overall; Phase 4B offline engineering PASS.** All authorized preparation,
bounded local validation and review artifacts are complete. Model qualification
and formal readiness fail their gates; this is a reportable result, not permission
to repair, replace or extend the runs. Engineering **GO**, model **BLOCKED**,
detector inputs **CONDITIONAL GO**, formal pilot **NO-GO**.

The starting tree was clean on main. Local HEAD, origin/main and live HTTPS remote
all verified **`27c22f338d357a0f18850e86cd6cf9a297d7eeb8`**, the pushed Phase 4A
baseline. This phase is an uncommitted delta. No commit, push, tag, release,
deployment, competition submission or Phase 4C occurred.

Frozen allocation stays **4 pilot +10 calibration +10 held-out groups /120 future
slots /0 formal executions**. Conditions, pairing, Arena/fallback/objective,
truth, abstention, split membership, thresholds and evaluation remain unchanged.
No actual detector inference, prediction, threshold selection or statistics ran.

## 2. Budgeted views and engineering

New public-only atomic bundles and a versioned deterministic common selector
retain an interpretable mandatory core, then test optional bundles against the
larger R/MAE complete request and all other views. Action/receipt correlation is
atomic. Missing/non-success integrity, failed/blocked permitted communication,
all proposal slots and ordering uncertainty remain truthful. No label/oracle/
score chooses facts. No model call or second independent truncation is used.

Lossless named public-task/allocation tables and payload/ordering dictionaries
reduce repeated syntax. R is readable flat JSONL; MAE groups exactly the same
selected facts. Both are already structured formats. Independent text parsing
reconstructs complete fact values/nulls/metadata, then verifies manifest binding
and selected R/MAE parity. MA is the selected M/A union and a subset of R; it
does not gain extra facts because its rendering is smaller.

`DetectorEnvelope` accounts for system, task, evidence, output instructions and
response schema in fresh contexts, with 4,096 input /256 reserved output. Exact
provider tokenization is unavailable; estimates are engineering guards, not exact
measurements or proven bounds. No context is silently expanded or truncated.
The prior full Phase 4A renderers/defaults remain available and unchanged.

The offline audit covered **34 source/policy sets: 33 fit the estimate, one
mandatory core overflows**, with 165 safe exports. All 28 hand-scripted
fixture/policy sets fit and constructed R/MAE inputs pass semantic parity.
For the historical six-receipt fake-model source:

| View | A retained/omitted | A bytes /estimated tokens | B retained/omitted | B bytes /estimated tokens |
|---|---|---|---|---|
| M | 5/3 | 2,519 /1,937 | 6/8 | 3,103 /2,229 |
| A | 11/7 | 3,494 /2,424 | 12/6 | 3,654 /2,504 |
| MA | 15/10 | 4,475 /2,915 | 17/14 | 5,227 /3,291 |
| R | 20/18 | 6,674 /4,014 | 20/24 | 6,670 /4,012 |
| MAE | 20/18 | 6,755 /4,055 | 20/24 | 6,751 /4,053 |

All mandatory IDs are retained; omissions and filtered scope are explicit. These
subsets retain only 2/6 successful integrity pairs under A and 1/6 under B, and
reduced speech. They are **insufficient for a complete episode-wide agreement/
lifecycle audit**. Token fit is not scientific sufficiency or MAE superiority.

The actual v1/B mandatory core still requires R=4,486 and MAE=4,527 estimated
tokens. It is a preserved `INPUT_BUDGET_EXCEEDED`, not a successful packet. No
blocked event or missing evidence was discarded to rescue it. Other actual-trace
sets fit. Full retained/mandatory/omitted category/size details are in the
[budget report](PHASE4B_TOKEN_BUDGET_REPORT.md) and machine audit. Budget failures
can depend on message volume/observer rights and must remain future abstentions,
not selective exclusions. Selection is a **PROPOSED lossy policy**, not formally
approved observation configuration.

## 3. Actual model engineering results

Existing numeric-loopback Ollama **0.35.1**, `phi4-mini:latest`, digest
**`78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753`**
was verified before inference. No download, paid/cloud provider, DNS/proxy route
or third-party effect was used. Both runs used the same public fixture task,
fixed model/configuration and common `ENG-phase4b-reliability-v1` seed schedule;
fresh independent contexts, UUID scopes and SQLite stores. Responses were never
copied. Consent is explicitly **synthetic test consent**, not authenticated humans.

| Observation | Legacy v1 | Candidate v2 |
|---|---:|---:|
| Actual generation calls | **6** | **3** |
| Valid outputs | 5 | 3 |
| Invalid responses | 1 | 0 |
| Valid submissions | 2 | 3 |
| Valid declines | 3 | 0 |
| Actual AIG Actions /verified local receipts | 2 /2 | 3 /3 |
| Finalized Arena | Yes | No |
| Episode status | **INCOMPLETE** | **INCOMPLETE** |
| Provider prompt tokens | 5,959 | 2,624 |
| Provider output tokens | 931 | 417 |
| Measured generation seconds | 131.330707 | 66.093942 |

**9 new generation calls total**, within 12/at-most-two-episode authorization.
The exclusive pre-dispatch ledger caps each profile at six and total at twelve;
there is no resume, retry or replacement episode. Total reported usage is 8,583
input /1,348 output, generation latency 197.424649 seconds. Readiness/model checks,
AIG and orchestration overhead are excluded; this is not an isolated benchmark.
Provider seeds remain requested, not verified deterministic.

V1's invalid response has malformed message routing/recipient structure, retained
as `INVALID_MESSAGE_ROUTING`. Its valid decline can still request undeliverable
speech; valid behavior is separate from Router permission/delivery. Declines
occurred once in round 1 and twice in round 2; one final submission succeeded.
No response was repaired into an effect.

V2 produced three valid **round-1** submissions. Before its first round-2 call,
the full 5,099-byte request estimated **2,838 tokens against 2,000**, so comparison
stopped. That call was not sent; the two other final steps were NOT_REACHED.
No exact future-token measurement, smaller prompt or budget bypass was attempted.
Actual v2 prompt counts on the three completed calls were 782/875/967; outputs
139 each. V1 actual inputs were 592–1,380 and outputs 120–191. These real past
usage measurements cannot replace preflight for an unsent future request.

Every response/request hash, protocol, usage, latency, JSON/schema/feasibility/
message validity, actual validation, Action state and receipt reference is in
the sanitized engineering summary. Original traces and original summary are
unchanged; a separate read-only schema audit corrects a derived structural flag,
without changing calls, responses, accept/reject decisions or effects.

Read-only durable verification found per-actor receipt counts `[1,1,0]` and
`[1,1,1]`, reconstructed the same Arena states and left store bytes unchanged.
Both pure replays match captured L3 with zero model/Gateway/new-effect calls.
No actual Unknown occurred in these two runs; original and new synthetic
Unknown/no-retry regressions still pass.

**REAL_MODEL_NOT_READY.** Three valid v2 first-round responses cannot establish
full-episode reliability, superiority or statistical improvement. Both failed
episodes remain; no extra run, prompt tuning or positive-control test followed.
The earlier six-call Phase 3 v1 episode remains a separate historical observation.

## 4. Methodological decisions and review preparation

| Decision | Recommendation/candidate | Status |
|---|---|---|
| Primary observer | A delivered/intercepted | PROPOSED |
| Router sensitivity | B, separately labelled | PROPOSED |
| N2 | Retain all-final-execution block; disclose secondary intervention artifact | PROPOSED interpretation; implementation retained |
| Selection | Shared atomic candidate v1 | PROPOSED |
| Model/prompt/protocol | Verified local model and unchanged v2 candidate | PENDING; not qualified |
| Reviewer rubric | Independent candidate forms and L2 workflow | PENDING; zero arranged/completed |
| Detector input/response | Versioned pure contracts, no scoring | PENDING |
| Formal pilot | Not authorized | **NO-GO** |

A reduces privileged Router signatures but does not remove all shortcuts. B has
legitimate additional audit evidence and can reveal C+/C− intervention; it is
not interchangeable with A. The engineering default stays B. N2's final missing
slots remain observable; low secondary N2 FPR would not establish sophisticated
collusion reasoning. Phase 1's older lawful-final-ballot fixture is distinct from
the later harness block; neither was rewritten. N2-B/C remain unimplemented.
Primary N1 FPR, coverage/recall guards and all frozen rules are unchanged.

Separate full A/B reviewer packets omit assignment/group/split/assigned pair,
L4 and peer judgments, with mechanical L2 comparators separately labelled.
Closed blank forms and seal/reconcile/indeterminate/L2-lock workflow are prepared.
No human was contacted, arranged or falsely counted as an independent reviewer.
One future reviewer only permits disclosed limited case/pipeline analysis.

Pure future detector response validation rejects malformed/nonfinite values and
unobserved citations. It preserves finite risk_score/confidence and adequacy;
errors/insufficiency abstain. Binary verdict remains PENDING_FROZEN_THRESHOLD for
adequate responses: no threshold or metric is computed. See the
[freeze package](PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md) for hashes and decisions.

## 5. Validation

**607 passed in 231.78s: all 480 original +127 new, zero failures/errors/skips.**
Offline dependency sync, Ruff check, format check, offline lock and compileall
pass. Installed AIG **0.2.0**, exact source pin
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`, all 57 RECORD hashes, installed import
and five-second budget remain verified. No upstream source was changed.

Only the existing harness source gains an optional comparison stop-on-budget
flag, default false. Existing prompts, parsers, Arena, conditions, AIG/store/
receipt/bridge, dependency pin/lock, original tests and historical reports remain
byte-identical. Four current-state documents receive additive updates. The
[test matrix](PHASE4B_TEST_MATRIX.md) records exact counts, intermediate test-setup
corrections, command logs, replay/boundary/privacy tests and interpretation limits.

## 6. Readiness and remaining risks

| Gate | Decision |
|---|---|
| Engineering | **GO** |
| Model | **BLOCKED /REAL_MODEL_NOT_READY** |
| Detector inputs | **CONDITIONAL GO** |
| Formal pilot | **NO-GO** |

Model adherence/history fit, exact tokenizer qualification, lossy evidence
sufficiency, Router/missingness/capture artifacts, attributed approvals and real
independent reviewers remain unresolved. Hashes establish consistency, not
malicious-host authenticity; synthetic consent is not production human
authentication. Small sequential three-actor synthetic cases and scripted
malicious controls cannot establish emergent collusion or general detector
performance. Twenty-four groups are not 120 independent observations.

The [machine readiness report](PHASE4B_PILOT_READINESS.md) retains every critical
unapproved gate. No formal experiment or Phase 4C is authorized by completing
this phase. No thresholds, trained models or independently adjudicated results
exist.

## 7. Review artifact and stop

**`D:\workshop\oct\pactlens-phase4b-review.zip`**, outside the repository.
Includes source/tests/config/safe fixtures/docs, actual checks, sanitized local
engineering measurements, safe budget/parity examples, proposed freeze/readiness
records, blank reviewer preparation, member SHA-256 manifest and an internal
payload verification receipt. The external `.zip.verification.json` records the
final ZIP hash, CRC, every member hash and exact working-source consistency.

Private raw agent prompts/traces, SQLite, capabilities/credentials, `.git`, `.venv`,
`.runtime`, weights/caches and previous archives are excluded. Selected safe logs
are copied into a separate review directory. An internal receipt cannot contain
its own final container hash; the external independent receipt supplies it.
Historical archives are preserved. The ZIP identifies an uncommitted Phase 4B
snapshot, not a release. Work stops here.
