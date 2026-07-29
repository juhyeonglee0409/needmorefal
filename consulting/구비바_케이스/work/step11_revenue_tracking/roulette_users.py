# -*- coding: utf-8 -*-
import re, datetime
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl
DATA=Path(__file__).parent.parent.parent/"data"/"revenue"
def won(s): return int(re.sub(r"[^\d]","",str(s))) if s else 0
wb=openpyxl.load_workbook(DATA/"구비바_일반후원_detail_20260729.xlsx",data_only=True,read_only=True)
rows=[]
for r in wb["상세내역"].iter_rows(min_row=3,values_only=True):
    if not r[1]: continue
    d=str(r[1])
    rows.append({"nick":str(r[0]),"date":d[:10],"hour":int(d[11:13]),"cheese":won(r[3]),"type":str(r[4])})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]

ext=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1200]
ent=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1100]
print("=== 연장 룰렛(1,200) 사용자 ===")
for n,k in Counter(r["nick"] for r in ext).most_common():
    ds=sorted({r["date"][5:] for r in ext if r["nick"]==n})
    print(f"  {n[:16]:<17} {k:>2}회  {ds}")
print("\n=== 연장 룰렛 날짜별 집중도 ===")
c=Counter(r["date"] for r in ext)
for d,k in sorted(c.items()): print(f"  {d}({wd(d)}) {k:>2}회")
print(f"  상위 2일 합계 {sum(sorted(c.values(),reverse=True)[:2])}회 / 전체 {len(ext)}회")

alld={r["nick"] for r in rows}
ru={r["nick"] for r in ext}|{r["nick"] for r in ent}
print(f"\n=== 저변 ===")
print(f"  전체 후원자 {len(alld)}명 / 룰렛 사용 경험자 {len(ru)}명 ({len(ru)/len(alld)*100:.0f}%)")
print(f"  룰렛 미사용 {len(alld-ru)}명: {sorted(alld-ru)}")
top3={"노롱이당","시드o1","타락악"}
print(f"\n  엔터 룰렛 88회 중 상위 3인 {len([r for r in ent if r['nick'] in top3])}회 ({len([r for r in ent if r['nick'] in top3])/len(ent)*100:.0f}%)")
print(f"  연장 룰렛 26회 중 상위 3인 {len([r for r in ext if r['nick'] in top3])}회")
