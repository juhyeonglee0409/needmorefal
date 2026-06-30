"""Verify Step 5 broadcast sample/full collection outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent.parent
SAMPLE_SPEC = PACKAGE_ROOT / "data" / "cohort" / "specs" / "구비바_§5_broadcast_sample_spec.json"
COHORT_DIR = PACKAGE_ROOT / "data" / "cohort" / "collected"
OUTPUT_DIR = COHORT_DIR / "broadcast_samples"
GUBIBA_BASELINE = PACKAGE_ROOT / "data" / "daily_stats" / "구비바_방송별_요약_586건_20260615.csv"
MANIFEST = OUTPUT_DIR / "_collection_manifest.json"
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


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader.fieldnames or []), list(reader)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"failed to read CSV {path}: {last_error}")


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def load_sample_unique() -> tuple[int, int, int]:
    data = json.loads(SAMPLE_SPEC.read_text(encoding="utf-8"))
    combined = data["samples"]["T1_main_general_game"] + data["samples"]["T2_aux_virtual"]
    unique = {item["channelId"] for item in combined}
    return len(data["samples"]["T1_main_general_game"]), len(data["samples"]["T2_aux_virtual"]), len(unique)


def load_full_counts() -> tuple[int, int]:
    t1 = [
        row
        for row in read_csv(COHORT_DIR / "cohort_final_main_general_game.csv")[1]
        if truthy(row.get("final_include"))
    ]
    t2 = [
        row
        for row in read_csv(COHORT_DIR / "cohort_final_aux_virtual.csv")[1]
        if truthy(row.get("final_include"))
    ]
    return len({row["channelId"] for row in t1}), len({row["channelId"] for row in t2})


def verify_outputs(min_rows: int) -> dict[str, Any]:
    files = list(OUTPUT_DIR.glob("T[12]/*_방송별_요약.csv"))
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for path in files:
        try:
            columns, rows = read_csv(path)
            missing = [col for col in EXPECTED_COLUMNS if col not in columns]
            record = {
                "path": str(path),
                "group": path.parent.name,
                "channel_id": path.name.replace("_방송별_요약.csv", ""),
                "row_count": len(rows),
                "missing_columns": missing,
            }
            if not missing and len(rows) >= min_rows:
                valid.append(record)
            else:
                invalid.append(record)
        except Exception as exc:  # noqa: BLE001
            invalid.append({"path": str(path), "error": str(exc)})

    sample_t1, sample_t2, sample_unique = load_sample_unique()
    full_t1, full_t2 = load_full_counts()
    baseline_columns, baseline_rows = read_csv(GUBIBA_BASELINE)

    manifest = None
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    return {
        "output_dir": str(OUTPUT_DIR),
        "sample_spec": {
            "t1_rows": sample_t1,
            "t2_rows": sample_t2,
            "unique_channels": sample_unique,
        },
        "full_candidates": {
            "t1_unique": full_t1,
            "t2_unique": full_t2,
            "total_before_cross_dedupe": full_t1 + full_t2,
        },
        "baseline": {
            "path": str(GUBIBA_BASELINE),
            "row_count": len(baseline_rows),
            "columns_match_expected": baseline_columns == EXPECTED_COLUMNS,
        },
        "collection": {
            "file_count": len(files),
            "valid_file_count": len(valid),
            "invalid_file_count": len(invalid),
            "groups": {
                "T1": sum(1 for item in valid if item.get("group") == "T1"),
                "T2": sum(1 for item in valid if item.get("group") == "T2"),
            },
            "meets_sample_minimum": len(valid) >= 60,
        },
        "invalid": invalid[:50],
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Step 5 broadcast outputs.")
    parser.add_argument("--min-rows", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = verify_outputs(args.min_rows)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["collection"]["invalid_file_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
