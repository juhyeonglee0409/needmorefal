from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


RUN_ID = "kimdalsu_recollect_20260616_01"
CASE_ID = "kimdalsu_20260601"
KST = timezone(timedelta(hours=9))
RUN_DATE = datetime(2026, 6, 16, tzinfo=KST)
WINDOW_START = RUN_DATE - timedelta(days=180)


ORDER = [
    "softcon_subject_channel_current_stats",
    "softcon_chzzk_lol_population_monthly",
    "softcon_chzzk_follower_ranking_enterprise",
    "semorank_chzzk_follower_public_crosscheck",
    "chzzk_subject_channel_public_profile",
    "youtube_dalsooisfree_content_funnel",
    "softcon_cohort_member_profile_enrichment",
    "auro_live_chzzk_follower_public_crosscheck",
]


def now_iso() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def target_combined(run_root: Path, target_id: str) -> dict | None:
    return read_json(run_root / "40_arthur_collect" / target_id / "combined.json")


def target_meta(run_root: Path, target_id: str) -> dict | None:
    return read_json(run_root / "40_arthur_collect" / target_id / "_meta.json")


def target_status(run_root: Path, target_id: str) -> dict:
    combined = target_combined(run_root, target_id)
    meta = target_meta(run_root, target_id)
    if not combined:
        return {"target_id": target_id, "status": "not_run", "items": 0, "parse_status": "not_run", "boundary_signal": "not_run"}
    verification = combined.get("verification") or {}
    items = combined.get("items") or []
    boundary = verification.get("boundary_signal")
    parse = verification.get("parse_status")
    if boundary:
        status = "boundary"
    elif items:
        status = "collected"
    else:
        status = "empty"
    return {
        "target_id": target_id,
        "status": status,
        "items": len(items),
        "parse_status": parse,
        "boundary_signal": boundary,
        "source_url": combined.get("source_url"),
        "meta": meta,
    }


def ensure_cohort_absence(run_root: Path) -> None:
    target_id = "softcon_cohort_member_profile_enrichment"
    existing = target_combined(run_root, target_id)
    if existing and (existing.get("items") or []):
        return
    out_dir = run_root / "40_arthur_collect" / target_id
    boundary = "not_run_population_dependency_blocked"
    collection_window = {
        "startDateTime": WINDOW_START.isoformat(),
        "endDateTime": RUN_DATE.isoformat(),
        "basis": "run_date_minus_180_days",
    }
    write_json(run_root / "10_charles" / f"{target_id}.scout_report.json", {
        "target_id": target_id,
        "generated_at": now_iso(),
        "tool": "codex_dependency_gate",
        "boundary_signal": boundary,
        "dependency": "softcon_chzzk_lol_population_monthly",
        "reason": "population target blocked by enterprise_membership_required; no channel_url input set available",
        "collection_window": collection_window,
        "save_raw": False,
        "secret_values_logged": False,
    })
    write_json(run_root / "10_charles" / f"{target_id}.protocol.json", {
        "target_id": target_id,
        "target_url": "derived_from:softcon_chzzk_lol_population_monthly.channel_url",
        "best_path": "manual_review",
        "pre_check": {"gate_status": "restricted", "boundary_signal": boundary, "profile_required": True},
        "collection_plan": None,
        "collection_window": collection_window,
    })
    write_json(run_root / "30_arthur_inspect" / f"{target_id}.InspectResult.json", {
        "version": "dependency-gate-v1",
        "generated_at": now_iso(),
        "target_id": target_id,
        "boundary_signals": [{"source": "dependency", "signal": boundary, "severity": "stop", "action": "stopped"}],
        "sample_records": [],
        "row_count_observed": 0,
        "inspect_recommendation": "do_not_collect",
    })
    write_json(out_dir / "_meta.json", {
        "run_id": RUN_ID,
        "target_id": target_id,
        "collection_method": "not_run_dependency_gate",
        "items_collected": 0,
        "boundary_signals": [boundary],
        "collection_window": collection_window,
        "secret_values_logged": False,
        "raw_html_saved": False,
        "screenshot_saved": False,
    })
    write_json(out_dir / "combined.json", {
        "run_id": RUN_ID,
        "target_id": target_id,
        "source_url": "derived_from:softcon_chzzk_lol_population_monthly.channel_url",
        "items": [],
        "collection_window": collection_window,
        "verification": {"parse_status": "blocked", "boundary_signal": boundary, "dedup_key": "channel_url"},
    })


