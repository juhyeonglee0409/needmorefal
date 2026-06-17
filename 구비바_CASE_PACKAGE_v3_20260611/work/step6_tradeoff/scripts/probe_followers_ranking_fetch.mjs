import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(scriptDir, '..', '..', '..');
const outputDir = join(packageRoot, 'data', 'cohort', 'collected');
const outPath = join(outputDir, '_upper_band_followers_fetch_probe.json');
const url = 'https://viewership.softc.one/ranking/followers?platform=naverchzzk';

mkdirSync(outputDir, { recursive: true });

const startedAt = new Date().toISOString();
const result = {
  generated_at: startedAt,
  url,
  raw_html_saved: false,
  secret_values_logged: false,
};

try {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    },
  });
  const text = await response.text();
  result.status = response.status;
  result.ok = response.ok;
  result.length = text.length;
  result.has_checkpoint = text.includes('Vercel Security Checkpoint') || text.includes("We're verifying your browser");
  result.has_rsc = text.includes('__next_f') || text.includes('self.__next_f');
  result.channel_link_count = (text.match(/\/channel\/(?:naverchzzk|soop)\/[a-f0-9]{20,}/g) || []).length;
  result.follower_count_hits = (text.match(/followerCount/g) || []).length;
  result.sample_text = text.replace(/\s+/g, ' ').slice(0, 300);
} catch (error) {
  result.error = error.message;
}

writeFileSync(outPath, JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify({ outPath, status: result.status, has_checkpoint: result.has_checkpoint, has_rsc: result.has_rsc, channel_link_count: result.channel_link_count, error: result.error || null }, null, 2));
