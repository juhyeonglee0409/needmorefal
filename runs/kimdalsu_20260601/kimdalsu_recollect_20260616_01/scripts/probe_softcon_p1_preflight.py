from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE = "https://viewership.softc.one"
SUBJECT_ID = "dcbccbf2d8e2a1b095244c5856d3613a"
KST = timezone(timedelta(hours=9))

TARGETS = {
    "subject": f"{BASE}/channel/naverchzzk/{SUBJECT_ID}",
    "lol_category": f"{BASE}/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C/softconeranking",
    "follower": f"{BASE}/ranking/followers?type=naverchzzk",
}


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


async def evaluate(page) -> dict:
    payload = await page.evaluate(
        r"""
        (() => {
          const norm = s => (s || '').replace(/\s+/g, ' ').trim();
          const body = norm(document.body?.innerText || '');
          const lines = (document.body?.innerText || '')
            .split(/\n+/)
            .map(norm)
            .filter(Boolean);
          const channelAnchors = [...document.querySelectorAll('a[href*="/channel/"]')]
            .map(a => ({ href: a.href, text: norm(a.innerText || a.textContent || '') }))
            .filter(x => x.href)
            .slice(0, 20);
          const followerSelect = [...document.querySelectorAll('select')]
            .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
          return JSON.stringify({
            final_url: location.href,
            title: document.title,
            body_text_length: body.length,
            visible_text_sample: body.slice(0, 1200),
            lines_sample: lines.slice(0, 80),
            channel_anchor_count: document.querySelectorAll('a[href*="/channel/"]').length,
            channel_anchors: channelAnchors,
            follower_select_value: followerSelect ? followerSelect.value : null,
            boundary: {
              checkpoint_detected: /(checkpoint|challenge|captcha|vercel|just a moment|보안 확인|브라우저를 확인)/i.test(body),
              rate_limited_detected: /(429|rate limit|too many requests|요청이 너무 많)/i.test(body),
              login_required_likely: /(login|sign in|로그인|권한|인증)/i.test(body),
              enterprise_required_likely: /(ENTERPRISE|높은 등급의 멤버십|멤버십이 필요|이용 가능합니다)/i.test(body)
            }
          });
        })()
        """
    )
    return json.loads(payload)


async def set_followers_platform(page) -> dict:
    payload = await page.evaluate(
        r"""
        (() => {
          const select = [...document.querySelectorAll('select')]
            .find(s => [...s.options].some(o => o.value === 'naverchzzk'));
          if (select && select.value !== 'naverchzzk') {
            select.value = 'naverchzzk';
            select.dispatchEvent(new Event('input', { bubbles: true }));
            select.dispatchEvent(new Event('change', { bubbles: true }));
          }
          return JSON.stringify({
            href: location.href,
            selected: select ? select.value : null
          });
        })()
        """
    )
    return json.loads(payload)


async def probe_target(browser, target_id: str, url: str, wait_seconds: float) -> dict:
    page = await browser.get(url)
    await asyncio.sleep(wait_seconds)
    extra = {}
    if target_id == "follower":
        extra["platform_switch"] = await set_followers_platform(page)
        await asyncio.sleep(wait_seconds)
    summary = await evaluate(page)
    return {
        "target_id": target_id,
        "requested_url": url,
        "probed_at": now_iso(),
        "summary": summary,
        "extra": extra,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wait-seconds", type=float, default=8.0)
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
        results = {
            "generated_at": now_iso(),
            "profile_dir": str(Path(args.profile_dir)),
            "targets": [],
        }
        for target_id, url in TARGETS.items():
            result = await probe_target(browser, target_id, url, args.wait_seconds)
            results["targets"].append(result)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
