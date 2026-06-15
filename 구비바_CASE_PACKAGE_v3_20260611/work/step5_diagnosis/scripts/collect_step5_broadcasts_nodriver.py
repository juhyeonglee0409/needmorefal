"""Collect Step 5 broadcast-history CSVs through nodriver.

This collector reads rendered SOFTC.ONE /streams pages in a real Chrome session.
It does not read or persist cookies, localStorage, session tokens, raw HTML, or
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


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent.parent
COHORT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected"
OUTPUT_DIR = COHORT_DIR / "broadcast_samples"
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def load_full_targets() -> tuple[list[dict[str, str]], int]:
    main = [
        {"group": "T1", "channelId": row["channelId"], "name": row.get("channel_name", "")}
        for row in read_csv(COHORT_DIR / "cohort_final_main_general_game.csv")
        if truthy(row.get("final_include"))
    ]
    aux = [
        {"group": "T2", "channelId": row["channelId"], "name": row.get("channel_name", "")}
        for row in read_csv(COHORT_DIR / "cohort_final_aux_virtual.csv")
        if truthy(row.get("final_include"))
    ]
    return main + aux, len(main) + len(aux)


def load_sample_targets() -> tuple[list[dict[str, str]], int]:
    spec_path = PACKAGE_ROOT / "data" / "cohort" / "specs" / "구비바_§5_broadcast_sample_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    targets: list[dict[str, str]] = []
    for key, rows in (spec.get("samples") or {}).items():
        group = "T1" if key.startswith("T1") else "T2"
        for row in rows:
            targets.append({"group": group, "channelId": row["channelId"], "name": row.get("name", "")})
    return targets, len(targets)


def dedupe_targets(targets: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    chosen: dict[str, dict[str, str]] = {}
    memberships: list[dict[str, str]] = []
    for target in targets:
        channel_id = target["channelId"]
        prev = chosen.get(channel_id)
        if prev is None:
            chosen[channel_id] = target
            continue
        if prev["group"] == "T2" and target["group"] == "T1":
            chosen[channel_id] = target
            memberships.append(
                {
                    "channel_id": channel_id,
                    "name": target.get("name", ""),
                    "dropped_group": "T2",
                    "kept_group": "T1",
                    "reason": "duplicate_channel_id_t1_priority",
                }
            )
        else:
            memberships.append(
                {
                    "channel_id": channel_id,
                    "name": target.get("name", ""),
                    "dropped_group": target["group"],
                    "kept_group": prev["group"],
                    "reason": "duplicate_channel_id_t1_priority",
                }
            )
    return list(chosen.values()), memberships


def load_targets(mode: str) -> tuple[list[dict[str, str]], int, list[dict[str, str]]]:
    if mode == "full":
        targets, before = load_full_targets()
    elif mode == "sample":
        targets, before = load_sample_targets()
    else:
        raise ValueError(f"unsupported mode: {mode}")
    deduped, memberships = dedupe_targets(targets)
    return deduped, before, memberships


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(value))


def out_path_for(target: dict[str, str]) -> Path:
    return OUTPUT_DIR / target["group"] / f"{safe_name(target['channelId'])}_방송별_요약.csv"


def csv_escape_row(row: dict[str, Any]) -> dict[str, str]:
    return {column: "" if row.get(column) is None else str(row.get(column, "")) for column in EXPECTED_COLUMNS}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_escape_row(row))


def append_progress(path: Path, event: dict[str, Any]) -> None:
    record = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def extraction_expression(channel_id: str) -> str:
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


async def evaluate_json(page: Any, expression: str) -> dict[str, Any]:
    value = await page.evaluate(expression)
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict) and value.get("type") == "string" and "value" in value:
        return json.loads(str(value["value"]))
    return json.loads(str(value))


async def collect_one(page: Any, target: dict[str, str], wait_ms: int) -> dict[str, Any]:
    channel_id = target["channelId"]
    url = f"https://viewership.softc.one/channel/naverchzzk/{channel_id}/streams"
    page = await page.browser.get(url)
    started = time.monotonic()
    state: dict[str, Any] | None = None
    while (time.monotonic() - started) * 1000 < wait_ms:
        await asyncio.sleep(2)
        state = await evaluate_json(page, extraction_expression(channel_id))
        if state.get("checkpoint"):
            raise RuntimeError("checkpoint")
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
        print("ERROR: nodriver is not installed", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "T1").mkdir(exist_ok=True)
    (OUTPUT_DIR / "T2").mkdir(exist_ok=True)
    progress_path = OUTPUT_DIR / args.progress_name
    manifest_path = OUTPUT_DIR / args.manifest_name
    errors_path = OUTPUT_DIR / args.errors_name
    progress_path.write_text("", encoding="utf-8")

    targets, before_dedupe, memberships = load_targets(args.mode)
    window = targets[args.offset :]
    if args.skip_existing:
        window = [target for target in window if not out_path_for(target).exists()]
    if args.limit is not None:
        window = window[: args.limit]

    append_progress(
        progress_path,
        {
            "event": "start",
            "mode": args.mode,
            "method": "nodriver_dom_browser",
            "candidate_rows_before_dedupe": before_dedupe,
            "unique_targets_after_dedupe": len(targets),
            "attempted_in_this_run": len(window),
            "skip_existing": args.skip_existing,
            "raw_html_saved": False,
            "secret_values_logged": False,
            "cookie_values_read": False,
        },
    )

    successes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    boundary_signal = None
    rng = random.Random(args.seed)
    browser = None

    try:
        browser = await uc.start(headless=False, lang="ko-KR")
        page = await browser.get("about:blank")
        setattr(page, "browser", browser)
        total = len(targets)
        for local_index, target in enumerate(window, start=1):
            ordinal = args.offset + local_index
            progress = f"{ordinal}/{total}"
            try:
                state = await collect_one(page, target, args.wait_ms)
                rows = [row.get("values", {}) for row in state.get("rows", [])]
                output_path = out_path_for(target)
                if rows:
                    write_csv(output_path, rows)
                status = "success" if len(rows) >= args.min_rows else "short_rows"
                record = {
                    "progress": progress,
                    "group": target["group"],
                    "channel_id": target["channelId"],
                    "name": target.get("name", ""),
                    "row_count": len(rows),
                    "status": status,
                    "output_path": str(output_path) if rows else None,
                    "source_url": state.get("url"),
                }
                successes.append(record)
                append_progress(progress_path, {"event": "collected", **record})
                print(json.dumps({"progress": progress, "channelId": target["channelId"], "rowCount": len(rows), "status": status}, ensure_ascii=False))
            except Exception as exc:  # noqa: BLE001
                reason = str(exc)
                record = {
                    "progress": progress,
                    "group": target["group"],
                    "channel_id": target["channelId"],
                    "name": target.get("name", ""),
                    "error": reason,
                }
                errors.append(record)
                append_progress(progress_path, {"event": "error", **record})
                print(json.dumps({"progress": progress, "channelId": target["channelId"], "error": reason}, ensure_ascii=False))
                if reason in {"429", "checkpoint"}:
                    boundary_signal = "checkpoint_or_rate_boundary"
                    break
            if local_index < len(window):
                delay = args.delay_ms + rng.randint(0, max(0, args.jitter_ms))
                await asyncio.sleep(delay / 1000)
    finally:
        if browser is not None:
            try:
                browser.stop()
            except Exception:
                pass

    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mode": args.mode,
        "method": "nodriver_dom_browser",
        "output_dir": str(OUTPUT_DIR),
        "raw_html_saved": False,
        "secret_values_logged": False,
        "cookie_values_read": False,
        "url_pattern": "https://viewership.softc.one/channel/naverchzzk/{channelId}/streams",
        "target_summary": {
            "candidate_rows_before_dedupe": before_dedupe,
            "unique_targets_after_dedupe": len(targets),
            "offset": args.offset,
            "limit": args.limit,
            "attempted_in_this_run": len(window),
            "skipped_existing": args.skip_existing,
        },
        "success_count": sum(1 for item in successes if item["status"] == "success"),
        "short_rows_count": sum(1 for item in successes if item["status"] == "short_rows"),
        "error_count": len(errors),
        "boundary_signal": boundary_signal,
        "deduped_memberships": memberships,
        "successes": successes,
        "errors": errors,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with errors_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["group", "channel_id", "name", "error", "progress"])
        writer.writeheader()
        writer.writerows(errors)
    append_progress(
        progress_path,
        {
            "event": "done",
            "success_count": manifest["success_count"],
            "short_rows_count": manifest["short_rows_count"],
            "error_count": manifest["error_count"],
            "boundary_signal": boundary_signal,
        },
    )
    print(json.dumps({"manifestPath": str(manifest_path), "progressPath": str(progress_path), "errorsPath": str(errors_path), "successCount": manifest["success_count"], "shortRowsCount": manifest["short_rows_count"], "errorCount": manifest["error_count"], "boundarySignal": boundary_signal}, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Step 5 broadcast outputs through nodriver.")
    parser.add_argument("--mode", choices=["full", "sample"], default="full")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--wait-ms", type=int, default=12000)
    parser.add_argument("--delay-ms", type=int, default=10000)
    parser.add_argument("--jitter-ms", type=int, default=5000)
    parser.add_argument("--min-rows", type=int, default=10)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--manifest-name", default="_collection_manifest_nodriver.json")
    parser.add_argument("--errors-name", default="_collection_errors_nodriver.csv")
    parser.add_argument("--progress-name", default="_collection_progress_nodriver.ndjson")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
