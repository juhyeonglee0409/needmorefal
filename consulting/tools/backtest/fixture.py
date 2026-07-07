"""Synthetic fixture generator for backtest unit tests."""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path


ANCHOR_DATE = "2025-07-07"


def make_week_dates(week_count: int = 53) -> list[str]:
    start = date.fromisoformat(ANCHOR_DATE)
    return [
        (start + timedelta(days=7 * week_idx)).isoformat()
        for week_idx in range(week_count)
    ]


def _linear(start: float, slope: float, week_count: int) -> list[float]:
    return [start + slope * week for week in range(week_count)]


def _build_channel(
    channel_id: str,
    segment: str,
    follower_series: list[float],
    avg_series: list[float],
    max_series: list[float],
    air_series: list[float],
    dates: list[str],
) -> dict:
    weeks = []
    for week_idx, week_date in enumerate(dates):
        weeks.append({
            "date": week_date,
            "maxFollowerCount": follower_series[week_idx],
            "avgLiveViews": avg_series[week_idx],
            "maxLiveViews": max_series[week_idx],
            "airTime": air_series[week_idx],
            "sumCount": 0,
            "viewership": 0,
        })
    return {
        "channel_id": channel_id,
        "channel_name": f"fixture-{channel_id}",
        "segment": segment,
        "follower_count": int(follower_series[0]),
        "weeks": weeks,
    }


def build_retention_dataset(week_count: int = 40) -> list[dict]:
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    for idx in range(6):
        follower = _linear(1500 + idx * 5, 7.0, week_count)
        avg = _linear(1200.0, 4.0, week_count)
        peak = _linear(2200.0, 4.2, week_count)
        air = _linear(6.0 + idx * 0.3, 0.2, week_count)
        channels.append(_build_channel(
            f"retention-normal-{idx}",
            "growth",
            follower,
            avg,
            peak,
            air,
            dates,
        ))

    follower = _linear(900.0, 0.0, week_count)
    avg = _linear(900.0, 2.0, week_count)
    peak = []
    for week in range(week_count):
        if 18 <= week <= 28:
            avg_v = 100.0
            peak_v = 5000.0
        else:
            avg_v = 900.0
            peak_v = 1500.0
        avg[week] = avg_v
        peak.append(peak_v)
    air = _linear(3.0, 0.0, week_count)
    channels.append(_build_channel(
        "retention-low",
        "growth",
        follower,
        avg,
        peak,
        air,
        dates,
    ))
    return channels


def build_threshold_dataset(week_count: int = 40) -> list[dict]:
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    # Baseline cohort for alpha normalization.
    for idx in range(6):
        follower = _linear(5000.0, 3.0, week_count)
        avg = _linear(900.0, 1.0, week_count)
        peak = _linear(1800.0, 1.0, week_count)
        air = _linear(8.0 + idx * 0.5, 0.2, week_count)
        channels.append(_build_channel(
            f"threshold-base-{idx}",
            "large",
            follower,
            avg,
            peak,
            air,
            dates,
        ))

    # Targets: crossing 1500 then slope increases.
    avg_target = [0.0] * week_count
    for week in range(week_count):
        if week < 20:
            avg_target[week] = 1440.0
        else:
            avg_target[week] = 1501.0 + 45.0 * (week - 20)
    peak_target = [v * 2.2 for v in avg_target]
    for idx in range(8):
        follower_target = [900.0 + 1.5 * week + idx * 2.0 for week in range(week_count)]
        air_target = _linear(10.0 + idx * 0.2, 0.15, week_count)
        channels.append(_build_channel(
            f"threshold-target-{idx}",
            "large",
            follower_target,
            avg_target,
            peak_target,
            air_target,
            dates,
        ))

    placebos = [
        ("threshold-placebo-750", 750, 0.0),
        ("threshold-placebo-1000", 1000, 0.0),
        ("threshold-placebo-2000", 2000, 0.0),
        ("threshold-placebo-3000", 3000, 0.0),
    ]
    for idx, (channel_id, thr, _phase) in enumerate(placebos):
        avg_placebo = [0.0] * week_count
        pre_slope = 1.0 if thr >= 2000 else 2.0
        pre_start = thr - 40.0
        for week in range(week_count):
            if week < 20:
                avg_placebo[week] = pre_start + pre_slope * week
            else:
                avg_placebo[week] = (pre_start + pre_slope * 20) + pre_slope * (week - 20)
        avg_placebo = [v + 70.0 if week == 20 else v for week, v in enumerate(avg_placebo)]
        follower_placebo = [4200.0 + 1.2 * week for week in range(week_count)]
        peak_placebo = [v * 2.2 for v in avg_placebo]
        air_placebo = _linear(6.0 + idx * 0.6, 0.1, week_count)
        channels.append(_build_channel(
            channel_id,
            "large",
            follower_placebo,
            avg_placebo,
            peak_placebo,
            air_placebo,
            dates,
        ))
    return channels


def build_airtime_dataset(week_count: int = 40) -> list[dict]:
    dates = make_week_dates(week_count)
    channels: list[dict] = []
    for pair_idx in range(10):
        base = 3000.0 + pair_idx * 10.0
        air = [20.0 + pair_idx] * week_count

        avg_plus = [250.0 + week for week in range(week_count)]
        follower_plus = [base + 2.0 * week for week in range(week_count)]
        peak_plus = [avg_plus[week] * 1.8 + 2.0 for week in range(week_count)]
        channels.append(_build_channel(
            f"airtime-pos-{pair_idx}",
            "rookie",
            follower_plus,
            avg_plus,
            peak_plus,
            air,
            dates,
        ))

        avg_minus = [250.0 - week for week in range(week_count)]
        avg_minus = [max(1.0, value) for value in avg_minus]
        follower_minus = [base + 1.0 + 2.0 * week for week in range(week_count)]
        peak_minus = [avg_minus[week] * 1.8 + 2.0 for week in range(week_count)]
        channels.append(_build_channel(
            f"airtime-neg-{pair_idx}",
            "rookie",
            follower_minus,
            avg_minus,
            peak_minus,
            air,
            dates,
        ))
    return channels


def build_bottleneck_dataset(week_count: int = 40) -> list[dict]:
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    follower = _linear(25000.0, 12.0, week_count)
    avg = _linear(1200.0, 10.0, week_count)
    peak = [value * 2.0 for value in avg]
    air = _linear(11.0, 0.1, week_count)
    channels.append(_build_channel(
        "bottleneck-baseline",
        "large",
        follower,
        avg,
        peak,
        air,
        dates,
    ))

    # Bottleneck candidate: strong efficiency/peak/air constraints with weak avg growth.
    follower_b = _linear(200000.0, 8.0, week_count)
    avg_b = _linear(80.0, 1.0, week_count)
    peak_b = [value * 2.0 for value in avg_b]
    air_b = _linear(3.0, 0.0, week_count)
    channels.append(_build_channel(
        "bottleneck-stall",
        "large",
        follower_b,
        avg_b,
        peak_b,
        air_b,
        dates,
    ))
    return channels


def build_mixed_dataset(week_count: int = 40) -> list[dict]:
    seen: set[str] = set()
    records: list[dict] = []
    for record in (
        build_retention_dataset(week_count)
        + build_threshold_dataset(week_count)
        + build_airtime_dataset(week_count)
        + build_bottleneck_dataset(week_count)
    ):
        if record["channel_id"] in seen:
            continue
        seen.add(record["channel_id"])
        records.append(record)
    return records


def write_fixture(records: list[dict], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
