# -*- coding: utf-8 -*-
"""백설호 데이터 카드 생성 (카드 v2 템플릿·규약 재사용, 단일 채널).

card_generator.py(v2)의 템플릿·티어·문구 규칙을 그대로 따르되,
인바운드 P0 케이스라 발송 큐는 만들지 않는다.
지표 기준: 2026-06-29 완결 주 (7/4 census 비교군과 시간 정렬). 각주에 명시.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
a = json.loads((BASE / "baekseolho_analysis_20260721.json").read_text(encoding="utf-8"))
ps = a["peer_card_stats"]
name = "백설호"
f, avg, hours = ps["subject"]["followers"], ps["subject"]["avg"], ps["subject"]["hours"]
eff, med_avg, med_eff, med_h = ps["subject"]["eff1k"], ps["med_avg"], ps["med_eff"], ps["med_h"]
n, ppct = ps["n"], ps["eff_top_pct"]
eff_ratio = eff / med_eff

# 티어 판정 (generator 규칙): ppct 37.2 → mid
tier = "strong" if ppct <= 30 else ("mid" if ppct <= 50 or ps["census_top_pct"] <= 30 else "soft")

hero_html = (
    f'    <div class="hv"><div class="k">팔로워 대비 시청자 효율</div><div class="v">상위 {ppct:.0f}%</div>'
    f'<div class="d">비슷한 규모 버튜버 {n:,}개 중 {ps["eff_rank"]:,}위</div></div>\n'
    f'    <div class="hv b"><div class="k">다음 이정표 — 팔로워 1,500</div><div class="v">{1500-f:,}명</div>'
    f'<div class="d">{f:,} / 1,500 · 첫 체급 구간</div></div>')

insight = (f"팔로워 {f:,}명에 평균 {avg}명 시청 — 팔로워 대비 시청 전환(효율)은 동급 중앙값의 <b>{eff_ratio:.1f}배</b>로 "
           f"안정적인 편이에요. 초기 3개월 채널에서 이 효율이 유지되는 건 좋은 신호입니다. "
           f"지금은 효율을 지키면서 <b>팔로워 기반을 넓히는 것</b>이 다음 과제로 보입니다.")

sig = a["signal_census_aligned"]
outlook_html = ('  <h3>성장 전망 신호 <small>— 1년 주간 데이터 패턴</small></h3>\n'
                '  <div class="hl p"><b><span style="color:#94a3b8;">●</span> 안정 구간</b> · '
                '시청 효율과 최근 팔로워 흐름이 동급 중간 범위예요. 특히 <b>최근 4주 팔로워 흐름은 '
                '동급 상위 30% 안</b>에 들어 있어요 — 이 흐름에 시청 효율(팔로워→시청 전환)까지 붙으면 '
                '데이터상 가장 강한 조합이 됩니다. 이 구간에서는 지표 하나를 정해 집중적으로 움직이는 것이 '
                '다음 변화를 만드는 패턴이었습니다.</div>')
outlook_note = ("<br>※ 성장 전망 신호는 치지직 버튜버 전수 7,472채널의 1년(53주) 주간 지표에서 확인된 "
                f"패턴 통계입니다 (기준 주: {sig['week']}). 경향 안내이지 예측 보장이 아닙니다.")

pctbar = f / 1500 * 100
ms_title = "다음 이정표 — 팔로워 1,500"
ms_body = (f'<div class="bar"><div style="width:{pctbar:.1f}%"></div></div>'
           f'<div style="font-size:11px;color:#64748b;">{f:,} / 1,500 · <b>{1500-f:,}명 남음</b></div>'
           f'<div class="hl p">현재 분포 기준, 팔로워 1,500 이상인 동급 채널의 <b>83%</b>가 "평균 시청자 14명 이상"을 '
           f'유지하고 있어요 (1,500 미만에서는 28%). 다만 이 숫자는 구간의 풍경이지 넘는 순간 저절로 바뀐다는 뜻은 '
           f'아니에요 — 실제로 먼저 움직이는 건 위의 <b>성장 전망 신호</b> 쪽 지표들입니다.</div>')

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
    <div class="sub">치지직 VTuber · 최근 완결 주(2026-06-29 주간) 공개 방송 지표 기준</div>
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
    ※ 출처: 공개 방송 지표 (공개 뷰어십 통계 사이트 + 치지직 공개 채널 정보), 2026.07.21 수집 · 본인 지표는 2026-06-29 완결 주, 비교군은 2026.07.04 수집 기준.<br>
    ※ 동급 = 팔로워 ±1,500 범위의 치지직 버튜버. 공개 지표 기반이라 채널 내부 데이터(시청 지속시간·유입 경로 등)는 반영되지 않았습니다.{outlook_note}
  </div>
  <div class="foot">
    <span>만든 사람: 이삭컨설팅 (스트리머 데이터 분석)</span>
    <span>정밀 진단(비교군 설계·병목 분석): 크몽 "이삭컨설팅" 검색</span>
  </div>
</div></body></html>
"""

html = CARD_TMPL.format(
    name=name, hero_html=hero_html,
    avg=avg, med_avg=med_avg, avg_ratio=f"{avg/med_avg:.1f}배",
    eff=eff, med_eff=med_eff, eff_ratio_s=f"{eff_ratio:.1f}배",
    hours=hours, med_h=med_h, h_diff=f"{hours-med_h:+.1f}h",
    insight=insight, outlook_html=outlook_html, outlook_note=outlook_note,
    ms_title=ms_title, ms_body=ms_body,
)
out = BASE / "card_백설호snowfox.html"
out.write_text(html, encoding="utf-8")
print("tier:", tier, "| card:", out)
