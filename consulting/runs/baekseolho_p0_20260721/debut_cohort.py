# -*- coding: utf-8 -*-
"""데뷔 정렬 신생 코호트 분석 — 백설호 3개월 차 위치 실측 (내부 참고치, L3 아님).

설계:
- 코호트 = census_full 7,472 중 "관측 시작이 창 내부"인 채널 (좌측 절단 제외).
  first_week >= 2025-08-04 (창 시작 2025-07-07 + 4주 버퍼) AND first_week <= 2026-04-20
  (자기 week 13이 창 안에 완결되도록).
- 데뷔 근사 = 소프트콘 시계열 첫 관측 주. 한계: 추적 시작 지연·타 플랫폼 이주 채널 혼입.
  → 소형 데뷔 부분집합(첫 주 팔로워 <= 300)을 별도 산출 (백설호 첫 주 80과 동질).
- week 정렬 = 달력 오프셋 기반 (gap 있으면 팔로워 carry-forward, 생존 편향 방지:
  중도 이탈 채널도 분모 유지).
- 평가 시점 = week 13 (백설호 최신 완결 주와 동일한 나이).
- 시대 드리프트 체크 = 데뷔 반기(2025H2 vs 2026H1) 분할 비교.

출력: debut_cohort_20260722.json
"""
import json
import statistics
from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
FULL = BASE.parent / "census_full_20260708" / "census_full_weekly.ndjson"

WINDOW_BUFFER_FIRST = date(2025, 8, 4)
LAST_DEBUT = date(2026, 4, 20)
EVAL_WEEK = 13          # 데뷔 주 = week 1
SMALL_START_MAX = 300   # 소형 데뷔 부분집합 기준

SUBJECT = {
    "name": "백설호", "first_week": date(2026, 4, 20),
    "fol_w1": 80, "fol_w13": 148, "avg_w13": 2, "air_w13": 18.7,
    "growth_mult": 148 / 80, "weekly_rise_streak": True,  # 13주 연속 비감소·순증
}


def parse_date(s):
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def pct_rank(value, population):
    ordered = sorted(population)
    if len(ordered) <= 1:
        return 0.5
    lo, hi = bisect_left(ordered, value), bisect_right(ordered, value)
    return (lo + hi - 1) / (2.0 * (len(ordered) - 1))


rows = [json.loads(l) for l in FULL.read_text(encoding="utf-8").splitlines() if l.strip()]
all_first = min(parse_date(w["date"]) for r in rows for w in r["weeks"] if r["weeks"])

cohort = []
for r in rows:
    weeks = sorted(r["weeks"], key=lambda w: w["date"])
    if not weeks:
        continue
    first = parse_date(weeks[0]["date"])
    if not (WINDOW_BUFFER_FIRST <= first <= LAST_DEBUT):
        continue
    by_offset = {}
    for w in weeks:
        off = (parse_date(w["date"]) - first).days // 7 + 1  # week 1 = 데뷔 주
        by_offset[off] = w
    # week 13 값: carry-forward (이탈해도 분모 유지 — 생존 편향 방지)
    fol13 = None
    last_fol = None
    active13 = False
    for off in range(1, EVAL_WEEK + 1):
        w = by_offset.get(off)
        if w and w.get("maxFollowerCount"):
            last_fol = w["maxFollowerCount"]
        if off == EVAL_WEEK:
            fol13 = last_fol
            active13 = bool(w and (w.get("airTime") or 0) > 0)
    w13 = by_offset.get(EVAL_WEEK)
    fol1 = weeks[0].get("maxFollowerCount") or None
    if fol13 is None or fol1 is None or fol1 <= 0:
        continue
    # 연속 상승 스트릭: week 2..13 전부 관측되고 매주 순증인가
    streak = all(
        by_offset.get(o) and by_offset.get(o - 1)
        and (by_offset[o].get("maxFollowerCount") or 0) > (by_offset[o - 1].get("maxFollowerCount") or 0)
        for o in range(2, EVAL_WEEK + 1)
    )
    cohort.append({
        "channel_id": r["channel_id"], "first_week": str(first),
        "fol_w1": fol1, "fol_w13": fol13, "mult": fol13 / fol1,
        "avg_w13": (w13 or {}).get("avgLiveViews"),
        "air_w13": (w13 or {}).get("airTime"),
        "active_w13": active13, "streak": streak,
        "era": "2025H2" if first < date(2026, 1, 1) else "2026H1",
    })


def describe(sub, label):
    fol = [c["fol_w13"] for c in sub]
    mult = [c["mult"] for c in sub]
    avgv = [c["avg_w13"] for c in sub if c["active_w13"] and c["avg_w13"] is not None]
    airs = [c["air_w13"] for c in sub if c["active_w13"] and c["air_w13"] is not None]
    active = sum(1 for c in sub if c["active_w13"])
    streaks = sum(1 for c in sub if c["streak"])
    return {
        "label": label, "n": len(sub),
        "active_w13_share": round(active / len(sub), 3) if sub else None,
        "streak_share": round(streaks / len(sub), 3) if sub else None,
        "fol_w13_median": statistics.median(fol) if fol else None,
        "fol_w13_p75": sorted(fol)[int(len(fol) * 0.75)] if fol else None,
        "fol_w13_p90": sorted(fol)[int(len(fol) * 0.90)] if fol else None,
        "subject_fol_pct": round(pct_rank(SUBJECT["fol_w13"], fol), 3) if fol else None,
        "mult_median": round(statistics.median(mult), 2) if mult else None,
        "subject_mult_pct": round(pct_rank(SUBJECT["growth_mult"], mult), 3) if mult else None,
        "avg_w13_median_active": statistics.median(avgv) if avgv else None,
        "subject_avg_pct_active": round(pct_rank(SUBJECT["avg_w13"], avgv), 3) if avgv else None,
        "air_w13_median_active": statistics.median(airs) if airs else None,
        "subject_air_pct_active": round(pct_rank(SUBJECT["air_w13"], airs), 3) if airs else None,
    }


small = [c for c in cohort if c["fol_w1"] <= SMALL_START_MAX]
out = {
    "generated_at": "2026-07-22",
    "design": {
        "window_first_observed": str(all_first),
        "debut_range": [str(WINDOW_BUFFER_FIRST), str(LAST_DEBUT)],
        "eval_week": EVAL_WEEK, "small_start_max": SMALL_START_MAX,
        "caveats": ["데뷔=추적시작 근사(이주채널 혼입 가능)", "시대 드리프트", "L3 아님 — 내부 참고치"],
    },
    "subject": SUBJECT | {"first_week": str(SUBJECT["first_week"])},
    "all_newcomers": describe(cohort, "관측시작 창내부 전체"),
    "small_debut": describe(small, f"소형 데뷔 (첫주 팔로워<={SMALL_START_MAX})"),
    "era_drift": {
        "2025H2": describe([c for c in small if c["era"] == "2025H2"], "소형 2025H2"),
        "2026H1": describe([c for c in small if c["era"] == "2026H1"], "소형 2026H1"),
    },
}
(BASE / "debut_cohort_20260722.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out["all_newcomers"], ensure_ascii=False))
print(json.dumps(out["small_debut"], ensure_ascii=False))
print(json.dumps(out["era_drift"]["2025H2"], ensure_ascii=False))
print(json.dumps(out["era_drift"]["2026H1"], ensure_ascii=False))
