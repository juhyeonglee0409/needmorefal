# 구비바 §4 — v3 구현 프롬프트

> **From**: CC
> **To**: Codex (Arthur)
> **Date**: 2026-06-15
> **Subject**: collect_30d_browser.js v2 → v3 업그레이드 지시서

---

## 대상 파일

```
D:\Codex_Workspace\Streamer Consulting Project\구비바_케이스\work\step4_cohort_collect_prep\scripts\collect_30d_browser.js
```

현재 v2, 588줄. v3로 업그레이드.

---

## 배경

Cowork 실측: SOFTC.ONE에서 custom date range (2024-01-01 ~ 2026-06-15) 설정 시:
- URL 파라미터: `?startDateTime=2023-12-31T15:00:00.000Z&endDateTime=2026-06-15T14:59:59.999Z`
- RSC payload가 **2,000채널**을 프리로드 (DOM에는 100채널만 표시)
- Peak 10-50 밴드: 첫 2,000채널에서 965건, 전체 추정 3,000-5,000+
- RSC 필드명이 프리셋(7일/30일)과 custom range에서 **다름**:
  - 프리셋: `peakViewers`, `avgViewers`
  - custom: `maxLiveViews`, `avgLiveViews`

---

## 변경 사항 (6건)

### 변경 1: 버전 헤더 (L1-19)

```
v2 → v3. 헤더 코멘트에 반영:
- "30-Day Collection Script v2" → "Collection Script v3 (full-history support)"
- Phase 1 설명에 "scanFromRSC() — RSC 직접 파싱 (primary)" 추가
```

### 변경 2: CONFIG 확장 (L24-36)

현재:
```javascript
downloadPrefix: 'gubiba_30d'
```

변경:
```javascript
dateRange: { start: null, end: null },
downloadPrefix: 'gubiba_30d'
```

`downloadPrefix` getter 함수 추가 (CONFIG 블록 바로 아래):
```javascript
function getDownloadPrefix() {
  if (CONFIG.dateRange.start && CONFIG.dateRange.end) {
    var s = CONFIG.dateRange.start.replace(/-/g, '').substring(0, 8);
    var e = CONFIG.dateRange.end.replace(/-/g, '').substring(0, 8);
    return 'gubiba_' + s + '_' + e;
  }
  return CONFIG.downloadPrefix;
}
```

`downloadPrefix`를 직접 참조하는 모든 곳을 `getDownloadPrefix()`로 교체:
- `downloadAll()` (L362): `CONFIG.downloadPrefix + '_full.csv'` → `getDownloadPrefix() + '_full.csv'`
- `downloadChunks()` (L376): 동일 패턴
- `downloadTimeSeries()` (L456): 동일 패턴

### 변경 3: scanFromRSC() 신규 (Phase 1 primary)

`applyPeakFilter()` 직후 (L188 부근), Phase 2 직전에 삽입.

```javascript
// =========================================================
//  PHASE 1-B: RSC DIRECT PARSE
//  2,000ch/load — DOM scan의 20배 효율
//  RSC 필드명 이원화: preset(peakViewers) vs custom(maxLiveViews)
// =========================================================

function scanFromRSC() {
  var html = document.documentElement.innerHTML;
  var added = 0;
  var seen = new Set(state.rankingChannels.map(function(c) { return c.channelId; }));

  // 채널 URL 패턴으로 channelId 추출 — 이건 모든 모드에서 동일
  var linkPattern = /\/channel\/(naverchzzk|soop)\/([a-f0-9]{20,})/g;
  var channelIds = [];
  var linkMatch;
  while ((linkMatch = linkPattern.exec(html)) !== null) {
    var platform = linkMatch[1];
    var cid = linkMatch[2];
    if (!seen.has(cid)) {
      channelIds.push({ platform: platform, channelId: cid, index: linkMatch.index });
      seen.add(cid);
    }
  }

  // hydration dedup: RSC payload가 서버/클라이언트 2회 반복
  channelIds = channelIds.slice(0, Math.ceil(channelIds.length / 2));

  // 각 채널 주변 텍스트에서 뷰어십 데이터 추출
  channelIds.forEach(function(entry) {
    var start = Math.max(0, entry.index - 300);
    var end = Math.min(html.length, entry.index + 600);
    var block = html.substring(start, end);

    // 이원화 대응: peakViewers (프리셋) || maxLiveViews (custom)
    var peakMatch = block.match(/\\"(?:peakViewers|maxLiveViews)\\":(\d+)/);
    var avgMatch = block.match(/\\"(?:avgViewers|avgLiveViews)\\":(\d+)/);
    var viewershipMatch = block.match(/\\"viewership\\":(\d+)/);
    var hoursMatch = block.match(/\\"(?:streamHours|airTime|totalStreamHours)\\":([\d.]+)/);
    var nameMatch = block.match(/\\"(?:name|channelName)\\":\\"([^\\]+)\\"/);

    var peak = peakMatch ? parseInt(peakMatch[1]) : null;
    var ch = {
      name: nameMatch ? nameMatch[1] : '',
      platform: entry.platform,
      channelId: entry.channelId,
      rank: null,
      stream_hours: hoursMatch ? parseFloat(hoursMatch[1]) : null,
      peak_viewers: peak,
      avg_viewers: avgMatch ? parseInt(avgMatch[1]) : null,
      viewership: viewershipMatch ? parseInt(viewershipMatch[1]) : null,
      band: bandLabel(peak),
      _source: 'rsc'
    };

    state.rankingChannels.push(ch);
    added++;
  });

  state.stats.scanned = state.rankingChannels.length;
  log('RSC scan: +' + added + ' channels (total ' + state.stats.scanned + ')');
  return {
    added: added,
    total: state.stats.scanned,
    method: 'rsc',
    note: added === 0 ? 'RSC에서 채널 미발견. scanCurrentPage()로 fallback.' : null
  };
}
```

