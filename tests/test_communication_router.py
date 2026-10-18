from dataclasses import replace

import pytest

from pactlens.agents.models import MessageIntent
from pactlens.evidence.records import Channel
from pactlens.experiments.channels import Router


@pytest.mark.parametrize(
    "case,status",
    [
        ("public", "DELIVERED"),
        ("private", "DELIVERED"),
        ("disabled", "BLOCKED"),
        ("failure", "FAILED"),
        ("self", "BLOCKED"),
        ("unknown", "BLOCKED"),
        ("outsider", "BLOCKED"),
        ("subset", "BLOCKED"),
    ],
)
def test_routing_only_actual_permitted_recipients(case, status):
    router = Router(
        ("a0", "a1", "a2"),
        private_pair=("a0", "a1"),
        private_enabled=case != "disabled",
        failed_sequences=(1,) if case == "failure" else (),
    )
    recipients = (
        ("a1", "a2")
        if case == "public"
        else ("a0",)
        if case == "self"
        else ("foreign",)
        if case == "unknown"
        else ("a2",)
        if case == "outsider"
        else ("a1",)
    )
    intent = MessageIntent(
        Channel.PUBLIC if case in ("public", "subset") else Channel.PRIVATE,
        recipients,
        "observed text",
    )
    delivery = router.route(
        intent, actor="a0", round_number=1, attempt_position=1, delivery_position=2
    )
    assert delivery.status == status
    assert bool(router.inbox("a1")) == (status == "DELIVERED")
    assert router.inbox("a0") == ()
    assert delivery.delivered == (recipients if status == "DELIVERED" else ())
    if status != "DELIVERED":
        assert delivery.observed_message() is None


def test_delivery_integrity_and_no_shared_mutable_inbox():
    router = Router(("a0", "a1", "a2"), private_pair=("a0", "a1"), private_enabled=True)
    delivery = router.route(
        MessageIntent(Channel.PRIVATE, ("a1",), "private"),
        actor="a0",
        round_number=1,
        attempt_position=1,
        delivery_position=2,
    )
    inbox = router.inbox("a1")
    assert type(inbox) is tuple and router.inbox("a2") == ()
    with pytest.raises(ValueError):
        replace(delivery, delivered=("a2",))
    with pytest.raises(ValueError):
        replace(delivery, delivery_position=1)
