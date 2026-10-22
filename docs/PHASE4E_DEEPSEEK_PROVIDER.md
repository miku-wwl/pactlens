# DeepSeek provider boundary

Explicit opt-in `deepseek_responses`; Ollama remains available and unchanged.
Authenticated `/models` returned `deepseek-flash`, `deepseek-v4-pro`. The only
generation candidate was Flash. Every actual response identified itself as
`deepseek-flash`; no immutable remote weight digest was provided. The pricing
page currently maps that alias to DeepSeek-V4.1-Flash-1017. Alias stability within
11 calls is not an immutable-version or determinism guarantee.

Reviewed [Responses API](https://api-docs.deepseek.com/api/create-response/):
fixed HTTPS `api.deepseek.com:443/responses`, TLS verification, no redirects,
no arbitrary endpoint, no tools. `text.format.type=json_schema`, closed root and
nested objects, `reasoning.effort=none`, temperature 0, stream false,
max_output_tokens 256. No undocumented strict flag, seed, top_p, Chat fallback
or thinking fallback. Seed support is UNSUPPORTED; host matching seeds still
bind exogenous inputs, not reproducible remote randomness.

`agents/deepseek_provider.py` reads only DEEPSEEK_API_KEY from process or Windows
user environment, never writes/logs/hashes it. HTTP error bodies and request
headers are discarded. Only reviewed synthetic Agent context or allowlisted L3
is sent. Agent briefs may contain instructed sandbox cooperation; Detector
requests contain no assignment, hidden coalition, private brief, oracle or L2.

Typed failures cover authentication, permission, rate limit, unsupported request,
HTTP/redirect, connect/read timeout, uncertain dispatch, empty/multipart output,
invalid JSON/envelope, refusal, model identity change, missing request ID/usage,
inconsistent or excessive usage, reasoning, incomplete and truncated generation.
An error stops that provider object. No request is retried. Cancellation retains
the reservation because a synchronous HTTP worker may still finish remotely.

Atomic SQLite `BEGIN IMMEDIATE` reservations bind profile, ceiling, role and exact
request/context identity. Engineering limits remain 36/20/56 and USD5, honoring
PACTLENS_DEEPSEEK_MAX_USD when lower. Cache-miss peak rates reserve full input/output
caps before POST; ambiguous reservations are retained. Restart with changed
configuration or duplicate identity is denied. The separately guarded future
Pilot factory requires verified authorization before creating its distinct ledger.

Evidence: [predeclared profile](../review/phase4e5a/live/predeclared-plan.json),
[sanitized ledger](../review/phase4e5a/live/usage-final.json).
Client accounting is a safeguard and estimate, not an account invoice guarantee.
