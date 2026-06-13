# 사용자-CLI 워크플로우 - 세션 작업 시스템

Version: 1.1 (2026-06-11)
Status: active

목적:

```text
solo user + CLI/Codex 기반 streamer case work를 낮은 context 비용으로 운영한다.
source-of-truth 경계를 보존하고, Charles/Arthur pipeline 작업에는 명시적인
approval/alignment gate를 둔다.
```

이 문서는 작업 효율을 위한 운영 문서다.

이 workflow는 case-neutral하게 적용한다.

이 문서는 `10_USER_CLI_WORKFLOW.md`의 한국어 번역본이다. 운영 의미가 충돌하면 원문과 함께 확인하고 동기화한다.

## 0. 문서 우선순위와 보호 파일

이 문서는 Streamer Consulting Project 안에서 solo user + CLI/Codex workflow를 운영하는 규칙을 정의한다.

우선순위:

- `AGENTS.md`는 프로젝트 전역 Codex 운영 제약을 정의한다.
- `_WORKING_CONTEXT/README.md`는 canonical project context entrypoint이자 source map이다.
- `10_USER_CLI_WORKFLOW.md`는 workflow rule을 정의한다.
- `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`는 scenario router와 detail layer다.
- `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`와 이 문서가 충돌하면 workflow rule은 이 문서가 우선한다.
- case reference가 충돌하면 package README나 reference index에 적힌 최신 canonical reference를 사용한다.
- safety boundary와 efficiency shortcut이 충돌하면 safety boundary가 우선한다.

보호 파일:

```text
AGENTS.md
_WORKING_CONTEXT/README.md
_WORKING_CONTEXT/09_NEW_SESSION_WORKFLOW_SCENARIOS.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.ko.md
```

보호 파일은 명시적인 사용자 지시가 있을 때만 변경할 수 있으며, decision log entry를 남겨야 한다.

`_WORKING_CONTEXT/PATCH_CANDIDATES/` 아래의 patch candidate는 user/operator가 명시적으로 accepted/applied 처리하기 전까지 canonical workflow를 변경하지 않는다.

Decision log는 `_WORKING_CONTEXT/07_DECISION_LOG.md`다. durable workflow decision과 status change를 append-only로 기록한다.

## 1. 목적과 역할

이 문서는 solo user + CLI/Codex session을 위한 managed workflow를 규정한다.

포함 범위:

- session startup과 context loading
- generic streamer case intake
- existing case review와 temporary judgment support
- Charles/Arthur pipeline preparation
- exact evidence lookup
- package mutation boundary
- `SESSION_NOTE.md`를 통한 session handoff

Collection은 user/operator가 별도로 승인한 경우에만 포함된다. Formal audit bundle은 선택 사항이며, 외부 공유나 공식 검토가 필요할 때만 만든다.

| Actor | Does | Must not do |
|---|---|---|
| User / Operator | final judgment, approval, direction | final approval을 조용히 위임 |
| User-CLI Orchestration Node | context 정리, spec 작성, execution support, alignment review, patch candidate 생성 | source-of-truth나 final package state를 조용히 변경 |
| Codex Session in this workflow | session behavior와 working-context 문서를 통해 Hosea-node process work를 임시 수행 | 자신을 별도 구현된 Hosea tool로 표현 |
| Charles / CrawlScouter | target 진단, ScoutReport/ExecutionProtocol 생성 | collection 실행 |
| Arthur | 승인된 protocol/directive에 따라 inspect/collect 실행 | final judgment 수행 |
| Pearson / Susan / ND / BEARING | Pearson/Susan은 2026-06-13 기준 spec 존재, ND/BEARING은 future 역할. Storage, QA, absence, cross-check tools | spec 존재를 현재 실행 가능한 구현체나 canonical mutation 승인으로 가정 |

이 workflow에서 CLI/Codex session plus `_WORKING_CONTEXT`는 Hosea-node 역할을 수행한다.
이것은 별도 구현된 tool이 아니라 process role이다.

## 2. 핵심 규칙

```text
Context routing != source evidence
Context summary != source-of-truth
Diagnosis != execution
Execution != judgment
Recommendation != operator approval
Patch candidate != final package mutation
Reference case != generic protocol
Legacy reference != fresh evidence
```

작업 원칙:

```text
Use working context to find the right source quickly. Do not treat working context as final evidence.
```

## 3. 세션 시작

