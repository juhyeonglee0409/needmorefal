from __future__ import annotations

from copy import deepcopy
import json
import tempfile
from pathlib import Path

from tools.backtest import rules
from tools.backtest.fixture import (
    build_airtime_dataset,
    build_bottleneck_dataset,
    build_mixed_dataset,
    build_retention_dataset,
    build_threshold_dataset,
)
from tools.backtest.run import run_backtest


def test_alpha_formula_and_forward_horizon() -> None:
    weeks = 16
    values = {
        w: {
            "avgLiveViews": 100.0 + 4.0 * w,
            "maxFollowerCount": 200.0 + 2.0 * w,
            "maxLiveViews": 220.0 + 4.0 * w,
            "airTime": 1.0,
            "sumCount": 0.0,
            "viewership": 0.0,
        }
        for w in range(weeks)
    }
    values_b = {
        w: {
            "avgLiveViews": 180.0 + 3.0 * w,
            "maxFollowerCount": 350.0 + 4.0 * w,
            "maxLiveViews": 280.0 + 3.0 * w,
            "airTime": 1.0,
            "sumCount": 0.0,
            "viewership": 0.0,
        }
        for w in range(weeks)
    }
    channels = [
        rules.ParsedChannel(
            channel_id="c1",
            segment="growth",
            follower_count=2000,
            weeks=values,
        ),
        rules.ParsedChannel(
            channel_id="c2",
            segment="growth",
            follower_count=2400,
            weeks=values_b,
        ),
    ]
    alpha_follower, alpha_views = rules.compute_alpha(channels=channels, week_count=weeks, forward_horizon=12)

    # c1 follower slope 2, c2 follower slope 4 -> median=3, so alpha=-1
    assert alpha_follower["c1"][0] == -1.0
    # c1 view slope 4, c2 view slope 3 -> median=3.5, so alpha=0.5
    assert alpha_views["c1"][0] == 0.5
    # After 12-week horizon, no forward alpha
    assert alpha_follower["c1"][12] is None
    assert alpha_views["c2"][12] is None


def test_retention_rule_supports_stagnation_signature() -> None:
    channels, week_dates = _load_records(build_retention_dataset())
    alpha_follower, alpha_views = rules.compute_alpha(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=rules.FORWARD_HORIZON,
    )
    result = rules.evaluate_retention_rule(
        channels=channels,
        week_count=len(week_dates),
        alpha_follower=alpha_follower,
        alpha_views=alpha_views,
    )

    assert result.verdict == rules.VERDICT_SUPPORT
    assert result.n > 0


def test_threshold_rule_detects_1500_and_placebo_weak() -> None:
    channels, week_dates = _load_records(build_threshold_dataset())
    _, alpha_views = rules.compute_alpha(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=rules.FORWARD_HORIZON,
    )
    result = rules.evaluate_threshold_1500_rule(
        channels=channels,
        week_count=len(week_dates),
        alpha_views=alpha_views,
        forward_horizon=rules.FORWARD_HORIZON,
        seed=rules.RANDOM_SEED,
    )

    assert result.verdict == rules.VERDICT_SUPPORT
    assert result.n >= rules.THRESHOLD_MIN_SIGNALS
    assert result.effect_size > rules.THRESHOLD_LIFT_MIN


def test_airtime_uncorrelated_rule_supports_independence() -> None:
    channels, week_dates = _load_records(build_airtime_dataset())
    alpha_follower, alpha_views = rules.compute_alpha(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=rules.FORWARD_HORIZON,
    )
    result = rules.evaluate_airtime_uncorrelated_rule(
        channels=channels,
        week_count=len(week_dates),
        alpha_follower=alpha_follower,
        alpha_views=alpha_views,
        seed=rules.RANDOM_SEED,
    )

    assert result.verdict == rules.VERDICT_SUPPORT
    assert result.n >= rules.AIRTIME_CORR_MIN_N


