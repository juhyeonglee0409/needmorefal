# Arthur Ephemeral Cookie Bridge Policy

Version: 1.0 (2026-06-12)
Status: applied - canonicalized by explicit user approval on 2026-06-12

## Scope

This policy applies to Arthur execution paths that need to reuse an operator-approved browser session for a specific external origin.

It defines an `ephemeral cookie bridge`: Arthur may open an operator-approved Chrome profile with Playwright, read cookies for an exact approved origin with `context.cookies(origin)`, and pass those cookie values in memory only to an approved same-origin `curl_cffi` transport.

This is session delegation by the operator. It is not durable credential extraction.

## Allowed

- Use an operator-approved guest/session Chrome profile for an exact target origin.
- Read cookies only through the active Playwright browser context after opening the exact approved origin.
- Pass cookie values in memory only to `curl_cffi` for the same approved origin and exact allowed URLs.
- Record cookie names, domains, expiry/session status, scope summary, and count.
- Record whether the bridge was used and whether secret values were persisted.
- Require explicit directive/policy flags such as `allow_ephemeral_cookie_bridge=true`.

## Required Gates

- for collect: `CollectDirective.approved=true`
- for inspect-only diagnostics: explicit operator request for the exact origin
- exact `approved_scope.allowed_urls`
- exact origin allowlist
- operator-approved `chrome_profile`
- explicit bridge enablement flag
- explicit `curl_cffi` impersonation mode if used
- raw HTML, screenshot, debug-log, and token-value storage disabled

## Not Allowed By Default

- Direct reads from the Chrome cookie database.
- Bulk cookie export.
- Cross-origin cookie forwarding.
- Storing cookie values in chat, ScoutReport, InspectResult, CollectionResult, SESSION_NOTE, RUN_MANIFEST, raw artifacts, screenshots, debug logs, or git-tracked files.
- Creating reusable plaintext token/cookie artifacts.
- Using the bridge to bypass CAPTCHA solvers, credential prompts, private account pages, or unexpected security pages.

## Stop Conditions

Arthur must stop and preserve the boundary when:

- the origin or URL is outside the exact approved scope
- cookie domains do not match the approved origin
- cookie bridge use cannot prove memory-only handling
- a checkpoint, CAPTCHA, private/account page, or unexpected security page appears
- required directive flags are missing
- ResearchPlan/InspectResult intent alignment has not passed

## Output Policy

Allowed output fields are summary-only:

```text
ephemeral_cookie_bridge_used: true|false
secret_values_persisted: false
cookie_names: [...]
cookie_domain_summary: [...]
cookie_expiry_summary: session|timestamp|mixed
origin_scope: https://example.com
curl_cffi_impersonation: explicit value or not_used
```

Cookie values must never be serialized.

## Boundary

This policy does not itself approve any live collect, Softcon collection, CaseResult promotion, DisclosureLog change, PublicDemoRow creation, or package canonical mutation. It only defines the operational gate for a future Arthur implementation or directive.
