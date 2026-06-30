# Arthur Chrome Profile Collect Patch Review - 2026-06-12

Scope: Scenario 3 / tooling review only. This review does not approve collection, does not create a CollectDirective file, does not create a CollectionResult, and does not mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.

## Inputs Reviewed

- `20_review/arthur_chrome_profile_collect_policy_20260612.md`
- `20_review/post_inspect_alignment_softcon_visible_networkidle_20260612.md`
- Arthur patch candidate files:
  - `arthur/cli.py`
  - `arthur/protocol_loader.py`
  - `arthur/collect_rsc_payload.py`
  - `arthur/collect_chrome_profile.py`
  - `tests/test_chrome_profile_collect_v0_6.py`
- Subject protocol:
  - `10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`
- Follower protocol:
  - `10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json`
- Subject InspectResult:
  - `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- Follower InspectResult:
  - `30_arthur_inspect/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`

## Context Summary

- Subject protocol: `target_url=https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`, `best_path=rsc_payload`, `gate_status=profile_cleared`, `risk_level=medium`, `profile_required=true`, `verification.expected_row_count=222`.
- Subject InspectResult: `response_status=200`, `effective_status=response_200`, `checkpoint_detected=false`, `rsc_payload_detected=true`, `sample_records=0`, `field_maps=3`, `artifacts=0`, boundary `robots_check`, `session_profile.secret_values_logged=false`.
- Follower protocol: `target_url=https://viewership.softc.one/ranking/followers?type=naverchzzk`, `best_path=rsc_payload`, `gate_status=profile_cleared`, `risk_level=medium`, `profile_required=true`, `verification.expected_row_count=100`.
- Follower InspectResult: `response_status=200`, `effective_status=response_200`, `checkpoint_detected=false`, `rsc_payload_detected=true`, `sample_records=0`, `field_maps=2`, `artifacts=0`, boundary `robots_check`, `session_profile.secret_values_logged=false`.
- Post-inspect review kept collect approval as `no` for every route. Subject and follower ranking were marked `later`, not approved.

## Patch Review Verdict

Overall recommendation: patch candidate is acceptable as a synthetic/mock candidate and is directionally aligned with the policy. It is not sufficient for live Softcon collect approval yet.

Go/no-go:

- Create a future `approved=false` CollectDirective draft: conditional GO, as a review artifact only, after the shape is adjusted to match the current loader requirement for embedded `source_protocol`.
- Set `approved=true`: NO-GO.
- Run Softcon live collect: NO-GO.

## Guard Checklist

| Review point | Verdict | Evidence / note |
|---|---|---|
| `chrome_profile` collect blocked by default | PASS | `arthur/cli.py` runs `_chrome_profile_collect_preflight` for `effective_transport=chrome_profile`; protocol-only input stops with `chrome_profile_collect_requires_directive`. |
| Requires CollectDirective | PASS | `arthur/collect_chrome_profile.py` stops when `prescription.directive is None`; test covers no-directive block. |
| Requires `approved=true` | PASS | `protocol_loader.py` derives `policy.approved` only from top-level directive `approved`; CLI and collect path stop if not true. Test covers `approved=false`. |
| Requires `allow_chrome_profile_collect=true` | PASS with test gap | Code checks `allow_chrome_profile_collect`; current test helper supports the false case but no explicit false-case test is present. Add one before live approval. |
| URL allowlist exact/domain/path checks | PARTIAL | `allowed_urls`, `allowed_domains`, and `path_prefixes` are supported. However `chrome_profile` collect can proceed with only domain/path scope if `allowed_urls` is absent. For Softcon live collect, exact `allowed_urls` should be mandatory. |
| Visible/headed guard | PARTIAL | The browser launch is blocked when `chrome_profile_options.visible_window_requested=true` and `visible_window_allowed=false`. The current code does not independently require `policy.visible_window_allowed=true` from the CollectDirective; it relies on the profile config options. |
| Raw HTML saving | PASS | `collect_chrome_profile` suppresses `ctx.save_raw` and calls RSC extraction with `record_raw=false`. Test covers `save_raw=True` suppression. |
| Screenshot saving | PASS | No screenshot save path exists in the collect patch; test asserts no artifacts. |
| Token/cookie values excluded | PASS with caution | `_load_profile` keeps chrome_profile headers/cookies out of HTTP memory and stores summary names only. The collect path does not read cookies/tokens. Caution: rendered URL/title are recorded in notes/boundaries; sanitize query values before live use. |
| Output is item rows plus metadata/provenance | PASS | The collector projects rows through existing `CollectContext.add_rows`; output remains CollectionResult items, field coverage, notes, boundaries, policy trace, artifacts list, session profile. |
| `source_url` and `fetched_at` preserved | PASS | `CollectContext.add_rows` sets both per item. Test checks `source_url`. |
| `protocol_hash` and `directive_hash` preserved | PASS | `protocol_loader` computes both for CollectDirective; `result_builder` exposes `operator_directive_hash`. Test checks both. |
| `profile_summary` preserved | PASS | `session_profile` is carried to result. Test checks summary names and absence of secret values. |
| `boundary_signals` preserved | PASS | Stops and grey 403/429 response boundaries are recorded through `ctx.record_boundary`. |
| `visible_window_used` preserved | PARTIAL | Present as `policy_trace` string (`chrome_profile_collect:visible_window_used=true/false`), not as a structured top-level field. Add structured metadata before live collect. |
| Checkpoint/private/account/security stop | PARTIAL | Checkpoint stop is implemented and tested. Private/account/security detection is title/URL-oriented plus checkpoint text; add body-text cases for login/CAPTCHA/account pages before live approval. |
| Missing/derived fields as absence/not_verifiable | PARTIAL | Direct missing projected fields become per-item `target_absent`; RSC absence becomes `undetermined`. Derived field policies such as follower rank/channel hash are not enforced yet. |
| Tests cover requested guards | PARTIAL | Tests cover no directive, `approved=false`, visible config guard, raw suppression, secret suppression, allowlist reject, synthetic RSC item/provenance, checkpoint stop. Missing tests: `allow_chrome_profile_collect=false`, directive-policy visible mismatch, rendered URL off-allowlist, non-checkpoint login/CAPTCHA/account body, validation/output policy enforcement. |

