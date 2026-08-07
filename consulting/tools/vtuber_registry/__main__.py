"""Command line entrypoint."""

from __future__ import annotations

import argparse

from .audit import run_audit
from . import bootstrap
from .coverage import generate_coverage_report
from .enrich_organizations import run_enrichment
from .enrich_youtube import enrich_official_youtube_seeds
from .qa_profiles import apply_qa_public_evidence, collect_qa_public_evidence
from .reconcile_soop import reconcile_official_soop
from .validate import load_schema, validate_ndjson


def main() -> int:
    parser = argparse.ArgumentParser(prog="vtuber_registry")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bootstrap = sub.add_parser("bootstrap", help="Run the offline local bootstrap")
    p_bootstrap.add_argument("--softcon", default=str(bootstrap.DEFAULT_SOFTCON))
    p_bootstrap.add_argument("--weekly", default=str(bootstrap.DEFAULT_WEEKLY))
    p_bootstrap.add_argument("--profiles", default=str(bootstrap.DEFAULT_PROFILES))
    p_bootstrap.add_argument("--agencies", default=str(bootstrap.DEFAULT_AGENCIES))
    p_bootstrap.add_argument("--schema", default=None)
    p_bootstrap.add_argument("--output", default=str(bootstrap.DEFAULT_OUTPUT))

    p_validate = sub.add_parser("validate", help="Validate an NDJSON registry artifact")
    p_validate.add_argument("path")
    p_validate.add_argument("--record-type", default=None)
    p_validate.add_argument("--schema", default=None)

    p_audit = sub.add_parser("audit", help="Audit generated registry referential integrity")
    p_audit.add_argument("run_dir")
    p_audit.add_argument("--output-suffix", default="")

    p_enrich = sub.add_parser(
        "enrich-organizations",
        help="Apply reviewed official organization evidence without crawling",
    )
    p_enrich.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")

    p_soop = sub.add_parser(
        "reconcile-soop",
        help="Materialize reviewed official SOOP accounts from preserved public evidence",
    )
    p_soop.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")

    p_youtube = sub.add_parser(
        "enrich-youtube-seeds",
        help="Add YouTube channels directly linked from official organization or group evidence",
    )
    p_youtube.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")

    p_coverage = sub.add_parser("coverage", help="Generate the current coverage and gap report")
    p_coverage.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")

    p_qa = sub.add_parser("qa-public-profiles", help="Fetch public profile evidence for the fixed QA sample")
    p_qa.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")
    p_qa.add_argument("--delay-seconds", type=float, default=0.35)

    p_qa_apply = sub.add_parser("qa-apply-evidence", help="Apply safe QA name backfills and queue name changes")
    p_qa_apply.add_argument("run_dir", nargs="?", default="consulting/runs/vtuber_registry_20260805")

    args = parser.parse_args()
    if args.command == "bootstrap":
        summary = bootstrap.run_bootstrap(args)
        print(summary["output_counts"])
        return 0
    if args.command == "validate":
        count, errors = validate_ndjson(
            args.path,
            expected_record_type=args.record_type,
            schema=load_schema(args.schema),
        )
        print({"records": count, "errors": len(errors)})
        for error in errors[:100]:
            print(error)
        return 1 if errors else 0
    if args.command == "audit":
        result = run_audit(args.run_dir, output_suffix=args.output_suffix)
        print({"status": result["status"], "problems": result["problems"]})
        return 0 if result["status"] == "pass" else 1
    if args.command == "enrich-organizations":
        print(run_enrichment(args.run_dir))
        return 0
    if args.command == "reconcile-soop":
        print(reconcile_official_soop(args.run_dir))
        return 0
    if args.command == "enrich-youtube-seeds":
        print(enrich_official_youtube_seeds(args.run_dir))
        return 0
    if args.command == "coverage":
        report = generate_coverage_report(args.run_dir)
        print({"status": report["status"], "counts": report["counts"]})
        return 0
    if args.command == "qa-public-profiles":
        print(collect_qa_public_evidence(args.run_dir, delay_seconds=args.delay_seconds))
        return 0
    if args.command == "qa-apply-evidence":
        print(apply_qa_public_evidence(args.run_dir))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
