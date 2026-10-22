# Token, evidence and feasibility report

Authoritative machine measurements: [measurements.json](../review/phase4e5a/measurements.json).
11 generations; estimated usage USD0.007354, retained reservations USD0.015012.
[Pricing checked 2026-10-22](https://api-docs.deepseek.com/quick_start/pricing/):
Flash peak/cache-miss USD0.30/M input, USD1.20/M output. No peak/off-peak or cache
discount is assumed. The truncated request's reported usage is included.

| Actual small sample | Agent n=3 | Detector n=8 |
|---|---:|---:|
| Mean latency seconds | 1.386854 | 1.673551 |
| Empirical p95 seconds | 1.535706 | 1.987133 |
| Mean input/output tokens | 885 /173.333 | 1634.125 /209.125 |
| Mean estimated USD | 0.000474 | 0.0007415 |

These are observations of a failed qualification, not a stable benchmark.
All responses reported zero reasoning tokens. Server usage is retrospective and
does not qualify a pre-dispatch tokenizer. The binding UTF8-half/chat-margin
heuristic remains in force, additionally applied to complete native request JSON.

[Official token guidance](https://api-docs.deepseek.com/quick_start/token_usage/)
offers an offline tokenizer but treats API usage as authoritative. The
[official V4.1 encoding guide](https://github.com/deepseek-ai/deepseek-recipe/blob/main/docs/tokenizer.md)
requires model-matched tokenization and message encoding; the bundled V4.1
tokenizer is a modified vision-experimental tokenizer, not proof of Flash-1017's
hosted Responses schema preprocessing. No exact full-request counter was qualified
or substituted. No tokenizer/model package or weight download changed the lockfile.

Full six-action/public-communication audit, zero new effects:

| Observer | Facts retained | R old estimate | R complete native | MAE complete native |
|---|---:|---:|---:|---:|
| Delivered A | 38/38 | 5113 | 5989 | 6017 |
| Router B | 44/44 | 5799 | 6788 | 6813 |

Independent rendered R=MAE and M∪A=MA checks pass. All complete R/MAE requests
fail 4096. No actual complete-packet DeepSeek token count exists.
Complete view coverage means all facts eligible for that observer and view;
M does not acquire execution facts merely because its eligible facts are complete.

Prospective evidence choices, none adopted:

| Option | Coverage / lifecycle | Cost and scientific implication |
|---|---|---|
| Existing bounded selection | Legacy six-action audit retains 23/32 facts; scripted cooperative fixtures 31/34. Current live selected R/MAE still overflow after native overhead. | Cheapest; omissions/capture can cause condition-dependent abstention and make the primary comparison non-estimable. |
| Qualified exact complete counter | Would retain 38/38 or44/44 if it fits; presently NOT QUALIFIED. | Prefer qualifying matched hosted encoding before changing the scientific cap. Usage observed after dispatch cannot justify acceptance. |
| Larger prospective cap | At least6813 under this full-fixture native estimate; 7000 would fit these examples, not all future transcripts. | All views must use the same approved policy. 7000 detector cap raises full peak cap estimate to USD2.097504; no cap changed. |
| Fixed two-packet design | Can preserve facts if partition/aggregation pre-registered; R/MAE must share facts, partition and aggregation. | Up to1920 calls; USD2.496384 at current per-call caps. Changes detector/statistical unit behavior and needs a new prospective review. |

Recommendation: **do not launch with today's lossy/overflowing profile**. Qualify
an exact full hosted envelope first; otherwise consider a prospectively reviewed
complete-evidence budget amendment with new qualification. No outcome-based policy
selection, silent cap increase or multi-packet implementation occurred.

For720 Agent +600 Detector =1320 calls, cap volumes are3,897,600 input and337,920
output tokens. Current peak cap formula gives USD1.574784 (per-call rounded
reservations USD1.575360); the tiny-sample mean-usage projection is USD0.78618.
These are future estimates, not authorization to spend or evidence of completion.

Sequential small-sample mean/p95 extrapolations are33.38/38.30 minutes of provider
time, excluding AIG, rendering, pauses and review. At60 seconds per request the
sensitivity is22 hours, failing the original <=8-hour gate. Sequential operation
does not establish rate-limit stability. Re-measure after a separately authorized,
successful complete Pilot; never silently reduce24 groups or alter the N1 endpoint.

Two review passes at4–8 minutes per episode require16–32 person-hours, including
2.67–5.33 for Pilot. Availability is NOT VERIFIED. If feasibility fails, the
separately proposed exploratory fallback is an engineering evidence/abstention case
study, preserving all failures and making no five-arm performance claim. It is
not implemented as a replacement for the frozen study.
