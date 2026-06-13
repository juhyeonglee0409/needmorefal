# Arthur Collect Vs Inspect Transport Diff - Subject Route

Date: 2026-06-12

Scenario: Scenario 3 / tooling debug review only.

Boundary: no live collect rerun, no new approved directive, no CaseResult / DisclosureLog / PublicDemoRow / package canonical mutation.

## Inputs Reviewed

- `30_arthur_inspect/softcon_subject_channel_current_stats.chrome_profile_visible_networkidle_inspect_20260612.InspectResult.json`
- `40_arthur_collect/results/softcon_subject_smoke_collect_20260612.CollectionResult.json`
- `40_arthur_collect/directives/softcon_subject_smoke_collect_directive.approved_true_20260612.json`
- `40_arthur_collect/directives/softcon_subject_smoke_collect_directive.draft_approved_false_20260612.json`
- `D:/Codex_Workspace/IsaacInfra/Arthur/current/Arthur_v0.6_pipeline_contract/arthur/inspect.py`
- `D:/Codex_Workspace/IsaacInfra/Arthur/current/Arthur_v0.6_pipeline_contract/arthur/collect_chrome_profile.py`
- `D:/Codex_Workspace/IsaacInfra/Arthur/current/Arthur_v0.6_pipeline_contract/arthur/collect_rsc_payload.py`
- `D:/Codex_Workspace/IsaacInfra/Arthur/current/Arthur_v0.6_pipeline_contract/arthur/cli.py`
- `D:/Codex_Workspace/IsaacInfra/Arthur/current/Arthur_v0.6_pipeline_contract/arthur/protocol_loader.py`

## Short Finding

The failed collect is not explained by an obvious URL mismatch, headless/visible mismatch, wait timing mismatch, or a separate collect-only Playwright launch implementation. Inspect and collect both render the same subject URL through the same `_fetch_with_chrome_profile()` helper, using the same visible profile config shape.

The observable difference is runtime outcome:

| Check | Visible-networkidle inspect | Approved smoke collect |
|---|---:|---:|
| target URL | subject URL | subject URL |
| rendered URL | subject URL | subject URL |
| profile config | `chrome_profile`, visible, `networkidle`, `1500ms` | same |
| response status | `200` | `429` |
| effective status | `response_200` | `checkpoint_not_cleared` |
| rendered title | subject page title | `Vercel Security Checkpoint` |
| checkpoint detected | `false` | `true` |
| RSC payload detected | `true` | `false` |

This points to a session/profile/runtime boundary condition, or a site-side challenge state at the time of collect, rather than a clear collect code path divergence.

## Requested URL Comparison

Inspect result:

- `target_url`: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- HTTP resource URL: same
- rendered URL: same

Collect result:

- `target_url`: same
- `protocol_ref.target_url`: same
- rendered URL: same

Directive:

- top-level directive has no separate `target_url`
- embedded `source_protocol.target_url`: same
- embedded `source_protocol.connection_test.url`: same
- `approved_scope.allowed_urls`: same single exact URL

Conclusion: no target URL mismatch found.

## Timing And Visible Flags

Profile config used by the successful inspect and the collect directive path:

- `transport=chrome_profile`
- `profile_directory=Default`
- `visible_window=true`
- `visible_window_allowed=true`
- `wait_until=networkidle`
- `settle_wait_ms=1500`
- `headers={}`
- `cookies={}`

Directive policy also carries:

- `allow_chrome_profile_collect=true`
- `allow_visible_window=true`
- `visible_window_allowed=true`
- `wait_until=networkidle`
- `settle_wait_ms=1500`

Conclusion: no visible/headed or wait timing mismatch found in the reviewed artifacts.

## Launch Path Comparison

Both inspect and collect use the same Playwright helper:

- `collect_chrome_profile.py` imports `_fetch_with_chrome_profile` from `inspect.py`.
- `_fetch_with_chrome_profile()` calls `pw.chromium.launch_persistent_context(...)`.
- Launch options are:
  - `user_data_dir`
  - `executable_path`
  - `headless = not visible_window_requested`
  - `args=["--profile-directory=Default"]` when profile directory is set
  - `page.goto(target, wait_until=wait_until, timeout=PLAYWRIGHT_TIMEOUT_MS)`
  - `page.wait_for_timeout(settle_wait_ms)`

Conclusion: no separate collect-only persistent-context launch implementation was found.

## Checkpoint And Status Handling

Shared diagnostics:

- `_chrome_profile_render_diagnostics()` marks `checkpoint_not_cleared` when response is `403/429` and checkpoint text/title is visible.
- It marks `rendered_rsc_payload_after_response_boundary` when response is `403/429` but RSC payload is visible.

Inspect handling:

- If `transport=chrome_profile`, `response.status in {403, 429}`, and checkpoint is detected, inspect stops with `chrome_profile_checkpoint_not_cleared`.
- If `response.status in {403, 429}` but RSC payload is detected and checkpoint is absent, inspect proceeds while preserving a grey boundary.

Collect handling:

- If checkpoint is detected, collect stops with `chrome_profile_checkpoint_not_cleared`.
- If `response.status in {403, 429}` and RSC payload is detected, collect records a grey boundary and passes `status_for_rows=200` to RSC extraction.
- If `response.status >= 400` without rendered RSC payload, collect stops.

Conclusion: collect does not appear stricter than inspect for the relevant successful case. Both should proceed on `429 + rendered RSC + no checkpoint`, and both stop on visible checkpoint.

## Embedded Protocol Vs Directive Target

`protocol_loader._from_collect_directive()` loads `directive.source_protocol` first and then overlays directive policy/scope:

- `prescription = load_protocol(source_protocol)`
- `approved_best_path` may override path
- `approved_scope` is copied into `prescription.policy`
- final `approved` is derived from top-level directive approval

