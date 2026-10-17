# PactLens — Phase 0 Validation Report

Date: **2026-10-17** (NZDT) · Scope: **Phase 0 only** (repository bootstrap,
runtime integration preflight, competition readiness, research-design
validation). No Phase 1+ work started; no experiments run; no commits, pushes,
tags, deployments, registrations, or external side effects performed.

## 0. Verdict

- **Overall status: PARTIAL** — all engineering preflight checks PASS; several
  competition-administration items (registration, PDF template, abstract limit,
  judging/disclosure rules) are UNVERIFIED from the authoritative page.
- **Decision: GO** — proceed to Phase 1 (arena pre-registration + deterministic
  environment). Engineering risk is low; the remaining items are user-side
  administrative actions and do not block implementation. If registration or
  submission later verifies as closed, the project continues as an independent
  (honestly disclosed, non-submitted) research artifact — see §8.

## 1. Files created / modified

Created:

- `pyproject.toml` — Python ≥3.13, name `pactlens`, pinned AIG Git dependency,
  dev group (ruff, pytest), hatchling build (`allow-direct-references = true`)
- `uv.lock` — 31 packages, reproducible (`uv lock --check --offline` PASS)
- `.python-version` — `3.13`
- `LICENSE` — MIT, "Copyright (c) 2026 PactLens contributors"
- `.gitignore` — venv/caches, `*.sqlite3`, `.runtime/`, `.env*` (keep
  `.env.example`)
- `.env.example` — no real keys
- `src/pactlens/__init__.py` — minimal package marker (docstring + `__version__`
  only; no speculative logic)
- `docs/HACKATHON_DESIGN.md` — exact copy of the root
  `PACTLENS_HACKATHON_DESIGN.md` (content preserved; root file kept, not
  removed)
- `docs/ARCHITECTURE.md` — consumer contract + verified API surface + feasibility
- `docs/EXPERIMENT_PLAN.md` — pre-registration draft, design validation findings
- `docs/PROVENANCE.md` — pre-sprint vs sprint work, baseline plan
- `docs/COMPETITION_REQUIREMENTS.md` — official requirements verification table

Modified:

- `AGENTS.md` — appended the "PactLens competition-specific invariants" section
  at the end; all upstream text preserved verbatim (nothing overwritten or
  weakened).

Per instruction, nothing was committed; the working tree is left dirty for user
review (`git status` shows `M AGENTS.md` + untracked new files).

## 2. Exact commands executed and actual outputs

