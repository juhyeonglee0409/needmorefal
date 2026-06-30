from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote
from urllib.request import Request, urlopen


RUN_ID = "kimdalsu_recollect_20260616_01"
CASE_ID = "kimdalsu_20260601"
STREAMER_KEY = "kimdalsu"
SUBJECT_ID = "dcbccbf2d8e2a1b095244c5856d3613a"
KST = timezone(timedelta(hours=9))
RUN_DATE = datetime(2026, 6, 16, tzinfo=KST)
YOUTUBE_START = RUN_DATE - timedelta(days=180)


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


def get_url(url: str, timeout: int = 35) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            text = body.decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
            return {
                "ok": True,
                "status": resp.status,
                "url": resp.geturl(),
                "text": text,
                "hash": digest_text(text),
                "bytes": len(body),
            }
    except HTTPError as exc:
        body = exc.read()
        text = body.decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "url": url, "text": text, "hash": digest_text(text), "bytes": len(body), "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "status": None, "url": url, "text": "", "hash": None, "bytes": 0, "error": str(exc)}


def scaffold(run_root: Path, target_id: str, url: str, response: dict, boundary: str | None, rows: list[dict], profile_required: bool = False) -> None:
    out_dir = run_root / "40_arthur_collect" / target_id
    out_dir.mkdir(parents=True, exist_ok=True)
    scout = {
        "url": url,
        "target_id": target_id,
        "generated_at": now_iso(),
        "tool": "codex_public_http_summary",
        "save_raw": False,
        "secret_values_logged": False,
        "status_code": response.get("status"),
        "final_url": response.get("url"),
        "response_hash": response.get("hash"),
        "response_bytes": response.get("bytes"),
        "boundary_signal": boundary,
    }
    protocol = {
        "target_id": target_id,
        "target_url": url,
        "best_path": "public_http_parse" if not boundary else "manual_review",
        "pre_check": {
            "gate_status": "public_cleared" if not boundary else "restricted",
            "boundary_signal": boundary,
            "profile_required": profile_required,
        },
        "collection_plan": {"source": "public_http_parse", "max_pages": 1} if not boundary else None,
        "verification": {"preserve_not_verifiable": True},
    }
    inspect = {
        "version": "operator-orchestrated-public-inspect-v1",
        "generated_at": now_iso(),
        "target_id": target_id,
        "target_url": url,
        "boundary_signals": [] if not boundary else [{"source": "http", "signal": boundary, "severity": "stop", "action": "stopped"}],
        "sample_records": rows[:5],
        "row_count_observed": len(rows),
        "inspect_recommendation": "collect_allowed" if not boundary else "do_not_collect",
    }
    meta = {
        "run_id": RUN_ID,
        "target_id": target_id,
        "collection_method": "public_http_parse",
        "source_url": url,
        "collected_at": now_iso(),
        "items_collected": len(rows),
        "boundary_signals": [] if not boundary else [boundary],
        "secret_values_logged": False,
        "raw_html_saved": False,
        "screenshot_saved": False,
    }
    combined = {
        "run_id": RUN_ID,
        "target_id": target_id,
        "source_url": url,
        "response": {
            "status_code": response.get("status"),
            "final_url": response.get("url"),
            "response_hash": response.get("hash"),
            "response_bytes": response.get("bytes"),
        },
        "items": rows,
        "verification": {
            "parse_status": "ok" if rows and not boundary else ("blocked" if boundary else "empty"),
            "boundary_signal": boundary,
        },
    }
    write_json(run_root / "10_charles" / f"{target_id}.scout_report.json", scout)
    write_json(run_root / "10_charles" / f"{target_id}.protocol.json", protocol)
    write_json(run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json", inspect)
    write_json(out_dir / "_meta.json", meta)
    write_json(out_dir / "combined.json", combined)
    write_jsonl(out_dir / "items.jsonl", rows)


def collect_chzzk(run_root: Path) -> dict:
    target_id = "chzzk_subject_channel_public_profile"
    candidates = [
        f"https://api.chzzk.naver.com/service/v1/channels/{SUBJECT_ID}",
        f"https://chzzk.naver.com/api/channels/{SUBJECT_ID}",
    ]
    last_response = None
    for url in candidates:
        response = get_url(url)
        last_response = response
        if response["ok"] and response["text"].lstrip().startswith("{"):
            data = json.loads(response["text"])
            content = data.get("content") or data
            row = {
                "run_id": RUN_ID,
                "case_id": CASE_ID,
                "streamer_key": STREAMER_KEY,
                "platform": "chzzk",
                "platform_channel_id": SUBJECT_ID,
                "channel_name": content.get("channelName") or content.get("name"),
                "channel_url": f"https://chzzk.naver.com/{SUBJECT_ID}",
                "profile_text": content.get("channelDescription") or content.get("description"),
                "follower_count": content.get("followerCount"),
                "recent_live_or_vod_titles": None,
                "recent_categories": content.get("openLive", {}).get("liveCategoryValue") if isinstance(content.get("openLive"), dict) else None,
                "collected_at": now_iso(),
                "raw_record_path": f"40_arthur_collect/{target_id}/combined.json",
                "disclosure_tag": "green",
                "thumbnail_present": bool(content.get("channelImageUrl") or content.get("profileImageUrl")),
                "parse_status": "ok",
                "missing_reason": None,
                "boundary_signal": None,
                "response_hash": response["hash"],
            }
            scaffold(run_root, target_id, url, response, None, [row])
            return {"target_id": target_id, "rows": 1, "boundary": None}
    boundary = "http_403_or_api_unavailable" if last_response and last_response.get("status") in (401, 403) else "public_api_not_parseable"
    scaffold(run_root, target_id, candidates[0], last_response or {}, boundary, [])
    return {"target_id": target_id, "rows": 0, "boundary": boundary}


def strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def collect_semorank(run_root: Path) -> dict:
    target_id = "semorank_chzzk_follower_public_crosscheck"
    url = "https://www.semorank.kr/ranking/chzzk"
    response = get_url(url)
    rows: list[dict] = []
    boundary = None
    if not response["ok"]:
        boundary = f"http_{response.get('status')}" if response.get("status") else "network_error"
    else:
        text = response["text"]
        plain = re.sub(r"\s+", " ", strip_tags(text))
        # Keep this intentionally conservative: parse only obvious CHZZK channel links and adjacent public text.
        for m in re.finditer(r"https?://(?:chzzk\.naver\.com|m\.chzzk\.naver\.com)/([a-f0-9]{20,})", text):
            channel_id = m.group(1)
            start = max(0, m.start() - 300)
            end = min(len(plain), m.end() + 300)
            snippet = plain[start:end]
            if any(r.get("channel_url", "").endswith(channel_id) for r in rows):
                continue
            rows.append({
                "run_id": RUN_ID,
                "source_name": "Semorank",
                "source_url": url,
                "platform": "chzzk",
                "channel_name": None,
                "channel_url": f"https://chzzk.naver.com/{channel_id}",
                "follower_count": None,
                "follower_rank": None,
                "rank_delta": None,
                "follower_delta": None,
                "mcn": None,
                "collected_at": now_iso(),
                "raw_record_path": f"40_arthur_collect/{target_id}/combined.json",
                "disclosure_tag": "green",
                "parse_status": "partial",
                "missing_reason": "only_channel_links_parseable_from_public_html",
                "boundary_signal": None,
                "response_hash": response["hash"],
                "text_sample": snippet[:300],
            })
        if not rows:
            boundary = "no_parseable_public_rows"
    scaffold(run_root, target_id, url, response, boundary, rows)
    if rows:
        write_csv(run_root / "40_arthur_collect" / target_id / "normalized.csv", rows, sorted({k for r in rows for k in r.keys()}))
    return {"target_id": target_id, "rows": len(rows), "boundary": boundary}


def find_json_object_after(text: str, marker: str) -> dict | None:
    idx = text.find(marker)
    if idx < 0:
        return None
    idx = text.find("{", idx)
    if idx < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for pos in range(idx, len(text)):
        ch = text[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[idx:pos + 1])
    return None


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def parse_relative_date(text: str | None) -> tuple[str | None, bool | None]:
    if not text:
        return None, None
    lower = text.lower()
    if "streamed" in lower:
        return None, False
    if any(token in lower for token in ["hour", "minute", "day", "시간", "분", "일 전", "어제"]):
        return RUN_DATE.date().isoformat(), True
    m = re.search(r"(\d+)\s*(week|weeks|주)", lower)
    if m:
        dt = RUN_DATE - timedelta(days=int(m.group(1)) * 7)
        return dt.date().isoformat(), dt >= YOUTUBE_START
    m = re.search(r"(\d+)\s*(month|months|개월|달)", lower)
    if m:
        dt = RUN_DATE - timedelta(days=int(m.group(1)) * 30)
        return dt.date().isoformat(), dt >= YOUTUBE_START
    m = re.search(r"(\d+)\s*(year|years|년)", lower)
    if m:
        dt = RUN_DATE - timedelta(days=int(m.group(1)) * 365)
        return dt.date().isoformat(), dt >= YOUTUBE_START
    return None, None


def collect_youtube(run_root: Path) -> dict:
    target_id = "youtube_dalsooisfree_content_funnel"
    url = "https://www.youtube.com/@dalsooisfree/videos"
    response = get_url(url)
    rows: list[dict] = []
    metadata_counts = {"seen": 0, "included_180d": 0, "outside_180d": 0, "date_unknown": 0}
    boundary = None
    if not response["ok"]:
        boundary = f"http_{response.get('status')}" if response.get("status") else "network_error"
    else:
        initial = find_json_object_after(response["text"], "var ytInitialData =") or find_json_object_after(response["text"], "ytInitialData")
        if initial:
            seen_ids = set()
            for node in walk(initial):
                video = node.get("videoRenderer") if "videoRenderer" in node else node if "videoId" in node and "title" in node else None
                if not isinstance(video, dict):
                    continue
                vid = video.get("videoId")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)
                title_runs = (((video.get("title") or {}).get("runs")) or [])
                title = title_runs[0].get("text") if title_runs else (video.get("title") or {}).get("simpleText")
                published_text = ((video.get("publishedTimeText") or {}).get("simpleText"))
                approx_date, in_range = parse_relative_date(published_text)
                metadata_counts["seen"] += 1
                if in_range is True:
                    metadata_counts["included_180d"] += 1
                elif in_range is False:
                    metadata_counts["outside_180d"] += 1
                    continue
                else:
                    metadata_counts["date_unknown"] += 1
                    continue
                view_text = ((video.get("viewCountText") or {}).get("simpleText")) or ((video.get("shortViewCountText") or {}).get("simpleText"))
                length_text = ((video.get("lengthText") or {}).get("simpleText"))
                row = {
                    "run_id": RUN_ID,
                    "case_id": CASE_ID,
                    "streamer_key": STREAMER_KEY,
                    "platform": "youtube",
                    "content_id": vid,
                    "content_url": f"https://www.youtube.com/watch?v={vid}",
                    "posted_at": approx_date,
                    "content_type": "video",
                    "content_topic": None,
                    "duration_sec": None,
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
                    "evidence_refs": f"40_arthur_collect/{target_id}/combined.json",
                    "disclosure_tag": "green",
                    "is_short": "/shorts/" in json.dumps(video, ensure_ascii=False),
                    "view_count_text_raw": view_text,
                    "like_count_text_raw": None,
                    "parse_status": "partial",
                    "missing_reason": "youtube_initial_page_only_no_continuation",
                    "boundary_signal": None,
                    "response_hash": response["hash"],
                    "published_text_raw": published_text,
                    "duration_text_raw": length_text,
                }
                rows.append(row)
        if not rows:
            boundary = "no_in_range_videos_parseable_from_initial_page"
    scaffold(run_root, target_id, url, response, boundary, rows)
    combined_path = run_root / "40_arthur_collect" / target_id / "combined.json"
    combined = json.loads(combined_path.read_text(encoding="utf-8"))
    combined["metadata_counts"] = metadata_counts
    combined["collection_window"] = {
        "basis": "run_date_minus_180_days",
        "start": YOUTUBE_START.date().isoformat(),
        "end": RUN_DATE.date().isoformat(),
    }
    write_json(combined_path, combined)
    if rows:
        write_csv(run_root / "40_arthur_collect" / target_id / "normalized.csv", rows, sorted({k for r in rows for k in r.keys()}))
        write_csv(run_root / "50_ingest_candidates" / "ContentFunnelAnalysis_candidate.csv", rows, sorted({k for r in rows for k in r.keys()}))
    return {"target_id": target_id, "rows": len(rows), "boundary": boundary, "metadata_counts": metadata_counts}


def collect_auro(run_root: Path) -> dict:
    target_id = "auro_live_chzzk_follower_public_crosscheck"
    url = "https://auro.live/rank/chzzk/0"
    response = get_url(url)
    rows: list[dict] = []
    boundary = None
    if not response["ok"]:
        boundary = f"http_{response.get('status')}" if response.get("status") else "network_error"
    else:
        boundary = "not_collected_route_requires_chrome_js_fetch_devalue_parser"
    scaffold(run_root, target_id, url, response, boundary, rows)
    return {"target_id": target_id, "rows": 0, "boundary": boundary}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root)
    results = [
        collect_chzzk(run_root),
        collect_semorank(run_root),
        collect_youtube(run_root),
        collect_auro(run_root),
    ]
    write_json(run_root / "40_arthur_collect" / "_public_targets_summary.json", {
        "generated_at": now_iso(),
        "results": results,
        "youtube_window": {
            "start": YOUTUBE_START.date().isoformat(),
            "end": RUN_DATE.date().isoformat(),
        },
    })
    print(json.dumps(results, ensure_ascii=False, indent=2))
    time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
