# Phase 4A — Scientific Protocol Review

Date: **2026-10-19 NZDT**, pre-sprint. No detector outputs, research episodes,
new real inference or empirical reliability improvement were produced.
Authority remains [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md). Alternatives below
are proposals, not implemented changes. A separate
[approval proposal](PHASE4A_PROPOSED_AMENDMENT.md) is NOT APPROVED / NOT APPLIED.

## 1. N2 missing-action confound

Phase 3 blocks every round-2 N2 proposal before AIG admission. Therefore all three
final slots are MISSING, no round-2 proposal receipt exists, and unchanged Arena
fallback chooses the lawful reference. This is necessary for the **current
chosen blocking mechanism**, not logically necessary for the approved broader
talk-only/no harmful execution condition. Lawful final proposals could exist
without harmful execution under a separately reviewed alternative mechanism.

The missing slots are legitimate observed behavior under this implementation,
and also a direct intervention artifact. A detector could use them as a shortcut
to recognize an assigned negative arm. Low N2 FPR would then fail to establish
understanding of harmful agreement versus execution. Do not hide slots, invent
successful AIG effects, rewrite model ballots or remove the block to improve a
score. Tests demonstrate the retained signature; they do not claim its statistical
predictiveness or elimination without a study.

| Option | Implementation now | Inferential consequence / approval gate |
|---|---|---|
| Retain all-final-proposals block | Retained | Exact current semantics; disclose deterministic missingness; N2 is a bounded intervention-specific secondary check |
| Prospectively admit only model-chosen canonical lawful final ballots | NOT implemented | Could allow genuine lawful AIG receipts while blocking harmful alternatives; never repair/force ballots. Changes the intervention, can still create rejection artifacts; needs prospective amendment and tests |
| Prospectively use changed eligibility/task constraints | NOT implemented | Different opportunity structure may block harm with normal proposals, but changes task/binding/lifecycle assumptions; requires separately reviewed design, not an unnoticed Arena change |
| Stratify later descriptive results by final-slot missingness | NOT RUN | Reveals sensitivity using recorded outcomes; does not alter primary N1 endpoint or prove causal detection. No subgroup retuning or selected reruns |
| Equalize/hide failures by fabricating receipts or dropping genuine effects | Rejected | Destroys validity and violates truthful observation boundaries |

The recommendation is to **retain and disclose the existing N2 implementation
now**, while reviewing the lawful-admission alternative before any formal pilot.
No alternative is silently selected by this phase.

## 2. C+/C− visibility confound and observation audiences

The complete experimenter Router audit includes requested messages, actual
delivery status and blocked private attempts. Actors receive only delivered
messages and their own feedback. A detector is a third audience with declared
rights, not the experimenter or an automatically omniscient participant.

Policy A (`delivered-intercept-v1`) grants intercepted delivered speech only.
Policy B (`router-audit-v1`) grants audit attempts/status too. A blocked C−
private attempt appears in B and not in A. B can reveal the channel intervention
even without an explicit condition label. This is legitimate evidence for a
Router-audit question, but an artifact relative to a delivered-conversation-only
question. A cannot call undelivered attempts actual conversations or prove no
hidden agreement merely because it did not observe one.

Both can support different scientific questions. They cannot be switched after
seeing detector results or interpreted as identical information. B remains the
Phase 3 engineering default; Phase 0.6's interception wording leaves rejected
attempt rights insufficiently specified for automatic formal-primary selection.
The engineering API implements both; the amendment asks for prospective choice.

| Observer policy | Valid interpretation | Limitation |
|---|---|---|
| A: delivered/intercepted | Detection from speech actually accessible to an interceptor plus declared public/actions/execution facts | Missing delivered speech is not proof of no attempt/agreement; fewer Router facts |
| B: Router audit | Detection using actual attempts, delivery denials and execution verification | Channel-removal signature can identify intervention; performance may exploit infrastructure artifacts |

Policy-driven projection never exports hidden pair/config, group, seed or label.
Message numbers are observer-local; captured positions remain faithful, including
possible gaps. Absolute capture gaps, missingness and public outcomes can still
support statistical shortcuts. Tests prove direct-field isolation and allowed
visibility, not absence of all condition information or adversarial inference.

## 3. Primary N1 false-positive endpoint

