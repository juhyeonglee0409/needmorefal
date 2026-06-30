import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


RUN_ID = "kimdalsu_recollect_20260616_01"
CASE_ID = "kimdalsu_20260601"
STREAMER_KEY = "kimdalsu"
SUBJECT_ID = "dcbccbf2d8e2a1b095244c5856d3613a"
BASE = "https://viewership.softc.one"
SUBJECT_URL = f"{BASE}/channel/naverchzzk/{SUBJECT_ID}"
FOLLOWER_PAGE_URL = f"{BASE}/ranking/followers?type=naverchzzk&page={{page}}"
KST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def to_int(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9]", "", value)
    return int(cleaned) if cleaned else None


def to_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[0-9][0-9,]*(?:\.[0-9]+)?", value)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def exact_index(lines: list[str], label: str, start: int = 0) -> int | None:
    for idx in range(start, len(lines)):
        if lines[idx] == label:
            return idx
    return None


def index_contains(lines: list[str], label: str, start: int = 0) -> int | None:
    for idx in range(start, len(lines)):
        if label in lines[idx]:
            return idx
    return None


def numeric_after(
    lines: list[str],
    label: str,
    *,
    start: int = 0,
    allow_float: bool = False,
    lookahead: int = 6,
    exact: bool = True,
    skip_substrings: tuple[str, ...] = (),
) -> int | float | None:
    finder = exact_index if exact else index_contains
    idx = finder(lines, label, start)
    if idx is None:
        return None
    for candidate in lines[idx + 1 : idx + 1 + lookahead]:
        if any(token in candidate for token in skip_substrings):
            continue
        parsed = to_float(candidate) if allow_float else to_int(candidate)
        if parsed is not None:
            return parsed
    return None


def subject_record(summary: dict) -> dict:
    lines = summary.get("lines") or []
    section_idx = exact_index(lines, "스트리머 요약 데이터") or 0
    follower_section_idx = exact_index(lines, "팔로워") or 0
    follower_count = numeric_after(
        lines,
        "팔로워",
        start=follower_section_idx,
        lookahead=4,
        exact=True,
        skip_substrings=("업데이트",),
    )
    peak_viewers = numeric_after(lines, "동시 최고 시청자", start=section_idx)
    avg_viewers = numeric_after(lines, "평균 시청자", start=section_idx)
    viewership = numeric_after(
        lines,
        "뷰어십 ( 평균 시청자 * 방송시간 )",
        start=section_idx,
        exact=True,
    )
    stream_hours = numeric_after(
        lines,
        "방송 시간",
        start=section_idx,
        allow_float=True,
    )
    max_chat = numeric_after(lines, "6분 최고 채팅", start=section_idx)
    avg_chat = numeric_after(lines, "6분 평균 채팅", start=section_idx)
    channel_name = (summary.get("title") or "").split("|")[0].strip() or "김달수 Dalsu"
    category = "리그 오브 레전드" if any("리그 오브 레전드" in line for line in lines) else None
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
        "category_1": category,
        "collected_at": now_iso(),
        "raw_record_path": "40_arthur_collect/softcon_subject_channel_current_stats/combined.json",
        "disclosure_tag": "red",
        "parse_status": (
            "ok"
            if all(v is not None for v in [follower_count, stream_hours, peak_viewers, avg_viewers, viewership, max_chat, avg_chat])
            else "partial"
        ),
        "missing_reason": None,
        "boundary_signal": None,
        "response_hash": digest(
            {
                "title": summary.get("title"),
                "lines": lines[:140],
            }
        ),
        "metric_lines": lines[:140],
    }


def parse_follower_row_text(text: str) -> dict:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    match = re.match(
        r"^\s*(\d+)\s+(.+?)\s+\d{4}\.\d{2}\.\d{2}\s+\([^)]+\)\s+\d{2}:\d{2}\s+([\d,]+)\s*$",
        normalized,
    )
    if match:
        return {
            "follower_rank": int(match.group(1)),
            "channel_name": match.group(2).strip(),
            "follower_count": to_int(match.group(3)),
        }
    fallback = re.match(r"^\s*(\d+)\s+(.+)$", normalized)
    nums = re.findall(r"\d[\d,]*", normalized)
    return {
        "follower_rank": int(fallback.group(1)) if fallback else None,
        "channel_name": (fallback.group(2).strip() if fallback else normalized)[:160],
        "follower_count": to_int(nums[-1]) if nums else None,
    }


def normalize_follower(row: dict, source_url: str, idx: int) -> dict:
    return {
        "run_id": RUN_ID,
        "source_name": "SOFTC.ONE",
        "source_url": source_url,
        "platform": "chzzk",
        "channel_id": row.get("channel_id"),
        "channel_name": row.get("channel_name"),
        "channel_url": row.get("channel_url"),
        "follower_count": row.get("follower_count"),
        "follower_rank": row.get("follower_rank") or idx,
        "channel_hash": row.get("channel_id"),
        "collected_at": now_iso(),
        "raw_record_path": "40_arthur_collect/softcon_chzzk_follower_ranking_enterprise/combined.json",
        "disclosure_tag": "red",
        "parse_status": "ok" if row.get("follower_count") and row.get("channel_id") else "partial",
        "missing_reason": None,
        "boundary_signal": None,
        "response_hash": digest(row),
        "row_text_sample": row.get("row_text_sample"),
    }


