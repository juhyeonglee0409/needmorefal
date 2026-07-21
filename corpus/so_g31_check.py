"""Sounding 수치 G31 대조 검증 — L4 v2의 So 관련 발견(So≥2 42.8%, So≥3 1.7%)이
rater(G35)의 약점 축 인공물인지 확인한다.

방법: 전환 전 G31(gemini-3.1-pro-preview)로 태깅된 부분본과 G35 전수본의
동일 레코드 교집합에서 sounding 분포·일치도·혼동 행렬을 비교.
(사전등록 A1 수정조항의 검증 숙제)

사용법: cd corpus && python so_g31_check.py
산출: data/analysis/so_g31_check.txt
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from p3_cross_validate import cohens_kappa

DATA = Path(__file__).parent / "data"
G31_PATH = DATA / "corpus_tagged_v2_g31_partial.ndjson"
G35_PATH = DATA / "corpus_tagged_v2.ndjson"
OUT = DATA / "analysis" / "so_g31_check.txt"


def load(path, key="tiller"):
    out = {}
    for l in path.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get(key):
            out[r["content_id"]] = r[key]
    return out


def so_dist(tags_list):
    c = Counter(int(t.get("sounding") or 1) for t in tags_list)
    n = sum(c.values())
    return {s: c.get(s, 0) / n * 100 for s in (1, 2, 3, 4)}, n


def main():
    g31 = load(G31_PATH)
    g35 = load(G35_PATH)
    common = sorted(set(g31) & set(g35))
    lines = [
        "Sounding G31 대조 검증 (사전등록 A1 숙제)",
        "=" * 46,
        f"G31 부분본 {len(g31)}건 / G35 전수본 {len(g35)}건 / 교집합 {len(common)}건",
        "",
    ]

    pairs = [(g31[cid], g35[cid]) for cid in common]

    # 분포 비교 (동일 레코드)
    d31, _ = so_dist([a for a, _ in pairs])
    d35, _ = so_dist([b for _, b in pairs])
    lines += ["동일 레코드에서의 So 분포:", f"  {'':6s}{'So1':>8s}{'So2':>8s}{'So3':>8s}{'So4':>8s}{'So≥2':>8s}"]
    for name, d in (("G31", d31), ("G35", d35)):
        lines.append(f"  {name:6s}" + "".join(f"{d[s]:7.1f}%" for s in (1, 2, 3, 4)) + f"{100-d[1]:7.1f}%")

    # 일치도
    a = [str(int(x.get("sounding") or 1)) for x, _ in pairs]
    b = [str(int(y.get("sounding") or 1)) for _, y in pairs]
    agree = sum(1 for x, y in zip(a, b) if x == y) / len(a) * 100
    kappa = cohens_kappa(a, b)
    lines += ["", f"sounding 일치율 {agree:.1f}% / κ={kappa:.3f}"]

    # 혼동 행렬
    conf = Counter(zip(a, b))
    lines += ["", "혼동 행렬 (행=G31, 열=G35):", "      " + "".join(f"{s:>6s}" for s in ("1", "2", "3", "4"))]
    for x in ("1", "2", "3", "4"):
        lines.append(f"  So{x} " + "".join(f"{conf.get((x, y), 0):6d}" for y in ("1", "2", "3", "4")))

    # channel도 참고로
    ca = [str(int(x.get("channel") or 1)) for x, _ in pairs]
    cb = [str(int(y.get("channel") or 1)) for _, y in pairs]
    c_agree = sum(1 for x, y in zip(ca, cb) if x == y) / len(ca) * 100
    lines += ["", f"(참고) channel 일치율 {c_agree:.1f}% / κ={cohens_kappa(ca, cb):.3f}"]

    # 핵심 판정: So≥2 격차
    gap = (100 - d35[1]) - (100 - d31[1])
    lines += [
        "",
        f"핵심 판정 — So≥2: G31 {100-d31[1]:.1f}% vs G35 {100-d35[1]:.1f}% (격차 {gap:+.1f}pp)",
        "  |격차| ≤ 5pp → L4 v2의 So 수치는 rater 견고 / > 10pp → G35 인공물 의심, 수치에 rater 단서 필수",
    ]

    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
