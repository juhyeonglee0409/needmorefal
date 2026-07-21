# -*- coding: utf-8 -*-
"""백설호 P0 무료 상담 준비 — 성장 전망 신호(§6.3.2) + 동급 비교 + 데이터 카드.

인바운드 문의(2026-07-21, 크몽 STANDARD)에 대한 P0 산출물.
- 신호 percentile 참조 모집단 = 전수 census_full 7,472 중 rookie 세그먼트 (본인 세그먼트)
  + growth 세그먼트 참고치 병기 (목표 체급 맥락용)
- 기준 주 = census 마지막 완결 주(2026-06-29, 시간 정렬). 본인 최신 주(7/13)는 참고 병기.
- 카드 비교군 = census_pool ±1,500 (카드 v2 규약 유지)

출력: baekseolho_analysis_20260721.json, card_백설호snowfox.html, consult_brief_20260721.md(별도 작성)
"""
import json
import statistics
from bisect import bisect_left, bisect_right
from pathlib import Path

BASE = Path(__file__).parent
RUNS = BASE.parent
FULL = RUNS / "census_full_20260708" / "census_full_weekly.ndjson"
POOL = RUNS / "vtuber_outreach_pilot_20260704" / "census_pool.ndjson"
CENSUS_TOTAL = 7203
MOMENTUM = 4
Q_HIGH, Q_LOW = 0.75, 0.25

subject = json.loads((BASE / "baekseolho_weekly_20260721.json").read_text(encoding="utf-8"))
S_WEEKS = {w["date"]: w for w in subject["weekly_summary"]}


def pct_rank(value, population):
    ordered = sorted(population)
    if len(ordered) <= 1:
        return 0.5
    lo, hi = bisect_left(ordered, value), bisect_right(ordered, value)
    return (lo + hi - 1) / (2.0 * (len(ordered) - 1))


def eff_mom(weeks_by_date, dates, t_idx):
    t, t0 = dates[t_idx], dates[t_idx - MOMENTUM]
    row, row0 = weeks_by_date.get(t), weeks_by_date.get(t0)
    if not row or not row0:
        return None, None
    avg, fol, fol0 = row.get("avgLiveViews"), row.get("maxFollowerCount"), row0.get("maxFollowerCount")
    eff = (avg / fol) if avg and fol and fol > 0 else None
    mom = (((fol / fol0) - 1.0) / MOMENTUM) if fol and fol0 and fol0 > 0 else None
    return eff, mom


# --- 전수 시계열 로드 ---
ref_rows = [json.loads(l) for l in FULL.read_text(encoding="utf-8").splitlines() if l.strip()]
all_dates = sorted({w["date"] for r in ref_rows for w in r["weeks"]})
t_idx = len(all_dates) - 2
ref_week = all_dates[t_idx]

pop = {"rookie": {"eff": [], "mom": [], "avg": [], "air": []},
       "growth": {"eff": [], "mom": [], "avg": [], "air": []}}
for r in ref_rows:
    seg = r["segment"]
    if seg not in pop:
        continue
    wbd = {w["date"]: w for w in r["weeks"]}
    row = wbd.get(ref_week)
    if row:
        if row.get("avgLiveViews") is not None:
            pop[seg]["avg"].append(row["avgLiveViews"])
        if row.get("airTime") is not None:
            pop[seg]["air"].append(row["airTime"])
    eff, mom = eff_mom(wbd, all_dates, t_idx)
    if eff is not None:
        pop[seg]["eff"].append(eff)
    if mom is not None:
        pop[seg]["mom"].append(mom)


def subject_signal(t_date_idx_dates, label):
    dates, idx = t_date_idx_dates
    eff, mom = eff_mom(S_WEEKS, dates, idx)
    out = {"label": label, "week": dates[idx], "eff": eff, "mom": mom}
    if eff is None or mom is None:
        out["signal"] = None
        return out
    for seg in ("rookie", "growth"):
        ep, mp = pct_rank(eff, pop[seg]["eff"]), pct_rank(mom, pop[seg]["mom"])
        if ep >= Q_HIGH and mp >= Q_HIGH:
            sig = "green"
        elif mp >= Q_HIGH:
            sig = "near"
        elif ep <= Q_LOW and mp <= Q_LOW:
            sig = "red"
        else:
            sig = "neutral"
        out[seg] = {"eff_pct": round(ep, 3), "mom_pct": round(mp, 3), "signal": sig}
    out["signal"] = out["rookie"]["signal"]  # 본인 세그먼트 기준
    return out


