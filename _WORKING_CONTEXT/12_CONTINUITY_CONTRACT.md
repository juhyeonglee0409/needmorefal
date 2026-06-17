# Continuity Contract

This document governs how all surfaces (Codex, Claude Code, Cowork/Hosea) persist state across sessions. It defines when, where, and how to write SESSION_NOTE entries and DECISION_LOG entries.

Every surface reads this contract. No surface is exempt.

---

## Part 1: SESSION_NOTE

### Purpose

Prevent the next session from reconstructing state from scratch. Every session that produces output must leave a handoff entry.

### Trigger

Any task completion that produces an output: file, data, report, actionable finding, or state change. If something was created, moved, or decided — write a handoff.

### Where to write

| Task type | Location |
|---|---|
| Streamer Consulting work | `_WORKING_CONTEXT/SESSION_NOTE.md` |
| Gunsmith general (non-Streamer) | Handoff section at the bottom of the relevant report in `Gunsmith_Mailbox/reports/` |

### Format

Each entry is appended. Do not overwrite prior entries. The primary surface may rewrite the main body (Date, Case, Scenario, Goal, etc.) to reflect current state — but handoff entries below are append-only.

```
## [Surface/Agent] YYYY-MM-DDTHH:MM

1. What was done
2. What files were produced (absolute or repo-relative path)
3. File status (raw / reviewed / commit-candidate / hold / excluded)
4. What the next surface should do
5. Boundaries and warnings
```

### Field definitions

**Surface tag**: `[Codex]`, `[CC]` (Claude Code), `[Cowork/Hosea]`. Required. Without it, provenance is unknown.

**Timestamp**: ISO 8601 local time, minute precision. Required. Without it, entry ordering is ambiguous when multiple surfaces write in the same day.

**File status values**:

| Status | Meaning |
|---|---|
| `raw` | Unverified output. May contain errors. |
| `reviewed` | Cross-checked and usable as input for downstream work. |
| `commit-candidate` | Ready for Codex to commit to git. |
| `hold` | Pending operator decision. Do not use without approval. |
| `excluded` | Dead end. Do not use. Kept for record only. |

**Next surface**: must name the target — Codex, CC, or Cowork. Not "next tool" or "next step." The reader must know which surface should pick this up.

**Boundaries**: rate limits hit, blocked paths, operator approval required, data quality caveats, policy constraints discovered. Anything the next surface would regret not knowing.

### What NOT to write

- Do not log routine intermediate steps. Only the final handoff matters.
- Do not duplicate DECISION_LOG content here. Reference the decision_id if relevant.
- Do not write a handoff for pure conversation with no output.

---

## Part 2: DECISION_LOG

### Purpose

Prevent the same question from being debated twice. Record durable decisions that future sessions must respect regardless of which surface they run on.

### Trigger

A DECISION_LOG entry is warranted when:

- A path was tried and confirmed dead (technical impossibility, not just failure)
- A policy was established that constrains future work
- The same question came up in two or more sessions and was resolved the same way
- An operator made an explicit ruling that future sessions must follow

### When NOT to write

- Routine findings that only matter for the current task → SESSION_NOTE is sufficient
- Anything already captured adequately in a SESSION_NOTE handoff
- Incremental progress updates

Most tasks do not produce a DECISION_LOG entry. The threshold is: "will a future session waste time re-debating this?"

### Where to write

`_WORKING_CONTEXT/07_DECISION_LOG.md`

New entries are prepended (newest first).

### Format

```
## YYYY-MM-DD - [title]

decision_id: `DL_[SCOPE]_YYYYMMDD_[NNN]`

scope:
- [affected files, systems, or policies]

what_changed:
[what was decided or established]

why:
[root cause, reasoning, or evidence]

authority:
[who approved — "operator YYYY-MM-DD" or "self-determined by [surface]"]

boundary:
[what this decision does NOT change — scope containment]

status: active
```

### Scope prefixes

| Prefix | Use |
|---|---|
| `DL_TOOLING_` | Tool implementation, pipeline, infrastructure |
| `DL_CONTEXT_` | Working context, documentation, workflow |
| `DL_INFRA_` | Cross-surface infrastructure, entry points, architecture |
| `DL_POLICY_` | Operating policy, rate limits, access rules |

### Numbering

Increment from the highest existing `NNN` in the log. Check the current highest number before assigning.

### Retroactive recording

If during work you discover a past decision that was made but never logged — log it now.

- Use the original decision date, not today's date
- Add `(retroactive)` to the title
- In the `why` field, note when and how the decision was originally made

Example: `## 2026-06-12 - Cookie export prohibition (retroactive)`

### Authority levels

| Level | Meaning |
|---|---|
| `operator YYYY-MM-DD` | User/operator explicitly approved |
| `self-determined by [surface]` | Surface made the call within its role boundary; operator may override |

Self-determined decisions are limited to: technical dead-end declarations, tool configuration within existing policy, and documentation corrections. Policy decisions require operator authority.

---

## Part 3: Cross-Surface Rules

### Every surface must

1. Read `SESSION_NOTE.md` before starting work on a Streamer task
2. Write a handoff entry on task completion
3. Check the current highest DECISION_LOG number before adding a new entry
4. Respect all `status: active` decisions in the log

### No surface may

1. Delete or overwrite another surface's SESSION_NOTE entries
2. Mark a DECISION_LOG entry as inactive without operator approval
3. Contradict an active decision without first logging a superseding decision with operator authority
4. Skip the handoff because the task felt minor — if output exists, handoff exists

---

## Part 4: Working Context Hygiene

The working context folder is a routing layer. It must stay small enough that a new session can load the entrypoint, choose the right pointer, and avoid raw-loading long documents.

### Top-level file discipline

- Target: keep `_WORKING_CONTEXT` top-level files near 20 or fewer.
- Review threshold: if top-level files exceed 25, propose a grouping or archive plan before adding more top-level files.
- Folder threshold: if one subject needs 3 or more files, create a subdirectory with its own `README.md`.
- Every top-level file or directory must be listed in `_WORKING_CONTEXT/README.md`.

### Role separation

Do not duplicate the same information across multiple context documents.

| Information type | Canonical home |
|---|---|
| Current handoff and recent state | `SESSION_NOTE.md` |
| Durable decisions and policy | `07_DECISION_LOG.md` |
| Site-specific working routes, failures, defaults, proven-run pointers | `site_runbooks/` |
| Cross-site reusable rules | `03_STREAMER_CASE_GENERIC_PROTOCOL.md` |
| Detailed execution evidence for one case/run | case-local run note |

If information belongs in more than one place, put the operational summary in the canonical home and link to the evidence. Do not copy long details.

### Archive review

- If `SESSION_NOTE.md` grows beyond roughly 30 handoff entries or becomes hard to scan, propose an archive split. Keep the current active state and latest handoffs in place.
- If `07_DECISION_LOG.md` grows hard to scan, add or update an index first. Do not move active decisions without operator approval.
- Archive work must preserve provenance, timestamps, decision IDs, and status values.
- No surface may silently compact, delete, or relocate active context entries.

### Conflict resolution

If a SESSION_NOTE entry and a DECISION_LOG entry contradict each other, the DECISION_LOG takes precedence. SESSION_NOTE is current state; DECISION_LOG is durable policy.

If two DECISION_LOG entries contradict each other, the newer one takes precedence (it should reference and supersede the older one).
