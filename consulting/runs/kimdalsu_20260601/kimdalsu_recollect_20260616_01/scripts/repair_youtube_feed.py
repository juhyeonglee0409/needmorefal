from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


RUN_ID = "kimdalsu_recollect_20260616_01"
CASE_ID = "kimdalsu_20260601"
STREAMER_KEY = "kimdalsu"
CHANNEL_ID = "UCvkwM7BIrqqEq7I_9UiCY6w"
TARGET_ID = "youtube_dalsooisfree_content_funnel"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
KST = timezone(timedelta(hours=9))
RUN_DATE = datetime(2026, 6, 16, tzinfo=KST)
WINDOW_START = RUN_DATE - timedelta(days=180)


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fetch(url: str) -> dict:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        "Accept": "application/atom+xml,application/xml,text/xml",
    })
    with urlopen(req, timeout=35) as resp:
        body = resp.read()
        text = body.decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
        return {"status": resp.status, "final_url": resp.geturl(), "text": text, "bytes": len(body), "hash": digest_text(text)}


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone(KST)
    except ValueError:
        return None


def duration_from_media_group(entry: ET.Element, ns: dict) -> int | None:
    # YouTube RSS usually omits duration. Keep this hook for future-compatible feeds.
    duration = entry.find(".//media:content", ns)
    if duration is not None and duration.get("duration"):
        try:
            return int(duration.get("duration") or "0")
        except ValueError:
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root)

    response = fetch(FEED_URL)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    root = ET.fromstring(response["text"])
    rows: list[dict] = []
    metadata_counts = {"seen": 0, "included_180d": 0, "outside_180d": 0, "date_unknown": 0}
    for entry in root.findall("atom:entry", ns):
        metadata_counts["seen"] += 1
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        title = entry.findtext("atom:title", default="", namespaces=ns)
        link_el = entry.find("atom:link", ns)
        published = parse_dt(entry.findtext("atom:published", default="", namespaces=ns))
        updated = parse_dt(entry.findtext("atom:updated", default="", namespaces=ns))
        if not published:
            metadata_counts["date_unknown"] += 1
            continue
        if published < WINDOW_START:
            metadata_counts["outside_180d"] += 1
            continue
        metadata_counts["included_180d"] += 1
        content_type = "short" if re.search(r"#?shorts?", title, re.IGNORECASE) else "video"
        rows.append({
            "run_id": RUN_ID,
            "case_id": CASE_ID,
            "streamer_key": STREAMER_KEY,
            "platform": "youtube",
            "content_id": video_id,
            "content_url": link_el.get("href") if link_el is not None else f"https://www.youtube.com/watch?v={video_id}",
            "posted_at": published.isoformat(),
            "content_type": content_type,
            "content_topic": None,
            "duration_sec": duration_from_media_group(entry, ns),
            "title": title,
            "identity_fit": None,
            "views": None,
            "likes": None,
            "comments": None,
            "shares": None,
            "cta_present": None,
            "main_link_present": None,
            "conversion_signal": None,
            "follower_delta_1d": None,
            "follower_delta_3d": None,
            "follower_delta_7d": None,
            "recommendation": "needs_human_review",
            "evidence_refs": f"40_arthur_collect/{TARGET_ID}/combined.json",
            "disclosure_tag": "green",
            "is_short": content_type == "short",
            "tags": None,
            "description_link_to_chzzk": None,
            "upload_sequence": metadata_counts["seen"],
            "thumbnail_text": None,
            "view_count_text_raw": None,
            "like_count_text_raw": None,
            "parse_status": "partial",
            "missing_reason": "rss_feed_metadata_only_no_engagement_counts",
            "boundary_signal": None,
            "response_hash": response["hash"],
            "updated_at": updated.isoformat() if updated else None,
        })

    boundary = None if rows else "rss_no_in_range_entries"
    out_dir = run_root / "40_arthur_collect" / TARGET_ID
    write_json(run_root / "10_charles" / f"{TARGET_ID}.scout_report.json", {
        "url": FEED_URL,
        "target_id": TARGET_ID,
        "generated_at": now_iso(),
        "tool": "codex_public_youtube_rss_summary",
        "save_raw": False,
        "secret_values_logged": False,
        "status_code": response["status"],
        "final_url": response["final_url"],
        "response_hash": response["hash"],
        "response_bytes": response["bytes"],
        "boundary_signal": boundary,
    })
    write_json(run_root / "10_charles" / f"{TARGET_ID}.protocol.json", {
        "target_id": TARGET_ID,
        "target_url": FEED_URL,
        "best_path": "public_rss_parse" if not boundary else "manual_review",
        "pre_check": {"gate_status": "public_cleared" if not boundary else "restricted", "boundary_signal": boundary, "profile_required": False},
        "collection_plan": {"source": "youtube_atom_feed", "window_start": WINDOW_START.date().isoformat(), "window_end": RUN_DATE.date().isoformat()} if not boundary else None,
        "verification": {"preserve_not_verifiable": True},
    })
    write_json(run_root / "30_arthur_inspect" / f"{TARGET_ID}.InspectResult.json", {
        "version": "operator-orchestrated-public-inspect-v1",
        "generated_at": now_iso(),
        "target_id": TARGET_ID,
        "target_url": FEED_URL,
        "boundary_signals": [] if not boundary else [{"source": "rss", "signal": boundary, "severity": "stop", "action": "stopped"}],
        "sample_records": rows[:5],
        "row_count_observed": len(rows),
        "inspect_recommendation": "collect_allowed" if rows else "review_required",
    })
    write_json(out_dir / "_meta.json", {
        "run_id": RUN_ID,
        "target_id": TARGET_ID,
        "collection_method": "youtube_atom_feed",
        "source_url": FEED_URL,
        "collected_at": now_iso(),
        "items_collected": len(rows),
        "boundary_signals": [] if not boundary else [boundary],
        "collection_window_start": WINDOW_START.date().isoformat(),
        "collection_window_end": RUN_DATE.date().isoformat(),
        "secret_values_logged": False,
        "raw_html_saved": False,
        "screenshot_saved": False,
    })
    write_json(out_dir / "combined.json", {
        "run_id": RUN_ID,
        "target_id": TARGET_ID,
        "source_url": FEED_URL,
        "response": {"status_code": response["status"], "final_url": response["final_url"], "response_hash": response["hash"], "response_bytes": response["bytes"]},
        "collection_window": {"start": WINDOW_START.date().isoformat(), "end": RUN_DATE.date().isoformat(), "basis": "run_date_minus_180_days"},
        "metadata_counts": metadata_counts,
        "items": rows,
        "verification": {"parse_status": "ok" if rows else "empty", "boundary_signal": boundary, "dedup_key": "content_id"},
    })
    write_jsonl(out_dir / "items.jsonl", rows)
    if rows:
        fields = sorted({k for row in rows for k in row.keys()})
        write_csv(out_dir / "normalized.csv", rows, fields)
        write_csv(run_root / "50_ingest_candidates" / "ContentFunnelAnalysis_candidate.csv", rows, fields)
    print(json.dumps({"target_id": TARGET_ID, "rows": len(rows), "boundary": boundary, "metadata_counts": metadata_counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
