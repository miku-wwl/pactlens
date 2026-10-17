# PactLens — Phase 0.5 Review Report

Date: **2026-10-17** (NZDT) · Scope: **Phase 0.5 only** — corrective review of
competition readiness and research protocol. **No Phase 1 implementation.**
No experiments, commits, pushes, tags, registrations, submissions, or external
side effects were performed.

## 0. Decisions

- **Competition readiness: GO (with user-side blockers, §5).** All official
  submission rules are now verified verbatim from the sprint page's Guidelines
  tab; the previously UNVERIFIED administrative items are resolved.
- **Research readiness: GO** (protocol corrected and pre-registered; no
  implementation claimed). Phase 1 remains requires explicit user approval.

## 1. Files changed in this pass

| File | Change |
|---|---|
| `docs/COMPETITION_REQUIREMENTS.md` | Rewritten: Guidelines/Resources/Schedule tab content captured via real browser session; official template URL; judging rubric; prior-work + AI-use rules; removed the invented sprint-start timestamp; "closed window" investigation recorded |
| `docs/EXPERIMENT_PLAN.md` | Rewritten: four-layer evidence separation (L1–L4), anti-circularity rules, condition/seed accounting fix, splits, size gate, failure behavior, matched information-content controls, fixed analysis order |
| `docs/PROVENANCE.md` | Baseline procedure defined (manifest-based, no silent commits/tags); precise-timestamp claim removed; baseline commit `34d3857` identified |
| `README.md` | Replaced stub with intended architecture, installation, reproducibility contract, not-yet-implemented list, layout, competition constraints |
| `docs/PHASE0_5_REVIEW.md` | This report |

Untouched by design: `AGENTS.md` (upstream + invariants intact),
`docs/HACKATHON_DESIGN.md` (blueprint preserved), `docs/ARCHITECTURE.md`
(API contract still accurate), `docs/PHASE0_REPORT.md` (historical record),
`pyproject.toml`, `uv.lock` (**pinned AIG dependency unchanged** — verified),
`src/pactlens/` (still marker-only).

## 2. Findings and corrections

### Task 1 — Competition requirements (was: UNVERIFIED → now VERIFIED)

The sprint page's tabs are client-rendered; earlier static fetches missed
them. Captured 2026-10-17 with a real browser session (Overview / Resources /
Guidelines / Schedule). Verified verbatim:

