# -*- coding: utf-8 -*-
"""86명 채널 데이터 카드 + 발송 큐 자동 생성 (give-first 전략).

v2 (2026-07-08): 성장 전망 신호(§6.3.2, 백테스트 지지) 추가,
1,500 변곡점 단정 문구를 분포 서술로 교체 (§8.6.4 기각 반영).
scratchpad에서 repo로 이식.

입력: send_list_20260704.ndjson(86), census_pool.ndjson(대조 풀),
      growth_outlook_20260708.json(성장 전망 신호)
출력: cards_20260704/{safe}.html, send_queue_20260704.md/.ndjson
"""
import json
import re
import statistics
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "cards_20260704"
OUT.mkdir(exist_ok=True)
CENSUS_TOTAL = 7203
TYPO_DOMAINS = {"gmai.com", "gamil.com"}

# --- 데이터 로드 ---
pool = {}
for l in (BASE / "census_pool.ndjson").open(encoding="utf-8"):
    r = json.loads(l)
    pool[r["channel_id"]] = r
pool = [r for r in pool.values()
        if (r.get("follower_count") or 0) > 0
        and (r.get("metrics", {}).get("softcon") or {}).get("avg") is not None]
for r in pool:
    r["eff"] = r["metrics"]["softcon"]["avg"] / (r["follower_count"] / 1000)

send = [json.loads(l) for l in (BASE / "send_list_20260704.ndjson").open(encoding="utf-8")]
outlook = json.loads((BASE / "growth_outlook_20260708.json").read_text(encoding="utf-8"))

def peer_stats(f, eff):
    peers = [r for r in pool if abs(r["follower_count"] - f) <= 1500]
    n = len(peers)
    rank = sum(1 for r in peers if r["eff"] >= eff)
    med_avg = statistics.median(r["metrics"]["softcon"]["avg"] for r in peers)
    med_eff = statistics.median(r["eff"] for r in peers)
    med_h = statistics.median(r["metrics"]["softcon"]["hours"] for r in peers)
    return n, rank, rank / n * 100, med_avg, med_eff, med_h

def safe_name(name):
    s = re.sub(r"[^\w가-힣]+", "_", name).strip("_")
    return s or "channel"

# --- 성장 전망 신호 블록 (§6.3.2, 1년 주간 데이터 패턴 통계) ---
OUTLOOK_BLOCKS = {
    "green": ('<span style="color:#059669;">●</span> 성장 구간',
              "시청 효율과 최근 4주 팔로워 흐름이 <b>둘 다 동급 상위권</b>이에요. 지난 1년 치지직 버튜버 "
              "데이터에서 이 조합의 채널은 10곳 중 9곳이 규모 대비 초과 성장으로 이어졌습니다. "
              "지금은 새 시도보다 <b>이 흐름을 지키는 것</b>이 최우선이에요."),
    "near": ('<span style="color:#2563eb;">●</span> 상승 흐름',
             "최근 4주 팔로워 흐름이 동급 상위권이에요. 지난 1년 데이터에서 이 흐름의 채널은 대부분 "
             "초과 성장으로 이어졌습니다. 여기에 시청 효율(팔로워→시청 전환)까지 붙으면 "
             "데이터상 가장 강한 조합이 돼요."),
    "neutral": ('<span style="color:#94a3b8;">●</span> 안정 구간',
                "시청 효율과 최근 팔로워 흐름이 동급 중간 범위예요. 이 구간에서는 지표 하나를 정해 "
                "집중적으로 움직이는 것이 다음 변화를 만드는 패턴이었습니다."),
    "red": ('<span style="color:#ea580c;">●</span> 전환 대기 구간',
            "시청 효율과 최근 팔로워 흐름이 함께 쉬고 있는 구간이에요. 1년 데이터에서 이 조합은 "
            "저절로 풀리기보다 <b>편성·복귀 동선 같은 구조를 바꿀 때</b> 움직이는 패턴이었습니다. "
            "바꿀 레버가 분명하다는 뜻이기도 해요."),
}

