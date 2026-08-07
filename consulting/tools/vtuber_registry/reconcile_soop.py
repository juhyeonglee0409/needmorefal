"""Materialize reviewed official SOOP accounts and resolve their coverage gaps."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .ids import stable_id


DEFAULT_RUN = Path("consulting/runs/vtuber_registry_20260805")
EVIDENCE_NAME = "soop_official_profiles_20260805.json"
AKAIV_SOURCE_URI = "https://www.akaiv.studio/"
ISEGYE_SOURCE_URI = "https://www.youtube.com/watch?v=Li4VvoZGiYs"
CORROBORATED_PERSONA_BY_HANDLE = {
    "beemong": "krvt_p_9317b8d7b2df5a74bbe77a1c168e970f",
}


def reconcile_official_soop(run_dir: str | Path = DEFAULT_RUN) -> dict[str, int]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    review_dir = run / "40_review"
    evidence_path = run / "10_raw" / EVIDENCE_NAME
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    observed_at = evidence["retrieved_at"]

    sources = {row["source_id"]: row for row in _iter_ndjson(normalized / "sources.ndjson")}
    sources_by_uri = {row["uri"]: row for row in sources.values()}
    personas = {row["persona_id"]: row for row in _iter_ndjson(normalized / "personas.ndjson")}
    accounts = {row["account_id"]: row for row in _iter_ndjson(normalized / "accounts.ndjson")}
    organizations = list(_iter_ndjson(normalized / "organizations.ndjson"))
    affiliations = {row["affiliation_id"]: row for row in _iter_ndjson(normalized / "affiliations.ndjson")}
    reviews = {row["review_id"]: row for row in _iter_ndjson(review_dir / "review_queue.ndjson")}

    organization_by_seed = _organization_by_seed(organizations)
    candidates = _read_csv(review_dir / "official_account_candidates.csv")
    candidate_by_handle = {row["official_platform_account_id"]: row for row in candidates}

    created_personas = 0
    created_accounts = 0
    created_affiliations = 0
    resolved_reviews = 0
    identity_reviews = 0

    for profile in evidence["records"]:
        handle = profile["user_id"]
        official_name = profile["official_name"]
        organization_seed = profile["organization_seed"]
        organization = organization_by_seed[organization_seed]
        roster_uri = AKAIV_SOURCE_URI if organization_seed == "아카이브" else ISEGYE_SOURCE_URI
        roster_source = sources_by_uri[roster_uri]

        profile_uri = f"https://bjapi.afreecatv.com/api/{handle}/station"
        profile_source_id = stable_id("source", profile_uri, observed_at)
        sources[profile_source_id] = {
            "record_type": "source",
            "source_id": profile_source_id,
            "uri": profile_uri,
            "source_tier": "P1",
            "publisher": "SOOP public station API",
            "observed_at": observed_at,
            "supports": ["account_link", "name"],
            "note": "Login-free public station profile snapshot; raw selected fields are preserved in 10_raw/soop_official_profiles_20260805.json.",
            "secret_values_stored": False,
        }
        source_ids = sorted({roster_source["source_id"], profile_source_id})

        persona_id = CORROBORATED_PERSONA_BY_HANDLE.get(handle)
        if persona_id is None:
            persona_id = stable_id("persona", "seed-account", "soop", handle)
        aliases = sorted(
            {
                value
                for value in (profile.get("user_nick"), profile.get("station_name"))
                if value and value != official_name
            }
        )
        if persona_id not in personas:
            personas[persona_id] = {
                "record_type": "persona",
                "persona_id": persona_id,
                "display_name": official_name,
                "public_aliases": aliases,
                "market": "ko_KR",
                "market_evidence": ["korean_platform:soop", "official_organization_roster"],
                "vtuber_status": "confirmed",
                "representation_mode": "unknown",
                "operating_model": "agency_ip_owned" if organization_seed == "아카이브" else "project_collective",
                "activity_status": "unknown",
                "first_seen_at": observed_at,
                "last_verified_at": observed_at,
                "review_status": "manual_confirmed",
                "source_ids": source_ids,
            }
            created_personas += 1
        else:
            persona = personas[persona_id]
            persona["public_aliases"] = sorted(set(persona.get("public_aliases", [])) | set(aliases) | {official_name})
            persona["market_evidence"] = sorted(set(persona.get("market_evidence", [])) | {"korean_platform:soop", "official_organization_roster"})
            persona["vtuber_status"] = "confirmed"
            persona["review_status"] = "manual_confirmed"
            persona["last_verified_at"] = observed_at
            persona["source_ids"] = sorted(set(persona.get("source_ids", [])) | set(source_ids))

        account_id = stable_id("account", "soop", handle)
        if account_id not in accounts:
            accounts[account_id] = {
                "record_type": "account",
                "account_id": account_id,
                "persona_id": persona_id,
                "platform": "soop",
                "platform_account_id": handle,
                "id_namespace": "official_platform_id",
                "display_name": profile.get("user_nick") or official_name,
                "handle": handle,
                "canonical_url": f"https://www.sooplive.com/station/{handle}",
                "account_role": "primary",
                "last_public_activity_at": None,
                "first_seen_at": observed_at,
                "last_verified_at": observed_at,
                "source_ids": source_ids,
            }
            created_accounts += 1

        relationship = "talent" if organization_seed == "아카이브" else "member"
        affiliation_id = stable_id("affiliation", persona_id, organization["organization_id"], relationship, "current")
        if affiliation_id not in affiliations:
            affiliations[affiliation_id] = {
                "record_type": "affiliation",
                "affiliation_id": affiliation_id,
                "persona_id": persona_id,
                "organization_id": organization["organization_id"],
                "relationship": relationship,
                "start_at": None,
                "end_at": None,
                "status": "current",
                "source_ids": source_ids,
            }
            created_affiliations += 1

        for review in reviews.values():
            details = review.get("details", {})
            official_handle_match = (
                review["issue_code"] == "official_soop_handle_missing_from_softcon_seed"
                and details.get("official_platform_account_id") == handle
            )
            roster_name_match = (
                review["issue_code"] == "official_roster_name_not_exact_unique"
                and review["entity_id"] == organization["organization_id"]
                and details.get("official_name") == official_name
            )
            if review["status"] == "open" and (official_handle_match or roster_name_match):
                review["status"] = "resolved"
                review["source_ids"] = sorted(set(review.get("source_ids", [])) | set(source_ids))
                review["details"]["materialized_account_id"] = account_id
                review["details"]["materialized_persona_id"] = persona_id
                resolved_reviews += 1

        candidate = candidate_by_handle[handle]
        candidate["already_in_registry_account_id"] = account_id
        if handle == "beemong":
            candidate["status"] = "materialized_existing_persona_corroborated"
        elif handle == "kaksjak0730":
            candidate["status"] = "materialized_new_persona_cross_platform_review"
            review_id = stable_id("review", "official_soop_cross_platform_identity_ambiguous", account_id)
            reviews[review_id] = {
                "record_type": "review_item",
                "review_id": review_id,
                "entity_type": "account",
                "entity_id": account_id,
                "issue_code": "official_soop_cross_platform_identity_ambiguous",
                "severity": "warning",
                "status": "open",
                "details": {
                    "official_name": official_name,
                    "candidate_account_ids": [
                        value for value in candidate["local_name_candidate_account_ids"].split("|") if value
                    ],
                    "note": "Name overlap alone does not establish that any CHZZK/CIME account is AKAIV Hangyeol.",
                },
                "source_ids": source_ids,
            }
            identity_reviews += 1
        else:
            candidate["status"] = "materialized_new_persona"
        candidate["note"] = "Official account materialized from organization roster plus current public SOOP station profile."

    _write_ndjson(normalized / "sources.ndjson", sorted(sources.values(), key=lambda row: row["source_id"]))
    _write_ndjson(normalized / "personas.ndjson", sorted(personas.values(), key=lambda row: row["persona_id"]))
    _write_ndjson(normalized / "accounts.ndjson", sorted(accounts.values(), key=lambda row: row["account_id"]))
    _write_ndjson(normalized / "affiliations.ndjson", sorted(affiliations.values(), key=lambda row: row["affiliation_id"]))
    _write_ndjson(review_dir / "review_queue.ndjson", sorted(reviews.values(), key=lambda row: row["review_id"]))
    _write_csv(review_dir / "official_account_candidates.csv", candidates)

    summary = {
        "created_personas": created_personas,
        "created_accounts": created_accounts,
        "created_affiliations": created_affiliations,
        "resolved_reviews": resolved_reviews,
        "new_identity_reviews": identity_reviews,
    }
    (run / "50_coverage" / "soop_reconciliation_summary.json").write_text(
        json.dumps({"observed_at": observed_at, **summary}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _organization_by_seed(organizations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for organization in organizations:
        names = {organization["display_name"], *organization.get("aliases", [])}
        if names & {"AKAIV STUDIO", "아카이브", "AkaiV"}:
            result["아카이브"] = organization
        if names & {"이세계아이돌", "ISEGYE IDOL", "이세돌"}:
            result["이세계아이돌"] = organization
    if set(result) != {"아카이브", "이세계아이돌"}:
        raise ValueError("required organizations are missing")
    return result


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    print(reconcile_official_soop())
