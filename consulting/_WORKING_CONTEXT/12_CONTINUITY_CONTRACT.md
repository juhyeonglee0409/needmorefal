# Continuity Contract

This document governs how all surfaces (Codex, Claude Code, Cowork/Hosea) persist state across sessions. It defines when, where, and how to write handoff databook entries and DECISION_LOG entries.

Every surface reads this contract. No surface is exempt.

---

## Part 1: Handoff Databook

### Purpose

Prevent the next session from reconstructing state from scratch. Every session that produces output must leave a handoff entry.

### Trigger

Any task completion that produces an output: file, data, report, actionable finding, or state change. If something was created, moved, or decided — write a handoff.

### Where to write

| Task type | Location |
|---|---|
| Streamer Consulting work | `_WORKING_CONTEXT/handoffs/YYYY-MM-DDTHHMM-<Surface>.md` |
| Gunsmith general (non-Streamer) | Handoff section at the bottom of the relevant report in `Gunsmith_Mailbox/reports/` |

`_WORKING_CONTEXT/SESSION_NOTE.md` is the legacy archive for pre-databook handoffs. Do not append new Streamer Consulting handoffs there unless the operator explicitly asks for legacy-format output.

`_WORKING_CONTEXT/handoffs/INDEX.md` is generated from individual handoff files. Do not edit it manually.

### Format

Each handoff is a separate file. Do not overwrite another surface's handoff file. If the same surface writes more than one handoff in the same minute, append `-02`, `-03`, etc. to the filename.

Filename:

```text
YYYY-MM-DDTHHMM-<Surface>.md
YYYY-MM-DDTHHMM-<Surface>-02.md
```

Use minute precision. Do not use colon characters in filenames.

Required frontmatter:

```yaml
---
surface: CC | Codex | Cowork
timestamp: 2026-07-04T17:30
task: one-line task title
status: raw | reviewed | commit-candidate | hold | excluded
next_surface: CC | Codex | Cowork | operator
files: [relative/path, ...]
decision_ids: [DL_CONTEXT_20260704_050]
links: [related-doc-slug]
---
```

Body:

```
1. What was done
2. What files were produced (absolute or repo-relative path)
3. File status (raw / reviewed / commit-candidate / hold / excluded)
4. What the next surface should do
5. Boundaries and warnings
```

### Field definitions

**Surface**: `Codex`, `CC` (Claude Code), or `Cowork`. Required. Without it, provenance is unknown.

**Timestamp**: ISO 8601 local time, minute precision. Required. Without it, entry ordering is ambiguous when multiple surfaces write in the same day.

**Task**: one-line title for the handoff. Keep details in the body.

**File status values**:

| Status | Meaning |
|---|---|
| `raw` | Unverified output. May contain errors. |
| `reviewed` | Cross-checked and usable as input for downstream work. |
| `commit-candidate` | Ready for Codex to commit to git. |
| `hold` | Pending operator decision. Do not use without approval. |
| `excluded` | Dead end. Do not use. Kept for record only. |

**Next surface**: must name the target — Codex, CC, Cowork, or operator. Not "next tool" or "next step." The reader must know who should pick this up.

**Boundaries**: rate limits hit, blocked paths, operator approval required, data quality caveats, policy constraints discovered. Anything the next surface would regret not knowing.

### Index

After writing or editing a handoff, regenerate the index:

```powershell
python -m consulting.tools.ops.status_board
```

CI checks the generated index:

```powershell
python -m consulting.tools.ops.status_board --check
```

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

1. Read `handoffs/INDEX.md` before resuming recent Streamer context work; read the referenced handoff files only as needed
2. Read legacy `SESSION_NOTE.md` only when pre-databook history is needed
3. Write a handoff file on task completion
4. Regenerate `handoffs/INDEX.md` after writing a handoff
5. Check the current highest DECISION_LOG number before adding a new entry
6. Respect all `status: active` decisions in the log

### No surface may

1. Delete or overwrite another surface's handoff files
2. Mark a DECISION_LOG entry as inactive without operator approval
3. Contradict an active decision without first logging a superseding decision with operator authority
4. Skip the handoff because the task felt minor — if output exists, handoff exists

### Write serialization (operator ruling 2026-07-04)

Operator works one active session at a time. That rule only holds if every surface also follows these two rules:

1. **Background runs count as writers.** A session that spawns a background process (codex exec, scheduled retry, batch collector) that writes to a repo must treat that repo as claimed until the run finishes. Either wait for it before handing off, or scope the run to paths no other session touches. "One active session" means one active *writer*, not one visible window.
2. **Re-read shared documents immediately before writing.** Long-lived sessions hold stale copies of `handoffs/INDEX.md`, `SESSION_NOTE.md`, specs, and runbooks. Before editing any shared document, re-read its current state first — anchor edits on what is on disk now, not on what the session remembers.

Commit frequently. Git turns the worst remaining case into a loud merge conflict instead of a silent overwrite.

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
| Current handoff and recent state | `handoffs/INDEX.md` + referenced handoff files |
| Legacy pre-databook handoff history | `SESSION_NOTE.md` |
| Durable decisions and policy | `07_DECISION_LOG.md` |
| Site-specific working routes, failures, defaults, proven-run pointers | `site_runbooks/` |
| Cross-site reusable rules | `03_STREAMER_CASE_GENERIC_PROTOCOL.md` |
| Detailed execution evidence for one case/run | case-local run note |

If information belongs in more than one place, put the operational summary in the canonical home and link to the evidence. Do not copy long details.

### Archive review

- If `handoffs/INDEX.md` grows hard to scan, update the index generator or add filters before moving handoff files.
- `SESSION_NOTE.md` is already legacy after the handoff databook transition. Do not migrate, compact, rename, or copy it without explicit operator approval.
- If `07_DECISION_LOG.md` grows hard to scan, add or update an index first. Do not move active decisions without operator approval.
- Archive work must preserve provenance, timestamps, decision IDs, and status values.
- No surface may silently compact, delete, or relocate active context entries.

### Conflict resolution

If a handoff entry and a DECISION_LOG entry contradict each other, the DECISION_LOG takes precedence. Handoffs are current state; DECISION_LOG is durable policy.

If two DECISION_LOG entries contradict each other, the newer one takes precedence (it should reference and supersede the older one).
