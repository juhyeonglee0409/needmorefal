# Intent Alignment Review - Softcon Non-Default Chrome Profile Diagnosis

Date: 2026-06-12
Scenario: Scenario 3 - Charles/Arthur collection preparation
Review scope: Charles diagnosis/protocol intent alignment only

## Boundary

- Arthur inspect was not run.
- Arthur collect was not run.
- CollectDirective was not created.
- Collect approval is `no` for every target at this stage.
- CaseResult, DisclosureLog, PublicDemoRow, and package canonical data were not changed.
- Legacy report and legacy CaseResult remain legacy references only, not fresh evidence.

## Inputs

- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `20_review/intent_alignment_checklist.md`
- `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_lol_category_page.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_streamer.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_softcone.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`

## Global Review

| Check | Result | Note |
|---|---:|---|
| Scenario fit | PASS | This is Scenario 3 pre-Arthur collection preparation. |
| Operator-approved scope | PASS | Profile config scope is `Softcon route diagnosis only`; all five protocol URLs are under `viewership.softc.one`. |
| Profile/session handling | PASS | Protocols record `type=guest_session`, `transport=chrome_profile`, `secret_values_logged=false`, `header_names=[]`, `cookie_names=[]`. |
| Token/cookie value storage | PASS | No token/cookie values were printed or recorded in this review. Protocol summaries show only empty name lists. |
| Raw/screenshot storage | PASS | All five browser probes have `browser_probe_raw_saved=false` and `browser_probe_screenshot_saved=false`. |
| Protocol gate | PASS | All five protocols use `best_path=rsc_payload` and `pre_check.gate_status=profile_cleared`. |
| Risk level | CAUTION | All five protocols remain `risk_level=medium` because profile-based diagnosis was used. |
| `collection_plan` / `verification` | PASS | Both are present in all five protocols. This is not collect approval. |
| Boundary/source preservation | PASS | Source paths and protocol hashes are recorded below. Boundary cautions are carried forward. |

## Per-Route Verdict

| Route | Research intent | Verdict | Arthur inspect allowed | Collect approval | Remaining blockers |
|---|---|---:|---:|---:|---|
| `softcon_subject_channel_current_stats` | Subject identity and current metrics | PASS | yes | no | Arthur inspect must confirm row shape and final mappings for `channel_name`, `category_1`, metadata fields, and raw record path. |
| `softcon_chzzk_follower_ranking_naverchzzk` | Follower count and channel hash/URL matching | PARTIAL | yes | no | `followerCount`, `name`, `id`, `userId`, and `slug` are present, but `channel_url`, `channel_hash`, and `follower_rank` must be derived or confirmed without legacy inference. |
| `softcon_chzzk_lol_category_page` | LoL/MOBA population reconstruction | PARTIAL | yes | no | Route and title are LoL-specific, but visible text shows an Enterprise membership boundary and protocol fields expose category/nested `liveChannels`, not a confirmed full cohort table yet. |
| `softcon_chzzk_ranking_streamer` | Population support/ranking metrics | CAUTION | yes | no | Clean protocol, but the route is broad streamer ranking. It cannot by itself prove LoL/MOBA population membership without category join/filter logic. |
| `softcon_chzzk_ranking_softcone` | Population support/ranking metrics | CAUTION | yes | no | Protocol is clean, but browser_probe reports `rate_limited=true` and `visible_content_likely=false`; keep as an inspect-time warning. |

## Route-Specific Evidence

### Subject Page

