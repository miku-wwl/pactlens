# Phase 4D — Token and evidence qualification

2026-10-22 NZDT; pre-sprint engineering. No accounting rule or cap was changed.

Agent limit: 2,000 input / 256 output. Detector: 4,096 input / 256 reserved output.
Complete request accounting includes system, task, evidence, output schema, role
labels and the existing chat margin. Exact bytes are measurements; tokens are
`ceil(UTF8 bytes/2) + 32*turns + 128` estimates unless expressly provider-reported.

## Tokenizer investigation

`review/phase4d/logs/tokenizer-investigation.txt` records actual Ollama 0.35.1,
the pinned phi4-mini digest, complete returned template and tokenizer metadata.
The active installed environment lacks transformers, tokenizers, sentencepiece,
llama_cpp and tiktoken. Metadata identifies GPT2/GPT-4o pretokenization; that does
not qualify an exact tokenizer or its full template. No undocumented tokenization
endpoint, downloaded dependency, weights or unrelated-model count was used.
The selected future formal detector is still unapproved:
**EXACT_DETECTOR_TOKENIZER_NOT_QUALIFIED**. Agent exact counts are also null.
The final read-only `/api/ps` check reports size_vram=0 and a currently loaded
4,096-token local context. Both engineering smoke requests plus the 256-token
output reservation fit that window under the unchanged estimate. A future full
4,096-input/256-output profile must explicitly qualify a sufficient provider
window (or let DetectorEnvelope reduce available input); the present context
metadata does not qualify a formal detector profile.

Historical provider usage from Phase 4C remains descriptive, not re-qualified:
v3 input 660–871 against estimates 1,430–1,723. New v3.1 N3 requests estimate
1,527–1,890; provider inputs are 678–942. R/MAE smoke estimates 3,584/3,625;
provider inputs 2,036/2,061. These after-dispatch counts cannot authorize an
unsent request or transfer qualification to another detector model.

## Full evidence and parity

The safe audit in `review/phase4d/audit/evidence-audit.json` reconstructs all five
final rendered texts separately. Full semantic records (IDs, values, source,
trust, nulls, completeness and ordering) satisfy:

`canonical_facts(R) == canonical_facts(MAE)`; `M union A == MA`; `MA subset R`.

The 30 source/policy sets cover all 14 historical safe fixtures plus a fresh
six-action, real-AIG, fake-agent source under each policy. They preserve all six
proposal slots, correlated Action/receipt identities, final allocation/public
cost, observed communications, missingness and known/unknown ordering. The
complete selector either retains everything or returns EVIDENCE_BUDGET_INFEASIBLE.
The selected audit lists every omitted fact and separately assesses mechanical
audit sufficiency. A fitting selected packet is not complete evidence.
`review/phase4d/full-six-action/verification.json` additionally binds independently
parsed **full, unselected** rendered texts under both policies to an unchanged
synthetic source trace. Their complete provenance/ordering values satisfy the same
three semantic relations. These diagnostic texts are not eligible model packets.

| Six-action source | Policy | Full R estimate | Selected R / source facts | Selected audit sufficiency |
|---|---|---:|---:|---|
| Silent | A | 4,631 | 23 / 32 | LIFECYCLE_INCOMPLETE |
| Silent | B | 4,626 | 23 / 32 | LIFECYCLE_INCOMPLETE |
| Public speech | A | 5,113 | 23 / 38 | LIFECYCLE_INCOMPLETE |
| Public speech | B | 5,799 | 23 / 44 | LIFECYCLE_INCOMPLETE |

Complete six-action evidence remains **EVIDENCE_BUDGET_INFEASIBLE**, even in the
silent six-action source. Exact budget fit is NOT QUALIFIED. Lossy selection
retains common sets and omission markers; no view receives favorable truncation.
R and MAE parity does not remedy information missing from both packets.

## Prospective decision record — none adopted

| Option | Technical consequence | Scientific consequence | Nominal calls |
|---|---|---|---:|
| Existing bounded lossy common selection | Current conservative guard; omissions explicit | Changes available evidence; differential omissions/abstention threaten interpretation; approval still needed | 1,320 |
| Exact-tokenizer-qualified full evidence | Pin model/digest/template, validate full-template counts against sent requests, review prospectively | Could restore completeness without cap expansion; cannot assume it fits or improves detection | 1,320 plus separately approved qualification work |
| Larger approved detector input cap | Requires prospective amendment and new forecast; current cap remains 4,096 | Alters input cost/context and comparability; freeze before scoring | 1,320 generations, more tokens |
| Multiple packets with frozen aggregation | NOT IMPLEMENTED; define packet boundaries, missing/error policy and aggregation prospectively | Episode remains sampling unit; packets are correlated, no inflated n; changes estimand/pipeline | Two calls for each of five views would be 720+1,200=1,920; aggregation inference adds more |

An approval should be based on evidence rights and sufficiency, not favorable
performance. The existing 1,320 envelope includes only five detector calls per
episode; observer sensitivity or baseline LLM calls are not free additions.
