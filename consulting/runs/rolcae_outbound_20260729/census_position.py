# -*- coding: utf-8 -*-
"""롤캐 센서스 위치 산출 (census_full_20260708, 7,472채널 53주)."""
import json
from pathlib import Path

CID = "b70ec4738c99441a62672fe4fb6edbe2"
SRC = Path(__file__).parent.parent / "census_full_20260708" / "census_full_weekly.ndjson"

target = None
channels = []
with open(SRC, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        channels.append(d)
        if d["channel_id"] == CID:
            target = d

print(f"채널 수: {len(channels)}")
w = target["weeks"]
print(f"롤캐: segment={target['segment']} followers={target['follower_count']} weeks={len(w)}")
print("\n[롤캐 53주 중 처음 4주 / 마지막 4주]")
for r in w[:4] + w[-4:]:
    print(f"  {r['date']}  평청 {r['avgLiveViews']:>3}  피크 {r['maxLiveViews']:>3}  방송 {r['airTime']:>5.1f}h  팔로워 {r['maxFollowerCount']:>5}")

# 최근 8주 창 (2026-05-11 ~ 2026-07-06 근처, 마지막 주는 2.6h라 불완전 -> 마지막 주 제외 8주)
def window(ws, n=8, skip_last=1):
    act = ws[:-skip_last] if skip_last else ws
    return act[-n:]

def metrics(ws):
    act = [r for r in ws if r["airTime"] and r["airTime"] > 0]
    if len(act) < 4: return None
    avg = sum(r["avgLiveViews"] for r in act)/len(act)
    peak = max(r["maxLiveViews"] for r in act)
    air = sum(r["airTime"] for r in act)/len(act)
    f0, f1 = ws[0]["maxFollowerCount"], ws[-1]["maxFollowerCount"]
    gain = (f1 or 0) - (f0 or 0)
    airsum = sum(r["airTime"] for r in act)
    eff = gain/airsum if airsum > 0 else None
    return {"avg":avg, "peak":peak, "air":air, "gain":gain, "eff":eff, "n_act":len(act)}

tw = window(w)
tm = metrics(tw)
print(f"\n[롤캐 최근 8주(마지막 불완전주 제외) {tw[0]['date']}~{tw[-1]['date']}]")
print(f"  평청 {tm['avg']:.1f} 피크 {tm['peak']} 주당방송 {tm['air']:.1f}h 팔로워증가 {tm['gain']} 효율 {tm['eff']:.2f}/h 활동주 {tm['n_act']}/8")

# 모수: 같은 창에서 활동한 채널
def pct(vals, x, reverse=False):
    vals = sorted(vals)
    below = sum(1 for v in vals if v < x)
    return below/len(vals)*100

pools = {"growth_seg": [], "band": []}
for c in channels:
    if c["channel_id"] == CID: continue
    m = metrics(window(c["weeks"]))
    if not m: continue
    fc = c.get("follower_count") or 0
    if c["segment"] == "growth":
        pools["growth_seg"].append((m, fc))
    if 0 < fc <= 2495:  # 995 +- 1500
        pools["band"].append((m, fc))

for name, pool in pools.items():
    ms = [m for m,_ in pool]
    print(f"\n[{name}] n={len(ms)}")
    for k, lbl in [("avg","평청"),("peak","피크"),("air","주당방송"),("gain","8주 팔로워증가")]:
        vals=[m[k] for m in ms]
        p=pct(vals, tm[k])
        med=sorted(vals)[len(vals)//2]
        print(f"  {lbl:<10} 롤캐 {tm[k]:>7.1f} | 중위 {med:>7.1f} | 상위 {100-p:>5.1f}%")
    effs=[m["eff"] for m in ms if m["eff"] is not None]
    p=pct(effs, tm["eff"])
    med=sorted(effs)[len(effs)//2]
    print(f"  {'효율(팔/h)':<9} 롤캐 {tm['eff']:>7.2f} | 중위 {med:>7.2f} | 상위 {100-p:>5.1f}%")

# 관성(모멘텀): 최근 4주 vs 직전 4주 팔로워 증가
w8 = window(w, 8)
g_recent = w8[-1]["maxFollowerCount"] - w8[3]["maxFollowerCount"]
g_prior  = w8[3]["maxFollowerCount"] - w8[0]["maxFollowerCount"]
print(f"\n[관성] 직전4주 +{g_prior} -> 최근4주 +{g_recent}")

# 52주 궤적
print(f"\n[52주 궤적] {w[0]['date']} {w[0]['maxFollowerCount']} -> {w[-2]['date']} {w[-2]['maxFollowerCount']}")
half = w[26]["maxFollowerCount"]
print(f"  전반 26주 +{half - w[0]['maxFollowerCount']} / 후반 26주 +{w[-2]['maxFollowerCount'] - half}")
