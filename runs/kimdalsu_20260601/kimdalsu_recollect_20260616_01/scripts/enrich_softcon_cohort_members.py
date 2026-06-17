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
TARGET_ID = "softcon_cohort_member_profile_enrichment"
KST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
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


def load_population_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    dedup: dict[str, dict] = {}
    for row in rows:
        key = row.get("channel_id") or row.get("channel_url")
        if key:
            dedup.setdefault(key, row)
    return list(dedup.values())


def load_follower_lookup(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        row["channel_id"]: row
        for row in rows
        if row.get("channel_id")
    }


def exact_index(lines: list[str], label: str, start: int = 0) -> int | None:
    for idx in range(start, len(lines)):
        if lines[idx] == label:
            return idx
    return None


def numeric_after(
    lines: list[str],
    label: str,
    *,
    start: int = 0,
    lookahead: int = 6,
    skip_substrings: tuple[str, ...] = (),
) -> int | None:
    idx = exact_index(lines, label, start)
    if idx is None:
        return None
    for candidate in lines[idx + 1 : idx + 1 + lookahead]:
        if any(token in candidate for token in skip_substrings):
            continue
        parsed = to_int(candidate)
        if parsed is not None:
            return parsed
    return None


def extract_recent_category(lines: list[str], fallback: str) -> str:
    idx = exact_index(lines, "카테고리별 뷰어십 그래프")
    if idx is not None:
        for candidate in lines[idx + 1 : idx + 8]:
            if not candidate:
                continue
            if "최근 한달" in candidate:
                continue
            if "%" in candidate:
                continue
            if re.search(r"\d{4}\.\d{2}\.\d{2}", candidate):
                continue
            if re.search(r"^[0-9.,\s]+$", candidate):
                continue
            if len(candidate) > 60:
                continue
            return candidate
    return fallback or ""


def extract_profile_text(lines: list[str], channel_id: str, channel_name: str) -> str:
    for line in lines[:30]:
        if channel_id in line and "|" in line:
            return line
    for line in lines[:30]:
        if channel_name and channel_name in line and "|" in line:
            return line
    return ""


def parse_page_record(source_row: dict, summary: dict, follower_lookup: dict[str, dict]) -> dict:
    lines = summary.get("lines") or []
    channel_id = source_row.get("channel_id") or ""
    channel_name = (summary.get("title") or "").split("|")[0].strip() or source_row.get("channel_name") or ""
    follower_page_row = follower_lookup.get(channel_id, {})
    follower_from_page = numeric_after(
        lines,
        "팔로워",
        lookahead=4,
        skip_substrings=("업데이트",),
    )
    follower_count = follower_from_page or to_int(follower_page_row.get("follower_count")) or to_int(source_row.get("follower_count"))
    recent_category = extract_recent_category(lines, source_row.get("primary_category") or "")
    profile_text = extract_profile_text(lines, channel_id, channel_name)
    missing_fields = []
    if not follower_count:
        missing_fields.append("follower_count")
    if not recent_category:
        missing_fields.append("recent_category")
    if not profile_text:
        missing_fields.append("profile_text")
    parse_status = "ok" if not missing_fields else "partial"
    return {
        "run_id": RUN_ID,
        "cohort_cell_id": source_row.get("cohort_cell_id") or "",
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_url": source_row.get("channel_url") or "",
        "follower_count": follower_count or "",
        "recent_category": recent_category,
        "profile_text": profile_text,
        "is_esports_team": "",
        "is_tournament": "",
        "is_corporate": "",
        "is_virtual": source_row.get("is_virtual") or "",
        "virtual_basis": "",
        "exclude_reason": source_row.get("exclude_reason") or "",
        "collected_at": now_iso(),
        "raw_record_path": f"40_arthur_collect/{TARGET_ID}/combined.json",
        "disclosure_tag": "red",
        "parse_status": parse_status,
        "missing_reason": "" if parse_status == "ok" else "missing_" + "_".join(missing_fields),
        "boundary_signal": "",
        "response_hash": digest({"channel_id": channel_id, "title": summary.get("title"), "lines": lines[:100]}),
    }


