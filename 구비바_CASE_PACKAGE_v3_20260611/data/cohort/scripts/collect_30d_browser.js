/**
 * 구비바 §4 — 30-Day Collection Script v2
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
 * Phase 1: scanCurrentPage()     — ranking DOM 추출 (Cowork 구동)
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
    downloadPrefix: 'gubiba_30d'
  };

  // ===== STATE =====
  var state = {
    phase: 'idle',
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
    'total_categories','is_general_game','gg_reason','exclude_reason'];

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
  //  PHASE 2: DETAIL ENRICHMENT
  //  RSC payload → follower + category shares + classify
  // =========================================================

  function parseDetailRSC(text) {
    var followerMatches = text.match(/FollowerCount\\":(\d+)/g);
    var follower = null;
    if (followerMatches && followerMatches.length > 0) {
      var last = followerMatches[followerMatches.length - 1];
      var fm = last.match(/(\d+)/);
      follower = fm ? parseInt(fm[1]) : null;
    }

    var catPattern = /\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)/g;
    var categories = [];
    var cm;
    while ((cm = catPattern.exec(text)) !== null) {
      categories.push({ name: cm[1], viewership: parseInt(cm[2]) });
    }
    categories.sort(function(a, b) { return b.viewership - a.viewership; });
    var total = categories.reduce(function(s, c) { return s + c.viewership; }, 0);
    function shareOf(idx) {
      if (!categories[idx] || !total) return 0;
      return Math.round(categories[idx].viewership / total * 1000) / 10;
    }

    return {
      follower: follower,
      category_1: categories[0] ? categories[0].name : '',
      category_1_share: shareOf(0),
      category_2: categories[1] ? categories[1].name : '',
      category_2_share: shareOf(1),
      category_3: categories[2] ? categories[2].name : '',
      category_3_share: shareOf(2),
      total_categories: categories.length
    };
  }

  async function enrichChannel(ch) {
    var url = CONFIG.baseUrl + '/channel/' + ch.platform + '/' + ch.channelId;
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

    state.phase = 'done';
    log('Done. ' + state.stats.enriched + ' enriched, ' + state.errors.length + ' errors.');
    log('Export: downloadAll() or downloadChunks() or getNext()');
    return { enriched: state.stats.enriched, errors: state.errors.length };
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
    var filename = CONFIG.downloadPrefix + '_full.csv';
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
      var filename = CONFIG.downloadPrefix + '_chunk_' + idx + '.csv';
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
  var MICRO_SIZE = 10;

  function getNext() {
    if (_cursor >= state.enrichedRecords.length) {
      return JSON.stringify({ done: true, total: state.enrichedRecords.length });
    }
    var batch = state.enrichedRecords.slice(_cursor, _cursor + MICRO_SIZE);
    _cursor += batch.length;

    // compact: [name, id(8), peak, follower, c1, c1%, gg, reason]
    var d = batch.map(function(r) {
      return [
        r.name,
        r.channelId.substring(0, 8),
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
    return {
      links: links.length,
      href: sample.getAttribute('href'),
      name: sample.textContent.trim(),
      rowTag: row ? row.tagName + '.' + row.className.substring(0, 60) : 'none',
      cells: cells.length,
      cellTexts: Array.from(cells).slice(0, 8).map(function(c) {
        return c.textContent.trim().substring(0, 30);
      })
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
      stats: state.stats,
      errors: state.errors.length,
      records: state.enrichedRecords.length,
      cursor: _cursor,
      config: { peakBand: CONFIG.peakBand, workers: CONFIG.workers, chunkSize: CONFIG.chunkSize }
    };
  }

  // ===== EXPOSE API =====
  window.__GUBIBA = state;
  window.__GUBIBA_API = {
    // Phase 1: Ranking
    scanCurrentPage: scanCurrentPage,
    applyPeakFilter: applyPeakFilter,

    // Phase 2: Enrichment
    startEnrichment: startEnrichment,

    // Phase 3: Export (primary = download, fallback = micro-chunk)
    downloadAll: downloadAll,
    downloadChunks: downloadChunks,
    getNext: getNext,
    getNextCSV: getNextCSV,
    resetCursor: resetCursor,

    // Diagnostics
    diagnoseDOM: diagnoseDOM,
    getBandDistribution: getBandDistribution,
    getStatus: getStatus,

    // Config
    setConfig: function(k, v) { CONFIG[k] = v; log(k + '=' + JSON.stringify(v)); },
    getConfig: function() { return Object.assign({}, CONFIG); }
  };

  log('v2 loaded. API: window.__GUBIBA_API');
  log('');
  log('=== Workflow ===');
  log('1. 종합 게임 ranking 페이지, "지난 30일" 선택');
  log('2. diagnoseDOM()       → DOM 셀렉터 확인');
  log('3. scanCurrentPage()   → 채널 추출 (페이지마다 반복)');
  log('4. applyPeakFilter()   → peak band 필터');
  log('5. startEnrichment()   → detail fetch + classify');
  log('6. downloadAll()       → Blob download (primary)');
  log('   getNext()           → micro-chunk fallback');
  log('');
  log('=== I/O Path ===');
  log('Primary:  downloadAll() → Downloads 폴더 → CLI pickup');
  log('Fallback: getNext() × N → JS output 10건씩 → Cowork append');

})();
