# CHZZK Subject Profile Rescout Alignment - 2026-06-12

Scenario: Scenario 3 - Charles subject profile rescout.

Scope: one approved external Charles unauthenticated/public CHZZK subject profile rescout, followed by offline intent-alignment review only.

## Inputs

- `20_review/chzzk_subject_profile_rescout_request_20260612.md`
- `20_review/chzzk_public_profile_protocol_intent_gap_20260612.md`
- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- Reference only: `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.scout_report.json`
- Reference only: `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.protocol.json`

## Outputs

- ScoutReport: `10_charles/chzzk_subject_profile_rescout_20260612.scout_report.json`
- Protocol: `10_charles/chzzk_subject_profile_rescout_20260612.protocol.json`
- Review: `20_review/chzzk_subject_profile_rescout_alignment_20260612.md`

## Execution Status

- Operator-approved external Charles run: yes
- External Charles run count: 1
- Target URL used: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- ScoutReport created: yes
- Protocol created: yes
- Arthur inspect run: no
- Arthur collect run: no
- CollectDirective created: no
- CollectionResult created: no
- Package canonical data mutated: no
- CaseResult / DisclosureLog / PublicDemoRow mutated: no

## Post-Run Verdict Fields

- `protocol_created`: yes
- `access_status`: HTTP 200 in phase1 and rendered phase2; no checkpoint detected; no boundary signals recorded.
- `best_path`: `playwright`
- `collection_plan_source`: `rendered_dom`
- `primary selectors/API basis`: `div.channel_home_vod_item__N7KA5` and VOD/card DOM selectors.
- `observed API basis`: channel and related CHZZK API URLs were observed with status 200, including the preferred channel, videos, and data endpoints.
- `diagnostic API status`: `rejected`; API candidates were seen but not confirmed as usable JSON data endpoints.
- `identity match status`: channel hash matches by target URL and observed API URLs; channel name was not directly preserved or verified.
- `follower/profile status`: `follower_count` and `profile_text` were not directly preserved; both remain `not_verifiable`.
- `boundary signals`: none recorded; diagnostic gap remains API-body/field preservation.
- `Arthur inspect eligibility`: no for the original subject profile/current metrics intent.
- `CollectDirective draft eligibility`: no
- `collect approval`: no
- `smallest next action`: review whether to improve Charles/API response-body field capture or create a separate VOD/card contextual target. Do not send this protocol to Arthur inspect for the original profile intent.

## Protocol Summary

- `target_url`: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `best_path`: `playwright`
- `pre_check.gate_status`: `none`
- `pre_check.risk_level`: `low`
- `profile_required`: `false`
- `transport`: `httpx`
- `collection_plan.source`: `rendered_dom`
- `collection_plan.fields`: `thumbnail`, `time`, `title`, `video_card_item__lOC8Y`, `blind`, `category`
- `collection_plan.selector_hints`: includes `div.channel_home_vod_item__N7KA5`
- `collection_plan.wait_condition`: waits for `div.channel_home_vod_item__N7KA5`
- `verification.dedup_key`: `title`
- `diagnostic_findings.api.status`: `rejected`
- `diagnostic_findings.rsc.status`: `not_found`

## Field Coverage

| Field | Status | Source / note |
|---|---|---|
| `platform_channel_id` | partial | Expected hash is present in target URL and observed API URLs, but not collected as a protocol field. |
| `channel_name` | not_verifiable | No preserved `김달수`, `Dalsu`, or channel name field in ScoutReport/protocol. |
| `channel_url` | partial | Target URL directly records the channel URL; not a collected field. |
| `profile_text` | not_verifiable | No preserved profile text or `channelDescription` field. |
| `follower_count` | not_verifiable | No preserved follower count or `followerCount` field. |
| `live_status` | not_verifiable | No preserved direct `openLive` / live-status field. |
| `profile_image_url` | not_verifiable | No preserved profile image or `channelImageUrl` field. |
| `recent_live_or_vod_titles` | partial_contextual_only | `title` exists only through VOD/card DOM. |
| `recent_categories` | partial_contextual_only | `category` exists only through VOD/card DOM. |

## Down-Rank Rule Application

The new rescout still selected `div.channel_home_vod_item__N7KA5` and VOD/card DOM as the primary rendered DOM collection plan.

Per the rescout request, this must not be treated as primary success for subject profile identity/current fields. It can support only:

- `recent_live_or_vod_titles`
- `recent_categories`
- weak contextual CHZZK activity/category signals

It cannot support:

- subject identity proof
- `channel_name`
- `profile_text`
- `follower_count`
- current channel metrics

## Alignment Verdict

Verdict: `PARTIAL / contextual only`.

Reasoning:

- Access succeeded and a protocol was created.
- The expected channel hash appears in the target URL and observed API URLs.
- Preferred API candidates were observed with status 200, but Charles did not preserve parsed response bodies or promote them into a usable API collection plan.
- The protocol remains VOD/card DOM oriented and does not cover the profile identity/current fields required by the ResearchPlan and TargetBatchPlan.
- `channel_name`, `profile_text`, `follower_count`, `live_status`, and `profile_image_url` remain `not_verifiable`.

This protocol should not proceed to Arthur inspect for the original `chzzk_subject_channel_public_profile` intent.

## Boundary Handling

- Preserve the new ScoutReport as diagnostic evidence.
- Preserve the new protocol as a contextual/partial artifact only.
- Preserve `not_verifiable` for direct profile/current fields.
- Preserve the API diagnostic gap: observed API URLs were not confirmed as usable JSON data endpoints.
- Do not promote this to CaseResult readiness.
- Do not treat field absence as final absence meaning.

## Next Action

Review whether Charles needs a targeted API response-body capture/field-preservation improvement for the CHZZK channel endpoint, or explicitly split VOD/card context into a separate future target. Do not run Arthur inspect, Arthur collect, or draft a CollectDirective from this protocol.
