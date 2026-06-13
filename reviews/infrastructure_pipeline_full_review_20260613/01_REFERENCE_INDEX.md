# 01 Reference Index

## Working Context

| Reference | Purpose |
|---|---|
| `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md` | project entrypoint and loading policy |
| `01_SOURCE_MAP.md` | source router |
| `02_TOOL_CONTRACTS_Charles_Arthur.md` | Charles/Arthur/Pearson/Susan current contract summary |
| `03_STREAMER_CASE_GENERIC_PROTOCOL.md` | generic case package and state model |
| `04_PIPELINE_ORCHESTRATOR_CONTEXT.md` | run directory and approval gate contract |
| `05_DECISION_SUPPORT_PROTOCOL.md` | temporary judgment-support boundary |
| `06_OPEN_TASKS_AND_GATES.md` | generic gates and orchestrator gates |
| `10_USER_CLI_WORKFLOW.md` | solo user + CLI/Codex workflow |

## Canonical / Current Specs

| Component | Path | Status Observed |
|---|---|---|
| IsaacInfra index | `D:\Codex_Workspace\IsaacInfra\GUNSMITH_SPECS_INDEX_20260613.md` | consolidated spec package index |
| Charles | `D:\Codex_Workspace\IsaacInfra\Charles\current\CrawlScouter_v0.10.0_pipeline_contract` | CLI version `CrawlScouter 0.10.1` |
| Arthur | `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract` | CLI version `ArthurCrawler 0.6.1` |
| Hosea | `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md` | operational spec, not separate automation runtime |
| Pearson | `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract` | CLI version `Pearson 0.1.0` |
| Susan | `D:\Codex_Workspace\IsaacInfra\Susan\current\Susan_v0.1_QA_contract` | CLI version `SusanGrimshaw 0.1.0` |
| Pearson/Susan queue | `D:\Codex_Workspace\Instruction\PEARSON_SUSAN_IMPLEMENTATION_BUILD_QUEUE_20260613.md` | P0-P8 and S0-S8 implemented according to queue |

## MASTER / Methodology / Schema

| Reference | Evidence Used |
|---|---|
| `MASTER_streamer_mcn_framework_v2_draft_M7_1_QA2_patched_20260610.md` | headings and targeted Bridge/PublicDemo/status lines |
| `스트리머_채널진단_방법론_v3_draft_START_20260610.md` | headings and targeted data/Bridge/disclosure lines |
| `MASTER_v2_M7_1_canonical_schema_pack_20260610.json` | top-level keys and object/status fields |
| `MASTER_v2_M7_1_canonical_enum_table_20260610.csv` | header and status enum rows |
| `MASTER_v2_M7_1_disclosure_boundary_matrix_20260610.csv` | header and first rows |

## Case Packages

| Case | Path | State Observed |
|---|---|---|
| KimDalsu | `D:\Codex_Workspace\Streamer Consulting Project\김달수_CASE_PACKAGE_v3_20260611` | CaseResult `partial`; PortfolioRow `partial_ready`; DisclosureLog `red/defer` |
| Gubiba | `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611` | CaseResult `not_ready` in JSON, README calls it stub; PortfolioRow `not_ready`; PublicDemoRow `blocked`; DisclosureLog `red/blocked` |
| KimDalsu TargetBatchPlan | `D:\Codex_Workspace\Streamer Consulting Project\KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611` | 8 targets; CollectDirective templates all `approved=false` |

## Run Evidence

| Reference | Evidence Used |
|---|---|
| `runs\kimdalsu_20260601\recollect_20260611_prep\RUN_MANIFEST.json` | Charles/Arthur/collect approval, result lineage, patch/review notes |
| `SESSION_NOTE.md` | handoff, blockers, no-promotion boundary |
| `40_arthur_collect\results\softcon_subject_smoke_collect_20260612.CollectionResult.json` | executed but stopped at checkpoint; zero items; boundary evidence |
| `40_arthur_collect\results\chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json` | one public profile item; `not_verifiable`; no canonical mutation |
| `20_review\post_collect_evidence_review_chzzk_subject_profile_20260613.md` | fresh evidence candidate review and mapping recommendation |
| `20_review\kimdalsu_recollection_flow_status_roadmap_20260613.md` | current run status and roadmap |

## Local Test Evidence

Direct-run tests passed:

- Pearson CLI: `13 PASS / 0 FAIL`
- Pearson artifact layer: `15 PASS / 0 FAIL`
- Susan CLI: `20 PASS / 0 FAIL`
- Arthur CLI: `27 PASS / 0 FAIL`
- Arthur chrome_profile collect: `41 PASS / 0 FAIL`
- Arthur protocol loader: `46 PASS / 0 FAIL`
- Arthur pipeline contract: `16 PASS / 0 FAIL`
- Charles pipeline contract: `11 PASS / 0 FAIL`
- Pearson/Susan integration smoke: `58 PASS / 0 FAIL`

Current bundled Python lacks `pytest`, so `python -m pytest` fails with `No module named pytest`. The project tests are mostly standalone and were run directly.

