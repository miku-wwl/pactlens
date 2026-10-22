# Phase 5A.3 + 5B qualification — 2026-10-22 NZDT

**Budget qualification succeeds; formal Pilot remains NO-GO. Recommended next path: B, a separately approved reduced exploratory study.** Complete evidence can now be scored; a genuine realized C+ positive and independent adjudication remain absent.

Entry working tree was clean. Local HEAD, origin/main and fresh remote main matched `3145710b993a2c6d6e8f27c795456b78acdaf193`. AIG remains the installed 0.2.0/full `7261fdd2…` pin, 57 verified RECORD hashes and five-second execution. No shared-core change, commit, push, release, deployment, submission or formal episode.

## Actual results

- New profile: **4096 Agent / 8192 Detector input**, both outputs 256. Historical 2000/4096 profiles, prompt hashes and prediction decisions remain unchanged.
- **63 generations**: 30 Agent + 33 Detector; one model metadata GET; zero retry, replacement or optional-control generation. Limits were prospectively narrowed to 75/80 authorized calls and $2, honoring any lower environment ceiling.
- Agent: all 30 opportunities dispatched, 29 valid decisions. N3/C+/N1/C− each completed 6/6; N2 completed 5/6 valid decisions after one `INVALID_MESSAGE_ROUTING` in round one. No budget overflow, timeout or Unknown. All five Arenas finalized using prescribed voting/fallback.
- **26 genuine verified AIG commits**, 15 isolated scopes. N2 has two first-round commits; all round-two admissions are blocked. No fabricated receipt or authenticated-human-consent claim.
- Historical ten cases: R and MAE each 10/10 budget fit, 6/10 source eligible, 6 dispatched and 6 scored. Eight source-ineligible view slots were typed unsent abstentions.
- New block: all 25 views fit; 21 eligible/dispatched/valid/scored. N2 M/MA/R/MAE remain unsent because capture is incomplete. New same-profile MA/MAE joint scoring **4/5**; historical cross-budget/time technical pairing **6/10**, not new episodes or formal observations.
- Every one of 33 Detector responses is strict-contract valid with permitted citations; no model-declared insufficiency. All **15 R/MAE pairs** independently parse to equal complete source facts and equal eligibility. Twelve of 45 total slots are host-abstained, none over budget.
- Peak-cache-miss usage estimate **$0.046995** (per-request micro-dollar rounding); conservative retained reservations **$0.137325**. Actual reported usage: Agent 28,943 input / 5,111 output; Detector 99,538 input / 1,908 output. These are estimates, not invoice charges. [Official pricing](https://api-docs.deepseek.com/quick_start/pricing/) was rechecked: $0.30/M input, $1.20/M output peak. Returned alias `deepseek-flash`; documented target DeepSeek-V4.1-Flash-1017 is not an immutable weights pin.

## Gates

| Gate | Result | Reason |
|---|---|---|
| ENGINEERING | GO | 150 focused tests; one final full run: 993 passed in 484.39s; lint/format/lock pass |
| BUDGET_PROFILE | GO | All enforcement layers and actual usage qualify; old limits preserved |
| AGENT_FULL_EPISODE | CONDITIONAL GO | Four complete episodes; N2 routing error retained, all 30 calls sent |
| DETECTOR_REAL_SCORABILITY | GO | 33/33 valid effective real scores, including genuine R/MAE |
| R_MAE_COMPLETE_EVIDENCE | CONDITIONAL GO | All 15 pairs equal/fit; five source-incomplete cases cannot be repaired by context |
| JOINT_MA_MAE_COVERAGE | CONDITIONAL GO | New 4/5, historical technical 6/10; one task and tiny engineering sample |
| REAL_CPLUS_POSITIVE | NO-GO | All new final harm zero; no independent positive |
| RESEARCH_METHODS | NO-GO | Full-study positive/semantic support and 16 attributable decisions unresolved |
| PILOT_OPERATIONS | CONDITIONAL GO | New source-bound candidate/scheduler ready; pending manifest correctly denied |
| FORMAL_PILOT | NO-GO | Depends on scientific gates, review assignments, amendment, start and owner authorization |
| SUBMISSION_READINESS | NO-GO | Depends on approved scientific claim/review; no completed formal study or final submission PDF |

The latter dependent NO-GOs are not independent software defects. Formal episodes remain **0/120**, independent human adjudications zero. Calibration and Held-out stay locked.

## Evidence and verification

`review/phase5a3/live/predeclared-plan.json` freezes namespaces, task/roles/seeds/order, complete-source policy, caps and source hash before inference. `qualification-analysis.json` contains per-call accounting, parity, coverage, paired scores/reasons/latency and immutable L4 references. The existing exporter produces `analysis/engineering-matrix.csv`. `end-to-end-example.json` links six real validated N3 proposals, AIG receipts, Arena, all five genuine scores and two unsigned reviewer packets. Historical files were checked against the independently sealed prior ZIP and remained byte-identical.

One final full regression preserved all 979 previous tests and added 14. A clean checkout without private `.runtime` passed all 14 new tests, the current public-source verifier, and replayed all 45 new predictions with zero inference/effects. Actual logs are under `review/phase5a3/logs`. The review ZIP contains safe artifacts and member hashes; its adjacent independent receipt records CRC, all member hashes, source consistency and secret scans.
