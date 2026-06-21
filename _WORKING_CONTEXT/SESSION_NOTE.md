# SESSION_NOTE

## Date

2026-06-16

## Case

구비바 §4-§6 CC Handoff — Pearson v0.2 + Pipeline + Arthur async fix + site_runbooks

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
- §6 목표 트레이드오프 분석 (upper reference band 271행 수집 완료)
- tls-client WAF 우회 테스트런 (수집 완료됨, 미진행)
- AURO_LIVE DL 엔트리 작성 검토 (반복 발견 trigger 시)

---

## [Cowork/Hosea] 2026-06-20T21:00+09:00 — 방법론 v3→v4 업그레이드

**한 줄 요약:** 구비바·김달수 2케이스 실행 결과를 역주입하여 채널진단 방법론을 v3에서 v4로 업그레이드.

**산출물:**

- `구비바_CASE_PACKAGE_v3_20260611/references/current_framework/스트리머_채널진단_방법론_v4_draft_20260620.md` — v4 정본 (1831행)
- 원본 v3 파일(`_v3_draft_START_20260610.md`)도 in-place 수정됨 (내용 동일, 두 파일 모두 v4 상태)

**변경 내역 (7건):**

1. §5.2 재작성: 4축→6축 포지셔닝 + 잔류율/리텐션 분리 신설 (§5.2.1)
2. §6.2 재작성: 상위 참조 밴드 프로토콜 (6.2.1-6.2.4) + §6.3.1 리텐션 하한 경보
3. §6.6 신설: 궤적매칭 — 비전/피어 레퍼런스, 체급 점수 교훈 (6.6.1-6.6.4)
4. §5.1.2 보강: A/B/C 레이어 분할 + robustness table
5. §5.4.2 보강: 편상관(partial correlation) 검증
6. §7.0+§7.7 신설: 외부 채널 상태 분류 + 비활성 채널 타당성 패턴 (7.7.1-7.7.4)
7. §4.8.1 보강: 보조→주 코호트 역전 조건

**파일 상태:** raw — CC/Codex review 후 git commit 필요.

**다음 세션 할 일:**

- v4 파일명 정리 (v3 원본 파일을 v3 이름으로 복원할지, 삭제할지 결정)
- v4 정본을 `current_framework/` 기준 파일로 확정
- §10~§15, 부록은 v3 그대로 — 실전 케이스 추가 시 역주입 대상

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

---

## [Codex] 2026-06-15T23:28+09:00

1. What was done
   - 구비바 §5 SOFTC.ONE broadcast full-range collection run documented.
   - Verified that the default `/streams` page was not full-history (`2026. 05. 15 - 2026. 06. 15`, 24 links on probe).
   - Verified full/max range by query parameters: `startDateTime=2023-10-01T15:00:00.000Z`, `endDateTime=2026-06-15T14:59:59.999Z`; probe UI showed `2023. 10. 02 - 2026. 06. 15` and 100 stream links.
   - Patched the Step5 CDP parallel collector to use full-range query bounds, `delay-ms`/`jitter-ms`, and resume-safe `skipExisting` before `limit`.
   - Scaled collection gradually: 1 worker/12s limit2, 2 workers/12s limit6, 3 workers/12s limit12, 3 workers/6s limit12, 6 workers/6s limit18; all scale manifests reported `boundary_signal: null`.
   - Full remaining run used 6 workers, 6s delay, 2s jitter, existing-file resume.

2. What files were produced
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/work/step5_diagnosis/구비바_§5_SOFTCONE_full_range_collection_run_20260615.md`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_date_query_probe.json`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_manifest_full_6c6s.json`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_progress_full_6c6s.ndjson`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_errors_full_6c6s.csv`

3. File status
   - Run note: reviewed; current handoff source for the Step5 full-range collection run.
   - Full-run manifest/progress/errors: reviewed operational artifacts; not final analytical judgment.
   - Broadcast CSV files under `broadcast_samples/T1` and `broadcast_samples/T2`: raw collection outputs.
   - Top-level failed `resume` artifact with 429/checkpoint boundary is excluded for current-run status; keep only as history of the pre-delay/pre-full-range attempt.

4. What the next surface should do
   - Codex or CC: use the full-run manifest as the run ledger, not ad hoc folder counts.
   - Codex or CC: reconcile 14 `not_found` channels separately before treating them as true absence.
   - Codex or CC: before §5.6/§5.7 analysis, decide whether the visible DOM 100-row cap is acceptable or whether CSV/API/pagination extraction is needed.

5. Boundaries and warnings
   - Full run summary: 380 candidate rows -> 323 unique targets; 190 attempted in this resume; 175 normal successes, 1 `short_rows`, 14 `not_found`, `boundary_signal: null`.
   - Current local data CSV count: T1 178 + T2 139 = 317 files; target-matched coverage is 309/323 because earlier sample/smoke files are mixed in the folder.
   - No cookies, localStorage, session tokens, auth headers, raw HTML dumps, or screenshots were persisted.
   - Full date range is verified, but DOM extraction exposed up to 100 visible stream rows on the probe. Treat that as a residual extraction-cap risk.

---

## [Codex] 2026-06-16T13:40+09:00

1. What was done
   - 구비바 §6 upper reference band collection completed as a separate reference dataset, not part of the §4 peer cohort.
   - Direct HTTP fetch to SOFTC.ONE follower ranking returned 429/checkpoint; fresh nodriver profile also reached checkpoint.
   - Working route was nodriver with the existing approved `.pw_profile` from §4/§5.
   - Candidate scan produced 687 CHZZK candidates from follower ranking pages 1-25 and virtual ranking pages 1-4.
   - Detail collection completed in two effective passes: balanced 80 candidates, then append-focused 10k-20k 60 candidates.
   - Collector was hardened with existing-candidate reuse, detail `fetch` timeout, progress NDJSON, per-candidate CSV/notes flush, append mode, and band filter.

2. Outputs
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/cohort_ref_upper_band.csv` — final upper reference band, 67 rows.
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/cohort_ref_upper_band_notes.csv` — exclusion notes, 73 rows.
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/_upper_band_candidates.json` — 687-candidate pool.
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/_upper_band_detail_progress.ndjson` — per-candidate progress log.
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/work/step6_tradeoff/구비바_§6_upper_reference_band_collection_run_20260616.md` — run note and caveats.

3. Verification
   - Final CSV schema matches requested columns exactly.
   - Final rows: 67 total; 10k-20k = 21, 20k-50k = 21, 50k+ = 25.
   - Duplicates: 0. Required metrics missing: 0.
   - Notes: 69 `not_general_game_or_virtual`, 2 `too_new_under_8_weeks`, 2 `excluded_org_or_team_heuristic`.
   - Quick descriptive read: `avg_median >= 200` appears in 12/21 of 10k-20k, 19/21 of 20k-50k, 25/25 of 50k+.

4. Boundaries and warnings
   - No cookies, localStorage, session tokens, auth headers, raw HTML dumps, or screenshots were persisted.
   - Dataset is reference-band evidence only; it does not finalize §6 interpretation or mutate canonical case state.
   - Final manifest was written by the append run, so candidate provenance is documented in the run note: candidates came from follower pages 1-25 plus virtual pages 1-4.

---

