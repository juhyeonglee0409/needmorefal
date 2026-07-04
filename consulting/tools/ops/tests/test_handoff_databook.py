from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from consulting.tools.ops.handoff_databook import parse_handoff, validate_handoff
from consulting.tools.ops.status_board import render_index


HANDOFF_TEXT = """---
surface: Codex
timestamp: 2026-07-04T17:42
task: Handoff databook test
status: reviewed
next_surface: operator
files: [consulting/_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md]
decision_ids: [DL_CONTEXT_20260704_050]
links: [proposal_handoff_databook_20260704]
---

1. What was done
Test body.
"""


class HandoffDatabookTests(unittest.TestCase):
    def test_valid_handoff_frontmatter_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-07-04T1742-Codex.md"
            path.write_text(HANDOFF_TEXT, encoding="utf-8")

            handoff = parse_handoff(path)

            self.assertEqual(validate_handoff(handoff), [])
            self.assertEqual(handoff.surface, "Codex")
            self.assertEqual(handoff.frontmatter["files"], [
                "consulting/_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md"
            ])

    def test_invalid_filename_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.md"
            path.write_text(HANDOFF_TEXT, encoding="utf-8")

            errors = validate_handoff(parse_handoff(path))

            self.assertIn("filename must be YYYY-MM-DDTHHMM-<Surface>.md", errors)

    def test_render_index_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-07-04T1742-Codex.md"
            path.write_text(HANDOFF_TEXT, encoding="utf-8")
            handoff = parse_handoff(path)

            rendered_once = render_index([handoff])
            rendered_twice = render_index([handoff])

            self.assertEqual(rendered_once, rendered_twice)
            self.assertIn("| 2026-07-04T17:42 | Codex | reviewed | operator |", rendered_once)


if __name__ == "__main__":
    unittest.main()
