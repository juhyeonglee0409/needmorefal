# Open Tasks And Gates

## Current Infrastructure Task

Set up efficient context scaffolding for future Codex sessions.

Status:

```text
root bootstrap: created
custom instruction draft: created
project _WORKING_CONTEXT: created
Gunsmith spec package imported: 2026-06-13
IsaacInfra canonical spec paths documented: 2026-06-13
```

## Generic Case Gates

For any streamer case, identify these before analysis or package mutation:

```text
case_id
case_package_dir
analysis_status
execution_status
case_result_status
default_disclosure_tag
open_tasks
missing_assets
```

Generic blocking gates:

- missing EvidencePackage or equivalent evidence inventory
- missing AbsenceInventory when expected assets are absent
- disclosure review absent for external/public use
- open tasks that affect the central recommendation
- execution/tracking assets absent when execution readiness is claimed

## Case-Specific Reference Gates

Keep case-specific gate lists in reference files, not here.

Known reference:

```text
08_REFERENCE_CASE_KIMDALSU.md
```

For any other streamer, derive gates from that streamer's own README/dossier/machine objects.

## Orchestrator Gates

Before implementation:

- choose location for orchestrator source
- spec package has been unzipped into versioned docs under `D:\Codex_Workspace\IsaacInfra`
- choose run output location
- define TargetBatchPlan for the active case; do not reuse another case's targets blindly
- decide whether profile support is needed in first implementation

Current spec documents:

- Charles v0.10.1: `D:\Codex_Workspace\IsaacInfra\Charles\current\CrawlScouter_v0.10.0_pipeline_contract\SPEC_Charles_v0_10_1.md`
- Arthur v0.6.1: `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- Hosea operational: `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md`
- Pearson v0.1: `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract\SPEC_pearson_v0_1.md`
- Susan v0.1: `D:\Codex_Workspace\IsaacInfra\Susan\current\Susan_v0.1_QA_contract\SPEC_susan_v0_1.md`

Before collect:

- Charles protocol exists
- Arthur inspect reviewed
- approved scope narrowed
- field exclude/mask reviewed
- `CollectDirective.approved=true` explicitly authorized

After collect:

- write EvidencePackage patch candidate
- write AbsenceInventory patch candidate
- write DisclosureLog patch candidate
- do not mutate CaseResult without user approval

## Custom Instruction Field

Recommended use:

1. Put only stable bootstrapping rules in the app custom instruction field.
2. Keep project-specific details in `_WORKING_CONTEXT`.
3. If field length is limited, use the short version from `_CUSTOM_INSTRUCTIONS_DRAFT.md`.
