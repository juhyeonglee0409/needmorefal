# SESSION_NOTE

## Date

2026-06-15

## Case

구비바 §4 CC Handoff — Pearson v0.2 + Pipeline Integration

## Scenario

Scenario 3 - Storage infrastructure + data pipeline integration

## Goal

Pearson v0.2 구현 검증 + 수집 데이터 → CollectionResult 변환 → Pearson 입고 완료

## Loaded Context

- `IsaacInfra/researches/pearson 리서치_v_4_ claude p12.md` — CHART v4 Phase 1+2 (163 facts)
- `IsaacInfra/researches/pearson_v4_source_lookup_table.md` — source lookup table
- `IsaacInfra/researches/pearson 리서치_v_4_ GPT p3.md` — CHART v4 Phase 3 결과
- `IsaacInfra/Pearson/current/Pearson_v0.2_storage_contract/SPEC_pearson_v0_2.md` — v0.2 정본 스펙
- `IsaacInfra/Pearson/current/Pearson_v0.1_storage_contract/` — v0.1→v0.2 코드베이스
- `구비바_CASE_PACKAGE_v3_20260611/machine/구비바_§4_case_params_v1.json` — 수집 프로토콜

## Actions

### [이전 세션] 수집 파이프라인
- Cookie Bridge 4경로 전부 실패 → Playwright persistent context 유일 경로
- `pw_enrich.py` 멀티탭 async 파이프라인 구축 → 수집 완료 (965/965, 조인 5,679)

### [CC] Pearson v0.2 CHART → SPEC → IMPL
- CHART v4 Phase 1+2 리서치 (163 facts) 확인
- CHART v4 Phase 3 프롬프트 생성 → GPT 세션에서 실행 → 오염검사 clean pass
- CHART → SPEC_pearson_v0_2.md 변환 (6 defense lines, §0–§12)
- Codex P1-P2 + Cowork P1-P6 리뷰 10건 반영
- IMPL_PROMPT_v0_2.md 생성 → Codex 구현 의뢰

### [Codex] Pearson v0.2 구현
- 신규 모듈 5개 + 기존 수정 7개 + 테스트 6개 = 20 files, +1,146 lines
- 145 tests 전부 PASS (직접 실행 러너, pytest 미설치; P6 code_commit follow-up 포함)
- CLI smoke: `--version` → 0.2.0, store/scrub/verify-tail PASS

### [CC] 파이프라인 연결
- CSV 컬럼 분석 → 24필드 매핑 테이블 작성
- `gubiba_csv_to_cr.py` 컨버터 작성 (CSV + JSONL → CollectionResult 0.6.1)
- `pearson validate` → valid (965 items, 6 absences)
- `pearson store --durability fsynced` → receipt v0.2 생성
- `pearson scrub` → 0 corrupted
- `pearson verify-tail` → valid
- git push 완료 (7 commits, rebase on 3 remote commits)

## Outputs

### 이전 세션 산출물 (수집 파이프라인)
- `work/step4_cohort_collect_prep/scripts/pw_enrich.py` — 멀티탭 async 수집 스크립트
- `data/cohort/collected/gubiba_20240101_20260615_enriched_965.csv` — 수집 완료 (965행)
- `data/cohort/collected/gubiba_20240101_20260615_pw_enriched.jsonl` — 시계열 enrichment (5,679건)

### 이번 세션 산출물 (Pearson v0.2 + 파이프라인 연결)
- `IsaacInfra/Pearson/current/Pearson_v0.2_storage_contract/SPEC_pearson_v0_2.md` — v0.2 정본 스펙 (CHART v4 163 facts → 6 defense lines)
- `IsaacInfra/Pearson/current/Pearson_v0.2_storage_contract/IMPL_PROMPT_v0_2.md` — Codex 구현 의뢰 프롬프트
- `IsaacInfra/Pearson/current/Pearson_v0.1_storage_contract/pearson/` — v0.2 구현 (5 신규 모듈 + 6 수정 모듈, 145 tests PASS after P6)
  - 신규: `source_id.py`, `presence.py`, `durability.py`, `writer_lock.py`, `integrity.py`
