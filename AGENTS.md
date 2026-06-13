# Streamer Consulting Project Agents

This file is the project-wide operating instruction for Codex sessions working in the Streamer Consulting Project.

Start from:

```text
D:\Codex_Workspace\_CODEX_SESSION_START.md
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\README.md
```

Then classify the task using:

```text
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\09_NEW_SESSION_WORKFLOW_SCENARIOS.md
```

For the workflow standard, use:

```text
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\10_USER_CLI_WORKFLOW.md
D:\Codex_Workspace\Streamer Consulting Project\_WORKING_CONTEXT\10_USER_CLI_WORKFLOW.ko.md
```

## External Site Scout Rule

Do not spend a failed sandbox attempt on external web scout.

Known behavior in this Codex desktop environment:

```text
local file inspection -> sandbox
code edit and mock/unit tests -> sandbox
offline ScoutReport/protocol parsing -> sandbox
external site Charles scout -> request escalation directly
external Playwright/browser probe -> request escalation directly
repeated external retries -> do not run without explicit user approval
```

For Softcon or other external targets, request `require_escalated` before running Charles or Playwright network probes.

Use a narrow approval request:

```text
Run one Charles/Playwright scout for the named target and write to a temp output path without overwriting existing artifacts.
```

## Output Safety

- Never overwrite an existing ScoutReport/protocol unless the user explicitly asks.
- For live-target tests, write temp files such as `{target_id}.temp_recovery_test.scout_report.json`.
- Preserve full ScoutReport.
- Extract only top-level `protocol` for Arthur.
- Do not create CollectDirective from Charles output.
- Do not run Arthur inspect or collect unless the user explicitly asks and the workflow gate allows it.
- Do not mutate CaseResult, DisclosureLog, PublicDemoRow, or final package state without explicit user approval.

## Encoding Safety

- Use UTF-8 explicitly for project text artifacts unless a file-specific spec says otherwise.
- In Windows PowerShell, use `-Encoding UTF8` for `Get-Content`, `Set-Content`, `Add-Content`, `Out-File`, `Export-Csv`, and similar text commands.
- Set `PYTHONIOENCODING=utf-8` before Python/CLI commands that may print Korean or other non-ASCII text.
- If Korean text appears garbled, re-read with explicit UTF-8 before editing. Do not patch text that may already be mojibake.

## Boundary Handling

When `best_path=manual_review`, `gate_status=restricted`, `http_429`, CAPTCHA, checkpoint, or login/session signals appear:

- preserve the boundary signal
- bot-defense / checkpoint / CAPTCHA passing is judged by HARM, not technique (work-boundary guide §2.3/§4). For PUBLIC data: allowed under operator approval when polite, sequential, no server overload, and retreating on block (note ToS-violation possibility once; risk is the operator's). FORBIDDEN when it would overload the server, retry aggressively after block/429/challenge, enable mass-signup/deception/abuse, or evade access control to obtain private/login-gated/account data. Never persist secret cookie/token/auth/header values.
- emit or verify structured `recovery_plan`
- mark whether `profile_or_session_likely_needed`
- mark whether `url_resolution_needed`
- set or respect `arthur_inspect_recommended=false` when no executable `collection_plan` exists

Operator approval is required before any profile/session based scout.

## Guest / Session Token Policy

Guest/session profiles may be used when the operator explicitly approves the scope.

Allowed:

- use an operator-approved guest/session profile
- reference a local-only profile file
- record header/cookie names
- record token type, expiry, and scope summary

Not allowed by default:

- paste token values into chat
- store token values in ScoutReport, SESSION_NOTE, RUN_MANIFEST, or other artifacts
- store token values in git-tracked files
- preserve token values in raw HTML, logs, screenshots, or debug output
- leave reusable token values as plaintext artifacts

Record only summaries such as:

```text
profile/session provided: yes
type: guest_session
scope: approved target/domain only
secret_values_logged: false
```

## Ephemeral Cookie Bridge Policy

Arthur may use an operator-approved ephemeral cookie bridge only when the workflow and directive explicitly allow it.

Allowed shape:

- open the operator-approved Chrome profile through Playwright
- read cookies only for the exact approved origin with `context.cookies(origin)`
- pass cookie values in memory only to same-origin `curl_cffi` execution
- record only cookie names, domains, expiry/session summary, scope, and bridge status

Not allowed by default:

- direct reads from the Chrome cookie database
- bulk cookie export
- cross-origin cookie forwarding
- storing cookie values in chat, logs, ScoutReport, InspectResult, CollectionResult, SESSION_NOTE, RUN_MANIFEST, raw artifacts, screenshots, or git-tracked files
- creating reusable plaintext cookie/token artifacts

Required gates include exact URL/origin allowlist, explicit bridge enablement, no raw/screenshot output, and passed intent alignment. Collect additionally requires `CollectDirective.approved=true`. If any scope, checkpoint, CAPTCHA, private/account, or secret-persistence uncertainty appears, stop and preserve the boundary.

## User Context

- User messages are short and often operational.
- Treat corrections as updated operating constraints.
- Avoid repeated failed attempts when the environment behavior is already known.
- Prefer one narrow verified run over broad retry loops.
