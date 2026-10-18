# PactLens Architecture — Consumer Contract and Feasibility

Current additive status: **Phase 4B, 2026-10-19 NZDT, pre-sprint engineering**.
Existing full Phase 4A projectors/renderers and engineering observer B remain
unchanged. Candidate budgeted input is an explicit additive path:

```text
allowed Inventory -> atomic fact bundles -> one common mandatory/optional selection
  -> lossless public constraint/allocation/payload/order tables
  -> M/A/MA/flat JSONL R/grouped JSON MAE -> independent semantic reconstruction
  -> complete system/task/evidence/output-schema envelope -> fit or typed failure
```

The selector has no L1/L2/score input. All six proposal slots, negative/missing/
Unknown integrity, failed permitted communication and source uncertainty remain.
Receipts stay with their Actions. Each optional bundle must fit both R/MAE and
the other views; cheaper MA receives no extra facts. Omitted facts and filtered
scope are explicit. The encoding is lossless; selection is a **PROPOSED lossy
policy**, not an approved formal observer configuration. Full source remains
available for independent L2 review.

`research/detector_contract.py` defines a complete bounded request and pure
finite-response validation only, with no provider or threshold. Freeze/readiness
modules hash unapproved candidates and mechanically retain NO-GO. Reviewer
preparation uses separate full packets/forms with labelled mechanical L2
comparators, no assignment/L4/peer judgments and no invented human review.

`agents/reliability.py` adds an explicit at-most-two local N3 comparison with an
exclusive 12-total/6-profile pre-dispatch ledger and fresh stores/contexts. The
existing harness gains only a trusted optional stop-on-input-budget flag, default
false; the comparison opts in. It made nine actual calls and stopped v2 on
preflight, leaving both episodes INCOMPLETE. No agent prompt/parser, condition,
Arena, AIG/store/receipt/bridge, pin or five-second budget changed.

No formal runner, detector inference/scoring/calibration, statistical pipeline
or Phase 4C is added. See [current report](PHASE4B_EXECUTION_REPORT.md) and
[candidate contract](PHASE4B_EVIDENCE_SELECTION_CONTRACT.md). Budget fit is
estimated and can fail; evidence sufficiency and research approvals remain gates.

The following Phase 4A status is retained as a historical snapshot; its statements
that no candidate selection exists are superseded by the additive path above.

Historical status: **Phase 4A, 2026-10-19 NZDT, pre-sprint engineering**.
The unchanged Phase 3 execution path remains available. The candidate protocol
is opt-in; `agents/budgets.py` and `agents/protocol_diagnostics.py` add bounded
preflight, versioned closed validation and diagnostic categories, while prompts
preserve the v1 system literal and add public-task examples/version hashes.
`experiments/traces.py` shares one 8,000,000-byte/131,072-byte/256-record contract
between Writer and Reader; rejected appends do not mutate accounting or files.

The evidence path is now:

```text
typed Arena + detached public AIG snapshots + host Router source observations
  -> observation_policy (delivered interception A or legitimate Router audit B)
  -> inventory (bounded allowlisted facts; opaque public IDs; source/trust/order)
  -> views (M / A / MA / R / MAE category selection)
  -> renderers (raw JSONL or grouped JSON + bound fact manifest + budget report)
  -> independent text reconstruction / parity checks
  -> fresh conversation only if token preflight fits (no provider/model call)
```

Private source audit is preserved, actors still see only delivered inboxes, and
detector rights are explicit. No label/config/oracle/credential reflection is
allowed. M/A/MA exclude privileged execution integrity; R/MAE contain identical
facts and missingness. Capture positions remain capture positions; unknown
cross-source order and receipt commit clocks are not invented. Integrity checks
establish consistency under the trusted host, not cryptographic authenticity.

The current full-inventory-or-overflow policy retains complete audit text but
refuses overflowing model inputs. Full engineering packets often exceed the
4,096-token estimate; no selection amendment or formal observer is selected.
No scoring model, formal-study executor, calibration or statistics is added.
Original Arena, bridge, AIG composition/store/receipt semantics and five-second
budget are preserved. See the [Phase 4A contract](PHASE4A_DETECTOR_VIEW_CONTRACT.md),
[report](PHASE4A_EXECUTION_REPORT.md) and [review](PHASE4A_PROTOCOL_REVIEW.md).

The following Phase 3 status is retained as a historical snapshot; its statement
that input views are absent is superseded above.

