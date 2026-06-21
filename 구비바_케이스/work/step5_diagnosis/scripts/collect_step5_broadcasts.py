"""Collect Step 5 broadcast-history CSVs for the Gubiba cohort.

The script prefers a discovered CSV/download endpoint. If direct HTTP cannot
identify a CSV endpoint, it records a bounded failure instead of forcing access.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent.parent
SAMPLE_SPEC = PACKAGE_ROOT / "data" / "cohort" / "specs" / "구비바_§5_broadcast_sample_spec.json"
COHORT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected"
OUTPUT_DIR = COHORT_DIR / "broadcast_samples"
WAF_PROBE = OUTPUT_DIR / "_waf_probe.json"
MANIFEST = OUTPUT_DIR / "_collection_manifest.json"
ERRORS_CSV = OUTPUT_DIR / "_collection_errors.csv"
BASE_URL = "https://viewership.softc.one"
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


@dataclass(frozen=True)
class Target:
    group: str
    channel_id: str
    name: str
    source_url: str
    source: str
    peak_recent_median: str | float | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def make_softc_urls(channel_id: str) -> list[str]:
    return [
        f"{BASE_URL}/channel/{channel_id},naverchzzk",
        f"{BASE_URL}/channel/naverchzzk/{channel_id}",
    ]


def load_sample_targets() -> tuple[list[Target], list[dict[str, Any]], dict[str, Any]]:
    data = json.loads(SAMPLE_SPEC.read_text(encoding="utf-8"))
    raw: list[Target] = []
    for key, group in (("T1_main_general_game", "T1"), ("T2_aux_virtual", "T2")):
        for item in data["samples"][key]:
            raw.append(
                Target(
                    group=group,
                    channel_id=item["channelId"],
                    name=item.get("name", ""),
                    source_url=item.get("url", make_softc_urls(item["channelId"])[0]),
                    source="sample_spec",
                    peak_recent_median=item.get("peak_recent_median"),
                )
            )
    targets, deduped = dedupe_targets_t1_first(raw)
    return targets, deduped, {
        "candidate_rows_before_dedupe": len(raw),
        "unique_targets_after_dedupe": len(targets),
    }


def load_full_targets() -> tuple[list[Target], list[dict[str, Any]], dict[str, Any]]:
    files = [
        ("T1", COHORT_DIR / "cohort_final_main_general_game.csv", "main"),
        ("T2", COHORT_DIR / "cohort_final_aux_virtual.csv", "virtual_peer"),
    ]
    raw: list[Target] = []
    for group, path, expected_group in files:
        for row in read_csv_rows(path):
            if not truthy(row.get("final_include")):
                continue
            channel_id = row.get("channelId", "").strip()
            if not channel_id:
                continue
            raw.append(
                Target(
                    group=group,
                    channel_id=channel_id,
                    name=(row.get("channel_name") or row.get("name") or "").strip(),
                    source_url=make_softc_urls(channel_id)[0],
                    source=expected_group,
                    peak_recent_median=row.get("peak_recent_median"),
                )
            )
    targets, deduped = dedupe_targets_t1_first(raw)
    return targets, deduped, {
        "candidate_rows_before_dedupe": len(raw),
        "unique_targets_after_dedupe": len(targets),
    }


def dedupe_targets_t1_first(raw: Iterable[Target]) -> tuple[list[Target], list[dict[str, Any]]]:
    priority = {"T1": 0, "T2": 1}
    sorted_targets = sorted(raw, key=lambda t: (priority.get(t.group, 9), t.channel_id))
    seen: dict[str, Target] = {}
    deduped: list[dict[str, Any]] = []
    for target in sorted_targets:
        if target.channel_id in seen:
            kept = seen[target.channel_id]
            deduped.append(
                {
                    "channel_id": target.channel_id,
                    "name": target.name,
                    "dropped_group": target.group,
                    "kept_group": kept.group,
                    "reason": "duplicate_channel_id_t1_priority",
                }
            )
            continue
        seen[target.channel_id] = target
    return list(seen.values()), deduped


def load_targets(mode: str) -> tuple[list[Target], list[dict[str, Any]], dict[str, Any]]:
    if mode == "sample":
        return load_sample_targets()
    if mode == "full":
        return load_full_targets()
    raise ValueError(f"unsupported mode: {mode}")


def output_path_for(target: Target) -> Path:
    return OUTPUT_DIR / target.group / f"{target.channel_id}_방송별_요약.csv"


def import_tls_client() -> Any:
    import tls_client  # type: ignore

    return tls_client


def is_waf_text(text: str, status_code: int | None) -> bool:
    head = text[:4000].lower()
    return status_code in {401, 403, 429} or any(
        marker.lower() in head for marker in ("Vercel Security", "Security Checkpoint", "captcha")
    )


def looks_like_csv(text: str) -> bool:
    first_line = text.splitlines()[0] if text.splitlines() else ""
    return "시작 시간" in first_line and "최고 시청자" in first_line


def discover_candidate_paths(html: str) -> list[str]:
    candidates: list[str] = []
    patterns = [
        r"""["']([^"']*(?:csv|download|export|broadcast|history)[^"']*)["']""",
        r"""href=["']([^"']+)["']""",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            value = match.group(1)
            if any(token in value.lower() for token in ("csv", "download", "export", "broadcast", "history")):
                candidates.append(value.replace("\\u002F", "/").replace("\\/", "/"))
    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped[:20]


def session_get(session: Any, url: str, timeout_seconds: int) -> Any:
    try:
        return session.get(url, timeout_seconds=timeout_seconds)
    except TypeError:
        return session.get(url)


def collect_one_tls(session: Any, target: Target, timeout_seconds: int) -> tuple[bool, str, dict[str, Any]]:
    tried: list[dict[str, Any]] = []
    for channel_url in make_softc_urls(target.channel_id):
        response = session_get(session, channel_url, timeout_seconds)
        text = getattr(response, "text", "") or ""
        status_code = getattr(response, "status_code", None)
        if is_waf_text(text, status_code):
            return False, "waf_or_rate_limited", {"status_code": status_code, "url": channel_url}
        if looks_like_csv(text):
            return True, text, {"download_url": channel_url, "mode": "direct_csv"}

        candidates = discover_candidate_paths(text)
        tried.append({"channel_url": channel_url, "status_code": status_code, "candidates": candidates})
        for candidate in candidates:
            download_url = urljoin(channel_url, candidate)
            r2 = session_get(session, download_url, timeout_seconds)
            text2 = getattr(r2, "text", "") or ""
            status2 = getattr(r2, "status_code", None)
            if is_waf_text(text2, status2):
                return False, "waf_or_rate_limited", {"status_code": status2, "url": download_url}
            if looks_like_csv(text2):
                return True, text2, {"download_url": download_url, "mode": "discovered_csv"}
    return False, "csv_endpoint_not_found", {"tried": tried}


def write_errors(rows: list[dict[str, Any]]) -> None:
    fieldnames = ["group", "channel_id", "name", "reason", "detail"]
    with ERRORS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summarize_probe(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"path": str(path), "read_error": str(exc)}
    if path.name == "_waf_probe.json":
        return {"path": str(path), "summary": data.get("summary")}
    if path.name == "_network_probe.json":
        probes = data.get("probes", [])
        return {
            "path": str(path),
            "probe_count": len(probes),
            "raw_html_saved": data.get("rawHtmlSaved"),
            "secret_values_logged": data.get("secretValuesLogged"),
            "pages": [
                {
                    "input_url": item.get("inputUrl"),
                    "final_url": item.get("afterClicks", {}).get("url"),
                    "title": item.get("afterClicks", {}).get("title"),
                    "checkpoint": "Security Checkpoint" in str(item.get("afterClicks", {}).get("title", ""))
                    or "보안 검문소" in str(item.get("afterClicks", {}).get("text", "")),
                }
                for item in probes[:10]
            ],
        }
    return {"path": str(path)}


def record_boundary_manifest(
    args: argparse.Namespace,
    targets: list[Target],
    deduped: list[dict[str, Any]],
    target_summary: dict[str, Any],
) -> int:
    reason = args.boundary_reason
    errors = [
        {
            "group": target.group,
            "channel_id": target.channel_id,
            "name": target.name,
            "reason": reason,
            "detail": "collection_not_attempted_after_waf_and_browser_checkpoint",
        }
        for target in targets
    ]
    write_errors(errors)
    manifest = {
        "generated_at": utc_now(),
        "mode": args.mode,
        "method": "boundary_record",
        "boundary_signal": reason,
        "target_summary": target_summary,
        "target_count": len(targets),
        "success_count": 0,
        "error_count": len(errors),
        "deduped_memberships": deduped,
        "waf_probe": summarize_probe(WAF_PROBE),
        "network_probe": summarize_probe(OUTPUT_DIR / "_network_probe.json"),
        "errors_csv": str(ERRORS_CSV),
        "secret_values_logged": False,
        "raw_html_saved": False,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "boundary_signal": reason, "target_count": len(targets)}, ensure_ascii=False))
    return 0


