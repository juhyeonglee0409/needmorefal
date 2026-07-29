# -*- coding: utf-8 -*-
"""롤캐 신호 조합 백테스트: 8주 효율 상위 15% + 4주 관성 가속.
기준 주: 2026-04-06 (인덱스 39). 결과 창: 이후 12주 (40~52).
모수: 팔로워 2,500 이하 (현재 밴드와 동일 정의)."""
import json
from pathlib import Path

SRC = Path(__file__).parent.parent / "census_full_20260708" / "census_full_weekly.ndjson"
AT = 39   # 2026-04-06
chs = []
with open(SRC, encoding="utf-8") as f:
    for line in f:
        chs.append(json.loads(line))
print("기준 주:", chs[0]["weeks"][AT]["date"], "| 결과 창:", chs[0]["weeks"][AT+1]["date"], "~", chs[0]["weeks"][52]["date"])

cands = []
for c in chs:
    w = c["weeks"]
    f_at = w[AT]["maxFollowerCount"]
    if not f_at or f_at > 2495: continue
    w8 = w[AT-7:AT+1]
    act = [r for r in w8 if r["airTime"] and r["airTime"] > 0]
    if len(act) < 4: continue
    airsum = sum(r["airTime"] for r in act)
    gain8 = (w8[-1]["maxFollowerCount"] or 0) - (w8[0]["maxFollowerCount"] or 0)
    eff = gain8 / airsum if airsum > 0 else None
    if eff is None: continue
    g_recent = (w8[-1]["maxFollowerCount"] or 0) - (w8[3]["maxFollowerCount"] or 0)
    g_prior = (w8[3]["maxFollowerCount"] or 0) - (w8[0]["maxFollowerCount"] or 0)
    out = (w[52]["maxFollowerCount"] or 0) - (w[AT]["maxFollowerCount"] or 0)
    cands.append({"eff": eff, "accel": g_recent > g_prior and g_recent > 0, "out": out, "f": f_at})

effs = sorted(c["eff"] for c in cands)
cut = effs[int(len(effs) * 0.85)]
sig = [c for c in cands if c["eff"] >= cut and c["accel"]]
rest = [c for c in cands if not (c["eff"] >= cut and c["accel"])]
med_all = sorted(c["out"] for c in cands)[len(cands)//2]
print(f"모수 {len(cands)} | 효율 상위15% 컷 {cut:.3f} | 신호 충족 {len(sig)}")
def stats(pool, name):
    outs = sorted(c["out"] for c in pool)
    med = outs[len(outs)//2]
    over = sum(1 for c in pool if c["out"] > med_all) / len(pool) * 100
    print(f"  {name}: 이후 12주 증가 중위 {med:+.0f} | 전체 중위({med_all:+.0f}) 초과 비율 {over:.0f}%")
stats(sig, "신호 충족")
stats(rest, "미충족  ")
ratio = (sorted(c['out'] for c in sig)[len(sig)//2]) / max(1, med_all)
print(f"  중위 배율: {ratio:.1f}배")
