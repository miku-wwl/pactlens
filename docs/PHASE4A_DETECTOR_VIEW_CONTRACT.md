# Phase 4A — Detector View and Candidate Protocol Contract

Date: **2026-10-19 NZDT; pre-sprint engineering / pre-existing work**.
Authority: [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md). These are input builders,
not detectors, predictions, calibration or approval to run a study. Source
baseline: `6bf93a996476e6433eedc3fa11784703bf61a31a`.

## 1. Candidate agent protocol and historical compatibility

Original `SYSTEM` and `pactlens-agent-v1` remain available; legacy parsing and
the default Phase 3 engineering profile remain compatible. The new profile is
**explicitly selected**, using
`run_episode(..., prompt_version="pactlens-agent-v2-candidate")`. There is no
automatic fallback from an overflowing v2 request to v1. Keeping the legacy
default does not make it token-qualified for formal experiments. Profile adoption
and freezing are future reviewed decisions, not a retrospective prompt change.

The candidate uses `pactlens-decision-v2-candidate` and diagnostic schema
`pactlens-protocol-diagnostic-v1`. Stable template/protocol hashes and a full
request digest are recorded privately. The template hash binds system text,
example-policy revision and protocol hash; the request digest additionally binds
task-specific examples, full context and private brief. Historical v1 requests
without the new metadata replay under v1, never under the candidate parser.

The exact closed object remains actor_id, round_number, task_hash, decision,
assignments, message and end_step. New instructions explicitly describe JSON
arrays/objects/null/true, all incident IDs exactly once, valid actors, skill,
capacity and eligibility, public broadcast/private single-recipient intents,
and valid decline. Duplicate keys, nonfinite JSON constants, extra authority,
wrong task/actor/round/types, malformed/infeasible allocations and oversized
responses remain rejected. No code fences, repairs, coercion, lawful substitution,
forced submission, positive-control forcing or inference/Action retry is added.

Examples use only public task data: first lexicographic feasible allocation,
**not a cost-minimizing reference/oracle**, plus a null-assignment decline. They
are syntax examples, not required choices, and can still anchor model behavior.
The rule is condition-independent and must be disclosed/frozen before pilot.
Private channel denial remains Router authority: a syntactically valid private
intent can be blocked. Candidate self/unknown/public-subset/multiple-private
audiences are invalid routing; v1 trace interpretation is retained separately.

| Diagnostic | Meaning |
|---|---|
| INVALID_JSON | malformed/duplicate/nonfinite JSON |
| FIELD_SET_MISMATCH | missing/extra root, message or assignment fields |
| WRONG_FIELD_TYPE | exact JSON types violated |
| INVALID_ASSIGNMENTS | invalid representation, missing/duplicate/unknown incident or assignee |
| INFEASIBLE_ASSIGNMENTS | capacity/skill/eligibility/forbidden-unassignment violation |
| WRONG_ACTOR / WRONG_ROUND / WRONG_TASK | exact trusted context mismatch |
| INVALID_MESSAGE_ROUTING | invalid audience/channel/message syntax |
| INCOMPLETE_RESPONSE | no valid choice or unfinished step |
| OUTPUT_BUDGET_EXCEEDED | >4,096 UTF-8 bytes, excess reported output tokens or length-limited candidate response |
| INPUT_BUDGET_EXCEEDED | preflight/byte limit or reported actual input >2,000 tokens |
| PROVIDER_TIMEOUT / PROVIDER_FAILURE | bounded generation failure, no retry |
| EXPLICIT_DECLINE | valid decision; not a failure |
| VALID_SUBMISSION | valid decision, still awaiting separate AIG gates |
| AIG_SUBMISSION_FAILURE | failed/denied/Unknown operation, preserved with its actual status |

Model-response text stays in L1; diagnostics do not copy exception text into
L3. Candidate successes/declines and generation failures record versioned codes;
terminal submission-failure records preserve independent AIG statuses. Neither
diagnostic nor receipt establishes harmful agreement or behavioral truth.

## 2. Token preflight

There is no exact Ollama pre-tokenizer in this adapter. A trusted local provider
may supply `count_input_tokens(turns)` for its **complete actual chat template**;
otherwise the explicit fallback is:

`ceil(UTF8_bytes(role+content)/2) + 32 * number_of_turns + 128`.

This English-oriented conservative heuristic is a safeguard, **not a proven
upper bound or exact token count**, particularly for different tokenizers,
Unicode and provider-added formatting. Reports retain bytes, estimated tokens,
optional exact count, method, limit and fits flag. Exact-counter unit tests use
synthetic seams and are not real tokenizer measurements. A malicious host or
misconfigured counter is outside this trust boundary.

Candidate agent requests fail explicitly before generation if the full context
does not fit the 2,000-token preflight or existing 24,000-byte guard. No evidence,
private brief or history is silently truncated. No condition-specific selection
exists. Actual usage is retained when returned; a reported input over 2,000,
output over the configured maximum (at most 256), or length-limited candidate
completion prevents submission. Missing usage stays unknown. Passing an
estimate cannot prove actual fit; post-response checks cannot undo tokens used.

View contexts apply the same mechanism at **4,096 input /256 future output**.
`render_view` returns a bounded audit artifact and budget report even when the
estimate fails. `RenderedView.conversation()` refuses an overflowing packet.
Complete R/MAE engineering packets currently exceed the conservative preflight;
actual tokenizer fit is unmeasured. No truncation policy was silently activated.
See the separate [unapproved proposal](PHASE4A_PROPOSED_AMENDMENT.md).

## 3. Three communication audiences

| Audience | Rights |
|---|---|
| Experimenter | Complete private Router audit and hidden channel/config assignment |
| Detector observer | Only the explicitly selected public/interception policy below |
| Actor | Only actually delivered inbox messages plus its own operation feedback |

`project_observation` first validates typed source data through the existing
Observation-v2/AIG/harness projectors, then emits a new explicit policy envelope.
It never dumps raw trace objects, private Gate rows or experiment configuration.

**Policy A — `delivered-intercept-v1`:** the declared observer can intercept all
recorded delivered communications, including delivered private speech. It gets
no blocked/failed Router attempts, text, requested audiences, attempt counts or
Router configuration. Policy A is not a claim that all actors received all
intercepted speech. Messages have observer-local contiguous numbering, rather
than hidden attempt IDs.

**Policy B — `router-audit-v1`:** the observer has legitimate Router-audit access
to attempted text, requested/actual public aliases, attempted flag, delivery
state and capture positions. BLOCKED/FAILED never means delivered. Original
private configuration/assigned pair and invalid raw unknown-recipient IDs remain
outside the public schema. Audit rows are absent when not available, not invented.

Default B preserves **Phase 3 engineering compatibility**. Phase 0.6's permitted
interception language does not independently settle rejected-attempt rights.
Neither new API default nor engineering implementation selects/changes a formal
primary policy. Formal observer choice requires explicit prospective review.

Both policies retain genuinely observed costs/failures and authorized source
ordering. Absolute shared capture positions can still have gaps from unobserved
host work; contiguous message IDs do not eliminate statistical shortcuts. The
capture counter is not a timestamp or proof of provider transaction order.

## 4. Canonical shared inventory

`build_inventory` accepts typed public source envelopes and detached observations;
it produces a frozen `Inventory` of at most **128 facts**, each payload at most
**32,768 UTF-8 bytes**. `Fact` owns only canonical JSON strings, not private
source references. Unknown root/nested fields, classifications, aliases,
completeness/order values and duplicate fact IDs fail closed. Source semantic
validation comes from the original typed projectors; re-render verification is
consistency checking, not authentication of a hostile host.

Each fact has exactly: opaque fact_id, category, kind, public actor/null,
allowlisted payload, source, trust, completeness and ordering. IDs are UUIDv5 of
an independently assigned public episode UUID and public logical fact key.
They do not embed condition, split, group, hidden actor IDs, seed or private path.
Available public Action UUIDs/receipt references remain legitimate values.

| Fact kind | Source/trust and payload |
|---|---|
| public_task | Public actor capabilities, incidents, eligibility and objective; no oracle reference |
| message | Host-observed intercepted speech, not authenticated intent |
| router_delivery | Authorized observer's Router attempt/delivery facts only |
| communication_coverage | Observer message coverage and audit availability, uniform schema |
| proposal_slot | Six actor/round slots, actual allocation or null, SUBMITTED/MISSING/PENDING/NOT_REACHED |
| arena_event | Accepted transitions, closures, final allocation/public accounting, without invented interleaving |
| execution | Actual finalized allocation/costs or explicit pending/null fields |
| aig_action | Detached public API state, approval/auth status, digests, synthetic-consent flag; local capability is not human authentication |
| consumer_receipt | Recorded correlated local commit/ref or explicit missingness; not collusion proof |
| execution_coverage | Captured Action coverage and episode status, without model/private failure prompts |

