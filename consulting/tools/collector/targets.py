"""Target loading — CSV/JSON sources, filtering, deduplication."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config, TargetSource


@dataclass
class Target:
    group: str
    channel_id: str
    name: str


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _load_csv_source(path: Path, src: TargetSource) -> list[Target]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    targets: list[Target] = []
    for row in rows:
        if src.filter:
            col = src.filter.get("column", "")
            if src.filter.get("truthy") and not _truthy(row.get(col, "")):
                continue
            if "value" in src.filter and str(row.get(col, "")) != str(src.filter["value"]):
                continue
        channel_id = str(row.get(src.id_column, "")).strip()
        if not channel_id:
            continue
        targets.append(Target(
            group=src.group,
            channel_id=channel_id,
            name=str(row.get(src.name_column, "")),
        ))
    return targets


def _load_json_source(path: Path, src: TargetSource) -> list[Target]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"JSON source must be a list or contain 'targets': {path}")
    targets: list[Target] = []
    for row in rows:
        channel_id = str(row.get(src.id_column, "")).strip()
        if not channel_id:
            continue
        targets.append(Target(
            group=row.get("group", src.group),
            channel_id=channel_id,
            name=str(row.get(src.name_column, row.get("name", ""))),
        ))
    return targets


def load_targets(config: Config) -> list[Target]:
    """Load targets from all configured sources."""
    all_targets: list[Target] = []
    for src in config.target_sources:
        path = config.resolve(src.file)
        if not path.exists():
            raise FileNotFoundError(f"target source not found: {path}")
        if src.format == "csv":
            all_targets.extend(_load_csv_source(path, src))
        elif src.format == "json":
            all_targets.extend(_load_json_source(path, src))
        else:
            raise ValueError(f"unsupported target format: {src.format}")
    return all_targets


def dedupe_targets(
    targets: list[Target],
    priority: list[str],
) -> tuple[list[Target], list[dict[str, str]]]:
    """Deduplicate by channel_id; higher-priority group wins.

    Returns (deduped targets, membership log of dropped duplicates).
    """
    rank = {g: i for i, g in enumerate(priority)}
    chosen: dict[str, Target] = {}
    memberships: list[dict[str, str]] = []

    for t in targets:
        prev = chosen.get(t.channel_id)
        if prev is None:
            chosen[t.channel_id] = t
            continue
        prev_rank = rank.get(prev.group, len(rank))
        curr_rank = rank.get(t.group, len(rank))
        if curr_rank < prev_rank:
            # current target has higher priority
            memberships.append({
                "channel_id": t.channel_id,
                "name": t.name,
                "dropped_group": prev.group,
                "kept_group": t.group,
                "reason": "duplicate_priority",
            })
            chosen[t.channel_id] = t
        else:
            memberships.append({
                "channel_id": t.channel_id,
                "name": t.name,
                "dropped_group": t.group,
                "kept_group": prev.group,
                "reason": "duplicate_priority",
            })

    return list(chosen.values()), memberships
