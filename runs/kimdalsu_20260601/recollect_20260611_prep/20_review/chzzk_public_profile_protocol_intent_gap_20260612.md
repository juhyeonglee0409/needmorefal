# CHZZK Public Profile Protocol Intent Gap Review

Date: 2026-06-12

Scenario: Scenario 3 review-only.

Boundary: offline review only. No live web access, no Charles rerun, no Arthur inspect/collect, no CollectDirective/CollectionResult creation, and no package/CaseResult/DisclosureLog/PublicDemoRow mutation.

## Inputs Reviewed

- `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.scout_report.json`
- `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.protocol.json`
- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `20_review/public_crosscheck_preliminary_alignment_20260612.md`

## Verdict

- Arthur inspect eligibility: `later`
- CollectDirective draft eligibility: `no`
- collect approval: `no`
- Current protocol role: `CHZZK VOD/card contextual signal`, not subject identity/current metrics evidence.
- Smallest next action: prepare a new Charles diagnostic request for the same CHZZK channel with explicit API/selector/field hints for channel identity/profile/follower fields; do not send this protocol to Arthur inspect until the target intent is either narrowed to VOD/card context or a new protocol covers the subject-profile fields.

## Research Intent

ResearchPlan primary intent includes:

- Reconfirm subject channel identity and current channel metrics.
- Collect public CHZZK profile signals for subject identity and recent category alignment.

TargetBatchPlan target `chzzk_subject_channel_public_profile` intent:

- Target URL: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- Intent: collect public subject profile, recent live/VOD titles, and recent categories for identity and category alignment.
- Required fields: `run_id`, `case_id`, `streamer_key`, `platform`, `platform_channel_id`, `channel_name`, `channel_url`, `profile_text`, `follower_count`, `recent_live_or_vod_titles`, `recent_categories`, `collected_at`, `raw_record_path`, `disclosure_tag`.
- Expected channel id: `dcbccbf2d8e2a1b095244c5856d3613a`
- Expected name contains: `김달수`, `Dalsu`

## What The Protocol Actually Targets

Protocol summary:

- `target_url`: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `best_path`: `playwright`
- `best_path_trace`: phase 1 had no data evidence; phase 2 rendered content produced usable data evidence.
- `pre_check.gate_status`: `none`
- `pre_check.risk_level`: `low`
- `profile_required`: `false`
- `collection_plan.source`: `rendered_dom`
- `transport`: `httpx`
- `verification.dedup_key`: `title`
- `verification.expected_row_count`: `null`

Collection fields:

- `thumbnail`
- `time`
- `title`
- `video_card_item__lOC8Y`
- `blind`
- `category`

Selector basis:

- `div.channel_home_vod_item__N7KA5`
- `div[class~="channel_home_vod_item__N7KA5"]`
- thumbnail/time selector fallbacks

Wait condition:

- `page.goto(wait_until='networkidle'); wait_for_selector('div.channel_home_vod_item__N7KA5')`

Interpretation: the executable collection plan is a recent VOD/card DOM plan. It is not a subject profile identity/current metrics plan.

## Why VOD/Card DOM Won

ScoutReport phase 2 evidence:

- Phase 2 was attempted and succeeded with status `200`.
- Rendered URL stayed on the CHZZK subject channel URL.
- Rendered title was generic: `치지직 CHZZK`.
- Rendered judgment recorded a data-array winner: `html.div.channel_home_vod_item__N7KA5#2`.
- Winner sample keys were `thumbnail`, `time`, `title`, `video_card_item__lOC8Y`, `blind`, `category`.

ScoutReport API/RSC evidence:

- API candidates seen: `21`.
- Usable API candidates promoted by protocol: `0`.
- RSC payload candidates: `0`.
- Sitemap candidates seen: `8`, usable `0`.

Observed API calls included potentially relevant CHZZK endpoints:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/videos?sortType=LATEST&pagingType=PAGE&size=24&videoType=&page=0`
- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/data?fields=banners,topExposedVideos,missionDonationChannelHomeExposure`

But the ScoutReport preserved these as observed browser XHR/fetch calls only. It did not preserve parsed response bodies or classify any as usable JSON data endpoints. Therefore protocol generation fell back to the highest scoring rendered DOM data array, which was the VOD/card list.

## Subject Identity / Current Metric Candidates In ScoutReport

Positive signals:

- The URL and observed API endpoints contain the expected channel hash `dcbccbf2d8e2a1b095244c5856d3613a`.
- The route is public and unauthenticated in this artifact: status `200`, no login/checkpoint/CAPTCHA boundary in the protocol summary.
- The channel API endpoint was observed with status `200`.

Missing or not preserved:

- Text search found no `김달수` or `Dalsu` in the ScoutReport.
- Text search found no `follower` / `팔로워`.
- Text search found no `channelName`, `channel_name`, `channelId`, or `channelIdHash`.
- HTTP title and rendered title were generic `치지직 CHZZK`.
- No profile text or follower count was preserved as a data field.
- Observed API response bodies were not captured into structured evidence.

Conclusion: the ScoutReport contains route/API hints that can guide a better rerun, but it does not itself preserve enough channel identity/current metric values to satisfy the target intent.

