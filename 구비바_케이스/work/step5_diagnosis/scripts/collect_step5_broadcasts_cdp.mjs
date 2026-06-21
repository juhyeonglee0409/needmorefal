// Step 5 SOFTC.ONE broadcast collection via an operator-opened Chrome CDP session.
// Reads public rendered /streams pages only. Does not read cookies, localStorage, or raw HTML.

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(scriptDir, '..', '..', '..');
const outputDir = join(packageRoot, 'data', 'cohort', 'collected', 'broadcast_samples');
const expectedColumns = [
  '시작 시간',
  '종료 시간',
  '카테고리',
  '연령',
  '시작제목',
  '방송 시간',
  '최고 시청자',
  '평균 시청자',
  '전체 채팅수',
  '팔로워 증감',
  '구독자 증감',
];

const sleep = ms => new Promise(resolveSleep => setTimeout(resolveSleep, ms));

function parseArgs() {
  const args = new Map();
  for (let i = 2; i < process.argv.length; i += 1) {
    const key = process.argv[i];
    if (!key.startsWith('--')) continue;
    const next = process.argv[i + 1];
    if (!next || next.startsWith('--')) {
      args.set(key.slice(2), 'true');
    } else {
      args.set(key.slice(2), next);
      i += 1;
    }
  }
  return {
    mode: args.get('mode') || 'sample',
    port: Number(args.get('port') || 9222),
    limit: args.has('limit') ? Number(args.get('limit')) : null,
    offset: Number(args.get('offset') || 0),
    waitMs: Number(args.get('wait-ms') || 6500),
    intervalMs: Number(args.get('interval-ms') || 2500),
    minRows: Number(args.get('min-rows') || 10),
  };
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cell += ch;
      }
      continue;
    }
    if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(cell);
      cell = '';
    } else if (ch === '\n') {
      row.push(cell.replace(/\r$/, ''));
      rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += ch;
    }
  }
  if (cell || row.length) {
    row.push(cell.replace(/\r$/, ''));
    rows.push(row);
  }
  if (!rows.length) return [];
  const header = rows[0];
  return rows.slice(1).filter(r => r.some(Boolean)).map(r => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

function loadFullTargets() {
  const mainPath = join(packageRoot, 'data', 'cohort', 'collected', 'cohort_final_main_general_game.csv');
  const auxPath = join(packageRoot, 'data', 'cohort', 'collected', 'cohort_final_aux_virtual.csv');
  const main = parseCsv(readFileSync(mainPath, 'utf8'))
    .filter(row => String(row.final_include).toLowerCase() === 'true')
    .map(row => ({ group: 'T1', channelId: row.channelId, name: row.channel_name }));
  const aux = parseCsv(readFileSync(auxPath, 'utf8'))
    .filter(row => String(row.final_include).toLowerCase() === 'true')
    .map(row => ({ group: 'T2', channelId: row.channelId, name: row.channel_name }));
  return { targets: [...main, ...aux], beforeDedupe: main.length + aux.length };
}

function loadSampleTargets() {
  const specPath = join(packageRoot, 'data', 'cohort', 'specs', '구비바_§5_broadcast_sample_spec.json');
  const spec = JSON.parse(readFileSync(specPath, 'utf8'));
  const targets = [];
  for (const [key, rows] of Object.entries(spec.samples || {})) {
    const group = key.startsWith('T1') ? 'T1' : 'T2';
    for (const row of rows) {
      targets.push({ group, channelId: row.channelId, name: row.name });
    }
  }
  return { targets, beforeDedupe: targets.length };
}

function dedupeTargets(targets) {
  const chosen = new Map();
  const dedupedMemberships = [];
  for (const target of targets) {
    const prev = chosen.get(target.channelId);
    if (!prev) {
      chosen.set(target.channelId, target);
      continue;
    }
    if (prev.group === 'T2' && target.group === 'T1') {
      chosen.set(target.channelId, target);
      dedupedMemberships.push({
        channel_id: target.channelId,
        name: target.name,
        dropped_group: 'T2',
        kept_group: 'T1',
        reason: 'duplicate_channel_id_t1_priority',
      });
    } else {
      dedupedMemberships.push({
        channel_id: target.channelId,
        name: target.name,
        dropped_group: target.group,
        kept_group: prev.group,
        reason: 'duplicate_channel_id_t1_priority',
      });
    }
  }
  return { targets: [...chosen.values()], dedupedMemberships };
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

function connect(wsUrl) {
  return new Promise((resolveConnect, reject) => {
    const ws = new WebSocket(wsUrl);
    let seq = 0;
    const pending = new Map();
    ws.addEventListener('open', () => resolveConnect({
      ws,
      send: (method, params = {}) => new Promise((resolveSend, rejectSend) => {
        const id = ++seq;
        pending.set(id, { resolveSend, rejectSend });
        ws.send(JSON.stringify({ id, method, params }));
      }),
    }));
    ws.addEventListener('message', event => {
      const msg = JSON.parse(event.data);
      if (!msg.id || !pending.has(msg.id)) return;
      const { resolveSend, rejectSend } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? rejectSend(new Error(JSON.stringify(msg.error))) : resolveSend(msg.result || {});
    });
    ws.addEventListener('error', reject);
  });
}

async function getPage(port) {
  const list = await fetchJson(`http://127.0.0.1:${port}/json/list`);
  const page = list.find(item => item.type === 'page' && item.webSocketDebuggerUrl && item.url.includes('viewership.softc.one'))
    || list.find(item => item.type === 'page' && item.webSocketDebuggerUrl);
  if (!page) throw new Error(`No attachable CDP page on port ${port}`);
  return page;
}

function csvEscape(value) {
  const text = value == null ? '' : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function writeCsv(path, rows) {
  const lines = [expectedColumns.join(',')];
  for (const row of rows) {
    lines.push(expectedColumns.map(column => csvEscape(row[column])).join(','));
  }
  writeFileSync(path, `${lines.join('\n')}\n`, 'utf8');
}

function safeName(channelId) {
  return String(channelId).replace(/[^a-zA-Z0-9_-]/g, '_');
}

async function evaluate(send, expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result?.value;
}

function extractionExpression(channelId) {
  return String.raw`(() => {
    const channelId = __CHANNEL_ID__;
    const norm = s => (s || '').replace(/\s+/g, ' ').trim();
    const onlyNumber = s => norm(s).replace(/,/g, '');
    const datePrefix = value => {
      const text = norm(value).replace(/\s+\(/, '(');
      return /^\d{2}\.\d{2}/.test(text) ? '2026.' + text : text;
    };
    const streamAnchors = Array.from(document.querySelectorAll('a'))
      .filter(a => a.href && a.href.includes('/channel/naverchzzk/' + channelId + '/streams/') && /[0-9]$/.test(a.href));
    const seen = new Set();
    const rows = [];
    for (const a of streamAnchors) {
      if (seen.has(a.href)) continue;
      seen.add(a.href);
      const leaves = Array.from(a.querySelectorAll('div,span,p')).map((el, i) => ({
        i,
        tag: el.tagName,
        text: norm(el.innerText || el.textContent),
        cls: String(el.className || ''),
        childCount: el.children.length
      })).filter(x => x.text);
      const labelIndex = leaves.findIndex(x => x.text === '카테고리 / 제목');
      const before = labelIndex >= 0 ? leaves.slice(0, labelIndex) : leaves;
      const categoryIndex = before.findIndex(x => x.cls.includes('foreground-40') && x.text);
      const categoryRaw = categoryIndex >= 0 ? before[categoryIndex].text.replace(/^LIVE/, '') : '';
      const titleLeaf = before.slice(Math.max(categoryIndex + 1, 0)).find(x => x.cls.includes('gap-1') && x.text && !x.text.includes('foreground'));
      let title = titleLeaf ? titleLeaf.text : '';
      const adult = title.includes('연령제한') || before.some(x => x.text === '연령제한');
      title = title.replace(/^연령제한/, '').replace('연령제한', '').trim();
      const period = before.find(x => x.text.includes('~') && /\d{2}\.\d{2}/.test(x.text))?.text || '';
      const parts = period.split('~');
      const startTime = datePrefix(parts[0] || '');
      const endTime = parts[1] && parts[1] !== 'LIVE' ? datePrefix(parts[1]) : (parts[1] || '');
      const rootCells = before.filter(x => x.tag === 'DIV' && x.cls.includes('justify-end') && x.text);
      const durationCellIndex = rootCells.findIndex(x => /h$/.test(x.text));
      const cells = durationCellIndex >= 0 ? rootCells.slice(durationCellIndex) : rootCells;
      const duration = onlyNumber((cells[0]?.text || '').replace(/h$/, ''));
      const peak = onlyNumber(cells[1]?.text || '');
      const avg = onlyNumber(cells[2]?.text || '');
      const chat = onlyNumber(cells[3]?.text || '');
      const follower = onlyNumber(cells[4]?.text || '');
      rows.push({
        streamId: a.href.split('/').pop(),
        href: a.href,
        values: {
          '시작 시간': startTime,
          '종료 시간': endTime,
          '카테고리': categoryRaw.replace(/,\s*/g, '|'),
          '연령': adult ? '성인' : '전체',
          '시작제목': title,
          '방송 시간': duration,
          '최고 시청자': peak,
          '평균 시청자': avg,
          '전체 채팅수': chat,
          '팔로워 증감': follower,
          '구독자 증감': ''
        }
      });
    }
    const bodyText = norm(document.body?.innerText || '');
    return {
      url: location.href,
      title: document.title,
      checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인/.test(bodyText),
      notFound: /존재하지 않는 페이지|404/.test(bodyText),
      accountTextExcluded: true,
      rowCount: rows.length,
      rows
    };
  })()`.replace('__CHANNEL_ID__', JSON.stringify(channelId));
}

async function collectOne(send, target, waitMs) {
  const url = `https://viewership.softc.one/channel/naverchzzk/${target.channelId}/streams`;
  await send('Page.navigate', { url });
  await sleep(waitMs);
  const state = await evaluate(send, extractionExpression(target.channelId));
  if (state.checkpoint) throw new Error('checkpoint');
  if (state.notFound) throw new Error('not_found');
  return state;
}

function loadTargetsForMode(mode) {
  if (mode === 'full') return loadFullTargets();
  if (mode === 'sample') return loadSampleTargets();
  throw new Error(`Unsupported mode: ${mode}`);
}

async function main() {
  const args = parseArgs();
  mkdirSync(join(outputDir, 'T1'), { recursive: true });
  mkdirSync(join(outputDir, 'T2'), { recursive: true });

  const loaded = loadTargetsForMode(args.mode);
  const deduped = dedupeTargets(loaded.targets);
  const runTargets = deduped.targets.slice(args.offset, args.limit == null ? undefined : args.offset + args.limit);

  const page = await getPage(args.port);
  const { ws, send } = await connect(page.webSocketDebuggerUrl);
  await send('Page.enable');
  await send('Runtime.enable');

  const successes = [];
  const errors = [];
  try {
    for (let i = 0; i < runTargets.length; i += 1) {
      const target = runTargets[i];
      const progress = `${args.offset + i + 1}/${deduped.targets.length}`;
      try {
        const state = await collectOne(send, target, args.waitMs);
        const rows = state.rows.map(row => row.values);
        const outPath = join(outputDir, target.group, `${safeName(target.channelId)}_방송별_요약.csv`);
        if (rows.length) writeCsv(outPath, rows);
        const status = rows.length >= args.minRows ? 'success' : 'short_rows';
        successes.push({
          progress,
          group: target.group,
          channel_id: target.channelId,
          name: target.name,
          row_count: rows.length,
          status,
          output_path: rows.length ? outPath : null,
          source_url: state.url,
        });
        console.log(JSON.stringify({ progress, channelId: target.channelId, name: target.name, rowCount: rows.length, status }));
      } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        errors.push({ progress, group: target.group, channel_id: target.channelId, name: target.name, error: reason });
        console.log(JSON.stringify({ progress, channelId: target.channelId, name: target.name, error: reason }));
        if (reason === 'checkpoint') break;
      }
      if (i < runTargets.length - 1) await sleep(args.intervalMs);
    }
  } finally {
    ws.close();
  }

  const manifestPath = join(outputDir, '_collection_manifest.json');
  const errorsPath = join(outputDir, '_collection_errors.csv');
  const manifest = {
    generated_at: new Date().toISOString(),
    mode: args.mode,
    method: 'cdp_dom_browser',
    cdp_port: args.port,
    output_dir: outputDir,
    raw_html_saved: false,
    secret_values_logged: false,
    cookie_values_read: false,
    url_pattern: 'https://viewership.softc.one/channel/naverchzzk/{channelId}/streams',
    target_summary: {
      candidate_rows_before_dedupe: loaded.beforeDedupe,
      unique_targets_after_dedupe: deduped.targets.length,
      offset: args.offset,
      limit: args.limit,
      attempted_in_this_run: runTargets.length,
    },
    success_count: successes.filter(item => item.status === 'success').length,
    short_rows_count: successes.filter(item => item.status === 'short_rows').length,
    error_count: errors.length,
    deduped_memberships: deduped.dedupedMemberships,
    successes,
    errors,
  };
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');
  const errorLines = ['group,channel_id,name,error,progress'];
  for (const error of errors) {
    errorLines.push([error.group, error.channel_id, error.name, error.error, error.progress].map(csvEscape).join(','));
  }
  writeFileSync(errorsPath, `${errorLines.join('\n')}\n`, 'utf8');
  console.log(JSON.stringify({ manifestPath, errorsPath, ...manifest.target_summary, successCount: manifest.success_count, shortRowsCount: manifest.short_rows_count, errorCount: manifest.error_count }, null, 2));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
