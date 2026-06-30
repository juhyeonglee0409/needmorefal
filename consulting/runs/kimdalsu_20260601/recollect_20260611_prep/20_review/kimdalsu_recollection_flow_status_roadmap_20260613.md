# KimDalsu Recollection Flow Status And Roadmap

Date: 2026-06-13  
Run: `kimdalsu_20260601 / recollect_20260611_prep`  
Document type: review note / operator handoff  
Canonical mutation: none  

## 1. Current Executive Summary

현재 흐름은 기존 legacy report를 곧바로 수정하는 단계가 아니라, fresh evidence 기반으로 김달수 케이스 패키지를 다시 만들 수 있는지 검증하는 재수집 준비/검토 흐름이다.

가장 중요한 변화는 CHZZK public profile 경로가 처음에는 VOD/card DOM 중심의 contextual signal에 머물렀지만, Charles API body summary 보강 이후 subject identity/current public profile API direct source로 재진단되었고, Arthur inspect와 bounded collect까지 통과했다는 점이다.

현재 CHZZK subject profile collect 결과는 다음 범위에서 `PASS`로 볼 수 있다.

- Fresh evidence candidate: yes
- Subject channel identity: `channelId` hash 일치
- Public profile/current fields: `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive` 수집됨
- Raw HTML/raw JSON/screenshot/secret storage: 없음
- Canonical package mutation: 없음
- Verification status: `not_verifiable`

다만 이 결과는 아직 CaseResult, DisclosureLog, PublicDemoRow, package canonical data로 승격된 것이 아니다. 지금 단계의 산출물은 "나중에 operator-approved patch candidate를 만들 수 있는 fresh evidence candidate"다.

Softcon 쪽은 접근 불가로 단정할 상태가 아니다. Charles와 Arthur inspect는 visible/headed profile 조건에서 profile-cleared 또는 response 200/RSC field map까지 도달했지만, collect는 checkpoint에 막혔다. 따라서 Softcon은 현재 "source absence"가 아니라 inspect/collect transport parity 문제와 checkpoint boundary evidence로 보존해야 한다.

## 2. Operating Foundation

운영 기반은 이미 다음 방향으로 정리되었다.

- 새 세션이 긴 문서를 raw-load하지 않도록 `_WORKING_CONTEXT` 기반 workflow를 사용한다.
- `10_USER_CLI_WORKFLOW.md`와 `10_USER_CLI_WORKFLOW.ko.md`를 active 운영 문서로 승격했다.
- patch candidate, status, decision log, `SESSION_NOTE.md`를 남기는 규칙을 고정했다.
- Codex는 Pearson/Susan/ND/BEARING이 구현되기 전의 임시 판단 보조로만 동작한다.
- 최종 판단, collect 승인, disclosure 판단, CaseResult promotion, PublicDemoRow readiness는 user/operator 권한으로 남긴다.

이 운영 기반의 핵심은 "작업 실행"과 "최종 판단"을 분리하는 것이다. Charles/Arthur는 진단과 실행을 담당하고, Codex는 산출물 검토와 patch candidate 준비를 돕지만, canonical mutation은 하지 않는다.

## 3. Recollection Preparation State

기존 리포트와 CaseResult는 legacy 또는 partial로 보고 fresh recollection을 준비했다.

준비된 주요 파일은 다음과 같다.

- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `20_review/intent_alignment_checklist.md`
- `RUN_MANIFEST.json`
- `SESSION_NOTE.md`

핵심 수집 목표는 다음 네 축이다.

- Subject identity/current metrics
- Follower count/rank/channel hash/url
- LoL/MOBA cohort/population 근거
- Public crosscheck

현재 이 네 축 중 CHZZK public source를 통한 subject identity/current public profile 일부는 fresh evidence candidate 단계까지 도달했다. follower/rank, Softcon, Semorank/Aurolive, LoL/MOBA population 쪽은 아직 package-ready evidence로 닫히지 않았다.

