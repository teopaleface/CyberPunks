// Headless renderer: serves this folder locally, drives Google Chrome with
// Playwright, renders stills and/or the motion-test frames.
//
//   node render/render.mjs stills [--spp 256] [--beats storm,where]
//   node render/render.mjs motion [--spp 64] [--frames 180] [--fps 30]
//   node render/render.mjs probe  --beat map --t 3 --spp 32 --out /tmp/x.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const args = process.argv.slice(2);
const mode = args[0] || 'stills';
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--headless=new', '--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader=false', '--disable-gpu-watchdog', '--disable-features=Translate'],
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('console', (m) => { if (m.type() === 'error' || m.text().startsWith('[daybreak]')) console.log('  [page]', m.text()); });
page.on('pageerror', (e) => console.log('  [pageerror]', e.message));

const firstBeat = opt('beat', 'storm');
const t0 = Date.now();
await page.goto(`http://127.0.0.1:${port}/index.html?beat=${firstBeat}&spp=1`);
await page.waitForFunction(() => window.__daybreakReady === true, null, { timeout: 180000 });
const info = await page.evaluate(() => window.daybreak.info());
console.log(`scene built in ${((Date.now() - t0) / 1000).toFixed(1)} s`, info);

async function frame(beat, t, spp, out) {
  const r = await page.evaluate(({ beat, t, spp }) => {
    const ms = window.daybreak.renderFrame(beat, t, spp);
    return { ms, png: window.daybreak.png() };
  }, { beat, t, spp });
  fs.writeFileSync(out, Buffer.from(r.png.split(',')[1], 'base64'));
  return r.ms;
}

const log = [];
if (mode === 'stills') {
  const spp = +opt('spp', 256);
  const beats = opt('beats', 'storm,where,problems,map,dawn').split(',');
  fs.mkdirSync(path.join(ROOT, 'stills'), { recursive: true });
  for (const b of beats) {
    const t = await page.evaluate((b) => window.daybreak.STILL_T[b], b);
    const out = path.join(ROOT, 'stills', `${b}.png`);
    const ms = await frame(b, t, spp, out);
    console.log(`${b}: ${spp} spp, ${(ms / 1000).toFixed(2)} s render -> ${path.relative(ROOT, out)}`);
    log.push({ beat: b, t, spp, seconds: +(ms / 1000).toFixed(2) });
  }
  fs.writeFileSync(path.join(ROOT, 'stills', 'timings.json'), JSON.stringify({ info, spp, stills: log }, null, 2));
} else if (mode === 'motion') {
  const spp = +opt('spp', 64), frames = +opt('frames', 180), fps = +opt('fps', 30);
  const dir = path.join(ROOT, 'motion', 'frames');
  fs.mkdirSync(dir, { recursive: true });
  let total = 0;
  for (let i = 0; i < frames; i++) {
    const t = i / fps;
    const ms = await frame('map', t, spp, path.join(dir, `f${String(i).padStart(4, '0')}.png`));
    total += ms;
    if (i % 15 === 0) console.log(`frame ${i}/${frames} t=${t.toFixed(2)} ${(ms / 1000).toFixed(2)} s`);
  }
  const rep = { info, spp, frames, fps, renderSecondsTotal: +(total / 1000).toFixed(1), renderSecondsPerFrame: +(total / frames / 1000).toFixed(3) };
  fs.writeFileSync(path.join(ROOT, 'motion', 'timings.json'), JSON.stringify(rep, null, 2));
  console.log(rep);
} else if (mode === 'probe') {
  if (opt('override')) await page.evaluate((o) => { window.daybreak.override = JSON.parse(o); }, opt('override'));
  const ms = await frame(opt('beat', 'map'), +opt('t', 0), +opt('spp', 16), opt('out', '/tmp/daybreak_probe.png'));
  console.log(`probe ${(ms / 1000).toFixed(2)} s`);
}

await browser.close();
server.close();
