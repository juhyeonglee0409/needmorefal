"""BERTH 모드 경계 명문화 효과 검증 — 새 프롬프트의 G35 vs G31, 동일 100건.

비교 기준(구 프롬프트, p3_model_matrix): berth κ(G35,G31)=0.768.
사용법: cd corpus && python p3_berth_check.py
산출: data/analysis/p3_berth_check.txt
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from p3_cross_validate import cohens_kappa
from retag_full_v2 import tag_one

DATA = Path(__file__).parent / "data" / "analysis"
SAMPLE_PATH = DATA / "p3_sample.ndjson"
CACHE = DATA / "p3_berth_check_tags.ndjson"
OUT = DATA / "p3_berth_check.txt"
MODELS = {"G35n": "gemini-3.5-flash", "G31n": "gemini-3.1-pro-preview"}
AXES = ["berth", "channel", "sounding", "heading"]


def main():
    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    cache: dict[tuple[str, str], dict] = {}
    if CACHE.exists():
        for l in CACHE.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                cache[(r["rater"], r["content_id"])] = r["tiller"]

    jobs = [(rater, r) for rater in MODELS for r in sample if (rater, r["content_id"]) not in cache]
    print(f"샘플 {len(sample)}건 × 2 rater / 캐시 {len(cache)} / 신규 호출 {len(jobs)}")
    if jobs:
        with open(CACHE, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=10) as pool:
            futs = {pool.submit(tag_one, MODELS[rater], r["body"] or ""): (rater, r["content_id"]) for rater, r in jobs}
            done = 0
            for fut in as_completed(futs):
                rater, cid = futs[fut]
                tags = fut.result()
                if tags:
                    out.write(json.dumps({"rater": rater, "content_id": cid, "tiller": tags}, ensure_ascii=False) + "\n")
                    out.flush()
                    cache[(rater, cid)] = tags
                done += 1
                if done % 40 == 0:
                    print(f"  {done}/{len(jobs)}")

    common = [r["content_id"] for r in sample if ("G35n", r["content_id"]) in cache and ("G31n", r["content_id"]) in cache]
    lines = ["BERTH 모드 경계 검증 — 새 프롬프트 G35 vs G31", "=" * 46, f"공통 유효 {len(common)}건", ""]

    for axis in AXES:
        a = [str(cache[("G35n", cid)].get(axis)) if cache[("G35n", cid)].get(axis) is not None else "null" for cid in common]
        b = [str(cache[("G31n", cid)].get(axis)) if cache[("G31n", cid)].get(axis) is not None else "null" for cid in common]
        k = cohens_kappa(a, b)
        agree = sum(1 for x, y in zip(a, b) if x == y) / len(a) * 100
        lines.append(f"  {axis:10s}: κ={k:.3f}  일치율={agree:.1f}%")

    # berth 상세: 공동 검출 사례의 모드 일치
    co = [(cache[("G35n", cid)].get("berth"), cache[("G31n", cid)].get("berth")) for cid in common
          if cache[("G35n", cid)].get("berth") and cache[("G31n", cid)].get("berth")]
    mode_agree = sum(1 for x, y in co if x == y)
    lines += [
        "",
        f"berth 공동 검출 {len(co)}건 중 모드 일치 {mode_agree}건 ({mode_agree/len(co)*100:.0f}%)" if co else "berth 공동 검출 0건",
        "구 프롬프트 기준선: berth κ(G35,G31)=0.768 (p3_model_matrix)",
    ]

    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
