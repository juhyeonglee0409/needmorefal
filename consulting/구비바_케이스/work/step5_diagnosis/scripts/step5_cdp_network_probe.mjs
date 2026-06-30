// Step 5 browser/CDP network probe for SOFTC.ONE broadcast-history discovery.
// Saves compact page/network metadata only; raw HTML and cookies are not saved.

import { spawn } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(scriptDir, '..', '..', '..');
const outputDir = join(packageRoot, 'data', 'cohort', 'collected', 'broadcast_samples');
const out = process.env.STEP5_NETWORK_PROBE_OUT || join(outputDir, '_network_probe.json');
const chromePath = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const channelId = process.argv[2] || '269edc95873a1ec9fc534851c0783d1f';
const profileDir = process.env.STEP5_CHROME_PROFILE || join(process.env.TEMP || '.', `codex_step5_chrome_${Date.now()}`);
const port = Number(process.env.STEP5_CDP_PORT || 9367);
const urls = [
  `https://viewership.softc.one/channel/${channelId},naverchzzk`,
  `https://viewership.softc.one/channel/naverchzzk/${channelId}`,
];

const sleep = ms => new Promise(resolveSleep => setTimeout(resolveSleep, ms));

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

async function waitTarget() {
  for (let i = 0; i < 80; i += 1) {
    try {
      const list = await fetchJson(`http://127.0.0.1:${port}/json/list`);
      const target = list.find(item => item.type === 'page' && item.webSocketDebuggerUrl);
      if (target) return target;
    } catch {
      // Chrome may still be booting.
    }
    await sleep(250);
  }
  throw new Error('Chrome DevTools target was not available');
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

async function main() {
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(profileDir, { recursive: true });

  const chrome = spawn(chromePath, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank',
  ], { stdio: 'ignore', windowsHide: true });

  const probes = [];
  try {
    const target = await waitTarget();
    const { ws, send } = await connect(target.webSocketDebuggerUrl);
    const network = [];
    ws.addEventListener('message', event => {
      const msg = JSON.parse(event.data);
      if (msg.method === 'Network.requestWillBeSent') {
        const request = msg.params.request;
        if (request.url.includes('viewership.softc.one') || request.url.includes('_next') || request.url.includes('api')) {
          network.push({ type: 'request', url: request.url, method: request.method, resourceType: msg.params.type });
        }
      }
      if (msg.method === 'Network.responseReceived') {
        const response = msg.params.response;
        if (response.url.includes('viewership.softc.one') || response.url.includes('_next') || response.url.includes('api')) {
          network.push({ type: 'response', url: response.url, status: response.status, mimeType: response.mimeType });
        }
      }
    });

    await send('Page.enable');
    await send('Runtime.enable');
    await send('Network.enable');
    await send('Page.setDownloadBehavior', { behavior: 'allow', downloadPath: outputDir }).catch(() => {});

    async function evaluate(expression) {
      const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
      return result.result?.value;
    }

    for (const url of urls) {
      const before = network.length;
      await send('Page.navigate', { url });
      await sleep(12000);
      const state = await evaluate(`(() => {
        const text = document.body ? document.body.innerText.slice(0, 800) : '';
        const links = [...document.querySelectorAll('a[href]')]
          .map(a => ({ text: a.innerText.trim().slice(0, 80), href: a.href }))
          .filter(x => /csv|download|broadcast|history/i.test(x.text + ' ' + x.href) || (x.text + ' ' + x.href).includes('방송') || (x.text + ' ' + x.href).includes('기록'))
          .slice(0, 50);
        const buttons = [...document.querySelectorAll('button,[role="button"]')]
          .map(b => b.innerText.trim())
          .filter(Boolean)
          .slice(0, 80);
        return { url: location.href, title: document.title, textSnippet: text, links, buttons };
      })()`);

      for (const label of ['방송기록', '방송 기록', 'CSV', '다운로드']) {
        const clicked = await evaluate(`(() => {
          const label = ${JSON.stringify(label)};
          const nodes = [...document.querySelectorAll('button,a,[role="button"],div,span')];
          const el = nodes.find(n => (n.innerText || '').trim() === label || (n.innerText || '').includes(label));
          if (!el) return false;
          el.click();
          return true;
        })()`);
        if (clicked) await sleep(5000);
      }

      const afterClicks = await evaluate(`(() => ({
        url: location.href,
        title: document.title,
        textSnippet: document.body ? document.body.innerText.slice(0, 800) : '',
        buttons: [...document.querySelectorAll('button,[role="button"]')]
          .map(b => b.innerText.trim())
          .filter(Boolean)
          .slice(0, 80)
      }))()`);
      probes.push({ inputUrl: url, state, afterClicks, network: network.slice(before) });
    }
    writeFileSync(out, JSON.stringify({
      generatedAt: new Date().toISOString(),
      rawHtmlSaved: false,
      secretValuesLogged: false,
      probes,
    }, null, 2), 'utf8');
    console.log(JSON.stringify({
      out,
      probes: probes.map(item => ({
        inputUrl: item.inputUrl,
        finalUrl: item.afterClicks.url,
        title: item.afterClicks.title,
        networkEvents: item.network.length,
      })),
    }, null, 2));
    ws.close();
  } finally {
    chrome.kill();
    await sleep(500);
    rmSync(profileDir, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
