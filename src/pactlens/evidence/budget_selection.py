"""Prospective, condition-blind shared selection. Not an approved study profile."""

import json
from dataclasses import dataclass

from pactlens.agents.models import closed_json
from pactlens.evidence.budgeted_views import TABLE_VERSION, render_budgeted, verify_budgeted_parity
from pactlens.evidence.fact_bundles import BUNDLE_VERSION, fact_bundles
from pactlens.evidence.views import View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-common-bundles-v1-candidate"
CONFIG = {
    "version": VERSION,
    "bundles": BUNDLE_VERSION,
    "tables": TABLE_VERSION,
    "mandatory": "task;all-six-proposals;source-coverage;execution;round-boundaries;all-nonsuccess-or-missing-integrity;all-failed-router;two-observed-speakers-if-available;one-successful-integrity-if-available",
    "priority": [
        "mandatory",
        "successful-integrity-round-desc-actor",
        "communication-round-sequence",
        "arena-round-sequence",
    ],
    "tie": "public-kind-slot-sequence-key;never-condition-or-oracle",
    "overflow": "reject-mandatory-overflow;common-R-MAE-fit;no-retry;no-context-expansion",
    "approval": "PROPOSED_NOT_APPROVED",
}
CONFIG_HASH = content_hash(CONFIG)


class SelectionFailure(ValueError):
    def __init__(self, diagnostics):
        super().__init__("INPUT_BUDGET_EXCEEDED")
        self.diagnostics_json = canonical_json(diagnostics)


@dataclass(frozen=True)
class SelectionResult:
    packets: tuple
    manifest_json: str

    def packet(self, view):
        return next(p for p in self.packets if p.view == view)

    def verify(self):
        if (
            type(self.packets) is not tuple
            or len(self.packets) != 5
            or {p.view for p in self.packets} != set(View)
        ):
            raise ValueError("FIVE_SELECTED_VIEWS_REQUIRED")
        for packet in self.packets:
            packet.verify()
        verify_budgeted_parity(self.packet(View.R), self.packet(View.MAE))
        manifest = closed_json(self.manifest_json, 524288)
        if type(manifest) is not dict or set(manifest) != {
            "version",
            "selection_config_hash",
            "base_config_hash",
            "approval",
            "episode_public_id",
            "observation_policy",
            "retained_fact_ids",
            "omitted_fact_ids",
            "mandatory_fact_ids",
            "retained_bundle_keys",
            "omitted_bundle_keys",
            "source_fact_count",
            "selected_fact_count",
            "original_evidence_complete",
            "methodological_sufficiency",
            "views",
        }:
            raise ValueError("SELECTION_MANIFEST_FIELDS")
        raw_manifest = json.loads(self.packet(View.R).manifest_json)
        retained = sorted(f["fact_id"] for f in raw_manifest["facts"])
        omitted = sorted(f["fact_id"] for f in raw_manifest["omitted"])
        if (
            manifest["retained_fact_ids"] != retained
            or manifest["omitted_fact_ids"] != omitted
            or manifest["mandatory_fact_ids"] != raw_manifest["mandatory_fact_ids"]
            or manifest["selected_fact_count"] != len(retained)
            or manifest["source_fact_count"] != len(retained) + len(omitted)
            or manifest["original_evidence_complete"] != (not omitted)
            or manifest["base_config_hash"] != CONFIG_HASH
            or manifest["approval"] != "PROPOSED_NOT_APPROVED"
            or manifest["version"] != VERSION
            or manifest["selection_config_hash"] != raw_manifest["header"]["selection_hash"]
            or manifest["episode_public_id"] != raw_manifest["header"]["episode"]
            or manifest["observation_policy"] != raw_manifest["header"]["policy"]
        ):
            raise ValueError("SELECTION_MANIFEST_BINDING")
        for packet in self.packets:
            p = json.loads(packet.manifest_json)
            expected = {
                "selected_fact_count": len(p["facts"]),
                "omitted_fact_count": len(p["omitted"]),
                "bytes": len(packet.text.encode("utf-8")),
                "budget": p["budget"],
                "reserved_output_tokens": packet.envelope.reserved_output_tokens,
            }
            if manifest["views"].get(packet.view.value) != expected:
                raise ValueError("SELECTION_VIEW_BUDGET_BINDING")
        return True