def run_tls_collection(
    args: argparse.Namespace,
    targets: list[Target],
    deduped: list[dict[str, Any]],
    target_summary: dict[str, Any],
) -> int:
    tls_client = import_tls_client()
    session = tls_client.Session(client_identifier=args.client_identifier, random_tls_extension_order=True)
    errors: list[dict[str, Any]] = []
    successes: list[dict[str, Any]] = []
    consecutive_429 = 0

    for index, target in enumerate(targets, start=1):
        out_path = output_path_for(target)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.overwrite:
            successes.append({"channel_id": target.channel_id, "group": target.group, "path": str(out_path), "status": "existing"})
            continue

        ok, payload, detail = collect_one_tls(session, target, args.timeout_seconds)
        status_code = detail.get("status_code")
        if status_code == 429:
            consecutive_429 += 1
            time.sleep(args.rate_limit_wait_seconds)
            if consecutive_429 >= 3:
                errors.append(
                    {
                        "group": target.group,
                        "channel_id": target.channel_id,
                        "name": target.name,
                        "reason": "consecutive_429_stop",
                        "detail": json.dumps(detail, ensure_ascii=False),
                    }
                )
                break
        else:
            consecutive_429 = 0

        if ok:
            out_path.write_text(payload, encoding="utf-8-sig")
            successes.append({"channel_id": target.channel_id, "group": target.group, "path": str(out_path), "detail": detail})
        else:
            errors.append(
                {
                    "group": target.group,
                    "channel_id": target.channel_id,
                    "name": target.name,
                    "reason": payload,
                    "detail": json.dumps(detail, ensure_ascii=False),
                }
            )
        print(f"[{index}/{len(targets)}] {target.group} {target.channel_id} {target.name}: {'ok' if ok else payload}")
        time.sleep(args.sleep_seconds)

    write_errors(errors)
    manifest = {
        "generated_at": utc_now(),
        "mode": args.mode,
        "method": "tls_client",
        "target_summary": target_summary,
        "target_count": len(targets),
        "success_count": len(successes),
        "error_count": len(errors),
        "deduped_memberships": deduped,
        "successes": successes,
        "errors_csv": str(ERRORS_CSV),
        "secret_values_logged": False,
        "raw_html_saved": False,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "success_count": len(successes), "error_count": len(errors)}, ensure_ascii=False))
    return 0 if len(successes) > 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Step 5 broadcast CSVs.")
    parser.add_argument("--mode", choices=("sample", "full"), default="full")
    parser.add_argument("--method", choices=("tls", "dry-run", "boundary"), default="dry-run")
    parser.add_argument("--client-identifier", default="chrome_120")
    parser.add_argument("--sleep-seconds", type=float, default=2.5)
    parser.add_argument("--rate-limit-wait-seconds", type=float, default=30.0)
    parser.add_argument("--timeout-seconds", type=int, default=25)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--boundary-reason", default="checkpoint")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "T1").mkdir(exist_ok=True)
    (OUTPUT_DIR / "T2").mkdir(exist_ok=True)

    targets, deduped, target_summary = load_targets(args.mode)
    if args.method == "dry-run":
        report = {
            "mode": args.mode,
            "target_summary": target_summary,
            "target_count": len(targets),
            "groups": {group: sum(1 for t in targets if t.group == group) for group in ("T1", "T2")},
            "deduped_memberships": deduped,
            "first_targets": [asdict(t) for t in targets[:5]],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.method == "boundary":
        return record_boundary_manifest(args, targets, deduped, target_summary)

    return run_tls_collection(args, targets, deduped, target_summary)


if __name__ == "__main__":
    raise SystemExit(main())
