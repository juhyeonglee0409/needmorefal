# Tool Contracts - Charles And Arthur

This is the working summary. Source files remain authoritative.

## Current Canonical Specs

Use these source specs for details before changing tool contracts:

- Charles v0.10.1: `D:\Codex_Workspace\IsaacInfra\Charles\current\CrawlScouter_v0.10.0_pipeline_contract\SPEC_Charles_v0_10_1.md`
- Arthur v0.6.1: `D:\Codex_Workspace\IsaacInfra\Arthur\current\Arthur_v0.6_pipeline_contract\SPEC_Arthur_v0_6_1.md`
- Hosea operational surface: `D:\Codex_Workspace\IsaacInfra\Hosea\current\SPEC_hosea_operational.md`
- Pearson v0.1 storage/pre-ingest: `D:\Codex_Workspace\IsaacInfra\Pearson\current\Pearson_v0.1_storage_contract\SPEC_pearson_v0_1.md`
- Susan v0.1 QA: `D:\Codex_Workspace\IsaacInfra\Susan\current\Susan_v0.1_QA_contract\SPEC_susan_v0_1.md`

## Charles / CrawlScouter v0.10.1

Role: diagnostic scout. It produces `ScoutReport` and Arthur-ready `ExecutionProtocol`.

Key CLI:

```bash
scouter URL --json --out report.json
scouter URL --engage --transport curl_cffi --profile profile.json --json --out report.json
```

MCP tools:

```text
scout_site(url)      -> text report
scout_json(url)      -> full ScoutReport JSON
scout_protocol(url)  -> ExecutionProtocol JSON
```

Important output fields:

```text
version
generated_at
target_url
best_path
best_path_trace
pre_check
connection_test
collection_plan
storage
verification
transport
profile_required
profile_summary
rsc_payload_candidates
diagnostic_findings
```

Important v0.10.1 facts:

- `diagnostic_findings` records API/sitemap/RSC status and provenance.
- `profile_cleared` does not override robots/login/terms risk.
- profile/cookie/header values are not stored, only names and summary status.
- RSC payload can produce `best_path = rsc_payload`, often with `transport = curl_cffi` and `profile_required = true`.
- Bounded `browser_probe` runs by default for `best_path=manual_review` or `gate_status=restricted`; use `--no-browser-probe` to disable it.
- `browser_probe` detects visibility/checkpoint/CAPTCHA/login/rate-limit and URL-candidate signals only. It does not bypass access gates.
- `browser_probe` artifacts require explicit `--save-raw`; raw HTML and screenshots are suppressed in profile/session contexts with saved/not-saved status fields.
- Browser-probe target/rendered/candidate URLs redact query values before report/protocol storage.
- v0.10.1 adds bounded in-memory API body summary classification for allowed JSON XHR/fetch responses.
- CHZZK `service/v1/channels/{hash}` can be promoted for profile intent when channel identity fields are present.
- CHZZK videos/clips/context endpoints remain contextual only for profile intent.
- Raw API response bodies are not stored by the body-summary feature.

## Arthur v0.6.1

Role: protocol-driven executor. It does not interpret strategic meaning.

Flow:

```text
arthur inspect protocol.json -> InspectResult
arthur collect CollectDirective.json -> CollectionResult + artifacts
```

Accepted input shapes:

| Shape | Use | Verification |
|---|---|---|
| `protocol` | `scouter --json` top-level `protocol` section only | canonical |
| `CollectDirective` | protocol + approved scope/policy | canonical |
| `scout_report` | full scouter report | forced `not_verifiable` |
| `compact` | manually compacted/MCP text JSON | forced `not_verifiable` |

Best paths:

```text
requests
api_direct
rsc_payload
sitemap_first
playwright
manual_review
```

`manual_review` is not executed.

Stop gates:

- `CollectDirective.approved=false`
- approved scope mismatch
- private/internal/execution environment target unless explicitly allowed
- `profile_required` without profile
- `login_required` without profile
- invalid/expired session
- `manual_review`
- restricted gate/risk
- operator policy stop on robots

Robots policy:

- robots is live-checked by Arthur UA.
- robots disallow is recorded and normally proceeds.
- it stops only if operator policy says stop.

Profile/session execution policy:

- operator-approved `chrome_profile` may be used for inspect or collect only within the approved scope.
- `chrome_profile` collect requires `CollectDirective.approved=true` and explicit policy permission.
- an ephemeral cookie bridge is allowed only when explicitly enabled by directive/policy.
- the bridge may read cookies only from the active Playwright context for the exact approved origin and pass values in memory only to same-origin `curl_cffi`.
- direct Chrome cookie database reads, bulk cookie export, cross-origin forwarding, and durable cookie/token value storage are not allowed by default.
- allowed outputs are summary-only: cookie names, domains, expiry/session summary, scope, bridge-used flag, and `secret_values_persisted=false`.
- if scope, checkpoint, CAPTCHA, private/account page, or secret-persistence uncertainty appears, Arthur stops and preserves the boundary.

CollectionResult preserves:

```text
items
absences
field_coverage
verification
execution
boundary_signals
policy_trace
artifacts
session_profile
protocol_ref
storage_hint
```

Absence source values:

```text
charles_not_found
arthur_collection_failed
target_absent
undetermined
```

Verification statuses:

```text
pass
count_mismatch
suspected_wrong_target
quality_fail
not_verifiable
not_executed
```

Hard rule: verification expected values must come from the official `verification` block only. Do not derive expected counts from `itemCount`, pagination totals, or collected row counts.

Important v0.6.1 facts:

- `chrome_profile` collect remains CollectDirective-gated and exact-scope only.
- `api_direct` row roots must be object/list containers, not scalar field paths.
- CHZZK-style profile API should use `json_path_hints=["$.content"]`; scalar field paths belong in metadata such as `field_json_path_hints`.
- Path/pagination incompatibility must not be silently hidden. If a path falls back to single-page behavior for an unsupported pagination type, notes should record the compatibility downgrade.

## Pearson / Susan Status

Pearson and Susan now have current specs but are not assumed implemented for case work unless a concrete executable exists and is invoked.

- Pearson v0.1 is storage/pre-ingest and emits StorageReceipt.
- Susan v0.1 is QA over Pearson StorageReceipt and linked Arthur/Charles artifacts.
- Until implementation is available, Codex/user workflow may only produce review notes, operator recommendations, and patch candidates.
- Do not treat Pearson/Susan specs as permission to mutate canonical case package data.
