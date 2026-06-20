#!/usr/bin/env python3
"""Collect YouTube co-usage signals for the Gubiba upper-band cohort.

The script stores only normalized CSV rows and a compact run note. It does not
persist raw HTML, raw JSON, cookies, tokens, localStorage, screenshots, or auth
headers.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TODAY = dt.date(2026, 6, 19)
CASE_CHANNEL_ID = "269edc95873a1ec9fc534851c0783d1f"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

PRESENCE_FIELDS = [
    "channel_name",
    "channelId",
    "band",
    "has_youtube",
    "youtube_channel_id",
    "youtube_url",
    "match_method",
    "match_confidence",
]

METRIC_FIELDS = [
    "youtube_channel_id",
    "youtube_url",
    "channel_name",
    "source_channelId",
    "band",
    "subscriber_count",
    "video_count",
    "view_count",
    "last_upload_date",
    "upload_frequency_30d",
    "content_type_primary",
]

GUBIVA_FIELDS = [
    "channel_name",
    "channelId",
    "has_youtube",
    "youtube_channel_id",
    "youtube_url",
    "match_method",
    "match_confidence",
    "subscriber_count",
    "video_count",
    "view_count",
    "last_upload_date",
    "upload_frequency_30d",
    "content_type_primary",
]


@dataclass
class Match:
    has_youtube: bool
    youtube_channel_id: str = ""
    youtube_url: str = ""
    match_method: str = "not_found"
    match_confidence: str = "low"


def http_get_text(url: str, timeout: int = 20) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", 200)
        raw = resp.read()
    return status, raw.decode("utf-8", "replace")


def api_get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    status, text = http_get_text(url, timeout=timeout)
    if status >= 400:
        raise RuntimeError(f"http {status}")
    return json.loads(text)


def normalize_name(value: str) -> str:
    lowered = (value or "").casefold()
    lowered = re.sub(r"[\s_\-()\[\]{}|·ㆍ.,!?'\"`~:;]+", "", lowered)
    lowered = lowered.replace("official", "").replace("youtube", "")
    lowered = lowered.replace("유튜브", "").replace("공식", "")
    return lowered


def confidence_for_name(channel_name: str, candidate_title: str) -> str:
    source = normalize_name(channel_name)
    target = normalize_name(candidate_title)
    if not source or not target:
        return "low"
    if source == target:
        return "high"
    if source in target or target in source:
        return "medium"
    return "low"


def clean_youtube_url(url: str) -> str:
    value = html.unescape(url).replace("\\u0026", "&")
    value = value.split("?")[0].rstrip("/")
    if value.startswith("//"):
        value = "https:" + value
    return value


def extract_youtube_links(text: str) -> list[str]:
    if not text:
        return []
    decoded = html.unescape(text).replace("\\/", "/").replace("\\u0026", "&")
    patterns = [
        r"https?://(?:www\.)?youtube\.com/[@A-Za-z0-9_\-./?=&%]+",
        r"https?://(?:www\.)?youtu\.be/[A-Za-z0-9_\-./?=&%]+",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, decoded))
    result: list[str] = []
    seen: set[str] = set()
    for url in found:
        cleaned = clean_youtube_url(url)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def youtube_url_to_channel_id(api_key: str, youtube_url: str) -> str:
    if "/channel/" in youtube_url:
        m = re.search(r"/channel/(UC[\w-]+)", youtube_url)
        if m:
            return m.group(1)
    if not api_key:
        return ""
    handle = ""
    m = re.search(r"youtube\.com/@([^/?#]+)", youtube_url)
    if m:
        handle = "@" + urllib.parse.unquote(m.group(1))
    if not handle:
        return ""
    params = urllib.parse.urlencode(
        {
            "part": "snippet",
            "type": "channel",
            "maxResults": "5",
            "q": handle,
            "key": api_key,
        }
    )
    data = api_get_json(f"https://www.googleapis.com/youtube/v3/search?{params}")
    for item in data.get("items", []):
        channel_id = item.get("snippet", {}).get("channelId") or item.get("id", {}).get("channelId")
        title = item.get("snippet", {}).get("channelTitle", "")
        if channel_id and confidence_for_name(handle.lstrip("@"), title) != "low":
            return channel_id
    return ""


def find_chzzk_social_link(channel_id: str, include_page: bool = True) -> tuple[str, str]:
    urls = [
        f"https://api.chzzk.naver.com/service/v1/channels/{channel_id}",
    ]
    if include_page:
        urls.append(f"https://chzzk.naver.com/{channel_id}")
    for url in urls:
        try:
            _status, text = http_get_text(url)
        except Exception:
            continue
        links = extract_youtube_links(text)
        if links:
            return links[0], url
        time.sleep(0.2)
    return "", ""


def youtube_api_search(api_key: str, channel_name: str) -> Match:
    if not api_key:
        return Match(False)
    query = f"{channel_name} 유튜브"
    params = urllib.parse.urlencode(
        {
            "part": "snippet",
            "type": "channel",
            "maxResults": "5",
            "q": query,
            "relevanceLanguage": "ko",
            "regionCode": "KR",
            "key": api_key,
        }
    )
    try:
        data = api_get_json(f"https://www.googleapis.com/youtube/v3/search?{params}")
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise RuntimeError(f"youtube_search_http_{exc.code}") from exc
        raise
    best: tuple[int, str, str, str] | None = None
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        channel_id = item.get("id", {}).get("channelId") or snippet.get("channelId", "")
        title = snippet.get("channelTitle") or snippet.get("title") or ""
        if not channel_id:
            continue
        confidence = confidence_for_name(channel_name, title)
        score = {"high": 3, "medium": 2, "low": 1}.get(confidence, 0)
        if score > 1 and (best is None or score > best[0]):
            best = (score, channel_id, title, confidence)
    if not best:
        return Match(False)
    return Match(
        True,
        youtube_channel_id=best[1],
        youtube_url=f"https://www.youtube.com/channel/{best[1]}",
        match_method="youtube_search",
        match_confidence=best[3],
    )


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_csv_row(path: Path, fields: list[str], row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})
        f.flush()


def read_existing_presence(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows = load_csv(path)
    return {r.get("channelId", ""): r for r in rows if r.get("channelId")}


def sample_by_band(rows: list[dict[str, str]], sample_per_band: int) -> list[dict[str, str]]:
    if sample_per_band <= 0:
        return rows
    selected: list[dict[str, str]] = []
    for band in ["10k-20k", "20k-50k", "50k+"]:
        band_rows = [r for r in rows if r.get("band") == band]
        selected.extend(band_rows[:sample_per_band])
    return selected


def collect_presence(
    rows: list[dict[str, str]],
    output_path: Path,
    api_key: str,
    delay: float,
    use_api_search: bool,
    use_chzzk_social: bool,
    include_chzzk_page: bool,
    sample_per_band: int,
    limit: int,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    selected = sample_by_band(rows, sample_per_band)
    if limit > 0:
        selected = selected[:limit]
    existing = read_existing_presence(output_path)
    stats = {
        "target_rows": len(selected),
        "skipped_existing": 0,
        "social_link": 0,
        "api_search": 0,
        "not_found": 0,
        "errors": 0,
    }
    for index, row in enumerate(selected, start=1):
        channel_id = row.get("channelId", "")
        if channel_id in existing:
            stats["skipped_existing"] += 1
            continue
        name = row.get("channel_name", "")
        try:
            link = ""
            if use_chzzk_social:
                link, _source = find_chzzk_social_link(
                    channel_id,
                    include_page=include_chzzk_page,
                )
            if link:
                yt_id = youtube_url_to_channel_id(api_key, link)
                match = Match(
                    True,
                    youtube_channel_id=yt_id,
                    youtube_url=link,
                    match_method="chzzk_social_link",
                    match_confidence="high",
                )
                stats["social_link"] += 1
            elif use_api_search:
                match = youtube_api_search(api_key, name)
                if match.has_youtube:
                    stats["api_search"] += 1
                else:
                    stats["not_found"] += 1
            else:
                match = Match(False)
                stats["not_found"] += 1
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise RuntimeError(f"boundary http_{exc.code} at {name}/{channel_id}") from exc
            stats["errors"] += 1
            match = Match(False)
        except RuntimeError as exc:
            message = str(exc)
            if "http_403" in message or "http_429" in message:
                raise RuntimeError(f"boundary {message} at {name}/{channel_id}") from exc
            stats["errors"] += 1
            match = Match(False)
        except Exception:
            stats["errors"] += 1
            match = Match(False)
        out = {
            "channel_name": name,
            "channelId": channel_id,
            "band": row.get("band", ""),
            "has_youtube": "true" if match.has_youtube else "false",
            "youtube_channel_id": match.youtube_channel_id,
            "youtube_url": match.youtube_url,
            "match_method": match.match_method,
            "match_confidence": match.match_confidence,
        }
        append_csv_row(output_path, PRESENCE_FIELDS, out)
        existing[channel_id] = out
        print(
            f"[presence] {index}/{len(selected)} {name} "
            f"{out['has_youtube']} {out['match_method']} {out['match_confidence']}",
            flush=True,
        )
        time.sleep(delay)
    return list(existing.values()), stats


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(values), size):
        yield values[i : i + size]


def get_channel_metrics(api_key: str, channel_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not api_key or not channel_ids:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for chunk in chunks(channel_ids, 50):
        params = urllib.parse.urlencode(
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(chunk),
                "key": api_key,
            }
        )
        try:
            data = api_get_json(f"https://www.googleapis.com/youtube/v3/channels?{params}")
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise RuntimeError(f"youtube_channels_http_{exc.code}") from exc
            raise
        for item in data.get("items", []):
            cid = item.get("id", "")
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            uploads = (
                content.get("relatedPlaylists", {}).get("uploads", "")
                if isinstance(content, dict)
                else ""
            )
            result[cid] = {
                "subscriber_count": stats.get("subscriberCount", ""),
                "video_count": stats.get("videoCount", ""),
                "view_count": stats.get("viewCount", ""),
                "uploads_playlist": uploads,
            }
    return result


def parse_duration_seconds(value: str) -> int:
    if not value:
        return 0
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not m:
        return 0
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def classify_content_type(videos: list[dict[str, Any]]) -> str:
    if not videos:
        return ""
    counts = {"clip": 0, "highlight": 0, "full_vod": 0, "original": 0}
    for video in videos:
        title = (video.get("title") or "").casefold()
        seconds = int(video.get("duration_seconds") or 0)
        if seconds > 3600 or any(k in title for k in ["풀영상", "풀버전", "vod", "다시보기"]):
            counts["full_vod"] += 1
        elif seconds <= 300 or any(k in title for k in ["클립", "shorts", "쇼츠"]):
            counts["clip"] += 1
        elif seconds <= 1200 or any(k in title for k in ["하이라이트", "highlight"]):
            counts["highlight"] += 1
        else:
            counts["original"] += 1
    top = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "mixed"
    return top[0][0] if top[0][1] else ""


def get_recent_videos(api_key: str, uploads_playlist: str, max_results: int = 10) -> list[dict[str, Any]]:
    if not api_key or not uploads_playlist:
        return []
    params = urllib.parse.urlencode(
        {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist,
            "maxResults": str(max_results),
            "key": api_key,
        }
    )
    try:
        data = api_get_json(f"https://www.googleapis.com/youtube/v3/playlistItems?{params}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        if exc.code in (403, 429):
            raise RuntimeError(f"youtube_playlist_http_{exc.code}") from exc
        raise
    video_ids: list[str] = []
    base: dict[str, dict[str, Any]] = {}
    for item in data.get("items", []):
        content = item.get("contentDetails", {})
        snippet = item.get("snippet", {})
        vid = content.get("videoId", "")
        if not vid:
            continue
        video_ids.append(vid)
        base[vid] = {
            "published_at": content.get("videoPublishedAt") or snippet.get("publishedAt", ""),
            "title": snippet.get("title", ""),
        }
    if not video_ids:
        return []
    params = urllib.parse.urlencode(
        {
            "part": "contentDetails,snippet",
            "id": ",".join(video_ids),
            "key": api_key,
        }
    )
    try:
        details = api_get_json(f"https://www.googleapis.com/youtube/v3/videos?{params}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return list(base.values())
        if exc.code in (403, 429):
            raise RuntimeError(f"youtube_videos_http_{exc.code}") from exc
        raise
    for item in details.get("items", []):
        vid = item.get("id", "")
        base.setdefault(vid, {})
        base[vid]["duration_seconds"] = parse_duration_seconds(
            item.get("contentDetails", {}).get("duration", "")
        )
        base[vid]["title"] = item.get("snippet", {}).get("title", base[vid].get("title", ""))
    return list(base.values())


def collect_metrics(
    presence_rows: list[dict[str, str]],
    output_path: Path,
    api_key: str,
    delay: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    active = [
        r
        for r in presence_rows
        if r.get("has_youtube") == "true" and r.get("youtube_channel_id")
    ]
    ids = sorted({r["youtube_channel_id"] for r in active})
    metrics = get_channel_metrics(api_key, ids)
    existing_metric_keys: set[tuple[str, str]] = set()
    if output_path.exists():
        for existing in load_csv(output_path):
            existing_metric_keys.add(
                (
                    existing.get("source_channelId", ""),
                    existing.get("youtube_channel_id", ""),
                )
            )
    out_rows: list[dict[str, Any]] = []
    stats = {
        "active_with_channel_id": len(active),
        "metrics_rows": 0,
        "missing_metrics": 0,
        "skipped_existing": 0,
    }
    for row in active:
        cid = row["youtube_channel_id"]
        metric_key = (row.get("channelId", ""), cid)
        if metric_key in existing_metric_keys:
            stats["skipped_existing"] += 1
            continue
        metric = metrics.get(cid)
        if not metric:
            stats["missing_metrics"] += 1
            continue
        videos = get_recent_videos(api_key, metric.get("uploads_playlist", ""), max_results=10)
        last_upload = ""
        upload_frequency_30d = 0
        if videos:
            dates = []
            for v in videos:
                published = (v.get("published_at") or "")[:10]
                if not published:
                    continue
                try:
                    parsed = dt.date.fromisoformat(published)
                except ValueError:
                    continue
                dates.append(parsed)
            if dates:
                last_upload = max(dates).isoformat()
                cutoff = TODAY - dt.timedelta(days=30)
                upload_frequency_30d = sum(1 for d in dates if d >= cutoff)
        out = {
            "youtube_channel_id": cid,
            "youtube_url": row.get("youtube_url", f"https://www.youtube.com/channel/{cid}"),
            "channel_name": row.get("channel_name", ""),
            "source_channelId": row.get("channelId", ""),
            "band": row.get("band", ""),
            "subscriber_count": metric.get("subscriber_count", ""),
            "video_count": metric.get("video_count", ""),
            "view_count": metric.get("view_count", ""),
            "last_upload_date": last_upload,
            "upload_frequency_30d": upload_frequency_30d,
            "content_type_primary": classify_content_type(videos),
        }
        out_rows.append(out)
        append_csv_row(output_path, METRIC_FIELDS, out)
        existing_metric_keys.add(metric_key)
        stats["metrics_rows"] += 1
        print(f"[metrics] {stats['metrics_rows']}/{len(active)} {row.get('channel_name','')}", flush=True)
        time.sleep(delay)
    return out_rows, stats


def collect_gubiva(
    output_path: Path,
    api_key: str,
    delay: float,
    include_chzzk_page: bool,
) -> tuple[dict[str, Any], dict[str, int]]:
    link, _source = find_chzzk_social_link(CASE_CHANNEL_ID, include_page=include_chzzk_page)
    if link:
        yt_id = youtube_url_to_channel_id(api_key, link)
        match = Match(True, yt_id, link, "chzzk_social_link", "high")
    else:
        match = youtube_api_search(api_key, "구비바 치지직")
    row = {
        "channel_name": "구비바",
        "channelId": CASE_CHANNEL_ID,
        "has_youtube": "true" if match.has_youtube else "false",
        "youtube_channel_id": match.youtube_channel_id,
        "youtube_url": match.youtube_url,
        "match_method": match.match_method,
        "match_confidence": match.match_confidence,
        "subscriber_count": "",
        "video_count": "",
        "view_count": "",
        "last_upload_date": "",
        "upload_frequency_30d": "",
        "content_type_primary": "",
    }
    if match.has_youtube and match.youtube_channel_id and api_key:
        metrics = get_channel_metrics(api_key, [match.youtube_channel_id]).get(match.youtube_channel_id, {})
        videos = get_recent_videos(api_key, metrics.get("uploads_playlist", ""), max_results=10)
        dates = []
        for v in videos:
            try:
                dates.append(dt.date.fromisoformat((v.get("published_at") or "")[:10]))
            except ValueError:
                pass
        row.update(
            {
                "subscriber_count": metrics.get("subscriber_count", ""),
                "video_count": metrics.get("video_count", ""),
                "view_count": metrics.get("view_count", ""),
                "last_upload_date": max(dates).isoformat() if dates else "",
                "upload_frequency_30d": sum(
                    1 for d in dates if d >= TODAY - dt.timedelta(days=30)
                ),
                "content_type_primary": classify_content_type(videos),
            }
        )
    write_csv(output_path, GUBIVA_FIELDS, [row])
    time.sleep(delay)
    return row, {"has_youtube": 1 if match.has_youtube else 0}


def write_run_note(
    path: Path,
    input_path: Path,
    presence_path: Path,
    metrics_path: Path,
    gubiva_path: Path,
    presence_stats: dict[str, int],
    metric_stats: dict[str, int],
    gubiva_stats: dict[str, int],
    api_key_present: bool,
    sample_per_band: int,
    boundary: str,
) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    sampling = (
        f"band sample {sample_per_band} each"
        if sample_per_band > 0
        else "full target set"
    )
    text = f"""# 구비바 §7 YouTube Survey Run 20260619

