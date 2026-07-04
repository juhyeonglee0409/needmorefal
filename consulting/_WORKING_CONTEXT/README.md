# Working Context README

This directory is the lightweight context layer for future Codex sessions.

It exists so a new session does not need to raw-load long framework documents, reports, JSON files, CSVs, or zip packages before doing useful work.

## Operating Standard

Always start with:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md
```

This file is the canonical project entrypoint.

Then read the session behavior contract:

```text
11_SESSION_BEHAVIOR_CONTRACT.md
```

Then classify the task using:

```text
09_NEW_SESSION_WORKFLOW_SCENARIOS.md
```

Read only the focused context files needed for that scenario.

## File Roles

| File | Role |
|---|---|
| `README.md` | canonical entrypoint and operating standard |
| `01_SOURCE_MAP.md` | source router |
| `02_TOOL_CONTRACTS_Charles_Arthur.md` | Charles/Arthur contract summary |
| `03_STREAMER_CASE_GENERIC_PROTOCOL.md` | generic streamer case protocol |
| `04_PIPELINE_ORCHESTRATOR_CONTEXT.md` | orchestrator run contract |
| `05_DECISION_SUPPORT_PROTOCOL.md` | temporary judgment support boundary |
| `06_OPEN_TASKS_AND_GATES.md` | generic gates and active setup gates |
| `07_DECISION_LOG.md` | durable decisions |
| `08_REFERENCE_CASE_KIMDALSU.md` | KimDalsu reference only |
| `09_NEW_SESSION_WORKFLOW_SCENARIOS.md` | scenario router |
| `10_USER_CLI_WORKFLOW.md` | solo user + CLI/Codex workflow and session handoff rules |
| `10_USER_CLI_WORKFLOW.ko.md` | Korean translation of the User-CLI workflow |
| `11_SESSION_BEHAVIOR_CONTRACT.md` | implementation session behavior contract |
| `12_CONTINUITY_CONTRACT.md` | cross-surface handoff databook and DECISION_LOG writing rules |
| `COLLECTION_TOOLKIT.md` | collection infrastructure inventory — scripts, profiles, tools, status |
| `handoffs/` | per-session handoff databook and generated recent-state index |
| `site_runbooks/` | site-specific operational runbooks (routes, failures, proven runs) |
| `SESSION_NOTE.md` | legacy pre-databook handoff archive; read only for older history |

## Source Loading Rule

Use source files as evidence, not as startup context.

Default:

```text
working context -> source map -> targeted rg -> relevant source lines
```

Avoid by default:

```text
Get-Content -Raw on long markdown
printing full JSON
printing full CSV
reading whole zip packages
```

## Encoding Rule

Use UTF-8 explicitly for project text artifacts.

Default Windows PowerShell pattern:

```text
Get-Content -Encoding UTF8 -LiteralPath "<path>"
Set-Content -Encoding UTF8 -LiteralPath "<path>"
Add-Content -Encoding UTF8 -LiteralPath "<path>"
$env:PYTHONIOENCODING='utf-8'
```

If Korean text appears garbled, re-read with explicit UTF-8 before editing. Do not patch text that may already be mojibake. Preserve file-specific exceptions such as CSV specs that explicitly require UTF-8 with BOM.

## Case Neutrality

This context layer is generic for streamer consulting cases.

Do not assume the active case is KimDalsu or Gubiba. Those are reference cases/templates only.

For any streamer case, start from:

```text
03_STREAMER_CASE_GENERIC_PROTOCOL.md
```

Use case-specific reference files only when the user explicitly names that case or asks for an example.

## Judgment Boundary

Codex may provide temporary judgment support because the implemented Pearson/Susan are not yet wired to canonical mutation, and ND/BEARING remain unimplemented; final judgment, disclosure, promotion, and collection approval stay with the operator.

Keep judgments as:

```text
operator_recommendation
decision_note
review_note
patch_candidate
remaining_risk
needs_user_approval
```

Do not silently finalize:

```text
CaseResult promotion
disclosure downgrade
PublicDemoRow readiness
absence meaning
CollectDirective approval
```

## Maintenance Rule

When operating policy changes, update:

```text
07_DECISION_LOG.md
```

When a case-specific pattern becomes reusable, move the reusable part into the generic protocol and leave the case-specific remainder in a reference file.

## Working Context Hygiene

`_WORKING_CONTEXT` is a routing layer, not an archive.

- Keep top-level files near 20 or fewer. If the top-level count exceeds 25, review whether related files should move into a subdirectory.
- If one topic needs 3 or more files, create a named subdirectory with its own `README.md` instead of adding more top-level files.
- Every top-level file or directory must appear in the File Roles table above.
- `README.md` remains the canonical entrypoint. Do not make a second master index inside this folder.
- Keep roles separated:
  - `handoffs/`: current handoff and recent state.
  - `SESSION_NOTE.md`: legacy pre-databook handoff history.
  - `07_DECISION_LOG.md`: durable decisions and policy.
  - case run notes: detailed execution evidence for a specific run.
  - `site_runbooks/`: site-specific routes, failures, collection defaults, and proven-run pointers.
  - `03_STREAMER_CASE_GENERIC_PROTOCOL.md`: cross-site reusable rules only.
- Do not duplicate the same operational finding across all documents. Put the summary in the right role document and link to the evidence.
- If `handoffs/INDEX.md`, `SESSION_NOTE.md`, or `07_DECISION_LOG.md` becomes hard to scan, create an archive/index plan first. Do not silently delete, compact, or move active entries.

## Session Workflow

For the lightweight solo user + CLI/Codex operating workflow, use:

```text
10_USER_CLI_WORKFLOW.md
```

Korean translation:

```text
10_USER_CLI_WORKFLOW.ko.md
```