Collect target is therefore derived from the embedded source protocol:

- `prescription.connection_url or prescription.target_url`

The approved directive does not define an independent top-level `target_url`. In this draft that is not a practical mismatch because source protocol target, source connection URL, and approved scope URL are identical.

Review note: successful inspect used `softcon_subject_channel_current_stats.chrome_profile_non_default_20260611.protocol.json`, while the collect directive embeds `softcon_subject_channel_current_stats.charles_profile_ab_smoke_20260612.protocol.json`. These protocols have the same subject URL and transport, but different generation time and expected row count (`222` vs `223`). This does not explain the checkpoint, but future debug retries should prefer protocol lineage alignment with the exact InspectResult used for approval.

## Preflight Or Extra Requests Before Render

No collect-only target/API request was found before page render.

What happens before collect render:

- local approved-scope check
- local chrome profile collect policy check
- profile/session status checks
- live robots check via `check_robots(fetcher, prescription.target_url, fetcher.ua)`
- `Fetcher.check_budget(target)`
- then `_fetch_with_chrome_profile(target, chrome_profile_options)`

Inspect also performs the live robots check before Chrome render. In both results the robots boundary is `robots 429`, recorded and proceeded.

`requests_made=1` in CollectionResult is consistent with the HTTP fetcher robots request. The Playwright render call is not counted by `Fetcher.requests_made`.

Conclusion: robots precheck is not unique to collect. No extra collect-only API/sitemap/target fetch was found before render.

## Debug Metadata Sufficiency

Current CollectionResult records enough to identify the stop:

- rendered URL
- rendered title
- response status
- effective status
- rendered HTML length
- checkpoint detected
- RSC payload detected
- visible window used
- raw/screenshot suppression flags
- session profile summary

Gaps that make transport comparison harder:

- no explicit `wait_until` / `settle_wait_ms` recorded in `execution_metadata`
- no `profile_path`, `profile_directory`, or redacted `user_data_dir` identity recorded
- no launch args / `headless` value recorded
- no clear split of `requests_made` into `robots_requests` vs `browser_render_requests`
- no `rendered_response_url` separate from `page.url` and requested target
- no direct link to the InspectResult used as the approval basis beyond directive metadata

## Likely Cause Assessment

Most likely:

- The site/profile state changed between the successful inspect and the later collect, causing visible Chrome to receive the Vercel checkpoint during collect.

Plausible contributing factors:

- Persistent Chrome profile state was updated during prior visible launches.
- Softcon/Vercel challenge state may vary by time, browser process, profile state, or repeated origin access.
- The approved directive embedded a newer Charles protocol than the protocol named in the successful inspect session note, though the URL and render settings matched.

Not supported by the reviewed evidence:

- wrong subject URL
- headless collect when inspect was visible
- missing `networkidle` / `1500ms` settle in the profile config
- separate collect-only Playwright implementation
- collect-only pre-render target/API request
- collect treating `429 + rendered RSC + no checkpoint` as stop while inspect would proceed

## Smallest Patch Recommendation

Patch recommendation: diagnostic alignment first, behavior change second.

1. Add `chrome_profile_options_used` to collect `execution_metadata`, with non-secret values only:
   - `visible_window_requested`
   - `visible_window_allowed`
   - `headless`
   - `wait_until`
   - `settle_wait_ms`
   - `profile_directory`
   - redacted/stable path identity for `profile_path` and `user_data_dir`
2. Add request counters:
   - `robots_requests_made`
   - `browser_render_attempted`
   - `browser_render_counted=false` or equivalent note
3. Add protocol lineage fields to CollectionResult metadata:
   - directive path/hash
   - embedded source protocol path/hash if present in directive
   - inspect_result_path used as approval basis if present in directive
4. Add a narrow unit test proving inspect and collect use the same `_fetch_with_chrome_profile()` options for `chrome_profile` visible-networkidle mode.
5. Optional behavior patch after diagnostics: add directive policy `skip_live_robots_when_recent_clean_inspect_ref_present=false` defaulting to false. This should not be enabled without a separate policy review because robots checking is part of Arthur's normal collect boundary.

No immediate behavior patch is recommended solely from this review, because the shared render helper already aligns collect with the successful inspect path.

## Live Retry Recommendation

Another live collect retry is not justified as data collection.

A single future retry may be justified only as a bounded transport reproducibility test if all preconditions below are met:

- New explicit operator approval for one subject-route-only retry.
- No follower, LoL, ranking, or broader collect.
- Use the same exact URL allowlist: `https://viewership.softc.one/channel/naverchzzk/dcbccbf2d8e2a1b095244c5856d3613a`
- `max_items=10`, `max_requests=3`, `max_runtime_seconds=60`.
- `chrome_profile`, visible/headed, `wait_until=networkidle`, `settle_wait_ms=1500`.
- No raw HTML, no screenshots, no token/cookie value storage.
- Diagnostic metadata patch above is applied first, or the retry is paired with an explicit no-mutation debug harness that records equivalent non-secret launch/options metadata.
- A fresh subject-only visible-networkidle Arthur inspect immediately before retry reaches:
  - `response_status=200`
  - `effective_status=response_200`
  - `checkpoint_detected=false`
  - `rsc_payload_detected=true`
- The retry uses protocol lineage aligned to that fresh InspectResult, preferably the same top-level protocol file or a directive embedding that exact protocol content.

If these preconditions are not met, the next action should remain code-level diagnostic patching and profile/session state review, not another live collect.

## Non-Mutation Check

This review created only this review note. It did not run live collect, did not create a new approved directive, and did not mutate CaseResult, DisclosureLog, PublicDemoRow, or package canonical data.
