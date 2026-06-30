# CHZZK Subject Profile API-Body Rescout Alignment - 2026-06-12

Type: `review_note`.

Scope: Scenario 3 Charles public rescout plus offline alignment review only. Arthur inspect, Arthur collect, CollectDirective creation, CollectionResult creation, CaseResult mutation, DisclosureLog mutation, PublicDemoRow mutation, and package canonical data mutation were not performed.

## Execution Status

- Verdict: `PASS`.
- Operator-approved external Charles run: yes, exactly 1 run.
- Charles command target: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`.
- Request budget used for Charles: `--max-requests 30`.
- ScoutReport created: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.scout_report.json`.
- Protocol extracted: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`.
- ScoutReport SHA-256: `614a7ed0e2c95e8e7c9e0d2fa1263084b613de484bb304ad628379a342a37eac`.
- Protocol SHA-256: `bbc4461c9efb1ba6a9c81546b2c1ce2d8e6a064eb31b3b9b982d2de3c4ce8d79`.
- Arthur inspect run: no.
- Arthur collect run: no.
- CollectDirective created: no.
- CollectionResult created: no.

## Exact Target URLs

- Page target executed: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`.
- Promoted profile API: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`.
- Context-only CHZZK channel-family endpoints observed included `videos`, `data`, `clips`, `donations/missions`, and `cafe-connection`; these were not promoted as subject profile sources.

## Request / API Counts

- External Charles run count: 1.
- Persisted XHR/fetch API observation records: 20.
- Unique persisted observed API URLs: 20.
- CHZZK `service/v1/channels/{hash}` family records: 6.
- Records with `body_summary`: 6.
- Profile-usable API candidates: 1.
- Contextual-only API candidates: 3.
- Exact total browser network request count beyond persisted `observed_apis` was not separately emitted by Charles.

## Body Summary Presence

- `body_summary` present for the primary channel profile API: yes.
- Parse status: `parsed`.
- Byte length: 655.
- Max body-summary cap: 256000 bytes.
- Classification: `chzzk_channel_profile`.
- `usable_for_profile_intent`: true.
- `contextual_only`: false.
- Preserved profile paths:
  - `content.channelId`
  - `content.channelName`
  - `content.channelDescription`
  - `content.followerCount`
  - `content.channelImageUrl`
  - `content.openLive`

The summary preserves field paths, classification, byte length, and bounded scalar samples. It does not persist the raw JSON response body.

## Promoted Usable API Candidates

The only promoted usable profile candidate is:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`

The endpoint was promoted because the body summary contains subject identity/current profile fields: `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, and `openLive`.

Videos, clips, and channel-home data endpoints were classified as contextual-only and were not promoted as subject profile/current metric sources.

## Primary Collection Plan

- `best_path`: `api_direct`.
- `collection_plan.source`: `api`.
- `connection_test.url`: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`.
- `collection_plan.fields`: `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive`.
- `json_path_hints`: `$.content.channelId`, `$.content.channelName`, `$.content.channelDescription`, `$.content.followerCount`, `$.content.channelImageUrl`, `$.content.openLive`.
- `selector_hints`: empty.
- VOD/card DOM primary: no.

## Item / Field Coverage

| Field | Status | Source / note |
|---|---:|---|
| `channel_id_or_hash` / `platform_channel_id` | direct | `content.channelId` equals `dcbccbf2d8e2a1b095244c5856d3613a`. `content.channelIdHash` was not present, but `channelId` satisfies the identity hash requirement. |
| `channel_name` | direct | `content.channelName` sample is `김달수 Dalsu`; matches expected subject name. |
| `channel_url` | direct | Protocol `target_url` and promoted API URL both carry the expected channel hash. |
| `profile_text` | direct | `content.channelDescription` present. |
| `follower_count` | direct | `content.followerCount` present; observed sample value `3754`. |
| `live_status` | direct | `content.openLive` present; observed sample value `false`. |
| `profile_image_url` | direct | `content.channelImageUrl` present as a bounded scalar sample. |
| `recent_live_or_vod_titles` | secondary/contextual | Available only through contextual endpoints such as `videos` / `data`; not primary profile evidence. |
| `recent_categories` | secondary/contextual | Available only through contextual endpoints such as `videos` / `data`; not primary profile evidence. |

## Identity Match Status

- Expected hash: `dcbccbf2d8e2a1b095244c5856d3613a`.
- Observed `content.channelId`: `dcbccbf2d8e2a1b095244c5856d3613a`.
- Observed `content.channelName`: `김달수 Dalsu`.
- Identity verdict: match.

## Not Verifiable Fields

- Required profile/current fields: none.
- Notes: `content.channelIdHash` was not observed, but `content.channelId` directly matches the expected subject hash. VOD/category context remains secondary and is not needed to satisfy profile identity/current metrics.

## Boundary Signals

- `boundary_signals`: `[]`.
- `pre_check.gate_status`: `none`.
- `pre_check.login_required`: `false`.
- `pre_check.risk_level`: `low`.
- Checkpoint: not detected.
- HTTP 429: not observed.
- Login/session boundary: not observed.
- CAPTCHA: not observed.
- `manual_review`: not selected.
- `restricted`: not observed.

## Raw / Secret / Screenshot / HTML Storage Check

- Durable raw JSON body storage: not found.
- Raw HTML artifact for this run: not found.
- Screenshot artifact for this run: not found.
- The existing `10_charles/browser_probe/` folder predates this run and was not a new artifact from this rescout.
- Cookie metadata records: 5.
- Cookie value fields: 0.
- Sensitive scalar-key scan hits: only `protocol.profile_or_session_likely_needed=false`.
- `Set-Cookie`, `Authorization`, `Bearer`, token, password, secret, raw body, screenshot, and raw HTML patterns were not found in the new ScoutReport/protocol except non-secret status fields noted above.
- Token/cookie/auth-like value redaction boundary is preserved for this run.

## Arthur / Collect Boundary

- Arthur inspect eligibility: `later`.
- Technical protocol candidate for Arthur inspect: yes, after separate operator review/approval. This review does not run Arthur inspect automatically.
- CollectDirective draft eligibility: `no`.
- Collect approval: `no`.
- Arthur collect eligibility: `no`.

## Recommendation

recommendation: Keep this as a `PASS` review note for Charles body-summary/profile API promotion. Treat the extracted protocol as an Arthur inspect candidate only after separate operator judgment.

evidence: The promoted CHZZK channel profile API has parsed bounded `body_summary`, identity match, direct name/profile/current fields, `best_path=api_direct`, and `collection_plan.source=api`.

source_paths:
- `10_charles/chzzk_subject_profile_api_body_rescout_20260612.scout_report.json`
- `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`
- `20_review/chzzk_subject_profile_api_body_rescout_alignment_20260612.md`

assumptions: The public `content.channelId` value is the platform channel hash intended by the ResearchPlan and TargetBatchPlan.

risks: Charles still records bounded public scalar samples in `body_summary`; continue to reject raw body, cookie values, auth headers, browser storage, screenshots, and raw HTML by default.

approval_needed: Separate operator approval is needed before any Arthur inspect. CollectDirective creation and collect approval remain `no`.

## Smallest Next Action

Operator reviews this PASS note and decides whether to consider `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json` as an Arthur inspect candidate. Do not run Arthur inspect, Arthur collect, or draft a CollectDirective in this step.
