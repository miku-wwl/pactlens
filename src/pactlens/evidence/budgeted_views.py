"""Lossless table encoding: flat JSONL versus grouped JSON of matched facts."""

import json
from dataclasses import dataclass
from uuid import UUID

from pactlens.agents.budgets import TokenBudget
from pactlens.agents.models import closed_json
from pactlens.evidence.inventory import KIND_META, PAYLOAD_FIELDS, Fact
from pactlens.evidence.observation_policy import ObservationPolicy
from pactlens.evidence.projection import _public_id
from pactlens.evidence.renderers import canonical_fact_records
from pactlens.evidence.views import CATEGORIES, View
from pactlens.research.detector_contract import DetectorEnvelope
from pactlens.serialization import canonical_json, content_hash

VERSION = "pactlens-budgeted-facts-v1-candidate"
TABLE_VERSION = "pactlens-lossless-public-tables-v1"
MAX_BYTES = 262144
ACTOR_COLUMNS = ("id", "skills", "capacity", "unit_cost", "speed")
INCIDENT_COLUMNS = (
    "id",
    "workload",
    "severity",
    "required_skill",
    "deadline",
    "sla_penalty",
    "eligible_agents",
)
ORDER_COLUMNS = ("stream", "source_sequence", "logical_position", "cross_source_order")
FACT_COLUMNS = ("fact_id", "kind", "actor", "payload_index", "completeness", "ordering_index")


def compact_task(task):
    if type(task) is not dict or set(task) != {"agents", "incidents", "objective"}:
        raise ValueError("PUBLIC_TASK_FIELDS")
    result = {"objective": task["objective"]}
    for key, columns in (("agents", ACTOR_COLUMNS), ("incidents", INCIDENT_COLUMNS)):
        result[key] = []
        for row in task[key]:
            if set(row) != set(columns):
                raise ValueError("PUBLIC_TASK_COLUMNS")
            result[key].append([row[c] for c in columns])
    return result


def expand_task(task):
    if type(task) is not dict or set(task) != {"agents", "incidents", "objective"}:
        raise ValueError("PUBLIC_TASK_TABLE")
    result = {"objective": task["objective"]}
    for key, columns in (("agents", ACTOR_COLUMNS), ("incidents", INCIDENT_COLUMNS)):
        if type(task[key]) is not list:
            raise ValueError("PUBLIC_TASK_TABLE")
        result[key] = []
        for row in task[key]:
            if type(row) is not list or len(row) != len(columns):
                raise ValueError("PUBLIC_TASK_TABLE_COLUMNS")
            result[key].append(dict(zip(columns, row, strict=True)))
    return result


def _allocation_tables(value, expand=False):
    if type(value) is dict:
        result = {}
        for key, item in value.items():
            if key in ("assignments", "allocation") and item is not None:
                if type(item) is not list:
                    raise ValueError("ALLOCATION_TABLE")
                rows = []
                for row in item:
                    if expand:
                        if type(row) is not list or len(row) != 2:
                            raise ValueError("ALLOCATION_TABLE_COLUMNS")
                        incident, actor = row
                        if (
                            type(incident) is not int
                            or not 1 <= incident <= 5
                            or (
                                actor is not None
                                and (type(actor) is not int or not 1 <= actor <= 3)
                            )
                        ):
                            raise ValueError("PUBLIC_ALLOCATION_CODES")
                        rows.append(
                            {
                                "incident": f"Incident-{incident}",
                                "agent": None if actor is None else f"Actor-{actor}",
                            }
                        )
                    else:
                        if type(row) is not dict or set(row) != {"incident", "agent"}:
                            raise ValueError("ALLOCATION_FIELDS")
                        incident, actor = row["incident"], row["agent"]
                        if incident not in tuple(f"Incident-{i}" for i in range(1, 6)) or (
                            actor is not None and actor not in ("Actor-1", "Actor-2", "Actor-3")
                        ):
                            raise ValueError("PUBLIC_ALLOCATION_ALIASES")
                        rows.append([int(incident[-1]), None if actor is None else int(actor[-1])])
                result[key] = rows
            else:
                result[key] = _allocation_tables(item, expand)
        return result
    if type(value) is list:
        return [_allocation_tables(x, expand) for x in value]
    return value


def _payload(fact):
    body = json.loads(fact.payload_json)
    body = compact_task(body) if fact.kind == "public_task" else _allocation_tables(body)
    return [body[c] for c in sorted(PAYLOAD_FIELDS[fact.kind])]


