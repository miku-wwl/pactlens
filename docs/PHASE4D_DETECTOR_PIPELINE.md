# Phase 4D — Detector vertical slice

2026-10-22 NZDT; offline interface works; formal detector execution disabled.

`research/detector_runner.py` accepts only a verified typed CompactView and ENG
engineering namespace. It rechecks final rendered facts/manifests and the full
request estimate, reuses the provider-neutral generation port and existing local
Ollama transport, validates strict Phase 4B score/confidence/adequacy/explanation
JSON, and resolves only explicitly supplied table citation keys to fact UUIDs.
Wrong/unobserved/omitted citations and duplicate JSON keys fail closed. It never
consults L1/L2 or chooses thresholds. Public episode/view/prompt identity is bound
by the host rather than copied from an untrusted model's self-report.

Versioned immutable records bind model/revision/config, envelope/schema/template,
budgets, seed, evidence text and manifest, usage, errors and response hash. An
exclusive fsynced intent precedes dispatch; the same request cannot silently run
again in that store. An interrupted intent has no automatic resume. Final writes
are exclusive, fsynced and hash checked. This is filesystem consistency/fencing
under a trusted host, not malicious-host authentication or distributed storage.

Finite numeric research serialization is separate from Arena's unchanged integer
serializer. PredictionRecord now accepts both existing v1 and v2 evidence versions;
the Phase 4B response schema and hashes retain their original meaning.

Missing/nonobserved facts or selection omissions force a host abstention, while
preserving a valid model's score if one exists. Provider/parse/budget/output errors
produce error abstentions. Read-only replay reconstructs the packet and record,
verifies hashes/citations/identities, and has no provider or AIG execution path.

## Actual validation

The deterministic fake-detector matrix exercises all five views, adequate and
insufficient outputs, provider errors, malformed JSON/duplicate keys, forbidden
citations, scores/types/extra fields, output truncation, pre-dispatch overflow,
incomplete evidence, immutable duplicate refusal, tamper rejection and replay.
These fake scores are test artifacts, not research predictions. A separate E2E
test joins fake-agent decisions, real installed AIG commits/receipt verification,
Arena, L3, fake detector, immutable L4 and pure synthetic analysis, verifying
effect-store bytes unchanged by inference/replay.

After that matrix passed, exactly **2 local engineering smoke calls** used R and
MAE from the failed N3 engineering episode. Both passed active estimated input
preflight, with provider inputs 2,036 and 2,061; outputs 116 tokens each. Both
were INVALID_OUTPUT and persisted as abstentions, not repaired or retried.
No valid real-model risk prediction or detector accuracy result was obtained.
Safe artifacts are under `review/phase4d/local-detector/`; the original provider
responses are represented by hashes, not exported text. This tests interface
dispatch and error preservation only. Formal model/tokenizer qualification and
methodological approval remain absent.
