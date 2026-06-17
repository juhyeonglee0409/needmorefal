"""Collect §6 upper reference band rows from SOFTC.ONE.

This script uses a browser session only as an execution transport. It does not
read or persist cookies, localStorage, sessionStorage, auth headers, raw HTML,
or screenshots.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any


BASE_URL = "https://viewership.softc.one"
START_DATE = "2023-10-02"
END_DATE = "2026-06-16"
START_UTC = "2023-10-01T15:00:00.000Z"
END_UTC = "2026-06-16T14:59:59.999Z"
DETAIL_FETCH_TIMEOUT_MS = 15_000

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent.parent
COHORT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected"
LOG_DIR = COHORT_DIR / "collection_logs"
PROFILE_DIR = PACKAGE_ROOT / "work" / "step4_cohort_collect_prep" / ".pw_profile"

OUT_CSV = COHORT_DIR / "cohort_ref_upper_band.csv"
OUT_NOTES = COHORT_DIR / "cohort_ref_upper_band_notes.csv"
OUT_CANDIDATES = COHORT_DIR / "_upper_band_candidates.json"
OUT_MANIFEST = LOG_DIR / "_upper_band_collection_manifest.json"
OUT_PROGRESS = LOG_DIR / "_upper_band_detail_progress.ndjson"
OUT_DETAIL_RECORDS = LOG_DIR / "_upper_band_detail_records.json"

CSV_FIELDS = [
    "channel_name",
    "channelId",
    "channel_url",
    "follower",
    "categories",
    "is_general_game",
    "is_virtual",
    "peak_max",
    "peak_p95",
    "peak_median",
    "peak_recent_median",
    "avg_median",
    "avg_recent_median",
    "stream_hours",
    "ts_weeks",
    "band",
]

NOTE_FIELDS = [
    "channelId",
    "channel_name",
    "source",
    "note_type",
    "detail",
]


def parse_pages(value: str) -> list[int]:
    pages: list[int] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def median(values: list[float]) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2


def percentile(values: list[float], pct: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def fmt_num(value: float | int | None, digits: int = 1) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(int(value))


def follower_band(follower: int | None) -> str:
    if follower is None:
        return ""
    if follower < 20_000:
        return "10k-20k"
    if follower < 50_000:
        return "20k-50k"
    return "50k+"


def classify_gg(row: dict[str, Any]) -> tuple[str, str]:
    c1 = str(row.get("category_1") or "").strip()
    c1s = float(row.get("category_1_share") or 0)
    c2 = str(row.get("category_2") or "").strip()
    c2s = float(row.get("category_2_share") or 0)
    c3 = str(row.get("category_3") or "").strip()
    c3s = float(row.get("category_3_share") or 0)

    if not c1:
        return "unknown", "no_category_data"
    if c1 in {"종합 게임", "종합게임"}:
        return "true", "gg_primary"
    if c1.lower() == "talk" and c1s >= 50:
        return "false", "talk_primary"
    if c1s >= 80:
        return "false", "single_game_dominant"

    pairs = [(c1, c1s), (c2, c2s), (c3, c3s)]
    non_talk = [
        (name, share)
        for name, share in pairs
        if name and name.lower() != "talk" and name not in {"그림/아트", "먹방"} and share >= 15
    ]
    if len(non_talk) >= 2:
        return "true", "multi_game"
    if c2 in {"종합 게임", "종합게임"} and c2s >= 15:
        return "true", "gg_secondary"
    return "false", "single_game_or_non_game"


def looks_like_org(name: str) -> bool:
    text = name.upper().replace(" ", "")
    org_tokens = [
        "공식",
        "OFFICIAL",
        "E-SPORTS",
        "ESPORTS",
        "ESPORT",
        "GEN.G",
        "GENG",
        "DPLUS",
        "DK",
        "DRX",
        "KDF",
        "광동프릭스",
        "농심",
        "T1ESPORTS",
    ]
    return any(token.upper().replace(" ", "") in text for token in org_tokens)


def row_is_eligible(detail: dict[str, Any]) -> tuple[bool, str]:
    follower = detail.get("follower")
    if follower is None or follower < 10_000:
        return False, "follower_below_10k"
    if not detail.get("maxLiveViews"):
        return False, "broadcast_metrics_unavailable"
    if detail.get("ts_weeks", 0) < 8:
        return False, "too_new_under_8_weeks"
    if looks_like_org(str(detail.get("name") or "")):
        return False, "excluded_org_or_team_heuristic"
    if detail.get("is_general_game") != "true" and detail.get("is_virtual") != "true":
        return False, "not_general_game_or_virtual"
    return True, ""


def output_row(detail: dict[str, Any]) -> dict[str, str]:
    peaks = detail.get("maxLiveViews") or []
    avgs = detail.get("avgLiveViews") or []
    hours = detail.get("airTime") or []
    recent_peaks = peaks[-8:]
    recent_avgs = avgs[-8:]
    cats = [detail.get("category_1"), detail.get("category_2"), detail.get("category_3")]
    categories = ",".join([str(c) for c in cats if c])
    follower = detail.get("follower")
    return {
        "channel_name": str(detail.get("name") or ""),
        "channelId": str(detail.get("channelId") or ""),
        "channel_url": f"https://chzzk.naver.com/live/{detail.get('channelId')}",
        "follower": "" if follower is None else str(follower),
        "categories": categories,
        "is_general_game": str(detail.get("is_general_game") == "true").lower(),
        "is_virtual": str(detail.get("is_virtual") == "true").lower(),
        "peak_max": fmt_num(max(peaks) if peaks else None),
        "peak_p95": fmt_num(percentile(peaks, 0.95)),
        "peak_median": fmt_num(median(peaks)),
        "peak_recent_median": fmt_num(median(recent_peaks)),
        "avg_median": fmt_num(median(avgs)),
        "avg_recent_median": fmt_num(median(recent_avgs)),
        "stream_hours": fmt_num(sum(hours) if hours else None),
        "ts_weeks": str(detail.get("ts_weeks") or ""),
        "band": follower_band(follower),
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):
        try:
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.25 * (attempt + 1))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, list) else []


def read_progress_channel_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    processed_statuses = {"accepted", "excluded", "fetch_error"}
    processed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("status") not in processed_statuses:
            continue
        channel_id = str(record.get("channelId") or "").strip()
        if channel_id:
            processed.add(channel_id)
    return processed


def read_output_channel_ids(csv_path: Path, notes_path: Path) -> set[str]:
    completed: set[str] = set()
    for row in read_csv_rows(csv_path):
        channel_id = str(row.get("channelId") or "").strip()
        if channel_id:
            completed.add(channel_id)
    for row in read_csv_rows(notes_path):
        channel_id = str(row.get("channelId") or "").strip()
        if channel_id:
            completed.add(channel_id)
    return completed


def write_json_list(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    for attempt in range(5):
        try:
            path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.25 * (attempt + 1))


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def eval_json(page: Any, expression: str, await_promise: bool = False) -> dict[str, Any]:
    value = await page.evaluate(expression, await_promise=await_promise, return_by_value=True)
    if value is None:
        raise ValueError("browser evaluation returned no value")
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    raise TypeError(f"browser evaluation returned unsupported value: {value!r}")


def extract_followers_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const select = [...document.querySelectorAll('select')]
        .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
      if (select && select.value !== 'naverchzzk') {
        select.value = 'naverchzzk';
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return JSON.stringify({ href: location.href, selected: select ? select.value : null });
    })()
    """


