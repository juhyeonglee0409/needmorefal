# User-CLI Workflow - Session Work System

Version: 1.1 (2026-06-11)
Status: applied - canonicalized by explicit user approval on 2026-06-11

Purpose:

```text
Operate solo user + CLI/Codex streamer case work with low context overhead,
preserved source-of-truth boundaries, and explicit approval/alignment gates
for Charles/Arthur pipeline work.
```

This document is for workflow efficiency.

This workflow is case-neutral.

## 0. Document Precedence And Protected Files

This document defines the operating rules for solo user + CLI/Codex workflow inside the Streamer Consulting Project.

Precedence:

- `AGENTS.md` defines project-wide Codex operating constraints.
- `_WORKING_CONTEXT/README.md` is the canonical project context entrypoint and source map.
- `10_USER_CLI_WORKFLOW.md` defines the workflow rules.
- `09_NEW_SESSION_WORKFLOW_SCENARIOS.md` is the scenario router and detail layer.
- If `09_NEW_SESSION_WORKFLOW_SCENARIOS.md` conflicts with this document, this document wins for workflow rules.
- If case references conflict, use the newest canonical reference listed in the package README or reference index.
- If a safety boundary conflicts with an efficiency shortcut, the safety boundary wins.

Protected files:

```text
AGENTS.md
_WORKING_CONTEXT/README.md
_WORKING_CONTEXT/09_NEW_SESSION_WORKFLOW_SCENARIOS.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.md
_WORKING_CONTEXT/10_USER_CLI_WORKFLOW.ko.md
```

Protected files may be changed only by explicit user instruction and with a decision log entry.

Patch candidates under `_WORKING_CONTEXT/PATCH_CANDIDATES/` do not change the canonical workflow until explicitly accepted/applied by the user/operator.

The decision log is `_WORKING_CONTEXT/07_DECISION_LOG.md`. It is append-only for durable workflow decisions and status changes.

## 1. Purpose And Responsibilities

This document governs the managed workflow for solo user + CLI/Codex sessions.

It covers:

- session startup and context loading
- generic streamer case intake
- existing case review and temporary judgment support
- Charles/Arthur pipeline preparation
- exact evidence lookup
- package mutation boundaries
- session handoff through `SESSION_NOTE.md`

Collection is included only when separately authorized by the user/operator. Formal audit bundles are optional and only needed for external sharing or formal review.

| Actor | Does | Must not do |
|---|---|---|
| User / Operator | final judgment, approval, direction | delegate final approval silently |
| User-CLI Orchestration Node | organize context, write specs, support execution, review alignment, create patch candidates | silently mutate source-of-truth or final package state |
| Codex Session in this workflow | temporarily performs Hosea-node process work through session behavior and working-context documents | represent itself as a separate implemented Hosea tool |
| Charles / CrawlScouter | diagnose targets and create ScoutReport/ExecutionProtocol | execute collection |
| Arthur | run inspect/collect from approved protocol/directive | make final judgment |
| Pearson / Susan / ND / BEARING | future storage, QA, absence, cross-check tools | be assumed available now |

In this workflow, the CLI/Codex session plus `_WORKING_CONTEXT` acts as the Hosea-node.
This is a process role, not a separate implemented tool.

## 2. Core Rules

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

Working principle:

```text
Use working context to find the right source quickly. Do not treat working context as final evidence.
```

## 3. Session Start

