"""
구비바 §4 — Playwright CLI Enrichment

브라우저 스크립트(collect_30d_browser.js)의 Python 포트.
Playwright로 실제 브라우저를 띄워 Vercel challenge를 통과하고,
detail page RSC를 파싱하여 enrichment 수행.

첫 실행: 브라우저 열림 → 수동 로그인 → Ctrl+C → 세션 저장됨
이후 실행: --ids 파일 지정 → 자동 enrichment

사용법:
  # 1회: 로그인 세션 설정
  python pw_enrich.py --login

  # enrichment 실행
  python pw_enrich.py --ids data/cohort/collected/gubiba_multipage_scan_ids.json

  # 이어하기 (이미 수집된 건 건너뜀)
  python pw_enrich.py --ids ids.json --resume output.csv

  # 커스텀 날짜 범위
  python pw_enrich.py --ids ids.json --start 2024-01-01 --end 2026-06-15
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(SCRIPT_DIR, "..", ".pw_profile")
BASE_URL = "https://viewership.softc.one"

CSV_FIELDS = [
    "channelId", "platform", "name", "rank", "stream_hours",
    "peak_viewers", "avg_viewers", "viewership", "band",
    "follower", "category_1", "category_1_share",
    "category_2", "category_2_share", "category_3", "category_3_share",
    "total_categories", "is_general_game", "gg_reason",
    "exclude_reason", "collected_at",
]


# ── Ported logic from collect_30d_browser.js ──

def band_label(peak):
    if peak is None:
        return ""
    peak = int(peak)
    if peak <= 15: return "10-15"
    if peak <= 20: return "16-20"
    if peak <= 30: return "21-30"
    if peak <= 40: return "31-40"
    if peak <= 50: return "41-50"
    if peak <= 100: return "51-100"
    if peak <= 200: return "101-200"
    if peak <= 300: return "201-300"
    return "300+"


def classify_gg(row):
    c1 = (row.get("category_1") or "").strip()
    c1s = float(row.get("category_1_share") or 0)
    c2 = (row.get("category_2") or "").strip()
    c2s = float(row.get("category_2_share") or 0)
    c3 = (row.get("category_3") or "").strip()
    c3s = float(row.get("category_3_share") or 0)

    if not c1:
        return "unknown", "no_category_data"
    if c1 in ("종합 게임", "종합게임"):
        return "true", "gg_primary"
    if c1.lower() == "talk" and c1s >= 50:
        return "false", "talk_primary"
    if c1s >= 80:
        return "false", "single_game_dominant"

    pairs = [(c1, c1s), (c2, c2s), (c3, c3s)]
    non_talk = [p for p in pairs if p[0] and p[0].lower() not in ("talk", "") and p[0] not in ("그림/아트", "먹방") and p[1] >= 15]
    if len(non_talk) >= 2:
        return "true", "multi_game"
    if c2 in ("종합 게임", "종합게임") and c2s >= 15:
        return "true", "gg_secondary"

    return "false", "single_game_or_non_game"


def extract_time_series(text, field_name):
    pattern = re.compile(r'\\"' + field_name + r'\\":(\d+)')
    values = [int(m.group(1)) for m in pattern.finditer(text)]
    if values:
        values = values[:math.ceil(len(values) / 2)]
    return values


def parse_detail_rsc(text):
    fol_matches = [int(m.group(1)) for m in re.finditer(r'\\"followerCount\\":(\d+)', text)]
    follower = fol_matches[-1] if fol_matches else None

    # fallback: unescaped JSON format
    if follower is None:
        fol2 = [int(m.group(1)) for m in re.finditer(r'"followerCount":(\d+)', text)]
        follower = fol2[-1] if fol2 else None

    cat_pattern = re.compile(r'\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)')
    categories = [{"name": m.group(1), "viewership": int(m.group(2))} for m in cat_pattern.finditer(text)]

    # fallback
    if not categories:
        cat2 = re.compile(r'"category":"([^"]+)","sumLiveViews":\d+,"viewership":(\d+)')
        categories = [{"name": m.group(1), "viewership": int(m.group(2))} for m in cat2.finditer(text)]

    categories.sort(key=lambda c: c["viewership"], reverse=True)
    total_vs = sum(c["viewership"] for c in categories)

    def share_of(idx):
        if idx >= len(categories) or not total_vs:
            return 0
        return round(categories[idx]["viewership"] / total_vs * 1000) / 10

    ts = {
        "maxLiveViews": extract_time_series(text, "maxLiveViews"),
        "avgLiveViews": extract_time_series(text, "avgLiveViews"),
        "airTime": extract_time_series(text, "airTime"),
    }

    return {
        "follower": follower,
        "category_1": categories[0]["name"] if len(categories) > 0 else "",
        "category_1_share": share_of(0),
        "category_2": categories[1]["name"] if len(categories) > 1 else "",
        "category_2_share": share_of(1),
        "category_3": categories[2]["name"] if len(categories) > 2 else "",
        "category_3_share": share_of(2),
        "total_categories": len(categories),
        "_timeSeries": ts,
    }


def build_detail_url(channel_id, platform, start=None, end=None):
    url = f"{BASE_URL}/channel/{platform}/{channel_id}"
    if start and end:
        from datetime import timezone, timedelta
        kst = timezone(timedelta(hours=9))
        ds = datetime.strptime(start, "%Y-%m-%d").replace(hour=0, minute=0, second=0, tzinfo=kst)
        de = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=kst)
        url += f"?start={start}&end={end}"
        url += f"&startDateTime={ds.isoformat().replace('+09:00', '.000Z')}"
        url += f"&endDateTime={de.isoformat().replace('+09:00', '.000Z')}"
    return url


# ── ID Loading ──

def load_ids(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = []
    items = data if isinstance(data, list) else data.get("channels") or data.get("ids") or data.get("channel_ids") or []

    for item in items:
        if isinstance(item, str):
            parts = item.split(",")
            if len(parts) >= 2:
                channels.append({"channelId": parts[0].strip(), "platform": parts[1].strip()})
            else:
                channels.append({"channelId": item.strip(), "platform": "naverchzzk"})
        elif isinstance(item, dict):
            cid = item.get("channelId") or item.get("id", "")
            if "," in str(cid):
                parts = str(cid).split(",")
                channels.append({"channelId": parts[0].strip(), "platform": parts[1].strip() if len(parts) > 1 else "naverchzzk"})
            else:
                channels.append({"channelId": str(cid), "platform": item.get("platform", "naverchzzk")})

    # dedup
    seen = set()
    unique = []
    for ch in channels:
        if ch["channelId"] not in seen:
            seen.add(ch["channelId"])
            unique.append(ch)

    return unique


def load_resume(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            done.add(row.get("channelId", ""))
    return done


# ── Main ──

def do_login():
    from playwright.sync_api import sync_playwright
    profile = os.path.abspath(PROFILE_DIR)
    os.makedirs(profile, exist_ok=True)

    print(f"[login] Profile: {profile}")
    print("[login] Browser will open. Log in to softc.one, then close the browser.")
    print()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass

        # Vercel challenge auto-solve
        time.sleep(5)
        title = page.title()
        if "Vercel" in title:
            print("[login] Vercel challenge detected, waiting for solve...")
            time.sleep(15)
            try:
                page.reload(wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass

        print("[login] Browser opened. Please log in.")
        print("[login] After login, close the browser window to save session.")
        print("[login] (waiting for browser close...)")

        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        try:
            context.close()
        except Exception:
            pass

    print("[login] Session saved. Run enrichment with --ids next.")


def do_enrich(args):
    import asyncio
    from playwright.async_api import async_playwright

    profile = os.path.abspath(PROFILE_DIR)
    if not os.path.exists(profile):
        print("[error] No saved session. Run with --login first.")
        return

    channels = load_ids(args.ids)
    print(f"[enrich] Loaded {len(channels)} channels from {args.ids}")

    resume_set = set()
    if args.resume:
        resume_set = load_resume(args.resume)
        print(f"[enrich] Resuming: {len(resume_set)} already done")

    pending = [ch for ch in channels if ch["channelId"] not in resume_set]
    print(f"[enrich] Pending: {len(pending)} channels")

    if not pending:
        print("[enrich] Nothing to do.")
        return

    out_path = args.output or args.resume
    if not out_path:
        prefix = "gubiba"
        if args.start and args.end:
            prefix = f"gubiba_{args.start.replace('-','')[:8]}_{args.end.replace('-','')[:8]}"
        out_path = f"{prefix}_enriched_{len(channels)}.csv"

    ts_path = out_path.replace("_enriched_", "_timeseries_").replace(".csv", ".jsonl")
    n_tabs = args.tabs
    delay_s = args.delay / 1000
    total = len(channels)

    async def run():
        write_header = not os.path.exists(out_path) or os.path.getsize(out_path) == 0
        csv_out = open(out_path, "a", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_out, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        ts_out = open(ts_path, "a", encoding="utf-8")

        errors = []
        enriched_count = len(resume_set)
        queue = asyncio.Queue()
        for ch in pending:
            await queue.put(ch)

        async with async_playwright() as p:
            print(f"[enrich] Launching browser ({n_tabs} tabs, {args.delay}ms delay)...")
            context = await p.chromium.launch_persistent_context(
                profile,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            # Solve Vercel challenge on first page
            scout = await context.new_page()
            await scout.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("[enrich] Solving Vercel challenge...")
            try:
                await scout.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass
            await asyncio.sleep(5)
            title = await scout.title()
            if "Vercel" in title:
                print("[enrich] Challenge detected, waiting...")
                await asyncio.sleep(15)
                try:
                    await scout.reload(wait_until="domcontentloaded", timeout=60000)
                except Exception:
                    pass
            await scout.close()

            # Create worker tabs
            pages = []
            for i in range(n_tabs):
                pg = await context.new_page()
                await pg.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                pages.append(pg)

            print(f"[enrich] Ready. {n_tabs} tabs, delay={args.delay}ms")
            print()

            async def worker(wid, page):
                nonlocal enriched_count
                while not queue.empty():
                    try:
                        ch = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    url = build_detail_url(ch["channelId"], ch["platform"], args.start, args.end)
                    try:
                        try:
                            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        except Exception:
                            resp = None
                        await asyncio.sleep(0.3)

                        if resp and resp.status == 429:
                            errors.append({"channelId": ch["channelId"], "error": "429"})
                            print(f"  [T{wid}] 429 - backing off 30s")
                            await asyncio.sleep(30)
                            try:
                                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            except Exception:
                                resp = None
                            await asyncio.sleep(0.3)

                        content = await page.content()

                        if "Vercel Security Checkpoint" in content:
                            print(f"  [T{wid}] Vercel challenge - waiting 15s")
                            await asyncio.sleep(15)
                            try:
                                await page.reload(wait_until="domcontentloaded", timeout=30000)
                            except Exception:
                                pass
                            await asyncio.sleep(3)
                            content = await page.content()

                        detail = parse_detail_rsc(content)
                        is_gg, gg_reason = classify_gg(detail)

                        row = {
                            "channelId": ch["channelId"],
                            "platform": ch["platform"],
                            "name": "",
                            "rank": None,
                            "stream_hours": None,
                            "peak_viewers": ch.get("peak_viewers"),
                            "avg_viewers": ch.get("avg_viewers"),
                            "viewership": ch.get("viewership"),
                            "band": band_label(ch.get("peak_viewers")),
                            "follower": detail["follower"],
                            "category_1": detail["category_1"],
                            "category_1_share": detail["category_1_share"],
                            "category_2": detail["category_2"],
                            "category_2_share": detail["category_2_share"],
                            "category_3": detail["category_3"],
                            "category_3_share": detail["category_3_share"],
                            "total_categories": detail["total_categories"],
                            "is_general_game": is_gg,
                            "gg_reason": gg_reason,
                            "exclude_reason": "",
                            "collected_at": datetime.now().isoformat(),
                        }

                        writer.writerow(row)
                        csv_out.flush()

                        if detail.get("_timeSeries"):
                            ts_record = {
                                "channelId": ch["channelId"],
                                "platform": ch["platform"],
                                **detail["_timeSeries"],
                            }
                            ts_out.write(json.dumps(ts_record, ensure_ascii=False) + "\n")
                            ts_out.flush()

                        enriched_count += 1
                        cat_info = detail["category_1"] or "(none)"
                        fol_info = detail["follower"] or "?"
                        print(f"  [{enriched_count}/{total}] T{wid} {ch['channelId'][:8]}.. fol={fol_info} cat={cat_info} gg={is_gg}")

                    except Exception as e:
                        errors.append({"channelId": ch["channelId"], "error": str(e)})
                        enriched_count += 1
                        print(f"  [{enriched_count}/{total}] T{wid} {ch['channelId'][:8]}.. ERROR: {e}")

                    await asyncio.sleep(delay_s)

            await asyncio.gather(*[worker(i, pages[i]) for i in range(n_tabs)])
            await context.close()

        csv_out.close()
        ts_out.close()

        print()
        print(f"[done] Enriched: {enriched_count}/{total}")
        print(f"[done] Errors: {len(errors)}")
        print(f"[done] Output: {out_path}")
        print(f"[done] TimeSeries: {ts_path}")

        if errors:
            err_path = out_path.replace(".csv", "_errors.json")
            with open(err_path, "w", encoding="utf-8") as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
            print(f"[done] Errors saved: {err_path}")

    asyncio.run(run())


def main():
    parser = argparse.ArgumentParser(description="Playwright CLI Enrichment")
    parser.add_argument("--login", action="store_true", help="Open browser for manual login")
    parser.add_argument("--ids", type=str, help="Path to channel IDs JSON file")
    parser.add_argument("--resume", type=str, help="Path to existing CSV to resume from")
    parser.add_argument("--output", "-o", type=str, help="Output CSV path")
    parser.add_argument("--start", type=str, help="Date range start (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Date range end (YYYY-MM-DD)")
    parser.add_argument("--delay", type=int, default=1000, help="Delay between requests in ms per tab (default: 1000)")
    parser.add_argument("--tabs", type=int, default=4, help="Number of parallel browser tabs (default: 4)")
    args = parser.parse_args()

    if args.login:
        do_login()
    elif args.ids:
        do_enrich(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
