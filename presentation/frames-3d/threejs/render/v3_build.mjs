// Daybreak film v3: ONE timing table -> assets/timing.js, index.html scene hosts,
// ledger.json (+ ledger.stamp.json) and the stamped seams.
//
//   node render/v3_build.mjs            (uses ../audio/timing.json when present, else estimates)
//
// Every composition reads window.V3 (line/word/beat times), so swapping in the audio team's
// timing.json is a data change: re-run this script, then lint + gate + render.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FILM = path.resolve(HERE, '..', 'film_v3');
const AUDIO = path.resolve(HERE, '..', '..', 'audio');
const STAMP = path.join(process.env.HOME, '.claude/skills/motion-doctrine/scripts/seam-stamp.mjs');

const LINES = [
  { n: 1, vo: 'A storm hits Banat.', screen: ['A storm hits Banat.'] },
  { n: 2, vo: 'Poles fall. Houses go dark.', screen: ['Poles fall.', 'Houses go dark.'] },
  { n: 3, vo: 'Meters get tampered with. Rooftop solar overloads the grid.', screen: ['Meters get tampered with.', 'Rooftop solar overloads the grid.'] },
  { n: 4, vo: 'Tomorrow, eleven crews must fix five hundred and fifty-six problems.', screen: ['11 crews.', '556 problems.'] },
  { n: 5, vo: 'Where should each crew go?', screen: ['Where should each crew go?'] },
  { n: 6, vo: 'Daybreak plans it for you.', screen: ['Daybreak'] },
  { n: 7, vo: 'It finds the problems,', screen: ['It finds the problems.'] },
  { n: 8, vo: 'puts the urgent ones first,', screen: ['Urgent ones first.'] },
  { n: 9, vo: 'and plans the shortest route for every crew.', screen: ['The shortest route for every crew.'] },
  { n: 10, vo: "Is this meter really tampered with? When Daybreak isn't sure, the dispatcher decides.", screen: ['Is this meter really tampered with?', 'Not sure? The dispatcher decides.'] },
  { n: 11, vo: 'Crews leave at daybreak.', screen: ['Crews leave at daybreak.'] },
  { n: 12, vo: 'Thirty percent less driving. Fewer wasted trips.', screen: ['30% less driving.', 'Fewer wasted trips.'] },
  { n: 13, vo: "Daybreak. Tomorrow's crews, planned tonight.", screen: ['Daybreak', "Tomorrow's crews, planned tonight."] },
];

// ---------------------------------------------------------------- timing
function estimate() {
  const slots = [4.0, 4.2, 5.6, 5.2, 3.4, 3.4, 2.6, 2.6, 3.8, 6.6, 3.4, 4.4, 5.4];
  let t = 0.6;
  const lines = LINES.map((L, i) => {
    const words = L.vo.split(/\s+/);
    let w = t;
    const W = words.map((word) => {
      const d = 0.2 + 0.035 * word.replace(/[^A-Za-z]/g, '').length;
      const o = { w: word, start: +w.toFixed(3), end: +(w + d).toFixed(3) };
      w += d + (/[.,?]$/.test(word) ? 0.28 : 0.04);
      return o;
    });
    const o = { ...L, start: +t.toFixed(3), end: W[W.length - 1].end, words: W };
    t += slots[i];
    return o;
  });
  const drop = lines[5].start;
  const beats = [];
  for (let b = drop - 0.7895 * 12; b < t; b += 0.7895) if (b > 0) beats.push(+b.toFixed(3));
  return { source: 'estimate', duration: +t.toFixed(3), drop, beats, lines };
}

function fromAudio(j) {
  // tolerant reader for the audio team's timing.json
  const arr = j.lines || j.vo || j.segments || [];
  const lines = LINES.map((L, i) => {
    const a = arr.find((x) => (x.index ?? x.n ?? x.line ?? x.id) == L.n) || arr[i];
    const ws = (a.words || []).map((w) => ({ w: w.word ?? w.w ?? w.text, start: +(w.start ?? w.t0), end: +(w.end ?? w.t1) }));
    return { ...L, start: +(a.start ?? a.t0 ?? ws[0]?.start), end: +(a.end ?? a.t1 ?? ws[ws.length - 1]?.end), words: ws };
  });
  const m = j.music || {};
  const drop = +(m.drop ?? j.drop ?? lines[5].start);
  let beats = (m.beats || j.beats || []).map((b) => +(typeof b === "object" ? b.t : b)).filter((b) => isFinite(b));
  const duration = +(j.total_duration ?? j.duration ?? m.duration ?? (lines[12].end + 2.8));
  if (!beats.length && m.beat_s) { // beat grid from the drop and the beat length
    const bs = +m.beat_s;
    for (let b = drop - bs * Math.floor(drop / bs); b < duration; b += bs) beats.push(+b.toFixed(3));
  }
  return { source: 'audio/timing.json', duration: +duration.toFixed(3), drop, beats, lines, button: m.button ? +m.button : null, sfx: j.sfx || [] };
}