def flush_outputs(
    out_dir: Path,
    rows: list[dict],
    page_summaries: list[dict],
    *,
    final: bool,
) -> None:
    write_json(
        out_dir / "_meta.json",
        {
            "run_id": RUN_ID,
            "target_id": TARGET_ID,
            "collection_method": "browser_channel_page_line_parse",
            "transport": "nodriver_existing_approved_profile_visible_chrome",
            "profile_used": True,
            "items_collected": len(rows),
            "requests_made": len(page_summaries),
            "boundary_signals": [],
            "secret_values_logged": False,
            "raw_html_saved": False,
            "screenshot_saved": False,
            "final_snapshot": final,
            "updated_at": now_iso(),
        },
    )
    write_json(
        out_dir / "combined.json",
        {
            "run_id": RUN_ID,
            "target_id": TARGET_ID,
            "source_url": "derived_from:softcon_chzzk_lol_population_monthly.channel_url",
            "items": rows,
            "page_summaries": page_summaries,
            "verification": {
                "parse_status": "ok" if rows and all(row.get("parse_status") == "ok" for row in rows) else "partial",
                "boundary_signal": None,
                "dedup_key": "channel_url",
            },
        },
    )
    write_jsonl(out_dir / "items.jsonl", rows)
    fields = sorted({key for row in rows for key in row.keys()}) if rows else [
        "run_id", "cohort_cell_id", "channel_id", "channel_name", "channel_url",
        "follower_count", "recent_category", "profile_text", "is_esports_team",
        "is_tournament", "is_corporate", "is_virtual", "virtual_basis",
        "exclude_reason", "collected_at", "raw_record_path", "disclosure_tag",
        "parse_status", "missing_reason", "boundary_signal", "response_hash",
    ]
    write_csv(out_dir / "normalized.csv", rows, fields)


async def eval_json(page, expression: str) -> dict:
    payload = await page.evaluate(expression)
    return json.loads(payload)


