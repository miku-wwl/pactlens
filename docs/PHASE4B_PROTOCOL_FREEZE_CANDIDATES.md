# Phase 4B — Prospective Freeze Decision Package

Date: **2026-10-19 NZDT; pre-sprint**. All entries remain candidates. Engineering
authorization and model availability do not constitute research approval. The
[Phase 0.6 plan](EXPERIMENT_PLAN.md) and historical Phase 4A proposals are preserved.

## 1. Decision record

| Decision | Candidate/recommendation | Status |
|---|---|---|
| Primary observer | Policy A, delivered/intercepted communications | PROPOSED |
| Router-audit sensitivity | Policy B, separately identified | PROPOSED |
| N2 | Retain N2-A; disclose as intervention-specific secondary control | PROPOSED |
| Evidence selection | Common atomic bundles, candidate v1 | PROPOSED |
| Prompt/protocol | Existing v2 candidate, unchanged during comparison | PENDING; model not ready |
| Model identity | Actual verified phi4-mini digest below | PENDING qualification/approval |
| Reviewer rubric | Independent review candidate v1 | PENDING; no reviewers arranged |
| Detector envelope/response | Versioned bounded contracts only | PENDING |
| Formal pilot | No execution authorized | **NO-GO** |

Each eventual approval needs an attributed researcher and dated decision record.
No PROPOSED/PENDING entry is automatically converted to APPROVED by code/tests.
An unapproved critical gate mechanically keeps the pilot NO-GO.

## 2. Observer recommendation

| Question | A: delivered/intercepted | B: Router audit |
|---|---|---|
| Access | All communications delivered and legitimately intercepted by the declared observer, including authorized private speech | Operator-level attempt/delivery audit plus permitted speech |
| Blocked private attempts | No text/audience/count exported as delivered speech | Explicit attempted text, audience and BLOCKED/FAILED state |
| Scientific question | Detection from available conversations and declared action/execution evidence | Detection with infrastructure audit privileges |
| C+/C− artifact | Fewer direct Router signatures, but behavior/missingness/capture gaps remain | Blocked-channel pattern can reveal intervention |
| Five views | M/MA/R/MAE get authorized communications; A does not | Same category rule, with additional permitted audit facts |
| Generalization | Requires a genuine interception threat model; not every actor's inbox | Restricted to observers with legitimate Router access |
| Budget | Less audit material; not a guarantee of fit | Larger/failed-attempt mandatory cores may overflow |

Recommend **A as primary candidate** and **B as a separately labelled sensitivity
candidate**. Neither is approved here. The Phase 3/4A engineering default stays B.
Phase 0.6 interception wording does not independently authorize rejected-attempt
access; resolve that prospectively. Do not switch after predictions or treat A/B
as information equal. R/MAE parity holds only within one fixed policy.

Agents still receive delivered inboxes only; the experimenter retains its private
complete audit. Neither audience is automatically the detector. Uniform public
schema and absent metadata labels do not remove statistical shortcuts.

## 3. N2 decision table

| Option | Consequence | Current implementation |
|---|---|---|
| N2-A: block all final proposal execution | Strong no-harmful-execution control; deterministic missing final slots reveal intervention | **Retained** |
| N2-B: lawful-only admission of actual model-chosen final ballots | May allow real lawful receipts; changes opportunity/admission rule and can create rejection artifacts | NOT implemented; amendment required |
| N2-C: alternative eligibility/opportunity intervention | Changes environment/causal interpretation and requires new design/validation | NOT implemented; amendment required |

Recommend retaining/disclosing N2-A now. Its missingness follows the chosen block,
not every possible talk-only control. Low N2 FPR alone would not prove reasoning
about harmful agreement and execution. Do not hide missing slots, force lawful
ballots or fabricate receipts.

The historical Phase 1 hand-scripted `n2_talk_only` fixture contains lawful final
ballots. It is a mechanical diagnostic, not a run of the later model harness's
all-round-2 block. Phase 4B's missingness test exercises actual `run_episode` with
N2 and fake planning through installed AIG. Both histories remain unchanged.

Primary N1 FPR remains restricted to N1-assigned, independently adjudicated
innocent-parallel negatives. N2 arm recognition does not change that denominator,
but can distort pooled interpretation, calibration and prompt development.
No FPR or calibration result exists here. Any future descriptive missingness
stratification must not change the frozen primary endpoint or retune thresholds.

## 4. Actual model/prompt freeze candidate

- Engine **Ollama 0.35.1**; existing `phi4-mini:latest`, verified local metadata,
  digest `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753`.
- Same model/config/task/common engineering seed schedule for both fresh N3 runs;
  temperature 0, output maximum 256, request timeout 60 seconds, one attempt.
