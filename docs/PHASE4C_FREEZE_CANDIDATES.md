# Phase 4C — Prospective Freeze Candidates and Open Decisions

**2026-10-20 NZDT; pre-sprint.** Every entry is a candidate. Engineering tests,
budget fits and the bounded local episode approve nothing. The frozen
[Phase 0.6 plan](EXPERIMENT_PLAN.md) and the [Phase 4B package](PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md)
remain authoritative and unchanged.

## 1. Decision record

| Decision | Candidate | Status |
|---|---|---|
| Agent context | `pactlens-agent-v3-candidate` (`pactlens-compact-context-v1-candidate`) | PROPOSED; **not model-qualified** (live engineering test 0/6 valid) |
| Decision protocol | `pactlens-decision-v2-candidate`, unchanged | PENDING (unchanged since 4B) |
| Example policy | One first-feasible public submit example; v2 decline example derived | PROPOSED; suspected contributor to duplicate keys and anchoring |
| Evidence tables | `pactlens-lossless-public-tables-v2-candidate` | PROPOSED |
| Complete-evidence policy | `pactlens-complete-evidence-v1-candidate` | PROPOSED |
| Common selection on v2 tables | `pactlens-common-bundles-v2-candidate` (4B rules) | PROPOSED |
| Sufficiency rubric | `pactlens-evidence-sufficiency-v1-candidate` | PROPOSED |
| Primary observer / Router sensitivity | A delivered-intercept / B router-audit | PROPOSED, unchanged |
| N2 | Retain N2-A all-round-2 execution block | PROPOSED, unchanged; no alternative implemented |
| Agent token feasibility | Heuristic not relaxed; no verified exact counter | **UNRESOLVED** |
| Message-volume coverage | Explicit overflow beyond the measured boundary | **UNRESOLVED** |
| Detector budget vs complete evidence | `EVIDENCE_BUDGET_INFEASIBLE` for six-action episodes | **UNRESOLVED** |
| Formal pilot | Not authorized | **NO-GO** |

Approval requires an attributed researcher and dated record; `phase4c_candidates`
and `readiness` keep every gate mechanically unapproved.

## 2. Candidate hashes

| Candidate | SHA-256 |
|---|---|
| v3 prompt profile (`system`, example policy, protocol hash, context version) | `e60eec5786046b6b944356afa8e562c186092617126931f743a60e1cdfaa43e1` |
| v3 system text | `1cf9b8df840bf702d0374b514954e048cb1e0c70afc489a15c9b918039469566` |
| Decision protocol v2 (unchanged) | `3f982b1c7b217e785c3d9416c1d47859ea4497367838cc3eb50903c72f7dc3b0` |
| Previous v2 prompt (unchanged) | `172bbe6f06dd39fb91cc8070b01baadb0dd84123037ae807519e2a4e709ec8da` |
| Complete-evidence policy config | `13c0508ba5ce974cfdb0d76c2b83ab95718d7062954c1de956fe5999512ee883` |
| Common selection on v2 tables config | `7f37338da8c7909f486dda3e35d74e3e7102298dca95e2f37ed9c80d5bfd456a` |
| Detector envelope (unchanged from 4B) | `4514c3d752300b690dbb1b1f6f9eff37d27c70af57b7099fd338f75799f5c53d` |
| Detector response schema (unchanged from 4B) | `28fc9e785981fb5010e5acfbd667415b9efa60c6a94371df88bad552b7f172bc` |
| Frozen evaluation rules (unchanged) | `ffe913cd49b82c676f42613619ea6fda0bdc4e65c9e009847425aefd7ddf72ee` |
| Full Phase 4C candidate manifest | `bd2fb4a78cd08836ec8ef872a3f75b7396c0b630d2e6e58f9bc6e1ed42573210` |

The machine-readable record is `review/validation/freeze-candidates-4c.json`.
Hashes identify candidates for review; they are not approvals. The review ZIP's
file manifest binds the concrete implementation snapshot.

## 3. What the agent sees differently in v3 (disclosed, prospective)

v3 carries exactly the information v2 carries (tests rebuild the v2 turns from v3
text byte-for-byte for all six steps in all five conditions), but presentation
changes can still change behavior:

1. **Chat structure.** Two turns instead of `2+3k`. The actor's own earlier output
   is shown as data inside the observation, not as an earlier assistant turn.
2. **Earlier observations** are shown as verified prefix counts and revision, not
   resent; the public task appears once and the task hash once (in the example).
3. **Own earlier output** is its exact JSON value; whitespace and key order are not
   preserved. Unparseable output is shown verbatim.
4. **Feedback statuses** are fields of the history entry instead of extra turns.
5. **Example policy.** v2's two examples become one (the identical submit example);
   the decline form is stated in text. Decline salience may change.
6. **Instructions** keep every v2 rule (regression-tested clause list), add table
   legends and the clarification "eligible_agents (null=any)", and say to copy the
   identity from the example (identical values to the observation in v2).

None of these is a hidden fallback: v2 remains selectable, and no v2 overflow is
silently rerouted to v3.

## 4. Open decisions and options (not taken here)

**A. Agent context under the 2,000-token estimate.** No-speech six-step paths fit
in every condition, including the largest generated 5-incident task; message-heavy
histories overflow explicitly (see the [context report](PHASE4C_MODEL_CONTEXT_REPORT.md)).
Options: (i) qualify an exact tokenizer for the chosen local model against
provider-reported counts, then budget on it; (ii) a prospective cap amendment with a
revised cost forecast; (iii) a protocol amendment bounding message length or count
(changes the decision protocol and possibly collusion opportunity); (iv) accept
overflow as logged coverage loss, reported by condition. Each is a methodological
decision; none is applied.

**B. Detector evidence under the 4,096-token estimate.** Complete evidence for every
six-action engineering source is `EVIDENCE_BUDGET_INFEASIBLE`; even the lifecycle
core alone slightly exceeds the estimate (see the
[sufficiency report](PHASE4C_EVIDENCE_SUFFICIENCY_REPORT.md)). Options: (i) exact
tokenizer qualification; (ii) a prospective detector-cap amendment; (iii) a
two-packet design (lifecycle and communication) with a revised detector protocol;
(iv) further lossless encodings (derived actor and cross-order columns, merged
legends; about 240 estimated tokens, lower readability, still infeasible for
complete evidence); (v) accept lossy selection with explicit insufficiency labels
and abstention, reporting coverage by condition; (vi) a lossy evidence amendment
(e.g. digest removal), which would change the research question's evidence and
needs explicit justification.

**C. Observer and N2.** Unchanged from Phase 4B. Under B, C−'s blocked attempts are
mandatory audit facts and enlarge its packets; under A they are absent. Selection
outcomes therefore differ by condition through observable behavior (see the
condition analysis), which must be reported, not corrected.

**D. v3 presentation after the live test.** The single bounded episode sent all six
requests within budget but produced 0/6 valid outputs: five repeated `round_number`
and/or `task_hash` (closed-parser duplicate keys) and one submitted null
assignments; parseable assignment lists copied the example's first-feasible
allocation. The most plausible contributors are "copy identity from the example"
and the single alphabetical-order example. Candidate remedies for a new version
(not implemented, not run): identity copied from `now` again, the example in the
instructed key order or an explicit "each key exactly once", the decline example
restored. Any revision is a new candidate requiring separate authorization for a
new bounded test; this run is never re-scored or replaced.
