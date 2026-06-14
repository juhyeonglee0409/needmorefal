# Decision Log

## 2026-06-14 - Hosea 운용 아키텍처 정의: 표면 재구조화 + Workspace 이원화

decision_id: `DL_INFRA_20260614_035`

scope:

- `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md`
- `D:\Codex_Workspace\Instruction\INFRA_ARCHITECTURE_PLAN_v3_1.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\01_SOURCE_MAP.md`
- `D:\Codex_Workspace\_CODEX_SESSION_START.md`

what_changed:

### 1. Hosea 운용 표면 재구조화 (5표면 나열 → 3계층)

기존: CLI, Codex, Cowork(Mailbox), Cowork(Box), Claude 채팅 — 역할 겹침, 확장 시 표면 수 증가.

변경:

```
Hosea = 인간 + 표면 3개

├─ CLI (코드)
│    ├─ Codex      → 구현/실행 (코드 생성, 테스트, git push)
│    └─ Claude Code → 리뷰/설계/위임 명세
│
├─ Cowork (메인 오케스트레이터)
│    ├─ Gunsmith_Mailbox       → 프로젝트 스테이징 (산출물 임시 → CLI가 배치)
│    ├─ Claude in Chrome    → 브라우저 인터랙티브 (DOM 수집, 프로토콜 생성)
│    └─ Claude 채팅         → 리서치, 전략, 해석
│
└─ Workspace (저장)
     ├─ Codex_Workspace         → git → GitHub (코드/스펙/케이스)
     └─ Claude_Code_Workspace   → 로컬 전용 (대용량 리소스, memory)
```

새 표면 추가 시 하위 노드로 편입. 최상위 3계층 불변.

### 2. 표면별 역할 및 바운더리

#### CLI (코드)

| 노드 | 역할 | 바운더리 |
|---|---|---|
| Codex | 구현, 테스트 실행, git push, 패키지 빌드 | 명세 받은 것만 구현. 스스로 scope 확장 안 함. 승인 권한 없음. |
| Claude Code | 리뷰, 설계, 위임 명세 작성, 상태 진단 | 읽기 중심. Codex_Workspace 직접 쓰기는 문서/정책만. 코드 구현은 Codex에 위임. |

CLI 공통: 전략 결정 안 함 (Cowork 소관). 데이터 수집 안 함. approved=true, canonical mutation, disclosure decision 권한 없음.

#### Cowork (메인 오케스트레이터)

| 노드 | 역할 | 바운더리 |
|---|---|---|
| Gunsmith_Mailbox | 프로젝트 산출물 스테이징, 다중 세션 종합, 인계 | 임시 저장소. CLI가 Codex_Workspace 내 프로젝트 경로에 배치 후 커밋. 장기 보관 안 함. |
| Claude in Chrome | 브라우저 DOM 직접 접근, 단건 수집, 사이트 구조 탐색, 프로토콜 생성 | 인터랙티브 단건만. 배치/스케줄 수집 안 함. 로그인/인증 페이지 접근 시 operator 판단. |
| Claude 채팅 | 리서치, 전략 논의, 해석, 설계, 문서 초안 | 파일시스템 직접 접근 없음. 산출물 반영 시 CLI를 거침. |

Cowork 공통: 추천은 하되 승인은 인간만. CollectDirective.approved=true 자동 생성 안 함. not_verifiable → pass/success 전환 안 함. CaseResult/DisclosureLog/PublicDemoRow 자동 승격 안 함. 수집 결과는 CollectionResult 스키마 준수.

#### Workspace (저장)

| 노드 | 역할 | 바운더리 |
|---|---|---|
| Codex_Workspace | git → GitHub. 코드, 스펙, 테스트, 정책, 케이스 패키지 | 100MB 초과 파일 금지. 크롬 프로필/영상/대형 덤프 저장 안 함. |
| Claude_Code_Workspace | 로컬 전용. 대용량 리소스, Hosea 수집 원본, memory | GitHub 백업 없음. git 추적 안 함. 코드/스펙 저장 안 함. |

Workspace 공통: 저장 규칙만 정의. 실행 로직 없음. Codex_Workspace에서 Claude_Code_Workspace 자산은 경로 참조(포인터)만. git 커밋 권한은 CLI 계층(Codex/Claude Code)만. Cowork 산출물은 Gunsmith_Mailbox에 임시 저장 → CLI가 Codex_Workspace 내 해당 프로젝트 경로에 배치 후 커밋. 대용량 리소스는 Claude_Code_Workspace에 배치 (git 미추적).

### 3. 전 표면 불변 규칙

```
어떤 표면을 쓰든:
  - 최종 판단 권한은 인간
  - operator 승인 없이 canonical mutation 없음
  - not_verifiable 세탁 금지
  - Charles/Arthur 내부 오케스트레이션에 외부 개입 안 함
  - 수집 방식(인터랙티브/배치) 무관하게 후단 스키마 계약 동일
```

### 4. 수집 이원화

| 방식 | 도구 | 용도 |
|---|---|---|
| 인터랙티브 | Claude in Chrome (Cowork) | 단건 분석, 사이트 구조 탐색, 프로토콜 생성 |
| 배치 | Arthur (CLI) | 무인 정기 수집, 대량 처리 |

