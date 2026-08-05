# -*- coding: utf-8 -*-
"""콘텐츠 역설계 1차 분석: 성장군 vs 정체군의 콘텐츠 차이 (최근 45일 VOD 기준)."""
import json, re
from collections import Counter, defaultdict

rows = json.load(open("collected_20260804.json", encoding="utf-8"))
CUT = "2026-06-20"
KW = {
    "시참": r"시참|시청자\s*참여|같이\s*할|참여코드",
    "합방": r"합방|콜라보|colab|w\.|위드|같이\s*(하는|보는)?\s*(방송)?\s*with|(\bft\.)",
    "기념": r"기념|축하|돌파|주년|백일|팔로우\s*\d|\d+\s*(팔|팔로)",
    "이벤트": r"이벤트|대회|챌린지|미션|내기|벌칙",
    "노래": r"노래|싱어|sing|콘서트|음방|노방",
    "저챗": r"저챗|저스트|잡담|토크|수다|소통",
    "신작첫": r"신작|첫\s|처음|1일차|1화",
}
def feat(videos):
    vs = [v for v in videos if (v.get("d") or "") >= CUT]
    if not vs: return None
    cats = Counter(v.get("cat") or "미분류" for v in vs)
    top_cat, top_n = cats.most_common(1)[0]
    kws = {k: sum(1 for v in vs if re.search(p, (v.get("t") or ""), re.I)) for k, p in KW.items()}
    talk_cats = sum(n for c, n in cats.items() if c and re.search(r"talk|저스트|Just|토크|잡담", c, re.I))
    return {"n": len(vs), "n_cats": len(cats), "top_share": top_n/len(vs), "talk_share": talk_cats/len(vs),
            "kw": kws, "cats": cats}

groups = defaultdict(list)
for r in rows:
    if "videos" not in r or r.get("f_census") is None or not r.get("f_now"): continue
    f = feat(r["videos"])
    if f is None: continue
    growth4 = (r["f_now"] - r["f_census"]) / max(1, r["f_census"])
    groups[r["group"]].append({**f, "name": r.get("name"), "g4": growth4, "f": r["f_now"]})

def agg(arr, key):
    vals = [a[key] for a in arr]; vals.sort()
    return vals[len(vals)//2]
def kwshare(arr, k):
    return sum(1 for a in arr if a["kw"][k] > 0) / len(arr) * 100

print(f"{'군':<8}{'n':>4}{'4주성장중위':>10}{'VOD수':>6}{'카테고리수':>7}{'집중도':>7}{'저챗비중':>8}")
for g in ["grow", "mid", "flat", "unni", "subject"]:
    arr = groups.get(g, [])
    if not arr: continue
    print(f"{g:<8}{len(arr):>4}{agg(arr,'g4')*100:>9.1f}%{agg(arr,'n'):>6}{agg(arr,'n_cats'):>7}{agg(arr,'top_share')*100:>6.0f}%{agg(arr,'talk_share')*100:>7.0f}%")

print("\n[제목 키워드 보유 채널 비율 %]")
print(f"{'키워드':<8}" + "".join(f"{g:>8}" for g in ["grow","mid","flat"]))
for k in KW:
    print(f"{k:<8}" + "".join(f"{kwshare(groups[g],k):>7.0f}%" for g in ["grow","mid","flat"]))

# 실제 4주 성장 재분류 (census 8주와 다를 수 있음): API 실측 기준 상위/하위
allc = [a for g in ["grow","mid","flat"] for a in groups[g]]
allc.sort(key=lambda a: -a["g4"])
top = allc[:30]; bot = [a for a in allc if a["g4"] <= 0.005][:30] or allc[-30:]
print(f"\n[API 실측 4주 성장 재분류] top30 중위 {agg(top,'g4')*100:.1f}% / bot30 중위 {agg(bot,'g4')*100:.1f}%")
print(f"{'키워드':<8}{'top30':>8}{'bot30':>8}")
for k in KW:
    print(f"{k:<8}{kwshare(top,k):>7.0f}%{kwshare(bot,k):>7.0f}%")
print(f"{'저챗비중':<8}{agg(top,'talk_share')*100:>7.0f}%{agg(bot,'talk_share')*100:>7.0f}%")
print(f"{'카테고리수':<7}{agg(top,'n_cats'):>8}{agg(bot,'n_cats'):>8}")
print(f"{'VOD수':<8}{agg(top,'n'):>8}{agg(bot,'n'):>8}")

print("\n[성장 top10 채널과 주력 콘텐츠]")
for a in allc[:10]:
    c3 = ", ".join(f"{c}({n})" for c, n in a["cats"].most_common(3))
    kws = ",".join(k for k, v in a["kw"].items() if v > 0)
    print(f"  {a['name'][:14]:<15} +{a['g4']*100:>5.1f}% f={a['f']:>5} | {c3[:52]} | {kws}")
