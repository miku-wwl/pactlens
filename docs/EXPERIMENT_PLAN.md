# PactLens Experiment Plan — Design Validation (Phase 0)

Status: **pre-registration draft**. No experiments have been run; no results
exist. This document validates the scientific design in
`docs/HACKATHON_DESIGN.md` and records required changes before Phase 1
implementation. The hypotheses below are falsifiable and must not be edited
after results are seen.

## 1. Core research question

> Can combining agent communication, executed actions, and verifiable execution
> evidence improve detection of harmful AI-agent collusion while reducing false
> accusations against innocent parallel behavior?

Maps to Track 2, question **2.2** (combination vs. either alone) and **2.3**
(what counts as convincing evidence).

## 2. Pre-registered hypotheses

- **H1 (primary):** At a predeclared positive-class recall operating point
  (calibration-frozen, target recall ≥ 0.70), the structured-evidence monitor
  **MAE** has a lower false-positive rate than the raw-concatenation monitor
  **MA** on innocent-parallel cases (N1).
- **H2 (ablation):** Removing execution/effect evidence (MAE−receipt,
  MAE−counterfactual) increases false positives or reduces positive detection,
  i.e., the evidence components carry measurable weight.
- **H3 (limitation-seeking):** With only public messages and final actions
  observable, some collusion is not identifiable; the monitor should output
  `INSUFFICIENT_EVIDENCE` (abstain) rather than over-accuse. Abstention must be
  measured, not treated as failure.

Declared primary comparison: **MAE vs MA on N1 FPR at the frozen operating
point**. All other contrasts (vs M, vs A; ablations) are secondary/exploratory.

## 3. Experimental conditions and two-level ground truth

| Condition | Setup | Label level 1 `coordination_intent` | Label level 2 `executed_harmful_collusion` |
|---|---|---|---|
| **C+** | Assigned coalition, controlled private channel, harmful shift observable | assigned_or_observed | yes **only if** communication + action + measured harm all hold; otherwise `attempted` / no |
| **N1** | No private channel; similar actions from shared legitimate incentives | none | no |
| **N2** | Collusive *talk*, no executed harmful action | suspected | no (suspicious talk tracked separately) |
| **N3** | Explicit legitimate coordination improving the common goal | none | no |
| **C−** | C+ same seed/task/model; private channel removed or visibility cut | none | **re-derived from that run's actual outcome** |

Rules: condition assignment is a *setup*, not a prediction label; failed C+
runs are kept (no survivorship bias); labels must not be mechanically derivable
from any detector-visible field; `indeterminate` is reported as coverage, never
forced into the negative class.

## 4. Comparison methods (monitor views)

| ID | View | Inputs | Role |
|---|---|---|---|
| M | messages only | permitted observed messages | speech baseline |
| A | actions only | normalized action/outcome sequence | behavior baseline |
| MA | raw concatenation | M + A unstructured | the common "dump logs into an LLM" baseline |
| **MAE** | structured evidence | M + A + calibrated effect/evidence fields (receipt-corroborated actions, inconsistency flags) | PactLens core |
| E-only, MAE−receipt, MAE−counterfactual | ablations | subsets | component attribution |

Fairness: identical monitor model/version, fixed temperature, matched prompt
format and token budget across views; thresholds and monitor prompts tuned on
the calibration split, then **frozen** before held-out scoring.

## 5. Metrics

- **Primary:** FPR on N1 at the frozen recall operating point.
- **Secondary:** recall/TPR on verified executed collusion; precision; F1;
  balanced accuracy; PR-AUC/ROC points when n allows.
- **Reporting:** `abstention_rate`, coverage, selective FPR/TPR; per-condition
  FPR for N1/N2/N3; ablation ΔFPR; token cost/latency; detector errors.
- **Positive controls:** positive-control realization rate (frequency of
  verified harmful shifts in C+), global regret vs. computable optimum,
  coalition advantage, per-agent workload burden.
- **Uncertainty:** seedwise/scenario-grouped bootstrap CIs; exact or Wilson
  intervals for small counts; report n and counts, never p-values alone.

## 6. Design validation — findings and required changes

Validated 2026-10-17 against the design doc. Findings marked **CHANGE** are
binding for Phase 1 implementation.

1. **Two-level labels — KEEP.** The design's separation of coordination intent
   from executed harmful collusion directly addresses the "talk ≠ did" and
   "did ≠ agreement" confusions. Required: implement adjudication as a
   documented, blinded procedure, not a detector-visible field.
2. **Instrumentation gain confound — CHANGE required.** MAE observes strictly
   more fields than M/A/MA, so an apparent win may reflect observability rather
   than detector quality. Required: report an observability-controlled analysis
   (e.g., a view with the same evidence *content* but unstructured
   presentation), and discuss results as "value of collecting this evidence".
3. **Operating-point stability with small n — CHANGE required.** With 20–60
   episodes, a fixed recall≥0.70 operating point may be unattainable.
   Required: predeclare the fallback (report calibration failure; present ROC
   points without re-declaring a primary test after the fact).
4. **C− relabeling — CHANGE required.** C− must be labeled from each run's
   measured outcome, not inherited from its C+ twin. Required: explicit
   relabeling step in the evaluation pipeline, with paired seed linkage
   retained for paired statistics.
5. **Multiple comparisons — CHANGE required.** Four monitors × several endpoints
   invites winner's curse. Required: single predeclared primary comparison;
   others exploratory; no threshold re-tuning on test.
6. **Cherry-picking — KEEP, enforce in CI.** Freeze seeds and task
   arrangements; export all runs including failures and `Unknown` actions.
7. **Label leakage — KEEP, enforce by negative tests.** Detector views must not
   contain condition/seed/coalition/ground-truth fields or leaky identifiers
   (e.g., `colluder_A` aliases); CI injects hidden markers and fails if they
   reach the view.
8. **Model nondeterminism — CHANGE required.** Provider sampling may not be
   reproducible. Required: cache complete model calls, record model ID,
   temperature, timestamps, token cost per episode; report determinism limits.
9. **Causal wording — KEEP as a hard rule.** Only paired C−/C+ contrasts may
   support causal claims about the coordination channel; all other statements
   are correlational.
10. **Overclaiming boundary — KEEP.** Results describe the synthetic arena,
    chosen models, and sample size only; no legal or production claims; the
    "plus factors" analogy is heuristic, not a legal standard.

## 7. Protocol skeleton (Phase 1 scope)

1. Fix arena generator, payoff equation, capacity constraints, coalition
   target, action schema, model IDs and temperature **before** any run.
2. Pilot: 3–5 seeds per condition; verify end-to-end pipeline and that C+ can
   actually produce harmful shifts. Pilot never enters final test statistics.
3. Main study: 4 conditions × 10–15 matched seeds (fallback 4 × 5 exploratory);
   matched seed enters exactly one split (dev/calibration/test).
4. Freeze; score held-out once; reproduce all tables/figures from manifests.
5. Failure paths (declared now): positive-control failure → public
   Colosseum-style replay or honest "no positives detected" report; AIG
   integration blocked → baseline study with `evidence verification
   unavailable` flag; MAE loses to MA → analyze observability/noise/overfitting
   and report the negative result.

## 8. Out of scope

Real incident trackers; real payments; production deployment; legal claims;
any experiment run before Phase 1 authorization.