- `IsaacInfra/Pearson/current/Pearson_v0.1_storage_contract/contrib/gubiba_csv_to_cr.py` — CSV→CollectionResult 컨버터
- `IsaacInfra/Pearson/current/Pearson_v0.1_storage_contract/contrib/gubiba_cr_field_mapping.md` — 24필드 매핑 테이블
- `data/cohort/collected/gubiba_CollectionResult.json` — 변환된 CR (v0.6.1, 965 items, 4.9MB)
- `data/cohort/pearson_store/` — Pearson 저장소 (version 000001)
  - `CollectionResult.json` (원재료 보존)
  - `StorageReceipt.json` (v0.2 영수증: source_id, presence_map, lineage_v2, durability=fsynced)
  - `checksums.json`
  - `artifacts/` (normalized_items.csv, field_coverage.csv, absence_summary.csv, item_index.jsonl)

## Decisions

- Vercel WAF는 TLS/H2 fingerprint + JS challenge로 HTTP 클라이언트를 차단함. 진짜 브라우저만 통과.
- Playwright persistent context가 현재 유일한 작동 경로.
- 수집 속도는 SOFTC.ONE 제휴 가능성 고려하여 보수적 유지 (~1 req/s).
- Pearson v0.2: CHART v4 리서치(163 facts) 기반 6개 방어선 설계. Codex+Cowork 리뷰 10건 반영 후 구현 의뢰.
- CSV→CR 컨버터: full spec 불필요, 필드 매핑 테이블로 충분 (입출력 양쪽 스키마 이미 확정).
- stream_hours 등 소수점 값 발견 → float 변환 적용.
- case_params_v1.json 잘림 복원 (`membership_restricted_fields.missing_reason` 미완성 → 닫음).

## Blockers

- 없음

## Next Step

- Susan QA (저장 품질 검수)
- §5 진단 진입: cohort_final_main_general_game.csv, cohort_robustness_table.csv 생성
- tls-client WAF 우회 테스트런 (수집 완료됨, 미진행)

---

## [Cowork/Hosea] 2026-06-15T09:27

1. What was done
   - Cross-surface infrastructure: created `Gunsmith_Mailbox/instructions/Cowork.md` (Cowork entry point) and `_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md` (SESSION_NOTE + DECISION_LOG cross-surface writing rules). README.md updated with pointer, DECISION_LOG entry DL_INFRA_20260615_044 recorded.
   - needmorefal card game — auro.live ranking data collection (Step 1 only):
     - Collected full follower ranking from auro.live API (SvelteKit `__data.json` endpoint), pages 0–219, ranks 1–11,000. 11,000 entries, 0 errors, 0 duplicates.
     - Generated card extraction: WHITE 10 cards (100-rank bands, 1–1000) + BLACK 10 cards (1000-rank bands, 1001–11000) = 20 cards total, random 1 per band (seed 42).
     - Step 2 (SOFTC.ONE enrichment for peak/avgViewers/chart) deferred by operator.
   - Pearson v0.2 spec review: reviewed CC's SPEC_pearson_v0_2.md against CHART v4 163 facts. Verdict: sound, proceed to implementation. 6 issues found (P1–P6), all refinement-level.
   - Pearson v0.2 implementation review: CC completed implementation (5 new modules, 144 tests pass at review time). Reviewed against spec + P1–P6. P1–P3 addressed. P4/P5 low priority. P6 (code_commit dead code) noted as medium; superseded by Codex P6 follow-up below.
   - CHART Phase 3 research results explained to operator in simplified form.

2. Files produced
   - `Gunsmith_Mailbox/instructions/Cowork.md` — Cowork surface entry point
   - `_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md` — cross-surface continuity spec
   - `Gunsmith_Mailbox/reports/auro_rank_1_11000.json` — auro.live rank 1–11000 raw data (11,000 entries)
   - `Gunsmith_Mailbox/reports/auro_rank_1_10000.json` — superseded by above, can be removed
   - `Gunsmith_Mailbox/reports/needmorefal_streamerData_COMBINED_v2.json` — 20 card extraction (peak/avgViewers/chart = null, pending Step 2)
   - `Gunsmith_Mailbox/reports/pearson_v0_2_spec_review_20260615.md` — spec review report

3. File status
   - `Cowork.md`: reviewed — operator must manually update Gunsmith_Mailbox project instruction to point here instead of bootstrap_v0_6.md
   - `12_CONTINUITY_CONTRACT.md`: commit-candidate
   - `auro_rank_1_11000.json`: raw — unverified against SOFTC.ONE, auro.live-only fields
   - `needmorefal_streamerData_COMBINED_v2.json`: hold — incomplete, waiting Step 2 enrichment
   - `pearson_v0_2_spec_review_20260615.md`: reviewed