Historical status: **Phase 3 controlled harness, 2026-10-18 NZDT,
pre-sprint engineering**. `agents/` owns independent immutable actor contexts,
strict decisions, provider-neutral requests and a local-only Ollama adapter.
`experiments/` owns engineering condition/seed contracts, controlled routing,
sequential current-revision scheduling, append-only traces and pure replay.
`aig/submission.py` composes the existing Phase 2 consumer public interfaces for
each proposal; original AIG, executor/store, bridge and Arena mechanics are
unchanged. `evidence/harness_adapter.py` extends the allowlisted Observation v2
inventory with router delivery facts and completeness/order. No detector views
or formal-study executor exists. See [current contract](PHASE3_HARNESS_CONTRACT.md),
[execution report](PHASE3_EXECUTION_REPORT.md) and [tests](PHASE3_TEST_MATRIX.md).

L1 request/response/assignment trace records and L2 comparative mechanics remain
private; L3 exports are constructed separately and retain source-local or shared
capture uncertainty. Pure replay validates historical facts and original pure
Arena transitions with zero new model/Gateway/effect operations. Local generation
and scripted synthetic consent do not establish human consent, collusion truth
or reproducibility of fresh inference. All work is pre-existing for the sprint.

The following Phase 2 description is retained as the historical baseline;
its statements that the Phase 3 engineering runner is absent are superseded.

Status: **Phase 2 pre-sprint local AIG integration, 2026-10-18 NZDT**. The installed
AIG 0.2.0 pin/public API was re-inspected. The fixed synthetic-proposal consumer,
durable local effects/receipts, real Run/Approval/Authorization/Gateway path,
three isolated compositions, Arena replay and AIG evidence adapter now exist.
Planning and consent are deterministic engineering stand-ins. No model inference,
formal study, detector, production login or interactive approval UI exists.
Current contract: [PHASE2_INTEGRATION_CONTRACT.md](PHASE2_INTEGRATION_CONTRACT.md);
actual results: [PHASE2_EXECUTION_REPORT.md](PHASE2_EXECUTION_REPORT.md).
Concrete mechanics: [DATA_DICTIONARY.md](DATA_DICTIONARY.md); evidence and checks:
[PHASE1_EXECUTION_REPORT.md](PHASE1_EXECUTION_REPORT.md) (historical) and
[PHASE1_1_EXECUTION_REPORT.md](PHASE1_1_EXECUTION_REPORT.md) (current hardening).

Phase 1.1 keeps the frozen allocation policy. Primitive domain values now live
in internal `arena/_domain.py` and remain reexported through `arena.models`.
The acyclic dependency direction is `models → allocation → _domain`; allocation
does not import state or construct one. State construction reuses the existing
executor to verify accepted round-2 ballots against final allocation. Transition
entry, source-envelope construction and projection recheck consistency; complete
stored mechanics are compared with canonical evaluation. No restoration/store
API, AIG adapter or execution framework is introduced.

The source envelope optionally carries a small logical capture journal. Its
unkeyed fact digests bind observed content to recorded positions; projection
exports only explicit public fields and neutral aliases, never these digests.
Observation v2 adds `events`/`event_ordering` while retaining existing observation
fields. Recorded, partial and source-local-only chronology are distinct. Legacy
data cannot acquire an invented global ordering. Finalization atomically records
round-2 close and allocation; public outcome remains deterministic accounting.
See the [event contract](DATA_DICTIONARY.md#phase-11-observable-event-ordering-contract).

Mechanical validation and journal consistency are not authenticated history.
A malicious host can rewrite observations and matching digests or remove capture
metadata. No cryptographic authenticity, durable evidence log or protection from
arbitrary in-process Python is claimed. Future matched R/MAE views must consume
the same available observations and ordering uncertainty; neither exists yet.

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

## 5. Planned PactLens components (Phase 0 assessment, with Phase 2 status)

Phase 1 implements component 1. Phase 2 implements the fixed consumer adapter in
component 4 and bounded receipt/evidence subset of component 5. Three isolated
runtime compositions are exercised by a six-submission engineering harness;
this is not component 2's research driver or component 3's model-driven runners.
Components 2–3 and 6–9 remain unimplemented. Gate transactions and consumer
proposal transactions remain separate. Conflicting cross-store Arena base
revisions stop reconstruction; there is no distributed Arena serialization.

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
