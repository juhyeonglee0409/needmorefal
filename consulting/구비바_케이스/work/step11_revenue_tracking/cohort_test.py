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
    rows.append({"nick":str(r[0]),"date":d[:10],"hour":int(d[11:13]),"cheese":won(r[3]),
                 "type":str(r[4]),"msg":(str(r[6]) if r[6] else "")})
wb.close()
WD=["월","화","수","목","금","토","일"]
def wd(ds):
    y,m,dd=[int(x) for x in ds.split(".")]; return WD[datetime.date(y,m,dd).weekday()]
mission=set(id(r) for r in rows if r["type"]=="미션" or "미션" in r["msg"])
def is_ev(r): return id(r) in mission or r["cheese"]>=10000
EXC={"2026.07.25","2026.07.26"}   # 같이보기 회차

print("=== 요일별 (같이보기 2일 제외, 일반 후원 기준) ===")
for w in WD:
    rs=[r for r in rows if wd(r["date"])==w and r["date"] not in EXC]
    if not rs: print(f"  {w}  방송 없음"); continue
    nd=len({r["date"] for r in rs})
    gen=[r for r in rs if not is_ev(r)]
    ev=sum(r["cheese"] for r in rs if is_ev(r))
    print(f"  {w}  방송{nd}일 | 일반 일평균 {sum(r['cheese'] for r in gen)/nd:>8,.0f} | 이벤트 {ev:>7,} | 후원자 {len({r['nick'] for r in rs}):>2}명")

print("\n=== 요일 x 시간대 (일반 후원 일평균) ===")
BUCK=[("13~14",range(13,15)),("15~18",range(15,19)),("19~20",range(19,21)),("21~",range(21,26))]
print(f"  {'':4} " + " ".join(f"{n:>9}" for n,_ in BUCK))
for w in WD:
    rs=[r for r in rows if wd(r["date"])==w and r["date"] not in EXC and not is_ev(r)]
    if not rs: continue
    nd=len({r["date"] for r in [x for x in rows if wd(x["date"])==w and x["date"] not in EXC]})
    cells=[]
    for n,hr in BUCK:
        c=sum(r["cheese"] for r in rs if r["hour"] in hr)
        cells.append(f"{c/nd:>9,.0f}")
    print(f"  {w}    " + " ".join(cells))

print("\n=== 후원자별 프로필 (일반 후원 기준, 상위 12명) ===")
prof=defaultdict(lambda:{"평일낮":0,"평일저녁":0,"토":0,"일":0,"tot":0,"days":set()})
for r in rows:
    if is_ev(r) or r["date"] in EXC: continue
    w=wd(r["date"]); p=prof[r["nick"]]
    p["tot"]+=r["cheese"]; p["days"].add(r["date"])
    if w=="일": p["일"]+=r["cheese"]
    elif w=="토": p["토"]+=r["cheese"]
    elif r["hour"]>=19: p["평일저녁"]+=r["cheese"]
    else: p["평일낮"]+=r["cheese"]
for n,p in sorted(prof.items(),key=lambda kv:-kv[1]["tot"])[:12]:
    t=p["tot"]
    print(f"  {n[:16]:<17} {t:>7,}  평일낮 {p['평일낮']/t*100:>4.0f}% 평일저녁 {p['평일저녁']/t*100:>4.0f}% 토 {p['토']/t*100:>4.0f}% 일 {p['일']/t*100:>4.0f}%  ({len(p['days'])}일 등장)")

print("\n=== 직장인 가설 검정 ===")
sun_donors={r["nick"] for r in rows if wd(r["date"])=="일" and r["date"] not in EXC}
eve_donors={r["nick"] for r in rows if wd(r["date"]) not in ("토","일") and r["hour"]>=19 and r["date"] not in EXC}
day_donors={r["nick"] for r in rows if wd(r["date"]) not in ("토","일") and r["hour"]<19 and r["date"] not in EXC}
print(f"  일요일 후원자 {len(sun_donors)}명 / 평일저녁(19시+) 후원자 {len(eve_donors)}명 / 평일낮 후원자 {len(day_donors)}명")
print(f"  일요일 & 평일저녁 겹침: {len(sun_donors&eve_donors)}명 = 평일저녁의 {len(sun_donors&eve_donors)/len(eve_donors)*100:.0f}%")
print(f"  평일저녁 전용(낮에 안 옴): {len(eve_donors-day_donors)}명 -> {sorted(eve_donors-day_donors)}")
print(f"  일요일 전용(평일 안 옴): {sorted(sun_donors-day_donors-eve_donors)}")

print("\n=== 토요일 vs 일요일 (같이보기 제외) ===")
for w in ("토","일"):
    rs=[r for r in rows if wd(r["date"])==w and r["date"] not in EXC]
    nd=len({r["date"] for r in rs}); gen=[r for r in rs if not is_ev(r)]
    ent=len([r for r in rs if r["type"]=="채팅" and r["cheese"]==1100])
    print(f"  {w} {nd}일: 일평균 {sum(r['cheese'] for r in gen)/nd:>8,.0f} | 엔터룰렛 {ent}회 | 날짜 {sorted({r['date'] for r in rs})}")
