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
    rows.append({"nick":r[0],"date":d[:10],"hour":int(d[11:13]),"pay":won(r[2]),
                 "cheese":won(r[3]),"type":str(r[4]),"msg":(str(r[6]) if r[6] else "")})
wb.close()

# 미션 실적 = type 미션 + 히든미션 채팅 결제
mission = [r for r in rows if r["type"]=="미션" or ("미션" in r["msg"] and r["type"]!="미션")]
print("=== 미션 실적 재집계 ===")
for r in sorted(mission,key=lambda r:r["date"]):
    print(f"  {r['date']} {r['hour']}시 {r['cheese']:>6,} [{r['type']}] {r['msg'][:35]}")
mc=sum(r["cheese"] for r in mission)
print(f"  합계 {mc:,}치즈 = 실수령 {mc*0.7:,.0f}원  | 계획 84,000원 대비 {mc*0.7/84000*100:.1f}%")
print(f"  (v4 집계: type=미션만 {sum(r['cheese'] for r in rows if r['type']=='미션'):,}치즈)")

ent=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1100]
ext=[r for r in rows if r["type"]=="채팅" and r["cheese"]==1200]
print(f"\n엔터 룰렛 {len(ent)}회 = {len(ent)*1100:,}치즈 = {len(ent)*1100*0.7:,.0f}원")
print(f"연장 룰렛 {len(ext)}회 = {len(ext)*1200:,}치즈 = {len(ext)*1200*0.7:,.0f}원")
print(f"장치 3종 합계 실수령 {(mc+len(ent)*1100+len(ext)*1200)*0.7:,.0f}원")

print("\n=== 19~20시 구성 ===")
n=[r for r in rows if r["hour"] in (19,20)]
m=[r for r in n if r in mission]; big=[r for r in n if r["cheese"]>=10000 and r not in mission]
oth=[r for r in n if r not in mission and r["cheese"]<10000]
print(f"  전체 {sum(r['cheese'] for r in n):,}치즈 / {len(n)}건")
print(f"   미션성 {sum(r['cheese'] for r in m):,} ({len(m)}건)")
print(f"   대형단발 {sum(r['cheese'] for r in big):,} ({len(big)}건)")
print(f"   일반 {sum(r['cheese'] for r in oth):,} ({len(oth)}건, 건당 {sum(r['cheese'] for r in oth)/len(oth):,.0f})")

print("\n=== 장치 배치 현황 (일반 후원 기준: 미션성·1만이상 제외) ===")
clean=[r for r in rows if r not in mission and r["cheese"]<10000]
tc=sum(r["cheese"] for r in clean)
for nm,hr in [("13~14시",range(13,15)),("15~18시",range(15,19)),("19~20시",range(19,21)),("21시~",range(21,26))]:
    s=[r for r in clean if r["hour"] in hr]
    c=sum(r["cheese"] for r in s)
    e=len([r for r in s if r["type"]=="채팅" and r["cheese"]==1100])
    x=len([r for r in s if r["type"]=="채팅" and r["cheese"]==1200])
    v=len([r for r in s if "영상" in r["type"]])
    ms=sum(r["cheese"] for r in mission if r["hour"] in hr)
    print(f"  {nm:<8} 일반 {c:>7,}치즈({c/tc*100:>4.1f}%) 건당{c/len(s):>6,.0f} | 영상{v:>3}건 엔터{e:>3}회 연장{x:>2}회 | 미션 {ms:>6,}")
