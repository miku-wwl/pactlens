# Phase 4C — Episode-Level Evidence Sufficiency Report

**2026-10-20 NZDT; pre-sprint engineering. No detector inference, prediction,
threshold or score.** Detector token figures are the existing conservative estimate
over the complete request envelope (system, task, evidence, output instructions and
response schema; 4,096 input / 256 reserved output). Exact counts are null.

## 1. Lossless representation first (4C.4)

`pactlens-lossless-public-tables-v2-candidate` changes presentation only:

| Change | Why it is lossless |
|---|---|
| Rows cite the public UUIDv5 *name* (`action/Actor-1/2`) instead of the UUID | `fact_id = UUIDv5(episode, key)` is recomputed exactly; the key is verified on encode and decode |
| Kind from key prefix (one legend) | Bijective prefix map; category/source/trust still listed per kind |
| Repeated long values (UUIDs, digests, repeated text, objects) listed once, cited `{"@": n}` | Values stored literally; references resolved before Fact validation |
| Allocations as owner vectors | Only when rows are exactly `Incident-1..n` in order; otherwise encoding fails |
| Action/receipt streams `[prefix, n]` | Prefix + listed Action ID equals the original stream string |
| Cross-source order codes R/U/N | Explicit legend; Fact invariants still reject invented order |

Decoding parses only the rendered text, rebuilds complete `Fact` records (values,
nulls, source, trust, completeness, ordering) and then requires the text to
re-render **byte-identically** from those facts, so non-canonical legends,
references, row order or whitespace are rejected. Detector citations use keys; the
host resolves them to canonical fact UUIDs and rejects unobserved citations.
Phase 4A/4B renderers and the Phase 4B selector are unchanged and still available.

Complete (unselected) packets, evidence bytes / estimated complete-request tokens,
v1 tables → v2 tables:

| Source | Policy | Facts | R | MAE | MA |
|---|---|---:|---|---|---|
| Six-receipt synthetic (4A) | A | 38 | 11,373 / 6,364 → 8,880 / 5,117 | 11,454 / 6,404 → 8,961 / 5,158 | 6,143 / 3,749 → 5,273 / 3,314 |
| Six-receipt synthetic (4A) | B | 44 | 13,113 / 7,234 → 10,294 / 5,824 | 13,194 / 7,274 → 10,375 / 5,865 | 7,883 / 4,619 → 6,687 / 4,021 |
| Local v1 trace (4B, 2 receipts) | A | 30 | 8,165 / 4,760 → 7,071 / 4,213 | 8,246 / 4,800 → 7,152 / 4,253 | 5,063 / 3,209 → 4,456 / 2,905 |
| Local v1 trace (4B, 2 receipts) | B | 35 | 9,821 / 5,588 → 8,343 / 4,849 | 9,902 / 5,628 → 8,424 / 4,889 | 6,726 / 4,040 → 5,728 / 3,541 |
| Local v2 trace (4B, 3 receipts) | A | 27 | 7,259 / 4,307 → 6,349 / **3,852** | 7,340 / 4,347 → 6,430 / **3,892** | 3,638 / 2,496 → 3,491 / 2,423 |
| Fixture `c_plus` | A | 34 | 7,510 / 4,432 → 6,996 / 4,175 | 7,591 / 4,473 → 7,077 / 4,216 | 5,601 / 3,478 → 4,869 / 3,112 |

The reduction is largest where Action/receipt identifiers repeat (about 20% of
estimated tokens for six actions) and smallest for scripted fixtures without AIG
identifiers. MAE remains slightly larger than R (grouping syntax), as in Phase 4B.

## 2. Complete-or-infeasible and common selection (4C.4–4C.5)

- `select_complete`: all eligible facts in all five views, or a typed
  `EVIDENCE_BUDGET_INFEASIBLE` with a measured bottleneck. No selection, retry or
  context expansion.
- `select_common`: the Phase 4B mandatory core, priority and common-fit rule,
  unchanged except for v2 tables, so differences are attributable to representation.

All five views derive from one validated inventory and one retained set.
`M ∪ A = MA`, `MA ⊆ R` and `canonical_facts(R) = canonical_facts(MAE)` are checked
from facts parsed out of each actual text; MAE never receives extra facts and R is
never selectively truncated. The complete request envelope is budgeted, and
`conversation()` refuses an overflowing request.

