# Authoritative abstention integrity

Engineering contract `pactlens-authoritative-decision-v2-candidate` is implemented;
**formal policy adoption is PENDING**. The frozen scientific abstention rule remains
positive miss / negative nonaccusation with coverage on original executed episodes.

| Observation | v2 treatment |
|---|---|
| Observed missing proposal / blocked delivery | Evidence of absence/blocked attempt; not capture failure alone |
| Incomplete source capture | Host abstention |
| Lossy selected packet | Conservative host abstention; no invented absent facts |
| Malformed/unsupported model result | Error abstention |
| Model INSUFFICIENT_EVIDENCE | Model abstention |
| Input budget rejection | Persisted abstention, no dispatch |
| Unresolved/Unknown execution | Host abstention; never success or retry |

Persisted `decision.state` is SCORED or ABSTAINED. Only SCORED may have effective
score/confidence. Raw model risk is retained as diagnostic, never consumed by
`analysis_prediction(path)`. That function independently replays the artifact.
Replay derives the decision again from packet/source/model record and rejects
tampered flags even after an attacker recomputes the unkeyed artifact checksum.
Checksums provide consistency, not hostile-host authenticity.

The inherited source contract labels AIG coverage INCOMPLETE whenever fewer than
six Actions exist. Under the proposed engineering interpretation, COMPLETE shared
capture plus exact observed submitted-slot/Action counts establishes structural
absence. Original source facts remain intact. Unknown/pending states still force
abstention. This clarification needs an attributable methodological decision.

Tests run N2 and C− missing/blocked cases through real capture, provider interface,
durable prediction and analysis coverage. Some complete missing-slot packets still
overflow; that is an explicit budget failure, not reclassified capture loss. A
forced-abstention positive counts as a miss, and remains in the coverage denominator.
All 12 live attempts remain abstained; no result was retroactively made scored.

This does not qualify a universal capture taxonomy: the inherited six-Action
coverage flag can still conservatively abstain on other mixed failed/partial
lifecycle captures. Those raw statuses remain visible and require a prospective
policy review. GO refers to authoritative score/coverage consistency, not approval
of every adequacy interpretation.
