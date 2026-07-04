from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.outreach.chzzk import extract_items, merge_candidate_detail, normalize_live_item
from tools.outreach.classify import AgencyRules, build_channel_record, follower_segment
from tools.outreach.email_extract import extract_public_email
from tools.outreach.llm import StubBoundaryClassifier
from tools.outreach.pool import ChannelPool


class OutreachTests(unittest.TestCase):
    def test_extract_public_email_only_when_present(self) -> None:
        self.assertEqual(
            extract_public_email("문의: test.channel+biz@example.co.kr 입니다"),
            "test.channel+biz@example.co.kr",
        )
        self.assertIsNone(extract_public_email("문의는 디엠으로 주세요"))

    def test_build_channel_record_classifies_qualified_solo_vtuber(self) -> None:
        record = build_channel_record(
            {
                "channel_id": "cid-1",
                "channel_name": "신입 버튜버",
                "follower_count": 321,
                "description": "버츄얼 종합게임 방송 business@example.com",
                "open_live": True,
            },
            agency_rules=AgencyRules(
                agency_terms=("스텔라이브",),
                email_domains=("pixelnetwork.co.kr",),
            ),
            seen_at="2026-07-04T00:00:00+0900",
        )

        self.assertEqual(record["segment"], "growth")
        self.assertEqual(
            record["vtuber"],
            {"value": True, "method": "heuristic", "confidence": "high"},
        )
        self.assertEqual(record["solo"], {"value": True, "matched_agency": None})
        self.assertEqual(record["email"]["value"], "business@example.com")
        self.assertEqual(record["outreach"]["status"], "qualified")

    def test_build_channel_record_excludes_agency_domain(self) -> None:
        record = build_channel_record(
            {
                "channel_id": "cid-2",
                "channel_name": "버튜버 채널",
                "follower_count": 900,
                "description": "contact@pixelnetwork.co.kr",
            },
            agency_rules=AgencyRules(email_domains=("pixelnetwork.co.kr",)),
        )

        self.assertEqual(
            record["solo"],
            {"value": False, "matched_agency": "pixelnetwork.co.kr"},
        )
        self.assertEqual(record["outreach"]["status"], "excluded")

    def test_follower_segment_boundaries(self) -> None:
        self.assertEqual(follower_segment(None), "unknown")
        self.assertEqual(follower_segment(149), "rookie")
        self.assertEqual(follower_segment(150), "growth")
        self.assertEqual(follower_segment(10000), "growth")
        self.assertEqual(follower_segment(10001), "large")

    def test_pool_preserves_any_opted_out_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pool = ChannelPool(Path(tmp) / "pool.ndjson")
            pool.append({"channel_id": "cid-1", "outreach": {"status": "candidate"}})
            pool.append({"channel_id": "cid-1", "outreach": {"status": "opted_out"}})
            pool.append({"channel_id": "cid-1", "outreach": {"status": "candidate"}})
            pool.append({"channel_id": "cid-2", "outreach": {"status": "qualified"}})

            self.assertEqual(pool.opted_out_ids(), {"cid-1"})

    def test_chzzk_extract_and_normalize_live_shape(self) -> None:
        payload = {
            "content": {
                "data": [
                    {
                        "liveTitle": "초보 버츄얼 방송",
                        "tags": ["버추얼", "게임"],
                        "concurrentUserCount": 12,
                        "liveCategoryValue": "talk",
                        "channel": {
                            "channelId": "cid-live",
                            "channelName": "라이브채널",
                        },
                    }
                ]
            }
        }

        items = extract_items(payload)
        normalized = normalize_live_item(items[0], matched_keyword="버츄얼")

        self.assertEqual(normalized["channel_id"], "cid-live")
        self.assertEqual(normalized["channel_name"], "라이브채널")
        self.assertIs(normalized["vtuber_signal"], True)
        self.assertEqual(normalized["matched_keyword"], "버츄얼")

    def test_merge_candidate_detail_preserves_live_signal(self) -> None:
        merged = merge_candidate_detail(
            {"channel_id": "cid", "open_live": True, "vtuber_signal": True},
            {"channel_id": "cid", "description": "bio", "open_live": False},
        )

        self.assertIs(merged["open_live"], True)
        self.assertIs(merged["vtuber_signal"], True)
        self.assertEqual(merged["description"], "bio")

    def test_canonical_record_is_json_serializable(self) -> None:
        record = build_channel_record(
            {
                "channel_id": "cid-3",
                "channel_name": "버미육 테스트",
                "description": "",
                "follower_count": 12,
            }
        )

        json.dumps(record, ensure_ascii=False)

    def test_live_artifact_sets_open_live_activity(self) -> None:
        record = build_channel_record(
            {
                "channel_id": "cid-4",
                "channel_name": "라이브 버튜버",
                "live_title": "버츄얼 방송",
                "concurrent_viewers": 7,
            }
        )

        self.assertIs(record["activity"]["open_live_seen"], True)

    def test_llm_classifier_is_stub_only(self) -> None:
        with self.assertRaises(NotImplementedError):
            StubBoundaryClassifier().classify({})


