# 02 System Map

## Intended Chain

```text
User / Operator
  -> User-CLI workflow as temporary Hosea-node
  -> TargetBatchPlan / ResearchPlan
  -> Charles ScoutReport
  -> top-level ExecutionProtocol extraction
  -> operator review
  -> Arthur InspectResult
  -> intent-alignment gate
  -> CollectDirective approved=false draft
  -> operator-approved approved=true copy
  -> Arthur CollectionResult
  -> Pearson StorageReceipt
  -> Susan QAReport
  -> operator decision
  -> EvidencePackage / AbsenceInventory / DisclosureLog patch candidates
  -> manual approved package mutation later
  -> CaseResult
  -> Bridge
  -> PortfolioRow / DecisionCard / PublicDemoRow
```

## Component Roles

| Component | Role | Must Not Do |
|---|---|---|
| MASTER | overall framework, disclosure and portfolio architecture | execute collection |
| Channel diagnosis methodology | individual deep-dive workflow | replace Bridge or public-demo review |
| User-CLI workflow | low-context human-operated orchestration | silently approve final state |
| Charles | diagnose and produce ScoutReport/ExecutionProtocol | collect data |
| Arthur | inspect/collect under protocol/directive gates | interpret strategic meaning |
| Pearson | append-only storage/pre-ingest receipt | promote canonical package data |
| Susan | QA/state-preservation/absence advisory | mutate CaseResult or DisclosureLog |
| ND | future absence interpretation engine | currently not implemented |
| BEARING | future cross-check layer | currently not implemented |
| Bridge | transform ready CaseResult to portfolio objects | invent new claims |

## Separation Rules Observed

Strongly represented in current docs and tests:

- context routing is not source evidence
- diagnosis is not execution
- execution is not judgment
- recommendation is not operator approval
- patch candidate is not canonical mutation
- CollectionResult is not CaseResult
- PublicDemoRow is not a redacted PortfolioRow
- `not_verifiable` is not pass/fail
- browser profile values must not be persisted

## Main Architectural Drift

The generic working-context status vocabulary diverges from M7.1 canonical enums:

- Working context says `case_result_status: stub | partial | ready | archived`.
- M7.1 says `case_result_status: not_ready | partial | ready`.
- Working context says `portfolio_row_status: none | partial_ready | ready`.
- M7.1 says `portfolio_row_status: not_ready | partial_ready | portfolio_ready`.
- Working context says `public_demo_status: none | synthetic_candidate | review_required | ready`.
- M7.1 says `public_demo_status: blocked | synthetic_candidate | public_demo_ready`.

Impact: validators and human notes can disagree on readiness state unless a transition map is added or the working context is patched.

## Current Handoff Gap

Pearson and Susan now run, but the stable case-package handoff is not complete:

```text
StorageReceipt + QAReport
  -> EvidencePackagePatchCandidate
  -> AbsenceInventoryPatchCandidate
  -> DisclosureLogPatchCandidate
  -> CaseResultPatchCandidate
```

This mapping is documented as a desired direction but not yet implemented as a first-class package contract.

