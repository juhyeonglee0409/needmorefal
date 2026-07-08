"""CLI entrypoint for trajectory-matching backtest rules."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from . import rules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run rule-based backtest for channel diagnostics.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input NDJSON path (one channel record per line).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory path for backtest_results.json and backtest_report.md.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=rules.RANDOM_SEED,
        help="Random seed for permutation/randomization checks.",
    )
    parser.add_argument(
        "--forward-horizon",
        type=int,
        default=rules.FORWARD_HORIZON,
        help="Forward window used by alpha.",
    )
    return parser.parse_args()


def run_backtest(
    input_path: str,
    out_dir: str,
    seed: int,
    forward_horizon: int,
) -> dict[str, object]:
    channels, week_dates = rules.load_input(input_path)
    results = rules.evaluate_all_rules(
        channels=channels,
        week_count=len(week_dates),
        forward_horizon=forward_horizon,
        seed=seed,
    )
    payload: dict[str, object] = {
        "input": str(Path(input_path)),
        "forward_horizon": forward_horizon,
        "week_count": len(week_dates),
        "seed": seed,
        "rules": {key: asdict(value) for key, value in results.items()},
    }

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "backtest_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "backtest_report.md").write_text(
        _build_report(payload),
        encoding="utf-8",
    )
    return payload


def _build_report(payload: dict[str, object]) -> str:
    rule_titles = {
        "retention_lower_band": "Retention lower-band (4 consecutive weeks)",
        "threshold_1500_inflexion": "1500 inflexion with placebo checks",
        "airtime_uncorrelated": "AirTime and future growth correlation",
        "bottleneck_axis": "Segment-axis bottleneck indicator",
        "growth_outlook": "Growth outlook (efficiency x momentum, §6.3.2)",
    }
    lines = [
        "# Backtest report",
        "",
        f"- input: `{payload['input']}`",
        f"- week_count: `{payload['week_count']}`",
        f"- forward_horizon: `{payload['forward_horizon']}`",
        f"- seed: `{payload['seed']}`",
        "",
        "## Rule results",
        "",
        "|rule|verdict|n|effect_size|evidence|claim_level|",
        "|---|---|---:|---:|---|---|",
    ]

    rules_block = payload.get("rules", {})
    assert isinstance(rules_block, dict)
    for key in (
        "retention_lower_band",
        "threshold_1500_inflexion",
        "airtime_uncorrelated",
        "bottleneck_axis",
        "growth_outlook",
    ):
        item = rules_block.get(key)
        if not isinstance(item, dict):
            continue
        verdict = str(item.get("verdict", rules.VERDICT_INSUFFICIENT))
        effect_size = float(item.get("effect_size") or 0.0)
        n = int(item.get("n") or 0)
        sensitivity = item.get("sensitivity", {})
        evidence = item.get("evidence", {})
        assert isinstance(sensitivity, dict)
        assert isinstance(evidence, dict)

        lines.append(
            f"|{rule_titles.get(key, key)}|"
            f"{verdict}|{n}|"
            f"{effect_size:.4f}|"
            f"{_evidence_summary(key, sensitivity, evidence)}|"
            f"{_claim_level(verdict)}|"
        )

    lines.extend([
        "",
        "## Decision constants",
        "",
        f"- `RETENTION_BAND_Q={rules.RETENTION_BAND_Q}`",
        f"- `RETENTION_STREAK={rules.RETENTION_STREAK}`",
        f"- `RETENTION_RISK_DIFF_MIN={rules.RETENTION_RISK_DIFF_MIN}`",
        f"- `RETENTION_PVALUE_MAX={rules.RETENTION_PVALUE_MAX}`",
        f"- `RETENTION_MIN_SIGNALS={rules.RETENTION_MIN_SIGNALS}`",
        f"- `THRESHOLD_TARGET={rules.THRESHOLD_TARGET}`",
        f"- `THRESHOLD_PLACEBOS={list(rules.THRESHOLD_PLACEBOS)}`",
        f"- `THRESHOLD_MIN_SIGNALS={rules.THRESHOLD_MIN_SIGNALS}`",
        f"- `THRESHOLD_LIFT_MIN={rules.THRESHOLD_LIFT_MIN}`",
        f"- `THRESHOLD_PVALUE_MAX={rules.THRESHOLD_PVALUE_MAX}`",
        f"- `AIRTIME_CORR_MAX_ABS={rules.AIRTIME_CORR_MAX_ABS}`",
        f"- `AIRTIME_CORR_MIN_N={rules.AIRTIME_CORR_MIN_N}`",
        f"- `AIRTIME_CORR_PVALUE_MAX={rules.AIRTIME_CORR_PVALUE_MAX}`",
        f"- `BOTTLENECK_AXIS_Q={rules.BOTTLENECK_AXIS_Q}`",
        f"- `BOTTLENECK_AXIS_WEAK_COUNT_MIN={rules.BOTTLENECK_AXIS_WEAK_COUNT_MIN}`",
        f"- `BOTTLENECK_CORR_MAX={rules.BOTTLENECK_CORR_MAX}`",
        f"- `BOTTLENECK_CORR_PVALUE_MAX={rules.BOTTLENECK_CORR_PVALUE_MAX}`",
        f"- `BOTTLENECK_MIN_SIGNALS={rules.BOTTLENECK_MIN_SIGNALS}`",
        f"- `BOTTLENECK_LIFT_MIN={rules.BOTTLENECK_LIFT_MIN}`",
        f"- `BOTTLENECK_PVALUE_MAX={rules.BOTTLENECK_PVALUE_MAX}`",
        f"- `GROWTH_OUTLOOK_Q_HIGH={rules.GROWTH_OUTLOOK_Q_HIGH}`",
        f"- `GROWTH_OUTLOOK_Q_LOW={rules.GROWTH_OUTLOOK_Q_LOW}`",
        f"- `GROWTH_OUTLOOK_MOMENTUM_WEEKS={rules.GROWTH_OUTLOOK_MOMENTUM_WEEKS}`",
        f"- `GROWTH_OUTLOOK_MIN_SIGNALS={rules.GROWTH_OUTLOOK_MIN_SIGNALS}`",
        f"- `GROWTH_OUTLOOK_LIFT_MIN={rules.GROWTH_OUTLOOK_LIFT_MIN}`",
        f"- `GROWTH_OUTLOOK_PVALUE_MAX={rules.GROWTH_OUTLOOK_PVALUE_MAX}`",
        f"- `PERMUTATION_ROUNDS={rules.PERMUTATION_ROUNDS}`",
        f"- `MOTION_MEDIAN_WINDOW={rules.MOTION_MEDIAN_WINDOW}`",
        f"- `MISSING_DELTA_FALLBACK={rules.MISSING_DELTA_FALLBACK}`",
        f"- `MISSING_DELTA_FALLBACK_Q={rules.MISSING_DELTA_FALLBACK_Q}`",
        f"- `FORWARD_HORIZON={rules.FORWARD_HORIZON}`",
        f"- `RANDOM_SEED={rules.RANDOM_SEED}`",
        "",
        "### Formula/logic changelog",
        "- `_binary_metrics` lift formula: `precision - base_rate` (changed from `recall - base_rate`).",
        "- Retention verdict uses `risk_diff >= RETENTION_RISK_DIFF_MIN` and `pvalue <= RETENTION_PVALUE_MAX`.",
        "- Threshold-delta missing values are replaced by 5th-percentile observed delta (or fallback default if none).",
        "- Missing-outcome sensitivity branch now treats missing outcome as stagnation candidate (`True`).",
        "- `_slope` is relative weekly growth `((end/start)-1)/delta` (changed from absolute delta; segment-pooled comparison needs level-free slopes per trajectory v3 spec).",
        "- Airtime verdict is effect-size-bound only (`abs(rho)<=0.20`); p-value reported as evidence, not required (equivalence claim).",
        "",
        "## Claim-level update",
        "",
        "- support -> L3 keep",
        "- reject  -> downgrade to L2",
        "- insufficient -> hold",
    ])
    return "\n".join(lines)


def _claim_level(verdict: str) -> str:
    if verdict == rules.VERDICT_SUPPORT:
        return "L3"
    if verdict == rules.VERDICT_REJECT:
        return "L2"
    return "hold"


def _evidence_summary(
    key: str,
    sensitivity: dict[str, dict[str, object]],
    evidence: dict[str, object],
) -> str:
    if key == "retention_lower_band":
        payload = sensitivity.get("missing_as_failure", {})
        risk = evidence.get("default_risk_diff")
        pvalue = evidence.get("default_risk_pvalue")
        return (
            f"precision={_format(payload.get('precision'))}, "
            f"recall={_format(payload.get('recall'))}, "
            f"risk_diff={_format(risk)}, "
            f"p={_format(pvalue)}, "
            f"band_q={evidence.get('band_q')}"
        )
    if key == "threshold_1500_inflexion":
        payload = sensitivity.get("missing_as_negative", {})
        return (
            f"effect={_format(payload.get('effect_lift'))}, "
            f"p={_format(payload.get('permutation_pvalue'))}, "
            f"target={evidence.get('target_threshold')}"
        )
    if key == "airtime_uncorrelated":
        payload = sensitivity.get("missing_excluded", {})
        return (
            f"rho={_format(payload.get('spearman_rho'))}, "
            f"p={_format(payload.get('permutation_pvalue'))}, "
            f"n={payload.get('n')}"
        )
    if key == "growth_outlook":
        payload = sensitivity.get("missing_as_failure", {})
        return (
            f"green_rate={_format(evidence.get('green_exceed_rate'))}, "
            f"red_rate={_format(evidence.get('red_exceed_rate'))}, "
            f"base={_format(evidence.get('base_exceed_rate'))}, "
            f"green_p={_format(payload.get('green_pvalue'))}, "
            f"red_p={_format(payload.get('red_pvalue'))}, "
            f"n_green={evidence.get('n_green')}, n_red={evidence.get('n_red')}"
        )
    if key == "bottleneck_axis":
        payload = sensitivity.get("missing_as_negative", {})
        corr = sensitivity.get("severity_corr", {})
        return (
            f"lift={_format(payload.get('lift'))}, "
            f"severity_corr={_format(corr.get('spearman_rho'))}, "
            f"severity_corr_p={_format(corr.get('permutation_pvalue'))}, "
            f"weak_axes_min={evidence.get('weak_axes_min')}, "
            f"axis_q={evidence.get('axis_q')}, "
            f"n={payload.get('n_scored')}"
        )
    return "-"


def _format(value: object) -> str:
    if isinstance(value, int):
        return f"{value}"
    if isinstance(value, float):
        return f"{value:.4f}"
    return "-"


def main() -> int:
    args = parse_args()
    run_backtest(
        input_path=args.input,
        out_dir=args.out,
        seed=args.seed,
        forward_horizon=args.forward_horizon,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
