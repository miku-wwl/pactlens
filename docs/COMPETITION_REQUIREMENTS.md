# PactLens — Competition Requirements Verification

Official event: **Apart Research AI Collusion Research Sprint**, 2026-10-23 to
2026-10-25. Verification date: **2026-10-17**. The sprint page has four tabs
(Overview / Resources / Guidelines / Schedule) that are rendered client-side;
the content below was captured with a real browser session on 2026-10-17, not
from cached prose. All times converted to `Pacific/Auckland` NZDT (UTC+13).

Source: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25

Status legend: **VERIFIED** (seen in authoritative source, quoted), **UNVERIFIED**
(not present / cannot confirm), **BLOCKED** (needs user action). No form was
submitted and no registration was performed on the user's behalf.

## 1. VERIFIED — official submission rules (Guidelines tab, retrieved 2026-10-17)

| Requirement | Verbatim from the Guidelines tab |
|---|---|
| Report format | "Research report (PDF) using the official template." |
| **Official template URL** | **https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy?usp=sharing** ("Submission Template" / "Link" — both point here) |
| Template currency rule | "Always use the one linked on the Guidelines tab. The template in any acceptance email may be older." |
| Abstract | "Project title and abstract, **150 words or fewer**." |
| Authors | "Author names and affiliations." |
| Required appendix | "A 'Limitations and Dual-Use / Ethical Considerations' appendix (required, see below)." |
| Recommended structure | 4–8 pages: Introduction / Related Work / Methodology (enough to replicate: models, prompts, environments, seeds, metrics) / Results ("report variance, seeds and baselines, and always include the positive control") / Discussion / Limitations & Dual-Use appendix / References |
| Judging rubric | 3 dimensions, scored 1–5: **Impact Potential & Innovation; Execution Quality; Presentation & Clarity**. "All projects are scored on the same rubric." |
| Prior-work disclosure | "Building on existing work is allowed and encouraged, but you must clearly identify what is new work done during the sprint. **Undisclosed prior work can lead to disqualification.**" |
| AI-use rules | "Use AI tools the way you would use a colleague… The report itself has to be your team's own writing about your team's own work… a report that reads as generated rather than written … will not be scored." |
| Submission mechanics | "through the official submission form on the sprint page"; resubmission replaces files if the "exact same title and details" are used; confirmation email follows |
| Optional | Public GitHub repo; 3–5 minute video demo |
| Deadline | "Submissions close Sunday, October 25 at 11:59 PM Anywhere on Earth (AoE)" (Overview, Guidelines FAQ, and Schedule tab, "Sun 11:59pm AoE — Submission deadline") |

**Deadline conversion:** 2026-10-25 23:59 AoE (UTC−12) = 2026-10-26 11:59 UTC =
**2026-10-27 00:59 NZDT** (UTC+13, NZDT active on that date). There is no
official published *start* time for the sprint; the only official date is
Friday 2026-10-23. No midnight-NZDT anchor is claimed (corrected — see
`docs/PHASE0_5_REVIEW.md` §2).

## 2. VERIFIED — official planning guidance for Track 2 (Resources tab)

Retrieved 2026-10-17; repo/paper links stated by organizers as "checked on 31
August 2026".

- Planning assumptions: "Start with **3 to 5 seeds per condition** and expand to
  **10 to 20 only after the positive control works**." All routes run on a
  16 GB laptop, no GPU.
- **Q2.2 starter code:** LLM-Trust-Breaking (Shi et al.; official harness
  recording private plans, public announcements, final actions, outcomes;
  OpenAI/OpenRouter; heterogeneous groups) + TraceGuard (single-agent
  monitoring system; reusable action-trace consistency rubric).
- **Q2.2 official weekend design:** "Generate a small balanced set from one
  game, then give the same monitor **four views: messages only; actions only;
  raw messages plus actions; and a structured report comparing claims with
  outcomes.** Freeze the monitor model, prompt and threshold before
  evaluation, and report both accuracy and false-positive rate."
  (PactLens's M/A/MA/MAE taxonomy matches this official 4-view design.)
- **Q2.2 budget:** ~20–40 short trajectories, ~160–250 monitor calls for a
  pilot; $5–$30 (agents), $30–$75 if stronger agent models generate logs.
- **Q2.3 starter code:** Colosseum (Nakamura et al.) + ColludeBench
  (preflight required).
- **Q2.3 official weekend design:** "Assemble three deliberately different case
  types: coordinated harmful action; similar behaviour caused by common
  incentives without agreement; and collusive-sounding talk that never changes
  behaviour. Compute the same conversation, coalition-advantage and dependence
  evidence for every case. Choose the decision rule on half the examples,
  freeze it, and test on the rest." (Matches PactLens C+/N1/N2 case types
  and the calibrate-then-freeze-then-held-out protocol.)
- Key caution from the cited literature (Resources tab): "Less can be more:
  sometimes giving a monitor too much detail degrades its performance (Arike
  et al. 2026)." — recorded as a first-class risk for MAE in
  `docs/EXPERIMENT_PLAN.md`.

## 3. VERIFIED — event facts

Dates Friday 2026-10-23 → Sunday 2026-10-25, online + optional hubs (Collider
NYC; AI Safety Hong Kong); teams of 1–5 recommended, larger allowed; prizes
$2,000 total ($1,000/$500/$300/$100/$100); talks on Zoom with RSVP; Discord
`discord.gg/XswWBvugYs`; support `sprints@apartresearch.com`; results 1–2
weeks after judging; Apart Fellowship fast-track for top teams.

## 4. UNVERIFIED / BLOCKED — remaining user-side items

| Item | Status | Action required |
|---|---|---|
| **User's own registration confirmation** | UNVERIFIED | The page shows a "Sign up" button and a public counter ("1,002 signed up" on 2026-10-17); the user's account state was not checked. Confirm personally and keep timestamped proof. Hub registration (if wanted) via the page / AI Safety Hong Kong hub page. |
| Submission form availability | UNVERIFIED (expected) | The official form is referenced as living on the sprint page; it is expected to open for the sprint window. Re-check during the sprint; do not assume it is open or closed before confirmation. |
| Any "submission window has closed" message | **NOT REPRODUCED** | The design blueprint (§1) recorded such a message "simultaneously with the countdown". On 2026-10-17, two independent static fetches plus a JS-rendered browser session all showed "Starts in 6 days" / "Starts Oct 23, 2026", a Sign-up button, and no closed-window notice. Conclusion: the earlier capture was not reproducible; treat the sprint page's current state as authoritative at each check time and re-verify near the deadline. |
| Judges' identity, reviewer count | UNVERIFIED | Not published; not required for preparation. |

## 5. Rules this section imposes on the project

1. Report must be ≤150-word abstract, on the official Google Docs template
   (linked above), with the Limitations and Dual-Use / Ethical appendix.
2. Methodology must disclose models, prompts, environments, seeds, metrics.
3. Results must report variance, seeds, baselines, and positive control.
4. `docs/PROVENANCE.md` must accurately separate pre-sprint from sprint work
   (undisclosed prior work risks disqualification).
5. AI use in writing must be disclosure-ready: our own writing over our own
   measured work; no generated-sounding prose.
6. Repo must ship a reproduction path (queued for README — see
   `docs/PHASE0_5_REVIEW.md` §5).
