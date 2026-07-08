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


def _geometric(start: float, weekly_rate: float, week_count: int) -> list[float]:
    """상대 성장률이 상수인 시계열 (상대 기울기 기반 α 검증용)."""
    return [start * (1.0 + weekly_rate) ** week for week in range(week_count)]


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
    """정답: 리텐션 하위 밴드 채널(5개)만 4주+ 연속 신호, 전방 상대 성장 정체.

    - 건강 12: 리텐션 0.50~0.72 분산, 상대 성장 +0.4%~+0.84%/주 분산
    - 저리텐션 정체 5: 리텐션 0.10, 성장 0 (예측 양성 → outcome 양성)
    - 정상리텐션 정체 2: 리텐션 0.60, 성장 0 (예측 음성인데 outcome 양성 → base rate 유지)
    저리텐션이 전체의 5/19(>25%)라 q25 경계가 저리텐션과 건강군 사이에 형성된다.
    """
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    for idx in range(12):
        rate = 0.004 + 0.0004 * idx
        ret = 0.50 + 0.02 * idx
        avg = _geometric(400.0, rate, week_count)
        peak = [v / ret for v in avg]
        follower = _geometric(3000.0 + 50 * idx, rate * 0.8, week_count)
        air = _linear(5.0 + 0.1 * idx, 0.0, week_count)
        channels.append(_build_channel(
            f"retention-normal-{idx}", "growth", follower, avg, peak, air, dates,
        ))

    for idx in range(5):
        avg = _linear(300.0 + idx * 10, 0.0, week_count)
        peak = [v / 0.10 for v in avg]
        follower = _linear(2000.0 + idx * 30, 0.0, week_count)
        air = _linear(4.0, 0.0, week_count)
        channels.append(_build_channel(
            "retention-low" if idx == 0 else f"retention-low-{idx}",
            "growth", follower, avg, peak, air, dates,
        ))

    for idx in range(2):
        avg = _linear(350.0 + idx * 10, 0.0, week_count)
        peak = [v / 0.60 for v in avg]
        follower = _linear(2500.0 + idx * 30, 0.0, week_count)
        air = _linear(5.0, 0.0, week_count)
        channels.append(_build_channel(
            f"retention-stall-normal-{idx}",
            "growth", follower, avg, peak, air, dates,
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

    # Targets: crossing 1500 and then much faster relative growth for clear post-1500 signal.
    avg_target = [0.0] * week_count
    for week in range(week_count):
        if week < 20:
            avg_target[week] = 1400.0 + 5.0 * week
        else:
            avg_target[week] = 1501.0 + 450.0 * (week - 20)
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
    """정답: 방송량과 상대 성장이 독립 (체급·성장 모두 방송량과 결합 금지).

    20채널 동일 체급(base 동일), 방송량은 채널 인덱스로 단조 증가,
    성장 부호는 인덱스 짝/홀로 교차 → 방송량 순위와 성장 순위 무상관.
    """
    dates = make_week_dates(week_count)
    channels: list[dict] = []
    for idx in range(20):
        air = [6.0 + (idx // 2) * 2.0] * week_count
        rate = 0.005 if idx % 2 == 0 else -0.005
        avg = _geometric(250.0, rate, week_count)
        follower = _geometric(3000.0, rate * 0.6, week_count)
        peak = [v * 1.8 for v in avg]
        channels.append(_build_channel(
            f"airtime-{'pos' if idx % 2 == 0 else 'neg'}-{idx}",
            "rookie", follower, avg, peak, air, dates,
        ))
    return channels


def build_bottleneck_dataset(week_count: int = 40) -> list[dict]:
    """정답: 다축(효율·피크·방송량) 병목 채널 2개만 예측 양성이고 이후 정체.

    - 건강 10: 효율 0.04, 피크 avg×2, 방송량 10~14.5, 상대 성장 +0.3%~+0.66%/주
    - 병목 정체 2: 효율 0.004, 피크 avg×1.2, 방송량 2 (3축 하위) + 성장 0.
      팔로워 레벨은 높게 두어 팔로워 축은 약축이 아니게 유지 (weak_axes=3).
    """
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    for idx in range(10):
        rate = 0.003 + 0.0004 * idx
        follower = _geometric(20000.0 + idx * 1000, rate, week_count)
        avg = [v * 0.04 for v in follower]
        peak = [v * 2.0 for v in avg]
        air = _linear(10.0 + idx * 0.45, 0.0, week_count)
        channels.append(_build_channel(
            f"bottleneck-healthy-{idx}", "large", follower, avg, peak, air, dates,
        ))

    for idx in range(2):
        follower = _linear(200000.0 + idx * 5000, 0.0, week_count)
        avg = [v * 0.004 for v in follower]
        peak = [v * 1.2 for v in avg]
        air = _linear(2.0, 0.0, week_count)
        channels.append(_build_channel(
            f"bottleneck-stall-{idx}", "large", follower, avg, peak, air, dates,
        ))
    return channels


def build_growth_outlook_dataset(week_count: int = 40) -> list[dict]:
    """정답: 효율×관성 상위 조합(4)은 초과 성장, 하위 조합(4)은 정체, 중간(8)이 기준선.

    세그먼트 라벨은 전용값('outlook')을 써서 mixed 데이터셋에서 타 규칙 코호트를
    오염시키지 않는다 (엔진은 세그먼트를 불투명 그룹 키로만 사용).
    """
    dates = make_week_dates(week_count)
    channels: list[dict] = []

    def add(cid, eff, rate):
        follower = _geometric(10000.0, rate, week_count)
        avg = [v * eff for v in follower]
        peak = [v * 2.0 for v in avg]
        air = _linear(6.0, 0.0, week_count)
        channels.append(_build_channel(cid, "outlook", follower, avg, peak, air, dates))

    for idx in range(4):
        add(f"outlook-green-{idx}", 0.10 + 0.005 * idx, 0.008)
    for idx in range(8):
        add(f"outlook-mid-{idx}", 0.02 + 0.004 * idx, 0.002 + 0.0003 * idx)
    for idx in range(4):
        add(f"outlook-red-{idx}", 0.004 + 0.0002 * idx, 0.0)
    return channels


def build_mixed_dataset(week_count: int = 40) -> list[dict]:
    seen: set[str] = set()
    records: list[dict] = []
    for record in (
        build_retention_dataset(week_count)
        + build_threshold_dataset(week_count)
        + build_airtime_dataset(week_count)
        + build_bottleneck_dataset(week_count)
        + build_growth_outlook_dataset(week_count)
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