def collect_followers_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const body = norm(document.body?.innerText || '');
      const links = [...document.querySelectorAll('a[href*="/channel/naverchzzk/"]')];
      const rows = [];
      const seen = new Set();
      for (const a of links) {
        const href = a.href;
        const m = href.match(/\/channel\/naverchzzk\/([a-f0-9]{20,})/);
        if (!m || seen.has(m[1])) continue;
        seen.add(m[1]);
        const text = norm(a.innerText || a.textContent);
        const nums = [...text.matchAll(/\d[\d,]*/g)].map(x => x[0]);
        const followerText = nums.length ? nums[nums.length - 1] : '';
        const follower = followerText ? parseInt(followerText.replace(/,/g, ''), 10) : null;
        const rank = nums.length ? parseInt(nums[0].replace(/,/g, ''), 10) : null;
        let name = text
          .replace(/^\d+\s*/, '')
          .replace(/\d{4}\.\d{2}\.\d{2}.*$/, '')
          .replace(/[↑↓].*$/, '')
          .trim();
        rows.push({
          source: 'followers',
          channelId: m[1],
          platform: 'naverchzzk',
          name,
          href,
          follower,
          rank,
          rowText: text.slice(0, 240)
        });
      }
      return JSON.stringify({
        href: location.href,
        title: document.title,
        checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인|We're verifying your browser/i.test(body),
        rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(body),
        rows
      });
    })()
    """


def collect_virtual_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const body = norm(document.body?.innerText || '');
      const links = [...document.querySelectorAll('a[href*="/channel/naverchzzk/"]')];
      const rows = [];
      const seen = new Set();
      for (const a of links) {
        const href = a.href;
        const m = href.match(/\/channel\/naverchzzk\/([a-f0-9]{20,})/);
        if (!m || seen.has(m[1])) continue;
        seen.add(m[1]);
        const text = norm(a.innerText || a.textContent);
        rows.push({
          source: 'virtual_ranking',
          channelId: m[1],
          platform: 'naverchzzk',
          name: text.replace(/^\d+\s*/, '').replace(/\d{4}\.\d{2}\.\d{2}.*$/, '').trim(),
          href,
          follower: null,
          rank: null,
          rowText: text.slice(0, 240),
          is_virtual_source: true
        });
      }
      return JSON.stringify({
        href: location.href,
        title: document.title,
        checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인|We're verifying your browser/i.test(body),
        rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(body),
        rows
      });
    })()
    """


