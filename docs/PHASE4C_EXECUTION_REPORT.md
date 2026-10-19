# Phase 4C — Execution Report

**2026-10-19/20 NZDT. Pre-sprint engineering / pre-existing work.**

## 1. Overall status

**PARTIAL overall; Phase 4C offline engineering PASS.** The v2 context overflow is
explained and removed for representative histories by a lossless, versioned v3
context; evidence representation is improved losslessly and complete-evidence
infeasibility is measured precisely. Two fundamental problems remain open: the
single bounded live episode produced **0/6 valid outputs**, and complete
six-action evidence is **`EVIDENCE_BUDGET_INFEASIBLE`** at the 4,096-token estimate.

| Handoff §22 criterion | Result |
|---|---|
| 1. v2 overflow explained | PASS: exact offline reproduction (5,099 B / 2,838 est.) and full byte attribution |
| 2. Versioned context candidate exists | PASS: `pactlens-agent-v3-candidate`, opt-in, v1/v2 unchanged |
| 3. Representative offline six-step path fits | PASS: all fixture speech scenarios and all no-speech scenarios on the largest generated task, every condition |
| 4. Decision-relevant history preserved or limits disclosed | PASS: v2 turns rebuilt byte-for-byte from v3 text; presentation changes and message-volume coverage limits disclosed |
| 5. Proposal and AIG validation intact | PASS: unchanged v2 decision protocol/parser; installed AIG path; no repair |
| 6. R/MAE information matched | PASS: parsed-text parity, `M∪A=MA⊆R`, byte re-render |
| 7. Detector request budgets enforced | PASS: complete envelope budgeted; overflow is typed |
| 8. Episode audit sufficiency shown or explicitly failing | Explicit gate failure: `EVIDENCE_BUDGET_INFEASIBLE` with measured bottleneck |
| 9. Earlier tests green | PASS: all 607 original cases pass (section 7) |
| 10. Formal research unexecuted | PASS: 0/120 slots, no detector inference |

| Gate | Decision |
|---|---|
| Engineering readiness | **GO** |
| Model generation-path readiness | **PARTIAL**: six-step path feasible; output validity **REAL_MODEL_NOT_READY** (0/6) |
| Detector evidence sufficiency | **NO-GO** for complete episode-level audit |
| Formal pilot readiness | **NO-GO** |

## 2. Baseline and provenance

