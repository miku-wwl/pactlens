"""Finite numeric research JSON; Arena's integer-only serialization stays unchanged."""

import hashlib
import json
from dataclasses import asdict, is_dataclass


def canonical_json(value):
    def convert(obj):
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        raise TypeError("EXPLICIT_RESEARCH_JSON_REQUIRED")

    return json.dumps(
        value,
        default=convert,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def content_hash(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
