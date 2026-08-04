# -*- coding: utf-8 -*-
"""유리아 궤적 매칭 (§6.6): 데뷔 정렬 유사 궤적 채널의 다음 분기 범위.
census는 채널별 첫 관측 주부터 저장 -> len(weeks) < 53 이면 창 내 등장 = 데뷔 정렬 가능.
유리아: census 14주 관측(3/23~7/6) 마지막 팔로워 161. 실측 7/31 246.
매칭 기준: 14주차 팔로워 80~250, 첫 14주 중 8주 이상 활동."""
import json
from pathlib import Path

SRC = Path(__file__).parent.parent.parent / "runs" / "census_full_20260708" / "census_full_weekly.ndjson"
chs = [json.loads(l) for l in open(SRC, encoding="utf-8")]

W_AT = 13   # 14주차 (유리아의 census 마지막 주와 정렬)
def build(min_len):
    out = []
    for c in chs:
        w = c["weeks"]
        if len(w) >= 51 or len(w) < min_len:  # 51+ = 창 이전 데뷔 가능성, 제외
            continue
        f14 = w[W_AT]["maxFollowerCount"] if len(w) > W_AT else None
        if not f14 or not (80 <= f14 <= 250):
            continue
        act = [r for r in w[:W_AT+1] if (r["airTime"] or 0) > 0]
        if len(act) < 8:
            continue
        avgv = [r["avgLiveViews"] for r in w[9:W_AT+1] if r["avgLiveViews"]]
        out.append({"w": w, "f14": f14, "avg": (sum(avgv)/len(avgv) if avgv else 0)})
    return out

# 4주 결과 창 (유리아 실측 +85와 비교: census 161 -> 7/31 246... 소프트콘 기준)
c4 = build(W_AT + 1 + 4)
g4 = sorted((c["w"][W_AT+4]["maxFollowerCount"] or 0) - c["f14"] for c in c4)
n4 = len(g4)
print(f"[4주 결과 창] n={n4}")
print(f"  중위 {g4[n4//2]:+.0f} | 상위 25% {g4[int(n4*.75)]:+.0f} | 상위 10% {g4[int(n4*.9)]:+.0f} | 상위 5% {g4[int(n4*.95)]:+.0f}")
yuria_4w = 246 - 161
over = sum(1 for g in g4 if g >= yuria_4w) / n4 * 100
print(f"  유리아 실측 +{yuria_4w} (161->246, 7/6~7/31) 이상: {over:.1f}% -> 상위 {over:.0f}%")

# 13주(분기) 결과 창
c13 = build(W_AT + 1 + 13)
g13 = sorted((c["w"][W_AT+13]["maxFollowerCount"] or 0) - c["f14"] for c in c13)
n13 = len(g13)
print(f"\n[13주(분기) 결과 창] n={n13}")
print(f"  하위 25% {g13[int(n13*.25)]:+.0f} | 중위 {g13[n13//2]:+.0f} | 상위 25% {g13[int(n13*.75)]:+.0f} | 상위 10% {g13[int(n13*.9)]:+.0f}")
pos = sum(1 for g in g13 if g > 0)/n13*100
print(f"  순증 비율 {pos:.0f}%")

# 유리아 페이스 유지 시 분기 환산 (+85/4주 -> 13주 약 +276) 위치
pace13 = round(yuria_4w / 4 * 13)
over13 = sum(1 for g in g13 if g >= pace13) / n13 * 100
print(f"  유리아 현 페이스 분기 환산 +{pace13} 이상: {over13:.1f}%")

# 효율 조건 추가: 유사 궤적 중 평청 5 이상(유리아 수준) 서브그룹
sub = [(c["w"][W_AT+13]["maxFollowerCount"] or 0) - c["f14"] for c in c13 if c["avg"] >= 5]
sub.sort()
if len(sub) >= 10:
    ns = len(sub)
    print(f"\n[유사 궤적 + 평청 5명 이상 (유리아 조건)] n={ns}")
    print(f"  중위 {sub[ns//2]:+.0f} | 상위 25% {sub[int(ns*.75)]:+.0f} | 상위 10% {sub[int(ns*.9)]:+.0f}")
