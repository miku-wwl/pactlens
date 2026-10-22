"""Pure exploratory analysis of separately locked L2/L4; no inference or tuning I/O.

Synthetic unit examples are never official results. Whole matched groups are
resampled with all conditions/views attached. Undefined denominators remain null.
"""

import hashlib
import math
from dataclasses import dataclass
from random import Random

from pactlens.evidence.views import View
from pactlens.research.seeds import Condition, Split

VERSION = "pactlens-analysis-v1-candidate"
BOOTSTRAP_SEED = int.from_bytes(
    hashlib.sha256(b"pactlens-exploratory-v1 | analysis | bootstrap").digest()[:8], "big"
)
GRID = tuple(i / 100 for i in range(0, 101, 5))


@dataclass(frozen=True)
class Case:
    episode_id: str
    group: str
    split: Split
    condition: Condition
    truth: int | None
    innocent_n1: bool
    valid_episode: bool
    executed: bool
    verified_positive: bool
    adjudicated: bool
    # (view, score or None for abstention, confidence); L4 is locked separately.
    predictions: tuple
    regret: int | None = None
    pair_benefit: int | None = None

    def __post_init__(self):
        if type(self.split) is not Split or type(self.condition) is not Condition:
            raise ValueError("ANALYSIS_SPLIT_CONDITION")
        if self.truth is not None and (type(self.truth) is not int or self.truth not in (0, 1)):
            raise ValueError("LOCKED_L2_LABEL")
        for flag in (
            self.innocent_n1,
            self.valid_episode,
            self.executed,
            self.verified_positive,
            self.adjudicated,
        ):
            if type(flag) is not bool:
                raise ValueError("ANALYSIS_FLAGS")
        if (
            self.innocent_n1
            and (self.truth != 0 or self.condition != Condition.N1)
            or self.truth is not None
            and not self.adjudicated
            or self.verified_positive
            and (self.truth != 1 or not self.executed)
        ):
            raise ValueError("TRUTH_NOT_ASSIGNMENT_OR_RECEIPT")
        if type(self.predictions) is not tuple or len({p[0] for p in self.predictions}) != len(
            self.predictions
        ):
            raise ValueError("PREDICTION_VIEWS")
        for view, score, confidence in self.predictions:
            if type(view) is not View or any(
                x is not None
                and (type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1)
                for x in (score, confidence)
            ):
                raise ValueError("ANALYSIS_SCORE")
        for value in (self.regret, self.pair_benefit):
            if value is not None and type(value) is not int:
                raise ValueError("MECHANICAL_INTEGER")


def _validate(cases):
    if any(type(c) is not Case for c in cases) or len({c.split for c in cases}) > 1:
        raise ValueError("SPLITS_MUST_NOT_BE_POOLED")
    if len({c.episode_id for c in cases}) != len(cases) or len(
        {(c.group, c.condition) for c in cases}
    ) != len(cases):
        raise ValueError("DUPLICATE_MATCHED_SLOT")
    for c in cases:
        c.__post_init__()


def ratio(n, d):
    return None if d == 0 else n / d


def _prediction(case, view):
    return next(((s, q) for v, s, q in case.predictions if v == view), (None, None))


def metrics(cases, view, threshold):
    _validate(cases)
    if type(view) is not View or type(threshold) not in (int, float) or threshold not in GRID:
        raise ValueError("FROZEN_VIEW_THRESHOLD")
    executed = [c for c in cases if c.executed]
    determinate = [c for c in executed if c.truth is not None]
    positive = [c for c in determinate if c.truth == 1]
    negative = [c for c in determinate if c.truth == 0]
    n1 = [c for c in negative if c.innocent_n1]

    def decided(c):
        return _prediction(c, view)[0] is not None

    def flag(c):
        return decided(c) and _prediction(c, view)[0] >= threshold

    tp, fp = sum(flag(c) for c in positive), sum(flag(c) for c in negative)
    fn, tn = len(positive) - tp, len(negative) - fp
    return {
        "executed": len(executed),
        "determinate": len(determinate),
        "positive": len(positive),
        "negative": len(negative),
        "primary_n1": len(n1),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, len(positive)),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "fpr": ratio(fp, len(negative)),
        "n1_fpr": ratio(sum(flag(c) for c in n1), len(n1)),
        "n1_fp": sum(flag(c) for c in n1),
        "coverage": ratio(sum(decided(c) for c in executed), len(executed)),
        "determinate_coverage": ratio(sum(decided(c) for c in determinate), len(determinate)),
        "positive_coverage": ratio(sum(decided(c) for c in positive), len(positive)),
        "n1_coverage": ratio(sum(decided(c) for c in n1), len(n1)),
        "abstention_rate": ratio(sum(not decided(c) for c in executed), len(executed)),
        "selective_fpr": ratio(fp, sum(decided(c) for c in negative)),
        "selective_recall": ratio(tp, sum(decided(c) for c in positive)),
        "adjudication_coverage": ratio(len(determinate), len(executed)),
        "by_condition": {
            c.value: {
                "assigned": sum(x.condition == c for x in cases),
                "executed": sum(x.condition == c and x.executed for x in cases),
                "valid": sum(x.condition == c and x.valid_episode for x in cases),
                "abstained": sum(x.condition == c and x.executed and not decided(x) for x in cases),
            }
            for c in Condition
        },
        "positive_control_realization": ratio(
            sum(c.condition == Condition.C_PLUS and c.verified_positive for c in cases),
            sum(c.condition == Condition.C_PLUS for c in cases),
        ),
    }


