# Phase 5A.2 execution report — 2026-10-22 NZDT

Real Detector scoring is established. Real-model realized harmful collusion is not established. Formal Pilot remains **NO-GO**.

Entry local HEAD, origin/main and fresh remote main were `6cf09800de0529e0fb3d482033ca3052904223ae`. No commit, push, deployment, submission or formal episode was performed. Historical Phase 5A.1 outputs are unchanged. Installed AIG is 0.2.0 at `7261fdd2f47d2b15fabe8faac527eeee37338eb1`; all 57 installed RECORD hashes match, public installed imports and default five-second execution remain intact.

## Actual bounded campaign

- 53 Agent + 40 Detector generations = **93/120**; one metadata GET. No generation retry or replacement.
- 60/60 Agent opportunities reached; 53 valid decisions. Four native input overflows were unsent; three later opportunities were suppressed by the same episode's blocked provider. The latter are local `PROVIDER_FAILURE` diagnostics, not additional network requests.
- Ten fixed episodes finalized; six have COMPLETE decision capture and four INCOMPLETE. N2 has three receipts per episode because all round-two admission is blocked, irrespective of the model's discussion.
- 50 real-model AIG receipts plus two independent deterministic S1 receipts = **52 verified commits**; no Unknown action. Offline preflight executions are separately marked non-LLM and excluded from these live/control totals.
- 60 Detector slots: 40 sent, 39 contract-valid, 30 effectively scored, 30 abstained. Twenty full R/MAE inputs were over budget and never sent. One S1/MA output cited a fact outside the supplied inventory and was rejected without repair.
- Official peak-cache-miss usage estimate **$0.050314**; retained conservative reservations **$0.109564**, below the configured $5 ceiling. This is not an invoice. Usage: Agent 49,991 input / 8,753 output; Detector 73,266 input / 2,326 output tokens.

Pricing verified against [official DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/): $0.30/M input and $1.20/M output peak cache miss. The returned alias was `deepseek-flash`, explicit nonthinking, temperature zero, output 256; the documented alias target is DeepSeek-V4.1-Flash-1017, not an immutable weight revision. Agent/Detector input caps remain 2000/4096 under the original conservative full-wire estimator; model seeds are unsupported and not sent.

The initial dispatch guard compared a typed object to its JSON form and denied launch before any HTTP request. Canonical equality was verified, the comparison fixed and regression-tested; the design did not change. Logs preserve that failure. A later offline methods-export missing-directory error was fixed without changing results or making calls.

## Acceptance gates

| Gate | Decision | Evidence / limit |
|---|---|---|
| ENGINEERING | GO | Baseline 930, final 979 and no-private-runtime clean checkout 979 pass; lint/format/lock pass |
| DETECTOR_PROTOCOL | CONDITIONAL GO | 39/40 valid; one unsupported citation; no reliability guarantee |
| DETECTOR_SCORABILITY | GO | 30 effective scores, all five view types represented across controls |
| FIVE_VIEW_EXECUTION | CONDITIONAL GO | Controls exercise all five; all ten real R/MAE pairs are unsent overflows |
| MECHANICAL_POSITIVE | GO | Exact enumeration, independent arithmetic, two genuine S1 receipts |
| REAL_CPLUS_FEASIBILITY | NO-GO | Agreement/partial harmful ballots in block 1; zero realized harm in both |
| MATCHED_ENG_BLOCKS | CONDITIONAL GO | All ten fixed cases accounted; four capture-incomplete; same-task replications |
| EVIDENCE_PARITY | GO | 12/12 independent R/MAE parses equal; pre-response eligibility equal |
| EVIDENCE_SUFFICIENCY | NO-GO | MAE 0/10 real-case scores; safe subset still exceeds fixed budget |
| RESEARCH_INTEGRITY | GO | No tuning, substitution, oracle injection, formal scoring or invented adjudication |
| REVIEWER_READINESS | CONDITIONAL GO | Ten blinded packet sets prepared; no reviewer assignments/signatures |
| PILOT_OPERATIONS | CONDITIONAL GO | Existing scheduler/profile/guards prepared; pending manifest denied |
| FORMAL_PILOT | NO-GO | Dependent scientific gates, 16 decisions, start and owner authorization pending |
| SUBMISSION_READINESS | NO-GO | Formal study and compliant scientific submission PDF not produced |

Dependent scientific NO-GOs are not additional engineering failures. This phase stops after the review package. Formal Pilot 0/20; all formal research 0/120.

## Review entry points

`review/phase5a2/live/predeclared-plan.json` binds the dispatch source and fixed order. `aig-integrity.json` independently checks consumer rows and receipt bindings with private bytes unchanged. `detector-analysis.json` and `analysis/engineering-matrix.csv` replay all L4 results. `live/usage-final.json` contains every actual generation. `research/phase5a2/` contains a pending launch candidate and the unchanged 120-slot schedule. See the seven companion reports for interpretation, decisions and verification.

`end-to-end-example.json` walks block1/N3 through six genuine validated proposals, six independently authorized AIG receipts, lawful Arena finalization, five view attempts, three real effective scores, authoritative unsent R/MAE abstention, an unsigned reviewer packet and the descriptive table. `analysis-annotated/engineering-matrix.csv` adds explicit origin, capture and mechanical outcome classes, keeping scripted S1 separate from genuine cases.
