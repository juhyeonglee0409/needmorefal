"""Offline bootstrap for the Korean VTuber registry.

This command reads existing local Softcon/CHZZK artifacts only. It performs no
network access and never sends messages. The Softcon platform code is retained
in the account natural key so SOOP/CIME/CHZZK identifiers cannot collide.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, TextIO

from .ids import stable_id
from .validate import load_schema, validate_ndjson, validate_record


REPO_ROOT = Path(__file__).resolve().parents[3]
CONSULTING = REPO_ROOT / "consulting"

DEFAULT_SOFTCON = Path(r"D:\Gunsmith_Mailbox\reports\softcon_virtual_census_20260704.ndjson")
DEFAULT_WEEKLY = CONSULTING / "runs" / "census_full_20260708" / "census_full_weekly.ndjson"
DEFAULT_PROFILES = (
    CONSULTING / "runs" / "vtuber_outreach_pilot_20260704" / "census_pool.ndjson"
)
DEFAULT_AGENCIES = CONSULTING / "tools" / "outreach" / "agencies.yaml"
DEFAULT_OUTPUT = CONSULTING / "runs" / "vtuber_registry_20260805"

PLATFORM_MAP = {
    "naverchzzk": "chzzk",
    "afreeca": "soop",
    "cime": "cime",
}
SOURCE_DATES = {
    "softcon": "2026-07-04T17:19:59+09:00",
    "weekly": "2026-07-09T00:30:00+09:00",
    "profiles": "2026-07-07T19:30:00+09:00",
    "agencies": "2026-07-04T18:15:00+09:00",
}
CHZZK_ID = re.compile(r"^[0-9a-f]{32}$")


class BootstrapError(RuntimeError):
    pass


def run_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    softcon_path = Path(args.softcon)
    weekly_path = Path(args.weekly)
    profiles_path = Path(args.profiles)
    agencies_path = Path(args.agencies)
    output = Path(args.output)
    _require_inputs([softcon_path, weekly_path, profiles_path, agencies_path])

    dirs = {
        "bootstrap": output / "10_bootstrap",
        "normalized": output / "20_normalized",
        "review": output / "40_review",
        "coverage": output / "50_coverage",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    output_files = {
        "sources": dirs["normalized"] / "sources.ndjson",
        "personas": dirs["normalized"] / "personas.ndjson",
        "accounts": dirs["normalized"] / "accounts.ndjson",
        "organizations": dirs["normalized"] / "organizations.ndjson",
        "affiliations": dirs["normalized"] / "affiliations.ndjson",
        "observations": dirs["normalized"] / "observations.ndjson",
        "review_queue": dirs["review"] / "review_queue.ndjson",
        "qa_sample": dirs["review"] / "manual_qa_sample_100.csv",
        "report": dirs["coverage"] / "bootstrap_report.md",
        "manifest": output / "run_manifest.json",
        "progress": output / "progress.ndjson",
    }
    _refuse_overwrite(output_files.values(), allow_existing={output_files["progress"]})
    progress = ProgressLog(output_files["progress"])
    progress.append({"event": "bootstrap_start", "network_access": False})

    schema = load_schema(args.schema)
    sources = _build_sources(softcon_path, weekly_path, profiles_path, agencies_path)
    source_by_label = {source["publisher"]: source["source_id"] for source in sources}
    _write_records(output_files["sources"], sources, schema=schema)

    seeds, raw_by_cid, raw_stats = _load_softcon(softcon_path)
    progress.append({"event": "softcon_loaded", **raw_stats})

    profiles, profile_stats = _load_latest_profiles(profiles_path)
    progress.append({"event": "profiles_loaded", **profile_stats})

    weekly_map, weekly_stats = _scan_weekly(weekly_path, seeds, raw_by_cid)
    progress.append({"event": "weekly_scanned", **weekly_stats})

    profile_added = 0
    for channel_id, profile in profiles.items():
        key = ("chzzk", channel_id)
        if key not in seeds:
            seeds[key] = {
                "platform": "chzzk",
                "cid": channel_id,
                "raw": None,
                "weekly": False,
                "weekly_name": "",
                "profile_only": True,
            }
            profile_added += 1

    accounts: list[dict[str, Any]] = []
    personas: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    account_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    names: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    profile_joined = 0
    profile_name_changes = 0

    for key in sorted(seeds):
        platform, cid = key
        seed = seeds[key]
        profile = profiles.get(cid) if platform == "chzzk" else None
        if profile:
            profile_joined += 1
        raw = seed.get("raw") if isinstance(seed.get("raw"), dict) else None
        raw_name = str(raw.get("name") or "") if raw else ""
        weekly_name = str(seed.get("weekly_name") or "")
        profile_name = str(profile.get("channel_name") or "") if profile else ""
        display_name = profile_name or raw_name or weekly_name
        aliases = _unique_nonempty([raw_name, weekly_name, profile_name], exclude=display_name)

        source_ids = []
        if raw:
            source_ids.append(source_by_label["softcon_virtual_census"])
        if seed.get("weekly"):
            source_ids.append(source_by_label["softcon_weekly_series"])
        if profile:
            source_ids.append(source_by_label["chzzk_profile_pool"])
        source_ids = sorted(set(source_ids))

        account_id = stable_id("account", platform, cid)
        persona_id = stable_id("persona", "seed-account", platform, cid)
        inferred_chzzk = platform == "chzzk" and not raw and bool(seed.get("weekly"))
        if platform == "chzzk":
            id_namespace = (
                "inferred_chzzk_channel_id" if inferred_chzzk else "official_platform_id"
            )
            canonical_url = f"https://chzzk.naver.com/{cid}"
        else:
            id_namespace = "softcon_platform_channel_id"
            canonical_url = None

        last_verified = _last_verified(raw=raw, weekly=bool(seed.get("weekly")), profile=profile)
        account = {
            "record_type": "account",
            "account_id": account_id,
            "persona_id": persona_id,
            "platform": platform,
            "platform_account_id": cid,
            "id_namespace": id_namespace,
            "display_name": display_name,
            "handle": None,
            "canonical_url": canonical_url,
            "account_role": "unknown",
            "last_public_activity_at": None,
            "first_seen_at": SOURCE_DATES["softcon"] if raw else last_verified,
            "last_verified_at": last_verified,
            "source_ids": source_ids,
        }

        vtuber = profile.get("vtuber") if isinstance(profile, dict) else None
        confirmed = isinstance(vtuber, dict) and vtuber.get("value") is True
        persona = {
            "record_type": "persona",
            "persona_id": persona_id,
            "display_name": display_name,
            "public_aliases": aliases,
            "market": "ko_KR",
            "market_evidence": _market_evidence(platform, bool(raw)),
            "vtuber_status": "confirmed" if confirmed else "probable",
            "representation_mode": "unknown",
            "operating_model": "unknown",
            "activity_status": "active_90d",
            "first_seen_at": account["first_seen_at"],
            "last_verified_at": last_verified,
            "review_status": "needs_review" if inferred_chzzk else "auto",
            "source_ids": source_ids,
        }

        _validate_or_raise(account, schema)
        _validate_or_raise(persona, schema)
        accounts.append(account)
        personas.append(persona)
        account_by_key[key] = account

        normalized_name = _normalized_name(display_name)
        if normalized_name:
            names[normalized_name].append((platform, account_id, persona_id, display_name))

        if inferred_chzzk:
            reviews.append(
                _review(
                    entity_type="account",
                    entity_id=account_id,
                    issue_code="platform_inferred_from_chzzk_id_shape",
                    severity="warning",
                    details={"platform": platform, "channel_id": cid, "display_name": display_name},
                    source_ids=source_ids,
                )
            )
        if raw_name and profile_name and _normalized_name(raw_name) != _normalized_name(profile_name):
            profile_name_changes += 1
            reviews.append(
                _review(
                    entity_type="persona",
                    entity_id=persona_id,
                    issue_code="public_name_changed_between_sources",
                    severity="info",
                    details={"softcon_name": raw_name, "profile_name": profile_name},
                    source_ids=source_ids,
                )
            )

    cross_platform_groups = 0
    for normalized_name, matches in sorted(names.items()):
        platforms = {match[0] for match in matches}
        if len(matches) < 2 or len(platforms) < 2:
            continue
        cross_platform_groups += 1
        reviews.append(
            _review(
                entity_type="persona",
                entity_id=matches[0][2],
                issue_code="cross_platform_same_name_no_auto_merge",
                severity="warning",
                details={
                    "normalized_name": normalized_name,
                    "candidates": [
                        {
                            "platform": platform,
                            "account_id": account_id,
                            "persona_id": persona_id,
                            "display_name": display_name,
                        }
                        for platform, account_id, persona_id, display_name in matches
                    ],
                },
                source_ids=sorted(
                    {
                        source_id
                        for _, account_id, _, _ in matches
                        for source_id in _account_sources(accounts, account_id)
                    }
                ),
            )
        )

    organizations, organization_reviews = _build_organization_seeds(
        agencies_path, source_by_label["outreach_agency_seed"]
    )
    reviews.extend(organization_reviews)

    _write_records(output_files["personas"], personas, schema=schema)
    _write_records(output_files["accounts"], accounts, schema=schema)
    _write_records(output_files["organizations"], organizations, schema=schema)
    output_files["affiliations"].write_text("", encoding="utf-8")
    _write_records(output_files["review_queue"], reviews, schema=schema)

    observation_stats = _write_observations(
        output_files["observations"],
        softcon_path=softcon_path,
        weekly_path=weekly_path,
        profiles=profiles,
        account_by_key=account_by_key,
        weekly_map=weekly_map,
        source_by_label=source_by_label,
        schema=schema,
        progress=progress,
    )
    _write_qa_sample(output_files["qa_sample"], accounts, personas)

    platform_counts = Counter(record["platform"] for record in accounts)
    review_counts = Counter(record["issue_code"] for record in reviews)
    raw_keys = {key for key, seed in seeds.items() if isinstance(seed.get("raw"), dict)}
    weekly_keys = set(weekly_map.values())
    summary = {
        "run_id": "vtuber_registry_20260805",
        "status": "completed_local_bootstrap_unreviewed",
        "generated_at": _now(),
        "network_access": False,
        "secret_values_stored": False,
        "input_files": {
            str(path): {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in [softcon_path, weekly_path, profiles_path, agencies_path]
        },
        "input_counts": {
            "softcon_rows": raw_stats["rows"],
            "softcon_unique_platform_keys": len(raw_keys),
            "weekly_rows": weekly_stats["rows"],
            "profile_rows": profile_stats["rows"],
            "profile_unique_channels": profile_stats["unique_channels"],
        },
        "join_counts": {
            "weekly_direct_platform_matches": weekly_stats["direct_matches"],
            "weekly_chzzk_id_shape_inferences": weekly_stats["chzzk_inferred"],
            "weekly_unresolved": weekly_stats["unresolved"],
            "softcon_without_weekly": len(raw_keys - weekly_keys),
            "profiles_joined": profile_joined,
            "profile_only_accounts_added": profile_added,
            "public_name_changes": profile_name_changes,
        },
        "output_counts": {
            "personas": len(personas),
            "accounts": len(accounts),
            "organizations": len(organizations),
            "affiliations": 0,
            "observations": observation_stats["total"],
            "review_items": len(reviews),
        },
        "platform_counts": dict(sorted(platform_counts.items())),
        "observation_counts": observation_stats,
        "review_counts": dict(sorted(review_counts.items())),
        "cross_platform_same_name_groups": cross_platform_groups,
    }

    validations = _validate_outputs(output_files, schema=schema)
    summary["validation"] = validations
    if validations["error_count"]:
        raise BootstrapError(f"output validation failed: {validations['error_count']} errors")

    output_files["manifest"].write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    output_files["report"].write_text(_render_report(summary), encoding="utf-8")
    progress.append({"event": "bootstrap_complete", **summary["output_counts"]})
    return summary


def _build_sources(*paths: Path) -> list[dict[str, Any]]:
    labels = [
        ("softcon_virtual_census", paths[0], "P2", SOURCE_DATES["softcon"], ["market", "vtuber_identity", "activity", "metrics", "name"]),
        ("softcon_weekly_series", paths[1], "P2", SOURCE_DATES["weekly"], ["activity", "metrics", "name"]),
        ("chzzk_profile_pool", paths[2], "P1", SOURCE_DATES["profiles"], ["account_link", "activity", "metrics", "name", "vtuber_identity"]),
        ("outreach_agency_seed", paths[3], "P4", SOURCE_DATES["agencies"], ["affiliation"]),
    ]
    records = []
    for publisher, path, tier, observed_at, supports in labels:
        uri = path.resolve().as_uri()
        records.append(
            {
                "record_type": "source",
                "source_id": stable_id("source", uri, observed_at),
                "uri": uri,
                "source_tier": tier,
                "publisher": publisher,
                "observed_at": observed_at,
                "supports": supports,
                "note": "Existing local artifact; no external access performed in this run.",
                "secret_values_stored": False,
            }
        )
    return records


def _load_softcon(path: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, tuple[str, str]], dict[str, Any]]:
    seeds: dict[tuple[str, str], dict[str, Any]] = {}
    raw_by_cid: dict[str, tuple[str, str]] = {}
    counts: Counter[str] = Counter()
    rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            rows += 1
            raw = json.loads(line)
            raw_platform = str(raw.get("platform") or "")
            platform = PLATFORM_MAP.get(raw_platform)
            cid = str(raw.get("cid") or "")
            if not platform or not cid:
                raise BootstrapError(f"softcon line {line_number}: invalid platform/cid")
            key = (platform, cid)
            if key in seeds:
                raise BootstrapError(f"softcon duplicate platform key: {key}")
            if cid in raw_by_cid and raw_by_cid[cid] != key:
                raise BootstrapError(f"softcon cross-platform cid collision: {cid}")
            seeds[key] = {
                "platform": platform,
                "cid": cid,
                "raw": raw,
                "weekly": False,
                "weekly_name": "",
                "profile_only": False,
            }
            raw_by_cid[cid] = key
            counts[platform] += 1
    return seeds, raw_by_cid, {
        "rows": rows,
        "platform_counts": dict(sorted(counts.items())),
    }


def _load_latest_profiles(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    latest: dict[str, dict[str, Any]] = {}
    rows = 0
    missing_id = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            record = json.loads(line)
            channel_id = str(record.get("channel_id") or "")
            if not channel_id:
                missing_id += 1
                continue
            latest[channel_id] = record
    return latest, {
        "rows": rows,
        "unique_channels": len(latest),
        "duplicate_updates": rows - missing_id - len(latest),
        "missing_id": missing_id,
    }


def _scan_weekly(
    path: Path,
    seeds: dict[tuple[str, str], dict[str, Any]],
    raw_by_cid: dict[str, tuple[str, str]],
) -> tuple[dict[str, tuple[str, str]], dict[str, int]]:
    mapping: dict[str, tuple[str, str]] = {}
    stats = {"rows": 0, "direct_matches": 0, "chzzk_inferred": 0, "unresolved": 0}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            stats["rows"] += 1
            row = json.loads(line)
            cid = str(row.get("channel_id") or "")
            if not cid:
                raise BootstrapError(f"weekly line {line_number}: missing channel_id")
            if cid in raw_by_cid:
                key = raw_by_cid[cid]
                stats["direct_matches"] += 1
            elif CHZZK_ID.fullmatch(cid):
                key = ("chzzk", cid)
                stats["chzzk_inferred"] += 1
                seeds.setdefault(
                    key,
                    {
                        "platform": "chzzk",
                        "cid": cid,
                        "raw": None,
                        "weekly": False,
                        "weekly_name": "",
                        "profile_only": False,
                    },
                )
            else:
                stats["unresolved"] += 1
                continue
            mapping[cid] = key
            seeds[key]["weekly"] = True
            if row.get("channel_name"):
                seeds[key]["weekly_name"] = str(row["channel_name"])
    return mapping, stats


def _write_observations(
    path: Path,
    *,
    softcon_path: Path,
    weekly_path: Path,
    profiles: dict[str, dict[str, Any]],
    account_by_key: dict[tuple[str, str], dict[str, Any]],
    weekly_map: dict[str, tuple[str, str]],
    source_by_label: dict[str, str],
    schema: dict[str, Any],
    progress: "ProgressLog",
) -> dict[str, int]:
    counts = {"softcon_snapshot": 0, "profile_snapshot": 0, "weekly": 0, "total": 0}
    with path.open("w", encoding="utf-8") as handle:
        with softcon_path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                raw = json.loads(line)
                key = (PLATFORM_MAP[str(raw["platform"])], str(raw["cid"]))
                account = account_by_key[key]
                record = _observation(
                    account_id=account["account_id"],
                    label="softcon_snapshot",
                    observed_at=SOURCE_DATES["softcon"],
                    period_start=None,
                    period_end="2026-07-04",
                    granularity="snapshot",
                    metrics={
                        "rank": raw.get("rank"),
                        "air_time_hours": raw.get("hours"),
                        "max_viewers": raw.get("max"),
                        "avg_viewers": raw.get("avg"),
                        "viewership": raw.get("vs"),
                    },
                    source_ids=[source_by_label["softcon_virtual_census"]],
                )
                _append_validated(handle, record, schema)
                counts["softcon_snapshot"] += 1

        for channel_id, profile in profiles.items():
            key = ("chzzk", channel_id)
            account = account_by_key.get(key)
            if account is None:
                continue
            activity = profile.get("activity")
            open_live_seen = (
                bool(activity.get("open_live_seen")) if isinstance(activity, dict) else False
            )
            record = _observation(
                account_id=account["account_id"],
                label="profile_snapshot",
                observed_at=SOURCE_DATES["profiles"],
                period_start=None,
                period_end="2026-07-07",
                granularity="snapshot",
                metrics={
                    "follower_count": profile.get("follower_count"),
                    "open_live_seen": open_live_seen,
                },
                source_ids=[source_by_label["chzzk_profile_pool"]],
            )
            _append_validated(handle, record, schema)
            counts["profile_snapshot"] += 1

        with weekly_path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                row = json.loads(line)
                cid = str(row.get("channel_id") or "")
                key = weekly_map.get(cid)
                if key is None or key not in account_by_key:
                    continue
                account = account_by_key[key]
                for week in row.get("weeks") or []:
                    if not isinstance(week, dict) or not week.get("date"):
                        continue
                    start = str(week["date"])
                    try:
                        end = (date.fromisoformat(start) + timedelta(days=6)).isoformat()
                    except ValueError:
                        end = None
                    record = _observation(
                        account_id=account["account_id"],
                        label="weekly",
                        observed_at=SOURCE_DATES["weekly"],
                        period_start=start,
                        period_end=end,
                        granularity="week",
                        metrics={
                            "avg_live_views": week.get("avgLiveViews"),
                            "max_live_views": week.get("maxLiveViews"),
                            "air_time_hours": week.get("airTime"),
                            "max_follower_count": week.get("maxFollowerCount"),
                            "sample_count": week.get("sumCount"),
                            "avg_chat_count": week.get("avgChatCount"),
                            "viewership": week.get("viewership"),
                        },
                        source_ids=[source_by_label["softcon_weekly_series"]],
                    )
                    _append_validated(handle, record, schema)
                    counts["weekly"] += 1
                    if counts["weekly"] % 50000 == 0:
                        handle.flush()
                        progress.append({"event": "weekly_observations", "count": counts["weekly"]})

        handle.flush()
    counts["total"] = counts["softcon_snapshot"] + counts["profile_snapshot"] + counts["weekly"]
    return counts


def _observation(
    *, account_id: str,
    label: str,
    observed_at: str,
    period_start: str | None,
    period_end: str | None,
    granularity: str,
    metrics: dict[str, Any],
    source_ids: list[str],
) -> dict[str, Any]:
    return {
        "record_type": "observation",
        "observation_id": stable_id(
            "observation", account_id, label, observed_at, period_start or "none"
        ),
        "account_id": account_id,
        "observed_at": observed_at,
        "period_start": period_start,
        "period_end": period_end,
        "granularity": granularity,
        "metrics": metrics,
        "source_ids": source_ids,
    }


def _build_organization_seeds(
    path: Path, source_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lists = _load_simple_yaml_lists(path)
    organizations = []
    reviews = []
    for name in lists.get("agency_terms", []):
        organization_id = stable_id("organization", _normalized_name(name))
        organization = {
            "record_type": "organization",
            "organization_id": organization_id,
            "display_name": name,
            "aliases": [],
            "organization_type": "unknown",
            "domains": [],
            "review_status": "needs_review",
            "source_ids": [source_id],
        }
        organizations.append(organization)
        reviews.append(
            _review(
                entity_type="organization",
                entity_id=organization_id,
                issue_code="organization_seed_requires_official_source",
                severity="warning",
                details={"display_name": name},
                source_ids=[source_id],
            )
        )
    for domain in lists.get("email_domains", []):
        reviews.append(
            _review(
                entity_type="source",
                entity_id=source_id,
                issue_code="agency_domain_requires_organization_mapping",
                severity="info",
                details={"domain": domain},
                source_ids=[source_id],
            )
        )
    return organizations, reviews


def _load_simple_yaml_lists(path: Path) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            current = line[:-1].strip()
            data.setdefault(current, [])
        elif line.startswith("- ") and current:
            value = line[2:].strip().strip("\"'")
            if value:
                data[current].append(value)
    return data


def _review(
    *,
    entity_type: str,
    entity_id: str,
    issue_code: str,
    severity: str,
    details: dict[str, Any],
    source_ids: list[str],
) -> dict[str, Any]:
    natural_details = json.dumps(details, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "record_type": "review_item",
        "review_id": stable_id("review", entity_type, entity_id, issue_code, natural_details),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "issue_code": issue_code,
        "severity": severity,
        "status": "open",
        "details": details,
        "source_ids": sorted(set(source_ids)),
    }


def _write_records(path: Path, records: Iterable[dict[str, Any]], *, schema: dict[str, Any]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            _append_validated(handle, record, schema)
            count += 1
            if count % 1000 == 0:
                handle.flush()
        handle.flush()
    return count


def _append_validated(handle: TextIO, record: dict[str, Any], schema: dict[str, Any]) -> None:
    _validate_or_raise(record, schema)
    handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def _validate_or_raise(record: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = validate_record(record, schema=schema)
    if errors:
        raise BootstrapError(f"invalid {record.get('record_type')} record: {'; '.join(errors[:5])}")


def _validate_outputs(output_files: dict[str, Path], *, schema: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "sources": "source",
        "personas": "persona",
        "accounts": "account",
        "organizations": "organization",
        "observations": "observation",
        "review_queue": "review_item",
    }
    details = {}
    all_errors: list[str] = []
    for label, expected in checks.items():
        count, errors = validate_ndjson(
            output_files[label], expected_record_type=expected, schema=schema
        )
        details[label] = {"records": count, "errors": len(errors)}
        all_errors.extend(f"{label}: {error}" for error in errors[:100])
    return {"error_count": len(all_errors), "details": details, "errors": all_errors}


def _write_qa_sample(path: Path, accounts: list[dict[str, Any]], personas: list[dict[str, Any]]) -> None:
    persona_by_id = {row["persona_id"]: row for row in personas}
    sample = sorted(
        accounts,
        key=lambda row: hashlib.sha256(row["account_id"].encode("utf-8")).hexdigest(),
    )[: min(100, len(accounts))]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "account_id", "persona_id", "platform", "platform_account_id",
            "display_name", "vtuber_status", "activity_status",
            "manual_vtuber_ok", "manual_platform_ok", "manual_name_ok", "review_note",
        ])
        for account in sample:
            persona = persona_by_id[account["persona_id"]]
            writer.writerow([
                account["account_id"], account["persona_id"], account["platform"],
                account["platform_account_id"], account["display_name"],
                persona["vtuber_status"], persona["activity_status"], "", "", "", "",
            ])


def _render_report(summary: dict[str, Any]) -> str:
    platform_rows = "\n".join(
        f"| {platform} | {count:,} |" for platform, count in summary["platform_counts"].items()
    )
    review_rows = "\n".join(
        f"| `{issue}` | {count:,} |" for issue, count in summary["review_counts"].items()
    )
    return f"""# 대한민국 버튜버 레지스트리 로컬 부트스트랩 보고서