인터랙티브 수집 결과 → ExecutionProtocol 스키마 변환 → Arthur 배치 입력. 후단 파이프라인(Pearson → Susan → Bridge) 불변.

### 5. Hosea 수집 산출물 저장 규칙

Gunsmith_Mailbox는 프로젝트 산출물 스테이징. Orchestrator_Box는 비프로젝트성 퍼스널 산출물 보관.

```
Cowork 산출물 흐름:
  프로젝트 산출물 → Gunsmith_Mailbox (임시)
    → CLI가 Codex_Workspace 내 해당 프로젝트 경로에 배치 후 커밋
    → 대용량 리소스는 Claude_Code_Workspace에 배치 (git 미추적)
  비프로젝트 퍼스널 산출물 → Orchestrator_Box (보관)
```

### 6. Workspace 이원화 정책

| 항목 | Codex_Workspace | Claude_Code_Workspace |
|---|---|---|
| 백업 | GitHub (remote) | 로컬 only (필요시 외장) |
| 내용 | 코드, 스펙, 테스트, 정책, 케이스 패키지 | 대용량 리소스, Hosea 수집 원본, memory |
| git | 추적 | 미추적 |
| 소유자 | CodexSandboxOffline | faust |
| 접근 | Codex + Claude Code(읽기) | Claude Code + 수동 |

why:

기존 표면 나열은 Claude in Chrome, 신규 workspace 등 추가될 때마다 목록이 늘어나는 구조였다. 역할 기준 3계층(CLI/Cowork/Workspace)으로 재구조화하면 확장에 안정적이고, workspace 이원화로 git 추적 자산과 대용량 로컬 자산의 경계가 명확해진다.

authority:

operator 2026-06-14.

boundary:

문서 구조 변경만. 코드, 런타임 동작, 파이프라인 스키마, 승인/게이트 규칙 미변경. Pearson/Susan/Bridge 계약 불변. Charles/Arthur 내부 오케스트레이션 불변.

status: active

## 2026-06-14 - I3 Full Chain End-to-End Integration Test

decision_id: `DL_TOOLING_20260614_034`

scope:

- `D:\Codex_Workspace\IsaacInfra\integration\pearson_susan_v0_1\tests\test_i3_full_chain_smoke.py`

what_changed:

Added I3 full chain integration test: CollectionResult → Pearson store → StorageReceipt → Susan QA → QAReport → PatchCandidate Adapter → Bridge plan (dry-run). 12 tests covering schema compatibility at each handoff, source immutability, and not_verifiable preservation through the entire chain.

why:

Individual tools (Pearson P0-P8, Susan S0-S8, Adapter, Bridge) were implemented and unit-tested, but no test verified that their schemas actually connect end-to-end. I3 closes the integration gap and confirms canonical lifecycle wiring readiness.

authority:

operator 2026-06-14.

boundary:

Offline synthetic fixtures only. Bridge apply not executed (plan/dry-run only). No canonical case package mutation. No live access.

status: active

## 2026-06-14 - Natural Interaction v2: WindMouse + Fitts (DLG-012)

decision_id: `DL_TOOLING_20260614_033`

scope:

- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\natural_mouse.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\inspect.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\tests\test_natural_interaction_v2.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_012_NATURAL_INTERACTION_V2_20260614.md`

what_changed:

Replaced DLG-010's fixed-coordinate `_natural_interaction_step` with WindMouse curved path generation + Fitts's Law timing + seeded variable scroll/poll intervals. New module `natural_mouse.py` (128 lines, pure Python, no external dependencies). Seeded via `random.Random`, deterministic for testing, variable across seeds. Interaction cap 8 and navigation==1 unchanged. SPEC updated.

why:

DLG-010 구현은 고정 좌표 4개 순환 + 고정 스크롤 + 고정 타이밍으로 패턴 fingerprinting에 즉시 식별 가능했다. WindMouse 물리 모델로 곡선 경로와 자연 가감속을 확보하면서 seed 결정론으로 테스트 재현성을 유지했다.

authority:

operator 2026-06-14.

boundary:

Offline implementation/tests only. No navigation/reload/retry added. No external packages. No live access. No canonical case/package mutation.

status: active

## 2026-06-13 - Session Behavior Contract Added

decision_id: `DL_CONTEXT_20260613_032`

scope:

- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\11_SESSION_BEHAVIOR_CONTRACT.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`

what_changed:

Added `11_SESSION_BEHAVIOR_CONTRACT.md` as the required post-README behavior contract for implementation sessions, and updated the working-context README load order/file-role table.

why:

Prevent future sessions from reintroducing DLG-002/008/010 technique-name moralization or overcautious policy drift. The contract keeps sessions aligned to operator scope, harm-based boundary judgment, and existing approval/no-laundering gates.

authority:

operator approved saving the rewritten contract on 2026-06-13.

boundary:

Working-context documentation only. No code, live access, Charles/Arthur run, profile/session access, package install, or case/package canonical mutation.

status: active