## 4. Softcon Diagnostic Status

### 4.1 Unauthenticated Charles

초기 unauthenticated Charles 진단은 Softcon에서 Vercel checkpoint 또는 HTTP 429 boundary에 걸렸다.

이 결과는 다음 의미를 갖는다.

- Softcon source가 존재하지 않는다는 뜻이 아니다.
- Unauthenticated/default transport 조건에서는 접근 또는 수집이 제한된다는 boundary evidence다.
- 이 단계에서 collection_plan 또는 verification이 비어 있는 것은 source absence가 아니라 access boundary로 보존해야 한다.

### 4.2 Charles Browser Probe 보강

Charles에 `browser_probe`를 붙여 checkpoint, rate-limit, login, CAPTCHA, visibility, rendered 상태를 진단하게 했다.

그 결과 operator-approved non-default Chrome profile 조건에서 Softcon 5개 route는 다음 상태까지 도달했다.

- `rsc_payload` 관측
- `profile_cleared`
- `collection_plan` present
- `verification` present

이는 Softcon이 원천적으로 막힌 것이 아니라, profile/session/transport 조건에 민감한 source라는 점을 보여준다.

### 4.3 Arthur Inspect / Collect 차이

Arthur headless/profile inspect는 checkpoint를 넘지 못했다. 이후 Arthur chrome_profile inspect를 보강했고, visible/headed Chrome profile, `wait_until=networkidle`, `settle_wait_ms=1500` 조건에서는 5개 route 모두 status 200, no checkpoint, RSC payload field map까지 도달했다.

하지만 subject smoke collect는 같은 목적의 bounded run에서 다시 checkpoint에 막혔다.

Softcon subject smoke collect 결과는 다음 상태다.

- Result: `40_arthur_collect/results/softcon_subject_smoke_collect_20260612.CollectionResult.json`
- Execution: executed, but stopped
- Stop reason: `chrome_profile_checkpoint_not_cleared`
- Item count: `0`
- Verification: `count_mismatch`
- Output use: smoke output / boundary evidence only
- Canonical package mutation: none

현재 결론은 다음과 같다.

Softcon은 "접근 불가"가 아니라 "inspect와 collect 사이의 profile/session/transport 재현성 문제"가 남아 있다. 다음 Softcon live retry는 transport parity synthetic harness 또는 ephemeral cookie bridge mock/test 이후에만 고려해야 한다.

## 5. Policy Reinforcement

Arthur chrome_profile collect는 directive-gated로 설계되었다.

고정된 정책 경계는 다음과 같다.

- `approved=false` draft를 먼저 만든다.
- `approved=true` copy는 operator가 exact scope를 승인한 경우에만 생성한다.
- exact URL allowlist를 사용한다.
- max items, max requests, runtime limit을 둔다.
- visible/headed/profile 사용 여부를 directive에 명시한다.
- raw HTML 저장 금지
- raw JSON body 저장 금지
- screenshot 저장 금지
- token/cookie/auth value 저장 금지
- CollectionResult 외 CaseResult/DisclosureLog/PublicDemoRow/package canonical mutation 금지

추가로 `ephemeral cookie bridge` 정책이 active 운영 정책으로 정리되었다.

의미는 다음과 같다.

- 승인된 Chrome profile에서 exact origin cookie를 메모리로만 읽을 수 있다.
- same-origin `curl_cffi` 요청에 한정해 전달할 수 있다.
- Chrome cookie DB 직접 읽기, bulk export, cross-origin forwarding, durable token/cookie storage는 금지다.

이 정책은 Softcon 같은 profile-sensitive source의 transport parity를 해결할 수 있는 후보지만, 아직 live Softcon 재시도 승인이나 full implementation 완료를 의미하지 않는다.

## 6. Public Crosscheck Pivot

Softcon live collect retry는 보류하고, 낮은 리스크 public source로 우회 검증을 시작했다.

