# Post-Inspect Intent Alignment Review - Softcon Visible Networkidle

Date: 2026-06-12
Scenario: Scenario 3 - Charles/Arthur collection preparation
Review scope: Arthur InspectResult intent alignment only

## Boundary

- Arthur inspect was already run on five Softcon routes using operator-approved headed `chrome_profile`, `wait_until=networkidle`, and `settle_wait_ms=1500`.
- This review does not run Arthur inspect, Arthur collect, or Charles.
- CollectDirective was not created.
- Collect approval is `no` for every route.
- CaseResult, DisclosureLog, PublicDemoRow, and package canonical data were not changed.
- Legacy report and legacy CaseResult remain legacy references only, not fresh evidence.

## Inputs

- `20_review/intent_alignment_softcon_profile_non_default_20260612.md`
- `20_review/intent_alignment_checklist.md`
- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `30_arthur_inspect/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `30_arthur_inspect/softcon_chzzk_lol_category_page.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `30_arthur_inspect/softcon_chzzk_ranking_streamer.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `30_arthur_inspect/softcon_chzzk_ranking_softcone.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_lol_category_page.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_streamer.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_ranking_softcone.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_subject_channel_current_stats.charles_profile_ab_smoke_20260612.protocol.json`

## Global Inspect Result

| Check | Result | Note |
|---|---:|---|
| Access checkpoint | PASS | All five InspectResults returned `response_status=200`, `effective_status=response_200`, `checkpoint_detected=false`. |
| RSC availability | PASS | All five InspectResults have `rsc_payload_detected=true` and `field_maps` from `rsc_payload`. |
| Field map availability | PASS | Field maps exist for all routes: subject 3, follower 2, LoL category 3, ranking/streamer 3, ranking/softcone 3. |
| Sample row availability | CAUTION | `sample_records=0` for all five routes. Arthur currently maps RSC fields but does not emit sample rows from these RSC payloads. |
| Profile/session boundary | CAUTION | Success requires headed/visible `chrome_profile`; headless `chrome_profile` previously returned checkpoint. Treat headed profile dependency as a boundary. |
| Token/cookie handling | PASS | Session profile summaries are value-free: `secret_values_logged=false`, `header_names=[]`, `cookie_names=[]`. |
| Raw/screenshot handling | PASS | `--save-raw` was not used. Raw HTML and screenshots were not saved. |
| LoL category API sample | CAUTION | LoL category InspectResult preserves a grey `api_sample/http_429`; keep as a boundary note. |
| Collect readiness | BLOCKED | Arthur collect has not been run and `chrome_profile` collect remains a separate tooling/approval decision. |

## Per-Route Verdict

| Route | Verdict | CollectDirective draft eligibility | Collect approval | Reason |
|---|---:|---:|---:|---|
| `softcon_subject_channel_current_stats` | PASS | later | no | Subject URL/title/hash align with identity intent, and metric field maps exist. Draft should wait for sample-row/value validation and headed collect transport policy. |
| `softcon_chzzk_follower_ranking_naverchzzk` | PARTIAL | later | no | Follower ranking fields exist, including `followerCount`, `name`, `id`, `userId`, and `slug`; `channel_url`, `channel_hash`, and `follower_rank` still need derivation/validation. |
| `softcon_chzzk_lol_category_page` | CAUTION | no | no | Route is LoL-specific and field maps exist, but payload is category summary/time-series rather than confirmed member-level cohort population. Membership/API boundary remains. |
| `softcon_chzzk_ranking_streamer` | PARTIAL | later | no | Broad streamer ranking has creator and metric fields useful for population/ranking support, but it is not LoL-specific without join/filter logic. |
| `softcon_chzzk_ranking_softcone` | CAUTION | later | no | Ranking metric payload exists, but this is a support signal, not core cohort membership evidence. Earlier browser-probe warning remains a caution. |

## Route Notes

### Subject Current Stats

Inspect evidence:

- Target URL: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- Rendered title: `김달수 Dalsu | 치지직 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- HTTP/effective status: `200` / `response_200`
- RSC detected: `true`
- Field maps: 3 from `rsc_payload`
- RSC row counts: 53, 53, 117
- Boundary signals: `robots_check`

