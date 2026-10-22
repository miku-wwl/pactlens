"""Lossless v3 row codec. Stable values, provenance, identifiers and ordering survive."""

import json
from uuid import UUID, uuid5

from pactlens.agents.models import closed_json
from pactlens.evidence import compact_views as old
from pactlens.evidence.inventory import KIND_META, PAYLOAD_FIELDS, Fact
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.projection import _public_id
from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.views import CATEGORIES, View
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-budgeted-facts-v3-candidate"
MARKER = "pactlens-facts-v3"
COMPLETE = {"OBSERVED": "O", "MISSING": "M", "PENDING": "P", "NOT_REACHED": "N", "INCOMPLETE": "I"}
LAYOUT = {
    "row": [
        "citation_index",
        "kind_index",
        "actor_1_to_3_or_null",
        "completeness",
        "order",
        "payload",
    ],
    "order": ["stream", "source_sequence", "logical_position", "cross_source_order"],
    "codes": "O=OBSERVED;M=MISSING;P=PENDING;N=NOT_REACHED;I=INCOMPLETE. Cross:R=RECORDED;U=UNKNOWN;N=NOT_APPLICABLE. @n=values[n];@@=literal @. Cite f{citation_index}.",
    "task": {"agents": list(old.ACTOR_COLUMNS), "incidents": list(old.INCIDENT_COLUMNS)},
    "owners": "allocation item k=Incident-(k+1),value n=Actor-n,null=unassigned",
    "metadata": ["category", "source", "trust"],
    "stream_prefixes": list(old.STREAM_PREFIXES),
    "render_order": "NOT_CHRONOLOGY",
}


def _refs(node, expand=False):
    if not expand and type(node) is dict and set(node) == {"@"}:
        return "@" + str(node["@"])
    if type(node) is str:
        if expand and node.startswith("@@"):
            return node[1:]
        if expand and node.startswith("@") and node[1:].isdigit():
            return {"@": int(node[1:])}
        if not expand and node.startswith("@"):
            return "@" + node
    if type(node) is list:
        return [_refs(x, expand) for x in node]
    if type(node) is dict:
        return {k: _refs(v, expand) for k, v in node.items()}
    return node


def _key(kind, actor, payload, order):
    fixed = {
        "public_task": "public-task",
        "communication_coverage": "communication-coverage",
        "execution": "execution",
        "execution_coverage": "execution-coverage",
    }
    if kind in fixed:
        return fixed[kind]
    if kind == "message":
        return "message/" + str(payload["event_order"])
    if kind == "router_delivery":
        return "router/" + str(payload["source_sequence"])
    if kind == "arena_event":
        return "arena/" + order["stream"] + "-" + str(order["source_sequence"])
    return (
        {"proposal_slot": "proposal", "aig_action": "action", "consumer_receipt": "receipt"}[kind]
        + "/"
        + actor
        + "/"
        + str(payload["round"])
    )


def _sort(facts):
    return sorted(facts, key=lambda f: (f.kind, f.actor or "", f.fact_id))


