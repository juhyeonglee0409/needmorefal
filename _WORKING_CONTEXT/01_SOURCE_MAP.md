# Source Map

Use this as the router. Do not load every source file.

## Root Session Files

| File | Purpose | When to read |
|---|---|---|
| `D:\Codex_Workspace\_CODEX_SESSION_START.md` | global bootstrap | every new session |
| `D:\Codex_Workspace\_CUSTOM_INSTRUCTIONS_DRAFT.md` | app custom instruction draft | when configuring the app instruction field |
| `D:\Codex_Workspace\instruction\*.md` | original root operating instructions | only when auditing or revising the operating doctrine |

## IsaacInfra Tool Sources

| Area | Path | Use |
|---|---|---|
| IsaacInfra specs index | `D:\Codex_Workspace\IsaacInfra\GUNSMITH_SPECS_INDEX_20260613.md` | consolidated tool spec package index |
| IsaacInfra README | `D:\Codex_Workspace\IsaacInfra\README.md` | canonical spec paths and compatibility alias policy |
| Charles current | `D:\Codex_Workspace\IsaacInfra\Charles\current\CrawlScouter_v0.10.0_pipeline_contract\` | diagnose/protocol contract |
| Charles spec | `...\CrawlScouter_v0.10.0_pipeline_contract\SPEC_Charles_v0_10_1.md` | canonical Charles v0.10.1 spec |
| Arthur current | `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\` | inspect/collect/result contract |
| Arthur spec | `...\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md` | canonical Arthur v0.6.1 spec |
| Hosea operational spec | `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md` | human-operated MCP/CLI orchestration surface |
| Pearson v0.1 spec | `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract\SPEC_pearson_v0_1.md` | storage/pre-ingest contract |
| Susan v0.1 spec | `D:\Codex_Workspace\IsaacInfra\Susan\current\Susan_v0.1_QA_contract\SPEC_susan_v0_1.md` | QA contract over Pearson/Arthur artifacts |
| Charles README | `...\CrawlScouter_v0.10.0_pipeline_contract\README.md` | CLI/profile/RSC overview |
| Charles schema | `...\CrawlScouter_v0.10.0_pipeline_contract\schemas.py` | ExecutionProtocol dataclasses |
| Charles protocol builder | `...\CrawlScouter_v0.10.0_pipeline_contract\protocol_builder.py` | best_path and diagnostic_findings rules |
| Arthur README | `...\Arthur_v0.6_pipeline_contract\README.md` | CLI/result contract |
| Arthur AGENTS | `...\Arthur_v0.6_pipeline_contract\AGENTS.md` | dev conventions and boundaries |
| Arthur schema | `...\Arthur_v0.6_pipeline_contract\arthur\schemas.py` | Prescription, InspectResult, CollectionResult |
| Arthur loader | `...\Arthur_v0.6_pipeline_contract\arthur\protocol_loader.py` | protocol/scout_report/compact/CollectDirective normalization |
| Arthur CLI | `...\Arthur_v0.6_pipeline_contract\arthur\cli.py` | actual stop gates and orchestration |

Compatibility alias note:

- Use canonical spec paths above for new references.
- Arthur alias `...\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0.6.1.md` is retained for older references.
- Charles alias `...\CrawlScouter_v0.10.0_pipeline_contract\SPEC_v0.10.1.md` is retained for older references.
- Canonical and alias files must remain byte-identical while aliases exist.

## Streamer Project Sources

| Area | Path | Use |
|---|---|---|
| working generic protocol | `D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\03_STREAMER_CASE_GENERIC_PROTOCOL.md` | default case-agnostic workflow |
| 김달수 package | `D:\Codex_Workspace\Streamer Consulting Project\김달수_CASE_PACKAGE_v3_20260611\` | completed/partial reference case |
| 구비바 package | `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\` | current/alternate reference case |
| 김달수 dossier | `...\김달수_CASE_DOSSIER_v3.md` | human-readable case summary |
| 김달수 CaseResult | `...\machine\김달수_CaseResult_v3_partial_20260611.json` | machine state |
| 김달수 EvidencePackage | `...\machine\김달수_EvidencePackage_v3_initial.json` | evidence inventory |
| 김달수 AbsenceInventory | `...\machine\김달수_AbsenceInventory_v3_initial.json` | missing execution/manual/demo facts |
| 김달수 DisclosureLog | `...\machine\김달수_DisclosureLog_v3_initial.json` | disclosure status |
| 김달수 report | `...\deliverables\milestone_report\김달수_채널분석_컨설팅리포트.md` | client-facing report; read only for exact claim evidence |
| 김달수 roadmap | `...\deliverables\roadmap\김달수_재방문_로드맵_v3.1.md` | internal follow-up strategy |
| 김달수 cohort CSV | `...\data\cohort\김달수_코호트_131명.csv` | cohort columns/sample rows |
| 김달수 daily stats CSV | `...\data\daily_stats\김달수_Dalsu_방송통계_1년_20260528.csv` | time series columns/sample rows |
| Orchestrator package | `D:\Codex_Workspace\Streamer Consulting Project\PIPELINE_ORCHESTRATOR_SPEC_PACKAGE_20260611.zip` | generic runbook/templates/prompts; included templates mention Gubiba but protocol is reusable |

## Zip Entry Names

`PIPELINE_ORCHESTRATOR_SPEC_PACKAGE_20260611.zip` contains:

```text
pipeline_orchestrator_spec_20260611/README.md
pipeline_orchestrator_spec_20260611/CLI_ORCHESTRATOR_RUNBOOK_20260611.md
pipeline_orchestrator_spec_20260611/CLI_ORCHESTRATOR_PROMPTS_20260611.md
pipeline_orchestrator_spec_20260611/CLI_ORCHESTRATOR_SPEC_TABLE_20260611.csv
pipeline_orchestrator_spec_20260611/PIPELINE_TOOL_REVIEW_Charles_Arthur_20260611.md
pipeline_orchestrator_spec_20260611/TargetBatchPlan_template_gubiba_cohort_v3.json
pipeline_orchestrator_spec_20260611/CollectDirective_template_gubiba_cohort_v3.json
pipeline_orchestrator_spec_20260611/MANIFEST.json
```

## Case Neutrality Rule

KimDalsu and Gubiba files are examples/reference cases. For a new streamer, first locate that streamer's package and machine objects, then apply `03_STREAMER_CASE_GENERIC_PROTOCOL.md`.
