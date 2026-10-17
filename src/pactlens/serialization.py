"""Canonical, integer-only JSON for synthetic tasks and private manifests.

This is not the public evidence exporter; that exporter constructs its own allowlist.
"""

import dataclasses
import hashlib
import json
from enum import Enum


def primitive(value):
    if isinstance(value, Enum):
        return primitive(value.value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: primitive(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) in (tuple, list):
        return [primitive(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: primitive(item) for key, item in value.items()}
    raise TypeError("Canonical JSON requires dataclasses and explicit JSON scalar/sequence types")


def canonical_json(value) -> str:
    return json.dumps(primitive(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def content_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8", errors="strict")).hexdigest()
