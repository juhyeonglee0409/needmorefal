# -*- coding: utf-8 -*-
import re, datetime
from collections import defaultdict, Counter
from pathlib import Path
import openpyxl

BASE = Path(__file__).parent
DATA = BASE.parent.parent / "data" / "revenue"
DETAIL = DATA / "구비바_일반후원_detail_20260729.xlsx"

def won(s): return int(re.sub(r"[^\d]", "", str(s))) if s else 0
wb = openpyxl.load_workbook(DETAIL, data_only=True, read_only=True)
rows = []
for r in wb["상세내역"].iter_rows(min_row=3, values_only=True):
    if not r[1]: continue
    d = str(r[1])
    rows.append({"nick": r[0], "date": d[:10], "time": d[11:16],
                 "hour": int(d[11:13]), "pay": won(r[2]), "cheese": won(r[3]),
                 "type": str(r[4])})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]

SUN = ["2026.07.05","2026.07.12","2026.07.19","2026.07.26"]
print("=== 일요일 4회 시간대별 (영상 / 채팅 / 기타) ===")
for d in SUN:
    rs=[r for r in rows if r["date"]==d]
    print(f"\n[{d}] 총 {len(rs)}건 / {sum(r['cheese'] for r in rs):,}치즈")
    byh=defaultdict(lambda: defaultdict(lambda:[0,0]))
    for r in rs:
        byh[r["hour"]][r["type"]][0]+=1; byh[r["hour"]][r["type"]][1]+=r["cheese"]
    for h in sorted(byh):
        parts=" ".join(f"{k}{v[0]}건/{v[1]:,}" for k,v in sorted(byh[h].items(),key=lambda kv:-kv[1][1]))
        tot_c=sum(v[1] for v in byh[h].values()); tot_n=sum(v[0] for v in byh[h].values())
        print(f"   {h:>2}시  {tot_n:>3}건 {tot_c:>7,}치즈   {parts}")

print("\n\n=== 요일별 평균 (방송일만, 7/25-26 포함) ===")
byw=defaultdict(lambda:{"c":0,"n":0,"d":set(),"vid":0,"vidn":0})
for r in rows:
    w=wd(r["date"]); byw[w]["c"]+=r["cheese"]; byw[w]["n"]+=1; byw[w]["d"].add(r["date"])
    if "영상" in r["type"]: byw[w]["vid"]+=r["cheese"]; byw[w]["vidn"]+=1
for w in WD:
    if w not in byw: print(f"  {w}  (방송 없음)"); continue
    v=byw[w]; nd=len(v["d"])
    print(f"  {w}  방송 {nd}일  일평균 {v['c']/nd:>8,.0f}치즈  (영상 {v['vid']/nd:>7,.0f} / {v['vidn']/nd:.1f}건)")

print("\n\n=== 룰렛 스핀 날짜별 (1,100 엔터 / 1,200 연장, 채팅형) ===")
for d in sorted({r["date"] for r in rows}):
    rs=[r for r in rows if r["date"]==d and r["type"]=="채팅"]
    e=[r for r in rs if r["cheese"]==1100]; x=[r for r in rs if r["cheese"]==1200]
    oth=[r for r in rs if r["cheese"] not in (1100,1200)]
    print(f"  {d}({wd(d)})  엔터 {len(e):>2}회  연장 {len(x):>2}회  기타채팅 {len(oth):>2}건/{sum(r['cheese'] for r in oth):,}")

print("\n\n=== 일요일 기여도 ===")
sun_c=sum(r["cheese"] for r in rows if wd(r["date"])=="일")
all_c=sum(r["cheese"] for r in rows)
print(f"  일요일 4일 합계 {sun_c:,}치즈 / 전체 {all_c:,} = {sun_c/all_c*100:.1f}%")
for d in SUN:
    rs=[r for r in rows if r["date"]==d]
    v=[r for r in rs if "영상" in r["type"]]
    print(f"   {d}: 총 {sum(r['cheese'] for r in rs):>7,}  영상 {len(v):>2}건/{sum(r['cheese'] for r in v):>7,}  영상평균 {(sum(r['cheese'] for r in v)/len(v) if v else 0):>6,.0f}")
nonsun_v=[r for r in rows if "영상" in r["type"] and wd(r["date"])!="일"]
print(f"   비일요일 영상 {len(nonsun_v)}건 평균 {sum(r['cheese'] for r in nonsun_v)/len(nonsun_v):,.0f}치즈")
