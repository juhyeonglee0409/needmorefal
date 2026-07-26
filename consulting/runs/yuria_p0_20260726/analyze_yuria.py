# -*- coding: utf-8 -*-
"""유리아 루네아 P0 상담 준비, 측정 착시 정량화 + 신호 + 코호트 위치.

백설호 케이스(runs/baekseolho_p0_20260721/)의 분석 틀 재사용.
핵심 가설: 본인 진술("팔로우는 느는데 시청자 변화 없음")은 §3.1 평균시청자 왜곡, 방송시간 급변(7.1h~35.6h)이 분모로 작용해 평청을 눌렀고, 총 시청량은 증가 중.
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

subj = json.loads((BASE / "yuria_weekly_20260726.json").read_text(encoding="utf-8"))
W = subj["weekly_summary"]
SW = {w["date"]: w for w in W}


def pct_rank(v, pop):
    o = sorted(pop)
    if len(o) <= 1:
        return 0.5
    lo, hi = bisect_left(o, v), bisect_right(o, v)
    return (lo + hi - 1) / (2.0 * (len(o) - 1))


def eff_mom(wbd, dates, i):
    t, t0 = dates[i], dates[i - MOMENTUM]
    r, r0 = wbd.get(t), wbd.get(t0)
    if not r or not r0:
        return None, None
    a, f, f0 = r.get("avgLiveViews"), r.get("maxFollowerCount"), r0.get("maxFollowerCount")
    return ((a / f) if a and f else None), ((((f / f0) - 1.0) / MOMENTUM) if f and f0 else None)


# ---- 1) 측정 착시 정량화 (§3.1) ----
def blk(dates):
    rows = [SW[d] for d in dates]
    h = sum(r["airTime"] for r in rows)
    vs = sum(r["viewership"] for r in rows)
    ch = sum(r["sumChatCount"] for r in rows)
    return {
        "weeks": dates, "airTime": round(h, 1), "viewership": vs, "chat": ch,
        "avg_of_avg": round(statistics.mean(r["avgLiveViews"] for r in rows), 1),
        "peak_max": max(r["maxLiveViews"] for r in rows),
        "follower_end": rows[-1]["maxFollowerCount"],
    }


june = blk(["2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29"])
july = blk(["2026-07-06", "2026-07-13", "2026-07-20"])
illusion = {
    "june_4w": june, "july_3w": july,
    "airtime_ratio": round(july["airTime"] / (june["airTime"] / 4 * 3), 2),
    "viewership_per_week_june": round(june["viewership"] / 4, 1),
    "viewership_per_week_july": round(july["viewership"] / 3, 1),
    "chat_per_week_june": round(june["chat"] / 4),
    "chat_per_week_july": round(july["chat"] / 3),
}

# ---- 2) 성장 전망 신호 (§6.3.2) ----
ref_rows = [json.loads(l) for l in FULL.read_text(encoding="utf-8").splitlines() if l.strip()]
all_dates = sorted({w["date"] for r in ref_rows for w in r["weeks"]})
t_idx = len(all_dates) - 2
ref_week = all_dates[t_idx]
pop = {"rookie": {"eff": [], "mom": [], "avg": [], "air": [], "peak": []},
       "growth": {"eff": [], "mom": [], "avg": [], "air": [], "peak": []}}
for r in ref_rows:
    seg = r["segment"]
    if seg not in pop:
        continue
    wbd = {w["date"]: w for w in r["weeks"]}
    row = wbd.get(ref_week)
    if row:
        for k, f in (("avg", "avgLiveViews"), ("air", "airTime"), ("peak", "maxLiveViews")):
            if row.get(f) is not None:
                pop[seg][k].append(row[f])
    e, m = eff_mom(wbd, all_dates, t_idx)
    if e is not None:
        pop[seg]["eff"].append(e)
    if m is not None:
        pop[seg]["mom"].append(m)

s_dates = sorted(SW.keys())
sig = {}
for label, dates, i in [("census_aligned", all_dates, t_idx), ("subject_latest", s_dates, len(s_dates) - 1)]:
    e, m = eff_mom(SW, dates, i)
    o = {"week": dates[i], "eff": e, "mom": m}
    if e is not None and m is not None:
        for seg in ("rookie", "growth"):
            ep, mp = pct_rank(e, pop[seg]["eff"]), pct_rank(m, pop[seg]["mom"])
            s = "green" if (ep >= Q_HIGH and mp >= Q_HIGH) else ("near" if mp >= Q_HIGH else
                ("red" if (ep <= Q_LOW and mp <= Q_LOW) else "neutral"))
            o[seg] = {"eff_pct": round(ep, 3), "mom_pct": round(mp, 3), "signal": s}
    sig[label] = o

# ---- 3) 세그먼트 맥락 (growth 기준, 7/20 주 실측 대입) ----
last = SW["2026-07-20"]
ctx = {
    "ref_week": ref_week, "growth_n": len(pop["growth"]["avg"]),
    "subject_avg_pct_growth": round(pct_rank(last["avgLiveViews"], pop["growth"]["avg"]), 3),
    "subject_peak_pct_growth": round(pct_rank(last["maxLiveViews"], pop["growth"]["peak"]), 3),
    "subject_air_pct_growth": round(pct_rank(last["airTime"], pop["growth"]["air"]), 3),
    "growth_avg_median": statistics.median(pop["growth"]["avg"]),
    "growth_peak_median": statistics.median(pop["growth"]["peak"]),
    "growth_air_median": statistics.median(pop["growth"]["air"]),
}

# ---- 4) 데뷔 정렬 코호트 (week 18 = 4개월차) ----
from datetime import date
def pdate(s):
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))

EVAL = 18
cohort = []
for r in ref_rows:
    ws = sorted(r["weeks"], key=lambda w: w["date"])
    if not ws:
        continue
    first = pdate(ws[0]["date"])
    if not (date(2025, 8, 4) <= first <= date(2026, 3, 23)):
        continue
    by = {}
    for w in ws:
        by[(pdate(w["date"]) - first).days // 7 + 1] = w
    f1 = ws[0].get("maxFollowerCount")
    if not f1:
        continue
    lastf = None
    for o in range(1, EVAL + 1):
        w = by.get(o)
        if w and w.get("maxFollowerCount"):
            lastf = w["maxFollowerCount"]
    if lastf is None:
        continue
    w18 = by.get(EVAL)
    cohort.append({"f18": lastf, "f1": f1, "mult": lastf / f1 if f1 else None,
                   "avg18": (w18 or {}).get("avgLiveViews"),
                   "peak18": (w18 or {}).get("maxLiveViews"),
                   "active": bool(w18 and (w18.get("airTime") or 0) > 0),
                   "small": f1 <= 300})
small = [c for c in cohort if c["small"]]
f18 = [c["f18"] for c in small]
avg18 = [c["avg18"] for c in small if c["active"] and c["avg18"] is not None]
peak18 = [c["peak18"] for c in small if c["active"] and c["peak18"] is not None]
debut = {
    "eval_week": EVAL, "n_all": len(cohort), "n_small": len(small),
    "active_share": round(sum(1 for c in small if c["active"]) / len(small), 3),
    "f18_median": statistics.median(f18), "subject_f18": 219,
    "subject_f18_pct": round(pct_rank(219, f18), 3),
    "avg18_median": statistics.median(avg18) if avg18 else None,
    "subject_avg18_pct": round(pct_rank(7, avg18), 3) if avg18 else None,
    "peak18_median": statistics.median(peak18) if peak18 else None,
    "subject_peak18_pct": round(pct_rank(15, peak18), 3) if peak18 else None,
}

# ---- 5) 카드용 peer stats (±1,500 밴드) ----
pool = {}
for l in POOL.open(encoding="utf-8"):
    r = json.loads(l)
    pool[r["channel_id"]] = r
pool = [r for r in pool.values() if (r.get("follower_count") or 0) > 0
        and (r.get("metrics", {}).get("softcon") or {}).get("avg") is not None]
for r in pool:
    r["eff1k"] = r["metrics"]["softcon"]["avg"] / (r["follower_count"] / 1000)
F, AVG, HOURS, PEAK = 219, 7, 24.0, 15
eff1k = AVG / (F / 1000)
peers = [r for r in pool if abs(r["follower_count"] - F) <= 1500]
prank = sum(1 for r in peers if r["eff1k"] >= eff1k)
card = {
    "n": len(peers), "eff_rank": prank, "eff_top_pct": round(prank / len(peers) * 100, 1),
    "med_avg": statistics.median(r["metrics"]["softcon"]["avg"] for r in peers),
    "med_eff": round(statistics.median(r["eff1k"] for r in peers), 2),
    "med_h": statistics.median(r["metrics"]["softcon"]["hours"] for r in peers),
    "subject": {"followers": F, "avg": AVG, "peak": PEAK, "hours": HOURS, "eff1k": round(eff1k, 1)},
}

out = {"generated_at": "2026-07-26", "measurement_illusion": illusion, "signal": sig,
       "segment_context": ctx, "debut_cohort": debut, "peer_card_stats": card}
(BASE / "yuria_analysis_20260726.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k in out:
    if k != "generated_at":
        print(k, "::", json.dumps(out[k], ensure_ascii=False))