def detail_expression(candidate: dict[str, Any]) -> str:
    channel_id = candidate["channelId"]
    url = (
        f"{BASE_URL}/channel/naverchzzk/{channel_id}"
        f"?start={START_DATE}&end={END_DATE}&startDateTime={START_UTC}&endDateTime={END_UTC}"
    )
    return f"""
    (async () => {{
      const candidate = {json.dumps(candidate, ensure_ascii=False)};
      const url = {json.dumps(url)};
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), {DETAIL_FETCH_TIMEOUT_MS});
      let response;
      let text;
      try {{
        response = await fetch(url, {{ credentials: 'include', signal: controller.signal }});
        text = await response.text();
      }} catch (e) {{
        clearTimeout(timer);
        return JSON.stringify({{
          channelId: candidate.channelId,
          source: candidate.source,
          source_rank: candidate.rank,
          source_follower: candidate.follower,
          source_name: candidate.name,
          detail_url: url,
          fetch_error: String(e && (e.name || e.message) ? ((e.name || '') + ':' + (e.message || '')) : e),
          name: candidate.name || '',
          follower: candidate.follower,
          maxLiveViews: [],
          avgLiveViews: [],
          airTime: [],
          is_virtual_source: !!candidate.is_virtual_source
        }});
      }}
      clearTimeout(timer);
      const nums = (pattern) => {{
        const out = [];
        let m;
        while ((m = pattern.exec(text)) !== null) out.push(Number(m[1]));
        if (out.length) return out.slice(0, Math.ceil(out.length / 2));
        return out;
      }};
      const firstText = (patterns) => {{
        for (const pattern of patterns) {{
          const m = text.match(pattern);
          if (m) return m[1];
        }}
        return '';
      }};
      const followerMatches = [...text.matchAll(/\\\\"followerCount\\\\":(\\d+)/g)].map(m => Number(m[1]));
      const followerMatches2 = [...text.matchAll(/"followerCount":(\\d+)/g)].map(m => Number(m[1]));
      const follower = followerMatches.length
        ? followerMatches[followerMatches.length - 1]
        : (followerMatches2.length ? followerMatches2[followerMatches2.length - 1] : candidate.follower);
      const cats = [];
      for (const pattern of [
        /\\\\"category\\\\":\\\\"([^\\\\]+)\\\\",\\\\"sumLiveViews\\\\":\\d+,\\\\"viewership\\\\":(\\d+)/g,
        /"category":"([^"]+)","sumLiveViews":\\d+,"viewership":(\\d+)/g
      ]) {{
        let m;
        while ((m = pattern.exec(text)) !== null) cats.push({{ name: m[1], viewership: Number(m[2]) }});
        if (cats.length) break;
      }}
      cats.sort((a, b) => b.viewership - a.viewership);
      const totalCat = cats.reduce((s, c) => s + c.viewership, 0);
      const share = idx => cats[idx] && totalCat ? Math.round(cats[idx].viewership / totalCat * 1000) / 10 : 0;
      const maxLiveViews = nums(/\\\\"maxLiveViews\\\\":([\\d.]+)/g);
      const avgLiveViews = nums(/\\\\"avgLiveViews\\\\":([\\d.]+)/g);
      const airTime = nums(/\\\\"airTime\\\\":([\\d.]+)/g);
      const bodyHead = text.replace(/\\s+/g, ' ').slice(0, 240);
      return JSON.stringify({{
        channelId: candidate.channelId,
        source: candidate.source,
        source_rank: candidate.rank,
        source_follower: candidate.follower,
        source_name: candidate.name,
        detail_url: url,
        http_status: response.status,
        checkpoint: /Security Checkpoint|We're verifying your browser|보안 검문/i.test(bodyHead),
        name: candidate.name || firstText([
          /\\\\"(?:nickname|channelName|name)\\\\":\\\\"([^\\\\]+)\\\\"/,
          /"(?:nickname|channelName|name)":"([^"]+)"/
        ]) || '',
        follower,
        category_1: cats[0] ? cats[0].name : '',
        category_1_share: share(0),
        category_2: cats[1] ? cats[1].name : '',
        category_2_share: share(1),
        category_3: cats[2] ? cats[2].name : '',
        category_3_share: share(2),
        total_categories: cats.length,
        maxLiveViews,
        avgLiveViews,
        airTime,
        is_virtual_source: !!candidate.is_virtual_source
      }});
    }})()
    """


