"""SOUNDING 주의 5·6 (표면 명시·부연 배제) 효과 검증 — 교차 가문 쌍 재측정.

기준선 (주의 4까지의 프롬프트, p3_family_check): sounding κ — C↔G35n 0.55, C↔G31n 0.59,
O2↔C 0.61, O2↔G35n 0.52 (이종 평균 0.547, 가족 내 0.747).

측정: 주의 5·6 추가 프롬프트로 G35·Claude 재태깅 → 교차 가문 sounding κ.
사용법: cd corpus && python p3_so_anchor_check.py
산출: data/analysis/p3_so_anchor_check.txt
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from p3_cross_validate import cohens_kappa
from p3_family_check import api_tag  # O2/C 태깅 함수 (llm_client 경유)
from retag_full_v2 import tag_one  # Vertex 태깅 함수

DATA = Path(__file__).parent / "data" / "analysis"
SAMPLE_PATH = DATA / "p3_sample.ndjson"
CACHE = DATA / "p3_so_anchor_tags.ndjson"
OUT = DATA / "p3_so_anchor_check.txt"

BASE = {"sounding": {"C-G35": 0.55, "채점불가기준": None}}
AXES = ["sounding", "channel", "heading", "berth"]


def tag(rater: str, body: str) -> dict | None:
    if rater == "G35a":
        return tag_one("gemini-3.5-flash", body)
    return api_tag("C", body)  # Ca


def main():
    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    cache: dict[tuple[str, str], dict] = {}
    if CACHE.exists():
        for l in CACHE.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                cache[(r["rater"], r["content_id"])] = r["tiller"]

    jobs = [(rater, r) for rater in ("G35a", "Ca") for r in sample if (rater, r["content_id"]) not in cache]
    print(f"신규 호출 {len(jobs)}건 (주의 5·6 반영 프롬프트)")
    if jobs:
        with open(CACHE, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=10) as pool:
            futs = {pool.submit(tag, rater, r["body"] or ""): (rater, r["content_id"]) for rater, r in jobs}
            done = 0
            for fut in as_completed(futs):
                rater, cid = futs[fut]
                t = fut.result()
                if t:
                    out.write(json.dumps({"rater": rater, "content_id": cid, "tiller": t}, ensure_ascii=False) + "\n")
                    out.flush()
                    cache[(rater, cid)] = t
                done += 1
                if done % 40 == 0:
                    print(f"  {done}/{len(jobs)}")

    common = [r["content_id"] for r in sample if ("G35a", r["content_id"]) in cache and ("Ca", r["content_id"]) in cache]
    lab = lambda v: str(v) if v is not None else "null"  # noqa: E731
    lines = [
        "SOUNDING 주의 5·6 효과 검증 — 교차 가문 (G35 ↔ claude-sonnet-5, 신 프롬프트)",
        "=" * 56,
        f"공통 유효 {len(common)}건",
        "",
    ]
    for axis in AXES:
        a = [lab(cache[("G35a", cid)].get(axis)) for cid in common]
        b = [lab(cache[("Ca", cid)].get(axis)) for cid in common]
        k = cohens_kappa(a, b)
        agree = sum(1 for x, y in zip(a, b) if x == y) / len(a) * 100
        base = " (기준선 C↔G35n: 0.55)" if axis == "sounding" else ""
        lines.append(f"  {axis:10s}: κ={k:.3f}  일치율={agree:.1f}%{base}")

    from collections import Counter
    d35 = Counter(int(cache[("G35a", cid)].get("sounding") or 1) for cid in common)
    dc = Counter(int(cache[("Ca", cid)].get("sounding") or 1) for cid in common)
    nn = len(common)
    lines += [
        "",
        f"So≥2 비율: G35 {sum(v for k2, v in d35.items() if k2 >= 2)/nn*100:.1f}% / Claude {sum(v for k2, v in dc.items() if k2 >= 2)/nn*100:.1f}%",
    ]
    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
