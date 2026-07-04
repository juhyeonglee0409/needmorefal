"""CLI orchestration for the CHZZK outreach candidate pipeline."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable

from .chzzk import BoundarySignal, ChzzkClient, ChzzkError, merge_candidate_detail
from .classify import build_channel_record, load_agency_rules
from .pool import ChannelPool, ProgressLog


DEFAULT_KEYWORDS = (
    "버튜버",
    "버츄얼",
    "버추얼",
    "Vtuber",
    "V튜버",
    "버미육",
    "신인 버튜버",
)


def run_collect(args: argparse.Namespace) -> int:
    agency_rules = load_agency_rules(args.agencies)
    pool = ChannelPool(args.pool)
    progress = ProgressLog(args.progress)
    client = ChzzkClient(timeout_seconds=args.timeout_seconds)
    opted_out = pool.opted_out_ids()
    seen: set[str] = set()
    summary = {
        "source": args.source,
        "keywords": args.keywords,
        "searched": 0,
        "discovered": 0,
        "appended": 0,
        "skipped_duplicate": 0,
        "skipped_opted_out": 0,
        "errors": 0,
        "boundary_signal": None,
    }

    progress.append({
        "event": "start",
        "source": args.source,
        "pool": str(Path(args.pool)),
        "raw_json_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
    })

    try:
        for candidate in iter_candidates(client, args):
            summary["discovered"] += 1
            channel_id = str(candidate.get("channel_id") or "")
            if not channel_id:
                summary["errors"] += 1
                progress.append({"event": "error", "error": "missing_channel_id", "candidate": candidate})
                continue
            if channel_id in seen:
                summary["skipped_duplicate"] += 1
                progress.append({"event": "skip_duplicate", "channel_id": channel_id})
                continue
            seen.add(channel_id)

            if channel_id in opted_out:
                summary["skipped_opted_out"] += 1
                progress.append({"event": "skip_opted_out", "channel_id": channel_id})
                continue

            record_input = candidate
            if not args.no_details:
                _sleep(args.delay_seconds)
                detail = client.channel_detail(channel_id)
                record_input = merge_candidate_detail(candidate, detail)

            record = build_channel_record(record_input, agency_rules=agency_rules)
            pool.append(record)
            summary["appended"] += 1
            progress.append({
                "event": "append",
                "channel_id": channel_id,
                "status": record["outreach"]["status"],
                "segment": record["segment"],
                "email": bool(record["email"]["value"]),
            })

            if args.max_candidates and summary["appended"] >= args.max_candidates:
                break
            _sleep(args.delay_seconds)

    except BoundarySignal as exc:
        summary["boundary_signal"] = exc.signal
        progress.append({"event": "boundary", "signal": exc.signal, "error": str(exc)})
    except ChzzkError as exc:
        summary["errors"] += 1
        progress.append({"event": "error", "error": str(exc)})

    progress.append({"event": "done", **summary})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["boundary_signal"] is None else 2


def iter_candidates(client: ChzzkClient, args: argparse.Namespace) -> Iterable[dict[str, Any]]:
    for keyword in args.keywords:
        for page in range(args.pages):
            offset = args.offset_start + (page * args.size)
            if args.source in {"channels", "both"}:
                for item in client.search_channels(keyword, offset=offset, size=args.size):
                    yield item
                _sleep(args.delay_seconds)
            if args.source in {"lives", "both"}:
                for item in client.search_lives(keyword, offset=offset, size=args.size):
                    yield item
                _sleep(args.delay_seconds)


def run_normalize(args: argparse.Namespace) -> int:
    agency_rules = load_agency_rules(args.agencies)
    pool = ChannelPool(args.pool)
    progress = ProgressLog(args.progress)
    opted_out = pool.opted_out_ids()
    summary = {
        "input": str(Path(args.input)),
        "appended": 0,
        "skipped_opted_out": 0,
        "errors": 0,
    }

    progress.append({
        "event": "start_normalize",
        "input": summary["input"],
        "pool": str(Path(args.pool)),
    })

    with Path(args.input).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                summary["errors"] += 1
                progress.append({
                    "event": "error",
                    "line": line_number,
                    "error": f"json_decode: {exc.msg}",
                })
                continue
            if not isinstance(raw, dict):
                summary["errors"] += 1
                progress.append({"event": "error", "line": line_number, "error": "not_object"})
                continue

            channel_id = str(raw.get("channel_id") or raw.get("channelId") or "")
            if channel_id in opted_out:
                summary["skipped_opted_out"] += 1
                progress.append({"event": "skip_opted_out", "channel_id": channel_id})
                continue

            record = build_channel_record(raw, agency_rules=agency_rules)
            pool.append(record)
            summary["appended"] += 1
            progress.append({
                "event": "append",
                "channel_id": record["channel_id"],
                "status": record["outreach"]["status"],
                "segment": record["segment"],
                "email": bool(record["email"]["value"]),
            })

    progress.append({"event": "done_normalize", **summary})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["errors"] == 0 else 1


def run_enrich_census(args: argparse.Namespace) -> int:
    """Cross-reference a softcon census against the CHZZK channel API.

    Reads a census NDJSON (channel_id + softcon metrics), fetches follower/bio
    for each channel via the public CHZZK detail API, classifies it, joins the
    softcon metrics into the record, and upserts into the append-only pool.
    Batch with --limit + --skip-existing; each item flushes immediately.
    """
    agency_rules = load_agency_rules(args.agencies)
    pool = ChannelPool(args.pool)
    progress = ProgressLog(args.progress)
    client = ChzzkClient(timeout_seconds=args.timeout_seconds)

    opted_out = pool.opted_out_ids()
    current = pool.current_by_channel_id()
    already_enriched = {
        cid for cid, rec in current.items()
        if rec.get("follower_count") is not None
    }

    summary = {
        "input": str(Path(args.input)),
        "seen": 0,
        "skipped_existing": 0,
        "skipped_opted_out": 0,
        "enriched": 0,
        "errors": 0,
        "boundary_signal": None,
    }
    progress.append({
        "event": "start_enrich_census",
        "input": summary["input"],
        "pool": str(Path(args.pool)),
        "skip_existing": bool(args.skip_existing),
        "limit": args.limit,
    })

    processed = 0
    with Path(args.input).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if args.limit is not None and processed >= args.limit:
                break
            if not line.strip():
                continue
            try:
                census = json.loads(line)
            except json.JSONDecodeError as exc:
                summary["errors"] += 1
                progress.append({"event": "error", "line": line_number, "error": f"json_decode: {exc.msg}"})
                continue
            if not isinstance(census, dict):
                summary["errors"] += 1
                progress.append({"event": "error", "line": line_number, "error": "not_object"})
                continue

            channel_id = str(census.get("channel_id") or census.get("channelId") or "")
            if not channel_id:
                summary["errors"] += 1
                progress.append({"event": "error", "line": line_number, "error": "missing_channel_id"})
                continue

            summary["seen"] += 1
            if channel_id in opted_out:
                summary["skipped_opted_out"] += 1
                progress.append({"event": "skip_opted_out", "channel_id": channel_id})
                continue
            if args.skip_existing and channel_id in already_enriched:
                summary["skipped_existing"] += 1
                continue

            processed += 1
            try:
                detail = client.channel_detail(channel_id)
            except BoundarySignal as exc:
                summary["boundary_signal"] = str(exc)
                progress.append({"event": "boundary", "channel_id": channel_id, "signal": str(exc)})
                break
            except ChzzkError as exc:
                summary["errors"] += 1
                progress.append({"event": "error", "channel_id": channel_id, "error": str(exc)})
                _sleep(args.delay_seconds)
                continue

            record = build_channel_record(detail, agency_rules=agency_rules)
            softcon = census.get("softcon")
            if isinstance(softcon, dict):
                record["metrics"]["softcon"] = softcon
                if softcon.get("avg") is not None:
                    record["metrics"]["avg_viewers_30d"] = softcon.get("avg")
            pool.append(record)
            already_enriched.add(channel_id)
            summary["enriched"] += 1
            progress.append({
                "event": "enrich",
                "channel_id": channel_id,
                "status": record["outreach"]["status"],
                "segment": record["segment"],
                "follower_count": record["follower_count"],
                "email": bool(record["email"]["value"]),
            })
            _sleep(args.delay_seconds)

    progress.append({"event": "done_enrich_census", **summary})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["errors"] == 0 and summary["boundary_signal"] is None else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="outreach",
        description="Public CHZZK outreach candidate discovery pipeline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="Run CHZZK search/enrich/classify")
    p_collect.add_argument("--pool", required=True, help="Append-only channel-pool NDJSON")
    p_collect.add_argument("--progress", default=None, help="Optional progress NDJSON")
    p_collect.add_argument("--agencies", default=None, help="Agency exclusion YAML/JSON")
    p_collect.add_argument("--source", choices=["channels", "lives", "both"], default="lives")
    p_collect.add_argument("--keywords", nargs="+", default=list(DEFAULT_KEYWORDS))
    p_collect.add_argument("--pages", type=int, default=1)
    p_collect.add_argument("--size", type=int, default=30)
    p_collect.add_argument("--offset-start", type=int, default=0)
    p_collect.add_argument("--max-candidates", type=int, default=None)
    p_collect.add_argument("--delay-seconds", type=float, default=1.0)
    p_collect.add_argument("--timeout-seconds", type=float, default=15.0)
    p_collect.add_argument("--no-details", action="store_true")

    p_normalize = sub.add_parser("normalize", help="Append existing NDJSON to canonical pool")
    p_normalize.add_argument("--input", required=True, help="Input candidate NDJSON")
    p_normalize.add_argument("--pool", required=True, help="Append-only channel-pool NDJSON")
    p_normalize.add_argument("--progress", default=None, help="Optional progress NDJSON")
    p_normalize.add_argument("--agencies", default=None, help="Agency exclusion YAML/JSON")

    p_enrich = sub.add_parser(
        "enrich-census",
        help="Cross-reference a softcon census against the CHZZK channel API",
    )
    p_enrich.add_argument("--input", required=True, help="Softcon census NDJSON (channel_id + softcon)")
    p_enrich.add_argument("--pool", required=True, help="Append-only channel-pool NDJSON")
    p_enrich.add_argument("--progress", default=None, help="Optional progress NDJSON")
    p_enrich.add_argument("--agencies", default=None, help="Agency exclusion YAML/JSON")
    p_enrich.add_argument("--limit", type=int, default=None, help="Max channels to enrich this batch")
    p_enrich.add_argument("--skip-existing", action="store_true", help="Skip channels already enriched in the pool")
    p_enrich.add_argument("--delay-seconds", type=float, default=0.35)
    p_enrich.add_argument("--timeout-seconds", type=float, default=15.0)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "collect":
        return run_collect(args)
    if args.command == "normalize":
        return run_normalize(args)
    if args.command == "enrich-census":
        return run_enrich_census(args)
    return 1


def _sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
