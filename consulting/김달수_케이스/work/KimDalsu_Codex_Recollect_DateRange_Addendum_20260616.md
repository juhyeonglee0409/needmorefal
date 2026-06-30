# 김달수 재수집 — 기간 설정 보충 지시

> 본 프롬프트의 재수집 프롬프트(`KimDalsu_Codex_Recollect_Prompt_20260616.md`) §3 이후에 적용한다.

---

## §3.8 수집 기간 정책

**기준일:** 실행일 (run_id 생성 시점)  
**기본 범위:** 기준일로부터 **최근 6개월**

### 타겟별 적용

| target_id | 기간 적용 | 구체 지시 |
|---|---|---|
| `softcon_subject_channel_current_stats` | 해당 없음 | 스냅샷. 실행 시점 값 수집 |
| `softcon_chzzk_lol_population_monthly` | 기존 정책 유지 | TBP `collection_window_policy.preferred = latest_complete_month` 따름 |
| `softcon_chzzk_follower_ranking_enterprise` | 해당 없음 | 스냅샷. 실행 시점 값 수집 |
| `semorank_chzzk_follower_public_crosscheck` | 해당 없음 | 스냅샷 |
| `chzzk_subject_channel_public_profile` | 해당 없음 | 스냅샷 |
| `youtube_dalsooisfree_content_funnel` | **최근 6개월** | 기준일 − 180일 이후 업로드된 영상만 대상. 전체 목록 중 범위 밖은 metadata만 count하고 본문 수집 생략 |
| `softcon_cohort_member_profile_enrichment` | **최근 6개월** | `?startDateTime={기준일−180d ISO}&endDateTime={기준일 ISO}` 명시. DL_045 full-range protocol 적용 |

### 구현 규칙

1. **startDateTime / endDateTime을 반드시 URL 파라미터에 명시한다.** 생략 시 서버 기본값(전체 기간)이 적용돼 불필요한 트래픽이 발생한다.
2. legacy 데이터(2025.05~2026.05)와 겹치는 구간이 있어도 **새로 수집한다.** legacy는 참조용이지 정본이 아니다.
3. 6개월 범위에서 데이터가 0건인 채널은 `absence` 기록 후 다음으로 진행한다. 범위를 임의로 확장하지 않는다.
4. 수집 완료 후 `RUN_MANIFEST.json`에 실제 적용된 `startDateTime`, `endDateTime`을 기록한다.
