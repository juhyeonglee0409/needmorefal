# -*- coding: utf-8 -*-
"""콘텐츠 역설계 수집: 구비바 체급 밴드에서 성장 3군 샘플 + 치지직 API 수집.
군: grow(최근 8주 성장 상위 60) / mid(중위 30) / flat(하위 30) + 언니채널·궤적 매칭 28개 강제 포함."""
import json, time, urllib.request, random
from pathlib import Path

CENSUS = Path("../../../runs/census_full_20260708/census_full_weekly.ndjson")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126"}

def api(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

# 1) 센서스 밴드 선정
chs = [json.loads(l) for l in open(CENSUS, encoding="utf-8")]
band = []
for c in chs:
    w = c["weeks"]
    if len(w) < 10: continue
    f_now = w[-1]["maxFollowerCount"] or 0
    if not (400 <= f_now <= 1500): continue
    act8 = [r for r in w[-9:-1] if (r["airTime"] or 0) > 0]
    if len(act8) < 5: continue
    f8 = w[-9]["maxFollowerCount"] or 0
    if f8 <= 0: continue
    band.append({"id": c["channel_id"], "f_census": f_now, "gain8": f_now - f8, "rate8": (f_now - f8) / f8})
band.sort(key=lambda x: -x["rate8"])
n = len(band)
print(f"밴드(팔로워 400~1500, 8주 5주+ 활동): {n}")
grow = band[:60]
mid = band[n//2 - 15 : n//2 + 15]
flat = [b for b in band if b["gain8"] <= 1][:30] or band[-30:]
forced = json.load(open("../unni_channel/targets_unni_trajectory.json", encoding="utf-8"))["targets"]
forced_ids = [t["channelId"] for t in forced if t.get("group") != "subject"]
sel = {}
for grp, arr in [("grow", grow), ("mid", mid), ("flat", flat)]:
    for b in arr: sel.setdefault(b["id"], {**b, "group": grp})
for fid in forced_ids:
    if fid in sel: sel[fid]["forced"] = True
    else:
        base = next((b for b in band if b["id"] == fid), None)
        sel[fid] = {**(base or {"id": fid, "f_census": None, "gain8": None, "rate8": None}), "group": "unni", "forced": True}
sel["269edc95873a1ec9fc534851c0783d1f"] = {"id": "269edc95873a1ec9fc534851c0783d1f", "group": "subject", "f_census": 745, "gain8": None, "rate8": None}
print(f"수집 대상: {len(sel)}")

# 2) API 수집
out = []
ids = list(sel.keys())
for i, cid in enumerate(ids):
    row = dict(sel[cid])
    try:
        ch = api(f"https://api.chzzk.naver.com/service/v1/channels/{cid}")["content"]
        row["name"] = ch.get("channelName")
        row["f_now"] = ch.get("followerCount")
        time.sleep(0.15)
        vd = api(f"https://api.chzzk.naver.com/service/v1/channels/{cid}/videos?size=50&sortType=LATEST")["content"]["data"]
        row["videos"] = [{"t": v.get("videoTitle"), "d": str(v.get("publishDate"))[:10],
                         "cat": v.get("videoCategoryValue"), "dur": v.get("duration"),
                         "pv": v.get("livePv"), "tags": v.get("tags")} for v in vd]
    except Exception as e:
        row["error"] = str(e)[:60]
    out.append(row)
    if (i+1) % 20 == 0: print(f"  {i+1}/{len(ids)}")
    time.sleep(0.15)

json.dump(out, open("collected_20260804.json", "w", encoding="utf-8"), ensure_ascii=False)
ok = [r for r in out if "videos" in r]
print(f"완료: {len(out)} 중 성공 {len(ok)}, VOD 보유 {sum(1 for r in ok if r['videos'])}")
