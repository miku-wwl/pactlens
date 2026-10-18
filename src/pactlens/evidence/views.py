"""Pure fact selection for five prospective detector inputs; no scoring."""

from enum import StrEnum

from pactlens.evidence.inventory import Inventory


class View(StrEnum):
    M = "M"
    A = "A"
    MA = "MA"
    R = "R"
    MAE = "MAE"


CATEGORIES = {
    View.M: frozenset(("CONTEXT", "COMMUNICATION")),
    View.A: frozenset(("CONTEXT", "BEHAVIOR")),
    View.MA: frozenset(("CONTEXT", "COMMUNICATION", "BEHAVIOR")),
    View.R: frozenset(("CONTEXT", "COMMUNICATION", "BEHAVIOR", "INTEGRITY")),
    View.MAE: frozenset(("CONTEXT", "COMMUNICATION", "BEHAVIOR", "INTEGRITY")),
}


def view_facts(inventory, view):
    if type(inventory) is not Inventory or type(view) is not View:
        raise ValueError("TYPED_INVENTORY_AND_VIEW")
    inventory.__post_init__()
    # Full eligible inventory or explicit overflow later; no condition-based selection.
    return tuple(f for f in inventory.facts if f.category in CATEGORIES[view])
