# Collection Toolkit Inventory

Last updated: 2026-06-20 (framework 추가)
Status: active

이 문서는 Streamer Consulting 프로젝트의 수집 인프라 전체 인벤토리다. 새 세션은 수집 작업 전에 이 문서를 읽고, 어떤 도구가 어디에 있고, 지금 무엇이 작동하는지 파악한 뒤 시작할 것.

---

## Quick Reference — 지금 뭘 쓰면 되나?

| 용도 | 추천 경로 | 상태 |
|---|---|---|
| **범용 배치 수집 (신규 권장)** | **`tools/collector/`** — `python -m tools.collector.collector collect --config <yaml>` | **working** — 323 대상 검증 완료, config-driven |
| SOFTC.ONE 배치 수집 (§5 방송기록 등) | **nodriver** — `collect_step5_broadcasts_nodriver.py` | **working** — 44/44 대상 중 41 성공, 429 0회 |
| SOFTC.ONE enrichment (§4 코호트) | Playwright persistent — `pw_enrich.py` | **프로필 필요** — `.pw_profile` 삭제됨, 재생성 시 사용 가능 |
| SOFTC.ONE upper band (§6) | nodriver — `collect_upper_band_reference_nodriver.py` | **working** — 687/687 완료 실적 |
| YouTube 데이터 | HTTP API — `collect_youtube_survey.py` | **working** — API key 기반, WAF 무관 |
| 단건 진단/탐색 | Chrome MCP | **working** — ~1 req/s 직렬, 탐색·확인용 |
| Arthur 자동 수집 | Arthur MCP (`collect_data`) | **조건부** — softcon은 프로필 필요 (`softcon_fallback_user_data`) |

---

## 1. 수집 경로별 WAF 통과 메커니즘

### nodriver (추천)
- 실제 Chrome 바이너리 사용 + `navigator.webdriver` 등 자동화 흔적 자체 제거
- **프로필 불필요** — Chrome 자체 fingerprint로 Vercel WAF 통과
- 프로브 3/3 성공 (6/16), 배치 41/44 성공 (6/20), 429/checkpoint 0회
- 설치: `pip install nodriver` (버전 미고정, 0.50.3 검증)

### Playwright persistent context
- Chromium 바이너리 + 사전 승인된 프로필 디렉토리 필요
- `.pw_profile`에 WAF 통과 세션 상태가 저장되어야 작동
- §4 enrichment 965/965 완료, §5 6워커×6초 309/323 완료 실적
- **현재 불가** — `.pw_profile` 삭제됨 (gitignored, 복구 불가)
- 복원 방법: Playwright visible 모드로 softcon 접속 → checkpoint 1회 통과 → 프로필 저장

### Chrome MCP
- 사용자 실제 Chrome 세션을 Cowork/Codex가 리모트 조종
- WAF 100% 통과 (진짜 사람 브라우저)
- **직렬 전용, ~1 req/s** — 배치 수집에는 부적합, 탐색·단건 확인용

### HTTP 클라이언트 (curl_cffi, tls_client, requests, urllib)
- Vercel WAF TLS fingerprint 단계에서 **100% 차단**
- SOFTC.ONE에는 절대 사용 불가. YouTube API 등 WAF 없는 대상에만 사용.

### Arthur MCP
- `collect_data` / `inspect_data` 도구로 호출
- 내부적으로 Playwright persistent context 사용 (`_fetch_with_chrome_profile`)
- softcon 수집 시 `softcon_fallback_user_data` 프로필 + 승인된 CollectDirective 필요
- 프로필 상태: `operator_approved_pending_manual_bootstrap` — 아직 수동 부트스트랩 안 됨

---

## 2. 스크립트 인벤토리