const tj = path.join(AUDIO, 'timing.json');
const V = fs.existsSync(tj) ? fromAudio(JSON.parse(fs.readFileSync(tj, 'utf8'))) : estimate();
V.duration = +Math.max(V.duration, V.lines[12].end + 2.6).toFixed(3); // end hold >= 2.5 s
const L = (n) => V.lines[n - 1];
const word = (n, re) => (L(n).words.find((w) => re.test(w.w)) || L(n).words[0]).start;
const LEAD = 0.12; // a seam lands just before the line's first word
// scenes: [id, first line, last line]
const SC = [
  ['s01', 1], ['s02', 2], ['s03', 3], ['s04', 4], ['s06', 6], ['s07', 7], ['s10', 10], ['s11', 11], ['s12', 12], ['s13', 13],
];
V.scenes = {};
SC.forEach(([id, n], i) => {
  const start = i === 0 ? 0 : +(L(n).start - LEAD).toFixed(3);
  const next = SC[i + 1];
  const end = next ? +(L(next[1]).start - LEAD).toFixed(3) : V.duration;
  V.scenes[id] = { start, end, dur: +(end - start).toFixed(3) };
});
// named word cues used by the scenes
V.cue = {
  houses: word(2, /^Houses/), dark: word(2, /^dark/),
  rooftop: word(3, /^Rooftop/),
  eleven: word(4, /^eleven/), problems4: word(4, /^problems/), five: word(4, /^five/),
  daybreak6: word(6, /^Daybreak/),
  urgent: word(8, /^urgent/), route: word(9, /^route/), every: word(9, /^every/),
  when: word(10, /^When/), decides: word(10, /^decides/),
  fewer: word(12, /^Fewer/), thirty: word(12, /^Thirty/),
  tomorrows: word(13, /^Tomorrow/),
};
V.mix = fs.existsSync(path.join(AUDIO, 'local', 'daybreak_mix.m4a'));
fs.mkdirSync(path.join(FILM, 'assets'), { recursive: true });
fs.writeFileSync(path.join(FILM, 'assets', 'timing.js'), `// generated by render/v3_build.mjs from ${V.source} - do not edit\nwindow.V3 = ${JSON.stringify(V, null, 1)};\n`);

// ---------------------------------------------------------------- index.html
const host = (id, z, track = 2, kind = 'graphics') => {
  const s = V.scenes[id];
  return `      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html"\n        data-start="${s.start}" data-duration="${s.dur}" data-track-index="${track}" data-track-kind="${kind}" data-width="1920" data-height="1080" style="z-index: ${z}"></div>`;
};
const S = V.scenes;
const audio = V.mix
  ? `      <audio id="mix" class="clip" data-start="0" data-duration="${V.duration}" data-track-index="9" data-volume="1" src="assets/audio/local/daybreak_mix.m4a"></audio>`
  : `      <!-- audio: assets/audio/local/daybreak_mix.m4a (local only) is added when the audio team delivers it -->`;
const index = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Daybreak v3 (generated by render/v3_build.mjs)</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/timing.js"></script>
    <script src="assets/plates/manifest.js"></script>
    <script src="assets/objects/manifest.js"></script>
    <script src="assets/db2d_v3.js"></script>
    <script src="assets/v3_layout.js"></script>
    <link rel="stylesheet" href="assets/theme.css" />
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #000f1e; }
      #root { background: #000f1e; } /* opaque stage ground: no white flash at any seam */
      #bg { position: absolute; inset: 0; background: #000f1e; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${V.duration}" data-width="1920" data-height="1080">
      <div id="bg" class="clip" data-start="0" data-duration="${V.duration}" data-track-index="0"></div>
${host('s01', 3)}
${host('s02', 3)}
${host('s03', 3)}
${host('s04', 3)}
${host('s06', 3)}
      <div id="s07-wrap" style="position: absolute; inset: 0; z-index: 3">
${host('s07', 3)}
      </div>
      <div id="s10-in" style="position: absolute; inset: 0; z-index: 3">
${host('s10', 3)}
      </div>
