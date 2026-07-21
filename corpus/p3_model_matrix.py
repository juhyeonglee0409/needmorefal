"""P3 종합: 5-rater 비교 매트릭스 — 전수 재태깅 모델 선정.

Rater: H  = v0.7 휴리스틱 (재계산)
       O  = gpt-4.1-mini          (p3_llm_results_v2.ndjson)
       G25= gemini-2.5-flash      (p3_llm_results_gemini.ndjson)
       G35= gemini-3.5-flash      (p3_llm_results_gemini-3-5-flash.ndjson)
       G31= gemini-3.1-pro-preview(p3_llm_results_gemini-3-1-pro-preview.ndjson)

산출: 축별 pairwise κ 매트릭스 + leave-one-out 패널 다수결 일치율(승자 지표).
사용법: cd corpus && python p3_model_matrix.py
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from p3_cross_validate import cohens_kappa
from tiller_tag import heuristic_tiller, normalize_tiller

DATA = Path(__file__).parent / "data" / "analysis"
SAMPLE_PATH = DATA / "p3_sample.ndjson"
REPORT_PATH = DATA / "p3_model_matrix.txt"

SOURCES = {
    "O": ("p3_llm_results_v2.ndjson", "llm"),
    "G25": ("p3_llm_results_gemini.ndjson", "gemini"),
    "G35": ("p3_llm_results_gemini-3-5-flash.ndjson", "gemini"),
    "G31": ("p3_llm_results_gemini-3-1-pro-preview.ndjson", "gemini"),
}
AXES = ["channel", "sounding", "heading", "berth"]  # bearing/slack은 양성 희소로 κ 공허
RATERS = ["H", "O", "G25", "G35", "G31"]


def load() -> list[dict]:
    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    tags: dict[str, dict[str, dict]] = {r["content_id"]: {"H": normalize_tiller(heuristic_tiller(r["body"]))} for r in sample}
    for name, (fname, key) in SOURCES.items():
        for l in (DATA / fname).read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            row = json.loads(l)
            if row.get(key) and row["content_id"] in tags:
                tags[row["content_id"]][name] = normalize_tiller(dict(row[key]))
    return [t for t in tags.values() if all(r in t for r in RATERS)]


def lab(v) -> str:
    return str(v) if v is not None else "null"


def main() -> None:
    rows = load()
    print(f"5-rater 공통 유효: {len(rows)}건")
    lines = [
        "P3 종합: 5-rater 비교 매트릭스",
        "=" * 46,
        f"공통 유효 표본: {len(rows)}건 / 축: {', '.join(AXES)}",
        "H=v0.7 휴리스틱, O=gpt-4.1-mini, G25/G35/G31=gemini-2.5-flash/3.5-flash/3.1-pro-preview",
        "",
    ]

    # 축별 pairwise κ
    for axis in AXES:
        lines.append(f"[{axis}] pairwise κ")
        header = "      " + "".join(f"{r:>8s}" for r in RATERS)
        lines.append(header)
        for a in RATERS:
            cells = []
            for b in RATERS:
                if a == b:
                    cells.append(f"{'—':>8s}")
                else:
                    k = cohens_kappa([lab(t[a].get(axis)) for t in rows], [lab(t[b].get(axis)) for t in rows])
                    cells.append(f"{k:8.3f}")
            lines.append(f"  {a:4s}" + "".join(cells))
        lines.append("")

    # leave-one-out 패널 다수결 일치율 (승자 지표)
    lines.append("패널 다수결 일치율 (leave-one-out; 동률 표본 제외):")
    scores: dict[str, list[float]] = {r: [] for r in RATERS}
    for axis in AXES:
        for r in RATERS:
            others = [x for x in RATERS if x != r]
            agree = total = 0
            for t in rows:
                votes = Counter(lab(t[o].get(axis)) for o in others)
                top, top_n = votes.most_common(1)[0]
                if list(votes.values()).count(top_n) > 1:
                    continue  # 동률
                total += 1
                if lab(t[r].get(axis)) == top:
                    agree += 1
            scores[r].append(agree / total * 100 if total else 0.0)
    lines.append("        " + "".join(f"{a:>10s}" for a in AXES) + f"{'평균':>10s}")
    ranking = []
    for r in RATERS:
        avg = sum(scores[r]) / len(scores[r])
        ranking.append((avg, r))
        lines.append(f"  {r:4s}  " + "".join(f"{v:9.1f}%" for v in scores[r]) + f"{avg:9.1f}%")
    ranking.sort(reverse=True)
    lines.append("")
    lines.append("순위: " + " > ".join(f"{r}({v:.1f}%)" for v, r in ranking))

    # bearing/slack 양성 사례 (희소 축은 κ 대신 사례 나열)
    lines.append("")
    lines.append("bearing/slack 양성 사례 (희소 축):")
    for axis in ("bearing", "slack"):
        for t_idx, t in enumerate(rows):
            found = {r: t[r].get(axis) for r in RATERS if t[r].get(axis)}
            if found:
                lines.append(f"  {axis}: 표본#{t_idx} → {found}")

    report = "\n".join(lines)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {REPORT_PATH}")


if __name__ == "__main__":
    main()
