// One frame per v3 scene (decoded from the rendered MP4) -> film_v3/stills/v3_strip.jpg
//   node render/v3_strip.mjs film_v3/renders/local/daybreak_v3_draft.mp4
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FILM = path.resolve(HERE, '..', 'film_v3');
const mp4 = path.resolve(process.argv[2] || path.join(FILM, 'renders/local/daybreak_v3_draft.mp4'));
const src = fs.readFileSync(path.join(FILM, 'assets/timing.js'), 'utf8');
const V = JSON.parse(src.slice(src.indexOf('{'), src.lastIndexOf('}') + 1));
// one moment per script line: just after its key line has landed
const shots = V.lines.map((l) => ({ n: l.n, t: Math.min(l.end + 0.15, (V.lines[l.n] ? V.lines[l.n].start - 0.3 : V.duration - 0.5)), label: `${l.n} · ${l.screen.join(' ')}` }));
const tmp = fs.mkdtempSync('/tmp/v3strip-');
shots.forEach((s, i) => execFileSync('ffmpeg', ['-v', 'error', '-ss', s.t.toFixed(3), '-i', mp4, '-frames:v', '1', '-vf', 'scale=640:360', path.join(tmp, `f${String(i).padStart(2, '0')}.png`)]));
const py = `
import glob, json, sys
from PIL import Image, ImageDraw, ImageFont
labels = json.loads(sys.argv[1]); fs = sorted(glob.glob(sys.argv[2] + '/f*.png'))
W, H, pad, L, cols = 640, 360, 12, 30, 4
rows = (len(fs) + cols - 1) // cols
sh = Image.new('RGB', (cols * W + (cols + 1) * pad, rows * (H + L + pad) + pad), (0, 15, 30))
d = ImageDraw.Draw(sh); font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 17)
for i, f in enumerate(fs):
    x = pad + (i % cols) * (W + pad); y = pad + (i // cols) * (H + L + pad)
    d.text((x, y + 6), labels[i][:70], fill=(245, 247, 250), font=font); sh.paste(Image.open(f).convert('RGB'), (x, y + L))
sh.save(sys.argv[3], quality=90)
`;
const out = path.join(FILM, 'stills', 'v3_strip.jpg');
fs.mkdirSync(path.dirname(out), { recursive: true });
execFileSync('python3', ['-c', py, JSON.stringify(shots.map((s) => `${s.label}  (t ${s.t.toFixed(1)})`)), tmp, out]);
console.log(out);