## Important Shape Mismatch

The policy note's proposed shape is path-oriented (`protocol_path`, `inspect_result_path`). The current Arthur loader requires:

```json
{
  "kind": "CollectDirective",
  "source_protocol": {}
}
```

`source_protocol` must be the embedded top-level Charles protocol object. A directive containing only `protocol_path` will not load today. A future draft may keep `source_protocol_path` for lineage, but it must either embed `source_protocol` or Arthur must be patched to load and hash `protocol_path` explicitly.

## Proposed Subject CollectDirective Shape

Text-only shape. No file was created.

```json
{
  "kind": "CollectDirective",
  "version": "draft",
  "approved": false,
  "case_id": "kimdalsu_20260601",
  "run_id": "recollect_20260611_prep",
  "target_id": "softcon_subject_channel_current_stats",
  "source_protocol_path": "10_charles/softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json",
  "source_protocol": {
    "_shape_note": "Embed the full top-level protocol JSON object here. Do not embed the full ScoutReport."
  },
  "inspect_result_path": "30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json",
  "approved_best_path": "rsc_payload",
  "transport": "chrome_profile",
  "profile_config_path": "00_inputs/softcon_chrome_profile_fallback.non_default.visible_networkidle.local.json",
  "approved_scope": {
    "allowed_urls": [
      "https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a"
    ],
    "allowed_domains": ["viewership.softc.one"],
    "path_prefixes": ["/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a"],
    "max_routes": 1,
    "max_pages": 1,
    "max_requests": 3,
    "max_items": 222,
    "max_runtime_seconds": 60
  },
  "policy": {
    "allow_chrome_profile_collect": true,
    "require_exact_allowed_url": true,
    "visible_window": true,
    "visible_window_allowed": true,
    "wait_until": "networkidle",
    "settle_wait_ms": 1500,
    "save_raw": false,
    "save_screenshot": false,
    "store_secret_values": false,
    "sanitize_rendered_url_query": true,
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
    "required_row_count": 222,
    "require_value_sample_count": 5,
    "required_fields": [
      "airTime",
      "avgChatCount",
      "avgLiveViews",
      "date",
      "maxAccumulateViews",
      "maxChatCount",
      "maxFollowerCount",
      "maxLiveViews",
      "maxSubscribers",
      "minAccumulateViews",
      "sumChatCount",
      "sumCount",
      "sumLiveViews",
      "viewership"
    ],
    "numeric_fields_must_be_non_negative": true,
    "date_field_must_parse": true,
    "on_missing_required_field": "record_absence_not_verifiable"
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

## Proposed Follower Ranking CollectDirective Shape

Text-only shape. No file was created.

```json
{
  "kind": "CollectDirective",
  "version": "draft",
  "approved": false,
  "case_id": "kimdalsu_20260601",
  "run_id": "recollect_20260611_prep",
  "target_id": "softcon_chzzk_follower_ranking_naverchzzk",
  "source_protocol_path": "10_charles/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_non_default_20260611.protocol.json",
  "source_protocol": {
    "_shape_note": "Embed the full top-level protocol JSON object here. Do not embed the full ScoutReport."
  },
  "inspect_result_path": "30_arthur_inspect/softcon_chzzk_follower_ranking_naverchzzk.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json",
  "approved_best_path": "rsc_payload",
  "transport": "chrome_profile",
  "profile_config_path": "00_inputs/softcon_chrome_profile_fallback.non_default.visible_networkidle.local.json",
  "approved_scope": {
    "allowed_urls": [
      "https://viewership.softc.one/ranking/followers?type=naverchzzk"
    ],
    "allowed_domains": ["viewership.softc.one"],
    "path_prefixes": ["/ranking/followers"],
    "max_routes": 1,
    "max_pages": 1,
    "max_requests": 3,
    "max_items": 100,
    "max_runtime_seconds": 60
  },
  "policy": {
    "allow_chrome_profile_collect": true,
    "require_exact_allowed_url": true,
    "visible_window": true,
    "visible_window_allowed": true,
    "wait_until": "networkidle",
    "settle_wait_ms": 1500,
    "save_raw": false,
    "save_screenshot": false,
    "store_secret_values": false,
    "sanitize_rendered_url_query": true,
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
    "required_row_count": 100,
    "require_value_sample_count": 5,
    "required_fields": [
      "createdAt",
      "followerCount",
      "id",
      "language",
      "name",
      "type",
      "userId"
    ],
    "derive_follower_rank": "one_based_row_order_after_verifying_followerCount_non_increasing",
    "derive_channel_hash": "userId_prefix_before_comma_when_type_is_naverchzzk",
    "derive_channel_url": "not_verifiable_unless derivation rule is separately approved",
    "subject_match": {
      "channel_hash": "dcbccbf2d8e2a1b095244c5856d3613a",
      "on_not_found": "record_absence_not_verifiable"
    },
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

## Route Allowlist Recommendation

Use exact `allowed_urls` as the authorization boundary for first live smoke attempts. Treat `allowed_domains` and `path_prefixes` as secondary checks only, not as sufficient authorization.

Recommended first-route allowlists:

- Subject current stats:
  - exact URL: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
  - domain: `viewership.softc.one`
  - path prefix: `/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- Follower ranking:
  - exact URL: `https://viewership.softc.one/ranking/followers?type=naverchzzk`
  - domain: `viewership.softc.one`
  - path prefix: `/ranking/followers`

Before live collect, update code or directive validation so `allowed_urls` is mandatory for `transport=chrome_profile`.

## Row / Value Validation Requirements

Subject smoke:

- Confirm row count against protocol `verification.expected_row_count=222`, unless operator intentionally caps `max_items` for a partial smoke. If capped, verification must be `not_verifiable`, not pass.
- Validate at least 5 sampled rows across beginning/middle/end of the selected RSC payload.
- Required fields must be present or recorded as absence/not_verifiable.
- Numeric metric fields must parse as numbers and be non-negative.
- `date` must parse consistently.
- Preserve route identity through target URL hash and source URL. Do not infer final identity readiness from metric rows alone.

Follower ranking smoke:

- Confirm row count against protocol `verification.expected_row_count=100`, unless operator intentionally caps `max_items`.
- Validate at least 5 sampled rows across beginning/middle/end.
- `followerCount` must be numeric and non-increasing if row order is used to derive `follower_rank`.
- `type` must be `naverchzzk` for rows used in CHZZK follower ranking.
- `channel_hash` derivation from `userId` must be explicitly defined and sample-validated.
- `channel_url` derivation is not yet proven by the field map; record `not_verifiable` unless a derivation rule is separately approved.
- Subject matching by hash/name must be verified or recorded as `not_verifiable`.

## Remaining Blockers

1. No operator approval exists for `approved=true`.
2. No real CollectDirective file should be created in this review step.
3. Current loader requires embedded `source_protocol`; the path-only directive shape is not executable.
4. Visible/headed approval is currently enforced through profile config options, not strictly through directive policy.
5. Exact `allowed_urls` is supported but not mandatory when domain/path scope is present.
6. `visible_window_used` is recorded in `policy_trace`, not a structured result field.
7. Rendered URL/title are recorded; query sanitization should be added before live use.
8. Private/account/security detection should include body text and structured CAPTCHA/login signals, not only checkpoint/title/URL.
9. Validation and output_policy blocks are proposed shape only; current collect path does not enforce row/value sample checks or derived field policy.
10. Follower `follower_rank`, `channel_hash`, and `channel_url` derivations remain unapproved.
11. InspectResults have `sample_records=0`; field availability is established, but value-level validation still depends on collect-time checks.
12. No package canonical mutation path is allowed from this patch candidate.

## Go / No-Go Recommendation

- GO: create a future `approved=false` draft CollectDirective as a review artifact only, with embedded `source_protocol` or after adding explicit `protocol_path` loader support.
- NO-GO: set `approved=true`.
- NO-GO: run Softcon live collect.
- NO-GO: treat subject or follower results as package-ready until row/value validation and intent alignment after collect are reviewed.

## Smallest Next Action

Patch the remaining tooling gaps before any live approval path:

1. Require exact `approved_scope.allowed_urls` for `transport=chrome_profile`.
2. Require directive policy `visible_window_allowed=true` when headed mode is requested, independent of profile config.
3. Add structured `visible_window_used` and sanitized rendered URL metadata.
4. Add tests for `allow_chrome_profile_collect=false`, directive-visible mismatch, rendered off-allowlist URL, non-checkpoint login/CAPTCHA/account pages, and row/value validation policy.
