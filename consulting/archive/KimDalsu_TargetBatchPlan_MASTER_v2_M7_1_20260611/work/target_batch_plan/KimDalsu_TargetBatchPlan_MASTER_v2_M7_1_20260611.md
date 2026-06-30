# 김달수 TargetBatchPlan — MASTER v2 M7.1 / 채널진단방법론 v3

**생성일:** 2026-06-11T16:47:18+09:00  
**case_id:** `kimdalsu_20260601`  
**목적:** 레거시 1차 리포트를 새 run의 정본으로 쓰지 않고, 최신 MASTER v2 M7.1 스키마 기준으로 김달수 코호트·팔로워·외부 퍼널 데이터를 재수집/재정규화한다.

---

## 0. 상태 결정

- 이전 `김달수_채널분석_컨설팅리포트.md`는 `legacy/previous_milestone_report/`로 이동했다.
- 기존 1년 통계, 183명 수집 대상, 131명 코호트는 **baseline seed**다. 새 CaseResult를 바로 갱신하지 않는다.
- 새 run의 목표는 `EvidencePackage_patch`, `AbsenceInventory_patch`, `DisclosureLog_patch`, `CohortBenchmark_candidate`, `ContentFunnelAnalysis_candidate` 생성이다.
- CaseResult/PortfolioRow 승격은 Hosea/operator 분석 후에만 수행한다.

---

## 1. Target groups

| 우선순위 | target_id | 역할 | profile |
|---:|---|---|---|
| 1 | `softcon_subject_channel_current_stats` | 김달수 현재 Softcon 채널 지표 | 필요 |
| 1 | `softcon_chzzk_lol_population_monthly` | 치지직 롤/MOBA 주 코호트 모집단 | 필요 |
| 1 | `softcon_chzzk_follower_ranking_enterprise` | follower_count/channel_hash 매칭 | 필요 |
| 2 | `semorank_chzzk_follower_public_crosscheck` | 공개 팔로워 랭킹 교차검증 | 불필요 |
| 3 | `auro_live_chzzk_follower_public_crosscheck` | 공개 팔로워 랭킹 보조 교차검증 | 불필요 |
| 2 | `chzzk_subject_channel_public_profile` | 치지직 공개 프로필 교차검증 | 불필요 |
| 2 | `youtube_dalsooisfree_content_funnel` | 유튜브 외부 퍼널 후보 | 불필요 |
| 3 | `softcon_cohort_member_profile_enrichment` | 누락/애매한 코호트 행 보강 | 필요 |

---

## 2. 핵심 경계

- Softcon 엔터/멤버 세션은 사람이 로그인하고, 도구는 profile summary만 기록한다.
- cookie/token/session/csrf/password는 필드 정책상 저장 금지.
- rate limit, checkpoint, login invalid, restricted gate는 반복 통과 시도하지 않고 boundary signal로 기록 후 중단한다.
- Semorank/Aurolive/CHZZK/YouTube는 공개 교차검증용이며, Softcon enterprise source를 대체하지 않는다.

---

## 3. Arthur 입력 원칙

Charles/CrawlScouter 전체 report가 아니라 **`protocol` 섹션만** Arthur에 넘긴다. collect는 아래 순서를 따른다.

```text
TargetBatchPlan
  -> Charles scout_json/scout_protocol per target
  -> Hosea/operator review
  -> Arthur inspect
  -> CollectDirective approved=true로 collect
  -> Evidence/Absence/Disclosure patch 생성
```

---

## 4. 산출물 위치

```text
runs/kimdalsu_20260601/{run_id}/
  10_charles/
  30_arthur_inspect/
  40_arthur_collect/
  50_ingest_candidates/
```

자세한 JSON은 `work/target_batch_plan/KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.json`을 기준으로 한다.
