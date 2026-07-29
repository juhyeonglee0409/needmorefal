# -*- coding: utf-8 -*-
import re
from collections import defaultdict, Counter
from pathlib import Path
import openpyxl
import datetime

BASE = Path(__file__).parent
DATA = BASE.parent.parent / "data" / "revenue"
DETAIL = DATA / "구비바_일반후원_detail_20260729.xlsx"

def won(s):
    return int(re.sub(r"[^\d]", "", str(s))) if s else 0

wb = openpyxl.load_workbook(DETAIL, data_only=True, read_only=True)
rows = []
for r in wb["상세내역"].iter_rows(min_row=3, values_only=True):
    if not r[1]:
        continue
    d = str(r[1])
    rows.append({"nick": r[0], "dt": d, "date": d[:10], "time": d[11:16],
                 "hour": int(d[11:13]) if len(d) > 12 else -1,
                 "pay": won(r[2]), "cheese": won(r[3]), "type": str(r[4]),
                 "msg": str(r[6]) if r[6] else ""})
wb.close()

WD = ["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd = [int(x) for x in ds.split(".")]
    return WD[datetime.date(y,m,dd).weekday()]

print("=== 날짜별 요약 (요일 / 건수 / 치즈 / 유형분해) ===")
bydate = defaultdict(lambda: defaultdict(lambda: [0,0]))
tot = defaultdict(lambda: [0,0])
for r in rows:
    bydate[r["date"]][r["type"]][0] += 1
    bydate[r["date"]][r["type"]][1] += r["cheese"]
    tot[r["date"]][0] += 1
    tot[r["date"]][1] += r["cheese"]

for d in sorted(bydate):
    parts = " | ".join(f"{k} {v[0]}건/{v[1]:,}" for k,v in sorted(bydate[d].items(), key=lambda kv:-kv[1][1]))
    mark = "  <<< 일요일" if wd(d)=="일" else ""
    print(f"{d}({wd(d)})  총 {tot[d][0]:>3}건 / {tot[d][1]:>7,}치즈   {parts}{mark}")

print()
print("=== 영상 후원 전수 (금액대 분포) ===")
vid = [r for r in rows if "영상" in r["type"]]
print(f"영상 후원 {len(vid)}건 / {sum(r['cheese'] for r in vid):,}치즈")
print("금액대 카운트:", dict(sorted(Counter(r["cheese"] for r in vid).items())))
print()
print("일자/시각별 영상 후원:")
for r in sorted(vid, key=lambda r: r["dt"]):
    print(f"  {r['date']}({wd(r['date'])}) {r['time']}  {r['cheese']:>6,}치즈  {r['nick']}")