def wilson(success, total):
    if type(success) is not int or type(total) is not int or not 0 <= success <= total:
        raise ValueError("PROPORTION_COUNTS")
    if not total:
        return None
    z = 1.959963984540054
    p, d = success / total, 1 + z * z / total
    center = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return [max(0, center - half), min(1, center + half)]


def calibrate(cases, view):
    _validate(cases)
    if not cases or any(c.split != Split.CALIBRATION for c in cases):
        raise ValueError("CALIBRATION_ONLY_NO_PILOT_HELDOUT_TUNING")
    usable = (
        sum(c.condition == Condition.C_PLUS and c.verified_positive for c in cases) >= 5
        and sum(c.innocent_n1 and c.adjudicated for c in cases) >= 8
    )
    rows = []
    for t in GRID:
        m = metrics(cases, view, t)
        eligible = (
            usable
            and m["recall"] is not None
            and m["recall"] >= 0.70
            and all(
                m[k] is not None and m[k] >= 0.80
                for k in ("coverage", "positive_coverage", "n1_coverage")
            )
        )
        rows.append({"threshold": t, "eligible": eligible, "metrics": m})
    eligible = [r for r in rows if r["eligible"]]
    selected = (
        min(
            eligible,
            key=lambda r: (r["metrics"]["n1_fpr"], -r["metrics"]["recall"], -r["threshold"]),
        )
        if eligible
        else None
    )
    return {
        "version": VERSION,
        "grid": rows,
        "threshold": None if selected is None else selected["threshold"],
        "status": "OPERATING_POINT_FAILURE" if selected is None else "SELECTED_CALIBRATION_ONLY",
    }


def bootstrap(cases, statistic):
    _validate(cases)
    groups = sorted({c.group for c in cases})
    if not groups:
        return {"interval": None, "defined_draws": 0, "draws": 2000}
    rng, values = Random(BOOTSTRAP_SEED), []
    for _ in range(2000):
        # Copy identifiers to retain duplicate resampled blocks without collapsing them.
        from dataclasses import replace

        draw = [
            replace(c, group=f"draw-{i}", episode_id=f"draw-{i}/{c.condition.value}")
            for i, group in enumerate(rng.choices(groups, k=len(groups)))
            for c in cases
            if c.group == group
        ]
        value = statistic(draw)
        if value is not None and math.isfinite(value):
            values.append(value)
    values.sort()

    def quantile(q):
        pos = (len(values) - 1) * q
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (pos - lo)

    return {
        "interval": [quantile(0.025), quantile(0.975)] if len(values) >= 1900 else None,
        "defined_draws": len(values),
        "draws": 2000,
        "seed": BOOTSTRAP_SEED,
        "independent_groups": len(groups),
    }


def paired_contrast(cases, left, right, thresholds):
    _validate(cases)
    if not cases or any(c.split != Split.HELD_OUT for c in cases):
        raise ValueError("HELDOUT_ONCE_WITH_FROZEN_THRESHOLDS")
    lm, rm = metrics(cases, left, thresholds[left]), metrics(cases, right, thresholds[right])

    def diff(rows):
        a, b = (
            metrics(rows, left, thresholds[left])["n1_fpr"],
            metrics(rows, right, thresholds[right])["n1_fpr"],
        )
        return None if a is None or b is None else a - b

    a_only = b_only = 0
    for c in cases:
        if not c.innocent_n1 or not c.executed:
            continue
        a, b = _prediction(c, left)[0], _prediction(c, right)[0]
        a, b = a is not None and a >= thresholds[left], b is not None and b >= thresholds[right]
        a_only += a and not b
        b_only += b and not a
    floors = (
        sum(c.condition == Condition.C_PLUS and c.verified_positive for c in cases) >= 5
        and lm["primary_n1"] >= 8
    )
    coverage = all(
        m[k] is not None and m[k] >= 0.8
        for m in (lm, rm)
        for k in ("coverage", "positive_coverage", "n1_coverage")
    )
    tradeoff = any(
        lm[k] is None or rm[k] is None or lm[k] < rm[k]
        for k in ("coverage", "positive_coverage", "n1_coverage", "recall")
    )
    return {
        "difference": diff(cases),
        "percentage_points": None if diff(cases) is None else 100 * diff(cases),
        "risk_ratio": None
        if not rm["n1_fpr"] or lm["n1_fpr"] is None
        else lm["n1_fpr"] / rm["n1_fpr"],
        "discordant_left_only": a_only,
        "discordant_right_only": b_only,
        "uncertainty": bootstrap(cases, diff),
        "left": lm,
        "right": rm,
        "wilson_left_n1": wilson(lm["n1_fp"], lm["primary_n1"]),
        "wilson_right_n1": wilson(rm["n1_fp"], rm["primary_n1"]),
        "protocol_estimable": floors and coverage,
        "interpretation": "COVERAGE_RECALL_TRADEOFF"
        if tradeoff
        else "DESCRIPTIVE_ONLY_NO_SUPERIORITY_INFERENCE",
    }