의미 있는 workspace session은 아직 읽지 않았다면 global bootstrap부터 시작한다.

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
```

의미 있는 Streamer Consulting Project session은 다음 순서로 시작한다.

1. `_WORKING_CONTEXT/README.md`를 읽는다.
2. `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`에서 task scenario를 분류한다.
3. 기존 case/run을 이어갈 때는 다른 case context를 읽기 전에 최신 관련 `SESSION_NOTE.md`를 읽는다. 이는 Scenario 2와 Scenario 7에서 필수이며, 기존 run을 재개하는 Scenario 3에도 적용된다.
4. active task context만 로드한다.
5. source file은 broad loading이 아니라 targeted lookup으로 사용한다.
6. session이 durable state, decision, blocker, next step을 만들면 `SESSION_NOTE.md`를 작성하거나 갱신한다.

작업이 문서 개정, QA, 비교, exact evidence review를 명시적으로 요구하지 않는 한 full MASTER, full methodology, old reports, archive packages, full CSV, full JSON은 로드하지 않는다.

## 4. Context Loading Rules

다음 고정 시작 비용은 task-context budget에 포함하지 않는다.

- `_WORKING_CONTEXT/README.md`
- `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`의 관련 줄
- case/run을 재개할 때 최신 관련 `SESSION_NOTE.md`

기본 제한:

- Task context: 현재 scenario에 필요한 최소만 로드한다.
- Default maximum: 작업상 명확히 더 필요하지 않으면 task-context file은 최대 2개.
- Framework: summary/capsule을 먼저 사용한다.
- Case package: 있으면 README와 CASE_DOSSIER를 먼저 읽는다.
- JSON: top-level key를 먼저 확인한다.
- CSV: header와 처음 20행을 먼저 확인한다.
- ZIP: contents를 읽기 전에 entry list를 먼저 확인한다.
- Legacy: 사용자가 comparison/history를 요청하지 않으면 기본 차단한다.
- Full document loading: revision, QA, explicit comparison, exact evidence review에만 허용한다.

Reference role exclusivity:

각 session에서 role별 active reference는 최대 1개만 로드한다.

Roles:

- framework
- methodology
- schema
- active_case
- active_plan
- tool_contract
- runbook

여러 candidate가 있으면 현재 package README나 reference index에 적힌 최신 canonical reference를 사용한다.

Legacy reference는 작업이 comparison, history, calibration을 명시적으로 요구할 때만 로드할 수 있다.

기본 금지 행동:

```text
raw-loading long framework markdown
printing full machine JSON
printing full CSV
reading all zip entries
using one reference case as default structure for all cases
```

허용되는 focused lookup:

- source map lookup
- exact `rg -n` search
- specific source lines
- CSV headers and small samples
- JSON top-level keys and named subtrees
- named zip entries only

## 5. Work Scenarios

상세 router로 `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`를 사용한다.

Top-level scenarios:

```text
Scenario 0 - Session start
Scenario 1 - New case intake
Scenario 2 - Existing case review
Scenario 3 - Charles/Arthur collection preparation
Scenario 4 - Reference case lookup
Scenario 5 - Context/package maintenance
Scenario 6 - Exact evidence lookup
Scenario 7 - Resume after context compaction
```

Scenario별 최소 session output:

| Scenario | Session output |
|---|---|
| New case intake | case orientation note, known assets, missing assets, next gates |
| Existing case review | facts, blockers, recommendation, approval needed, remaining risk |
| Charles/Arthur preparation | RUN_MANIFEST, command draft, protocol path, InspectResult path, CollectDirective draft |
| Reference case lookup | reusable pattern, case-specific remainder, source paths |
| Context maintenance | changed files, rationale, decision log entry |
| Exact evidence lookup | claim, source path, exact evidence, remaining uncertainty |
| Resume after compaction | current goal, loaded context, next action |

## 6. Charles/Arthur Pipeline

Generic pipeline:

```text
TargetBatchPlan
  -> Charles ScoutReport
  -> ExecutionProtocol extraction
  -> operator review
  -> Arthur InspectResult
  -> intent-alignment gate
  -> CollectDirective
  -> approved collect
  -> Arthur CollectionResult
  -> patch candidates
  -> manual/Pearson package update later
```

Pipeline rules:

- Charles는 진단한다.
- Arthur는 실행한다.
- orchestrator는 scope, file, approval, handoff를 관리한다.
- user/operator는 collection과 final judgment를 승인한다.
- full ScoutReport는 disk에 보존한다.
- ScoutReport는 targeted lookup으로만 로드하고, 전체를 chat에 출력하지 않는다.
- 의도적으로 thin-input `not_verifiable`을 받아들이는 경우가 아니라면 Arthur에는 top-level `protocol`을 넘긴다.
- collect 전 ResearchPlan 또는 case intent를 InspectResult fields와 대조한다.
- mismatch는 boundary signal 또는 review blocker로 기록한다.
- `CollectDirective.approved=true` 없이 collect하지 않는다.
- secret profile value를 저장하지 않는다.
- `not_verifiable`, `boundary_signals`, absences, `protocol_hash`, `directive_hash`, source paths를 보존한다.
- CollectionResult를 CaseResult로 직접 promote하지 않는다.

Intent-alignment gate:

Collect 전 original ResearchPlan 또는 TargetBatchPlan intent를 Arthur InspectResult와 대조한다.

확인 항목:

- inspected source가 의도한 cohort 또는 data type과 실제로 맞는가?
- required fields가 확보 가능해 보이는가?
- source가 boundary/checkpoint/manual-review signal을 반환했는가?
- approved scope가 여전히 충분히 좁은가?

Mismatch가 있으면 중단하거나 operator review로 되돌린다.

Collection이 포함될 때 run directory:

```text
runs/{case_id}/{run_id}/
  00_inputs/
  10_charles/
  20_review/
  30_arthur_inspect/
  40_arthur_collect/
  50_ingest_candidates/
  RUN_MANIFEST.json
