"""Collect public profile evidence for the fixed 100-account QA sample."""

from __future__ import annotations

import csv
import json
import time
import unicodedata
from pathlib import Path

from consulting.tools.outreach.chzzk import BoundarySignal, ChzzkClient, ChzzkError
from .ids import stable_id


VTUBER_TERMS = (
    "버튜버",
    "버츄얼",
    "버추얼",
    "vtuber",
    "virtual",
    "live2d",
    "브이튜버",
)


def collect_qa_public_evidence(
    run_dir: str | Path,
    *,
    delay_seconds: float = 0.35,
) -> dict[str, int]:
    run = Path(run_dir)
    review_dir = run / "40_review"
    sample_path = review_dir / "manual_qa_sample_100.csv"
    output_path = review_dir / "manual_qa_public_evidence_100.csv"
    rows = _read_csv(sample_path)
    client = ChzzkClient(timeout_seconds=15.0)
    output: list[dict[str, object]] = []
    counts = {"ok": 0, "error": 0, "not_checked": 0, "name_match": 0, "explicit_vtuber_signal": 0}

    for index, row in enumerate(rows):
        base = {
            "account_id": row["account_id"],
            "platform": row["platform"],
            "requested_platform_account_id": row["platform_account_id"],
            "expected_name": row["display_name"],
            "fetch_status": "not_checked",
            "fetched_name": "",
            "normalized_name_match": "",
            "description": "",
            "verified_mark": "",
            "open_live": "",
            "explicit_vtuber_signal": "",
            "fetched_at": "",
            "error": "",
        }
        if row["platform"] != "chzzk":
            base["error"] = "platform namespace requires a separate public verifier"
            output.append(base)
            counts["not_checked"] += 1
            continue

        try:
            detail = client.channel_detail(row["platform_account_id"])
            fetched_name = str(detail.get("channel_name") or "")
            description = str(detail.get("description") or "")
            name_match = bool(row["display_name"]) and _normalized_name(row["display_name"]) == _normalized_name(fetched_name)
            vtuber_signal = any(term in description.casefold() for term in VTUBER_TERMS)
            base.update(
                fetch_status="ok",
                fetched_name=fetched_name,
                normalized_name_match="yes" if name_match else "no",
                description=description,
                verified_mark="yes" if detail.get("verified") else "no",
                open_live="yes" if detail.get("open_live") else "no",
                explicit_vtuber_signal="yes" if vtuber_signal else "no",
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            )
            counts["ok"] += 1
            counts["name_match"] += int(name_match)
            counts["explicit_vtuber_signal"] += int(vtuber_signal)
        except BoundarySignal as exc:
            base["fetch_status"] = "boundary"
            base["error"] = f"{exc.signal}: {exc}"
            counts["error"] += 1
            output.append(base)
            break
        except ChzzkError as exc:
            base["fetch_status"] = "error"
            base["error"] = str(exc)
            counts["error"] += 1
        output.append(base)
        if index + 1 < len(rows):
            time.sleep(delay_seconds)

    _write_csv(output_path, output)
    return counts


def apply_qa_public_evidence(run_dir: str | Path) -> dict[str, int]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    review_dir = run / "40_review"
    evidence_path = review_dir / "manual_qa_public_evidence_100.csv"
    evidence_rows = _read_csv(evidence_path)
    ok_rows = [row for row in evidence_rows if row["fetch_status"] == "ok"]
    if not ok_rows:
        raise ValueError("no successful QA evidence rows")

    source_uri = evidence_path.resolve().as_uri()
    source_id = stable_id("source", source_uri)
    observed_at = max(row["fetched_at"] for row in ok_rows)
    source_record = {
        "record_type": "source",
        "source_id": source_id,
        "uri": source_uri,
        "source_tier": "P1",
        "publisher": "CHZZK public profile API QA snapshot",
        "observed_at": observed_at,
        "supports": ["account_link", "activity", "name"],
        "note": "Login-free public profile evidence for the fixed 100-account QA sample; 98 CHZZK rows fetched.",
        "secret_values_stored": False,
    }

    sources_path = normalized / "sources.ndjson"
    accounts_path = normalized / "accounts.ndjson"
    personas_path = normalized / "personas.ndjson"
    reviews_path = review_dir / "review_queue.ndjson"
    sources = {record["source_id"]: record for record in _iter_ndjson(sources_path)}
    accounts = {record["account_id"]: record for record in _iter_ndjson(accounts_path)}
    personas = {record["persona_id"]: record for record in _iter_ndjson(personas_path)}
    reviews = {record["review_id"]: record for record in _iter_ndjson(reviews_path)}
    sources[source_id] = source_record

    names_backfilled = 0
    name_change_reviews = 0
    verified_accounts = 0
    for evidence in ok_rows:
        account = accounts[evidence["account_id"]]
        fetched_name = evidence["fetched_name"].strip()
        account["last_verified_at"] = evidence["fetched_at"]
        account["source_ids"] = sorted(set(account["source_ids"]) | {source_id})
        persona = personas[account["persona_id"]]
        persona["last_verified_at"] = evidence["fetched_at"]
        persona["source_ids"] = sorted(set(persona["source_ids"]) | {source_id})
        verified_accounts += 1

        if not account["display_name"] and fetched_name:
            account["display_name"] = fetched_name
            if not persona["display_name"]:
                persona["display_name"] = fetched_name
            names_backfilled += 1
            continue

        if fetched_name and _normalized_name(account["display_name"]) != _normalized_name(fetched_name):
            review_id = stable_id(
                "review", "public_name_changed_since_qa_sample", account["account_id"], fetched_name
            )
            reviews[review_id] = {
                "record_type": "review_item",
                "review_id": review_id,
                "entity_type": "account",
                "entity_id": account["account_id"],
                "issue_code": "public_name_changed_since_qa_sample",
                "severity": "warning",
                "status": "open",
                "details": {
                    "registry_name": account["display_name"],
                    "current_public_name": fetched_name,
                    "platform": account["platform"],
                    "platform_account_id": account["platform_account_id"],
                },
                "source_ids": [source_id],
            }
            name_change_reviews += 1

    _write_ndjson(sources_path, sorted(sources.values(), key=lambda item: item["source_id"]))
    _write_ndjson(accounts_path, sorted(accounts.values(), key=lambda item: item["account_id"]))
    _write_ndjson(personas_path, sorted(personas.values(), key=lambda item: item["persona_id"]))
    _write_ndjson(reviews_path, sorted(reviews.values(), key=lambda item: item["review_id"]))
    return {
        "verified_accounts": verified_accounts,
        "names_backfilled": names_backfilled,
        "name_change_reviews": name_change_reviews,
        "total_reviews": len(reviews),
    }


def _normalized_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in value if char.isalnum())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _iter_ndjson(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _write_ndjson(path: Path, records) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )
