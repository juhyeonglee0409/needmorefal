#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const CSV_PATH = process.argv[2] || path.join(__dirname, '..', 'gubiba_cohort_enriched_v2.csv');

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
  const check = (name, expected, actual) => {
    const pass = JSON.stringify(expected) === JSON.stringify(actual);
    results.push({ name, expected, actual, status: pass ? 'PASS' : 'FAIL' });
    return pass;
  };

  check('row_count', 506, rows.length);

  const platforms = [...new Set(rows.map(r => r.platform))];
  check('platform_all_chzzk', ['naverchzzk'], platforms);

  const peaks = rows.map(r => parseInt(r.peak_viewers));
  check('peak_min_gte_10', true, Math.min(...peaks) >= 10);
  check('peak_max_lte_50', true, Math.max(...peaks) <= 50);

  const ggDist = {};
  rows.forEach(r => { ggDist[r.is_general_game] = (ggDist[r.is_general_game] || 0) + 1; });
  check('is_gg_true', 235, ggDist['true'] || 0);
  check('is_gg_false', 271, ggDist['false'] || 0);
  check('is_gg_unknown', 0, ggDist['unknown'] || 0);

  const reasonDist = {};
  rows.forEach(r => { reasonDist[r.gg_reason] = (reasonDist[r.gg_reason] || 0) + 1; });
  check('gg_reason_count', 6, Object.keys(reasonDist).length);

  const nullFollower = rows.filter(r => !r.follower).length;
  const nullCat1 = rows.filter(r => !r.category_1).length;
  const nullIsGG = rows.filter(r => !r.is_general_game).length;
  check('null_follower', 0, nullFollower);
  check('null_category_1', 0, nullCat1);
  check('null_is_general_game', 0, nullIsGG);

  const ids = rows.map(r => r.channelId);
  check('channelId_unique', rows.length, new Set(ids).size);

  console.log('\n=== Verification Results ===\n');
  let allPass = true;
  results.forEach(r => {
    const icon = r.status === 'PASS' ? '[PASS]' : '[FAIL]';
    console.log(`${icon} ${r.name}: expected=${JSON.stringify(r.expected)}, actual=${JSON.stringify(r.actual)}`);
    if (r.status !== 'PASS') allPass = false;
  });

  console.log(`\n=== gg_reason Distribution ===`);
  Object.entries(reasonDist).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => console.log(`  ${k}: ${v}`));

  const bandDist = {};
  rows.forEach(r => { bandDist[r.band] = (bandDist[r.band] || 0) + 1; });
  console.log(`\n=== Band Distribution ===`);
  Object.entries(bandDist).sort((a, b) => a[0].localeCompare(b[0])).forEach(([k, v]) => console.log(`  ${k}: ${v}`));

  console.log(`\n${allPass ? 'ALL CHECKS PASSED' : 'SOME CHECKS FAILED'}`);
  process.exit(allPass ? 0 : 1);
}

const text = fs.readFileSync(CSV_PATH, 'utf-8');
verify(parseCSV(text));
