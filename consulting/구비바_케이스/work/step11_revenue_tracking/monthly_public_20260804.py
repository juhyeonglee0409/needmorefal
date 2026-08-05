# -*- coding: utf-8 -*-
"""구비바 공개 지표 월별 비교 (소프트콘, 2026-08-04 수집).
주간 집계 행(월요일 + airTime>=12h)만 사용해 월 귀속은 주 시작일 기준."""
import json, datetime
from pathlib import Path

rows = json.load(open(Path(__file__).parent / "softc_gubiba_20260804.json", encoding="utf-8"))["rows"]
weekly = []
for r in rows:
    d = datetime.date(*[int(x) for x in r[0].split("-")])
    if d.weekday() == 0 and r[3] >= 12:  # 월요일 + 주간 집계로 판단
        weekly.append(r)
# 중복 주 제거 (같은 날짜 주간 행 하나만)
seen = set(); wk = []
for r in weekly:
    if r[0] in seen: continue
    seen.add(r[0]); wk.append(r)

from collections import defaultdict
mon = defaultdict(list)
for r in wk: mon[r[0][:7]].append(r)

print(f"{'월':<9}{'주':>3}{'주평균 방송':>10}{'평청(가중)':>9}{'피크':>5}{'주평균 시청량':>11}{'주평균 채팅':>10}{'팔로워(말)':>9}")
prev_f = None
for m in sorted(mon):
    rs = mon[m]
    air = sum(r[3] for r in rs)
    wavg = sum(r[1]*r[3] for r in rs)/air
    peak = max(r[2] for r in rs)
    vw = sum(r[6] for r in rs)/len(rs)
    ch = sum(r[5] for r in rs)/len(rs)
    f_end = rs[-1][4]
    dcol = f" (+{f_end-prev_f})" if prev_f else ""
    print(f"{m:<9}{len(rs):>3}{air/len(rs):>9.1f}h{wavg:>9.1f}{peak:>5}{vw:>11.0f}{ch:>10.0f}{f_end:>8}{dcol}")
    prev_f = f_end
