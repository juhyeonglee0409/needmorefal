# Charles CHZZK API Body Capture Patch Review - 2026-06-12

Type: `review_note` / `patch_candidate`.

Scope: offline tooling patch and synthetic/mock tests only. No live web access, no Charles live rerun, no Arthur inspect/collect.

## Inputs Reviewed

- `20_review/chzzk_subject_profile_rescout_alignment_20260612.md`
- `20_review/chzzk_subject_profile_rescout_request_20260612.md`
- `10_charles/chzzk_subject_profile_rescout_20260612.scout_report.json`
- `10_charles/chzzk_subject_profile_rescout_20260612.protocol.json`
- Prior comparison only: `20_review/chzzk_public_profile_protocol_intent_gap_20260612.md`

## Root Cause

The CHZZK rescout reached page/API HTTP 200 and recorded XHR/fetch JSON observations, including:

- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a`
- `https://api.chzzk.naver.com/service/v1/channels/dcbccbf2d8e2a1b095244c5856d3613a/videos?...`

However, `observed_apis` stored only URL/method/resource/status/content_type. It did not store parsed body summaries, field paths, or scalar hints. Protocol promotion then required a reusable JSON data API but had no body-level proof that the CHZZK channel endpoint contained `content.channelName`, `content.followerCount`, or other profile fields.

The existing protocol therefore fell back to rendered DOM data evidence:

- `collection_plan.source=rendered_dom`
- primary selector `div.channel_home_vod_item__N7KA5`
- fields `thumbnail`, `time`, `title`, `video_card_item__lOC8Y`, `blind`, `category`
- diagnostic API status `rejected`, usable candidates `0`

This is a VOD/card contextual plan, not a subject profile/current metrics plan.

## Patch Candidate

Changed Charles tooling files:

- `IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract/api_body_summary.py`
- `IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract/schemas.py`
- `IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract/playwright_phase2.py`
- `IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract/protocol_builder.py`
- `IsaacInfra/Charles/current/CrawlScouter_v0.10.0_pipeline_contract/tests/test_chzzk_api_body_capture_v0_10.py`

Behavior added:

- Capture allowed JSON XHR/fetch response bodies in memory during Playwright phase2.
- Parse only under a max response body cap.
- Store no raw JSON body by default.
- Store only structured `body_summary`: parse status, byte length, field paths, profile field paths, contextual field paths, redacted sample scalar values, and classification.
- Redact token/cookie/auth-like URL query and scalar values.
- Do not capture cookies, auth headers, or browser storage values.
- Restrict body capture to same target-domain JSON APIs plus the explicit CHZZK page-to-`api.chzzk.naver.com/service/v1/channels/...` allowlist.
- Classify CHZZK channel profile endpoint as profile-usable only when identity fields are present, especially `content.channelName` plus `content.channelId` or `content.channelIdHash`.
- Classify CHZZK videos/clips/channel-home data endpoints as contextual only for the subject profile/current metrics intent.
- Prefer API/profile field summaries over rendered VOD/card DOM when the usable profile API summary exists.

Supported CHZZK field hints:

- `content.channelId`
- `content.channelIdHash`
- `content.channelName`
- `content.channelDescription`
- `content.followerCount`
- `content.channelImageUrl`
- `content.openLive`

## Safety Constraints Implemented

- No durable raw response body artifact is added.
- `body_summary` contains structured summaries only.
- Token/cookie/auth-like body scalar values are redacted as `<redacted>`.
- Token/cookie/auth-like query values are redacted before report/protocol serialization.
- Cookies remain name/domain/path metadata only; no cookie values are stored.
- Auth headers and browser storage values are not captured.
- Oversize bodies are skipped and not promoted.
- Non-JSON bodies are skipped and not promoted.
- JSON parse failure records a non-success parse status and does not force API usability.
- CHZZK cross-subdomain promotion requires the explicit path allowlist and body-level profile field proof.

## Tests

Executed with bundled Python:

- `tests/test_chzzk_api_body_capture_v0_10.py`: 14 PASS / 0 FAIL
- `tests/test_protocol_v0_8.py`: 20 PASS / 0 FAIL with `PYTHONIOENCODING=utf-8`
- `tests/test_playwright_phase2_v0_4.py`: 15 PASS / 0 FAIL
- `tests/test_review_improvements_v0_8.py`: 31 PASS / 0 FAIL
- `tests/test_verification_gate_phase2_v0_6.py`: 11 PASS / 0 FAIL
- `tests/test_html_report_v0_5.py`: 24 PASS / 0 FAIL
- `tests/test_challenge_phase2_v0_5.py`: 10 PASS / 0 FAIL
- `python -m py_compile api_body_summary.py schemas.py playwright_phase2.py protocol_builder.py tests/test_chzzk_api_body_capture_v0_10.py`: pass

Note: one first run of `test_protocol_v0_8.py` without `PYTHONIOENCODING=utf-8` failed in a pre-existing CLI help stdout decoding path. The same test passed after setting the encoding environment variable.

## Current Protocol Verdict

This patch does not make the current saved CHZZK protocol sufficient.

Current artifacts remain unchanged and still lack `body_summary`. Offline checks confirm the saved protocol remains:

- `best_path=playwright`
- `collection_plan.source=rendered_dom`
- VOD/card DOM selector primary
- API usable candidates `0`
- `channel_name`, `profile_text`, `follower_count`, `live_status`, and `profile_image_url` remain `not_verifiable`

Verdict: `PARTIAL / contextual only`.

Arthur inspect eligibility: `no/later` until a new protocol covers the profile intent.

CollectDirective draft eligibility: `no`.

Collect approval: `no`.

## Next Action

Patch candidate is ready for one future operator-approved CHZZK subject profile rescout. The next action is a single approved Charles rescout against the already scoped CHZZK subject profile target/API hints, followed by offline alignment review.

Do not run Arthur inspect, Arthur collect, or create a CollectDirective from the current protocol.

## Boundary Confirmation

- Live web access used in this patch session: no
- Charles live rerun executed: no
- Arthur inspect executed: no
- Arthur collect executed: no
- CollectDirective created: no
- CollectionResult created: no
- Package canonical data mutated: no
- CaseResult mutated: no
- DisclosureLog mutated: no
- PublicDemoRow mutated: no
