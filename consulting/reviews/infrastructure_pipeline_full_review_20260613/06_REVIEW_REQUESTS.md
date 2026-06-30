# 06 Review Requests

## Review Questions Answered

1. Is the infrastructure coherent?

Answer: yes, with issues. The architecture is coherent and the separation rules are unusually clear. The main issues are enum drift, storage/path hygiene, and incomplete Pearson/Susan patch handoff.

2. What is the current MVP maturity?

Answer: strong internal pilot / late prototype. Charles/Arthur and core docs are usable. Pearson/Susan now execute in smoke tests, but repeated case package mutation is not ready.

3. What is the biggest bottleneck?

Answer: not conceptual design. The bottleneck is operational repeatability: path length, profile isolation, and the missing patch-candidate handoff from Pearson/Susan outputs to case package objects.

4. What is the next smallest MVP gate?

Answer: an offline short-path Pearson/Susan pre-ingest and QA gate using the existing CHZZK CollectionResult, followed by generation of review-only patch-candidate JSON objects. Do not mutate the case package.

5. Are filesystem, schema, tools, workflow, cases, pipeline, runtime aligned?

Answer: mostly aligned at the policy and test-contract level; not fully aligned at storage layout, status enum, and runtime asset isolation levels.

6. What must be fixed now vs later?

Answer:

- P0 before next MVP gate: short storage root/path guard; move/exclude Chrome profile runtime assets from review/package scan roots.
- P1 before repeated operation: enum alignment; Pearson/Susan patch-candidate handoff; test/dev environment policy.
- P2/P3 later: folder README consistency, archive hygiene, local DB, ND/BEARING automation.

## Exact Next Gate Proposed

Target:

Existing CHZZK public profile `CollectionResult` from KimDalsu recollect run.

Inputs:

- `40_arthur_collect\results\chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json`
- source approved directive
- source protocol hash and operator directive hash
- short Pearson storage root such as `D:\Codex_Workspace\_tmp\p_smoke` or a new short canonical root

Steps:

1. Store with Pearson in a short path.
2. Validate StorageReceipt.
3. Run Susan QA.
4. Generate review-only patch candidates:
   - EvidencePackage patch candidate
   - AbsenceInventory patch candidate, probably empty/no-op
   - DisclosureLog patch candidate or no-op review note
5. Confirm no canonical case package file changes.

Pass criteria:

- Pearson writes StorageReceipt and derived artifacts.
- Susan QAReport preserves `not_verifiable` as conditional.
- protocol/directive hashes are retained.
- no raw body/html/screenshot/secret storage is created.
- patch candidates are review-only and do not mutate CaseResult.

Fail criteria:

- path length failure
- `not_verifiable` converted to pass/fail without operator review
- any canonical package mutation
- profile/session/raw artifact leakage
- missing source path/hash lineage

Do not do:

- no Softcon live retry
- no approved=true CollectDirective expansion
- no PublicDemoRow creation
- no CaseResult promotion

