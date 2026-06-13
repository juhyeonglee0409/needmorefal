# Overall Infrastructure + Pipeline Review

## 1. Executive Verdict

- Overall maturity: strong internal pilot / late prototype
- MVP status: usable for bounded internal gates, not ready for repeated case-package promotion
- Biggest strength: separation of diagnosis, execution, storage, QA, judgment, disclosure, and public-demo objects is explicit and mostly enforced by docs, tests, and run notes
- Biggest risk: operational repeatability breaks at the filesystem/runtime layer, especially Windows path length and copied Chrome profile runtime assets under active run folders
- Most important missing implementation: first-class Pearson/Susan to EvidencePackage/AbsenceInventory/DisclosureLog/CaseResult patch-candidate handoff
- Next required gate: short-path offline Pearson/Susan pre-ingest + QA + review-only patch-candidate smoke on the existing CHZZK CollectionResult
- One-sentence final judgment: the system is coherent enough for an internal MVP gate, but storage layout, runtime profile isolation, enum alignment, and patch-candidate handoff must be tightened before repeated operation.

## 2. Component Scores

| Component | Score /10 | Verdict | Notes |
|---|---:|---|---|
| MASTER Framework | 8.0 | PASS WITH ISSUES | Strong Deep-Dive -> CaseResult -> Bridge -> Portfolio/PublicDemo separation; still a draft/workbench, not production governance. |
| Diagnosis Methodology | 7.5 | PASS WITH ISSUES | Covers data, cohorts, absences, execution, Bridge, disclosure; still cost-heavy and case-count-light. |
| Bridge / Portfolio Layer | 6.5 | PASS WITH ISSUES | Concept is clear; implementation remains mostly schema/procedure, not an executable adapter. |
| User-CLI Workflow | 8.0 | PASS | Low-context startup and scenario routing are practical; SESSION_NOTE discipline is good. |
| Charles/Arthur Pipeline | 8.5 | PASS WITH ISSUES | Contracts and tests are strong; Softcon profile inspect/collect parity remains unresolved. |
| Schema Pack | 7.0 | PASS WITH ISSUES | M7.1 identity/disclosure/status fields are strong; working-context enum drift must be fixed. |
| Case Package Design | 7.0 | PASS WITH ISSUES | Human/machine/data/archive split is sound; helper docs and status wording are uneven. |
| Data Collection Readiness | 6.0 | PASS WITH ISSUES | TargetBatchPlan and column contracts are strong; only one fresh evidence candidate is package-adjacent. |
| Filesystem Hygiene | 5.5 | PASS WITH ISSUES | Active context is small; copied Chrome profile and `_inbox` dominate scans and storage. |
| Runtime / Hardware | 6.0 | PASS WITH ISSUES | Windows + 12 logical processors can run MVP; hardware/storage details are partly unknown under sandbox. |
| Storage / Backup | 4.5 | BLOCKED FOR REPEATABILITY | Pearson works on short path but fails at 260-char nested path; backup/cold-storage policy not proven. |
| Tooling / Dependencies | 7.0 | PASS WITH ISSUES | CLI versions and direct tests pass; `pytest`, `uv`, `jq`, `node` are not on PATH. |
| Security / Profile Handling | 5.5 | PASS WITH ISSUES | Secret-value policies are strong; real Chrome profile copy inside run folder is a scan/package risk. |
| MVP Readiness | 6.5 | PASS WITH ISSUES | Internal gate-ready if scoped narrowly; not ready for repeated case promotion. |
| Productization Readiness | 4.0 | BLOCKED | Too much human judgment, too few completed cases, no public-demo path, no stable storage/patch lifecycle. |

Area verdicts:

| Area | Verdict | Strengths | Risks | Concrete Fixes | Priority |
|---|---|---|---|---|---|
| A. Architecture Coherence | PASS WITH ISSUES | Separation model is coherent. | Bridge and downstream automation are not fully executable. | Define Bridge/Pearson/Susan patch handoff. | P1 |
| B. Workflow Efficiency | PASS | Startup context is 2-5 files; source map works. | Broad searches can hit runtime/profile blobs. | Add exclude patterns and source-map-first search policy. | P1 |
| C. Tool Pipeline Safety | PASS WITH ISSUES | Approval gates and boundary signals are preserved. | Softcon inspect/collect parity unresolved. | Synthetic transport parity harness before live retry. | P1 |
| D. Schema Quality | PASS WITH ISSUES | M7.1 identity/disclosure objects are strong. | Status enum drift in working context. | Patch generic protocol to M7.1 or add transition map. | P1 |
| E. Case Package Design | PASS WITH ISSUES | Human/machine/archive split is good. | Package helper docs inconsistent. | Add lightweight folder READMEs and status enum consistency. | P2 |
| F. Data Collection Readiness | PASS WITH ISSUES | Column contracts include provenance/boundaries. | Broad cohort/rank/public crosscheck incomplete. | Next small public-source gate before larger collect. | P1 |
| G. Filesystem Hygiene | PASS WITH ISSUES | Active context stays small. | Chrome profile and `_inbox` pollute scans. | Move/exclude runtime and cold archive roots. | P0/P1 |
| H. Runtime / Hardware | PASS WITH ISSUES | Windows runtime can execute tools. | physical storage/RAM/GPU unknown; path length issue observed. | Document hardware inventory; enforce short paths. | P1 |
| I. Tooling / Version Management | PASS WITH ISSUES | Versions and standalone tests pass. | no pytest/dev env pin visible. | Pin or document direct-test harness. | P1 |
| J. Lifecycle / Backup | BLOCKED FOR REPEATABILITY | Archive role is documented. | backup/cold storage policy not executable. | Define active/run/archive/backup roots. | P1 |
| K. Security / Profile | PASS WITH ISSUES | Secret values are blocked in policy/tests. | profile content is copied into run tree. | reference profile outside packages; store summaries only. | P1 |
| L. MVP Readiness | PASS WITH ISSUES | Internal gate feasible. | package promotion path still manual. | run offline pre-ingest patch-candidate gate. | P0 |
| M. Productization Risk | BLOCKED | architecture can become product. | manual bottleneck, few cases, no public demo, storage risk. | stabilize repeatable private MVP first. | P2/P3 |

## 3. MVP Maturity Matrix

| MVP Area | Status | Evidence | Missing Piece | Next Action |
|---|---|---|---|---|
| Documentation MVP | done | Working context, MASTER, methodology, tool specs exist. | Minor drift cleanup. | Patch status vocabulary. |
| Schema MVP | partial | M7.1 schema pack defines key objects. | Working-context enum drift and patch-candidate schemas. | Align enums and define patch objects. |
| Case Package MVP | partial | KimDalsu/Gubiba packages exist with machine objects. | Uniform helper docs and package-ready handoff. | Add package consistency checklist. |
| User-CLI Workflow MVP | done | Scenario router and SESSION_NOTE workflow are active. | Search excludes for runtime assets. | Add profile/runtime exclusion rule. |
| Charles/Arthur Contract MVP | done | CLI versions and contract tests pass. | Softcon transport parity unresolved. | Keep next live retry blocked. |
| Inspect-level Pipeline MVP | partial | Arthur inspect artifacts exist; CHZZK inspect/collect aligned. | InspectResult to ResearchPlan gate not fully machine-enforced. | Make alignment checklist machine-readable. |
| Collect-level Pipeline MVP | partial | Approved bounded CHZZK collect exists. | General repeated collect safety for profile sources. | Use only exact approved public/API scope. |
| Evidence/Patch MVP | partial | Review notes map CollectionResult to evidence candidate. | First-class patch candidate files/contracts. | Generate review-only patch candidates. |
| CaseResult MVP | partial | KimDalsu partial, Gubiba not_ready. | Fresh evidence ingestion not promoted. | Keep no-mutation gate. |
| PortfolioRow MVP | partial | KimDalsu partial PortfolioRow exists. | Bridge adapter not executable. | Define Bridge readiness adapter later. |
| PublicDemoRow MVP | blocked | M7.1 object exists; real cases blocked/red. | Disclosure-approved synthetic/anonymized row. | Do not generate from real row yet. |
| Pearson MVP | partial | CLI works; tests pass; short-path store succeeds. | Long-path failure and package handoff. | Add short root/path-length guard. |
| Susan QA MVP | partial | QA/validate works; integration tests pass. | Deep alignment with ResearchPlan/InspectResult limited. | Feed inspect/research paths in next smoke. |
| ND Engine MVP | not_started | Architecture references ND. | No executable interface. | Keep human absence judgment. |
| BEARING MVP | not_started | Roadmap references BEARING. | No executable cross-check layer. | Defer. |
| Productization Readiness | blocked | Internal workflow exists. | repeatability, case count, public-demo governance, storage policy. | Stabilize private MVP first. |

## 4. P0 Blockers

Issue:
Pearson/Susan storage path can fail in realistic nested project paths on Windows.