Every meaningful workspace session starts with the global bootstrap if it has not already been read:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
```

Every meaningful Streamer Consulting Project session then starts with:

1. Read `_WORKING_CONTEXT/README.md`.
2. Classify the task scenario from `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`.
3. If continuing an existing case/run, read the newest relevant `SESSION_NOTE.md` before loading other case context. This is mandatory for Scenario 2 and Scenario 7, and also applies to Scenario 3 when resuming an existing run.
4. Load only the active task context.
5. Use source files by targeted lookup, not broad loading.
6. Write or update `SESSION_NOTE.md` when the session creates durable state, decisions, blockers, or next steps.

Do not load full MASTER, full methodology, old reports, archive packages, full CSV, or full JSON unless the task explicitly requires document revision, QA, comparison, or exact evidence review.

## 4. Context Loading Rules

Fixed startup overhead is not counted against the task-context budget:

- `_WORKING_CONTEXT/README.md`
- the relevant lines of `09_NEW_SESSION_WORKFLOW_SCENARIOS.md`
- the newest relevant `SESSION_NOTE.md` when resuming a case/run

Default limits:

- Task context: load the minimum needed for the current scenario.
- Default maximum: 2 task-context files unless the task clearly requires more.
- Framework: use summary/capsule first.
- Case package: read README and CASE_DOSSIER first if present.
- JSON: inspect top-level keys first.
- CSV: inspect header and first 20 rows first.
- ZIP: list entries before reading contents.
- Legacy: blocked by default unless the user asks for comparison or history.
- Full document loading: allowed only for revision, QA, explicit comparison, or exact evidence review.

Reference role exclusivity:

For each session, load at most one active reference per role.

Roles:

- framework
- methodology
- schema
- active_case
- active_plan
- tool_contract
- runbook

If multiple candidates exist, use the newest canonical reference listed in the current package README or reference index.

Legacy references may be loaded only when the task explicitly asks for comparison, history, or calibration.

Default prohibited behavior:

```text
raw-loading long framework markdown
printing full machine JSON
printing full CSV
reading all zip entries
using one reference case as default structure for all cases
```

Allowed focused lookup:

- source map lookup
- exact `rg -n` search
- specific source lines
- CSV headers and small samples
- JSON top-level keys and named subtrees
- named zip entries only

## 5. Work Scenarios

Use `09_NEW_SESSION_WORKFLOW_SCENARIOS.md` as the detailed router.

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

Minimum session output by scenario:

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

- Charles diagnoses.
- Arthur executes.
- The orchestrator manages scope, files, approvals, and handoff.
- The user/operator approves collection and final judgment.
- Preserve the full ScoutReport on disk.
- Load ScoutReport by targeted lookup only; never print it in full.
- Pass Arthur the top-level `protocol` unless intentionally accepting thin-input `not_verifiable`.
- Compare ResearchPlan or case intent against InspectResult fields before collect.
- Record mismatch as boundary signal or review blocker.
- Do not collect without `CollectDirective.approved=true`.
- Do not store secret profile values.
- Preserve `not_verifiable`, `boundary_signals`, absences, `protocol_hash`, `directive_hash`, and source paths.
- Do not promote CollectionResult directly into CaseResult.

Intent-alignment gate:

Before collect, compare the original ResearchPlan or TargetBatchPlan intent against Arthur InspectResult.

Check:

- does the inspected source actually match the intended cohort or data type?
- are required fields likely available?
- did the source return boundary/checkpoint/manual-review signals?
- is the approved scope still narrow enough?

If mismatch is found, stop or return to operator review.

Run directory when collection is involved:

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

CLI/Codex may create:

- notes
- drafts
- patch candidates
- proposed JSON updates
- run artifacts
- `SESSION_NOTE.md`

CLI/Codex may not silently overwrite:

- `project.json`
- `CaseResult`
- `PortfolioRow`
- `PublicDemoRow`
- `DisclosureLog`
- final client deliverables

Final package mutation requires explicit user approval or a clear user instruction.

Working-context mutation rule:

- CLI/Codex may edit ordinary `_WORKING_CONTEXT` documents when the user request requires it.
- Protected files listed in Section 0 require explicit user instruction.
- Every working-context edit requires a decision log entry unless it is a purely local draft in `_WORKING_CONTEXT/PATCH_CANDIDATES/`.
- Patch candidates are created as `proposed` by default.

Guest/session token policy:

Guest/session profiles may be used when the operator explicitly approves the scope.

Allowed:

- use an operator-approved guest/session profile
- reference a local-only profile file
- record header/cookie names
- record token type, expiry, and scope summary

Not allowed by default:

- paste token values into chat
- store token values in ScoutReport, SESSION_NOTE, RUN_MANIFEST, or other artifacts
- store token values in git-tracked files
- preserve token values in raw HTML, logs, screenshots, or debug output
- leave reusable token values as plaintext artifacts

Record only summaries such as:

```text
profile/session provided: yes
type: guest_session
scope: approved target/domain only
secret_values_logged: false
```

Patch candidate status:

- `proposed`
- `accepted`
- `rejected`
- `applied`
- `superseded`

Default status is `proposed`.

Status transition rules:

- CLI/Codex may set only `proposed` and `superseded`.
- A `superseded` candidate must name the replacing candidate.
- Only the user/operator may set `accepted`, `rejected`, or `applied`.
- `accepted` means the user approved the candidate but it has not been reflected in canonical files or packages yet.
- `applied` means the accepted or explicitly approved change has been executed.
- A candidate may move from `proposed` to `applied` only when the user explicitly instructs application in the same session.
- `rejected` and `applied` are terminal unless the user explicitly instructs rollback or restoration.
- Every status change except initial `proposed` requires a decision log entry.

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
- patch candidate status changes other than initial `proposed`
- package mutation approvals

Session note location:

For collection or pipeline sessions:

```text
runs/{case_id}/{run_id}/SESSION_NOTE.md
```

For ordinary case/package work:

```text
{case_package}/work/session_notes/SESSION_NOTE_{YYYYMMDD}_{task_slug}.md
```

For project working-context maintenance:

```text
_WORKING_CONTEXT/SESSION_NOTE.md
```

Session note update rule:

- Update an existing note only when explicitly continuing the same run.
- For ordinary case/package work, update an existing note only when it is the same task on the same date.
- For project working-context maintenance, update `_WORKING_CONTEXT/SESSION_NOTE.md`.
- Otherwise create a new note.
- Never silently overwrite or delete previous session notes.

For ordinary workflow sessions, one lightweight note is enough:

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

Collection sessions should additionally leave:

- `RUN_MANIFEST.json`
- `CollectDirective`
- `CollectionResult`
- patch candidates, if package updates are proposed

Optional only:

- `AUDIT_BUNDLE`
- detailed loaded-context manifest
- external sharing package

## 8. End-Of-Session Self-Check

Before ending a meaningful session, check:

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

### v1.1 applied - 2026-06-11

- Added Section 0 for document precedence and protected files.
- Marked `AGENTS.md` as a protected project-wide instruction file.
- Added startup rule to read the newest relevant `SESSION_NOTE.md` when resuming an existing case/run.
- Reframed context budget as fixed startup overhead plus minimum necessary task context.
- Added rule to preserve full ScoutReport on disk while loading it only by targeted lookup.
- Added explicit working-context mutation rule.
- Added patch candidate status transition rules.
- Corrected decision log location to `_WORKING_CONTEXT/07_DECISION_LOG.md`.
- Added decision log definition and required entry cases.
- Preserved the guest/session token policy already promoted by `DL_CONTEXT_20260611_013`.
- Unified session note update-vs-new rules.
- Added Self-Check fields to the session note template.
- Expanded end-of-session self-check for resume notes, decision log entries, protected files, ScoutReport handling, and token-value safety.

### v1.0 - 2026-06-11

- Replaced external-audit framing with solo user + CLI/Codex workflow framing.
- Defined context loading, scenario routing, package mutation boundaries, Charles/Arthur alignment gates, and session handoff expectations.