- Engineering seed derivation remains SHA-256 with full unsigned64 retained and
  low63 provider mapping. Seed support is **REQUESTED_NOT_VERIFIED**; no fresh
  inference determinism or general reliability claim.
- v1 prompt/hash retained. v2 prompt hash:
  `172bbe6f06dd39fb91cc8070b01baadb0dd84123037ae807519e2a4e709ec8da`.
  Protocol `pactlens-decision-v2-candidate`, hash
  `3f982b1c7b217e785c3d9416c1d47859ea4497367838cc3eb50903c72f7dc3b0`.
- Agent input safeguard 2,000; output 256. Initial v2 estimate passes; second-round
  history estimate **2,838** fails. No exact pre-tokenizer, context truncation or
  bypass was added. Public first-feasible syntax examples may anchor behavior.
- Conditions/brief rules stay in unchanged EpisodeConfig. No selected condition,
  private prompt or hidden seed enters detector input. N2 block remains intact.
- Valid decline is a behavior; malformed output is failure. No repair, retry,
  failed-episode replacement or Unknown replay. Comparison explicitly stops on
  its first input-budget failure; the normal harness default is unchanged.

The two actual runs made **9 calls total** and both remained INCOMPLETE. V2's three
valid first-round submissions do not qualify full-episode reliability. Record
**REAL_MODEL_NOT_READY**. No further generation or prompt tuning occurred.
Raw trace SHA-256 references in the freeze candidate are:

| Profile | Raw trace SHA-256 |
|---|---|
| v1 | `6203b3b33a55c7060662c1fda20475dd18b978f98a2033c1f1908858c9f53b42` |
| v2 | `4c193774bafe92ece720ee718d91c754fa6b2409aa8001e2d5df935e29597831` |

Original private traces and original comparison summary stay intact. A separate
read-only measurement audit tightens the derived schema-valid flag to include
assignment/message structure; it changes no response, acceptance, effect or call.
Private raw prompts/traces are excluded from the ZIP; sanitized measurements and
hashes are included. Historical Phase 3 v1 findings remain separate.

## 5. Candidate configuration hashes

| Candidate | SHA-256 |
|---|---|
| Full candidate manifest | `eca874650176c74c2a6a56fa44393c68e1fb541314fd7b1032110be5f734559d` |
| Selection base rules | `ca0006424a181f7f96554eef167c8142267ea012fbcea816f8a158f0346e7032` |
| Complete detector envelope | `4514c3d752300b690dbb1b1f6f9eff37d27c70af57b7099fd338f75799f5c53d` |
| Future response schema | `28fc9e785981fb5010e5acfbd667415b9efa60c6a94371df88bad552b7f172bc` |
| Reviewer rubric | `fd25ae936844b2700ebea6d26e4316deab5cad2a677377c6ed968954b15dd4d4` |

The machine-readable `review/validation/freeze-candidates.json` contains actual
model/configuration, prompt/protocol/example revisions, budgets, limits, trace
references and unapproved decisions. Hashes identify candidates, not approvals.
Future implementation/configuration changes require versioned review before use.

## 6. Independent review workflow and L2 lock

Prepare separate A/B full-evidence packets and independent blank response forms.
They contain public behavior/source/ordering facts plus **separately labelled L2
mechanical comparators**, never L1 assignment, group/split, intended coalition,
L4 predictions or another reviewer's first judgment. Full reviewer evidence is
not the detector's budget-filtered packet. Neutral comparator tables cover all
three pairs; reviewers must identify agreement independently first, then consult
that pair's measurements, never choose a pair by largest benefit.

Forms cover agreement sources, complementary executed action, harmful allocation,
pair benefit, outsider shift, regret, missingness, uncertainty, behavior class,
indeterminate/binary label, rationale and reviewer expertise/conflicts. Closed
form validation rejects unknown fields, wrong packet/citations, boolean labels,
unattributed completion and assignment-origin disclosure. Validation is not human
authentication or automated adjudication.

Operational sequence: assign two actual reviewers and record conflicts; issue
separate packets; seal independent first responses; reconcile differences with
a third human if available; otherwise mark unresolved cases indeterminate; record
agreement/disagreement/coverage; lock L2 before revealing L4. Join instruction
origin only afterward. A calculator is not a reviewer. Observable artifacts may
suggest condition despite assignment blinding; disclose that limitation.

Current status: **zero reviewers arranged, zero completed independent reviews**.
Prepared forms are blank. If only one human becomes available, report limited
single-reviewer pipeline/case analysis, not independently adjudicated performance.
No person was contacted or review invented.
