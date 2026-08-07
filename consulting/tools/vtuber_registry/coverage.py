"""Generate a current, evidence-aware coverage report for a registry run."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def generate_coverage_report(run_dir: str | Path) -> dict[str, Any]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    review_dir = run / "40_review"
    coverage_dir = run / "50_coverage"

    sources = list(_iter_ndjson(normalized / "sources.ndjson"))
    personas = list(_iter_ndjson(normalized / "personas.ndjson"))
    accounts = list(_iter_ndjson(normalized / "accounts.ndjson"))
    organizations = list(_iter_ndjson(normalized / "organizations.ndjson"))
    affiliations = list(_iter_ndjson(normalized / "affiliations.ndjson"))
    reviews = list(_iter_ndjson(review_dir / "review_queue.ndjson"))

    platform_counts = Counter(record["platform"] for record in accounts)
    source_tiers = Counter(record["source_tier"] for record in sources)
    organization_statuses = Counter(record["review_status"] for record in organizations)
    review_statuses = Counter(record["status"] for record in reviews)
    open_review_codes = Counter(
        record["issue_code"] for record in reviews if record["status"] == "open"
    )
    resolved_review_codes = Counter(
        record["issue_code"] for record in reviews if record["status"] == "resolved"
    )

    official_candidates = _read_csv(review_dir / "official_account_candidates.csv")
    official_candidate_statuses = Counter(row["status"] for row in official_candidates)
    qa_rows = _read_csv(review_dir / "manual_qa_sample_100.csv")
    qa_completed = sum(
        bool(row.get("manual_vtuber_ok"))
        and bool(row.get("manual_platform_ok"))
        and bool(row.get("manual_name_ok"))
        for row in qa_rows
    )
    evidence_path = review_dir / "manual_qa_public_evidence_100.csv"
    evidence_rows = _read_csv(evidence_path) if evidence_path.exists() else []
    successful_evidence = [row for row in evidence_rows if row["fetch_status"] == "ok"]
    nonblank_expected = [row for row in successful_evidence if row["expected_name"]]
    qa_public_evidence = {
        "rows": len(evidence_rows),
        "successful_public_profiles": len(successful_evidence),
        "not_checked_non_chzzk": sum(row["fetch_status"] == "not_checked" for row in evidence_rows),
        "nonblank_expected_names": len(nonblank_expected),
        "exact_name_matches": sum(row["normalized_name_match"] == "yes" for row in nonblank_expected),
        "name_changes_queued": sum(row["normalized_name_match"] == "no" for row in nonblank_expected),
        "blank_names_backfilled": sum(not row["expected_name"] for row in successful_evidence),
        "explicit_vtuber_text_signals": sum(
            row["explicit_vtuber_signal"] == "yes" for row in successful_evidence
        ),
    }

    generated_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    report = {
        "generated_at": generated_at,
        "status": "in_progress_manual_qa_and_platform_expansion_pending",
        "counts": {
            "sources": len(sources),
            "personas": len(personas),
            "accounts": len(accounts),
            "organizations": len(organizations),
            "affiliations": len(affiliations),
            "reviews": len(reviews),
        },
        "platform_counts": dict(sorted(platform_counts.items())),
        "source_tier_counts": dict(sorted(source_tiers.items())),
        "organization_status_counts": dict(sorted(organization_statuses.items())),
        "review_status_counts": dict(sorted(review_statuses.items())),
        "open_review_counts": dict(sorted(open_review_codes.items())),
        "resolved_review_counts": dict(sorted(resolved_review_codes.items())),
        "official_account_candidate_counts": dict(sorted(official_candidate_statuses.items())),
        "manual_qa": {"sample_size": len(qa_rows), "completed": qa_completed},
        "public_profile_qa_evidence": qa_public_evidence,
        "known_coverage_gaps": [
            {
                "code": "softcon_soop_official_handle_gap",
                "count": official_candidate_statuses.get("missing_from_softcon_seed", 0),
                "note": "Official ISEGYE IDOL SOOP handles absent from the Softcon seed.",
            },
            {
                "code": "softcon_cid_not_official_soop_handle",
                "count": official_candidate_statuses.get("needs_account_and_identity_review", 0),
                "note": "AKAIV official SOOP handles require identity reconciliation; Softcon cid is not assumed to be the handle.",
            },
            {
                "code": "youtube_independent_population_not_systematically_discovered",
                "count": None,
                "note": (
                    f"{platform_counts.get('youtube', 0)} official-linked YouTube seed accounts are present, "
                    "but YouTube-only and independent YouTube-primary Korean VTubers remain outside the current population frame."
                ),
            },
            {
                "code": "manual_qa_incomplete",
                "count": len(qa_rows) - qa_completed,
                "note": "The stratified 100-account manual QA sheet is not yet closed.",
            },
        ],
        "collection_boundaries": {
            "public_web_research_used": True,
            "logged_in_session_used": False,
            "external_contact_performed": False,
            "secrets_stored": False,
        },
    }

    coverage_dir.mkdir(parents=True, exist_ok=True)
    json_path = coverage_dir / "coverage_status.json"
    md_path = coverage_dir / "unresolved_population.md"
    manifest_path = run / "run_manifest_post_enrichment.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    base_manifest = run / "run_manifest.json"
    manifest = {
        "run_id": run.name,
        "status": report["status"],
        "generated_at": generated_at,
        "base_manifest": str(base_manifest.resolve()),
        "base_manifest_sha256": _sha256(base_manifest),
        "public_web_research": True,
        "logged_in_session_used": False,
        "external_contact_performed": False,
        "secret_values_stored": False,
        "counts": report["counts"],
        "platform_counts": report["platform_counts"],
        "review_status_counts": report["review_status_counts"],
        "manual_qa": report["manual_qa"],
        "coverage_report": str(json_path.resolve()),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    count_rows = "\n".join(
        f"| {name} | {count:,} |" for name, count in report["counts"].items()
    )
    platform_rows = "\n".join(
        f"| {name} | {count:,} |" for name, count in report["platform_counts"].items()
    )
    open_rows = "\n".join(
        f"| `{name}` | {count:,} |" for name, count in report["open_review_counts"].items()
    ) or "| - | 0 |"
    gaps = "\n".join(
        f"- `{item['code']}`: "
        + (f"{item['count']:,}건. " if isinstance(item["count"], int) else "규모 미산정. ")
        + item["note"]
        for item in report["known_coverage_gaps"]
    )
    qa = report["manual_qa"]
    public_qa = report["public_profile_qa_evidence"]
    return f"""# 미해결 모집단과 커버리지 현황