## Required Field Coverage

| Required field | Current coverage |
|---|---|
| `run_id` | pipeline metadata, not target field |
| `case_id` | pipeline metadata, not target field |
| `streamer_key` | pipeline metadata, not target field |
| `platform` | pipeline metadata / inferable, not target collection field |
| `platform_channel_id` | inferable from URL hash, not collected field |
| `channel_name` | not available in protocol |
| `channel_url` | inferable from target URL, not collected field |
| `profile_text` | not available in protocol |
| `follower_count` | not available in protocol |
| `recent_live_or_vod_titles` | partial via `title` from VOD/card DOM |
| `recent_categories` | partial via `category` from VOD/card DOM |
| `collected_at` | pipeline metadata, not target field |
| `raw_record_path` | pipeline metadata, not target field |
| `disclosure_tag` | pipeline metadata, not target field |

Current protocol can support only weak contextual claims about recent VOD/card titles/categories. It cannot support channel identity, profile text, follower count, or current channel metrics.

## Arthur Inspect Value

Arthur inspect should not be run as the next step for the original subject identity/current metrics intent.

Reasons:

- The current `collection_plan.fields` do not include `channel_name`, `profile_text`, `follower_count`, or a collected `platform_channel_id`.
- The plan's `dedup_key=title` confirms it is row-oriented around VOD/card titles.
- `best_path=playwright` but `transport=httpx`; passing the protocol to Arthur inspect without explicit transport handling may not reproduce the rendered DOM evidence.
- Inspecting this protocol would at best validate a VOD/card DOM surface, not the subject identity/current metric fields required by the ResearchPlan.

Therefore:

- If the intent remains subject identity/current metrics: Arthur inspect eligibility is `later`.
- If the target is explicitly re-scoped to CHZZK VOD/card contextual signal: Arthur inspect could be considered later as exploratory surface validation only.
- CollectDirective draft eligibility remains `no` either way until a post-inspect alignment review exists and operator approval is explicit.

## Should The Target Intent Be Lowered?

Do not silently lower `chzzk_subject_channel_public_profile` from subject profile identity/current metrics to VOD/card context.

Recommended handling:

- Keep the original target intent open as not yet satisfied.
- Treat this existing protocol as a contextual support artifact only.
- If useful, create a separate future target/review label such as `chzzk_subject_vod_card_context_public` so VOD/card data does not masquerade as profile/current metric evidence.

## Rediagnosis Direction

A future Charles rerun should be explicit about expected data surfaces and should not let VOD/card DOM be the first successful winner for the profile intent.

Target URLs to use or compare:

- `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `https://chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- Candidate API target to test from observed XHR: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- Candidate VOD API target only for contextual titles/categories: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/videos?sortType=LATEST&pagingType=PAGE&size=24&videoType=&page=0`
- Candidate supplemental API target: `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/data?fields=banners,topExposedVideos,missionDonationChannelHomeExposure`

Expected field hints for Charles:

- Required identity/profile fields: `platform_channel_id`, `channel_name`, `channel_url`, `profile_text`, `follower_count`.
- Context fields: `recent_live_or_vod_titles`, `recent_categories`.
- Validation expectations: channel id/hash equals `dcbccbf2d8e2a1b095244c5856d3613a`; name contains `김달수` or `Dalsu`.

JSON/API path hints to test, not verified by current artifact:

- `content.channelId`
- `content.channelIdHash`
- `content.channelName`
- `content.channelDescription`
- `content.followerCount`
- `content.channelImageUrl`
- `content.openLive`
- `content.videos[*].videoTitle`
- `content.videos[*].categoryType` / `content.videos[*].videoCategory`

DOM selector hints to test, not verified by current artifact:

- Prefer channel/profile/header selectors over VOD card selectors.
- Candidate profile selectors: `[class*="channel"][class*="profile" i]`, `[class*="channel"][class*="name" i]`, `[class*="profile" i]`, `[class*="follower" i]`, `[aria-label*="팔로워"]`.
- Candidate validation text selectors: page regions containing `김달수`, `Dalsu`, or the channel hash.
- Exclude or down-rank `div.channel_home_vod_item__N7KA5` when the target intent is profile identity/current metrics; use it only for the contextual VOD/card target.

Suggested Charles instruction:

```text
Diagnose the CHZZK public subject channel for profile identity fields first.
Prefer the channel API endpoint and profile/header DOM over VOD/card DOM.
Required fields: platform_channel_id, channel_name, channel_url, profile_text, follower_count.
Context fields: recent_live_or_vod_titles, recent_categories.
Expected channel id/hash: dcbccbf2d8e2a1b095244c5856d3613a.
Expected name contains: 김달수 or Dalsu.
Do not select VOD/card DOM as the primary collection_plan unless profile identity fields are absent; if only VOD/card fields are found, mark subject profile fields not_verifiable and classify the protocol as contextual signal only.
```

## Final Boundary

This review does not approve Arthur inspect, does not approve a CollectDirective draft, and does not approve collect. It preserves the protocol as a partial/contextual artifact and recommends a targeted Charles rediagnosis before any Arthur step.