**주의사항:**
- `channelId` 필드명: URL 패턴(`/channel/platform/id`)으로 추출하므로 RSC 내부 필드명(`channelId` vs `chzzkId`)에 의존하지 않음. 안전.
- `name` 필드: `name` 또는 `channelName` 패턴 시도. 매칭 실패 시 빈 문자열 (enrichment에서 보충됨).
- `_source: 'rsc'` 태그: DOM scan과 구분용.
- hydration dedup: 전체 channelId 배열에 `slice(0, ceil/2)` 적용.

### 변경 4: diagnoseDOM() 강화 (L473-508)

현재 "지난 N일" 버튼만 감지. 추가:

집계 윈도우 감지 블록 뒤에 (L495 직후) 삽입:

```javascript
    // custom date range 감지: URL 파라미터 또는 날짜 텍스트
    var urlParams = new URLSearchParams(window.location.search);
    var urlStart = urlParams.get('startDateTime');
    var urlEnd = urlParams.get('endDateTime');
    if (urlStart && urlEnd) {
      activeWindow = 'custom:' + urlStart.substring(0, 10) + '~' + urlEnd.substring(0, 10);
    }

    // 날짜 범위 텍스트 감지 (달력 UI 표시)
    if (!activeWindow || activeWindow === 'unknown') {
      var allText = document.body.innerText;
      var dateRangeMatch = allText.match(/(\d{4})\.\s*(\d{2})\.\s*(\d{2})\s*[–-]\s*(\d{4})\.\s*(\d{2})\.\s*(\d{2})/);
      if (dateRangeMatch) {
        activeWindow = 'custom:' + dateRangeMatch[1] + '-' + dateRangeMatch[2] + '-' + dateRangeMatch[3] +
          '~' + dateRangeMatch[4] + '-' + dateRangeMatch[5] + '-' + dateRangeMatch[6];
      }
    }
```

return 객체에 추가:
```javascript
    urlDateRange: urlStart ? { start: urlStart, end: urlEnd } : null
```

### 변경 5: resume() 신규

`abort()` 바로 아래에 삽입:

```javascript
  function resume() {
    if (!state.aborted && state.phase !== 'aborted') {
      return { error: 'not aborted. use startEnrichment() for first run.' };
    }
    var enrichedIds = new Set(state.enrichedRecords.map(function(r) { return r.channelId; }));
    var remaining = state.filteredChannels.filter(function(ch) {
      return !enrichedIds.has(ch.channelId);
    });
    if (remaining.length === 0) {
      return { error: 'all filtered channels already enriched', enriched: state.enrichedRecords.length };
    }

    // 재개 준비: abort 플래그 리셋, 잔여 큐만 재실행
    state.aborted = false;
    state.phase = 'enriching';
    var total = remaining.length;
    log('Resume: ' + total + ' remaining (' + state.stats.enriched + ' already done)');

    var queue = remaining.slice();
    var processed = 0;

    async function worker(wid) {
      while (queue.length > 0) {
        if (state.aborted) { log('Worker ' + wid + ' aborted'); return; }
        var ch = queue.shift();
        if (!ch) break;
        processed++;
        try {
          var enriched = await enrichChannel(ch);
          var gg = classifyGG(enriched);
          enriched.is_general_game = gg.is_gg;
          enriched.gg_reason = gg.reason;
          enriched.exclude_reason = '';
          enriched.band = bandLabel(enriched.peak_viewers);
          enriched.collected_at = new Date().toISOString();
          state.enrichedRecords.push(enriched);
          state.stats.enriched++;
          state.stats.classified++;
        } catch (e) {
          state.errors.push({ channelId: ch.channelId, error: e.message });
        }
        if (processed % 20 === 0 || processed === total) {
          log('Resume ' + processed + '/' + total + ' (total ok=' + state.stats.enriched + ')');
        }
        await delay(CONFIG.enrichDelayMs);
      }
    }

    var stagger = Math.round(CONFIG.enrichDelayMs / CONFIG.workers);
    var workers = [];
    for (var w = 0; w < CONFIG.workers; w++) {
      (function(wid) {
        workers.push(delay(wid * stagger).then(function() { return worker(wid); }));
      })(w);
    }

    Promise.all(workers).then(function() {
      state.phase = state.aborted ? 'aborted' : 'done';
      log(state.phase + '. total enriched=' + state.stats.enriched + ', errors=' + state.errors.length);
    });

    return { resuming: total, alreadyDone: state.stats.enriched };
  }
```