def text_for(inventory, facts, view, selection_hash, counts):
    facts = _sort(facts)
    kinds = sorted({f.kind for f in facts})
    values = old._values(facts)
    index = {v: n for n, v in enumerate(values)}
    metadata = sorted({x for k in kinds for x in KIND_META[k]})

    def stream_ref(stream):
        if stream is not None:
            for n, prefix in enumerate(old.STREAM_PREFIXES):
                if stream.startswith(prefix) and old._dump(stream[len(prefix) :]) in index:
                    return [n, index[old._dump(stream[len(prefix) :])]]
        return stream

    streams = sorted(
        {s for f in facts if type(s := stream_ref(json.loads(f.ordering_json)["stream"])) is str}
    )
    head = {
        "v": MARKER,
        "episode": inventory.episode_public_id,
        "policy": inventory.observation_policy.value,
        "view": view.value,
        "selection": selection_hash,
        "omitted": counts,
        "values": [json.loads(v) for v in values],
        "kinds": [
            [k, sorted(PAYLOAD_FIELDS[k]), [metadata.index(x) for x in KIND_META[k]]] for k in kinds
        ],
        "metadata": metadata,
        "streams": streams,
        "layout": LAYOUT,
    }
    rows = []
    for n, f in enumerate(facts):
        ordering = json.loads(f.ordering_json)
        stream = stream_ref(ordering["stream"])
        stream = streams.index(stream) if type(stream) is str else stream
        row = [
            n,
            kinds.index(f.kind),
            None if f.actor is None else int(f.actor[-1]),
            COMPLETE[f.completeness],
            [
                stream,
                ordering["source_sequence"],
                ordering["logical_position"],
                old.CROSS[ordering["cross_source_order"]],
            ],
            _refs(old._intern(old._payload(f), index)),
        ]
        rows.append(row)
    if view == View.MAE:
        return old._dump(
            {
                "h": head,
                "groups": {
                    c: [r for r, f in zip(rows, facts, strict=True) if f.category == c]
                    for c in sorted(CATEGORIES[view])
                },
            }
        )
    return "\n".join([old._dump(head), *(old._dump(r) for r in rows)])


def view_of(text):
    if text.startswith('{"h":'):
        return closed_json(text, old.MAX_BYTES)["h"]["view"]
    return closed_json(text.split("\n", 1)[0], old.MAX_BYTES)["view"]


def extract(text, view):
    if len(text.encode("utf-8")) > old.MAX_BYTES:
        raise ValueError("TIGHT_TEXT_BOUND")
    if view == View.MAE:
        body = closed_json(text, old.MAX_BYTES)
        if set(body) != {"h", "groups"} or list(body["groups"]) != sorted(CATEGORIES[view]):
            raise ValueError("TIGHT_GROUPS")
        h = body["h"]
        rows = [(c, r) for c, rs in body["groups"].items() for r in rs]
    else:
        lines = text.split("\n")
        h = closed_json(lines[0], old.MAX_BYTES)
        rows = [(None, closed_json(line, 40000)) for line in lines[1:]]
    if (
        set(h)
        != {
            "v",
            "episode",
            "policy",
            "view",
            "selection",
            "omitted",
            "values",
            "kinds",
            "metadata",
            "streams",
            "layout",
        }
        or h["v"] != MARKER
        or h["view"] != view.value
        or h["layout"] != LAYOUT
    ):
        raise ValueError("TIGHT_HEADER")
    episode = _public_id(h["episode"])
    policy = ObservationPolicy(h["policy"])
    if (
        type(h["selection"]) is not str
        or len(h["selection"]) != 64
        or any(c not in "0123456789abcdef" for c in h["selection"])
    ):
        raise ValueError("TIGHT_SELECTION")
    if not 1 <= len(rows) <= 128 or len({r[1][0] for r in rows}) != len(rows):
        raise ValueError("TIGHT_ROWS")
    facts = []
    for category, row in rows:
        if type(row) is not list or len(row) != 6:
            raise ValueError("TIGHT_ROW")
        number, ki, actor, completeness, order, values = row
        if (
            type(number) is not int
            or not 0 <= number < len(rows)
            or type(ki) is not int
            or not 0 <= ki < len(h["kinds"])
        ):
            raise ValueError("TIGHT_INDICES")
        kind, columns, meta = h["kinds"][ki]
        if (
            kind not in KIND_META
            or columns != sorted(PAYLOAD_FIELDS[kind])
            or [h["metadata"][n] for n in meta] != list(KIND_META[kind])
        ):
            raise ValueError("TIGHT_LEGEND")
        if actor is not None and (type(actor) is not int or actor not in (1, 2, 3)):
            raise ValueError("TIGHT_ACTOR")
        actor = None if actor is None else f"Actor-{actor}"
        stream = order[0]
        if type(stream) is list:
            stream = old.STREAM_PREFIXES[stream[0]] + h["values"][stream[1]]
        elif stream is not None:
            stream = h["streams"][stream]
        payload = old._resolve(_refs(values, True), h["values"])
        if type(payload) is not list or len(payload) != len(columns):
            raise ValueError("TIGHT_PAYLOAD")
        p = dict(zip(columns, payload, strict=True))
        p = old.expand_task(p) if kind == "public_task" else old._allocations(p, True)
        ordering = {
            "stream": stream,
            "source_sequence": order[1],
            "logical_position": order[2],
            "cross_source_order": old.CODES["cross_source_order"][order[3]],
        }
        key = _key(kind, actor, p, ordering)
        fact = Fact(
            str(uuid5(UUID(episode), key)),
            *(
                [
                    KIND_META[kind][0],
                    kind,
                    actor,
                    canonical_json(p),
                    KIND_META[kind][1],
                    KIND_META[kind][2],
                    {v: k for k, v in COMPLETE.items()}[completeness],
                    canonical_json(ordering),
                ]
            ),
        )
        if category is not None and category != fact.category:
            raise ValueError("TIGHT_CATEGORY")
        if fact.category not in CATEGORIES[view]:
            raise ValueError("TIGHT_VIEW")
        facts.append(fact)
    facts = tuple(_sort(facts))
    if len({f.fact_id for f in facts}) != len(facts):
        raise ValueError("TIGHT_DUPLICATE")
    counts = h["omitted"]
    if list(counts) != sorted(CATEGORIES[view]) or any(
        type(n) is not int or not 0 <= n <= 128 for n in counts.values()
    ):
        raise ValueError("TIGHT_OMISSION")
    source = old._Source(episode, policy)
    if text_for(source, facts, view, h["selection"], counts) != text:
        raise ValueError("TIGHT_NONCANONICAL")
    # Reconstruct every original legend and provenance value from validated rows.
    header = old._header(source, facts, view, h["selection"], counts, old._values(facts))
    header["version"] = VERSION
    return header, facts


