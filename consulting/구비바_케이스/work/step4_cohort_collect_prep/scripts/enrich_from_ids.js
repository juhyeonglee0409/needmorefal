/**
 * 구비바 §4 — Node.js Enrichment Script (CC용)
 *
 * 입력: gubiba_multipage_scan_ids.json (5,679 channel IDs from multi-page RSC scan)
 * 출력: gubiba_enriched_multipage.csv + gubiba_timeseries_multipage.jsonl
 *
 * 동작:
 *   1. ID JSON 로드 → 기존 enriched CSV 로드 (있으면 skip)
 *   2. 채널 상세 페이지 fetch → RSC 파싱 (follower, categories, timeseries)
 *   3. timeseries에서 peak/avg/hours 계산
 *   4. GG 분류
 *   5. CSV + JSONL 출력
 *
 * 실행: node enrich_from_ids.js [--ids path] [--existing path] [--out-dir path]
 *       [--workers N] [--delay-ms N] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
 *
 * Resume: checkpoint 파일(enrich_checkpoint.json)로 자동 재개
 */

const fs = require('fs');
const path = require('path');

// ===== CONFIG =====
const CONFIG = {
  workers: 2,
  delayMs: 3000,        // per-worker delay between requests
  maxRetries: 3,
  backoffMs: 60000,     // 429/403 backoff
  baseUrl: 'https://viewership.softc.one',
  startDate: '2024-01-01',
  endDate: '2026-06-15',
  platform: 'naverchzzk',
  peakBand: { min: 10, max: 50 },
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
};

// ===== CLI ARGS =====
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    idsPath: null,
    existingPath: null,
    outDir: '.',
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--ids':       opts.idsPath = args[++i]; break;
      case '--existing':  opts.existingPath = args[++i]; break;
      case '--out-dir':   opts.outDir = args[++i]; break;
      case '--workers':   CONFIG.workers = parseInt(args[++i]); break;
      case '--delay-ms':  CONFIG.delayMs = parseInt(args[++i]); break;
      case '--start-date': CONFIG.startDate = args[++i]; break;
      case '--end-date':   CONFIG.endDate = args[++i]; break;
    }
  }
  return opts;
}

// ===== CSV COLUMNS =====
const CSV_COLS = [
  'name','platform','channelId','rank','stream_hours','peak_viewers',
  'avg_viewers','viewership','follower','band','category_1','category_1_share',
  'category_2','category_2_share','category_3','category_3_share',
  'total_categories','is_general_game','gg_reason','exclude_reason','collected_at'
];

function escapeCSV(v) {
  if (v == null) return '';
  v = String(v);
  if (v.includes(',') || v.includes('"') || v.includes('\n')) {
    return '"' + v.replace(/"/g, '""') + '"';
  }
  return v;
}

function recordToCSVRow(r) {
  return CSV_COLS.map(c => escapeCSV(r[c])).join(',');
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

// ===== GG CLASSIFICATION (v3 검증 완료 로직 그대로) =====
function classifyGG(row) {
  const c1 = (row.category_1 || '').trim();
  const c1s = parseFloat(row.category_1_share) || 0;
  const c2 = (row.category_2 || '').trim();
  const c2s = parseFloat(row.category_2_share) || 0;
  const c3 = (row.category_3 || '').trim();
  const c3s = parseFloat(row.category_3_share) || 0;

  if (!c1) return { is_gg: 'unknown', reason: 'no_category_data' };
  if (c1 === '종합 게임' || c1 === '종합게임') return { is_gg: 'true', reason: 'gg_primary' };
  if (c1.toLowerCase() === 'talk' && c1s >= 50) return { is_gg: 'false', reason: 'talk_primary' };
  if (c1s >= 80) return { is_gg: 'false', reason: 'single_game_dominant' };

  const nonTalkCats = [[c1, c1s], [c2, c2s], [c3, c3s]].filter(([name, share]) =>
    name && name.toLowerCase() !== 'talk' &&
    name !== '그림/아트' && name !== '먹방' && share >= 15
  );
  if (nonTalkCats.length >= 2) return { is_gg: 'true', reason: 'multi_game' };
  if ((c2 === '종합 게임' || c2 === '종합게임') && c2s >= 15) return { is_gg: 'true', reason: 'gg_secondary' };
  return { is_gg: 'false', reason: 'single_game_or_non_game' };
}

// ===== FETCH WITH RETRY =====
const delay = ms => new Promise(r => setTimeout(r, ms));

async function fetchSafe(url, retries = CONFIG.maxRetries) {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, {
        headers: {
          'User-Agent': CONFIG.userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        },
      });
      if (res.ok) return await res.text();
      if (res.status === 429 || res.status === 403) {
        console.error(`  [BLOCKED ${res.status}] backoff ${CONFIG.backoffMs/1000}s — ${url}`);
        if (i < retries) { await delay(CONFIG.backoffMs); continue; }
        return null;
      }
      console.error(`  [HTTP ${res.status}] ${url}`);
      return null;
    } catch (e) {
      console.error(`  [Network] ${e.message}`);
      if (i < retries) await delay(5000);
      else return null;
    }
  }
  return null;
}