**startEnrichment()와의 차이**: resume()은 enrichedRecords를 초기화하지 않고, 이미 처리된 channelId를 건너뛴다. Promise를 반환하지 않고 fire-and-forget (비동기 실행 중 getStatus()로 모니터링).

### 변경 6: API 노출 + 사용법 로그 (L536-587)

API 객체에 추가:
```javascript
    // Phase 1: Ranking
    scanCurrentPage: scanCurrentPage,
    scanFromRSC: scanFromRSC,          // 추가
    applyPeakFilter: applyPeakFilter,

    // Phase 2: Enrichment
    startEnrichment: startEnrichment,
    abort: abort,
    resume: resume,                     // 추가
```

사용법 로그 교체:
```javascript
  log('v3 loaded. API: window.__GUBIBA_API');
  log('');
  log('=== Workflow ===');
  log('0. 종합 게임 ranking 페이지, custom date range 또는 "지난 30일" 선택');
  log('1. diagnoseDOM()            → DOM + 집계 윈도우 + URL 파라미터 확인');
  log('2. scanFromRSC()            → RSC 직접 파싱 (2,000ch/load, primary)');
  log('   scanCurrentPage()        → DOM 추출 (100ch/page, fallback)');
  log('3. applyPeakFilter()        → peak band 필터');
  log('4. startEnrichment()        → detail fetch + classify');
  log('   abort()                  → 진행 중 중단');
  log('   resume()                 → abort 후 재개');
  log('5. downloadAll()            → CSV Blob download (primary)');
  log('   downloadTimeSeries()     → 시계열 JSONL download');
  log('   getNext()                → micro-chunk fallback');
  log('');
  log('=== Config ===');
  log('setConfig("dateRange", {start:"2024-01-01", end:"2026-06-15"})');
  log('  → downloadPrefix가 "gubiba_20240101_20260615"로 자동 전환');
  log('');
  log('=== Diagnostics ===');
  log('getStatus()    → phase, stats, aborted, config');
  log('getErrors()    → 최근 에러 20건');
  log('');
  log('=== I/O Path ===');
  log('Primary:  downloadAll() → Downloads → CLI pickup_downloads.ps1');
  log('TimeSeries: downloadTimeSeries() → JSONL (§5 진단용)');
  log('Fallback: getNext() × N → JS output ~8건씩 → Cowork append');
```

---

## 변경하지 않는 것

| 항목 | 이유 |
|------|------|
| `classifyGG()` | discovery pass 검증 완료본. 변경 불요. |
| `parseDetailRSC()` | 상세 페이지 전용. `maxLiveViews` 단일 패턴 유지 (상세 페이지에서는 모드 무관 동일). |
| `fetchSafe()` | backoff 로직 정상. |
| `triggerDownload()` / BOM | 실증 패턴 그대로. |
| `getNext()` / micro-chunk | MICRO_SIZE=8, full channelId. 변경 불요. |
| `verify_cohort_v2.js` | 이번 세션에서 이미 하드코딩 제거 완료. |
| `pickup_downloads.ps1` | prefix가 동적으로 바뀌면 `gubiba_*` glob 패턴 조정 필요할 수 있으나, v3 구현 후 실측에서 판단. |

---

## 테스트 기준

### diagnoseDOM() 출력 예시 (custom range)
```json
{
  "links": 100,
  "href": "/channel/naverchzzk/abc123...",
  "aggregationWindow": "custom:2024-01-01~2026-06-15",
  "windowOptions": ["지난 7일", "지난 30일", "지난 90일"],
  "urlDateRange": {
    "start": "2023-12-31T15:00:00.000Z",
    "end": "2026-06-15T14:59:59.999Z"
  }
}
```

### scanFromRSC() 출력 예시
```json
{
  "added": 1847,
  "total": 1847,
  "method": "rsc",
  "note": null
}
```
- `added > 100`이면 RSC 파싱 성공 (DOM은 100/page)
- `added === 0`이면 RSC 구조 변경됨 → `scanCurrentPage()` fallback 사용

### resume() 출력 예시
```json
{
  "resuming": 342,
  "alreadyDone": 623
}
```
- `resuming + alreadyDone ≈ filteredChannels.length`

---

## 실행 순서 (Codex용)

1. 파일 읽기
2. 변경 1-6 순차 적용
3. 문법 검증: IIFE 구조, var 선언 (ES5), 세미콜론
4. 변경 후 전체 줄 수 확인 (~700줄 예상)
5. 커밋하지 않음 (operator 검토 후)

---

## 제약

- operator 승인 없이 collection approval, disclosure decision, CaseResult promotion, PublicDemo readiness, canonical mutation을 확정하지 않는다.
- 이 스크립트는 공개 API를 인증된 브라우저 세션에서 좁은 범위로 사용한다. 별도 정당화 불요.
- URL 자동 조작 금지. 날짜 범위는 사용자가 수동으로 달력 UI에서 설정.
