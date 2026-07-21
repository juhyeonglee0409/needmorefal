"""So1/So2 경계 명문화(주의 4) 효과 검증 — G31 교집합 284건을 새 프롬프트의
gemini-3.5-flash로 재태깅해서, 경계 수정이 G31의 보수적 판정에 수렴하는지 본다.

사용법: cd corpus && python so_boundary_fix_check.py
산출: data/analysis/so_boundary_fix_check.txt
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from p3_cross_validate import cohens_kappa
from retag_full_v2 import tag_one

DATA = Path(__file__).parent / "data"
G31_PATH = DATA / "corpus_tagged_v2_g31_partial.ndjson"
CACHE = DATA / "analysis" / "so_boundary_fix_tags.ndjson"
OUT = DATA / "analysis" / "so_boundary_fix_check.txt"
MODEL = "gemini-3.5-flash"


def main():
    g31 = {}
    for l in G31_PATH.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("tiller"):
                g31[r["content_id"]] = r

    cached = {}
    if CACHE.exists():
        for l in CACHE.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                cached[r["content_id"]] = r["tiller"]

    from concurrent.futures import ThreadPoolExecutor

    todo = [cid for cid in g31 if cid not in cached]
    print(f"교집합 {len(g31)}건 / 캐시 {len(cached)}건 / 재태깅 {len(todo)}건 ({MODEL}, 새 프롬프트)")
    if todo:
        with open(CACHE, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=16) as pool:
            futs = {pool.submit(tag_one, MODEL, g31[cid]["body"] or ""): cid for cid in todo}
            done = 0
            for fut in futs:
                pass
            from concurrent.futures import as_completed
            for fut in as_completed(futs):
                cid = futs[fut]
                tags = fut.result()
                if tags:
                    out.write(json.dumps({"content_id": cid, "tiller": tags}, ensure_ascii=False) + "\n")
                    out.flush()
                    cached[cid] = tags
                done += 1
                if done % 50 == 0:
                    print(f"  {done}/{len(todo)}")

    common = [cid for cid in g31 if cid in cached]
    a = [str(int(g31[cid]["tiller"].get("sounding") or 1)) for cid in common]  # G31 (구 프롬프트)
    b = [str(int(cached[cid].get("sounding") or 1)) for cid in common]  # G35 (새 프롬프트)

    def dist(labels):
        c = Counter(labels)
        n = len(labels)
        return {s: c.get(s, 0) / n * 100 for s in ("1", "2", "3", "4")}

    d31, d35 = dist(a), dist(b)
    agree = sum(1 for x, y in zip(a, b) if x == y) / len(a) * 100
    lines = [
        "So1/So2 경계 명문화 효과 검증 (주의 4 추가 후)",
        "=" * 46,
        f"표본 {len(common)}건 — G31(구 프롬프트) vs G35(새 프롬프트)",
        "",
        f"  {'':18s}{'So1':>8s}{'So2':>8s}{'So3':>8s}{'So4':>8s}{'So≥2':>8s}",
        f"  {'G31·구':18s}" + "".join(f"{d31[s]:7.1f}%" for s in ("1", "2", "3", "4")) + f"{100-d31['1']:7.1f}%",
        f"  {'G35·신':18s}" + "".join(f"{d35[s]:7.1f}%" for s in ("1", "2", "3", "4")) + f"{100-d35['1']:7.1f}%",
        "  (참고: G35·구 프롬프트는 동일 표본에서 So≥2 40.8%였음 — so_g31_check)",
        "",
        f"sounding 일치율 {agree:.1f}% / κ={cohens_kappa(a, b):.3f}",
        f"So≥2 격차: {(100-d35['1']) - (100-d31['1']):+.1f}pp (수정 전 +11.3pp)",
    ]
    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
