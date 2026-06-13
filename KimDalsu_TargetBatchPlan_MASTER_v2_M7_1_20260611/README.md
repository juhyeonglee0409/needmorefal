# KimDalsu TargetBatchPlan Package — MASTER v2 M7.1

**생성일:** 2026-06-11T16:47:18+09:00  
**case_id:** `kimdalsu_20260601`  

이 패키지는 김달수 케이스를 최신 MASTER v2 M7.1 + 채널진단방법론 v3 기준으로 재수집/재정규화하기 위한 CLI 오케스트레이터 입력 묶음이다.

## 핵심 파일

- `work/target_batch_plan/KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.json`
- `work/target_batch_plan/KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.md`
- `work/target_batch_plan/KimDalsu_TargetBatchPlan_column_contract_20260611.csv`
- `work/orchestrator/KimDalsu_CLI_Orchestrator_Prompt_20260611.md`
- `work/orchestrator/KimDalsu_Recollect_Runbook_20260611.md`
- `work/collect_directives/CollectDirective_TEMPLATE_*.json`

## Legacy 정책

이전 김달수 1차 리포트는 `legacy/previous_milestone_report/`로 이동했다. 이 리포트는 baseline/reference로만 쓰고, 새 CaseResult/PortfolioRow의 fresh evidence로 직접 쓰지 않는다.

## Target 요약

1. Softcon subject channel current stats
2. Softcon CHZZK LoL/MOBA monthly population
3. Softcon follower ranking enterprise match
4. Semorank public follower cross-check
5. Aurolive public follower cross-check
6. CHZZK public subject profile
7. YouTube `@dalsooisfree` content funnel
8. Softcon cohort member profile enrichment

## 주의

- Softcon enterprise/member data는 profile/session이 필요할 수 있다.
- 비밀번호·쿠키·토큰·세션 값은 절대 저장하지 않는다.
- 수집 결과는 바로 CaseResult에 쓰지 말고 `50_ingest_candidates/` patch 후보로 둔다.