// ===== RSC PARSING (v3 parseDetailRSC 포팅) =====

function extractTimeSeries(text, fieldName) {
  const pattern = new RegExp(`\\\\"${fieldName}\\\\":(\\d+)`, 'g');
  const values = [];
  let m;
  while ((m = pattern.exec(text)) !== null) {
    values.push(parseInt(m[1]));
  }
  // hydration dedup: 서버/클라이언트 데이터가 2번 반복됨
  if (values.length > 0) {
    return values.slice(0, Math.ceil(values.length / 2));
  }
  return values;
}

function parseDetailRSC(text) {
  // followerCount
  const folMatches = [];
  const folPattern = /\\"followerCount\\":(\d+)/g;
  let fm;
  while ((fm = folPattern.exec(text)) !== null) {
    folMatches.push(parseInt(fm[1]));
  }
  const follower = folMatches.length > 0 ? folMatches[folMatches.length - 1] : null;

  // name/nickname
  const nameMatch = text.match(/\\"(?:nickname|channelName)\\":\\"([^\\]+)\\"/);
  const name = nameMatch ? nameMatch[1] : '';

  // 카테고리별 viewership
  const catPattern = /\\"category\\":\\"([^\\]+)\\",\\"sumLiveViews\\":\d+,\\"viewership\\":(\d+)/g;
  const categories = [];
  let cm;
  while ((cm = catPattern.exec(text)) !== null) {
    categories.push({ name: cm[1], viewership: parseInt(cm[2]) });
  }
  categories.sort((a, b) => b.viewership - a.viewership);
  const totalVS = categories.reduce((s, c) => s + c.viewership, 0);
  const shareOf = idx => {
    if (!categories[idx] || !totalVS) return 0;
    return Math.round(categories[idx].viewership / totalVS * 1000) / 10;
  };

  // 시계열
  const timeSeries = {
    maxLiveViews: extractTimeSeries(text, 'maxLiveViews'),
    avgLiveViews: extractTimeSeries(text, 'avgLiveViews'),
    airTime: extractTimeSeries(text, 'airTime'),
  };

  // timeseries에서 ranking metrics 계산
  const peakViewers = timeSeries.maxLiveViews.length > 0
    ? Math.max(...timeSeries.maxLiveViews) : null;
  const avgViewers = timeSeries.avgLiveViews.length > 0
    ? Math.round(timeSeries.avgLiveViews.reduce((a, b) => a + b, 0) / timeSeries.avgLiveViews.length) : null;
  const streamHours = timeSeries.airTime.length > 0
    ? Math.round(timeSeries.airTime.reduce((a, b) => a + b, 0) * 10) / 10 : null;
  // viewership = sum(avg × airTime) per stream, but airTime is in hours and avg is viewer count
  // 실제로는 SOFTC.ONE이 별도로 계산. 근사치 사용.
  const viewership = (timeSeries.avgLiveViews.length > 0 && timeSeries.airTime.length > 0)
    ? Math.round(timeSeries.avgLiveViews.reduce((sum, avg, i) => {
        const air = timeSeries.airTime[i] || 0;
        return sum + avg * air;
      }, 0))
    : null;

  return {
    name,
    follower,
    category_1: categories[0] ? categories[0].name : '',
    category_1_share: shareOf(0),
    category_2: categories[1] ? categories[1].name : '',
    category_2_share: shareOf(1),
    category_3: categories[2] ? categories[2].name : '',
    category_3_share: shareOf(2),
    total_categories: categories.length,
    peak_viewers: peakViewers,
    avg_viewers: avgViewers,
    stream_hours: streamHours,
    viewership,
    _timeSeries: timeSeries,
  };
}

