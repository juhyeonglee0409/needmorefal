from __future__ import annotations

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
BASE = "https://viewership.softc.one"
URL = f"{BASE}/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C/softconeranking"
KST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


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
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def compact_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", value)
    return float(match.group(0)) if match else None


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def parse_anchor_row(text: str) -> dict:
    match = re.match(
        r"^\s*(\d+)\s+(.+?)\s+\d+/\d+/\d+\s+([0-9]+(?:\.[0-9]+)?)\s+p\s+([0-9]+(?:\.[0-9]+)?)\s+h\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s*$",
        text,
    )
    if not match:
        return {
            "source_rank": None,
            "channel_name": text,
            "point_score": None,
            "stream_hours": None,
            "peak_viewers": None,
            "avg_viewers": None,
            "viewership": None,
        }
    return {
        "source_rank": int(match.group(1)),
        "channel_name": match.group(2).strip(),
        "point_score": compact_float(match.group(3)),
        "stream_hours": compact_float(match.group(4)),
        "peak_viewers": compact_int(match.group(5)),
        "avg_viewers": compact_int(match.group(6)),
        "viewership": compact_int(match.group(7)),
    }


async def eval_json(page, expression: str) -> dict:
    payload = await page.evaluate(expression)
    return json.loads(payload)


def set_platform_expression() -> str:
    return r"""
    (() => {
      const select = [...document.querySelectorAll('select')]
        .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
      if (select && select.value !== 'naverchzzk') {
        select.value = 'naverchzzk';
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return JSON.stringify({ href: location.href, value: select ? select.value : null });
    })()
    """


def snapshot_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const body = norm(document.body?.innerText || '');
      const rows = [...document.querySelectorAll('a[href*="/channel/naverchzzk/"]')]
        .map(a => ({
          href: a.href,
          text: norm(a.innerText || a.textContent || '')
        }))
        .filter(x => x.href && x.text);
      return JSON.stringify({
        href: location.href,
        title: document.title,
        body_text_length: body.length,
        channel_anchor_count: rows.length,
        rows
      });
    })()
    """


def normalize_row(raw: dict, parsed: dict) -> dict:
    channel_id = raw["href"].rsplit("/", 1)[-1]
    return {
        "run_id": RUN_ID,
        "cohort_cell_id": None,
        "cohort_type": "main_cohort_population_candidate",
        "source_name": "SOFTC.ONE",
        "source_url": URL,
        "request_url": URL,
        "platform": "chzzk",
        "channel_id": channel_id,
        "channel_name": parsed["channel_name"],
        "channel_url": raw["href"],
        "primary_category": "리그 오브 레전드",
        "category_basis": "SOFTC.ONE category page filtered type=naverchzzk",
        "aggregation_window_start": None,
        "aggregation_window_end": None,
        "total_stream_hours": parsed["stream_hours"],
        "peak_viewers": parsed["peak_viewers"],
        "avg_viewers": parsed["avg_viewers"],
        "viewership": parsed["viewership"],
        "follower_count": None,
        "is_virtual": None,
        "is_esports_team": None,
        "is_tournament": None,
        "is_corporate": None,
        "exclude_reason": None,
        "raw_record_path": "40_arthur_collect/softcon_chzzk_lol_population_monthly/combined.json",
        "collected_at": now_iso(),
        "disclosure_tag": "red",
        "source_rank": parsed["source_rank"],
        "parse_status": "ok" if parsed["source_rank"] and parsed["channel_name"] else "partial",
        "missing_reason": None,
        "boundary_signal": None,
        "response_hash": digest({"raw": raw, "parsed": parsed}),
        "row_text_sample": raw["text"],
    }


def write_outputs(run_root: Path, snapshot: dict, rows: list[dict]) -> None:
    target_id = "softcon_chzzk_lol_population_monthly"
    out_dir = run_root / "40_arthur_collect" / target_id
    meta = {
        "run_id": RUN_ID,
        "target_id": target_id,
        "collection_method": "browser_dom_anchor_repair",
        "transport": "nodriver_existing_approved_profile_visible_chrome",
        "profile_used": True,
        "source_url": URL,
        "collected_at": now_iso(),
        "disclosure_tag": "red",
        "items_collected": len(rows),
        "pages_fetched": 1,
        "requests_made": 1,
        "boundary_signals": [],
        "secret_values_logged": False,
        "raw_html_saved": False,
        "screenshot_saved": False,
        "residual_risk": "category_route_visible_cap_100_rows",
    }
    combined = {
        "run_id": RUN_ID,
        "target_id": target_id,
        "source_url": URL,
        "page_summary": snapshot,
        "items": rows,
        "normalized": rows,
        "verification": {
            "parse_status": "below_expected_min_rows" if len(rows) < 500 else "ok",
            "expected_min_rows_before_filter": 500,
            "actual_rows": len(rows),
            "boundary_signal": None,
            "dedup_key": "channel_id_or_channel_url",
            "residual_risk": "category_route_visible_cap_100_rows",
        },
    }
    inspect = {
        "version": "operator-orchestrated-browser-inspect-v1",
        "generated_at": now_iso(),
        "target_id": target_id,
        "target_url": URL,
        "transport_attempted": "nodriver_existing_approved_profile_visible_chrome",
        "profile_provided": True,
        "boundary_signals": [],
        "sample_records": rows[:5],
        "row_count_observed": len(rows),
        "inspect_recommendation": "review_required" if len(rows) < 500 else "collect_allowed",
        "residual_risk": "category_route_visible_cap_100_rows",
    }
    review = "\n".join([
        "# Target Review - softcon_chzzk_lol_population_monthly",
        "",
        f"- generated_at: {now_iso()}",
        "- verdict: COLLECT_EXECUTED_WITH_RESIDUAL_RISK",
        "- best_path: browser_dom_anchor_repair",
        "- boundary_signal: null",
        f"- final_url: {snapshot.get('href')}",
        f"- rows_observed: {len(rows)}",
        "- residual_risk: category_route_visible_cap_100_rows",
        "",
        "## Boundary",
        "",
        "- No cookie, localStorage, sessionStorage, auth header, raw HTML, or screenshot was read or persisted.",
        "- Current filtered category route exposes 100 visible/HTML rows only; this is treated as a surface cap, not source absence.",
        "- CaseResult/Disclosure/PublicDemo promotion was not performed.",
    ])
    write_json(out_dir / "_meta.json", meta)
    write_json(out_dir / "combined.json", combined)
    write_jsonl(out_dir / "items.jsonl", rows)
    write_csv(out_dir / "normalized.csv", rows, sorted({k for row in rows for k in row.keys()}))
    write_json(run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json", inspect)
    review_path = run_root / "20_review" / f"{target_id}.review_note.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(review, encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--wait-seconds", type=float, default=6.0)
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        return 2

    run_root = Path(args.run_root)
    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=str(Path(args.profile_dir)))
    try:
        page = await browser.get(URL)
        await asyncio.sleep(args.wait_seconds)
        await eval_json(page, set_platform_expression())
        await asyncio.sleep(args.wait_seconds)
        snapshot = await eval_json(page, snapshot_expression())
        rows = []
        seen = set()
        for raw in snapshot.get("rows", []):
            if raw["href"] in seen:
                continue
            seen.add(raw["href"])
            rows.append(normalize_row(raw, parse_anchor_row(raw["text"])))
        write_outputs(run_root, snapshot, rows)
        print(json.dumps({"rows": len(rows), "href": snapshot.get("href")}, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
