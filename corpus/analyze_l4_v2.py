"""L4 v2 분석 — 재태깅(corpus_tagged_v2.ndjson) 통계 재산출 + 사전등록 가설 채점.

사전등록: data/analysis/L4v2_preregistration.md (2026-07-08 잠금, H1~H10 + 수정조항 A1).

v1 기준선: 현행 corpus_tagged.ndjson은 재구축 과정에서 구 태그가 소실(tiller=null)되어
짝비교가 불가능하다. 따라서 v1 수치는 L4 v3 리포트(2026-06-24, 5,836건)의 공표값을
기준선으로 쓴다 — 사전등록의 예측도 그 공표값 기준이므로 채점에는 정합적이다.
단 코퍼스가 5,836→6,345건으로 성장했고 도메인 구성이 변했으므로(other 재분류 등)
도메인별 낙폭은 근사치다.

사용법: cd corpus && python analyze_l4_v2.py
산출: data/analysis/L4_v2_report.md
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).parent / "data"
INPUT = DATA / "corpus_tagged_v2.ndjson"
OUT = DATA / "analysis" / "L4_v2_report.md"

CRUISE = {(c, s) for c in (2, 3) for s in (2, 3)}  # 고구조 밀도 영역 (구 순항)

# L4 v3 리포트 (2026-06-24) 공표 기준선
V1_OVERALL = {"heading": 39.6, "berth": 14.5, "bearing": 11.2, "slack": 12.3}
V1_DOMAIN = {  # domain: (heading, berth, bearing, slack)
    "coding": (65, 41, 32, 17),
    "roleplay": (84, 12, 15, 10),
    "analysis": (58, 21, 19, 15),
    "writing": (39, 18, 9, 15),
    "business": (38, 9, 7, 20),
    "education": (41, 16, 11, 14),
    "creative": (22, 6, 6, 10),
    "other": (14, 6, 2, 7),
}
V1_AXES = ("heading", "berth", "bearing", "slack")


def load():
    rows, seen = [], set()
    for l in INPUT.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r["content_id"] in seen:
            continue
        seen.add(r["content_id"])
        if r.get("tiller"):
            rows.append(r)
    return rows


def ch_so(t):
    return int(t.get("channel") or 1), int(t.get("sounding") or 1)


def helm_rate(rows, axis):
    return sum(1 for r in rows if (r.get("tiller") or {}).get(axis)) / len(rows) * 100 if rows else 0.0


def cruise_rate(rows):
    return sum(1 for r in rows if ch_so(r["tiller"]) in CRUISE) / len(rows) * 100 if rows else 0.0


def record_month(r) -> str | None:
    """occurrences[].published_at에서 레코드 대표 월(YYYY-MM) 도출 — 최초 게시 기준."""
    months = []
    for o in r.get("occurrences") or []:
        raw = o.get("published_at")
        if not raw or raw == "null":
            continue
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        if len(digits) < 6:
            continue
        y, m = digits[:4], digits[4:6]
        if not ("2019" <= y <= "2026") or not ("01" <= m <= "12"):
            continue
        months.append(f"{y}-{m}")
    return min(months) if months else None


def verdict(ok: bool | None, partial: bool = False) -> str:
    if ok is None:
        return "판정 불가"
    if partial:
        return "부분 지지"
    return "지지" if ok else "**반증**"


def main():
    rows = load()
    n = len(rows)
    model = rows[0].get("tiller_model", "?") if rows else "?"
    lines = [
        f"# L4 v2 리포트 — 재태깅 코퍼스 (v0.7 F층 코드북 × {model})",
        "",
        f"> 태깅 레코드 {n}건 / 코퍼스 6,345건 (실패 {6345 - n}건)",
        "> v1 기준선 = L4 v3 리포트 공표값 (구 태그가 코퍼스 재구축으로 소실되어 짝비교 불가; 코퍼스 성장분 감안해 낙폭은 근사치)",
        "",
    ]

    # ── TRIM ──
    mat = Counter(ch_so(r["tiller"]) for r in rows)
    lines += ["## 1. TRIM 분포", "", "|  | So1 | So2 | So3 | So4 | 합계 |", "|---|---|---|---|---|---|"]
    for c in (1, 2, 3, 4):
        cells = [mat.get((c, s), 0) for s in (1, 2, 3, 4)]
        tot = sum(cells)
        lines.append(f"| Ch{c} | " + " | ".join(f"{v} ({v/n*100:.1f}%)" for v in cells) + f" | {tot} ({tot/n*100:.1f}%) |")
    so_tot = [sum(mat.get((c, s), 0) for c in (1, 2, 3, 4)) for s in (1, 2, 3, 4)]
    lines.append("| 합계 | " + " | ".join(f"{v} ({v/n*100:.1f}%)" for v in so_tot) + f" | {n} |")

    ch1so1 = mat.get((1, 1), 0) / n * 100
    so2plus = sum(v for (c, s), v in mat.items() if s >= 2) / n * 100
    ch3 = sum(v for (c, s), v in mat.items() if c == 3) / n * 100
    cruise = cruise_rate(rows)
    lines += ["", f"- Ch1×So1: **{ch1so1:.1f}%** (v1: 58.2%) / So≥2: **{so2plus:.1f}%** (v1: 28.3%) / Ch3: **{ch3:.1f}%** (v1: 19.1%) / 고구조 밀도: **{cruise:.1f}%** (v1: 9.5%)", ""]

    # ── HELM ──
    helm_new = {axis: helm_rate(rows, axis) for axis in V1_AXES}
    lines += ["## 2. HELM 사용률 (v1 공표값 대비)", "", "| 축 | v1(공표) | v2(재태깅) | Δ |", "|---|---|---|---|"]
    for axis in V1_AXES:
        lines.append(f"| {axis} | {V1_OVERALL[axis]:.1f}% | **{helm_new[axis]:.1f}%** | {helm_new[axis] - V1_OVERALL[axis]:+.1f}pp |")

    by_dom = defaultdict(list)
    for r in rows:
        by_dom[r.get("domain") or "unknown"].append(r)
    lines += ["", "### 도메인별 (신규): n / heading / berth / bearing / slack / 고구조", ""]
    dom_cruise, dom_heading = {}, {}
    for dom, rs in sorted(by_dom.items(), key=lambda kv: -len(kv[1])):
        dom_cruise[dom] = cruise_rate(rs)
        dom_heading[dom] = helm_rate(rs, "heading")
        lines.append(
            f"- {dom}: {len(rs)} / {helm_rate(rs,'heading'):.0f}% / {helm_rate(rs,'berth'):.0f}% / "
            f"{helm_rate(rs,'bearing'):.0f}% / {helm_rate(rs,'slack'):.0f}% / 고구조 {dom_cruise[dom]:.1f}%"
        )

    lines += ["", "### 도메인별 낙폭 (v1 공표 − v2, pp — 근사)", ""]
    drops = {}
    for i, axis in enumerate(V1_AXES):
        dd = {}
        for dom, base in V1_DOMAIN.items():
            if dom in by_dom and len(by_dom[dom]) >= 100:
                dd[dom] = base[i] - helm_rate(by_dom[dom], axis)
        drops[axis] = dd
        top = sorted(dd.items(), key=lambda kv: -kv[1])[:3]
        lines.append(f"- {axis} 낙폭 상위: " + ", ".join(f"{d} {v:+.1f}pp" for d, v in top))

    # ── 언어 ──
    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r.get("lang") or "?"].append(r)
    lines += ["", "## 3. 언어별", ""]
    lang_cruise = {}
    for lang in ("ko", "en", "mixed"):
        rs = by_lang.get(lang, [])
        if not rs:
            continue
        lang_cruise[lang] = cruise_rate(rs)
        c1s1 = sum(1 for r in rs if ch_so(r["tiller"]) == (1, 1)) / len(rs) * 100
        lines.append(f"- {lang}: n={len(rs)} / Ch1×So1 {c1s1:.1f}% / 고구조 {lang_cruise[lang]:.1f}%")

    # ── 시간 추세 (occurrences[].published_at 복원) ──
    early, late = [], []
    for r in rows:
        m = record_month(r)
        if not m:
            continue
        (early if m <= "2024-10" else late).append(r)
    lines += ["", "## 3b. 시간 추세 (published_at 복원분)", ""]
    trend_ok = None
    if len(early) >= 100 and len(late) >= 100:
        e_c1s1 = sum(1 for r in early if ch_so(r["tiller"]) == (1, 1)) / len(early) * 100
        l_c1s1 = sum(1 for r in late if ch_so(r["tiller"]) == (1, 1)) / len(late) * 100
        e_cr, l_cr = cruise_rate(early), cruise_rate(late)
        e_so2 = sum(1 for r in early if ch_so(r["tiller"])[1] >= 2) / len(early) * 100
        l_so2 = sum(1 for r in late if ch_so(r["tiller"])[1] >= 2) / len(late) * 100
        trend_ok = (l_c1s1 < e_c1s1) and (l_cr > e_cr)
        lines += [
            f"- ~2024-10 (n={len(early)}): Ch1×So1 {e_c1s1:.1f}% / So≥2 {e_so2:.1f}% / 고구조 {e_cr:.1f}%",
            f"- 2024-11~ (n={len(late)}): Ch1×So1 {l_c1s1:.1f}% / So≥2 {l_so2:.1f}% / 고구조 {l_cr:.1f}%",
            "- 주의: 부분 표본(35.9%)이며 소스 구성이 시기별로 달라 대표성 한계 있음",
        ]
    else:
        lines.append(f"- 표본 부족 (early {len(early)} / late {len(late)})")

    # ── 채점 ──
    lines += ["", "## 4. 사전등록 가설 채점 (H1~H10)", ""]
    bearing, slack, berth, heading = helm_new["bearing"], helm_new["slack"], helm_new["berth"], helm_new["heading"]

    def top_drop(axis):
        dd = drops.get(axis, {})
        return max(dd, key=dd.get) if dd else None

    scores = []
    scores.append(("H1 bearing<3%", f"{bearing:.1f}%", verdict(bearing < 3, partial=3 <= bearing < 5)))
    h2_num = slack < 3
    h2_dom = top_drop("slack")
    scores.append(("H2 slack<3% & creative 최대낙폭", f"{slack:.1f}% / 최대낙폭 {h2_dom}",
                   verdict(h2_num and h2_dom == "creative", partial=h2_num)))
    h3_num = 6 <= berth <= 12
    h3_dom = top_drop("berth")
    scores.append(("H3 berth 6~12% & coding 최대낙폭", f"{berth:.1f}% / 최대낙폭 {h3_dom}",
                   verdict(h3_num and h3_dom == "coding",
                           partial=(h3_num or (3 <= berth < 6) or (12 < berth <= 13)) and not (h3_num and h3_dom == "coding"))))
    scores.append(("H4 Ch3 8~14%", f"{ch3:.1f}%", verdict(8 <= ch3 <= 14, partial=(5 <= ch3 < 8) or (14 < ch3 < 17))))
    scores.append(("H5 So≥2 25~40%", f"{so2plus:.1f}%", verdict(25 <= so2plus <= 40, partial=20 <= so2plus < 25 or 40 < so2plus <= 45)))
    if all(k in lang_cruise for k in ("ko", "en", "mixed")):
        h6 = lang_cruise["mixed"] > lang_cruise["ko"] and lang_cruise["mixed"] > lang_cruise["en"]
        scores.append(("H6 mixed 구조화 우위", f"mixed {lang_cruise['mixed']:.1f} vs ko {lang_cruise['ko']:.1f} / en {lang_cruise['en']:.1f}", verdict(h6)))
    h7_num = abs(heading - 39.6) <= 8
    role_top = max((d for d in dom_heading if len(by_dom[d]) >= 100), key=dom_heading.get)
    h7_full = h7_num and role_top == "roleplay"
    scores.append(("H7 heading ±8pp & roleplay 1위", f"{heading:.1f}% (Δ{heading-39.6:+.1f}pp) / 1위 {role_top}",
                   verdict(h7_full, partial=(h7_num or role_top == "roleplay") and not h7_full)))
    big = {d: c for d, c in dom_cruise.items() if len(by_dom[d]) >= 200 and d != "other"}
    ranked = sorted(big, key=big.get, reverse=True)
    if len(ranked) >= 4:
        h8 = set(ranked[:2]) == {"analysis", "coding"} and set(ranked[-2:]) == {"creative", "roleplay"}
        scores.append(("H8 도메인 순위 유지", " > ".join(f"{d}({big[d]:.1f})" for d in ranked),
                       verdict(h8, partial=(not h8) and set(ranked[:2]) == {"analysis", "coding"})))
    scores.append(("H9 시간 추세 유지", f"§3b 참조 (early n={len(early)}, late n={len(late)})", verdict(trend_ok)))
    scores.append(("H10 Ch1×So1 50~70%", f"{ch1so1:.1f}%", verdict(50 <= ch1so1 <= 70, partial=45 <= ch1so1 < 50 or 70 < ch1so1 <= 80)))

    lines += ["| 가설 | 측정값 | 판정 |", "|---|---|---|"]
    for name, val, v in scores:
        lines.append(f"| {name} | {val} | {v} |")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