초기 CHZZK public profile route는 clean access였지만 protocol이 VOD/card DOM 중심으로 생성되었다. 따라서 원래 subject identity/current metrics intent에는 부족했고, `CHZZK VOD/card contextual signal`로만 취급하기로 했다.

Semorank와 Aurolive는 실행환경 escalation 제한 때문에 미실행 상태였다. 이는 source absence가 아니며, "not run / pending public scout"로 보존해야 한다.

## 7. CHZZK Profile Rediagnosis And Charles Patch

### 7.1 Initial Gap

초기 CHZZK protocol은 target URL이 subject profile page였음에도 collection_plan primary selector가 VOD/card DOM으로 잡혔다.

원인은 Charles가 CHZZK XHR/fetch API를 URL, status, content-type 수준으로만 기록했고, API response body summary를 durable raw body 없이 구조적으로 남기지 않았기 때문이다.

그 결과 `m.chzzk.naver.com` 페이지에서 관측된 `api.chzzk.naver.com/service/v1/channels/{hash}` endpoint가 subject profile JSON으로 승격되지 못했고, visible DOM의 VOD/card selector가 primary plan이 되었다.

관련 review:

- `20_review/chzzk_public_profile_protocol_intent_gap_20260612.md`
- `20_review/chzzk_subject_profile_rescout_request_20260612.md`
- `20_review/chzzk_subject_profile_rescout_alignment_20260612.md`

초기 verdict는 `PARTIAL / contextual only`였다.

### 7.2 Charles API Body Summary Patch

Charles 쪽에 CHZZK API body summary capture가 추가되었다.

Patch intent:

- Allowed JSON XHR/fetch response body를 메모리에서 bounded parse한다.
- raw JSON body를 저장하지 않는다.
- `body_summary`에는 field paths, profile/contextual paths, sample scalar, classification만 저장한다.
- CHZZK `service/v1/channels/{hash}`는 `content.channelName`과 `content.channelId/channelIdHash`가 있을 때 profile usable로 분류한다.
- videos/clips/data endpoint는 profile intent에서는 contextual-only로 유지한다.
- token/cookie/auth-like query/scalar value는 redaction한다.
- oversize, non-JSON, parse-failed body는 promote하지 않는다.

관련 patch review:

- `20_review/charles_chzzk_api_body_capture_patch_review_20260612.md`

대표 테스트 결과:

- `test_chzzk_api_body_capture_v0_10.py`: 14 PASS / 0 FAIL
- `test_protocol_v0_8.py`: 20 PASS / 0 FAIL
- `test_playwright_phase2_v0_4.py`: 15 PASS / 0 FAIL
- `test_review_improvements_v0_8.py`: 31 PASS / 0 FAIL
- `test_verification_gate_phase2_v0_6.py`: 11 PASS / 0 FAIL
- `test_html_report_v0_5.py`: 24 PASS / 0 FAIL
- `test_challenge_phase2_v0_5.py`: 10 PASS / 0 FAIL

### 7.3 CHZZK API Body Rescout

이후 operator-approved CHZZK public Charles rescout가 1회 실행되었고 `PASS`를 받았다.

Artifacts:

- ScoutReport: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.scout_report.json`
- Protocol: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`
- Review: `20_review/chzzk_subject_profile_api_body_rescout_alignment_20260612.md`

핵심 결과:

- Target: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- Promoted API: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- `best_path`: `api_direct`
- `collection_plan.source`: `api`
- Observed XHR/fetch API records: 20
- CHZZK channel-family records: 6
- `body_summary` records: 6
- usable profile candidate: 1
- Direct coverage: `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive`
- Identity match: `channelId=dcbccbf2d8e2a1b095244c5856d3613a`, `channelName=김달수 Dalsu`
- videos/data/clips endpoints: contextual-only 유지
- raw JSON body/raw HTML/screenshot/cookie/token/auth storage: 없음