// ===== CHANNEL ENRICHMENT =====

function buildChannelUrl(channelId) {
  // 채널 상세 페이지 URL (date range 포함)
  const startDT = new Date(CONFIG.startDate + 'T00:00:00+09:00');
  startDT.setHours(startDT.getHours() - 9); // KST → UTC
  const endDT = new Date(CONFIG.endDate + 'T23:59:59+09:00');
  endDT.setHours(endDT.getHours() - 9);

  const params = new URLSearchParams({
    start: CONFIG.startDate,
    end: CONFIG.endDate,
    startDateTime: startDT.toISOString().replace(/\.000Z$/, '.000Z'),
    endDateTime: endDT.toISOString().replace(/\.000Z$/, '.000Z'),
  });

  return `${CONFIG.baseUrl}/channel/${CONFIG.platform}/${channelId}?${params}`;
}

async function enrichChannel(channelId) {
  const url = buildChannelUrl(channelId);
  const text = await fetchSafe(url);

  if (!text) {
    return {
      channelId,
      platform: CONFIG.platform,
      name: '',
      rank: null,
      stream_hours: null,
      peak_viewers: null,
      avg_viewers: null,
      viewership: null,
      follower: null,
      band: '',
      category_1: '', category_1_share: 0,
      category_2: '', category_2_share: 0,
      category_3: '', category_3_share: 0,
      total_categories: 0,
      is_general_game: 'unknown',
      gg_reason: 'fetch_failed',
      exclude_reason: '',
      collected_at: new Date().toISOString(),
      _enrich_error: true,
      _timeSeries: null,
    };
  }

  const parsed = parseDetailRSC(text);
  const gg = classifyGG(parsed);

  return {
    channelId,
    platform: CONFIG.platform,
    name: parsed.name,
    rank: null,
    stream_hours: parsed.stream_hours,
    peak_viewers: parsed.peak_viewers,
    avg_viewers: parsed.avg_viewers,
    viewership: parsed.viewership,
    follower: parsed.follower,
    band: bandLabel(parsed.peak_viewers),
    category_1: parsed.category_1,
    category_1_share: parsed.category_1_share,
    category_2: parsed.category_2,
    category_2_share: parsed.category_2_share,
    category_3: parsed.category_3,
    category_3_share: parsed.category_3_share,
    total_categories: parsed.total_categories,
    is_general_game: gg.is_gg,
    gg_reason: gg.reason,
    exclude_reason: '',
    collected_at: new Date().toISOString(),
    _timeSeries: parsed._timeSeries,
  };
}

// ===== CHECKPOINT =====

function loadCheckpoint(outDir) {
  const cpPath = path.join(outDir, 'enrich_checkpoint.json');
  if (fs.existsSync(cpPath)) {
    const cp = JSON.parse(fs.readFileSync(cpPath, 'utf8'));
    console.log(`[checkpoint] Loaded: ${cp.completed.length} already done`);
    return cp;
  }
  return { completed: [], errors: [] };
}

function saveCheckpoint(outDir, checkpoint) {
  const cpPath = path.join(outDir, 'enrich_checkpoint.json');
  fs.writeFileSync(cpPath, JSON.stringify(checkpoint));
}

// ===== LOAD EXISTING CSV =====

