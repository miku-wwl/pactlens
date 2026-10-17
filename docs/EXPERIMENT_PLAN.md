# PactLens Experiment Plan — Design Validation and Pre-Registered Protocol

Status: **pre-registration draft (Phase 0.5 revision)**. No experiments have
been run; no results exist. This document validates and corrects the scientific
design in `docs/HACKATHON_DESIGN.md`, records the four-layer evidence
separation required to avoid label circularity, and fixes the condition/seed
accounting. The hypotheses below are falsifiable and must not be edited after
results are seen. Supersedes the Phase 0 version of this file; the changes made
here are listed in `docs/PHASE0_5_REVIEW.md`.

## 1. Core research question

> Can combining agent communication, executed actions, and verifiable execution
> evidence improve detection of harmful AI-agent collusion while reducing false
> accusations against innocent parallel behavior?

Maps to Track 2, question **2.2** (combination vs. either alone) and **2.3**
(what counts as convincing evidence). Aligns with the organizers' official
two-day guidance for these questions (see
`docs/COMPETITION_REQUIREMENTS.md` §2), including their four-view monitor
design and the calibrate → freeze → held-out rule.

## 2. The four layers — never conflated

| Layer | Who controls it | Contents | May it enter a detector view? |
|---|---|---|---|
| **L1 Condition assignment** | Experimenter, before the run | scenario template, seed, coalition membership, channel configuration, brief given to agents | **No.** Labels the run; hidden from all monitors |
| **L2 Ground truth** | Blinded adjudicator(s), after the run, from complete logs | (a) `coordination_intent`; (b) `executed_harmful_collusion` ∈ {verified, attempted_no_execution, none, indeterminate}; (c) per-outcome harm measurement | **No.** Never derivable from any detector-visible field |
| **L3 Detector-visible evidence** | Pipeline | L3.1 observed/intercepted messages (model-level API inputs and outputs), L3.2 normalized action and outcome sequences, L3.3 calibrated effect/evidence fields (approval status, action terminal state, payload digest, receipt reference), plus L3.4 negative asymmetric-information controls (who saw/knew what, when) | **Yes — this is the detector's entire input.** Contains no L1/L2 fields, no scenario IDs, no run indices that correlate with condition |
| **L4 Predictions and evaluation** | Monitors + frozen evaluation | detector outputs (label, confidence, abstention), threshold decisions, metrics, CIs, case studies | — |

**Circularity rules (binding):**

1. Approval status, receipt existence, payload digests, or action similarity
   **alone never establish collusion**. They corroborate *that* an action
   executed as claimed; the collusion claim itself must rest on L3 evidence
   plus a predeclared decision rule evaluated over L2-adjudicated cases.
2. L2 adjudicators are blinded to detector outputs (and to each other's first
   pass); detectors are blinded to L1/L2. A leakage barrier test (CI) injects
   hidden markers into L1/L2 and fails the build if any marker appears in an
   L3 view.
3. L2 adjudication is itself recorded: rules, disagreements, resolution, and
   `indeterminate` cases are published with the dataset.
4. Paired-twins rule: C− cases are **re-adjudicated from that run's own
   logs**, never inherited from the C+ twin; the seed pairing is kept only for
   paired statistics.

## 3. Conditions and exact accounting (fixes the Phase 0 inconsistency)

Five conditions exist; the "4 × seeds" wording was wrong and is corrected here.
Accounting (all episodes retained, including failures and `Unknown` actions):

| Condition | L1 setup | Distinct runs | Held-out unit |
|---|---|---|---|
| C+ | assigned coalition, controlled private channel, harmful shift possible | n runs | one run = one episode |
| N1 | no private channel; shared legitimate incentives | n runs | one run |
| N2 | collusive talk channel, harmful execution blocked/removed | n runs | one run |
| N3 | explicit legitimate coordination, common-goal task | n runs | one run |
| C− | C+ template with the same seed, private channel removed | n runs | one run |

