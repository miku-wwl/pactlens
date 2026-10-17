# PactLens Architecture — Consumer Contract and Feasibility

Status: **Phase 1 pre-sprint arena implemented, 2026-10-18 NZDT**. The installed
AIG 0.2.0 pin/public API was re-inspected; the integration contract below remains
the Phase 0 reference, not an implemented adapter. Arena mechanics, private
manifest/adjudication contracts and allowlisted observation projection now exist.
No AIG dispatch, providers, monitors or research study has been implemented/run.
Concrete mechanics: [DATA_DICTIONARY.md](DATA_DICTIONARY.md); evidence and checks:
[PHASE1_EXECUTION_REPORT.md](PHASE1_EXECUTION_REPORT.md).

## 1. Position: independent consumer, not a fork

PactLens is an independent application that consumes the shared **Agentic Intent
Gate (AIG)** Python runtime through its published public API only. PactLens must
not copy, fork, reimplement, monkeypatch, or bypass AIG's approval,
authorization, execution, ledger, or receipt mechanisms.

- Upstream: https://github.com/miku-wwl/agentic-intent-gate
- Release: annotated tag `v0.2.0` → peeled commit
  `7261fdd2f47d2b15fabe8faac527eeee37338eb1` (verified 2026-10-17 via
  `git ls-remote`).
- Public integration module: `agentic_intent_gate.runtime` (never the package
  root).

## 2. Verified public API surface (from the installed package, not docs alone)

Inspected 2026-10-17 with `inspect.signature` on the installed distribution:

| Symbol | Verified signature (abridged) |
|---|---|
| `ToolBinding` | `(tool_name: str, tool_version: str, adapter_id: str, binding_revision: str, target: str, execution_scope: str)` |
| `ToolCapability` | `(binding, description: str, input_schema: Mapping, target_argument: str \| None = None, semantic_rule: Callable \| None = None)` |
| `ExecutableRegistry` | `(executor=None, *, binding=None)` |
| `CapabilityVerifier` | `(token=None, *, subject_id=None, binding=None, operations=())` |
| `BoundCapabilityAuthorization` | `(verifier, *, policy_revision: str)` |
| `execution_budget_binding` | `(binding, execution_timeout_seconds)` |
| `open_runtime` | `(*, gate_path, provider, capability, registry, verifier, policy, predecessor_stopped=False, execution_timeout_seconds=5)` |
| `provision_capability` | `(path)` |

`agentic_intent_gate.runtime.__all__` (22 names, verified): `ActionCommand`,
`AdmissionCommand`, `ApprovalChoice`, `ApprovalDecisionRequest`,
`AttemptContext`, `AuthorizationPort`, `BoundCapabilityAuthorization`,
`CapabilityVerifier`, `EXTERNAL_PAYLOAD_REVISION`, `ExecutableRegistry`,
`ExecutionSpec`, `Intent`, `ModelProvider`, `Outcome`, `Runtime`,
`ToolBinding`, `ToolCapability`, `ToolExecutor`, `ToolOutcome`,
`execution_budget_binding`, `open_runtime`, `provision_capability`.

The reference consumer pattern (`examples/consumer/app.py` upstream, read
2026-10-17) provisions a private directory containing an `identity.json`
binding, a capability token, and a consumer-owned SQLite effect store; `open_runtime`
is then called with a trusted `ModelProvider`, one `ToolCapability` (closed,
flat schema), one `ExecutableRegistry` + `ToolExecutor`, a `CapabilityVerifier`,
and a `BoundCapabilityAuthorization` policy. The workflow is
`create Run → Approval → Admission → Authorization → execute → verify receipt`.

Constructor arguments are taken from this installed-version inspection; no
method or parameter has been assumed beyond it.

## 3. Hard constraints inherited from AIG v0.2.0

These are verified upstream constraints, not PactLens choices:

1. **One trusted `SIDE_EFFECT` tool per Runtime composition**; single-step
   Actions only. No multi-tool or multi-step orchestration.
2. **No plugin discovery, no generic MCP execution, no READ_ONLY dispatch.**
3. **Strict closed Plan schema**: 1–16 required flat fields, no nested
   objects/arrays, no defaults; strings bounded 1–1024 chars; canonical
   arguments ≤ 4 KiB.
4. **Trusted configurable execution budget**: default 5 s; values in `(0, 15]`
   accepted; >5 s requires a fresh reviewed binding via
   `execution_budget_binding` (canonical `.exec-15s` revision), a fresh UUIDv4
   scope, and separate ledger/store identity. PactLens uses the **5 s default**
   (synthetic SQLite writes are fast); 15 s is a documented non-goal for the MVP.
5. **Human Approval ≠ execution Authorization**; approval binds the exact Plan.
6. **Fail-closed**: timeout / lost ack / uncertain commit → `Unknown`; **no
   automatic retry, no recovery replay**; recovery without executor calls.
