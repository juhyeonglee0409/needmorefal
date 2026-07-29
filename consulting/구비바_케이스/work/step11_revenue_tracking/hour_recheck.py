# -*- coding: utf-8 -*-
import re, datetime
from collections import defaultdict
from pathlib import Path
import openpyxl
DATA=Path(__file__).parent.parent.parent/"data"/"revenue"
def won(s): return int(re.sub(r"[^\d]","",str(s))) if s else 0
wb=openpyxl.load_workbook(DATA/"구비바_일반후원_detail_20260729.xlsx",data_only=True,read_only=True)
rows=[]
for r in wb["상세내역"].iter_rows(min_row=3,values_only=True):
    if not r[1]: continue
    d=str(r[1])
    rows.append({"nick":r[0],"date":d[:10],"hour":int(d[11:13]),"cheese":won(r[3]),
                 "type":str(r[4]),"msg":(str(r[6])[:30] if r[6] else "")})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]

BUCK=[("13~14시",range(13,15)),("15~18시",range(15,19)),("19~20시",range(19,21)),("21시~",range(21,26))]
def report(title, rs):
    tot=sum(r["cheese"] for r in rs)
    print(f"\n--- {title} (총 {tot:,}치즈 / {len(rs)}건) ---")
    for nm,hr in BUCK:
        sub=[r for r in rs if r["hour"] in hr]
        c=sum(r["cheese"] for r in sub)
        ext=len([r for r in sub if r["type"]=="채팅" and r["cheese"]==1200])
        ent=len([r for r in sub if r["type"]=="채팅" and r["cheese"]==1100])
        avg=c/len(sub) if sub else 0
        print(f"  {nm:<8} {c:>8,}치즈 ({c/tot*100:>4.1f}%)  {len(sub):>3}건  건당 {avg:>6,.0f}  연장 {ext:>2}회 엔터 {ent:>2}회")

report("전체 (v4 기준)", rows)
clean=[r for r in rows if r["type"]!="미션" and r["cheese"]<10000]
report("미션 + 1만이상 대형 제외", clean)
report("영상 후원만", [r for r in rows if "영상" in r["type"]])

print("\n\n=== 19~21시 발생 후원 전수 ===")
for r in sorted([r for r in rows if r["hour"]>=19],key=lambda r:(r["date"],r["hour"])):
    print(f"  {r['date']}({wd(r['date'])}) {r['hour']}시  {r['cheese']:>7,}  [{r['type']}]  {r['nick']}  {r['msg']}")
