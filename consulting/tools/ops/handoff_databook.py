# -*- coding: utf-8 -*-
"""Shared helpers for per-session handoff databook files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SURFACES = ("CC", "Codex", "Cowork")
NEXT_SURFACES = ("CC", "Codex", "Cowork", "operator")
STATUSES = ("raw", "reviewed", "commit-candidate", "hold", "excluded")
REQUIRED_FIELDS = (
    "surface",
    "timestamp",
    "task",
    "status",
    "next_surface",
    "files",
    "decision_ids",
    "links",
)
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{4})-(CC|Codex|Cowork)(?:-\d{2})?\.md$")
DECISION_ID_RE = re.compile(r"^DL_[A-Z]+_\d{8}_\d{3}$")


@dataclass(frozen=True)
class Handoff:
    path: Path
    frontmatter: dict[str, object]
    body: str

    @property
    def surface(self) -> str:
        return str(self.frontmatter.get("surface", ""))

    @property
    def timestamp(self) -> str:
        return str(self.frontmatter.get("timestamp", ""))

    @property
    def task(self) -> str:
        return str(self.frontmatter.get("task", ""))

    @property
    def status(self) -> str:
        return str(self.frontmatter.get("status", ""))

    @property
    def next_surface(self) -> str:
        return str(self.frontmatter.get("next_surface", ""))


class HandoffParseError(ValueError):
    pass


def handoff_files(ctx_dir: Path) -> list[Path]:
    handoffs_dir = ctx_dir / "handoffs"
    if not handoffs_dir.exists():
        return []
    return sorted(
        path
        for path in handoffs_dir.glob("*.md")
        if path.name not in {"INDEX.md", "README.md"}
    )


def load_handoffs(ctx_dir: Path) -> list[Handoff]:
    return [parse_handoff(path) for path in handoff_files(ctx_dir)]


def parse_handoff(path: Path) -> Handoff:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise HandoffParseError("missing opening frontmatter delimiter")

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise HandoffParseError("missing closing frontmatter delimiter")

    frontmatter = parse_frontmatter(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).strip()
    return Handoff(path=path, frontmatter=frontmatter, body=body)


def parse_frontmatter(lines: Iterable[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise HandoffParseError(f"invalid frontmatter line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise HandoffParseError(f"empty frontmatter key: {raw_line}")
        data[key] = parse_value(value.strip())
    return data


def parse_value(value: str) -> object:
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item.strip()) for item in inner.split(",") if item.strip()]
    return _strip_quotes(value)


def validate_handoff(handoff: Handoff) -> list[str]:
    errors: list[str] = []
    frontmatter = handoff.frontmatter

    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"missing required field '{field}'")

    surface = str(frontmatter.get("surface", ""))
    if surface and surface not in SURFACES:
        errors.append(f"invalid surface '{surface}'")

    timestamp = str(frontmatter.get("timestamp", ""))
    if timestamp and not TIMESTAMP_RE.match(timestamp):
        errors.append(f"invalid timestamp '{timestamp}'")

    filename_match = FILENAME_RE.match(handoff.path.name)
    if not filename_match:
        errors.append("filename must be YYYY-MM-DDTHHMM-<Surface>.md")
    elif timestamp and TIMESTAMP_RE.match(timestamp):
        expected_stamp = timestamp.replace(":", "")
        if filename_match.group(1) != expected_stamp:
            errors.append("filename timestamp does not match frontmatter timestamp")
        if surface and filename_match.group(2) != surface:
            errors.append("filename surface does not match frontmatter surface")

    status = str(frontmatter.get("status", ""))
    if status and status not in STATUSES:
        errors.append(f"invalid status '{status}'")

    next_surface = str(frontmatter.get("next_surface", ""))
    if next_surface and next_surface not in NEXT_SURFACES:
        errors.append(f"invalid next_surface '{next_surface}'")

    for field in ("files", "decision_ids", "links"):
        value = frontmatter.get(field)
        if field in frontmatter and not isinstance(value, list):
            errors.append(f"field '{field}' must be a one-line array")

    for decision_id in _as_list(frontmatter.get("decision_ids")):
        if decision_id and not DECISION_ID_RE.match(str(decision_id)):
            errors.append(f"invalid decision_id '{decision_id}'")

    if not handoff.body:
        errors.append("handoff body is empty")

    return errors


def sort_handoffs(handoffs: Iterable[Handoff]) -> list[Handoff]:
    return sorted(handoffs, key=lambda item: (item.timestamp, item.path.name), reverse=True)


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