7. **Idempotency**: stable UUIDv4 effect key; same key + same payload → original
   receipt; same key + different payload → `PAYLOAD_CONFLICT`; wrong store
   identity → `STORE_IDENTITY_MISMATCH`.
8. The bundled local LLM provider and browser UI are demo-specific
   (`service-demo`); a non-demo consumer supplies its own `ModelProvider` and
   admission path.
9. No production multi-user authentication, no distributed HA, no malicious-
   Python isolation, **no universal remote exactly-once guarantee**.
10. Consumer-side constraints (sandbox targets, budgets, secrets, spend limits)
    live in the PactLens application, not the runtime.

## 4. Three planes

```
 Experiment Plane (PactLens-owned; research orchestration, no production rights)
   scenario/seed/role/condition randomization, message channels, model calls
        |                    |                    |
   Agent A               Agent B               Agent C
   own policy            own policy            own policy
   own AIG instance      own AIG instance      own AIG instance
   isolated scope        1 trusted tool        1 SIDE_EFFECT step
        |                    |                    |
   per-agent synthetic proposal → SQLite effect/receipt store (consumer-owned)
        \___________________|___________________/
                            |
              Synthetic Allocation Judge (deterministic outcomes)
                            |
            Versioned Evidence Exporter (messages | plans | actions | receipts | outcomes)
                            |
        Future Monitor Views: M, A, MA, R, MAE (not implemented)
                            |
        Frozen detectors & thresholds → metrics, CIs, case-study report
```

1. **Experiment Plane** — PactLens research orchestrator. Owns randomization,
   controlled private messaging, condition assignment, and measurement. Research
   metadata (condition, seed, assigned coalition, ground truth) is **never**
   passed to any detector.
2. **Execution Plane** — one isolated AIG runtime composition per agent, each
   registering exactly one trusted `SIDE_EFFECT` tool (planned name
   `submit_incident_proposal/1`, target `incident-sim`, adapter
   `pactlens-sqlite-v1`, revision fixed, fresh persisted UUIDv4 scope), whose
   only effect is appending one proposal row to a consumer-owned SQLite store
   keyed by AIG's stable effect key with a durable UUID receipt.
3. **Audit/Research Plane** — builds a common `EvidenceRecord` schema from
   (a) research-owned message logs and (b) AIG's durable, verifiable Action
   records (approval status, action state, payload digest, receipt
   reference). The two sources have **different trust levels** and must be
   labelled as such; AIG's private SQLite tables are never read directly at
   runtime — only through public interfaces / documented exports.

## 5. Planned PactLens components (Phase 0 assessment, with Phase 1 status)

Phase 1 implements component 1 and the arena-only record/projection subset of
component 5. It has no AIG-backed evidence collector, receipts or Runtime calls.
Components 2–4 and 6–9 remain unimplemented.

| # | Component | AIG reuse | Feasibility (Phase 0 assessment) |
|---|---|---|---|
| 1 | Synthetic Incident Allocation Arena | none (PactLens-owned, fully offline) | Feasible; deterministic seeded generator; no external effects |
| 2 | Research Experiment Driver | none | Feasible; external orchestration is a PactLens responsibility |
| 3 | Independent Agent Runners | one isolated composition each | Feasible within the single-tool/single-step constraint; multi-agent orchestration stays outside AIG |
| 4 | Thin AIG Consumer Adapter | `open_runtime` + public API | Feasible; reference pattern verified; needs own `ModelProvider` (bundled demo prompt is service-specific) |
| 5 | Evidence Collector | Action outcomes/receipts via public API | Feasible; must respect trust distinction and 4 KiB argument schema |
| 6 | Collusion Detection Monitors | none | Feasible; pure research code over leak-safe views |
| 7 | Evaluation Pipeline | none | Feasible; frozen splits, metrics, intervals |
| 8 | Research Reporting Tools | none | Feasible; figures derive only from finalized artifacts |
| 9 | Optional read-only dashboard | none | Deferred; explicitly out of Phase 0/1 scope |

## 6. Deliberate non-goals (guard against scope creep)

No general-purpose agent framework; no modification/fork of AIG; no real issue
tracker or third-party mutation; no plugin/MCP marketplace; no deployment; no
claimed statistical results before a frozen evaluation exists.

## 7. Acceptance gate for Phase 2 integration (recorded now, enforced later)

An external consumer using the pinned **installed** package, without modifying
core source, must demonstrate:
**validated Plan → persistent Run → exact human Approval → Admission →
independent Authorization → durable Action claim → consumer executor →
verified effect → durable receipt**, plus negative tests (wrong
binding/target/scope, missing authorization, stale approval, duplicate/
conflicting effects, concurrent attempts, ambiguous outcome, restart with no
second effect). In offline research runs, scripted consent must be explicitly
labelled `synthetic_consent=true` and never described as authenticated human
consent.