Why it blocks:
The next MVP gate requires storing an existing CollectionResult and producing a QAReport. Pearson failed under the review package path at a 260-character `normalized_items.csv` path, while the same input succeeded under a short `_tmp` root.

Affected files/modules:

- `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract\pearson\store.py`
- `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract\pearson\artifact_layer.py`
- future Pearson storage root policy

Fix:
Before the next gate, run Pearson/Susan under a short canonical root or patch Pearson to shorten target keys and fail early with a path-length diagnostic. Add one regression test using a nested Windows-style path.

Owner:
Operator/Codex for policy; Pearson implementation owner for code hardening.

## 5. P1 Fixes

- Move or quarantine Chrome profile runtime assets outside `runs/` and store only local reference summaries in run inputs.
- Add default exclude patterns for `local_chrome_profiles`, browser storage, raw HTML/screenshots, `_inbox`, and large archive folders.
- Align `_WORKING_CONTEXT/03_STREAMER_CASE_GENERIC_PROTOCOL.md` status enums with M7.1 canonical values or define an explicit transition map.
- Define first-class patch candidate schemas for EvidencePackage, AbsenceInventory, DisclosureLog, and CaseResult candidates.
- Add a clear local test policy: direct standalone tests are acceptable, or pin a dev env with `pytest`, `ruff`, and `mypy`.
- Keep Softcon live retry blocked until a synthetic transport parity harness or exact operator-approved route/profile plan passes.
- Add a root-level repo/ignore decision if this workspace will be versioned.

## 6. P2/P3 Improvements

- Add `machine/README.md` or equivalent folder guides to Gubiba and future packages.
- Move IsaacInfra `_inbox` to cold archive or mark it lookup-only with stronger tooling excludes.
- Add hardware/storage inventory outside sandbox: RAM, disk type, external HDD/SSD, backup cadence.
- Introduce DuckDB/SQLite only after two source families pass file-backed Pearson/Susan and patch-candidate handoff.
- Build ND and BEARING after Pearson/Susan handoff stabilizes; do not block the human-operated MVP on them.
- Create a synthetic PublicDemoRow fixture, not derived from a real client row.

## 7. Infrastructure / Filesystem Recommendation

