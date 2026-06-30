# CHZZK Subject Profile API Body CollectDirective Draft Review - 2026-06-12

Type: `review_note`.

Scope: Scenario 3 CollectDirective draft only. This creates an `approved=false` review artifact for the CHZZK subject profile API. It does not run Arthur collect, does not create CollectionResult, and does not mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.

## Draft Path

- Draft directive: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_20260612.json`
- Draft file SHA-256: `ea2dcd41af2d00774dca4760e71461440be163d0ec9a293cddd1cba112c477af`
- Source protocol: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`
- Source protocol file SHA-256: `bbc4461c9efb1ba6a9c81546b2c1ce2d8e6a064eb31b3b9b982d2de3c4ce8d79`
- Source InspectResult: `30_arthur_inspect/chzzk_subject_profile_api_body_rescout_api_direct_20260612.InspectResult.json`
- Source InspectResult SHA-256: `8ec3a43baec66cf454131f124d72e580f38e4ba310bf9e667fa81edfcfca375c`

## Draft Summary

- `kind=CollectDirective`
- `status=draft`
- `approved=false`
- `target_id=chzzk_subject_channel_public_profile`
- `approved_best_path=api_direct`
- `transport=httpx`
- Profile/session/Chrome profile: disallowed
- Softcon/follower/LoL/ranking scope: disallowed
- Raw HTML / screenshot / raw JSON artifact / secret value storage: disabled
- Proposed future result path only: `40_arthur_collect/results/chzzk_subject_profile_api_body_collect_20260612.CollectionResult.json`

## Loader Validation

Arthur `load_protocol()` parsed the draft offline:

- `input_shape=collect_directive`
- `best_path=api_direct`
- `transport=httpx`
- `target_url=https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `connection_url=https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- `approved=False`
- `fields=channelId, channelName, channelDescription, followerCount, channelImageUrl, openLive`
- loader `protocol_hash=93d31aadcf7f1c906d8b3dc0f6a030175a243da434987ce17ff4c1803f2bf915`
- loader `directive_hash=930d8664040f21acd42bf4a072dcdc4dcfaef12c5a784d606a087bbc22ba6b24`

This validation was offline parsing only. No network request or collect execution was performed.

## Approved Scope

Exact allowed URLs:

- `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`

Allowed domains:

- `m.chzzk.naver.com`
- `api.chzzk.naver.com`

Limits:

- `max_items=1`
- `max_pages=1`
- `max_requests=3`
- `max_runtime_seconds=60`
- `max_routes=1`

Videos, clips, channel-home data, Softcon, follower, LoL, and ranking routes are outside this draft scope.

## Field / Validation Scope

Required direct fields:

| Field | Expected source path |
|---|---|
| `channelId` | `content.channelId` |
| `channelName` | `content.channelName` |
| `channelDescription` | `content.channelDescription` |
| `followerCount` | `content.followerCount` |
| `channelImageUrl` | `content.channelImageUrl` |
| `openLive` | `content.openLive` |

Expected identity:

- `channelId=dcbccbf2d8e2a1b095244c5856d3613a`
- `channelName=김달수 Dalsu`

Prior inspect status:

- Arthur inspect verdict: `PASS`
- API status: 200
- Content type: `application/json`
- JSON sample count: 1
- Field maps reproduced all required fields

## Policy Checks

| Check | Status | Note |
|---|---:|---|
| `approved=false` | PASS | Draft cannot authorize collect. |
| Embedded `source_protocol` | PASS | Required by current Arthur `CollectDirective` loader. |
| `approved_best_path=api_direct` | PASS | Matches Charles/Arthur PASS path. |
| Exact API URL allowlisted | PASS | `connection_url` is included in `approved_scope.allowed_urls`. |
| Page URL allowlisted | PASS | Subject page URL retained for provenance/robots target. |
| Raw artifacts disabled | PASS | `raw_policy.save_raw=false`, raw JSON/HTML/screenshot disabled. |
| Secret storage disabled | PASS | Cookie values, auth headers, browser storage, and secret values disabled. |
| Profile/session disabled | PASS | Public unauthenticated API only. |
| Contextual endpoints blocked | PASS | videos/clips/data promotion policy is stop. |
| CollectionResult creation | PASS | Not created. |

## Collect Shape Preflight

Status: `CAUTION / needs review before approved=true`.

Reason:

- The source protocol's `json_path_hints` are scalar paths:
  - `$.content.channelId`
  - `$.content.channelName`
  - `$.content.channelDescription`
  - `$.content.followerCount`
  - `$.content.channelImageUrl`
  - `$.content.openLive`
- Arthur `collect_api` currently tries `json_path_hints` in order and returns rows from the first matching hint.
- If approved and executed as-is, the collector may extract the first scalar value rather than the whole `content` object.

Required before any `approved=true` collect:

1. Confirm the collector uses `$.content` as the record root for this directive, or
2. add a safe directive/protocol override for the extraction root, or
3. patch Arthur/Charles so scalar profile field hints do not produce scalar-only collect rows.

Until this is resolved, the draft is useful as a scope and policy artifact, not as an approved execution artifact.

## Approval Boundary

- Collect approval: `no`
- `approved=true`: not set
- Arthur collect run: no
- CollectionResult: not created
- CaseResult / DisclosureLog / PublicDemoRow / package canonical mutation: no

This draft may be reviewed by the operator, but it must not be executed until the operator explicitly approves:

- exact API URL,
- extraction shape,
- field scope,
- output path,
- limits,
- and `approved=true`.

## Smallest Next Action

Review the draft and decide whether to resolve the collect-shape preflight issue by adding an extraction-root override or patching Arthur/Charles behavior. Do not run collect or set `approved=true` yet.
