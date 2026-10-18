# Phase 4B — Measured Evidence and Request Budgets

**2026-10-19 NZDT; pre-sprint engineering. No detector inference.** All detector
token numbers below are **heuristic estimates**, not exact tokenizer measurements
or guaranteed bounds. Actual agent-provider token usage is reported separately
in the [execution report](PHASE4B_EXECUTION_REPORT.md).

## 1. Measurement contract

The audit measures complete system/task/evidence/output-schema requests, not just
evidence text. Every view reserves 256 output tokens and limits input to 4,096.
Three-turn UTF-8 size and named heuristic are recorded; all detector exact-token
fields are null. `conversation()` fails closed if the full envelope cannot fit.
Source facts first pass existing typed projectors and the allowlisted inventory.
See the [selection contract](PHASE4B_EVIDENCE_SELECTION_CONTRACT.md).

The audit covers **34 source/policy sets**: 14 existing scripted fixtures ×2
policies, the historical six-receipt fake-model AIG trace ×2, and this phase's
two actual local-model traces ×2. **33/34 sets fit** the estimate; **1/34 retains
an explicit mandatory-core overflow**. There are 165 safe view exports. These
are related engineering cases, not independent research observations or a
population budget-success estimate. No fit-based research exclusion is applied.

## 2. Existing scripted fixtures

All **28/28** fixture/policy sets produce all five bounded packets and pass
independently reconstructed R/MAE parity. All mandatory facts are retained.

| View | Selected facts range | Omitted range | Rendered bytes range | Estimated complete-request tokens |
|---|---:|---:|---:|---:|
| M | 2–4 | 0 | 1,794–2,452 | 1,574–1,903 |
| A | 13–17 | 0–5 | 3,757–4,508 | 2,556–2,931 |
| MA | 16–18 | 0–5 | 4,460–4,830 | 2,907–3,092 |
| R | 29–31 | 0–5 | 6,356–6,742 | 3,855–4,048 |
| MAE | 29–31 | 0–5 | 6,437–6,823 | 3,896–4,089 |

These scripts do not have real model-generated AIG histories: explicit missing
Action/receipt slots are preserved. Fit on these compact tasks is not proof of
fit for all future generated tasks or long messages. Exact retained/omitted IDs,
mandatory IDs and category counts for every case are in
`review/validation/budget-selection-audit.json`.

## 3. Historical six-receipt AIG synthetic source

This is the **unchanged Phase 4A fake-model engineering trace**, replayed read-only
with zero new generation, Gateway calls or effects. Source facts are 38 under A
and 44 under B. It is not a new actual-model observation. Compact encoding plus
common selection produces:

| Policy | View | Retained | Mandatory retained | Omitted | Bytes | Estimated tokens | Result |
|---|---|---:|---:|---:|---:|---:|---|
| A | M | 5 | 4 | 3 | 2,519 | 1,937 | fits estimate |
| A | A | 11 | 11 | 7 | 3,494 | 2,424 | fits estimate |
| A | MA | 15 | 14 | 10 | 4,475 | 2,915 | fits estimate |
| A | R | 20 | 17 | 18 | 6,674 | 4,014 | fits estimate |
| A | MAE | 20 | 17 | 18 | 6,755 | 4,055 | fits estimate |
| B | M | 6 | 6 | 8 | 3,103 | 2,229 | fits estimate |
| B | A | 12 | 11 | 6 | 3,654 | 2,504 | fits estimate |
| B | MA | 17 | 16 | 14 | 5,227 | 3,291 | fits estimate |
| B | R | 20 | 19 | 24 | 6,670 | 4,012 | fits estimate |
| B | MAE | 20 | 19 | 24 | 6,751 | 4,053 | fits estimate |

R/MAE parity **PASS within each policy**, including source/trust, nulls, receipt
correlation and ordering uncertainty. A/B facts are not equal.

| Omitted category | A M | A A | A MA | A R/MAE | B M | B A | B MA | B R/MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CONTEXT | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| COMMUNICATION | 3 | — | 3 | 3 | 8 | — | 8 | 8 |
| BEHAVIOR | — | 7 | 7 | 7 | — | 6 | 6 | 6 |
| INTEGRITY | — | — | — | 8 | — | — | — | 10 |

M/A/MA receive no omitted integrity counts; dashes are ineligible categories,
not zero hidden facts. All six proposal slots, public task, actual outcome and
source coverage remain. A retains 3/6 speech events and 2/6 successful integrity
pairs; B retains 2/6 speech events with their 2 audit events and 1/6 integrity
pair. Action and receipt are never separated.

**Methodological rating:** these are interpretable bounded subsets but
**insufficient for a complete episode-wide agreement/lifecycle audit**. Token fit
alone cannot qualify them as sufficient detector evidence. Missing relevant
speech or provenance could require future abstention; researcher review of this
lossy policy remains necessary. No detector adequacy prediction is made here.

## 4. Actual local engineering traces

| Source / policy | Retained/source facts | R bytes / estimate | MAE bytes / estimate | Outcome |
|---|---:|---|---|---|
| v1 / A | 25/30 | 6,706 /4,030 | 6,787 /4,071 | fits estimate; parity PASS |
| v1 / B | mandatory core cannot fit /35 | 7,618 /4,486 | 7,699 /4,527 | **INPUT_BUDGET_EXCEEDED** |
| v2 / A | 25/27 | 6,513 /3,934 | 6,594 /3,974 | fits estimate; parity PASS |
| v2 / B | 25/27 | 6,502 /3,928 | 6,583 /3,969 | fits estimate; parity PASS |

The v1/B attempted-core sizes include its mandatory blocked attempts and missing
execution evidence. No successful model-ready packet is exported for that set.
Its failure includes per-view budget diagnostics: M=2,723, A=2,404, MA=3,698,
R=4,486, MAE=4,527 estimated tokens. No view gets an independent shorter input
that would violate the common selected-set contract.

The v2 source is not finalized; pending/not-reached final slots remain such.
Its fitting detector packet does not mean the agent episode completed or that
evidence is adequate to establish executed harm. Exact per-view selected,
mandatory, omitted-category and usage fields are in the machine audit.

## 5. Limits and prospective decisions

The Phase 4A full raw/grouped inputs remain available as historical audit
formats. Current reductions are lossless table encoding **plus explicit lossy
bundle selection**, not proof that complete original evidence fits. No loss is
hidden behind a COMPLETE label. Larger contexts fail explicitly rather than
dropping negative/Unknown/failed facts.

The narrow flat-versus-grouped presentation still has different byte/token
costs. Shared semantic facts do not establish salience neutrality, true tokenizer
fit or model quality. Near-limit estimates are particularly fragile. Qualify a
complete-template tokenizer/provider, review the mandatory core and permissible
loss, and freeze the observer/selection/overflow policy prospectively before
formal use. No heuristic relaxation, context enlargement or post-prediction retry
is authorized here. Budget failures must stay in coverage/abstention accounting;
they may correlate with intervention, observer rights or message volume.
