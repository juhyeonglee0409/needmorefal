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
      return JSON.stringify({
        before,
        after: select ? select.value : null,
        options: select ? [...select.options].map(o => ({ value: o.value, text: (o.textContent || '').trim() })) : []
      });
    })()
    """


def snapshot_expression() -> str:
    return r"""
    (() => {
      const norm = s => (s || '').replace(/\s+/g, ' ').trim();
      const body = norm(document.body?.innerText || '');
      const html = document.documentElement?.innerHTML || '';
      const anchors = [...document.querySelectorAll('a[href*="/channel/naverchzzk/"]')].map(a => ({
        href: a.href,
        text: norm(a.innerText || a.textContent || '')
      }));
      const htmlMatches = [...html.matchAll(/\/channel\/naverchzzk\/([a-f0-9]{20,})/g)].map(m => ({
        channel_id: m[1],
        index: m.index
      }));
      const buttons = [...document.querySelectorAll('button,a')]
        .map(el => ({
          tag: el.tagName.toLowerCase(),
          text: norm(el.innerText || el.textContent || '').slice(0, 80),
          href: el.href || null
        }))
        .filter(x => x.text)
        .filter(x => /(csv|다운로드|download|더보기|다음|next|이전|prev|페이지|\b1\b|\b2\b|\b3\b)/i.test(x.text))
        .slice(0, 80);
      return JSON.stringify({
        href: location.href,
        title: document.title,
        body_text_length: body.length,
        channel_anchor_count: anchors.length,
        sample_anchors: anchors.slice(0, 20),
        html_link_count: htmlMatches.length,
        html_link_samples: htmlMatches.slice(0, 20),
        buttons,
        lines_sample: (document.body?.innerText || '').split(/\n+/).map(norm).filter(Boolean).slice(0, 120)
      });
    })()
    """


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wait-seconds", type=float, default=6.0)
    parser.add_argument("--scrolls", type=int, default=6)
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
        snapshots = []
        for idx in range(args.scrolls + 1):
            snap = await eval_json(page, snapshot_expression())
            snap["scroll_idx"] = idx
            snapshots.append(snap)
            await page.evaluate("window.scrollBy(0, Math.max(900, window.innerHeight * 0.9))")
            await asyncio.sleep(args.wait_seconds)
        result = {
            "generated_at": now_iso(),
            "url": URL,
            "platform": platform,
            "snapshots": snapshots,
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