모든 경로는 `D:\Codex_Workspace\Streamer Consulting Project\` 기준 상대경로.

### 구비바 — step4 (코호트 수집/enrichment)

| 스크립트 | 도구 | 용도 | 프로필 |
|---|---|---|---|
| `구비바.../work/step4_.../scripts/pw_enrich.py` | Playwright | §4 enrichment, asyncio.Queue 멀티탭 | `.pw_profile` **(삭제됨)** |
| `구비바.../work/step4_.../scripts/cdp_cookie_bridge.py` | Raw CDP + curl_cffi | 쿠키 브릿지 실험 | 임시 |
| `구비바.../work/step4_.../scripts/playwright_cookie_bridge.py` | Playwright | 쿠키 브릿지 실험 | 임시 |
| `구비바.../work/step4_.../scripts/read_chrome_cookies.py` | sqlite3 + DPAPI | 시스템 Chrome 쿠키 읽기 | 시스템 Chrome |
| `구비바.../work/step4_.../scripts/test_cookie_bridge.py` | curl_cffi | 쿠키 브릿지 테스트 | 없음 |
| `구비바.../work/step4_.../scripts/verify_cohort_v2.js` | Node.js | 코호트 검증 | 없음 |
| `구비바.../work/step4_.../scripts/enrich_from_ids.js` | Node.js fetch | HTTP enrichment | 없음 |
| `구비바.../work/step4_.../scripts/collect_30d_browser.js` | 브라우저 콘솔 | 수동 30일 수집 | 기존 브라우저 세션 |

### 구비바 — step5 (방송 기록 수집)

| 스크립트 | 도구 | 용도 | 프로필 | 상태 |
|---|---|---|---|---|
| `구비바.../work/step5_.../scripts/collect_step5_broadcasts_nodriver.py` | **nodriver** | §5 방송기록 DOM 추출 | `.pw_profile` (기본값, 없어도 작동) | **주력** |
| `구비바.../work/step5_.../scripts/step5_nodriver_probe.py` | nodriver | WAF 프로브 | nodriver 자체 관리 | 프로브 전용 |
| `구비바.../work/step5_.../scripts/collect_step5_broadcasts.py` | tls_client | TLS 우회 시도 | 없음 | **실패 — WAF 차단** |
| `구비바.../work/step5_.../scripts/step5_tls_waf_probe.py` | tls_client | TLS WAF 프로브 | 없음 | 프로브 전용 |
| `구비바.../work/step5_.../scripts/verify_step5_broadcasts.py` | 순수 Python | CSV 검증 | 없음 | 유틸 |

### 구비바 — step6 (상위 참조 밴드)

| 스크립트 | 도구 | 프로필 | 상태 |
|---|---|---|---|
| `구비바.../work/step6_.../scripts/collect_upper_band_reference_nodriver.py` | **nodriver** | `.pw_profile` | 687/687 완료 |
| `구비바.../work/step6_.../scripts/probe_upper_band_followers_nodriver.py` | nodriver | `.pw_profile` | 프로브 전용 |

### 구비바 — step7 (YouTube)

| 스크립트 | 도구 | 상태 |
|---|---|---|
| `구비바.../work/step7_.../scripts/collect_youtube_survey.py` | urllib (YouTube Data API) | working |

### 구비바 — unni_channel

| 스크립트 | 도구 | 프로필 | 상태 |
|---|---|---|---|
| `구비바.../work/unni_channel/collect_unni_trajectories.py` | **nodriver** | `.pw_profile` (기본값, CLI 오버라이드 가능) | working |

### 김달수 — 데이터

| 스크립트 | 도구 | 상태 |
|---|---|---|
| `김달수.../data/youtube_collect_dalsooisfree.py` | requests (YouTube API) | working |

### 김달수 — recollect run (runs/)

| 스크립트 | 도구 | 프로필 |
|---|---|---|
| `runs/.../scripts/probe_softcon_p1_preflight.py` | nodriver | `--profile-dir` (필수 인자) |
| `runs/.../scripts/probe_softcon_category_surface.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/probe_softcon_category_windows.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/collect_softcon_p1.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/repair_softcon_category.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/probe_softcon_subject_metrics.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/probe_softcon_follower_rows.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/repair_softcon_subject_followers.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/enrich_softcon_cohort_members.py` | nodriver | `--profile-dir` (필수) |
| `runs/.../scripts/collect_public_targets.py` | urllib | 없음 |
| `runs/.../scripts/repair_youtube_feed.py` | urllib | 없음 |
| `runs/.../scripts/finalize_run.py` | 순수 Python | 없음 |

---

## 3. 브라우저 프로필

### Profile A — `softcon_fallback_user_data` (현존)

- **경로**: `runs/kimdalsu_20260601/recollect_20260611_prep/00_inputs/local_chrome_profiles/softcon_fallback_user_data/`
- **크기**: 77MB
- **내용**: 완전한 Chrome user-data-dir (Default/, Local State, Cookies, Preferences, Extensions, History)
- **참조**: Arthur 설정 JSON 4개, kimdalsu recollect 스크립트 (--profile-dir)
- **상태**: `operator_approved_pending_manual_bootstrap` — 수동으로 Chrome을 이 프로필로 열어 softcon 접속 후 checkpoint 통과 필요
- **gitignored**: 예 — git 복구 불가

### Profile B — `.pw_profile` (삭제됨)

- **경로**: `구비바.../work/step4_cohort_collect_prep/.pw_profile/`
- **참조**: pw_enrich.py, collect_step5_broadcasts_nodriver.py (기본값), collect_upper_band_reference_nodriver.py, probe_upper_band_followers_nodriver.py, collect_unni_trajectories.py
- **상태**: **삭제됨, 복구 불가** (gitignored)
- **복원 방법**: Playwright visible 모드로 softcon.one 접속 → JS challenge 통과 → 프로필 자동 저장
- **영향**: nodriver 스크립트는 이 프로필 없이도 작동 (nodriver 자체 WAF 우회). Playwright 스크립트만 영향.

### Profile C — 시스템 Chrome (외부)

- **경로**: `C:\Users\faust\AppData\Local\Google\Chrome\User Data`
- **참조**: `softcon_chrome_profile_fallback.local.json`, `read_chrome_cookies.py`
- **상태**: 사용자 실제 Chrome — 직접 사용하지 않음, Arthur 초기 폴백 용도

---

## 4. 설정 파일

### Arthur Chrome 프로필 설정

모두 `runs/kimdalsu_20260601/recollect_20260611_prep/00_inputs/`에 위치.

| 파일 | 대상 프로필 | 상태 |
|---|---|---|
| `softcon_chrome_profile_fallback.local.json` | 시스템 Chrome (Default) | `operator_approved` |
| `softcon_chrome_profile_fallback.non_default.local.json` | `softcon_fallback_user_data` | `pending_manual_bootstrap` |
| `...visible_diagnostic.local.json` | 위와 동일 + headed Chrome | `visible_diagnostic` |
| `...visible_networkidle.local.json` | 위와 동일 + networkidle wait | `visible_networkidle_diagnostic` |

### Arthur ExecutionProtocol

| 파일 | 위치 |
|---|---|
| `Arthur_ExecutionProtocol_v3.json` | `구비바.../machine/`, `구비바.../data/cohort/specs/` |
| `구비바_Arthur_ExecutionProtocol_v2_TEMPLATE_20260610.json` | `구비바.../data/cohort/specs/` |
| `구비바_Arthur_ExecutionProtocol_v2_FILLED_20260614.json` | 동일 |

---

## 5. 의존성

개별 스크립트는 lazy import. 프레임워크는 `tools/collector/requirements.txt` 참조.

| 패키지 | 버전 | 사용처 | 비고 |
|---|---|---|---|
| nodriver | ≥0.50 (0.50.3 검증) | 프레임워크 + 개별 14개 | 주력 수집 도구. pip install nodriver |
| pyyaml | ≥6.0 | 프레임워크 전용 | YAML config 파싱 |
| playwright | 미고정 | 개별 2개 | .pw_profile 필요. pip install playwright && playwright install |
| tls_client | 미고정 | 개별 2개 | WAF 프로브 전용, 실제 수집 실패 |
| curl_cffi | 미고정 | 개별 1~3개 | Chrome TLS impersonation, WAF 실패 |
| requests | 미고정 | 개별 2개 | YouTube API 등 WAF 없는 대상 |
| Python | 3.12 | 전체 | cpython-312.pyc 확인 |

---

## 6. 수집 실적 요약 (매니페스트 기반)

### §4 Enrichment — Playwright
- 965/965 완료, 5679 JSONL join (6/15)

### §5 Broadcast — CDP parallel
- 323 대상 중 309 성공 (6/15), 6워커×6초
- 14개 `not_found` (채널 비존재)

### §5 Layer AC — nodriver
- 44 대상 중 41 성공 (6/20), 순차 chunk 방식
- 429/checkpoint 0회

### §6 Upper Band — nodriver
- 687 후보 detail 완료, 271행 채택 (6/16)

---

## 7. Rate Limit 기준

| 경로 | 안정 실측값 | 비고 |
|---|---|---|
| §4 Playwright 멀티탭 | 3탭×3초, 6탭×6초 | §4 enrichment 한정 |
| §5 CDP parallel | 6워커×6초 | §5 본체 실적, 이후 2-worker 429 발생 |
| §5 nodriver 순차 | 채널당 ~12초 + delay ~10초 | layer_ac 실적, 429 0회 |
| 전체 도메인 정책 | ~1 req/s 총합 | DL_040, 제휴 고려 보수적 |

---

## 8. Universal Collector Framework — `tools/collector/`

기존 30+ 개별 스크립트를 대체하는 config-driven 범용 수집 프레임워크. YAML 설정 파일 하나로 대상·URL·엔진·추출·속도·재개·시그널을 모두 선언한다.

### 구조

```
tools/collector/
├── __init__.py, __main__.py     # 패키지 + python -m 진입점
├── collector.py                 # CLI (collect / verify 서브커맨드)
├── config.py                    # YAML 로더 + dataclass
├── targets.py                   # 다중 소스 로딩 + 중복제거
├── tracking.py                  # NDJSON progress + manifest + resume
├── rate.py                      # delay/jitter + signal 감지
├── engines/
│   ├── base.py                  # Engine ABC (start/navigate/evaluate/stop)
│   ├── nodriver_engine.py       # nodriver — WAF bypass, 프로필 불필요
│   └── http_engine.py           # urllib 기반 HTTP/JSON
├── extractors/
│   ├── dom_eval.py              # JS 평가 → CSV
│   └── api_json.py              # HTTP JSON 정규화
├── expressions/
│   └── softcon_channel_streams.js  # §5 DOM 추출 JS (외부 파일)
├── configs/
│   └── gubiba_step5.yaml        # 구비바 §5 방송기록 설정
└── requirements.txt             # nodriver>=0.50, pyyaml>=6.0
```

### 사용법

```bash
# 수집
python -m tools.collector.collector collect --config tools/collector/configs/gubiba_step5.yaml

