# Pipeline Orchestrator Context

Source zip:

```text
D:\Codex_Workspace\Streamer Consulting Project\PIPELINE_ORCHESTRATOR_SPEC_PACKAGE_20260611.zip
```

## Purpose

The CLI orchestrator manages execution order, files, approvals, and patches. It is not the final judge.

## Pipeline

```text
A0 run init
A1 Charles phase1 scout
A2 Charles engage profile scout if needed
A3 extract protocol section only
B1 review gate
B2 Arthur inspect
C1 build CollectDirective after approval
C2 Arthur collect
D1 generate ingest patch candidates
D2 manual/Pearson package update later
```

## Run Directory Contract

```text
runs/{case_id}/{run_id}/
  00_inputs/
    target_batch_plan.json
    cohort_spec.json
    profile_summary.json
  10_charles/
    {target_id}.scout_report.json
    {target_id}.protocol.json
    {target_id}.scout_raw/
  20_review/
    {target_id}.review_note.md
    collect_directives/
      {target_id}.CollectDirective.json
  30_arthur_inspect/
    {target_id}.InspectResult.json
  40_arthur_collect/
    {target_id}/
      _meta.json
      items.jsonl
      combined.json
      raw/
    {target_id}.CollectionResult.json
  50_ingest_candidates/
    EvidencePackage_patch.json
    AbsenceInventory_patch.json
    DisclosureLog_patch.json
  RUN_MANIFEST.json
```

## Critical Rules

- Validate target plan before Charles.
- Stop early on localhost/private IP/file path targets.
- Run Charles first; preserve full ScoutReport.
- Extract and save only top-level `protocol` for Arthur canonical input.
- Do not send full ScoutReport to Arthur unless intentionally accepting forced `not_verifiable`.
- Run Arthur inspect before collect.
- Build `CollectDirective.approved=true` only after operator/user approval.
- Generate patch candidates only. Do not promote CaseResult.

## Review Gate Inputs

Read from protocol:

```text
best_path
pre_check.robots_status
pre_check.gate_status
pre_check.login_required
pre_check.terms_flag
pre_check.risk_level
transport
profile_required
diagnostic_findings
```

Do not create collect directive if:

```text
best_path = manual_review
gate_status = restricted / not_attempted / phase2_error
login_required = true and profile missing
profile_required = true and profile missing
risk_level = high and operator approval missing
target-specific bypass appears necessary
approved_scope cannot be narrowed
```

## Patch Candidate Mapping

| Arthur/Charles field | Patch target |
|---|---|
| CollectionResult items/artifacts | EvidencePackage patch |
| absences | AbsenceInventory patch |
| boundary_signals | EvidencePackage + DisclosureLog patch |
| field_coverage | work notes or data quality note |
| verification.status | data quality note |
| protocol_hash/directive_hash | RUN_MANIFEST and EvidencePackage provenance |

`not_verifiable` must be preserved. It is not a reason to discard data by itself.