이 단계에서 CHZZK는 원래 subject identity/current profile intent에 대해 Arthur inspect 후보가 되었다.

## 8. Arthur CHZZK Inspect, Directive, Collect

### 8.1 Arthur Inspect

Arthur inspect가 operator-approved로 1회 실행되었고 `PASS`를 받았다.

Artifacts:

- InspectResult: `30_arthur_inspect/chzzk_subject_profile_api_body_rescout_api_direct_20260612.InspectResult.json`
- Review: `20_review/post_inspect_alignment_chzzk_subject_profile_api_body_20260612.md`

핵심 결과:

- Arthur target page: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- Actual HTTP/JSON resource: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- response status: `200`
- field map/sample surface: `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive`

이 단계는 "Arthur도 Charles가 찾은 API source를 볼 수 있는지" 확인한 것이다. 아직 collect는 아니었고, canonical package 반영도 아니었다.

### 8.2 Initial CollectDirective Draft

Arthur inspect PASS 이후 approved=false CollectDirective draft가 생성되었다.

Artifacts:

- Draft: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_20260612.json`
- Review: `20_review/chzzk_subject_profile_api_body_collect_directive_draft_review_20260612.md`

검토 중 중요한 문제를 찾았다.

초기 draft는 `json_path_hints`에 `$.content.channelId` 같은 scalar field paths를 포함하고 있었다. Arthur `collect_api`는 row 후보를 순서대로 시도하므로, 첫 scalar path가 매칭되면 object row가 아니라 scalar-only `{"value": ...}` row가 만들어질 위험이 있었다.

따라서 이 draft는 정책/범위 초안으로는 의미가 있었지만, 바로 `approved=true`로 올리면 안 되는 상태였다.

### 8.3 Record-Root Collect Shape Fix

offline mock review로 collect shape가 수정되었다.

Artifacts:

- Revised draft: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_record_root_20260612.json`
- Review: `20_review/chzzk_subject_profile_api_direct_collect_shape_patch_review_20260612.md`

핵심 수정:

- `source_protocol.collection_plan.json_path_hints = ["$.content"]`
- record root를 `$.content`로 고정
- 기존 scalar field paths는 `field_json_path_hints` metadata로 보존

Mock/test 결과:

- Synthetic CHZZK payload에서 exactly one object row 생성
- scalar-only `{"value": ...}` row 없음
- `tests/test_collect_api_v0_1.py`: 16 PASS / 0 FAIL
- `tests/test_protocol_loader_v0_1.py`: 46 PASS / 0 FAIL

이 단계 후에야 operator가 revised draft를 보고 승인 여부를 판단할 수 있는 상태가 되었다.

### 8.4 Operator-Approved Bounded Collect

이후 revised draft를 기반으로 approved=true copy가 생성되었고, Arthur collect가 정확히 1회 실행되었다.

Artifacts:

