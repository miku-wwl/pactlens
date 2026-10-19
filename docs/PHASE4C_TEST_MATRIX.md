# Phase 4C — Test Matrix

**2026-10-20 NZDT; pre-sprint engineering / pre-existing work.** Six new modules,
**117 new cases**, plus one new helper (`tests/context_helpers.py`). All 54
pre-existing test files are unchanged under git's normalized comparison. Unit
tests use deterministic fake transcripts or an offline transport stub; effects go
through the installed AIG 0.2.0 with explicitly synthetic consent. No test calls a
model, network endpoint, detector or paid API (the existing socket guard applies).

## Final validation (actual, `UV_OFFLINE=1`)

| Command | Result |
|---|---|
| `uv sync --locked` | exit 0 (31 packages checked) |
| `uv run pytest -q` (+ JUnit) | **724 passed in 444.95 s: 607 original + 117 new; 0 failed, 0 errors, 0 skipped** |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 148 files already formatted |
| `uv lock --check --offline` | exit 0 (31 packages resolved) |
| `python -m compileall -q src tests` | exit 0 |

New cases by module: context v3 20, six-step budget 14, compact evidence 52,
evidence sufficiency 15, candidates/readiness 10, bounded qualification runner 6.
Baseline before any edit: 607 passed. An interim full run during development
recorded 707 passed with the tests then present. A wrapper `tail -2` in the final
batch exited 1 on Git Bash after all six commands had exited 0; command results
are taken from their own recorded exit lines.

## Requirement coverage