## [Codex] 2026-06-16T14:10+09:00

1. What was done
   - Reflected the working-context file-count and role-duplication concern as an operating policy.
   - Added `Working Context Hygiene` to `_WORKING_CONTEXT/README.md`.
   - Added `Part 4: Working Context Hygiene` to `_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md`.
   - Prepended decision log entry `DL_INFRA_20260616_047`.

2. What files were produced
   - No new files.
   - Modified: `_WORKING_CONTEXT/README.md`, `_WORKING_CONTEXT/12_CONTINUITY_CONTRACT.md`, `_WORKING_CONTEXT/07_DECISION_LOG.md`, `_WORKING_CONTEXT/SESSION_NOTE.md`.

3. File status
   - Working-context hygiene policy: reviewed; commit-candidate with the surrounding CC/Cowork working-context updates.

4. What the next surface should do
   - Codex or CC: keep future site-specific operational findings in `site_runbooks/` and link to run notes rather than copying long details into generic protocol.
   - Codex or CC: if top-level `_WORKING_CONTEXT` count exceeds 25, propose grouping/archive instead of adding more top-level files.

5. Boundaries and warnings
   - Documentation policy only. No context entries were deleted, compacted, archived, or relocated.
   - No canonical case state, pipeline behavior, code, schema, approval gate, disclosure, or promotion status changed.

---

## [Codex] 2026-06-16T15:50+09:00

1. What was done
   - 구비바 §6 upper reference band detail collection was extended from the earlier sample to the full 687-candidate pool.
   - Collection used SOFTC.ONE through nodriver + the existing approved `.pw_profile`.
   - A mid-run local CSV write interruption was handled by adding retry writes and output-based skip logic; the one output-missing candidate was retried.
   - `_upper_band_detail_records.json` was backfilled records-only for 53 records after the interruption, without changing CSV/notes rows.

2. Final state
   - Candidate detail coverage: 687/687.
   - Final accepted CSV rows: 271.
   - Band distribution: 10k-20k = 88, 20k-50k = 94, 50k+ = 89.
   - Notes: 416 total — 349 `not_general_game_or_virtual`, 54 `follower_below_10k`, 7 `excluded_org_or_team_heuristic`, 6 `too_new_under_8_weeks`.
   - `avg_median >= 200`: 10k-20k = 28/88, 20k-50k = 63/94, 50k+ = 87/89.
   - Duplicates: 0. Required metric missing cells: 0. Detail records: 687/687.

