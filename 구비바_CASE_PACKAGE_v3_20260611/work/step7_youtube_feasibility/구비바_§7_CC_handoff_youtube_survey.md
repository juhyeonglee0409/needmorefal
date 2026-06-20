# §7 Codex Handoff — 유튜브 병행 현황 조사

**날짜:** 2026-06-19
**발신:** Cowork/Hosea
**수신:** Codex (CC)
**목적:** 상위밴드 271채널의 유튜브 병행 여부 조사 + 활성 채널 기본 지표 수집

---

## 배경

구비바 1부 보고서(v3)에서 리텐션(27%, 하위 25%)이 성장 병목으로 식별됨. 2부 §7에서 "유튜브를 (재)시작해야 하는가"를 데이터 기반으로 답하려 함. 이를 위해 상위밴드 채널(팔로워 10k+)의 유튜브 병행 현황을 먼저 파악해야 함.

구비바 본인은 유튜브 채널이 있으나 비활성(방치) 상태.

---

## 입력 데이터

- **타겟 채널 목록:** `data/cohort/collected/cohort_ref_upper_band.csv` — 271행
  - 컬럼: channel_name, channelId, channel_url, follower, categories, is_general_game, is_virtual, peak_max, peak_p95, peak_median, avg_median, stream_hours, ts_weeks, band
  - band: 10k-20k(88), 20k-50k(94), 50k+(89)
- **구비바 치지직 ID:** `269edc95873a1ec9fc534851c0783d1f` (참고용, 타겟에 미포함)

---

## 수집 요청

### Task 1: 유튜브 존재 여부 확인 (271채널)

각 채널에 대해 유튜브 채널 존재 여부를 확인. 방법 우선순위:

1. **치지직 채널 페이지 소셜 링크** — 치지직 채널 프로필에 유튜브 링크가 있는 경우 직접 사용
2. **YouTube 검색** — 채널명(channel_name)으로 YouTube 검색, 동일인 채널 매칭

매칭 기준: 채널명 일치 또는 유사 + 콘텐츠(게임/버추얼) 일치. 동명이인 주의.

**출력 형식:** CSV — `youtube_presence_271.csv`

```
channel_name,channelId,band,has_youtube,youtube_channel_id,youtube_url,match_method,match_confidence
한동숙,75cbf189...,50k+,true,UC...,https://youtube.com/@...,chzzk_social_link,high
...
```

- `has_youtube`: true/false
- `match_method`: chzzk_social_link / youtube_search / not_found
- `match_confidence`: high / medium / low

### Task 2: 활성 채널 지표 수집 (Task 1에서 has_youtube=true인 채널)

YouTube Data API 또는 공개 페이지에서:

```
youtube_channel_id,subscriber_count,video_count,view_count,last_upload_date,upload_frequency_30d,content_type_primary
UC...,15000,120,2500000,2026-06-15,8,clip
```

- `upload_frequency_30d`: 최근 30일 업로드 수
- `content_type_primary`: 최근 영상 10개 기준 주요 유형 분류
  - `clip` — 방송 클립/하이라이트 (5분 이하)
  - `highlight` — 편집 하이라이트 (5-20분)
  - `full_vod` — 풀 VOD/다시보기
  - `original` — 방송과 무관한 오리지널 콘텐츠
  - `mixed` — 혼합

### Task 3: 구비바 유튜브 채널 확인

구비바의 유튜브 채널을 찾아서 Task 2와 동일 지표 수집. 치지직 채널 프로필 소셜 링크 또는 "구비바 치지직" 등으로 검색.

---

## 수집 원칙

- **속도 제한:** ~1 req/s, 과부하 금지. 차단 시 후퇴.
- **API 우선:** YouTube Data API 키가 있으면 사용. 없으면 공개 페이지 파싱.
- **secret/raw 금지:** 쿠키, localStorage, session token, auth header, raw HTML, screenshot 값 저장 금지.
- **271채널 전수가 이상적이지만**, 시간 제약 시 밴드별 샘플링(각 30채널 = 90채널) 허용. 이 경우 샘플링 방법을 명시.

---

## 출력 위치

- `data/cohort/collected/youtube_presence_271.csv` — Task 1
- `data/cohort/collected/youtube_metrics_active.csv` — Task 2
- `data/cohort/collected/youtube_gubiva.csv` — Task 3 (1행)
- `work/step7_youtube_feasibility/구비바_§7_youtube_survey_run_[날짜].md` — 수집 런노트

---

## Hosea(Cowork)가 이후에 할 것

수집 데이터를 받아서:
1. 유튜브 활성/비활성 그룹 간 치지직 지표(리텐션, 팔로워 성장률, 전환율) 비교
2. 콘텐츠 유형별 효과 분석
3. 구비바에 대한 유튜브 타당성 결론 도출
4. `gubiva_§7_youtube_feasibility_[날짜].md` 작성

---

## 우선순위

Task 1 > Task 2 > Task 3. Task 1만 완료되어도 Hosea가 분석 착수 가능.