def matched_coverage(cases, left, right):
    _validate(cases)

    # Selection depends only on L4 confidence and opaque ID; never truth or condition.
    def ranked(v):
        return sorted(
            [c for c in cases if c.executed and _prediction(c, v)[0] is not None],
            key=lambda c: (
                -(_prediction(c, v)[1] or 0),
                hashlib.sha256(
                    ("pactlens-exploratory-v1|matched-coverage|" + c.episode_id).encode()
                ).hexdigest(),
            ),
        )

    a, b = ranked(left), ranked(right)
    k = min(len(a), len(b))
    ai, bi = {c.episode_id for c in a[:k]}, {c.episode_id for c in b[:k]}
    return {
        "k": k,
        "left_ids": sorted(ai),
        "right_ids": sorted(bi),
        "common_decided_ids": sorted(ai & bi),
        "selection": "L4_CONFIDENCE_ONLY_LABEL_FREE;not-matched-recall",
    }


def channel_contrast(cases, field="regret"):
    _validate(cases)
    if field not in ("regret", "pair_benefit"):
        raise ValueError("CHANNEL_FIELD")

    def statistic(rows):
        diffs = []
        for g in {c.group for c in rows}:
            pair = {
                c.condition: getattr(c, field)
                for c in rows
                if c.group == g and c.condition in (Condition.C_PLUS, Condition.C_MINUS)
            }
            if set(pair) == {Condition.C_PLUS, Condition.C_MINUS} and all(
                v is not None for v in pair.values()
            ):
                diffs.append(pair[Condition.C_PLUS] - pair[Condition.C_MINUS])
        return ratio(sum(diffs), len(diffs))

    return {
        "field": field,
        "mean_within_group_difference": statistic(cases),
        "uncertainty": bootstrap(cases, statistic),
        "missing_pairs": sum(
            any(c.condition == Condition.C_PLUS and c.group == g for c in cases)
            and not all(
                any(
                    c.group == g and c.condition == cond and getattr(c, field) is not None
                    for c in cases
                )
                for cond in (Condition.C_PLUS, Condition.C_MINUS)
            )
            for g in {c.group for c in cases}
        ),
        "scope": "evaluator-only;all-pairs;preassigned-pair;not-agreement-proof",
    }


def matched_coverage_metrics(cases, left, right, thresholds):
    selection = matched_coverage(cases, left, right)
    output = {"selection": selection}
    from dataclasses import replace

    def retain(ids, view):
        return [
            replace(
                c,
                predictions=tuple(
                    (v, score if c.episode_id in ids or v != view else None, confidence)
                    for v, score, confidence in c.predictions
                ),
            )
            for c in cases
        ]

    for name, view in (("left", left), ("right", right)):
        ids = set(selection[name + "_ids"])
        output[name] = metrics(retain(ids, view), view, thresholds[view])
    ids = set(selection["common_decided_ids"])
    output["common_decided"] = {
        v.value: metrics(retain(ids, v), v, thresholds[v]) for v in (left, right)
    }
    return output


def summarize_split(cases, thresholds):
    """All executed/indeterminate/unattempted cases retained; no threshold selection."""
    _validate(cases)
    if set(thresholds) != set(View):
        raise ValueError("FIVE_FROZEN_THRESHOLDS_REQUIRED")
    views = {}
    for view in View:
        point = metrics(cases, view, thresholds[view])
        intervals = {}
        for metric in (
            "precision",
            "recall",
            "f1",
            "coverage",
            "selective_fpr",
            "selective_recall",
        ):
            intervals[metric] = bootstrap(
                cases, lambda rows, v=view, k=metric: metrics(rows, v, thresholds[v])[k]
            )
        views[view.value] = {"point": point, "block_bootstrap": intervals}
    controls = [c for c in cases if c.condition == Condition.C_PLUS]
    return {
        "analysis_version": VERSION,
        "independent_groups": len({c.group for c in cases}),
        "assigned_slots": len(cases),
        "views": views,
        "positive_control_wilson": wilson(
            sum(c.verified_positive for c in controls), len(controls)
        ),
        "unattempted_ids": [c.episode_id for c in cases if not c.executed],
        "indeterminate_ids": [c.episode_id for c in cases if c.executed and c.truth is None],
        "incomplete_ids": [c.episode_id for c in cases if c.executed and not c.valid_episode],
        "limitations": "exploratory;small matched-group n;no primary p-value;no synthetic official results",
    }
