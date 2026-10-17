"""Replay local committed effects, never redispatch AIG Actions."""

from pactlens.arena.models import ArenaState, Lifecycle
from pactlens.arena.transitions import begin, close_round, submit_proposal
from pactlens.serialization import canonical_json


def apply_committed(state, store, *, effect_key):
    """Read and verify the durable row at this boundary; a receipt string is insufficient."""
    found = [effect for effect in store.committed() if effect.effect_key == effect_key]
    if len(found) != 1:
        raise ValueError("Verified committed effect required")
    effect = found[0]
    prepared = effect.prepared
    if canonical_json(state) != canonical_json(prepared.state):
        raise ValueError("Committed proposal base revision/state mismatch")
    return submit_proposal(
        state,
        prepared.proposal,
        actor_id=prepared.proposal.agent_id,
        expected_revision=prepared.arguments["expected_revision"],
    )


def reconstruct(task, stores, *, finalize=False):
    effects = tuple((store, effect) for store in stores for effect in store.committed())
    if len({e.effect_key for _, e in effects}) != len(effects):
        raise ValueError("Duplicate effect identity")
    revisions = [e.prepared.state.revision for _, e in effects]
    if len(set(revisions)) != len(revisions):
        raise ValueError("Conflicting proposal slots or base revisions")
    state = begin(ArenaState(task), expected_revision=0)
    # This is dependency/revision order, not a claim about cross-store commit time.
    for store, effect in sorted(effects, key=lambda pair: pair[1].prepared.state.revision):
        if effect.prepared.proposal.round_number == 2 and state.status == Lifecycle.ROUND_1:
            state = close_round(state, expected_revision=state.revision)
        state = apply_committed(state, store, effect_key=effect.effect_key)
    if finalize:
        while state.status != Lifecycle.FINALIZED:
            state = close_round(state, expected_revision=state.revision)
    return state
