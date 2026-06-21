# 구비바 §4 — v3 loadIds 구현 프롬프트

> **From**: CC
> **To**: Codex (Arthur)
> **Date**: 2026-06-15
> **Subject**: collect_30d_browser.js v3에 ID 로딩 + enrichment 기능 추가, 병합 스크립트 생성

---

## 배경

Cowork이 SOFTC.ONE 멀티페이지 RSC 스캔으로 **5,679개 peak 10-50 채널 ID**를 확보했다.
이 ID들을 `gubiba_multipage_scan_ids.json`으로 저장했다.

**Node.js CLI 스크립트로 enrichment 하는 것은 불가능하다.**
- Node.js가 시스템에 설치되어 있지 않다.
- 설치되어 있어도 SOFTC.ONE은 Vercel JS challenge로 비브라우저 요청을 차단한다.
- 따라서 enrichment는 반드시 브라우저 인증 세션에서 실행해야 한다.

**대안**: 기존 v3 브라우저 스크립트(`collect_30d_browser.js`)에 `loadIds()` 함수를 추가하여,
사전 스캔된 ID 목록을 로드 → 기존 enrichment 파이프라인(`startEnrichment()`) 실행.

---

## 대상 파일

### 수정
```
work/step4_cohort_collect_prep/scripts/collect_30d_browser.js  (v3, 765줄)
```

### 신규 생성
```
work/step4_cohort_collect_prep/scripts/merge_enriched.ps1
```

---

## 변경 1: collect_30d_browser.js — loadIds() 함수 추가

`applyPeakFilter()` 바로 아래, `scanFromRSC()` 바로 위에 삽입.

```javascript
// =========================================================
//  ID LOADING — 사전 스캔된 채널 ID를 직접 로드
//  Cowork 멀티페이지 RSC 스캔 결과를 브라우저에 주입
// =========================================================

function loadIds(input) {
  var channels = [];

  // 포맷 자동 감지
  if (Array.isArray(input)) {
    // [{channelId, platform}, ...] 또는 ["id,platform", ...]
    input.forEach(function(item) {
      if (typeof item === 'string') {
        var parts = item.split(',');
        if (parts.length >= 2) {
          channels.push({ channelId: parts[0].trim(), platform: parts[1].trim() });
        }
      } else if (item && item.channelId) {
        channels.push({ channelId: item.channelId, platform: item.platform || CONFIG.platform });
      } else if (item && item.id) {
        // "id" 필드에 "hexstring,platform" 형식일 수 있음
        var idParts = String(item.id).split(',');
        if (idParts.length >= 2) {
          channels.push({ channelId: idParts[0].trim(), platform: idParts[1].trim() });
        } else {
          channels.push({ channelId: idParts[0].trim(), platform: CONFIG.platform });
        }
      }
    });
  } else if (input && input.channels) {
    // { channels: [...] } wrapper
    return loadIds(input.channels);
  } else if (input && input.ids) {
    // { ids: [...] } wrapper
    return loadIds(input.ids);
  }

  if (channels.length === 0) {
    return { error: 'no channels parsed from input' };
  }

  // 중복 제거 (이미 rankingChannels에 있는 것 포함)
  var seen = new Set(state.rankingChannels.map(function(c) { return c.channelId; }));
  var added = 0;
  channels.forEach(function(ch) {
    if (seen.has(ch.channelId)) return;
    seen.add(ch.channelId);
    state.rankingChannels.push({
      name: '',
      platform: ch.platform,
      channelId: ch.channelId,
      rank: null,
      stream_hours: null,
      peak_viewers: null,
      avg_viewers: null,
      viewership: null,
      band: '',
      _source: 'loaded'
    });
    added++;
  });

  state.stats.scanned = state.rankingChannels.length;
  log('loadIds: +' + added + ' channels (total ' + state.stats.scanned + ', skipped ' + (channels.length - added) + ' dupes)');
  return { added: added, total: state.stats.scanned, parsed: channels.length };
}

function loadIdsFromUrl(url) {
  log('Fetching IDs from ' + url + '...');
  return fetch(url)
    .then(function(r) { return r.json(); })
    .then(function(data) { return loadIds(data); })
    .catch(function(e) { return { error: e.message }; });
}

function skipFilter() {
  // loadIds로 로드한 채널은 peak 필터를 건너뜀 (이미 필터링됨)
  state.filteredChannels = state.rankingChannels.slice();
  state.stats.filtered = state.filteredChannels.length;
  log('skipFilter: all ' + state.stats.filtered + ' channels passed to enrichment');
  return { filtered: state.stats.filtered };
}
```

