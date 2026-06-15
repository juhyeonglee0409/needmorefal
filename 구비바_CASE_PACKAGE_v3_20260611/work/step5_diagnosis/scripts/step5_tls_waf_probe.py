"""Step 5 SOFTC.ONE tls-client WAF probe.

Writes a compact probe report without saving raw HTML or cookies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent.parent
OUTPUT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected" / "broadcast_samples"
DEFAULT_OUT = OUTPUT_DIR / "_waf_probe.json"

TEST_CHANNEL_ID = "269edc95873a1ec9fc534851c0783d1f"
BASE_URL = "https://viewership.softc.one"
CLIENT_IDENTIFIERS = ("chrome_120", "chrome_124", "firefox_120", "safari_16_0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def detect_waf(text: str, status_code: int | None) -> bool:
    head = text[:4000]
    waf_markers = (
        "Vercel Security",
        "Security Checkpoint",
        "This request was blocked",
        "Attention Required",
        "cf-challenge",
        "captcha",
    )
    return status_code in {401, 403, 429} or any(marker.lower() in head.lower() for marker in waf_markers)


def inspect_body(text: str) -> dict[str, Any]:
    return {
        "len": len(text),
        "sha256": sha256_text(text),
        "has_next_f": "__next_f" in text or "self.__next_f" in text,
        "has_next_data": "__NEXT_DATA__" in text,
        "has_broadcast_terms": any(
            marker in text
            for marker in ("방송기록", "방송 시간", "최고 시청자", "broadcast", "Broadcast")
        ),
        "has_csv_terms": any(marker in text.lower() for marker in ("csv", "download", "export")),
    }


def session_get(session: Any, url: str, timeout_seconds: int) -> Any:
    try:
        return session.get(url, timeout_seconds=timeout_seconds)
    except TypeError:
        return session.get(url)


def run_one_client(tls_client: Any, client_identifier: str, timeout_seconds: int, sleep_seconds: float) -> list[dict[str, Any]]:
    session = tls_client.Session(
        client_identifier=client_identifier,
        random_tls_extension_order=True,
    )
    urls = [
        {
            "name": "ranking",
            "url": f"{BASE_URL}/ranking/virtualsoftcone?type=naverchzzk",
        },
        {
            "name": "channel_comma",
            "url": f"{BASE_URL}/channel/{TEST_CHANNEL_ID},naverchzzk",
        },
        {
            "name": "channel_slash",
            "url": f"{BASE_URL}/channel/naverchzzk/{TEST_CHANNEL_ID}",
        },
        {
            "name": "broadcast_comma",
            "url": f"{BASE_URL}/channel/{TEST_CHANNEL_ID},naverchzzk/broadcast",
        },
        {
            "name": "broadcast_slash",
            "url": f"{BASE_URL}/channel/naverchzzk/{TEST_CHANNEL_ID}/broadcast",
        },
    ]

    results: list[dict[str, Any]] = []
    for item in urls:
        started = time.time()
        record: dict[str, Any] = {
            "client_identifier": client_identifier,
            "name": item["name"],
            "url": item["url"],
            "started_at": utc_now(),
        }
        try:
            response = session_get(session, item["url"], timeout_seconds)
            text = getattr(response, "text", "") or ""
            status_code = getattr(response, "status_code", None)
            body = inspect_body(text)
            record.update(
                {
                    "ok": True,
                    "status_code": status_code,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "waf": detect_waf(text, status_code),
                    **body,
                }
            )
        except Exception as exc:  # noqa: BLE001 - report the exact probe failure class.
            record.update(
                {
                    "ok": False,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:500],
                }
            )
        results.append(record)
        time.sleep(sleep_seconds)
    return results


def classify(results: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [r for r in results if r.get("ok")]
    no_waf = [r for r in successful if not r.get("waf")]
    basic = [r for r in no_waf if r["name"].startswith("channel") and (r.get("has_next_f") or r.get("has_next_data"))]
    broadcast = [r for r in no_waf if r["name"].startswith("broadcast") and (r.get("has_broadcast_terms") or r.get("has_csv_terms"))]

    if broadcast:
        verdict = "pass_broadcast_candidate"
        next_action = "tls_client_collect_full"
    elif basic:
        verdict = "partial_pass_endpoint_discovery_needed"
        next_action = "playwright_network_probe_then_collect"
    elif any(r.get("waf") for r in successful):
        verdict = "blocked_or_rate_limited"
        next_action = "playwright_collect"
    else:
        verdict = "not_verifiable"
        next_action = "inspect_errors"

    best_url_pattern = None
    for r in no_waf:
        if r["name"] == "channel_comma":
            best_url_pattern = "comma"
            break
        if r["name"] == "channel_slash":
            best_url_pattern = "slash"
            break

    return {
        "verdict": verdict,
        "next_action": next_action,
        "best_url_pattern": best_url_pattern,
        "successful_requests": len(successful),
        "no_waf_requests": len(no_waf),
        "broadcast_candidate_requests": len(broadcast),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe SOFTC.ONE WAF with tls-client.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path.")
    parser.add_argument("--client", action="append", dest="clients", help="Client identifier to test. May be repeated.")
    parser.add_argument("--timeout-seconds", type=int, default=25)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import tls_client  # type: ignore
    except Exception as exc:  # noqa: BLE001
        report = {
            "generated_at": utc_now(),
            "source": BASE_URL,
            "dependency": "tls_client",
            "verdict": "dependency_missing",
            "next_action": "install_tls_client_then_rerun_probe",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    clients = tuple(args.clients or CLIENT_IDENTIFIERS)
    all_results: list[dict[str, Any]] = []
    for client_identifier in clients:
        all_results.extend(
            run_one_client(
                tls_client=tls_client,
                client_identifier=client_identifier,
                timeout_seconds=args.timeout_seconds,
                sleep_seconds=args.sleep_seconds,
            )
        )

    summary = classify(all_results)
    report = {
        "generated_at": utc_now(),
        "source": BASE_URL,
        "test_channel_id": TEST_CHANNEL_ID,
        "clients": list(clients),
        "summary": summary,
        "results": all_results,
        "raw_body_saved": False,
        "secret_values_logged": False,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out_path), **summary}, ensure_ascii=False, indent=2))
    return 0 if summary["verdict"] != "not_verifiable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
