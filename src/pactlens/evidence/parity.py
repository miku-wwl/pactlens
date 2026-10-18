"""Independent rendered-input semantic reconstruction and information parity."""

from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.views import View
from pactlens.serialization import canonical_json


def canonical_facts(rendered):
    header, facts = rendered.verify()
    return canonical_json(
        {
            "inventory_version": header["inventory_version"],
            "episode_public_id": header["episode_public_id"],
            "observation_policy": header["observation_policy"],
            "facts": canonical_fact_records(facts),
        }
    )


def verify_parity(raw, structured):
    if raw.view != View.R or structured.view != View.MAE:
        raise ValueError("R_AND_MAE_REQUIRED")
    if canonical_facts(raw) != canonical_facts(structured):
        raise ValueError("RAW_STRUCTURED_INFORMATION_MISMATCH")
    return True
