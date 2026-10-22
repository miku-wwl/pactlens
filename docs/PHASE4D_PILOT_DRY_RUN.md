# Phase 4D — Pilot operations dry run and feasibility

2026-10-22 NZDT. **20 engineering episodes / 0 formal slots / 0 model inference.**

`DryRunConfig` is frozen/versioned and yields a deterministic manifest. The actual
run used four distinct ENG matched tasks, each across all five conditions, with
fresh model contexts, stores, runtime scopes and independent receipts per episode.
It charged before each fake dispatch and wrote durable traces. Unknown stops the
affected execution; failed/incomplete episodes and unattempted counts are retained.

Actual `review/phase4d/audit/pilot-dry-run.json`: **20 episodes, 120 fake generation
requests, 0 failed/incomplete episodes, 0 unattempted slots, 108 verified local AIG
receipts** (N2 admits only its three first-round proposals). All 20 replay checks
equal original evidence with zero new calls/effects. This is orchestration/mechanics
evidence with synthetic consent, not model reliability, actual research Pilot
execution, harmful collusion realization or human approval.

Reproduce offline in fresh output/private directories:

```powershell
uv run python scripts/phase4d_audit.py review-new .runtime/engineering-new
```

The script generates only engineering fixtures/fake predictions. Never point it at
private formal stores. `formal=True` is rejected. A future formal runner still
needs an approved freeze and reviewed mapping to the existing manifest; this
phase deliberately provides no formal-dispatch switch.

## Frozen nominal call and token envelope

| Split | Episodes | Agent maximum | Detector views | Total generations |
|---|---:|---:|---:|---:|
| Pilot | 20 | 120 | 100 | 220 |
| Calibration | 50 | 300 | 250 | 550 |
| Held-out | 50 | 300 | 250 | 550 |
| Total | 120 | 720 | 600 | 1,320 |

Original planned maximum: 3,897,600 input and 337,920 output tokens. Additional
sensitivity or packet calls require separate approval and a revised envelope.

## Measured local runtime projection

New agent calls totaled 144.825089 s, mean 24.137515, min 15.695742,
max 31.774102. Detector smoke totaled 78.965413 s, mean 39.482707,
min 38.589726, max 40.375687. These are six/two engineering observations on a
shared CPU while tests also ran; they are not clean hardware benchmarks or valid
detector performance observations.

At full 720+600 calls, minimum-observed timing projects **9.57 h**, mean **11.41 h**,
maximum-observed timing **13.08 h**, before AIG/storage/review overhead. These are
explicit extrapolations, not guaranteed bounds. Even the optimistic measured-rate
projection misses the frozen eight-hour model-time gate. Do not assume a future
speedup or silently shrink the study. Local API fees are $0; electricity and human
time are unmeasured. No cloud/paid-provider estimate is treated as a quotation.

Two independent first reviews of 120 episodes mean 240 review assignments. At an
assumed 5–10 minutes each, that is 20–40 person-hours plus disagreement resolution;
these are workload assumptions, with zero reviewers arranged/zero reviews done.
Schema failures, input overflows, Unknown stops, incomplete captures, missing
reviewers, unqualified detector and inconsistent submission access remain risks.

Within the current authorization, the defensible deliverable is reproducible
engineering/failure evidence and a study decision package. Any incomplete future
formal study must retain failed/unattempted slots, disclose missing denominators
and report protocol non-estimability rather than replacing controls or weakening
gates. No actual formal Pilot launch is approved by this dry run.
