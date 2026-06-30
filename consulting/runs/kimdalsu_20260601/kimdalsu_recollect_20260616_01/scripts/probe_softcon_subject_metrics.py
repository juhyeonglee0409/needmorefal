import argparse
import asyncio
import json
import sys
from pathlib import Path


SUBJECT_URL = "https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a"


async def evaluate(page) -> dict:
    payload = await page.evaluate(
        r"""
        (() => {
          const norm = s => (s || '').replace(/\s+/g, ' ').trim();
          const lines = (document.body?.innerText || '')
            .split(/\n+/)
            .map(norm)
            .filter(Boolean);
          const nodes = [...document.querySelectorAll('body *')]
            .map((el, idx) => {
              const text = norm(el.innerText || el.textContent || '');
              if (!text || text.length > 120) return null;
              return {
                idx,
                tag: el.tagName,
                text,
                child_count: el.children.length,
              };
            })
            .filter(Boolean)
            .slice(0, 400);
          const metrics = nodes.filter(n => /\d/.test(n.text)).slice(0, 200);
          return JSON.stringify({
            final_url: location.href,
            title: document.title,
            line_count: lines.length,
            lines_sample: lines.slice(0, 200),
            metric_nodes: metrics,
          });
        })()
        """
    )
    return json.loads(payload)


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
        page = await browser.get(SUBJECT_URL)
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