- Approved directive: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.approved_true_record_root_20260613.json`
- CollectionResult: `40_arthur_collect/results/chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json`

Execution summary:

- Execution status: `executed=true`, `stopped_reason=null`
- Path: `api_direct`
- Transport: `httpx`
- Requests made: 2
- Requests: live robots check + exact CHZZK channel API GET
- Item count: 1
- Row root: `$.content`
- Row shape: single object row
- Scalar-only `{"value": ...}` row: 없음
- Boundary signals: `robots_check`, robots allowed
- Absences: none
- Errors: none

Fields present:

- `channelId`
- `channelName`
- `channelDescription`
- `followerCount`
- `channelImageUrl`
- `openLive`

Storage/safety:

- Artifacts: 0
- Raw artifact directory: not created
- Raw HTML saved: no
- Raw JSON body saved: no
- Screenshot saved: no
- Session/profile used: no
- Token/cookie/auth/header/browser-storage value storage: no
- `session_profile.secret_values_logged=false`

Verification status는 `not_verifiable`이다. 이유는 `expected_row_count=null`이기 때문이다. shape/null-ratio checks는 통과했지만, Arthur가 이 single profile API에 대한 row count baseline을 추론하지 않으므로 row-count verification을 success로 올리지 않았다.

이 `not_verifiable`은 실패로 바꾸면 안 된다. 현재 의미는 "field evidence는 usable하지만 row-count baseline verification은 없음"이다.

### 8.5 Post-Collect Evidence Review

CollectionResult는 별도 post-collect review에서 fresh evidence candidate로 검토되었다.

Artifact:

- `20_review/post_collect_evidence_review_chzzk_subject_profile_20260613.md`

Verdict:

- `PASS` as fresh evidence candidate for CHZZK subject identity/profile/current public fields
- CaseResult mutation: none
- DisclosureLog mutation: none
- PublicDemoRow mutation: none
- Package canonical mutation: none

따라서 CHZZK subject profile API direct result는 다음 단계의 EvidencePackage patch candidate 또는 Pearson pre-ingest validation sample로 사용할 수 있다.

## 9. Current Evidence State By Source

| Source | Current State | Evidence Use | Boundary |
|---|---:|---|---|
| CHZZK subject profile API | PASS fresh evidence candidate | subject identity, profile text, follower count, profile image, live/open state | verification remains `not_verifiable` due no row-count baseline |
| CHZZK VOD/card DOM | PARTIAL / contextual only | recent VOD/category context only | not primary identity/current metrics evidence |
| Softcon subject route | boundary / transport parity unresolved | checkpoint/profile-session behavior evidence | collect failed with checkpoint, item_count=0 |
| Softcon 5 profile routes | inspect/profile-cleared evidence exists | proves visible profile can reach RSC maps | collect reproducibility unresolved |
| Semorank | not run | none yet | not absence |
| Aurolive | not run | none yet | not absence |
| LoL/MOBA cohort/population | open | none package-ready yet | must preserve not_verifiable or absence only after targeted work |

## 10. Current Artifact Map

CHZZK profile diagnostic and collection artifacts:

- `20_review/chzzk_public_profile_protocol_intent_gap_20260612.md`
- `20_review/chzzk_subject_profile_rescout_request_20260612.md`
- `20_review/chzzk_subject_profile_rescout_alignment_20260612.md`
- `20_review/charles_chzzk_api_body_capture_patch_review_20260612.md`
- `10_charles/chzzk_subject_profile_api_body_rescout_20260612.scout_report.json`
- `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`
- `20_review/chzzk_subject_profile_api_body_rescout_alignment_20260612.md`
- `30_arthur_inspect/chzzk_subject_profile_api_body_rescout_api_direct_20260612.InspectResult.json`
- `20_review/post_inspect_alignment_chzzk_subject_profile_api_body_20260612.md`
- `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_20260612.json`
- `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_record_root_20260612.json`
- `20_review/chzzk_subject_profile_api_body_collect_directive_draft_review_20260612.md`
- `20_review/chzzk_subject_profile_api_direct_collect_shape_patch_review_20260612.md`
- `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.approved_true_record_root_20260613.json`
- `40_arthur_collect/results/chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json`
- `20_review/post_collect_evidence_review_chzzk_subject_profile_20260613.md`

Softcon diagnostic and smoke artifacts:

- `10_charles/softcon_subject_channel_current_stats.charles_profile_ab_smoke_20260612.protocol.json`
- `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `40_arthur_collect/directives/softcon_subject_smoke_collect_directive.draft_approved_false_20260612.json`
- `40_arthur_collect/directives/softcon_subject_smoke_collect_directive.approved_true_20260612.json`
- `40_arthur_collect/results/softcon_subject_smoke_collect_20260612.CollectionResult.json`

Run control:

- `RUN_MANIFEST.json`
- `SESSION_NOTE.md`

## 11. Boundary And Not-Verifiable Inventory

The following states must be preserved as-is:

