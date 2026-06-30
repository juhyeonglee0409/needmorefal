# Next Public Cross-Check Plan

Date: 2026-06-12

Scenario: Scenario 3 - Charles/Arthur collection preparation.

Scope: planning only. This note does not run Softcon live collect, Arthur inspect, Arthur collect, create a CollectDirective, create a CollectionResult, or mutate CaseResult / DisclosureLog / PublicDemoRow / package canonical data.

## Current Softcon Status

- Charles profile diagnosis produced clean Softcon protocols for the operator-provided routes.
- Arthur headed/visible `chrome_profile` inspect reached clean rendered pages for the five Softcon routes: `response_status=200`, `checkpoint_detected=false`, `rsc_payload_detected=true`, and field maps present.
- The subject smoke collect was later approved and run once, but stopped at `chrome_profile_checkpoint_not_cleared` with zero items. Treat this as boundary evidence only.
- Arthur `chrome_profile` collect debug metadata hardening is complete. Future approved diagnostics can compare non-secret option and render metadata.
- Softcon live collect retry is deferred. Do not treat the clean inspect as collect success, and do not treat the failed smoke collect as final source failure.

## Public/Cross-Check Route Order

1. `chzzk_subject_channel_public_profile`
   - URL: `https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a`
   - Reason: narrowest subject-only public route. It directly supports subject identity, channel hash alignment, profile text, recent titles/categories, and any public follower signal.
   - Start mode: Charles unauthenticated scout.
   - Expected use: identity/profile support; not a replacement for Softcon current metric rows.

2. `semorank_chzzk_follower_public_crosscheck`
   - URL: `https://www.semorank.kr/ranking/chzzk`
   - Reason: TargetBatchPlan priority 2 public CHZZK follower ranking cross-check. It can corroborate or conflict with follower rank/count signals without using profile-gated Softcon.
   - Start mode: Charles unauthenticated scout.
   - Expected use: support-only public follower rank evidence; do not replace profile-gated scope if public range is limited.

3. `auro_live_chzzk_follower_public_crosscheck`
   - URL: `https://auro.live/rank/chzzk/0`
   - Reason: secondary public CHZZK rank source after Semorank. Useful if Semorank is blocked, too shallow, or lacks the subject/cohort rows.
   - Start mode: Charles unauthenticated scout.
   - Expected use: independent rank/count support, with public range and parsing limits preserved.

4. `youtube_dalsooisfree_content_funnel`
   - URL: `https://www.youtube.com/@dalsooisfree/videos`
   - Alternate URL: `https://www.youtube.com/channel/UCvkwM7BIrqqEq7I_9UiCY6w`
   - Reason: weak/contextual content funnel only. Use after the subject/profile and public follower-rank routes if still useful for context.
   - Start mode: Charles unauthenticated scout with high caution for consent/checkpoint/bot boundary.
   - Expected use: contextual content candidates only; no causal proof of CHZZK conversion.

## Routes Eligible For Charles Unauthenticated Scout

All four public/cross-check targets can start with Charles unauthenticated scout because `profile_required=false` in the TargetBatchPlan:

- `chzzk_subject_channel_public_profile`
- `semorank_chzzk_follower_public_crosscheck`
- `auro_live_chzzk_follower_public_crosscheck`
- `youtube_dalsooisfree_content_funnel`

If Charles returns clean protocol candidates, the next gate is protocol review against ResearchPlan intent before any Arthur inspect. Arthur inspect/collect remains separate and unapproved.

## Stop Gates

Stop and preserve boundary evidence if any scout returns:

- login/session/profile requirement;
- CAPTCHA, checkpoint, Vercel/security challenge, or HTTP 429;
- private/internal/account/security data surface;
- `best_path=manual_review` with restricted gate/risk;
- route too broad or irrelevant for the target intent;
- required fields absent from collection plan or visible payload;
- URL resolution cannot be narrowed to the approved public route;
- token/cookie/header value exposure risk;
- raw HTML/screenshot requirement for profile/session context.

For public ranking pages, a broad ranking is not automatically usable. It must expose enough fields to identify rows and match the subject or cohort: channel name, channel URL or stable ID/hash, follower count, follower rank, source URL, and collected timestamp/provenance.

## Softcon Boundary Handling

Softcon findings remain boundary evidence:

- Clean Charles/Arthur inspect proves reachable rendered RSC field surfaces under headed `chrome_profile`.
- Failed subject smoke collect proves the collect-time browser/session state can still hit checkpoint.
- Neither result promotes CaseResult, DisclosureLog, PublicDemoRow, package canonical state, or final absence classification.
- Do not rerun Softcon live collect until there is a new explicit operator approval and a fresh diagnostic rationale.

## Recommended Next Prompt

```text
Scenario 3으로 진행해줘.

Softcon live collect retry는 계속 보류하고, public/cross-check route에 대해 Charles unauthenticated scout만 실행한다.

Targets:
1. chzzk_subject_channel_public_profile
   https://m.chzzk.naver.com/dcbccbf2d8e2a1b095244c5856d3613a
2. semorank_chzzk_follower_public_crosscheck
   https://www.semorank.kr/ranking/chzzk
3. auro_live_chzzk_follower_public_crosscheck
   https://auro.live/rank/chzzk/0

Rules:
- Charles scout only.
- External website scout이므로 실행 전 require_escalated 승인 요청.
- Arthur inspect/collect 실행 금지.
- CollectDirective/CollectionResult 생성 금지.
- CaseResult, DisclosureLog, PublicDemoRow, package canonical data 변경 금지.
- full ScoutReport는 10_charles/에 저장하고 chat에는 요약만 출력.
- 기존 artifacts는 덮어쓰지 말고 suffix public_crosscheck_20260612 사용.
- CAPTCHA/checkpoint/429/login/profile/manual_review/restricted면 stop하고 boundary로 보존.

Output:
- target별 ScoutReport/protocol path
- best_path/gate_status/risk_level
- collection_plan/verification presence
- public route가 ResearchPlan intent에 맞는지 preliminary review
- Arthur inspect 가능 여부
- smallest next action
```

## Smallest Next Action

Run only the first public scout batch for `chzzk_subject_channel_public_profile`, `semorank_chzzk_follower_public_crosscheck`, and `auro_live_chzzk_follower_public_crosscheck` after explicit escalation approval for external websites. Defer YouTube until these three results show whether weak contextual evidence is still needed.
