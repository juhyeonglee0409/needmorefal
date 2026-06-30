# Public Cross-Check Preliminary Alignment

Date: 2026-06-12

Scenario: Scenario 3 - Charles/Arthur collection preparation.

Scope: Charles unauthenticated scout review only. This note does not run Arthur inspect, Arthur collect, create CollectDirective, create CollectionResult, or mutate CaseResult / DisclosureLog / PublicDemoRow / package canonical data.

## Execution Summary

| Target | Execution | ScoutReport | Protocol |
|---|---|---|---|
| `chzzk_subject_channel_public_profile` | executed | `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.scout_report.json` | `10_charles/chzzk_subject_channel_public_profile.public_crosscheck_20260612.protocol.json` |
| `semorank_chzzk_follower_public_crosscheck` | not executed | n/a | n/a |
| `auro_live_chzzk_follower_public_crosscheck` | not executed | n/a | n/a |

Semorank execution was requested with `require_escalated`, but the approval review rejected it because the usage limit was reached. Aurolive was not attempted after that rejection. This is an execution-environment blocker, not a source boundary signal.

## Target Results

### chzzk_subject_channel_public_profile

- Target URL: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
- ScoutReport SHA256: `C92ED22B1E52185E4BBDAD10C46816E81DFB9365850E4C1AB429DAF1BB73C3E7`
- Protocol SHA256: `02C9240A65AE2649950969B6D64276C5C6A089FBBC0DA6008012332231AE9BF1`
- `best_path`: `playwright`
- `pre_check.gate_status`: `none`
- `pre_check.risk_level`: `low`
- `profile_required`: `false`
- `collection_plan`: present
- `verification`: present
- Checkpoint / login / CAPTCHA / HTTP 429 / restricted / manual_review: not observed in the protocol summary.

Collection plan summary:

- Source: `rendered_dom`
- Fields: `thumbnail`, `time`, `title`, `video_card_item__lOC8Y`, `blind`, `category`
- Selector basis includes CHZZK VOD/card selectors such as `div.channel_home_vod_item__N7KA5`.
- Verification uses `dedup_key=title`, `sample_check_count=5`, and no fixed expected row count.

Preliminary intent alignment:

- Verdict: `partial`.
- The source route matches the intended subject channel hash and is public/unauthenticated.
- The scout result is useful for recent VOD/title/category signals.
- The extracted protocol does not yet cover the full TargetBatchPlan subject profile intent: `channel_name`, `channel_url`, `profile_text`, `follower_count`, and stable `platform_channel_id` are not direct collection-plan fields.
- This protocol is technically clean enough to consider a later Arthur inspect, but Arthur inspect should be treated as exploratory field-surface validation, not as collect approval.

### semorank_chzzk_follower_public_crosscheck

- Target URL: `https://www.semorank.kr/ranking/chzzk`
- Execution: not executed.
- Blocker: external-site escalation was rejected by the approval review due usage limit.
- Source boundary: not evaluated.
- Preliminary alignment: unknown until Charles scout runs.

### auro_live_chzzk_follower_public_crosscheck

- Target URL: `https://auro.live/rank/chzzk/0`
- Execution: not executed.
- Blocker: not attempted after the Semorank escalation rejection.
- Source boundary: not evaluated.
- Preliminary alignment: unknown until Charles scout runs.

## Arthur Inspect Eligibility

| Target | Arthur inspect eligibility | Reason |
|---|---|---|
| `chzzk_subject_channel_public_profile` | `possible_later_with_caution` | Clean unauthenticated protocol exists, but field coverage is partial for ResearchPlan subject profile intent. |
| `semorank_chzzk_follower_public_crosscheck` | `unknown` | No ScoutReport/protocol yet. |
| `auro_live_chzzk_follower_public_crosscheck` | `unknown` | No ScoutReport/protocol yet. |

No Arthur inspect was run in this step.

## Boundary Handling

- Softcon findings remain separate boundary evidence and are not mixed with these public cross-check routes.
- The CHZZK public route does not resolve the Softcon collect checkpoint.
- Semorank/Aurolive remain pending due environment approval/usage limit, not due observed site behavior.

## Smallest Next Action

After the external execution limit is available again, run only the remaining two Charles unauthenticated scouts:

1. `semorank_chzzk_follower_public_crosscheck`
2. `auro_live_chzzk_follower_public_crosscheck`

If both return clean protocols, update this review and then decide whether any public protocol should proceed to Arthur inspect. Do not run Arthur inspect, Arthur collect, or create a CollectDirective without a separate instruction.