def _row(fact, ordering_table, payload_table):
    order = json.loads(fact.ordering_json)
    return [
        fact.fact_id,
        fact.kind,
        fact.actor,
        payload_table.index(_payload(fact)),
        fact.completeness,
        ordering_table.index([order[c] for c in ORDER_COLUMNS]),
    ]


def _fact(row, ordering_table, payload_table):
    if type(row) is not list or len(row) != len(FACT_COLUMNS):
        raise ValueError("COMPACT_FACT_COLUMNS")
    identity, kind, actor, payload, completeness, order = row
    if (
        kind not in KIND_META
        or type(payload_table) is not list
        or type(payload) is not int
        or not 0 <= payload < len(payload_table)
        or type(ordering_table) is not list
        or type(order) is not int
        or not 0 <= order < len(ordering_table)
    ):
        raise ValueError("COMPACT_FACT_SHAPE")
    payload = payload_table[payload]
    if type(payload) is not list or len(payload) != len(PAYLOAD_FIELDS[kind]):
        raise ValueError("PAYLOAD_TABLE_COLUMNS")
    order = ordering_table[order]
    if type(order) is not list or len(order) != len(ORDER_COLUMNS):
        raise ValueError("ORDERING_TABLE_COLUMNS")
    body = dict(zip(sorted(PAYLOAD_FIELDS[kind]), payload, strict=True))
    body = expand_task(body) if kind == "public_task" else _allocation_tables(body, True)
    category, source, trust = KIND_META[kind]
    return Fact(
        identity,
        category,
        kind,
        actor,
        canonical_json(body),
        source,
        trust,
        completeness,
        canonical_json(dict(zip(ORDER_COLUMNS, order, strict=True))),
    )


def extract_budgeted(text, view):
    if type(view) is not View or type(text) is not str or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("BOUNDED_BUDGETED_TEXT")
    if view == View.MAE:
        body = closed_json(text, MAX_BYTES)
        if type(body) is not dict or set(body) != {"header", "groups"}:
            raise ValueError("GROUPED_TABLE_FIELDS")
        header, groups = body["header"], body["groups"]
        if type(groups) is not dict or set(groups) != set(CATEGORIES[view]):
            raise ValueError("GROUPED_TABLE_CATEGORIES")
        rows = []
        for category in sorted(groups):
            if type(groups[category]) is not list:
                raise ValueError("GROUPED_TABLE_ROWS")
            for row in groups[category]:
                if type(header) is not dict:
                    raise ValueError("BUDGETED_HEADER_FIELDS")
                fact = _fact(row, header.get("ordering_table"), header.get("payload_table"))
                if fact.category != category:
                    raise ValueError("WRONG_TABLE_GROUP")
                rows.append(fact)
    else:
        lines = text.splitlines()
        if not 2 <= len(lines) <= 129:
            raise ValueError("FLAT_TABLE_LINES")
        header = closed_json(lines[0], MAX_BYTES)
        if type(header) is not dict:
            raise ValueError("BUDGETED_HEADER_FIELDS")
        rows = [
            _fact(
                closed_json(line, 40000), header.get("ordering_table"), header.get("payload_table")
            )
            for line in lines[1:]
        ]
    if type(header) is not dict or set(header) != {
        "version",
        "episode",
        "policy",
        "view",
        "selection_hash",
        "table_version",
        "fact_columns",
        "payload_columns",
        "payload_table",
        "kind_metadata",
        "kind_metadata_columns",
        "ordering_columns",
        "ordering_table",
        "task_columns",
        "allocation_columns",
        "allocation_codes",
        "scope",
        "omitted_by_category",
        "render_order",
    }:
        raise ValueError("BUDGETED_HEADER_FIELDS")
    _public_id(header["episode"])
    ObservationPolicy(header["policy"])
    if (
        type(header["selection_hash"]) is not str
        or len(header["selection_hash"]) != 64
        or any(c not in "0123456789abcdef" for c in header["selection_hash"])
    ):
        raise ValueError("SELECTION_CONFIG_HASH")
    if (
        not rows
        or len(rows) > 128
        or len({f.fact_id for f in rows}) != len(rows)
        or any(f.category not in CATEGORIES[view] for f in rows)
    ):
        raise ValueError("BUDGETED_FACT_SET")
    kinds = sorted({f.kind for f in rows})
    expected_orders = sorted(
        {canonical_json([json.loads(f.ordering_json)[c] for c in ORDER_COLUMNS]) for f in rows}
    )
    if (
        header["version"] != VERSION
        or header["view"] != view.value
        or header["table_version"] != TABLE_VERSION
        or header["fact_columns"] != list(FACT_COLUMNS)
        or header["ordering_columns"] != list(ORDER_COLUMNS)
        or header["ordering_table"] != [json.loads(x) for x in expected_orders]
        or header["allocation_columns"] != ["incident", "agent"]
        or header["allocation_codes"]
        != {"incident": "n=Incident-n(1..5)", "agent": "n=Actor-n(1..3);null=unassigned"}
        or header["task_columns"]
        != {"agents": list(ACTOR_COLUMNS), "incidents": list(INCIDENT_COLUMNS)}
        or header["payload_columns"] != {k: sorted(PAYLOAD_FIELDS[k]) for k in kinds}
        or header["payload_table"]
        != [json.loads(x) for x in sorted({canonical_json(_payload(f)) for f in rows})]
        or header["kind_metadata"] != {k: list(KIND_META[k]) for k in kinds}
        or header["kind_metadata_columns"] != ["category", "source", "trust"]
        or header["render_order"] != "PRESENTATION_ORDER_NOT_CHRONOLOGY"
    ):
        raise ValueError("BUDGETED_TABLE_LEGEND")
    counts = header["omitted_by_category"]
    if (
        type(counts) is not dict
        or set(counts) != set(CATEGORIES[view])
        or any(type(x) is not int or not 0 <= x <= 128 for x in counts.values())
    ):
        raise ValueError("OMISSION_COVERAGE")
    expected = (
        "SELECTED_SUBSET_NOT_COMPLETE_SOURCE" if any(counts.values()) else "FULL_ELIGIBLE_SOURCE"
    )
    if header["scope"] != expected:
        raise ValueError("FALSE_COMPLETENESS")
    return header, tuple(rows)


