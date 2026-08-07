"""Add official-linked YouTube seed accounts to known registry personas."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .ids import stable_id


DEFAULT_RUN = Path("consulting/runs/vtuber_registry_20260805")
EVIDENCE_NAME = "youtube_official_seed_profiles_20260805.json"
GENERATED_NOTES = {
    "Official member or creator page directly linking the individual's YouTube channel.",
    "Public canonical and externalId metadata verified without login.",
}


def enrich_official_youtube_seeds(run_dir: str | Path = DEFAULT_RUN) -> dict[str, int]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    evidence = json.loads((run / "10_raw" / EVIDENCE_NAME).read_text(encoding="utf-8"))
    observed_at = evidence["retrieved_at"]

    all_sources = list(_iter_ndjson(normalized / "sources.ndjson"))
    stale_source_ids = {
        row["source_id"] for row in all_sources if row.get("note") in GENERATED_NOTES
    }
    sources = {
        row["source_id"]: row
        for row in all_sources
        if row["source_id"] not in stale_source_ids
    }
    sources_by_uri = {row["uri"]: row for row in sources.values()}
    personas = {row["persona_id"]: row for row in _iter_ndjson(normalized / "personas.ndjson")}
    accounts = {row["account_id"]: row for row in _iter_ndjson(normalized / "accounts.ndjson")}
    for persona in personas.values():
        persona["source_ids"] = [
            source_id for source_id in persona.get("source_ids", []) if source_id not in stale_source_ids
        ]
    for account in accounts.values():
        account["source_ids"] = [
            source_id for source_id in account.get("source_ids", []) if source_id not in stale_source_ids
        ]
    natural_accounts = {(row["platform"], row["platform_account_id"]): row for row in accounts.values()}

    created_accounts = 0
    updated_personas = 0
    for record in evidence["records"]:
        source_uri = record["direct_link_source_uri"]
        if source_uri not in sources_by_uri:
            source_id = stable_id("source", source_uri, observed_at)
            sources[source_id] = {
                "record_type": "source",
                "source_id": source_id,
                "uri": source_uri,
                "source_tier": "P0",
                "publisher": record["organization_seed"],
                "observed_at": observed_at,
                "supports": ["account_link", "affiliation", "name", "vtuber_identity"],
                "note": "Official member or creator page directly linking the individual's YouTube channel.",
                "secret_values_stored": False,
            }
            sources_by_uri[source_uri] = sources[source_id]

        channel_uri = f"https://www.youtube.com/channel/{record['channel_id']}"
        channel_source_id = stable_id("source", channel_uri, observed_at)
        sources[channel_source_id] = {
            "record_type": "source",
            "source_id": channel_source_id,
            "uri": channel_uri,
            "source_tier": "P1",
            "publisher": "YouTube public channel page",
            "observed_at": observed_at,
            "supports": ["account_link", "name"],
            "note": "Public canonical and externalId metadata verified without login.",
            "secret_values_stored": False,
        }
        source_ids = sorted({sources_by_uri[source_uri]["source_id"], channel_source_id})

        persona_id = record.get("persona_id")
        if persona_id is None:
            soop_account = natural_accounts.get(("soop", record["known_soop_handle"]))
            if soop_account is None:
                raise ValueError(f"known SOOP account missing for {record['official_name']}")
            persona_id = soop_account["persona_id"]
        if persona_id not in personas:
            raise ValueError(f"persona missing for {record['official_name']}: {persona_id}")

        account_id = stable_id("account", "youtube", record["channel_id"])
        if account_id not in accounts:
            accounts[account_id] = {
                "record_type": "account",
                "account_id": account_id,
                "persona_id": persona_id,
                "platform": "youtube",
                "platform_account_id": record["channel_id"],
                "id_namespace": "official_platform_id",
                "display_name": record["channel_title"],
                "handle": record["handle"],
                "canonical_url": channel_uri,
                "account_role": "primary",
                "last_public_activity_at": None,
                "first_seen_at": observed_at,
                "last_verified_at": observed_at,
                "source_ids": source_ids,
            }
            created_accounts += 1
        else:
            account = accounts[account_id]
            account["persona_id"] = persona_id
            account["display_name"] = record["channel_title"]
            account["handle"] = record["handle"]
            account["canonical_url"] = channel_uri
            account["last_verified_at"] = observed_at
            account["source_ids"] = source_ids

        persona = personas[persona_id]
        old_source_ids = set(persona.get("source_ids", []))
        persona["source_ids"] = sorted(old_source_ids | set(source_ids))
        persona["last_verified_at"] = observed_at
        if set(persona["source_ids"]) != old_source_ids:
            updated_personas += 1

    _write_ndjson(normalized / "sources.ndjson", sorted(sources.values(), key=lambda row: row["source_id"]))
    _write_ndjson(normalized / "personas.ndjson", sorted(personas.values(), key=lambda row: row["persona_id"]))
    _write_ndjson(normalized / "accounts.ndjson", sorted(accounts.values(), key=lambda row: row["account_id"]))

    frontier = _build_frontier(run, evidence["records"], natural_accounts)
    _write_csv(run / "40_review" / "youtube_official_frontier.csv", frontier)

    summary = {
        "official_link_records": len(evidence["records"]),
        "created_accounts": created_accounts,
        "updated_personas": updated_personas,
        "official_roster_frontier": len(frontier),
        "frontier_needs_official_youtube_link": sum(
            row["status"] == "needs_official_youtube_link" for row in frontier
        ),
        "frontier_needs_persona_resolution": sum(
            row["status"] == "needs_persona_resolution" for row in frontier
        ),
    }
    (run / "50_coverage" / "youtube_seed_enrichment_summary.json").write_text(
        json.dumps({"observed_at": observed_at, **summary}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _build_frontier(
    run: Path,
    linked_records: list[dict[str, Any]],
    natural_accounts: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, str]]:
    linked_by_key = {
        (row["organization_seed"], row["official_name"]): row for row in linked_records
    }
    frontier = []
    with (run / "40_review" / "official_roster_matches.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        roster_rows = list(csv.DictReader(handle))
    for row in roster_rows:
        key = (row["organization_seed"], row["official_name"])
        linked = linked_by_key.get(key)
        status = "linked_official_seed" if linked else (
            "needs_official_youtube_link"
            if row["matched_persona_ids"]
            else "needs_persona_resolution"
        )
        frontier.append(
            {
                "organization_seed": row["organization_seed"],
                "official_name": row["official_name"],
                "persona_ids": row["matched_persona_ids"],
                "official_source_uri": row["source_uri"],
                "youtube_channel_id": linked["channel_id"] if linked else "",
                "youtube_handle": linked["handle"] if linked else "",
                "status": status,
            }
        )

    for linked in linked_records:
        if linked["organization_seed"] != "아카이브":
            continue
        soop_account = natural_accounts[("soop", linked["known_soop_handle"])]
        frontier.append(
            {
                "organization_seed": linked["organization_seed"],
                "official_name": linked["official_name"],
                "persona_ids": soop_account["persona_id"],
                "official_source_uri": linked["direct_link_source_uri"],
                "youtube_channel_id": linked["channel_id"],
                "youtube_handle": linked["handle"],
                "status": "linked_official_seed",
            }
        )
    return sorted(frontier, key=lambda row: (row["organization_seed"], row["official_name"]))


def _iter_ndjson(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _write_ndjson(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    print(enrich_official_youtube_seeds())