Six Action and receipt slots use explicit null/MISSING where unobserved. Missing
does not mean failed, denied, no effect or negative truth. Unknown with a verified
local receipt remains Unknown. The exporter does not freshly re-verify SQLite;
the source collector supplied that correlation. Full capture does not imply all
proposals succeeded or all behavioral evidence exists.

Ordering stores stream, source_sequence, logical_position and RECORDED/UNKNOWN/
NOT_APPLICABLE. Null positions remain unknown; equal positions remain unresolved.
Action sequence is its observed public version. Receipt capture inherits the
enclosing host observation position, but **consumer SQL sequence/commit time is
not inferred**: its source_sequence remains null. Static task/slot snapshots do
not acquire event timestamps. Existing source-local order is preserved.

## 5. Fact-availability matrix

| Facts | M | A | MA | R | MAE |
|---|---|---|---|---|---|
| Common public task/capabilities/constraints | Yes | Yes | Yes | Yes | Yes |
| Authorized intercepted messages | Yes | No | Yes | Yes | Yes |
| Router attempt/delivery facts under B | Yes | No | Yes | Yes | Yes |
| Message/audit completeness | Yes | No | Yes | Yes | Yes |
| Proposal slots and accepted Arena transitions | No | Yes | Yes | Yes | Yes |
| Actual final allocation and public costs | No | Yes | Yes | Yes | Yes |
| AIG lifecycle, approval/auth and payload linkage | No | No | No | Yes | Yes |
| Correlated receipts and execution-integrity coverage | No | No | No | Yes | Yes |
| Ordering/uncertainty for each included fact | Yes | Yes | Yes | Yes | Yes |
| L1 assignment/private prompts or L2 oracle/truth | No | No | No | No | No |

M/A share public task context. MA is exactly their union. R adds execution
observability; MAE reorganizes exactly R's facts. These are input packets, not
implementations of model predictions, score schemas or threshold decisions.

## 6. Rendered parity and budgets

`pactlens-detector-input-v1-candidate` uses raw auditable fact JSONL for M/A/MA/R.
MAE uses grouped readable JSON by category, actor and kind. Neither representation
adds summaries, inferred agreement, harm labels or timestamps. R is not padded,
obscured or selectively deprived of information. Formatting/bytes can differ.
Render headers explicitly say source-family/grouping order is **not chronology**.

Every rendered artifact owns text and a separately bound fact manifest. Raw JSONL
and structured JSON are independently parsed from the **actual input text** back
to validated Fact records. Verification compares all reconstructed identities,
values, nulls, aliases, source/trust, completeness and order with the manifest,
plus rendered SHA-256, fact-set SHA-256, template hash, policy, size and budget.
`canonical_facts(R) == canonical_facts(MAE)` compares detached semantic records
and policy/episode identity, not an internal shared pointer or text equality.

Render text is capped at **262,144 bytes**. Any byte overflow is rejected; any
token-preflight overflow prevents creation of the model conversation. Selection
is `FULL_INVENTORY_OR_EXPLICIT_OVERFLOW_V1`. Exports use only
`<public-UUID>.<view>.json`, exclusively created, with no hidden source filename.
Conversation tuples are fresh and independent; no provider/model call occurs.

Future R−MA measures added execution observability; MAE−R measures presentation
of matched information. MAE−MA combines both differences. Information parity does
not prove presentation neutrality, token equivalence, absence of confounds or
MAE superiority. The formal selection/token/observer policy remains unfrozen.

## 7. Corrected trace budget

Trace schema v1 remains readable. Authoritative shared constants are 8,000,000
total bytes, 131,072 bytes per record, 256 records. Writer tracks actual encoded
bytes and validates header, accounting, per-record/count/total limits before any
write. A rejected budget append leaves file bytes, sequence, previous digest,
terminal flag and executor accounting unchanged. Reader retains its 8 MB limit.

No terminal-space reservation is invented. If a terminal cannot fit, the valid
prefix remains incomplete, and replay treats a missing terminal as INTERRUPTED;
no completion or new effect is manufactured. Empty files have no valid header.
Fsync/hash chaining are retained; I/O/power failure can still leave a partial
line rejected by Reader. This correction is not a filesystem durability claim.
