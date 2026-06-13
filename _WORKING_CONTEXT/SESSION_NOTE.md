# SESSION_NOTE

## Date

2026-06-12

## Case

project working context

## Scenario

Scenario 5 - Context/package maintenance

## Goal

Maintain the lightweight solo user + CLI/Codex workflow and active Charles/Arthur operating policy.

## Loaded Context

- `_WORKING_CONTEXT/README.md`
- `_WORKING_CONTEXT/10_EXTERNAL_AUDIT_PROCESS.md`
- user-provided review attachment

## Actions

- Deleted `10_EXTERNAL_AUDIT_PROCESS.md`.
- Added `10_USER_CLI_WORKFLOW.md`.
- Updated `README.md` to point to `10_USER_CLI_WORKFLOW.md`.
- Updated `07_DECISION_LOG.md` with `DL_CONTEXT_20260611_009`.
- Marked the previous external-audit framing decisions as superseded.
- Applied final User-CLI workflow stability patch from follow-up review.
- Added reference role exclusivity, session note location rules, patch candidate status, and intent-alignment gate definition.
- Updated `07_DECISION_LOG.md` with `DL_CONTEXT_20260611_010`.
- Added Korean translation `10_USER_CLI_WORKFLOW.ko.md`.
- Updated `README.md` and `07_DECISION_LOG.md` with the translation reference.
- Synced Korean and English workflow headers by removing external-audit contrast and named reference-case examples.
- Promoted guest/session token handling into project policy.
- Reviewed external v1.1 workflow revision and prepared a merged `proposed` patch candidate without replacing canonical workflow files.
- Corrected the proposed decision log path to `_WORKING_CONTEXT/07_DECISION_LOG.md`, preserved the guest/session token policy, and added `AGENTS.md` to the protected-file list in the candidate.
- Applied the v1.1 workflow candidate by explicit user approval.
- Replaced the active English workflow with v1.1 `Status: active`.
- Rebuilt the Korean translation to match v1.1.
- Marked the v1.1 patch candidate as `applied`.
- Updated `07_DECISION_LOG.md` with `DL_CONTEXT_20260611_015`.
- Promoted the Arthur ephemeral cookie bridge policy into active operating policy by explicit user instruction.
- Added an applied policy record in `_WORKING_CONTEXT/PATCH_CANDIDATES/`.
- Updated `10_USER_CLI_WORKFLOW.md`, `10_USER_CLI_WORKFLOW.ko.md`, `02_TOOL_CONTRACTS_Charles_Arthur.md`, `AGENTS.md`, and `07_DECISION_LOG.md`.

## Outputs

- `10_USER_CLI_WORKFLOW.md`
- `10_USER_CLI_WORKFLOW.ko.md`
- `README.md`
- `07_DECISION_LOG.md`
- `SESSION_NOTE.md`
- `PATCH_CANDIDATES/10_USER_CLI_WORKFLOW_v1_1_proposed_20260611.md`
- `PATCH_CANDIDATES/arthur_ephemeral_cookie_bridge_policy_applied_20260612.md`

## Decisions

- Default document frame is workflow efficiency, not external audit.
- Hosea remains modeled as CLI/Codex session plus working-context documents.
- External audit bundle/logging is optional, not part of default operation.
- `SESSION_NOTE.md` is the default handoff artifact for meaningful sessions.
- `SESSION_NOTE.md` locations are now fixed by session type.
- Patch candidates require explicit state and do not mutate packages unless marked `applied` by user instruction.
- Each session should load at most one active reference per role.
- Korean workflow translation exists for operator readability; the source workflow file remains `10_USER_CLI_WORKFLOW.md`.
- Workflow headers now state operating purpose and case-neutrality directly.
- Operator-approved guest/session profiles may be used, but token values must not be pasted, logged, stored in artifacts, committed, or preserved in raw outputs by default.
- External v1.1 workflow revision should not be copied verbatim; it must preserve current token policy, use `07_DECISION_LOG.md`, and protect project-wide `AGENTS.md`.
- User explicitly approved applying the v1.1 workflow candidate.
- `10_USER_CLI_WORKFLOW.md` is now active v1.1.
- `10_USER_CLI_WORKFLOW.ko.md` is synced to active v1.1.
- Arthur ephemeral cookie bridge is active operating policy only as same-origin, memory-only session delegation.
- Direct Chrome cookie database reads, bulk cookie export, cross-origin forwarding, and durable token/cookie value storage remain forbidden by default.
- The policy does not approve live collect or `CollectDirective.approved=true`; those still require separate operator approval and intent alignment.

## Blockers

- None.

## Next Step

Use `10_USER_CLI_WORKFLOW.md` as the operating workflow for future sessions.
For future sessions, treat the ephemeral cookie bridge policy as active only when exact origin scope, explicit directive enablement, no secret persistence, and normal collect approval gates are all satisfied.
