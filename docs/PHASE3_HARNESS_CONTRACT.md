# Phase 3 — Controlled Harness Contract

Implemented 2026-10-18 NZDT, entirely **pre-sprint engineering / pre-existing
work**. Baseline: `1aec45859c901994a08478800498b9925237dce8` (Phase 2,
verified local HEAD, tracking and live HTTPS remote). No official study runner
or detector is introduced. Research authority remains EXPERIMENT_PLAN.md.

## Layers and scope

| Layer | Contents | Export |
|---|---|---|
| L1 | Engineering condition/group, private briefs, role/order/request seeds, full model requests/responses/configuration | Private trace only |
| L2 | Independently computed reference, regret, pair benefit, outsider burden; pending adjudication | Private trace only |
| L3 | Explicit public task, observed messages/router attempts, committed proposal ballots, public costs, detached AIG evidence, completeness/order | Observation v2 plus opt-in extensions |
| L4 | Future detection/evaluation | Unimplemented |

`run_episode` accepts only `EpisodeConfig` with an `ENG-...` group and the literal
`pre_sprint_engineering` namespace. It has no Pilot/Calibration/Held-out entry
point. Frozen `research/seeds.py`, `manifest.py`, generator, allocation policy,
costs, tie rules and missing-ballot fallback are unchanged. The official future
allocation is 4+10+10 groups, five conditions per group, **24 groups /120 slots /
zero formal executions**. Existing manifest tests construct planned slots;
they never execute or inspect held-out outcomes.

## Agent and generation contract

Exactly three immutable `ActorContext` values have separate private instructions
and independent tuples of conversation turns. Each step receives public task
data, current accepted proposals/revision, its delivered inbox, channel access
and its own prior requests/responses and operation feedback. No other actor's
private prompt/history, experiment label, seed or oracle enters this context.
The seed is provider metadata, not prompt content. The trusted Python host and
model server are outside the malicious-agent isolation boundary.

`ModelProvider.generate(ModelRequest) -> ModelResponse` is provider-neutral.
`ModelConfig` pins name/revision and records endpoint type, integer milli-
temperature, output cap (at most 256 tokens), timeout (1–120 seconds), seed
support and **one attempt / zero retries**. Each actor makes one decision call
per round, at most six per episode. No reflection, repair or model judge calls.
Fresh inference can differ despite temperature zero and requested seeds.

`agents/prompts.py` provides the Incident Allocation prompt, never AIG's service
demo prompt. Contexts have a 24,000-byte fail-closed bound, no silent truncation.
This is **not proof of the prospective 2,000 input-token planning cap**; actual
usage is recorded when returned. Token fit and prompt freeze remain pilot work.

The closed response object requires `actor_id`, `round_number`, `task_hash`,
`decision`, `assignments`, `message`, `end_step`. Identity/task/round must match
trusted context; `end_step` is exactly true. `submit` carries one full allocation;
`decline` requires null assignments. A message is null or exactly channel,
recipients and text (256 characters/1,024 UTF-8 bytes). Entire output is at most
4,096 UTF-8 bytes. Duplicate keys, unknown fields, booleans as integers, wrong
identity, infeasible allocations and authority/tool/path/scope fields fail.
JSON parsing does not repair output, strip code fences or invent proposals.

## Communication and condition interventions

The experiment-owned `Router` validates a trusted sender and declared recipients.
Public messages must address both other actors. Private messages address the
other member of the configured pair and require enabled access. Self/unknown/
wrong/private-disabled routing is BLOCKED. A trusted engineering failure seam
produces FAILED, with zero recipients. This profile has no partial delivery.
Only DELIVERED messages enter recipient contexts or `EpisodeRecord.messages`.
Attempt, requested audience, actual audience, status, round, bounded text,
source sequence and explicit attempt/delivery capture positions are retained.
Sender feedback reports actual delivery rather than assuming it succeeded.

The declared L3 observation policy sees **all router attempts and confirmed
deliveries**, including blocked/failed text. Recipients see delivered text only.
This is an interception policy, not a claim that a peer saw an attempted message.
Observed predictive speech is preserved. Hidden experimental briefs are excluded.

| Condition | Enforced setup; behavioral outcome always separately pending |
|---|---|
| C+ | First two permuted actors receive explicit malicious-cooperation briefs; private pair enabled; feasible proposal opportunity |
| C− | Identical task, roles/order, briefs, model configuration and seed scheme; pair channel disabled |
| N1 | Shared public lawful objective, independent lawful briefs, no private pair access |
| N2 | Malicious-cooperation discussion setup/private pair; **all round-2 proposal execution blocked before AIG admission** |
| N3 | Explicit lawful public cooperation; no private pair access |

N2 retains attempted final proposals and missing slots. Round 1 remains
deliberation; all missing final ballots use the frozen lawful fallback. This
conservative intervention blocks execution opportunity without consulting an
oracle to rewrite model ballots. Missingness/intervention artifacts are a
methodological limitation, not hidden successful proposals. Discussion does
not establish collusion or execution. These are prospective condition contracts,
not established labels or a run of the official condition matrix.

C+/C− execute independently in fresh directories/contexts/stores/scopes. No
response, action or outcome is copied between them. Engineering seeds use
SHA-256 of `pactlens-engineering-v1 | engineering | ENG-group | purpose`, retaining
full digest and the unsigned big-endian first eight bytes. Purpose spelling and
local `Random(role_seed).shuffle(sorted actors)` follow the original convention;
the domain differs from official experiment seeds. Actor order is the same in
both rounds and across matched conditions. This is sequential controlled
execution, not simultaneous independent actions or spontaneous emergence.