# 기준 주(census 정렬) + 본인 최신 완결 주
sig_ref = subject_signal((all_dates, t_idx), "census-aligned")
s_dates = sorted(S_WEEKS.keys())
sig_latest = subject_signal((s_dates, len(s_dates) - 2), "subject-latest")

# --- rookie/growth 분포 맥락 ---
rk_avg = sorted(pop["rookie"]["avg"])
gw_avg = sorted(pop["growth"]["avg"])
ctx = {
    "ref_week": ref_week,
    "rookie_n": len(rk_avg),
    "growth_n": len(gw_avg),
    "rookie_avg_median": statistics.median(rk_avg) if rk_avg else None,
    "rookie_air_median": statistics.median(pop["rookie"]["air"]) if pop["rookie"]["air"] else None,
    "growth_air_median": statistics.median(pop["growth"]["air"]) if pop["growth"]["air"] else None,
    "subject_avg_pct_in_rookie": round(pct_rank(3, rk_avg), 3) if rk_avg else None,
    "rookie_share_avg_ge10": round(sum(1 for v in rk_avg if v >= 10) / len(rk_avg), 3) if rk_avg else None,
    "growth_share_avg_ge15": round(sum(1 for v in gw_avg if v >= 15) / len(gw_avg), 3) if gw_avg else None,
    "growth_share_avg_ge40": round(sum(1 for v in gw_avg if v >= 40) / len(gw_avg), 3) if gw_avg else None,
    "all_share_avg_ge40": None,
}
all_avg = rk_avg + gw_avg
ctx["all_share_avg_ge40"] = round(sum(1 for v in all_avg if v >= 40) / len(all_avg), 3) if all_avg else None

# 방송시간 percentile (본인 6/29 주 25.9h)
air_all = sorted(pop["rookie"]["air"] + pop["growth"]["air"])
ctx["subject_air_pct_all"] = round(pct_rank(25.9, air_all), 3) if air_all else None
ctx["subject_air_pct_rookie"] = round(pct_rank(25.9, sorted(pop["rookie"]["air"])), 3) if pop["rookie"]["air"] else None

# --- 카드 비교군 (census_pool ±1,500, 카드 v2 규약) ---
pool = {}
for l in POOL.open(encoding="utf-8"):
    r = json.loads(l)
    pool[r["channel_id"]] = r
pool = [r for r in pool.values()
        if (r.get("follower_count") or 0) > 0
        and (r.get("metrics", {}).get("softcon") or {}).get("avg") is not None]
for r in pool:
    r["eff1k"] = r["metrics"]["softcon"]["avg"] / (r["follower_count"] / 1000)

F = 145            # 6/29 주 팔로워 (census 시점 정렬)
AVG, HOURS = 3, 25.9
RANK = 5618        # 7/4 census 뷰어십 랭크
eff1k = AVG / (F / 1000)
peers = [r for r in pool if abs(r["follower_count"] - F) <= 1500]
n = len(peers)
prank = sum(1 for r in peers if r["eff1k"] >= eff1k)
ppct = prank / n * 100
med_avg = statistics.median(r["metrics"]["softcon"]["avg"] for r in peers)
med_eff = statistics.median(r["eff1k"] for r in peers)
med_h = statistics.median(r["metrics"]["softcon"]["hours"] for r in peers)
cen_pct = RANK / CENSUS_TOTAL * 100

result = {
    "generated_at": "2026-07-21",
    "signal_census_aligned": sig_ref,
    "signal_subject_latest": sig_latest,
    "segment_context": ctx,
    "peer_card_stats": {
        "band": "follower ±1500 (card v2 규약)", "n": n,
        "eff_rank": prank, "eff_top_pct": round(ppct, 1),
        "med_avg": med_avg, "med_eff": round(med_eff, 2), "med_h": med_h,
        "census_rank": RANK, "census_top_pct": round(cen_pct, 1),
        "subject": {"followers": F, "avg": AVG, "hours": HOURS, "eff1k": round(eff1k, 1)},
    },
}
(BASE / "baekseolho_analysis_20260721.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved analysis json")
print(json.dumps(result["signal_census_aligned"], ensure_ascii=False))
print(json.dumps(result["signal_subject_latest"], ensure_ascii=False))
print(json.dumps(result["peer_card_stats"], ensure_ascii=False))
