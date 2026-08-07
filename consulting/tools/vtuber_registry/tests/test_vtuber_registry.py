from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from consulting.tools.vtuber_registry.audit import run_audit
from consulting.tools.vtuber_registry.bootstrap import run_bootstrap
from consulting.tools.vtuber_registry.enrich_organizations import _substring_candidates
from consulting.tools.vtuber_registry.ids import stable_id
from consulting.tools.vtuber_registry.validate import load_schema, validate_ndjson, validate_record


class RegistryContractTests(unittest.TestCase):
    def test_stable_id_is_deterministic_and_typed(self) -> None:
        first = stable_id("account", "chzzk", "abc")
        second = stable_id("account", "chzzk", "abc")
        persona = stable_id("persona", "chzzk", "abc")

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("krvt_a_"))
        self.assertTrue(persona.startswith("krvt_p_"))
        self.assertNotEqual(first.removeprefix("krvt_a_"), persona.removeprefix("krvt_p_"))

    def test_schema_rejects_unknown_properties(self) -> None:
        schema = load_schema()
        source_id = stable_id("source", "fixture", "2026-08-05")
        record = {
            "record_type": "source",
            "source_id": source_id,
            "uri": "file:///fixture",
            "source_tier": "P1",
            "publisher": "fixture",
            "observed_at": "2026-08-05",
            "supports": ["name"],
            "note": "fixture",
            "secret_values_stored": False,
            "unexpected": True,
        }

        errors = validate_record(record, schema=schema)
        self.assertTrue(any("additional property" in error for error in errors))

    def test_substring_candidates_ignore_blank_names_and_normalize(self) -> None:
        accounts = [
            {"account_id": "blank", "display_name": ""},
            {"account_id": "spacing", "display_name": "우사미 공식"},
            {"account_id": "other", "display_name": "다른사람"},
        ]

        matches = _substring_candidates(accounts, "우사미")

        self.assertEqual([item["account_id"] for item in matches], ["spacing"])


class BootstrapTests(unittest.TestCase):
    def _write_ndjson(self, path: Path, rows: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_multiplatform_bootstrap_preserves_platform_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpname:
            tmp = Path(tmpname)
            softcon = tmp / "softcon.ndjson"
            weekly = tmp / "weekly.ndjson"
            profiles = tmp / "profiles.ndjson"
            agencies = tmp / "agencies.yaml"
            output = tmp / "run"

            self._write_ndjson(
                softcon,
                [
                    {"rank": 1, "name": "가상A", "platform": "naverchzzk", "cid": "a" * 32, "hours": 10, "max": 20, "avg": 10, "vs": 100},
                    {"rank": 2, "name": "같은이름", "platform": "afreeca", "cid": "10", "hours": 5, "max": 9, "avg": 5, "vs": 25},
                    {"rank": 3, "name": "같은이름", "platform": "cime", "cid": "20", "hours": 4, "max": 8, "avg": 4, "vs": 16},
                ],
            )
            self._write_ndjson(
                weekly,
                [
                    {
                        "channel_id": "a" * 32,
                        "channel_name": "가상A",
                        "weeks": [{"date": "2026-07-06", "avgLiveViews": 10, "maxLiveViews": 20, "airTime": 4, "maxFollowerCount": 100, "sumCount": 40, "avgChatCount": 3, "viewership": 40}],
                    },
                    {
                        "channel_id": "b" * 32,
                        "channel_name": "신규B",
                        "weeks": [{"date": "2026-07-06", "avgLiveViews": 3, "maxLiveViews": 7, "airTime": 2, "maxFollowerCount": 30, "sumCount": 20, "avgChatCount": 1, "viewership": 6}],
                    },
                ],
            )
            self._write_ndjson(
                profiles,
                [
                    {"channel_id": "a" * 32, "channel_name": "가상A 공식", "follower_count": 100, "vtuber": {"value": True}, "activity": {"open_live_seen": False}},
                    {"channel_id": "b" * 32, "channel_name": "신규B", "follower_count": 30, "vtuber": {"value": True}, "activity": {"open_live_seen": True}},
                ],
            )
            agencies.write_text(
                "agency_terms:\n  - 테스트기획\nemail_domains:\n  - test.example\n",
                encoding="utf-8",
            )

            args = argparse.Namespace(
                softcon=str(softcon),
                weekly=str(weekly),
                profiles=str(profiles),
                agencies=str(agencies),
                schema=None,
                output=str(output),
            )
            summary = run_bootstrap(args)

            self.assertEqual(summary["platform_counts"], {"chzzk": 2, "cime": 1, "soop": 1})
            self.assertEqual(summary["output_counts"]["accounts"], 4)
            self.assertEqual(summary["join_counts"]["weekly_direct_platform_matches"], 1)
            self.assertEqual(summary["join_counts"]["weekly_chzzk_id_shape_inferences"], 1)
            self.assertEqual(summary["validation"]["error_count"], 0)

            accounts = [
                json.loads(line)
                for line in (output / "20_normalized" / "accounts.ndjson").read_text(encoding="utf-8").splitlines()
            ]
            natural_keys = {(row["platform"], row["platform_account_id"]) for row in accounts}
            self.assertEqual(len(natural_keys), 4)
            self.assertIn(("soop", "10"), natural_keys)
            self.assertIn(("cime", "20"), natural_keys)

            reviews = [
                json.loads(line)
                for line in (output / "40_review" / "review_queue.ndjson").read_text(encoding="utf-8").splitlines()
            ]
            issues = {row["issue_code"] for row in reviews}
            self.assertIn("cross_platform_same_name_no_auto_merge", issues)
            self.assertIn("platform_inferred_from_chzzk_id_shape", issues)

            count, errors = validate_ndjson(
                output / "20_normalized" / "accounts.ndjson",
                expected_record_type="account",
            )
            self.assertEqual(count, 4)
            self.assertEqual(errors, [])

            audit = run_audit(output)
            self.assertEqual(audit["status"], "pass")
            self.assertTrue(all(value == 0 for value in audit["problems"].values()))


if __name__ == "__main__":
    unittest.main()
