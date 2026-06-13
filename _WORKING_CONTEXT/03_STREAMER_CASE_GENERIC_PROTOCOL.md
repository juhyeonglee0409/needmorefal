# Streamer Case Generic Protocol

This is the default protocol for any streamer consulting case. It must not assume the case is 김달수 or 구비바.

## Case-Agnostic State Model

Use these fields for any streamer case:

```text
case_id
case_package_dir
streamer_key
platform
case_type
analysis_status
execution_status
case_result_status
portfolio_row_status
public_demo_status
default_disclosure_tag
```

Common status values:

```text
analysis_status: not_started | collecting | analysis_open | analysis_closed
execution_status: not_started | tracking | execution_open | execution_closed
case_result_status: stub | partial | ready | archived
portfolio_row_status: none | partial_ready | ready
public_demo_status: none | synthetic_candidate | review_required | ready
default_disclosure_tag: red | yellow | green
```

## Generic Package Shape

A well-formed streamer case package should usually contain:

```text
README.md
CASE_DOSSIER.md or <case>_CASE_DOSSIER_v*.md
MANIFEST.json

machine/
  <case>_CaseResult*.json
  <case>_EvidencePackage*.json
  <case>_AbsenceInventory*.json
  <case>_DisclosureLog*.json
  schema/

data/
  daily_stats/
  cohort/
  cohort/specs/

deliverables/
  milestone_report/
  roadmap/
  reporting_tools/
  anonymized/

source_inputs/
references/
work/
archive/
```

Not every case will have every directory. Missing expected assets should be recorded as absences, not silently ignored.

## Generic Workflow

For any streamer case:

1. Read the case package README/dossier if present.
2. Identify machine objects: CaseResult, EvidencePackage, AbsenceInventory, DisclosureLog.
3. Determine current status and blocking gates.
4. Identify data assets and their shapes with file heads, not full raw reads.
5. Use exact source lookup only when a claim or recommendation needs evidence.
6. Keep disclosure default at red unless a specific review says otherwise.
7. Treat public demo output as synthetic/anonymized until reviewed.

## Generic Data Assets

Typical data categories:

```text
channel_stats
cohort_population
cohort_final
follower_rank
category_rank
interview_or_manual_review
client_deliverable
external_validation
```

When reading CSVs, first inspect only:

```powershell
Get-Content -Encoding UTF8 -TotalCount 5 -LiteralPath "<csv>"
```

## Generic Decision Gates

Do not promote `CaseResult` to ready unless:

- analysis milestone is complete or explicitly waived
- evidence references are present
- major absences are resolved or intentionally accepted
- disclosure boundary is reviewed
- execution/tracking state is clear
- open tasks are closed, deferred, or explicitly accepted

Do not create `PublicDemoRow` from a real client case unless:

- disclosure review allows it, or
- the row is explicitly synthetic/anonymized

## Generic Collection Pipeline

Use the same Charles/Arthur pipeline for any case:

```text
TargetBatchPlan
-> Charles ScoutReport
-> protocol extraction
-> review gate
-> Arthur InspectResult
-> CollectDirective
-> Arthur CollectionResult
-> Evidence/Absence/Disclosure patch candidates
```

Case-specific target plans may be named after a case, but the protocol remains case-agnostic.

## Output Discipline

When Codex provides judgment support, write it as:

```text
operator_recommendation
decision_note
review_note
patch_candidate
remaining_risk
needs_user_approval
```

Do not hide uncertainty by overfitting to a previous case. If the active case lacks an asset seen in another case, record the actual absence and ask whether to create it.
