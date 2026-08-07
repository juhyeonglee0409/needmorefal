"""Referential-integrity audit for a generated registry run."""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def run_audit(run_dir: str | Path, output_suffix: str = "") -> dict[str, Any]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    review_dir = run / "40_review"
    coverage = run / "50_coverage"
    if output_suffix and not output_suffix.startswith("_"):
        output_suffix = "_" + output_suffix
    output_json = coverage / f"integrity_audit{output_suffix}.json"
    output_md = coverage / f"integrity_audit{output_suffix}.md"
    if output_json.exists() or output_md.exists():
        raise FileExistsError("refusing to overwrite existing integrity audit")

    paths = {
        "sources": normalized / "sources.ndjson",
        "personas": normalized / "personas.ndjson",
        "accounts": normalized / "accounts.ndjson",
        "organizations": normalized / "organizations.ndjson",
        "affiliations": normalized / "affiliations.ndjson",
        "observations": normalized / "observations.ndjson",
        "reviews": review_dir / "review_queue.ndjson",
    }
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        raise FileNotFoundError(f"missing registry artifacts: {missing_files}")

    source_ids, source_duplicates, source_records = _ids(paths["sources"], "source_id")
    persona_ids, persona_duplicates, persona_records = _ids(paths["personas"], "persona_id")
    account_ids, account_duplicates, account_records = _ids(paths["accounts"], "account_id")
    organization_ids, organization_duplicates, organization_records = _ids(
        paths["organizations"], "organization_id"
    )
    affiliation_ids, affiliation_duplicates, affiliation_records = _ids(
        paths["affiliations"], "affiliation_id"
    )

    natural_keys: set[tuple[str, str]] = set()
    duplicate_natural_keys: list[str] = []
    missing_persona_refs: list[str] = []
    missing_source_refs: Counter[str] = Counter()
    platform_counts: Counter[str] = Counter()
    for record in _iter_ndjson(paths["accounts"]):
        key = (str(record.get("platform")), str(record.get("platform_account_id")))
        if key in natural_keys:
            duplicate_natural_keys.append(":".join(key))
        natural_keys.add(key)
        platform_counts[str(record.get("platform"))] += 1
        if record.get("persona_id") not in persona_ids:
            missing_persona_refs.append(str(record.get("account_id")))
        _count_missing_sources(record, source_ids, missing_source_refs, "account")

    persona_missing_sources = Counter()
    for record in _iter_ndjson(paths["personas"]):
        _count_missing_sources(record, source_ids, persona_missing_sources, "persona")
    missing_source_refs.update(persona_missing_sources)

    observation_count = 0
    missing_observation_accounts = 0
    observation_ids: set[str] = set()
    duplicate_observation_ids = 0
    for record in _iter_ndjson(paths["observations"]):
        observation_count += 1
        observation_id = str(record.get("observation_id"))
        if observation_id in observation_ids:
            duplicate_observation_ids += 1
        observation_ids.add(observation_id)
        if record.get("account_id") not in account_ids:
            missing_observation_accounts += 1
        _count_missing_sources(record, source_ids, missing_source_refs, "observation")

    missing_affiliation_personas = 0
    missing_affiliation_organizations = 0
    for record in _iter_ndjson(paths["affiliations"]):
        if record.get("persona_id") not in persona_ids:
            missing_affiliation_personas += 1
        if record.get("organization_id") not in organization_ids:
            missing_affiliation_organizations += 1
        _count_missing_sources(record, source_ids, missing_source_refs, "affiliation")

    review_count = 0
    review_ids: set[str] = set()
    duplicate_review_ids = 0
    missing_review_entities = 0
    entity_sets = {
        "persona": persona_ids,
        "account": account_ids,
        "organization": organization_ids,
        "affiliation": affiliation_ids,
        "source": source_ids,
        "observation": observation_ids,
    }
    for record in _iter_ndjson(paths["reviews"]):
        review_count += 1
        review_id = str(record.get("review_id"))
        if review_id in review_ids:
            duplicate_review_ids += 1
        review_ids.add(review_id)
        entity_type = str(record.get("entity_type"))
        entity_id = record.get("entity_id")
        if entity_type not in entity_sets or entity_id not in entity_sets[entity_type]:
            missing_review_entities += 1
        _count_missing_sources(record, source_ids, missing_source_refs, "review")

    problems = {
        "duplicate_source_ids": len(source_duplicates),
        "duplicate_persona_ids": len(persona_duplicates),
        "duplicate_account_ids": len(account_duplicates),
        "duplicate_organization_ids": len(organization_duplicates),
        "duplicate_affiliation_ids": len(affiliation_duplicates),
        "duplicate_observation_ids": duplicate_observation_ids,
        "duplicate_review_ids": duplicate_review_ids,
        "duplicate_account_natural_keys": len(duplicate_natural_keys),
        "missing_account_persona_refs": len(missing_persona_refs),
        "missing_observation_account_refs": missing_observation_accounts,
        "missing_affiliation_persona_refs": missing_affiliation_personas,
        "missing_affiliation_organization_refs": missing_affiliation_organizations,
        "missing_review_entity_refs": missing_review_entities,
        "missing_source_refs": sum(missing_source_refs.values()),
    }
    result = {
        "status": "pass" if sum(problems.values()) == 0 else "fail",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "counts": {
            "sources": source_records,
            "personas": persona_records,
            "accounts": account_records,
            "organizations": organization_records,
            "affiliations": affiliation_records,
            "observations": observation_count,
            "reviews": review_count,
        },
        "platform_counts": dict(sorted(platform_counts.items())),
        "problems": problems,
        "missing_source_ref_types": dict(sorted(missing_source_refs.items())),
        "samples": {
            "duplicate_account_natural_keys": duplicate_natural_keys[:20],
            "missing_account_persona_refs": missing_persona_refs[:20],
        },
    }
    coverage.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(_render_markdown(result), encoding="utf-8")
    return result


def _ids(path: Path, key: str) -> tuple[set[str], set[str], int]:
    values: set[str] = set()
    duplicates: set[str] = set()
    count = 0
    for record in _iter_ndjson(path):
        count += 1
        value = str(record.get(key) or "")
        if value in values:
            duplicates.add(value)
        values.add(value)
    return values, duplicates, count


def _iter_ndjson(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: record is not object")
            yield record


def _count_missing_sources(
    record: dict[str, Any],
    source_ids: set[str],
    counter: Counter[str],
    label: str,
) -> None:
    for source_id in record.get("source_ids") or []:
        if source_id not in source_ids:
            counter[label] += 1


def _render_markdown(result: dict[str, Any]) -> str:
    problem_rows = "\n".join(
        f"| `{name}` | {count:,} |" for name, count in result["problems"].items()
    )
    count_rows = "\n".join(
        f"| {name} | {count:,} |" for name, count in result["counts"].items()
    )
    return f"""# Registry Referential Integrity Audit

- status: **{result['status']}**
- generated_at: {result['generated_at']}

## Counts

| artifact | records |
|---|---:|
{count_rows}

## Problems

| invariant | count |
|---|---:|
{problem_rows}
"""