The full unsigned 64-bit derived seed is retained. Each request also records
`UNSIGNED64_LOW63_V1`: the requested provider seed is its low 63 bits, to fit
Ollama's signed integer input. This fixed condition-independent mapping is not
evidence that a provider honors seeding or produces identical fresh outputs.

## Existing AIG path and failure behavior

After strict parsing/dry feasibility checks, the **current committed Arena**
snapshot is frozen by that actor's existing `ProposalStore.prepare`. Only then:

`trusted Plan construction → real Run → exact Approval → admission → separate
Authorization → Gateway claim/execute → verified SQLite receipt → arena_bridge`.

`aig/submission.py` uses the installed public API and existing Phase 2 consumer.
It adds no grant engine or executor. Each operation obtains a fresh Run/Approval/
admission/Authorization; the model supplies none of these decisions. The default
five-second budget and original trusted binding remain unchanged. Inference
happens before AIG composition/execution and outside that budget.

All automated episodes require **explicit synthetic test consent**. The trusted
test consent seam can reject Approval or withhold Authorization; withholding
does not call execute. This is not authenticated human consent. No interactive
operator mode or production authentication is implemented.

Invalid output, inference errors/timeouts and delivery failures remain logged;
the episode is INCOMPLETE and other bounded steps continue using existing missing
ballot rules. An explicit valid decline is retained without being a technical
failure. Approval rejection/authorization withholding leaves no effect and marks
INCOMPLETE. Unknown stops the affected episode immediately, without applying its
possibly committed row or creating another Action. A verified local receipt can
coexist with Unknown; it never promotes that Action to success. Revision/store/
bridge exceptions stop with STOPPED_CONFLICT and propagate. Cancellation and
keyboard interruption record INTERRUPTED and propagate. No directory resume,
reset, reconciliation execution, duplicate dispatch or automatic retry exists.

The scheduler applies at most one accepted proposal per actor/round, then closes
rounds with the original functions. Sequential snapshots avoid the known
cross-store stale-base problem without weakening Arena checks. This is not a
distributed transaction or multi-host serialization guarantee.

## Trace, chronology and pure replay

`TraceWriter` creates a new exclusive JSONL, at most 256 records /131,072 bytes
per record. Each append flushes and fsyncs. Rows include schema/episode, explicit
shared-host capture position, sequence, kind, L1/L2/L3_SOURCE classification,
experimenter-owned trust, bounded canonical payload, previous hash and digest.
The reader caps total input at 8 MB and rejects duplicate/noncanonical keys,
truncated lines, bad chains, mixed IDs, unknown fields and post-terminal data.
L3_SOURCE is a **source classification**, not permission to dump a payload to L3.

Separate records cover configuration/task, generation requests/responses/digests,
failures, validation, router attempts/delivery, proposal attempts, Run/Plan digest,
Approval, admission, Authorization, detached Action/receipt snapshot, Arena
application/closure, final public accounting, private mechanics and terminal
completeness. No capability, grant, execution scope, subject identity, private
Gate tables, unrestricted environment dump or secret-bearing URL is stored.
Private model text is experimenter-owned; untrusted text cannot access host
credentials. Private traces/stores are excluded from the review archive.

Positions capture real host observations in interleaved invocation order, not
provider/Gate transaction timestamps. Existing Observation-v2 source grouping
remains **not global chronology**. Shared capture binds actual delivered-message
positions and observed Action-before-Arena application. Legacy/independent
sources require null positions and explicit UNKNOWN cross-source order. The
new `harness` extension uses neutral actor aliases and an explicit allowlist;
base fields and `aig_execution` retain their existing contracts. Future R/MAE
must consume the same inventory, missingness and uncertainty. No detector views,
transforms, thresholds or metrics are implemented.

`replay_trace(path)` is pure: validate chain and decision/receipt/application
correlations, reconstruct using original pure transitions, validate canonical
states/private mechanics, and project the same observation with its original
UUID/receipt references. It invokes **zero model calls, zero Gateway operations,
zero new effects or grants**. Historical captured receipt status is retained,
not claimed freshly verified from live SQLite. For live store verification use
the existing read-only `committed`/`reconstruct` interfaces. Missing terminal
means INTERRUPTED even if final allocation was captured. Truncated partial lines
fail closed for manual diagnosis. An unkeyed chain is not a signature; an
experimenter can consistently rewrite/omit history. No malicious-host security,
cryptographic authenticity or universal remote exactly-once guarantee is claimed.

## Local Ollama and explicit smoke command

No new dependencies. The only network module uses `http.client` plus URL parsing
for numeric **loopback HTTP with explicit port and `/v1` path**. No DNS hostnames,
userinfo, proxy environment, redirects, credentials, cloud SDKs or downloads.
Exact installed model name/digest and local server version are checked with
`/api/version`, `/api/tags`, `/api/show`; remote/cloud metadata is rejected and
revision rechecked before generation. Trust in the local server is required;
loopback cannot attest its internals. HTTP body limits and socket timeout apply.
Model request cancellation cannot guarantee server-side inference cancellation;
late generation has no tool authority and is never automatically retried.

Set only explicit local settings (no API key):

```powershell
$env:PACTLENS_OLLAMA_BASE_URL='http://127.0.0.1:11434/v1'
$env:PACTLENS_OLLAMA_MODEL='<exact installed local model name>'
uv run python -m pactlens.experiments.smoke .runtime/<fresh-engineering-directory> --allow-one-local-engineering-episode
```

Disabled by default; command opt-in and a fresh directory are mandatory. It runs
one N3 engineering episode, at most six generation requests, with synthetic AIG
consent and actual outcomes retained. It is not a study block and guarantees no
successful proposal. No model name is assumed by application code.
Ollama's [compatibility reference](https://docs.ollama.com/api/openai-compatibility)
documents the supported endpoint/fields; behavior is qualified by actual tests.