Intent fit:

- PASS for subject identity/current metrics intent.
- Expected channel hash is present in the target URL.
- Available metric fields include `airTime`, `avgChatCount`, `avgLiveViews`, `date`, `maxFollowerCount`, `maxLiveViews`, `maxSubscribers`, `sumLiveViews`, and `viewership`.

Remaining gaps:

- `sample_records=0` prevents value-level sample validation in the InspectResult.
- Metadata fields such as `run_id`, `case_id`, `streamer_key`, `platform`, `raw_record_path`, and `disclosure_tag` remain orchestration/ingest fields, not source payload fields.
- `channel_name`, `channel_url`, and `category_1` need explicit extraction/mapping rules; do not fill them from legacy material.

### Follower Ranking

Inspect evidence:

- Target URL: `https://viewership.softc.one/ranking/followers?type=naverchzzk`
- Rendered title: `스트리머 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- HTTP/effective status: `200` / `response_200`
- RSC detected: `true`
- Field maps: 2 from `rsc_payload`
- Main RSC row count: 100
- Boundary signals: `robots_check`

Intent fit:

- PARTIAL for follower count/channel matching intent.
- Available fields include `createdAt`, `followerCount`, `id`, `language`, `name`, `nospacename`, `profileImg`, `recentLiveAt`, `recentLiveCategory`, `recentLiveTitle`, `simulcastId`, `slug`, `subscriberCount`, `tags`, `teamsId`, `type`, `updatedAt`, and `userId`.

Remaining gaps:

- `follower_rank` is not a direct field in the field map; it may need row-order derivation and must be verified during collection.
- `channel_url` and `channel_hash` are not directly confirmed. `slug`/`userId` may support derivation, but that rule must be explicit and verified.
- `sample_records=0` means no value-level examples are available in InspectResult output.

### LoL Category Page

Inspect evidence:

- Target URL: `https://viewership.softc.one/category/%EB%A6%AC%EA%B7%B8%20%EC%98%A4%EB%B8%8C%20%EB%A0%88%EC%A0%84%EB%93%9C`
- Rendered title: `리그 오브 레전드 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- HTTP/effective status: `200` / `response_200`
- RSC detected: `true`
- Field maps: 3 from `rsc_payload`
- RSC row counts: 3530, 3530, 3530
- Boundary signals: `robots_check`, grey `api_sample/http_429`

Intent fit:

- CAUTION for LoL/MOBA population reconstruction.
- The route is category-correct and exposes category time-series/summary fields: `category`, `categoryCode`, `chatCount`, `createdAt`, `id`, `liveChannels`, `liveViews`, and `type`.
- The payload does not yet prove member-level cohort rows with `channel_id`, `channel_name`, `channel_url`, `stream_hours`, `peak_viewers`, `avg_viewers`, and `follower_count`.

Remaining gaps:

- Treat as category summary/stat signal unless collection proves nested member rows.
- Enterprise/membership boundary from the pre-inspect review remains relevant.
- Grey `api_sample/http_429` must be preserved. Do not reinterpret it as success or failure.

### Ranking Streamer

Inspect evidence:

- Target URL: `https://viewership.softc.one/ranking/streamer`
- Rendered title: `스트리머 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- HTTP/effective status: `200` / `response_200`
- RSC detected: `true`
- Field maps: 3 from `rsc_payload`
- Main RSC row count: 100
- Boundary signals: `robots_check`

Intent fit:

- PARTIAL for population support.
- Available fields include `airTime`, `avgChatCount`, `avgLiveViews`, nested `creator.name`, nested `creator.profileImg`, nested `creator.type`, `maxChatCount`, `maxLiveViews`, `maxSubscribers`, `sumChatCount`, `sumCount`, `sumLiveViews`, and `viewership`.
- This is useful for ranking/metric support but is broad, not LoL-specific.

Remaining gaps:

- Requires category join/filter logic before it can support LoL/MOBA cohort population reconstruction.
- `channel_id`, `channel_url`, and exclusion classification fields are not yet verified as direct output fields.
- `sample_records=0` prevents value-level sanity checks.

### Ranking Softcone

Inspect evidence:

- Target URL: `https://viewership.softc.one/ranking/softcone`
- Rendered title: `소프트콘 랭킹 : 소프트콘 뷰어십 SOFTC.ONE VIEWERSHIP`
- HTTP/effective status: `200` / `response_200`
- RSC detected: `true`
- Field maps: 3 from `rsc_payload`
- Main RSC row count: 100
- Boundary signals: `robots_check`