```

## 7. Package Mutation And Session Output

CLI/Codex가 만들 수 있는 것:

- notes
- drafts
- patch candidates
- proposed JSON updates
- run artifacts
- `SESSION_NOTE.md`

CLI/Codex가 조용히 overwrite하면 안 되는 것:

- `project.json`
- `CaseResult`
- `PortfolioRow`
- `PublicDemoRow`
- `DisclosureLog`
- final client deliverables

Final package mutation에는 명시적인 사용자 승인 또는 명확한 사용자 지시가 필요하다.

Working-context mutation rule:

- CLI/Codex는 사용자 요청 수행에 필요한 경우 ordinary `_WORKING_CONTEXT` document를 편집할 수 있다.
- Section 0의 protected files는 명시적인 사용자 지시가 필요하다.
- `_WORKING_CONTEXT/PATCH_CANDIDATES/`의 purely local draft가 아닌 모든 working-context edit에는 decision log entry가 필요하다.
- Patch candidate는 기본적으로 `proposed` 상태로 생성한다.

Guest/session token policy:

Guest/session profile은 operator가 scope를 명시적으로 승인한 경우 사용할 수 있다.

Allowed:

- operator-approved guest/session profile 사용
- local-only profile file 참조
- header/cookie name 기록
- token type, expiry, scope summary 기록

Not allowed by default:

- token value를 chat에 붙여넣기
- token value를 ScoutReport, SESSION_NOTE, RUN_MANIFEST 또는 다른 artifact에 저장
- token value를 git-tracked file에 저장
- token value를 raw HTML, logs, screenshots, debug output에 보존
- 반복 재사용 가능한 token value를 plaintext artifact로 남기기

다음과 같은 summary만 기록한다.

```text
profile/session provided: yes
type: guest_session
scope: approved target/domain only
secret_values_logged: false
```

Ephemeral cookie bridge policy:

Arthur는 operator-approved ephemeral cookie bridge를 same-origin session delegation으로만 사용할 수 있다.

Allowed:

- operator-approved Chrome profile을 Playwright로 연다.
- 정확히 승인된 origin에 대해서만 `context.cookies(origin)`으로 cookie를 읽는다.
- cookie value는 memory 안에서만 same-origin `curl_cffi` 실행에 전달한다.
- cookie name, domain, expiry/session summary, scope, bridge status만 기록한다.

Required:

- collect의 경우 `CollectDirective.approved=true`
- exact `approved_scope.allowed_urls`
- exact origin allowlist
- `allow_ephemeral_cookie_bridge=true` 같은 명시적 bridge enablement
- intent-alignment gate 통과
- raw HTML, screenshot, debug-log, secret-value artifact 저장 금지

Not allowed by default:

- Chrome cookie database 직접 읽기
- bulk cookie export
- cross-origin cookie forwarding
- durable cookie/token value 저장
- CAPTCHA solver, credential prompt, private/account page, unexpected security page 우회 용도로 bridge 사용

scope, checkpoint, CAPTCHA, private/account page, secret-persistence 불확실성이 나타나면 stop하고 boundary를 보존한다.

Patch candidate status:

- `proposed`
- `accepted`
- `rejected`
- `applied`
- `superseded`

Default status는 `proposed`다.

Status transition rules:

- CLI/Codex는 `proposed`와 `superseded`만 설정할 수 있다.
- `superseded` candidate는 replacing candidate를 명시해야 한다.
- `accepted`, `rejected`, `applied`는 user/operator만 설정할 수 있다.
- `accepted`는 사용자가 candidate를 승인했지만 아직 canonical file 또는 package에 반영되지 않은 상태다.
- `applied`는 accepted 또는 explicitly approved change가 실행된 상태다.
- Candidate는 같은 session에서 사용자가 명시적으로 적용을 지시한 경우에만 `proposed`에서 `applied`로 이동할 수 있다.
- `rejected`와 `applied`는 사용자의 명시적인 rollback/restoration 지시가 없는 한 terminal 상태다.
- initial `proposed`를 제외한 모든 status change는 decision log entry가 필요하다.

Decision log:

```text
Location: _WORKING_CONTEXT/07_DECISION_LOG.md
Mode: append-only for durable decisions and status changes
```

Entry fields:

- date
- scope
- what changed
- why
- authority

Required for:

- working-context edits
- workflow-document edits
- protected-file edits
- initial `proposed`가 아닌 patch candidate status changes
- package mutation approvals

Session note location:

Collection 또는 pipeline session:

```text
runs/{case_id}/{run_id}/SESSION_NOTE.md
```

Ordinary case/package work:

```text
{case_package}/work/session_notes/SESSION_NOTE_{YYYYMMDD}_{task_slug}.md
```

Project working-context maintenance:

```text
_WORKING_CONTEXT/SESSION_NOTE.md
```

Session note update rule:

- 동일한 run을 명시적으로 이어가는 경우에만 existing note를 update한다.
- ordinary case/package work에서는 같은 날짜의 같은 task일 때만 existing note를 update한다.
- project working-context maintenance에서는 `_WORKING_CONTEXT/SESSION_NOTE.md`를 update한다.
- 그 외에는 new note를 만든다.
- previous session note를 조용히 overwrite하거나 delete하지 않는다.

Ordinary workflow session에는 lightweight note 하나면 충분하다.

```markdown
# SESSION_NOTE