- 상태: `{summary['status']}`
- 생성: {summary['generated_at']}
- 외부 네트워크 접근: 없음
- secret 저장: 없음

## 결과

| 항목 | 건수 |
|---|---:|
| 소프트콘 플랫폼 원본 | {summary['input_counts']['softcon_rows']:,} |
| 주간 시계열 입력 | {summary['input_counts']['weekly_rows']:,} |
| 정규화 계정 | {summary['output_counts']['accounts']:,} |
| 임시 페르소나 | {summary['output_counts']['personas']:,} |
| 관측 레코드 | {summary['output_counts']['observations']:,} |
| 조직 시드 | {summary['output_counts']['organizations']:,} |
| 리뷰 항목 | {summary['output_counts']['review_items']:,} |

## 플랫폼

| 플랫폼 | 계정 |
|---|---:|
{platform_rows}

## 조인 감사

- 주간 시계열 직접 플랫폼 연결: {summary['join_counts']['weekly_direct_platform_matches']:,}
- 32자리 ID 형태로 치지직 판정: {summary['join_counts']['weekly_chzzk_id_shape_inferences']:,}
- 플랫폼 미해결: {summary['join_counts']['weekly_unresolved']:,}
- 소프트콘 원본에 있으나 주간 시계열이 없는 계정: {summary['join_counts']['softcon_without_weekly']:,}
- 치지직 프로필 조인: {summary['join_counts']['profiles_joined']:,}
- 프로필 전용 추가 계정: {summary['join_counts']['profile_only_accounts_added']:,}

