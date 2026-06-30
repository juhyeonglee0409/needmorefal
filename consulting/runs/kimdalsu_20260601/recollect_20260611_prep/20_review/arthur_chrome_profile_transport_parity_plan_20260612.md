# Arthur Chrome Profile Transport Parity Plan

Date: 2026-06-12

Scenario: Scenario 3 - tooling design for Charles/Arthur collection preparation.

Scope: synthetic/no-network tooling design only. This note does not launch Chrome, make live requests, run Arthur collect, create CollectDirective, create CollectionResult, or mutate CaseResult / DisclosureLog / PublicDemoRow / package canonical data.

## Current Option Shape

Arthur inspect and collect both use the same profile loader shape from `arthur/cli.py`:

| Field | Inspect Path | Collect Path | Parity Note |
|---|---|---|---|
| `chrome_executable` | `_load_chrome_profile_options()` -> `inspect_target()` -> `_fetch_with_chrome_profile()` | `_load_chrome_profile_options()` -> `collect()` -> `collect_chrome_profile_rsc_payload()` -> `_fetch_with_chrome_profile()` | Same option key. |
| `user_data_dir` | same | same | Same option key. |
| `profile_directory` | passed to shared fetch helper and converted to `--profile-directory=...` | same | Same launch helper. |
| `visible_window_requested` | inspected by `_chrome_profile_stop_signal()` and shared fetch helper | checked by `_chrome_profile_collect_preflight()`, collect metadata, and shared fetch helper | Collect adds directive approval gates. |
| `visible_window_allowed` | profile option gate only | profile option gate plus directive policy gates | Collect is intentionally stricter. |
| `wait_until` | passed to shared fetch helper; helper normalizes default/allowed values | same | Parity should verify the value passed to helper. |
| `settle_wait_ms` | passed to shared fetch helper; helper clamps range | same | Parity should verify the value passed to helper. |
| requested URL | `prescription.connection_url or target_url` | same, from embedded `source_protocol` in directive | Directive/protocol lineage should be checked. |
| allowed URL/directive policy | not applicable to inspect | required by collect preflight and collect path | Not expected to be identical; expected to be collect-only authorization. |

Existing transport review found no obvious separate collect-only Playwright launch path: both inspect and collect use `_fetch_with_chrome_profile()` from `arthur.inspect`.

## Proposed Synthetic Harness

Add a no-network test file:

```text
tests/test_chrome_profile_transport_parity_v0_6.py
```

The harness should:

1. Build a synthetic top-level protocol with:
   - `target_url=https://example.com/softcon/channel`
   - `best_path=rsc_payload`
   - `transport=chrome_profile`
   - `profile_required=true`
   - RSC fields and verification block.

2. Build a synthetic CollectDirective with:
   - embedded `source_protocol`;
   - `approved=true`;
   - `transport=chrome_profile`;
   - `approved_best_path=rsc_payload`;
   - exact `approved_scope.allowed_urls=["https://example.com/softcon/channel"]`;
   - `policy.allow_chrome_profile_collect=true`;
   - `policy.allow_visible_window=true`;
   - `policy.visible_window_allowed=true`;
   - `policy.wait_until=networkidle`;
   - `policy.settle_wait_ms=1500`;
   - `raw_policy.save_raw=false`.

3. Use one shared synthetic profile options dict:
   - `chrome_executable=sys.executable`;
   - `user_data_dir=os.getcwd()`;
   - `profile_directory=Synthetic`;
   - `visible_window_requested=true`;
   - `visible_window_allowed=true`;
   - `wait_until=networkidle`;
   - `settle_wait_ms=1500`.

4. Monkeypatch both module references, because collect imports the helper directly:
   - `arthur.inspect._fetch_with_chrome_profile`
   - `arthur.collect_chrome_profile._fetch_with_chrome_profile`

5. Use `MockFetcher` for robots so no external request occurs.

6. Fake browser response:
   - status `200`;
   - rendered URL equal to target for the success parity case;
   - rendered title with no secret values;
   - synthetic `self.__next_f.push(...)` RSC payload.

## Test Cases To Add

1. `test_inspect_and_collect_pass_same_chrome_profile_options_no_network`
   - Run `inspect_target()` and `collect()` with the same `chrome_profile_options`.
   - Capture spy calls from both paths.
   - Assert requested URL equality.
   - Assert these option keys match exactly:
     - `chrome_executable`
     - `user_data_dir`
     - `profile_directory`
     - `visible_window_requested`
     - `visible_window_allowed`
     - `wait_until`
     - `settle_wait_ms`

2. `test_collect_directive_policy_is_authorization_not_transport_drift`
   - Confirm collect requires `approved=true`, `allow_chrome_profile_collect=true`, and exact `allowed_urls`.
   - Confirm these gates do not alter the options passed to `_fetch_with_chrome_profile()`.

3. `test_collect_metadata_parity_no_network`
   - After synthetic collect success, assert `execution_metadata` includes:
     - `chrome_profile_collect=true`
     - `visible_window_used=true`
     - `visible_window_allowed=true`
     - `wait_until=networkidle`
     - `settle_wait_ms=1500`
     - sanitized `requested_url`
     - sanitized `rendered_url`
     - `response_status=200`
     - `effective_status=response_200`
     - `checkpoint_detected=false`
     - `rsc_payload_detected=true`
     - `protocol_hash`
     - `directive_hash`
     - `exact_allowed_url_match=true`

4. `test_collect_rendered_query_redaction_no_network`
   - Return a synthetic rendered URL with query values such as `?token=SHOULD_NOT_APPEAR`.
   - Expect collect to stop on rendered URL allowlist mismatch.
   - Assert stored metadata redacts query values and secret sentinels are absent.

5. `test_inspect_checkpoint_and_collect_checkpoint_stop_have_comparable_diagnostics`
   - Return synthetic checkpoint HTML/title from both paths.
   - Inspect should record checkpoint diagnostics in `available_resources`.
   - Collect should record checkpoint diagnostics in `execution_metadata` and `stopped_stage=rendered_checkpoint`.
   - No raw HTML/screenshot artifacts.

## Runtime Behavior Change

No runtime behavior change is required for the first parity harness.

If a later test needs normalized launch options rather than raw input options, add a pure helper such as:

```text
_chrome_profile_public_option_summary(options) -> dict
```

The helper should not launch Chrome, read cookies/tokens, or expose secret values. It should only summarize non-secret options for assertions and metadata. Do not add this unless the mock harness cannot assert parity through existing monkeypatch points.

## Expected Test Commands

```powershell
& 'C:\Users\faust\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile arthur\inspect.py arthur\collect_chrome_profile.py arthur\cli.py
& 'C:\Users\faust\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests\test_chrome_profile_transport_parity_v0_6.py
& 'C:\Users\faust\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests\test_chrome_profile_collect_v0_6.py
& 'C:\Users\faust\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests\test_chrome_profile_inspect_v0_6.py
```

These commands are local/synthetic only and must not launch real Chrome or make external website requests.

## Remaining Risks

- The synthetic harness can prove option parity and metadata parity, but it cannot prove real Softcon challenge state parity.
- Inspect and collect still differ intentionally: collect has directive approval, exact allowlist, and output policy gates.
- The previous failed Softcon smoke collect remains boundary evidence until a separate operator-approved diagnostic is authorized.

## Smallest Next Action

Implement only the no-network parity test file above. Do not change runtime behavior unless the test exposes an actual mismatch in option propagation.