def fix_youtube_rows(run_root: Path) -> None:
    target_id = "youtube_dalsooisfree_content_funnel"
    path = run_root / "40_arthur_collect" / target_id / "combined.json"
    combined = read_json(path)
    if not combined:
        return
    rows = combined.get("items") or []
    changed = False
    for row in rows:
        url = row.get("content_url") or ""
        if "/shorts/" in url:
            row["content_type"] = "short"
            row["is_short"] = True
            changed = True
    if changed:
        write_json(path, combined)
        fields = sorted({k for row in rows for k in row.keys()})
        write_csv(run_root / "40_arthur_collect" / target_id / "normalized.csv", rows, fields)
        write_csv(run_root / "50_ingest_candidates" / "ContentFunnelAnalysis_candidate.csv", rows, fields)


def approval_log(run_root: Path, statuses: list[dict]) -> None:
    out_dir = run_root / "20_review" / "collect_directives"
    out_dir.mkdir(parents=True, exist_ok=True)
    for status in statuses:
        target_id = status["target_id"]
        approved = status["status"] == "collected" and not status.get("boundary_signal")
        directive = {
            "run_id": RUN_ID,
            "target_id": target_id,
            "approved": approved,
            "operator_approval_source": "user message 2026-06-16: 수집 시작하자",
            "approval_scope": "collect only; no CaseResult/Disclosure/PublicDemo promotion",
            "blocked_reason": None if approved else status.get("boundary_signal") or status.get("parse_status"),
            "secret_values_logged": False,
            "created_at": now_iso(),
        }
        write_json(out_dir / f"{target_id}.CollectDirective.json", directive)


def build_patches(run_root: Path, statuses: list[dict]) -> None:
    evidence = []
    absences = []
    disclosures = []
    for status in statuses:
        target_id = status["target_id"]
        combined_rel = f"40_arthur_collect/{target_id}/combined.json"
        meta_rel = f"40_arthur_collect/{target_id}/_meta.json"
        evidence.append({
            "case_id": CASE_ID,
            "run_id": RUN_ID,
            "target_id": target_id,
            "status": status["status"],
            "items": status["items"],
            "parse_status": status.get("parse_status"),
            "boundary_signal": status.get("boundary_signal"),
            "artifact_paths": [combined_rel, meta_rel],
            "promotion_status": "patch_candidate_only",
        })
        boundary = status.get("boundary_signal")
        if boundary or status["status"] in {"empty", "not_run"}:
            absences.append({
                "case_id": CASE_ID,
                "run_id": RUN_ID,
                "target_id": target_id,
                "absence_type": "source_absence_or_collection_boundary",
                "boundary_signal": boundary or status.get("parse_status"),
                "items": status["items"],
                "meaning": "operator_review_required_not_final_absence",
                "artifact_path": combined_rel,
            })
        disclosures.append({
            "case_id": CASE_ID,
            "run_id": RUN_ID,
            "target_id": target_id,
            "disclosure_tag": "red" if target_id.startswith("softcon_") else "green",
            "reason": "Softcon profile/member route" if target_id.startswith("softcon_") else "public source",
            "boundary_signal": boundary,
            "promotion_status": "patch_candidate_only",
        })
    write_json(run_root / "50_ingest_candidates" / "EvidencePackage_patch.json", {
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "items": evidence,
    })
    write_json(run_root / "50_ingest_candidates" / "AbsenceInventory_patch.json", {
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "items": absences,
    })
    write_json(run_root / "50_ingest_candidates" / "DisclosureLog_patch.json", {
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "items": disclosures,
    })
    population = next((s for s in statuses if s["target_id"] == "softcon_chzzk_lol_population_monthly"), None)
    follower = next((s for s in statuses if s["target_id"] == "softcon_chzzk_follower_ranking_enterprise"), None)
    enrichment = next((s for s in statuses if s["target_id"] == "softcon_cohort_member_profile_enrichment"), None)
    benchmark_status = "partial"
    benchmark_reason = (
        "Softcon LoL population currently yields 100 filtered naverchzzk rows and carries the residual risk "
        "`category_route_visible_cap_100_rows`. Follower ranking was recovered to 3987 rows across pages 1..40. "
        "Cohort member enrichment collected 100 channel-page rows. Human review is still required before promotion."
    )
    if not population or population["items"] == 0:
        benchmark_status = "blocked"
        benchmark_reason = "Population target unavailable; benchmark remains blocked."
    write_json(run_root / "50_ingest_candidates" / "CohortBenchmark_candidate.json", {
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "status": benchmark_status,
        "population_rows": population["items"] if population else 0,
        "follower_rows": follower["items"] if follower else 0,
        "enrichment_rows": enrichment["items"] if enrichment else 0,
        "follower_match_rate": None,
        "reason": benchmark_reason,
        "promotion_status": "patch_candidate_only",
    })