${host('s11', 3)}
${host('s12', 3)}
${host('s13', 3)}
${audio}
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      window.__timelines["main"] = tl;

      // <seams:auto>
      // </seams:auto>

      // ---- hand-authored seams (Tier-A morphs; rows kept in ledger.json) ----
      // E (${S.s07.start}): the camera keeps pushing down onto the flat map, which becomes the app's map (carrier: the map)
      tl.set("#s06", { autoAlpha: 0 }, ${S.s07.start});
      // F (${S.s10.start}): rack-focus blur-cut onto the suspicious house (outgoing opaque, blur spike, lens breathing)
      tl.fromTo("#s07-wrap", { filter: "blur(0px)", scale: 1 }, { filter: "blur(10px)", scale: 1.06, duration: 0.3, ease: "power2.in", immediateRender: false }, ${+(S.s10.start - 0.3).toFixed(3)});
      tl.set("#s07-wrap", { autoAlpha: 0 }, ${S.s10.start});
      tl.fromTo("#s10-in", { autoAlpha: 1, filter: "blur(10px)", scale: 1.06 }, { autoAlpha: 1, filter: "blur(0px)", scale: 1, duration: 0.42, ease: "power2.out", immediateRender: false }, ${S.s10.start});
      // I (${S.s13.start}): everything pulls back into the orange dot (carrier tracked in s12 and s13)
      tl.set("#s12", { autoAlpha: 0 }, ${S.s13.start});
    </script>
  </body>
</html>
`;
fs.writeFileSync(path.join(FILM, 'index.html'), index);

// ---------------------------------------------------------------- ledger
const row = (id, cut, technique, ex, en, extra = {}) => ({ id, cut, technique, exit: ex, entry: en, ...extra });
const up = (sel) => ({ selector: sel, axis: 'y', dir: -1 });
const z = (sel, dir) => ({ selector: sel, axis: 'z', dir });
const seams = [
  row('A storm -> dark', S.s02.start, 'cut-the-curve UP', up('#s01'), up('#s02')),
  row('B dark -> meter', S.s03.start, 'cut-the-curve UP', up('#s02'), up('#s03')),
  row('B2 meter -> solar', +(V.cue.rooftop - LEAD).toFixed(3), 'cut-the-curve UP (in-scene plates)', up('#m3-meter'), up('#m3-solar')),
  row('C solar -> wide', S.s04.start, 'cut-the-curve UP', up('#s03'), up('#s04')),
  row('D wide -> unfold (the drop)', S.s06.start, 'zoom-through (push)', z('#s04', 1), { ...z('#s06', 1), scanRoot: '#s06' }, { blur: 18 }),
  { id: 'E unfold -> app map', cut: S.s07.start, type: 'morph', technique: 'push continues; the flat map becomes the app map', exit: { selector: '#s06' }, entry: { selector: '#s07' }, carrier: { out: '#un-flat', in: '#pr-carrier' } },
  { id: 'F app -> house (rack focus)', cut: S.s10.start, type: 'morph', technique: 'rack-focus blur-cut', exit: { selector: '#s07-wrap' }, entry: { selector: '#s10-in' }, carrier: { out: '#pr-house', in: '#hs-house' } },
  row('G house -> dawn', S.s11.start, 'cut-the-curve UP (sun enters rising)', up('#s10-in'), up('#s11')),
  row('H dawn -> day', S.s12.start, 'cut-the-curve UP', up('#s11'), up('#s12')),
  { id: 'I day -> end (into the orange dot)', cut: S.s13.start, type: 'morph', technique: 'Z pull into the dot', exit: { selector: '#s12' }, entry: { selector: '#s13' }, carrier: { out: '#dy-pc', in: '#en-pc' } },
];
fs.writeFileSync(path.join(FILM, 'ledger.json'), JSON.stringify({ fps: 30, source: 'MOTION_SCRIPT.md rules + FILM_V3.md scenes; generated by render/v3_build.mjs', current: 'UP', seams }, null, 1));
const stampRows = seams.filter((r) => !r.type && !r.id.startsWith('B2'));
fs.writeFileSync(path.join(FILM, 'ledger.stamp.json'), JSON.stringify({ fps: 30, seams: stampRows }, null, 1));
execFileSync('node', [STAMP, '--ledger', path.join(FILM, 'ledger.stamp.json'), '--write', path.join(FILM, 'index.html')], { stdio: 'inherit' });
// the stamper hides seam selectors that never 'enter': the s10 entry wrapper is revealed by hand at its cut (seam F)
console.log(`v3 timing from ${V.source}: ${V.duration} s, drop ${V.drop}, ${V.lines.length} lines; scenes:`, Object.entries(S).map(([k, s]) => `${k} ${s.start}-${s.end}`).join(' | '));