def test_bottleneck_rule_supports_stagnation() -> None:
    channels, week_dates = _load_records(build_bottleneck_dataset())
    alpha_follower, alpha_views = rules.compute_alpha(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=rules.FORWARD_HORIZON,
    )
    result = rules.evaluate_bottleneck_rule(
        channels=channels,
        week_count=len(week_dates),
        alpha_follower=alpha_follower,
        alpha_views=alpha_views,
        seed=rules.RANDOM_SEED,
    )

    assert result.verdict == rules.VERDICT_SUPPORT
    assert result.sensitivity["missing_as_negative"]["n_scored"] > rules.BOTTLENECK_MIN_SIGNALS


def test_lookahead_guard_preserves_past_predictions() -> None:
    week_count = 40
    t_cut = 20
    base_records = build_mixed_dataset(week_count=week_count)
    future_shocked_records = _mutate_future_records(
        deepcopy(base_records),
        week_count=week_count,
        cutoff_week=t_cut,
    )

    base_channels, week_dates = _load_records(base_records)
    shocked_channels, shocked_week_dates = _load_records(future_shocked_records)

    assert week_dates == shocked_week_dates

    assert _collect_retention_predictions(base_channels, t_cut) == _collect_retention_predictions(
        shocked_channels,
        t_cut,
    )
    assert _collect_threshold_predictions(base_channels, week_count, t_cut) == _collect_threshold_predictions(
        shocked_channels,
        week_count,
        t_cut,
    )
    assert _collect_bottleneck_predictions(base_channels, week_count, t_cut) == _collect_bottleneck_predictions(
        shocked_channels,
        week_count,
        t_cut,
    )

    assert (
        base_channels[0].weeks[t_cut]["avgLiveViews"]
        != shocked_channels[0].weeks[t_cut]["avgLiveViews"]
    )


def _collect_retention_predictions(
    channels: list[rules.ParsedChannel],
    cutoff_week: int,
) -> dict[tuple[str, int], bool]:
    signals = rules.collect_retention_signals(channels=channels, week_count=max(2, cutoff_week))
    return {
        (signal["channel_id"], int(signal["week"])): bool(signal["signal"])
        for signal in signals
        if int(signal["week"]) < cutoff_week
    }


def _collect_threshold_predictions(
    channels: list[rules.ParsedChannel],
    week_count: int,
    cutoff_week: int,
) -> dict[tuple[str, int], bool]:
    moving_medians = {
        channel.channel_id: rules._build_moving_median_series(
            values=[
                channel.weeks.get(week, {}).get("avgLiveViews")
                for week in range(week_count)
            ],
            window=rules.MOTION_MEDIAN_WINDOW,
        )
        for channel in channels
    }
    predictions: dict[tuple[str, int], bool] = {}
    for channel in channels:
        crossed = False
        for week in range(week_count):
            if week == 0:
                predictions[(channel.channel_id, week)] = False
                continue
            prev = moving_medians[channel.channel_id][week - 1]
            curr = moving_medians[channel.channel_id][week]
            pred = False
            if not crossed and prev is not None and curr is not None and prev <= rules.THRESHOLD_TARGET < curr:
                pred = True
                crossed = True
            predictions[(channel.channel_id, week)] = pred

    return {
        key: value
        for key, value in predictions.items()
        if key[1] < cutoff_week
    }


