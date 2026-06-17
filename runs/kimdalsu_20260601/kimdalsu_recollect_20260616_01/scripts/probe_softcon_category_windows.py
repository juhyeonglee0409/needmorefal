from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


KST = timezone(timedelta(hours=9))
URL = "https://viewership.softc.one/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C/softconeranking"


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


async def eval_json(page, expression: str) -> dict:
    payload = await page.evaluate(expression)
    return json.loads(payload)


def set_platform_expression() -> str:
    return r"""
    (() => {
      const select = [...document.querySelectorAll('select')]
        .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
      const before = select ? select.value : null;
      if (select && select.value !== 'naverchzzk') {
        select.value = 'naverchzzk';
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return JSON.stringify({ before, after: select ? select.value : null });
    })()
    """


def click_window_expression(label: str) -> str:
    safe = json.dumps(label, ensure_ascii=False)
    return rf"""
    (() => {{
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const want = {safe};
      const nodes = [...document.querySelectorAll('button,a,div')];
      const target = nodes.find(el => norm(el.innerText || el.textContent || '') === want);
      if (!target) {{
        return JSON.stringify({{ found: false, href: location.href }});
      }}
      target.click();
      return JSON.stringify({{ found: true, href: location.href, tag: target.tagName.toLowerCase() }});
    }})()
    """


def snapshot_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const body = norm(document.body?.innerText || '');
      const html = document.documentElement?.innerHTML || '';
      const htmlMatches = [...html.matchAll(/\/channel\/naverchzzk\/([a-f0-9]{20,})/g)];
      return JSON.stringify({
        href: location.href,
        title: document.title,
        body_text_length: body.length,
        channel_anchor_count: document.querySelectorAll('a[href*="/channel/naverchzzk/"]').length,
        html_link_count: htmlMatches.length,
        lines_sample: (document.body?.innerText || '').split(/\n+/).map(norm).filter(Boolean).slice(0, 80)
      });
    })()
    """


async def capture_window(page, label: str, wait_seconds: float) -> dict:
    clicked = await eval_json(page, click_window_expression(label))
    await asyncio.sleep(wait_seconds)
    snap = await eval_json(page, snapshot_expression())
    return {"label": label, "clicked": clicked, "snapshot": snap}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wait-seconds", type=float, default=6.0)
    args = parser.parse_args()

    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver not installed", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    browser = await uc.start(headless=False, lang="ko-KR", user_data_dir=str(Path(args.profile_dir)))
    try:
        page = await browser.get(URL)
        await asyncio.sleep(args.wait_seconds)
        platform = await eval_json(page, set_platform_expression())
        await asyncio.sleep(args.wait_seconds)
        baseline = await eval_json(page, snapshot_expression())
        windows = []
        for label in ["지난달", "지난 한달"]:
            windows.append(await capture_window(page, label, args.wait_seconds))
        result = {
            "generated_at": now_iso(),
            "url": URL,
            "platform": platform,
            "baseline": baseline,
            "windows": windows,
        }
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
