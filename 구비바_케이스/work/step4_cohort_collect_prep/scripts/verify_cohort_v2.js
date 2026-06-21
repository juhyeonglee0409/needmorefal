#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const CSV_PATH = process.argv[2] || path.join(__dirname, '..', '..', '..', 'data', 'cohort', 'discovery', 'gubiba_cohort_enriched_v2.csv');

function parseCSV(text) {
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',');
  return lines.slice(1).map(line => {
    const vals = line.split(',');
    const obj = {};
    headers.forEach((h, i) => obj[h.trim()] = (vals[i] || '').trim());
    return obj;
  });
}

function verify(rows) {
  const results = [];
  const check = (name, pass, detail) => {
    results.push({ name, status: pass ? 'PASS' : 'FAIL', detail });
    return pass;
  };

  // --- 구조 검증 (윈도우 무관) ---
  check('row_count_nonzero', rows.length > 0,
    'rows=' + rows.length);

  const platforms = [...new Set(rows.map(r => r.platform))];
  check('platform_all_chzzk', platforms.length === 1 && platforms[0] === 'naverchzzk',
    'platforms=' + JSON.stringify(platforms));

  const peaks = rows.map(r => parseInt(r.peak_viewers)).filter(n => !isNaN(n));
  check('peak_all_numeric', peaks.length === rows.length,
    'numeric=' + peaks.length + '/' + rows.length);
  check('peak_in_band', peaks.every(p => p >= 10 && p <= 50),
    'range=' + Math.min(...peaks) + '-' + Math.max(...peaks));

  // --- 결측 검증 ---
  const nullFollower = rows.filter(r => !r.follower).length;
  const nullCat1 = rows.filter(r => !r.category_1).length;
  const nullIsGG = rows.filter(r => !r.is_general_game).length;
  check('no_null_follower', nullFollower === 0,
    'null=' + nullFollower);
  check('no_null_category_1', nullCat1 === 0,
    'null=' + nullCat1);
  check('no_null_is_general_game', nullIsGG === 0,
    'null=' + nullIsGG);

  // --- 분류 무결성 ---
  const ggDist = {};
  rows.forEach(r => { ggDist[r.is_general_game] = (ggDist[r.is_general_game] || 0) + 1; });
  check('is_gg_no_unknown', (ggDist['unknown'] || 0) === 0,
    'unknown=' + (ggDist['unknown'] || 0));
  check('is_gg_values_valid',
    Object.keys(ggDist).every(k => k === 'true' || k === 'false'),
    'values=' + JSON.stringify(Object.keys(ggDist)));

  const reasonDist = {};
  rows.forEach(r => { reasonDist[r.gg_reason] = (reasonDist[r.gg_reason] || 0) + 1; });
  const VALID_REASONS = ['gg_primary', 'multi_game', 'gg_secondary',
    'talk_primary', 'single_game_dominant', 'single_game_or_non_game'];
  const unknownReasons = Object.keys(reasonDist).filter(k => !VALID_REASONS.includes(k));
  check('gg_reason_all_valid', unknownReasons.length === 0,
    unknownReasons.length ? 'unexpected=' + JSON.stringify(unknownReasons) : 'all valid');

  // --- 중복 ---
  const ids = rows.map(r => r.channelId);
  const uniqueCount = new Set(ids).size;
  check('channelId_unique', uniqueCount === rows.length,
    'unique=' + uniqueCount + '/' + rows.length);

  // --- 결과 출력 ---
  console.log('\n=== Verification Results ===\n');
  let allPass = true;
  results.forEach(r => {
    const icon = r.status === 'PASS' ? '[PASS]' : '[FAIL]';
    console.log(`${icon} ${r.name}: ${r.detail}`);
    if (r.status !== 'PASS') allPass = false;
  });

  console.log('\n=== Summary ===');
  console.log('  rows: ' + rows.length);
  console.log('  is_general_game: ' + JSON.stringify(ggDist));

  console.log('\n=== gg_reason Distribution ===');
  Object.entries(reasonDist).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => console.log(`  ${k}: ${v}`));

  const bandDist = {};
  rows.forEach(r => { bandDist[r.band] = (bandDist[r.band] || 0) + 1; });
  console.log('\n=== Band Distribution ===');
  Object.entries(bandDist).sort((a, b) => a[0].localeCompare(b[0])).forEach(([k, v]) => console.log(`  ${k}: ${v}`));

  console.log(`\n${allPass ? 'ALL CHECKS PASSED' : 'SOME CHECKS FAILED'}`);
  process.exit(allPass ? 0 : 1);
}

const text = fs.readFileSync(CSV_PATH, 'utf-8');
verify(parseCSV(text));