def _collect_bottleneck_predictions(
    channels: list[rules.ParsedChannel],
    week_count: int,
    cutoff_week: int,
) -> dict[tuple[str, int], bool]:
    weekly_records: dict[int, list[dict[str, object]]] = {}
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
                "efficiency": rules._efficiency(channel, week),
                "peak": rules._metric(channel, week, "maxLiveViews"),
                "airtime": rules._metric(channel, week, "airTime"),
                "follower": rules._metric(channel, week, "maxFollowerCount"),
            }
            for axis, value in metrics.items():
                if value is not None:
                    axis_values.setdefault(channel.segment, {}).setdefault(axis, []).append(value)
            weekly_records.setdefault(week, []).append(record)

        for channel in channels:
            metrics = {
                "efficiency": rules._efficiency(channel, week),
                "peak": rules._metric(channel, week, "maxLiveViews"),
                "airtime": rules._metric(channel, week, "airTime"),
                "follower": rules._metric(channel, week, "maxFollowerCount"),
            }
            percentiles: dict[str, float] = {}
            for axis, value in metrics.items():
                if value is None:
                    continue
                population = axis_values.get(channel.segment, {}).get(axis, [])
                if len(population) < 1:
                    continue
                percentiles[axis] = rules._percentile_rank(value, population)
            if percentiles:
                severity = min(percentiles.values())
                weak_axes = sum(1 for value in percentiles.values() if value <= rules.BOTTLENECK_AXIS_Q)
                for row in weekly_records[week]:
                    if row["channel_id"] == channel.channel_id:
                        row["severity"] = severity
                        row["weak_axes"] = weak_axes
                        break

    predictions: dict[tuple[str, int], bool] = {}
    for week, rows in weekly_records.items():
        severity_values = [row["severity"] for row in rows if row["severity"] is not None]
        severity_cutoff = rules._quantile(
            [float(value) for value in severity_values],
            rules.BOTTLENECK_AXIS_Q,
        ) if len(severity_values) >= 2 else 0.0
        for row in rows:
            severity = row.get("severity")
            weak_axes = int(row["weak_axes"])
            prediction = False
            if severity is not None:
                prediction = (
                    float(severity) <= severity_cutoff
                    and weak_axes >= rules.BOTTLENECK_AXIS_WEAK_COUNT_MIN
                )
            predictions[(str(row["channel_id"]), week)] = prediction

    return {
        key: value
        for key, value in predictions.items()
        if key[1] < cutoff_week
    }


def _mutate_future_records(
    records: list[dict],
    *,
    week_count: int,
    cutoff_week: int,
    factor: float = 10.0,
) -> list[dict]:
    for row in records:
        weeks = row.get("weeks", [])
        for week_idx in range(week_count):
            if week_idx < cutoff_week:
                continue
            if week_idx >= len(weeks):
                continue
            week_row = weeks[week_idx]
            if week_row.get("avgLiveViews") is not None:
                week_row["avgLiveViews"] *= factor
            if week_row.get("maxLiveViews") is not None:
                week_row["maxLiveViews"] *= factor
    return records


def test_survival_bias_treated_as_negative() -> None:
    records = build_retention_dataset(week_count=20)
    for record in records:
        if record["channel_id"] == "retention-low":
            record["weeks"] = record["weeks"][:10]

    channels, week_dates = _load_records(records)
    alpha_follower, alpha_views = rules.compute_alpha(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=10,
    )
    result = rules.evaluate_retention_rule(
        channels=channels,
        week_count=len(week_dates),
        alpha_follower=alpha_follower,
        alpha_views=alpha_views,
    )

    as_negative = result.sensitivity["missing_as_negative"]["n_scored"]
    excluded = result.sensitivity["missing_excluded"]["n_scored"]
    assert as_negative > excluded


def test_cli_smoke_writes_outputs(tmp_path: Path) -> None:
    records = build_mixed_dataset(week_count=36)
    input_path = tmp_path / "input.ndjson"
    out_dir = tmp_path / "out"
    _write_ndjson(input_path, records)
    payload = run_backtest(
        input_path=str(input_path),
        out_dir=str(out_dir),
        seed=rules.RANDOM_SEED,
        forward_horizon=rules.FORWARD_HORIZON,
    )

    assert (out_dir / "backtest_results.json").exists()
    assert (out_dir / "backtest_report.md").exists()
    assert set(payload["rules"].keys()) == {
        "retention_lower_band",
        "threshold_1500_inflexion",
        "airtime_uncorrelated",
        "bottleneck_axis",
    }


def _load_records(records: list[dict]) -> tuple[list[rules.ParsedChannel], list]:
    with tempfile.TemporaryDirectory() as tmpname:
        path = Path(tmpname) / "fixture.ndjson"
        _write_ndjson(path, records)
        channels, dates = rules.load_input(path)
    return channels, dates


def _write_ndjson(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