def page_expression() -> str:
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
          rate_limited_detected: /(429\s+Too Many Requests|Too Many Requests|rate limit|요청이 너무 많)/i.test(body)
        }
      });
    })()
    """


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--tabs", type=int, default=3)
    parser.add_argument("--delay-ms", type=int, default=3000)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        return 2

    run_root = Path(args.run_root)
    population_csv = run_root / "40_arthur_collect" / "softcon_chzzk_lol_population_monthly" / "normalized.csv"
    follower_csv = run_root / "40_arthur_collect" / "softcon_chzzk_follower_ranking_enterprise" / "normalized.csv"
    out_dir = run_root / "40_arthur_collect" / TARGET_ID
    progress_path = out_dir / "_progress.ndjson"
    if progress_path.exists():
        progress_path.unlink()

    population_rows = load_population_rows(population_csv)
    follower_lookup = load_follower_lookup(follower_csv)
    source_rows = population_rows[: args.limit] if args.limit else population_rows

    collected_rows: list[dict] = []
    page_summaries: list[dict] = []
    delay_seconds = args.delay_ms / 1000
    queue: asyncio.Queue[dict] = asyncio.Queue()
    for row in source_rows:
        await queue.put(row)

    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=str(Path(args.profile_dir)))
    try:
        scout = await browser.get("https://viewership.softc.one")
        await asyncio.sleep(5)

        worker_count = 1

        async def worker(worker_id: int) -> None:
            while not queue.empty():
                try:
                    source_row = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                channel_id = source_row.get("channel_id") or ""
                channel_url = source_row.get("channel_url") or ""
                try:
                    page = await browser.get(channel_url)
                    await asyncio.sleep(0.5)
                    summary = await eval_json(page, page_expression())
                    boundary = summary.get("boundary") or {}
                    if boundary.get("checkpoint_detected"):
                        row = {
                            "run_id": RUN_ID,
                            "cohort_cell_id": source_row.get("cohort_cell_id") or "",
                            "channel_id": channel_id,
                            "channel_name": source_row.get("channel_name") or "",
                            "channel_url": channel_url,
                            "follower_count": "",
                            "recent_category": "",
                            "profile_text": "",
                            "is_esports_team": "",
                            "is_tournament": "",
                            "is_corporate": "",
                            "is_virtual": source_row.get("is_virtual") or "",
                            "virtual_basis": "",
                            "exclude_reason": "",
                            "collected_at": now_iso(),
                            "raw_record_path": f"40_arthur_collect/{TARGET_ID}/combined.json",
                            "disclosure_tag": "red",
                            "parse_status": "blocked",
                            "missing_reason": "checkpoint_or_challenge",
                            "boundary_signal": "checkpoint_or_challenge",
                            "response_hash": digest({"channel_id": channel_id, "boundary": "checkpoint_or_challenge"}),
                        }
                    elif boundary.get("rate_limited_detected"):
                        row = {
                            "run_id": RUN_ID,
                            "cohort_cell_id": source_row.get("cohort_cell_id") or "",
                            "channel_id": channel_id,
                            "channel_name": source_row.get("channel_name") or "",
                            "channel_url": channel_url,
                            "follower_count": "",
                            "recent_category": "",
                            "profile_text": "",
                            "is_esports_team": "",
                            "is_tournament": "",
                            "is_corporate": "",
                            "is_virtual": source_row.get("is_virtual") or "",
                            "virtual_basis": "",
                            "exclude_reason": "",
                            "collected_at": now_iso(),
                            "raw_record_path": f"40_arthur_collect/{TARGET_ID}/combined.json",
                            "disclosure_tag": "red",
                            "parse_status": "blocked",
                            "missing_reason": "http_429_or_rate_limit",
                            "boundary_signal": "http_429_or_rate_limit",
                            "response_hash": digest({"channel_id": channel_id, "boundary": "http_429_or_rate_limit"}),
                        }
                    else:
                        row = parse_page_record(source_row, summary, follower_lookup)
                    collected_rows.append(row)
                    page_summaries.append(
                        {
                            "channel_id": channel_id,
                            "channel_url": channel_url,
                            "worker_id": worker_id,
                            "final_url": summary.get("final_url"),
                            "title": summary.get("title"),
                            "body_text_length": summary.get("body_text_length"),
                            "parse_status": row.get("parse_status"),
                            "boundary_signal": row.get("boundary_signal"),
                            "collected_at": row.get("collected_at"),
                        }
                    )
                    append_jsonl(
                        progress_path,
                        {
                            "channel_id": channel_id,
                            "channel_url": channel_url,
                            "worker_id": worker_id,
                            "parse_status": row.get("parse_status"),
                            "boundary_signal": row.get("boundary_signal"),
                            "row": row,
                            "timestamp": now_iso(),
                        },
                    )
                except Exception as exc:
                    row = {
                        "run_id": RUN_ID,
                        "cohort_cell_id": source_row.get("cohort_cell_id") or "",
                        "channel_id": channel_id,
                        "channel_name": source_row.get("channel_name") or "",
                        "channel_url": channel_url,
                        "follower_count": "",
                        "recent_category": "",
                        "profile_text": "",
                        "is_esports_team": "",
                        "is_tournament": "",
                        "is_corporate": "",
                        "is_virtual": source_row.get("is_virtual") or "",
                        "virtual_basis": "",
                        "exclude_reason": "",
                        "collected_at": now_iso(),
                        "raw_record_path": f"40_arthur_collect/{TARGET_ID}/combined.json",
                        "disclosure_tag": "red",
                        "parse_status": "error",
                        "missing_reason": str(exc),
                        "boundary_signal": "",
                        "response_hash": digest({"channel_id": channel_id, "error": str(exc)}),
                    }
                    collected_rows.append(row)
                    page_summaries.append(
                        {
                            "channel_id": channel_id,
                            "channel_url": channel_url,
                            "worker_id": worker_id,
                            "parse_status": "error",
                            "boundary_signal": "",
                            "error": str(exc),
                            "collected_at": row.get("collected_at"),
                        }
                    )
                    append_jsonl(
                        progress_path,
                        {
                            "channel_id": channel_id,
                            "channel_url": channel_url,
                            "worker_id": worker_id,
                            "parse_status": "error",
                            "error": str(exc),
                            "row": row,
                            "timestamp": now_iso(),
                        },
                    )
                await asyncio.sleep(delay_seconds)

        await asyncio.gather(*[worker(idx) for idx in range(1, worker_count + 1)])
    finally:
        try:
            browser.stop()
        except Exception:
            pass

    flush_outputs(out_dir, collected_rows, page_summaries, final=True)
    print(
        json.dumps(
            {
                "target_id": TARGET_ID,
                "input_rows": len(source_rows),
                "collected_rows": len(collected_rows),
                "ok_rows": sum(1 for row in collected_rows if row.get("parse_status") == "ok"),
                "partial_rows": sum(1 for row in collected_rows if row.get("parse_status") == "partial"),
                "error_rows": sum(1 for row in collected_rows if row.get("parse_status") == "error"),
                "blocked_rows": sum(1 for row in collected_rows if row.get("parse_status") == "blocked"),
                "progress_file": str(progress_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
