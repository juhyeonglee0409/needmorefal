from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from .analysis import analyze_corpus  # type: ignore  # noqa: E402
    from .board_crawler import crawl_sources  # type: ignore  # noqa: E402
    from .board_crawler import DEFAULT_SOURCES_PATH  # type: ignore  # noqa: E402
    from .config import DATA_DIR, ERRORS_PATH, EXTRACTED_DIR, GATED_DIR, GITHUB_SOURCES, PROGRESS_PATH, RAW_DIR, ensure_data_dirs  # type: ignore  # noqa: E402
    from .extract import extract_prompts  # type: ignore  # noqa: E402
    from .gate import gate_urls, page_from_record_or_fetch  # type: ignore  # noqa: E402
    from .github_fetch import fetch_sources  # type: ignore  # noqa: E402
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson, utc_now  # type: ignore  # noqa: E402
    from .normalize import normalize_files  # type: ignore  # noqa: E402
    from .search_serp import DEFAULT_SERP_QUERIES_PATH, load_serp_queries, search_sources  # type: ignore  # noqa: E402
    from .prpt_fetch import fetch_prpt_prompts  # type: ignore  # noqa: E402
    from .tiller_tag import tag_file  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover - direct script execution fallback.
    from analysis import analyze_corpus  # noqa: E402
    from board_crawler import crawl_sources  # noqa: E402
    from board_crawler import DEFAULT_SOURCES_PATH  # noqa: E402
    from config import DATA_DIR, ERRORS_PATH, EXTRACTED_DIR, GATED_DIR, GITHUB_SOURCES, PROGRESS_PATH, RAW_DIR, ensure_data_dirs  # noqa: E402
    from extract import extract_prompts  # noqa: E402
    from gate import gate_urls, page_from_record_or_fetch  # noqa: E402
    from github_fetch import fetch_sources  # noqa: E402
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson, utc_now  # noqa: E402
    from normalize import normalize_files  # noqa: E402
    from search_serp import DEFAULT_SERP_QUERIES_PATH, load_serp_queries, search_sources  # noqa: E402
    from prpt_fetch import fetch_prpt_prompts  # noqa: E402
    from tiller_tag import tag_file  # noqa: E402


