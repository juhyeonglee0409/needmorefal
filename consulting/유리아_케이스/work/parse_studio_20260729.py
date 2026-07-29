# -*- coding: utf-8 -*-
"""유리아 치지직 스튜디오 라이브 분석 파싱 (2026-03-01 ~ 07-27, 119방송)."""
import json, re
from pathlib import Path
import openpyxl

BASE = Path(__file__).parent.parent / "data" / "studio"

def hms_to_h(s):
    if not s or s in ("-", "0"): return 0.0
    p = [int(x) for x in str(s).split(":")]
    return p[0] + p[1]/60 + (p[2] if len(p) > 2 else 0)/3600

def num(s):
    if s is None or str(s).strip() in ("-", "", "후원 치즈"): return None
    m = re.sub(r"[^\d.]", "", str(s))
    return float(m) if m else None

rows = []
for fn in ["유리아_live_2026030104_20260727.xlsx", "유리아_live_2026050727_20260727.xlsx"]:
    wb = openpyxl.load_workbook(BASE / fn, data_only=True, read_only=True)
    ws = wb["상세내역"]
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < 2 or not r[0]: continue
        rows.append({
            "start": str(r[0])[:19], "date": str(r[0])[:10], "title": str(r[1]),
            "air_h": round(hms_to_h(r[2]), 2), "plays": num(r[3]), "uniq": num(r[4]),
            "avg_ccv": num(r[5]), "max_ccv": num(r[6]),
            "watch_h": round(hms_to_h(r[7]), 2), "avg_dur_min": round(hms_to_h(r[8])*60, 1),
            "retention_pct": num(str(r[9]).replace("%","")) if r[9] else None,
            "chat_users": num(r[10]),
            "chat_rate_pct": num(str(r[11]).replace("%","")) if r[11] else None,
            "cheese": num(r[12]), "don_cnt": num(r[13]),
        })
    wb.close()

rows.sort(key=lambda r: r["start"])
print(f"총 {len(rows)}방송  {rows[0]['date']} ~ {rows[-1]['date']}")

# 치즈 컬럼 상태 확인
cz = [r for r in rows if r["cheese"] is not None]
dn = [r for r in rows if r["don_cnt"]]
print(f"치즈값 있는 행 {len(cz)} / 후원건수>0 행 {len(dn)}")
for r in dn: print(f"  {r['date']} {r['title'][:30]:<32} 치즈={r['cheese']} 건수={r['don_cnt']:.0f}")

out = Path(__file__).parent / "studio_live_119_20260729.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nsaved: {out.name}")

# 월별 요약
from collections import defaultdict
mon = defaultdict(list)
for r in rows: mon[r["date"][:7]].append(r)
print(f"\n{'월':<9}{'방송':>4}{'시간':>7}{'유니크':>7}{'평CCV':>6}{'피크':>5}{'지속분':>7}{'지속률':>7}{'채팅률':>7}")
for m in sorted(mon):
    rs = mon[m]
    air = sum(r["air_h"] for r in rs)
    uq = sum(r["uniq"] or 0 for r in rs)
    ccv = [r["avg_ccv"] for r in rs if r["avg_ccv"]]
    mx = max(r["max_ccv"] or 0 for r in rs)
    dur = [r["avg_dur_min"] for r in rs if r["avg_dur_min"]]
    ret = [r["retention_pct"] for r in rs if r["retention_pct"] is not None]
    cr = [r["chat_rate_pct"] for r in rs if r["chat_rate_pct"] is not None]
    print(f"{m:<9}{len(rs):>4}{air:>7.1f}{uq:>7.0f}{(sum(ccv)/len(ccv) if ccv else 0):>6.1f}{mx:>5.0f}{(sum(dur)/len(dur) if dur else 0):>7.1f}{(sum(ret)/len(ret) if ret else 0):>7.2f}{(sum(cr)/len(cr) if cr else 0):>7.1f}")