# 부분 수집 (offset/limit)
python -m tools.collector.collector collect --config ... --offset 100 --limit 50

# 검증
python -m tools.collector.collector verify --config tools/collector/configs/gubiba_step5.yaml
```

### 설계 원칙

- **Config-driven**: 새 수집은 YAML 파일 하나만 추가. 코드 수정 불필요.
- **Engine 추상화**: nodriver(주력, WAF bypass) / http(API 전용). Playwright는 인터페이스만 예약.
- **Extractor 분리**: `dom_eval`(JS 표현식 → CSV), `api_json`(HTTP JSON). JS 로직은 `.js` 파일로 외부화.
- **Resume-safe**: `skip_existing`(출력 파일 체크) + `skip_progress`(NDJSON 기록 체크) 이중 레이어.
- **Signal 기반 제어**: config에 regex 패턴 + action(abort/skip) 선언. checkpoint→abort, not_found→skip 등.
- **CC 코드 리뷰 반영**: CDP 엔진 제외(nodriver 충분), `dom_eval` 네이밍, signal action 선언, tracking↔targets resume 협력.

### 검증 실적

- config 로딩: YAML → dataclass 정상
- 323 대상 로딩/중복제거: T1 109 + T2 272 → 323 unique
- resume: 323/323 skip (기존 수집분)
- expression 치환: `{CHANNEL_ID}` → 실제 ID
- signal 감지: checkpoint/rate_limit/not_found 정규식 매칭
- verify: 304 ok, 14 missing, 5 short_rows

### 기존 스크립트 → 프레임워크 전환 가이드

1. 기존 스크립트의 URL 패턴, DOM 추출 JS, 시그널 조건 파악
2. `configs/` 아래 YAML 작성 (gubiba_step5.yaml 참조)
3. DOM 추출 로직은 `expressions/` 아래 `.js` 파일로 분리
4. `python -m tools.collector.collector collect --config <yaml>`로 실행
5. `verify` 서브커맨드로 결과 검증

---

## Related Documents

- `site_runbooks/SOFTC_ONE_RUNBOOK.md` — WAF 상세, failure modes, proven runs
- `02_TOOL_CONTRACTS_Charles_Arthur.md` — Arthur/Charles 도구 계약
- `07_DECISION_LOG.md` — DL_038 (WAF 우회 경로 확정), DL_039 (멀티탭 병렬화), DL_040 (rate limit), DL_045 (Step5 protocol)
- `SESSION_NOTE.md` — 최근 세션 핸드오프