def select_evidence(inventory, *, envelope=None, token_counter=None):
    envelope = DetectorEnvelope() if envelope is None else envelope
    if type(envelope) is not DetectorEnvelope:
        raise ValueError("TRUSTED_DETECTOR_ENVELOPE")
    envelope.__post_init__()
    bundles = fact_bundles(inventory)
    mandatory = {f.fact_id for b in bundles if b.mandatory for f in b.facts}
    chosen = set(mandatory)
    config_hash = content_hash({"selection": CONFIG_HASH, "envelope": envelope.config_hash})

    def render(ids):
        return tuple(
            render_budgeted(
                inventory, ids, mandatory, config_hash, view, envelope, token_counter=token_counter
            )
            for view in View
        )

    def fits(packets):
        return all(json.loads(p.manifest_json)["budget"]["fits"] for p in packets)

    packets = render(chosen)
    if not fits(packets):
        raise SelectionFailure(
            {
                "version": VERSION,
                "config_hash": config_hash,
                "error": "MANDATORY_CORE_OVERFLOW",
                "mandatory_fact_ids": sorted(mandatory),
                "source_fact_count": len(inventory.facts),
                "attempted_selected_fact_count": len(chosen),
                "prediction_generated": False,
                "views": {
                    p.view.value: {
                        "bytes": len(p.text.encode("utf-8")),
                        "budget": json.loads(p.manifest_json)["budget"],
                    }
                    for p in packets
                },
            }
        )
    retained_bundles = [b.key for b in bundles if b.mandatory]
    for bundle in bundles:
        if bundle.mandatory:
            continue
        proposed = chosen | {f.fact_id for f in bundle.facts}
        candidate = render(proposed)
        # The larger matched presentation and every other complete request must fit.
        if fits(candidate):
            chosen, packets = proposed, candidate
            retained_bundles.append(bundle.key)
    verify_budgeted_parity(
        next(p for p in packets if p.view == View.R), next(p for p in packets if p.view == View.MAE)
    )
    omitted = sorted(f.fact_id for f in inventory.facts if f.fact_id not in chosen)
    manifest = {
        "version": VERSION,
        "selection_config_hash": config_hash,
        "base_config_hash": CONFIG_HASH,
        "approval": "PROPOSED_NOT_APPROVED",
        "episode_public_id": inventory.episode_public_id,
        "observation_policy": inventory.observation_policy.value,
        "retained_fact_ids": sorted(chosen),
        "omitted_fact_ids": omitted,
        "mandatory_fact_ids": sorted(mandatory),
        "retained_bundle_keys": retained_bundles,
        "omitted_bundle_keys": [b.key for b in bundles if b.key not in retained_bundles],
        "source_fact_count": len(inventory.facts),
        "selected_fact_count": len(chosen),
        "original_evidence_complete": not omitted,
        "methodological_sufficiency": "REQUIRES_PROSPECTIVE_RESEARCHER_REVIEW",
        "views": {
            p.view.value: {
                "selected_fact_count": len(json.loads(p.manifest_json)["facts"]),
                "omitted_fact_count": len(json.loads(p.manifest_json)["omitted"]),
                "bytes": len(p.text.encode("utf-8")),
                "budget": json.loads(p.manifest_json)["budget"],
                "reserved_output_tokens": envelope.reserved_output_tokens,
            }
            for p in packets
        },
    }
    result = SelectionResult(packets, canonical_json(manifest))
    result.verify()
    return result