function loadExistingCSV(csvPath) {
  if (!csvPath || !fs.existsSync(csvPath)) return new Set();
  const text = fs.readFileSync(csvPath, 'utf8');
  const lines = text.split('\n');
  const header = lines[0];
  const cidIdx = header.split(',').indexOf('channelId');
  if (cidIdx < 0) return new Set();

  const ids = new Set();
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (cols[cidIdx]) ids.add(cols[cidIdx].replace(/"/g, ''));
  }
  console.log(`[existing] Loaded ${ids.size} already-enriched channel IDs`);
  return ids;
}

// ===== MAIN =====

async function main() {
  const opts = parseArgs();

  // Find input files
  const idsPath = opts.idsPath || findFile('gubiba_multipage_scan_ids.json');
  if (!idsPath || !fs.existsSync(idsPath)) {
    console.error('ERROR: Cannot find gubiba_multipage_scan_ids.json');
    console.error('Usage: node enrich_from_ids.js --ids <path-to-ids.json>');
    process.exit(1);
  }

  const idsData = JSON.parse(fs.readFileSync(idsPath, 'utf8'));
  const allIds = idsData.channel_ids || idsData;
  console.log(`[input] ${allIds.length} channel IDs from ${idsPath}`);

  // Load existing enriched data to skip
  const existingIds = loadExistingCSV(opts.existingPath);

  // Load checkpoint
  const checkpoint = loadCheckpoint(opts.outDir);
  const completedSet = new Set(checkpoint.completed);

  // Filter: skip already done
  const todoIds = allIds.filter(id =>
    !existingIds.has(id) && !completedSet.has(id)
  );
  console.log(`[plan] ${todoIds.length} to enrich (${existingIds.size} existing, ${completedSet.size} checkpointed)`);

  if (todoIds.length === 0) {
    console.log('[done] Nothing to do.');
    return;
  }

  // Output streams
  const csvPath = path.join(opts.outDir, 'gubiba_enriched_multipage.csv');
  const jsonlPath = path.join(opts.outDir, 'gubiba_timeseries_multipage.jsonl');

  // Write CSV header if new file
  const csvExists = fs.existsSync(csvPath) && fs.statSync(csvPath).size > 0;
  if (!csvExists) {
    fs.writeFileSync(csvPath, '﻿' + CSV_COLS.join(',') + '\n');
  }

  // Worker queue
  const queue = [...todoIds];
  let processed = 0;
  const total = queue.length;
  const startTime = Date.now();
  let errors = 0;

  async function worker(wid) {
    while (queue.length > 0) {
      const channelId = queue.shift();
      if (!channelId) break;

      processed++;
      const record = await enrichChannel(channelId);

      // Append CSV
      fs.appendFileSync(csvPath, recordToCSVRow(record) + '\n');

      // Append timeseries JSONL
      if (record._timeSeries && record._timeSeries.maxLiveViews.length > 0) {
        const tsLine = JSON.stringify({
          channelId: record.channelId,
          name: record.name,
          platform: record.platform,
          maxLiveViews: record._timeSeries.maxLiveViews,
          avgLiveViews: record._timeSeries.avgLiveViews,
          airTime: record._timeSeries.airTime,
        });
        fs.appendFileSync(jsonlPath, tsLine + '\n');
      }

      // Update checkpoint
      checkpoint.completed.push(channelId);
      if (record._enrich_error) {
        checkpoint.errors.push(channelId);
        errors++;
      }

      // Save checkpoint every 50 records
      if (processed % 50 === 0) {
        saveCheckpoint(opts.outDir, checkpoint);
      }

      // Progress log
      if (processed % 20 === 0 || processed === total) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
        const rate = (processed / (elapsed || 1)).toFixed(2);
        const eta = Math.round((total - processed) / (rate || 1));
        console.log(
          `[w${wid}] ${processed}/${total} (${errors} err) — ` +
          `${elapsed}s elapsed, ${rate}/s, ETA ${eta}s`
        );
      }

      await delay(CONFIG.delayMs);
    }
  }

  // Stagger workers
  const stagger = Math.round(CONFIG.delayMs / CONFIG.workers);
  const workers = [];
  for (let w = 0; w < CONFIG.workers; w++) {
    workers.push(delay(w * stagger).then(() => worker(w)));
  }

  console.log(`[start] ${CONFIG.workers} workers, ${CONFIG.delayMs}ms delay`);
  await Promise.all(workers);

  // Final checkpoint
  saveCheckpoint(opts.outDir, checkpoint);

  // Summary
  const elapsed = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  console.log(`\n[DONE] ${processed} enriched in ${elapsed} min, ${errors} errors`);
  console.log(`  CSV:   ${csvPath}`);
  console.log(`  JSONL: ${jsonlPath}`);
  console.log(`  Checkpoint: ${path.join(opts.outDir, 'enrich_checkpoint.json')}`);
}

function findFile(name) {
  // Check current dir and parent dirs
  const candidates = [
    path.join(process.cwd(), name),
    path.join(process.cwd(), '..', name),
    path.join(process.cwd(), '..', '..', name),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
