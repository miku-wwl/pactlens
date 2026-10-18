# Phase 4B — Candidate Evidence Selection and Request Contract

Date: **2026-10-19 NZDT; pre-sprint engineering / pre-existing work**.
Status: **PROPOSED, NOT APPROVED FOR FORMAL USE**. The frozen
[Phase 0.6 protocol](EXPERIMENT_PLAN.md) remains authoritative. Full Phase 4A
renderers and the engineering Router-audit default are unchanged.

## 1. Public boundary and atomic bundles

`fact_bundles` accepts only the existing typed, validated `Inventory`, not an
EpisodeRecord, private trace, oracle, adjudication, score or condition. All facts
are partitioned into atomic groups; selection never splits a fact's identity,
payload, provenance, completeness or known/unknown ordering.

- Each public task, source-coverage record, proposal slot, execution snapshot and
  Arena event is a bundle.
- Each actor/round Action and its correlated receipt are one indivisible bundle.
  Their Action ID, round and payload/proposal digests must agree. Verified receipt
  without the corresponding Action identity fails. Unknown with a committed
  receipt stays Unknown.
- Delivered speech and matching permitted Router delivery facts stay together.
  Identical ambiguous communications form a complete equivalence group, preserving
  every original fact ID and ordering value. They are not coalesced into one
  occurrence or assigned an invented one-to-one chronology.
- Blocked/failed Router attempts remain separate observed events under B. Under
  A they were never permitted detector observations; selection does not censor
  them after projection.

The mandatory core retains the full public task, both coverage records, all six
actor/round proposal slots, actual/pending execution, observed round boundaries,
all missing/non-success Action/receipt bundles, all blocked/failed Router events,
the first speech from at least two observed senders when available, and at least
one successful Action/receipt bundle when available. A single observed sender is
not fabricated into two; no available speech stays explicitly unavailable.

MISSING, PENDING, NOT_REACHED, Failed and Unknown retain their actual meanings.
An unobserved Action cannot be labelled a decline. Explicit model declines are
recorded by the private harness and engineering summary, without inventing that
reason for every absent L3 Action slot.

## 2. Deterministic candidate selection

Version: `pactlens-common-bundles-v1-candidate`.
Canonical base configuration SHA-256:
`ca0006424a181f7f96554eef167c8142267ea012fbcea816f8a158f0346e7032`.
The episode-independent profile hash additionally binds the complete envelope.
The review ZIP's file manifest binds the concrete implementation snapshot.

Mandatory bundles are considered first. Optional priority is:

1. Successful integrity bundles, round descending then neutral public actor.
2. Communication bundles, public round/source sequence/actor.
3. Arena events, public round/source sequence.

Public bundle key breaks remaining ties. No condition, private seed/group,
assigned coalition, oracle, adjudication or model prediction selects facts.
Source iteration order does not determine the result. A trusted exact counter,
if later supplied, must be part of the prospectively reviewed provider profile.

The selector first renders the mandatory set into all five complete requests.
If any cannot fit, it returns typed `SelectionFailure(INPUT_BUDGET_EXCEEDED)`
with mandatory IDs and per-view budget diagnostics. It does not return an empty
or incomplete mandatory core as success. Each optional bundle is then tentatively
added to **one common selected set**; it is retained only if both R and MAE, and
the other three requests, fit. A rejected bundle is excluded from both matched
presentations. Later smaller bundles may fit under the same declared priority.
There is no model call, scoring, outcome-based retry or context expansion.

This is a lossy selection candidate even though its encoding is lossless. It is
implemented only for engineering review; approval and freezing are still required.

## 3. Lossless compact representation

Version: `pactlens-lossless-public-tables-v1`. The original full fact records can
be independently reconstructed from the actual rendered text:

- Public agents and incidents use explicitly named column tables, retaining all
  capabilities, capacities, eligibility, costs and objective parameters.
- Allocation rows use declared neutral numeric aliases: n means Incident-n or
  Actor-n; null owner means unassigned. Every alias reconstructs exactly.
- Repeated payloads and ordering tuples use explicit lookup tables. Fact rows
  label their payload_index and ordering_index. Indices are lookups, not clocks.
- Kind metadata has explicitly labelled category/source/trust columns. Original
  fact UUIDs, payload values, nulls and completeness remain intact.

