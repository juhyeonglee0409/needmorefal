from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse


RUN_ID = "kimdalsu_recollect_20260616_01"
CASE_ID = "kimdalsu_20260601"
STREAMER_KEY = "kimdalsu"
SUBJECT_ID = "dcbccbf2d8e2a1b095244c5856d3613a"
BASE = "https://viewership.softc.one"
SUBJECT_URL = f"{BASE}/channel/naverchzzk/{SUBJECT_ID}"
LOL_CATEGORY_URL = f"{BASE}/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C/softconeranking"
FOLLOWER_URL = f"{BASE}/ranking/followers?type=naverchzzk"
KST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def compact_int(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9]", "", value)
    return int(cleaned) if cleaned else None


def compact_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[0-9][0-9,]*(?:\.[0-9]+)?", value)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def first_int_after(label: str, text: str) -> int | None:
    pattern = re.compile(re.escape(label) + r"[\s:：]*([0-9][0-9,]*)")
    match = pattern.search(text)
    if match:
        return compact_int(match.group(1))
    return None


def extract_channel_ref(url: str) -> tuple[str | None, str | None]:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 3 and parts[0] == "channel":
        return parts[1], parts[-1]
    return None, None


def extract_rank(text: str) -> int | None:
    match = re.search(r"(?:^|\s)([0-9]{1,5})(?:위|\s)", text)
    return int(match.group(1)) if match else None


