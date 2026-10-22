"""Prospective 4096/8192 amendment. Same Detector semantics and complete L3 facts."""

from dataclasses import dataclass

from pactlens.agents.budgets import CONTEXT_PROFILE, budget_hash
from pactlens.evidence.tight_views import VERSION as CODEC_VERSION
from pactlens.evidence.tight_views import render
from pactlens.evidence.views import View
from pactlens.research.reason_detector import SCHEMA_HASH, ReasonEnvelope
from pactlens.research.reason_detector import envelope as historical_envelope
from pactlens.serialization import content_hash, primitive

VERSION = "pactlens-detector-budget-8192-v1-candidate"
COMPLETE_SELECTION_HASH = content_hash(
    {
        "version": "pactlens-complete-source-tight-v1-candidate",
        "codec": CODEC_VERSION,
        "rule": "ALL_PERMITTED_SOURCE_FACTS_NO_SELECTION_NO_TRUNCATION",
    }
)


@dataclass(frozen=True)
class ContextEnvelope(ReasonEnvelope):
    input_limit: int = 8192

    def __post_init__(self):
        self._validate_limits(8192)

    @property
    def budget_profile(self):
        return CONTEXT_PROFILE

    @property
    def config_hash(self):
        return content_hash(
            {
                "version": VERSION,
                "budget_hash": budget_hash(CONTEXT_PROFILE),
                "schema_hash": SCHEMA_HASH,
                "config": primitive(self),
            }
        )


def envelope():
    old = historical_envelope()
    return ContextEnvelope(system=old.system, task=old.task, output=old.output)


def full_packets(inventory):
    ids = {f.fact_id for f in inventory.facts}
    return tuple(render(inventory, ids, ids, COMPLETE_SELECTION_HASH, v, envelope()) for v in View)
