"""Core utilities for trajectory-matching v3 analytics.

Month-to-week porting map (spec v3):

| Month period | Weekly equivalent |
|--------------|------------------|
| 3 months rolling median | 12 weeks |
| 3 months outcome horizon | 12 weeks |
| 6 months outcome horizon | 24 weeks |
| 0.3/month alpha budget | 0.3 / 4.33 ≈ 0.069/week |
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import asdict, dataclass
from typing import Any

from tools.backtest import rules as backtest_rules


TRACK_C_HORIZONS = (12, 24)
TRACK_A_BAND_HORIZONS = (12, 24)
SENSITIVITY_LEVELS = (0.15, 0.20, 0.25)
TRACK_C_TARGET_BAND = 0.10
LEVEL_BAND_LOWER = 0.70
LEVEL_BAND_UPPER = 1.50
MEDIAN_WINDOW_WEEKS = 12
DEFAULT_LEVELS = (10.0, 17.0, 30.0, 60.0, 120.0)
ALPHA_WINDOW_WEEKS = 12
ALPHA_LIMIT_WEEK = 0.3 / 4.33  # 0.069 / week
CV_LIMIT = 0.25
BOOTSTRAP_ITERS = 1000
BOOTSTRAP_NOISE = 0.5
BOOTSTRAP_SEED = backtest_rules.RANDOM_SEED
TIME_SPLIT_FIRST = (12, 28)
TIME_SPLIT_SECOND = (29, 40)
N_PER_LEVEL_MIN = 20
VALIDATION_COVERAGE_NOMINAL = 0.80
VALIDATION_COVERAGE_TOL = 0.10


def load_input(path: str) -> tuple[list[backtest_rules.ParsedChannel], list[Any]]:
    """Load NDJSON using the same parser as backtest rules."""

    return backtest_rules.load_input(path)


@dataclass(frozen=True)
class TrackCOutcome:
    rise: float
    flat: float
    fall: float
    n: int
    immature: int

    @property
    def rise_pct(self) -> float:
        if self.n <= 0:
            return 0.0
        return self.rise / self.n

    @property
    def flat_pct(self) -> float:
        if self.n <= 0:
            return 0.0
        return self.flat / self.n

    @property
    def fall_pct(self) -> float:
        if self.n <= 0:
            return 0.0
        return self.fall / self.n


@dataclass(frozen=True)
class TrackCRecord:
    channel_id: str
    t0: int
    outcomes: dict[int, str]
    horizon_values: dict[int, float]
    anchor: float


def _metric_series(
    channel: backtest_rules.ParsedChannel,
    week_count: int,
    key: str = "avgLiveViews",
) -> list[float | None]:
    return [channel.weeks.get(week, {}).get(key) for week in range(week_count)]


def _rolling_median(values: list[float | None], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be > 0")
    result: list[float | None] = []
    for end in range(len(values)):
        start = end - window + 1
        if start < 0:
            result.append(None)
            continue
        window_values = [value for value in values[start : end + 1] if value is not None]
        if len(window_values) < window:
            result.append(None)
            continue
        result.append(statistics.median(window_values))
    return result


def _first_t0_by_level(
    medians: list[float | None],
    level: float,
) -> int | None:
    lower = level * (1 - TRACK_C_TARGET_BAND)
    upper = level * (1 + TRACK_C_TARGET_BAND)
    for week, value in enumerate(medians):
        if value is not None and lower <= value <= upper:
            return week
    return None


def detect_t0_by_levels(
    channels: list[backtest_rules.ParsedChannel],
    levels: tuple[float, ...],
    week_count: int,
) -> dict[float, dict[str, int | None]]:
    t0_by_level: dict[float, dict[str, int | None]] = {level: {} for level in levels}
    for channel in channels:
        med = _rolling_median(_metric_series(channel, week_count), MEDIAN_WINDOW_WEEKS)
        for level in levels:
            t0_by_level[level][channel.channel_id] = _first_t0_by_level(med, level)
    return t0_by_level


def _classify_outcome(
    anchor: float,
    future: float,
    tolerance: float,
) -> str:
    if anchor <= 0:
        raise ValueError("anchor value must be positive")
    ratio = (future / anchor) - 1.0
    if ratio >= tolerance:
        return "rise"
    if ratio <= -tolerance:
        return "fall"
    return "flat"


def _relative_growth(anchor: float, future: float) -> float:
    if anchor <= 0:
        return 0.0
    return (future / anchor) - 1.0


def _coefficient_of_variation(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if len(clean) < 2:
        return None
    mean = statistics.mean(clean)
    if not mean:
        return None
    stdev = statistics.pstdev(clean)
    return stdev / mean


def compute_alpha(
    channels: list[backtest_rules.ParsedChannel],
    week_count: int,
    *,
    horizon_weeks: int = ALPHA_WINDOW_WEEKS,
    seed: int = BOOTSTRAP_SEED,
    bootstrap: bool = False,
    bootstrap_iters: int = BOOTSTRAP_ITERS,
    points: set[tuple[str, int]] | None = None,
) -> tuple[
    dict[str, dict[int, float | None]],
    dict[str, dict[int, tuple[float, float] | None]],
]:
    """Compute channel-level relative slope (alpha) and optional bootstrap CI."""

    _, alpha = backtest_rules.compute_alpha(
        channels=channels,
        week_count=week_count,
        forward_horizon=horizon_weeks,
    )

    required_ci_points: set[tuple[str, int]]
    if points is None:
        required_ci_points = {
            (channel_id, week)
            for channel_id, weeks in alpha.items()
            for week, value in weeks.items()
            if value is not None
        }
    else:
        required_ci_points = {
            (channel_id, week) for channel_id, week in points if week < week_count
        }

    if not bootstrap or not required_ci_points:
        return {
            channel_id: week_map.copy() for channel_id, week_map in alpha.items()
        }, {
            channel_id: {week: None for week in week_map}
            for channel_id, week_map in alpha.items()
        }

    max_start = max(0, week_count - horizon_weeks)
    by_segment: dict[str, list[backtest_rules.ParsedChannel]] = {}
    for channel in channels:
        by_segment.setdefault(channel.segment, []).append(channel)

    alpha_samples: dict[tuple[str, int], list[float]] = {
        point: []
        for point in required_ci_points
    }

    raw_start_end_cache: dict[str, dict[int, tuple[float, float] | None]] = {}
    for channel in channels:
        cache: dict[int, tuple[float, float] | None] = {}
        for week in range(max_start):
            start = backtest_rules._metric(channel, week, "avgLiveViews")
            end = backtest_rules._metric(channel, week + horizon_weeks, "avgLiveViews")
            if start is None or end is None:
                cache[week] = None
            else:
                cache[week] = (start, end)
        raw_start_end_cache[channel.channel_id] = cache

    rng = random.Random(seed)
    for segment_members in by_segment.values():
        for _ in range(bootstrap_iters):
            for week in range(max_start):
                perturbed_slopes: dict[str, float] = {}
                for channel in segment_members:
                    base = raw_start_end_cache[channel.channel_id].get(week)
                    if base is None:
                        continue
                    start = base[0] + rng.uniform(-BOOTSTRAP_NOISE, BOOTSTRAP_NOISE)
                    end = base[1] + rng.uniform(-BOOTSTRAP_NOISE, BOOTSTRAP_NOISE)
                    noisy_channel = backtest_rules.ParsedChannel(
                        channel_id=channel.channel_id,
                        segment=channel.segment,
                        follower_count=channel.follower_count,
                        weeks={
                            week: {"avgLiveViews": start},
                            week + horizon_weeks: {"avgLiveViews": end},
                        },
                    )
                    slope = backtest_rules._slope(
                        noisy_channel,
                        week,
                        week + horizon_weeks,
                        "avgLiveViews",
                    )
                    if slope is None:
                        continue
                    perturbed_slopes[channel.channel_id] = slope

                if not perturbed_slopes:
                    continue
                median_slope = statistics.median(perturbed_slopes.values())
                for channel_id, base_alpha in alpha.items():
                    if base_alpha.get(week) is None:
                        continue
                    if (channel_id, week) not in required_ci_points:
                        continue
                    slope = perturbed_slopes.get(channel_id)
                    if slope is None:
                        continue
                    alpha_samples[(channel_id, week)].append(slope - median_slope)

    alpha_ci: dict[str, dict[int, tuple[float, float] | None]] = {}
    for channel in channels:
        ci_map: dict[int, tuple[float, float] | None] = {}
        for week in range(week_count):
            samples = alpha_samples.get((channel.channel_id, week))
            if not samples:
                ci_map[week] = None
                continue
            ci_map[week] = (
                backtest_rules._quantile(samples, 0.025),
                backtest_rules._quantile(samples, 0.975),
            )
        alpha_ci[channel.channel_id] = ci_map
    return alpha, alpha_ci


def _ci_overlap(
    left: tuple[float, float] | None,
    right: tuple[float, float] | None,
) -> bool:
    if left is None or right is None:
        return False
    return not (left[1] < right[0] or left[0] > right[1])


def _relative_outcome_series(
    channel: backtest_rules.ParsedChannel,
    week_count: int,
    t0: int,
    horizons: tuple[int, ...] = TRACK_A_BAND_HORIZONS,
) -> dict[int, float | None]:
    anchor = backtest_rules._metric(channel, t0, "avgLiveViews")
    if anchor is None or anchor <= 0:
        return {h: None for h in horizons}
    outcomes: dict[int, float | None] = {}
    for horizon in horizons:
        future = backtest_rules._metric(channel, t0 + horizon, "avgLiveViews")
        if future is None:
            outcomes[horizon] = None
        else:
            outcomes[horizon] = _relative_growth(anchor, future)
    return outcomes


def build_track_c(
    level: float,
    channels: list[backtest_rules.ParsedChannel],
    t0_by_channel: dict[str, int | None],
    week_count: int,
    *,
    sensitivity_levels: tuple[float, ...] = SENSITIVITY_LEVELS,
    horizons: tuple[int, ...] = TRACK_C_HORIZONS,
) -> tuple[dict[int, dict[float, TrackCOutcome]], dict[str, TrackCRecord]]:
    per_horizon: dict[int, dict[float, dict[str, int]]] = {
        horizon: {level_sens: {"rise": 0, "flat": 0, "fall": 0} for level_sens in sensitivity_levels}
        for horizon in horizons
    }
    immature: dict[int, int] = {horizon: 0 for horizon in horizons}
    records: dict[str, TrackCRecord] = {}

    for channel in channels:
        t0 = t0_by_channel.get(channel.channel_id)
        if t0 is None:
            continue
        anchor = backtest_rules._metric(channel, t0, "avgLiveViews")
        if anchor is None or anchor <= 0:
            continue
        outcomes = _relative_outcome_series(channel, week_count, t0, horizons)
        matured = False
        record_outcomes: dict[int, str] = {}
        record_values: dict[int, float] = {}
        for horizon in horizons:
            if t0 + horizon >= week_count:
                immature[horizon] += 1
                continue
            future = backtest_rules._metric(channel, t0 + horizon, "avgLiveViews")
            if future is None:
                immature[horizon] += 1
                continue
            matured = True
            rel = _relative_growth(anchor, future)
            record_outcomes[horizon] = _classify_outcome(anchor, future, sensitivity_levels[1])
            record_values[horizon] = rel
            for sensitivity in sensitivity_levels:
                bucket = per_horizon[horizon][sensitivity]
                cls = _classify_outcome(anchor, future, sensitivity)
                bucket[cls] += 1
        if matured:
            records[channel.channel_id] = TrackCRecord(
                channel_id=channel.channel_id,
                t0=t0,
                outcomes=record_outcomes,
                horizon_values=record_values,
                anchor=anchor,
            )

    results: dict[int, dict[float, TrackCOutcome]] = {}
    for horizon in horizons:
        result_by_sens = {}
        for sensitivity in sensitivity_levels:
            buckets = per_horizon[horizon][sensitivity]
            n = sum(buckets.values())
            result_by_sens[sensitivity] = TrackCOutcome(
                rise=float(buckets["rise"]),
                flat=float(buckets["flat"]),
                fall=float(buckets["fall"]),
                n=n,
                immature=immature[horizon],
            )
        results[horizon] = result_by_sens
    return results, records


def build_track_a(
    level: float,
    channels: list[backtest_rules.ParsedChannel],
    t0_by_channel: dict[str, int | None],
    alpha: dict[str, dict[int, float | None]],
    alpha_ci: dict[str, dict[int, tuple[float, float] | None]] | None,
    week_count: int,
    *,
    top_n: int = 10,
    horizons: tuple[int, ...] = TRACK_A_BAND_HORIZONS,
) -> dict[str, Any]:
    candidate_rows: list[dict[str, Any]] = []

    for channel in channels:
        t0 = t0_by_channel.get(channel.channel_id)
        if t0 is None:
            continue
        if t0 + max(horizons) >= week_count:
            continue
        anchor = backtest_rules._metric(channel, t0, "avgLiveViews")
        if anchor is None:
            continue
        if not (level * LEVEL_BAND_LOWER <= anchor <= level * LEVEL_BAND_UPPER):
            continue
        alpha_value = alpha.get(channel.channel_id, {}).get(t0)
        if alpha_value is None or abs(alpha_value) > ALPHA_LIMIT_WEEK:
            continue
        values_window = _metric_series(channel, week_count)
        cv = _coefficient_of_variation(values_window[max(0, t0 - 11) : t0 + 1])
        if cv is None or cv > CV_LIMIT:
            continue
        outcomes = _relative_outcome_series(channel, week_count, t0, horizons)
        row: dict[str, Any] = {
            "channel_id": channel.channel_id,
            "t0": t0,
            "anchor": anchor,
            "alpha": alpha_value,
            "alpha_ci": alpha_ci[channel.channel_id][t0] if alpha_ci else None,
            "cv": cv,
            "outcomes": outcomes,
        }
        candidate_rows.append(row)

    band: dict[int, dict[str, float | None]] = {}
    for horizon in horizons:
        values = [
            float(row["outcomes"][horizon])
            for row in candidate_rows
            if row["outcomes"][horizon] is not None
        ]
        if len(values) >= 2:
            band[horizon] = {
                "n": len(values),
                "q10": backtest_rules._quantile(values, 0.10),
                "q50": backtest_rules._quantile(values, 0.50),
                "q90": backtest_rules._quantile(values, 0.90),
            }
        elif len(values) == 1:
            band[horizon] = {
                "n": len(values),
                "q10": values[0],
                "q50": values[0],
                "q90": values[0],
            }
        else:
            band[horizon] = {"n": 0, "q10": None, "q50": None, "q90": None}

    for row in candidate_rows:
        errors = []
        for horizon in horizons:
            q = band[horizon]["q50"]
            y = row["outcomes"][horizon]
            if q is None or y is None:
                continue
            errors.append((y - q) ** 2)
        row["rmse"] = math.sqrt(statistics.mean(errors)) if errors else None

    candidate_rows.sort(
        key=lambda item: (
            math.inf if item["rmse"] is None else item["rmse"],
            item["channel_id"],
        )
    )
    all_alphas = [
        float(row["alpha"])
        for row in candidate_rows
        if row["alpha"] is not None
    ]
    if all_alphas:
        alpha_values_count = len(all_alphas)
        if alpha_values_count >= 2:
            for row in candidate_rows:
                alpha_value = row.get("alpha")
                if alpha_value is None:
                    row["alpha_percentile"] = None
                else:
                    row["alpha_percentile"] = backtest_rules._percentile_rank(
                        alpha_value,
                        all_alphas,
                    )
        else:
            for row in candidate_rows:
                if row.get("alpha") is not None:
                    row["alpha_percentile"] = 1.0
    top_rows = candidate_rows[:top_n]

    return {
        "horizons": {
            f"{horizon}w": band[horizon] for horizon in horizons
        },
        "n": len(candidate_rows),
        "top10": top_rows,
    }


def build_track_b(
    level: float,
    channels: list[backtest_rules.ParsedChannel],
    t0_by_channel: dict[str, int | None],
    alpha: dict[str, dict[int, float | None]],
    alpha_ci: dict[str, dict[int, tuple[float, float] | None]] | None,
    week_count: int,
    *,
    top_n: int = 10,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for channel in channels:
        t0 = t0_by_channel.get(channel.channel_id)
        if t0 is None:
            continue
        if t0 + TRACK_A_BAND_HORIZONS[0] >= week_count:
            continue
        anchor = backtest_rules._metric(channel, t0, "avgLiveViews")
        future = backtest_rules._metric(channel, t0 + TRACK_A_BAND_HORIZONS[0], "avgLiveViews")
        if anchor is None or future is None or anchor <= 0:
            continue
        alpha_value = alpha.get(channel.channel_id, {}).get(t0)
        if alpha_value is None:
            continue
        growth = _classify_outcome(anchor, future, 0.20)
        if growth != "rise":
            continue
        rows.append(
            {
                "channel_id": channel.channel_id,
                "t0": t0,
                "alpha": alpha_value,
                "alpha_ci": alpha_ci[channel.channel_id][t0] if alpha_ci else None,
            },
        )

    rows.sort(key=lambda item: item["alpha"], reverse=True)

    previous_ci: tuple[float, float] | None = None
    for row in rows[:top_n]:
        row["ci_overlap_previous"] = _ci_overlap(row["alpha_ci"], previous_ci)
        previous_ci = row["alpha_ci"]

    return {
        "n": len(rows),
        "top10": rows[:top_n],
        "note": "rank only after CI overlap-aware grouping",
    }


def validate_track_c_stability(
    level: float,
    channels: list[backtest_rules.ParsedChannel],
    t0_by_channel: dict[str, int | None],
    week_count: int,
) -> dict[str, Any]:
    track_c, records = build_track_c(
        level=level,
        channels=channels,
        t0_by_channel=t0_by_channel,
        week_count=week_count,
    )
    split_a = range(TIME_SPLIT_FIRST[0], TIME_SPLIT_FIRST[1] + 1)
    split_b = range(TIME_SPLIT_SECOND[0], TIME_SPLIT_SECOND[1] + 1)

    def _counts(weeks: range) -> tuple[int, dict[str, int]]:
        labels = {"rise": 0, "flat": 0, "fall": 0}
        total = 0
        for cid, t0 in t0_by_channel.items():
            if t0 is None or t0 not in weeks:
                continue
            rec = records.get(cid)
            if rec is None:
                continue
            outcome = rec.outcomes.get(TRACK_C_HORIZONS[0])
            if outcome is None:
                continue
            labels[outcome] += 1
            total += 1
        return total, labels

    n_a, label_a = _counts(split_a)
    n_b, label_b = _counts(split_b)
    def _prop(total: int, count: int) -> float:
        return count / total if total else 0.0
    diffs = {key: abs(_prop(n_a, label_a[key]) - _prop(n_b, label_b[key])) for key in label_a}
    stable = all(delta <= 0.10 for delta in diffs.values())
    return {
        "n_first_half": n_a,
        "n_second_half": n_b,
        "counts_first_half": {
            "rise": label_a["rise"],
            "flat": label_a["flat"],
            "fall": label_a["fall"],
        },
        "counts_second_half": {
            "rise": label_b["rise"],
            "flat": label_b["flat"],
            "fall": label_b["fall"],
        },
        "proportions_first_half": {
            "rise": _prop(n_a, label_a["rise"]),
            "flat": _prop(n_a, label_a["flat"]),
            "fall": _prop(n_a, label_a["fall"]),
        },
        "proportions_second_half": {
            "rise": _prop(n_b, label_b["rise"]),
            "flat": _prop(n_b, label_b["flat"]),
            "fall": _prop(n_b, label_b["fall"]),
        },
        "diffs": diffs,
        "stable": stable,
        "verdict": "stable" if stable else "unstable",
    }


def validate_track_a_coverage(
    level: float,
    channels: list[backtest_rules.ParsedChannel],
    t0_by_channel: dict[str, int | None],
    week_count: int,
    alpha: dict[str, dict[int, float | None]],
    *,
    horizon: int = 12,
) -> dict[str, Any]:
    candidates = []
    for channel in channels:
        t0 = t0_by_channel.get(channel.channel_id)
        if t0 is None:
            continue
        anchor = backtest_rules._metric(channel, t0, "avgLiveViews")
        if anchor is None:
            continue
        if not (level * LEVEL_BAND_LOWER <= anchor <= level * LEVEL_BAND_UPPER):
            continue
        alpha_value = alpha.get(channel.channel_id, {}).get(t0)
        if alpha_value is None or abs(alpha_value) > ALPHA_LIMIT_WEEK:
            continue
        values_window = _metric_series(channel, week_count)
        cv = _coefficient_of_variation(values_window[max(0, t0 - 11) : t0 + 1])
        if cv is None or cv > CV_LIMIT:
            continue
        outcome = _relative_outcome_series(channel, week_count, t0, (horizon,)).get(horizon)
        if outcome is None:
            continue
        candidates.append({"channel_id": channel.channel_id, "t0": t0, "outcome": outcome})

    target_rows = [
        row
        for row in candidates
        if TIME_SPLIT_SECOND[0] <= row["t0"] <= TIME_SPLIT_SECOND[1]
    ]
    target_rows.sort(key=lambda item: item["channel_id"])

    inside = 0
    eligible_targets = 0
    inspected_targets = 0
    for target in target_rows:
        t0 = target["t0"]
        peers = [
            peer
            for peer in candidates
            if peer["t0"] + horizon <= t0
        ]
        peer_values = [peer["outcome"] for peer in peers]
        if len(peer_values) < 2:
            continue
        q10 = backtest_rules._quantile(peer_values, 0.10)
        q90 = backtest_rules._quantile(peer_values, 0.90)
        if q10 is None or q90 is None:
            continue
        inspected_targets += 1
        if q10 <= target["outcome"] <= q90:
            inside += 1
        eligible_targets += 1

    coverage = inside / inspected_targets if inspected_targets else 0.0
    return {
        "n_targets": len(target_rows),
        "n_eligible": eligible_targets,
        "n_inspected": inspected_targets,
        "inside": inside,
        "coverage": coverage,
        "nominal": VALIDATION_COVERAGE_NOMINAL,
        "diff": abs(coverage - VALIDATION_COVERAGE_NOMINAL),
        "verdict": (
            "stable" if (inspected_targets and abs(coverage - VALIDATION_COVERAGE_NOMINAL) <= VALIDATION_COVERAGE_TOL) else "insufficient" if not inspected_targets else "unstable"
        ),
    }


def run_trajectory(
    input_path: str,
    level: float,
    out_dir: str | None = None,
    *,
    seed: int = BOOTSTRAP_SEED,
    bootstrap_iterations: int = BOOTSTRAP_ITERS,
) -> dict[str, Any]:
    channels, week_dates = load_input(input_path)
    week_count = len(week_dates)
    t0_by_level = detect_t0_by_levels(channels, (float(level),), week_count)
    t0_by_channel = t0_by_level.get(float(level), {})

    alpha, alpha_ci = compute_alpha(
        channels=channels,
        week_count=week_count,
        horizon_weeks=ALPHA_WINDOW_WEEKS,
        seed=seed,
        bootstrap=True,
        bootstrap_iters=bootstrap_iterations,
    )

    track_c, _track_c_records = build_track_c(
        level=float(level),
        channels=channels,
        t0_by_channel=t0_by_channel,
        week_count=week_count,
    )
    track_a = build_track_a(
        level=float(level),
        channels=channels,
        t0_by_channel=t0_by_channel,
        alpha=alpha,
        alpha_ci=alpha_ci,
        week_count=week_count,
    )
    track_b = build_track_b(
        level=float(level),
        channels=channels,
        t0_by_channel=t0_by_channel,
        alpha=alpha,
        alpha_ci=alpha_ci,
        week_count=week_count,
    )

    track_c_payload = {
        h: {tol: asdict(outcome) for tol, outcome in by_tol.items()}
        for h, by_tol in track_c.items()
    }
    payload: dict[str, Any] = {
        "input": str(input_path),
        "level": float(level),
        "week_count": week_count,
        "seed": seed,
        "bootstrap_iterations": bootstrap_iterations,
        "track_c": track_c_payload,
        "track_a": track_a,
        "track_b": track_b,
    }
    return payload


def run_validation(
    input_path: str,
    *,
    out_dir: str | None = None,
    levels: tuple[float, ...] = DEFAULT_LEVELS,
    seed: int = BOOTSTRAP_SEED,
    bootstrap_iterations: int = BOOTSTRAP_ITERS,
) -> dict[str, Any]:
    channels, week_dates = load_input(input_path)
    week_count = len(week_dates)
    t0_by_level = detect_t0_by_levels(channels, levels, week_count)
    alpha, _ = compute_alpha(
        channels=channels,
        week_count=week_count,
        horizon_weeks=ALPHA_WINDOW_WEEKS,
        seed=seed,
        bootstrap=False,
    )

    level_results: dict[str, Any] = {}
    for level in levels:
        t0_by_channel = t0_by_level[level]
        with_t0 = [cid for cid, t0 in t0_by_channel.items() if t0 is not None]
        if len(with_t0) < N_PER_LEVEL_MIN:
            level_results[str(level)] = {
                "track_c": {
                    "verdict": "insufficient",
                    "reason": "insufficient_t0_channels",
                    "n_t0": len(with_t0),
                },
                "track_a": {
                    "verdict": "insufficient",
                    "reason": "insufficient_t0_channels",
                    "n_t0": len(with_t0),
                },
            }
            continue

        track_c = validate_track_c_stability(
            level=level,
            channels=channels,
            t0_by_channel=t0_by_channel,
            week_count=week_count,
        )
        track_a = validate_track_a_coverage(
            level=level,
            channels=channels,
            t0_by_channel=t0_by_channel,
            week_count=week_count,
            alpha=alpha,
        )
        level_results[str(level)] = {
            "track_c": track_c,
            "track_a": track_a,
        }

    return {
        "input": str(input_path),
        "levels": tuple(levels),
        "week_count": week_count,
        "seed": seed,
        "bootstrap_iterations": bootstrap_iterations,
        "results": level_results,
    }
