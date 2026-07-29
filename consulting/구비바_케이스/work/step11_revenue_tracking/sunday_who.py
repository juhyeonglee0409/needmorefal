# -*- coding: utf-8 -*-
import re, datetime
from collections import defaultdict, Counter
from pathlib import Path
import openpyxl
DATA=Path(__file__).parent.parent.parent/"data"/"revenue"
def won(s): return int(re.sub(r"[^\d]","",str(s))) if s else 0
wb=openpyxl.load_workbook(DATA/"구비바_일반후원_detail_20260729.xlsx",data_only=True,read_only=True)
rows=[]
for r in wb["상세내역"].iter_rows(min_row=3,values_only=True):
    if not r[1]: continue
    d=str(r[1])
    rows.append({"nick":str(r[0]),"date":d[:10],"hour":int(d[11:13]),"time":d[11:16],
                 "cheese":won(r[3]),"type":str(r[4]),"msg":(str(r[6]) if r[6] else "")})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]

print("=== 엔터 룰렛(1,100) 메시지 샘플 ===")
ent=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1100]
for r in ent[:12]: print(f"  {r['date']}({wd(r['date'])}) {r['time']}  {r['nick'][:14]:<15} {r['msg'][:40]}")
print(f"  ... 총 {len(ent)}회")
print("\n=== 연장 룰렛(1,200) 메시지 샘플 ===")
ext=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1200]
for r in ext[:10]: print(f"  {r['date']}({wd(r['date'])}) {r['time']}  {r['nick'][:14]:<15} {r['msg'][:40]}")

print("\n=== 엔터 룰렛 사용자 분포 ===")
c=Counter(r["nick"] for r in ent)
for n,k in c.most_common():
    sun=len([r for r in ent if r["nick"]==n and wd(r["date"])=="일"])
    print(f"  {n[:16]:<17} {k:>3}회 (일요일 {sun}회)")

print("\n=== 일요일 초과분 기여자 (일반 후원, 평일 대비) ===")
EXC={"2026.07.25","2026.07.26"}
mission=set(id(r) for r in rows if r["type"]=="미션" or "미션" in r["msg"])
def ev(r): return id(r) in mission or r["cheese"]>=10000
sun=defaultdict(int); wkd=defaultdict(int)
sd={r["date"] for r in rows if wd(r["date"])=="일" and r["date"] not in EXC}
wd_={r["date"] for r in rows if wd(r["date"]) not in ("토","일") and r["date"] not in EXC}
for r in rows:
    if ev(r) or r["date"] in EXC: continue
    if wd(r["date"])=="일": sun[r["nick"]]+=r["cheese"]
    elif wd(r["date"])!="토": wkd[r["nick"]]+=r["cheese"]
print(f"  (일요일 {len(sd)}일 / 평일 {len(wd_)}일)")
diff=[(n, sun[n]/len(sd), wkd.get(n,0)/len(wd_)) for n in sun]
for n,s,w in sorted(diff,key=lambda x:-(x[1]-x[2]))[:10]:
    print(f"  {n[:16]:<17} 일요일 일평균 {s:>7,.0f} | 평일 일평균 {w:>7,.0f} | 차 {s-w:>+8,.0f}")
tot_s=sum(x[1] for x in diff); tot_w=sum(x[2] for x in diff)
print(f"  합계: 일요일 {tot_s:,.0f} / 평일(같은 사람들) {tot_w:,.0f}")
