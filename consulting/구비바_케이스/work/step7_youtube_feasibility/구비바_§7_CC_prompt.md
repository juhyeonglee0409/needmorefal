# §7 유튜브 병행 현황 조사 — Codex 실행 프롬프트

아래를 Codex 세션에 붙여넣기:

---

```
구비바 케이스 §7 유튜브 타당성 분석을 위한 데이터 수집을 실행해줘.

## 컨텍스트 로딩

1. `Streamer Consulting Project/_WORKING_CONTEXT/README.md` 읽기
2. `Streamer Consulting Project/구비바_케이스/work/step7_youtube_feasibility/구비바_§7_CC_handoff_youtube_survey.md` 읽기 — 이게 작업 지시서

## 요약

Cowork/Hosea가 2부 §7 "유튜브를 (재)시작해야 하는가" 분석을 위해 데이터 수집을 위임했다.

타겟: `data/cohort/collected/cohort_ref_upper_band.csv` (271채널, 팔로워 10k+)
구비바 치지직 ID: 269edc95873a1ec9fc534851c0783d1f

## 실행할 것 (우선순위순)

Task 1: 271채널 각각의 유튜브 채널 존재 여부 확인
- 방법: 치지직 채널 프로필의 소셜 링크 확인 → 없으면 YouTube에서 채널명 검색
- 출력: `data/cohort/collected/youtube_presence_271.csv`

Task 2: Task 1에서 has_youtube=true인 채널의 유튜브 기본 지표 수집
- 구독자, 영상 수, 조회수, 마지막 업로드, 최근 30일 업로드 빈도, 콘텐츠 유형
- 출력: `data/cohort/collected/youtube_metrics_active.csv`

Task 3: 구비바 유튜브 채널 찾아서 동일 지표 수집
- 출력: `data/cohort/collected/youtube_gubiva.csv`

## 수집 원칙

- ~1 req/s, 과부하 금지, 차단 시 후퇴
- YouTube Data API 키가 있으면 사용, 없으면 공개 페이지
- 271 전수가 이상적이지만, 시간 제약 시 밴드별 30채널 샘플링(총 90) 허용
- secret/raw 금지 (쿠키, token, raw HTML 저장 금지)
- 런노트를 `work/step7_youtube_feasibility/구비바_§7_youtube_survey_run_[날짜].md`에 작성

세부 스펙은 핸드오프 문서에 있으니 그걸 따라가면 된다. Task 1만 완료돼도 Hosea가 분석 착수 가능.
```
