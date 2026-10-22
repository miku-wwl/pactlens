# Phase 4E + Phase 5A execution report

2026-10-22 NZDT. Pre-sprint engineering. Baseline main/local/origin/remote:
`65a003263cccfb3d0370db13b086de958dab0db4`; initial tree clean.
[Discrepancies recorded before source edits](PHASE4E_BASELINE_REVIEW.md).

**Delivery is implemented and tested; scientific launch remains NO-GO.**

| Actual observation | Result |
|---|---|
| Isolated original baseline | 832 passed in 554.84s |
| Final regression | 885 passed in 583.32s |
| Paid generation requests | 3 Agent + 8 Detector = 11 |
| Authenticated metadata requests | 1 GET /models; 12 total DeepSeek HTTP requests |
| Estimated peak/cache-miss usage expense | USD 0.007354, including truncated generation |
| Retained conservative reservations | USD 0.015012; ceiling USD 5 |
| Real Agent N3 | 3 valid submits /6 opportunities, 3 verified durable receipts |
| N3 stopping reason | Round-2 complete request estimate 2132 >2000 before dispatch |
| Further Agent conditions | C+/C−, N1, N2 NOT RUN; gate failed, no replacement |
| Detector packets | 12 attempted of 15; 8 dispatched, 4 pre-dispatch overflows |
| Detector contract | 4 valid schema/citation results, 3 INVALID_OUTPUT, 1 truncation |
| Effective scored predictions | 0; all 12 persisted attempts abstained |
| Full schedule dry run | 120 slots, 360 fresh stores/scopes, zero inference/effects |
| Formal study / human adjudication | 0 / NOT RUN |

No retry, favorable rerun, parser repair, Pro substitution, cap increase or paid
search/fetch occurred. Native Responses structured output works for some outputs;
this does not establish its enforcement of every application constraint.

Implementation reuses the strict parser, compact observation, existing harness,
real installed AIG, evidence renderer, detector runner, matched analysis and
reviewer preparation. Adds fixed-host HTTPS, atomic inference reservations,
separate v3.2 candidate, authoritative v2 abstention/analysis bridge, full metadata
scheduling, guarded Pilot composition and watermarked synthetic export.

[Provider](PHASE4E_DEEPSEEK_PROVIDER.md), [Agent](PHASE4E_MODEL_QUALIFICATION.md),
[Detector](PHASE4E_DETECTOR_QUALIFICATION.md), [measurement/cost](PHASE4E_COST_AND_TOKEN_REPORT.md),
[abstention](PHASE4E_ABSTENTION_INTEGRITY.md), [launch/readiness](PHASE5A_STUDY_LAUNCH_READINESS.md),
[test matrix](PHASE5A_TEST_MATRIX.md) contain the evidence and limitations.

Source pin/lock, Arena, AIG consumer, frozen protocol/splits, old prompts and old
reports remain unchanged. No commit, push, tag, release, deployment, submission,
formal calibration, held-out outcome access or next-phase work occurred.

Review archive: `D:\workshop\oct\pactlens-phase4e-phase5a-review.zip`.
Adjacent verification receipt supplies its final SHA-256 and member verification.
