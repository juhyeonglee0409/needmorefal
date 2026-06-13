# CHZZK Subject Profile Post-Collect Evidence Review - 2026-06-13

Scope: Scenario 3 post-collect review only. This note reviews the existing CHZZK `CollectionResult` as a fresh evidence candidate. It does not run Charles, Arthur inspect, Arthur collect, or any live web access. It does not mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.

## Inputs Reviewed

- CollectionResult: `40_arthur_collect/results/chzzk_subject_profile_api_body_collect_20260613.CollectionResult.json`
- Approved directive: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.approved_true_record_root_20260613.json`
- Source draft: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_record_root_20260612.json`
- Prior collect-shape review: `20_review/chzzk_subject_profile_api_direct_collect_shape_patch_review_20260612.md`
- Target intent references:
  - `00_inputs/research_plan.md`
  - `00_inputs/target_batch_plan.draft.json`

## Short Verdict

PASS as a fresh evidence candidate for CHZZK subject identity and public profile/current fields.

This is not canonical package data. The result can support a later EvidencePackage patch candidate, but CaseResult, DisclosureLog, PublicDemoRow, and package canonical files must remain unchanged unless separately approved by the operator.

## Execution Summary

| Check | Result |
|---|---|
| `executed` | `true` |
| `stopped_reason` | `null` |
| `path_used` | `api_direct` |
| transport | `httpx` |
| requests made | `2` |
| pages fetched | `1` |
| item count | `1` |
| row root | `$.content` |
| scalar-only row risk | not observed |
| source URL | `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a` |
| fetched at | `2026-06-13 00:06:46` |

Requests made are consistent with one robots check plus one exact CHZZK channel API GET.

## Collected Row

The single collected item is an object row, not a scalar `value` row.

| Field | Value / status | Evidence use |
|---|---|---|
| `channelId` | `dcbccbf2d8e2a1b095244c5856d3613a` | Direct subject platform channel id/hash evidence. |
| `channelName` | `김달수 Dalsu` | Direct subject name evidence. |
| `channelDescription` | `문의 : biz@nobent.co.kr` | Direct public profile text evidence. |
| `followerCount` | `3755` | Direct public follower count at collection time. |
| `channelImageUrl` | present | Direct public profile image URL evidence. |
| `openLive` | `false` | Direct public live-status/current-state evidence. |

## Intent Alignment

| Research/target field | Review status | Notes |
|---|---|---|
| `platform_channel_id` / channel hash | PASS | `channelId` exactly matches expected hash `dcbccbf2d8e2a1b095244c5856d3613a`. |
| `channel_name` | PASS | `channelName` is `김달수 Dalsu`, matching expected `김달수` / `Dalsu`. |
| `profile_text` | PASS | `channelDescription` is present. |
| `follower_count` | PASS | `followerCount=3755` is direct from the CHZZK channel API. Treat as time-sensitive. |
| `live_status` | PASS | `openLive=false` is direct from the CHZZK channel API. |
| `profile_image_url` | PASS | `channelImageUrl` is present. |
| `channel_url` | PARTIAL | The result preserves target/source URL provenance, but `channel_url` is not a collected item field. A later patch candidate may derive it only if derivation is explicitly allowed. |
| `recent_live_or_vod_titles` | not in scope | This bounded collect intentionally used the profile API only. |
| `recent_categories` | not in scope | This bounded collect intentionally used the profile API only. |

## Field Coverage

All six approved collected fields have `present=1` and `absent=0`:

- `channelId`
- `channelName`
- `channelDescription`
- `followerCount`
- `channelImageUrl`
- `openLive`

`absences=[]` and `errors=[]`.

## Verification Status

Arthur verification status is `not_verifiable`.

Reason: `expected_row_count=null`; Arthur has no independent expected-row-count baseline for this singleton profile API. Shape and null-ratio checks passed:

- shape hints observed;
- `null_ratio=0.0`;
- `duplicate_count=0` with `dedup_key=channelId`.

Interpretation: this does not invalidate the collected identity/profile fields, but it prevents treating the result as fully verified by Arthur's row-count verification gate.

## Boundary Signals

Only one boundary signal is present:

- `robots_check`, severity `info`, action `recorded`, robots allowed.

No checkpoint, HTTP 429, login/session, CAPTCHA, manual-review, or restricted boundary appears in the CollectionResult.

## Storage And Secret Check

Safety review result: PASS.

- `artifacts=[]`
- raw artifact directory: not created for this result
- raw HTML stored: no
- raw JSON body stored: no
- screenshots stored: no
- session/profile used: no
- `session_profile.provided=false`
- `session_profile.secret_values_logged=false`
- `header_names=[]`
- `cookie_names=[]`
- no token/cookie/auth/header/browser-storage values are present in the result

The only external media-like value retained is the public `channelImageUrl` field, which is part of the approved field scope.

## Drift / Consistency Notes

Prior Charles rescout sample observed `followerCount=3754`; Arthur inspect and this collect observed `3755`. Treat this as live metric drift across reads, not as identity mismatch. Any EvidencePackage patch should preserve `fetched_at` and source URL with the follower count.

## Eligibility

| Output / mutation | Eligibility |
|---|---|
| Fresh evidence candidate | yes |
| EvidencePackage patch candidate | later, with operator approval |
| AbsenceInventory patch candidate | not needed for this result; no absences were collected |
| CaseResult mutation | no |
| DisclosureLog mutation | no |
| PublicDemoRow mutation | no |
| Package canonical mutation | no |

## Recommended Mapping For Later Patch Candidate

If the operator later approves a patch candidate, map fields conservatively:

- `platform_channel_id` <- `channelId`
- `channel_name` <- `channelName`
- `profile_text` <- `channelDescription`
- `follower_count` <- `followerCount`
- `profile_image_url` <- `channelImageUrl`
- `live_status` <- `openLive`
- `source_url` <- item `source_url`
- `collected_at` <- item `fetched_at`
- `protocol_hash` <- `b9669a599d0eaa12bd5013fec1efdaca189faec6586907d8650178214ee0b4ca`
- `operator_directive_hash` <- `60b5a07dfe0481ca2f75e23028baa3ad5bc32eaafde9b1daa9fab7de252e6eaf`

Do not derive or fill `channel_url`, recent titles, recent categories, rank, Softcon metrics, or cohort fields from this result without a separate derivation rule or source.

## Next Action

Use this review as the evidence-candidate basis for either:

1. an offline Pydantic/Polars artifact validation design, or
2. a separately approved EvidencePackage patch candidate.

Do not promote this CollectionResult into canonical package data without a separate operator decision.