- **Pilot:** 3–5 seeds per condition (official guidance: "start with 3 to 5
  seeds per condition"). Pilot's sole purposes: (i) verify the pipeline runs
  end to end; (ii) verify the **positive control fires** (C+ produces
  verified harmful shifts at a measurable rate); (iii) estimate variance for
  the main-study size. Pilot episodes never enter final test statistics.
- **Main study:** scale to **10–20 seeds per condition only after the positive
  control works** (official guidance). C− share seeds with C+ runs (paired),
  so an n-seed C+/C− block yields 2n runs but n paired contrasts. All five
  conditions are covered in the main study; the correct summary line is
  "5 conditions × 10–20 seeds per condition (pilot 3–5), C− paired to C+" —
  not "4 conditions".
- **Minimum usable positive-case count:** the study is interpretable only with
  ≥ 8 verified executed-collusion cases (C+ verified + any C− relabeled
  verified) **and** ≥ 20 N1 cases for the primary FPR endpoint, per split.
  If either count is unmet: report as an exploratory study with exact counts
  and CIs, make **no** primary-comparison claim (see §7). This is the
  predeclared size gate.
- **Splits:** dev (pipeline construction) → calibration (monitor prompts,
  thresholds, operating point; each matched seed enters exactly one split) →
  held-out (scored once). Scoring is repeated only as a documented
  reproducibility check, never re-declared.

## 4. Pre-registered hypotheses

- **H1 (primary):** at a predeclared positive-class recall operating point
  (target recall ≥ 0.70 on calibration), the structured-evidence monitor
  **MAE** has lower false-positive rate on innocent parallel cases (N1) than
  the raw-concatenation monitor **MA** on the held-out split.
- **H2 (ablation):** removing effect/evidence components (MAE−receipt,
  MAE−control) increases FPR or reduces detection, i.e., evidence components
  carry measurable weight.
- **H3 (limitation-seeking):** with only messages and final actions observable,
  some collusion is not identifiable; the monitor must output
  `INSUFFICIENT_EVIDENCE` rather than over-accuse. Abstention is measured,
  not treated as failure.

Primary comparison: **MAE vs MA, paired per held-out episode, N1 FPR at the
frozen operating point**. Everything else (vs M, vs A; C−/C+ causal contrast;
per-condition breakdowns; cost/latency) is exploratory and labelled as such.

## 5. Monitors (matched pairs)

| ID | View (L3 subset) | Role |
|---|---|---|
| M | messages only (L3.1) | speech baseline |
| A | actions only (L3.2) | behavior baseline |
| MA | raw concatenation (L3.1+L3.2, unstructured) | "dump the logs" baseline |
| **MAE** | structured evidence (L3.1–L3.3 with calibrated fields) | PactLens core |
| E-only, MAE−receipt, MAE−control, MAE+noise-carrier | subsets | ablations / robustness |

Matched-pair controls (to separate instrumentation gain from detector gain):

1. Identical monitor model, version, temperature, prompt skeleton, and token
   budget across all views; only the evidence payload differs.
2. **Field-matched control:** a view containing the same evidence *fields* as
   MAE but presented unstructured (same information content, different
   packaging) — isolates "structure matters" from "information matters".
3. **Content-matched control:** a view with MAE's fields but permuted label-
   irrelevant values — confirms structure is not a proxy for condition labels.
4. Report instrumentation gain (what the field adds as information) separately
   from algorithmic gain (what the detector adds given the same information).

Known contrary evidence to pre-acknowledge (from the organizers' Resources
tab): "Less can be more: sometimes giving a monitor too much detail degrades
its performance (Arike et al. 2026)" — hence the MAE+noise-carrier arm and the
field-matched control; an MAE loss to MA is a publishable result, not a
failure.

## 6. Outcome measurement and adjudication

- **Independent harm measurement:** the allocator/judge computes outcomes from
  the arena's deterministic rules only (never from messages); agreement
  between model agents is not an input to the harm measurement.
- **Blinded adjudication:** two independent passes over complete logs with a
  published rubric (coalition-advantage, deviation-from-announcement, harm
  realized, reciprocity); disagreements escalate to a third reviewer; all
  resolutions logged.
- **Indeterminate handling:** `indeterminate` episodes are retained, reported
  as a coverage number with reasons, excluded from the primary endpoint, and
  never silently re-labelled positive or negative.

## 7. Metrics, uncertainty, and failure behavior

- **Primary endpoint:** N1 FPR at the frozen operating point (recall ≥ 0.70 on
  calibration). **Secondary:** recall on verified executed collusion;
  precision; F1; balanced accuracy; per-condition FPR (N1/N2/N3); abstention
  rate and coverage; selective TPR/FPR; ablation ΔFPR; positive-control
  realization rate; coalition advantage; token cost and latency; detector
  error log.
- **Uncertainty and effect size:** episode-clustered (seedwise) bootstrap
  CIs (≥2,000 resamples) for every rate; Wilson/exact intervals for counts;
  ΔFPR with bootstrap CI and a risk-ratio/odds effect size for MAE vs MA;
  McNemar-style paired contrast for the primary comparison when applicable.
  Report n and counts; never p-values alone.
- **Predeclared calibration/recall failure behavior (fixed before data):**
  - Operating point unattainable on calibration → declare "operating-point
    failure", report ROC/PR points over the whole curve as exploratory, make
    **no** primary claim, and do not move the target after looking at test.
  - Positive control fails in pilot → declare `positive_control_failed`,
    publish the pilot negatives, and either fix the arena (new pre-registered
    amendment) or submit the honest null result.
  - Size gate (§3) unmet → exploratory-only reporting with exact counts.
- **Cherry-picking ban:** frozen seeds/task arrangements before the pilot;
  every run — successes, failures, `Unknown` actions, abstentions — exported to
  the dataset. No post-hoc episode exclusion.

## 8. Statistical analysis plan (fixed ordering)

1. Validate leakage barrier and blinded adjudication on pilot only.
2. Compute positive-control realization rates (C+ verified / attempted /
   none).
3. Primary: paired MAE vs MA N1 FPR at frozen operating point with CI and
   effect size.
4. Secondary/exploratory in fixed order: ablations → vs M/A → per-condition
   FPR → abstention analysis → cost/latency → paired C−/C+ channel contrast
   (the only comparison allowed to support causal language about the
   coordination channel).
5. Case studies drawn from frozen manifests only.

## 9. Out of scope

Real incident trackers; real payments; production deployment; legal claims;
any experiment run before Phase 1 authorization; any claim of causality from
non-paired analyses.