Generated: {now}

## Scope

- Input: `{input_path}`
- Sampling: {sampling}
- YouTube Data API key present: {api_key_present}
- Raw HTML/JSON persisted: no
- Cookie/token/localStorage/sessionStorage/auth header/screenshot persisted: no
- Canonical case state mutated: no

## Outputs

- Presence: `{presence_path}`
- Active metrics: `{metrics_path}`
- Gubiva: `{gubiva_path}`

## Results

### Task 1 Presence

- target_rows: {presence_stats.get('target_rows', 0)}
- skipped_existing: {presence_stats.get('skipped_existing', 0)}
- chzzk_social_link: {presence_stats.get('social_link', 0)}
- youtube_search: {presence_stats.get('api_search', 0)}
- not_found: {presence_stats.get('not_found', 0)}
- errors: {presence_stats.get('errors', 0)}

### Task 2 Metrics

- active_with_channel_id: {metric_stats.get('active_with_channel_id', 0)}
- metrics_rows: {metric_stats.get('metrics_rows', 0)}
- missing_metrics: {metric_stats.get('missing_metrics', 0)}

### Task 3 Gubiva

- has_youtube: {gubiva_stats.get('has_youtube', 0)}

## Boundary

{boundary or 'No boundary signal observed.'}

## Notes