| Requirement (handoff §19) | Tests |
|---|---|
| Historical round-2 overflow reproduction | `test_phase4c_context_v3::test_historical_v2_round_two_overflow_is_reproduced_and_attributed` (5,099 B / 2,838 est., round-1 estimates 1,669/1,796/1,924, attribution partition, 2 task copies, 8 task-hash copies) |
| Compact context lossless reconstruction | `test_v3_text_rebuilds_exact_v2_turns_for_all_six_steps[C+,N1,N2,N3,C−]` (decoder reads only v3 text; equals actual v2 turns byte-for-byte for all six steps) |
| Six-step request budgeting | `test_phase4c_six_step_budget::test_all_six_decisions_fit_without_speech_in_every_condition` (fixture and largest generated 5-incident task × five conditions), `test_request_accounting_is_recorded_for_every_attempted_step`, `test_same_historical_transcript_completes_six_steps_under_v3` |
| Worst-case bounded history | `test_maximal_speech_on_largest_task_is_an_explicit_overflow[ascii,cjk]`, `test_overflow_fails_closed_without_truncation_or_sending`, `test_round_one_never_carries_history_and_round_two_has_one_entry` |
| Actor-context isolation | `test_delivered_inbox_is_exactly_the_routed_messages_and_actors_stay_isolated` (no other actor's brief; outsider never receives pair-private text) |
| Delivered-message fidelity | same test (inbox equals messages delivered before the request's capture position), `test_own_commitments_feedback_and_delivery_status_survive` (own earlier text, BLOCKED feedback in C−) |
| Historical prompt compatibility | `test_historical_v1_v2_request_construction_is_unchanged` (4 pre-edit golden digests), `test_phase4c_candidates::test_historical_candidate_hashes_are_unchanged` (v2 prompt, protocol and 4B selection hashes) |
| Valid submit and decline | `test_valid_declines_and_identity_errors_keep_v2_protocol_semantics`, qualification `example` mode (six receipts) |
| Incorrect actor/task/round rejection | same test: WRONG_ACTOR / WRONG_ROUND / WRONG_TASK, no Action for rejected steps |
| Unparseable earlier output | `test_unparseable_earlier_output_is_kept_verbatim_not_repaired` |
| Tampered or non-prefix history | `test_history_that_is_not_a_prefix_or_not_v3_is_rejected` (7 variants) |
| Request binding | `test_candidate_request_binding_and_budget_record` (v3 prompt cannot bind v1 protocol; oversized brief fails preflight) |
| Unknown Action no-retry | `test_unknown_stops_without_retry_and_replay_is_pure`, compact `test_unknown_with_committed_receipt_stays_unknown_in_tables` |
| Pure replay, zero new side effects | `test_unknown_stops_without_retry_and_replay_is_pure` (trace bytes unchanged; zero model/new-effect calls), qualification replay checks |
| Full six-action evidence | `test_phase4c_compact_evidence::test_six_action_real_aig_source_reconstructs_and_cites_by_key[A,B]` |
| Action/Receipt correlation | same test (shared value references), sufficiency `test_classification_of_constructed_retained_sets` (SPLIT detected) |
| Lossless compact rendering | `test_fixture_tables_reconstruct_every_original_fact` (14 fixtures × 2 policies), `test_owner_vectors_require_complete_neutral_order` |
| R/MAE independent text parity | `check_exact` in every reconstruction test; `test_parity_rejects_unequal_information_between_r_and_mae` |
| Tamper rejection | `test_tampered_flat_text_is_rejected` (13 kinds), `test_tampered_grouped_text_is_rejected` (2), `test_compact_view_requires_matching_manifest_and_budget` |
| Complete detector request budgeting | `test_complete_six_action_evidence_is_typed_infeasible_with_bottleneck[A,B]` (byte attribution sums to the request), `test_complete_policy_returns_full_packets_when_the_episode_fits` (`conversation()` rechecks fit) |
| Explicit evidence omissions | `test_v2_tables_retain_more_lifecycle_under_unchanged_rules[A,B]` (packet classified `LIFECYCLE_INCOMPLETE`, never complete) |
| Evidence sufficiency classification | `test_classification_of_constructed_retained_sets` (four classes) |
| Condition-independent selection | `test_selection_has_no_label_input_and_ignores_private_metadata`, `test_condition_differences_arise_only_from_observable_facts[five conditions]` |
| L1/L2 leakage prevention | `test_private_labels_never_reach_tables_and_do_not_change_text` |
| Incorrect chronology rejection | tamper `order` (recorded position removed), `test_capture_positions_and_unknown_order_survive_without_invention`, v3 non-prefix history |
| Missing/Failed/Unknown distinctions | `test_withheld_authorization_and_denied_approval_stay_explicit`, Unknown-with-receipt test, `test_condition_differences...` (N2 missing Actions retained) |
| Mandatory overflow typed failure | `test_mandatory_overflow_is_typed_and_never_an_empty_success` |
| Cross-view relations | `check_exact` (M∪A=MA⊆R, R=MAE from parsed text), `test_packet_bundle_detects_cross_view_and_manifest_tampering` |
| Determinism | `test_fresh_processes_render_identical_tables` (two hash seeds) |
| Original Arena/AIG unchanged | full existing suite; environment check (protected sources identical to HEAD); `test_historical_v1_v2_request_construction_is_unchanged` |
| Bounded live runner | `test_phase4c_qualification` (ledger cap, offline gate, opt-in, fresh directory, overflow and malformed outputs recorded, ≤6 calls) |
| Readiness never auto-approves | `test_phase4c_candidates` (model gate never GO from engineering evidence; pilot always NO-GO) |

## Intermediate development corrections (recorded, not hidden)

- Attribution initially read a removed v3 history shape (`KeyError: 'seen'`) and
  counted an empty `[]` as history; both corrected before acceptance.
- The task-hash counter initially looked only in observations; v3 shows the hash
  once in the example, so it now matches the JSON field anywhere in the request.
- Two tests were too brittle (a non-ASCII stress case may legitimately overflow in
  round 1; history size is asserted structurally rather than by a byte guess).
- `pytest` tried to collect `TestConsent`; tests alias it as existing tests do.
- Ruff fixes: `min(...)` instead of `sorted(...)[0]`, an unused unpacked name, and
  a combined `if` branch.