Audit of **54 source/policy sets** (14 scripted fixtures, three read-only historical
traces and ten new fake-transcript real-AIG condition episodes, each under A and B;
`evidence-audit.json`). Classes of the common retained set:

| Outcome | Phase 4B rules, v1 tables | Same rules, v2 tables | Complete-or-infeasible |
|---|---:|---:|---:|
| `COMPLETE_EPISODE_EVIDENCE` | 4 | 18 | 18 fit |
| `LIFECYCLE_AND_COMMUNICATION_COMPLETE` | 24 | 12 | — |
| `LIFECYCLE_INCOMPLETE` | 25 | 23 | — |
| Typed failure | 1 mandatory overflow | 1 mandatory overflow | 36 `EVIDENCE_BUDGET_INFEASIBLE` |

The single mandatory-core overflow is the actual Phase 4B v1 trace under B (blocked
attempts plus missing execution are mandatory); it remains a preserved failure.
All fitting packets passed independent text reconstruction, byte re-render and
R/MAE parity; all mandatory and negative facts were retained.

Six-action sources (integrity pairs and communication retained/source facts):

| Source | Policy | v1 tables pairs · comm | v2 tables pairs · comm | Complete needs (est.) | Lifecycle core alone |
|---|---|---|---|---:|---:|
| Six-receipt synthetic | A | 4/12 · 3/6 | **8/12** · 2/6 | 5,117 | 4,266 |
| Six-receipt synthetic | B | 2/12 · 4/12 | **4/12** · 6/12 | 5,824 | 4,261 |
| Condition run C+ (pair speech) | A | 4/12 · 3/4 | 8/12 · 2/4 | 5,002 | 4,267 |
| Condition run C+ (pair speech) | B | 2/12 · 4/8 | 4/12 · 6/8 | 5,491 | 4,262 |
| Condition run N1/N3 (silent) | A or B | 6/12 · 0/0 | 10/12 · 0/0 | 4,624–4,629 | 4,261–4,266 |
| Condition run C− (blocked) | A | 6/12 · 0/0 | 10/12 · 0/0 | 4,630 | 4,267 |
| Condition run C− (blocked) | B | 2/12 · 4/4 | 6/12 · 4/4 | 5,127 | 4,262 |
| Condition run N2 (3 Actions) | A | 8/12 · 3/4 | 10/12 · 4/4 | 4,473 | **3,898** |

No six-action source fits completely, under either policy or either table version.

## 3. Bottleneck for the six-action engineering source

Measured attribution of the complete R request for the six-receipt source under A
(`EVIDENCE_BUDGET_INFEASIBLE`: 5,117 estimated against 4,096, overflow 1,021):

| Part | Bytes |
|---|---:|
| Fixed detector envelope (system, task, output, response schema, labels) | 906 |
| Header legends (row/order/kind/payload/task columns, codes, identity, scope) | 2,743 |
| Value table (6 Action UUIDs, 12 digests, shared objects) | 1,268 |
| Rows: Action/receipt pairs (12) | 1,820 |
| Rows: messages (6) | 791 |
| Rows: Arena events beyond round boundaries (7) | 732 |
| Rows: public task, coverage, execution | 601 |
| Rows: proposal slots (6) | 594 |
| Rows: round boundaries (3) | 331 |

Diagnostic subsets (estimates only; not selected packets or policies): lifecycle
core alone 4,266; lifecycle core plus all communication 4,754; all except Arena
event copies 4,754; all except communication 4,637. Under B the communication rows
grow to 1,892 bytes (message plus Router audit facts) and the complete request to
5,824. The usable evidence allowance after the fixed envelope is 6,838 bytes.

The bottleneck is therefore structural: per-kind legends that must make source,
trust and payload columns reconstructable from the text, irreducible 64-hex digests
and UUIDs (about 1.3 KB), and twelve integrity facts. Even with zero communication
the six-action lifecycle core exceeds the estimate by about 170 tokens. Remaining
lossless options (derived actor and order columns, merged legends) would save about
240 estimated tokens at a readability cost, enough for the core alone but not for
complete evidence. Message volume makes the gap larger; budget failures therefore
also depend on observer rights and speech.

## 4. Scientific sufficiency assessment (4C.6)

`assess` reports mechanical public coverage, never detector adequacy or truth.

