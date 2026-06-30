# Arthur Chrome Profile Collect Policy / Patch Candidate

Date: 2026-06-12

Scope: design/review only. This note does not approve collection, does not create a CollectDirective, and does not mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.

## Scenario

Primary: Scenario 3 - Charles/Arthur collection preparation.

This note prepares a policy and patch candidate for possible Arthur `chrome_profile` collect support after Softcon visible-networkidle inspect succeeded. It is not a collection run plan approval.

## Inputs Reviewed

- `20_review/post_inspect_alignment_softcon_visible_networkidle_20260612.md`
- `20_review/intent_alignment_checklist.md`
- `00_inputs/research_plan.md`
- `00_inputs/target_batch_plan.draft.json`
- `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`
- `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `30_arthur_inspect/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`

## Current Evidence State

- Charles `chrome_profile` diagnosis produced clean Softcon protocols.
- Arthur headed/visible `chrome_profile` inspect reached clean rendered pages for all five priority Softcon routes.
- Subject visible-networkidle inspect: `response_status=200`, `checkpoint_detected=false`, `rsc_payload_detected=true`, `field_maps=3`, `sample_records=0`.
- Follower visible-networkidle inspect: `response_status=200`, `checkpoint_detected=false`, `rsc_payload_detected=true`, `field_maps=2`, `sample_records=0`.
- Headless Arthur `chrome_profile` inspect still stops at checkpoint, so collect must not silently fall back to headless.
- Post-inspect review kept collect approval as `no` for all routes. Draft eligibility is `later`, not approval.

## Policy Decision

Arthur `chrome_profile` collect may be designed only as an explicit, directive-gated, operator-approved path.

Default behavior must remain:

- `transport=chrome_profile` collect is blocked.
- Headed/visible Chrome is blocked unless the CollectDirective explicitly allows it.
- No collect may run from protocol alone.
- No collect may run from InspectResult alone.
- No collect may run with `approved=true` absent explicit operator approval.

Allowed design path, if implemented later:

- Input must be a CollectDirective wrapping a top-level Charles protocol.
- Directive must include `approved=false` until the operator approves the exact route, profile mode, output directory, and limits.
- Directive approval must be scoped to an allowlist of exact Softcon URLs.
- Any route outside the allowlist stops with `approved_scope_mismatch`.
- Headed/visible mode must require both `visible_window=true` and `visible_window_allowed=true`.
- `wait_until=networkidle` and `settle_wait_ms=1500` must be explicit or defaulted for this Softcon profile path.
- `--save-raw` must remain unavailable for `chrome_profile` collect.
- Screenshots must not be saved.
- Cookie/token/header values must not be printed, copied, or persisted.

## Required Runtime Guards

Arthur collect with `chrome_profile` must enforce:

- `approved=true` in a CollectDirective before execution.
- `transport=chrome_profile` allowed only when the directive has `allow_chrome_profile_collect=true`.
- `visible_window=true` allowed only when the directive has `visible_window_allowed=true`.
- `target_url` must exactly match an operator-approved Softcon allowlist entry.
- `max_routes=1` for first smoke collect.
- `max_pages=1` for RSC single-page payload collect.
- `max_items` set per route from the protocol verification block or a smaller operator cap.
- `max_runtime_seconds` hard cap.
- `max_requests` hard cap.
- Stop if rendered URL leaves `https://viewership.softc.one/`.
- Stop if rendered title/body indicates login, account, payment, security checkpoint, CAPTCHA, private dashboard, or unrelated page.
- Stop if `checkpoint_detected=true`, `captcha_detected=true`, `login_required_likely=true`, or `response_status` is 403/429 and no rendered RSC payload is extracted.
- Produce `arthur_collection_failed` or `undetermined` absences rather than filling missing fields.
- Preserve grey boundary signals instead of converting them into pass/fail judgment.

## Artifact Policy

Allowed:

- CollectionResult JSON.
- Structured `items`.
- Metadata/provenance: `source_url`, `fetched_at`, `protocol_hash`, `directive_hash`, `profile_summary`, `boundary_signals`, `policy_trace`, `visible_window_used=true`, rendered status summary.

Not allowed:

- raw HTML artifact.
- screenshot artifact.
- browser storage state artifact.
- cookies, tokens, Authorization values, session IDs, CSRF values, or full request headers.
- package canonical mutation.

## Patch Candidate Notes

Candidate implementation files:

- `arthur/cli.py`
  - Replace the absolute `collect + chrome_profile` CLI rejection with a directive-gated check.
  - Keep protocol-only `chrome_profile` collect blocked.
  - Require CollectDirective policy keys for `allow_chrome_profile_collect`, `visible_window_allowed`, route allowlist, and limits.

- `arthur/inspect.py`
  - Reuse or extract the current `_fetch_with_chrome_profile` logic for a collect renderer.
  - Keep `networkidle` and `settle_wait_ms` policy behavior aligned with inspect.
  - Return rendered diagnostics without raw artifact persistence.

- New candidate: `arthur/collect_chrome_profile.py`
  - Launch persistent Chrome context using approved profile config.
  - Navigate to a single allowlisted URL.
  - Evaluate rendered page safety signals.
  - Extract RSC payload arrays from `page.content()` in memory only.
  - Project rows through existing `CollectContext.add_rows`.
  - Close page/context in `finally`.

