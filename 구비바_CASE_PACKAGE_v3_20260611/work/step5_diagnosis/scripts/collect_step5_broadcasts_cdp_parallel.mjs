// Step 5 SOFTC.ONE broadcast collection via multiple operator-opened Chrome CDP tabs.
// Reads public rendered /streams pages only. Does not read cookies, localStorage, or raw HTML.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
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
    mode: args.get('mode') || 'full',
    port: Number(args.get('port') || 9222),
    concurrency: Math.max(1, Math.min(6, Number(args.get('concurrency') || 3))),
    limit: args.has('limit') ? Number(args.get('limit')) : null,
    offset: Number(args.get('offset') || 0),
    waitMs: Number(args.get('wait-ms') || 12000),
    minRows: Number(args.get('min-rows') || 10),
    staggerMs: Number(args.get('stagger-ms') || 1500),
    delayMs: Number(args.get('delay-ms') || 0),
    jitterMs: Number(args.get('jitter-ms') || 0),
    dateStartUtc: args.get('date-start-utc') || '2023-10-01T15:00:00.000Z',
    dateEndUtc: args.get('date-end-utc') || '2026-06-15T14:59:59.999Z',
    fullRange: args.get('full-range') !== 'false',
    manifestName: args.get('manifest-name') || '_collection_manifest.json',
    errorsName: args.get('errors-name') || '_collection_errors.csv',
    progressName: args.get('progress-name') || '_collection_progress.ndjson',
    skipExisting: args.get('skip-existing') === 'true',
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
    if (ch === '"') quoted = true;
    else if (ch === ',') {
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
      dedupedMemberships.push({ channel_id: target.channelId, name: target.name, dropped_group: 'T2', kept_group: 'T1', reason: 'duplicate_channel_id_t1_priority' });
    } else {
      dedupedMemberships.push({ channel_id: target.channelId, name: target.name, dropped_group: target.group, kept_group: prev.group, reason: 'duplicate_channel_id_t1_priority' });
    }
  }
  return { targets: [...chosen.values()], dedupedMemberships };
}

function loadTargetsForMode(mode) {
  if (mode === 'full') return loadFullTargets();
  if (mode === 'sample') return loadSampleTargets();
  throw new Error(`Unsupported mode: ${mode}`);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

function connect(wsUrl, onEvent = null) {
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
      if (!msg.id && onEvent) onEvent(msg);
      if (!msg.id || !pending.has(msg.id)) return;
      const { resolveSend, rejectSend } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? rejectSend(new Error(JSON.stringify(msg.error))) : resolveSend(msg.result || {});
    });
    ws.addEventListener('error', reject);
  });
}

async function createTab(port) {
  return fetchJson(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' });
}

async function closeTab(port, id) {
  try {
    await fetch(`http://127.0.0.1:${port}/json/close/${id}`);
  } catch {
    // Best-effort cleanup.
  }
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
      rows.push({
        streamId: a.href.split('/').pop(),
        values: {
          '시작 시간': startTime,
          '종료 시간': endTime,
          '카테고리': categoryRaw.replace(/,\s*/g, '|'),
          '연령': adult ? '성인' : '전체',
          '시작제목': title,
          '방송 시간': onlyNumber((cells[0]?.text || '').replace(/h$/, '')),
          '최고 시청자': onlyNumber(cells[1]?.text || ''),
          '평균 시청자': onlyNumber(cells[2]?.text || ''),
          '전체 채팅수': onlyNumber(cells[3]?.text || ''),
          '팔로워 증감': onlyNumber(cells[4]?.text || ''),
          '구독자 증감': ''
        }
      });
    }
    const bodyText = norm(document.body?.innerText || '');
    return {
      url: location.href,
      title: document.title,
      checkpoint: /Security Checkpoint|보안 검문|브라우저를 확인/.test(bodyText),
      rateLimited: /Too Many Requests|rate limit|요청이 너무 많/i.test(bodyText),
      notFound: /존재하지 않는 페이지|404/.test(bodyText),
      rowCount: rows.length,
      rows
    };
  })()`.replace('__CHANNEL_ID__', JSON.stringify(channelId));
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

function outPathFor(target) {
  return join(outputDir, target.group, `${safeName(target.channelId)}_방송별_요약.csv`);
}

function targetUrl(target, args) {
  const base = `https://viewership.softc.one/channel/naverchzzk/${target.channelId}/streams`;
  if (!args.fullRange) return base;
  const params = new URLSearchParams({
    startDateTime: args.dateStartUtc,
    endDateTime: args.dateEndUtc,
  });
  return `${base}?${params.toString()}`;
}