## 2026-06-13 - Harm-Based Boundary Normalization Cleanup (DLG-011)

decision_id: `DL_TOOLING_20260613_031`

scope:

- `D:\Codex_Workspace\Instruction\BOT_DEFENSE_OPERATIONAL_ROUTING_v0_2.md`
- `D:\Codex_Workspace\Instruction\delegation\DELEGATION_FENCE_v0_1.md`
- `D:\Codex_Workspace\Instruction\delegation\handoffs\DELEGATION_BRIEF_FENCE_B4_B5_HARDENING_20260613.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_000_MINOR_HARDENING_20260613.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_002_FENCE_B4_B5_HARDENING_20260613.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_008_UNIVERSAL_CHALLENGE_ROUTING_20260613.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_010_NATURAL_INTERACTION_20260613.md`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\AGENTS.md`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\README.md`
- Arthur runtime/user-facing notes and related tests under `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\`

what_changed:

Normalized DLG-002/008/010 wording away from technique-name prohibitions such as solver/stealth/proxy/bypass/VPN/fingerprint as moral blacklines. Replacement wording follows `boundary_black_area_guide_v2_3_diversed.md` §2.3/§4: public-data checkpoint/CAPTCHA/bot-defense handling is judged by harm, operator-approved scope, politeness, sequential access, no overload, and retreat-on-block. STOP/escalate language is reserved for overload, aggressive retry after block/429/challenge, deception/abuse infrastructure, private/login-gated/account-data access outside lawful scope, or secret persistence.

why:

Future sessions were beginning to inherit DLG-002/008/010 as technique-based safety doctrine. The canonical boundary is harm-based, not tool-name-based. This cleanup preserves implementation behavior while removing policy contamination.

authority:

operator 2026-06-13 (DLG-011 full normalization request).

boundary:

Documentation, historical DLG wording, user-facing notes, and test expectation strings only. `boundary_black_area_guide_v2_3_diversed.md` unchanged. Arthur bounded wait/cooldown/exact-scope/no-secret/canonical-mutation gates remain. No live access, Charles/Arthur run, profile/session access, package install, or case/package canonical mutation. Bridge/Pearson/Susan approval and no-laundering guards unchanged.

status: active

## 2026-06-13 - Arthur challenge wait natural interaction (DLG-010)

decision_id: `DL_TOOLING_20260613_030`

scope:

- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\inspect.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\tests\test_natural_interaction_v0_1.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- `D:\Codex_Workspace\Instruction\BOT_DEFENSE_OPERATIONAL_ROUTING_v0_2.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_010_NATURAL_INTERACTION_20260613.md`

what_changed:

Arthur chrome_profile challenge wait에 bounded same-page interaction을 추가했다. Passive checkpoint 관측 시 같은 페이지 안에서 deterministic mouse move, light scroll, focus 신호를 보낸다. 현재 route는 host-agnostic이며, 추가 navigation/reload/retry, automated human-check handling, external routing, host/site branch는 이번 구현 범위에 포함하지 않았다.

why:

DLG-008은 rendered-state polling만 고정해 대기 중 일반 사용자 같은 same-page behavior가 없었다. DLG-010은 같은 navigation 안에서만 bounded interaction을 추가해 current route의 재현성을 높였다.

authority:

operator 2026-06-13 (DLG-010 natural interaction execution approved).

boundary:

Offline implementation/tests only. No overload, aggressive retry, private/login-gated/account-data access, secret persistence, host/site branch, or canonical case/package mutation introduced. Live access was not part of this implementation/test pass; future live access follows the harm-based operational routing policy.

status: active
## 2026-06-13 - Bridge v0.1 patch-candidate apply contract (DLG-009)

decision_id: `DL_TOOLING_20260613_029`

scope:

- `D:\Codex_Workspace\IsaacInfra\Bridge\v0.1\bridge_apply_contract\`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_009_BRIDGE_APPLY_20260613.md`

what_changed:

Bridge v0.1을 신규 추가했다. `bridge plan`은 R2.5 adapter output과 operator approval JSON을 검증하고 dry-run preview만 출력한다. `bridge apply`는 approval 검증 통과 시 EvidencePackage `source_items` append, AbsenceInventory `absence_items` append 또는 empty no-op, 신규 DisclosureLog 파일 생성, backup, ApplyReceipt 생성을 수행한다.

why:

DLG-003에서 닫은 envelope-to-canonical draft gap 다음 단계로, proposed PatchCandidate를 operator-gated case package mutation lifecycle에 연결하는 최소 Bridge 계약이 필요했다.

authority:

operator 2026-06-13 (DLG-009 Bridge v0.1 execution approved).

boundary:

오프라인 구현/테스트만. 실제 canonical case package 실파일은 테스트에서 읽기 전용 참조만 했고 mutation은 임시 복사본에서만 수행했다. approval 없는 mutation은 STOP. operator-only 필드는 approval JSON 값만 사용. Pearson/Susan/Charles/Arthur 코드, `_tmp\i2`, CaseResult, PortfolioRow, PublicDemoRow 미변경. Live access was not part of this offline Bridge implementation/test pass.

status: active