def render(
    inventory, selected_ids, mandatory_ids, selection_hash, view, envelope, *, token_counter=None
):
    inventory.__post_init__()
    eligible = [f for f in inventory.facts if f.category in CATEGORIES[view]]
    facts = tuple(f for f in eligible if f.fact_id in selected_ids)
    omitted = sorted(
        [
            {"fact_id": f.fact_id, "category": f.category, "kind": f.kind}
            for f in eligible
            if f.fact_id not in selected_ids
        ],
        key=lambda f: f["fact_id"],
    )
    counts = {c: sum(f["category"] == c for f in omitted) for c in sorted(CATEGORIES[view])}
    text = text_for(inventory, facts, view, selection_hash, counts)
    header, parsed = extract(text, view)
    if canonical_fact_records(facts) != canonical_fact_records(parsed):
        raise ValueError("TIGHT_INFORMATION_LOSS")
    manifest = {
        "version": VERSION,
        "header": header,
        "facts": canonical_fact_records(facts),
        "omitted": omitted,
        "mandatory_fact_ids": sorted(set(mandatory_ids) & {f.fact_id for f in facts}),
        "render_hash": content_hash(text),
        "envelope_hash": envelope.config_hash,
        "budget": envelope.budget(text, token_counter=token_counter),
        "reserved_output_tokens": envelope.reserved_output_tokens,
    }
    packet = old.CompactView(view, text, canonical_json(manifest), envelope)
    packet.verify()
    return packet


def citation_keys(text):
    _, facts = extract(text, View(view_of(text)))
    return tuple("f" + str(n) for n in range(len(facts)))


def resolve(text, keys):
    _, facts = extract(text, View(view_of(text)))
    known = {"f" + str(n): f.fact_id for n, f in enumerate(facts)}
    if len(set(keys)) != len(keys) or not set(keys) <= set(known):
        raise ValueError("UNOBSERVED_EVIDENCE_CITATION")
    return [known[k] for k in keys]