function appendProgress(path, event) {
  writeFileSync(path, `${JSON.stringify({ generated_at: new Date().toISOString(), ...event })}\n`, { flag: 'a', encoding: 'utf8' });
}

async function collectOne(send, target, args, networkState) {
  const url = targetUrl(target, args);
  networkState.statusCodes = [];
  networkState.rateLimited = false;
  await send('Page.navigate', { url });
  const startedAt = Date.now();
  let state = null;
  while (Date.now() - startedAt < args.waitMs) {
    await sleep(2000);
    if (networkState.rateLimited) throw new Error('429');
    state = await evaluate(send, extractionExpression(target.channelId));
    if (state.checkpoint) throw new Error('checkpoint');
    if (state.rateLimited) throw new Error('429');
    if (state.notFound) throw new Error('not_found');
    if (state.rowCount > 0) return state;
  }
  return state || await evaluate(send, extractionExpression(target.channelId));
}

async function workerLoop({ workerId, port, queue, args, successes, errors, progressPath, stop }) {
  const tab = await createTab(port);
  const networkState = { statusCodes: [], rateLimited: false };
  const { ws, send } = await connect(tab.webSocketDebuggerUrl, msg => {
    if (msg.method !== 'Network.responseReceived') return;
    const status = msg.params?.response?.status;
    if (typeof status === 'number') {
      networkState.statusCodes.push(status);
      if (status === 429) networkState.rateLimited = true;
    }
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  try {
    while (!stop.value) {
      const item = queue.shift();
      if (!item) break;
      const { target, ordinal, total } = item;
      const progress = `${ordinal}/${total}`;
      try {
        const state = await collectOne(send, target, args, networkState);
        const rows = state.rows.map(row => row.values);
        const outputPath = outPathFor(target);
        if (rows.length) writeCsv(outputPath, rows);
        const status = rows.length >= args.minRows ? 'success' : 'short_rows';
        const record = { worker_id: workerId, progress, group: target.group, channel_id: target.channelId, name: target.name, row_count: rows.length, status, output_path: rows.length ? outputPath : null, source_url: state.url };
        successes.push(record);
        appendProgress(progressPath, { event: 'collected', ...record });
        console.log(JSON.stringify({ workerId, progress, channelId: target.channelId, name: target.name, rowCount: rows.length, status }));
      } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        const record = {
          worker_id: workerId,
          progress,
          group: target.group,
          channel_id: target.channelId,
          name: target.name,
          error: reason,
          network_rate_limited: networkState.rateLimited,
          status_codes: networkState.statusCodes.slice(0, 30),
        };
        errors.push(record);
        appendProgress(progressPath, { event: 'error', ...record });
        console.log(JSON.stringify({ workerId, progress, channelId: target.channelId, name: target.name, error: reason }));
        if (reason === 'checkpoint' || reason === '429') stop.value = true;
      }
      if (!stop.value && queue.length > 0 && (args.delayMs > 0 || args.jitterMs > 0)) {
        const jitter = args.jitterMs > 0 ? Math.floor(Math.random() * (args.jitterMs + 1)) : 0;
        await sleep(args.delayMs + jitter);
      }
    }
  } finally {
    ws.close();
    await closeTab(port, tab.id);
  }
}

async function main() {
  const args = parseArgs();
  mkdirSync(join(outputDir, 'T1'), { recursive: true });
  mkdirSync(join(outputDir, 'T2'), { recursive: true });

  const loaded = loadTargetsForMode(args.mode);
  const deduped = dedupeTargets(loaded.targets);
  let runTargets = deduped.targets.slice(args.offset);
  if (args.skipExisting) {
    runTargets = runTargets.filter(target => !existsSync(outPathFor(target)));
  }
  if (args.limit != null) {
    runTargets = runTargets.slice(0, args.limit);
  }

  const progressPath = join(outputDir, args.progressName);
  writeFileSync(progressPath, '', 'utf8');
  const queue = runTargets.map((target, i) => ({ target, ordinal: args.offset + i + 1, total: deduped.targets.length }));
  const successes = [];
  const errors = [];
  const stop = { value: false };

  appendProgress(progressPath, {
    event: 'start',
    mode: args.mode,
    concurrency: args.concurrency,
    full_range: args.fullRange,
    date_start_utc: args.fullRange ? args.dateStartUtc : null,
    date_end_utc: args.fullRange ? args.dateEndUtc : null,
    delay_ms: args.delayMs,
    jitter_ms: args.jitterMs,
    candidate_rows_before_dedupe: loaded.beforeDedupe,
    unique_targets_after_dedupe: deduped.targets.length,
    attempted_in_this_run: runTargets.length,
    raw_html_saved: false,
    secret_values_logged: false,
    cookie_values_read: false,
  });

  const workers = [];
  for (let i = 0; i < Math.min(args.concurrency, runTargets.length); i += 1) {
    if (i > 0) await sleep(args.staggerMs);
    workers.push(workerLoop({ workerId: i + 1, port: args.port, queue, args, successes, errors, progressPath, stop }));
  }
  await Promise.all(workers);

  successes.sort((a, b) => Number(a.progress.split('/')[0]) - Number(b.progress.split('/')[0]));
  errors.sort((a, b) => Number(a.progress.split('/')[0]) - Number(b.progress.split('/')[0]));

  const manifestPath = join(outputDir, args.manifestName);
  const errorsPath = join(outputDir, args.errorsName);
  const manifest = {
    generated_at: new Date().toISOString(),
    mode: args.mode,
    method: 'cdp_dom_browser_parallel',
    cdp_port: args.port,
    concurrency: args.concurrency,
    output_dir: outputDir,
    raw_html_saved: false,
    secret_values_logged: false,
    cookie_values_read: false,
    url_pattern: 'https://viewership.softc.one/channel/naverchzzk/{channelId}/streams',
    date_range: args.fullRange ? {
      startDateTime: args.dateStartUtc,
      endDateTime: args.dateEndUtc,
      label: 'full_max_range',
    } : null,
    target_summary: {
      candidate_rows_before_dedupe: loaded.beforeDedupe,
      unique_targets_after_dedupe: deduped.targets.length,
      offset: args.offset,
      limit: args.limit,
      attempted_in_this_run: runTargets.length,
      skipped_existing: args.skipExisting,
      delay_ms: args.delayMs,
      jitter_ms: args.jitterMs,
    },
    success_count: successes.filter(item => item.status === 'success').length,
    short_rows_count: successes.filter(item => item.status === 'short_rows').length,
    error_count: errors.length,
    boundary_signal: stop.value ? 'checkpoint_or_rate_boundary' : null,
    deduped_memberships: deduped.dedupedMemberships,
    successes,
    errors,
  };
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');
  const errorLines = ['group,channel_id,name,error,progress,worker_id'];
  for (const error of errors) {
    errorLines.push([error.group, error.channel_id, error.name, error.error, error.progress, error.worker_id].map(csvEscape).join(','));
  }
  writeFileSync(errorsPath, `${errorLines.join('\n')}\n`, 'utf8');
  appendProgress(progressPath, { event: 'done', success_count: manifest.success_count, short_rows_count: manifest.short_rows_count, error_count: manifest.error_count, boundary_signal: manifest.boundary_signal });
  console.log(JSON.stringify({ manifestPath, errorsPath, progressPath, ...manifest.target_summary, successCount: manifest.success_count, shortRowsCount: manifest.short_rows_count, errorCount: manifest.error_count, boundarySignal: manifest.boundary_signal }, null, 2));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
