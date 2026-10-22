# Phase 5A.2 test and security matrix

Final regression results are recorded after completion in `review/phase5a2/verification.json` and `logs/final-*.txt`; no test outcome is inferred from scaffolding.

| Check | Actual evidence / acceptance |
|---|---|
| Entry regression | Isolated archived HEAD: 930 passed in 535.94s |
| Initial scoped regression | 132 passed in 29.29s |
| Final candidate tests | 49 passed in 17.16s; protocol, host abstention, replay/analysis, exact witness, ledger slots, frozen design |
| Full source regression | 979 passed in 548.60s; no failures |
| Clean checkout, no private runtime | 979 passed in 555.48s; current-source verifier PASS without `.runtime` |
| Installed dependency | AIG 0.2.0 exact commit, 57 RECORD hashes, site-packages import, default five seconds |
| Current Phase 5A.1 verifier | PASS on actual current HEAD and independent clean checkout, no private `.runtime` |
| Optional historical audit | PASS on archived private receipts: N3 five, C+ four, files unchanged |
| New durable effects | 52 receipt bindings verified locally, 36 distinct scopes/stores, private bytes unchanged |
| Unknown / duplicate / authorization / stale / conflicting effects | Preserved AIG consumer tests plus new host Unknown abstention; no live Unknown, no replay dispatch |
| Actor/context isolation | Fresh per-actor stores, exact actor/task schemas, fixed ten Agent / 60 Detector ledger contexts |
| Caps and slots | 53 Agent + 40 Detector; exact 60 opportunities/60 view slots; role≤60, total≤120, projected $0.109564≤$5 |
| Strict Detector | Invalid/uncited/out-of-packet citations, score bool, fields, reason enum, truncation rejected; valid record analysis/replay |
| Evidence | Final-render R/MAE independent parity and eligibility equality 12/12; zero paid packet omissions |
| Truth isolation | Only strict L3 packets reach Detector; rubric labels/coalition assignment/witness are experimenter-side |
| Formal guards | Pending 16-decision manifest denied; all formal slots 0; no fabricated reviewer approval |
| Archive | CRC, every member SHA-256, current-source bytes and secret scans recorded in independent adjacent receipt |

Required commands: `uv sync --locked`, `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv lock --check --offline`. Tests use safe fixtures/fake providers; no pytest performs live DeepSeek inference. The real campaign is separately fenced behind its engineering allowance, fresh directories and fixed ledger.

All five required commands passed. The initial final lint found only a missing blank line separating two test imports; it was corrected, lint passed and all 49 candidate tests passed again in 13.37s. Production source bytes remain identical to dispatch. The clean clone used the current source overlay, all public fixtures and the installed pinned environment, with no private campaign directory. The original baseline archive remains unmodified.

`scripts/verify_phase5a1.py` now separates current public-source checks from `--historical`. The default resolves today's HEAD rather than asserting the old campaign's base commit, and replays ten public historical prediction files without private databases. `--historical` requires archived original receipts; missing private state is a typed historical-audit requirement, not a current-source test failure. The source distribution and review ZIP omit private state, credentials and full private Agent prompts.