## 리뷰 큐

| 사유 | 건수 |
|---|---:|
{review_rows}

## 판정

플랫폼 키는 `platform + platform_account_id`로 분리되어 SOOP·CIME·치지직 ID가 섞이지 않는다.
같은 이름의 타 플랫폼 계정은 자동 병합하지 않았고 리뷰 큐로만 보냈다.
현재 persona는 계정당 하나의 임시 개체이므로, 공식 교차링크 검증 후 병합해야 실제 인원 수가 된다.

## 다음 게이트

1. `manual_qa_sample_100.csv` 100건 수동 대조
2. 704개 치지직 ID형 추론 계정의 공개 프로필 보강
3. SOOP 109·CIME 177계정의 공식 계정 ID와 프로필 연결 검증
4. 조직 시드에 공식 출처를 붙인 뒤 affiliation 생성
"""


def _market_evidence(platform: str, from_softcon: bool) -> list[str]:
    evidence = [f"korean_platform:{platform}"]
    if from_softcon:
        evidence.append("softcon_virtual_ranking")
    return evidence


def _last_verified(*, raw: dict[str, Any] | None, weekly: bool, profile: dict[str, Any] | None) -> str:
    if weekly:
        return SOURCE_DATES["weekly"]
    if profile:
        return SOURCE_DATES["profiles"]
    if raw:
        return SOURCE_DATES["softcon"]
    return SOURCE_DATES["profiles"]


def _normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in normalized if char.isalnum())


def _unique_nonempty(values: Iterable[str], *, exclude: str) -> list[str]:
    result = []
    seen = {_normalized_name(exclude)}
    for value in values:
        value = value.strip()
        key = _normalized_name(value)
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def _account_sources(accounts: list[dict[str, Any]], account_id: str) -> list[str]:
    for account in accounts:
        if account["account_id"] == account_id:
            return list(account["source_ids"])
    return []


def _require_inputs(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise BootstrapError(f"missing input files: {missing}")


def _refuse_overwrite(paths: Iterable[Path], *, allow_existing: set[Path]) -> None:
    existing = [str(path) for path in paths if path.exists() and path not in allow_existing]
    if existing:
        raise BootstrapError(f"refusing to overwrite existing outputs: {existing}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class ProgressLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"generated_at": _now(), **event}, ensure_ascii=False) + "\n")
            handle.flush()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Korean VTuber registry bootstrap")
    parser.add_argument("--softcon", default=str(DEFAULT_SOFTCON))
    parser.add_argument("--weekly", default=str(DEFAULT_WEEKLY))
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILES))
    parser.add_argument("--agencies", default=str(DEFAULT_AGENCIES))
    parser.add_argument("--schema", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_bootstrap(args)
    print(json.dumps({
        "status": summary["status"],
        "output_counts": summary["output_counts"],
        "platform_counts": summary["platform_counts"],
        "validation_errors": summary["validation"]["error_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