### loadIds 설계 근거

- **포맷 자동 감지**: Cowork이 RSC에서 추출한 JSON 포맷이 확정되지 않음. 배열, 문자열 배열, wrapper 객체 모두 대응.
- **`_source: 'loaded'`**: RSC scan/DOM scan과 구분.
- **`skipFilter()`**: 로드된 ID는 이미 peak 10-50 필터링 완료 상태. `applyPeakFilter()` 대신 사용.
- **`loadIdsFromUrl()`**: Python 로컬 서버(`python -m http.server`)에서 JSON 파일을 로드하는 경로.

---

## 변경 2: enrichChannel()에 dateRange 전달 (선택적)

현재 (L335-336):
```javascript
async function enrichChannel(ch) {
  var url = CONFIG.baseUrl + '/channel/' + ch.platform + '/' + ch.channelId;
```

변경:
```javascript
async function enrichChannel(ch) {
  var url = CONFIG.baseUrl + '/channel/' + ch.platform + '/' + ch.channelId;
  if (CONFIG.dateRange.start && CONFIG.dateRange.end) {
    var ds = new Date(CONFIG.dateRange.start + 'T00:00:00+09:00');
    var de = new Date(CONFIG.dateRange.end + 'T23:59:59+09:00');
    url += '?start=' + CONFIG.dateRange.start + '&end=' + CONFIG.dateRange.end +
      '&startDateTime=' + ds.toISOString().replace('.000Z', '.000Z') +
      '&endDateTime=' + de.toISOString().replace('.000Z', '.000Z');
  }
```

이렇게 하면 `setConfig("dateRange", {start:"2024-01-01", end:"2026-06-15"})` 설정 시 detail 페이지도 full-history 기간으로 요청된다.

---

## 변경 3: API 노출 + 사용법 로그

API 객체에 추가:
```javascript
    // Phase 1: Ranking
    scanCurrentPage: scanCurrentPage,
    scanFromRSC: scanFromRSC,
    loadIds: loadIds,              // 추가
    loadIdsFromUrl: loadIdsFromUrl, // 추가
    applyPeakFilter: applyPeakFilter,
    skipFilter: skipFilter,         // 추가
```

사용법 로그에 추가 (기존 workflow 뒤에):
```javascript
  log('');
  log('=== ID Loading (멀티페이지 스캔 결과 주입) ===');
  log('loadIds([...])            → 채널 ID 배열 직접 로드');
  log('loadIdsFromUrl(url)       → URL에서 JSON 파일 로드');
  log('skipFilter()              → 이미 필터링된 ID는 peak 필터 건너뛰기');
  log('');
  log('=== Multi-Page Enrichment Workflow ===');
  log('1. setConfig("dateRange", {start:"2024-01-01", end:"2026-06-15"})');
  log('2. setConfig("workers", 2); setConfig("enrichDelayMs", 3000)');
  log('3. loadIds(data) 또는 loadIdsFromUrl("http://localhost:8080/ids.json")');
  log('4. skipFilter()');
  log('5. startEnrichment()');
  log('6. downloadAll()');
```

---

## 신규 파일: merge_enriched.ps1

```
work/step4_cohort_collect_prep/scripts/merge_enriched.ps1
```

기존 965건 CSV + 신규 enrichment CSV를 channelId 기준으로 병합/중복 제거.