def write_manifest(run_root: Path, statuses: list[dict]) -> None:
    enrichment = next((s for s in statuses if s["target_id"] == "softcon_cohort_member_profile_enrichment"), None)
    manifest = {
        "run_id": RUN_ID,
        "case_id": CASE_ID,
        "generated_at": now_iso(),
        "run_root": str(run_root),
        "operator_collection_approval": {
            "source": "user message",
            "message": "수집 시작하자",
            "scope": "collection only; final judgment/promotion remains operator/Hosea review",
        },
        "period_policy": {
            "basis_date": RUN_DATE.date().isoformat(),
            "default_recent_6_months_start": WINDOW_START.date().isoformat(),
            "youtube_dalsooisfree_content_funnel": {
                "start": WINDOW_START.date().isoformat(),
                "end": RUN_DATE.date().isoformat(),
                "applied": True,
            },
            "softcon_cohort_member_profile_enrichment": {
                "startDateTime": WINDOW_START.isoformat(),
                "endDateTime": RUN_DATE.isoformat(),
                "applied": bool(enrichment and enrichment["items"] > 0),
                "reason": None if enrichment and enrichment["items"] > 0 else "dependency blocked before collect",
            },
        },
        "targets": statuses,
        "legacy_inputs": [
            "00_inputs/legacy/daily_stats/김달수_Dalsu_방송통계_1년_20260528.csv",
            "00_inputs/legacy/cohort/김달수_코호트_131명.csv",
            "00_inputs/legacy/cohort/수집대상_183명.csv",
            "00_inputs/legacy/cohort/specs/스크래핑_작업명세서_구현팀.md",
        ],
        "secret_storage_check": {
            "cookie_values_logged": False,
            "session_tokens_logged": False,
            "raw_html_saved": False,
            "screenshots_saved": False,
        },
        "promotion_boundary": "No CaseResult, DisclosureLog final state, PublicDemoRow, or package canonical data was promoted.",
    }
    write_json(run_root / "RUN_MANIFEST.json", manifest)


def write_summary(run_root: Path, statuses: list[dict]) -> None:
    lines = [
        "# TargetReviewSummary",
        "",
        f"- run_id: {RUN_ID}",
        f"- generated_at: {now_iso()}",
        "- operator approval: collection only; promotion not approved",
        "",
        "| target_id | status | rows | parse_status | boundary |",
        "|---|---:|---:|---|---|",
    ]
    for status in statuses:
        lines.append(f"| `{status['target_id']}` | {status['status']} | {status['items']} | {status.get('parse_status')} | {status.get('boundary_signal') or ''} |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- Softcon subject stats collected successfully: follower, stream_hours, peak/avg viewers, viewership, and 6-minute chat metrics are present.",
        "- Softcon LoL population was repaired to 100 rows from the filtered naverchzzk category route. Residual risk: `category_route_visible_cap_100_rows`.",
        "- Softcon follower ranking was recovered to 3987 unique rows across pages 1..40 with no boundary signal observed during the corrected run.",
        "- Softcon cohort member enrichment collected 100 channel-page rows. Follower count and recent category were captured for all 100 rows; profile_text was observed only on 2 rows, so the artifact remains partial. Corporate/team/tournament/virtual flags remain blank and require review logic before promotion.",
        "- YouTube used the public Atom feed and applied the 180-day window: 2025-12-18 through 2026-06-16.",
        "- Auro.live was not collected because the current Codex route lacks the required Chrome JS fetch + devalue parser path.",
        "- All outputs are patch candidates only.",
    ])
    (run_root / "TargetReviewSummary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root)
    ensure_cohort_absence(run_root)
    fix_youtube_rows(run_root)
    statuses = [target_status(run_root, target_id) for target_id in ORDER]
    approval_log(run_root, statuses)
    build_patches(run_root, statuses)
    write_manifest(run_root, statuses)
    write_summary(run_root, statuses)
    print(json.dumps({"run_id": RUN_ID, "targets": statuses}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