class EnrichCensusTests(unittest.TestCase):
    """Offline fixture tests for the census cross-ref subcommand (no network)."""

    def _args(self, tmp: Path, **overrides):
        import argparse

        defaults = dict(
            input=str(tmp / "census.ndjson"),
            pool=str(tmp / "pool.ndjson"),
            progress=str(tmp / "progress.ndjson"),
            agencies=None,
            limit=None,
            skip_existing=False,
            delay_seconds=0.0,
            timeout_seconds=15.0,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _write_census(self, path: Path) -> None:
        rows = [
            {"channel_id": "solo1", "channel_name": "꽃분홍",
             "softcon": {"avg": 46, "vs": 1485, "max": 89, "hours": 31.7, "rank": 320}},
            {"channel_id": "agency1", "channel_name": "니니아",
             "softcon": {"avg": 387, "vs": 16507, "max": 1506, "hours": 42.6, "rank": 99}},
        ]
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    def _patch_client(self, details: dict):
        from tools.outreach import pipeline as pl

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            def channel_detail(self, cid):
                return details[cid]

        original = pl.ChzzkClient
        pl.ChzzkClient = FakeClient
        return original

    def test_enrich_joins_softcon_and_classifies(self) -> None:
        from tools.outreach import pipeline as pl

        with tempfile.TemporaryDirectory() as tmpname:
            tmp = Path(tmpname)
            self._write_census(tmp / "census.ndjson")
            details = {
                "solo1": {"channel_id": "solo1", "channel_name": "꽃분홍",
                          "follower_count": 1169, "description": "문의 blossiiiv@gmail.com 버튜버"},
                "agency1": {"channel_id": "agency1", "channel_name": "니니아",
                            "follower_count": 41621, "description": "business niniaovo@enchantenter.co.kr"},
            }
            original = self._patch_client(details)
            try:
                rc = pl.run_enrich_census(self._args(tmp))
            finally:
                pl.ChzzkClient = original

            self.assertEqual(rc, 0)
            records = {r["channel_id"]: r for r in ChannelPool(tmp / "pool.ndjson").iter_records()}
            # solo channel with public email → qualified, softcon metrics joined
            self.assertEqual(records["solo1"]["outreach"]["status"], "qualified")
            self.assertEqual(records["solo1"]["segment"], "growth")
            self.assertEqual(records["solo1"]["metrics"]["softcon"]["rank"], 320)
            self.assertEqual(records["solo1"]["metrics"]["avg_viewers_30d"], 46)
            self.assertEqual(records["solo1"]["email"]["value"], "blossiiiv@gmail.com")
            # agency-domain email → excluded from solo pool
            self.assertEqual(records["agency1"]["outreach"]["status"], "excluded")
            self.assertIsNotNone(records["agency1"]["solo"]["matched_agency"])

    def test_skip_existing_and_opted_out(self) -> None:
        from tools.outreach import pipeline as pl

        with tempfile.TemporaryDirectory() as tmpname:
            tmp = Path(tmpname)
            self._write_census(tmp / "census.ndjson")
            pool = ChannelPool(tmp / "pool.ndjson")
            # solo1 already enriched; agency1 opted out earlier
            pool.append({"channel_id": "solo1", "follower_count": 1169, "outreach": {"status": "qualified"}})
            pool.append({"channel_id": "agency1", "outreach": {"status": "opted_out"}})
            details = {"solo1": {"channel_id": "solo1", "follower_count": 1169, "description": "x"},
                       "agency1": {"channel_id": "agency1", "follower_count": 1, "description": "x"}}
            original = self._patch_client(details)
            try:
                rc = pl.run_enrich_census(self._args(tmp, skip_existing=True))
            finally:
                pl.ChzzkClient = original

            self.assertEqual(rc, 0)
            # neither re-enriched: solo1 skipped (existing), agency1 skipped (opted_out永久)
            new_rows = [r for r in ChannelPool(tmp / "pool.ndjson").iter_records()
                        if r["channel_id"] == "agency1" and r.get("follower_count") == 1]
            self.assertEqual(new_rows, [])

    def test_limit_batches(self) -> None:
        from tools.outreach import pipeline as pl

        with tempfile.TemporaryDirectory() as tmpname:
            tmp = Path(tmpname)
            self._write_census(tmp / "census.ndjson")
            details = {
                "solo1": {"channel_id": "solo1", "follower_count": 1169, "description": "버튜버 a@b.com"},
                "agency1": {"channel_id": "agency1", "follower_count": 41621, "description": "버튜버 c@d.com"},
            }
            original = self._patch_client(details)
            try:
                rc = pl.run_enrich_census(self._args(tmp, limit=1))
            finally:
                pl.ChzzkClient = original

            self.assertEqual(rc, 0)
            records = list(ChannelPool(tmp / "pool.ndjson").iter_records())
            self.assertEqual(len(records), 1)


if __name__ == "__main__":
    unittest.main()