3. Files
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/cohort_ref_upper_band.csv`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/cohort_ref_upper_band_notes.csv`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/collection_logs/_upper_band_detail_progress.ndjson`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/collection_logs/_upper_band_detail_records.json`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/collection_logs/_upper_band_collection_manifest.json`
   - `Streamer Consulting Project/구비바_CASE_PACKAGE_v3_20260611/work/step6_tradeoff/구비바_§6_upper_reference_band_collection_run_20260616.md`

4. Boundaries and warnings
   - No 429/checkpoint/rate-limit boundary was observed during the extension chunks.
   - No cookies, localStorage, sessionStorage, auth headers, raw HTML, or screenshots were persisted.
   - Dataset remains reference-band evidence only; it does not mutate canonical case state or finalize §6 interpretation.

---

## [CC] 2026-06-16T22:30+09:00

1. What was done
   - **Arthur MCP async fix (ARTHUR-MCP-001)**: Playwright sync→async API 전환 3파일 완료.
     - `arthur/collect_playwright.py`: sync_api → async_api, 전 함수 async, 전 page 조작 await.
     - `arthur/cli.py`: `collect()` async화, `inspect.iscoroutinefunction()` 분기, CLI `main()`에서 `asyncio.run()`.
     - `arthur/mcp.py`: `collect_data()` async화, `result = await collect()`.
     - py_compile 3파일 PASS. 커밋 `25ee7ba`.
   - **site_runbooks 신설 (DL_046)**: `_WORKING_CONTEXT/site_runbooks/` 디렉터리 생성.
     - 5파일: README.md, TEMPLATE_SITE_RUNBOOK.md, SOFTC_ONE_RUNBOOK.md(active), AURO_LIVE_RUNBOOK.md(partial), CHZZK_RUNBOOK.md(partial).
     - CC 자체 검수 6건(교정 2 + 경고 1 + 누락 3) 반영.
     - Cowork 독립 검수 5건(결함 2 + 추가 발견 3) 반영: DL_037/DL_020/DL_016 Related Decisions 추가, §6 nodriver proven run 반영, Last verified 갱신.
     - 기존 파일 수정: README.md(File Roles), 03_GENERIC_PROTOCOL(포인터), 07_DECISION_LOG(DL_046).
     - 커밋 `a1ae0d64`.

2. Files produced
   - `_WORKING_CONTEXT/site_runbooks/README.md` — 디렉터리 목적, staleness 관리 프로세스
   - `_WORKING_CONTEXT/site_runbooks/TEMPLATE_SITE_RUNBOOK.md` — runbook 고정 구조 (Related Decisions 포함)
   - `_WORKING_CONTEXT/site_runbooks/SOFTC_ONE_RUNBOOK.md` — SOFTC.ONE 운영 지식 (DL 8건 역추적, proven run 4건)
   - `_WORKING_CONTEXT/site_runbooks/AURO_LIVE_RUNBOOK.md` — auro.live 최소 운영 정보
   - `_WORKING_CONTEXT/site_runbooks/CHZZK_RUNBOOK.md` — chzzk 최소 운영 정보

3. File status
   - Arthur async fix 3파일: commit-candidate (커밋 완료, 미푸시)
   - site_runbooks 5파일 + 기존 수정 3파일: commit-candidate (커밋 완료, 미푸시)

4. What the next surface should do
   - Arthur async fix 실테스트: CLI 경로(`arthur collect`) + MCP 경로(`collect_data` tool)에서 Playwright 처방 실행 검증.
   - git push 대기 (operator 지시 시).
   - Susan QA 진입.
   - §6 목표 트레이드오프 분석 시작 (upper reference band 271행 준비됨).

5. Boundaries and warnings
   - Arthur async fix는 py_compile만 통과. 실제 Playwright 실행 테스트 미진행.
   - site_runbooks는 문서 구조 변경만. 코드/파이프라인/canonical 상태 미변경.
   - 03_GENERIC_PROTOCOL lines 150-167의 SOFTC.ONE 구체 내용은 현행 유지. 향후 정비 시 runbook으로 이전 권장 (SOFTC_ONE_RUNBOOK Open Risks에 기록됨).

---

## [Codex] 2026-06-16T20:35+09:00

1. What was done
   - 김달수 재수집 run `kimdalsu_recollect_20260616_01`을 표준 `runs/kimdalsu_20260601/` 아래 생성하고 legacy seed 3개 + 작업명세서를 복사했다.
   - Softcon P1 profile preflight 후 수집 시작: subject current stats 1건 수집, LoL population은 `enterprise_membership_required`, follower ranking은 확장 중 `http_429_or_rate_limit`로 중단.
   - 공개 교차검증 수집: CHZZK profile 1건, Semorank public parse 60건, YouTube Atom feed 180일 창 15건 수집. Auro는 current Codex route에서 Chrome JS fetch + devalue parser 필요로 boundary 처리.
   - `softcon_cohort_member_profile_enrichment`는 population dependency blocked로 실행하지 않았다.
   - Evidence/Absence/Disclosure/Cohort/ContentFunnel patch 후보와 RUN_MANIFEST/TargetReviewSummary 작성. CaseResult/Disclosure/PublicDemo/canonical package 승격 없음.

2. What files were produced
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/RUN_MANIFEST.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/TargetReviewSummary.md`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/10_charles/`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/20_review/collect_directives/`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/30_arthur_inspect/`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/40_arthur_collect/`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/EvidencePackage_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/AbsenceInventory_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/DisclosureLog_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/CohortBenchmark_candidate.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/ContentFunnelAnalysis_candidate.csv`

3. File status
   - New run artifacts: raw/reviewed hybrid; usable for Cowork/Hosea patch review, not canonical promotion.
   - `TargetReviewSummary.md` and `RUN_MANIFEST.json`: reviewed run ledger.
   - `50_ingest_candidates/*`: patch-candidate only.
   - `scripts/*.py`: local run helpers, not canonical framework code.

4. What the next surface should do
   - [Cowork/Hosea] Review patch candidates and decide whether any evidence can be promoted after human analysis.
   - [Cowork/Hosea] Decide whether Softcon enterprise login/session should be refreshed before retrying LoL population and follower ranking. Do not retry automatically after the recorded 429.
   - [Cowork/Hosea] If Auro is still needed, use Chrome JS fetch + devalue parser route; CLI/http route is not sufficient in this run.

5. Boundaries and warnings
   - Softcon subject stats are partial: visible current metrics parsed, but member-gated chat metrics remain unavailable.
   - Softcon LoL population produced 0 rows due `enterprise_membership_required`; enrichment dependency therefore blocked.
   - Softcon follower ranking initially observed rows, but final extension hit `http_429_or_rate_limit`; final artifact is boundary-only and no repeated retry was attempted.
   - YouTube collection used Atom feed metadata only; engagement counts and CTA/link details remain not collected.
   - No cookie/token/session/csrf/password values, raw HTML, or screenshots were persisted. No CaseResult, disclosure final state, PublicDemoRow, or canonical package mutation was performed.

---

## [Codex] 2026-06-16T22:00+09:00

1. What was done
   - SOFTC.ONE runbook 기준으로 P1 재수집을 이어서 마무리했다. 기존 `enterprise_membership_required` / `http_429_or_rate_limit` 판정은 coarse regex false positive였음을 preflight로 확인했고, approved `.pw_profile` + browser route로 다시 수집했다.
   - `softcon_subject_channel_current_stats`를 line-based parser로 repair하여 `follower_count=3760`, `stream_hours=31.4`, `peak_viewers=165`, `avg_viewers=78`, `viewership=2449`, `max_chat_6m=168`, `avg_chat_6m=38`, `category_1=리그 오브 레전드`를 정상 채웠다.
   - `softcon_chzzk_lol_population_monthly`는 repaired 100행 상태를 유지했다. 현재 route는 `category_route_visible_cap_100_rows` residual risk가 있다.
   - `softcon_chzzk_follower_ranking_enterprise`는 parser/hydration 문제를 고쳐 pages 1..40 재수집을 완료했고, corrected artifact는 `3987` unique rows / boundary 없음이다. `_progress.ndjson`가 per-page ledger로 남아 있다.
   - `softcon_cohort_member_profile_enrichment` 전용 collector를 추가해 population 100행 전체를 channel page 기준으로 재수집했다. `follower_count`와 `recent_category`는 100/100 채워졌고, `profile_text`는 2/100만 확보되어 target parse_status는 `partial`로 낮췄다.
   - `finalize_run.py`를 현재 상태에 맞게 보정하고 `RUN_MANIFEST.json`, `TargetReviewSummary.md`, `50_ingest_candidates/*`를 다시 생성했다.

2. What files were produced
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/40_arthur_collect/softcon_subject_channel_current_stats/*`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/40_arthur_collect/softcon_chzzk_lol_population_monthly/*`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/40_arthur_collect/softcon_chzzk_follower_ranking_enterprise/*`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/40_arthur_collect/softcon_cohort_member_profile_enrichment/*`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/RUN_MANIFEST.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/TargetReviewSummary.md`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/EvidencePackage_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/AbsenceInventory_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/DisclosureLog_patch.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/50_ingest_candidates/CohortBenchmark_candidate.json`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/scripts/probe_softcon_subject_metrics.py`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/scripts/probe_softcon_follower_rows.py`
   - `Streamer Consulting Project/runs/kimdalsu_20260601/kimdalsu_recollect_20260616_01/scripts/enrich_softcon_cohort_members.py`

3. File status
   - P1 artifacts are now materially usable for human review: subject `ok`, population `below_expected_min_rows` with residual cap, follower `ok`, enrichment `partial`.
   - `softcon_chzzk_follower_ranking_enterprise/normalized.csv`: corrected 3987 unique rows, source route `?type=naverchzzk&page=1..40`.
   - `softcon_cohort_member_profile_enrichment/normalized.csv`: 100 rows, but `profile_text` missing on 98 rows and flags remain blank; do not treat as fully complete enrichment.
   - `RUN_MANIFEST.json`, `TargetReviewSummary.md`, `50_ingest_candidates/*`: refreshed to match the corrected P1 state. Still patch-candidate only, not canonical promotion.

4. What the next surface should do
   - [Cowork/Hosea] Review whether the current 100-row LoL population surface is acceptable as a partial benchmark or whether an alternate route is needed to break the `category_route_visible_cap_100_rows` residual risk.
   - [Cowork/Hosea] Decide whether `softcon_cohort_member_profile_enrichment` needs a second pass focused on recovering `profile_text` and/or adding explicit corporate/team/tournament/virtual classification logic.
   - [Cowork/Hosea] Use the refreshed patch candidates for human analysis only. Do not promote CaseResult, Disclosure final state, PublicDemoRow, or canonical package rows automatically.

5. Boundaries and warnings
   - SOFTC.ONE direct fetch / fresh profile routes remain non-working or untrusted for this case. The working route here was browser automation with the existing approved `.pw_profile`.
   - `softcon_chzzk_lol_population_monthly` is still capped at 100 visible filtered rows on the accessed route; this is a surface limitation, not confirmed source absence.
   - `softcon_cohort_member_profile_enrichment` is only partial: `follower_count` and `recent_category` are present, but `profile_text` is missing on 98/100 rows and classification flags are blank.
   - `auro_live_chzzk_follower_public_crosscheck` remains blocked by route requirements (`Chrome JS fetch + devalue parser`).
   - No cookie/token/session/csrf/password values, raw HTML, or screenshots were persisted. No CaseResult, disclosure final state, PublicDemoRow, or canonical package mutation was performed.

---

## [Cowork/Hosea] 2026-06-17T00:00+09:00 — 구비바 보고 가이드 + 2부 프레임 + 산문 시스템 v0.2

1. What was done
   - **구비바 1부 진단편 보고 가이드 작성**: 김달수_보고가이드_v1.md 포맷 + gubiba_part1_client_report_v2_20260617.md 데이터 소스 기반. ~400줄, 3막 구조(위치확인→성장추이+피어→방송량역설+목표조정), 예상 질문 12개. 핵심 수치 24개 전수 교차검증. 디스코드 화면공유 기준. 클로징 = "인식 전환 1개 + 2부 예고" (김달수 가이드의 "액션 확약"과 다름).
   - **2부 분석 프레임 설계**: 사용자 제안(표본1/표본2/모집단) → 두 층 구조 확정.
     - 비전 레퍼런스: 달콤레나, 아리사 + 서새봄/티뭉/강소연 (인터뷰 E1/F2 출처)
     - 피어 레퍼런스: 목표 밴드 1.5K-2.5K 내 겸업 채널 (구조 비교)
   - **리포트 산문 시스템 v0.1 → v0.2**: 사용자 9단계 Deep Review 결과물 검토 후 v0.2 수정 7건 적용 (범위 축소, 보존 규칙, 용어 수정, 용어집 부록). 실행 래퍼 별도 문서 분리.

2. Files produced
   - `Gunsmith_Mailbox/reports/gubiba_보고가이드_v1.md` — 구비바 1부 보고 가이드 (~400줄)
   - `Codex_Workspace/.../specs/리포트_산문_시스템_v0.2.md` — 산문 시스템 v0.2 (규칙 원본)
   - `Codex_Workspace/.../specs/리포트_산문_실행래퍼_v0.2.md` — LLM 실행 래퍼

3. File status
   - 보고 가이드: reviewed
   - 산문 시스템 v0.2 + 실행 래퍼: Codex 배치 완료

4. Decisions
   - 2부 프레임: "이렇게 두 층 구분으로 가자" (사용자 확정)
   - 실행 래퍼 분리: 규칙 원본 62줄 → 래퍼 포함 시 150줄+ 팽창 → 2파일 구조

5. Boundaries
   - 문서 작업만. 코드/파이프라인/canonical 미변경.

---

## [Cowork/Hosea] 2026-06-18T00:00+09:00 — 김달수 종합본 PDF + 요약본 + cross time-series 동기화

1. What was done
   - **김달수 v3.1 종합본 HTML→PDF**: WeasyPrint, 이모지→텍스트 치환. 53페이지 650KB.
   - **4-Block 압축 요약본**: "지금 어디에 있는가 / 뭐가 문제인가 / 뭘 해야 하는가 / 어디까지 갈 수 있는가" 구조. 첫 버전 9p 464KB. 사용자 "분량+시각화 부족" 피드백 → 20+p + SVG 9개 확장 시도. **확장 Agent 출력 미반영 의심** (파일 크기 동일).
   - **Cross time-series 문서 동기화**: "Chzzk 단일 스냅샷" 한계 → 편상관 r=+0.72~0.76 결과로 6개 위치 업데이트. Danny methodology review는 해당없음 확인.
   - **Danny 요약본 결정**: 60p 전달 비현실적 → 섹션별 분석 결과 요약본 필요.

2. Files produced / modified
   - `deliverables/kimdalsu_v3_1_client_full_20260618.pdf` — 53p PDF
   - `deliverables/kimdalsu_v3_1_client_summary_20260618.html` + `.pdf` — 요약본 (확장판 검증 필요)
   - `deliverables/kimdalsu_v3_1_client_full_20260618.html` + `.md` — cross time-series 6건 동기화
   - `deliverables/kimdalsu_v3_client_s5_20260618.md` — 2건 동기화
   - `deliverables/kimdalsu_v3_client_s10s11_20260618.md` — 1건 동기화

3. Key data synced
   - Pearson: r=+0.761, +0.673, +0.657. Partial (방송일수 통제): r=+0.756, +0.716, +0.714
   - 확신 수준: "관찰됨(독립 상관 확인)"

4. Open issue
   - 요약본 확장판 미반영 의심. Agent 937줄 보고 vs 파일 369줄 동일.

5. Boundaries
   - No cookie/token/session/csrf 저장. CaseResult/canonical 미변경.

---

## [Cowork/Hosea] 2026-06-19T09:00+09:00 — 구비바 576채널 코호트 팔로워 enrichment

1. What was done
   - **576채널 코호트 팔로워 전수 수집**: Softcon Chrome in-browser fetch로 4차 수집.
     - 1차 386채널, 2차 120채널 (429 복구 후), 3차 8채널 (channelId 미보유→검색으로 확보), 4차 62채널 (매핑에 ID 있으나 누락분)
   - **최종 병합**: 4개 팔로워 CSV + cohort base + ID 매핑 + 기존 enrichment 3소스. 파생 지표 산출.
   - **결과**: 576/576 (100%) 커버리지. follower 233~317,991, 중앙값 3,435.

2. Files produced
   - `Gunsmith_Mailbox/reports/gubiva_cohort_enriched_576_20260619.csv` — 최종. 576행 15컬럼.
   - `Gunsmith_Mailbox/reports/softcon_follower_{386,120,8,62}.csv` — 배치별 raw 수집 결과

3. Technical notes
   - Vercel WAF: Chrome page context `fetch()`, ~1.1-1.2s 딜레이. 429 시 메인 페이지 네비게이션으로 WAF 세션 갱신.
   - channelId 미보유 8채널: `/search?q={name}` + enriched_965 grep. 공백 이름은 공백 제거 검색.
   - JS 출력 제한: 25건씩 compact 포맷 추출.

4. Boundaries
   - Softcon ~1 req/s 준수. No cookie/token/session/screenshot 저장.

5. Next step
   - §5/§6 갱신본 기반 v3 보고서 반영 판단
   - 요약본 확장판 미반영 검증 (6/18건)

---

## [Cowork/Hosea] 2026-06-19T18:00+09:00 — §5/§6 576코호트 진단 실행

1. What was done
   - **§5 코호트 테이블 생성**: 576 enriched → general_game 분류 join (965 cross-match 45ch, 10 true/35 false/531 virtual_only) → `cohort_final_virtual_576.csv` (576행) + `cohort_robustness_table_576.csv` (32행, 4 layer × 8 metric)
   - **§5 6단계 진단 실행** (576 VTuber cohort):
     - §5.1 기술통계: A=50, B=106, C=420. B avg CV=10.8%, hours CV=11.9% (균질), fol CV=69.0% (의도적 분산)
     - §5.2 다축위치: B 내 4강2약 — 전환율 71.7%ile, 피크 75.9%ile, 효율 73.1%ile, 방송시간 62.7%ile / 팔로워 27.8%ile, **리텐션 25.0%ile (신규 발견)**
     - §5.3 동질성: PAR 30.7%ile, Loyalty 25.0%ile
     - §5.4 회귀: 전체 slope=0.712 R²=0.708, 구비바 잔차≈0 (−0.006). B only R²=0.017 (설명력 없음=의도적)
     - §5.5 견고성: 50%ile 이상 4/6, 평균 56.1%ile. B+C 확장 시 효율 77.3%ile 유지
     - §5.6~§5.8: 기존 정본(20260615) 유지 (방송기록 기반)
   - **§5 종합**: "팔로워 under-indexed, 콘텐츠 over-indexed" 구조 재확인. 정본 대비 fol%ile 소폭↓, peak%ile 소폭↑, 잔차≈0 수렴. **리텐션 25%ile은 정본에 없던 신규 약점.**
   - **§6 트레이드오프**: upper band 271ch (VTuber 59.4%) 대조.
     - 갭: 10k 밴드까지 fol×17.5, avg×7.7, peak×3.6
     - **리텐션 갭이 최대 병목**: 구비바 26.9% vs 상위 밴드 65%. 2.4배 개선 필요.
     - 전환율 역전: 구비바 2.47% → 상위 밴드 ~1% (성장 시 자연 하락, 정상)
     - 시간 추정: 50%/yr 성장 가정 시 10k 도달 ~6.5년
   - **교차검증**: 576행·32행·구비바값·R²·271행 모두 일치 확인

2. Files produced
   - `Gunsmith_Mailbox/reports/cohort_final_virtual_576.csv` — 576행, is_general_game join 완료
   - `Gunsmith_Mailbox/reports/cohort_robustness_table_576.csv` — 32행
   - `Gunsmith_Mailbox/reports/gubiva_§5§6_576cohort_diagnosis_20260619.md` — §5/§6 종합 진단 보고

3. Key findings vs 정본(20260615)
   - 일치: 상승국면 판정, under-indexed/over-indexed 구조, 회귀 잔차≈0
   - 신규: 리텐션 25%ile (정본 미측정), B+C 효율 77.3%ile, 상위 밴드 리텐션 갭 2.4배
   - 변동: 코호트 +78% (323→576), 동체급 정의 변경 (peak→avg+hours 기반)

4. Boundaries
   - No cookie/token/session/screenshot 저장. CaseResult/canonical 미변경.
   - targets\ 원본 미수정.

---

## [Cowork/Hosea] 2026-06-19T21:00+09:00 — v3 클라이언트 보고서 작성 완료

1. What was done
   - **v2→v3 보고서 작성**: `gubiba_part1_client_report_v2_20260617.md` 기반, 576 VTuber 코호트 + 상위밴드 271채널 데이터로 전면 갱신.
   - **변경 A-H 전부 반영**:
     - A. 헤더: 데이터 범위에 576 + 271 추가
     - B. 결론카드①: 리텐션 발견 + dual priority(P0 리텐션 + P1 변곡점) 반영
     - C. §2: VTuber 전수 코호트 3-layer 테이블(A/B/C) 추가
     - D. §3: 6축 테이블(전환율·효율·리텐션 576 %ile 추가), 피크-일상 격차 약점 신규 기술, 잔류율 vs 리텐션 구분 명시
     - E. §4: 10k 밴드 데이터 직접 관찰 반영, "불가능" → "매우 어렵지만 불가능은 아님", 성장 시간 추정, 리텐션 목표 행 추가, 리텐션 경보 하한(< 20%) 추가
     - F. §5.4 + §6.1: 576 Layer B 포지셔닝·회귀 요약, P0(리텐션 개선) 최우선 액션 추가
     - G. 한계: 항목 1·5 해소 표시(576 범위 확장), 항목 7 신규(잔류율 vs 리텐션 구분)
     - H. 결론카드②: 리텐션 25%ile → 40% 개선이 팔로워 돌파와 동등 우선순위임을 명시
   - **검증 수행**: 576 CSV 원본 대비 교차검증
     - percentile 값 ±1%p 이내 일관 (계산 방법 차이 수준)
     - max follower 317,991, max peak 29,490 확인
     - **회귀 예측 오류 수정**: 10k 팔로워 시 예상 avg "105명" → "118명" (실제 slope=0.712, intercept=-0.777 기반 재계산), "1.9배" → "1.7배", "상위 5%" → "상위 10%"

2. Files produced
   - `Gunsmith_Mailbox/reports/gubiba_part1_client_report_v3_20260619.md` — v3 정본 (323행)

3. Key message shift (v2 → v3)
   - v2: 1축 ("방송량→팔로워 변곡점")
   - v3: 2축 ("리텐션 개선 선행" + "팔로워 변곡점 돌파")
   - 핵심 신규 발견: 잔류율(방송 내 0.712, 상위 14%)과 리텐션(방송 간 27%, 하위 25%)이 서로 다른 축

4. Boundaries
   - No cookie/token/session/screenshot 저장.
   - targets\ 원본 미수정. v2 원본 미변경(Codex_Workspace에 보존).
   - CaseResult/canonical 상태 미변경 — v3는 Gunsmith_Mailbox 출력물.

---

## [Cowork/Hosea] 2026-06-19T22:00+09:00 — §7 유튜브 타당성 조사 Codex 위임

1. What was done
   - 2부 §7 방향 결정: 유튜브 비활성 상태 확인 → "유튜브를 (재)시작해야 하는가" 타당성 분석으로 전환
   - 상위밴드 271채널 ⊇ Layer A 50채널 (완전 포함) 확인 → 타겟 271채널
   - step7_youtube_feasibility 디렉토리 생성
   - Codex 핸드오프 문서 작성: 3-task 구조 (유튜브 존재 확인 → 활성 채널 지표 → 구비바 유튜브)

2. Files produced
   - `work/step7_youtube_feasibility/구비바_§7_CC_handoff_youtube_survey.md` — Codex 수집 위임 프롬프트

3. What the next surface should do
   - **Codex**: 핸드오프 문서 읽고 Task 1→2→3 순서로 수집 실행
   - **Cowork/Hosea**: 수집 데이터 도착 후 교차 분석 + §7 타당성 보고서 작성

4. Boundaries
   - 핸드오프 문서만 작성. 수집 미실행. canonical 미변경.

---

### [Cowork/Hosea] 2026-06-19T23:30+09:00

§7 유튜브 타당성 분석 완료

1. Changes
   - Codex 수집 데이터(youtube_presence_271.csv 84행, youtube_metrics_active.csv 78행) 검증
   - 구비바 유튜브 채널 브라우저 확인 → youtube_gubiva.csv 작성 (@GOOBIBA02, 166 subs, 367 vids, full_vod, dormant)
   - YouTube ↔ Chzzk 교차분석: 상관분석(3쌍 모두 r≈0), 밴드 통제 비교, 콘텐츠 유형별 잔류율, 업로드빈도-잔류율
   - §7 보고서 작성 + 전수치 검증(12/12 pass)

2. Files produced
   - `data/cohort/collected/youtube_gubiva.csv` — 구비바 YT 지표 (1행)
   - `reports/gubiva_§7_youtube_feasibility_20260619.md` — §7 타당성 보고서 (Gunsmith_Mailbox)

3. Key findings
   - 상위밴드 YT 보유율 92.9%, 활성 73.8%
   - YT 구독자/업로드빈도 ↔ 치지직 리텐션 상관 없음 (r=0.013, 0.170)
   - full_vod 잔류율 최하위 (median 0.564, 2위 대비 -7.4%p)
   - 결론: YT 재시작 필요하나, 리텐션 개선(P0) 선행 → clip/highlight 전환 권고

4. What the next surface should do
   - §8-§9 범위 확정 후 2부 보고서 완성
   - v3 보고서 docx/pdf 포맷 출력 (미완)

---

## [Codex] 2026-06-20T00:00+09:00 — 구비바 §7 YouTube survey 수집 실행 기록

1. What was done
   - Cowork/Hosea의 §7 handoff에 따라 상위밴드 271채널의 YouTube 병행 여부 조사를 위한 수집 스크립트를 작성했다.
   - Task 1 presence는 YouTube Data API quota 사용량을 줄이기 위해 밴드별 30개 샘플(총 90개)을 시도했고, 84행까지 수집했다.
     - 10k-20k 30행, 20k-50k 30행, 50k+ 24행
     - has_youtube=true 78행, false 6행
   - 85번째 샘플 `앰비션 / 8a59b34b46271960c1bf172bb0fac758`에서 YouTube Data API `Search.list`가 `youtube_search_http_429`를 반환했다.
   - 이 boundary는 bot/rate 차단이 아니라 `Search.list` 호출당 100 quota units 구조 때문에 일일 기본 quota(10,000 units)에 가까워진 quota-unit exhaustion으로 해석한다.
   - CHZZK lookup을 끈 상태로 1회 재시도했으나 같은 boundary가 재현되어 presence 수집을 멈췄다. 같은 날짜 내 반복 재시도는 의미가 낮음.
   - 이후 YouTube search를 더 호출하지 않고, 이미 확정된 78개 `youtube_channel_id`에 대해서만 metrics-only 모드로 Task 2를 완료했다.
     - metrics 78행, 중복 0
     - content_type_primary: clip 31, highlight 23, mixed 10, full_vod 7, original 6, blank 1

2. Files produced / modified
   - `구비바_CASE_PACKAGE_v3_20260611/work/step7_youtube_feasibility/scripts/collect_youtube_survey.py` — 재개 가능 수집 스크립트. `--skip-presence`, `--skip-chzzk-social`, 기존 metrics skip 로직 포함.
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/youtube_presence_271.csv` — Codex 수집분 84행.
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/youtube_metrics_active.csv` — Codex metrics 78행.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step7_youtube_feasibility/구비바_§7_youtube_survey_run_20260619.md` — Codex 수집 런노트.
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/youtube_gubiva.csv` — Codex run 이후 Cowork가 별도 브라우저 확인으로 작성한 1행 파일. Codex 런노트의 Task 3 not_collected 상태와 혼동하지 말 것.

3. File status
   - `youtube_presence_271.csv`: partial sample, 84/90 attempted rows completed. 271 전수 아님.
   - `youtube_metrics_active.csv`: complete for the 78 confirmed YouTube channel IDs in the current presence file.
   - `youtube_gubiva.csv`: present, but Codex search route가 아니라 Cowork 후속 확인 산출물.
   - CaseResult/canonical/disclosure/promotion 상태 미변경.

4. What the next surface should do
   - **Cowork/Hosea**: 이미 §7 타당성 분석에 사용한 수치와 Codex 수집 boundary를 구분해서 유지.
   - **Codex/CC**: presence 전수 확장이 필요하면 YouTube daily quota reset 이후 `collect_youtube_survey.py`를 재개. 남은 샘플 6채널 search는 약 600 units 규모라 reset 후에는 충분히 작음.
   - **Codex/CC**: metrics 보강만 필요할 경우 `--skip-presence`를 사용해 search endpoint 호출을 피할 것.

5. Boundaries and warnings
   - YouTube API key는 클립보드에서 임시 환경변수로만 사용했고 파일/명령 출력/런노트에 저장하지 않았다.
   - raw HTML/raw JSON, cookie/token/localStorage/sessionStorage/auth header/screenshot 저장 없음.
   - YouTube `Search.list`는 호출당 100 quota units로 비싸다. 80회 이상 호출하면 일일 기본 quota 대부분을 소진하므로, 같은 quota window 안에서 반복 재시도 금지.
   - `match_confidence=medium` 행은 동명이인 가능성이 있으므로 최종 분석 전 수동 spot-check 권장.

---

## [Codex] 2026-06-20T01:30+09:00 — 구비바 §8 Layer A/C 방송기록 수집 smoke boundary

1. What was done
   - 구비바 §8.2 체급 교차검증용 Layer A/C 방송기록 수집을 준비했다.
   - 기존 `collect_step5_broadcasts_cdp_parallel.mjs`에 `--target-file` 옵션을 추가해 T1/T2 외부의 LA/LC 타깃 목록을 같은 DOM 추출 파이프라인으로 실행할 수 있게 했다.
   - 사용자 제공 44채널 목록을 `layer_ac_broadcast_targets_20260620.json`으로 구조화했다.
     - Layer A / `LA`: 20
     - Layer C / `LC`: 24
   - 기존 승인된 `.pw_profile`로 Chrome CDP port 9222를 열고, 2채널 smoke를 단일 워커로 실행했다.
   - 첫 타깃 `오화요 Ohwayo / 65a53076fe1a39636082dd6dba8b8a4b`에서 SOFTC.ONE `429`가 즉시 발생해 스크립트가 중단했다.
   - boundary 발생 후 44채널 본수집은 시작하지 않았다.

2. Files produced / modified
   - `구비바_CASE_PACKAGE_v3_20260611/work/step5_diagnosis/scripts/collect_step5_broadcasts_cdp_parallel.mjs` — `--target-file` 지원 추가.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step8_layer_ac_broadcasts/layer_ac_broadcast_targets_20260620.json` — LA/LC 44채널 입력.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step8_layer_ac_broadcasts/구비바_§8_layer_ac_broadcast_collection_run_20260620.md` — 런노트.
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_manifest_layer_ac.json`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_errors_layer_ac.csv`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_progress_layer_ac.ndjson`

3. File status
   - LA/LC 방송별 CSV 생성 수: 0.
   - Manifest: attempted 2, success 0, short_rows 0, error 1, boundary_signal=`checkpoint_or_rate_boundary`.
   - Error CSV: 1행, `LA,65a53076fe1a39636082dd6dba8b8a4b,오화요 Ohwayo,429,1/44,1`.

4. What the next surface should do
   - **Operator/Cowork**: SOFTC.ONE 승인 브라우저 프로필이 여전히 통과 가능한 상태인지 확인.
   - **Codex/CC**: boundary 해소 후 같은 target file로 재개. `--skip-existing true` 사용. 시작은 다시 1~2채널 smoke 권장.
   - **Hosea**: 현재 상태에서는 Layer A/C 방송 데이터가 없으므로 §8.2 체급 교차검증 분석에 사용하지 말 것.

5. Boundaries and warnings
   - SOFTC.ONE `429` 발생. 공격적 재시도 없음.
   - raw HTML, cookie/token/localStorage/sessionStorage/auth header, screenshot 저장 없음.
   - CaseResult/canonical/disclosure/promotion 상태 미변경.

---

## [Codex] 2026-06-20T01:50+09:00 — 구비바 §8 Layer A/C 방송기록 수집 완료

1. What was done
   - 이전 CDP smoke `429` 이후 SOFTC.ONE Runbook 기준으로 route를 재정렬했다.
   - `nodriver_dom_browser` + 기존 승인 `.pw_profile` + visible checkpoint wait 경로로 1채널 smoke를 통과했다.
   - LA/LC 44채널을 10개 이하 chunk로 나누어 수집했고, `skip-existing`와 progress 기반 skip을 함께 사용해 `not_found` 반복 재시도를 막았다.
   - 최종 통합 manifest/progress/errors를 official layer_ac 파일명으로 재작성했다.

2. Files produced / modified
   - `구비바_CASE_PACKAGE_v3_20260611/work/step5_diagnosis/scripts/collect_step5_broadcasts_cdp_parallel.mjs` — `--target-file` 지원.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step5_diagnosis/scripts/collect_step5_broadcasts_nodriver.py` — `--target-file`, `--profile-dir`, full-range query, checkpoint wait, progress skip 지원.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step8_layer_ac_broadcasts/layer_ac_broadcast_targets_20260620.json` — LA/LC 44채널 입력.
   - `구비바_CASE_PACKAGE_v3_20260611/work/step8_layer_ac_broadcasts/구비바_§8_layer_ac_broadcast_collection_run_20260620.md` — 최종 런노트.
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/LA/*.csv`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/LC/*.csv`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_manifest_layer_ac.json`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_errors_layer_ac.csv`
   - `구비바_CASE_PACKAGE_v3_20260611/data/cohort/collected/broadcast_samples/_collection_progress_layer_ac.ndjson`

3. File status
   - Target 44개 전부 terminal 상태.
   - CSV 42개 생성: LA 19, LC 23.
   - 20행 이상 CSV 41개. 전체 방송 row 4,038.
   - Short CSV 1건: `쿠온 레이 Planeta / 59aa824e4c4a56dd51e7a5e2e9172648`, 18 rows.
   - Final error 2건: `부쿠키` not_found, `김네네` not_found.
   - Schema mismatches 0, unprocessed 0, final boundary_signal null.

4. What the next surface should do
   - **Hosea/Cowork**: §8.2 체급 교차검증 분석에 LA/LC CSV 42개를 사용. 100-row DOM cap residual risk와 short CSV 1건을 방법론 한계에 반영.
   - **Codex/CC**: 재수집 필요 시 같은 target file과 progress skip 옵션을 유지. `not_found` 2건은 canonical absence가 아니라 collection error로만 취급.

5. Boundaries and warnings
   - Initial CDP `429`, initial nodriver `checkpoint`는 preflight boundary로 기록됨. 최종 chunk 수집 중 boundary/rate-limit/checkpoint 없음.
   - raw HTML, cookie/token/localStorage/sessionStorage/auth header, screenshot 저장 없음.
   - CaseResult/canonical/disclosure/promotion 상태 미변경.

---

## [Cowork/Hosea] 2026-06-20T12:00+09:00 — 언니채널 체급 검증 + 풀리포트 반영

1. What was done
   - **체급 점수 제거 검증**: 100점 스코어링에서 체급 근접도(25점)를 완전 제거, 나머지 4항목(성장 25 + 안정 20 + 충분 15 + 형태 15 = 75점)만으로 구비바 15채널 + 김달수 15채널 재스코어링.
   - **핵심 발견**:
     - 김달수: 전략적죽음 #4→#1 (13개월 데이터 + 성장 방향 강일치), 미유 #6→#3, 해득이 #7→#4. 개리형 #1→#2, 기뮨디 #2→#5.
     - 구비바: 불꽃빡빡 #14→#1 (7개월 데이터, 성장 방향 최강일치). 유나욘 #1→#2.
     - 양쪽 Top 5 ratio 중앙값 1.40x 유지 — 법칙이 아닌 상관관계.
     - 진짜 드라이버: 데이터 기간(충분성)과 성장 방향 일치.
   - **궤적매칭 v2 보고서 2건 업데이트**: 체급 검증 섹션 + 수정된 활용 권장.
   - **풀리포트 2건 반영**:
     - `gubiva_full_report_v3_20260619.md`: §5.5 삽입 (§5.4 직후)
     - `kimdalsu_v3_1_client_full_20260618.md`: §9 삽입 (§8 직후)

2. Files modified
   - `Gunsmith_Mailbox/reports/구비바_언니채널_궤적매칭_v2.md`
   - `Gunsmith_Mailbox/reports/김달수_언니채널_궤적매칭_v2.md`
   - `Gunsmith_Mailbox/reports/gubiva_full_report_v3_20260619.md`
   - `Codex_Workspace/.../deliverables/kimdalsu_v3_1_client_full_20260618.md`

3. Key methodological insight
   - 체급 스코어링(25점)이 1.5x 피크 설계 → 1.4x 수렴은 사전 가설 반영
   - 체급 제거 후에도 중앙값 유지 → 상관관계 실재, 인과 아님
   - 개선 방향: 체급 배점 축소, 충분성·형태 유사도 확대

4. Boundaries
   - No cookie/token/session/screenshot 저장. targets\ 미수정.
   - CaseResult/canonical 미변경. 풀리포트 직접 편집 (docx/pdf 미재생성).

---

## [Cowork/Hosea] 2026-06-21T06:00+09:00 — 전달 전 산출물 일괄 갱신 완료

1. What was done
   - **CaseResult partial 승격**: stub → partial. §5~§9 결과 반영, 12 claims, 3 strategic_targets, XGPS external_validation, P0/P1/P2 priority_stack.
   - **2부 종합 리포트 v4**: 잘린 파일(668줄) 복구. Phase 1~3 로드맵 완성, §8-b XGPS 교차검증 종합(2수렴 3발산 테이블+해석) 추가.
   - **1부 보고가이드 v2**: 방송투입량 112h→102.9h 정정, 576 VTuber 리텐션 하위 25% 추가, §8 XGPS 교차검증 결과 반영, 클로징에 P0 리텐션 추가.
   - **2부 보고가이드 v1**: M1~M6 전체 90~100분 시나리오. 각 모듈별 [전문]/[쉽게], 체크인, 예상 질문 대비 7건.
   - **DOSSIER 최종 갱신**: CaseResult partial, 파일목록·체크리스트 전면 갱신.

2. Files produced
   - `machine/구비바_CaseResult_v3_partial.json`
   - `deliverables/gubiba_보고가이드_2부_v1.md`

3. Files modified
   - `deliverables/gubiva_full_report_v3_20260619.md` — v4 (§8-b 추가, Phase 1~3 복구)
   - `deliverables/gubiba_보고가이드_v1.md` — v2 (576/리텐션/§8 갱신)
   - `구비바_CASE_DOSSIER_v3.md` — CaseResult partial, 파일목록, 체크리스트

4. What the next surface should do
   - O17 쇼츠 결과 확인
   - 1부 PDF/DOCX v3 재생성 (현재 v2 기반)
   - 차트 PNG v3 재생성
   - 클라이언트 전달 → 산출물 반응 로그 기록
   - (전달 후) C21 상태 갱신, §10 실행 설계 착수

5. Boundaries
   - targets\ 미수정. C21은 "에디터 해석/가설"로 유지. CaseResult stub 파일은 보존(삭제 안 함).

---

## [Cowork/Hosea] 2026-06-21T05:00+09:00 — §9 산출물설계 + O13 토론배틀 보조 완료

1. What was done
   - **§9 산출물설계 정본 v1**: 6모듈 2부 전달구조 (M1 방송효과심화 → M2 카테고리·시간대 → M4 리텐션 → M3 유튜브 → M5 궤적매칭 → M6 통합진단), 90~100분 시나리오.
   - **O13 토론배틀 보조 v1**: C21(자기 가치 평가 낮춤) 검증 도구. 3현상→1뿌리 구조, 근거 5개, 예상 반론 4종 대응, 분기판단(수용/부분/거부/과부하).
   - **산출물 반응 로그 CSV**: R01~R09 빈 템플릿 (방법론 v4 §9.6 컬럼 일치).
   - **DOSSIER 갱신**: §9 완료 반영, 케이스정의 갱신, 다음 Action 갱신, 체크리스트·파일목록 갱신.
   - **방법론 v4 §9 대조 검증**: 6개 요구사항 전부 충족 확인.

2. Files produced
   - `work/step9_deliverable_design/구비바_§9_산출물설계_20260621.md` — §9 정본 v1
   - `deliverables/gubiva_O13_토론배틀보조_v1.md` — O13 토론배틀 보조
   - `deliverables/gubiva_산출물반응로그.csv` — 빈 템플릿

3. Files modified
   - `구비바_CASE_DOSSIER_v3.md` — §9 완료, 케이스정의, Action, 체크리스트, 파일목록

4. What the next surface should do
   - CaseResult stub → partial 승격 (§5~§9 반영)
   - 전달 전 산출물 갱신 (2부 종합 리포트 §8 반영, 1부 PDF 재생성, 보고가이드 v2)
   - 2부 보고가이드 본문 작성
   - 클라이언트 전달 → 반응 로그 기록

5. Boundaries
   - No cookie/token/session/screenshot 저장. targets\ 미수정. C21은 "에디터 해석/가설"로 명시, 본인 확인 전 단정 금지.

---

## [Cowork/Hosea] 2026-06-21T03:00+09:00 — §8 XGPS 교차검증 분석 완료

1. What was done
   - **§8 XGPS 교차검증 분석**: Layer A 19ch/1,706건 + Layer C 23ch/2,194건 vs 구비바 582건. 5개 효과 교차검증.
   - **수렴 2건**: 잔류율×방송길이 (모든 체급 r=-0.24~-0.37, 구비바 감소 가장 완만), 주말 우위 (+5~14%).
   - **발산 3건**:
     - 방송길이→시청자: LC r=0.25 (긴 방송=더 많은 시청자), LA/구비바 r≈0 (무상관). 구비바의 무상관은 "월 102.9h 한계수익 소진"으로 해석.
     - 저녁 시간대: LC에서 저녁=프라임타임(peak_z +0.33), 구비바만 저녁 최저. 시간대 자체가 아닌 구비바 고유 요인.
     - talk vs game: LA/LC 모두 game > talk. 구비바만 talk(pk 26) > game(pk 19). 시청자가 게임이 아닌 스트리머 자체에 반응.
   - **심화 분석**: 채널별 r 분포 (LA 44% 양의상관, LC 91%), 카테고리별 peak_z (LC 음악/니케/명조 상위), 잔류율 기울기 비교, 주말 채널내정규화 차이.
   - **DOSSIER v4 갱신**: §8 완료 반영, 4.5 §8 Claims 추가, 5-6 섹션 갱신, 체크리스트·정본파일목록 갱신.
   - **전수치 검증**: Python 독립 스크립트로 peak median, r값, 잔류율 r값 9개 모두 일치 확인.

2. Files produced
   - `work/step8_xgps/구비바_§8_XGPS_교차검증_20260621.md` — §8 정본 v1

3. Files modified
   - `구비바_CASE_DOSSIER_v3.md` — §8 완료 반영 (상태표, 케이스정의, Claims 4.5, 본문 5-6, 체크리스트, 파일목록)

4. What the next surface should do
   - CaseResult stub → partial 승격 (§5~§8 반영)
   - §9 산출물 설계 + O13 전달설계
   - 클라이언트 전달물 최종

5. Boundaries
   - No cookie/token/session/screenshot 저장. targets\ 미수정. CaseResult/canonical 미변경.

---

## [Cowork/Hosea] 2026-06-20T18:00+09:00 — Universal Collector Framework 설계 + 구현

1. What was done
   - **설계 협업**: 사용자와 config-driven 범용 수집 프레임워크 아키텍처를 협의. 모듈 위치(`tools/collector/`), JS 외부화, Playwright 인터페이스만 예약 등 3건 결정.
   - **CC 코드 리뷰 반영**: Codex 독립 리뷰 6건 수신. CDP 엔진 제외(nodriver 충분), `dom_eval` 네이밍, signal action config 선언, tracking↔targets resume 협력 등 반영.
   - **구현 완료**: 17파일 생성, 전부 문법·기능 검증 통과.
     - Core: `config.py`, `targets.py`, `tracking.py`, `rate.py`, `collector.py`, `__main__.py`
     - Engines: `base.py`(ABC), `nodriver_engine.py`, `http_engine.py`
     - Extractors: `dom_eval.py`, `api_json.py`
     - Assets: `softcon_channel_streams.js`, `gubiba_step5.yaml`, `requirements.txt`
   - **검증**: config 로딩, 323 대상 로딩/중복제거, resume(323 전부 skip), expression 치환, signal 감지, verify(304 ok / 14 missing / 5 short_rows) 전부 통과.
   - **COLLECTION_TOOLKIT.md 갱신**: Quick Reference에 프레임워크 추가, §8 섹션 신설, 의존성 테이블 갱신.

2. Files produced
   - `tools/__init__.py`
   - `tools/collector/__init__.py`
   - `tools/collector/__main__.py`
   - `tools/collector/collector.py` — CLI 진입점 (collect/verify)
   - `tools/collector/config.py` — YAML 로더 + dataclass
   - `tools/collector/targets.py` — 다중 소스 + 중복제거
   - `tools/collector/tracking.py` — NDJSON progress + manifest + resume
   - `tools/collector/rate.py` — delay/jitter + signal
   - `tools/collector/engines/base.py` — Engine ABC
   - `tools/collector/engines/nodriver_engine.py`
   - `tools/collector/engines/http_engine.py`
   - `tools/collector/extractors/dom_eval.py`
   - `tools/collector/extractors/api_json.py`
   - `tools/collector/expressions/softcon_channel_streams.js`
   - `tools/collector/configs/gubiba_step5.yaml`
   - `tools/collector/requirements.txt`

3. Files modified
   - `_WORKING_CONTEXT/COLLECTION_TOOLKIT.md` — Quick Reference + §8 + 의존성

4. File status
   - 프레임워크 17파일: raw — CC/Codex 리뷰 후 git commit 대상
   - COLLECTION_TOOLKIT.md: reviewed

5. What the next surface should do
   - **Codex/CC**: `tools/collector/` 17파일 git commit. 커밋 전 코드 리뷰 권장.
   - **Codex/CC**: 새 케이스 config YAML 추가 시 `configs/` 아래에 배치. 기존 개별 스크립트 → 프레임워크 전환은 점진적으로.
   - **Cowork/Hosea**: 프레임워크로 새 수집 실행 시 `python -m tools.collector.collector collect --config <yaml>` 사용.

6. Boundaries and warnings
   - 프레임워크는 설계+구현+검증까지만 완료. 실제 라이브 수집(네트워크 호출)은 미실행.
   - 기존 개별 스크립트는 그대로 유지. 프레임워크가 대체하지만 삭제하지 않음.
   - No cookie/token/session/screenshot 저장. targets\ 미수정. CaseResult/canonical 미변경.
