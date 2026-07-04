# Handoffs Databook

This directory is the forward-only replacement for appending new entries to
`_WORKING_CONTEXT/SESSION_NOTE.md`.

## File Rule

One handoff equals one file:

```text
YYYY-MM-DDTHHMM-<Surface>.md
YYYY-MM-DDTHHMM-<Surface>-02.md
```

Use the suffix only when the same surface writes more than one handoff in the
same minute. Do not use colon characters in filenames.

## Frontmatter

```yaml
---
surface: Codex
timestamp: 2026-07-04T17:30
task: one-line task title
status: commit-candidate
next_surface: operator
files: [relative/path.md]
decision_ids: [DL_CONTEXT_20260704_050]
links: [related-slug]
---
```

Supported values:

- `surface`: `CC`, `Codex`, `Cowork`
- `status`: `raw`, `reviewed`, `commit-candidate`, `hold`, `excluded`
- `next_surface`: `CC`, `Codex`, `Cowork`, `operator`

`files`, `decision_ids`, and `links` must be one-line arrays. Use `[]` when
empty.

## Index

Regenerate the index after adding or editing a handoff:

```powershell
python -m consulting.tools.ops.status_board
```

CI checks the index with:

```powershell
python -m consulting.tools.ops.status_board --check
```
