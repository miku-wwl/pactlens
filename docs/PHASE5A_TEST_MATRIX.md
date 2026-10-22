# Actual verification matrix

| Check | Evidence / result |
|---|---|
| Original baseline | isolated HEAD snapshot:832 passed,554.84s |
| Final full suite | `uv run pytest -q`:885 passed,583.32s |
| Locked environment | `uv sync --locked` PASS |
| Lint | `uv run ruff check .` PASS |
| Format | `uv run ruff format --check .` PASS after wrapping the scoped import guard |
| Lock | `uv lock --check --offline` PASS; dependency files unchanged |
| AIG | installed0.2.0, exact7261fdd2 pin,57 RECORD hashes; public API/default5s |
| New provider tests | atomic caps/concurrency/restart/ceilings/usage/errors/identity/no retry |
| New Agent tests | six opportunities, canonical submits/declines, wrong actor, pair-array and capacity rejection, routing/history/replay |
| Detector/analysis | effective scores only; N2/C− observed absence and blocked attempts, tamper denial, legacy read-only compatibility |
| Launch guards | missing approval/qualification/start/owner/split/hash, future start, changed evidence/source; no provider/files |
| Launch wiring | manufactured/mock-only Unknown stop; no formal harness episode |
| Full schedule |120 slots,360 stores/scopes, zero models/effects/formal slots; duplicate intents denied |
| Synthetic exporter |9 watermarked tables, source/hash binding, formal exporter rejection |
| Evidence parity | independently rendered R=MAE, M∪A=MA; full native overflow explicit |
| Real campaign |11 generations plus1 metadata GET;3 verified receipts; no retry/fallback |
| Safety/static | protected paths/prompts, private-source replay, secret exclusions, no formal output access |
| Review ZIP | external receipt verifies CRC, every member hash and source consistency |

Logs: [review/phase4e5a/logs](../review/phase4e5a/logs). The first overlapping
development baseline produced831 passes/one import-guard failure while new files
were being added. It is retained, and superseded by the clean isolated832-pass
baseline. Development test failures and later targeted passes are retained too;
they are not reported as initial successes. The earlier complete884-pass development regression is retained. The provider
stop-condition correction added one test and triggered the final885-pass suite.
The later N2 test refinement passed all four targeted abstention tests; the
format-only import-guard follow-up passed its affected test.

Actual formal Pilot/Calibration/Held-out, human adjudication, positive C+ real
control and genuine R/MAE generation: **NOT RUN**, not PASS.