| Question | Requirement in the packet |
|---|---|
| Messages and agreement | every source communication fact retained (or none observed) |
| Proposal and execution observability | all six proposal slots and all six Action/receipt pairs |
| Talk-only versus executed | both of the above |
| Missing vs Failed vs Unknown | every MISSING/PENDING/NOT_REACHED/INCOMPLETE fact, non-success Action and non-delivered Router event retained with its value |
| Final allocation and public costs | execution fact retained |
| Action/receipt correlation | pairs never split (atomic bundles) |
| Observer rights | declared policy A or B |
| Timing uncertainty | retained versus source facts with recorded capture positions |

Classes: `COMPLETE_EPISODE_EVIDENCE` (sufficient mechanical coverage);
`LIFECYCLE_AND_COMMUNICATION_COMPLETE` (conditional: only Arena event copies and
their capture positions omitted); `LIFECYCLE_COMPLETE_COMMUNICATION_PARTIAL` and
`LIFECYCLE_INCOMPLETE` (insufficient for an episode-level audit).

**Condition dependence through observable behavior (`condition-selection-analysis.json`).**
The selector has no label input (signature test) and gives identical results for
identical observable inventories with injected private markers. Ten new fake-
transcript episodes through real AIG (same task, lawful ballots, synthetic consent)
show how behavior, not labels, moves the selection (v2 tables, 4B rules):

| Behavior | Condition | Policy | Facts | Integrity pairs | Communication | Complete needs |
|---|---|---|---:|---|---|---:|
| Identical public messages | C+, N1, N3, C− | A | 38 | 8/12 | 2/6 | 5,116–5,118 |
| Identical public messages | C+, N1, N3, C− | B | 44 | 4/12 | 6/12 | 5,823–5,825 |
| Identical public messages | N2 | A | 35 | 10/12 | 4/6 | 4,589 |
| Brief-shaped pair speech | C+ (delivered) | A | 36 | 8/12 | 2/4 | 5,002 |
| Brief-shaped pair speech | C+ (delivered) | B | 40 | 4/12 | 6/8 | 5,491 |
| Brief-shaped pair speech | C− (blocked) | A | 32 | 10/12 | 0/0 | 4,630 |
| Brief-shaped pair speech | C− (blocked) | B | 36 | 6/12 | 4/4 | 5,127 |
| Brief-shaped pair speech | N1, N3 (silent) | A/B | 32 | 10/12 | 0/0 | 4,624–4,629 |
| Brief-shaped pair speech | N2 (round 2 blocked) | A | 33 | 10/12 | 4/4 | 4,473 |

Identical behavior yields identical packets across C+/N1/N3/C−. When behavior
follows the briefs, packet composition differs: more speech (C+) displaces
integrity evidence; under A, C−'s blocked attempts are invisible and C− looks like
silent N1/N3; under B they are mandatory audit facts and displace half of the
integrity pairs; N2's blocked final Actions are mandatory but compact. These are
legitimate observable differences, yet they make evidence loss **differential
across arms** (the positive-control arm loses the most lifecycle evidence) and can
act as statistical shortcuts (omission counts, missing slots, audit rows). They
must enter coverage and abstention reporting by condition; they must not be
"corrected" by condition-aware selection.

## 5. Conclusions

1. **Lossless representation improved** packet size by about 20% of estimated tokens
   for six-action sources, with independent text reconstruction, byte re-render,
   key-based citations and R/MAE parity. Under unchanged Phase 4B rules, retained
   integrity pairs roughly double (2/6 → 4/6 under A; 1/6 → 2/6 under B), and 16 of
   28 fixture sets plus the 3-receipt local trace now fit completely.
2. **Complete six-action evidence is `EVIDENCE_BUDGET_INFEASIBLE`** for every
   six-action source, both policies, both table versions (5,002–5,825 estimated
   against 4,096). Even the lifecycle core alone exceeds the estimate by about 170
   tokens; only episodes with missing Actions (N2) fit the core.
3. Fitting selected packets are **insufficient for an episode-level audit**
   (`LIFECYCLE_INCOMPLETE`): they omit successful Action/receipt pairs and/or
   communication. They are labelled as such, never as complete.
4. Selection differences across conditions arise from observable behavior and
   observer rights, but evidence loss is differential across arms.

**Detector evidence sufficiency: NO-GO** for complete episode-level auditing under
the current 4,096-token estimate and envelope. Lifecycle-only or communication-only
auditing of six-action episodes, a cap or estimator change, a split-packet design
or lossy evidence are prospective research decisions (see the
[freeze candidates](PHASE4C_FREEZE_CANDIDATES.md)); none is taken here.