## 2026-06-13 - 정본 추가: Isaac_Gunsmith_FULL_EN_revised git 등록 (DLG-009 0단계)

decision_id: `DL_TOOLING_20260613_028`

scope: `Instruction\Isaac_Gunsmith_FULL_EN_revised.md` (git baseline 누락분 등록)

what_changed: DLG-004 베이스라인에서 untracked로 남았던 설계철학 정본을 git에 등록.

why: 정본 문서가 git 안전망 밖에 있는 위험 제거.

authority: operator 2026-06-13.

boundary: 파일 내용 미변경. 등록만.

status: active

## 2026-06-13 - Arthur universal challenge/throttle/cooldown routing (DLG-008)

decision_id: `DL_TOOLING_20260613_027`

scope:

- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\inspect.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\collect_chrome_profile.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\fetcher.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\arthur\cli.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\tests\test_universal_challenge_pass_v0_1.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\tests\test_universal_path_v0_1.py`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- `D:\Codex_Workspace\Instruction\BOT_DEFENSE_OPERATIONAL_ROUTING_v0_2.md`

what_changed:

Arthur chrome_profile path에 host-agnostic non-interactive checkpoint wait, same-host min interval stop, and HTTP 429/unresolved-checkpoint host cooldown을 추가했다. Interactive CAPTCHA는 current route에서 자동 진행하지 않고 operator manual decision boundary로 기록한다.

why:

Softcon inspect/collect parity 문제를 site-specific route가 아니라 host-agnostic, polite, bounded current route로 좁힌다. Same-route bounded wait, no aggressive retry, and no raw/secret/screenshot storage are fixed by code and tests.

authority:

operator 2026-06-13 (DLG-008 implementation request).

boundary:

Implementation/tests were offline for this work item; that is not a general live-request ban. Operational live access follows `BOT_DEFENSE_OPERATIONAL_ROUTING_v0_2.md` and operator-approved scope. No overload, aggressive retry, private/login-gated/account-data access, secret persistence, or canonical case/package mutation introduced.

status: active
## 2026-06-13 - Softcon Chrome Profile Cache Slim (DLG-007)

decision_id: `DL_TOOLING_20260613_026`

scope:

- recycled (Windows 휴지통) under `...\local_chrome_profiles\softcon_fallback_user_data\`: Default\Cache(60M), Default\Code Cache(15M), optimization_guide_model_store(43M), ko-3-0.bdic(11M), GPU/shader caches, en-US dict (~138M)

what_changed:

크롬 프로필의 재생성 캐시만 휴지통으로 이동. 세션(Network\Cookies, Local Storage, Login Data, Preferences, Web Data, Local State)은 보존. 프로필 143MB → ~5MB.

why:

Softcon parity 작업 추진 결정에 따라 프로필은 유지하되, parity와 무관한 캐시 ~138MB 회수. "캐시 비우기 하되 로그인 유지"와 동일. git 미추적이라 휴지통이 안전망.

authority:

operator 2026-06-13 (Softcon parity 추진 + 프로필 슬림).

boundary:

세션·정본·코드 미변경. git 미추적 자산만. 휴지통(복구 가능).

status: active

## 2026-06-13 - Legacy preflight_v0_4 cache cleanup (DLG-006)

decision_id: `DL_TOOLING_20260613_025`

scope:

- recycled (Windows 휴지통) under `IsaacInfra\_inbox\legacy_tools\preflight_v0_4_dev\`: `.codex_deps`(202M), `.mypy_cache`(15M), `.ruff_cache`, `dist`, `__pycache__` (~218M)

what_changed:

레거시 도구 preflight_v0_4의 재생성 가능 캐시/벤더 패키지를 휴지통으로 이동(영구삭제 아님, 복구 가능). 전부 git 미추적이라 추적 파일 수 불변(1529).

why:

~218MB 공간 회수. 현행 파이프라인 미사용(현행 Charles=v0.10.1). 공개 PyPI 패키지라 재설치 가능. git 백업 불가라 휴지통을 안전망으로 사용.

regeneration:

필요시 `preflight_v0_4_dev`에서 `pip install -r requirements.txt -r requirements-llm.txt`(원래 벤더 절차대로, 예: `--target .codex_deps`). .mypy_cache/.ruff_cache/dist/__pycache__는 빌드/검사 시 자동 재생성.

authority:

operator 2026-06-13 (휴지통 + 옆 캐시 포함).

boundary:

소스코드·정본·코드동작 미변경. git 미추적 자산만. 휴지통 이동(복구 가능). 다른 레거시 도구 미변경.

status: active

## 2026-06-13 - SPEC Alias Dedup (Charles/Arthur) (DLG-005)

decision_id: `DL_TOOLING_20260613_024`

scope:

- deleted: `IsaacInfra\Charles\current\CrawlScouter_v0.10.0_pipeline_contract\SPEC_v0.10.1.md`, `IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0.6.1.md`
- edited: Charles README, Arthur README, `IsaacInfra\README.md`, `_WORKING_CONTEXT\01_SOURCE_MAP.md`

what_changed:

호환용 SPEC 별칭(사본) 2개 제거, 정본만 유지. 별칭 안내문을 4개 문서에서 제거/tombstone. Charles 별칭은 정본과 바이트동일했음. Arthur 별칭은 DL_022 수정이 정본에만 들어가 1줄 stale였음(정본이 올바름).

why:

이중관리가 DL_022에서 alias 미동기화 사고를 냄 → 단일 정본 통합. IsaacInfra\README cleanup 조건 충족(head 참조검증: 활성 참조 0, 안내문만).

authority:

operator 2026-06-13 (선택지 A).

boundary:

정본 내용 미변경. git history로 복원 가능. 코드/도구/케이스 canonical 데이터 미변경.

status: active

## 2026-06-13 - Local Git Baseline (DLG-004)

decision_id: `DL_TOOLING_20260613_023`

scope:

- `D:\Codex_Workspace` (git init, root .gitignore, 첫 커밋 cde6166)

what_changed:

로컬 전용 git 착공. root .gitignore(런타임캐시/크롬프로필 실데이터/_tmp/.codex_deps/embedded repo 제외) + 베이스라인 커밋 cde6166 (추적 1530 파일).

why:

이후 삭제·정리의 되돌리기 안전망. 추적 파일만 보호되며 gitignored 자산(.codex_deps·크롬프로필)은 미보호.

authority:

operator 2026-06-13 (PROPOSAL-001 승인).

boundary:

remote/push/글로벌 config 없음. 파일 이동·삭제 없음. embedded repo는 ignore 처리(디스크·nested .git 보존).

status: active

## 2026-06-13 - PROPOSAL-002 Git-Pre Document Consistency Cleanup

decision_id: `DL_TOOLING_20260613_022`

scope:

- `D:\Codex_Workspace\Streamer Consulting Project\AGENTS.md`
- `D:\Codex_Workspace\Instruction\delegation\DELEGATION_FENCE_v0_1.md`
- `D:\Codex_Workspace\_CODEX_SESSION_START.md`
- `D:\Codex_Workspace\Instruction\INFRA_ARCHITECTURE_PLAN_v3_1.md`
- `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\05_DECISION_SUPPORT_PROTOCOL.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`

what_changed:

Git 전 문서정합 청소 — (A) 봇방어 정책을 work-boundary guide harm-based로 정렬(AGENTS §70 + fence B5; DLG-002의 기존 B5 문안 대체), (B) Pearson/Susan "미구현" stale 문구를 "구현·테스트됨, 미배선"으로 정정(ND/BEARING은 미구현 유지).

why:

첫 git 커밋 전 canonical 문서를 정합 상태로. boundary guide가 봇방어 정본.

authority:

operator 2026-06-13.

boundary:

문서 문구만. 코드/도구 동작/케이스 canonical 데이터 미변경. 삭제 없음. 새 권한은 "공개데이터 polite 통과(운영자승인)"로 한정. ND/BEARING 상태 불변.

status: active

## 2026-06-13 - R2.5 PatchCandidate Adapter (DLG-003)

decision_id: `DL_TOOLING_20260613_021`

scope:

- `D:\Codex_Workspace\IsaacInfra\integration\pearson_susan_v0_1\patch_candidate_adapter.py`
- `D:\Codex_Workspace\IsaacInfra\integration\pearson_susan_v0_1\tests\test_r2_5_patch_candidate_adapter.py`
- `D:\Codex_Workspace\Instruction\delegation\README.md`

what_changed:

Added the R2.5 patch-candidate adapter `build_proposed_payloads(receipt_path, qa_report_path, case_id)` producing `proposed_canonical_payload` for EvidencePackage/AbsenceInventory/DisclosureLog with operator-only fields (final_tag/decision/reviewed_at/reviewer) null, plus a fixture test (20 PASS / 0 FAIL). Head review (Claude Code) = PASS, re-ran independently.

why:

Close the envelope->canonical-draft gap (R1 Evidence/Patch cell) at minimal scope; candidates become canonical-mappable without applying.

authority:

Operator approved DLG-003 execution; head review accepted 2026-06-13.

boundary:

Offline adapter + test only. No canonical mutation, no apply/accept/promote, no CaseResult/PortfolioRow/PublicDemoRow. not_verifiable preserved. DEFERRED P3: move DisclosureLog `case_id` from `proposed_canonical_payload` to the wrapper (DisclosureLog schema has no case_id) — fold into future Bridge graduation, not now.

status: active

Append durable decisions here so future sessions do not reconstruct them from long source files.

## 2026-06-13 - DLG-001 I2 Real-Artifact Offline Smoke

decision_id: `DL_TOOLING_20260613_020`

scope:

- `D:\Codex_Workspace\Instruction\delegation\handoffs\DELEGATION_BRIEF_I2_REAL_ARTIFACT_OFFLINE_20260613.md`
- `D:\Codex_Workspace\_tmp\i2\store\`
- `D:\Codex_Workspace\Instruction\delegation\README.md`
- `D:\Codex_Workspace\Instruction\delegation\reports\DELEGATION_REPORT_DLG_001_I2_REAL_ARTIFACT_OFFLINE_20260613.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`

what_changed:

Executed DLG-001 / I2 real-artifact offline smoke after R3 GO WITH PRECONDITIONS and operator approval. Ran the existing I1 Pearson/Susan regression, stored the one CHZZK CollectionResult through Pearson under the workspace-local short scratch root, generated a Susan QAReport, wrote three interim proposed patch candidates, and recorded the DLG-001 report. Updated the delegation index row for DLG-001 to `accepted`.

why:

The infrastructure needed to prove the Pearson -> Susan path on a real Arthur CollectionResult while preserving `not_verifiable`, source hashes, absence state, boundary signals, and `stored_not_promoted` without canonical mutation.

authority:

Operator approved DLG-001 execution after R3 gate readiness result `GO WITH PRECONDITIONS` on 2026-06-13.

boundary:

- Offline only.
- Store root refined to `D:\Codex_Workspace\_tmp\i2\store\` by R3 precondition.
- No live web access.
- No Charles run.
- No Arthur inspect or collect.
- No profile/session access.
- No package install.
- No CollectDirective creation or approval.
- No CaseResult, DisclosureLog, PublicDemoRow, final deliverable, or package canonical mutation.
- No protected-file edits.
- Patch candidates are interim, proposed-only, and marked `interim_pending_R2_PATCH_CANDIDATE`.

status: active

## 2026-06-13 - Delegation Fence B4/B5 Hardening

decision_id: `DL_TOOLING_20260613_019`

scope:

- `D:\Codex_Workspace\Instruction\delegation\DELEGATION_FENCE_v0_1.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`

what_changed:

Hardened fence B4 wording. Superseded B5 note: the earlier technique-name prohibition is replaced by PROPOSAL-002/DLG-011 harm-based handling. Credential/cookie handling remains exact-scope, memory-only where approved, and secret values remain non-persistent.

why:

Head review found B4 needed clearer operator-gated wording. B5 was later normalized: fence strictness is measured against boundary guide §2.3/§4, where harm is the line rather than technique names.

authority:

Operator approved the fence hardening patch on 2026-06-13.

boundary:

Fence wording only. No canonical case/package mutation. No new data-integrity relaxation. DLG-001/I2 not executed. No protected-file (AGENTS.md/10/README) edits.

status: active
## 2026-06-13 - Code To Codex Delegation Interface

decision_id: `DL_TOOLING_20260613_018`

scope:

- `D:\Codex_Workspace\Instruction\delegation\`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\05_DECISION_SUPPORT_PROTOCOL.md`
- `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\07_DECISION_LOG.md`

