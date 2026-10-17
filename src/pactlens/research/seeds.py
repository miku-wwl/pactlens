"""Frozen group identities and UTF-8 SHA-256 domain-separated seed derivation."""

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum


class Split(StrEnum):
    PILOT = "pilot"
    CALIBRATION = "calibration"
    HELD_OUT = "held_out"


class Condition(StrEnum):
    C_PLUS = "C+"
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
    C_MINUS = "C−"


CONDITIONS = tuple(Condition)
GROUPS = tuple(
    (split, f"{prefix}{index:03}")
    for split, prefix, count in (
        (Split.PILOT, "P", 4),
        (Split.CALIBRATION, "K", 10),
        (Split.HELD_OUT, "T", 10),
    )
    for index in range(1, count + 1)
)


@dataclass(frozen=True)
class SeedMaterial:
    purpose: str
    digest_hex: str
    integer: int


def derive_seed(split: Split, group_id: str, purpose: str) -> SeedMaterial:
    if type(split) is not Split or (split, group_id) not in GROUPS:
        raise ValueError("Unknown frozen split/group")
    if type(purpose) is not str or re.fullmatch(r"[a-z0-9/_-]{1,96}", purpose) is None:
        raise ValueError("Invalid seed purpose")
    message = f"pactlens-exploratory-v1 | {split.value} | {group_id} | {purpose}"
    digest = hashlib.sha256(message.encode("utf-8", errors="strict")).digest()
    return SeedMaterial(purpose, digest.hex(), int.from_bytes(digest[:8], "big", signed=False))
