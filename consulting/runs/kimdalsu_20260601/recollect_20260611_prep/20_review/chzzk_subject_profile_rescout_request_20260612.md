# CHZZK Subject Profile Rescout Request - 2026-06-12

Scope: Scenario 3 design-only. This is a Charles rediagnosis request design, not an execution record.

## Boundary

- Live web access: no
- Charles execution: no
- Arthur inspect: no
- Arthur collect: no
- CollectDirective / CollectionResult creation: no
- CaseResult / DisclosureLog / PublicDemoRow / package canonical mutation: no
- Arthur inspect eligibility: `later`
- CollectDirective draft eligibility: `no`
- Collect approval: `no`

## Source Inputs

- `20_review/chzzk_public_profile_protocol_intent_gap_20260612.md`
- `20_review/public_crosscheck_preliminary_alignment_20260612.md`
- `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.scout_report.json`
- `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.protocol.json`
- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`

## Why Previous Protocol Is Insufficient

The previous protocol is access-clean but intent-incomplete for `chzzk_subject_channel_public_profile`.

- The ResearchPlan intent is to reconfirm subject channel identity/current public metrics and collect public CHZZK profile signals.
- The TargetBatchPlan intent is public subject profile collection for identity and category alignment.
- The prior protocol selected `best_path=playwright` with `collection_plan.source=rendered_dom`.
- Its primary selector is `div.channel_home_vod_item__N7KA5`.
- Its fields are VOD/card-oriented: `thumbnail`, `time`, `title`, `video_card_item__lOC8Y`, `blind`, `category`.
- The ScoutReport observed useful CHZZK API calls, but did not preserve parsed response bodies or classify them as usable JSON data endpoints.
- The protocol does not directly preserve `channel_name`, `profile_text`, `follower_count`, or a collected `platform_channel_id`.

Conclusion: the existing CHZZK protocol must remain a weak contextual VOD/card signal. It must not be promoted to subject identity/current metrics evidence.

## Exact Target Intent

Diagnose the same CHZZK public subject channel for direct profile identity and current public profile fields first.

Primary intent:

- Confirm the platform channel hash is `dcbccbf2d8e2a1b095244c5856d3613a`.
- Confirm the channel name contains `김달수` or `Dalsu`.
- Prefer direct channel API/profile-header evidence over rendered VOD/card DOM.
- Extract or explicitly mark unavailable profile/current fields.
- Use recent live/VOD titles and categories only as secondary context.

This request does not narrow the target to VOD/card context. If only VOD/card data is recoverable, preserve that as `PARTIAL / contextual only`.

## Allowed Target URLs

Page targets:

- `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- `https://chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`

Do not expand beyond these page targets and the preferred API endpoints below unless the operator updates the request.

## Preferred API Endpoints To Test

Primary channel API:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`

Context-only VOD API:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/videos?sortType=LATEST&pagingType=PAGE&size=24&videoType=&page=0`

