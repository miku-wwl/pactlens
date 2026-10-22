# Launch readiness and final gates

Current machine report: [gates.json](../review/phase4e5a/gates.json).

| Gate | Decision | Reason |
|---|---|---|
| ENGINEERING | GO | 885 regression passes, installed AIG, full dry schedule, tested guards/export |
| DEEPSEEK_PROVIDER | CONDITIONAL GO | Authentication and native-schema generation work; hosted alias only, no complete research profile |
| AGENT_MODEL | NO-GO | 3/6 opportunities valid; round-2 preflight overflow |
| DETECTOR_MODEL | NO-GO | 4 contract-valid results/8 calls; truncation/invalids; no genuine R/MAE |
| ABSTENTION_INTEGRITY | GO | Durable decision, recomputed replay, effective-score analysis bridge tested |
| EVIDENCE_SUFFICIENCY | NO-GO | Complete and selected R/MAE fail full native request cap |
| POSITIVE_CONTROL | NO-GO | Real C+ not run; independent reviewers absent |
| RESEARCH_METHODS | NO-GO | All methodological decisions and formal freeze pending |
| PILOT_OPERATIONS | CONDITIONAL GO | 120-slot dry provision and guarded composition pass; complete real group unqualified |
| FORMAL_PILOT | NO-GO | Missing qualifications, approvals, verified start and owner authorization |
| SUBMISSION_READINESS | NO-GO | No formal results, independent review or final PDF/team/portal confirmation |

`study_launch` supports the frozen Pilot groups, ordered five conditions, fresh
contexts/scopes/stores and exact group seed/role/task matching. `study_provider`
uses the existing real AIG harness and Detector pipeline. Calibration and Held-out
dispatch remain locked; only their schedule metadata was inspected. No formal
Pilot command with --execute was invoked. Positive-control/adjudication gates
must be checked before any later calibration authorization; no main-study launch
command is exposed in this phase.

Future exact owner actions, **not requested or presumed now**:

1. Resolve the Agent/Detector/evidence blockers prospectively. Authorize any new
   qualification campaign separately; current engineering calls are finished.
2. Arrange two independent reviewers or explicitly approve a disclosed reduced
   claim; approve observer, N2 interpretation, evidence, abstention, prompts/model,
   rubric, baselines, positive-control and cost/time decisions with names/dates.
3. Verify actual organizer start/portal status after the sprint begins, preserving
   a local evidence file and its SHA-256. The current webpage is contradictory.
4. Create an approved copy of `research/phase5a/freeze-candidate.json`. Bind every
   GO qualification to a file+SHA; fill attributable decision records, approved
   start evidence and owner authorization for exactly
   `RUN_FORMAL_PILOT_20_EPISODES_ONLY`, configuration hash, max220 generations,
   explicit USD ceiling<=5 and acceptance of synthetic sandbox AIG consent.
   Recompute manifest_hash over all other fields. This attests operator records;
   it does not authenticate human per-Plan consent.
5. First check only:

```powershell
uv run python -m pactlens.research.study_launch --manifest research/phase5a/owner-approved-freeze.json
```

After a new explicit owner instruction to launch the qualified approved Pilot:

```powershell
uv run python -m pactlens.research.study_launch --manifest research/phase5a/owner-approved-freeze.json --execute --output .runtime/approved-pilot-unique
```

The current candidate fails closed before files/providers. Source/configuration
changes invalidate approval. Existing output, intent or ledger prevents automatic
restart. Unknown and provider uncertainty stop dispatch; there is no effect replay.
An eight-hour envelope bounds the authorized Pilot composition; cancellation can
leave uncertain remote inference and retains its reservation. No checkpoint
recovery is silently promoted into a second effect.
