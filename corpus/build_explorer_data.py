#!/usr/bin/env python3
"""Build compact JSON for corpus_explorer.html.

The source corpus is NDJSON with one tagged prompt per line. This script keeps
the fields needed by the browser dashboard and writes a compact JSON payload
that can be fetched by the single-file HTML explorer.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(__file__).resolve().parent / "data" / "corpus_tagged.ndjson"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "explorer_data.json"
BODY_PREVIEW_LIMIT = 2000


def first_occurrence(record: dict[str, Any]) -> dict[str, Any]:
    occurrences = record.get("occurrences") or []
    if not occurrences:
        return {}
    return occurrences[0]


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{10}", text):
        return datetime(
            int(text[0:4]),
            int(text[4:6]),
            int(text[6:8]),
            int(text[8:10]),
            tzinfo=timezone.utc,
        )
    if re.fullmatch(r"\d{8}", text):
        return datetime(
            int(text[0:4]),
            int(text[4:6]),
            int(text[6:8]),
            tzinfo=timezone.utc,
        )
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def time_fields(occurrence: dict[str, Any]) -> dict[str, Any]:
    published_raw = occurrence.get("published_at")
    collected_raw = occurrence.get("collected_at")
    published = parse_datetime(published_raw)
    collected = parse_datetime(collected_raw)
    chosen = published or collected
    source = "published_at" if published else "collected_at" if collected else None
    fields: dict[str, Any] = {
        "published_at": published_raw,
        "collected_at": collected_raw,
        "time_source": source,
        "time_value": None,
        "time_label": None,
        "time_ts": None,
    }
    if chosen is None:
        return fields
    fields["time_value"] = chosen.isoformat()
    fields["time_ts"] = int(chosen.timestamp())
    if chosen.hour or chosen.minute or chosen.second:
        fields["time_label"] = chosen.strftime("%Y-%m-%d %H:%M")
    else:
        fields["time_label"] = chosen.strftime("%Y-%m-%d")
    return fields


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    tiller = record.get("tiller") or {}
    occurrence = first_occurrence(record)
    body = record.get("body") or ""
    item: dict[str, Any] = {
        "id": record.get("content_id"),
        "body": body,
        "lang": record.get("lang"),
        "domain": record.get("domain"),
        "tokens": record.get("body_tokens"),
        "source": occurrence.get("source_id"),
        "models": record.get("target_models") or [],
        "placeholders": bool(record.get("has_placeholders")),
        "system": bool(record.get("is_system_prompt")),
        "ch": tiller.get("channel"),
        "so": tiller.get("sounding"),
        "ch_reason": tiller.get("channel_reason"),
        "so_reason": tiller.get("sounding_reason"),
        "heading": tiller.get("heading"),
        "berth": tiller.get("berth"),
        "bearing": tiller.get("bearing"),
        "slack": tiller.get("slack"),
        **time_fields(occurrence),
    }
    if len(body) > BODY_PREVIEW_LIMIT:
        item["body_full"] = body
        item["body"] = body[:BODY_PREVIEW_LIMIT] + "..."
    return item


def build(input_path: Path, output_path: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    skipped = 0
    with input_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(compact_record(json.loads(line)))
            except json.JSONDecodeError as exc:
                skipped += 1
                print(f"skip malformed line {line_no}: {exc}")

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(input_path),
            "count": len(records),
            "skipped": skipped,
            "body_preview_limit": BODY_PREVIEW_LIMIT,
        },
        "records": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return payload["meta"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"source NDJSON path (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output JSON path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    meta = build(args.input, args.out)
    size_mb = args.out.stat().st_size / (1024 * 1024)
    print(f"records: {meta['count']:,}")
    print(f"skipped: {meta['skipped']:,}")
    print(f"output: {args.out}")
    print(f"size: {size_mb:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
