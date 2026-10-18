# Prospective Decision Proposal — NOT APPROVED / NOT APPLIED

Prepared **2026-10-19 NZDT**, Phase 4A pre-sprint engineering. This proposal is
separately reviewable. It does not amend EXPERIMENT_PLAN, execute a pilot,
authorize model calls, select thresholds or start Phase 4B.

## Decisions requested before formal experiments

| Decision | Current implementation | Proposed review choice and consequence |
|---|---|---|
| Primary communication observer | Phase 3 engineering default Router audit B | Explicitly choose A (delivered/intercepted) if the intended primary question excludes Router administrator rights; otherwise explicitly retain B and qualify conclusions. Both input builders exist, no formal policy selected here |
| N2 mechanism | All final proposals blocked, lawful missing-ballot fallback | Retain/disclose for compatibility now. Review a future canonical-lawful-ballot admission control if reducing deterministic missingness is necessary; no ballot repair, forced choice or fake receipt. Requires new implementation/acceptance and prospective approval |
| Agent protocol | Legacy v1 remains default; v2 candidate is opt-in | Review/adopt/freeze the candidate only after separately authorized reliability engineering. Keep all v1 records and the failed original smoke |
| Token fit | Complete packet or explicit failure; heuristic estimates disclosed | Prefer trusted complete-template token counting. If full packets do not fit, approve deterministic shared fact-bundle selection or declare cases unusable under existing abstention rules |

No preferred observer should be chosen based on detector results. Selecting A
for a delivered-speech question changes available information versus Phase 3 B;
it must be recorded prospectively, applied uniformly across conditions and kept
fixed through the eventual study. If B is retained, explicitly state the Router
audit threat model and do not claim delivered-only inference.

## Candidate selection policy for review, not active code

1. Keep mandatory complete public task, all six proposal-slot statuses, final
   public allocation/cost status, execution/receipt missingness, source/trust and
   order uncertainty. They cannot be silently dropped to rescue a result.
2. Define complete correlated bundles for message/delivery observations and
   Action/receipt/proposal links; do not split a claim from contradictory evidence.
3. Order optional bundles using fixed public actor/round/source keys independent
   of assignment, private IDs, scores and outcomes. Do not select favorable text.
4. Select **one shared fact-ID set for R and MAE**, fit against the larger complete
   rendered/tokenized packet, and preserve exact parity. Any removal is recorded
   uniformly as omitted-observation coverage, never as proof of absence.
5. If mandatory information or a safe complete bundle cannot fit, return the
   explicit input failure/abstention required by the frozen protocol. No unequal
   truncation, hidden cap increase, model retry or selected episode replacement.

This policy is deliberately not executable in Phase 4A. Mandatory-bundle fit,
time ordering under partial capture and representativeness need review first;
implementing an underspecified lossy policy would silently change the experiment.

## Evaluation and approval boundaries

The proposal leaves 4 pilot +10 calibration +10 held-out groups, 120 slots,
C+/C− pairing, truth/adjudication, primary N1 endpoint, abstention, thresholds and
statistical rules unchanged. Alternative N2 controls must still establish no
harmful execution without fabricating success. Additional detector arms/calls
or analyses need prospective resource/protocol approval; none ran here.

**Approval requested for prospective choices only. Status remains pending.**
No alternative condition, primary observer change or truncation policy is
applied. Actual formal pilot readiness remains NO-GO until these gates and
model/reviewer feasibility are resolved in a separately authorized stage.
