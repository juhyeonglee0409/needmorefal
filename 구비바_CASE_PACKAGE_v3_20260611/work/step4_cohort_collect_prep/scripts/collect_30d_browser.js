/**
 * 구비바 §4 — Collection Script v3 (full-history support)
 *
 * I/O Architecture:
 *   수집 = 브라우저 fetch (인증 세션)
 *   반출 = Blob download → Downloads 폴더 → CLI pickup
 *   fallback = micro-chunk JS output (10건씩, 1.2KB 이내)
 *
 * 이전 패스 병목: 수집과 반출이 같은 파이프라인이 아니었음.
 * 브라우저 메모리에 80KB 쌓은 뒤 JS tool output(1.2KB 제한)으로
 * 빼려 해서 막힘. 이번엔 Blob download = 화물차 출입구.
 *
 * Phase 1: scanFromRSC()         — RSC 직접 파싱 (primary)
 *          scanCurrentPage()     — ranking DOM 추출 (fallback)
 * Phase 2: startEnrichment()     — detail fetch + classify (자율)
 * Phase 3: downloadAll/Chunks()  — Blob download (primary)
 *          getNext()             — micro-chunk fallback
 *
 * CLI companion: scripts/pickup_downloads.ps1
 */

(function() {
  'use strict';

  // ===== CONFIG =====
  var CONFIG = {
    peakBand: { min: 10, max: 50 },
    platform: 'naverchzzk',
    enrichDelayMs: 1500,
    rankingDelayMs: 2500,
    workers: 3,
    chunkSize: 50,
    maxRetries: 2,
    backoffMs: 30000,
    baseUrl: 'https://viewership.softc.one',
    dateRange: { start: null, end: null },
    downloadPrefix: 'gubiba_30d'
  };

  function getDownloadPrefix() {
    if (CONFIG.dateRange.start && CONFIG.dateRange.end) {
      var s = CONFIG.dateRange.start.replace(/-/g, '').substring(0, 8);
      var e = CONFIG.dateRange.end.replace(/-/g, '').substring(0, 8);
      return 'gubiba_' + s + '_' + e;
    }
    return CONFIG.downloadPrefix;
  }

  // ===== STATE =====
  var state = {
    phase: 'idle',
    aborted: false,
    rankingChannels: [],
    filteredChannels: [],
    enrichedRecords: [],
    errors: [],
    stats: { pages: 0, scanned: 0, filtered: 0, enriched: 0, classified: 0, downloaded: 0 }
  };

  var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };
  var log = function(msg) { console.log('[gubiba] ' + msg); };

  // ===== CSV COLUMNS (discovery pass 검증 완료) =====
  var CSV_COLS = ['name','platform','channelId','rank','stream_hours','peak_viewers',
    'avg_viewers','viewership','follower','band','category_1','category_1_share',
    'category_2','category_2_share','category_3','category_3_share',
    'total_categories','is_general_game','gg_reason','exclude_reason','collected_at'];

  function recordToCSVRow(r) {
    return CSV_COLS.map(function(c) {
      var v = r[c];
      if (v == null) return '';
      v = String(v);
      if (v.indexOf(',') >= 0 || v.indexOf('"') >= 0) return '"' + v.replace(/"/g, '""') + '"';
      return v;
    }).join(',');
  }

  function bandLabel(peak) {
    if (peak == null) return '';
    if (peak <= 15) return '10-15';
    if (peak <= 20) return '16-20';
    if (peak <= 30) return '21-30';
    if (peak <= 40) return '31-40';
    if (peak <= 50) return '41-50';
    if (peak <= 100) return '51-100';
    if (peak <= 200) return '101-200';
    if (peak <= 300) return '201-300';
    return '300+';
  }

  // ===== FETCH WITH RETRY + POLITE BACKOFF =====
  async function fetchSafe(url, retries) {
    retries = retries != null ? retries : CONFIG.maxRetries;
    for (var i = 0; i <= retries; i++) {
      try {
        var res = await fetch(url, { credentials: 'include' });
        if (res.ok) return await res.text();
        if (res.status === 429 || res.status === 403) {
          state.errors.push({ url: url, status: res.status, time: new Date().toISOString() });
          log('BLOCKED ' + res.status + ' — backoff ' + (CONFIG.backoffMs/1000) + 's');
          if (i < retries) { await delay(CONFIG.backoffMs); continue; }
          return null;
        }
        log('HTTP ' + res.status + ': ' + url);
        return null;
      } catch (e) {
        log('Network: ' + e.message);
        if (i < retries) await delay(3000);
        else return null;
      }
    }
    return null;
  }

  // ===== classifyGG (506-row discovery pass: unknown=0) =====
  function classifyGG(row) {
    var c1 = (row.category_1 || '').trim();
    var c1s = parseFloat(row.category_1_share) || 0;
    var c2 = (row.category_2 || '').trim();
    var c2s = parseFloat(row.category_2_share) || 0;
    var c3 = (row.category_3 || '').trim();
    var c3s = parseFloat(row.category_3_share) || 0;
    if (!c1) return { is_gg: 'unknown', reason: 'no_category_data' };
    if (c1 === '종합 게임' || c1 === '종합게임') return { is_gg: 'true', reason: 'gg_primary' };
    if (c1.toLowerCase() === 'talk' && c1s >= 50) return { is_gg: 'false', reason: 'talk_primary' };
    if (c1s >= 80) return { is_gg: 'false', reason: 'single_game_dominant' };
    var nonTalkCats = [[c1, c1s], [c2, c2s], [c3, c3s]].filter(function(pair) {
      return pair[0] && pair[0].toLowerCase() !== 'talk' &&
        pair[0] !== '그림/아트' && pair[0] !== '먹방' && pair[1] >= 15;
    });
    if (nonTalkCats.length >= 2) return { is_gg: 'true', reason: 'multi_game' };
    if ((c2 === '종합 게임' || c2 === '종합게임') && c2s >= 15) return { is_gg: 'true', reason: 'gg_secondary' };
    return { is_gg: 'false', reason: 'single_game_or_non_game' };
  }


  // =========================================================
  //  PHASE 1: RANKING SCAN
  //  Cowork이 페이지마다 호출. DOM → channels.
  // =========================================================

  function scanCurrentPage() {
    var links = document.querySelectorAll('a[href*="/channel/"]');
    var added = 0;
    var seen = new Set(state.rankingChannels.map(function(c) { return c.channelId; }));

    links.forEach(function(link) {
      var href = link.getAttribute('href') || '';
      var m = href.match(/\/channel\/(naverchzzk|soop)\/([a-f0-9]{20,})/);
      if (!m) return;
      if (seen.has(m[2])) return;

      var row = link.closest('tr') ||
        link.closest('[class*="ranking"]') ||
        link.closest('[class*="item"]') ||
        link.parentElement && link.parentElement.parentElement;
      var cells = row ? row.querySelectorAll('td, [class*="cell"], [class*="col"]') : [];
      var textCells = Array.from(cells).map(function(c) { return c.textContent.trim(); });
      var nums = [];
      textCells.forEach(function(t) {
        var n = t.replace(/,/g, '');
        if (/^\d+(\.\d+)?$/.test(n)) nums.push(parseFloat(n));
      });

      var ch = {
        name: link.textContent.trim(),
        platform: m[1],
        channelId: m[2],
        rank: nums[0] || null,
        stream_hours: nums[1] || null,
        peak_viewers: nums[2] != null ? Math.round(nums[2]) : null,
        avg_viewers: nums[3] != null ? Math.round(nums[3]) : null,
        viewership: nums[4] != null ? Math.round(nums[4]) : null,
        _raw_cells: textCells
      };
      ch.band = bandLabel(ch.peak_viewers);
      state.rankingChannels.push(ch);
      seen.add(m[2]);
      added++;
    });

    state.stats.pages++;
    state.stats.scanned = state.rankingChannels.length;
    log('Page ' + state.stats.pages + ': +' + added + ' (total ' + state.stats.scanned + ')');
    return { added: added, total: state.stats.scanned, page: state.stats.pages };
  }

  function applyPeakFilter() {
    state.filteredChannels = state.rankingChannels.filter(function(ch) {
      return ch.peak_viewers != null &&
        ch.peak_viewers >= CONFIG.peakBand.min &&
        ch.peak_viewers <= CONFIG.peakBand.max;
    });
    state.stats.filtered = state.filteredChannels.length;
    log('Filter ' + CONFIG.peakBand.min + '-' + CONFIG.peakBand.max +
      ': ' + state.stats.filtered + '/' + state.stats.scanned);
    return { filtered: state.stats.filtered, total: state.stats.scanned };
  }

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


  // =========================================================
  //  PHASE 2: DETAIL ENRICHMENT
  //  RSC payload → follower + category shares + classify
  // =========================================================

  // RSC payload에서 시계열 배열 추출 + hydration 중복 제거
  function extractTimeSeries(text, fieldName) {
    var pattern = new RegExp('\\\\"' + fieldName + '\\\\":(\\d+)', 'g');
    var values = [];
    var m;
    while ((m = pattern.exec(text)) !== null) {
      values.push(parseInt(m[1]));
    }
    // hydration 중복: 서버/클라이언트 데이터가 2번 반복됨
    if (values.length > 0) {
      values = values.slice(0, Math.ceil(values.length / 2));
    }
    return values;
  }

  function parseDetailRSC(text) {
    // followerCount: lowercase f (Cowork 실측 보정). 마지막 매치 = 최신값.
    var folMatches = [];
    var folPattern = /\\"followerCount\\":(\d+)/g;
    var fm;
    while ((fm = folPattern.exec(text)) !== null) {
      folMatches.push(parseInt(fm[1]));
    }
    var follower = folMatches.length > 0 ? folMatches[folMatches.length - 1] : null;

    // 카테고리별 viewership (핸드오프 regex, Cowork 검증 완료)
    var catPattern = /\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)/g;
    var categories = [];
    var cm;
    while ((cm = catPattern.exec(text)) !== null) {
      categories.push({ name: cm[1], viewership: parseInt(cm[2]) });
    }
    categories.sort(function(a, b) { return b.viewership - a.viewership; });
    var totalVS = categories.reduce(function(s, c) { return s + c.viewership; }, 0);
    function shareOf(idx) {
      if (!categories[idx] || !totalVS) return 0;
      return Math.round(categories[idx].viewership / totalVS * 1000) / 10;
    }

    // 시계열 (24 data points = 6개월 주간, hydration dedup 적용)
    var timeSeries = {
      maxLiveViews: extractTimeSeries(text, 'maxLiveViews'),
      avgLiveViews: extractTimeSeries(text, 'avgLiveViews'),
      airTime: extractTimeSeries(text, 'airTime')
    };

    return {
      follower: follower,
      category_1: categories[0] ? categories[0].name : '',
      category_1_share: shareOf(0),
      category_2: categories[1] ? categories[1].name : '',
      category_2_share: shareOf(1),
      category_3: categories[2] ? categories[2].name : '',
      category_3_share: shareOf(2),
      total_categories: categories.length,
      _timeSeries: timeSeries
    };
  }

  async function enrichChannel(ch) {
    var url = CONFIG.baseUrl + '/channel/' + ch.platform + '/' + ch.channelId;
    if (CONFIG.dateRange.start && CONFIG.dateRange.end) {
      var ds = new Date(CONFIG.dateRange.start + 'T00:00:00+09:00');
      var de = new Date(CONFIG.dateRange.end + 'T23:59:59+09:00');
      url += '?start=' + CONFIG.dateRange.start + '&end=' + CONFIG.dateRange.end +
        '&startDateTime=' + ds.toISOString().replace('.000Z', '.000Z') +
        '&endDateTime=' + de.toISOString().replace('.000Z', '.000Z');
    }
    var text = await fetchSafe(url);
    if (!text) {
      state.errors.push({ channelId: ch.channelId, error: 'fetch_failed' });
      return Object.assign({}, ch, {
        follower: null, category_1: '', category_1_share: 0,
        category_2: '', category_2_share: 0, category_3: '', category_3_share: 0,
        total_categories: 0, _enrich_error: true
      });
    }
    return Object.assign({}, ch, parseDetailRSC(text));
  }

  async function startEnrichment() {
    if (state.filteredChannels.length === 0) {
      log('No filtered channels. Run applyPeakFilter() first.');
      return { error: 'no_filtered_channels' };
    }
    state.phase = 'enriching';
    var total = state.filteredChannels.length;
    log('Enrichment: ' + total + ' channels, ' + CONFIG.workers + ' workers');

    var queue = state.filteredChannels.slice();
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
          log(processed + '/' + total + ' (ok=' + state.stats.enriched + ' err=' + state.errors.length + ')');
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
    await Promise.all(workers);

    state.phase = state.aborted ? 'aborted' : 'done';
    log(state.phase + '. ' + state.stats.enriched + '/' + total + ' enriched, ' + state.errors.length + ' errors.');
    if (!state.aborted) log('Export: downloadAll() or downloadChunks() or getNext()');
    return { phase: state.phase, enriched: state.stats.enriched, total: total, errors: state.errors.length };
  }


  // =========================================================
  //  PHASE 3: EXPORT — I/O PATH REDESIGN
  //
  //  Primary:  Blob download → Downloads 폴더 → CLI pickup
  //            화물차 출입구. 크기 제한 없음.
  //
  //  Fallback: getNext() → JS tool output (10건/1.2KB 이내)
  //            사람 문 우회. Blob이 안 될 때만.
  // =========================================================

  // --- Blob download (primary) ---

  function triggerDownload(csvText, filename) {
    var blob = new Blob(['﻿' + csvText], { type: 'text/csv;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(function() {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
    log('Download: ' + filename + ' (' + csvText.length + ' bytes)');
  }

  function recordsToCSV(records, includeHeader) {
    var lines = [];
    if (includeHeader) lines.push(CSV_COLS.join(','));
    records.forEach(function(r) { lines.push(recordToCSVRow(r)); });
    return lines.join('\n');
  }

  function downloadAll() {
    if (state.enrichedRecords.length === 0) return { error: 'no records' };
    var csv = recordsToCSV(state.enrichedRecords, true);
    var filename = getDownloadPrefix() + '_full.csv';
    triggerDownload(csv, filename);
    state.stats.downloaded = state.enrichedRecords.length;
    return { filename: filename, records: state.enrichedRecords.length, bytes: csv.length };
  }

  function downloadChunks() {
    if (state.enrichedRecords.length === 0) return { error: 'no records' };
    var results = [];
    var total = state.enrichedRecords.length;
    for (var i = 0; i < total; i += CONFIG.chunkSize) {
      var end = Math.min(i + CONFIG.chunkSize, total);
      var chunk = state.enrichedRecords.slice(i, end);
      var idx = String(Math.floor(i / CONFIG.chunkSize) + 1).padStart(3, '0');
      var filename = getDownloadPrefix() + '_chunk_' + idx + '.csv';
      var csv = recordsToCSV(chunk, i === 0);
      triggerDownload(csv, filename);
      results.push({ filename: filename, records: chunk.length });
    }
    state.stats.downloaded = total;
    log(results.length + ' chunks downloaded');
    return results;
  }

  // --- Micro-chunk fallback (JS tool output, 1.2KB budget) ---
  // Compact array format: ~80 bytes/record → 10 records/chunk

  var _cursor = 0;
  var MICRO_SIZE = 8;

  function getNext() {
    if (_cursor >= state.enrichedRecords.length) {
      return JSON.stringify({ done: true, total: state.enrichedRecords.length });
    }
    var batch = state.enrichedRecords.slice(_cursor, _cursor + MICRO_SIZE);
    _cursor += batch.length;

    // compact: [name, channelId(full), peak, follower, c1, c1%, gg, reason]
    var d = batch.map(function(r) {
      return [
        r.name,
        r.channelId,
        r.peak_viewers,
        r.follower,
        r.category_1,
        r.category_1_share,
        r.is_general_game === 'true' ? 1 : r.is_general_game === 'unknown' ? -1 : 0,
        r.gg_reason
      ];
    });
    return JSON.stringify({ i: _cursor, t: state.enrichedRecords.length, d: d });
  }

  // full-column micro-chunk (CSV, fewer records to stay under 1.2KB)
  function getNextCSV() {
    if (_cursor >= state.enrichedRecords.length) return 'DONE:' + state.enrichedRecords.length;
    var batch = state.enrichedRecords.slice(_cursor, _cursor + 5); // 5건 ≈ ~1KB CSV
    _cursor += batch.length;
    var csv = recordsToCSV(batch, _cursor <= 5);
    return csv;
  }

  function resetCursor() { _cursor = 0; log('Cursor reset'); }


  // --- 시계열 반출 (§5 진단용, JSONL) ---

  function triggerDownloadRaw(text, filename, mimeType) {
    var blob = new Blob([text], { type: mimeType || 'application/octet-stream' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1000);
    log('Download: ' + filename + ' (' + text.length + ' bytes)');
  }

  function downloadTimeSeries() {
    var records = state.enrichedRecords.filter(function(r) { return r._timeSeries; });
    if (records.length === 0) return { error: 'no timeseries data' };
    var lines = records.map(function(r) {
      return JSON.stringify({
        channelId: r.channelId,
        name: r.name,
        platform: r.platform,
        maxLiveViews: r._timeSeries.maxLiveViews,
        avgLiveViews: r._timeSeries.avgLiveViews,
        airTime: r._timeSeries.airTime
      });
    });
    var jsonl = lines.join('\n');
    triggerDownloadRaw(jsonl, getDownloadPrefix() + '_timeseries.jsonl', 'application/jsonl');
    return { records: records.length, bytes: jsonl.length };
  }

  // --- Abort ---

  function abort() {
    state.aborted = true;
    log('Abort requested. Workers will stop after current request.');
    return { enrichedSoFar: state.stats.enriched, errors: state.errors.length };
  }

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


  // =========================================================
  //  DIAGNOSTICS
  // =========================================================

  function diagnoseDOM() {
    var links = document.querySelectorAll('a[href*="/channel/"]');
    if (links.length === 0) return { error: 'No channel links. Wrong page?' };
    var sample = links[0];
    var row = sample.closest('tr') || sample.closest('[class*="ranking"]') ||
      sample.closest('[class*="item"]') || (sample.parentElement && sample.parentElement.parentElement);
    var cells = row ? row.querySelectorAll('td, [class*="cell"], [class*="col"]') : [];

    // 집계 윈도우 감지: "지난 7일" / "지난 30일" / "지난 90일" 버튼
    var windowButtons = document.querySelectorAll('button, [role="tab"], [class*="tab"]');
    var activeWindow = null;
    var windowOptions = [];
    windowButtons.forEach(function(btn) {
      var txt = btn.textContent.trim();
      if (/지난\s*\d+일/.test(txt) || /\d+\s*days?/i.test(txt)) {
        var isActive = btn.classList.contains('active') ||
          btn.getAttribute('aria-selected') === 'true' ||
          btn.getAttribute('data-state') === 'active' ||
          getComputedStyle(btn).fontWeight > 500;
        windowOptions.push(txt + (isActive ? ' [ACTIVE]' : ''));
        if (isActive) activeWindow = txt;
      }
    });

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

    return {
      links: links.length,
      href: sample.getAttribute('href'),
      name: sample.textContent.trim(),
      rowTag: row ? row.tagName + '.' + row.className.substring(0, 60) : 'none',
      cells: cells.length,
      cellTexts: Array.from(cells).slice(0, 8).map(function(c) {
        return c.textContent.trim().substring(0, 30);
      }),
      aggregationWindow: activeWindow || 'unknown',
      windowOptions: windowOptions,
      urlDateRange: urlStart ? { start: urlStart, end: urlEnd } : null
    };
  }

  function getBandDistribution() {
    var dist = {};
    state.rankingChannels.forEach(function(ch) {
      var b = ch.band || 'null';
      dist[b] = (dist[b] || 0) + 1;
    });
    return dist;
  }

  function getStatus() {
    return {
      phase: state.phase,
      aborted: state.aborted,
      stats: state.stats,
      errors: state.errors.length,
      records: state.enrichedRecords.length,
      cursor: _cursor,
      config: {
        peakBand: CONFIG.peakBand,
        workers: CONFIG.workers,
        chunkSize: CONFIG.chunkSize,
        dateRange: CONFIG.dateRange,
        downloadPrefix: getDownloadPrefix()
      }
    };
  }

  function getErrors() {
    return state.errors.slice(-20);
  }

  // ===== EXPOSE API =====
  window.__GUBIBA = state;
  window.__GUBIBA_API = {
    // Phase 1: Ranking
    scanCurrentPage: scanCurrentPage,
    scanFromRSC: scanFromRSC,
    loadIds: loadIds,
    loadIdsFromUrl: loadIdsFromUrl,
    applyPeakFilter: applyPeakFilter,
    skipFilter: skipFilter,

    // Phase 2: Enrichment
    startEnrichment: startEnrichment,
    abort: abort,
    resume: resume,

    // Phase 3: Export
    downloadAll: downloadAll,
    downloadChunks: downloadChunks,
    downloadTimeSeries: downloadTimeSeries,
    getNext: getNext,
    getNextCSV: getNextCSV,
    resetCursor: resetCursor,

    // Diagnostics
    diagnoseDOM: diagnoseDOM,
    getBandDistribution: getBandDistribution,
    getStatus: getStatus,
    getErrors: getErrors,

    // Config
    setConfig: function(k, v) { CONFIG[k] = v; log(k + '=' + JSON.stringify(v)); },
    getConfig: function() { return Object.assign({}, CONFIG); }
  };

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

})();
