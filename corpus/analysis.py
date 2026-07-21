from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .config import DATA_DIR, GITHUB_SOURCES
    from .io_utils import read_ndjson
    from .search_serp import DEFAULT_SERP_QUERIES_PATH, load_serp_queries
    from .board_crawler import DEFAULT_SOURCES_PATH
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import DATA_DIR, GITHUB_SOURCES
    from io_utils import read_ndjson
    from search_serp import DEFAULT_SERP_QUERIES_PATH, load_serp_queries
    from board_crawler import DEFAULT_SOURCES_PATH


def analyze_corpus(input_path: Path) -> dict[str, Any]:
    rows = read_ndjson(input_path)
    source_counts: Counter[str] = Counter()
    multi_source_records = 0
    for row in rows:
        sources = occurrence_sources(row)
        for source_id in sources:
            source_counts[source_id] += 1
        if len(sources) > 1:
            multi_source_records += 1

    tokens = [int(row.get("body_tokens") or 0) for row in rows if row.get("body_tokens") is not None]
    active_sources = configured_active_sources()
    covered_sources = set(source_counts) & set(active_sources)
    tiller_stats = analyze_tiller(rows)

    return {
        "input": str(input_path),
        "records": len(rows),
        "source_counts": dict(sorted(source_counts.items())),
        "source_coverage": {
            "configured_active_sources": len(active_sources),
            "sources_with_records": len(covered_sources),
            "coverage_ratio": safe_ratio(len(covered_sources), len(active_sources)),
            "missing_sources": [source for source in active_sources if source not in covered_sources],
        },
        "lang": dict(Counter(str(row.get("lang") or "unknown") for row in rows)),
        "domain": dict(Counter(str(row.get("domain") or "unknown") for row in rows)),
        "target_models": dict(Counter(model for row in rows for model in row.get("target_models", []) or [])),
        "tiller": tiller_stats,
        "tokens": token_stats(tokens),
        "dedup": load_normalize_stats(),
        "cross_source_overlap": {
            "records_with_multiple_sources": multi_source_records,
            "ratio": safe_ratio(multi_source_records, len(rows)),
        },
    }


def analyze_tiller(rows: list[dict[str, Any]]) -> dict[str, Any]:
    heatmap = {f"C{channel}": {f"S{sounding}": 0 for sounding in range(1, 5)} for channel in range(1, 5)}
    helm_axes: dict[str, Counter[str]] = {
        "heading": Counter(),
        "berth": Counter(),
        "bearing": Counter(),
        "slack": Counter(),
    }
    untagged = 0
    invalid = 0
    for row in rows:
        tiller = row.get("tiller")
        if not isinstance(tiller, dict):
            untagged += 1
            continue
        try:
            channel = int(tiller.get("channel"))
            sounding = int(tiller.get("sounding"))
        except (TypeError, ValueError):
            invalid += 1
            continue
        if channel not in {1, 2, 3, 4} or sounding not in {1, 2, 3, 4}:
            invalid += 1
            continue
        heatmap[f"C{channel}"][f"S{sounding}"] += 1
        for axis in helm_axes:
            helm_axes[axis][str(tiller.get(axis) or "null")] += 1
    tagged = len(rows) - untagged - invalid
    return {
        "tagged": tagged,
        "untagged": untagged,
        "invalid": invalid,
        "untagged_ratio": safe_ratio(untagged, len(rows)),
        "channel_sounding_heatmap": heatmap,
        "helm_axes": {axis: dict(counter) for axis, counter in helm_axes.items()},
    }


def token_stats(tokens: list[int]) -> dict[str, Any]:
    if not tokens:
        return {
            "min": 0,
            "max": 0,
            "median": 0,
            "p95": 0,
            "histogram": {},
        }
    sorted_tokens = sorted(tokens)
    return {
        "min": sorted_tokens[0],
        "max": sorted_tokens[-1],
        "median": percentile(sorted_tokens, 0.5),
        "p95": percentile(sorted_tokens, 0.95),
        "histogram": token_histogram(sorted_tokens),
    }


def token_histogram(tokens: list[int]) -> dict[str, int]:
    buckets = {
        "0-50": 0,
        "51-100": 0,
        "101-250": 0,
        "251-500": 0,
        "501-1000": 0,
        "1001-3000": 0,
        "3001+": 0,
    }
    for token in tokens:
        if token <= 50:
            buckets["0-50"] += 1
        elif token <= 100:
            buckets["51-100"] += 1
        elif token <= 250:
            buckets["101-250"] += 1
        elif token <= 500:
            buckets["251-500"] += 1
        elif token <= 1000:
            buckets["501-1000"] += 1
        elif token <= 3000:
            buckets["1001-3000"] += 1
        else:
            buckets["3001+"] += 1
    return buckets


def percentile(sorted_values: list[int], ratio: float) -> int:
    if not sorted_values:
        return 0
    index = int(round((len(sorted_values) - 1) * ratio))
    return sorted_values[index]


def occurrence_sources(row: dict[str, Any]) -> set[str]:
    sources: set[str] = set()
    for occurrence in row.get("occurrences", []) or []:
        if isinstance(occurrence, dict) and occurrence.get("source_id"):
            sources.add(str(occurrence["source_id"]))
    return sources


def configured_active_sources() -> list[str]:
    source_ids: list[str] = []
    source_ids.extend(GITHUB_SOURCES.keys())
    serp_sources = load_serp_queries(DEFAULT_SERP_QUERIES_PATH)
    source_ids.extend(serp_sources.keys())
    board_sources = load_serp_queries(DEFAULT_SOURCES_PATH)
    source_ids.extend(
        source_id
        for source_id, config in board_sources.items()
        if config.get("type") in {"community", "platform"} and config.get("enabled") is not False
    )
    return dedupe_preserve_order(source_ids)


def load_normalize_stats() -> dict[str, Any] | None:
    path = DATA_DIR / "normalize_stats.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_normalize_stats_json", "path": str(path)}


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