- **Official template:** "Research report (PDF) using the official template…"
  URL: `https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy?usp=sharing`
  ("Always use the one linked on the Guidelines tab. The template in any
  acceptance email may be older.")
- **Abstract ≤ 150 words**; **author names and affiliations**; **required
  "Limitations and Dual-Use / Ethical Considerations" appendix**.
- **Judging:** 3 dimensions × 1–5 (Impact Potential & Innovation; Execution
  Quality; Presentation & Clarity); same rubric for all tracks.
- **Prior work:** "Building on existing work is allowed and encouraged, but you
  must clearly identify what is new work done during the sprint. Undisclosed
  prior work can lead to disqualification."
- **AI use:** report "has to be your team's own writing about your team's own
  work"; generated-sounding reports "will not be scored".
- **Deadline:** Sun 2026-10-25 23:59 AoE (all three tabs) = **2026-10-27 00:59
  NZDT**. Submission via the official form on the sprint page; resubmission
  with the same title replaces files.
- **Correction:** the invented "sprint start 2026-10-23 00:00 NZDT" anchor is
  removed — no official start *time* is published, only the date.
- **"Submission window has closed" message — NOT REPRODUCED.** Two static
  fetches + the browser session all show "Starts in 6 days" / "Starts Oct 23,
  2026" and a Sign-up button, with no closed-window notice. Recorded as a
  non-reproducible earlier capture; page state is treated as per-check-time
  authoritative, to be re-verified near the deadline.

### Task 2 — Methodology repaired (`docs/EXPERIMENT_PLAN.md`)

- Added the **four layers** (L1 condition assignment / L2 ground truth / L3
  detector-visible evidence / L4 predictions) with an explicit
  may-not-enter-detector rule for L1/L2.
- **Anti-circularity:** approval status, receipt existence, payload digests,
  or action similarity can never alone establish collusion — they only
  corroborate *that* an action executed; the collusion claim requires L3
  evidence plus a predeclared decision rule over blinded L2 adjudication.
- **Blinded adjudication** (two independent blinded passes + escalation),
  **independent outcome measurement** (allocator/judge computed from arena
  rules only, never from messages), and **indeterminate handling** (kept,
  reported as coverage, never silently re-labelled).

### Task 3 — Evaluation protocol fixed (`docs/EXPERIMENT_PLAN.md`)

- **Inconsistency resolved:** five conditions exist; "4 conditions × 10–15
  seeds" was wrong. Correct accounting: **5 conditions (C+, N1, N2, N3, C−),
  pilot 3–5 seeds/condition → main 10–20 seeds/condition only after the
  positive control works** (matching the organizers' published guidance);
  C− paired to C+ on the same seeds.
- **Splits:** dev → calibration (prompts/thresholds/operating point; each
  matched seed in exactly one split) → held-out, scored once.
- **Positive-control realization rate** and **count gates** (≥ 8 verified
  executed-collusion cases and ≥ 20 N1 cases per split) declared, with
  exploratory-only fallback.
- **Predeclared calibration/recall failure behavior:** operating-point failure
  → ROC/PR exploratory reporting, no primary claim, no post-hoc target moves;
  positive-control failure → public pilot negatives + honest null or a new
  pre-registered amendment.
- **Uncertainty:** seed-clustered bootstrap CIs, Wilson intervals, ΔFPR CI +
  risk/odds effect size, paired (McNemar-style) primary contrast.
- **Matched information-content comparisons for MA vs MAE:** identical
  monitor model/prompt/temperature/token budget; field-matched control (same
  fields, unstructured packaging) separating instrumentation gain from
  algorithmic gain; content-matched control; noise-carrier arm acknowledging
  the organizers' cited "more detail can degrade monitors (Arike et al. 2026)"
  risk.
- **Primary comparison** (MAE vs MA, paired per episode, N1 FPR at frozen
  operating point) vs **exploratory** analyses, in a fixed order; unsuccessful
  and ambiguous episodes all retained; cherry-picking ban enforced by freeze +
  full export.

### Task 4 — Provenance/reproducibility repaired

- Invented precise start timestamp removed (§2 above).
- Baseline procedure rewritten: baseline = commit `34d3857` (pre-sprint, no
  sprint code) + the Phase 0.5 correction commit, recorded as a hashed
  **manifest** (not a tag); tags/commits only on explicit user authorization.
- README rebuilt with intended architecture, `uv sync --locked` installation,
  reproducibility expectations, and an explicit not-yet-implemented list; the
  blueprint is referenced, not duplicated; AIG pin unchanged.

## 3. Evidence — checks actually executed (2026-10-17)

```text
uv run ruff check .                       -> All checks passed!            (exit 0)
uv lock --check --offline                 -> Resolved 31 packages           (exit 0)
installed AIG import + pin verification   -> "AIG 0.2.0 pinned-commit import
                                              + 22-name public API: OK; pactlens 0.0.0"
   (version==0.2.0; direct_url commit==7261fdd2f47d2b15fabe8faac527eeee37338eb1)
git status --short                         -> only: M README.md
                                              M docs/COMPETITION_REQUIREMENTS.md
                                              M docs/EXPERIMENT_PLAN.md
                                              M docs/PROVENANCE.md
Browser session (playwright-cli): tab clicks on the official sprint page;
Guidelines/Resources/Schedule innerText + link dump captured; browser closed
and browser artifacts removed from the repository afterwards.
```

No test was claimed that was not executed. No arena, adapter, detector,
evaluation code, or UI was written in this pass.

## 4. Research validity risks remaining (tracked, not eliminated)

1. Small-n statistics (mitigated by gates + exact CIs + exploratory labels).
2. MAE observability confound (mitigated by field/content-matched controls).
3. Monitor degradation from over-rich inputs (mitigated by noise-carrier arm;
   acknowledged in the protocol as a publishable outcome).
4. Blinded-adjudication independence is only as strong as the rubric — rubric
   text must be frozen with the protocol before scoring.
5. Model nondeterminism must be captured per run (cached calls, model IDs,
   temperature) — planned in Phase 1, not yet implemented.

## 5. Remaining competition blockers (user-side)

1. **Registration confirmation** for the user's own account (page shows
   public sign-up only; was not checked on the user's behalf). Keep
   timestamped proof.
2. **Submission form availability** — expected to open for the sprint window;
   re-check on 2026-10-23. Do not assume open or closed without confirmation.
3. **Report logistics to prepare in Phase 1–3**: official Google Docs
   template, ≤150-word abstract, authors + affiliations, Limitations &
   Dual-Use appendix, disclosure of prior work and AI assistance.

## 6. Recommended Phase 1 scope (not started)

Freeze `docs/EXPERIMENT_PLAN.md` as the pre-registration; implement the
seeded deterministic arena (allocator, payoff, capacity constraints,
outcome evaluator), the four-layer evidence schema with the leakage-barrier
test, and the 3 minimal synthetic cases proving similar actions do not
themselves yield a collusion label. Preflight external starter repos
(LLM-Trust-Breaking, TraceGuard, Colosseum, ColludeBench) **read-only** — no
network side effects beyond cloning to a local cache if the user authorizes
it. Gate: offline, leakage-free dataset before any monitor work.

**Phase 0.5 ends here. Phase 1 requires explicit user approval.**