- Protocol URL: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- Expected channel hash from TargetBatchPlan: `dcbccbf2d8e2a1b095244c5856d3613a`
- Browser title: `김달수 Dalsu | 치지직 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- Visible text confirms the subject page names `김달수 Dalsu`, includes the target hash, shows follower/current metrics text, and includes LoL category share text.
- Collection fields include `date`, `maxFollowerCount`, `airTime`, `maxLiveViews`, `avgLiveViews`, `viewership`, `maxChatCount`, and `avgChatCount`.

Review result: aligned with subject identity/current metrics intent, pending Arthur inspect for exact field extraction and metadata mapping.

### Follower Ranking

- Protocol URL: `https://viewership.softc.one/ranking/followers?type=naverchzzk`
- Browser title: `스트리머 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- Visible text identifies `스트리머 팔로워 랭킹`, `팔로워 / 애청자 랭킹`, and platform filters including `치지직`.
- Collection fields include `followerCount`, `name`, `id`, `userId`, `slug`, `recentLiveAt`, and `recentLiveCategory`.

Review result: aligned with follower count intent, partial for channel URL/hash matching until Arthur inspect confirms whether `slug`/`userId` can produce canonical `channel_url`, `channel_hash`, and `follower_rank`.

### LoL Category Route

- Protocol URL: `https://viewership.softc.one/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C`
- Browser title: `리그 오브 레전드 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- Visible text confirms the category boundary: `리그 오브 레전드 / League of Legends`.
- Visible text also records a membership boundary: `높은 등급의 멤버십이 필요합니다 ENTERPRISE 부터 이용 가능합니다`.
- Collection fields include `category`, `categoryCode`, `chatCount`, `liveChannels`, `liveViews`, and `type`.

Review result: the URL and visible text match the LoL category intent, but population reconstruction remains partial until Arthur inspect confirms whether nested `liveChannels` yields the required member-level cohort fields and whether membership-gated UI affects completeness.

### Ranking Streamer

- Protocol URL: `https://viewership.softc.one/ranking/streamer`
- Browser title: `스트리머 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- Visible text describes broad streamer ranking filters and platform filters.
- Collection fields include `creator`, `airTime`, `maxLiveViews`, `avgLiveViews`, `maxSubscribers`, `viewership`, `maxChatCount`, and `avgChatCount`.

Review result: useful as a support route for ranking metrics, but not sufficient alone for LoL/MOBA population membership.

### Ranking Softcone

- Protocol URL: `https://viewership.softc.one/ranking/softcone`
- Browser title: `소프트콘 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- Protocol status is clean: `rsc_payload/profile_cleared`.
- Browser-probe warning remains: `rate_limited=true`, `visible_content_likely=false`.
- Collection fields include `creator`, `rankPoint`, `minRank`, `airTime`, `maxLiveViews`, `avgLiveViews`, `viewership`, and rank columns.

Review result: Arthur inspect may run, but this target carries a warning. If InspectResult cannot verify the visible/rate-limit discrepancy, do not use it to fill critical cohort membership fields.

## Required Field Coverage Gaps

Subject current stats:

- Plausibly covered: `platform_channel_id`, `channel_url`, `follower_count`, `stream_hours`, `peak_viewers`, `avg_viewers`, `viewership`, `max_chat_6m`, `avg_chat_6m`, `collected_at`.
- Needs mapping/metadata: `run_id`, `case_id`, `streamer_key`, `platform`, `raw_record_path`, `disclosure_tag`.
- Gap: `channel_name` and `category_1` must be extracted from page/payload evidence, not legacy assumptions.

Cohort population:

- Plausibly covered by route set: category fields, nested `liveChannels`, creator/ranking metric payloads, stream/view/chat/subscriber metrics.
- Needs mapping/metadata: `run_id`, `cohort_cell_id`, `cohort_type`, `source_name`, `source_url`, `request_url`, `platform`, `raw_record_path`, `collected_at`, `disclosure_tag`.
- Gaps: member-level `channel_id`, `channel_name`, `channel_url`, category basis, aggregation window, expected row count, and classification fields such as `is_virtual`, `is_esports_team`, `is_tournament`, `is_corporate`, and `exclude_reason`.

Follower ranking:

- Plausibly covered: `source_url`, `channel_name`, `follower_count`, timestamp fields, candidate id/slug fields.
- Needs mapping/metadata: `run_id`, `source_name`, `platform`, `raw_record_path`, `disclosure_tag`.
- Gaps: `channel_url`, `channel_hash`, and `follower_rank` must be validated from payload/order or documented as absent.

## Source Paths And Hashes

| Target | ScoutReport SHA256 | Protocol SHA256 |
|---|---|---|
| `softcon_subject_channel_current_stats` | `0b08677bdccc88d52a25c67148fc1445bd6a3b178d8799ad909b98f583b60dfd` | `7bca74c59ed699cf48dc2359d0cf567915a18e6e78c7b44144be68af46acec90` |
| `softcon_chzzk_lol_category_page` | `5c73a303eefe5eb2a52ddf42cd7f18ab36f68e6d4a105edba09a072807c01845` | `160bb74ca3d4b65a4f73d386dd5bc5bc585ae9e0457b422c57aafc94cdf3f890` |
| `softcon_chzzk_ranking_streamer` | `a18e329d54475cf00078295bb8949e0f7819ce015f3a3eced4bc9d94aa80b21e` | `3fb35e8ecb2308ff96b419f2b494c3de5e6997ce048cd5af93c211f8f7db76a4` |
| `softcon_chzzk_ranking_softcone` | `2e54017517e1c83f5decd875ba0830e09a2a2f3c8ae60c43f7e06f70c374d755` | `7c9de3015991ab7d9c9a11339c5e364a7f188e0768bc88aa55e0695f431c5b56` |
| `softcon_chzzk_follower_ranking_naverchzzk` | `23e04e3eb9ca74ed419df2a85a5660ca1b08075fb4503faa603b94643832eb45` | `14d171c8a4c423c3181e234482ffec4b03c96122bb6675e9178ed1b26564a158` |

Protocol path set:

- `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_lol_category_page.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_streamer.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_softcone.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`

## Remaining Blockers

- Arthur InspectResult does not exist yet.
- CollectDirective does not exist and must not be created from this review alone.
- LoL population completeness is not proven until nested route payloads are inspected.
- Follower ranking hash/URL/rank derivation is not proven until inspect confirms payload shape or records absence.
- `ranking/softcone` browser_probe warning must be carried into any future InspectResult review.
- No required field should be filled from legacy report or legacy CaseResult.

## Smallest Next Action

If the operator explicitly approves the next step, run Arthur inspect on the five top-level protocol files only. Then repeat this intent-alignment checklist against the InspectResults before any CollectDirective draft or collection approval.
