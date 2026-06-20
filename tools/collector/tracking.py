"""Tracking — progress NDJSON, manifest JSON, error CSV, resume filtering."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .targets import Target


@dataclass
class Tracking:
    """Manages progress recording and resume state for a collection run."""

    output_dir: Path
    progress_path: Path | None = None
    manifest_path: Path | None = None
    errors_path: Path | None = None
    _completed_ids: set[str] = field(default_factory=set, repr=False)

    # ------------------------------------------------------------------
    # Init helpers
    # ------------------------------------------------------------------

    def init_paths(
        self,
        job_name: str,
        *,
        progress_name: str | None = None,
        manifest_name: str | None = None,
        errors_name: str | None = None,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_path = self.output_dir / (
            progress_name or f"_collection_progress_{job_name}.ndjson"
        )
        self.manifest_path = self.output_dir / (
            manifest_name or f"_collection_manifest_{job_name}.json"
        )
        self.errors_path = self.output_dir / (
            errors_name or f"_collection_errors_{job_name}.csv"
        )

    # ------------------------------------------------------------------
    # Resume
    # ------------------------------------------------------------------

    def load_completed_from_progress(self, glob_pattern: str) -> None:
        """Scan existing progress NDJSON files for completed channel IDs."""
        for path in self.output_dir.glob(glob_pattern):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") in {"collected", "error"}:
                    cid = str(event.get("channel_id", "")).strip()
                    if cid:
                        self._completed_ids.add(cid)

    def is_completed(self, channel_id: str) -> bool:
        return channel_id in self._completed_ids

    def filter_completed(
        self,
        targets: list[Target],
        *,
        skip_existing: bool = True,
        skip_progress: bool = True,
        progress_glob: str = "_collection_progress_*.ndjson",
        output_file_pattern: str = "{channelId}.csv",
    ) -> list[Target]:
        """Remove targets that already have results or progress records."""
        if skip_progress:
            self.load_completed_from_progress(progress_glob)

        remaining: list[Target] = []
        for t in targets:
            if skip_progress and self.is_completed(t.channel_id):
                continue
            if skip_existing:
                out = self._target_output_path(t, output_file_pattern)
                if out.exists():
                    continue
            remaining.append(t)
        return remaining

    def _target_output_path(self, target: Target, pattern: str) -> Path:
        name = pattern.format(
            group=target.group,
            channelId=target.channel_id,
            name=target.name,
        )
        return self.output_dir / name

    # ------------------------------------------------------------------
    # Progress NDJSON
    # ------------------------------------------------------------------

    def append_progress(self, event: dict[str, Any]) -> None:
        if self.progress_path is None:
            return
        record = {"generated_at": _now(), **event}
        with self.progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    def record_start(self, meta: dict[str, Any]) -> None:
        self.append_progress({"event": "start", **meta})

    def record_success(
        self,
        target: Target,
        row_count: int,
        *,
        status: str = "success",
        progress: str = "",
        source_url: str = "",
        output_path: str = "",
    ) -> None:
        self.append_progress({
            "event": "collected",
            "progress": progress,
            "group": target.group,
            "channel_id": target.channel_id,
            "name": target.name,
            "row_count": row_count,
            "status": status,
            "output_path": output_path,
            "source_url": source_url,
        })

    def record_error(
        self,
        target: Target,
        reason: str,
        *,
        progress: str = "",
    ) -> None:
        self.append_progress({
            "event": "error",
            "progress": progress,
            "group": target.group,
            "channel_id": target.channel_id,
            "name": target.name,
            "error": reason,
        })

    def record_done(self, summary: dict[str, Any]) -> None:
        self.append_progress({"event": "done", **summary})

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------

    def write_manifest(self, manifest: dict[str, Any]) -> None:
        if self.manifest_path is None:
            return
        manifest["generated_at"] = _now()
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Error CSV
    # ------------------------------------------------------------------

    def write_errors(self, errors: list[dict[str, str]]) -> None:
        if self.errors_path is None:
            return
        cols = ["group", "channel_id", "name", "error", "progress"]
        with self.errors_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(errors)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
