# Phase 4B — Pilot Readiness Gates

**2026-10-19 NZDT; pre-sprint. Formal pilot: NO-GO.** Engineering completion does
not approve study choices or model readiness. The machine report is included as
`review/validation/pilot-readiness.json` in the review ZIP.

## 1. Independent decisions

| Readiness | Result | Evidence / remaining gate |
|---|---|---|
| Engineering | **GO** | 607 tests, preserved installed AIG, common selection/parity, complete-envelope fit or typed failure, isolated local comparison and safe replay |
| Model | **BLOCKED — REAL_MODEL_NOT_READY** | v1 invalid response and both episodes INCOMPLETE; v2 stops before round 2 at input preflight; at most nine calls cannot qualify general reliability |
| Detector inputs | **CONDITIONAL GO** | 33/34 audited sets fit an estimate; one actual Router core overflows; lossy subsets insufficient for full episode audit; exact tokenizer and policy review pending |
| Formal pilot | **NO-GO** | Critical approvals, qualified model/token feasibility and reviewer arrangements unresolved; no formal-run authorization |

These are separate gates, not a composite success score. A passing estimate or
valid three-call prefix does not make the model/study ready.

## 2. Frozen allocation and evaluation

| Split | Independent groups | Planned episodes | Executed |
|---|---:|---:|---:|
| Pilot | 4 | 20 | 0 |
| Calibration | 10 | 50 | 0 |
| Held-out | 10 | 50 | 0 |
| Total | 24 | 120 | **0** |

Authoritative [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) is byte-identical to the
pushed Phase 4A baseline. No split/task/condition reselection or official slot
execution occurred. All five matched conditions stay in one block; C+/C− remain
independently executed paired episodes when a future run is authorized.

Frozen recall ≥0.70; calibration coverage ≥0.80 overall/positives/primary N1;
threshold grid `{0,.05,.10,...,1}`; held-out innocent N1 FPR contrast; abstention
denominators; matched-coverage analysis; block uncertainty and 2,000 bootstrap
draws; pilot ≥2/4 realized C+ and later realization floors all remain unchanged.
No threshold is selected, no score evaluated, no prediction or statistical table
generated. Budget failure remains a future logged abstention, not a dropped case.

## 3. Mechanical engineering gate evidence

Machine gate names cover pinned AIG integrity, isolated contexts, Unknown without
retry, receipt-to-Arena reconstruction, capture/replay, trace limits, deterministic
views, selected semantic parity, complete budget/failure, private-field isolation
and versioned diagnostics. All have passing regression evidence; see the
[test matrix](PHASE4B_TEST_MATRIX.md). Installed AIG is 0.2.0 at immutable
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`, 57 RECORD hashes verified, five-second
budget unchanged. No new core execution framework is introduced.

Actual local stores have receipt counts `[1,1,0]` for v1 and `[1,1,1]` for v2.
Read-only verification reconstructs the same captured Arena states and leaves
store bytes unchanged. Pure replay makes zero model/Gateway/new-effect calls.
The original Phase 3 trace remains separate; v1 history is never scored as v2.

## 4. Unapproved methodological gates

Primary observer A; B sensitivity; retained N2-A interpretation; common bundle
selection; model/prompt/protocol; reviewer rubric; detector interface; reviewer
arrangements; tokenizer/coverage feasibility; model reliability review; and
formal-run authorization are **NOT APPROVED** in the machine report. Candidate
choices are in the [freeze package](PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md).
Attribution and a dated researcher decision are required for approvals. No
default API value, test result, local model availability or engineering command
supplies that approval.

There are **zero reviewers arranged and zero independent reviews completed**.
Separate A/B full-evidence packets and blank closed forms are prepared, with
privileged mechanical measurements labelled L2 and no assignment/L4/peer labels.
Use sealed first passes, third-human reconciliation or unresolved indeterminate,
and lock L2 before L4. One reviewer permits only disclosed limited case/pipeline
analysis, not independently adjudicated performance. Do not treat code or a
calculator as a second reviewer.

## 5. Before any later authorized pilot

Resolve candidate token feasibility without weakening existing rules or tuning
on held-out outcomes; review evidence loss/observer rights and N2 interpretation;
qualify and prospectively freeze the model, prompt, views, rubric and provider
envelope at prescribed protocol boundaries; arrange real independent review;
record explicit run authorization and unchanged stop/realization/coverage gates.
This checklist authorizes no inference, detector, Phase 4C or formal execution.
Phase 4B stops after verification, reporting and the external review package.
