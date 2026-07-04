"""Append-only NDJSON channel pool helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable


class ChannelPool:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def iter_records(self) -> Iterable[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    yield record

    def current_by_channel_id(self) -> dict[str, dict[str, Any]]:
        current: dict[str, dict[str, Any]] = {}
        for record in self.iter_records():
            channel_id = str(record.get("channel_id") or "")
            if channel_id:
                current[channel_id] = record
        return current

    def opted_out_ids(self) -> set[str]:
        ids: set[str] = set()
        for record in self.iter_records():
            channel_id = str(record.get("channel_id") or "")
            if channel_id and _outreach_status(record) == "opted_out":
                ids.add(channel_id)
        return ids

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()


class ProgressLog:
    def __init__(self, path: str | Path | None) -> None:
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> None:
        if self.path is None:
            return
        record = {"generated_at": _now(), **event}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()


def _outreach_status(record: dict[str, Any]) -> str | None:
    outreach = record.get("outreach")
    if isinstance(outreach, dict):
        status = outreach.get("status")
        if status:
            return str(status)
    return None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