what_changed:

Created the D-ladder Code-to-Codex delegation interface with protocol, fence, brief template, report template, README, DLG-001 I2 real-artifact offline brief, and DLG-000 canonicalization report. Added a one-line pointer from `05_DECISION_SUPPORT_PROTOCOL.md` to the delegation fence.

why:

The infrastructure now needs a repeatable way for Claude Code/head review to issue bounded work orders to Codex/hands execution without creating a parallel source of truth, widening scope, or silently crossing approval boundaries.

authority:

User/operator explicitly instructed Codex to proceed with canonicalizing option 2 from `D:\Codex_Workspace\Instruction\CODEX_DELEGATION_INTERFACE_PROPOSAL_20260613.md`.

boundary:

- No live web access.
- No Charles run.
- No Arthur inspect or collect.
- No DLG-001 execution.
- No CollectDirective creation or approval.
- No CaseResult, DisclosureLog, PublicDemoRow, final deliverable, or package canonical mutation.
- No protected-file edits to `AGENTS.md`, `_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.md`, or `_WORKING_CONTEXT/README.md`; future pointers require explicit operator approval.

status: active

## 2026-06-12 - Arthur Ephemeral Cookie Bridge Policy

decision_id: `DL_TOOLING_20260612_017`

scope:

```text
_WORKING_CONTEXT/PATCH_CANDIDATES/arthur_ephemeral_cookie_bridge_policy_applied_20260612.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.ko.md
_WORKING_CONTEXT/02_TOOL_CONTRACTS_Charles_Arthur.md
AGENTS.md
```