- CHZZK CollectionResult `verification_status=not_verifiable`
  - Reason: `expected_row_count=null`
  - Meaning: field evidence is usable as candidate; row-count verification baseline is absent

- Softcon smoke collect `item_count=0`
  - Reason: checkpoint not cleared in collect path
  - Meaning: boundary evidence and transport parity problem, not source absence

- Softcon unauthenticated 429/checkpoint/manual/restricted signals
  - Meaning: unauthenticated/default path boundary, not absence

- Semorank/Aurolive not executed
  - Meaning: pending public scout, not absence

- LoL/MOBA cohort/population not yet established
  - Meaning: open requirement, not disproven

None of these should be silently rewritten into success, failure, or final absence without a dedicated review note and operator decision.

## 12. Updated Goal Point

최종 목표는 기존 legacy report를 대체할 fresh evidence 기반 김달수 case package 후보를 만드는 것이다.

구체적으로 필요한 것은 다음과 같다.

- Subject identity/current metrics를 fresh source로 확인한다.
- Follower count/rank/channel hash/url을 public 또는 Softcon source로 교차검증한다.
- LoL/MOBA cohort/population 근거를 확보하거나, 명시적 `not_verifiable` 또는 absence로 보존한다.
- Membership/checkpoint/rate-limit/manual boundary를 source absence와 구분해 보존한다.
- CollectionResult를 바로 CaseResult로 승격하지 않는다.
- Evidence/Absence/Disclosure/CaseResult patch candidate를 만든 뒤 operator 승인으로만 canonical package를 갱신한다.
- PublicDemoRow는 별도 익명화/공개성 검토 후 판단한다.

현재 CHZZK result는 이 목표 중 subject identity/current public profile 축의 첫 fresh evidence candidate다.

## 13. Roadmap From Here

### Step 1. Pearson v0.1 Pre-Ingest Spec

가장 가까운 다음 작업으로는 Pearson v0.1 pre-ingest/storage contract spec을 만드는 것이 적절하다.

이유:

- CHZZK CollectionResult는 이제 실제 fresh evidence candidate가 되었지만, 아직 canonical package로 넣으면 안 된다.
- Pydantic/Polars artifact validation layer는 Arthur나 Charles의 역할이 아니라 Pearson pre-ingest 및 Susan Layer 0 QA 지원 역할에 가깝다.
- 따라서 먼저 Pearson이 어떤 입력을 받고, 어떤 검증을 하고, 어떤 receipt/patch candidate를 내보내는지 명세해야 한다.

권장 산출물:

- `D:\Codex_Workspace\Instruction\PEARSON_PRE_INGEST_SPEC_v0_1.md`

포함할 내용:

- Input contracts: ScoutReport, Protocol, InspectResult, CollectDirective, CollectionResult
- Pydantic validation responsibilities
- Polars summary responsibilities
- StorageReceipt / IngestCandidate / EvidencePackage patch candidate boundary
- Raw/secret/screenshot storage prohibition
- `not_verifiable`, boundary, absence preservation rule
- Canonical mutation prohibition without operator approval

### Step 2. Pydantic / Polars Artifact Validation Layer

Pearson spec 이후에는 offline validation layer를 만든다.

Pydantic responsibility:

- Protocol schema validation
- InspectResult schema validation
- CollectDirective schema and approval boundary validation
- CollectionResult shape, lineage, artifact, secret, status validation
- protocol_hash/directive_hash/source path lineage checks

Polars responsibility:

- item count summary
- field coverage table
- null ratio table
- boundary signals table
- absence table
- source/source_time/fetched_at comparison
- candidate evidence comparison table

초기에는 PostgreSQL로 바로 가지 않는 것이 낫다. file-artifact contract와 validation output이 안정화된 후 PostgreSQL을 run/target/artifact/item/provenance registry로 도입하는 순서가 안전하다.

### Step 3. CHZZK EvidencePackage Patch Candidate

Pearson-style validation이 준비되면 CHZZK CollectionResult를 기반으로 EvidencePackage patch candidate를 만들 수 있다.

