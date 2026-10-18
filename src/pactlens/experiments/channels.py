"""Trusted routing policy; model message intent is never proof of delivery."""

from dataclasses import dataclass

from pactlens.agents.models import MessageIntent
from pactlens.evidence.records import Channel, Message


@dataclass(frozen=True)
class Delivery:
    sequence: int
    round_number: int
    sender: str
    requested: tuple[str, ...]
    delivered: tuple[str, ...]
    channel: Channel
    text: str
    status: str
    attempt_position: int | None
    delivery_position: int | None

    def __post_init__(self):
        from pactlens.arena.models import integer

        integer(self.sequence, 1, 6)
        MessageIntent(self.channel, self.requested, self.text)
        integer(self.round_number, 1, 2)
        if type(self.delivered) is not tuple or len(set(self.delivered)) != len(self.delivered):
            raise ValueError("DELIVERY_RECIPIENTS")
        if not set(self.delivered) <= set(self.requested):
            raise ValueError("DELIVERY_WIDENED")
        if self.status not in ("DELIVERED", "BLOCKED", "FAILED"):
            raise ValueError("DELIVERY_STATUS")
        if (self.status == "DELIVERED") != (self.delivered == self.requested):
            raise ValueError("DELIVERY_STATUS")
        if self.status != "DELIVERED" and self.delivered:
            raise ValueError("NO_PARTIAL_DELIVERY_PROFILE")
        for p in (self.attempt_position, self.delivery_position):
            if p is not None:
                integer(p, 1, 4096)
        if (
            self.attempt_position is not None
            and self.delivery_position is not None
            and self.attempt_position >= self.delivery_position
        ):
            raise ValueError("DELIVERY_ORDER")

    def observed_message(self):
        if not self.delivered:
            return None
        return Message(
            self.sequence, self.round_number, self.sender, self.delivered, self.channel, self.text
        )


class Router:
    def __init__(self, actors, *, private_pair, private_enabled, failed_sequences=()):
        if (
            len(actors) != 3
            or len(set(actors)) != 3
            or len(private_pair) != 2
            or not set(private_pair) <= set(actors)
        ):
            raise ValueError("ROUTER_ACTORS")
        if type(private_enabled) is not bool:
            raise ValueError("ROUTER_POLICY")
        self.actors = tuple(actors)
        self.private_pair = tuple(private_pair)
        self.private_enabled = private_enabled
        self.failed_sequences = frozenset(failed_sequences)
        self.deliveries = ()

    def route(self, intent, *, actor, round_number, attempt_position, delivery_position):
        if type(intent) is not MessageIntent or actor not in self.actors:
            raise ValueError("TRUSTED_SENDER_REQUIRED")
        intent.__post_init__()
        recipients = set(intent.recipients)
        valid = actor not in recipients and recipients <= set(self.actors)
        if intent.channel == Channel.PUBLIC:
            valid = valid and recipients == set(self.actors) - {actor}
        else:
            valid = (
                valid
                and self.private_enabled
                and actor in self.private_pair
                and recipients == set(self.private_pair) - {actor}
            )
        sequence = len(self.deliveries) + 1
        status = (
            "BLOCKED"
            if not valid
            else "FAILED"
            if sequence in self.failed_sequences
            else "DELIVERED"
        )
        delivery = Delivery(
            sequence,
            round_number,
            actor,
            intent.recipients,
            intent.recipients if status == "DELIVERED" else (),
            intent.channel,
            intent.text,
            status,
            attempt_position,
            delivery_position,
        )
        self.deliveries += (delivery,)
        return delivery

    def inbox(self, actor):
        return tuple(d.observed_message() for d in self.deliveries if actor in d.delivered)