what_changed:

```text
Promoted the Arthur ephemeral cookie bridge policy into active operating policy.
Created an applied patch-candidate record and updated the workflow, Korean translation, Charles/Arthur contract summary, and project AGENTS instructions.
```

why:

```text
Arthur may need to perform the same approved browser-session work the operator would otherwise do manually. The policy permits same-origin, memory-only session delegation while continuing to block durable token/cookie value storage, bulk cookie export, direct Chrome cookie database reads, and cross-origin forwarding.
```

authority:

```text
User explicitly instructed promotion from candidate to active operating policy on 2026-06-12.
```

boundary:

```text
This is an operating policy update only. It does not approve any live Softcon collect, CollectDirective.approved=true, CollectionResult promotion, CaseResult promotion, DisclosureLog change, PublicDemoRow creation, or package canonical mutation.
Implementation must still be reviewed/tested separately before use.
```

status: active

## 2026-06-11 - Charles Browser Probe Contract Promotion

decision_id: `DL_TOOLING_20260611_016`

decision:

```text
Promote Charles v0.10.0 browser_probe from temporary patch to the active diagnostic contract, with safety gates for artifact storage.
```

rationale:

```text
manual_review/restricted protocols need a bounded browser visibility diagnostic before operator review. The probe improves boundary classification while preserving scope, access, rate, and artifact-storage boundaries. Artifact storage must remain explicit and must not preserve profile/session raw HTML or screenshots.
```

