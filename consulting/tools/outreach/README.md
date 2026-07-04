# Outreach Pipeline

Minimal implementation for `specs/vtuber_outreach_pipeline_spec_20260704.md`.

## Scope

- S1 discovery: CHZZK public `/service/v1/search/channels` and `/service/v1/search/lives`.
- S2 enrich: CHZZK public `/service/v1/channels/{channelId}`.
- S3 classify: local heuristic plus `agencies.yaml` exclusion seed. `llm.py` exposes an interface stub only.
- S4 label: follower segment `rookie`, `growth`, `large`, or `unknown`.
- S5 email: explicit public email regex from channel bio only.

S6 Softcon metrics and S7 draft generation remain separate gates.

## Commands

From `consulting/`:

```powershell
python -m tools.outreach collect --source lives --pages 1 --pool runs/vtuber_outreach_pilot_20260704/channel_pool.ndjson --progress runs/vtuber_outreach_pilot_20260704/outreach_progress.ndjson
```

Normalize an existing NDJSON artifact into the canonical append-only pool:

```powershell
python -m tools.outreach normalize --input runs/vtuber_outreach_pilot_20260704/live_candidates_enriched.ndjson --pool runs/vtuber_outreach_pilot_20260704/channel_pool.ndjson
```

In this Codex desktop environment, live external runs require escalation before execution. Unit tests do not access the network.

## Output Contract

The pool is append-only NDJSON. Each line is one canonical channel record with:

- `channel_id`, `channel_name`, `follower_count`, `description`
- `segment`
- `vtuber`, `solo`, `email`, `activity`, `metrics`, `outreach`

If any prior pool line marks a channel as `outreach.status=opted_out`, later `collect` or `normalize` skips that channel and records `skip_opted_out` in progress.