CARD_TMPL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>{name} 채널 데이터 카드</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Malgun Gothic','Apple SD Gothic Neo',-apple-system,sans-serif;
    color:#1e293b; background:#f1f5f9; font-size:12.5px; line-height:1.55; padding:14px; }}
  .card {{ max-width:640px; margin:0 auto; background:white; border-radius:14px;
    padding:24px 32px; box-shadow:0 4px 24px rgba(15,23,42,0.08); }}
  .top {{ border-top:5px solid; border-image:linear-gradient(90deg,#7c3aed,#3b82f6,#06b6d4) 1;
    margin:-24px -32px 16px; padding:18px 32px 0; }}
  .label {{ font-size:10px; color:#64748b; letter-spacing:3px; text-transform:uppercase; }}
  h1 {{ font-size:22px; font-weight:800; margin:6px 0 2px; }}
  .sub {{ font-size:11.5px; color:#94a3b8; }}
  .hero {{ display:flex; gap:10px; margin:12px 0 4px; }}
  .hv {{ flex:1; padding:11px 10px; border-radius:10px; text-align:center; background:#faf5ff; border:1px solid #e9d5ff; }}
  .hv.b {{ background:#eff6ff; border-color:#bfdbfe; }}
  .hv .k {{ font-size:10px; color:#7c3aed; font-weight:700; }}
  .hv.b .k {{ color:#2563eb; }}
  .hv .v {{ font-size:24px; font-weight:800; margin-top:2px; }}
  .hv .d {{ font-size:9.5px; color:#94a3b8; margin-top:2px; }}
  h3 {{ font-size:13.5px; font-weight:800; margin:14px 0 6px; }}
  h3 small {{ font-size:9.5px; color:#94a3b8; font-weight:400; }}
  table {{ width:100%; border-collapse:collapse; font-size:12px; }}
  th,td {{ padding:6px 10px; border-bottom:1px solid #f1f5f9; text-align:left; }}
  th {{ background:#f8fafc; font-size:10.5px; color:#475569; }}
  td.n,th.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .me {{ color:#7c3aed; font-weight:800; }}
  .hl {{ border-left:3px solid #06b6d4; background:#ecfeff; padding:8px 12px;
    border-radius:0 6px 6px 0; margin:8px 0; font-size:12px; }}
  .hl.p {{ border-color:#7c3aed; background:#faf5ff; }}
  .hl.g {{ border-color:#059669; background:#f0fdf4; }}
  .bar {{ height:10px; background:#e2e8f0; border-radius:5px; overflow:hidden; margin:6px 0 4px; }}
  .bar > div {{ height:100%; background:linear-gradient(90deg,#7c3aed,#3b82f6); border-radius:5px; }}
  .note {{ margin-top:12px; font-size:9px; color:#94a3b8; line-height:1.5; }}
  .foot {{ margin-top:10px; padding-top:8px; border-top:1px solid #e2e8f0;
    font-size:10.5px; color:#64748b; display:flex; justify-content:space-between; }}
</style></head><body>
<div class="card">
  <div class="top">
    <div class="label">Channel Data Card · 2026.07</div>
    <h1>{name}</h1>
    <div class="sub">치지직 VTuber · 최근 7일 공개 방송 지표 기준</div>
  </div>
  <div class="hero">
{hero_html}
  </div>
  <h3>동급 버튜버 중앙값과 비교</h3>
  <table>
    <tr><th>지표</th><th class="n">{name}</th><th class="n">동급 중앙값</th><th class="n">차이</th></tr>
    <tr><td>평균 시청자</td><td class="n me">{avg}명</td><td class="n">{med_avg:.0f}명</td><td class="n me">{avg_ratio}</td></tr>
    <tr><td>1천 팔로워당 시청자</td><td class="n me">{eff:.1f}명</td><td class="n">{med_eff:.1f}명</td><td class="n me">{eff_ratio_s}</td></tr>
    <tr><td>주간 방송시간</td><td class="n me">{hours}h</td><td class="n">{med_h:.1f}h</td><td class="n">{h_diff}</td></tr>
  </table>
  <div class="hl">{insight}</div>
{outlook_html}
  <h3>{ms_title}</h3>
  {ms_body}
  <div class="note">
    ※ 출처: 공개 방송 지표 (공개 뷰어십 통계 사이트 + 치지직 공개 채널 정보), 2026.07.04 수집 · 최근 7일 기준.<br>
    ※ 동급 = 팔로워 ±1,500 범위의 치지직 버튜버. 공개 지표 기반이라 채널 내부 데이터(시청 지속시간·유입 경로 등)는 반영되지 않았습니다.{outlook_note}
  </div>
  <div class="foot">
    <span>만든 사람: 이삭컨설팅 (스트리머 데이터 분석)</span>
    <span>정밀 진단(비교군 설계·병목 분석): 크몽 "이삭컨설팅" 검색</span>
  </div>
</div></body></html>
"""

queue_md = ["# 발송 큐 — 채널 데이터 카드 증정 (2026-07-04, 카드 v2 2026-07-08)\n",
            "- 전략: give-first. 답장 요구 없음. [실명]·[연락처]는 발송 전 채움.\n",
            "- 카드 PDF: `cards_20260704/{안전이름}.pdf`\n"]
queue_nd = []
tiers = {"strong": 0, "mid": 0, "soft": 0}

for r in sorted(send, key=lambda x: x["channel_name"]):
    name = r["channel_name"]
    f = r["follower_count"]
    sc = r["metrics"]["softcon"]
    avg, hours, rank = sc["avg"], sc["hours"], sc["rank"]
    eff = avg / (f / 1000)
    n, prank, ppct, med_avg, med_eff, med_h = peer_stats(f, eff)
    cen_pct = rank / CENSUS_TOTAL * 100
    eff_ratio = eff / med_eff if med_eff else 0

    # --- 티어 ---
    if ppct <= 30:
        tier = "strong"
    elif ppct <= 50 or cen_pct <= 30:
        tier = "mid"
    else:
        tier = "soft"
    tiers[tier] += 1

    # --- 히어로 (2026-07-04 operator 확정: soft는 윤비나형 사실형, strong/mid 현행) ---
    if tier in ("strong", "mid"):
        hero_html = (
            f'    <div class="hv"><div class="k">팔로워 대비 시청자 효율</div><div class="v">상위 {ppct:.0f}%</div>'
            f'<div class="d">비슷한 규모 버튜버 {n:,}개 중 {prank:,}위</div></div>\n'
            f'    <div class="hv b"><div class="k">치지직 버튜버 전체 뷰어십</div><div class="v">상위 {cen_pct:.0f}%</div>'
            f'<div class="d">7,203개 채널 중 {rank:,}위</div></div>')
    else:
        hero1 = (f'    <div class="hv b"><div class="k">이 카드의 비교군</div><div class="v">{n:,}개</div>'
                 f'<div class="d">비슷한 규모(±1,500) 치지직 버튜버 전수</div></div>')
        avg_ratio_v = avg / med_avg if med_avg else 0
        # 폴백 체인: 평청 우위 → 다음 이정표 → 전체 뷰어십(≤50%) → 방송시간
        if avg_ratio_v >= 1.0:
            hero2 = (f'    <div class="hv"><div class="k">평균 시청자</div><div class="v">{avg}명</div>'
                     f'<div class="d">동급 중앙값({med_avg:.0f}명)의 {avg_ratio_v:.1f}배</div></div>')
        elif f < 1500:
            hero2 = (f'    <div class="hv"><div class="k">다음 이정표 — 팔로워 1,500</div><div class="v">{1500-f:,}명</div>'
                     f'<div class="d">{f:,} / 1,500 · 1,500+ 채널의 83%가 평청 14명 이상 (현재 분포)</div></div>')
        elif cen_pct <= 50:
            hero2 = (f'    <div class="hv"><div class="k">치지직 버튜버 전체 뷰어십</div><div class="v">상위 {cen_pct:.0f}%</div>'
                     f'<div class="d">7,203개 채널 중 {rank:,}위</div></div>')
        else:
            hero2 = (f'    <div class="hv"><div class="k">주간 방송시간</div><div class="v">{hours}h</div>'
                     f'<div class="d">최근 7일 · 동급 중앙값 {med_h:.1f}h</div></div>')
        hero_html = hero1 + "\n" + hero2

    # --- 인사이트 문구 ---
    if tier == "strong":
        insight = (f"팔로워 {f:,}명 규모에서 평균 {avg}명이 봅니다. 이 비율(효율)은 동급의 <b>{eff_ratio:.1f}배</b>로, "
                   f"팔로워가 실제 시청으로 잘 이어지는 <b>드문 체질</b>이에요. 지금 팔로워 수는 콘텐츠 대비 저평가 상태에 가깝습니다.")
    elif tier == "mid":
        insight = (f"팔로워 {f:,}명에 평균 {avg}명 시청 — 동급 흐름과 비교해 안정적인 편이에요. "
                   f"효율(동급의 {eff_ratio:.1f}배)을 유지하면서 팔로워 기반을 넓히는 게 다음 과제로 보입니다.")
    else:
        insight = (f"팔로워 {f:,}명 대비 평균 시청 {avg}명 — 팔로워를 시청으로 전환하는 고리에 여지가 보여요. "
                   f"이건 약점이라기보다 <b>가장 빨리 움직일 수 있는 레버</b>입니다. 편성·복귀 동선 쪽 요인이 큰 경우가 많아요.")

    # --- 성장 전망 신호 (v2 신설, §6.3.2) ---
    ol = outlook.get(r["channel_id"], {})
    if ol.get("signal") in OUTLOOK_BLOCKS:
        badge, text = OUTLOOK_BLOCKS[ol["signal"]]
        cls = "g" if ol["signal"] in ("green", "near") else "p"
        outlook_html = (f'  <h3>성장 전망 신호 <small>— 1년 주간 데이터 패턴</small></h3>\n'
                        f'  <div class="hl {cls}"><b>{badge}</b> · {text}</div>')
        outlook_note = ("<br>※ 성장 전망 신호는 치지직 버튜버 전수 7,472채널의 1년(53주) 주간 지표에서 확인된 "
                        f"패턴 통계입니다 (기준 주: {ol['week']}). 경향 안내이지 예측 보장이 아닙니다.")
        outlook_signal = ol["signal"]
    else:
        outlook_html = ""
        outlook_note = ""
        outlook_signal = None

    # --- 마일스톤 (v2: 분포 서술로 교체 — 임계 통과가 변화를 만든다는 단정 제거) ---
    if f < 1500:
        pctbar = f / 1500 * 100
        ms_title = "다음 이정표 — 팔로워 1,500"
        ms_body = (f'<div class="bar"><div style="width:{pctbar:.1f}%"></div></div>'
                   f'<div style="font-size:11px;color:#64748b;">{f:,} / 1,500 · <b>{1500-f:,}명 남음</b></div>'
                   f'<div class="hl p">현재 분포 기준, 팔로워 1,500 이상인 동급 채널의 <b>83%</b>가 "평균 시청자 14명 이상"을 '
                   f'유지하고 있어요 (1,500 미만에서는 28%). 다만 이 숫자는 구간의 풍경이지 넘는 순간 저절로 바뀐다는 뜻은 '
                   f'아니에요 — 실제로 먼저 움직이는 건 위의 <b>성장 전망 신호</b> 쪽 지표들입니다.</div>')
    elif f < 2500:
        pctbar = f / 2500 * 100
        ms_title = "현재 구간 — 1,500~2,500 밴드"
        ms_body = (f'<div class="bar"><div style="width:{pctbar:.1f}%"></div></div>'
                   f'<div style="font-size:11px;color:#64748b;">{f:,} / 2,500</div>'
                   f'<div class="hl p">현재 분포 기준, 이 밴드 채널의 <b>83%</b>가 "평균 시청자 14명 이상"을 유지하고 있어요. '
                   f'여기서는 팔로워 숫자보다 <b>일상 방송의 시청 바닥을 올리는 것</b>이 다음 체급의 열쇠예요.</div>')
    else:
        ms_title = "현재 구간 — 1,500 밴드 위"
        ms_body = ('<div class="hl p">코호트에서 팔로워가 한 구간 오를 때마다 효율은 평균 ~40%씩 자연 감소합니다. '
                   '이 체급부터는 "팔로워 늘리기"보다 <b>효율(팔로워→시청 전환)을 지키면서 크는 것</b>이 과제예요. '
                   '지금 효율을 기준점으로 잡아두면 성장의 질을 매달 점검할 수 있습니다.</div>')

    html = CARD_TMPL.format(
        name=name, hero_html=hero_html,
        avg=avg, med_avg=med_avg, avg_ratio=(f"{avg/med_avg:.1f}배" if med_avg else "-"),
        eff=eff, med_eff=med_eff, eff_ratio_s=f"{eff_ratio:.1f}배",
        hours=hours, med_h=med_h, h_diff=f"{hours-med_h:+.1f}h",
        insight=insight, outlook_html=outlook_html, outlook_note=outlook_note,
        ms_title=ms_title, ms_body=ms_body,
    )
    sn = safe_name(name)
    (OUT / f"{sn}.html").write_text(html, encoding="utf-8")

    # --- 메일 문안 (2026-07-04 operator 확정 문안 유지) ---
    email = r["email"]["value"]
    hold = email.split("@")[1] in TYPO_DOMAINS
    if tier == "strong":
        summary = (f"요약하면: 팔로워 대비 시청자 비율이 비슷한 규모 버튜버 {n:,}개 중 상위 {ppct:.0f}%예요. "
                   f"동급 중앙값의 {eff_ratio:.1f}배라, 팔로워가 실제 시청으로 잘 이어지는 드문 체질이에요.")
    elif tier == "mid":
        summary = (f"요약하면: 동급 버튜버 {n:,}개 사이에서 안정적인 위치에 있고, "
                   f"카드에 동급 중앙값과 비교한 지표랑 다음 이정표까지 담아뒀어요.")
    else:
        summary = ("요약하면: 동급 버튜버들 중앙값과 비교한 내 위치, 그리고 지금 가장 빨리 움직일 수 있는 "
                   "지표 하나를 카드에 담아뒀어요.")
    subject = f"{name}님 채널 데이터 카드 만들었어요 (그냥 드리는 거예요)"
    body = (f"{name}님 안녕하세요! 치지직 버튜버 채널들 데이터를 정리하는 프로젝트를 하고 있는데요, "
            f"하다 보니 {name}님 채널 카드도 나와서 보내드려요.\n\n{summary} 자세한 건 첨부 카드에 있어요.\n\n"
            "공개 방송 지표 기준이라 한계는 있지만, 내 채널이 동급 사이에서 어디쯤인지 보는 데는 쓸만할 거예요. "
            "답장 안 하셔도 되고, 그냥 쓰시면 됩니다. 방송에 도움 되면 좋겠어요!\n\n"
            "이삭컨설팅 [실명] · [연락처]")
    queue_nd.append({"channel_id": r["channel_id"], "channel_name": name, "email": email,
                     "tier": tier, "growth_outlook": outlook_signal, "hold": hold,
                     "card": f"cards_20260704/{sn}.pdf", "subject": subject, "body": body})
    hold_s = " ⚠️발송보류(이메일 오타 의심)" if hold else ""
    ol_s = f" · 전망={outlook_signal}" if outlook_signal else ""
    queue_md.append(f"\n---\n\n## {name} 〈{email}〉{hold_s}\n"
                    f"팔로워 {f:,} · 평청 {avg} · 동급효율 상위 {ppct:.0f}% · tier={tier}{ol_s}\n\n"
                    f"**제목:** {subject}\n\n{body}\n\n〔첨부: {sn}.pdf〕\n")

(BASE / "send_queue_20260704.md").write_text("".join(queue_md), encoding="utf-8")
with (BASE / "send_queue_20260704.ndjson").open("w", encoding="utf-8") as fh:
    for q in queue_nd:
        fh.write(json.dumps(q, ensure_ascii=False) + "\n")

print(f"카드 HTML {len(queue_nd)}개 생성 → {OUT}")
print(f"티어 분포: {tiers} | 발송보류(오타): {sum(1 for q in queue_nd if q['hold'])}")
ol_counts = {}
for q in queue_nd:
    ol_counts[q["growth_outlook"]] = ol_counts.get(q["growth_outlook"], 0) + 1
print(f"성장 전망 분포: {ol_counts}")
