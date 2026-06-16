# §6 상위 참조 밴드 수집 — Codex 프롬프트

## 맥락

구비바 채널 진단 §6(목표 트레이드오프 정량화)에서, 본인 목표가 "1만 팔로워 + 평청 200"이다. 현 코호트(323ch)는 최대 팔로워 5,579까지만 커버하므로 목표 지점의 실측 데이터가 없다. **목표 도달 시 어떤 숫자가 현실적인지** 확인하기 위해 상위 참조 밴드를 별도 수집한다.

기존 §4 코호트(peer 비교용)와는 **분리**한다. 이건 peer가 아니라 **도착지 풍경**을 보는 참조 데이터다.

## 수집 대상

| 항목 | 기준 |
|---|---|
| 플랫폼 | 치지직 |
| 카테고리 | 종합게임 계열 + 버추얼 (기존 T1/T2와 동일 판정 기준) |
| 팔로워 범위 | **10,000 이상** (상한 없음) |
| 최소 수집량 | **20~30ch** |
| 상한 | 없음. 가능한 한 많이 수집 |
| 제외 | e스포츠팀·대회·기업 운영 계정, 휴면, 신생 2개월 미만 |

구간별 최소 분배 (가이드, 강제 아님):
- 10k-20k: 최소 8ch
- 20k-50k: 최소 5ch  
- 50k+: 있는 만큼 전부

종합게임과 버추얼이 자연스럽게 섞여도 무방. `is_general_game`, `is_virtual` 플래그로 구분만 하면 된다.

## 필요 컬럼

채널당 1행, 채널 레벨 집계. 기존 코호트와 동일 구조:

```csv
channel_name,channelId,channel_url,follower,categories,is_general_game,is_virtual,peak_max,peak_p95,peak_median,peak_recent_median,avg_median,avg_recent_median,stream_hours,ts_weeks,band
```

| 컬럼 | 정의 |
|---|---|
| channel_name | 채널명 |
| channelId | 치지직 채널 ID |
| channel_url | 채널 URL |
| follower | 현재 팔로워 수 |
| categories | 주요 방송 카테고리 (쉼표 구분) |
| is_general_game | 종합게임 판정 (true/false) |
| is_virtual | 버추얼 판정 (true/false) |
| peak_max | 전체 방송 중 최고 시청자 최대값 |
| peak_p95 | 전체 방송의 최고 시청자 p95 |
| peak_median | 전체 방송의 최고 시청자 중앙값 |
| peak_recent_median | 최근 8주 방송의 최고 시청자 중앙값 |
| avg_median | 전체 방송의 평균 시청자 중앙값 |
| avg_recent_median | 최근 8주 방송의 평균 시청자 중앙값 |
| stream_hours | 총 방송 시간 (h) |
| ts_weeks | 관측 기간 (주) |
| band | 팔로워 구간 라벨 (10k-20k / 20k-50k / 50k+) |

값이 없으면 빈칸이 아니라 빈 문자열 + 별도 노트. 수집 불가 사유가 있으면 기록.

## 저장

```
data/cohort/collected/cohort_ref_upper_band.csv
```

## 수집 시 주의

1. **polite하게.** 간격을 두고, 과부하 없이, 차단 시 후퇴.
2. 대형 채널은 콜라보·대회·레이드로 peak이 크게 튀는 경우가 많다. peak_median과 peak_max 괴리가 클 수 있는데, 이건 의도된 것이다 — 둘 다 수집.
3. 버추얼 대형은 사무소(기업) 소속이 많다. 기업 운영 계정은 제외하되, **사무소 소속 개인 채널은 포함**. `is_virtual` 플래그로 구분.
4. 방송 기록 수집이 어려운 채널(비공개 등)은 스킵하고 사유 기록.

## 핵심 질문 (이 데이터로 답할 것)

- avg_median 200은 어느 팔로워 구간에서 달성 가능한가?
- 10k 팔로워에서 avg_median의 실제 분포는?
- 체급 상승 비용(eff = peak/follower)은 10k+ 구간에서도 같은 패턴으로 하락하는가?
