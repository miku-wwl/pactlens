# Phase 4A — Execution Report

**2026-10-19 NZDT. Pre-sprint engineering; pre-existing work.**

## 1. Overall status — PASS (offline engineering)

Phase 4A is implemented and offline verification passes. This is not formal
research or proof of improved real-model reliability. Engineering readiness is
**GO**; detector-view methodological readiness is **CONDITIONAL GO**; formal pilot
readiness is **NO-GO**. Full evidence contexts currently exceed the conservative
monitor preflight; unresolved observer/token/freeze decisions remain explicit.

The initially clean `main` tree, `origin/main` and live HTTPS remote all confirmed
the pushed Phase 3 baseline **`6bf93a996476e6433eedc3fa11784703bf61a31a`**.
This phase remains an **uncommitted working-tree delta**. No commit, push, tag,
release, deploy, competition submission or Phase 4B work was performed.

The frozen Phase 0.6 study remains 4 pilot +10 calibration +10 held-out matched
groups, five conditions each: **24 groups /120 future slots /0 formal executions**.
Condition definitions, pairing, truth, split membership, abstention, thresholds,
Arena mechanics, fallback and statistical rules are preserved.

## 2. Engineering changes

**Model contract:** retain original Phase 3 v1 system prompt/parser/history and
engineering default. Add explicit opt-in `pactlens-agent-v2-candidate` /
`pactlens-decision-v2-candidate`, versioned hashes/diagnostics and public-task
canonical JSON examples. Examples choose the first feasible allocation rather
than consulting the lawful optimum/oracle. Strict JSON, closed fields, exact
identities, full feasible assignments, recipient rules and size limits remain
trusted host checks. Valid voluntary decline is distinct from malformed output.
No repair, forced submission, proposal replacement or Action retry was added.

**Budgets:** candidate input preflight records bytes, an explicit conservative
heuristic and optional trusted full-template token count against 2,000 input
tokens. Actual usage is recorded when available; excess input/output or truncated
candidate completion cannot submit. The adapter has no exact Ollama tokenizer;
estimates are not exact or guaranteed bounds. Full context fits or fails without
silent truncation. Future view contexts similarly guard 4,096 input /256 output.

**Trace consistency:** preserve Reader's 8,000,000-byte total, 131,072-byte record
and 256-record limits, shared with Writer. Pre-write checks preserve file,
sequence, digest, terminal flag and executor accounting on budget rejection.
The old mismatch was reproduced at 8,609,987 bytes before repair. If no terminal
fits, the prefix remains incomplete. Existing v1 traces replay without new model
or Gateway calls and are not retroactively interpreted using the candidate.

**Evidence:** add policy projection, immutable allowlisted fact inventory,
five pure view builders, deterministic versioned renderers and independently
reconstructed semantic parity. Metadata preserves opaque public identity, source/
trust, missingness, receipt correlation and known/unknown capture order. Raw
private traces, Gate tables, scopes, grants, labels and oracle results are not
source dumps for detectors. AIG remains installed **0.2.0** at
`7261fdd2f47d2b15fabe8faac527eeee37338eb1`, unchanged public API and five-second
execution budget; all 57 installed RECORD hashes were verified.

## 3. Detector views

| Fact family | M | A | MA | R | MAE |
|---|---|---|---|---|---|
| Public task/capabilities/constraints | Yes | Yes | Yes | Yes | Yes |
| Authorized communications and their coverage | Yes | No | Yes | Yes | Yes |
| Router attempts/status (only under Policy B) | Yes | No | Yes | Yes | Yes |
| Proposal slots, accepted Arena events, final allocation/costs | No | Yes | Yes | Yes | Yes |
| AIG lifecycle/approval/authorization and correlated receipts | No | No | No | Yes | Yes |
| Source/trust, missingness and order for included facts | Yes | Yes | Yes | Yes | Yes |
| Hidden assignment/private prompts/oracle/truth | No | No | No | No | No |

M/A/MA/R use readable fact JSONL; MAE groups the **same R facts** into structured
JSON. Actual rendered text is independently parsed and compared with bound
manifests and across R/MAE, including values/nulls/provenance/order. Parity passes
all 14 fixtures under both policies and actual installed-AIG synthetic snapshots.
This does not prove token equivalence, presentation neutrality or MAE superiority.
R−MA adds execution observability; MAE−R changes representation; MAE−MA combines
both differences.

One six-step fake-model engineering audit produced six real local AIG Actions/
verified receipts and **zero actual inference**. Its R/MAE rendered sizes were
22,125/38,265 bytes under A, and 26,005/44,977 bytes under B. Corresponding input
estimates were 11,373/19,443 and 13,313/22,799 tokens; exact token counts are
unknown. The full ten-row measurement table is in the
[test matrix](PHASE4A_TEST_MATRIX.md). These complete audit artifacts are not
model-ready within the current guard. Overflow prevents conversation creation;
no view gets favorable truncation or meaningless padding.

