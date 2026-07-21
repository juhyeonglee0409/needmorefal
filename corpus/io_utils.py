from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_ndjson(path: Path, record: dict[str, Any]) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def write_ndjson(path: Path, records: Iterable[dict[str, Any]]) -> int:
    ensure_parent(path)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")
            count += 1
        f.flush()
        os.fsync(f.fileno())
    return count


def read_ndjson(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return records


def load_progress_keys(path: Path) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for row in read_ndjson(path):
        layer = str(row.get("layer") or "")
        source_id = str(row.get("source_id") or "")
        item = str(row.get("url") or row.get("content_id") or "")
        if layer and item:
            keys.add((layer, source_id, item))
    return keys


def append_progress(path: Path, layer: str, source_id: str, item: str, status: str = "done") -> None:
    field = "content_id" if layer == "L3" else "url"
    append_ndjson(
        path,
        {
            "layer": layer,
            "source_id": source_id,
            field: item,
            "status": status,
            "at": utc_now(),
        },
    )


def append_error(path: Path, layer: str, source_id: str, error: str, **extra: Any) -> None:
    payload = {
        "layer": layer,
        "source_id": source_id,
        "error": error,
        "at": utc_now(),
    }
    payload.update(extra)
    append_ndjson(path, payload)