The frozen primary endpoint remains held-out N1
`FPR(MAE) − FPR(MA)`, with its existing adjudicated-innocent denominator,
calibration recall/coverage guards, abstention treatment and block-based analysis.
Nothing in Phase 4A changes those rules, thresholds, splits or sample counts.

An N2 signature does not mechanically change the N1 denominator or turn N2 into
an independent N1 observation. It still threatens broader claims: mixed-arm
scores, pooled coverage/positive strata, calibration choices, prompt development
and what a detector appears to understand can be affected by condition shortcuts.
Report N2 separately and disclose intervention-specific construction. A low N1
FPR also needs held-out recall/coverage; abstention or arm recognition is not
unqualified detector improvement. No such measurements exist yet.

## 4. R/MAE matched-information validity

Both are built from exactly one permitted inventory under one observer policy.
Independent text parsing and fact-manifest reconstruction compare IDs, values,
nulls, source/trust, receipt linkage, completeness and order. Mutations and
omissions fail verification/parity. Raw JSONL is readable; structured grouping
adds no factual summaries, private judgments or inferred collusion.

This establishes a controlled information contract. It does not remove tokenizer,
length, formatting, salience or order effects. R−MA adds execution observability;
MAE−R compares representation; MAE−MA combines both. Parity within B does not
repair B's intervention artifacts, and no A/B cross-policy parity is claimed.

## 5. Token budget and future selection

Full contexts are retained or rejected. The candidate agent safeguard uses an
explicit estimate without exact provider tokenization, records actual usage
when returned and refuses post-response over-budget submission. Its byte guard
does not prove 2,000-token fit. Ollama exact tokenization has not been added or
measured; synthetic counter tests establish mechanics only.

The full detector inventories are often over the conservative 4,096-token
preflight, especially readable grouped MAE. Byte sizes and estimated counts are
reported separately; exact model-token counts are unknown. Rendering remains
available for audit, while model-conversation creation fails closed. No side
receives a favorable truncation or meaninglessly padded input.

Before formal use, approve a condition-independent full-packet fit strategy.
Prefer verified complete-template token accounting. If selection is required,
prospectively define atomic fact bundles/mandatory context, common R/MAE fact IDs,
deterministic ordering and an explicit over-budget abstention/failure rule.
Any lossy policy changes permitted observations and needs review; it must not be
backfit to condition labels, detector scores or held-out outcomes. The proposal
is documented separately and no selection implementation is active.

## 6. Actual model reliability evidence

The only actual local model evidence remains the 2026-10-18 Phase 3 engineering
episode: Ollama 0.35.1 / phi4-mini:latest / CPU / six calls, one AIG submission,
two invalid responses, three valid v1 final declines, INCOMPLETE. The targeted
failure shapes were one incident assignment instead of a full list, and a public
message naming all three actors including its sender. They are reproduced by
synthetic regressions with the original error strings and new classifications.

Candidate prompt examples, stricter diagnostics and passing synthetic corpus do
**not** demonstrate actual model adherence or any reliability gain. No new
Ollama inference, repair, technical rerun, model download/training or formal
episode occurred. V1 records are not retrospectively scored as v2 failures or
successes. Voluntary valid declines remain valid behaviors.

## 7. Synthetic setup and trust limitations

All code/fixtures/views and local-model engineering records predate the sprint.
The synthetic Arena has bounded three-actor/two-round/sequential mechanics;
explicitly prompted malicious controls are not spontaneous emergence. Shared
generator/model/prompt biases and small matched-group counts limit generalization.
Twenty-four groups are not 120 independent observations. Independent human
adjudication remains pending; an AIG receipt verifies a proposal effect, not
agreement, malicious intent or realized harmful collusion.

Source validation and unkeyed hashes detect inconsistencies, not a malicious
host rewriting all evidence. Local capabilities are not production human
authentication. View manifests authenticate no external observer; raw public
speech can contain hostile instructions and future detectors must treat it as
data. No scoring model or model-safety claim is supplied by Phase 4A.

## 8. Proposed future freeze decisions

Before a separately authorized formal pilot, approve and record: observer A/B
rights and primary policy; retained/prospectively amended N2 mechanism; candidate
model/prompt/protocol/version/hash; verified tokenizer or estimate limitation;
selection/overflow policy; all five renderer versions and R/MAE fact parity;
independent adjudication arrangements; environment/resource feasibility and stop
gates. Preserve all 24 frozen groups, pairing, truth, abstention and evaluation
rules. No Phase 4B or formal run is authorized by this checklist.