## 4. Experimental validity

**N2:** all round-2 execution is still blocked. Its missing slots are truthful
observable facts and a direct intervention artifact, not proof that a detector
understands talk versus harmful action. Retain/disclose now; a lawful-ballot
alternative is separately proposed and **not implemented**. Do not fabricate
receipts, hide failures or rewrite model choices to equalize arms.

**C+/C−:** Policy A intercepts only delivered speech; Policy B legitimately sees
Router attempts/status, including blocked private messages. Experimenter audit,
detector rights and actor inbox are separate audiences. Hidden assignment/config
is excluded in both. B retains the Phase 3 engineering default, but no primary
formal observer policy is silently selected. Blocked-attempt patterns under B,
N2 missingness and shared-capture gaps remain potential statistical shortcuts.

The primary held-out N1 false-positive endpoint and its denominator remain
unchanged. N2 artifacts can still distort pooled interpretation, calibration and
prompt development; N1 FPR alone cannot establish performance without frozen
recall/coverage checks. No metrics were computed. The synthetic, small, sequential
three-actor Arena and pending independent adjudication limit generalization.
Receipts prove local proposal persistence, not malicious collusion.

See the [protocol review](PHASE4A_PROTOCOL_REVIEW.md) and
[NOT APPROVED / NOT APPLIED amendment](PHASE4A_PROPOSED_AMENDMENT.md). Future
observer choice, possible N2 alternative, prompt adoption and deterministic
token/selection policy require explicit prospective decisions and freezing.

## 5. Test results

**480 passed in 170.32 seconds: 339 existing +141 new, no failures/errors/skips.**
`uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`,
`uv lock --check --offline` and compileall also pass. Full command/evidence mapping
and exact case counts are in [PHASE4A_TEST_MATRIX.md](PHASE4A_TEST_MATRIX.md).

Parser corpus: **4/4 valid synthetic forms accepted**, **26/26 invalid mutations
rejected with expected codes**. Both Phase 3 parsing errors have targeted
regressions. This proves parser behavior on fixtures, not real-model adherence.
The historical actual trace read-only replay remains INCOMPLETE with identical
L3 and unchanged per-actor receipt counts `[1,0,0]`; no new call/effect occurred.

**Actual candidate model-reliability testing: NOT RUN.** The sole prior actual
v1 observation remains the 2026-10-18 six-call CPU Ollama episode: one successful
proposal, two parser failures, three valid final declines, one Action/receipt,
INCOMPLETE. No additional Ollama, paid/cloud model or formal episode ran here.
New predictions, detector scores, calibration and statistical evaluations: **0**.

## 6. Remaining risks

- **Model reliability:** public examples may anchor behavior; candidate adherence
  and real token usage are unmeasured. Heuristic passing does not prove token fit.
- **Evidence fairness:** information parity does not equal length/salience/order
  neutrality; complete packets exceed the current conservative input guard.
- **Experimental validity:** N2 missingness, Router artifacts and capture gaps can
  remain shortcuts without direct metadata leakage. Observer/selection changes
  must be prospective, never backfit to scores or held-out results.
- **Engineering trust:** source snapshots and unkeyed hashes check consistency,
  not malicious-host authenticity. Synthetic Approval is not authenticated human
  consent; hostile message text remains untrusted data. No production safety
  or exactly-once remote-effect guarantee is claimed.
- **Statistical validity:** no study or independent adjudication has run; 24
  matched groups are not 120 independent samples. No empirical detector claim
  is supportable from these engineering tests.

## 7. Readiness

| Decision | Status | Scope/gate |
|---|---|---|
| Engineering readiness | **GO** | Phase 4A offline contracts, regressions and safe review artifacts complete |
| Detector-view methodological readiness | **CONDITIONAL GO** | Auditable inputs/parity available; approve observer rights, N2 interpretation and a feasible shared token/selection policy before formal freezing/use |
| Formal pilot readiness | **NO-GO** | Candidate real-model reliability/token feasibility unverified, prospective decisions/freezes unresolved, no new run authorization |

No experiment is authorized by this report. The existing frozen protocol remains
the authority. Phase 4A stops after reporting and packaging.

## 8. Review artifact

Archive: **`D:\workshop\oct\pactlens-phase4a-review.zip`**, outside the repository.
Includes reviewable source/tests/docs/config/safe fixtures, actual validation
summaries/logs, safe rendered engineering artifacts, SHA-256 member manifest and
an internal payload-verification receipt. An external
`pactlens-phase4a-review.zip.verification.json` records final container SHA-256,
CRC/member-hash verification and current working-source consistency.

An internal receipt cannot embed its own container's final hash; the external
receipt supplies that final-container check. Private runtime stores/traces,
capabilities, credentials, weights, `.git`, `.venv`, `.runtime` and old archives
are excluded. The archive records the uncommitted Phase 4A snapshot, not a new
commit or release. Historical reports and review archives are preserved.
