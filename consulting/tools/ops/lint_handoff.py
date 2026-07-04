# -*- coding: utf-8 -*-
"""Handoff/decision-log format linter.

Checks handoff databook files, legacy SESSION_NOTE.md handoff headers, and
07_DECISION_LOG.md decision ids against 12_CONTINUITY_CONTRACT.md. Errors
exit 1 (CI-gating); warnings exit 0.

Usage: python -m consulting.tools.ops.lint_handoff [WORKING_CONTEXT_DIR]
"""
import re
import sys
from pathlib import Path

from .handoff_databook import (
    HandoffParseError,
    SURFACES,
    handoff_files,
    parse_handoff,
    validate_handoff,
)

SCOPES = ("TOOLING", "CONTEXT", "INFRA", "POLICY")

HANDOFF_RE = re.compile(r"^##\s*\[([^\]]+)\]\s*(\S+)")           # ## [Surface] <date>...
DECISION_RE = re.compile(r"DL_([A-Z]+)_(\d{8})_(\d+)")
HAS_TIME = re.compile(r"T\d{2}:\d{2}")


def lint(ctx_dir: Path):
    errors, warnings = [], []

    handoffs_dir = ctx_dir / "handoffs"
    if handoffs_dir.exists():
        for path in handoff_files(ctx_dir):
            try:
                handoff = parse_handoff(path)
            except HandoffParseError as exc:
                errors.append(f"{path.relative_to(ctx_dir)}: {exc}")
                continue
            for error in validate_handoff(handoff):
                errors.append(f"{path.relative_to(ctx_dir)}: {error}")
    else:
        warnings.append("handoffs/ not found; legacy SESSION_NOTE.md remains the only handoff source")

    note = ctx_dir / "SESSION_NOTE.md"
    if note.exists():
        for i, line in enumerate(note.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("## ["):
                continue
            m = HANDOFF_RE.match(line)
            if not m:
                errors.append(f"SESSION_NOTE:{i}: malformed handoff header: {line.strip()}")
                continue
            surface, datestr = m.group(1), m.group(2)
            if not any(surface == s or surface.startswith(s + "/") for s in SURFACES):
                errors.append(f"SESSION_NOTE:{i}: unknown surface tag [{surface}] (expected {SURFACES})")
            if not re.match(r"\d{4}-\d{2}-\d{2}", datestr):
                errors.append(f"SESSION_NOTE:{i}: unparseable date '{datestr}'")
            elif not HAS_TIME.search(line):
                warnings.append(f"SESSION_NOTE:{i}: timestamp lacks minute precision (contract wants YYYY-MM-DDTHH:MM)")
    else:
        warnings.append("SESSION_NOTE.md not found")

    log = ctx_dir / "07_DECISION_LOG.md"
    if log.exists():
        seen = {}
        for m in DECISION_RE.finditer(log.read_text(encoding="utf-8")):
            scope, date, num = m.group(1), m.group(2), int(m.group(3))
            if scope not in SCOPES:
                errors.append(f"DECISION_LOG: unknown scope prefix DL_{scope}_ (expected {SCOPES})")
            if num in seen and seen[num] != m.group(0):
                errors.append(f"DECISION_LOG: duplicate id number {num:03d}: {seen[num]} vs {m.group(0)}")
            seen[num] = m.group(0)
    else:
        warnings.append("07_DECISION_LOG.md not found")

    return errors, warnings


def main():
    ctx = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parents[2] / "_WORKING_CONTEXT"
    errors, warnings = lint(ctx)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) in {ctx}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
