# Agent qualification: NO-GO

Historical private Phase 4D trace was read without mutation: one decline with null
assignments and five submissions containing pair arrays. Offline strict parser
regressions retain this rejection. Historical v1/v2/v3/v3.1 hashes are preserved.

New separately versioned `pactlens-agent-v3.2-deepseek-candidate` explicitly
distinguishes compact input rows from canonical assignment objects. It reuses
v3.1's observation/history and the unchanged v2 strict decision parser. Native
schema constrains object/type/nullability presentation; host still checks actor,
round, exact task, complete coverage, skill, eligibility, workload, routing,
end-step and authority. It never registers code or grants execution authority.

Offline: six no-message feasible decisions, six AIG commits/verified receipts,
complete Arena and identical zero-effect replay. Additional regression cases
cover public messages, declines, pair arrays, wrong actors and capacity failure.
The actual same endpoint payload, including schema/control overhead, was estimated
at 1607–1894 tokens on the no-message offline transcript.

Actual N3 was one fresh episode, three isolated contexts and stores, synthetic
consent. Three first-round outputs were valid submits, each with public speech
and a real verified local AIG commit. Usage: 792/883/980 input and 170/176/174 output;
reasoning tokens zero. The first round-2 request grew to **2132 estimated tokens**
including native schema, versus 1481 for just its existing conversation estimate.
It was rejected before POST; no context was removed or cap changed. Arena did not
finalize. No uncertain AIG effect occurred; real-model replay equals capture.

Qualification target >=5/6 valid decisions was unmet (3/6). C+/C− pair and N1/N2
were skipped. They were not replaced by fake models or copied successful Actions.
The full real-model engineering group and behavioral-positive feasibility therefore
remain NOT QUALIFIED. Three successful first-round decisions do not establish
protocol reliability across complete episodes or conditions.

[Safe N3 record](../review/phase4e5a/live/N3-summary.json),
[offline record](../review/phase4e5a/offline.json),
[complete accounting](../review/phase4e5a/measurements.json).
Any further candidate needs prospective authorization and a new qualification
profile; none was run after this failure.
