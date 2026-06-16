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
