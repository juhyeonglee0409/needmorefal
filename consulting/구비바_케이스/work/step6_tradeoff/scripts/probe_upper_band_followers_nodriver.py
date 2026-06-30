"""Probe SOFTC.ONE followers ranking through nodriver.

Saves compact DOM-derived metadata only. Does not read or persist cookies,
localStorage, sessionStorage, auth headers, raw HTML, or screenshots.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path


BASE_URL = "https://viewership.softc.one"
FOLLOWERS_URL = f"{BASE_URL}/ranking/followers?platform=naverchzzk"

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected"
OUT_PATH = OUTPUT_DIR / "_upper_band_followers_nodriver_probe.json"
PROFILE_DIR = PACKAGE_ROOT / "work" / "step4_cohort_collect_prep" / ".pw_profile"


async def main() -> None:
    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": "nodriver",
        "url": FOLLOWERS_URL,
        "profile_dir": str(PROFILE_DIR),
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
    }

    print(f"[nodriver] open {FOLLOWERS_URL}")
    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=PROFILE_DIR)
    try:
        page = await browser.get(FOLLOWERS_URL)
        await asyncio.sleep(12)

        payload = await page.evaluate(
            r"""
            (() => {
              const norm = s => (s || '').replace(/\s+/g, ' ').trim();
              const body = norm(document.body?.innerText || '');
              const links = [...document.querySelectorAll('a[href]')]
                .map(a => ({ text: norm(a.innerText || a.textContent).slice(0, 120), href: a.href }))
                .filter(x => x.href.includes('/channel/') || x.href.includes('chzzk.naver.com'))
                .slice(0, 80);
              const rows = [...document.querySelectorAll('tr, [role="row"], a[href*="/channel/"]')]
                .map((el, i) => ({ i, text: norm(el.innerText || el.textContent).slice(0, 400) }))
                .filter(x => x.text)
                .slice(0, 80);
              const buttons = [...document.querySelectorAll('button,[role="button"]')]
                .map(b => norm(b.innerText || b.textContent))
                .filter(Boolean)
                .slice(0, 80);
              const inputs = [...document.querySelectorAll('input,select')]
                .map(el => ({
                  tag: el.tagName,
                  type: el.getAttribute('type'),
                  value: el.value,
                  text: norm(el.innerText || ''),
                  options: el.tagName === 'SELECT'
                    ? [...el.options].map(o => ({ value: o.value, text: norm(o.textContent || '') }))
                    : []
                }))
                .slice(0, 30);
              return JSON.stringify({
                href: location.href,
                title: document.title,
                checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인|We're verifying your browser/i.test(body),
                rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(body),
                bodyHead: body.slice(0, 1000),
                linkCount: links.length,
                links,
                rows,
                buttons,
                inputs
              });
            })()
            """
        )
        result.update(json.loads(payload))
    finally:
        try:
            browser.stop()
        except Exception:
            pass

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT_PATH),
        "checkpoint": result.get("checkpoint"),
        "rateLimited": result.get("rateLimited"),
        "linkCount": result.get("linkCount"),
        "title": result.get("title"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