RUN_SOURCE_ORDER = ["E1", "E2", "E3", "E4", "E10", "E11", "E12", "E13", "K1", "K6", "K7", "K2", "K10", "K11", "K13", "K14", "K15", "K16", "K12"]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ensure_data_dirs()
    try:
        if args.command == "fetch":
            return cmd_fetch(args)
        if args.command == "search":
            return cmd_search(args)
        if args.command == "crawl":
            return cmd_crawl(args)
        if args.command == "gate":
            return cmd_gate(args)
        if args.command == "extract":
            return cmd_extract(args)
        if args.command == "normalize":
            return cmd_normalize(args)
        if args.command == "tag":
            return cmd_tag(args)
        if args.command == "run":
            return cmd_run(args)
        if args.command == "rebuild":
            return cmd_rebuild(args)
        if args.command == "stats":
            return cmd_stats(args)
        if args.command == "analyze":
            return cmd_analyze(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prompt corpus collection pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Fetch source records")
    fetch.add_argument("--source", "--sources", required=True, help="Comma-separated source IDs, e.g. E1,E2,E3,E4")
    fetch.add_argument("--output", default=str(RAW_DIR / "raw_github.ndjson"))
    fetch.add_argument("--limit", type=int, default=None)
    fetch.add_argument("--sleep-sec", type=float, default=0.2)
    fetch.add_argument("--progress", default=str(PROGRESS_PATH))
    fetch.add_argument("--errors", default=str(ERRORS_PATH))

    search = sub.add_parser("search", help="Collect seed URLs from search APIs")
    search.add_argument("--engine", choices=["google", "naver"], default="google")
    search.add_argument("--source", "--sources", required=True, help="Comma-separated source IDs, e.g. E10,E11,E12")
    search.add_argument("--output-dir", default=str(RAW_DIR))
    search.add_argument("--limit", type=int, default=None)
    search.add_argument("--sleep-sec", type=float, default=2.0)
    search.add_argument("--progress", default=str(PROGRESS_PATH))
    search.add_argument("--errors", default=str(ERRORS_PATH))

    crawl = sub.add_parser("crawl", help="Crawl board/platform pages for post URLs")
    crawl.add_argument("--source", "--sources", required=True, help="Comma-separated source IDs, e.g. K1,K2,K6,K7")
    crawl.add_argument("--output-dir", default=str(RAW_DIR))
    crawl.add_argument("--limit", type=int, default=None)
    crawl.add_argument("--progress", default=str(PROGRESS_PATH))
    crawl.add_argument("--errors", default=str(ERRORS_PATH))

    gate = sub.add_parser("gate", help="Filter URL records with regex and optional LLM gate")
    gate.add_argument("--input", required=True)
    gate.add_argument("--output", required=True)
    gate.add_argument("--regex-only", action="store_true", help="Skip LLM gate; regex uncertain records pass")
    gate.add_argument("--sleep-sec", type=float, default=2.0)
    gate.add_argument("--progress", default=str(PROGRESS_PATH))
    gate.add_argument("--errors", default=str(ERRORS_PATH))

    extract = sub.add_parser("extract", help="Extract prompt bodies from gated page text")
    extract.add_argument("--input", required=True)
    extract.add_argument("--output", required=True)
    extract.add_argument("--progress", default=str(PROGRESS_PATH))
    extract.add_argument("--errors", default=str(ERRORS_PATH))

    normalize = sub.add_parser("normalize", help="Normalize and exact-dedup records")
    normalize.add_argument("--input", nargs="+", required=True, help="Input NDJSON paths or glob patterns")
    normalize.add_argument("--output", default=str(DATA_DIR / "corpus.ndjson"))

    tag = sub.add_parser("tag", help="TILLER tag normalized records")
    tag.add_argument("--input", required=True)
    tag.add_argument("--output", default=str(DATA_DIR / "corpus_tagged.ndjson"))
    tag.add_argument("--mode", choices=["null", "heuristic", "llm", "anthropic"], default="null")
    tag.add_argument("--progress", default=str(PROGRESS_PATH))
    tag.add_argument("--errors", default=str(ERRORS_PATH))

    rebuild = sub.add_parser("rebuild", help="Rebuild canonical corpus from all extracted files")
    rebuild.add_argument("--tag-mode", choices=["null", "heuristic", "llm", "anthropic"], default="heuristic")
    rebuild.add_argument("--progress", default=str(PROGRESS_PATH))
    rebuild.add_argument("--errors", default=str(ERRORS_PATH))

    run = sub.add_parser("run", help="Run routed source collection -> normalize -> tag")
    run.add_argument("--sources", required=True, help="Comma-separated source IDs")
    run.add_argument("--tag-mode", choices=["null", "heuristic", "llm", "anthropic"], default="null")
    run.add_argument("--limit", type=int, default=None)
    run.add_argument("--sleep-sec", type=float, default=0.2)
    run.add_argument("--dry-run", action="store_true", help="Plan source routing without network or LLM calls")
    run.add_argument("--skip-gate", action="store_true", help="Fetch pages and pass all URL records to extraction")
    run.add_argument("--progress", default=str(PROGRESS_PATH))
    run.add_argument("--errors", default=str(ERRORS_PATH))

    stats = sub.add_parser("stats", help="Print corpus statistics")
    stats.add_argument("--input", required=True)

    analyze = sub.add_parser("analyze", help="Analyze normalized or tagged corpus")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--format", choices=["json"], default="json")
    return parser


def parse_sources(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def cmd_fetch(args: argparse.Namespace) -> int:
    output = Path(args.output)
    count = fetch_sources(
        parse_sources(args.source),
        output,
        progress_path=Path(args.progress),
        errors_path=Path(args.errors),
        limit=args.limit,
        sleep_sec=args.sleep_sec,
    )
    print(f"fetch wrote {count} records -> {output}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    count = search_sources(
        parse_sources(args.source),
        Path(args.output_dir),
        progress_path=Path(args.progress),
        errors_path=Path(args.errors),
        limit=args.limit,
        sleep_sec=args.sleep_sec,
    )
    print(f"search wrote {count} URL records -> {args.output_dir}")
    return 0


def cmd_crawl(args: argparse.Namespace) -> int:
    count = crawl_sources(
        parse_sources(args.source),
        Path(args.output_dir),
        progress_path=Path(args.progress),
        errors_path=Path(args.errors),
        limit=args.limit,
    )
    print(f"crawl wrote {count} URL records -> {args.output_dir}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    count = gate_urls(
        Path(args.input),
        Path(args.output),
        progress_path=Path(args.progress),
        errors_path=Path(args.errors),
        sleep_sec=args.sleep_sec,
        llm_gate=not args.regex_only,
    )
    mode = "regex-only" if args.regex_only else "regex+llm"
    print(f"gate wrote {count} records -> {args.output} ({mode})")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    count = extract_prompts(
        Path(args.input),
        Path(args.output),
        progress_path=Path(args.progress),
        errors_path=Path(args.errors),
    )
    print(f"extract wrote {count} records -> {args.output}")
    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    output = Path(args.output)
    stats = normalize_files(args.input, output)
    write_normalize_stats(stats)
    print(f"normalize wrote {stats['records']} records -> {output}")
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    output = Path(args.output)
    count = tag_file(Path(args.input), output, mode=args.mode, progress_path=Path(args.progress), errors_path=Path(args.errors))
    print(f"tag wrote {count} records -> {output} (mode={args.mode})")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    requested = resolve_run_sources(args.sources)
    routes = classify_run_sources(requested)
    if routes["unknown"]:
        print(f"unknown sources: {','.join(routes['unknown'])}", file=sys.stderr)
        return 2

    print_run_plan(routes)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "sources": requested,
                    "routes": routes,
                    "note": "dry-run performs source classification only; no network, LLM, normalize, or tag calls were run.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    raw_github = RAW_DIR / "raw_github.ndjson"
    corpus = DATA_DIR / "corpus.ndjson"
    tagged = DATA_DIR / "corpus_tagged.ndjson"

    normalize_inputs: list[str] = []
    web_sources = routes["google_cse"] + routes["board"] + routes["naver"]

    fetch_count = 0
    if routes["github"]:
        fetch_count = fetch_sources(
            routes["github"],
            raw_github,
            progress_path=Path(args.progress),
            errors_path=Path(args.errors),
            limit=args.limit,
            sleep_sec=args.sleep_sec,
        )
        normalize_inputs.append(str(raw_github))
    print(f"[run] step 1/9: github fetch wrote {fetch_count} records")

    google_count = 0
    if routes["google_cse"]:
        google_count = search_sources(
            routes["google_cse"],
            RAW_DIR,
            progress_path=Path(args.progress),
            errors_path=Path(args.errors),
            limit=args.limit,
            sleep_sec=args.sleep_sec,
        )
    print(f"[run] step 2/9: google_cse search wrote {google_count} URL records")

    board_count = 0
    if routes["board"]:
        board_count = crawl_sources(
            routes["board"],
            RAW_DIR,
            progress_path=Path(args.progress),
            errors_path=Path(args.errors),
            limit=args.limit,
        )
    print(f"[run] step 3/9: board crawl wrote {board_count} URL records")

    naver_count = 0
    if routes["naver"]:
        naver_count = search_sources(
            routes["naver"],
            RAW_DIR,
            progress_path=Path(args.progress),
            errors_path=Path(args.errors),
            limit=args.limit,
            sleep_sec=args.sleep_sec,
        )
    print(f"[run] step 4/9: naver search wrote {naver_count} URL records")

    prpt_count = 0
    if routes["prpt"]:
        for source_id in routes["prpt"]:
            output_path = EXTRACTED_DIR / f"extracted_{source_id}.ndjson"
            prpt_count += fetch_prpt_prompts(
                output_path,
                progress_path=Path(args.progress),
                errors_path=Path(args.errors),
                limit=args.limit,
                sleep_sec=args.sleep_sec,
            )
            normalize_inputs.append(str(output_path))
    print(f"[run] step 5/9: prpt.ai API wrote {prpt_count} extracted records")

    gate_count = 0
    gated_paths: list[Path] = []
    for si, source_id in enumerate(web_sources, 1):
        input_path = RAW_DIR / f"urls_{source_id}.ndjson"
        output_path = GATED_DIR / f"gated_{source_id}.ndjson"
        print(f"[run] step 6/9: gate {source_id} ({si}/{len(web_sources)}) ...", flush=True)
        if args.skip_gate:
            n = pass_all_urls_to_gated(input_path, output_path, progress_path=Path(args.progress), errors_path=Path(args.errors))
        else:
            n = gate_urls(
                input_path,
                output_path,
                progress_path=Path(args.progress),
                errors_path=Path(args.errors),
                sleep_sec=args.sleep_sec,
            )
        gate_count += n
        print(f"[run] step 6/9: gate {source_id} done -{n} pass (total {gate_count})", flush=True)
        gated_paths.append(output_path)
    gate_mode = "skip_gate" if args.skip_gate else "gate"
    print(f"[run] step 6/9: {gate_mode} wrote {gate_count} gated records")

    extract_count = 0
    for si, (source_id, gated_path) in enumerate(zip(web_sources, gated_paths), 1):
        output_path = EXTRACTED_DIR / f"extracted_{source_id}.ndjson"
        print(f"[run] step 7/9: extract {source_id} ({si}/{len(gated_paths)}) ...", flush=True)
        n = extract_prompts(
            gated_path,
            output_path,
            progress_path=Path(args.progress),
            errors_path=Path(args.errors),
        )
        extract_count += n
        print(f"[run] step 7/9: extract {source_id} done -{n} prompts (total {extract_count})", flush=True)
        normalize_inputs.append(str(output_path))
    print(f"[run] step 7/9: extract wrote {extract_count} prompt records")

    normalize_stats = normalize_files(normalize_inputs, corpus)
    write_normalize_stats(normalize_stats)
    print(f"[run] step 8/9: normalize wrote {normalize_stats['records']} records")

    tag_count = tag_file(corpus, tagged, mode=args.tag_mode, progress_path=Path(args.progress), errors_path=Path(args.errors))
    print(f"[run] step 9/9: tag wrote {tag_count} records")
    if args.tag_mode == "null":
        print("[run] WARNING: tag-mode=null -tiller values are empty. Run 'rebuild --tag-mode heuristic' for analysis-ready corpus.", flush=True)
    print(
        json.dumps(
            {
                "sources": requested,
                "routes": routes,
                "github_records_written": fetch_count,
                "google_url_records_written": google_count,
                "board_url_records_written": board_count,
                "naver_url_records_written": naver_count,
                "prpt_records_written": prpt_count,
                "gated_records_written": gate_count,
                "extracted_records_written": extract_count,
                "normalize": normalize_stats,
                "tag_records_written": tag_count,
                "raw_github": str(raw_github),
                "raw_dir": str(RAW_DIR),
                "gated_dir": str(GATED_DIR),
                "extracted_dir": str(EXTRACTED_DIR),
                "corpus": str(corpus),
                "tagged": str(tagged),
                "tag_mode": args.tag_mode,
                "skip_gate": bool(args.skip_gate),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    corpus = DATA_DIR / "corpus.ndjson"
    tagged = DATA_DIR / "corpus_tagged.ndjson"
    known_ids = DATA_DIR / "known_ids.txt"
    progress_path = Path(args.progress)
    errors_path = Path(args.errors)

    inputs = _collect_rebuild_inputs()
    if not inputs:
        print("[rebuild] no input files found", file=sys.stderr)
        return 1

    print("[rebuild] === input validation ===")
    valid = _validate_rebuild_inputs(inputs)
    if not valid:
        return 1

    print("[rebuild] === reset ===")
    for reset_file in (tagged, known_ids):
        try:
            reset_file.unlink(missing_ok=True)
            print(f"  deleted {reset_file.name}")
        except PermissionError:
            reset_file.write_text("", encoding="utf-8")
            print(f"  truncated {reset_file.name} (locked, cleared instead)")
    cleared = _clear_progress_layer(progress_path, "L3")
    print(f"  cleared {cleared} L3 progress entries")

    print("[rebuild] === normalize ===")
    stats = normalize_files([str(p) for p in inputs], corpus)
    write_normalize_stats(stats)
    print(f"  input: {stats['input_records']} records")
    print(f"  exact dedup removed: {stats['exact_dupes_removed']}")
    print(f"  near dedup removed: {stats['near_dupes_removed']}")
    print(f"  quality filtered: {stats['quality_filtered']}")
    print(f"  output: {stats['records']} records -> {corpus}")

    print(f"[rebuild] === tag (mode={args.tag_mode}) ===")
    tag_count = tag_file(corpus, tagged, mode=args.tag_mode, progress_path=progress_path, errors_path=errors_path)
    print(f"  tagged: {tag_count} records -> {tagged}")

    print("[rebuild] === verification ===")
    _print_rebuild_report(corpus, tagged)

    print(json.dumps({
        "rebuild": True,
        "normalize": stats,
        "tag_mode": args.tag_mode,
        "tag_count": tag_count,
    }, ensure_ascii=False, indent=2))
    return 0


def _collect_rebuild_inputs() -> list[Path]:
    inputs: list[Path] = []
    raw_github = RAW_DIR / "raw_github.ndjson"
    if raw_github.exists():
        inputs.append(raw_github)
    for f in sorted(EXTRACTED_DIR.glob("extracted_*.ndjson")):
        inputs.append(f)
    return inputs


def _validate_rebuild_inputs(inputs: list[Path]) -> bool:
    total_rows = 0
    all_ok = True
    for path in inputs:
        try:
            rows = read_ndjson(path)
        except ValueError as exc:
            print(f"  FAIL {path.name}: {exc}", file=sys.stderr)
            all_ok = False
            continue
        missing_body = sum(1 for r in rows if not r.get("body"))
        missing_occ = sum(1 for r in rows if not r.get("occurrences"))
        total_rows += len(rows)
        status = "OK" if missing_body == 0 else f"missing_body={missing_body}"
        if missing_occ:
            status += f" missing_occ={missing_occ}"
        print(f"  {path.name}: {len(rows)} rows -{status}")
    print(f"  total: {total_rows} input rows across {len(inputs)} files")
    return all_ok


def _clear_progress_layer(progress_path: Path, layer: str) -> int:
    if not progress_path.exists():
        return 0
    try:
        from .io_utils import write_ndjson as _write_ndjson
    except ImportError:
        from io_utils import write_ndjson as _write_ndjson
    rows = _read_ndjson_lenient(progress_path)
    kept = [r for r in rows if r.get("layer") != layer]
    cleared = len(rows) - len(kept)
    _write_ndjson(progress_path, kept)
    return cleared


def _read_ndjson_lenient(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    dropped = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                dropped += 1
    if dropped:
        print(f"  warning: dropped {dropped} corrupt lines from {path.name}")
    return records


def _print_rebuild_report(corpus_path: Path, tagged_path: Path) -> None:
    corpus_rows = read_ndjson(corpus_path)
    tagged_rows = read_ndjson(tagged_path)
    print(f"  L2 (corpus): {len(corpus_rows)}")
    print(f"  L3 (tagged): {len(tagged_rows)}")
    match = "PASS" if len(corpus_rows) == len(tagged_rows) else "FAIL"
    print(f"  L2 == L3: {match}")

    source_counts: Counter[str] = Counter()
    for row in corpus_rows:
        for occ in row.get("occurrences", []):
            sid = occ.get("source_id", "?")
            source_counts[sid] += 1
            break
    print("  source distribution:")
    for sid, count in source_counts.most_common():
        print(f"    {sid}: {count}")

    tiller_null = sum(1 for r in tagged_rows if r.get("tiller") is None)
    tiller_set = len(tagged_rows) - tiller_null
    print(f"  tiller: {tiller_set} tagged, {tiller_null} null")

    if tagged_rows:
        helm_dist: dict[str, Counter[str]] = {
            "heading": Counter(), "berth": Counter(), "bearing": Counter(), "slack": Counter(),
        }
        for row in tagged_rows:
            tiller = row.get("tiller")
            if not tiller:
                continue
            for axis in helm_dist:
                val = str(tiller.get(axis, "null"))
                helm_dist[axis][val] += 1
        print("  HELM distribution:")
        for axis, counts in helm_dist.items():
            parts = ", ".join(f"{v}={c}" for v, c in counts.most_common())
            print(f"    {axis}: {parts}")


def cmd_stats(args: argparse.Namespace) -> int:
    return print_analysis(Path(args.input))


def cmd_analyze(args: argparse.Namespace) -> int:
    return print_analysis(Path(args.input))


def print_analysis(input_path: Path) -> int:
    result = analyze_corpus(input_path)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def resolve_run_sources(value: str) -> list[str]:
    if value.strip().upper() == "ALL":
        return all_active_sources()
    return order_sources(parse_sources(value))


def all_active_sources() -> list[str]:
    sources: list[str] = []
    sources.extend(GITHUB_SOURCES.keys())
    sources.extend(load_serp_queries(DEFAULT_SERP_QUERIES_PATH).keys())
    board_sources = load_serp_queries(DEFAULT_SOURCES_PATH)
    sources.extend(
        source_id
        for source_id, config in board_sources.items()
        if config.get("type") in {"community", "platform"} and config.get("enabled") is not False
    )
    return order_sources(dedupe_preserve_order(sources))


def classify_run_sources(source_ids: list[str]) -> dict[str, list[str]]:
    serp_sources = load_serp_queries(DEFAULT_SERP_QUERIES_PATH)
    board_sources = load_serp_queries(DEFAULT_SOURCES_PATH)
    routes: dict[str, list[str]] = {
        "github": [],
        "google_cse": [],
        "board": [],
        "naver": [],
        "prpt": [],
        "unknown": [],
    }
    for source_id in order_sources(dedupe_preserve_order(source_ids)):
        if source_id in GITHUB_SOURCES:
            routes["github"].append(source_id)
            continue
        if source_id in serp_sources:
            engine = serp_sources[source_id].get("engine")
            if engine in ("google_cse", "serper"):
                routes["google_cse"].append(source_id)
            elif engine == "naver":
                routes["naver"].append(source_id)
            else:
                routes["unknown"].append(source_id)
            continue
        if source_id in board_sources:
            if board_sources[source_id].get("type") == "prpt_api":
                routes["prpt"].append(source_id)
            else:
                routes["board"].append(source_id)
            continue
        routes["unknown"].append(source_id)
    return routes


def print_run_plan(routes: dict[str, list[str]]) -> None:
    print("[run] source routing:")
    for key in ["github", "google_cse", "board", "naver", "prpt", "unknown"]:
        values = routes.get(key) or []
        print(f"[run]   {key}: {','.join(values) if values else '-'}")


def pass_all_urls_to_gated(
    input_path: Path,
    output_path: Path,
    *,
    progress_path: Path,
    errors_path: Path,
) -> int:
    progress = load_progress_keys(progress_path)
    written = 0
    for row in read_ndjson(input_path):
        source_id = str(row.get("source_id") or "")
        url = str(row.get("url") or "")
        if not source_id or not url:
            append_error(errors_path, "L0.5", source_id, "invalid_url_record", raw=row)
            continue
        progress_key = ("L0.5", source_id, url)
        if progress_key in progress:
            continue
        try:
            page = page_from_record_or_fetch(row)
            output = {
                "url": url,
                "source_id": source_id,
                "title": row.get("title"),
                "collected_at": row.get("collected_at") or utc_now(),
                "page_text": page["page_text"],
                "structured_blocks": page.get("structured_blocks") or [],
                "gate": {"skipped": True, "pass": True, "reason": "skip_gate"},
            }
            if row.get("render"):
                output["render"] = row.get("render")
            append_ndjson(output_path, output)
            append_progress(progress_path, "L0.5", source_id, url, status="skip_gate")
            progress.add(progress_key)
            written += 1
        except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
            append_error(errors_path, "L0.5", source_id, type(exc).__name__, url=url, detail=str(exc), mode="skip_gate")
            append_progress(progress_path, "L0.5", source_id, url, status="error_skip_gate")
            progress.add(progress_key)
    return written


def write_normalize_stats(stats: dict[str, int]) -> None:
    path = DATA_DIR / "normalize_stats.json"
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def order_sources(source_ids: list[str]) -> list[str]:
    order = {source_id: index for index, source_id in enumerate(RUN_SOURCE_ORDER)}
    return sorted(source_ids, key=lambda source_id: (order.get(source_id, len(order)), source_ids.index(source_id)))


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


if __name__ == "__main__":
    raise SystemExit(main())
