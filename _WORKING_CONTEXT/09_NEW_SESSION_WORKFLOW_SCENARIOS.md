# New Session Workflow Scenarios

Use this when a new Codex session starts. The goal is fast orientation without loading long source documents.

## Scenario 0 - Universal Session Entry

Trigger:

```text
Any new Codex session in this workspace.
```

Read:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md
```

Then classify the user request into one of the scenarios below.

Do not read:

```text
large reports
full framework docs
full machine JSONs
full CSVs
zip entries
```

unless the scenario requires exact evidence.

## Scenario 1 - Generic Streamer Case Intake

Trigger:

```text
User mentions a new streamer or a case package that is not already loaded.
```

Read:

```text
03_STREAMER_CASE_GENERIC_PROTOCOL.md
01_SOURCE_MAP.md
```

Actions:

1. Locate the active case package with `rg --files`.
2. Read package `README.md` and dossier if present.
3. Identify machine objects without raw-loading all JSON.
4. Inspect data file heads only.
5. Produce a short `case_orientation_note`.

Output shape:

```text
case_id:
package_dir:
known_assets:
missing_assets:
current_status:
disclosure_default:
next_gates:
source_paths:
```

Stop condition:

```text
If no case package exists, propose a package skeleton instead of inventing state.
```

## Scenario 2 - Existing Case Review Or Judgment Support

Trigger:

```text
User asks whether a case is ready, publishable, validated, blocked, partial, or comparable.
```

Read:

```text
03_STREAMER_CASE_GENERIC_PROTOCOL.md
05_DECISION_SUPPORT_PROTOCOL.md
06_OPEN_TASKS_AND_GATES.md
```

Then read case-specific README/dossier/machine objects as needed.

Actions:

1. Separate observed facts from recommendation.
2. Check EvidencePackage, AbsenceInventory, DisclosureLog, CaseResult.
3. Identify unresolved gates.
4. Provide `operator_recommendation`, not final judgment.

Output shape:

```text
facts:
blocking_gates:
operator_recommendation:
approval_needed:
remaining_risk:
source_paths:
```

Rule:

```text
Do not promote CaseResult, disclosure status, PublicDemoRow, or absence meaning without user approval.
```

## Scenario 3 - Charles / Arthur Collection Pipeline Setup

Trigger:

```text
User asks to collect, diagnose, run Charles, run Arthur, create TargetBatchPlan, or prepare CollectDirective.
```

Read:

```text
02_TOOL_CONTRACTS_Charles_Arthur.md
04_PIPELINE_ORCHESTRATOR_CONTEXT.md
05_DECISION_SUPPORT_PROTOCOL.md
```

Actions:

1. Validate active case and target plan.
2. Create or inspect `TargetBatchPlan`.
3. Prepare Charles commands.
4. Extract protocol only from ScoutReport.
5. Prepare Arthur inspect commands.
6. Create draft CollectDirective with `approved=false`.
7. Ask for/record operator approval before setting `approved=true`.
8. After collect, create patch candidates only.

Output paths:

```text
runs/{case_id}/{run_id}/00_inputs/
runs/{case_id}/{run_id}/10_charles/
runs/{case_id}/{run_id}/20_review/
runs/{case_id}/{run_id}/30_arthur_inspect/
runs/{case_id}/{run_id}/40_arthur_collect/
runs/{case_id}/{run_id}/50_ingest_candidates/
```

Rules:

```text
Do not pass full ScoutReport to Arthur unless intentionally accepting not_verifiable.
Do not run collect without CollectDirective approved=true.
Do not store profile secret values.
Do not mutate CaseResult from collection output directly.
```

## Scenario 4 - Reference Case Use

Trigger:

```text
User explicitly mentions KimDalsu, Gubiba, or asks for an example/reference.
```

Read:

```text
08_REFERENCE_CASE_KIMDALSU.md     # only for KimDalsu-specific/reference work
```

For other reference cases, locate or create a matching `08_REFERENCE_CASE_<CASE>.md` only if it will be reused.

Actions:

1. Treat the reference case as an example, not the default.
2. Extract transferable pattern.
3. Apply the generic protocol to the active case.

Output shape:

```text
reference_pattern:
active_case_application:
non_transferable_parts:
source_paths:
```

## Scenario 5 - Context Maintenance

Trigger:

```text
User asks to improve setup, reduce context, update protocol, or make future sessions faster.
```

Read:

```text
README.md
01_SOURCE_MAP.md
07_DECISION_LOG.md
```

Actions:

1. Update `_WORKING_CONTEXT` files, not long source documents.
2. Keep generic protocol case-neutral.
3. Move case-specific material into reference files.
4. Append durable decisions to `07_DECISION_LOG.md`.
5. Keep custom instruction draft short.

Output shape:

```text
changed_files:
new_session_effect:
remaining_context_risk:
```

## Scenario 6 - Exact Evidence Lookup

Trigger:

```text
A recommendation needs proof from a source document.
```

Read:

```text
01_SOURCE_MAP.md
```

Actions:

1. Locate likely files.
2. Use `rg -n "<specific term>" "<path>"`.
3. Open only relevant line windows.
4. Cite source paths in the decision note.

Avoid:

```text
Get-Content -Raw on long markdown
printing full JSON
printing full CSV
reading all zip entries
```

## Scenario 7 - Resume After Context Compaction

Trigger:

```text
Session resumes after long work or summary compaction.
```

Read:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
README.md
07_DECISION_LOG.md
06_OPEN_TASKS_AND_GATES.md
```

Actions:

1. Reconfirm newest user request.
2. Check decision log before re-reading sources.
3. Continue from current task; do not restart discovery unless source state changed.
4. If uncertain, search targeted evidence rather than broad-loading context.

Output shape:

```text
current_task:
last_known_decisions:
next_action:
blocked_or_not:
```

## Minimal New Session Script

If a future session needs a literal startup checklist:

```powershell
Get-Content -Raw -Encoding UTF8 -LiteralPath "D:\Codex_Workspace\_CODEX_SESSION_START.md"
Get-Content -Raw -Encoding UTF8 -LiteralPath "D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md"
Get-Content -Raw -Encoding UTF8 -LiteralPath "D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\09_NEW_SESSION_WORKFLOW_SCENARIOS.md"
```

Then choose only the focused context file required by the user's request.