- Active workspace recommendation: keep `_WORKING_CONTEXT`, current specs, active case packages, and active run manifests in the workspace; move volatile browser profiles and cold legacy bundles outside default scan roots.
- Canonical files recommendation: treat M7.1 schema pack, current tool specs, case README/dossier, machine JSON, RUN_MANIFEST, and SESSION_NOTE as canonical or routing sources depending on their role.
- Archive / legacy policy: archive remains lookup-only; legacy reports are calibration/reference only, never fresh evidence.
- Browser profile handling: do not copy profile directories into case/run packages by default. Use local-only profile references, summary JSON, and exact approval scope. Exclude profile content from review packages, search, and backup bundles unless the operator explicitly snapshots runtime state.
- Raw/run artifact handling: keep ScoutReports, protocols, InspectResults, CollectionResults, and receipts in run-specific paths with hashes. Raw HTML/screenshots require explicit approval and should be suppressed in profile/session contexts.
- Gitignore/exclude suggestions: add ignores/excludes for `local_chrome_profiles/`, `Cookies`, `Login Data`, `Local State`, `Session Storage`, `Network`, raw browser artifacts, `__pycache__/`, `_inbox/`, and generated smoke stores.
- Storage layout recommendation: use a short active artifact root such as `D:\CWS_RUNS\` or `D:\Codex_Workspace\_store\` for Pearson/Susan, then reference receipts from review notes.
- Backup recommendation: active SSD for current workspace and short store; external HDD for cold archives; optional external SSD for run artifacts; cloud only for redacted or encrypted non-secret artifacts.

## 8. Tooling Recommendation

- Charles: keep v0.10.1 as current; preserve browser_probe safety and CHZZK API body summary behavior; avoid raw artifacts in profile/session contexts.
- Arthur: keep v0.6.1 as current; keep chrome_profile collect directive-gated, exact-scope, no durable secrets.
- Python environment: Codex Python 3.12.13 can run CLIs; add a dev/test env if repeated test runs should use `pytest`.
- uv/venv: introduce a small pinned venv/uv env for repeatable tests, but do not make it a prerequisite for operator review notes.
- Browser runtime: use only operator-approved profiles; prefer reference paths over copied profile trees.
- RUN_MANIFEST: continue recording protocol hash, directive hash, approved copy, output paths, operator approval, and no-promotion notes.
- Dependency pinning: tool packages have pyproject metadata; add lock/requirements for the combined review/test environment later.
- Test policy: keep standalone contract tests as the no-install smoke path; add one path-length regression and one full Pearson/Susan real-artifact smoke.

## 9. Schema Recommendation

- Fields to add: patch-candidate object schemas with `source_collection_path`, `storage_receipt_path`, `qa_report_path`, `protocol_hash`, `directive_hash`, `candidate_status`, `operator_approval_required`, and `canonical_mutation_allowed=false`.
- Fields to remove: do not remove M7.1 fields now; deprecations are already documented for `privacy_tag`, `privacy_alias`, and `streamer_id`.
- Enum drift: align working context to `case_result_status=not_ready|partial|ready`, `portfolio_row_status=not_ready|partial_ready|portfolio_ready`, `public_demo_status=blocked|synthetic_candidate|public_demo_ready`.
- Over-heavy objects: CaseResult is heavy but acceptable for canonical state; Bridge/Portfolio objects should remain thinner and reference evidence instead of duplicating raw claims.
- Missing objects: `EvidencePackagePatchCandidate`, `AbsenceInventoryPatchCandidate`, `DisclosureLogPatchCandidate`, `CaseResultPatchCandidate`, and `BridgeReadinessReport`.
- Object promotion gates: StorageReceipt/QAReport can only become patch candidates; patch candidates can only become canonical package mutation after operator approval.

## 10. Pipeline Safety Recommendation

- Approval gates: keep `CollectDirective.approved=false` drafts and operator-created `approved=true` copies. Record exact approval source, allowed URLs, fields, max requests, runtime, raw artifact policy, and profile policy.
- Intent-alignment gate: make the ResearchPlan/TargetBatchPlan vs InspectResult checklist machine-readable for the next iteration.
- Boundary signals: preserve checkpoint, HTTP 429, login/session, CAPTCHA, private/internal scope, robots, and policy stops as data-quality facts.
- `not_verifiable`: preserve as conditional; do not launder to pass, do not discard automatically.
- Secret/profile handling: prohibit durable cookie/token/auth/header/browser storage values; allow only exact-origin, memory-only session delegation when explicitly approved.
- Patch candidate lifecycle: CollectionResult -> Pearson StorageReceipt -> Susan QAReport -> review-only patch candidates -> operator decision -> canonical mutation.
- CaseResult promotion control: no CollectionResult, StorageReceipt, or QAReport can directly mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.

## 11. MVP Gate Test Recommendation

Target:
Existing CHZZK subject public profile CollectionResult from KimDalsu recollect run.

Inputs:

- `D:\Codex_Workspace\Streamer Consulting Project\runs\kimdalsu_20260601\recollect_20260611_prep\40_arthur_collect\results\chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json`
- approved directive path from the same run
- short Pearson storage root
- no live web access

Steps:

1. Store the CollectionResult with Pearson under a short storage root.
2. Validate the StorageReceipt.
3. Run Susan QA with the StorageReceipt.
4. Generate review-only patch candidates for EvidencePackage and any necessary AbsenceInventory/DisclosureLog no-op notes.
5. Verify no canonical package file changed.

Expected outputs:

- StorageReceipt
- derived Pearson artifacts
- QAReport
- EvidencePackage patch candidate or draft review note
- explicit no-op AbsenceInventory/DisclosureLog note if no absences/disclosure mutation are proposed
- gate report recording `not_verifiable` and no canonical mutation

Pass criteria:

- Pearson writes successfully without path-length failure.
- Susan returns valid QAReport.
- `verification_status=not_verifiable` is preserved as conditional.
- protocol/directive hashes and source paths are retained.
- no raw body/html/screenshot/secret artifacts are created.
- no CaseResult, DisclosureLog, PublicDemoRow, or canonical package file changes.

Fail criteria:

- path-length failure
- missing lineage/hash
- `not_verifiable` translated to pass/fail without operator review
- any canonical mutation
- any profile/session/raw secret leakage

Do not do:

- do not run live Softcon collect
- do not expand `approved=true` scope
- do not create PublicDemoRow
- do not promote CaseResult

## 12. Final Recommendation

1. Define and use a short Pearson/Susan storage root, then rerun the CHZZK CollectionResult pre-ingest/QA gate there.

2. Patch the enum drift between `_WORKING_CONTEXT/03_STREAMER_CASE_GENERIC_PROTOCOL.md` and M7.1 canonical statuses.

3. Move Chrome profile runtime assets out of run/package scan roots and replace them with local-only profile reference summaries plus exclude rules.