@dataclass(frozen=True)
class BudgetedView:
    view: View
    text: str
    manifest_json: str
    envelope: DetectorEnvelope

    def verify(self):
        header, facts = extract_budgeted(self.text, self.view)
        manifest = closed_json(self.manifest_json, 2 * MAX_BYTES)
        if type(manifest) is not dict or set(manifest) != {
            "version",
            "header",
            "facts",
            "omitted",
            "mandatory_fact_ids",
            "render_hash",
            "envelope_hash",
            "budget",
            "reserved_output_tokens",
        }:
            raise ValueError("BUDGETED_MANIFEST_FIELDS")
        budget = TokenBudget(**manifest["budget"])
        estimated = self.envelope.budget(self.text)
        if (budget.limit, budget.utf8_bytes, budget.estimated_tokens) != (
            estimated.limit,
            estimated.utf8_bytes,
            estimated.estimated_tokens,
        ):
            raise ValueError("COMPLETE_REQUEST_BUDGET_MISMATCH")
        omitted = manifest["omitted"]
        if type(omitted) is not list or any(
            type(x) is not dict
            or set(x) != {"fact_id", "category", "kind"}
            or x["kind"] not in KIND_META
            or x["category"] != KIND_META[x["kind"]][0]
            or x["category"] not in CATEGORIES[self.view]
            for x in omitted
        ):
            raise ValueError("OMITTED_MANIFEST")
        omitted_ids = {x["fact_id"] for x in omitted}
        if any(
            type(x) is not str or str(UUID(x)) != x or UUID(x).version != 5 for x in omitted_ids
        ):
            raise ValueError("OPAQUE_OMITTED_FACT_ID")
        selected_ids = {f.fact_id for f in facts}
        if len(omitted_ids) != len(omitted) or omitted_ids & selected_ids:
            raise ValueError("OMITTED_FACT_IDENTITY")
        counts = {
            k: sum(x["category"] == k for x in omitted) for k in sorted(CATEGORIES[self.view])
        }
        if (
            manifest["version"] != VERSION
            or manifest["header"] != header
            or manifest["facts"] != canonical_fact_records(facts)
            or manifest["render_hash"] != content_hash(self.text)
            or manifest["envelope_hash"] != self.envelope.config_hash
            or manifest["reserved_output_tokens"] != self.envelope.reserved_output_tokens
            or counts != header["omitted_by_category"]
            or not set(manifest["mandatory_fact_ids"]) <= selected_ids
        ):
            raise ValueError("BUDGETED_MANIFEST_BINDING")
        return header, facts

    def conversation(self, *, token_counter=None):
        self.verify()
        self.envelope.budget(self.text, token_counter=token_counter, require=True)
        return self.envelope.turns(self.text)


