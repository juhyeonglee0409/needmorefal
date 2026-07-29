# -*- coding: utf-8 -*-
"""구비바 룰렛 도입 4주 결산 (2026-07-01 도입, 07-29 기준).

7/22 중간 점검(20일차) 대비 최종 4주 결산.
비교 기준선: 6월 결제액 676,786원(31일), 1~6월 월별 결제액.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

BASE = Path(__file__).parent
DATA = BASE.parent.parent / "data" / "revenue"
DETAIL = DATA / "구비바_일반후원_detail_20260729.xlsx"

MONTH_PAY = {"1월": 362489, "2월": 600508, "3월": 587873,
             "4월": 457644, "5월": 712034, "6월": 676786}
JUNE_REV = 473751


def won(s):
    return int(re.sub(r"[^\d]", "", s)) if s else 0


wb = openpyxl.load_workbook(DETAIL, data_only=True, read_only=True)
rows = []
for r in wb["상세내역"].iter_rows(min_row=3, values_only=True):
    if not r[1]:
        continue
    rows.append({"nick": r[0], "dt": r[1], "date": r[1][:10],
                 "pay": won(r[2]), "cheese": won(r[3]), "type": r[4],
                 "msg": str(r[6]) if r[6] else ""})
wb.close()

days = sorted({r["date"] for r in rows})
total_pay = sum(r["pay"] for r in rows)
total_cheese = sum(r["cheese"] for r in rows)
n_cal = 29  # 7/1~7/29

# 주차 분해 (7/1 기준 7일 단위)
def wk(d):
    day = int(d.split(".")[2])
    return min((day - 1) // 7 + 1, 5)

weekly = defaultdict(lambda: {"pay": 0, "cheese": 0, "n": 0, "donors": set(), "days": set()})
for r in rows:
    w = weekly[wk(r["date"])]
    w["pay"] += r["pay"]; w["cheese"] += r["cheese"]; w["n"] += 1
    w["donors"].add(r["nick"]); w["days"].add(r["date"])

# 유형별
types = defaultdict(lambda: {"n": 0, "cheese": 0})
for r in rows:
    types[r["type"]]["n"] += 1
    types[r["type"]]["cheese"] += r["cheese"]

# 룰렛 시그니처 (1,100치즈 채팅)
r1100 = [r for r in rows if r["cheese"] == 1100 and r["type"] == "채팅"]
r1100_by_wk = Counter(wk(r["date"]) for r in r1100)

# 후원자 집중도
donors = defaultdict(lambda: {"cheese": 0, "n": 0})
for r in rows:
    donors[r["nick"]]["cheese"] += r["cheese"]
    donors[r["nick"]]["n"] += 1
ranked = sorted(donors.items(), key=lambda kv: -kv[1]["cheese"])
top1 = ranked[0][1]["cheese"] / total_cheese
top5 = sum(v["cheese"] for _, v in ranked[:5]) / total_cheese

print("=" * 56)
print(f"기간: {days[0]} ~ {days[-1]} | 방송일 {len(days)}일 / 달력 {n_cal}일")
print(f"총 결제액 {total_pay:,}원 | 총 치즈 {total_cheese:,} | 예상수익(70%) {round(total_cheese*0.7):,}원")
print(f"유니크 후원자 {len(donors)}명")
print()
print("[6월 대비]")
print(f"  6월 결제액 {MONTH_PAY['6월']:,}원(31일) → 7월 {total_pay:,}원({n_cal}일)")
print(f"  총액 대비 {total_pay/MONTH_PAY['6월']*100-100:+.1f}%")
print(f"  일평균 {MONTH_PAY['6월']/31:,.0f} → {total_pay/n_cal:,.0f} ({total_pay/n_cal/(MONTH_PAY['6월']/31)*100-100:+.1f}%)")
print(f"  31일 환산 {total_pay/n_cal*31:,.0f}원 (역대 최고 5월 {MONTH_PAY['5월']:,} 대비 {total_pay/n_cal*31/MONTH_PAY['5월']*100-100:+.1f}%)")
print()
print("[주차별]")
for w in sorted(weekly):
    v = weekly[w]
    lbl = f"{(w-1)*7+1}~{min(w*7,29)}일"
    print(f"  W{w} ({lbl:>7}) 결제 {v['pay']:>8,}원 | {v['n']:>3}건 | 후원자 {len(v['donors']):>2}명 | 방송일 {len(v['days'])}일 | 1100채팅 {r1100_by_wk.get(w,0):>2}회")
print()
print("[유형별 치즈]")
for k, v in sorted(types.items(), key=lambda kv: -kv[1]["cheese"]):
    print(f"  {k:<8} {v['cheese']:>7,} ({v['cheese']/total_cheese*100:4.1f}%) / {v['n']:>3}건")
print()
print(f"[룰렛 시그니처] 1,100치즈 채팅 {len(r1100)}건 = {sum(r['cheese'] for r in r1100):,}치즈 ({sum(r['cheese'] for r in r1100)/total_cheese*100:.1f}%)")
print(f"[집중도] top1 {top1*100:.1f}% / top5 {top5*100:.1f}% / n={len(donors)}")
