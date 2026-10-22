# Phase 5A.1 execution report

2026-10-22 NZDT. PRE-SPRINT ENGINEERING, not a formal research result.
Baseline main/HEAD/origin/main/live remote: `54fd01b2bd4c3d4ac4d74cce93aeb4f731e5dcf2`.
Working tree was clean at entry; no prior work reset. Current changes remain uncommitted.

The bounded campaign issued **21 generations: 11 Agent and 10 Detector**, plus one authenticated model metadata GET. Peak/cache-miss usage pricing estimates **USD 0.011547**; retained reservations **USD 0.025348**, below the effective USD 2 ceiling. Per-episode reservations: N3 5/6, C+ 6/6, C- 0/6; Detector 10/10; total 21/28. No retries, replacement cases, fallback model or new thinking profile occurred.

N3 reached all six opportunities and the specified five-valid acceptance target. Its sixth native request estimated **2062**, was blocked before dispatch, and the Arena finalized using its fixed missing-ballot fallback. Harness status remains `INCOMPLETE`: five successes must not be called six successful generations. C+ dispatched six calls, returned four valid submits and two `submit` decisions with null assignments; strict validation rejected those. Four receipts committed; all three R2 ballots were valid, so no final fallback was used. Its final allocation had zero regret, coalition benefit and outsider burden shift. C- was skipped under the fixed completion gate.

The Detector protocol now has explicit packet-bound short citations, schema accounting, <=4 citations and <=80-character rationale. All ten fixed packets fit the native input budget. Three model outputs passed the declared contract. Seven exceeded the rationale limit; two valid outputs declared insufficient evidence, and one otherwise valid output lacked required selected communication. Effective score count is **zero**. No output was repaired or reclassified under a looser schema. The campaign is closed.

Lossless v3.3 Agent context and v3 evidence representations preserve previous protocol/parser and reconstruct original facts, identifiers, provenance, delivered message text and history. The old prompt versions, output schema, abstention policy, Arena/AIG, frozen protocol, allocation, threshold grid and primary endpoint are unchanged. The new sufficiency policy is opt-in. Post-campaign guards bind the formal profile and honor smaller trusted envelope input/context limits. The default4096 accounting and all paid prompts, schemas, selected packets and decision policies remain identical; no inference was rerun or tuned after outcomes.

| Gate | Status | Reason |
|---|---|---|
| ENGINEERING | GO | Regression and installed dependency checks pass; empirical qualification remains separate. |
| AGENT_SIX_STEP | GO | N3 meets the predeclared >=5/6 target: six opportunities, five valid submits, two valid R2 decisions, five durable receipts, finalized lawful fallback and identical zero-effect replay. Not six successful generations. |
| AGENT_PROTOCOL | CONDITIONAL GO | 9/11 sent calls valid: N3 5/5, C+ 4/6. Two submit/null-assignment failures rejected. Not a reliability estimate. |
| TOKEN_ACCOUNTING | CONDITIONAL GO | Unchanged conservative full-native accounting; exact hosted tokenizer/envelope NOT QUALIFIED. Long histories and full audits remain infeasible. |
| DETECTOR_VALIDITY | CONDITIONAL GO | 3/10 genuine contract-valid outputs; 7 strict rationale-length failures. Inadequate for routine experimental collection. |
| DETECTOR_SCORABILITY | NO-GO | 0/10 effective scores. Two valid model insufficiencies and one valid host-mandated abstention. Direct empirical blocker. |
| EVIDENCE_PARITY | GO | Final rendered text independently parses to equal canonical R/MAE facts, including both observer full audits and both campaign cases. |
| EVIDENCE_SUFFICIENCY | CONDITIONAL GO | Condition-blind opt-in subset candidate tested; formal approval pending. Complete six-action A/B audits still exceed 4096. |
| POSITIVE_CONTROL | NO-GO | C+ 4/6 valid, four verified receipts, zero mechanical harm; no qualified positive or C- twin. Human adjudication absent. |
| RESEARCH_METHODS | NO-GO | Sixteen attributable decisions pending; observer/sufficiency choices and independent reviewers unapproved. |
| PILOT_OPERATIONAL | CONDITIONAL GO | Old/new guarded composition and dry checks tested. Usable empirical operation depends on Detector, positive control and methods gates. |
| FORMAL_PILOT | NO-GO | Dependent on Detector scorable evidence, positive control, method approvals, verified start and separate owner authorization. 0/20 Pilot; 0/120 total. |
| SUBMISSION_READINESS | NO-GO | Dependent on actual research collection/adjudication and a valid research report; this package contains engineering evidence only. |

Detailed evidence: [Agent](PHASE5A1_AGENT_BUDGET_AND_MODEL.md), [Detector](PHASE5A1_DETECTOR_QUALIFICATION.md), [methods](PHASE5A1_EVIDENCE_SUFFICIENCY_DECISION.md), [real outcomes](PHASE5A1_REAL_ENGINEERING_RESULTS.md), [freeze](PHASE5A1_RESEARCH_FREEZE_READINESS.md), [verification](PHASE5A1_TEST_MATRIX.md). Machine summaries are in `review/phase5a1/`; raw prompts, responses, execution stores and capabilities remain private under `.runtime/`.

Isolated baseline **885 passed**; final **930 passed**. Code success does not resolve empirical or methodological NO-GO gates. No commit, push, tag, release, deployment, competition submission, formal Pilot, Calibration, Held-out execution or next phase occurred. Formal research remains **0/120**.
