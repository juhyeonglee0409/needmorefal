"""Collect full broadcast histories for unni-channel trajectory matching.

Reuses the proven nodriver DOM extraction from collect_step5_broadcasts_nodriver.py.
Targets: 구비바 (missing 2023-10~2024-01) + top 14 trajectory candidates.

Runbook reference: SOFTC_ONE_RUNBOOK.md
- Route: nodriver + existing approved profile
- Rate: ~1 req/s total
- Full-range: ?startDateTime={iso}&endDateTime={iso}
- DOM 100-row cap: date windowing으로 우회 필요시 적용

Does not read or persist cookies, localStorage, session tokens, raw HTML, or
browser storage values.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_PROFILE_DIR = PACKAGE_ROOT / "work" / "step4_cohort_collect_prep" / ".pw_profile"
OUTPUT_DIR = SCRIPT_DIR / "collected"
TARGET_FILE = SCRIPT_DIR / "targets_unni_trajectory.json"
PROGRESS_PATH = OUTPUT_DIR / "_collection_progress.ndjson"
MANIFEST_PATH = OUTPUT_DIR / "_collection_manifest.json"
ERRORS_PATH = OUTPUT_DIR / "_collection_errors.csv"

DEFAULT_DATE_START_UTC = "2023-10-01T00:00:00.000Z"
DEFAULT_DATE_END_UTC = "2026-06-20T23:59:59.999Z"

EXPECTED_COLUMNS = [
    "시작 시간",
    "종료 시간",
    "카테고리",
    "연령",
    "시작제목",
    "방송 시간",
    "최고 시청자",
    "평균 시청자",
    "전체 채팅수",
    "팔로워 증감",
    "구독자 증감",
]


def load_targets() -> list[dict[str, Any]]:
    data = json.loads(TARGET_FILE.read_text(encoding="utf-8"))
    return data["targets"]


def out_path_for(target: dict[str, Any]) -> Path:
    cid = target["channelId"]
    name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in target.get("name", cid[:12]))
    return OUTPUT_DIR / f"{cid}_{name}_방송별_요약.csv"


def target_url(channel_id: str, start_utc: str, end_utc: str) -> str:
    base = f"https://viewership.softc.one/channel/naverchzzk/{channel_id}/streams"
    params = urlencode({"startDateTime": start_utc, "endDateTime": end_utc})
    return f"{base}?{params}"


def extraction_expression(channel_id: str) -> str:
    """DOM extraction JS — identical to collect_step5_broadcasts_nodriver.py"""
    return r"""
        (() => {
          const channelId = __CHANNEL_ID__;
          const norm = s => (s || '').replace(/\s+/g, ' ').trim();
          const onlyNumber = s => norm(s).replace(/,/g, '');
          const datePrefix = value => {
            const text = norm(value).replace(/\s+\(/, '(');
            return /^\d{2}\.\d{2}/.test(text) ? '2026.' + text : text;
          };
          const streamAnchors = Array.from(document.querySelectorAll('a'))
            .filter(a => a.href && a.href.includes('/channel/naverchzzk/' + channelId + '/streams/') && /[0-9]$/.test(a.href));
          const seen = new Set();
          const rows = [];
          for (const a of streamAnchors) {
            if (seen.has(a.href)) continue;
            seen.add(a.href);
            const leaves = Array.from(a.querySelectorAll('div,span,p')).map((el, i) => ({
              i,
              tag: el.tagName,
              text: norm(el.innerText || el.textContent),
              cls: String(el.className || ''),
              childCount: el.children.length
            })).filter(x => x.text);
            const labelIndex = leaves.findIndex(x => x.text === '카테고리 / 제목');
            const before = labelIndex >= 0 ? leaves.slice(0, labelIndex) : leaves;
            const categoryIndex = before.findIndex(x => x.cls.includes('foreground-40') && x.text);
            const categoryRaw = categoryIndex >= 0 ? before[categoryIndex].text.replace(/^LIVE/, '') : '';
            const titleLeaf = before.slice(Math.max(categoryIndex + 1, 0)).find(x => x.cls.includes('gap-1') && x.text && !x.text.includes('foreground'));
            let title = titleLeaf ? titleLeaf.text : '';
            const adult = title.includes('연령제한') || before.some(x => x.text === '연령제한');
            title = title.replace(/^연령제한/, '').replace('연령제한', '').trim();
            const period = before.find(x => x.text.includes('~') && /\d{2}\.\d{2}/.test(x.text))?.text || '';
            const parts = period.split('~');
            const startTime = datePrefix(parts[0] || '');
            const endTime = parts[1] && parts[1] !== 'LIVE' ? datePrefix(parts[1]) : (parts[1] || '');
            const rootCells = before.filter(x => x.tag === 'DIV' && x.cls.includes('justify-end') && x.text);
            const durationCellIndex = rootCells.findIndex(x => /h$/.test(x.text));
            const cells = durationCellIndex >= 0 ? rootCells.slice(durationCellIndex) : rootCells;
            rows.push({
              streamId: a.href.split('/').pop(),
              values: {
                '시작 시간': startTime,
                '종료 시간': endTime,
                '카테고리': categoryRaw.replace(/,\s*/g, '|'),
                '연령': adult ? '성인' : '전체',
                '시작제목': title,
                '방송 시간': onlyNumber((cells[0]?.text || '').replace(/h$/, '')),
                '최고 시청자': onlyNumber(cells[1]?.text || ''),
                '평균 시청자': onlyNumber(cells[2]?.text || ''),
                '전체 채팅수': onlyNumber(cells[3]?.text || ''),
                '팔로워 증감': onlyNumber(cells[4]?.text || ''),
                '구독자 증감': ''
              }
            });
          }
          const bodyText = norm(document.body?.innerText || '');
          return JSON.stringify({
            url: location.href,
            title: document.title,
            checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인/.test(bodyText),
            rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(bodyText),
            notFound: /존재하지 않는 페이지|404/.test(bodyText),
            rowCount: rows.length,
            rows
          });
        })()
    """.replace("__CHANNEL_ID__", json.dumps(channel_id))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for row in rows:
            cleaned = {col: "" if row.get(col) is None else str(row.get(col, "")) for col in EXPECTED_COLUMNS}
            writer.writerow(cleaned)


def append_progress(event: dict[str, Any]) -> None:
    record = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **event}
    with PROGRESS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


async def evaluate_json(page: Any, expression: str) -> dict[str, Any]:
    value = await page.evaluate(expression)
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict) and value.get("type") == "string" and "value" in value:
        return json.loads(str(value["value"]))
    return json.loads(str(value))


async def collect_one(browser: Any, channel_id: str, args: argparse.Namespace) -> dict[str, Any]:
    url = target_url(channel_id, args.date_start_utc, args.date_end_utc)
    page = await browser.get(url)
    deadline = time.monotonic() + (args.wait_ms / 1000)
    checkpoint_started: float | None = None
    state: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        await asyncio.sleep(2)
        state = await evaluate_json(page, extraction_expression(channel_id))
        if state.get("checkpoint"):
            if checkpoint_started is None:
                checkpoint_started = time.monotonic()
                deadline = max(deadline, checkpoint_started + 30)
            if time.monotonic() < checkpoint_started + 30:
                continue
            raise RuntimeError("checkpoint")
        checkpoint_started = None
        if state.get("rateLimited"):
            raise RuntimeError("429")
        if state.get("notFound"):
            raise RuntimeError("not_found")
        if int(state.get("rowCount") or 0) > 0:
            return state

    if state is None:
        state = await evaluate_json(page, extraction_expression(channel_id))
    return state


async def run(args: argparse.Namespace) -> int:
    try:
        import nodriver as uc
    except ImportError:
        print("ERROR: nodriver is not installed. pip install nodriver", file=sys.stderr)
        return 2

    targets = load_targets()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text("", encoding="utf-8")

    # Skip already collected
    window = [t for t in targets if not out_path_for(t).exists()] if args.skip_existing else targets
    if args.limit:
        window = window[:args.limit]

    append_progress({
        "event": "start",
        "total_targets": len(targets),
        "attempted": len(window),
        "full_range": True,
        "date_start_utc": args.date_start_utc,
        "date_end_utc": args.date_end_utc,
    })

    successes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    boundary_signal = None
    rng = random.Random(42)
    browser = None

    try:
        browser = await uc.start(
            headless=False,
            lang="ko-KR",
            user_data_dir=Path(args.profile_dir).resolve(),
        )

        for i, target in enumerate(window, 1):
            channel_id = target["channelId"]
            name = target.get("name", channel_id[:12])
            try:
                state = await collect_one(browser, channel_id, args)
                rows = [row.get("values", {}) for row in state.get("rows", [])]
                output = out_path_for(target)
                if rows:
                    write_csv(output, rows)
                status = "success" if len(rows) >= 10 else "short_rows"
                record = {
                    "channel_id": channel_id,
                    "name": name,
                    "row_count": len(rows),
                    "status": status,
                    "output": str(output),
                }
                successes.append(record)
                append_progress({"event": "collected", **record})
                print(f"[{i}/{len(window)}] {name}: {len(rows)} rows — {status}")
            except Exception as exc:
                reason = str(exc)
                record = {"channel_id": channel_id, "name": name, "error": reason}
                errors.append(record)
                append_progress({"event": "error", **record})
                print(f"[{i}/{len(window)}] {name}: ERROR — {reason}")
                if reason in {"429", "checkpoint"}:
                    boundary_signal = "checkpoint_or_rate_boundary"
                    break

            if i < len(window):
                delay = args.delay_ms + rng.randint(0, args.jitter_ms)
                await asyncio.sleep(delay / 1000)
    finally:
        if browser is not None:
            try:
                browser.stop()
            except Exception:
                pass

    # Write manifest
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": "nodriver_dom_browser",
        "purpose": "unni_channel_trajectory_matching",
        "output_dir": str(OUTPUT_DIR),
        "profile_dir": args.profile_dir,
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
        "date_range": {
            "startDateTime": args.date_start_utc,
            "endDateTime": args.date_end_utc,
        },
        "target_count": len(targets),
        "attempted": len(window),
        "success_count": sum(1 for s in successes if s["status"] == "success"),
        "short_rows_count": sum(1 for s in successes if s["status"] == "short_rows"),
        "error_count": len(errors),
        "boundary_signal": boundary_signal,
        "successes": successes,
        "errors": errors,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write errors CSV
    with ERRORS_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["channel_id", "name", "error"])
        writer.writeheader()
        writer.writerows(errors)

    append_progress({
        "event": "done",
        "success_count": manifest["success_count"],
        "short_rows_count": manifest["short_rows_count"],
        "error_count": manifest["error_count"],
        "boundary_signal": boundary_signal,
    })

    ok = manifest["success_count"]
    short = manifest["short_rows_count"]
    err = manifest["error_count"]
    print(f"\nDone: {ok} success, {short} short, {err} errors. Boundary: {boundary_signal}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect unni-channel broadcast histories via nodriver.")
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))
    parser.add_argument("--date-start-utc", default=DEFAULT_DATE_START_UTC)
    parser.add_argument("--date-end-utc", default=DEFAULT_DATE_END_UTC)
    parser.add_argument("--wait-ms", type=int, default=15000, help="Page load timeout")
    parser.add_argument("--delay-ms", type=int, default=10000, help="Inter-request delay")
    parser.add_argument("--jitter-ms", type=int, default=5000, help="Random jitter added to delay")
    parser.add_argument("--limit", type=int, help="Max targets to attempt")
    parser.add_argument("--skip-existing", action="store_true", help="Skip already collected channels")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(run(args)))
