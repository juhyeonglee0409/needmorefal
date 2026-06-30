# 김달수 재수집 Runbook — 최신 MASTER 기준

## 목적
김달수 케이스를 기존 v1 산출물에서 분리하고, MASTER v2 M7.1 + 채널진단방법론 v3 기준으로 새 수집 run을 만든다.

## 실행 전 확인
- Softcon profile/session 사용 가능 여부
- Softcon에서 300위 너머가 보이는지 여부
- `TargetBatchPlan`의 unresolved target URL 해결 여부
- Arthur 의존성 설치 여부: `protego`, `httpx`, `beautifulsoup4`, optional playwright/curl_cffi

## 권장 순서
1. `softcon_subject_channel_current_stats`
2. `softcon_chzzk_lol_population_monthly`
3. `softcon_chzzk_follower_ranking_enterprise`
4. `semorank_chzzk_follower_public_crosscheck`
5. `chzzk_subject_channel_public_profile`
6. `youtube_dalsooisfree_content_funnel`
7. 누락분에 한해 `softcon_cohort_member_profile_enrichment`

## 중단 조건
- 로그인 세션 만료/권한 부족
- 반복 429/403/checkpoint
- target-specific bypass 필요
- 공개 범위가 아닌 개인/민감 정보 노출
- approved_scope 밖 URL 확장 필요

## 완료 조건
- main cohort population 재수집 또는 source_absence 명시
- follower match rate 산출
- target subject current stats 재확인
- external content funnel 후보 수집 또는 not_collected 이유 기록
- Evidence/Absence/Disclosure patch 산출