Starting tree clean on `main`; local HEAD, `origin/main` and live `ls-remote` all
**`d26995ee91a2fa9dbaae59b97befacaf7e050e21`** (pushed Phase 4B). Baseline suite:
**607 passed**. Installed AIG **0.2.0** from `.venv`, direct-URL commit
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`, 57/57 RECORD hashes, 22 public names,
five-second default. Phase 4C is an uncommitted delta: six new source modules,
three additive source edits, seven new test files, six new documents and additive
README/architecture/data-dictionary/provenance entries. Protected sources, the
frozen plan, AGENTS, dependency config/lock, all 54 existing test files and the
tracked Phase 1 ZIP are unchanged under git's normalized comparison. All work is
pre-sprint ([provenance §10](PROVENANCE.md)).

Discrepancies with the handoff: after the Phase 4B v2 stop, one round-2 step failed
preflight and two were NOT_REACHED (three unexecuted, as stated); on the nine
historical sent requests the provider counted 0.425–0.522 of the estimate, so the
v2 overflow is a conservative-safeguard failure rather than proven model overflow.
The estimate was kept binding, not relaxed.

## 3. Context diagnosis and v3

The overflow came from duplication and verbose serialization: the public task twice
(1,478 B), the task hash eight times, accepted proposals as verbose objects (771 B)
and five chat turns. v3 sends one compact observation built from exactly the v2
information: task tables once, proposal rows, verified prefix counts for earlier
views, the actor's own earlier output as its JSON value (verbatim if unparseable)
and the same feedback statuses. The same step falls to **2,849 B / 1,617** in two
turns. Details: [context report](PHASE4C_MODEL_CONTEXT_REPORT.md).

## 4. Six-step offline budget

| Scenario (estimated tokens, limit 2,000) | Worst step |
|---|---:|
| Historical transcript (v2 overflowed at step 4 with 2,838) | 1,664 |
| Fixture, five conditions × {none, round-1 80, pair 80, everyone 40} | 1,923 |
| Largest generated 5-incident task, no speech, five conditions | 1,931 |
| Largest generated task, pair private 80: C+ and N2 | 2 explicit overflows each |

Coverage boundaries (largest uniform message that keeps all six steps in budget):
C+ 91–133 characters on the fixture, 41–66 on the median generated task and 0–7 on
the largest; C− up to 256 where attempts are blocked. Overflow is explicit, never
sent, never truncated, and condition-correlated through speech.

## 5. Evidence sufficiency and parity

Lossless tables v2 (key-cited facts, listed values, owner vectors, stream
references) reduce complete six-action packets by about 20% of estimated tokens
(six-receipt R: 6,364 → 5,117 under A; 7,234 → 5,824 under B). Text is parsed back to
complete facts, must re-render byte-identically, and R/MAE parity plus `M∪A=MA⊆R`
are checked from parsed text. Over 54 audited source/policy sets the same Phase 4B
rules now give 18 complete-episode packets (from 4) and double retained integrity
pairs, but **every six-action source is `EVIDENCE_BUDGET_INFEASIBLE`**
(5,002–5,825); the lifecycle core alone needs about 4,261–4,267. Selection differs
across conditions only through observable behavior and observer rights, yet the
loss is differential (C+ loses the most lifecycle evidence; C− under B carries
mandatory blocked attempts). Details: [sufficiency report](PHASE4C_EVIDENCE_SUFFICIENCY_REPORT.md).

## 6. Local-model result

One N3 v3 episode on Ollama 0.35.1 / phi4-mini (digest `78fad5d1…7363753`), numeric
loopback, synthetic consent: **6 generation calls** (ledger-capped), all within the
input budget (estimated 1,430–1,723; provider 660–871; 4,419 input / 885 output;
127.0 s). **0/6 valid**: five duplicate-key JSON objects (repeated `round_number`
and/or `task_hash`) and one submit with null assignments. Zero Actions, receipts
or effects; Arena finalized only through the lawful fallback; INCOMPLETE; replay
pure; stores unchanged by verification. Most plausible cause: v3's instruction to
copy identity from the single alphabetical-order example. No repair, retry, rerun
or tuning followed.

## 7. Validation

Offline (`UV_OFFLINE=1`): `uv sync --locked` exit 0; `uv run pytest -q` **724
passed (607 original + 117 new), 0 failed/errors/skipped, 444.95 s**; `ruff check`
all passed; `ruff format --check` 148 files formatted; `uv lock --check --offline`
exit 0; compileall exit 0. v1/v2 request bytes match pre-edit golden digests; the v2
prompt, protocol and Phase 4B selection hashes are unchanged. Installed AIG 0.2.0
pin and 57/57 RECORD hashes re-verified; protected sources and all existing test
files unchanged. Audits: context attribution, 30 six-step scenarios, 39 coverage
boundaries (verified by real runs at L* and L*+1 or bisection), 54 evidence
source/policy sets and 10 condition episodes, all with zero model calls; the private
Phase 4B traces were read-only (hashes unchanged). Matrix: [test matrix](PHASE4C_TEST_MATRIX.md).

## 8. Methodological risks and unresolved decisions

- **Estimator binding.** The conservative estimate is about twice the observed
  provider count for agent prompts; no exact counter is qualified. Agent coverage
  of message-heavy histories, and detector feasibility of complete evidence, depend
  on this unresolved decision (options in the [freeze candidates](PHASE4C_FREEZE_CANDIDATES.md)).
- **Presentation effects.** Identical information produced very different model
  behavior (v2 3/3 valid round-1 outputs; v3 0/6). The same caution applies to the
  planned MAE-versus-R presentation contrast.
- **Differential coverage.** Agent overflow concentrates in C+ and N2 pair
  speech; detector evidence loss is largest for C+ and for C− under Router audit.
  Coverage and abstention must be reported by condition.
- **Shortcuts.** Missing slots (N2), blocked audit rows (C−/B) and omission counts
  are legitimate observations but can reveal arms.
- Synthetic consent is not human authentication; fake transcripts are not model
  behavior; hashes show consistency, not malicious-host authenticity; observer A/B,
  N2-A, v3, v2 tables and both evidence policies remain unapproved candidates.

## 9. Readiness for future detector development

Engineering inputs are reproducible and information matched, but a detector study
at the current budget cannot receive complete six-action evidence. Before any
detector work: decide the estimator/cap or split-packet design, decide how evidence
insufficiency maps to abstention, revise and re-qualify the agent presentation,
and arrange independent reviewers. No detector inference, scoring or calibration
was implemented.

## 10. Review package and stop

`D:\workshop\oct\pactlens-phase4c-review.zip` (outside the repository) with an
external `D:\workshop\oct\pactlens-phase4c-review.zip.verification.json` receipt
holding the final archive SHA-256, CRC and per-member/source checks. It includes
source, tests, documents, safe fixtures, validation logs, attribution, six-step and
boundary reports, evidence audit and safe compact packets, the sanitized live
summary, candidate/readiness records, validation scripts and a SHA-256 manifest. It
excludes `.git`, `.venv`, `.runtime` raw data, SQLite stores, capabilities, private
prompts/traces, model weights and earlier archives. Work stops here: no commit,
push, tag, release, deployment, submission or next phase.
