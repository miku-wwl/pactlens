# Prospective budget amendment — engineering authorized, formal adoption PENDING

Named contract: `pactlens-phase5a3-4096-agent-8192-detector-candidate`.
Hash: `ab99c0c1f132abe07509ebe310a703433963d9e5095d88915c68b4ccb3f5e3cb`.

| Role | Historical input | New input | Output, unchanged |
|---|---:|---:|---:|
| Agent, every condition | 2000 | 4096 | 256 |
| Detector, every view | 4096 | 8192 | 256 |

The estimator remains conservative UTF8-half-plus-chat-margin over the complete native JSON request, including schema, JSON escapes and generation controls. No exact tokenizer or empirical-ratio substitution was introduced. The generic TokenBudget record can represent 8192; legacy preflight still rejects that limit without the explicit new profile. Unrelated response byte bounds, message 256-character limits, bootstrap counts and structural limits are unchanged.

| Enforcement point | Binding |
|---|---|
| Prompt construction | v3.5 budget identity uses unchanged v3.4 text/context/briefs; request limit 4096 |
| Native preflight and dispatch | Fixed host-selected profile, role cap and exact trusted provider/ledger profile |
| Provider actual usage | Reject input above 4096/8192 and output above 256; no reasoning output |
| Ledger | Full-role-cap conservative reservations, exact declared contexts, atomic per-context/role/total/spend limits |
| Harness | New prompt's Agent actual-input cap 4096; legacy prompts retain 2000 |
| Detector envelope/rendering | Separate ContextEnvelope, input 8192, same strict reason schema and semantic text |
| L4/replay | Separate v5 runner namespace; envelope, budget contract/hash and recorded budget recomputed on replay |
| Analysis | Profile/hash in descriptive matrix; repeated historical measurements identified explicitly |
| Freeze/launch | Separate v5 candidate binds both caps, complete-source selection, model/schema/policy/source hashes; 16 approvals still PENDING |

Complete source facts are retained for all views with no truncation. This matches the previous paid engineering campaign; the future formal candidate proposes complete-source selection instead of the previous unapproved greedy selector. Both changes need prospective owner approval. Larger context permits communication histories and full execution evidence but cannot make invalid messages, incomplete capture or semantic errors disappear.

Measured native estimates: Agent **1474–2139**, Detector **2415–5294**. Actual inputs: **777–1208** and **1416–3919** respectively, all within the new caps. Four Agent and twenty Detector dispatched requests exceed their old conservative estimate limits. Estimate minus actual ranges: Agent 697–960, Detector 971–1375. Actual observed inputs do not reach the new maxima; offline boundary tests separately exercise exact cap and over-cap usage. Offline six-position tests in all five conditions with maximum 256-character communication fit, maximum native estimate 2382. Maximum real delivered message length was 248 characters. Request/schema byte costs and per-call estimation errors are in `qualification-analysis.json`; none were used to tune the estimator.

Across all 15 actual actor round-one/round-two request pairs, maximum complete-native estimate growth was 475 tokens; maximum observation growth was 875 UTF8 bytes. `communication-growth.json` records every pair's request/observation sizes without exporting private prompts. These histories include communications and previous decisions; the growth is not attributed to messages alone.

Engineering spend cap is $2 and 75 prospectively selected generations (below authorization of 80); no unused control quota was spent. Proposed full-study maximum input becomes 7,864,320 tokens, output remains 337,920, generation cap remains 1320. At rechecked peak rates the full-cap nominal estimate is $2.764800; per-request rounded reservations $2.764920. The 20-episode Pilot maximum is 220 generations and $0.460820 rounded reservations. These are forecasts, not approvals; price, model alias, actual usage and latency must be rechecked before launch.

Exact prospective formal amendment proposed: “Adopt the named hash-bound 4096/8192 profile for a newly approved formal Pilot only, retaining output 256, unchanged Agent/Detector semantic instructions and strict schema, all five evidence views, complete permitted facts, observer, authoritative insufficiency/Unknown rules, Arena mechanics, AIG authorization/default five seconds, rubric, 24-group split, primary endpoint and calibration/coverage/stopping rules. Preserve historical 2000/4096 results without reclassification. Obtain all method decisions and separate `RUN_FORMAL_PILOT_20_EPISODES_ONLY` owner authorization.” **PROPOSED, NOT APPROVED.** `EXPERIMENT_PLAN.md` is unchanged.