implementation:

```text
Updated IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract README/release notes and _WORKING_CONTEXT/02_TOOL_CONTRACTS_Charles_Arthur.md. browser_probe artifacts require --save-raw; raw HTML and screenshots are suppressed in profile/session contexts; URL query values are redacted in browser_probe report/protocol fields.
```

boundary:

```text
This is a Charles diagnostic contract decision only. It does not approve Softcon collection, Arthur inspect/collect, CollectDirective creation, CaseResult promotion, DisclosureLog changes, PublicDemoRow creation, or package canonical mutation.
```

status: active

## 2026-06-11 - Context Strategy

decision_id: `DL_CONTEXT_20260611_001`

decision:

```text
Use a small working context layer instead of raw-loading long project docs.
```

rationale:

```text
Reading source files directly consumed too much context. Future sessions should read root bootstrap and project working context first, then use targeted source lookup.
```

source_paths:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\
```

status: active

## 2026-06-11 - User-CLI Workflow v1.1 Patch Candidate

decision_id: `DL_CONTEXT_20260611_014`

scope:

```text
_WORKING_CONTEXT/PATCH_CANDIDATES/10_USER_CLI_WORKFLOW_v1_1_proposed_20260611.md
```

what_changed:

```text
Created a proposed v1.1 patch candidate for 10_USER_CLI_WORKFLOW.md from the external review, without replacing the canonical workflow file.
```

why:

```text
The external review added useful operating controls: document precedence, protected files, resume SESSION_NOTE loading, patch status transition rules, decision log definition, session note update rules, and self-check fields.
The candidate was merged with current project policy rather than copied verbatim.
```

authority:

```text
User requested review and preparation for applying the external revision.
```

boundary:

```text
Canonical 10_USER_CLI_WORKFLOW.md and 10_USER_CLI_WORKFLOW.ko.md were not replaced.
The proposed candidate corrects the decision log location to _WORKING_CONTEXT/07_DECISION_LOG.md, preserves the existing guest/session token policy, and adds AGENTS.md as a protected project-wide instruction file.
```

status: active; candidate status changed to `applied` by `DL_CONTEXT_20260611_015`

## 2026-06-11 - User-CLI Workflow v1.1 Applied

decision_id: `DL_CONTEXT_20260611_015`

scope:

```text
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.ko.md
_WORKING_CONTEXT/PATCH_CANDIDATES/10_USER_CLI_WORKFLOW_v1_1_proposed_20260611.md
```

what_changed:

```text
Applied the v1.1 User-CLI workflow candidate as the active canonical workflow and synced the Korean translation.
Changed the patch candidate status from proposed to applied.
```

why:

```text
The user explicitly approved applying the v1.1 candidate.
The applied version formalizes document precedence, protected files, resume SESSION_NOTE loading, task-context budget framing, ScoutReport handling, working-context mutation rules, patch status transitions, decision log requirements, session note update rules, and end-of-session self-check additions.
```

authority:

```text
User/operator explicit approval: "1.1 후보 적용 승인할게."
```

boundary:

```text
This is a workflow-document update only. No CaseResult, DisclosureLog, PublicDemoRow, CollectDirective, InspectResult, CollectionResult, or case package canonical data was changed.
```

status: active

## 2026-06-11 - Guest Session Token Handling Policy

decision_id: `DL_CONTEXT_20260611_013`

decision:

```text
Promote guest/session token handling into project policy: operator-approved guest/session profiles may be used, but token values must not be pasted, logged, stored in artifacts, committed, or preserved in raw outputs by default.
```

rationale:

```text
Guest/session tokens may be operationally useful for approved browser/profile diagnostics, but reusable access values should not become durable project artifacts. The policy separates allowed local use from forbidden value disclosure/storage.
```

implementation:

```text
Updated AGENTS.md, 10_USER_CLI_WORKFLOW.md, and 10_USER_CLI_WORKFLOW.ko.md.
```

status: active

## 2026-06-11 - Workflow Header Wording Sync

decision_id: `DL_CONTEXT_20260611_012`

decision:

```text
Simplify the opening wording of 10_USER_CLI_WORKFLOW.md and 10_USER_CLI_WORKFLOW.ko.md by removing explicit external-audit contrast and named reference-case examples from the header.
```

rationale:

```text
The workflow document should state its operating purpose directly without carrying unnecessary contrastive or case-specific wording in the header.
```

implementation:

```text
Updated 10_USER_CLI_WORKFLOW.md and 10_USER_CLI_WORKFLOW.ko.md.
```

status: active

## 2026-06-11 - Korean Translation For User-CLI Workflow

decision_id: `DL_CONTEXT_20260611_011`

decision:

```text
Add a Korean translation of the solo User-CLI workflow document while keeping 10_USER_CLI_WORKFLOW.md as the source workflow file.
```

rationale:

```text
The operating workflow is intended for Korean-language user review and future session handoff. A Korean translation reduces interpretation overhead while preserving the existing file as the source reference.
```

implementation:

```text
Added 10_USER_CLI_WORKFLOW.ko.md and linked it from _WORKING_CONTEXT/README.md.
```

status: active

## 2026-06-11 - User-CLI Workflow Stability Patch

decision_id: `DL_CONTEXT_20260611_010`

decision:

```text
Apply the final solo User-CLI workflow review patch: clarify Hosea as a process role, add reference role exclusivity, define session note locations, add patch candidate status values, define the intent-alignment gate, and strengthen end-of-session checks.
```

rationale:

```text
The workflow document was already usable, but these rules reduce context duplication, prevent scattered handoff notes, and make patch candidate and collect-gate state easier to resume in later sessions.
```

implementation:

```text
Updated 10_USER_CLI_WORKFLOW.md.
```

status: active

## 2026-06-11 - Replace External Audit Framing With User-CLI Workflow

decision_id: `DL_CONTEXT_20260611_009`

decision:

```text
Replace 10_EXTERNAL_AUDIT_PROCESS.md with 10_USER_CLI_WORKFLOW.md and treat the document as a lightweight solo user + CLI/Codex workflow, not an external audit protocol.
```

rationale:

```text
The project currently needs faster session startup, context efficiency, pipeline ordering, package-mutation safety, and next-session handoff. External audit framing makes the default operating document heavier than needed.
```

implementation:

```text
Deleted 10_EXTERNAL_AUDIT_PROCESS.md, added 10_USER_CLI_WORKFLOW.md, and updated _WORKING_CONTEXT/README.md.
```

supersedes:

```text
DL_CONTEXT_20260611_007
DL_CONTEXT_20260611_008
```

status: active

## 2026-06-11 - External Audit Revision: Hosea And Alignment Gate

decision_id: `DL_CONTEXT_20260611_008`

decision:

```text
Revise the external audit process document so Codex Session is explicitly mapped to the Hosea node, and so the ResearchPlan/case-intent versus InspectResult alignment gate is treated as a required control before collection.
```

rationale:

```text
Operator approval alone does not prove that the intended data is being collected. The audit process must check both authority and intent alignment.
```

implementation:

```text
Updated 10_EXTERNAL_AUDIT_PROCESS.md sections 1, 2, 7 UC3, 9, 10, 11, 12, and 13.
```

status: superseded by `DL_CONTEXT_20260611_009`

## 2026-06-11 - External Audit Process Document

decision_id: `DL_CONTEXT_20260611_007`

decision:

```text
Create a process-level external audit document covering use cases, session scenarios, pipeline structure, work system layers, controls, risks, and audit checklist.
```

implementation:

```text
Added 10_EXTERNAL_AUDIT_PROCESS.md and linked it from _WORKING_CONTEXT/README.md.
```

status: superseded by `DL_CONTEXT_20260611_009`

## 2026-06-11 - Canonical Entrypoint Cleanup

decision_id: `DL_CONTEXT_20260611_006`

decision:

```text
Use _WORKING_CONTEXT/README.md as the single canonical project entrypoint. Keep 00_READ_FIRST.md only as a compatibility pointer.
```

rationale:

```text
README.md and 00_READ_FIRST.md overlapped and could confuse new sessions. A single canonical entrypoint reduces instruction ambiguity.
```

status: active

## 2026-06-11 - Working Context README

decision_id: `DL_CONTEXT_20260611_005`

decision:

```text
Create a README.md in _WORKING_CONTEXT so future sessions can discover the operating standard from a conventional file name.
```

implementation:

```text
Added _WORKING_CONTEXT/README.md and linked it from 00_READ_FIRST.md.
```

status: active

## 2026-06-11 - New Session Scenario Router

decision_id: `DL_CONTEXT_20260611_004`

decision:

```text
Future Codex sessions should classify the user request into a workflow scenario before reading additional context.
```

implementation:

```text
Added 09_NEW_SESSION_WORKFLOW_SCENARIOS.md and linked it from 00_READ_FIRST.md.
```

status: active

## 2026-06-11 - Case Neutrality

decision_id: `DL_CONTEXT_20260611_003`

decision:

```text
Working context must remain generic for any streamer case. KimDalsu and Gubiba are reference cases/templates, not defaults.
```

implementation:

```text
Added 03_STREAMER_CASE_GENERIC_PROTOCOL.md.
Moved KimDalsu-specific context to 08_REFERENCE_CASE_KIMDALSU.md.
Updated indexes to route generic case work through the generic protocol first.
```

status: active

## 2026-06-11 - Temporary Judgment Support

decision_id: `DL_CONTEXT_20260611_002`

decision:

```text
Codex may provide temporary judgment support in this project because Pearson/Susan/ND/BEARING are not implemented.
```

boundary:

```text
Recommendations must remain operator recommendations, review notes, decision notes, or patch candidates. User/operator approval is required for final judgment, disclosure, collection approval, and CaseResult promotion.
```

status: active