Supplemental channel-home API:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/data?fields=banners,topExposedVideos,missionDonationChannelHomeExposure`

## Required Fields

Charles should attempt these fields and preserve the source path or `not_verifiable` reason for each:

- `platform_channel_id`
- `channel_name`
- `channel_url`
- `profile_text`
- `follower_count`
- `live_status`
- `profile_image_url`
- `recent_live_or_vod_titles`
- `recent_categories`

Required validation:

- `platform_channel_id` or channel hash must equal `dcbccbf2d8e2a1b095244c5856d3613a`.
- `channel_name` should contain `김달수` or `Dalsu`.
- `follower_count` must be directly sourced or marked `not_verifiable`.
- `profile_text` must be directly sourced or marked `not_verifiable`.
- If only VOD/card fields are found, verdict must be `PARTIAL / contextual only`.

## Preferred Fields

- `source_api_endpoint`
- `source_json_path`
- `field_source_type`
- `api_status_code`
- `api_parse_status`
- `rendered_url`
- `observed_api_urls`
- `profile_header_selector_used`
- `missing_reason`
- `boundary_signal`
- `response_hash`
- `collected_at`
- `raw_record_path`
- `disclosure_tag`

## API Hints

Test these JSON path hints when the relevant endpoint returns usable JSON. They are hints, not facts from the previous artifact.

- `content.channelId`
- `content.channelIdHash`
- `content.channelName`
- `content.channelDescription`
- `content.followerCount`
- `content.channelImageUrl`
- `content.openLive`
- `content.videos[*].videoTitle`
- `content.videos[*].categoryType`
- `content.videos[*].videoCategory`

Record whether each field came from API response body, profile/header DOM, URL validation, or VOD/card DOM.

## Selector Hints

Prefer channel/profile/header selectors over VOD/card selectors:

- `[class*="channel"][class*="profile" i]`
- `[class*="channel"][class*="name" i]`
- `[class*="profile" i]`
- `[class*="follower" i]`
- `[aria-label*="팔로워"]`
- Page regions containing `김달수`, `Dalsu`, or `dcbccbf2d8e2a1b095244c5856d3613a`

The selector search should establish profile/header field availability before ranking any VOD/card array.

## VOD/Card Down-Rank Rule

`div.channel_home_vod_item__N7KA5` and any VOD/card DOM arrays must not become the primary `collection_plan` for this target.

Allowed use:

- Populate `recent_live_or_vod_titles`.
- Populate `recent_categories`.
- Provide weak context only after identity/profile field attempts are recorded.

Disallowed use:

- Treat VOD/card DOM as subject identity evidence.
- Treat VOD/card DOM as follower/profile evidence.
- Silently select VOD/card DOM as success when profile/API fields are absent.

If Charles cannot find profile/API fields, preserve the gap as `not_verifiable` or `intent_gap`. Do not downgrade the target intent to VOD/card success.

## Pass / Partial / No-Go Criteria

`PASS`:

- A usable channel API or profile/header DOM source is found.
- Channel hash equals `dcbccbf2d8e2a1b095244c5856d3613a`.
- Channel name contains `김달수` or `Dalsu`.
- `follower_count` and `profile_text` are either directly sourced or explicitly marked `not_verifiable` with source-specific reasons.
- Primary `collection_plan` is API/profile-header oriented, not VOD/card DOM.
- VOD/card fields, if present, are secondary context only.
- No checkpoint, CAPTCHA, login/session, `http_429`, restricted gate, or missing-plan boundary is present.

`PARTIAL`:

- Identity is plausibly confirmed by channel API/profile/header evidence, but one or more profile/current fields are `not_verifiable`.
- Channel API is observed but not parse-confirmed, while profile/header DOM gives some identity signal.
- Only recent VOD/card titles/categories are extracted. In this case the verdict must be `PARTIAL / contextual only`, not subject-profile success.
- The protocol may be retained as a review artifact but does not satisfy the original subject profile/current metrics intent by itself.

`NO-GO`:

- Channel hash mismatches the expected hash.
- Channel name conflicts with `김달수` / `Dalsu` expectation and no boundary explains the mismatch.
- `best_path=manual_review`, `gate_status=restricted`, `http_429`, CAPTCHA, checkpoint, login/session boundary, or missing `collection_plan` appears.
- Charles must use targets outside the allowed URL/API list to continue.
- VOD/card DOM is the only available evidence and is selected as the primary success path.

## Expected Boundary Handling

- Preserve `not_verifiable` exactly where a direct field source is absent.
- Preserve `boundary_signals`, `absences`, `protocol_hash`, source paths, and raw/structured artifact lineage.
- If API candidates are observed but not usable JSON endpoints, record that as an API diagnostic gap.
- If the page is visible but profile fields are unavailable, record `intent_gap` rather than promoting VOD/card context.
- If any restricted/manual-review/login/checkpoint/CAPTCHA/rate-limit condition appears, stop and preserve the boundary.
- Do not create or approve a CollectDirective from this request.

## Output Artifact Expectations

Future Charles execution, if separately approved, should produce:

- Full ScoutReport: `10_charles/chzzk_subject_channel_public_profile.profile_rescout_20260612.scout_report.json`
- Top-level protocol only: `10_charles/chzzk_subject_channel_public_profile.profile_rescout_20260612.protocol.json`
- Follow-up review note after execution: `20_review/chzzk_subject_profile_rescout_alignment_20260612.md`

Expected ScoutReport content:

- Tested page URLs and API endpoints.
- API status/parse results.
- Field-level source paths or `not_verifiable` reasons.
- Selector ranking with profile/header attempts before VOD/card arrays.
- Boundary signals and diagnostic findings.

Expected protocol behavior:

- Use API/profile-header evidence as the primary collection plan when available.
- If only VOD/card evidence is available, label the result contextual/partial and preserve missing profile fields as `not_verifiable`.
- Do not encode VOD/card DOM as the successful primary plan for the subject-profile intent.

## Arthur Inspect Eligibility

This request itself does not approve Arthur inspect.

After a future Charles rescout:

- `PASS`: Arthur inspect eligibility remains `later`; operator must first review the new ScoutReport/protocol against this request and the ResearchPlan intent.
- `PARTIAL`: no Arthur inspect for the original subject profile/current metrics intent. A separate contextual VOD/card target may be considered later only if explicitly scoped.
- `NO-GO`: no Arthur inspect.

CollectDirective draft eligibility remains `no`. Collect approval remains `no`.

## Next Operator Action

Review this request. If accepted, run one narrow Charles rediagnosis later against the allowed CHZZK page/API targets with the above field and down-rank rules. Then review the new ScoutReport/protocol before any Arthur step.