- `arthur/collect_rsc_payload.py`
  - Refactor RSC extraction so both HTTP fetch and rendered Chrome HTML can share row extraction/projecting logic.
  - Do not call `record_raw` for `chrome_profile` rendered HTML.

- `arthur/schemas.py` / `arthur/protocol_loader.py`
  - Preserve directive policy and hashes.
  - Add optional policy fields only if needed; avoid changing protocol semantics.

- Tests
  - synthetic directive-gated collect allowed/blocked tests.
  - visible-window guard test.
  - no raw/screenshot artifact test.
  - route allowlist mismatch stop test.
  - checkpoint page stop test.
  - RSC row extraction with sample validation test.
  - token/cookie value redaction test.

## Proposed CollectDirective Shape

This is a proposed shape only. No CollectDirective file was created.

```json
{
  "kind": "CollectDirective",
  "version": "draft",
  "approved": false,
  "case_id": "kimdalsu_20260601",
  "run_id": "recollect_20260611_prep",
  "target_id": "softcon_subject_channel_current_stats",
  "protocol_path": "10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json",
  "inspect_result_path": "30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json",
  "transport": "chrome_profile",
  "profile_config_path": "00_inputs/softcon_chrome_profile_fallback.non_default.visible_networkidle.local.json",
  "policy": {
    "allow_chrome_profile_collect": true,
    "visible_window": true,
    "visible_window_allowed": true,
    "wait_until": "networkidle",
    "settle_wait_ms": 1500,
    "save_raw": false,
    "save_screenshot": false,
    "store_secret_values": false,
    "approved_scope": {
      "allowed_urls": [
        "https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a"
      ],
      "max_routes": 1,
      "max_pages": 1,
      "max_requests": 3,
      "max_items": 222,
      "max_runtime_seconds": 60
    },
    "stop_on": [
      "checkpoint_detected",
      "captcha_detected",
      "login_required_likely",
      "unexpected_private_or_account_page",
      "off_allowlist_url",
      "rendered_no_rsc_payload"
    ]
  },
  "validation": {
    "require_row_count_check": true,
    "require_sample_check_count": 5,
    "require_value_samples": true,
    "on_missing_required_field": "record_absence_not_verifiable",
    "on_rank_or_hash_derivation_gap": "record_absence_not_verifiable"
  },
  "output_policy": {
    "items_only_plus_metadata": true,
    "preserve_source_url": true,
    "preserve_fetched_at": true,
    "preserve_protocol_hash": true,
    "preserve_directive_hash": true,
    "preserve_profile_summary": true,
    "preserve_boundary_signals": true,
    "record_visible_window_used": true,
    "do_not_mutate_case_package": true
  }
}
```

For follower ranking, the same shape would change:

- `target_id`: `softcon_chzzk_follower_ranking_naverchzzk`
- `protocol_path`: `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`
- `inspect_result_path`: `30_arthur_inspect/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `allowed_urls`: `https://viewership.softc.one/ranking/followers?type=naverchzzk`
- `max_items`: `100`
- validation must include rank/hash/url derivation checks.

## Route-Level Collect Readiness Proposal

| Route | Proposal | Why | Must Validate Before Collect |
|---|---|---|---|
| Subject current stats | Candidate for first smoke collect after patch, still approval blocked | Field maps exactly cover protocol metric fields; response clean; RSC detected | row/value samples, expected row count 222, source URL/fetched_at/protocol hash, identity hash from route, no raw artifacts |
| Follower ranking | Candidate for second smoke collect after subject, still approval blocked | Field maps include `followerCount`, `name`, `id`, `userId`, `slug`, and profile fields; response clean; RSC detected | row-order `follower_rank`, channel URL/hash derivation, subject row matching, expected row count 100, null ratios, not_verifiable handling for missing derived fields |

Not ready for collect approval:

- Neither route has a generated CollectDirective.
- Neither route has operator approval for `approved=true`.
- Arthur has no implemented directive-gated `chrome_profile` collect path yet.

## Blockers Before Collect

1. Implement and test directive-gated Arthur `chrome_profile` collect support.
2. Keep protocol-only `chrome_profile` collect blocked by default.
3. Add route allowlist enforcement for exact Softcon URLs.
4. Add visible/headed guard requiring explicit directive approval.
5. Add no raw/no screenshot enforcement in profile collect.
6. Add rendered-page safety checks for checkpoint, CAPTCHA, login, private/account/security page, and off-allowlist URL.
7. Add RSC row sample validation because InspectResult had `sample_records=0`.
8. Define follower `follower_rank` derivation from row order.
9. Define channel URL/hash derivation from `userId`, `id`, `slug`, or route conventions; if derivation cannot be verified, record `not_verifiable` or field absences.
10. Confirm subject current stats collect should be metric-only or explicitly combine route/title identity metadata with RSC metric rows.
11. Confirm output directory and file naming for future `40_arthur_collect/`.
12. Operator must approve exact first route and set the future directive to `approved=true`.

## Smallest Next Action

Patch Arthur with a synthetic, directive-gated `chrome_profile` collect candidate that is blocked by default and supports only an in-memory rendered RSC extraction path. Run mock tests only. Do not run live collect until the patch passes review and the operator explicitly approves a concrete CollectDirective.