## Date
## Case
## Scenario
## Goal

## Loaded Context

### Active references
- framework:
- methodology:
- schema:
- active_case:
- active_plan:

### Legacy references loaded?
- no / yes
- if yes, why:

### Full documents loaded?
- no / yes
- if yes, why:

## Actions
## Outputs
## Decisions
## Blockers
## Next Step

## Self-Check
- Section 8 self-check run: yes / no
- Exceptions or failed items:
```

Collection session은 추가로 남긴다.

- `RUN_MANIFEST.json`
- `CollectDirective`
- `CollectionResult`
- package update가 제안되면 patch candidates

Optional only:

- `AUDIT_BUNDLE`
- detailed loaded-context manifest
- external sharing package

## 8. End-Of-Session Self-Check

의미 있는 session을 끝내기 전에 확인한다.

```text
Did the session start from the canonical README?
Did it classify the scenario before loading more context?
If resuming a case/run, did it read the newest relevant SESSION_NOTE.md first?
Did it keep task-context loading within the default limits?
Did it load at most one active reference per role?
If legacy was loaded, was its purpose recorded as comparison/history/calibration only?
Did it use working context as router, not final evidence?
Did it preserve source paths for important claims?
Did it separate fact, recommendation, approval, and mutation?
Did it avoid reference-case overfit?
Did it avoid unapproved CaseResult/disclosure/PublicDemo promotion?
Did it preserve absences, boundary signals, and not_verifiable states?
If collect was involved, did it compare ResearchPlan or case intent against InspectResult?
If collect was involved, was CollectDirective approved=true before collect?
If Charles/Arthur artifacts were involved, did it preserve hashes and source paths?
If ScoutReport was involved, did it avoid printing the full report in chat?
If profile/session access was involved, did it avoid storing token values in artifacts?
If working-context files changed, did it write a decision log entry?
If a patch candidate status changed, did it write a decision log entry?
If a protected file changed, was there explicit user instruction?
Did it leave SESSION_NOTE.md or equivalent next-step state when needed?
Did it leave the next session with a clear smallest next action?
```

## 9. Changelog

### v1.1 - 2026-06-11

- Section 0에 document precedence와 protected files를 추가했다.
- `AGENTS.md`를 protected project-wide instruction file로 표시했다.
- 기존 case/run을 재개할 때 최신 관련 `SESSION_NOTE.md`를 먼저 읽는 startup rule을 추가했다.
- Context budget을 fixed startup overhead와 minimum necessary task context로 재정의했다.
- Full ScoutReport는 disk에 보존하고 targeted lookup으로만 로드하는 규칙을 추가했다.
- Working-context mutation rule을 명시했다.
- Patch candidate status transition rules를 추가했다.
- Decision log location을 `_WORKING_CONTEXT/07_DECISION_LOG.md`로 명확히 했다.
- Decision log definition과 required entry cases를 추가했다.
- `DL_CONTEXT_20260611_013`에서 이미 승격한 guest/session token policy를 보존했다.
- Session note update-vs-new rules를 통일했다.
- Session note template에 Self-Check fields를 추가했다.
- Resume notes, decision log entries, protected files, ScoutReport handling, token-value safety를 end-of-session self-check에 추가했다.

### v1.0 - 2026-06-11

- External-audit framing을 solo user + CLI/Codex workflow framing으로 교체했다.
- Context loading, scenario routing, package mutation boundaries, Charles/Arthur alignment gates, session handoff expectations를 정의했다.
