from __future__ import annotations

from pathlib import Path

from tools.backtest import rules
from tools.trajectory import core


def _channel(channel_id: str, values: list[float]) -> rules.ParsedChannel:
    return rules.ParsedChannel(
        channel_id=channel_id,
        segment="growth",
        follower_count=10_000,
        weeks={idx: {"avgLiveViews": float(value)} for idx, value in enumerate(values)},
    )


def _series(length: int, base: float = 10.0) -> list[float]:
    return [float(base)] * length


def test_t0_detection_rolling_median_ignores_single_spike() -> None:
    values = [2.0] * 11 + [10.0] + [2.0] * 8 + [10.0] * 20
    channels = [_channel("spike", values)]
    t0_by_level = core.detect_t0_by_levels(channels, (10.0,), len(values))
    t0 = t0_by_level[10.0]["spike"]
    assert t0 is not None
    assert t0 >= 20


def _classification_channels() -> list[rules.ParsedChannel]:
    def make(channel_id: str, rise12: float, rise24: float) -> rules.ParsedChannel:
        values = _series(60, 10.0)
        values[23] = 10.0 * (1.0 + rise12)
        values[35] = 10.0 * (1.0 + rise24)
        return _channel(channel_id, values)

    return [
        make("up", 0.30, 0.35),
        make("flat", 0.00, -0.02),
        make("down", -0.35, -0.40),
    ]


def test_track_c_classification_recovers_ground_truth() -> None:
    channels = _classification_channels()
    t0_by_level = core.detect_t0_by_levels(channels, (10.0,), 60)
    outcomes, _ = core.build_track_c(
        level=10.0,
        channels=channels,
        t0_by_channel=t0_by_level[10.0],
        week_count=60,
        sensitivity_levels=(0.15, 0.20, 0.25),
    )
    outcome12 = outcomes[12][0.20]
    assert int(outcome12.n) == 3
    assert int(outcome12.rise) == 1
    assert int(outcome12.flat) == 1
    assert int(outcome12.fall) == 1


def _track_a_channels() -> list[rules.ParsedChannel]:
    def make(channel_id: str, rise12: float, rise24: float) -> rules.ParsedChannel:
        values = _series(80, 10.0)
        values[23] = 10.0 * (1.0 + rise12)
        values[35] = 10.0 * (1.0 + rise24)
        return _channel(channel_id, values)

    return [
        make("best", 0.03, 0.04),
        make("mid", 0.025, 0.00),
        make("bad", 0.01, 0.01),
        make("reject", 0.90, 0.90),
    ]


def test_track_a_filter_and_rmse_ordering() -> None:
    channels = _track_a_channels()
    t0_by_level = core.detect_t0_by_levels(channels, (10.0,), 80)
    alpha, alpha_ci = core.compute_alpha(
        channels=channels,
        week_count=80,
        bootstrap=False,
    )
    track_a = core.build_track_a(
        level=10.0,
        channels=channels,
        t0_by_channel=t0_by_level[10.0],
        alpha=alpha,
        alpha_ci=alpha_ci,
        week_count=80,
    )

    top_ids = [row["channel_id"] for row in track_a["top10"]]
    assert track_a["n"] == 3
    assert top_ids == ["mid", "bad", "best"]


def _validation_channel(channel_id: str, t0: int, outcome_12: float, week_count: int) -> rules.ParsedChannel:
    values = _series(week_count, 10.0)
    values[t0 + 12] = 10.0 * (1.0 + outcome_12)
    return _channel(channel_id, values)


def _build_validation_dataset(
    outcome_first: list[float],
    outcome_second: list[float],
    leak_outcome: float | None = None,
) -> tuple[list[rules.ParsedChannel], dict[str, int]]:
    channels: list[rules.ParsedChannel] = []
    t0_by_channel: dict[str, int] = {}

    for idx, outcome in enumerate(outcome_first):
        cid = f"peer-{idx}"
        channels.append(_validation_channel(cid, 20, outcome, 90))
        t0_by_channel[cid] = 20

    for idx, outcome in enumerate(outcome_second):
        cid = f"target-{idx}"
        channels.append(_validation_channel(cid, 35, outcome, 90))
        t0_by_channel[cid] = 35

    if leak_outcome is not None:
        for idx in range(20):
            cid = f"leak-{idx}"
            channels.append(_validation_channel(cid, 60, leak_outcome, 90))
            t0_by_channel[cid] = 60

    return channels, t0_by_channel


def test_validate_track_a_band_coverage_recover_nominal_coverage() -> None:
    peers = [-0.06] * 8 + [0.0] * 4 + [0.06] * 8
    targets = [0.0] * 16 + [0.2] * 4

    channels, t0_by_channel = _build_validation_dataset(
        outcome_first=peers,
        outcome_second=targets,
        leak_outcome=None,
    )
    alpha, _ = core.compute_alpha(channels=channels, week_count=90, bootstrap=False)
    result = core.validate_track_a_coverage(
        level=10.0,
        channels=channels,
        t0_by_channel=t0_by_channel,
        week_count=90,
        alpha=alpha,
    )
    assert result["verdict"] == "stable"
    assert abs(result["coverage"] - 0.8) < 0.02


def test_validate_track_a_coverage_lookahead_guard() -> None:
    peers = [-0.06] * 8 + [0.0] * 4 + [0.06] * 8
    targets = [0.0] * 16 + [0.2] * 4

    channels, t0_by_channel = _build_validation_dataset(
        outcome_first=peers,
        outcome_second=targets,
        leak_outcome=0.0,
    )
    base_alpha, _ = core.compute_alpha(channels=channels, week_count=90, bootstrap=False)
    base = core.validate_track_a_coverage(
        level=10.0,
        channels=channels,
        t0_by_channel=t0_by_channel,
        week_count=90,
        alpha=base_alpha,
    )

    shocked_channels, _ = _build_validation_dataset(
        outcome_first=peers,
        outcome_second=targets,
        leak_outcome=0.9,
    )
    shocked_alpha, _ = core.compute_alpha(channels=shocked_channels, week_count=90, bootstrap=False)
    shocked = core.validate_track_a_coverage(
        level=10.0,
        channels=shocked_channels,
        t0_by_channel=t0_by_channel,
        week_count=90,
        alpha=shocked_alpha,
    )

    assert base["coverage"] == shocked["coverage"]


def test_forbidden_phrase_absent_from_module() -> None:
    root = Path(__file__).resolve().parents[1]
    phrase = "Synthetic" + " Control"
    for path in root.rglob("*.py"):
        assert phrase not in path.read_text(encoding="utf-8"), path
