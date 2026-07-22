# -*- coding: utf-8 -*-
"""구비바 7월 후원 분석 — 룰렛 시스템(7/1 도입) 이후 추이 (§11 실행 트래킹).

입력: 치지직 스튜디오 내보내기 2종 (7/22 수집, data/revenue/에 보존)
- 구비바_일반후원_detail_20260722.xlsx: 7월 상세내역 (362건, 7/2~7/21)
- 구비바_revenue_20260722.xlsx: 1~6월 정산 (기준선)

비교 기준: '후원 금액'(VAT 포함 결제액) ↔ 정산표의 '항목별 결제액·치즈 후원'.
'후원받은 치즈'(gross 치즈)는 참여도 지표용. 정산 수익은 치즈의 ~70%(프로).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

BASE = Path(__file__).parent
DATA = BASE.parent.parent / "data" / "revenue"
DETAIL = DATA / "구비바_일반후원_detail_20260722.xlsx"

JUNE_PAYMENT = 676_786   # 6월 치즈후원 결제액 (정산표)
JUNE_REVENUE = 473_751   # 6월 치즈후원 수익
MONTH_PAYMENTS = {"1월": 362_489, "2월": 600_508, "3월": 587_873,
                  "4월": 457_644, "5월": 712_034, "6월": 676_786}


def won(s):
    return int(re.sub(r"[^\d]", "", s)) if s else 0


wb = openpyxl.load_workbook(DETAIL, data_only=True, read_only=True)
rows = []
for r in wb["상세내역"].iter_rows(min_row=3, values_only=True):
    if not r[1]:
        continue
    rows.append({
        "nick": r[0], "dt": r[1], "date": r[1][:10], "hour": int(r[1][11:13]),
        "pay": won(r[2]), "cheese": won(r[3]), "type": r[4],
        "msg": str(r[6]) if r[6] else "", "broadcast": str(r[7]) if r[7] else "",
    })
wb.close()

days = sorted({r["date"] for r in rows})
daily = {d: {"pay": 0, "cheese": 0, "n": 0, "donors": set()} for d in days}
for r in rows:
    d = daily[r["date"]]
    d["pay"] += r["pay"]; d["cheese"] += r["cheese"]; d["n"] += 1
    d["donors"].add(r["nick"])

total_pay = sum(r["pay"] for r in rows)
total_cheese = sum(r["cheese"] for r in rows)
n_days_observed = (21 - 2 + 1)  # 7/2~7/21 달력일 기준 (무후원일 포함)

# 반기 비교 (7/2~11 vs 7/12~21)
h1 = [r for r in rows if r["date"] <= "2026.07.11"]
h2 = [r for r in rows if r["date"] >= "2026.07.12"]

# 유형/금액 클러스터
types = defaultdict(lambda: {"n": 0, "cheese": 0})
for r in rows:
    types[r["type"]]["n"] += 1
    types[r["type"]]["cheese"] += r["cheese"]
amount_clusters = Counter(r["cheese"] for r in rows).most_common(12)

# 후원자 집중도
donors = defaultdict(lambda: {"cheese": 0, "n": 0, "days": set()})
for r in rows:
    donors[r["nick"]]["cheese"] += r["cheese"]
    donors[r["nick"]]["n"] += 1
    donors[r["nick"]]["days"].add(r["date"])
ranked = sorted(donors.items(), key=lambda kv: -kv[1]["cheese"])
top5_share = sum(v["cheese"] for _, v in ranked[:5]) / total_cheese

# 룰렛 후보: 1,100치즈 채팅 후원 (룰렛 언급 메시지 2건이 모두 1,100)
r1100 = [r for r in rows if r["cheese"] == 1100]
r1000 = [r for r in rows if r["cheese"] == 1000]

out = {
    "generated_at": "2026-07-22",
    "coverage": {"first": days[0], "last": days[-1], "rows": len(rows),
                 "calendar_days": n_days_observed, "active_days": len(days)},
    "totals": {"pay": total_pay, "cheese": total_cheese,
               "est_revenue_70pct": round(total_cheese * 0.7),
               "unique_donors": len(donors)},
    "daily": {d: {"pay": v["pay"], "cheese": v["cheese"], "n": v["n"],
                  "donors": len(v["donors"])} for d, v in daily.items()},
    "halves": {
        "h1_0702_0711": {"pay": sum(r["pay"] for r in h1), "n": len(h1),
                         "donors": len({r["nick"] for r in h1})},
        "h2_0712_0721": {"pay": sum(r["pay"] for r in h2), "n": len(h2),
                         "donors": len({r["nick"] for r in h2})},
    },
    "types": {k: dict(v) for k, v in types.items()},
    "amount_clusters_cheese": amount_clusters,
    "donor_concentration": {
        "top1_share": round(ranked[0][1]["cheese"] / total_cheese, 3),
        "top5_share": round(top5_share, 3),
        "n_donors": len(donors),
        "top_detail_internal": [
            {"nick": k, "cheese": v["cheese"], "n": v["n"], "days": len(v["days"])}
            for k, v in ranked[:8]],
    },
    "roulette_candidates": {"cheese_1100_count": len(r1100),
                            "cheese_1000_count": len(r1000),
                            "msg_roulette_count": sum(1 for r in rows if "룰렛" in r["msg"])},
    "baseline": {"june_payment": JUNE_PAYMENT, "june_revenue": JUNE_REVENUE,
                 "month_payments_2026": MONTH_PAYMENTS,
                 "june_daily_pace": round(JUNE_PAYMENT / 30),
                 "july_daily_pace_calendar": round(total_pay / n_days_observed),
                 "july_projection_31d": round(total_pay / n_days_observed * 31)},
}
(BASE / "july_donations_20260722.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ["coverage", "totals", "halves", "types",
                                      "amount_clusters_cheese", "roulette_candidates",
                                      "baseline"]}, ensure_ascii=False, indent=1))
print("donor_concentration:", json.dumps({k: v for k, v in out["donor_concentration"].items()
                                          if k != "top_detail_internal"}, ensure_ascii=False))
