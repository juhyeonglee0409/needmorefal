# TargetReviewSummary

- run_id: kimdalsu_recollect_20260616_01
- generated_at: 2026-06-16T22:00:17+09:00
- operator approval: collection only; promotion not approved

| target_id | status | rows | parse_status | boundary |
|---|---:|---:|---|---|
| `softcon_subject_channel_current_stats` | collected | 1 | ok |  |
| `softcon_chzzk_lol_population_monthly` | collected | 100 | below_expected_min_rows |  |
| `softcon_chzzk_follower_ranking_enterprise` | collected | 3987 | ok |  |
| `semorank_chzzk_follower_public_crosscheck` | collected | 60 | ok |  |
| `chzzk_subject_channel_public_profile` | collected | 1 | ok |  |
| `youtube_dalsooisfree_content_funnel` | collected | 15 | ok |  |
| `softcon_cohort_member_profile_enrichment` | collected | 100 | partial |  |
| `auro_live_chzzk_follower_public_crosscheck` | boundary | 0 | blocked | not_collected_route_requires_chrome_js_fetch_devalue_parser |

## Notes

- Softcon subject stats collected successfully: follower, stream_hours, peak/avg viewers, viewership, and 6-minute chat metrics are present.
- Softcon LoL population was repaired to 100 rows from the filtered naverchzzk category route. Residual risk: `category_route_visible_cap_100_rows`.
- Softcon follower ranking was recovered to 3987 unique rows across pages 1..40 with no boundary signal observed during the corrected run.
- Softcon cohort member enrichment collected 100 channel-page rows. Follower count and recent category were captured for all 100 rows; profile_text was observed only on 2 rows, so the artifact remains partial. Corporate/team/tournament/virtual flags remain blank and require review logic before promotion.
- YouTube used the public Atom feed and applied the 180-day window: 2025-12-18 through 2026-06-16.
- Auro.live was not collected because the current Codex route lacks the required Chrome JS fetch + devalue parser path.
- All outputs are patch candidates only.