```text
$ git status
On branch main
Untracked files: AGENTS.md  PACTLENS_HACKATHON_DESIGN.md
(initial state: only AGENTS.md, PACTLENS_HACKATHON_DESIGN.md, README.md tracked)

$ git ls-remote https://github.com/miku-wwl/agentic-intent-gate.git refs/tags/v0.2.0 'refs/tags/v0.2.0^{}'
b193d38a4804725d44ca536a3bd9778679cc7b4c	refs/tags/v0.2.0
7261fdd2f47d2b15fabe8faac527eeee37338eb1	refs/tags/v0.2.0^{}     <-- matches pinned commit

$ uv --version
uv 0.11.16 (135a36367 2026-05-21 x86_64-pc-windows-msvc)

$ python --version
Python 3.13.14

$ uv lock
Using CPython 3.13.14 interpreter
Resolved 31 packages in 4.08s

$ uv sync --locked          # first attempt
× Failed to build `pactlens`
  ValueError: Dependency #1 of field `project.dependencies` cannot be a direct
  reference unless field `tool.hatch.metadata.allow-direct-references` is set
  to `true`
  -> fixed by adding [tool.hatch.metadata] allow-direct-references = true

$ uv sync --locked          # after fix
Resolved 31 packages
Installed 31 packages, incl.
  agentic-intent-gate==0.2.0 (from git+https://github.com/miku-wwl/agentic-intent-gate.git@7261fdd2f47d2b15fabe8faac527eeee37338eb1)
  pactlens==0.0.0 (from file:///D:/workshop/oct/pactlens)
  ruff==0.17.1, pytest==9.1.1

$ uv lock --check --offline
Resolved 31 packages in 2ms        (exit 0 — lockfile up to date, offline-reproducible)

$ grep -c 7261fdd2f47d2b15fabe8faac527eeee37338eb1 uv.lock
2
(lockfile source line: git = "...?rev=7261fdd2f47d2b15fabe8faac527eeee37338eb1#7261fdd...")

$ uv run python -c "import importlib.metadata as md; ..."   # installed-package verification
version: 0.2.0
module_file: d:\workshop\oct\pactlens\.venv\Lib\site-packages\agentic_intent_gate\__init__.py
direct_url: {"url": "https://github.com/miku-wwl/agentic-intent-gate",
             "vcs_info": {"vcs": "git",
                          "commit_id": "7261fdd2f47d2b15fabe8faac527eeee37338eb1",
                          "requested_revision": "7261fdd2f47d2b15fabe8faac527eeee37338eb1"}}
runtime_file: d:\workshop\oct\pactlens\.venv\Lib\site-packages\agentic_intent_gate\runtime.py
runtime_all_count: 22
has_open_runtime: True

$ uv run python -c "... inspect.signature ..."   # public API surface
__all__ = ['ActionCommand','AdmissionCommand','ApprovalChoice','ApprovalDecisionRequest',
 'AttemptContext','AuthorizationPort','BoundCapabilityAuthorization','CapabilityVerifier',
 'EXTERNAL_PAYLOAD_REVISION','ExecutableRegistry','ExecutionSpec','Intent','ModelProvider',
 'Outcome','Runtime','ToolBinding','ToolCapability','ToolExecutor','ToolOutcome',
 'execution_budget_binding','open_runtime','provision_capability']
ToolBinding (tool_name: str, tool_version: str, adapter_id: str, binding_revision: str, target: str, execution_scope: str) -> None
ToolCapability (binding, description: str, input_schema: Mapping, target_argument: str | None = None, semantic_rule: Callable | None = None) -> None
ExecutableRegistry (executor=None, *, binding=None)
CapabilityVerifier (token=None, *, subject_id=None, binding=None, operations=())
BoundCapabilityAuthorization (verifier, *, policy_revision: str)
execution_budget_binding (binding, execution_timeout_seconds)
open_runtime (*, gate_path, provider, capability, registry, verifier, policy, predecessor_stopped=False, execution_timeout_seconds=5)
provision_capability (path)

$ uv run ruff check .        -> All checks passed!            (exit 0)
$ uv run ruff format --check -> 5 files already formatted     (exit 0)
$ uv run python -c "import pactlens; ..."
pactlens import OK 0.0.0 D:\workshop\oct\pactlens\src\pactlens\__init__.py

$ git check-ignore -v .venv artifacts/test.sqlite3 .runtime/x
.gitignore:10:.venv/	.venv
.gitignore:30:artifacts/**/*.sqlite3	artifacts/test.sqlite3
.gitignore:22:.runtime/	.runtime/x

$ ls -a | grep -E '^\.env$'   -> (no output; no .env file exists)
```

Upstream references read in full 2026-10-17: `docs/V0.2.0-CONSUMER-HANDOFF.md`,
`docs/ADAPTER_GUIDE.md` (v0.2.0), `examples/consumer/app.py`.

## 3. Dependency verification results

| Check | Result |
|---|---|
| uv available | PASS — 0.11.16 |
| Python 3.13 | PASS — 3.13.14 (`.python-version` = 3.13) |
| Tag `v0.2.0` peels to pinned commit | PASS — `7261fdd2…` |
| Installed version | PASS — `0.2.0` |
| Resolves to pinned commit | PASS — `direct_url.json` commit_id matches |
| Imported from installed env (not adjacent checkout) | PASS — `.venv/Lib/site-packages/...` |
| Public API importable / signatures inspected | PASS — 22 names in `runtime.__all__` |
| Lockfile reproducibility | PASS — `uv lock --check --offline` exit 0; commit pinned in `uv.lock` |
| Ruff check / format | PASS |
| Package import | PASS |
| Secrets / .gitignore hygiene | PASS — no `.env`; caches, venv, sqlite, runtime state ignored |
| Core unmodified | PASS — no source copy/fork/monkeypatch exists in this repo |

