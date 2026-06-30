# Softcon Subject CollectDirective Draft Review - 2026-06-12

Scope: Scenario 3 / directive draft. This is a review artifact only. Arthur collect was not run, no CollectionResult was created, and no CaseResult, DisclosureLog, PublicDemoRow, or package canonical data was changed.

## Output

- Draft directive:
  - `40_arthur_collect/directives/softcon_subject_smoke_collect_directive.draft_approved_false_20260612.json`

## Inputs

- Policy:
  - `20_review/arthur_chrome_profile_collect_policy_20260612.md`
  - `20_review/arthur_chrome_profile_collect_patch_review_20260612.md`
  - `20_review/post_inspect_alignment_softcon_visible_networkidle_20260612.md`
- Protocol:
  - `10_charles/softcon_subject_channel_current_stats.charles_profile_ab_smoke_20260612.protocol.json`
- InspectResult:
  - `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- Profile config reference:
  - `00_inputs/softcon_chrome_profile_fallback.non_default.visible_networkidle.local.json`

## Draft Summary

- `status=draft`
- `approved=false`
- Target: `softcon_subject_channel_current_stats`
- Target URL: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- Collect mode: `chrome_profile`, headed/visible, `wait_until=networkidle`, `settle_wait_ms=1500`
- Exact `allowed_urls`: subject URL only
- Smoke cap: `max_items=10`
- Runtime cap: `max_runtime_seconds=60`
- Request cap: `max_requests=3`
- Raw HTML: disabled
- Screenshot: disabled
- Token/cookie value storage: disabled
- Output path proposal only:
  - `40_arthur_collect/results/softcon_subject_smoke_collect_20260612.CollectionResult.json`

## Embedded Protocol

The draft embeds `source_protocol` because current Arthur `CollectDirective` loading requires a source protocol object, not only a path.

- `source_protocol_path`: `10_charles/softcon_subject_channel_current_stats.charles_profile_ab_smoke_20260612.protocol.json`
- `source_protocol_hash`: `37daf61a0b92c644738bcf5a1bab7b178e1dc333f70958e314ea5281438a0cdc`
- `protocol_hash`: `37daf61a0b92c644738bcf5a1bab7b178e1dc333f70958e314ea5281438a0cdc`

Validation note: Arthur `load_protocol()` parsed the file as `input_shape=collect_directive`, kept `transport=chrome_profile`, `best_path=rsc_payload`, `approved=false`, exact `allowed_urls`, and a computed directive hash.

## Policy Checks

| Check | Status | Note |
|---|---|---|
| `approved=false` | PASS | Draft cannot authorize collect. |
| `allow_chrome_profile_collect=true` | PASS | Present for future operator-approved execution path. |
| `allow_visible_window=true` | PASS | Present, matching hardening requirement. |
| `visible_window_allowed=true` | PASS | Present, matching hardening requirement. |
| `wait_until=networkidle` | PASS | Present. |
| `settle_wait_ms=1500` | PASS | Present. |
| Exact `allowed_urls` only | PASS | Only the subject URL is allowlisted. |
| Domain/path scope supplemental | PASS | Domain and path prefix are included but not sufficient without exact URL. |
| Raw HTML disabled | PASS | `save_raw=false`, raw artifact allowed=false. |
| Screenshot disabled | PASS | `save_screenshot=false`, screenshot artifact allowed=false. |
| Secret storage disabled | PASS | `store_secret_values=false`, secret value storage allowed=false. |
| Embedded `source_protocol` | PASS | Included for current Arthur loader compatibility. |
| CollectionResult creation | PASS | Not created. |

## Smoke Validation Plan

The AB smoke protocol has `verification.expected_row_count=223`. This draft intentionally sets `max_items=10` as a small smoke limit.

Implication:

- A future collect with this directive must not be treated as full-count verification.
- `expected_row_count=223` remains provenance and full-run context.
- The capped smoke should validate row shape, field coverage, sample values, source URL, protocol hash, directive hash, session profile summary, and boundary signals.
- If verification compares actual row count against 223 under `max_items=10`, the expected outcome is not full pass.

Required smoke checks:

- At least 5 sampled rows from collected output.
- Required fields from the protocol are present or recorded as absence/not_verifiable.
- Numeric metric fields parse and are non-negative.
- `date` parses consistently.
- `source_url`, `fetched_at`, `protocol_hash`, and directive hash are preserved.
- `visible_window_used=true` is recorded structurally.
- Raw HTML and screenshots remain absent.

## Approval Boundary

This draft does not approve collect.

Current approval state:

- `operator_collect_approval=no`
- `approved=false`
- `approved=true` must not be set without explicit operator approval for this exact route, profile mode, output path, and limits.

## Remaining Blockers

1. Operator has not approved `approved=true`.
2. Arthur collect has not been run.
3. No CollectionResult exists.
4. A smoke collect, if later approved, still requires post-collect intent alignment before any package or CaseResult use.
5. This is subject-only; it does not authorize follower ranking, category, ranking/streamer, or ranking/softcone routes.

## Smallest Next Action

Operator review of the `approved=false` draft. If accepted, the next separate step would be an explicit operator decision on whether to set `approved=true` for this exact subject smoke directive and then run one bounded Arthur collect. Until that approval exists, collect remains blocked.
