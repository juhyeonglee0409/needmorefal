"""CLI entrypoint for trajectory-matching v3 run analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run trajectory-matching v3 run mode.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input NDJSON path (one channel record per line).",
    )
    parser.add_argument(
        "--level",
        required=True,
        type=float,
        help="Level threshold (avgLiveViews anchor).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for trajectory_result.json and trajectory_report.md.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=core.BOOTSTRAP_SEED,
        help="Random seed for alpha bootstrap.",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=core.BOOTSTRAP_ITERS,
        help="Bootstrap iterations for alpha CI.",
    )
    return parser.parse_args()


def _pct(value: float) -> str:
    return f"{value * 100:0.1f}%"


def _quantile_text(
    band: dict[str, float | None],
    *,
    window: str,
    n: int,
) -> str:
    if band.get("q10") is None or band.get("q90") is None:
        return f"{window} (window={window}, n={n}): no band"
    return (
        f"{window} (window={window}, n={n}): "
        f"q10={band['q10']:.4f}, q50={band['q50']:.4f}, q90={band['q90']:.4f}"
    )


def _build_report(payload: dict[str, object]) -> str:
    track_c = payload.get("track_c", {})
    track_a = payload.get("track_a", {})
    track_b = payload.get("track_b", {})
    level = float(payload.get("level", 0.0))
    lines: list[str] = [
        "# Trajectory report",
        "",
        f"- input: `{payload.get('input')}`",
        f"- level: `{level}`",
        f"- week_count: `{payload.get('week_count')}`",
        f"- seed: `{payload.get('seed')}`",
        f"- bootstrap_iterations: `{payload.get('bootstrap_iterations')}`",
        "",
        "## 1) Track C",
    ]

    for h in (12, 24):
        sensitivity_map = track_c.get(h, {}) if isinstance(track_c, dict) else {}
        if not sensitivity_map:
            lines.append(f"- {h}w (window={h}w): insufficient data")
            continue

        for tol_key in sorted(sensitivity_map):
            tol = float(tol_key)
            outcome = sensitivity_map.get(tol_key) or {}
            n = int(outcome.get("n", 0))
            immature = int(outcome.get("immature", 0))
            rise = float(outcome.get("rise", 0.0))
            flat = float(outcome.get("flat", 0.0))
            fall = float(outcome.get("fall", 0.0))
            if n <= 0:
                lines.append(
                    f"- {h}w (window={h}w, n={n}, immature={immature}, "
                    f"sensitivity={tol * 100:.0f}%): no mature samples"
                )
            else:
                lines.append(
                    f"- {h}w (window={h}w, n={n}, immature={immature}, "
                    f"sensitivity={tol * 100:.0f}%): "
                    f"rise={_pct(rise / n)}, flat={_pct(flat / n)}, fall={_pct(fall / n)}"
                )

    track_a_horizons = track_a.get("horizons", {})
    a_top = track_a.get("top10", [])
    a_n = int(track_a.get("n", 0))
    lines.extend([
        "",
        "## 2) Track A",
        f"- eligible channels: `window=12w/24w`, `n={a_n}`",
    ])
    for window_key in ("12w", "24w"):
        band = track_a_horizons.get(window_key, {})
        n_band = int(band.get("n", 0))
        lines.append(_quantile_text(band, window=window_key, n=n_band))

    lines.append(f"- Track A top10 by RMSE (window=12w/24w, n={min(10, a_n)}):")
    for idx, item in enumerate(a_top[:10], start=1):
        rmse = item.get("rmse")
        rmse_text = "-" if rmse is None else f"{float(rmse):0.4f}"
        lines.append(
            f"- top{idx} (window=12w/24w): channel_id={item.get('channel_id')} "
            f"t0={item.get('t0')} rmse={rmse_text}"
        )

    lines.extend([
        "",
        "## 3) Track B",
        "- Track B sorted by alpha descending at 12w; channels with overlapping CI have `ci_overlap_previous=True`",
    ])
    top_b = track_b.get("top10", [])
    for idx, item in enumerate(top_b, start=1):
        alpha = item.get("alpha")
        if alpha is None:
            alpha = 0.0
        ci = item.get("alpha_ci")
        ci_text = "-" if ci is None else f"[{ci[0]:0.5f}, {ci[1]:0.5f}]"
        overlap = bool(item.get("ci_overlap_previous"))
        lines.append(
            f"- Track B top{idx} (window=12w): channel_id={item.get('channel_id')} "
            f"alpha={float(alpha):0.6f} alpha_ci={ci_text} "
            f"ci_overlap_previous={overlap} t0={item.get('t0')}"
        )

    return "\n".join(lines)


def run_trajectory_cli(
    input_path: str,
    level: float,
    out_dir: str,
    seed: int,
    bootstrap: int,
) -> dict[str, object]:
    payload = core.run_trajectory(
        input_path=input_path,
        level=level,
        out_dir=out_dir,
        seed=seed,
        bootstrap_iterations=bootstrap,
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "trajectory_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "trajectory_report.md").write_text(_build_report(payload), encoding="utf-8")
    return payload


def main() -> int:
    args = parse_args()
    run_trajectory_cli(
        input_path=args.input,
        level=args.level,
        out_dir=args.out,
        seed=args.seed,
        bootstrap=args.bootstrap,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
