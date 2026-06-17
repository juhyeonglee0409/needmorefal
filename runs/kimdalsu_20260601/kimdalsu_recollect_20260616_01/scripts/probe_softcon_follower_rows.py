import argparse
import asyncio
import json
import sys
from pathlib import Path


FOLLOWER_URL = "https://viewership.softc.one/ranking/followers?type=naverchzzk&page=1"


async def evaluate(page) -> dict:
    payload = await page.evaluate(
        r"""
        (() => {
          const norm = s => (s || '').replace(/\s+/g, ' ').trim();
          const rows = [...document.querySelectorAll('a[href*="/channel/naverchzzk/"]')]
            .slice(0, 12)
            .map((a, idx) => {
              const samples = [];
              let node = a;
              for (let depth = 0; depth < 5; depth++) {
                const text = norm(node.innerText || node.textContent || '');
                samples.push({ depth, tag: node.tagName, text });
                if (!node.parentElement) break;
                node = node.parentElement;
              }
              return {
                idx,
                href: a.href,
                anchor_text: norm(a.innerText || a.textContent || ''),
                chain: samples
              };
            });
          return JSON.stringify({
            title: document.title,
            rows
          });
        })()
        """
    )
    return json.loads(payload)


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
        page = await browser.get(FOLLOWER_URL)
        await asyncio.sleep(args.wait_seconds)
        result = await evaluate(page)
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
