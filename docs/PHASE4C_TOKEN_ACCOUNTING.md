# Phase 4C — Token Accounting

**2026-10-20 NZDT; pre-sprint.** Three different quantities are kept separate and
never substituted for one another.

| Quantity | Meaning | Where it appears |
|---|---|---|
| UTF-8 bytes | Exact size of role + content of every turn of the complete request | every request and packet budget |
| Estimated tokens | `ceil(bytes/2) + 32 × turns + 128` (`UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE`) | preflight decision for v2/v3 agents and all detector packets |
| Exact tokens | A trusted counter over the provider's full chat template | **null everywhere**: no verified counter exists |
| Provider-reported tokens | `prompt_tokens`/`completion_tokens` returned after a sent request | descriptive only; cannot authorize an unsent request |

Limits are unchanged: agents 2,000 input / 256 output; detectors 4,096 input /
256 reserved output over the complete envelope. The estimator was not relaxed,
calibrated or replaced. Synthetic counter seams in tests are not measurements.

## 1. Agent requests

Historical v2 round-2 request (not sent): 5,099 bytes, 5 turns →
`2,550 + 160 + 128 = 2,838`. The same step under v3: 2,849 bytes, 2 turns →
`1,425 + 64 + 128 = 1,617`. Two turns save 96 estimated tokens of chat overhead;
the rest is removed duplication (category table in the
[context report](PHASE4C_MODEL_CONTEXT_REPORT.md)).

Provider-reported versus estimated on the nine historical sent requests:

| Request | Estimated | Provider-reported | Ratio |
|---|---:|---:|---:|
| v2 a0 r1 / a2 r1 / a1 r1 | 1,669 / 1,796 / 1,924 | 782 / 875 / 967 | 0.468 / 0.487 / 0.502 |
| v1 a0 r1 / a2 r1 / a1 r1 | 1,392 / 1,610 / 1,610 | 592 / 740 / 740 | 0.425 / 0.459 / 0.459 |
| v1 a0 r2 / a2 r2 / a1 r2 | 2,433 / 2,640 / 2,604 | 1,189 / 1,380 / 1,318 | 0.488 / 0.522 / 0.506 |

(v1 had no candidate preflight; its round-2 requests were sent although their
estimates exceed 2,000.) The estimate is about twice the observed count for this
model, template and content, yet it stays binding: ratios from nine related
engineering requests are not a qualified tokenizer, and hex/UUID-heavy or
non-English content can tokenize less favorably than English JSON.

Bounded v3 live episode (2026-10-20): six sent requests estimated 1,430–1,723 and
provider-reported 660–871 (ratios 0.462–0.506); totals 4,419 input / 885 output.
Across all fifteen observed sent requests (v1 six, v2 three, v3 six) the largest
provider-reported input was 1,380. These are descriptive engineering observations
on one model and template, not a tokenizer qualification.

## 2. Detector requests

The fixed envelope (system, task, output instructions, response schema and turn
labels) costs 906 bytes before evidence; with three turns the evidence text may
use at most `2 × (4,096 − 96 − 128) − 906 = 6,838` bytes. Hex digests and UUIDs
are irreducible values of lossless evidence; for such strings a real tokenizer
may approach the 2-bytes-per-token estimate, so the detector estimate is not
necessarily conservative by the same margin as for agent prompts.

Complete six-receipt evidence needs 5,117 (A) and 5,824 (B) estimated tokens with
v2 tables (6,364 and 7,234 with v1 tables); the lifecycle core alone needs about
4,261–4,267 in every six-action source. Selected R packets from the historical and
condition sources fit at 3,846–4,044 (one mandatory core overflows at 4,226). Every
detector exact-token field is null, and no detector request was sent.

## 3. What a future exact counter would need

A verified counter must reproduce provider-reported `prompt_tokens` exactly for
the complete chat template (system/user/assistant markers included) on a held set
of real requests, be pinned to the model digest and template revision, and be
approved prospectively. Until then every decision uses the estimate, and every
overflow remains an explicit, logged `INPUT_BUDGET_EXCEEDED` or
`EVIDENCE_BUDGET_INFEASIBLE`.
