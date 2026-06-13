# Decision Log

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

Git 전 문서정합 청소 — (A) 봇방어 정책을 work-boundary guide harm-based로 정렬(AGENTS §70 + fence B5; DLG-002의 무조건 B5 문안 대체), (B) Pearson/Susan "미구현" stale 문구를 "구현·테스트됨, 미배선"으로 정정(ND/BEARING은 미구현 유지).

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

Hardened fence B4/B5 wording. B4: CollectDirective-from-Charles prohibition restated as unconditional, with the only legitimate creation cited as the operator-gated pipeline step (10_USER_CLI_WORKFLOW.md C1). B5: split bypass/solver/stealth (now unconditional, no scope exception) from credential/cookie handling (allowed only via the operator-approved ephemeral cookie bridge in exact scope, never to bypass gates). No new permission granted; no prohibition removed.

why:

Head review (Claude Code) found B4/B5 qualifiers ("unless the workflow explicitly calls for it", "outside approved scope") could be read as narrower than the unconditional AGENTS.md prohibitions. A safety fence must be at least as strict as its sources.

authority:

Operator approved the fence hardening patch on 2026-06-13.

boundary:

Fence wording only. No canonical case/package mutation. No new permission. DLG-001/I2 not executed. No protected-file (AGENTS.md/10/README) edits.

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
manual_review/restricted protocols need a bounded browser visibility diagnostic before operator review. The probe improves boundary classification without bypassing login, CAPTCHA, checkpoint, or rate-limit gates. Artifact storage must remain explicit and must not preserve profile/session raw HTML or screenshots.
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
