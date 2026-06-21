# 구비바 §4 — CC Handoff v2: Multi-Page Enrichment

## Summary

Hosea가 SOFTC.ONE 멀티페이지 RSC 스캔으로 **5,679개 peak 10-50 채널 ID**를 확보했다. 기존 enrichment 완료분 965개를 제외하면 **~4,714개**가 신규 enrichment 대상이다.

---

## What Hosea Did (Cowork Session 2026-06-14~15)

### Phase 1: Initial Collection (965 channels)
1. SOFTC.ONE 종합 게임 ranking, full-history (2024-01-01 → 2026-06-15)
2. 단일 페이지 RSC 스캔 → 2,000 channels → peak 10-50 필터 → 965
3. 965 channels enrichment 완료 (follower + categories + timeseries + GG classification)
4. 결과: `data/cohort/collected/gubiba_20240101_20260615_enriched_965.csv` (965 rows, 21 columns)
5. 시계열: `data/cohort/collected/gubiba_20240101_20260615_timeseries_965.jsonl` (957 records)

### Phase 2: Multi-Page RSC Discovery
**핵심 발견**: SOFTC.ONE의 `page=N` URL 파라미터가 다른 값일 때, RSC가 **서로 다른 2,000개 채널**을 프리로드한다. 5개 페이지 위치를 스캔하여 zero overlap으로 ~10,000개 채널을 커버했다.

| Page Position | RSC Channels | Peak 10-50 | New Unique IDs |
|---|---|---|---|
| p75 | ~1,116 | 1,086 | 1,086 |
| p100 | ~906 | 886 | 886 |
| p50 | ~1,389 | 1,308 | 1,308 |
| p25 | ~1,634 | 1,434 | 1,434 |
| p1 | ~1,899 | 965 | 965 |
| **Total** | **~6,944** | **5,679** | **5,679** |

결과: `gubiba_multipage_scan_ids.json` (사용자 Downloads 폴더)

---

## Files Layout

```
구비바_케이스/
├── data/cohort/
│   ├── collected/
│   │   ├── gubiba_20240101_20260615_enriched_965.csv      ← 기존 enrichment (965ch)
│   │   ├── gubiba_20240101_20260615_timeseries_965.jsonl   ← 기존 시계열 (957ch)
│   │   └── gubiba_multipage_scan_ids.json                  ← ⚠️ 사용자가 Downloads에서 옮겨야 함
│   └── specs/
│       └── 구비바_§4_cohort_spec_v2_20260610.json
└── work/step4_cohort_collect_prep/
    └── scripts/
        ├── enrich_from_ids.js       ← CC용 Node.js enrichment 스크립트 (NEW)
        ├── collect_30d_browser.js    ← 브라우저용 v3 스크립트 (reference)
        ├── verify_cohort_v2.js       ← 검증 스크립트
        └── pickup_downloads.ps1     ← PowerShell pickup
```

---

## Task for CC

### Step 0: File Setup
사용자에게 `gubiba_multipage_scan_ids.json`을 Downloads에서 `data/cohort/collected/`로 옮기도록 안내.

### Step 1: Run Enrichment
```bash
cd "구비바_케이스/data/cohort/collected"
node "../../work/step4_cohort_collect_prep/scripts/enrich_from_ids.js" \
  --ids gubiba_multipage_scan_ids.json \
  --existing gubiba_20240101_20260615_enriched_965.csv \
  --out-dir . \
  --workers 2 \
  --delay-ms 3000
```

**예상 소요**: ~4,714 channels × 3s / 2 workers ≈ 118분 (2시간)

**Checkpoint/Resume**: 중단 시 `enrich_checkpoint.json`이 자동 생성됨. 같은 명령 재실행하면 완료분 건너뛰고 이어서 진행.

**Rate limit 대응**: 
- 429/403 발생 시 60초 자동 backoff (3회 재시도)
- Vercel Security Checkpoint이 뜰 경우 → 브라우저에서 `viewership.softc.one` 방문하여 체크포인트 해제 후 스크립트 재시작

### Step 2: Merge & Deduplicate
enrichment 완료 후 기존 965개 + 신규 ~4,714개를 병합:

```bash
# 기존 CSV에서 header 제거 후 신규 뒤에 append
tail -n +2 gubiba_20240101_20260615_enriched_965.csv >> gubiba_enriched_multipage.csv

# 또는 별도 merge 스크립트로 channelId 기준 deduplicate
```

**주의**: 기존 965개의 peak/avg/hours/viewership은 **ranking RSC** 기준이고, 신규는 **channel detail timeseries** 기준으로 계산됨. 값이 약간 다를 수 있음. 일관성을 위해 기존 965개도 재enrichment 할지 결정 필요.

### Step 3: Validate
```bash
node "../../work/step4_cohort_collect_prep/scripts/verify_cohort_v2.js"
```

### Step 4: Final Output
- 병합된 CSV → `cohort_general_game_population_normalized.csv`로 정규화
- 시계열 JSONL 병합 → §5 진단용

---

## Technical Notes

### RSC Parsing Pattern (Cowork 실측 검증 완료)
- Channel ID: `\"id\":\"([a-f0-9]{20,}),(naverchzzk|soop)\"`
- Follower: `\"followerCount\":(\d+)` — 마지막 매치가 최신값
- Categories: `\"category\":\"([^\\]+)\",\"sumLiveViews\":\d+,\"viewership\":(\d+)`
- Timeseries: `\"maxLiveViews\":(\d+)`, `\"avgLiveViews\":(\d+)`, `\"airTime\":(\d+)`
- Hydration dedup: 모든 배열값을 절반으로 잘라야 함 (서버/클라이언트 2회 반복)

### Channel Detail Page URL Format
```
https://viewership.softc.one/channel/naverchzzk/{channelId}?start=2024-01-01&end=2026-06-15&startDateTime=2023-12-31T15:00:00.000Z&endDateTime=2026-06-14T14:59:59.000Z
```

### GG Classification Rules (v3 검증 완료)
1. category_1 = "종합 게임" or "종합게임" → true (gg_primary)
2. category_1 = "talk" && share ≥ 50% → false (talk_primary)
3. category_1 share ≥ 80% → false (single_game_dominant)
4. non-talk/non-art categories with share ≥ 15%, count ≥ 2 → true (multi_game)
5. category_2 = "종합 게임" && share ≥ 15% → true (gg_secondary)
6. else → false (single_game_or_non_game)
7. no categories → unknown (no_category_data)

### Polite Collection Config
- 2 workers × 3s delay → ~0.67 req/s
- Max retries: 3 (with 60s backoff on 429/403)
- No aggressive retry after block

---

## Expected Final Numbers

| Metric | Count |
|---|---|
| Total unique peak 10-50 IDs | 5,679 + overlap TBD with existing 965 |
| Already enriched | 965 |
| New enrichment needed | ~4,714 |
| Expected enrichment time | ~2 hours |
| Target final CSV rows | ~5,679–6,644 |

---

## Previous Handoff Context
기존 CC handoff: `구비바_§4_CC_handoff_prompt.md` (7일 데이터 기준, superseded)
기존 v3 구현 프롬프트: `구비바_§4_v3_impl_prompt.md`
기존 CC IO supplement: `구비바_§4_CC_IO_supplement.md`
