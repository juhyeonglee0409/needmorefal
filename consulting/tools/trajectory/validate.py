"""CLI entrypoint for v3 trajectory matching validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate trajectory-matching v3 stability and band coverage.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input NDJSON path (one channel record per line).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for validation_result.json and validation_report.md.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=core.BOOTSTRAP_SEED,
        help="Random seed for any bootstrap operations.",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=core.BOOTSTRAP_ITERS,
        help="Bootstrap iterations for internal stability checks.",
    )
    return parser.parse_args()


def _pct(value: float) -> str:
    return f"{value * 100:0.1f}%"


def _build_report(payload: dict[str, object]) -> str:
    lines = [
        "# Trajectory validation report",
        "",
        f"- input: `{payload.get('input')}`",
        f"- week_count: `{payload.get('week_count')}`",
        f"- levels: `{', '.join(str(level) for level in payload.get('levels', []))}`",
        "",
        "|level|track|window|verdict|n|n_first|n_second|value|",
        "|---|---|---|---|---:|---:|---:|---|",
    ]

    results = payload.get("results", {})
    if not isinstance(results, dict):
        return "\n".join(lines)

    for level_text in sorted(results):
        level_payload = results[level_text]
        if not isinstance(level_payload, dict):
            continue

        track_c = level_payload.get("track_c", {})
        track_a = level_payload.get("track_a", {})

        if track_c.get("verdict") == "insufficient":
            lines.append(
                f"|{level_text}|Track C|12w|{track_c.get('verdict')}|"
                f"{track_c.get('n_t0', 0)}| - | - |"
                f"{track_c.get('reason', 'insufficient')}|"
            )
        else:
            lines.append(
                f"|{level_text}|Track C|12w|{track_c.get('verdict')}|"
                f"{track_c.get('n_first_half', 0) + track_c.get('n_second_half', 0)}|"
                f"{track_c.get('n_first_half', 0)}|{track_c.get('n_second_half', 0)}|"
                f"rise {_pct(track_c.get('proportions_first_half', {}).get('rise', 0.0))} (first) / "
                f"{_pct(track_c.get('proportions_second_half', {}).get('rise', 0.0))} (second), "
                f"flat {_pct(track_c.get('proportions_first_half', {}).get('flat', 0.0))} (first) / "
                f"{_pct(track_c.get('proportions_second_half', {}).get('flat', 0.0))} (second), "
                f"fall {_pct(track_c.get('proportions_first_half', {}).get('fall', 0.0))} (first) / "
                f"{_pct(track_c.get('proportions_second_half', {}).get('fall', 0.0))} (second), "
                f"diff={track_c.get('diffs')}"
            )

        if track_a.get("verdict") == "insufficient":
            lines.append(
                f"|{level_text}|Track A|12w|{track_a.get('verdict')}|"
                f"{track_a.get('n_targets', 0)}| - | - |"
                f"{track_a.get('reason', 'insufficient')}|"
            )
        else:
            coverage = float(track_a.get("coverage", 0.0))
            n_targets = int(track_a.get("n_targets", 0))
            n_inspected = int(track_a.get("n_inspected", 0))
            lines.append(
                f"|{level_text}|Track A|12w|{track_a.get('verdict')}|{n_targets}|"
                f"{n_targets}|{n_inspected}|"
                f"coverage {_pct(coverage)} vs nominal {_pct(track_a.get('nominal', 0.0))} "
                f"(inside={track_a.get('inside', 0)})"
            )

    return "\n".join(lines)


def run_validate_cli(
    input_path: str,
    out_dir: str,
    seed: int,
    bootstrap: int,
) -> dict[str, object]:
    payload = core.run_validation(
        input_path=input_path,
        seed=seed,
        bootstrap_iterations=bootstrap,
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "validation_report.md").write_text(
        _build_report(payload),
        encoding="utf-8",
    )
    return payload


def main() -> int:
    args = parse_args()
    run_validate_cli(
        input_path=args.input,
        out_dir=args.out,
        seed=args.seed,
        bootstrap=args.bootstrap,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
