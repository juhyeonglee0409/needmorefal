# Intent Alignment Review - Softcon Non-Default Chrome Profile Protocols

Date: 2026-06-11
Scenario: Scenario 3 - Charles/Arthur collection preparation
Scope: pre-Arthur protocol review only

## Decision Boundary

- This review checks whether five Charles clean protocols are aligned enough for Arthur inspect.
- This review does not approve collection.
- No Arthur inspect was run during this review.
- No Arthur collect was run.
- No CollectDirective was created.
- CaseResult, DisclosureLog, PublicDemoRow, and package canonical data remain unchanged.
- Legacy report and legacy CaseResult remain legacy references only, not fresh evidence.

## Inputs Reviewed

- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `20_review/intent_alignment_checklist.md`
- `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_lol_category_page.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_streamer.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_softcone.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`

## Global Checklist Result

| Check | Result | Note |
|---|---:|---|
| Operator-approved route match | PASS | All five protocol `target_url` values match the operator-provided Softcon routes. |
| Domain/scope | PASS | All targets remain under `viewership.softc.one`. |
| `best_path` executable | PASS | All five protocols use `best_path=rsc_payload`, not `manual_review`. |
| Gate status | PASS | All five protocols use `pre_check.gate_status=profile_cleared`. |
| Risk level | CAUTION | All five protocols use `risk_level=medium` because an operator-approved local profile was used. |
| `collection_plan` and `verification` | PASS | Present on all five protocols. |
| Profile secret handling | PASS | `profile_summary` records summary only: `type=guest_session`, `transport=chrome_profile`, `header_names=[]`, `cookie_names=[]`, `secret_values_logged=false`. |
| Raw/screenshot artifact handling | PASS | Browser-probe raw and screenshot saved flags are false on all five protocols. |
| Source path preservation | PASS | ScoutReport and protocol paths are listed below with hashes. |
| Boundary signals | PASS | No active restricted/checkpoint/http_429 boundary signal remains in these clean protocols. |
| Collect approval | BLOCKED | Collect remains blocked until Arthur inspect is reviewed and operator explicitly approves. |

## Per-Route Review

| Route | Mapped Research Intent | Result | Reason |
|---|---|---:|---|
| `softcon_subject_channel_current_stats` | Subject identity and current Softcon metrics | PASS | URL hash matches `dcbccbf2d8e2a1b095244c5856d3613a`; browser title includes `김달수 Dalsu`; protocol is `rsc_payload/profile_cleared`; plan and verification are present. |
| `softcon_chzzk_lol_category_page` | LoL/MOBA cohort population route set | CAUTION | URL and title are LoL-specific and visible, but protocol fields expose nested/category payloads. Arthur inspect must confirm that nested `liveChannels` can produce member-level cohort rows. |
| `softcon_chzzk_ranking_streamer` | LoL/MOBA cohort population route set | CAUTION | Clean broad streamer-ranking protocol. It may provide ranking metrics, but it is not LoL-specific by URL alone and must be joined or filtered against the LoL category route. |
| `softcon_chzzk_ranking_softcone` | Population/supporting ranking route | CAUTION | Protocol is clean and has plan/verification, but browser_probe reports `rate_limited=true` and `visible_content_likely=false`. Treat as an inspect-time review note, not collection approval. |
| `softcon_chzzk_follower_ranking_naverchzzk` | Follower count and channel URL/hash matching | CAUTION | Clean follower-ranking protocol with `followerCount`, `name`, `id`, `userId`, and `slug`. Arthur inspect must verify whether `channel_url`, `channel_hash`, and row-order `follower_rank` can be produced without inference from legacy data. |

## Protocol Status Summary

| Protocol | best_path | gate_status | risk | browser_probe | collection_plan | verification | Arthur inspect |
|---|---|---|---|---|---|---|---|
| `softcon_subject_channel_current_stats...protocol.json` | `rsc_payload` | `profile_cleared` | `medium` | ok, 200, checkpoint=false, rate_limited=false, visible=true | present | present | allowed |
| `softcon_chzzk_lol_category_page...protocol.json` | `rsc_payload` | `profile_cleared` | `medium` | ok, 200, checkpoint=false, rate_limited=false, visible=true | present | present | allowed with caution |
| `softcon_chzzk_ranking_streamer...protocol.json` | `rsc_payload` | `profile_cleared` | `medium` | ok, 200, checkpoint=false, rate_limited=false, visible=true | present | present | allowed with caution |
| `softcon_chzzk_ranking_softcone...protocol.json` | `rsc_payload` | `profile_cleared` | `medium` | ok, 200, checkpoint=false, rate_limited=true, visible=false | present | present | allowed with caution |
| `softcon_chzzk_follower_ranking_naverchzzk...protocol.json` | `rsc_payload` | `profile_cleared` | `medium` | ok, 200, checkpoint=false, rate_limited=false, visible=true | present | present | allowed with caution |

## Field Coverage Gaps To Carry Into Arthur Inspect

Subject current stats:

