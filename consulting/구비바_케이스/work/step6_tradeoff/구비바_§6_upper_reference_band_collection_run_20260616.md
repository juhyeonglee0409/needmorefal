# 구비바 §6 Upper Reference Band Collection Run

Date: 2026-06-16

## Purpose

§6 목표 트레이드오프 정량화를 위해 기존 §4 peer cohort와 분리된 10k+ 상위 참조 밴드를 수집했다.

이 데이터는 peer 비교용이 아니라 "목표 도달 지점의 풍경" 확인용이다.

## Scope

- Platform: CHZZK (`naverchzzk`)
- Source: SOFTC.ONE browser-session route
- Date range: full available range used in prior §5 collection
  - UI-equivalent range: `2023-10-02` to `2026-06-16`
  - Query bounds: `2023-10-01T15:00:00.000Z` to `2026-06-16T14:59:59.999Z`
- Included rows: follower >= 10,000 and either general-game or virtual by existing T1/T2-style heuristic.
- Excluded: non-general-game/non-virtual, too-new under 8 weeks, org/team heuristic.

## Route

Direct HTTP fetch to `https://viewership.softc.one/ranking/followers?platform=naverchzzk` returned HTTP 429/checkpoint.

Fresh nodriver profile also reached checkpoint.

The working route was nodriver + existing approved browser profile:

```text
work/step4_cohort_collect_prep/.pw_profile
```

No cookies, localStorage, sessionStorage, auth headers, raw HTML, or screenshots were read or persisted.

## Scripts

Created:

```text
work/step6_tradeoff/scripts/probe_followers_ranking_fetch.mjs
work/step6_tradeoff/scripts/probe_upper_band_followers_nodriver.py
work/step6_tradeoff/scripts/collect_upper_band_reference_nodriver.py
```

Important collector safeguards added during run:

- `--use-existing-candidates` to avoid rescanning ranking pages.
- Browser `fetch` timeout for detail pages.
- Per-candidate progress NDJSON.
- Per-candidate CSV/notes flush.
- `--append-existing-output` for band 보강 without losing prior rows.
- `--detail-bands` for focused 10k-20k append.

## Candidate Scan

Candidate pool:

```text
data/cohort/collected/_upper_band_candidates.json
```

Candidate scan scope:

- follower ranking pages: `1-25`
- virtual ranking pages: `1-4`

Candidate count:

```text
687 total
633 followers source
54 virtual_ranking source
279 in 10k-20k
197 in 20k-50k
157 in 50k+
```

## Detail Collection

Final output:

```text
data/cohort/collected/cohort_ref_upper_band.csv
data/cohort/collected/cohort_ref_upper_band_notes.csv
data/cohort/collected/collection_logs/_upper_band_detail_progress.ndjson
data/cohort/collected/collection_logs/_upper_band_detail_records.json
data/cohort/collected/collection_logs/_upper_band_collection_manifest.json
```

Detail runs:

1. Smoke: 20 candidates, 9 accepted. This exposed a detail-name parser issue (`Next.MetadataOutlet`), fixed by preferring ranking candidate name.
2. Balanced detail run: 80 candidates, 46 accepted.
3. Focused append: 10k-20k only, 60 candidates, final accepted count 67.
4. Full extension: 687/687 candidate detail attempts completed in <=100-candidate chunks.
5. A mid-run local CSV write interruption left 53 raw detail records missing; those records were backfilled records-only without changing CSV/notes.

Final row distribution:

```text
687 candidates detail-attempted
271 accepted rows total
10k-20k: 88
20k-50k: 94
50k+: 89
general_game true: 144
virtual true: 161
duplicates: 0
required metric missing: 0
schema match: true
detail_records: 687
```

Notes:

```text
416 notes total
349 excluded: not_general_game_or_virtual
54 excluded: follower_below_10k
7 excluded: excluded_org_or_team_heuristic
6 excluded: too_new_under_8_weeks
```

## Preliminary §6 Read

This is a quick descriptive read, not final judgment.

`avg_median >= 200`:

```text
10k-20k: 28/88
20k-50k: 63/94
50k+: 87/89
```

Median `avg_median` by band:

```text
10k-20k: 138.5
20k-50k: 296.5
50k+: 1008.0
```

The 10k follower target is plausibly in the zone where avg_median 200 appears, but distribution is mixed and heavily dependent on category/virtual/general-game composition. Use row-level data for final §6 tradeoff analysis.

## Caveats

- This is a reference band, not a peer cohort.
- Candidate provenance is documented here: the 687-candidate pool came from follower pages 1-25 plus virtual pages 1-4.
- The final manifest includes `final_validation`; use that block for current coverage and row counts.
- SOFTC.ONE checkpoint requires browser-profile route; direct fetch is not stable.
- Large-channel peak values include collab/event/raid spikes. This is expected; use `peak_median`, `peak_p95`, and `avg_median` alongside `peak_max`.
- No cookies, localStorage, sessionStorage, auth headers, raw HTML, or screenshots were persisted during the full extension.
