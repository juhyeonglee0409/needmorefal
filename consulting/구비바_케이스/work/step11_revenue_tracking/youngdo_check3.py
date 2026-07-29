# -*- coding: utf-8 -*-
import re, datetime
from collections import defaultdict
from pathlib import Path
import openpyxl
BASE=Path(__file__).parent; DATA=BASE.parent.parent/"data"/"revenue"
def won(s): return int(re.sub(r"[^\d]","",str(s))) if s else 0
wb=openpyxl.load_workbook(DATA/"구비바_일반후원_detail_20260729.xlsx",data_only=True,read_only=True)
rows=[]
for r in wb["상세내역"].iter_rows(min_row=3,values_only=True):
    if not r[1]: continue
    d=str(r[1])
    rows.append({"nick":r[0],"date":d[:10],"time":d[11:16],"hour":int(d[11:13]),
                 "pay":won(r[2]),"cheese":won(r[3]),"type":str(r[4]),
                 "msg":(str(r[6])[:40] if r[6] else "")})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]

print("=== 10,000치즈 이상 단일 후원 ===")
for r in sorted([r for r in rows if r["cheese"]>=10000],key=lambda r:-r["cheese"]):
    print(f"  {r['date']}({wd(r['date'])}) {r['time']}  {r['cheese']:>7,}  [{r['type']}]  {r['nick']}  {r['msg']}")

print("\n=== 룰렛 스핀의 요일 분포 ===")
ent=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1100]
ext=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1200]
for nm,arr in [("엔터(1,100)",ent),("연장(1,200)",ext)]:
    c=defaultdict(int)
    for r in arr: c[wd(r["date"])]+=1
    tot=len(arr)
    s=" ".join(f"{w}{c.get(w,0)}" for w in WD)
    sun=c.get("일",0)
    print(f"  {nm} 총 {tot}회  |  {s}  |  일요일 {sun}회 = {sun/tot*100:.1f}%")

print("\n=== 주차별: 대형 채팅 후원(1만 이상) 제외 시 ===")
def wk(d): return min((int(d.split(".")[2])-1)//7+1,5)
EXC_DATES={"2026.07.25","2026.07.26"}
for w in [1,2,3,4]:
    rs=[r for r in rows if wk(r["date"])==w]
    days={r["date"] for r in rs}
    days_adj=days-EXC_DATES if w==4 else days
    rs2=[r for r in rs if r["date"] in days_adj]
    mission=sum(r["cheese"] for r in rs2 if r["type"]=="미션")
    big=sum(r["cheese"] for r in rs2 if r["cheese"]>=10000 and r["type"]!="미션")
    tot=sum(r["cheese"] for r in rs2)
    n=len(days_adj)
    print(f"  W{w} 방송{n}일  원본 {tot/n:>8,.0f}  미션제외 {(tot-mission)/n:>8,.0f}  미션+대형제외 {(tot-mission-big)/n:>8,.0f}")

print("\n=== 일요일 vs 평일 (7/26 같이보기 제외) ===")
sun=[r for r in rows if wd(r["date"])=="일" and r["date"]!="2026.07.26"]
oth=[r for r in rows if wd(r["date"])!="일" and r["date"]!="2026.07.25"]
for nm,arr in [("일요일 3일",sun),("그 외 16일",oth)]:
    nd=len({r["date"] for r in arr})
    v=[r for r in arr if "영상" in r["type"]]
    e=[r for r in arr if r["type"]=="채팅" and r["cheese"]==1100]
    print(f"  {nm}: 일평균 {sum(r['cheese'] for r in arr)/nd:>8,.0f}치즈 | 영상 {len(v)/nd:.1f}건 {sum(r['cheese'] for r in v)/nd:>7,.0f} | 엔터룰렛 {len(e)/nd:.1f}회 | 후원자 {len({r['nick'] for r in arr})}명")
