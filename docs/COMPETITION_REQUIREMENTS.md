# PactLens — Competition Requirements Verification

Official event: **Apart Research AI Collusion Research Sprint**, 2026-10-23 to
2026-10-25. Verification date: **2026-10-17, Phase 0.6**. This pass read the
official page's extracted Overview, Resources, Guidelines, Schedule and
submission content, plus a direct public text export of the linked report
template. The Phase 0.5 browser observations are historical evidence; no new
rendered-browser check or account/form submission was performed here.
All deadline conversions use `Pacific/Auckland` NZDT (UTC+13).

Source: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25

Status legend: **VERIFIED** (read in authoritative source), **UNRESOLVED**
(conflicting observations), **UNVERIFIED** (cannot confirm), **BLOCKED**
(requires further action). No form was
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
| Public registration UI | VERIFIED as page content only | Sign-up controls exist. This is not proof of the user's registration or submission access. |
| **User's own registration confirmation** | UNVERIFIED | Account state was not inspected. Keep actual confirmation separately from submission status. |
| Submission availability | **UNRESOLVED** | This pass's official-page extraction contains a submission form AND “The submission window has closed.” Future event dates and registration controls cannot establish an open submission window. No actual submission was attempted. |
| Conflicting rendered/captured states | **UNRESOLVED** | Phase 0.5 recorded future-start/registration UI without a closed notice; the blueprint and this pass's extraction contain a closed notice. Extraction may include hidden UI branches. Neither proves the server will accept submissions. Seek organizer clarification or a fresh authoritative availability check near the event; do not infer that submissions will automatically open. |
| Judges' identity, reviewer count | UNVERIFIED | Not published; not required for preparation. |

## 5. Template contradiction and precedence (Phase 0.6 correction)

The Guidelines require **150 words or fewer**. The linked Google Docs template
instead says “150–250 words”. Both were read in this pass; the conflict is
real and remains unresolved by the organizers. Use **≤150 English words**
for the abstract, including exactly 150 as acceptable, unless organizers
explicitly resolve it otherwise. The template's optional-appendix wording also
does not remove the event's required Limitations and Dual-Use / Ethical appendix.

Template evidence: [official linked document](https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/edit),
[public text export](https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/export?format=txt).
The export was 5,695 bytes, SHA-256
`2010058b97eb5f9fca8ccd1cf2d564fdec0d13fde9c72436fa7dc81e875677e2`.
The web reader failed to open the editor URL; the direct HTTP text export
succeeded. No copy was created in the user's Google Drive.

Schedule content was also checked: online talks October 22/23, optional hub
activities October 24/25, and Sunday 23:59 AoE submission cutoff. Talk times
do not establish the sprint's precise start time. The verified deadline remains
**October 27, 2026, 00:59 NZDT**; submission availability remains unresolved.

Resources' sample/budget numbers are organizer guidance, not a PactLens power
analysis or measured resource estimate. PactLens chooses the concrete
exploratory 4/10/10-block allocation in [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md)
and adds mandatory raw-evidence control R to separate information from structure.

## 6. Rules this section imposes on the project

1. Report must be ≤150-word abstract, on the official Google Docs template
   (linked above), with the Limitations and Dual-Use / Ethical appendix.
2. Methodology must disclose models, prompts, environments, seeds, metrics.
3. Results must report variance, seeds, baselines, and positive control.
4. `docs/PROVENANCE.md` must accurately separate pre-sprint from sprint work
   (undisclosed prior work risks disqualification).
5. AI use in writing must be disclosure-ready: our own writing over our own
   measured work; no generated-sounding prose.
6. Repo must ship a reproduction path; README currently documents installation
   and the future research contract, not a working experiment CLI.
7. Registration and submission are separate statuses. Do not register, send
   organizer messages or submit on the user's behalf under Phase 0.6.
