# 김달수 재수집 — Codex 실행 프롬프트

> 이 프롬프트를 Codex 세션에 붙여넣고 실행한다.
> 세션 진입 체인(`_CODEX_SESSION_START.md` → `README.md`)을 먼저 로드한 뒤, 이 프롬프트의 지시를 따른다.

---

## 0. 세션 컨텍스트

**case_id**: `kimdalsu_20260601`
**작업**: TargetBatchPlan MASTER v2 M7.1 기준 재수집 (deep_dive_recollect)
**시나리오 분류**: Deep-Dive — 세션 진입 시 `README.md` 시나리오 테이블에서 확인

### 핵심 문서 위치 (모두 읽을 것)

| 문서 | 경로 | 역할 |
|---|---|---|
| TargetBatchPlan JSON | `KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/work/target_batch_plan/KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.json` | 8개 타겟 정의, 필드셋, scope, 검증 힌트 |
| CLI Orchestrator Prompt | `KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/work/orchestrator/KimDalsu_CLI_Orchestrator_Prompt_20260611.md` | 7단계 실행 순서, 작업 원칙, 산출물 계약 |
| Recollect Runbook | `KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/work/orchestrator/KimDalsu_Recollect_Runbook_20260611.md` | 권장 순서, 중단/완료 조건 |
| Source URL Notes | `KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/work/target_batch_plan/SOURCE_URL_NOTES.md` | 타겟 URL 후보 |
| site_runbooks/ | `_WORKING_CONTEXT/site_runbooks/` | 사이트별 작동 경로·실패 모드·속도 제약 |
| DECISION_LOG | `_WORKING_CONTEXT/07_DECISION_LOG.md` | 활성 결정사항 (DL_016~047) |
| SESSION_NOTE | `_WORKING_CONTEXT/SESSION_NOTE.md` | 최신 핸드오프 |
| CONTINUITY_CONTRACT | `_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md` | SESSION_NOTE/DL 작성 규칙 |

---

## 1. 데이터 현황 (2026-06-16 정리 완료)

### TBP 패키지 상태

14개 중복 파일이 제거됐다. 상세 내역은 `LEGACY_RELOCATION_NOTE.md` 하단 "2026-06-16 Data Cleanup" 참조.

**현재 TBP 구조** (work/ 디렉토리만 남음):
```
KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/
├── LEGACY_RELOCATION_NOTE.md          ← 정리 이력 포함
├── work/
│   ├── orchestrator/
│   │   ├── KimDalsu_CLI_Orchestrator_Prompt_20260611.md
│   │   └── KimDalsu_Recollect_Runbook_20260611.md
│   └── target_batch_plan/
│       ├── KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.json
│       ├── KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.md
│       └── SOURCE_URL_NOTES.md
```

- `legacy/`, `references/`, `.zip` 모두 삭제됨. 정본은 CASE_PACKAGE에 있다.
- legacy seed 파일(방송통계 287행, 수집대상 183명, 코호트 131명)의 정본 위치: `김달수_케이스/data/`

### CASE_PACKAGE 정본 위치

```
김달수_케이스/
├── data/
│   ├── daily_stats/김달수_Dalsu_방송통계_1년_20260528.csv   (287행)
│   ├── cohort/김달수_코호트_131명.csv                       (131행)
│   ├── cohort/수집대상_183명.csv                            (183행)
│   └── cohort/specs/스크래핑_작업명세서_구현팀.md
├── deliverables/milestone_report/김달수_채널분석_컨설팅리포트.md
├── references/current_framework/
│   ├── MASTER_streamer_mcn_framework_v2_draft_M7_1_QA2_patched_20260610.md
│   ├── MASTER_v2_M7_1_canonical_enum_table_20260610.csv
│   ├── MASTER_v2_M7_1_canonical_schema_pack_20260610.json
│   ├── MASTER_v2_M7_1_disclosure_boundary_matrix_20260610.csv
│   └── 스트리머_채널진단_방법론_v3_draft_START_20260610.md
└── machine/                                                 (schema/ 삭제됨, 정본은 references/)
```

---

## 2. 사이트별 운영 지식 — site_runbooks 요약

아래는 `_WORKING_CONTEXT/site_runbooks/`에서 추출한 핵심 운영 제약이다. 전문은 각 runbook 파일을 직접 읽어라.

### SOFTC.ONE (Softcon Viewership)