This removes repeated syntax, not facts. Tests compare reconstructed records
against originals. Unknown source order remains unknown; receipt capture does
not acquire a SQL commit sequence or timestamp.

R is **flat JSONL with readable legends and lookup tables**. MAE groups the same
fact rows by category, ordered by actor/kind. Both already contain structured
data. The prospective contrast is **grouped structured presentation versus flat
JSONL presentation of matched evidence**, not a universal structured/unstructured
benefit. No padding, deliberate raw-control degradation, inferred summaries,
agreement labels or additional MAE facts are added.

## 4. Cross-view and omission contract

| Fact family | M | A | MA | R | MAE |
|---|---|---|---|---|---|
| Common public task | Yes | Yes | Yes | Yes | Yes |
| Permitted communications/coverage | Yes | No | Yes | Yes | Yes |
| Router facts under B only | Yes | No | Yes | Yes | Yes |
| Selected proposal/Arena/public outcome facts | No | Yes | Yes | Yes | Yes |
| Selected Action/receipt/integrity coverage | No | No | No | Yes | Yes |
| Included fact provenance/missingness/order | Yes | Yes | Yes | Yes | Yes |
| L1 assignment/L2 truth | No | No | No | No | No |

All views derive from the same selected inventory: MA=M∪A; MA⊆R; R=MAE as
semantic fact sets. Cheaper M/A/MA rendering does not receive extra facts omitted
from R. Per-view omission manifests expose only that view's eligible categories;
M/A/MA do not receive privileged integrity counts/IDs through omission metadata.

Full retained/omitted fact and bundle manifests are auditable sidecars, not extra
model evidence. Input text declares per-category omissions and either
FULL_ELIGIBLE_SOURCE or SELECTED_SUBSET_NOT_COMPLETE_SOURCE. Original source
coverage remains a source fact; it never means the filtered packet is complete.
Independently parsed flat/grouped text, complete values/nulls, metadata, omission
lists and mandatory identities are compared by `verify_budgeted_parity`.
Manifests/hash checks detect inconsistency, not a hostile host rewriting history.

## 5. Complete request accounting and failure

`DetectorEnvelope` includes system instructions, evidence task, complete evidence
text, output instructions and the required JSON response schema in three fresh
immutable turns. Its hash is
`4514c3d752300b690dbb1b1f6f9eff37d27c70af57b7099fd338f75799f5c53d`.
The input cap is 4,096 and output reservation is 256. If a provider context window
is specified, available input is `min(4096, window-reserved_output)`; output is
not silently subtracted from the separate protocol input cap. An eventual model
must support the complete combined envelope/window requirement.

The current fallback estimates
`ceil(UTF8(role+content)/2)+32*turn_count+128`. It is an English-oriented engineering
safeguard, **not an exact measurement or mathematical upper bound**. Exact token
fields remain null in this phase's detector audit. A trusted counter must include
the provider's actual chat-template overhead, not evidence text alone. Synthetic
counter tests are not real tokenizer qualification.

Reports preserve bytes, estimate/exact count, method, available input, reserved
output, selected/omitted counts, mandatory IDs and per-category omissions.
Conversation creation rechecks the complete request and rejects overflow. No
detector inference is implemented. Future overflow, parse error, provider error
or missing prediction remains abstention under the frozen policy, with the
failure preserved; no selected rerun or automatic shorter prompt is allowed.

## 6. Scientific limits and approval gate

All 28 hand-scripted fixture/policy sets fit the heuristic guard. The six-receipt
synthetic example also fits after selection, but retains only 2/6 successful
integrity pairs under A and 1/6 under B; speech is also reduced. These packets are
**insufficient for a complete episode-wide agreement/lifecycle audit**. They are
auditable subsets, not proof that the intended detector comparison is adequate.

One actual v1 Router-audit mandatory core still overflows; it is retained as a
failure. No failure/blocked evidence was removed to make it fit. Longer speech,
different tasks/tokenizers or additional metadata can also overflow. Budget
abstention may correlate with condition, observer policy or communication volume;
future coverage must be reported, not rescued by dropping cases. See the
[measurements](PHASE4B_TOKEN_BUDGET_REPORT.md) and
[freeze decisions](PHASE4B_PROTOCOL_FREEZE_CANDIDATES.md).