Intent fit:

- CAUTION as support ranking signal.
- Available fields include `airTime`, `avgChatCount`, `avgLiveViews`, `avgLiveViewsRank`, nested `creator.name`, nested `creator.profileImg`, `maxLiveViewsRank`, `minRank`, `rankPoint`, `sumLiveViewsRank`, and `viewership`.
- This route can support relative ranking/metric context, but it is not a primary source for LoL cohort membership.

Remaining gaps:

- Earlier browser_probe warning from the Charles review remains: `rate_limited=true`, `visible_content_likely=false`.
- Not sufficient as core cohort membership evidence without corroborating route joins.
- `sample_records=0` prevents value-level sanity checks.

## Required Field Coverage Summary

| Field group | Coverage judgment | Notes |
|---|---:|---|
| Subject current stats | PARTIAL-PASS | Core metric fields are mapped; identity is supported by target URL/title. Metadata and source path fields are orchestration fields. Channel/category text needs explicit extraction rules. |
| Follower rank | PARTIAL | `followerCount`, `name`, `id`, `userId`, `slug` are mapped. `follower_rank`, `channel_url`, and `channel_hash` require derivation/validation. |
| Cohort population | PARTIAL/CAUTION | LoL category route is category-correct but summary-like. Ranking routes are broad and require category join/filter logic. |
| Public/profile boundary | CAUTION | Headed `chrome_profile` is required. Treat this as an operator-approved, profile-gated diagnostic/collection boundary. |
| Value samples | CAUTION | `sample_records=0` across all five InspectResults. Field maps establish availability, not row-level sample validation. |

## CollectDirective Draft Eligibility

No route should receive `approved=true`.

Draft eligibility is not the same as collect approval:

- `subject`: `later`, after value/sample validation strategy and headed collect transport policy are defined.
- `follower ranking`: `later`, after rank/hash/url derivation rules are defined.
- `LoL category`: `no` for cohort population as currently scoped; possible future summary/support directive only.
- `ranking/streamer`: `later`, as a population-support route after category join/filter design.
- `ranking/softcone`: `later`, as a support signal only, preserving browser_probe caution.

Current blocking condition:

```text
Arthur collect with headed chrome_profile is not yet an approved execution path.
```

## Source Paths And Hashes

InspectResult hashes use SHA256 prefix for handoff traceability.

| Route | InspectResult SHA256 prefix | Protocol SHA256 prefix |
|---|---|---|
| subject | `c9947da522c7b75e` | `7bca74c59ed699cf` |
| follower ranking | `28030154dff12205` | `14d171c8a4c423c3` |
| LoL category | `29b06cc11f57cf58` | `160bb74ca3d4b65a` |
| ranking/streamer | `554cd23059a9f460` | `3fb35e8ecb2308ff` |
| ranking/softcone | `5bce8fa84124b208` | `7c9de3015991ab7d` |

## Final Review Verdict

The five visible-networkidle InspectResults are sufficient to confirm that Arthur can inspect the Softcon RSC field surfaces under operator-approved headed `chrome_profile`.

They are not sufficient to approve collect.

Main reasons:

- field maps exist, but sample rows are absent from InspectResult output;
- LoL cohort population intent is not fully satisfied by the category route alone;
- follower rank/hash/url fields require derivation or explicit absence handling;
- headed profile dependency is a material boundary;
- Arthur collect does not yet have an approved headed `chrome_profile` execution contract.

## Smallest Next Action

Prepare an Arthur collect `chrome_profile` patch candidate or collect-run design, but keep it scoped and unapproved:

1. define headed `chrome_profile` collect policy and artifact restrictions;
2. define row/value sample validation requirements;
3. start with `subject` and `follower ranking` as the first possible collect candidates;
4. keep `CollectDirective.approved=false`;
5. ask the operator for explicit approval before any collect execution.
