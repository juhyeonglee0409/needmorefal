# 구비바 §8 Layer A/C 방송기록 수집 런노트

Generated: 2026-06-20

## Scope

- Purpose: 구비바 582건 방송 분석에서 발견한 카테고리 효과와 방송길이 효과를 Layer A/C 샘플에서 교차검증하기 위한 방송별 기록 수집
- Source: `https://viewership.softc.one/channel/naverchzzk/{channelId}/streams`
- Date range: `2023-10-01T15:00:00.000Z` to `2026-06-15T14:59:59.999Z`
- Target file: `work/step8_layer_ac_broadcasts/layer_ac_broadcast_targets_20260620.json`
- Target count: 44 total
  - Layer A / `LA`: 20
  - Layer C / `LC`: 24

## Route

- Initial CDP smoke with existing `.pw_profile` hit `429`; no repeated CDP retry.
- Initial nodriver smoke with the same profile hit `checkpoint`.
- Final route: `nodriver_dom_browser` + existing approved `.pw_profile` + visible browser checkpoint wait.
- Collection chunks were limited to 10 targets or fewer and used `skip-existing` plus progress-based skip to avoid retrying previous `not_found` records.
- No raw HTML, cookies, tokens, localStorage, sessionStorage, auth headers, or screenshots were saved.

## Result

| Metric | Value |
|---|---:|
| Targets | 44 |
| Terminal channel count | 44 |
| CSV count | 42 |
| CSV count with >=20 rows | 41 |
| LA CSV | 19 |
| LC CSV | 23 |
| Total broadcast rows | 4,038 |
| Schema mismatches | 0 |
| Final unprocessed | 0 |
| Final boundary signal | null |

Short CSV:

| Group | Channel | channelId | Rows |
|---|---|---|---:|
| LA | 쿠온 레이 Planeta | `59aa824e4c4a56dd51e7a5e2e9172648` | 18 |

Final errors:

| Group | Channel | channelId | Error |
|---|---|---|---|
| LA | 부쿠키 | `f2fd35b4bce38e375cd77b6a6904b4a4` | `not_found` |
| LC | 김네네 | `107b9e4102fb92e546a3aff932babea0` | `not_found` |

## Outputs

- `data/cohort/collected/broadcast_samples/LA/*.csv`
- `data/cohort/collected/broadcast_samples/LC/*.csv`
- `data/cohort/collected/broadcast_samples/_collection_manifest_layer_ac.json`
- `data/cohort/collected/broadcast_samples/_collection_errors_layer_ac.csv`
- `data/cohort/collected/broadcast_samples/_collection_progress_layer_ac.ndjson`

Chunk/preflight manifests are retained under `data/cohort/collected/broadcast_samples/` with `_collection_*_layer_ac_nodriver_*` names.

## Implementation Notes

- `collect_step5_broadcasts_cdp_parallel.mjs` now supports `--target-file` for non-T1/T2 target sets.
- `collect_step5_broadcasts_nodriver.py` now supports:
  - `--target-file`
  - `--profile-dir`
  - full-range query parameters
  - manual checkpoint wait
  - progress-based skip for already collected/error targets
- `layer_ac_broadcast_targets_20260620.json` stores the operator-provided 44-channel LA/LC target list.

## Residual Risk

- SOFTC.ONE `/streams` DOM extraction still has a 100-row display cap risk. 100 rows should be treated as "captured visible full-range page rows", not proof that the channel only has 100 broadcasts.
- One valid CSV has only 18 rows, below the requested 20-row threshold. The overall completion threshold remains satisfied because 41 CSV files have at least 20 rows.
- `not_found` records are preserved as collection errors, not canonical absence judgments.
- CaseResult, disclosure, promotion, and canonical state were not changed.
