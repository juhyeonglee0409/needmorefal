# 구비바 §7 YouTube Survey Run 20260619

Generated: 2026-06-19T23:42:34

## Scope

- Input: `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\data\cohort\collected\cohort_ref_upper_band.csv`
- Sampling: band sample 30 each was attempted. Presence stopped at 84/90 because YouTube search returned HTTP 429 at the 85th sampled channel.
- YouTube Data API key present: True
- Raw HTML/JSON persisted: no
- Cookie/token/localStorage/sessionStorage/auth header/screenshot persisted: no
- Canonical case state mutated: no

## Outputs

- Presence: `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\data\cohort\collected\youtube_presence_271.csv`
- Active metrics: `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\data\cohort\collected\youtube_metrics_active.csv`
- Gubiva: `D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\data\cohort\collected\youtube_gubiva.csv`

## Results

### Task 1 Presence

- target_rows: 84
- skipped_existing: 0
- chzzk_social_link: 0
- youtube_search: 78
- not_found: 6
- errors: 0

### Task 2 Metrics

- active_with_channel_id: 78
- metrics_rows: 78
- missing_metrics: 0
- band distribution: 10k-20k 29, 20k-50k 26, 50k+ 23
- content_type_primary: clip 31, highlight 23, mixed 10, full_vod 7, original 6, blank 1
- duplicates: 0

### Task 3 Gubiva

- has_youtube: not_collected

## Boundary

- Task 1 boundary: YouTube Data API `Search.list` returned `youtube_search_http_429` at `앰비션 / 8a59b34b46271960c1bf172bb0fac758`.
- Interpretation: quota-unit exhaustion, not WAF/rate probing failure. `Search.list` costs 100 quota units per call, so 80+ searches can consume most of the default 10,000 daily units.
- Retried once with CHZZK lookup disabled; the same YouTube search boundary persisted, so presence collection stopped without further retry in the same quota window.
- Task 2 metrics collection for the 78 confirmed YouTube channel IDs completed after switching to metrics-only mode.
- Task 3 Gubiva channel search was not run after the YouTube search boundary.

## Notes

- `youtube_search` uses YouTube Data API `Search.list`, which is expensive at 100 quota units per call.
- After daily quota reset, the remaining 6 sampled channels should cost roughly 600 units; metrics-only collection is cheap because `Channels.list`, `PlaylistItems.list`, and `Videos.list` cost about 1 unit per call.
- `chzzk_social_link` is preferred when available because it is directly linked from the streamer profile/page.
- `match_confidence=medium` rows should be manually spot-checked before analytic conclusions.
- `youtube_gubiva.csv` remains uncreated because Task 3 requires a new YouTube search after the search boundary.
