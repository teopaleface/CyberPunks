"""Re-render lines that whisper got wrong, trying nearby speeds, and keep the first that passes.
usage: python fix.py <onnx> <voices.bin> <vo_dir> voice:line [voice:line ...]"""
import sys, os, re, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kokoro_onnx import Kokoro
from tts import render
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check.py")).read().split("vo, out = sys.argv")[0]
ns = {"__file__": os.path.abspath(__file__)}; exec(src, ns)
from lines import LINES
k = Kokoro(sys.argv[1], sys.argv[2]); vo = sys.argv[3]
for job in sys.argv[4:]:
    voice, idx = job.split(":"); idx = int(idx)
    text = next(t for i, t, _ in LINES if i == idx)
    for sp in [0.93, 0.94, 0.92, 0.95, 0.91, 0.96, 0.90]:
        y, sr, _, _ = render(k, voice, idx, sp)
        path = f"/tmp/dbk/cand_{voice}_{idx}.wav"; sf.write(path, y, sr, subtype="PCM_24")
        heard = " ".join(w for w, _, _ in ns["transcribe"](path, text))
        ok = ns["norm"](heard) == ns["norm"](text)
        print(voice, idx, sp, "OK " if ok else "BAD", heard, flush=True)
        if ok:
            os.replace(path, f"{vo}/{voice}/line_{idx:02d}.wav"); print("  -> SPEED[(%r, %d)] = %s" % (voice, idx, sp)); break
