# SOFTC.ONE Runbook

Last verified: 2026-06-16
Status: active
Scope: 스트리머 코호트 수집 (§4 enrichment, §5 broadcast history, §6 upper reference band)

## Quick Read

- Vercel WAF가 TLS/H2 fingerprint + JS challenge로 HTTP 클라이언트를 전부 차단함. 진짜 브라우저만 통과.
- 안정 경로: operator-approved 브라우저 프로필 + Playwright persistent context 또는 nodriver.
- 피해야 할 경로: curl_cffi, CDP headless, Playwright cookies → HTTP client 전달, fresh nodriver profile — 전부 실패 검증됨.
- 총 요청률 ~1 req/s 유지. 향후 제휴 가능성 고려하여 보수적 속도 유지.

## Working Routes

| Route | Status | Use For | Notes |
|---|---|---|---|
| Playwright persistent context (async, multi-tab) | **working** | §4 enrichment, §5 broadcast | pw_enrich.py — 965/965 완료 실적. asyncio.Queue 기반 워커 패턴. |
| Browser DOM row extraction | **working** | §5 broadcast records | canonical streams path에서 DOM 직접 추출. CSV 다운로드보다 안정적. |
| nodriver + existing approved profile | **working** | §6 upper reference band | collect_upper_band_reference_nodriver.py — 687/687 후보 detail 완료, 271행 채택. fresh profile은 checkpoint 도달(실패). |
| UI CSV 다운로드 버튼 | **opportunistic** | — | framework/user-gesture 이슈로 자동화 불안정. DOM extraction 우선. |

## URL / Data Surfaces

| Surface | Pattern | Data | Caveat |
|---|---|---|---|
| 채널 상세 | `/channel/{platform}/{channelId}` | 프로필, 시계열(peak/avg/airTime) | RSC payload로 structured data 포함 |
| 방송 기록 | `/channel/{platform}/{channelId}/streams` | 방송 리스트, 날짜/시간/시청자 | 기본 윈도우는 최근 ~1개월. full-range는 명시적 query 필수. |
| 카테고리 랭킹 | `/category/{game}/ranking` | 랭킹 테이블 (CSV 2000행 제한) | DL_037에서 일반 랭킹 → 카테고리 랭킹 전환 |
| 팔로워 랭킹 | `/ranking/followers?platform={platform}` | 팔로워 순 전체 랭킹 | §6에서 상위 참조밴드(10k+) 후보 스캔에 사용 |
| 일반 랭킹 | `/ranking` | 상위 400ch | 카테고리 랭킹보다 범위 좁음 |

## Failure Modes

| Signal | Meaning | Action |
|---|---|---|
| HTTP 429 + `x-vercel-mitigated: challenge` | Vercel WAF rate limit / TLS fingerprint 탐지 | 즉시 중단. 속도 낮추거나 브라우저 경로로 전환. |
| Checkpoint page (JS challenge) | Vercel bot detection | 브라우저 세션에서 1회 해결. HTTP client로는 통과 불가. |
| DOM 100-row cap | `/streams` 페이지 표시 상한 | extraction-cap residual risk. 데이터 부재 증거 아님. |
| 429 loop after ~1.5 req/s | 서버 rate limit 임계값 | 탭 수 × 딜레이 조합으로 총 요청률 ~1 req/s 이하 유지. |

## Collection Defaults

- **속도**: 총 요청률 ~1 req/s. 탭 수 늘리면 딜레이 비례 증가. (DL_040)
- **동시성**: 멀티탭 — 3탭×3초 또는 6탭×6초 안정 실측. (DL_039)
- **Step5 full-range**: 반드시 `?startDateTime={iso}&endDateTime={iso}` 명시. 기본 윈도우 가정 금지. (DL_045)
- **scale ladder**: 소규모 single-worker → 점진적 concurrency/delay 변경. rung별 별도 manifest/progress/error. (DL_045)
- **resume**: `skipExisting` before `limit` — smoke가 이미 수집된 것이 아닌 다음 미수집 대상을 커버하도록. (DL_045)
- **long run**: progress NDJSON + per-item CSV/notes flush 필수.
- **secret/raw 금지**: 쿠키, localStorage, session token, auth header, raw HTML, screenshot 값 저장 금지. 브라우저 프로필은 memory-only 사용.

