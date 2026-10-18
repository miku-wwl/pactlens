"""Public engineering sources, never formal slots or detector predictions."""

from pactlens.agents.models import MessageIntent
from pactlens.arena.models import ArenaState
from pactlens.arena.transitions import begin
from pactlens.evidence.records import Channel, EpisodeRecord, capture_message, capture_transition
from pactlens.experiments.channels import Router
from pactlens.research.fixtures import fixture_task

PUBLIC_ID = "d6dd1a02-5135-4fd7-9844-2dd36366a68e"


def routed_record(*, enabled, failed=False, text="Observed private coordination"):
    state = begin(ArenaState(fixture_task()), expected_revision=0)
    journal = capture_transition(state, logical_position=1)
    router = Router(
        ("a0", "a1", "a2"),
        private_pair=("a0", "a1"),
        private_enabled=enabled,
        failed_sequences=(1,) if failed else (),
    )
    delivery = router.route(
        MessageIntent(Channel.PRIVATE, ("a1",), text),
        actor="a0",
        round_number=1,
        attempt_position=2,
        delivery_position=3,
    )
    message = delivery.observed_message()
    if message is not None:
        journal = capture_message(state, message, journal, logical_position=3)
    record = EpisodeRecord(
        state,
        () if message is None else (message,),
        event_journal=journal,
        private_metadata={
            "condition": "C+" if enabled else "C−",
            "private_pair": router.private_pair,
        },
    )
    return record, router