async def collect_candidates(browser: Any, follower_pages: list[int], virtual_pages: list[int], delay_ms: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: dict[str, dict[str, Any]] = {}
    notes: list[dict[str, Any]] = []

    for page_num in follower_pages:
        url = f"{BASE_URL}/ranking/followers?page={page_num}"
        print(f"[followers] page {page_num}: {url}")
        page = await browser.get(url)
        await asyncio.sleep(delay_ms / 1000)
        await eval_json(page, extract_followers_expression())
        await asyncio.sleep(delay_ms / 1000)
        payload = await eval_json(page, collect_followers_expression())
        if payload.get("checkpoint") or payload.get("rateLimited"):
            notes.append({"channelId": "", "channel_name": "", "source": "followers", "note_type": "boundary", "detail": json.dumps(payload, ensure_ascii=False)})
            break
        rows = payload.get("rows") or []
        print(f"  rows={len(rows)} href={payload.get('href')}")
        for row in rows:
            follower = safe_int(row.get("follower"))
            if follower is not None and follower < 10_000:
                continue
            cid = row["channelId"]
            prev = candidates.get(cid)
            if prev:
                prev.setdefault("sources", []).append("followers")
                if follower and not prev.get("follower"):
                    prev["follower"] = follower
                continue
            row["follower"] = follower
            row["sources"] = ["followers"]
            candidates[cid] = row

    for page_num in virtual_pages:
        url = f"{BASE_URL}/ranking/virtualsoftcone?platform=naverchzzk&page={page_num}"
        print(f"[virtual] page {page_num}: {url}")
        page = await browser.get(url)
        await asyncio.sleep(delay_ms / 1000)
        payload = await eval_json(page, collect_virtual_expression())
        if payload.get("checkpoint") or payload.get("rateLimited"):
            notes.append({"channelId": "", "channel_name": "", "source": "virtual_ranking", "note_type": "boundary", "detail": json.dumps(payload, ensure_ascii=False)})
            break
        rows = payload.get("rows") or []
        print(f"  rows={len(rows)} href={payload.get('href')}")
        for row in rows:
            cid = row["channelId"]
            prev = candidates.get(cid)
            if prev:
                prev["is_virtual_source"] = True
                prev.setdefault("sources", []).append("virtual_ranking")
                continue
            row["sources"] = ["virtual_ranking"]
            row["is_virtual_source"] = True
            candidates[cid] = row

    return list(candidates.values()), notes


def prioritize_candidates(candidates: list[dict[str, Any]], max_details: int) -> list[dict[str, Any]]:
    def band_key(item: dict[str, Any]) -> int:
        follower = safe_int(item.get("follower"))
        if follower is None:
            return 3
        if 10_000 <= follower < 20_000:
            return 0
        if 20_000 <= follower < 50_000:
            return 1
        return 2

    grouped: dict[int, list[dict[str, Any]]] = {0: [], 1: [], 2: [], 3: []}
    for item in candidates:
        follower = safe_int(item.get("follower"))
        if follower is not None and follower < 10_000:
            continue
        grouped[band_key(item)].append(item)

    for rows in grouped.values():
        rows.sort(key=lambda r: safe_int(r.get("follower")) or 0, reverse=True)

    ordered: list[dict[str, Any]] = []
    first_pass = [(2, 40), (1, 40), (0, 60), (3, 40)]
    for key, cap in first_pass:
        ordered.extend(grouped[key][:cap])

    seen = {item["channelId"] for item in ordered}
    for key in [2, 1, 0, 3]:
        ordered.extend(item for item in grouped[key] if item["channelId"] not in seen)
        seen.update(item["channelId"] for item in grouped[key])
    return ordered[:max_details]


async def collect_details(
    page: Any,
    candidates: list[dict[str, Any]],
    delay_ms: int,
    initial_rows: list[dict[str, str]] | None = None,
    initial_notes: list[dict[str, str]] | None = None,
    initial_detail_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    rows: list[dict[str, str]] = list(initial_rows or [])
    notes: list[dict[str, str]] = list(initial_notes or [])
    detail_records: list[dict[str, Any]] = list(initial_detail_records or [])

    for idx, candidate in enumerate(candidates, start=1):
        await asyncio.sleep(delay_ms / 1000)
        try:
            detail = await eval_json(page, detail_expression(candidate), await_promise=True)
        except Exception as exc:
            note = {
                "channelId": candidate.get("channelId", ""),
                "channel_name": candidate.get("name", ""),
                "source": ",".join(candidate.get("sources") or [candidate.get("source", "")]),
                "note_type": "detail_fetch_error",
                "detail": str(exc),
            }
            notes.append(note)
            append_jsonl(OUT_PROGRESS, {
                "idx": idx,
                "total": len(candidates),
                "channelId": candidate.get("channelId", ""),
                "status": "fetch_error",
                "detail": str(exc),
            })
            write_csv(OUT_CSV, rows, CSV_FIELDS)
            write_csv(OUT_NOTES, notes, NOTE_FIELDS)
            continue

        if detail.get("fetch_error"):
            note = {
                "channelId": candidate.get("channelId", ""),
                "channel_name": candidate.get("name", ""),
                "source": ",".join(candidate.get("sources") or [candidate.get("source", "")]),
                "note_type": "detail_fetch_error",
                "detail": str(detail.get("fetch_error") or ""),
            }
            notes.append(note)
            append_jsonl(OUT_PROGRESS, {
                "idx": idx,
                "total": len(candidates),
                "channelId": candidate.get("channelId", ""),
                "channel_name": candidate.get("name", ""),
                "status": "fetch_error",
                "detail": note["detail"],
            })
            write_csv(OUT_CSV, rows, CSV_FIELDS)
            write_csv(OUT_NOTES, notes, NOTE_FIELDS)
            print(f"[detail] {idx}/{len(candidates)} fetch_error {candidate.get('name')} {note['detail']}")
            continue

        detail["follower"] = safe_int(detail.get("follower"))
        detail["is_virtual"] = "true" if detail.get("is_virtual_source") else "false"
        detail["ts_weeks"] = max(len(detail.get("maxLiveViews") or []), len(detail.get("avgLiveViews") or []), len(detail.get("airTime") or []))
        gg, gg_reason = classify_gg(detail)
        detail["is_general_game"] = gg
        detail["gg_reason"] = gg_reason
        detail_records.append(detail)
        write_json_list(OUT_DETAIL_RECORDS, detail_records)

        ok, reason = row_is_eligible(detail)
        if ok:
            rows.append(output_row(detail))
            append_jsonl(OUT_PROGRESS, {
                "idx": idx,
                "total": len(candidates),
                "channelId": detail.get("channelId", ""),
                "channel_name": detail.get("name", ""),
                "status": "accepted",
                "accepted_count": len(rows),
                "follower": detail.get("follower"),
                "band": follower_band(detail.get("follower")),
                "is_general_game": gg,
                "is_virtual": detail.get("is_virtual"),
            })
            print(f"[detail] {idx}/{len(candidates)} accepted={len(rows)} {detail.get('name')} follower={detail.get('follower')} gg={gg} virtual={detail.get('is_virtual')}")
        else:
            notes.append({
                "channelId": str(detail.get("channelId") or ""),
                "channel_name": str(detail.get("name") or candidate.get("name") or ""),
                "source": ",".join(candidate.get("sources") or [candidate.get("source", "")]),
                "note_type": "excluded",
                "detail": reason,
            })
            append_jsonl(OUT_PROGRESS, {
                "idx": idx,
                "total": len(candidates),
                "channelId": detail.get("channelId", ""),
                "channel_name": detail.get("name") or candidate.get("name") or "",
                "status": "excluded",
                "detail": reason,
                "follower": detail.get("follower"),
                "band": follower_band(detail.get("follower")),
                "is_general_game": gg,
                "is_virtual": detail.get("is_virtual"),
            })
            print(f"[detail] {idx}/{len(candidates)} skip {detail.get('name') or candidate.get('name')} reason={reason}")
        write_csv(OUT_CSV, rows, CSV_FIELDS)
        write_csv(OUT_NOTES, notes, NOTE_FIELDS)

    return rows, notes, detail_records


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_band: dict[str, int] = {"10k-20k": 0, "20k-50k": 0, "50k+": 0}
    for row in rows:
        by_band[row["band"]] = by_band.get(row["band"], 0) + 1
    return {
        "row_count": len(rows),
        "by_band": by_band,
        "general_game_count": sum(1 for row in rows if row["is_general_game"] == "true"),
        "virtual_count": sum(1 for row in rows if row["is_virtual"] == "true"),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--follower-pages", default="1-12")
    parser.add_argument("--virtual-pages", default="1-4")
    parser.add_argument("--delay-ms", type=int, default=3000)
    parser.add_argument("--detail-delay-ms", type=int, default=3000)
    parser.add_argument("--max-details", type=int, default=140)
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--use-existing-candidates", action="store_true")
    parser.add_argument("--detail-bands", default="")
    parser.add_argument("--append-existing-output", action="store_true")
    parser.add_argument("--skip-progress-existing", action="store_true")
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        sys.exit(1)

    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    follower_pages = parse_pages(args.follower_pages)
    virtual_pages = parse_pages(args.virtual_pages)
    manifest: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": "nodriver_profile_browser_fetch",
        "profile_dir": str(PROFILE_DIR),
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
        "date_range": {"start": START_DATE, "end": END_DATE, "start_utc": START_UTC, "end_utc": END_UTC},
        "follower_pages": follower_pages,
        "virtual_pages": virtual_pages,
        "delay_ms": args.delay_ms,
        "detail_delay_ms": args.detail_delay_ms,
    }

    candidates: list[dict[str, Any]] | None = None
    boundary_notes: list[dict[str, Any]] = []
    if args.use_existing_candidates:
        previous_manifest: dict[str, Any] = {}
        if OUT_MANIFEST.exists():
            try:
                previous_manifest = json.loads(OUT_MANIFEST.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                previous_manifest = {}
        if not OUT_CANDIDATES.exists():
            print(f"ERROR: missing candidate file: {OUT_CANDIDATES}", file=sys.stderr)
            sys.exit(1)
        candidates = json.loads(OUT_CANDIDATES.read_text(encoding="utf-8"))
        manifest["candidate_source"] = "existing_file"
        manifest["candidate_count"] = len(candidates)
        manifest["candidate_path"] = str(OUT_CANDIDATES)
        if previous_manifest.get("existing_candidate_provenance"):
            manifest["existing_candidate_provenance"] = previous_manifest["existing_candidate_provenance"]
        elif previous_manifest.get("mode") == "candidates_only":
            manifest["existing_candidate_provenance"] = {
                "candidate_count": previous_manifest.get("candidate_count"),
                "follower_pages": previous_manifest.get("follower_pages"),
                "virtual_pages": previous_manifest.get("virtual_pages"),
                "note": "Candidate pool was generated by a previous candidates_only run.",
            }

    print(f"[start] profile={PROFILE_DIR}")
    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=PROFILE_DIR)
    try:
        if candidates is None:
            candidates, boundary_notes = await collect_candidates(browser, follower_pages, virtual_pages, args.delay_ms)
            OUT_CANDIDATES.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest["candidate_source"] = "fresh_scan"
            manifest["candidate_count"] = len(candidates)
            manifest["candidate_path"] = str(OUT_CANDIDATES)

        if args.candidates_only:
            manifest["mode"] = "candidates_only"
            manifest["notes"] = boundary_notes
            OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"candidates": len(candidates), "candidate_path": str(OUT_CANDIDATES), "manifest": str(OUT_MANIFEST)}, ensure_ascii=False, indent=2))
            return

        allowed_bands = {band.strip() for band in args.detail_bands.split(",") if band.strip()}
        if allowed_bands:
            candidates = [
                item
                for item in candidates
                if follower_band(safe_int(item.get("follower"))) in allowed_bands
            ]
            manifest["detail_bands"] = sorted(allowed_bands)

        if args.skip_progress_existing:
            progress_ids = read_progress_channel_ids(OUT_PROGRESS)
            output_ids = read_output_channel_ids(OUT_CSV, OUT_NOTES)
            completed_ids = progress_ids & output_ids
            candidates = [
                item
                for item in candidates
                if str(item.get("channelId") or "").strip() not in completed_ids
            ]
            manifest["skip_progress_existing"] = True
            manifest["progress_existing_count"] = len(progress_ids)
            manifest["output_existing_count"] = len(output_ids)
            manifest["completed_existing_count"] = len(completed_ids)
            manifest["progress_without_output_count"] = len(progress_ids - output_ids)

        ordered = prioritize_candidates(candidates, args.max_details)
        detail_path = OUT_DETAIL_RECORDS
        initial_rows: list[dict[str, str]] = []
        initial_notes: list[dict[str, str]] = []
        initial_detail_records: list[dict[str, Any]] = []
        if args.append_existing_output:
            initial_rows = read_csv_rows(OUT_CSV)
            initial_notes = read_csv_rows(OUT_NOTES)
            initial_detail_records = read_json_list(detail_path)
            existing_ids = {row.get("channelId") for row in initial_rows if row.get("channelId")}
            ordered = [item for item in ordered if item.get("channelId") not in existing_ids]
            manifest["append_existing_output"] = True
            manifest["initial_row_count"] = len(initial_rows)

        manifest["detail_candidate_count"] = len(ordered)
        manifest["mode"] = "details_running"
        manifest["progress_path"] = str(OUT_PROGRESS)
        if args.append_existing_output and OUT_PROGRESS.exists():
            append_jsonl(OUT_PROGRESS, {"event": "append_run_start", "candidate_count": len(ordered), "bands": sorted(allowed_bands)})
        else:
            OUT_PROGRESS.write_text("", encoding="utf-8")
        write_csv(OUT_CSV, initial_rows, CSV_FIELDS)
        write_csv(OUT_NOTES, initial_notes, NOTE_FIELDS)
        OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        page = await browser.get(BASE_URL)
        await asyncio.sleep(args.delay_ms / 1000)
        rows, notes, detail_records = await collect_details(
            page,
            ordered,
            args.detail_delay_ms,
            initial_rows=initial_rows,
            initial_notes=initial_notes,
            initial_detail_records=initial_detail_records,
        )
        notes.extend({k: str(v) for k, v in note.items()} for note in boundary_notes)
        write_csv(OUT_CSV, rows, CSV_FIELDS)
        write_csv(OUT_NOTES, notes, NOTE_FIELDS)
        write_json_list(detail_path, detail_records)

        manifest["output_csv"] = str(OUT_CSV)
        manifest["notes_csv"] = str(OUT_NOTES)
        manifest["detail_records_path"] = str(detail_path)
        manifest["mode"] = "details_complete"
        manifest["summary"] = summarize(rows)
        OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"csv": str(OUT_CSV), "notes": str(OUT_NOTES), "summary": manifest["summary"]}, ensure_ascii=False, indent=2))
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
