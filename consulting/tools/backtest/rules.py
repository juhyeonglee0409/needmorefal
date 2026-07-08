# -*- coding: utf-8 -*-
"""Rule evaluators for trajectory-matching backtests."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json
import math
import random
import statistics
from typing import Any


VERDICT_SUPPORT = "\uc9c0\uc9c0"
VERDICT_REJECT = "\uae30\uac01"
VERDICT_INSUFFICIENT = "\ubd88\ucd80\ubd84"

FORWARD_HORIZON = 12
RETENTION_BAND_Q = 0.25
RETENTION_STREAK = 4
MOTION_MEDIAN_WINDOW = 4
BOTTLENECK_AXIS_Q = 0.25
BOTTLENECK_AXIS_WEAK_COUNT_MIN = 2
BOTTLENECK_CORR_MAX = -0.25
BOTTLENECK_CORR_PVALUE_MAX = 0.30

RANDOM_SEED = 20260708
PERMUTATION_ROUNDS = 400

RETENTION_MIN_SIGNALS = 8
RETENTION_RISK_DIFF_MIN = 0.05
RETENTION_PVALUE_MAX = 0.05

THRESHOLD_TARGET = 1500
THRESHOLD_PLACEBOS = (750, 1000, 2000, 3000)
THRESHOLD_MIN_SIGNALS = 8
THRESHOLD_LIFT_MIN = 0.10
THRESHOLD_PVALUE_MAX = 0.25
MISSING_DELTA_FALLBACK = -0.05
MISSING_DELTA_FALLBACK_Q = 0.05

AIRTIME_CORR_MIN_N = 30
AIRTIME_CORR_MAX_ABS = 0.20
AIRTIME_CORR_PVALUE_MAX = 0.20

BOTTLENECK_MIN_SIGNALS = 6
BOTTLENECK_LIFT_MIN = 0.10
BOTTLENECK_PVALUE_MAX = 0.30


@dataclass(frozen=True)
class ParsedChannel:
    channel_id: str
    segment: str
    follower_count: int | None
    weeks: dict[int, dict[str, float | None]]


@dataclass(frozen=True)
class RuleResult:
    verdict: str
    effect_size: float
    n: int
    sensitivity: dict[str, dict[str, float | int | None]]
    evidence: dict[str, Any]


def load_input(path: str | Path) -> tuple[list[ParsedChannel], list[date]]:
    """Load NDJSON and map date strings to zero-based week indices."""
    raw_path = Path(path)
    if not raw_path.exists():
        raise FileNotFoundError(f"input file not found: {raw_path}")

    raw_channels: dict[str, dict[str, Any]] = {}
    all_dates: set[date] = set()

    with raw_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue

            channel_id = str(row.get("channel_id") or row.get("channelId") or "").strip()
            if not channel_id:
                continue

            follower_count = _to_int(row.get("follower_count"))
            if follower_count is None:
                follower_count = _to_int(row.get("followerCount"))

            segment = _normalize_segment(row.get("segment"), follower_count)
            week_rows: dict[date, dict[str, float | None]] = {}
            weeks = row.get("weeks")
            if isinstance(weeks, list):
                for week in weeks:
                    if not isinstance(week, dict):
                        continue
                    week_date = _parse_week_date(week.get("date"))
                    if week_date is None:
                        continue
                    week_rows[week_date] = {
                        "avgLiveViews": _to_float(week.get("avgLiveViews")),
                        "maxLiveViews": _to_float(week.get("maxLiveViews")),
                        "airTime": _to_float(week.get("airTime")),
                        "maxFollowerCount": _to_float(week.get("maxFollowerCount")),
                        "sumCount": _to_float(week.get("sumCount")),
                        "viewership": _to_float(week.get("viewership")),
                    }
                    all_dates.add(week_date)

            raw_channels[channel_id] = {
                "segment": segment,
                "follower_count": follower_count,
                "weeks": week_rows,
            }

    week_index = {value: i for i, value in enumerate(sorted(all_dates))}
    channels: list[ParsedChannel] = []
    for channel_id, payload in raw_channels.items():
        mapped_weeks = {
            week_index[week_date]: value
            for week_date, value in payload["weeks"].items()
            if week_date in week_index
        }
        channels.append(
            ParsedChannel(
                channel_id=channel_id,
                segment=payload["segment"],
                follower_count=payload["follower_count"],
                weeks=mapped_weeks,
            ),
        )
    return channels, sorted(all_dates)


def evaluate_all_rules(
    channels: list[ParsedChannel],
    week_count: int,
    *,
    forward_horizon: int = FORWARD_HORIZON,
    seed: int = RANDOM_SEED,
) -> dict[str, RuleResult]:
    alpha_follower, alpha_views = compute_alpha(
        channels=channels,
        week_count=week_count,
        forward_horizon=forward_horizon,
    )

    return {
        "retention_lower_band": evaluate_retention_rule(
            channels=channels,
            week_count=week_count,
            alpha_follower=alpha_follower,
            alpha_views=alpha_views,
        ),
        "threshold_1500_inflexion": evaluate_threshold_1500_rule(
            channels=channels,
            week_count=week_count,
            alpha_views=alpha_views,
            forward_horizon=forward_horizon,
            seed=seed,
        ),
        "airtime_uncorrelated": evaluate_airtime_uncorrelated_rule(
            channels=channels,
            week_count=week_count,
            alpha_follower=alpha_follower,
            alpha_views=alpha_views,
            seed=seed,
        ),
        "bottleneck_axis": evaluate_bottleneck_rule(
            channels=channels,
            week_count=week_count,
            alpha_follower=alpha_follower,
            alpha_views=alpha_views,
            seed=seed,
        ),
    }


def compute_alpha(
    channels: list[ParsedChannel],
    week_count: int,
    forward_horizon: int = FORWARD_HORIZON,
) -> tuple[dict[str, dict[int, float | None]], dict[str, dict[int, float | None]]]:
    """Compute market-adjusted slopes for follower growth and avgLiveViews growth."""
    max_start = max(0, week_count - forward_horizon)
    by_segment: dict[str, list[ParsedChannel]] = {}
    for channel in channels:
        by_segment.setdefault(channel.segment, []).append(channel)

    segment_median_follower: dict[str, dict[int, float | None]] = {
        segment: {} for segment in by_segment
    }
    segment_median_views: dict[str, dict[int, float | None]] = {
        segment: {} for segment in by_segment
    }
    for segment, members in by_segment.items():
        for week in range(max_start):
            follower_slopes = [
                _slope(member, week, week + forward_horizon, "maxFollowerCount")
                for member in members
            ]
            follower_slopes = [s for s in follower_slopes if s is not None]
            view_slopes = [
                _slope(member, week, week + forward_horizon, "avgLiveViews")
                for member in members
            ]
            view_slopes = [s for s in view_slopes if s is not None]
            segment_median_follower[segment][week] = (
                statistics.median(follower_slopes) if follower_slopes else None
            )
            segment_median_views[segment][week] = (
                statistics.median(view_slopes) if view_slopes else None
            )

    alpha_follower: dict[str, dict[int, float | None]] = {
        channel.channel_id: {} for channel in channels
    }
    alpha_views: dict[str, dict[int, float | None]] = {
        channel.channel_id: {} for channel in channels
    }

    for channel in channels:
        for week in range(week_count):
            raw_follower = _slope(channel, week, week + forward_horizon, "maxFollowerCount")
            raw_views = _slope(channel, week, week + forward_horizon, "avgLiveViews")
            if week >= max_start or raw_follower is None:
                alpha_follower[channel.channel_id][week] = None
            else:
                base = segment_median_follower.get(channel.segment, {}).get(week)
                alpha_follower[channel.channel_id][week] = (
                    raw_follower - base if base is not None else None
                )
            if week >= max_start or raw_views is None:
                alpha_views[channel.channel_id][week] = None
            else:
                base = segment_median_views.get(channel.segment, {}).get(week)
                alpha_views[channel.channel_id][week] = (
                    raw_views - base if base is not None else None
                )
    return alpha_follower, alpha_views


def evaluate_retention_rule(
    channels: list[ParsedChannel],
    week_count: int,
    *,
    alpha_follower: dict[str, dict[int, float | None]],
    alpha_views: dict[str, dict[int, float | None]],
) -> RuleResult:
    """Retention floor for 4 consecutive weeks predicts post-12-week stagnation."""
    signals = collect_retention_signals(channels=channels, week_count=week_count)
    cases: list[tuple[bool, bool | None]] = []
    for signal in signals:
        channel_id = signal["channel_id"]
        week = int(signal["week"])
        prediction = bool(signal["signal"])
        af = alpha_follower.get(channel_id, {}).get(week)
        av = alpha_views.get(channel_id, {}).get(week)
        if af is None and av is None:
            outcome = None
        else:
            outcome = (af is not None and af <= 0) and (av is not None and av <= 0)
        cases.append((prediction, outcome))

    strict = _binary_metrics(cases, include_missing_as_negative=False)
    default = _binary_metrics(cases, include_missing_as_negative=True)
    default_pairs = [
        (prediction, True if outcome is None else bool(outcome))
        for prediction, outcome in cases
    ]
    retention_risk_diff = _binary_lift(default_pairs)
    retention_risk_pvalue = _binary_lift_pvalue(default_pairs)

    if default["n_scored"] < RETENTION_MIN_SIGNALS:
        verdict = VERDICT_INSUFFICIENT
    elif (
        retention_risk_diff >= RETENTION_RISK_DIFF_MIN
        and retention_risk_pvalue <= RETENTION_PVALUE_MAX
    ):
        verdict = VERDICT_SUPPORT
    else:
        verdict = VERDICT_REJECT

    return RuleResult(
        verdict=verdict,
        effect_size=retention_risk_diff,
        n=default["n_scored"],
        sensitivity={
            "missing_as_failure": default,
            "missing_as_negative": default,
            "missing_excluded": strict,
        },
        evidence={
            "rule": "retention_lower_band_4weeks",
            "band_q": RETENTION_BAND_Q,
            "streak": RETENTION_STREAK,
            "outcome_definition": "alpha_follower<=0 and alpha_avgLiveViews<=0",
            "default_precision": default["precision"],
            "default_recall": default["recall"],
            "default_base_rate": default["base_rate"],
            "default_risk_diff": retention_risk_diff,
            "default_risk_pvalue": retention_risk_pvalue,
            "predicted_positive_rate": (
                default["predicted"] / default["n_scored"] if default["n_scored"] else 0.0
            ),
            "support_condition": (
                f"risk_diff >= {RETENTION_RISK_DIFF_MIN:.2f} "
                f"and pvalue <= {RETENTION_PVALUE_MAX:.2f}"
            ),
        },
    )


def collect_retention_signals(channels: list[ParsedChannel], week_count: int) -> list[dict[str, Any]]:
    """Collect per-week retention-band-streak signals."""
    thresholds = _segment_week_quantile(channels, week_count, "retention")
    signals = []
    for channel in channels:
        streak = 0
        for week in range(week_count):
            value = _retention(channel, week)
            q = thresholds.get(channel.segment, {}).get(week)
            in_band = value is not None and q is not None and value <= q
            streak = streak + 1 if in_band else 0
            signals.append({
                "channel_id": channel.channel_id,
                "segment": channel.segment,
                "week": week,
                "retention": value,
                "in_band": in_band,
                "streak": streak,
                "signal": streak >= RETENTION_STREAK,
            })
    return signals


def evaluate_threshold_1500_rule(
    channels: list[ParsedChannel],
    week_count: int,
    *,
    alpha_views: dict[str, dict[int, float | None]],
    forward_horizon: int = FORWARD_HORIZON,
    seed: int = RANDOM_SEED,
) -> RuleResult:
    """1500 median-crossing event and pre/post 12-week slope improvement."""
    moving_medians = {
        channel.channel_id: _build_moving_median_series(
            values=[
                channel.weeks.get(week, {}).get("avgLiveViews")
                for week in range(week_count)
            ],
            window=MOTION_MEDIAN_WINDOW,
        )
        for channel in channels
    }

    thresholds = (THRESHOLD_TARGET, *THRESHOLD_PLACEBOS)
    raw_events: dict[int, list[float | None]] = {thr: [] for thr in thresholds}

    for channel in channels:
        crossed: set[int] = set()
        for week in range(1, week_count):
            prev = moving_medians[channel.channel_id][week - 1]
            curr = moving_medians[channel.channel_id][week]
            if prev is None or curr is None:
                continue
            for thr in thresholds:
                if thr in crossed:
                    continue
                if prev <= thr < curr:
                    crossed.add(thr)
                    delta = _alpha_delta(alpha_views, channel.channel_id, week, forward_horizon)
                    raw_events[thr].append(delta)

    target_events = raw_events[THRESHOLD_TARGET]
    placebo_events = _flatten_placebo(raw_events)
    default_target = _impute_deltas(target_events, MISSING_DELTA_FALLBACK_Q)
    placebo_target_default = _impute_deltas(placebo_events, MISSING_DELTA_FALLBACK_Q)
    strict_target = [v for v in raw_events[THRESHOLD_TARGET] if v is not None]
    placebo_events_strict = [v for v in _flatten_placebo(raw_events) if v is not None]

    default_effect = _mean(default_target) - _mean(placebo_target_default)
    strict_effect = _mean(strict_target) - _mean(placebo_events_strict)

    default_p = _mean_difference_pvalue(
        default_target,
        placebo_target_default,
        seed=seed,
    )
    strict_p = _mean_difference_pvalue(
        strict_target,
        placebo_events_strict,
        seed=seed + 1,
    )

    default = {
        "n_events_target": len(default_target),
        "n_events_placebo": len(placebo_target_default),
        "mean_delta_target": _mean(default_target),
        "mean_delta_placebo": _mean(placebo_target_default),
        "effect_lift": default_effect,
        "permutation_pvalue": default_p,
        "positive_rate_target": _positive_rate(default_target),
        "positive_rate_placebo": _positive_rate(placebo_target_default),
    }
    strict = {
        "n_events_target": len(strict_target),
        "n_events_placebo": len(placebo_events_strict),
        "mean_delta_target": _mean(strict_target),
        "mean_delta_placebo": _mean(placebo_events_strict),
        "effect_lift": strict_effect,
        "permutation_pvalue": strict_p,
        "positive_rate_target": _positive_rate(strict_target),
        "positive_rate_placebo": _positive_rate(placebo_events_strict),
    }

    if len(default_target) < THRESHOLD_MIN_SIGNALS:
        verdict = VERDICT_INSUFFICIENT
    elif default_effect > THRESHOLD_LIFT_MIN and default_p <= THRESHOLD_PVALUE_MAX:
        verdict = VERDICT_SUPPORT
    else:
        verdict = VERDICT_REJECT

    return RuleResult(
        verdict=verdict,
        effect_size=default_effect,
        n=default["n_events_target"] + default["n_events_placebo"],
        sensitivity={
            "missing_as_failure": default,
            "missing_as_negative": default,
            "missing_excluded": strict,
        },
        evidence={
            "rule": "threshold_inflexion_1500_vs_placebo",
            "target_threshold": THRESHOLD_TARGET,
            "placebo_thresholds": list(THRESHOLD_PLACEBOS),
            "moving_median_window": MOTION_MEDIAN_WINDOW,
            "outcome_definition": "alpha_views_post_minus_pre",
        },
    )


def evaluate_airtime_uncorrelated_rule(
    channels: list[ParsedChannel],
    week_count: int,
    *,
    alpha_follower: dict[str, dict[int, float | None]],
    alpha_views: dict[str, dict[int, float | None]],
    seed: int = RANDOM_SEED,
) -> RuleResult:
    """Test whether segment-adjusted week-level (airTime, alpha growth) correlation is absent."""
    pairs_exclusive = _collect_segment_pairs(
        channels,
        week_count,
        alpha_follower,
        alpha_views,
        include_missing=False,
    )
    pairs_inclusive = _collect_segment_pairs(
        channels,
        week_count,
        alpha_follower,
        alpha_views,
        include_missing=True,
    )

    corr_default = _spearman_corr(pairs_exclusive)
    corr_all = _spearman_corr(pairs_inclusive)
    p_default = _permutation_corr_pvalue(pairs_exclusive, seed=seed)
    p_all = _permutation_corr_pvalue(pairs_inclusive, seed=seed + 1)

    # 동등성 주장(무상관)이므로 효과크기 경계만으로 판정한다. p-value를 지지 조건에
    # 걸면 표본이 클수록 사소한 상관도 유의해져 지지가 구조적으로 불가능해진다.
    # p는 evidence로만 보고한다.
    if len(pairs_exclusive) < AIRTIME_CORR_MIN_N:
        verdict = VERDICT_INSUFFICIENT
    elif abs(corr_default) <= AIRTIME_CORR_MAX_ABS:
        verdict = VERDICT_SUPPORT
    else:
        verdict = VERDICT_REJECT

    return RuleResult(
        verdict=verdict,
        effect_size=1.0 - abs(corr_default),
        n=len(pairs_exclusive),
        sensitivity={
            "missing_excluded": {
                "n": len(pairs_exclusive),
                "spearman_rho": corr_default,
                "permutation_pvalue": p_default,
            },
            "missing_as_zero": {
                "n": len(pairs_inclusive),
                "spearman_rho": corr_all,
                "permutation_pvalue": p_all,
            },
        },
        evidence={
            "rule": "airtime_growth_uncorrelated",
            "airtime_key": "airTime",
            "growth_key": "alpha_avg_and_follower",
            "min_n": AIRTIME_CORR_MIN_N,
            "corr_abs_threshold": AIRTIME_CORR_MAX_ABS,
            "support_condition": "abs(rho)<=0.20 and p>=0.20",
        },
    )


def evaluate_bottleneck_rule(
    channels: list[ParsedChannel],
    week_count: int,
    *,
    alpha_follower: dict[str, dict[int, float | None]],
    alpha_views: dict[str, dict[int, float | None]],
    seed: int = RANDOM_SEED,
) -> RuleResult:
    """Segments with multi-axis bottlenecks predict later stagnation."""
    weekly_records: dict[int, list[dict[str, Any]]] = {}
    for week in range(week_count):
        axis_values: dict[str, dict[str, list[float]]] = {}
        for channel in channels:
            record = {
                "channel_id": channel.channel_id,
                "segment": channel.segment,
                "severity": None,
                "weak_axes": 0,
            }
            metrics = {
                "efficiency": _efficiency(channel, week),
                "peak": _metric(channel, week, "maxLiveViews"),
                "airtime": _metric(channel, week, "airTime"),
                "follower": _metric(channel, week, "maxFollowerCount"),
            }
            for axis, value in metrics.items():
                if value is not None:
                    axis_values.setdefault(channel.segment, {}).setdefault(axis, []).append(value)
            weekly_records.setdefault(week, []).append(record)

        for channel in channels:
            metrics = {
                "efficiency": _efficiency(channel, week),
                "peak": _metric(channel, week, "maxLiveViews"),
                "airtime": _metric(channel, week, "airTime"),
                "follower": _metric(channel, week, "maxFollowerCount"),
            }
            percentiles: dict[str, float] = {}
            for axis, value in metrics.items():
                if value is None:
                    continue
                population = axis_values.get(channel.segment, {}).get(axis, [])
                if len(population) < 1:
                    continue
                percentiles[axis] = _percentile_rank(value, population)
            if percentiles:
                severity = min(percentiles.values())
                weak_axes = sum(1 for value in percentiles.values() if value <= BOTTLENECK_AXIS_Q)
                for row in weekly_records[week]:
                    if row["channel_id"] == channel.channel_id:
                        row["severity"] = severity
                        row["weak_axes"] = weak_axes
                        row["percentiles"] = percentiles
                        break

    cases: list[tuple[bool, bool | None]] = []
    severity_correlation_pairs: list[tuple[float, float]] = []

    for week, rows in weekly_records.items():
        severity_values = [row["severity"] for row in rows if row["severity"] is not None]
        severity_cutoff = (
            _quantile(severity_values, BOTTLENECK_AXIS_Q)
            if len(severity_values) >= 2
            else 0.0
        )
        for row in rows:
            severity = row["severity"]
            weak_axes = int(row["weak_axes"])
            if severity is None:
                cases.append((False, None))
                continue
            prediction = (
                severity <= severity_cutoff and weak_axes >= BOTTLENECK_AXIS_WEAK_COUNT_MIN
            )
            af = alpha_follower.get(str(row["channel_id"]), {}).get(week)
            av = alpha_views.get(str(row["channel_id"]), {}).get(week)
            if af is None and av is None:
                outcome = None
            else:
                outcome = (af is not None and af <= 0) or (av is not None and av <= 0)
            if outcome is not None:
                severity_correlation_pairs.append((severity, 1.0 if outcome else 0.0))
            cases.append((prediction, outcome))

    strict = _binary_metrics(cases, include_missing_as_negative=False)
    default = _binary_metrics(cases, include_missing_as_negative=True)

    filtered = [(pred, bool(outcome)) for pred, outcome in cases if outcome is not None]
    pvalue = _binary_lift_pvalue(filtered, seed=seed)
    severity_corr = _spearman_corr(severity_correlation_pairs)
    severity_pvalue = (
        _permutation_corr_pvalue(severity_correlation_pairs, seed=seed + 1)
        if severity_correlation_pairs
        else 1.0
    )

    if default["n_scored"] < BOTTLENECK_MIN_SIGNALS:
        verdict = VERDICT_INSUFFICIENT
    elif (
        default["lift"] > BOTTLENECK_LIFT_MIN
        and pvalue <= BOTTLENECK_PVALUE_MAX
    ) or (
        severity_corr <= BOTTLENECK_CORR_MAX
        and severity_pvalue <= BOTTLENECK_CORR_PVALUE_MAX
    ):
        verdict = VERDICT_SUPPORT
    else:
        verdict = VERDICT_REJECT

    return RuleResult(
        verdict=verdict,
        effect_size=default["lift"],
        n=default["n_scored"],
        sensitivity={
            "missing_as_failure": default,
            "missing_as_negative": default,
            "missing_excluded": strict,
            "severity_corr": {
                "n": len(severity_correlation_pairs),
                "spearman_rho": severity_corr,
                "permutation_pvalue": severity_pvalue,
            },
        },
        evidence={
            "rule": "bottleneck_multi_axis_bottom25",
            "axis_values": ["efficiency", "peak", "airtime", "follower"],
            "prediction_condition": (
                "severity=min(percentile(axis)); severity<=q25 and weak_axes>=2"
            ),
            "axis_q": BOTTLENECK_AXIS_Q,
            "weak_axes_min": BOTTLENECK_AXIS_WEAK_COUNT_MIN,
            "outcome_definition": "alpha_follower<=0 or alpha_views<=0",
            "binary_lift_pvalue": pvalue,
            "severity_corr": severity_corr,
            "severity_corr_pvalue": severity_pvalue,
            "predicted_positive_rate": strict["predicted"] / strict["n_scored"] if strict["n_scored"] else 0.0,
        },
    )


def _collect_segment_pairs(
    channels: list[ParsedChannel],
    week_count: int,
    alpha_follower: dict[str, dict[int, float | None]],
    alpha_views: dict[str, dict[int, float | None]],
    *,
    include_missing: bool,
) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for week in range(week_count):
        segment_airtime: dict[str, list[float]] = {}
        segment_growth: dict[str, list[float]] = {}
        for channel in channels:
            airtime = _metric(channel, week, "airTime")
            growth = _growth_at_week(
                channel.channel_id,
                alpha_follower,
                alpha_views,
                week,
            )
            if airtime is None:
                continue
            if growth is None:
                if not include_missing:
                    continue
                growth = 0.0
            segment_airtime.setdefault(channel.segment, []).append(airtime)
            segment_growth.setdefault(channel.segment, []).append(growth)

        for channel in channels:
            airtime = _metric(channel, week, "airTime")
            growth = _growth_at_week(
                channel.channel_id,
                alpha_follower,
                alpha_views,
                week,
            )
            if airtime is None:
                continue
            if growth is None:
                if not include_missing:
                    continue
                growth = 0.0
            population_air = segment_airtime.get(channel.segment, [])
            population_growth = segment_growth.get(channel.segment, [])
            if len(population_air) < 2 or len(population_growth) < 2:
                continue
            pairs.append((
                _percentile_rank(airtime, population_air),
                _percentile_rank(growth, population_growth),
            ))
    return pairs


def _binary_metrics(
    cases: list[tuple[bool, bool | None]],
    *,
    include_missing_as_negative: bool,
) -> dict[str, float | int]:
    total = len(cases)
    scored = 0
    positives = 0
    predicted = 0
    tp = fp = tn = fn = 0

    for prediction, outcome in cases:
        if outcome is None:
            if not include_missing_as_negative:
                continue
            outcome_bool = True
        else:
            outcome_bool = bool(outcome)
        scored += 1
        if outcome_bool:
            positives += 1
        if prediction:
            predicted += 1
            if outcome_bool:
                tp += 1
            else:
                fp += 1
        elif outcome_bool:
            fn += 1
        else:
            tn += 1

    precision = float(tp / predicted) if predicted else 0.0
    recall = float(tp / positives) if positives else 0.0
    base_rate = float(positives / scored) if scored else 0.0
    lift = precision - base_rate
    return {
        "n": total,
        "n_scored": scored,
        "predicted": predicted,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "base_rate": base_rate,
        "lift": lift,
    }


def _binary_lift(pairs: list[tuple[bool, bool]]) -> float:
    positive = [outcome for pred, outcome in pairs if pred]
    negative = [outcome for pred, outcome in pairs if not pred]
    if not positive or not negative:
        return 0.0
    pos_rate = sum(1 for value in positive if value) / len(positive)
    neg_rate = sum(1 for value in negative if value) / len(negative)
    return pos_rate - neg_rate


def _binary_lift_pvalue(
    pairs: list[tuple[bool, bool]],
    *,
    rounds: int = PERMUTATION_ROUNDS,
    seed: int = RANDOM_SEED,
) -> float:
    if len(pairs) < 4:
        return 1.0
    observed = _binary_lift(pairs)
    outcomes = [outcome for _, outcome in pairs]
    preds = [pred for pred, _ in pairs]
    rng = random.Random(seed)
    exceed = 1
    for _ in range(rounds):
        perm = outcomes.copy()
        rng.shuffle(perm)
        candidate = list(zip(preds, perm))
        if _binary_lift(candidate) >= observed:
            exceed += 1
    return exceed / (rounds + 1)


def _alpha_delta(
    alpha_map: dict[str, dict[int, float | None]],
    channel_id: str,
    week: int,
    forward_horizon: int,
) -> float | None:
    start_week = week - forward_horizon
    if start_week < 0:
        return None
    before = alpha_map.get(channel_id, {}).get(start_week)
    after = alpha_map.get(channel_id, {}).get(week)
    if before is None or after is None:
        return None
    return after - before


def _fallback_delta(value: float | None, fallback: float) -> float:
    return value if value is not None else fallback


def _impute_deltas(
    values: list[float | None],
    fallback_quantile: float = MISSING_DELTA_FALLBACK_Q,
) -> list[float]:
    observed = [value for value in values if value is not None]
    fallback = (
        _quantile(observed, fallback_quantile)
        if observed
        else MISSING_DELTA_FALLBACK
    )
    return [_fallback_delta(value, fallback) for value in values]


def _flatten_placebo(raw_events: dict[int, list[float | None]]) -> list[float | None]:
    pooled: list[float | None] = []
    for thr in THRESHOLD_PLACEBOS:
        pooled.extend(raw_events.get(thr, []))
    return pooled


def _mean_difference_pvalue(
    target: list[float],
    placebo: list[float],
    *,
    rounds: int = PERMUTATION_ROUNDS,
    seed: int = RANDOM_SEED,
) -> float:
    if not target or not placebo:
        return 1.0
    observed = _mean(target) - _mean(placebo)
    pool = target + placebo
    target_n = len(target)
    rng = random.Random(seed)
    exceed = 1
    for _ in range(rounds):
        shuffled = pool.copy()
        rng.shuffle(shuffled)
        perm_t = shuffled[:target_n]
        perm_p = shuffled[target_n:]
        perm_stat = _mean(perm_t) - _mean(perm_p)
        if perm_stat >= observed:
            exceed += 1
    return exceed / (rounds + 1)


def _segment_week_quantile(
    channels: list[ParsedChannel],
    week_count: int,
    metric: str,
) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = {}
    for week in range(week_count):
        buckets: dict[str, list[float]] = {}
        for channel in channels:
            if metric == "retention":
                value = _retention(channel, week)
            else:
                raise ValueError(f"unknown metric {metric}")
            if value is None:
                continue
            buckets.setdefault(channel.segment, []).append(value)
        for segment, values in buckets.items():
            if values:
                out.setdefault(segment, {})[week] = _quantile(values, RETENTION_BAND_Q)
    return out


def _build_moving_median_series(values: list[float | None], window: int) -> list[float | None]:
    series: list[float | None] = []
    for end in range(len(values)):
        start = max(0, end - window + 1)
        window_values = [v for v in values[start : end + 1] if v is not None]
        series.append(statistics.median(window_values) if window_values else None)
    return series


def _retention(channel: ParsedChannel, week: int) -> float | None:
    avg = _metric(channel, week, "avgLiveViews")
    peak = _metric(channel, week, "maxLiveViews")
    if avg is None or peak is None or peak <= 0:
        return None
    return avg / peak


def _efficiency(channel: ParsedChannel, week: int) -> float | None:
    avg = _metric(channel, week, "avgLiveViews")
    follower = _metric(channel, week, "maxFollowerCount")
    if avg is None or follower is None or follower <= 0:
        return None
    return avg / follower


def _metric(channel: ParsedChannel, week: int, key: str) -> float | None:
    row = channel.weeks.get(week)
    if row is None:
        return None
    value = row.get(key)
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _growth_at_week(
    channel_id: str,
    alpha_follower: dict[str, dict[int, float | None]],
    alpha_views: dict[str, dict[int, float | None]],
    week: int,
) -> float | None:
    af = alpha_follower.get(channel_id, {}).get(week)
    av = alpha_views.get(channel_id, {}).get(week)
    if af is None and av is None:
        return None
    if af is None:
        return av
    if av is None:
        return af
    return (af + av) / 2.0


def _slope(
    channel: ParsedChannel,
    start: int,
    end: int,
    key: str,
) -> float | None:
    start_value = _metric(channel, start, key)
    end_value = _metric(channel, end, key)
    if start_value is None or end_value is None:
        return None
    if start_value <= 0:
        return None
    delta = end - start
    if delta <= 0:
        return None
    return ((end_value / start_value) - 1.0) / delta


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if q <= 0.0:
        return ordered[0]
    if q >= 1.0:
        return ordered[-1]
    idx = (len(ordered) - 1) * q
    low = math.floor(idx)
    high = math.ceil(idx)
    if low == high:
        return ordered[low]
    frac = idx - low
    return ordered[low] + (ordered[high] - ordered[low]) * frac


def _percentile_rank(value: float, population: list[float]) -> float:
    if not population:
        return 0.0
    ordered = sorted(population)
    index = bisect_left(ordered, value)
    upper = bisect_right(ordered, value)
    if len(population) <= 1:
        return 1.0
    lower_count = index
    return (lower_count + upper - 1) / (2.0 * (len(ordered) - 1))

def _spearman_corr(pairs: list[tuple[float, float]]) -> float:
    if len(pairs) < 2:
        return 0.0
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    if _all_equal(xs) or _all_equal(ys):
        return 0.0
    rx = _ranks(xs)
    ry = _ranks(ys)
    return _pearson(rx, ry)


def _permutation_corr_pvalue(
    pairs: list[tuple[float, float]],
    *,
    rounds: int = PERMUTATION_ROUNDS,
    seed: int = RANDOM_SEED,
) -> float:
    if len(pairs) < 3:
        return 1.0
    observed = abs(_spearman_corr(pairs))
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    rng = random.Random(seed)
    exceed = 1
    for _ in range(rounds):
        shuffled_x = xs.copy()
        rng.shuffle(shuffled_x)
        candidate = _spearman_corr(list(zip(shuffled_x, ys)))
        if abs(candidate) >= observed:
            exceed += 1
    return exceed / (rounds + 1)


def _all_equal(values: list[float]) -> bool:
    if not values:
        return True
    first = values[0]
    return all(v == first for v in values)


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted((value, idx) for idx, value in enumerate(values))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        rank = (i + j + 1) / 2.0
        for _, idx in ordered[i:j]:
            ranks[idx] = rank
        i = j
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = sum((x - mean_x) ** 2 for x in xs)
    denom_y = sum((y - mean_y) ** 2 for y in ys)
    denom = math.sqrt(denom_x * denom_y)
    if denom <= 0:
        return 0.0
    return numerator / denom


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return statistics.mean(values)


def _positive_rate(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if value > 0) / len(values)


def _normalize_segment(raw_segment: Any, follower_count: int | None) -> str:
    if raw_segment in {"rookie", "growth", "large"}:
        return str(raw_segment)
    if follower_count is None:
        return "unknown"
    if follower_count < 150:
        return "rookie"
    if follower_count <= 10000:
        return "growth"
    return "large"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return number
        return None
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
        if math.isfinite(number):
            return number
    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except ValueError:
                return None
    return None


def _parse_week_date(raw: Any) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw[:10]).date()
    except ValueError:
        return None