- Plausibly covered by protocol/source: `platform_channel_id` from URL hash, `channel_url` from target URL, `follower_count` via `maxFollowerCount`, `stream_hours` via `airTime`, `peak_viewers` via `maxLiveViews`, `avg_viewers` via `avgLiveViews`, `viewership`, `max_chat_6m` via `maxChatCount`, `avg_chat_6m` via `avgChatCount`, `collected_at` via `fetched_at`.
- Metadata/transform required: `run_id`, `case_id`, `streamer_key`, `platform`, `raw_record_path`, `disclosure_tag`.
- Gap to verify: `channel_name` must be captured from page/title or payload, not only inferred from legacy; `category_1` is not obvious in the current subject metrics fields.

Cohort population:

- Plausibly covered by protocol/source: LoL category route has `category`, `categoryCode`, `liveChannels`, `liveViews`; ranking routes have `creator`, `airTime`, `avgLiveViews`, `maxLiveViews`, `maxSubscribers`, `viewership`, chat metrics, and ranking-like fields.
- Metadata/transform required: `run_id`, `cohort_cell_id`, `cohort_type`, `source_name`, `source_url`, `request_url`, `platform`, `raw_record_path`, `collected_at`, `disclosure_tag`.
- Gaps to verify: nested `liveChannels` or `creator` must yield `channel_id`, `channel_name`, and `channel_url`; LoL/MOBA filter basis must be explicit; aggregation window start/end must be derivable; `follower_count` mapping from `maxSubscribers` must be validated; `is_virtual`, `is_esports_team`, `is_tournament`, `is_corporate`, and `exclude_reason` require downstream classification, not Charles inference.

Follower ranking:

- Plausibly covered by protocol/source: `followerCount`, `name`, `id`, `userId`, `slug`, timestamps, and source URL.
- Metadata/transform required: `run_id`, `source_name`, `platform`, `raw_record_path`, `disclosure_tag`.
- Gaps to verify: `channel_url` construction, exact `channel_hash` mapping, and `follower_rank` from row order must be confirmed by Arthur inspect or later transform rules; do not fill these from legacy data.

## Arthur Inspect Allowed Targets

Arthur inspect is allowed for these protocol-only inputs, subject to operator instruction:

1. `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
2. `10_charles/softcon_chzzk_lol_category_page.chrome_profile_non_default_20260611.protocol.json`
3. `10_charles/softcon_chzzk_ranking_streamer.chrome_profile_non_default_20260611.protocol.json`
4. `10_charles/softcon_chzzk_ranking_softcone.chrome_profile_non_default_20260611.protocol.json`
5. `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`

Recommended inspect order:

1. Subject channel current stats.
2. LoL category page.
3. Follower ranking.
4. Ranking streamer.
5. Ranking softcone.

Rationale: subject identity, category basis, and follower/hash matching should be validated before using broader ranking surfaces.

## Arthur Inspect Blocked Targets

None at the protocol-review stage.

This does not mean collection is approved. Any target can still be blocked after Arthur inspect if the InspectResult fails target identity, field coverage, source scope, or verification alignment.

## Source Paths And Hashes

| Target | ScoutReport SHA256 | Protocol SHA256 |
|---|---|---|
| `softcon_subject_channel_current_stats` | `0b08677bdccc88d52a25c67148fc1445bd6a3b178d8799ad909b98f583b60dfd` | `7bca74c59ed699cf48dc2359d0cf567915a18e6e78c7b44144be68af46acec90` |
| `softcon_chzzk_lol_category_page` | `5c73a303eefe5eb2a52ddf42cd7f18ab36f68e6d4a105edba09a072807c01845` | `160bb74ca3d4b65a4f73d386dd5bc5bc585ae9e0457b422c57aafc94cdf3f890` |
| `softcon_chzzk_ranking_streamer` | `a18e329d54475cf00078295bb8949e0f7819ce015f3a3eced4bc9d94aa80b21e` | `3fb35e8ecb2308ff96b419f2b494c3de5e6997ce048cd5af93c211f8f7db76a4` |
| `softcon_chzzk_ranking_softcone` | `2e54017517e1c83f5decd875ba0830e09a2a2f3c8ae60c43f7e06f70c374d755` | `7c9de3015991ab7d9c9a11339c5e364a7f188e0768bc88aa55e0695f431c5b56` |
| `softcon_chzzk_follower_ranking_naverchzzk` | `23e04e3eb9ca74ed419df2a85a5660ca1b08075fb4503faa603b94643832eb45` | `14d171c8a4c423c3181e234482ffec4b03c96122bb6675e9178ed1b26564a158` |

Source path set:

- `10_charles/*.chrome_profile_non_default_20260611.scout_report.json`
- `10_charles/*.chrome_profile_non_default_20260611.protocol.json`

## Remaining Risks

- The review is pre-Arthur. InspectResult identity and executable detail are still pending.
- `ranking/softcone` has a browser-probe caution: `rate_limited=true`, `visible_content_likely=false`.
- Several required fields require transform metadata or nested payload interpretation; they must not be silently inferred from legacy sources.
- Profile-based access keeps risk at `medium`; secret values must remain excluded from notes, manifests, logs, ScoutReports, and downstream artifacts.

## Smallest Next Action

Run Arthur inspect on the five allowed top-level protocol files only, then repeat this checklist against the resulting InspectResults. Do not create CollectDirective and do not collect until the InspectResults pass intent alignment and the operator explicitly approves the next step.