이 patch candidate는 다음을 포함해야 한다.

- Source: CHZZK subject profile API direct
- CollectionResult path
- Approved directive path
- Protocol path
- InspectResult path
- fetched_at
- observed fields and values
- field coverage summary
- verification status: `not_verifiable`
- boundary signals: `robots_check`
- storage safety checks
- non-canonical status

이 단계도 canonical mutation이 아니다. operator가 검토할 후보를 만드는 단계다.

### Step 4. Public Crosscheck Resume

Semorank와 Aurolive는 아직 source absence가 아니라 미실행 상태다.

다음 public crosscheck는 각각 unauthenticated Charles scout 1회로 좁게 진행해야 한다.

Gate:

- clean protocol이면 Arthur inspect 후보로 넘긴다.
- checkpoint, manual_review, restricted, login, CAPTCHA, HTTP 429이면 boundary로 보존한다.
- missing collection_plan이면 collect로 넘기지 않는다.

### Step 5. Softcon Transport Parity

Softcon live collect retry는 아직 보류해야 한다.

먼저 해야 할 tooling 작업:

- inspect/collect parity synthetic harness
- chrome_profile runtime state comparison
- `wait_until`, `settle_wait_ms`, visible/headed flags parity review
- response_status vs effective_status handling review
- optional ephemeral cookie bridge mock/test

그 후 operator가 승인하면 subject route 1개만 bounded smoke retry를 고려한다.

### Step 6. LoL / MOBA Cohort And Population Evidence

김달수 case package가 legacy report를 대체하려면 LoL/MOBA cohort/population 근거도 필요하다.

다음 작업은 다음 둘 중 하나로 정리해야 한다.

- Public/Softcon source에서 cohort/population 근거를 찾는 수집 계획을 세운다.
- 접근이나 자료 부재가 확인되면 `not_verifiable` 또는 absence candidate로 보존한다.

이 단계는 CHZZK subject profile evidence와 별도 축이다.

### Step 7. Package Patch Candidates

충분한 fresh evidence와 boundary inventory가 모이면 다음 patch candidate들을 만든다.

- EvidencePackage patch candidate
- AbsenceInventory patch candidate
- DisclosureLog patch candidate
- CaseResult partial -> ready 검토 candidate
- PublicDemoRow readiness candidate

각 candidate는 operator review 대상이며, 자동 canonical mutation 대상이 아니다.

## 14. Explicit No-Go Rules

현재 상태에서 다음은 금지 또는 보류다.

- CHZZK CollectionResult를 바로 CaseResult에 반영하지 않는다.
- DisclosureLog를 자동 갱신하지 않는다.
- PublicDemoRow를 자동 ready 처리하지 않는다.
- Softcon collect를 transport parity 없이 재시도하지 않는다.
- Semorank/Aurolive 미실행을 source absence로 쓰지 않는다.
- `not_verifiable`을 임의로 success 또는 failure로 바꾸지 않는다.
- raw HTML/raw JSON body/screenshot/token/cookie/auth value를 저장하지 않는다.
- `approved=false` directive를 operator 승인 없이 `approved=true`로 바꾸지 않는다.

## 15. Smallest Next Action

가장 작은 다음 액션은 Pearson v0.1 pre-ingest spec을 작성하는 것이다.

추천 이유는 단순하다. CHZZK collect는 이미 fresh evidence candidate까지 왔고, 이제 필요한 것은 더 많은 live 실행이 아니라 이 artifact를 package 후보로 올리기 전의 검수/저장 계약이다.

Recommended next output:

- `D:\Codex_Workspace\Instruction\PEARSON_PRE_INGEST_SPEC_v0_1.md`

그 다음에는 이 spec을 기준으로 Pydantic/Polars offline artifact validation layer를 설계하거나 구현한다.

Arthur/Charles next live work는 그 이후에 각 source별로 별도 승인받아 진행한다.