**이것만 작동한다:**
- **Playwright persistent context** (async, multi-tab) — pw_enrich.py, 965/965 완료 실적
- **nodriver + existing approved profile** (.pw_profile) — 687/687 완료 실적. **fresh profile은 checkpoint 도달(실패). 사용 금지.**
- **Browser DOM row extraction** — CSV 다운로드보다 안정적

**이것은 전부 실패한다** (DL_038):
- curl_cffi, CDP headless, Playwright cookies→HTTP client, tls-client/got-scraping/patchright/botright/camoufox (미테스트이나 WAF 동일)

**속도 제약:**
- 총 요청률 ~1 req/s 유지 (DL_040, DL_041 제휴 고려)
- 멀티탭: 3탭×3초 또는 6탭×6초 안정 실측 (DL_039)
- 429 + `x-vercel-mitigated: challenge` → 즉시 중단

**Step5 full-range protocol** (DL_045):
- 반드시 `?startDateTime={iso}&endDateTime={iso}` 명시
- scale ladder: 소규모 single-worker → 점진적 concurrency
- resume: `skipExisting` before `limit`
- progress NDJSON + per-item CSV/notes flush 필수

**카테고리 랭킹** (DL_037):
- 일반 랭킹(400ch) → 카테고리 랭킹(롤 10,000ch, CSV 2000행 제한) 전환 완료
- 김달수 타겟의 `softcon_chzzk_lol_population_monthly`에서 카테고리 랭킹 사용

### CHZZK

- 수집 대상이 아니라 **upstream identity source**
- 공개 프로필 API (`chzzk.naver.com/api/channels/{channelId}`) — working, 인증 불필요
- 403/401 → absence 기록, 재시도 불필요
- 방송 기록/시계열 endpoint는 별도 탐색 필요 (미검증)

### Semorank

- 공개 랭킹 페이지 — Charles 진단 후 수집
- site_runbook 미작성 (공개 사이트, 특이 제약 없음)

### Auro.live

- SvelteKit `__data.json` API — devalue format 파싱 필요
- **Codex sandbox proxy 403 차단** — Chrome JS fetch route만 작동
- 50 entries/page, 1.5s delay 안정
- 김달수 P3 보조 교차검증용이므로 불가 시 absence 기록 후 진행

### YouTube

- 공개 채널 영상 목록 — Charles 진단 후 수집
- site_runbook 미작성 (표준 공개 접근)

---

## 3. 실행 지시

### 3.1 준비

1. `_CODEX_SESSION_START.md` → `README.md` 로드
2. `SESSION_NOTE.md` 최신 핸드오프 확인
3. `07_DECISION_LOG.md`에서 활성 결정 확인 (특히 DL_037~047)
4. 위 §2의 사이트별 운영 지식을 숙지
5. run_id를 `kimdalsu_recollect_20260616_01` 형태로 생성
6. `runs/kimdalsu_20260601/{run_id}/` 아래 표준 폴더 생성:
   ```
   00_inputs/legacy/
   10_charles/
   30_arthur_inspect/
   40_arthur_collect/
   50_ingest_candidates/
   ```
7. legacy seed 파일을 `00_inputs/legacy/`에 복사/symlink (정본 위치: CASE_PACKAGE `data/`)

### 3.2 타겟 실행 순서

Runbook 권장 순서를 따른다:

| 순서 | target_id | P | profile | 사이트 제약 요약 |
|---:|---|---:|---|---|
| 1 | `softcon_subject_channel_current_stats` | 1 | 필요 | Playwright/nodriver+existing, ~1req/s |
| 2 | `softcon_chzzk_lol_population_monthly` | 1 | 필요 | 카테고리 랭킹, CSV 2000행 제한, Playwright |
| 3 | `softcon_chzzk_follower_ranking_enterprise` | 1 | 필요 | follower ranking, 300위 컷 시 중단 |
| 4 | `semorank_chzzk_follower_public_crosscheck` | 2 | 불필요 | 공개, Charles 진단 먼저 |
| 5 | `chzzk_subject_channel_public_profile` | 2 | 불필요 | 공개 API |
| 6 | `youtube_dalsooisfree_content_funnel` | 2 | 불필요 | 공개, content funnel 후보 |
| 7 | `softcon_cohort_member_profile_enrichment` | 3 | 필요 | 누락분만 대상, Playwright |

`auro_live_chzzk_follower_public_crosscheck` (P3)은 sandbox 403 제약으로 Codex에서 직접 수집 불가할 가능성 높음. Charles 진단 후 불가 시 absence 기록.

