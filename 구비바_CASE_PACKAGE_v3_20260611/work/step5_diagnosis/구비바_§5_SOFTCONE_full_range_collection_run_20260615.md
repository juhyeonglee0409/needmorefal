# 구비바 §5 SOFTC.ONE Full-Range Collection Run

Date: 2026-06-15  
Surface: Codex  
Scope: §5 cohort broadcast records, SOFTC.ONE `/streams` route  
Status: reviewed operational run note; not a final analytical judgment

---

## 1. Run Purpose

The original §5 instruction required broadcast-history collection for the full available period, not the default recent window.

This run established a browser-bound full-range collection path for the deduped T1/T2 cohort target set and recorded the remaining extraction risks.

Target source:

```text
data/cohort/specs/구비바_§5_broadcast_sample_spec.json
```

Output root:

```text
data/cohort/collected/broadcast_samples/
```

---

## 2. Full-Range Verification

Default `/streams` behavior was not full-history.

Observed default probe:

```text
visible date range: 2026. 05. 15 - 2026. 06. 15
visible stream links: 24
```

Full/max range was verified by appending explicit SOFTC.ONE query parameters to `/streams`:

```text
startDateTime=2023-10-01T15:00:00.000Z
endDateTime=2026-06-15T14:59:59.999Z
```

Probe artifact:

```text
data/cohort/collected/broadcast_samples/_date_query_probe.json
```

Verified probe result:

```text
visible date range: 2023. 10. 02 - 2026. 06. 15
visible stream links: 100
checkpoint: false
rateLimited: false
```

Interpretation:

- Full-range query bounds were accepted by the page.
- The visible DOM still exposed only 100 stream links on the probe channel.
- Treat the 100-row observation as an extraction-cap risk, not as evidence that only 100 broadcasts exist.

---

## 3. Collector Changes Used For This Run

Script:

```text
work/step5_diagnosis/scripts/collect_step5_broadcasts_cdp_parallel.mjs
```

Relevant changes:

- Added full-range URL generation for `/streams`.
- Added `--date-start-utc`, `--date-end-utc`, and `--full-range`.
- Added `--delay-ms` and `--jitter-ms` to avoid bursty browser-bound collection.
- Changed resume smoke order to `offset -> skipExisting -> limit`, so smoke runs cover the next missing targets.
- Recorded `date_range`, `delay_ms`, `jitter_ms`, and target-summary fields in manifests.

No cookie, localStorage, session token, auth header, raw HTML dump, or screenshot was persisted.

---

## 4. Scale Ladder

The run did not jump directly to the final concurrency. It scaled gradually and preserved separate manifests.

| Rung | Manifest | Concurrency | Delay/Jitter | Attempted | Normal Success | Short Rows | Errors | Boundary |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `_collection_manifest_scale1.json` | 1 | 12s / 3s | 2 | 2 | 0 | 0 | null |
| 2 | `_collection_manifest_scale2.json` | 2 | 12s / 3s | 6 | 5 | 0 | 1 | null |
| 3 | `_collection_manifest_scale3.json` | 3 | 12s / 3s | 12 | 11 | 0 | 1 | null |
| 4 | `_collection_manifest_scale4_3c6s.json` | 3 | 6s / 2s | 12 | 11 | 0 | 1 | null |
| 5 | `_collection_manifest_scale5_6c6s.json` | 6 | 6s / 2s | 18 | 16 | 0 | 2 | null |

Errors during scale-up were `not_found`, not rate-limit or checkpoint signals.

---

## 5. Final Full Resume Run

Command shape:

```powershell
node work/step5_diagnosis/scripts/collect_step5_broadcasts_cdp_parallel.mjs `
  --mode full `
  --port 9222 `
  --concurrency 6 `
  --wait-ms 15000 `
  --delay-ms 6000 `
  --jitter-ms 2000 `
  --stagger-ms 1000 `
  --skip-existing true `
  --progress-name _collection_progress_full_6c6s.ndjson `
  --manifest-name _collection_manifest_full_6c6s.json `
  --errors-name _collection_errors_full_6c6s.csv
```

Manifest:

```text
data/cohort/collected/broadcast_samples/_collection_manifest_full_6c6s.json
```

Final manifest summary:

| Field | Value |
|---|---:|
| candidate_rows_before_dedupe | 380 |
| unique_targets_after_dedupe | 323 |
| skipped_existing | true |
| attempted_in_this_run | 190 |
| concurrency | 6 |
| delay_ms | 6000 |
| jitter_ms | 2000 |
| normal success_count | 175 |
| short_rows_count | 1 |
| error_count | 14 |
| boundary_signal | null |

Date range recorded in the manifest:

```json
{
  "startDateTime": "2023-10-01T15:00:00.000Z",
  "endDateTime": "2026-06-15T14:59:59.999Z",
  "label": "full_max_range"
}
```

Short-row item:

```text
T2 / 97be9cdfb3dcd0c98219dfcbffb4baab / row_count=7
```

The 14 full-run errors were `not_found`; sampled error records had repeated HTTP 200 status codes and `network_rate_limited=false`, so they are not currently classified as 429/checkpoint failures.

---

## 6. Current File-Level Coverage

Current local data CSV count under `broadcast_samples`:

```text
T1: 178
T2: 139
total data CSV: 317
```

Coverage note:

- The folder includes earlier sample/smoke outputs.
- Use the full-run manifest and target set as the run ledger.
- Current target-matched coverage was recalculated as 309/323, leaving 14 missing targets matching the full-run `not_found` errors.

Top-level `_collection_errors*.csv` files are operational ledgers, not data CSVs.

---

## 7. Operational Meaning

This run established several reusable facts for SOFTC.ONE Step5 collection:

- Full-history collection must be explicit; the default UI window is not enough.
- Browser-bound CDP collection can be run with 6 workers at 6s delay plus jitter in the current route without triggering a rate/checkpoint boundary.
- `not_found` must be handled separately from WAF/rate-limit boundaries.
- Resume behavior must be manifest-driven because partial files, smoke files, and full-run files can coexist in the output folder.

This does not promote any CaseResult, disclosure status, PublicDemo readiness, or final absence classification.

---

## 8. Remaining Risks And Next Actions

Remaining risks:

- DOM extraction may be capped at 100 visible stream rows per channel.
- The 14 `not_found` channels need separate reconciliation before being treated as true source absence.
- The `short_rows` channel should be reviewed before downstream cohort trend analysis.

Next actions:

1. Decide whether 100-row DOM extraction is sufficient for §5.6/§5.7 or whether CSV/API/pagination extraction is required.
2. Reconcile the 14 `not_found` targets against current channel URLs or cohort membership source.
3. If proceeding to analysis, read `_collection_manifest_full_6c6s.json` first and use its `date_range`, `target_summary`, `successes`, and `errors` fields as the run ledger.