- 상태: `{report['status']}`
- 생성: {report['generated_at']}
- 로그인 세션 사용: 없음
- 외부 연락: 없음

## 현재 원장

| 항목 | 건수 |
|---|---:|
{count_rows}

| 플랫폼 | 계정 |
|---|---:|
{platform_rows}

조직 시드 12곳은 공식 출처 검증을 마쳤고, 버츄얼 유니온 공식 회원사 4곳을 추가했어요.
공식 소속과 이름이 정확히 하나의 기존 persona에 대응한 {report['counts']['affiliations']:,}건만
affiliation으로 물질화했어요.

## 열린 검토 항목

| 사유 | 건수 |
|---|---:|
{open_rows}

## 알려진 커버리지 공백

{gaps}

## 수동 QA

- 표본: {qa['sample_size']:,}건
- 완료: {qa['completed']:,}건
- 미완료: {qa['sample_size'] - qa['completed']:,}건

공개 프로필 사전 검증은 CHZZK {public_qa['successful_public_profiles']:,}건을 완료했어요.
기존 이름이 있던 {public_qa['nonblank_expected_names']:,}건 중
{public_qa['exact_name_matches']:,}건이 일치했고, {public_qa['name_changes_queued']:,}건은
이름 변경 검토 큐로 보냈어요. 빈 이름 {public_qa['blank_names_backfilled']:,}건은 현재 공개 이름으로 채웠어요.
프로필 텍스트에 버튜버 표현이 명시된 것은 {public_qa['explicit_vtuber_text_signals']:,}건뿐이므로,
텍스트 신호가 없는 계정은 자동 확정하지 않았어요.

따라서 현재 원장은 CHZZK·SOOP·CIME의 강한 출발점이지만, 아직 대한민국 활동 버튜버
‘전원’ 원장이라고 부를 단계는 아니에요. 다음 모집단 확장은 YouTube-only/YouTube-primary
계정 발견과 공식 SOOP 계정 후보 11건의 식별 병합이에요.
"""


def _iter_ndjson(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
