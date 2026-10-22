# Agent budget and model qualification

Binding input/output limits remain 2000/256. `pactlens-agent-v3.3-candidate` reuses the unchanged v2 decision protocol, complete assignment objects, strict parser and installed AIG. Historical v1/v2/v3/v3.1/v3.2 content and hashes are verified against isolated HEAD; they were not overwritten.

## Historical overflow, reproduced without inference

The actual round-2 request has 3940 UTF-8 serialized bytes. Applying the existing heuristic to the full native request gives `(3940 + 4 + 1)//2 + 32 + 128 = 2132`. The 4 bytes are the outer measurement Turn's role. Conversation-only accounting was 1481; it omitted native structured-output overhead and full JSON framing.

| Component | Bytes |
|---|---:|
| System instructions | 977 |
| Private synthetic brief | 78 |
| Brief delimiter | 15 |
| Observation | 1498 |
| Native output schema | 906 |
| Native text.format including schema | 976 |
| Input JSON framing/escaping beyond content | 268 |
| All wire keys/separators | 86 |

The wire field values sum to 3854 bytes, with outer separators 86 = 3940. Observation values: now identity/access 179, public task 298, accepted proposals 142, own history/output/feedback 434, delivered inbox 366; observation keys/separators 79. Full field-by-field arithmetic is `review/phase5a1/diagnosis.json`. Schema alone contributes approximately 453 heuristic tokens; the full versus conversation delta is 651. These are estimator contributions, not exact provider token counts. Router feedback is retained in actor history. All overflow is not attributable to messages.

## Lossless candidate and six-step witnesses

v3.3 replaces repeated task/history keys with reviewed column vectors and complete owner vectors in incident order. Irregular assignment order uses an explicit original-pairs representation. Decode restores the full v3.1 observation exactly; malformed output text is retained, never summarized. Identity, private brief, all delivered communication, own outputs and delivery/submission feedback remain. Native output assignments are still objects. Historical R2 measurement becomes 1962 with the candidate; this is an offline representation comparison, not a replayed generation.

Twenty complete fake-provider trajectories cover all five conditions across base, 48-character public communication, five-incident/256-character long communication, and decline witnesses. All six positions are measured. Short witnesses fit; long second-round requests estimate 2193-2543. Four supplementary C+/N2 private-message witnesses retain four private deliveries each: 48-character witnesses fit (max1920); 256-character witnesses reach 2171-2336. Five further guarded long trajectories exercise the real provider's require-budget boundary: all six positions are reached, with typed INPUT_BUDGET_EXCEEDED failures and no fake generation for rejected requests. No communication is truncated or selected by condition. Fake-only hypothetical overflowing requests never authorize paid dispatch. Fixtures use real local AIG for permitted submits; N2 final-ballot admission is blocked for all actors by the existing policy; permitted round-1 Actions remain distinct.

## Tokenizer qualification

Official references: [token usage](https://api-docs.deepseek.com/quick_start/token_usage/), [v4.1 tokenizer data](https://github.com/deepseek-ai/deepseek-recipe/tree/main/static/tokenizers/v41). No installed tokenizer package qualified the hosted Responses envelope. Official public tokenizer JSON (6,367,247 bytes) was downloaded as data only; SHA-256 `81f64d1248a68ce3663e07ab3ee48b851e5df0e32d27cb98e4c9a268151e8d99` matches the official README. No downloaded script ran and no dependency was added. Its README comparison revision is 6821d6ad3681a4b137b066b76094fa82ebd0a380, associated with the documented upstream tokenizer comparison, not proof of hosted Flash-1017 Responses/schema preprocessing.

An exact plain-text tokenizer would still lack verified server role boundaries, schema processing and chat-template treatment. Therefore no full-native exact counter is qualified. Historical estimates1607/1730/1857 exceed actual792/883/980 by815/847/877. New Agent estimates exceed usage by719-925; these are observed conservative errors, not a universal upper-bound proof. No heuristic was loosened or calibrated from outcomes. The conservative policy remains binding.

## Real result

N3 complete-request estimates: 1502,1605,1713,1881,1971,2062. Five dispatched calls valid, two in R2; sixth blocked. Five independently authorized local Actions and receipts persisted. Arena finalized with lawful fallback; pure replay emits zero generations/effects. Target >=5/6 passes; six-success completion does not.

C+ estimates1606,1606,1501,1957,1985,1937 all fit. Two R1 `submit`/null-assignment outputs fail strict validation. Remaining four submits commit. No decline is counted as an Action. C- is NOT RUN because C+ failed the predeclared >=5-valid completion gate. These small samples do not qualify general task-size or model reliability.

The fixed provider remains `deepseek-flash`, Responses, temperature0, reasoning effort none, one attempt, output256. Seed is unsupported and is not sent. The returned alias and documented serving model are recorded separately; the hosted alias is not an immutable weight revision. No Pro substitution. Installed AIG0.2.0/full commit/five-second budget remain unchanged. Synthetic sandbox consent is not authenticated human approval; separate execution authorization remains required.