def extract_followers(text: str) -> int | None:
    for pattern in [
        r"팔로워\s*([0-9][0-9,]*)",
        r"([0-9][0-9,]*)\s*팔로워",
        r"follower[s]?\s*([0-9][0-9,]*)",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return compact_int(match.group(1))
    compact = [compact_int(x) for x in re.findall(r"\d[\d,]*", text)]
    compact = [x for x in compact if x is not None]
    if compact:
        return compact[-1]
    return None


def parse_category_row_text(row_text: str) -> dict:
    match = re.match(
        r"^\s*(\d+)\s+(.+?)\s+\d+/\d+/\d+\s+[0-9]+(?:\.[0-9]+)?\s+p\s+([0-9]+(?:\.[0-9]+)?)\s+h\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        row_text,
    )
    if not match:
        return {
            "source_rank": extract_rank(row_text),
            "channel_name": None,
            "stream_hours": None,
            "peak_viewers": None,
            "avg_viewers": None,
            "viewership": None,
        }
    return {
        "source_rank": int(match.group(1)),
        "channel_name": match.group(2).strip(),
        "stream_hours": compact_float(match.group(3)),
        "peak_viewers": compact_int(match.group(4)),
        "avg_viewers": compact_int(match.group(5)),
        "viewership": compact_int(match.group(6)),
    }


def parse_follower_row_text(row_text: str) -> dict:
    match = re.match(r"^\s*(\d+)\s+(.+?)\s+\d{4}\.\d{2}\.\d{2}.*?(\d[\d,]*)\s*$", row_text)
    if not match:
        return {
            "source_rank": extract_rank(row_text),
            "channel_name": None,
            "follower_count": extract_followers(row_text),
        }
    return {
        "source_rank": int(match.group(1)),
        "channel_name": match.group(2).strip(),
        "follower_count": compact_int(match.group(3)),
    }


async def evaluate_page(page) -> dict:
    payload = await page.evaluate(
        r"""
        (() => {
          const norm = s => (s || '').replace(/\s+/g, ' ').trim();
          const body = norm(document.body?.innerText || '');
          const lower = body.toLowerCase();
          const lines = (document.body?.innerText || '')
            .split(/\n+/)
            .map(norm)
            .filter(Boolean);
          const metricLines = lines
            .filter(x => /(김달수|Dalsu|팔로워|시청자|뷰어십|방송|채팅|리그 오브 레전드|랭킹|ENTERPRISE|멤버십|높은 등급|로그인|checkpoint|challenge|429)/i.test(x))
            .slice(0, 220);
          const channelAnchors = [...document.querySelectorAll('a[href*="/channel/"]')]
            .map((a, i) => {
              let node = a;
              for (let depth = 0; depth < 4 && node.parentElement; depth++) {
                const txt = norm(node.parentElement.innerText || node.parentElement.textContent || '');
                if (txt.length > 20 && txt.length < 900) {
                  node = node.parentElement;
                } else {
                  break;
                }
              }
              return {
                i,
                href: a.href,
                anchor_text: norm(a.innerText || a.textContent).slice(0, 160),
                row_text: norm(node.innerText || node.textContent || '').slice(0, 800)
              };
            })
            .filter(x => x.href);
          const boundary = {
            checkpoint_detected: /(Security Checkpoint|checkpoint|captcha|verifying your browser|just a moment|보안 확인|브라우저를 확인|보안 검문)/i.test(body),
            rate_limited_detected: /(429\s+Too Many Requests|Too Many Requests|rate limit|요청이 너무 많)/i.test(body),
            login_required_likely: /(로그인이 필요|login required|sign in to continue|권한이 없습니다|인증이 필요)/i.test(body),
            enterprise_required_likely: /(높은 등급의 멤버십에서 이용 가능합니다|해당 기능은 .*멤버십.*이용 가능합니다|멤버십이 필요합니다)/i.test(body)
          };
          return JSON.stringify({
            final_url: location.href,
            title: document.title,
            body_text_length: body.length,
            body_hash: body ? null : null,
            visible_text_sample: body.slice(0, 700),
            metric_lines: metricLines,
            link_count: document.querySelectorAll('a[href]').length,
            channel_anchor_count: channelAnchors.length,
            channel_anchors: channelAnchors.slice(0, 260),
            boundary,
            content_signals: {
              has_kimdalsu: body.includes('김달수') || lower.includes('dalsu'),
              has_softcon: body.includes('소프트콘') || lower.includes('softc'),
              has_lol: body.includes('리그 오브 레전드') || lower.includes('league of legends'),
              has_follower: body.includes('팔로워') || lower.includes('follower'),
              has_ranking: body.includes('랭킹') || lower.includes('ranking')
            }
          });
        })()
        """
    )
    return json.loads(payload)


async def visit(page, url: str, wait_seconds: float = 8.0) -> dict:
    await page.get(url)
    await asyncio.sleep(wait_seconds)
    return await evaluate_page(page)


async def set_naverchzzk_platform(page) -> None:
    await page.evaluate(
        r"""
        (() => {
          const select = [...document.querySelectorAll('select')]
            .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
          if (select && select.value !== 'naverchzzk') {
            select.value = 'naverchzzk';
            select.dispatchEvent(new Event('input', { bubbles: true }));
            select.dispatchEvent(new Event('change', { bubbles: true }));
          }
        })()
        """
    )


async def collect_scrolling(
    page,
    url: str,
    max_items: int,
    max_scrolls: int,
    delay_seconds: float,
    *,
    row_kind: str = "generic",
    allowed_platforms: set[str] | None = None,
) -> dict:
    await page.get(url)
    await asyncio.sleep(max(6.0, delay_seconds))
    if row_kind in {"category", "follower"}:
        await set_naverchzzk_platform(page)
        await asyncio.sleep(delay_seconds)
    seen: dict[str, dict] = {}
    snapshots: list[dict] = []
    stagnant = 0
    last_count = 0
    latest = await evaluate_page(page)
    for scroll_idx in range(max_scrolls + 1):
        latest = await evaluate_page(page)
        for row in latest.get("channel_anchors", []):
            href = row.get("href") or ""
            platform, channel_id = extract_channel_ref(href)
            key = channel_id or href
            if not key:
                continue
            if allowed_platforms and platform not in allowed_platforms:
                continue
            row_text = (row.get("anchor_text") or "") if row_kind == "category" else (row.get("row_text") or row.get("anchor_text") or "")
            parsed = {}
            if row_kind == "category":
                parsed = parse_category_row_text(row_text)
            elif row_kind == "follower":
                parsed = parse_follower_row_text(row_text)
            seen[key] = {
                "platform": platform,
                "source_url": url,
                "channel_id": channel_id,
                "channel_url": href,
                "channel_name": parsed.get("channel_name") or row.get("anchor_text") or None,
                "follower_count": parsed.get("follower_count") if row_kind == "follower" else None,
                "source_rank": parsed.get("source_rank") or extract_rank(row_text),
                "stream_hours": parsed.get("stream_hours"),
                "peak_viewers": parsed.get("peak_viewers"),
                "avg_viewers": parsed.get("avg_viewers"),
                "viewership": parsed.get("viewership"),
                "row_text_sample": row_text[:500],
            }
        snapshots.append({
            "scroll_idx": scroll_idx,
            "unique_channels": len(seen),
            "anchor_count": latest.get("channel_anchor_count"),
            "boundary": latest.get("boundary"),
        })
        boundary = latest.get("boundary", {})
        if boundary.get("checkpoint_detected") or boundary.get("rate_limited_detected"):
            break
        if len(seen) >= max_items:
            break
        if len(seen) == last_count:
            stagnant += 1
        else:
            stagnant = 0
            last_count = len(seen)
        if stagnant >= 4:
            break
        await page.evaluate("window.scrollBy(0, Math.max(700, window.innerHeight * 0.85))")
        await asyncio.sleep(delay_seconds)
    rows = list(seen.values())
    rows.sort(key=lambda x: (x.get("source_rank") is None, x.get("source_rank") or 999999, x.get("channel_name") or ""))
    return {"page_summary": latest, "scroll_snapshots": snapshots, "rows": rows[:max_items]}


def boundary_signal(summary: dict) -> str | None:
    b = summary.get("boundary") or {}
    if b.get("rate_limited_detected"):
        return "http_429_or_rate_limit"
    if b.get("checkpoint_detected"):
        return "checkpoint_or_challenge"
    if b.get("enterprise_required_likely"):
        return "enterprise_membership_required"
    if b.get("login_required_likely") and not summary.get("content_signals", {}).get("has_softcon"):
        return "login_or_permission_required"
    return None


def write_charles_protocol(run_root: Path, target_id: str, url: str, summary: dict, best_path: str, collection_plan: dict | None) -> None:
    signal = boundary_signal(summary)
    scout = {
        "url": url,
        "target_id": target_id,
        "generated_at": now_iso(),
        "tool": "codex_browser_profile_summary",
        "transport": "nodriver_existing_approved_profile_visible_chrome",
        "save_raw": False,
        "save_screenshot": False,
        "secret_values_logged": False,
        "final_url": summary.get("final_url"),
        "title": summary.get("title"),
        "body_text_length": summary.get("body_text_length"),
        "content_signals": summary.get("content_signals"),
        "boundary": summary.get("boundary"),
        "boundary_signal": signal,
        "visible_text_sample": summary.get("visible_text_sample"),
        "metric_lines": summary.get("metric_lines", [])[:80],
        "channel_anchor_count": summary.get("channel_anchor_count"),
    }
    protocol = {
        "target_id": target_id,
        "target_url": url,
        "best_path": best_path if not signal else "manual_review",
        "pre_check": {
            "gate_status": "profile_cleared" if not signal else "restricted",
            "boundary_signal": signal,
            "profile_required": True,
            "profile_type": "browser_profile",
            "secret_values_logged": False,
        },
        "diagnostic_findings": {
            "title": summary.get("title"),
            "final_url": summary.get("final_url"),
            "content_signals": summary.get("content_signals"),
            "boundary": summary.get("boundary"),
        },
        "profile_required": True,
        "collection_plan": collection_plan if not signal else None,
        "verification": {"preserve_not_verifiable": True},
        "source_paths": {
            "scout_report": f"10_charles/{target_id}.scout_report.json",
            "protocol": f"10_charles/{target_id}.protocol.json",
        },
    }
    write_json(run_root / "10_charles" / f"{target_id}.scout_report.json", scout)
    write_json(run_root / "10_charles" / f"{target_id}.protocol.json", protocol)


def write_review(run_root: Path, target_id: str, summary: dict, rows: list[dict] | None, approved: bool) -> None:
    signal = boundary_signal(summary)
    row_count = len(rows or [])
    verdict = "COLLECT_APPROVED_AND_EXECUTED" if approved and not signal else "STOP_BOUNDARY"
    text = "\n".join([
        f"# Target Review - {target_id}",
        "",
        f"- generated_at: {now_iso()}",
        f"- verdict: {verdict}",
        f"- best_path: {'browser_dom_extraction' if not signal else 'manual_review'}",
        f"- boundary_signal: {signal or 'null'}",
        f"- title: {summary.get('title')}",
        f"- final_url: {summary.get('final_url')}",
        f"- rows_observed: {row_count}",
        f"- operator_collection_approval: {'recorded_from_user_start_collection_instruction' if approved else 'not_used_due_boundary'}",
        "",
        "## Boundary",
        "",
        "- No cookie, localStorage, sessionStorage, auth header, raw HTML, or screenshot was read or persisted.",
        "- CaseResult/Disclosure/PublicDemo promotion was not performed.",
    ])
    path = run_root / "20_review" / f"{target_id}.review_note.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_inspect(run_root: Path, target_id: str, url: str, summary: dict, rows: list[dict] | None) -> None:
    signal = boundary_signal(summary)
    data = {
        "version": "operator-orchestrated-browser-inspect-v1",
        "generated_at": now_iso(),
        "target_id": target_id,
        "target_url": url,
        "transport_attempted": "nodriver_existing_approved_profile_visible_chrome",
        "profile_provided": True,
        "boundary_signals": [] if not signal else [{
            "source": "browser_dom",
            "signal": signal,
            "severity": "stop",
            "action": "stopped" if signal else "none",
        }],
        "sample_records": (rows or [])[:5],
        "row_count_observed": len(rows or []),
        "inspect_recommendation": "collect_allowed" if not signal else "do_not_collect",
    }
    write_json(run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json", data)


def subject_record(summary: dict) -> dict:
    text = "\n".join(summary.get("metric_lines") or [])
    title = summary.get("title") or ""
    channel_name = title.split("|")[0].strip() if "|" in title else "김달수 Dalsu"
    follower_count = first_int_after("팔로워", text) or extract_followers(text)
    peak_viewers = first_int_after("최고 시청자", text)
    avg_viewers = first_int_after("평균 시청자", text)
    viewership = first_int_after("뷰어십", text)
    stream_hours = first_int_after("방송 시간", text)
    max_chat = first_int_after("최고 채팅", text) or first_int_after("최대 채팅", text)
    avg_chat = first_int_after("평균 채팅", text)
    return {
        "run_id": RUN_ID,
        "case_id": CASE_ID,
        "streamer_key": STREAMER_KEY,
        "platform": "chzzk",
        "platform_channel_id": SUBJECT_ID,
        "channel_name": channel_name,
        "channel_url": f"https://chzzk.naver.com/{SUBJECT_ID}",
        "follower_count": follower_count,
        "stream_hours": stream_hours,
        "peak_viewers": peak_viewers,
        "avg_viewers": avg_viewers,
        "viewership": viewership,
        "max_chat_6m": max_chat,
        "avg_chat_6m": avg_chat,
        "category_1": "리그 오브 레전드" if "리그 오브 레전드" in text or "리그 오브 레전드" in (summary.get("visible_text_sample") or "") else None,
        "collected_at": now_iso(),
        "raw_record_path": "40_arthur_collect/softcon_subject_channel_current_stats/combined.json",
        "disclosure_tag": "red",
        "parse_status": "partial" if any(v is None for v in [follower_count, peak_viewers, avg_viewers, viewership]) else "ok",
        "missing_reason": None,
        "boundary_signal": boundary_signal(summary),
        "response_hash": sha256_text(json.dumps({
            "title": summary.get("title"),
            "metric_lines": summary.get("metric_lines", [])[:120],
        }, ensure_ascii=False)),
        "metric_lines": summary.get("metric_lines", [])[:120],
    }


def normalize_softcon_rows(rows: list[dict], target_id: str, source_url: str, raw_record_path: str) -> list[dict]:
    out = []
    for idx, row in enumerate(rows, start=1):
        channel_id = row.get("channel_id")
        item = {
            "run_id": RUN_ID,
            "source_name": "SOFTC.ONE",
            "source_url": source_url,
            "request_url": source_url,
            "platform": "chzzk",
            "platform_source": row.get("platform"),
            "channel_id": channel_id,
            "channel_hash": channel_id,
            "channel_name": row.get("channel_name"),
            "channel_url": row.get("channel_url"),
            "follower_count": row.get("follower_count"),
            "follower_rank": row.get("source_rank") or idx,
            "source_rank": row.get("source_rank") or idx,
            "primary_category": "리그 오브 레전드" if target_id == "softcon_chzzk_lol_population_monthly" else None,
            "category_basis": "SOFTC.ONE category page" if target_id == "softcon_chzzk_lol_population_monthly" else None,
            "aggregation_window_start": None,
            "aggregation_window_end": None,
            "total_stream_hours": row.get("stream_hours"),
            "peak_viewers": row.get("peak_viewers"),
            "avg_viewers": row.get("avg_viewers"),
            "viewership": row.get("viewership"),
            "raw_record_path": raw_record_path,
            "collected_at": now_iso(),
            "disclosure_tag": "red",
            "parse_status": "ok" if channel_id and row.get("channel_name") else "partial",
            "missing_reason": None,
            "boundary_signal": None,
            "response_hash": sha256_text(json.dumps(row, ensure_ascii=False)),
            "row_text_sample": row.get("row_text_sample"),
        }
        out.append(item)
    return out


def write_collection(run_root: Path, target_id: str, source_url: str, summary: dict, rows: list[dict], normalized: list[dict]) -> None:
    out_dir = run_root / "40_arthur_collect" / target_id
    out_dir.mkdir(parents=True, exist_ok=True)
    signal = boundary_signal(summary)
    meta = {
        "run_id": RUN_ID,
        "target_id": target_id,
        "collection_method": "browser_dom_extraction",
        "transport": "nodriver_existing_approved_profile_visible_chrome",
        "profile_used": True,
        "source_url": source_url,
        "collected_at": now_iso(),
        "disclosure_tag": "red",
        "items_collected": len(rows),
        "pages_fetched": 1,
        "requests_made": 1,
        "boundary_signals": [] if not signal else [signal],
        "secret_values_logged": False,
        "raw_html_saved": False,
        "screenshot_saved": False,
    }
    write_json(out_dir / "_meta.json", meta)
    write_json(out_dir / "combined.json", {
        "run_id": RUN_ID,
        "target_id": target_id,
        "source_url": source_url,
        "page_summary": {
            "final_url": summary.get("final_url"),
            "title": summary.get("title"),
            "body_text_length": summary.get("body_text_length"),
            "content_signals": summary.get("content_signals"),
            "boundary": summary.get("boundary"),
        },
        "items": rows,
        "normalized": normalized,
        "verification": {
            "parse_status": "blocked" if signal else ("ok" if rows else "empty"),
            "boundary_signal": signal,
            "dedup_key": "channel_url" if target_id != "softcon_subject_channel_current_stats" else "platform_channel_id",
        },
    })
    write_jsonl(out_dir / "items.jsonl", rows)
    if normalized:
        write_csv(out_dir / "normalized.csv", normalized, sorted({k for r in normalized for k in r.keys()}))


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--follower-max-items", type=int, default=1100)
    parser.add_argument("--category-max-items", type=int, default=700)
    parser.add_argument("--max-scrolls", type=int, default=45)
    parser.add_argument("--delay-seconds", type=float, default=2.5)
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        return 2

    run_root = Path(args.run_root)
    profile_dir = Path(args.profile_dir)
    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=str(profile_dir))
    try:
        page = await browser.get("about:blank")

        subject_summary = await visit(page, SUBJECT_URL, wait_seconds=10)
        write_charles_protocol(run_root, "softcon_subject_channel_current_stats", SUBJECT_URL, subject_summary, "browser_dom_extraction", {"items": 1, "source": "visible_dom_metrics"})
        subject = subject_record(subject_summary)
        write_inspect(run_root, "softcon_subject_channel_current_stats", SUBJECT_URL, subject_summary, [subject])
        write_review(run_root, "softcon_subject_channel_current_stats", subject_summary, [subject], approved=True)
        write_collection(run_root, "softcon_subject_channel_current_stats", SUBJECT_URL, subject_summary, [subject], [subject])
        await asyncio.sleep(args.delay_seconds)

        category = await collect_scrolling(
            page,
            LOL_CATEGORY_URL,
            args.category_max_items,
            args.max_scrolls,
            args.delay_seconds,
            row_kind="category",
            allowed_platforms={"naverchzzk"},
        )
        category_rows = normalize_softcon_rows(
            category["rows"],
            "softcon_chzzk_lol_population_monthly",
            LOL_CATEGORY_URL,
            "40_arthur_collect/softcon_chzzk_lol_population_monthly/combined.json",
        )
        write_charles_protocol(run_root, "softcon_chzzk_lol_population_monthly", LOL_CATEGORY_URL, category["page_summary"], "browser_dom_extraction", {"max_items": args.category_max_items, "source": "category_ranking_dom_scroll"})
        write_inspect(run_root, "softcon_chzzk_lol_population_monthly", LOL_CATEGORY_URL, category["page_summary"], category_rows)
        write_review(run_root, "softcon_chzzk_lol_population_monthly", category["page_summary"], category_rows, approved=True)
        write_collection(run_root, "softcon_chzzk_lol_population_monthly", LOL_CATEGORY_URL, category["page_summary"], category["rows"], category_rows)
        await asyncio.sleep(args.delay_seconds)

        follower = await collect_scrolling(
            page,
            FOLLOWER_URL,
            args.follower_max_items,
            args.max_scrolls,
            args.delay_seconds,
            row_kind="follower",
            allowed_platforms={"naverchzzk"},
        )
        follower_rows = normalize_softcon_rows(
            follower["rows"],
            "softcon_chzzk_follower_ranking_enterprise",
            FOLLOWER_URL,
            "40_arthur_collect/softcon_chzzk_follower_ranking_enterprise/combined.json",
        )
        write_charles_protocol(run_root, "softcon_chzzk_follower_ranking_enterprise", FOLLOWER_URL, follower["page_summary"], "browser_dom_extraction", {"max_items": args.follower_max_items, "source": "follower_ranking_dom_scroll"})
        write_inspect(run_root, "softcon_chzzk_follower_ranking_enterprise", FOLLOWER_URL, follower["page_summary"], follower_rows)
        write_review(run_root, "softcon_chzzk_follower_ranking_enterprise", follower["page_summary"], follower_rows, approved=True)
        write_collection(run_root, "softcon_chzzk_follower_ranking_enterprise", FOLLOWER_URL, follower["page_summary"], follower["rows"], follower_rows)

        summary = {
            "subject_boundary": boundary_signal(subject_summary),
            "subject_parse_status": subject.get("parse_status"),
            "category_boundary": boundary_signal(category["page_summary"]),
            "category_rows": len(category_rows),
            "follower_boundary": boundary_signal(follower["page_summary"]),
            "follower_rows": len(follower_rows),
        }
        write_json(run_root / "40_arthur_collect" / "_softcon_p1_summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