### 3.3 타겟별 실행 흐름

각 타겟에 대해 CLI Orchestrator의 7단계를 따른다:

```
1. 준비 (run_id, 폴더)
2. Charles 진단 → 10_charles/{target_id}.scout_report.json + .protocol.json
3. Review → protocol.best_path, boundary signal, profile_required 확인
4. Arthur inspect → 30_arthur_inspect/{target_id}.InspectResult.json
5. CollectDirective 승인 → approved=true (operator 승인 후)
6. Arthur collect → 40_arthur_collect/{target_id}/
7. Ingest candidate 생성 → 50_ingest_candidates/
```

**핵심 원칙:**
- Charles output 중 Arthur에는 `protocol` 섹션만 전달
- CollectDirective는 `approved=false`로 시작, review 후에만 `true`
- CaseResult/PortfolioRow 자동 갱신 금지. `50_ingest_candidates/`의 patch 후보로만 남긴다
- secret 값(cookie, token, session, csrf, password) 저장 금지

### 3.4 Softcon 타겟 (P1) 특별 지시

Softcon 3개 타겟은 operator-logged-in profile이 필요하다:

1. **Playwright persistent context 사용**. nodriver + existing profile도 가능하나, Playwright가 965/965 + 687/687 실적으로 더 검증됨
2. **fresh nodriver profile 사용 금지** — checkpoint 도달 실패 실측 (§6 upper band run)
3. `softcon_chzzk_lol_population_monthly`의 URL은 미확정(`operator_or_charles_must_resolve`). Charles로 카테고리 랭킹 URL을 먼저 확인:
   - 후보: `/category/League of Legends/ranking` 계열 (DL_037 전환)
   - platform=naverchzzk, aggregation_window=최근 완전 월
4. `softcon_chzzk_follower_ranking_enterprise`도 URL 미확정. follower ranking 페이지에서 전체 범위 확인. 300위 컷이면 `profile_invalid`로 중단
5. 속도: 총 ~1 req/s, 429 즉시 중단, scale ladder 적용

### 3.5 중단 조건

Runbook 중단 조건을 준수한다:
- 로그인 세션 만료/권한 부족
- 반복 429/403/checkpoint
- target-specific bypass 필요
- 공개 범위 밖 개인/민감 정보 노출
- approved_scope 밖 URL 확장 필요

중단 시 boundary signal을 기록하고, 해당 타겟을 absence로 처리한 뒤 다음 타겟으로 진행.

### 3.6 완료 조건

- main cohort population 재수집 또는 source_absence 명시
- follower match rate 산출
- target subject current stats 재확인
- external content funnel 후보 수집 또는 not_collected 이유 기록
- Evidence/Absence/Disclosure patch 산출

### 3.7 최종 산출물

```
runs/kimdalsu_20260601/{run_id}/
├── RUN_MANIFEST.json
├── TargetReviewSummary.md
├── 10_charles/
├── 30_arthur_inspect/
├── 40_arthur_collect/
└── 50_ingest_candidates/
    ├── EvidencePackage_patch.json
    ├── AbsenceInventory_patch.json
    ├── DisclosureLog_patch.json
    ├── CohortBenchmark_candidate.json
    └── ContentFunnelAnalysis_candidate.csv
```

---

## 4. 핸드오프

작업 완료 후 `SESSION_NOTE.md`에 5항 핸드오프를 남긴다 (12_CONTINUITY_CONTRACT 형식):

1. What was done
2. What files were produced
3. File status
4. What the next surface should do → `[Cowork/Hosea]` — patch review 및 CaseResult 승격 판단
5. Boundaries and warnings

DECISION_LOG 엔트리가 필요한 결정이 있으면 `07_DECISION_LOG.md`에 추가한다 (현재 최고 번호 확인 후 increment).

---

## 5. 경계 재확인

- 이전 김달수 리포트는 legacy reference. 새 수집의 정본으로 쓰지 않는다.
- CaseResult/PortfolioRow 승격은 Hosea/operator 분석 후에만.
- Softcon enterprise session은 operator 직접 로그인. 도구는 profile summary만 기록.
- cookie/token/session/csrf/password 저장 금지.
- rate limit, checkpoint, login invalid, restricted gate → 반복 통과 시도 금지, boundary signal 기록 후 중단.
- Semorank/Aurolive/CHZZK/YouTube는 공개 교차검증용. Softcon enterprise source를 대체하지 않는다.
