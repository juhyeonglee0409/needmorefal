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

## Browser-Bound Collection Failure Matrix

Site-specific working routes, failure patterns, and proven runs are maintained in `_WORKING_CONTEXT/site_runbooks/`. Below are the generic principles.

When a source is checkpoint-gated or browser-session-bound, separate the policy boundary from the technical execution path.

Reusable handling:

- Do not export or persist cookies, localStorage, session tokens, auth headers, or account secrets.
- Use only an operator-approved browser session for bounded observation/collection.
- CDP or persistent browser context is an execution transport, not a permission grant.
- Record the confirmed canonical URL pattern once discovered; do not keep retrying dead URL variants.
- Prefer structured API/RSC extraction when it is visible without secret persistence.
- If no stable API exists and rows are rendered in the browser, DOM row extraction is an acceptable primary path when verified by downstream schema checks.
- Treat UI download buttons as opportunistic. If framework/user-gesture/visibility handling makes them automation-unstable, use DOM extraction rather than repeated clicking.
- Stop and preserve the boundary on 429 loops, repeated challenge loops, scope expansion, private/account data, or secret persistence uncertainty.

Observed SOFTC.ONE Step5 route:

- Source is checkpoint-gated and requires a user-approved browser session.
- Canonical streams path: `/channel/{platform}/{channelId}/streams`.
- `CSV 다운로드` is not automation-stable in current observations.
- DOM row extraction is the primary §5 broadcast-record path unless later verification shows data loss.
- Cookie/localStorage/session export remains prohibited.

SOFTC.ONE Step5 full-range guard:

- Do not assume the default date window is the requested collection window. Verify the UI/input/query state before batch collection.
- For full-history collection, record the exact UTC query bounds and the visible UI range label in the run artifact.
- Current verified full-range query shape: `?startDateTime={iso_utc}&endDateTime={iso_utc}` on `/streams`.
- Use a scale ladder before full batch: small single-worker smoke, then gradual concurrency/delay changes, with a separate manifest/progress/error file for each rung.
- Apply `skipExisting` before `limit` in resume smoke tests so the smoke covers the next missing targets, not already collected files.
- Distinguish `not_found`/source path errors from rate-limit or challenge boundaries. Do not treat `not_found` as a 429/checkpoint signal.
- If the visible DOM exposes a fixed row cap, record it as an extraction cap/residual risk, not as evidence that older broadcasts are absent.

## Output Discipline

When the session provides judgment support, write it as:

```text
operator_recommendation
decision_note
review_note
patch_candidate
remaining_risk
needs_user_approval
```

Do not hide uncertainty by overfitting to a previous case. If the active case lacks an asset seen in another case, record the actual absence and ask whether to create it.