def render_budgeted(
    inventory, selected_ids, mandatory_ids, selection_hash, view, envelope, *, token_counter=None
):
    inventory.__post_init__()
    eligible = [f for f in inventory.facts if f.category in CATEGORIES[view]]
    facts = tuple(f for f in eligible if f.fact_id in selected_ids)
    omitted = [
        {"fact_id": f.fact_id, "category": f.category, "kind": f.kind}
        for f in eligible
        if f.fact_id not in selected_ids
    ]
    omitted.sort(key=lambda x: x["fact_id"])
    kinds = sorted({f.kind for f in facts})
    payload_table = [json.loads(x) for x in sorted({canonical_json(_payload(f)) for f in facts})]
    ordering_table = [
        json.loads(x)
        for x in sorted(
            {canonical_json([json.loads(f.ordering_json)[c] for c in ORDER_COLUMNS]) for f in facts}
        )
    ]
    counts = {k: sum(x["category"] == k for x in omitted) for k in sorted(CATEGORIES[view])}
    header = {
        "version": VERSION,
        "episode": inventory.episode_public_id,
        "policy": inventory.observation_policy.value,
        "view": view.value,
        "selection_hash": selection_hash,
        "table_version": TABLE_VERSION,
        "fact_columns": FACT_COLUMNS,
        "payload_columns": {k: sorted(PAYLOAD_FIELDS[k]) for k in kinds},
        "payload_table": payload_table,
        "kind_metadata": {k: KIND_META[k] for k in kinds},
        "kind_metadata_columns": ["category", "source", "trust"],
        "ordering_columns": ORDER_COLUMNS,
        "ordering_table": ordering_table,
        "task_columns": {"agents": ACTOR_COLUMNS, "incidents": INCIDENT_COLUMNS},
        "allocation_columns": ("incident", "agent"),
        "allocation_codes": {
            "incident": "n=Incident-n(1..5)",
            "agent": "n=Actor-n(1..3);null=unassigned",
        },
        "scope": "SELECTED_SUBSET_NOT_COMPLETE_SOURCE" if omitted else "FULL_ELIGIBLE_SOURCE",
        "omitted_by_category": counts,
        "render_order": "PRESENTATION_ORDER_NOT_CHRONOLOGY",
    }
    if view == View.MAE:
        text = canonical_json(
            {
                "header": header,
                "groups": {
                    category: [
                        _row(f, ordering_table, payload_table)
                        for f in sorted(facts, key=lambda f: (f.actor or "", f.kind, f.fact_id))
                        if f.category == category
                    ]
                    for category in sorted(CATEGORIES[view])
                },
            }
        )
    else:
        text = "\n".join(
            (
                canonical_json(header),
                *(
                    canonical_json(_row(f, ordering_table, payload_table))
                    for f in sorted(facts, key=lambda f: (f.kind, f.actor or "", f.fact_id))
                ),
            )
        )
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("BUDGETED_RENDER_BYTE_BOUND")
    budget = envelope.budget(text, token_counter=token_counter)
    manifest = {
        "version": VERSION,
        "header": header,
        "facts": canonical_fact_records(facts),
        "omitted": omitted,
        "mandatory_fact_ids": sorted(mandatory_ids & {f.fact_id for f in facts}),
        "render_hash": content_hash(text),
        "envelope_hash": envelope.config_hash,
        "budget": budget,
        "reserved_output_tokens": envelope.reserved_output_tokens,
    }
    rendered = BudgetedView(view, text, canonical_json(manifest), envelope)
    rendered.verify()
    return rendered


def verify_budgeted_parity(raw, grouped):
    if raw.view != View.R or grouped.view != View.MAE:
        raise ValueError("R_MAE_REQUIRED")
    rh, rf = raw.verify()
    gh, gf = grouped.verify()
    for key in ("episode", "policy", "selection_hash", "scope", "omitted_by_category"):
        if rh[key] != gh[key]:
            raise ValueError("BUDGETED_INFORMATION_MISMATCH")
    rm, gm = json.loads(raw.manifest_json), json.loads(grouped.manifest_json)
    if (
        canonical_fact_records(rf) != canonical_fact_records(gf)
        or rm["omitted"] != gm["omitted"]
        or rm["mandatory_fact_ids"] != gm["mandatory_fact_ids"]
        or raw.envelope != grouped.envelope
    ):
        raise ValueError("BUDGETED_INFORMATION_MISMATCH")
    return True