## Related Decisions

| Decision ID | Date | Summary |
|---|---|---|
| DL_TOOLING_20260615_045 | 2026-06-15 | Step5 full-range browser collection protocol |
| DL_CONTEXT_20260615_041 | 2026-06-15 | SOFTC.ONE 제휴 고려 수집 정책 (~1 req/s) |
| DL_TOOLING_20260615_040 | 2026-06-15 | Rate limit 경계 실측 및 속도 튜닝 |
| DL_TOOLING_20260615_039 | 2026-06-15 | pw_enrich.py 멀티탭 async 병렬화 |
| DL_TOOLING_20260615_038 | 2026-06-15 | Vercel WAF 우회 경로 확정: Playwright 유일 작동 |
| DL_INFRA_20260614_037 | 2026-06-14 | ExecutionProtocol 범용/케이스 분리 + 카테고리 랭킹 소스 전환 |
| DL_TOOLING_20260612_017 | 2026-06-12 | Arthur ephemeral cookie bridge policy |
| DL_TOOLING_20260611_016 | 2026-06-11 | Charles browser probe contract promotion |

## Proven Runs

| Date | Case/Step | Result | Artifact |
|---|---|---|---|
| 2026-06-15 | 구비바 §4 enrichment | 965/965 완료, 5679 JSONL join | `data/cohort/collected/gubiba_*_enriched_965.csv`, `*_pw_enriched.jsonl` |
| 2026-06-15 | 구비바 §5 full-range probe | full-range query 검증, DOM 100-row cap 확인 | `data/cohort/collected/broadcast_samples/_date_query_probe.json` |
| 2026-06-15 | 구비바 §5 scale ladder | 6 workers, 6s delay — checkpoint/rate boundary 미발생 | `구비바_§5_SOFTCONE_full_range_collection_run_20260615.md` |
| 2026-06-16 | 구비바 §6 upper reference band | nodriver + existing profile, 687/687 후보 detail 완료, 271행 채택 | `cohort_ref_upper_band.csv`, `구비바_§6_upper_reference_band_collection_run_20260616.md` |

## Open Risks

- **DOM 100-row extraction cap**: `/streams` 페이지에서 한 번에 100개만 표시. 100건 초과 방송 기록 수집 시 pagination 또는 date windowing 필요. 현재 미검증.
- **tls-client WAF 우회 미테스트**: tls-client, got-scraping, patchright, botright, camoufox 5개 스택 테스트 예정이나 미진행. 성공 시 Playwright 대체 가능. 검증된 실패 경로 4개는 DL_038 참조.
- **nodriver fresh profile 실패**: nodriver + fresh profile은 checkpoint 도달(§6 실측). nodriver + existing approved profile(.pw_profile)은 §6에서 687/687 후보 detail 완료. fresh profile 경로는 사용하지 말 것.
- **03_GENERIC_PROTOCOL 내용 중복**: `03_STREAMER_CASE_GENERIC_PROTOCOL.md` lines 150-167에 SOFTC.ONE Step5 구체 내용이 있음. 향후 generic protocol 정비 시 사이트 특화 내용을 이 runbook으로 이전하고 원칙만 남기는 것 권장.
- **.pw_profile 삭제됨 (2026-06-20)**: gitignored로 복구 불가. nodriver 스크립트는 프로필 없이 작동하므로 영향 없음. Playwright 경로 복원 시 재생성 필요.

## See Also

- `_WORKING_CONTEXT/COLLECTION_TOOLKIT.md` — 전체 수집 인프라 인벤토리 (스크립트 30개, 프로필, 도구, 매니페스트)