## 4. AIG integration constraints (verified, binding on Phase 2+)

1. One trusted `SIDE_EFFECT` tool per runtime composition; single-step Actions
   only — one isolated AIG instance per research agent.
2. No plugin discovery, MCP, multi-step or READ_ONLY dispatch — not available.
3. Plan schema: closed, flat, 1–16 required fields; no nested objects/arrays;
   canonical arguments ≤ 4 KiB — incident proposals must be encoded compactly.
4. Execution budget default 5 s; PactLens keeps the default (synthetic SQLite
   writes only). 15 s opt-in is a documented non-goal for the MVP.
5. Approval ≠ Authorization; exact Plan binding; durable claim required.
6. `Unknown` outcomes are terminal; no automatic retry or recovery replay.
7. Effect-key idempotency: same key+payload → original receipt; conflicts are
   confirmed failures, never overwritten.
8. Bundled demo LLM prompt/UI are `service-demo`-specific — PactLens supplies
   its own `ModelProvider` and admission path.
9. No production auth/HA, no malicious-Python isolation, no universal
   exactly-once remote guarantee.
10. Bundled HTTP Action routes keep a 10 s parent deadline; PactLens's
    consumer-owned envelope governs any request budgeting.

Full contract: `docs/ARCHITECTURE.md` §§2–3.

## 5. Competition eligibility & submission uncertainties

Verified 2026-10-17 from the official page: dates 2026-10-23→25 (online),
Track 2 and questions 2.2/2.3 verbatim, deadline 2026-10-25 23:59 AoE =
2026-10-27 00:59 NZDT, team size 1–5, prizes $2,000. **UNVERIFIED:** actual
registration confirmation, PDF report template, abstract word limit, judging
criteria, prior-work/AI-use disclosure rules, Resources starter code — see
`docs/COMPETITION_REQUIREMENTS.md` §2 for the exact rows and required actions.
No registration or submission was performed (by instruction).

## 6. Research validity risks (from `docs/EXPERIMENT_PLAN.md` §6)

Key risks and the required mitigations now recorded as binding for Phase 1:
instrumentation-gain confound (MAE sees strictly more than MA — add an
observability-controlled comparison); unstable recall operating point at small
n (predeclared fallback); C− must be re-labeled per run (not inherited);
multiple comparisons (single predeclared primary comparison); label leakage
(hidden-marker CI tests); model nondeterminism (cached calls, recorded IDs);
cherry-picking (frozen seeds, all runs exported incl. failures/`Unknown`);
causal overclaiming (only paired C−/C+ contrasts); legal overclaiming
(synthetic results only).

## 7. Outstanding blockers

- **User action:** register for the sprint and archive timestamped proof;
  obtain the official PDF template, abstract limit, judging criteria, and
  AI/prior-work rules from the organizers. (BLOCKED for submission
  preparation, not for Phase 1 engineering.)
- **User action:** review this Phase 0 tree and, if approved, authorize the
  `PRE_SPRINT_BASELINE` commit/tag plan (`docs/PROVENANCE.md` §3). Nothing was
  committed at Phase 0.
- Minor: only one unexpected build failure occurred and was fixed
  (`allow-direct-references`); no unresolved technical blockers.

## 8. Recommended Phase 1 scope (not started)

Research pre-registration + deterministic arena: freeze
`docs/EXPERIMENT_PLAN.md`; implement the seeded incident-allocation generator,
payoff equation, capacity constraints, deterministic allocator and outcome
evaluator; create 3 minimal synthetic cases proving that similar actions do not
by themselves yield a collusion label; tests for same-seed reproducibility,
condition controls, computable cooperative optimum, and rejection of invalid
proposals. Gate: an offline, leakage-free dataset before any monitor work.
Success/negative-result handling per `docs/EXPERIMENT_PLAN.md` §7.

**Phase 0 ends here. Phase 1 requires explicit user approval.**
