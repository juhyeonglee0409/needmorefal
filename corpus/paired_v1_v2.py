"""v1↔v2 진짜 짝비교 — 동일 레코드에서 구 휴리스틱 태그와 r2 태그를 직접 대조.

v1 태그는 shared 리포에서 복구 (corpus_tagged_v1_recovered.ndjson, 6,133건).
사전등록 채점은 L4 공표값 대비 근사 비교였다 — 이 분석은 레코드 단위 확정 증거:
  - v1 오탐(v1+ → v2-)과 v1 미탐(v1- → v2+)의 정확한 분해
  - H3("berth는 하락한다" 반증)의 기전: 오탐 < 미탐 을 수치로 확정
  - Ch3 거품의 행선지 (v1 Ch3 레코드들이 v2에서 어디로 갔나)

사용법: cd corpus && python paired_v1_v2.py
산출: data/analysis/paired_v1_v2.md
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent / "data"
V1 = DATA / "corpus_tagged_v1_recovered.ndjson"
V2 = DATA / "corpus_tagged_v2.ndjson"
OUT = DATA / "analysis" / "paired_v1_v2.md"

HELM = ("heading", "berth", "bearing", "slack")


def load(path):
    out = {}
    for l in path.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("tiller"):
                out[r["content_id"]] = r["tiller"]
    return out


def main():
    v1, v2 = load(V1), load(V2)
    common = sorted(set(v1) & set(v2))
    n = len(common)
    lines = [
        "# v1↔v2 짝비교 (동일 레코드)",
        "",
        f"> v1(구 휴리스틱, shared 복구본) {len(v1)}건 / v2(r2, G35) {len(v2)}건 / **교집합 {n}건**",
        "> 사전등록 채점의 근사 비교(L4 공표값 대비)를 레코드 단위 확정 증거로 보강한다.",
        "",
    ]

    # ── TRIM 흐름 ──
    for axis, name in (("channel", "CHANNEL"), ("sounding", "SOUNDING")):
        conf = Counter()
        for cid in common:
            a = int(v1[cid].get(axis) or 1)
            b = int(v2[cid].get(axis) or 1)
            conf[(a, b)] += 1
        lines += [f"## {name} 이동 행렬 (행=v1, 열=v2)", "", "| v1\\v2 | 1 | 2 | 3 | 4 | v1 합계 |", "|---|---|---|---|---|---|"]
        for a in (1, 2, 3, 4):
            row = [conf.get((a, b), 0) for b in (1, 2, 3, 4)]
            lines.append(f"| **{a}** | " + " | ".join(str(x) for x in row) + f" | {sum(row)} |")
        stay = sum(conf.get((x, x), 0) for x in (1, 2, 3, 4))
        lines += ["", f"- 유지율: {stay/n*100:.1f}%", ""]
        if axis == "channel":
            ch3_total = sum(conf.get((3, b), 0) for b in (1, 2, 3, 4))
            if ch3_total:
                to1 = conf.get((3, 1), 0)
                lines.append(f"- **v1 Ch3 {ch3_total}건의 행선지**: Ch1로 {to1}건({to1/ch3_total*100:.0f}%), Ch3 유지 {conf.get((3,3),0)}건({conf.get((3,3),0)/ch3_total*100:.0f}%) — 거품 규모의 레코드 단위 확정")
                lines.append("")
        if axis == "sounding":
            so34 = sum(conf.get((a, b), 0) for a in (3, 4) for b in (1, 2, 3, 4))
            if so34:
                down = sum(conf.get((a, b), 0) for a in (3, 4) for b in (1, 2))
                lines.append(f"- **v1 So≥3 {so34}건 중 {down}건({down/so34*100:.0f}%)이 v2에서 So≤2로 하향** — '어휘 다양성 ≠ 체인 깊이' 확정")
                lines.append("")

    # ── HELM 분해 ──
    lines += ["## HELM 검출 분해 (v1 오탐 vs 미탐)", "", "| 축 | v1+ | v2+ | 동시+ | v1 오탐 (v1+→v2-) | v1 미탐 (v1-→v2+) | 판정 |", "|---|---|---|---|---|---|---|"]
    for axis in HELM:
        p1 = {cid for cid in common if v1[cid].get(axis)}
        p2 = {cid for cid in common if v2[cid].get(axis)}
        both = p1 & p2
        fp = len(p1 - p2)  # v1이 잡고 v2가 부정 → v1 오탐 추정
        fn = len(p2 - p1)  # v2가 잡고 v1이 놓침 → v1 미탐
        verdict = "오탐 우세 (거품)" if fp > fn * 1.5 else ("미탐 우세 (과소 측정)" if fn > fp * 1.5 else "혼합")
        lines.append(f"| {axis} | {len(p1)} ({len(p1)/n*100:.1f}%) | {len(p2)} ({len(p2)/n*100:.1f}%) | {len(both)} | {fp} | {fn} | {verdict} |")

    # 모드 승계 (berth: 동시+에서 모드 일치율)
    lines += ["", "### berth 동시 검출의 모드 대조", ""]
    mode_conf = Counter()
    for cid in common:
        a, b = v1[cid].get("berth"), v2[cid].get("berth")
        if a and b:
            mode_conf[(a, b)] += 1
    for (a, b), c in mode_conf.most_common(8):
        lines.append(f"- v1 {a} → v2 {b}: {c}건")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