4. Next surface actions
   - **Cowork**: needmorefal Step 2 — SOFTC.ONE enrichment for 20 cards (peak/avgViewers/chart). Operator deferred, resume when instructed.
   - **Codex**: commit `12_CONTINUITY_CONTRACT.md` + README.md pointer update. Review DECISION_LOG DL_INFRA_20260615_044.
   - **Codex**: P6 code_commit wiring completed in the 2026-06-15T18:41+09:00 block below. Pearson remaining follow-ups are P4/P5 low-priority.

5. Boundaries and warnings
   - Sandbox proxy blocks auro.live (403 Tunnel Forbidden). All auro.live API access must go through Chrome browser JS fetch, not sandbox bash.
   - auro.live API: 50 entries/page, SvelteKit devalue format. 1.5s delay between requests was stable. Charles confirmed: no gate, Cloudflare, robots allowed.
   - Operator has not yet updated Gunsmith_Mailbox project instruction from bootstrap_v0_6.md → Cowork.md.
   - `auro_rank_1_10000.json` is superseded by `auro_rank_1_11000.json` — operator may delete the former.

---

## [Codex] 2026-06-15T18:41+09:00

1. What was done
   - Pearson v0.2 implementation P6 follow-up completed.
   - Added best-effort `code_commit` wiring in `pearson/store.py`.
   - `store_collection_result()` now calls `git rev-parse HEAD` from the workspace root and passes a 40-char commit hash into `lineage.activity.code_commit` when available.
   - Non-git or git-failure environments remain supported: `code_commit` stays `None`.
   - `tests/test_store_v02_integration.py` now verifies `code_commit is None or 40-char hex`.

2. Verification
   - `tests/test_store_v02_integration.py`: 19 PASS / 0 FAIL.
   - Pearson direct-run test suite: 145 PASS / 0 FAIL.
   - `py_compile` for `pearson/*.py` and `tests/*.py`: PASS.
   - `git diff --check` for P6 files: PASS.
   - Smoke confirmed receipt `lineage.activity.code_commit` was populated with current git commit `753ec3ea5b0803911cecf915cebd340c481350f6`.
   - `pytest tests` still not run because bundled Python has no `pytest` module.

3. Commit candidates
   - Pearson v0.2 implementation under `IsaacInfra/Pearson/current/Pearson_v0.1_storage_contract/`.
   - Includes modified core modules, new v0.2 modules, test updates, and `pyproject.toml`.
   - P6-specific modified files:
     - `pearson/store.py`
     - `tests/test_store_v02_integration.py`

4. Hold / excluded
   - P4 `ALLOWED_CR_VERSIONS` hardcoding remains accepted low-priority follow-up.
   - P5 typed `source_id` reproduction CLI remains accepted low-priority follow-up.
   - Non-Pearson dirty files in workspace are unrelated to this Pearson commit and must not be mixed unless explicitly reviewed.

5. Next action
   - Codex: stage only Pearson v0.2 implementation files when committing.
   - Do not include unrelated Instruction, Streamer, Crashpad, or Gubiba data artifacts in the Pearson commit.
   - After commit, run/report targeted Pearson test command summary before push.

---

## [Codex] 2026-06-15 - SOFTC.ONE Step5 browser-bound collection note

1. What was learned
   - SOFTC.ONE §5 broadcast records are browser-session-bound and checkpoint-gated.
   - Current stable route is a user-approved Chrome/CDP session after the operator passes the checkpoint.
   - Confirmed streams URL shape: `/channel/{platform}/{channelId}/streams`.
   - `CSV 다운로드` exists in the UI but is not automation-stable in current observations.
   - No stable separate JSON/CSV endpoint was confirmed for this path; DOM row extraction is the current primary collection path.

2. Boundary
   - Do not export or persist cookies, localStorage, session tokens, auth headers, or account secrets.
   - CDP/persistent browser context is only an execution transport inside the approved scope.
   - Stop on 429 loops, repeated challenge loops, scope expansion, private/account data, or secret persistence uncertainty.

3. Protocol update
   - Added the reusable browser-bound collection failure matrix to `_WORKING_CONTEXT/03_STREAMER_CASE_GENERIC_PROTOCOL.md`.
   - SOFTC.ONE Step5 is now recorded as: user-approved browser session, canonical streams URL, DOM row extraction primary, UI CSV download opportunistic only.