```powershell
# 구비바 §4 — 다회차 enrichment 병합
#
# 여러 enrichment 라운드의 CSV를 channelId 기준으로 병합.
# 동일 channelId가 양쪽에 있으면 나중 것(신규)을 우선.

param(
    [Parameter(Mandatory=$true)]
    [string[]]$InputFiles,
    [string]$OutFile = "gubiba_enriched_merged.csv"
)

$allRows = @{}
$header = $null

foreach ($file in $InputFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "[merge] SKIP: $file not found"
        continue
    }
    $csv = Import-Csv $file
    if (-not $header -and $csv.Count -gt 0) {
        $header = ($csv[0].PSObject.Properties | ForEach-Object { $_.Name }) -join ','
    }
    foreach ($row in $csv) {
        $allRows[$row.channelId] = $row
    }
    Write-Host "[merge] $file : $($csv.Count) rows loaded"
}

$merged = $allRows.Values | Sort-Object { [int]$_.peak_viewers } -Descending
$merged | Export-Csv -Path $OutFile -NoTypeInformation -Encoding utf8
Write-Host "[merge] Output: $OutFile ($($merged.Count) unique rows)"

# 검증
$platforms = ($merged | Select-Object -ExpandProperty platform -Unique) -join ', '
$peaks = $merged | ForEach-Object { [int]$_.peak_viewers }
$ggDist = $merged | Group-Object is_general_game | ForEach-Object { "$($_.Name)=$($_.Count)" }
Write-Host "[verify] Platforms: $platforms"
Write-Host "[verify] Peak range: $($peaks | Measure-Object -Minimum | Select-Object -ExpandProperty Minimum)-$($peaks | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum)"
Write-Host "[verify] is_general_game: $($ggDist -join ', ')"
```

사용법:
```powershell
.\merge_enriched.ps1 -InputFiles @(
  "data\cohort\collected\gubiba_20240101_20260615_enriched_965.csv",
  "data\cohort\collected\gubiba_20240101_20260615_enriched_round2.csv"
) -OutFile "data\cohort\collected\gubiba_enriched_final.csv"
```

---

## 변경하지 않는 것

| 항목 | 이유 |
|------|------|
| `parseDetailRSC()` | 상세 페이지 RSC 파싱. 변경 불요. |
| `classifyGG()` | 분류 규칙 검증 완료. 변경 불요. |
| `downloadAll()` / Blob export | 작동 확인됨. 변경 불요. |
| `resume()` | abort 후 재개. 변경 불요. |
| `verify_cohort_v2.js` | 구조 검증 스크립트. 이미 하드코딩 제거됨. 변경 불요. |
| `enrich_from_ids.js` | 생성하지 않음. Node.js 미설치 + Vercel 차단. |

---

## 실행 계획 (Cowork + CC 역할 분담)

### Cowork (브라우저)
1. `softc.one` 접속 (인증 세션)
2. v3 스크립트 주입
3. `setConfig("dateRange", {start:"2024-01-01", end:"2026-06-15"})`
4. `setConfig("workers", 2); setConfig("enrichDelayMs", 3000)`
5. ID 로딩: 콘솔에 JSON 붙여넣기 또는 `loadIdsFromUrl()`
6. `skipFilter()` → `startEnrichment()`
7. 완료 후 `downloadAll()`, `downloadTimeSeries()`

### CC/Codex (CLI)
1. `pickup_downloads.ps1`로 Downloads → collected 이동
2. `merge_enriched.ps1`로 병합
3. `verify_cohort_v2.js` (PowerShell Import-Csv로) 검증
4. 커밋

---

## 제약

- operator 승인 없이 collection approval, disclosure decision, CaseResult promotion, PublicDemo readiness, canonical mutation을 확정하지 않는다.
- 이 스크립트는 공개 API를 인증된 브라우저 세션에서 좁은 범위로 사용한다. 별도 정당화 불요.
- URL 자동 조작 금지. 날짜 범위는 사용자가 수동으로 설정.