async def eval_json(page, expression: str) -> dict:
    payload = await page.evaluate(expression)
    return json.loads(payload)


def subject_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const lines = (document.body?.innerText || '')
        .split(/\n+/)
        .map(norm)
        .filter(Boolean)
        .slice(0, 260);
      const body = lines.join('\n');
      return JSON.stringify({
        final_url: location.href,
        title: document.title,
        body_text_length: body.length,
        lines,
        boundary: {
          checkpoint_detected: /(Security Checkpoint|checkpoint|captcha|verifying your browser|just a moment|보안 확인|브라우저를 확인)/i.test(body),
          rate_limited_detected: /(429\s+Too Many Requests|Too Many Requests|rate limit|요청이 너무 많)/i.test(body),
          login_required_likely: /(로그인이 필요|login required|sign in to continue|인증이 필요)/i.test(body),
          enterprise_required_likely: /(멤버십이 필요|멤버십 이용 가능|해당 기능은 .* 멤버십 이용 가능)/i.test(body)
        }
      });
    })()
    """


def set_followers_platform_expression() -> str:
    return r"""
    (() => {
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


def follower_rows_expression() -> str:
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
        const anchorText = norm(a.innerText || a.textContent || '');
        rows.push({
          channel_id: m[1],
          channel_url: href,
          anchor_text: anchorText,
          row_text_sample: anchorText
        });
      }
      return JSON.stringify({
        href: location.href,
        title: document.title,
        body_text_length: body.length,
        checkpoint: /(Security Checkpoint|checkpoint|captcha|verifying your browser|just a moment|보안 확인|브라우저를 확인)/i.test(body),
        rate_limited: /(429\s+Too Many Requests|Too Many Requests|rate limit|요청이 너무 많)/i.test(body),
        rows
      });
    })()
    """


def rewrite_subject(run_root: Path, summary: dict, record: dict) -> None:
    target_id = "softcon_subject_channel_current_stats"
    out_dir = run_root / "40_arthur_collect" / target_id
    write_json(
        out_dir / "combined.json",
        {
            "run_id": RUN_ID,
            "target_id": target_id,
            "source_url": SUBJECT_URL,
            "page_summary": {
                "final_url": summary.get("final_url"),
                "title": summary.get("title"),
                "body_text_length": summary.get("body_text_length"),
                "boundary": summary.get("boundary"),
            },
            "items": [record],
            "normalized": [record],
            "verification": {
                "parse_status": record["parse_status"],
                "boundary_signal": record.get("boundary_signal"),
                "dedup_key": "platform_channel_id",
            },
        },
    )
    write_jsonl(out_dir / "items.jsonl", [record])
    write_csv(out_dir / "normalized.csv", [record], sorted(record.keys()))
    meta_path = out_dir / "_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta.update(
        {
            "items_collected": 1,
            "repair_pass": "subject_line_parse",
            "parse_status": record["parse_status"],
            "updated_at": now_iso(),
            "secret_values_logged": False,
            "raw_html_saved": False,
            "screenshot_saved": False,
        }
    )
    write_json(meta_path, meta)
    inspect_path = run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json"
    inspect = json.loads(inspect_path.read_text(encoding="utf-8")) if inspect_path.exists() else {}
    inspect.update({"sample_records": [record], "row_count_observed": 1, "updated_at": now_iso()})
    write_json(inspect_path, inspect)


def write_followers_snapshot(
    run_root: Path,
    rows: list[dict],
    page_summaries: list[dict],
    boundary: str | None,
    *,
    final: bool,
) -> None:
    target_id = "softcon_chzzk_follower_ranking_enterprise"
    start_page = page_summaries[0]["page"] if page_summaries else 1
    end_page = page_summaries[-1]["page"] if page_summaries else 1
    source_url = f"{BASE}/ranking/followers?type=naverchzzk&page={start_page}..{end_page}"
    out_dir = run_root / "40_arthur_collect" / target_id
    normalized = [normalize_follower(row, source_url, i) for i, row in enumerate(rows, start=1)]
    write_json(
        out_dir / "_meta.json",
        {
            "run_id": RUN_ID,
            "target_id": target_id,
            "collection_method": "browser_dom_page_number_extraction",
            "transport": "nodriver_existing_approved_profile_visible_chrome",
            "profile_used": True,
            "source_url": source_url,
            "collected_at": now_iso(),
            "disclosure_tag": "red",
            "items_collected": len(rows),
            "pages_fetched": len(page_summaries),
            "requests_made": len(page_summaries),
            "boundary_signals": [] if not boundary else [boundary],
            "secret_values_logged": False,
            "raw_html_saved": False,
            "screenshot_saved": False,
            "final_snapshot": final,
        },
    )
    write_json(
        out_dir / "combined.json",
        {
            "run_id": RUN_ID,
            "target_id": target_id,
            "source_url": source_url,
            "page_summaries": page_summaries,
            "items": rows,
            "normalized": normalized,
            "verification": {
                "parse_status": "ok" if len(rows) >= 1000 and not boundary else "below_expected_min_rows",
                "expected_min_rows": 1000,
                "actual_rows": len(rows),
                "boundary_signal": boundary,
                "dedup_key": "channel_hash_or_channel_url",
            },
        },
    )
    write_jsonl(out_dir / "items.jsonl", rows)
    write_csv(out_dir / "normalized.csv", normalized, sorted({k for row in normalized for k in row.keys()}))
    if final:
        inspect = {
            "version": "operator-orchestrated-browser-inspect-v1",
            "generated_at": now_iso(),
            "target_id": target_id,
            "target_url": source_url,
            "transport_attempted": "nodriver_existing_approved_profile_visible_chrome",
            "profile_provided": True,
            "boundary_signals": [] if not boundary else [{"source": "browser_dom", "signal": boundary, "severity": "stop", "action": "stopped"}],
            "sample_records": normalized[:5],
            "row_count_observed": len(rows),
            "inspect_recommendation": "collect_allowed" if len(rows) >= 1000 and not boundary else "review_required",
        }
        write_json(run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json", inspect)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--pages", type=int, default=10)
    parser.add_argument("--delay-seconds", type=float, default=2.5)
    parser.add_argument("--progress-file", default="")
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        return 2

    run_root = Path(args.run_root)
    progress_path = (
        Path(args.progress_file)
        if args.progress_file
        else run_root
        / "40_arthur_collect"
        / "softcon_chzzk_follower_ranking_enterprise"
        / "_progress.ndjson"
    )
    if progress_path.exists():
        progress_path.unlink()

    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=str(Path(args.profile_dir)))
    try:
        page = await browser.get(SUBJECT_URL)
        await asyncio.sleep(8)
        subject_summary = await eval_json(page, subject_expression())
        subject = subject_record(subject_summary)
        rewrite_subject(run_root, subject_summary, subject)

        all_rows: dict[str, dict] = {}
        page_summaries: list[dict] = []
        boundary = None
        for page_num in range(args.start_page, args.start_page + args.pages):
            url = FOLLOWER_PAGE_URL.format(page=page_num)
            page = await browser.get(url)
            await asyncio.sleep(max(5.0, args.delay_seconds))
            payload = await eval_json(page, follower_rows_expression())
            page_summary = {
                "page": page_num,
                "url": url,
                "href": payload.get("href"),
                "title": payload.get("title"),
                "rows": len(payload.get("rows") or []),
                "checkpoint": payload.get("checkpoint"),
                "rate_limited": payload.get("rate_limited"),
                "collected_at": now_iso(),
            }
            page_summaries.append(page_summary)
            for row in payload.get("rows") or []:
                parsed = parse_follower_row_text(row.get("row_text_sample") or row.get("anchor_text") or "")
                all_rows.setdefault(
                    row["channel_id"],
                    {
                        "channel_id": row["channel_id"],
                        "channel_url": row["channel_url"],
                        "channel_name": parsed.get("channel_name") or row.get("anchor_text"),
                        "follower_count": parsed.get("follower_count"),
                        "follower_rank": parsed.get("follower_rank"),
                        "row_text_sample": row.get("row_text_sample"),
                    },
                )
            if payload.get("checkpoint"):
                boundary = "checkpoint_or_challenge"
            elif payload.get("rate_limited"):
                boundary = "http_429_or_rate_limit"

            rows = list(all_rows.values())
            rows.sort(key=lambda item: (item.get("follower_rank") is None, item.get("follower_rank") or 999999))
            write_followers_snapshot(run_root, rows, page_summaries, boundary, final=False)
            append_jsonl(
                progress_path,
                {
                    "page": page_num,
                    "rows_seen_this_page": len(payload.get("rows") or []),
                    "unique_rows_total": len(rows),
                    "boundary": boundary,
                    "timestamp": now_iso(),
                },
            )
            if boundary:
                break
            await asyncio.sleep(args.delay_seconds)

        rows = list(all_rows.values())
        rows.sort(key=lambda item: (item.get("follower_rank") is None, item.get("follower_rank") or 999999))
        write_followers_snapshot(run_root, rows, page_summaries, boundary, final=True)
        result = {
            "subject_parse_status": subject["parse_status"],
            "subject_follower_count": subject.get("follower_count"),
            "subject_peak_viewers": subject.get("peak_viewers"),
            "subject_avg_viewers": subject.get("avg_viewers"),
            "follower_pages": len(page_summaries),
            "follower_rows": len(rows),
            "follower_boundary": boundary,
            "progress_file": str(progress_path),
        }
        write_json(run_root / "40_arthur_collect" / "_softcon_repair_summary.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
