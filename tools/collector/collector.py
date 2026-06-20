"""Universal Collector — config-driven collection CLI.

Usage:
    python -m tools.collector.collector collect --config configs/gubiba_step5.yaml
    python -m tools.collector.collector verify --config configs/gubiba_step5.yaml
    python -m tools.collector.collector collect --config configs/gubiba_step5.yaml --limit 3
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .config import Config, load_config
from .engines.base import Engine
from .extractors import dom_eval
from .rate import RateController, SignalSkip
from .targets import Target, dedupe_targets, load_targets
from .tracking import Tracking


# ------------------------------------------------------------------
# Engine factory
# ------------------------------------------------------------------

def create_engine(config: Config) -> Engine:
    if config.engine_type == "nodriver":
        from .engines.nodriver_engine import NodriverEngine

        return NodriverEngine(
            headless=config.engine_headless,
            lang=config.engine_lang,
            profile_dir=config.engine_profile_dir,
        )
    if config.engine_type == "http":
        from .engines.http_engine import HttpEngine

        return HttpEngine()
    raise ValueError(f"unknown engine: {config.engine_type}")


# ------------------------------------------------------------------
# URL builder
# ------------------------------------------------------------------

def build_url(config: Config, target: Target) -> str:
    url = config.url_template.format(
        channelId=target.channel_id,
        group=target.group,
        name=target.name,
    )
    if config.url_params:
        url += ("&" if "?" in url else "?") + urlencode(config.url_params)
    return url


# ------------------------------------------------------------------
# Output path
# ------------------------------------------------------------------

def output_path_for(config: Config, target: Target) -> Path:
    name = config.output_file_pattern.format(
        channelId=target.channel_id,
        group=target.group,
        name=target.name,
    )
    return config.resolve(config.output_dir) / name


# ------------------------------------------------------------------
# Collect
# ------------------------------------------------------------------

async def run_collect(config: Config, cli: argparse.Namespace) -> int:
    # load & dedupe targets
    all_targets = load_targets(config)
    targets, memberships = dedupe_targets(all_targets, config.dedupe_priority) \
        if config.dedupe_enabled else (all_targets, [])

    # resolve output dir
    out_dir = config.resolve(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ensure group subdirectories exist
    for t in targets:
        (out_dir / t.group).mkdir(exist_ok=True)

    # tracking
    tracking = Tracking(output_dir=out_dir)
    tracking.init_paths(config.job_name)

    # filter completed (resume)
    window = tracking.filter_completed(
        targets,
        skip_existing=config.resume_skip_existing,
        skip_progress=config.resume_skip_progress,
        progress_glob=config.resume_progress_glob,
        output_file_pattern=config.output_file_pattern,
    )

    # apply CLI offset/limit
    offset = getattr(cli, "offset", 0) or 0
    limit = getattr(cli, "limit", None)
    window = window[offset:]
    if limit is not None:
        window = window[:limit]

    # rate controller
    rate = RateController(
        delay_ms=config.rate_delay_ms,
        jitter_ms=config.rate_jitter_ms,
        seed=config.rate_seed,
        signals=config.signals,
    )

    # load JS expression template (for dom_eval)
    expression_template: str | None = None
    if config.extraction_method == "dom_eval":
        expression_template = dom_eval.load_expression(config)

    # record start
    tracking.record_start({
        "job": config.job_name,
        "method": config.engine_type,
        "extraction": config.extraction_method,
        "total_targets": len(targets),
        "attempted": len(window),
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
    })

    # run
    engine = create_engine(config)
    successes: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    boundary_signal: str | None = None

    try:
        await engine.start()
        total = len(targets)

        for idx, target in enumerate(window, start=1):
            ordinal = offset + idx
            progress = f"{ordinal}/{total}"
            url = build_url(config, target)

            try:
                if config.extraction_method == "dom_eval":
                    assert expression_template is not None
                    expr = dom_eval.build_expression(expression_template, target)
                    state = await dom_eval.extract_one(
                        engine, target, url, expr, config, rate,
                    )
                elif config.extraction_method == "api_json":
                    from .extractors import api_json
                    state = await api_json.extract_one(engine, target, url)
                else:
                    raise ValueError(f"unknown extraction method: {config.extraction_method}")

                rows = [row.get("values", row) for row in state.get("rows", [])]
                row_count = len(rows)
                out = output_path_for(config, target)

                if rows and config.output_columns:
                    dom_eval.write_csv(out, rows, config.output_columns)
                elif rows:
                    # auto-detect columns from first row
                    cols = list(rows[0].keys())
                    dom_eval.write_csv(out, rows, cols)

                status = "success" if row_count >= config.validation_min_rows else "short_rows"
                record = {
                    "progress": progress,
                    "group": target.group,
                    "channel_id": target.channel_id,
                    "name": target.name,
                    "row_count": row_count,
                    "status": status,
                    "output_path": str(out) if rows else "",
                    "source_url": state.get("url", url),
                }
                successes.append(record)
                tracking.record_success(
                    target, row_count,
                    status=status,
                    progress=progress,
                    source_url=state.get("url", url),
                    output_path=str(out) if rows else "",
                )
                print(json.dumps({
                    "progress": progress,
                    "channelId": target.channel_id,
                    "rowCount": row_count,
                    "status": status,
                }, ensure_ascii=False))

            except SignalSkip as skip:
                record_e = {
                    "progress": progress,
                    "group": target.group,
                    "channel_id": target.channel_id,
                    "name": target.name,
                    "error": skip.signal_name,
                }
                errors.append(record_e)
                tracking.record_error(target, skip.signal_name, progress=progress)
                print(json.dumps({
                    "progress": progress,
                    "channelId": target.channel_id,
                    "error": skip.signal_name,
                }, ensure_ascii=False))

            except Exception as exc:
                reason = str(exc)
                record_e = {
                    "progress": progress,
                    "group": target.group,
                    "channel_id": target.channel_id,
                    "name": target.name,
                    "error": reason,
                }
                errors.append(record_e)
                tracking.record_error(target, reason, progress=progress)
                print(json.dumps({
                    "progress": progress,
                    "channelId": target.channel_id,
                    "error": reason,
                }, ensure_ascii=False))

                if reason in {"429", "checkpoint", "checkpoint_or_rate_boundary"}:
                    boundary_signal = reason
                    break

            # rate limit between requests (skip after last)
            if idx < len(window):
                await rate.wait()

    finally:
        await engine.stop()

    # manifest
    manifest = {
        "job": config.job_name,
        "method": config.engine_type,
        "extraction": config.extraction_method,
        "output_dir": str(out_dir),
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
        "url_template": config.url_template,
        "url_params": config.url_params,
        "target_summary": {
            "total_before_dedupe": len(all_targets),
            "unique_after_dedupe": len(targets),
            "attempted": len(window),
        },
        "success_count": sum(1 for s in successes if s["status"] == "success"),
        "short_rows_count": sum(1 for s in successes if s["status"] == "short_rows"),
        "error_count": len(errors),
        "boundary_signal": boundary_signal,
        "memberships": memberships,
        "successes": successes,
        "errors": errors,
    }
    tracking.write_manifest(manifest)
    tracking.write_errors(errors)
    tracking.record_done({
        "success_count": manifest["success_count"],
        "short_rows_count": manifest["short_rows_count"],
        "error_count": manifest["error_count"],
        "boundary_signal": boundary_signal,
    })

    print(json.dumps({
        "manifest": str(tracking.manifest_path),
        "progress": str(tracking.progress_path),
        "errors": str(tracking.errors_path),
        "successCount": manifest["success_count"],
        "shortRowsCount": manifest["short_rows_count"],
        "errorCount": manifest["error_count"],
        "boundarySignal": boundary_signal,
    }, ensure_ascii=False, indent=2))

    return 0


# ------------------------------------------------------------------
# Verify
# ------------------------------------------------------------------

def run_verify(config: Config) -> int:
    """Verify collected outputs against config expectations."""
    out_dir = config.resolve(config.output_dir)
    all_targets = load_targets(config)
    targets, _ = dedupe_targets(all_targets, config.dedupe_priority) \
        if config.dedupe_enabled else (all_targets, [])

    ok = 0
    missing = 0
    short = 0
    columns = config.output_columns

    for target in targets:
        path = output_path_for(config, target)
        if not path.exists():
            missing += 1
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) < config.validation_min_rows:
            short += 1
            print(f"SHORT  {target.channel_id}  rows={len(rows)}  min={config.validation_min_rows}")
        else:
            ok += 1
        # check column consistency
        if columns and rows:
            actual = list(rows[0].keys())
            if actual != columns:
                print(f"COLS   {target.channel_id}  expected={columns}  actual={actual}")

    total = len(targets)
    print(f"\nVerify: {ok}/{total} ok, {missing} missing, {short} short_rows")
    return 0 if (missing == 0 and short == 0) else 1


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="collector",
        description="Universal config-driven collection framework.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = sub.add_parser("collect", help="Run collection")
    p_collect.add_argument("--config", required=True, help="Path to YAML config")
    p_collect.add_argument("--offset", type=int, default=0)
    p_collect.add_argument("--limit", type=int, default=None)

    # verify
    p_verify = sub.add_parser("verify", help="Verify collected outputs")
    p_verify.add_argument("--config", required=True, help="Path to YAML config")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    if args.command == "collect":
        return asyncio.run(run_collect(config, args))
    if args.command == "verify":
        return run_verify(config)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
