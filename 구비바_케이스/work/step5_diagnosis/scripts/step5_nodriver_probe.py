"""
§5 nodriver WAF probe — SOFTC.ONE Vercel Security Checkpoint 통과 테스트.

nodriver는 실제 Chrome 바이너리를 자동화하되 navigator.webdriver 등
자동화 흔적을 제거해 봇 탐지를 회피한다.

테스트 대상:
1. 채널 페이지 로드 (checkpoint 통과 여부)
2. /streams 탭 이동 (방송기록 로드 여부)
3. CSV 다운로드 버튼 클릭 (다운로드 발생 여부)

사용법:
  pip install nodriver
  python step5_nodriver_probe.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

CHANNEL_ID = "269edc95873a1ec9fc534851c0783d1f"  # 구비바
BASE_URL = "https://viewership.softc.one"
CHANNEL_URL = f"{BASE_URL}/channel/naverchzzk/{CHANNEL_ID}"
STREAMS_URL = f"{CHANNEL_URL}/streams"

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected" / "broadcast_samples"
PROBE_OUTPUT = OUTPUT_DIR / "_nodriver_probe.json"


async def main():
    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed. Run: pip install nodriver")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": "nodriver",
        "channel_id": CHANNEL_ID,
        "tests": [],
        "secret_values_logged": False,
        "cookie_values_read": False,
        "raw_html_saved": False,
    }

    print("[nodriver] Starting Chrome...")
    browser = await uc.start(
        headless=False,  # 실제 Chrome 창 — headless는 탐지 위험
        lang="ko-KR",
    )

    # ── Test 1: 채널 페이지 로드 ──
    print(f"[nodriver] Navigating to channel page: {CHANNEL_URL}")
    page = await browser.get(CHANNEL_URL)
    await asyncio.sleep(10)  # checkpoint 통과 대기

    title = await page.evaluate("document.title")
    url = await page.evaluate("location.href")
    is_checkpoint = "checkpoint" in (title or "").lower() or "vercel security" in (title or "").lower()
    body_snippet = await page.evaluate("(document.body?.innerText || '').slice(0, 800)")

    test1 = {
        "name": "channel_page_load",
        "url": url,
        "title": title,
        "is_checkpoint": is_checkpoint,
        "body_snippet_length": len(body_snippet or ""),
        "passed": not is_checkpoint and len(body_snippet or "") > 200,
    }
    result["tests"].append(test1)
    print(f"  → title={title}, checkpoint={is_checkpoint}, passed={test1['passed']}")

    if is_checkpoint:
        # checkpoint에 걸렸으면 10초 더 대기 (자동 해결 시도)
        print("[nodriver] Checkpoint detected, waiting 10s more...")
        await asyncio.sleep(10)
        title = await page.evaluate("document.title")
        is_checkpoint = "checkpoint" in (title or "").lower() or "vercel security" in (title or "").lower()
        test1["retry_title"] = title
        test1["retry_passed"] = not is_checkpoint
        print(f"  → retry: title={title}, passed={not is_checkpoint}")

    # ── Test 2: /streams 탭 이동 ──
    if not is_checkpoint:
        print(f"[nodriver] Navigating to streams page: {STREAMS_URL}")
        page = await browser.get(STREAMS_URL)
        await asyncio.sleep(8)

        title2 = await page.evaluate("document.title")
        stream_count = await page.evaluate(
            "Array.from(document.querySelectorAll('a')).filter(a => a.href && a.href.includes('/streams/') && /[0-9]$/.test(a.href)).length"
        )
        has_csv_button = await page.evaluate(
            "!!Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'CSV 다운로드')"
        )

        test2 = {
            "name": "streams_tab_load",
            "url": STREAMS_URL,
            "title": title2,
            "stream_link_count": stream_count,
            "has_csv_button": has_csv_button,
            "passed": (stream_count or 0) > 0,
        }
        result["tests"].append(test2)
        print(f"  → streams={stream_count}, csv_button={has_csv_button}, passed={test2['passed']}")

        # ── Test 3: CSV 다운로드 버튼 클릭 ──
        if has_csv_button:
            print("[nodriver] Clicking CSV 다운로드 button...")
            csv_btn = await page.evaluate("""
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const el = btns.find(b => {
                        const r = b.getBoundingClientRect();
                        return (b.innerText || '').trim() === 'CSV 다운로드' && r.width > 2 && r.height > 2;
                    });
                    if (!el) return null;
                    el.scrollIntoView({block: 'center'});
                    const r = el.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                })()
            """)

            if csv_btn:
                # nodriver의 mouse click
                try:
                    await page.evaluate("""
                        (() => {
                            const btns = Array.from(document.querySelectorAll('button'));
                            const el = btns.find(b => {
                                const r = b.getBoundingClientRect();
                                return (b.innerText || '').trim() === 'CSV 다운로드' && r.width > 2 && r.height > 2;
                            });
                            if (el) el.click();
                            return !!el;
                        })()
                    """)
                    await asyncio.sleep(5)
                    test3 = {"name": "csv_download_click", "button_found": True, "clicked": True}
                except Exception as e:
                    test3 = {"name": "csv_download_click", "button_found": True, "clicked": False, "error": str(e)}
            else:
                test3 = {"name": "csv_download_click", "button_found": False, "clicked": False}

            result["tests"].append(test3)
            print(f"  → csv click: {test3}")

    # ── DOM extraction test (fallback) ──
    if not is_checkpoint and (stream_count or 0) > 0:
        print("[nodriver] Testing DOM row extraction...")
        rows = await page.evaluate("""
            (() => {
                const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
                const anchors = Array.from(document.querySelectorAll('a')).filter(a => a.href && a.href.includes('/streams/') && /[0-9]$/.test(a.href));
                return anchors.slice(0, 5).map(a => ({
                    href: a.href,
                    text: norm(a.innerText || a.textContent).slice(0, 300)
                }));
            })()
        """)
        test4 = {
            "name": "dom_row_extraction",
            "sample_rows": rows,
            "passed": len(rows or []) > 0,
        }
        result["tests"].append(test4)
        print(f"  → extracted {len(rows or [])} sample rows")

    # ── Save result ──
    PROBE_OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[nodriver] Probe result saved to: {PROBE_OUTPUT}")
    print(f"[nodriver] Summary: {len([t for t in result['tests'] if t.get('passed')])} / {len(result['tests'])} tests passed")

    # 브라우저 종료
    try:
        browser.stop()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