- `youtube_search` uses the YouTube Data API search endpoint and may be quota-bound.
- `chzzk_social_link` is preferred when available because it is directly linked from the streamer profile/page.
- `match_confidence=medium` rows should be manually spot-checked before analytic conclusions.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def summarize_presence_file(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    rows = load_csv(path)
    return {
        "target_rows": len(rows),
        "skipped_existing": 0,
        "social_link": sum(1 for r in rows if r.get("match_method") == "chzzk_social_link"),
        "api_search": sum(1 for r in rows if r.get("match_method") == "youtube_search"),
        "not_found": sum(1 for r in rows if r.get("match_method") == "not_found"),
        "errors": 0,
    }


def summarize_metrics_file(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    rows = load_csv(path)
    return {
        "active_with_channel_id": len(rows),
        "metrics_rows": len(rows),
        "missing_metrics": 0,
        "skipped_existing": 0,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/cohort/collected/cohort_ref_upper_band.csv")
    parser.add_argument("--presence-out", default="data/cohort/collected/youtube_presence_271.csv")
    parser.add_argument("--metrics-out", default="data/cohort/collected/youtube_metrics_active.csv")
    parser.add_argument("--gubiva-out", default="data/cohort/collected/youtube_gubiva.csv")
    parser.add_argument(
        "--run-note",
        default="work/step7_youtube_feasibility/구비바_§7_youtube_survey_run_20260619.md",
    )
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--sample-per-band", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-api-search", action="store_true")
    parser.add_argument("--skip-chzzk-social", action="store_true")
    parser.add_argument("--skip-chzzk-page", action="store_true")
    parser.add_argument("--skip-presence", action="store_true")
    parser.add_argument("--skip-metrics", action="store_true")
    parser.add_argument("--skip-gubiva", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path.cwd()
    input_path = root / args.input
    presence_path = root / args.presence_out
    metrics_path = root / args.metrics_out
    gubiva_path = root / args.gubiva_out
    run_note_path = root / args.run_note
    api_key = os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if not input_path.exists():
        print(f"missing input: {input_path}", file=sys.stderr)
        return 2
    rows = load_csv(input_path)
    boundary = ""
    presence_stats: dict[str, int] = {}
    metric_stats: dict[str, int] = {}
    gubiva_stats: dict[str, int] = {}
    try:
        if args.skip_presence:
            presence_rows = load_csv(presence_path) if presence_path.exists() else []
            presence_stats = summarize_presence_file(presence_path)
        else:
            presence_rows, presence_stats = collect_presence(
                rows=rows,
                output_path=presence_path,
                api_key=api_key,
                delay=args.delay,
                use_api_search=(not args.skip_api_search and bool(api_key)),
                use_chzzk_social=(not args.skip_chzzk_social),
                include_chzzk_page=(not args.skip_chzzk_page),
                sample_per_band=args.sample_per_band,
                limit=args.limit,
            )
        if not args.skip_metrics and api_key:
            _metrics_rows, metric_stats = collect_metrics(
                presence_rows=presence_rows,
                output_path=metrics_path,
                api_key=api_key,
                delay=args.delay,
            )
        elif args.skip_metrics:
            metric_stats = {"active_with_channel_id": 0, "metrics_rows": 0, "missing_metrics": 0}
        else:
            boundary = "YouTube API key absent; metrics collection skipped."
        if not args.skip_gubiva:
            _gubiva_row, gubiva_stats = collect_gubiva(
                gubiva_path,
                api_key,
                args.delay,
                include_chzzk_page=(not args.skip_chzzk_page),
            )
    except RuntimeError as exc:
        boundary = str(exc)
        print(f"boundary: {boundary}", file=sys.stderr)
    finally:
        if not presence_stats and presence_path.exists():
            presence_stats = summarize_presence_file(presence_path)
        if not metric_stats and metrics_path.exists():
            metric_stats = summarize_metrics_file(metrics_path)
        write_run_note(
            run_note_path,
            input_path,
            presence_path,
            metrics_path,
            gubiva_path,
            presence_stats,
            metric_stats,
            gubiva_stats,
            bool(api_key),
            args.sample_per_band,
            boundary,
        )
    return 1 if boundary.startswith("boundary") else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
