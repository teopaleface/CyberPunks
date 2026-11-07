"""Render every VO line with Kokoro (kokoro-onnx, Apache-2.0) for each voice.
usage: python tts.py <kokoro-v1.0.onnx> <voices-v1.0.bin> <out_vo_dir> [voice|all] [line|all]
Each sentence is rendered separately and joined with the pause given in lines.py."""
import sys, os, json, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import LINES, VOICES

BASE_SPEED = 0.93
# Banat is stressed on the last syllable in Romanian (ba-NAT); Kokoro's default says BAN-at.
PHONEME_FIX = {"bˈænæt": "banˈat", "bˈanat": "banˈat"}
# Per-line phoneme tweaks for words whisper heard wrong in the full line (see README):
# af_heart swallowed the -d of "planned" before "tonight" (also in the full mix): a slightly longer
# vowel and a rounder "to-" keep it audible; am_michael reduced "at" to "a".
PH_LINE = {
    ("af_heart", 13): [("plˈænd tənˈaɪt", "plˈæːnd tʊnˈaɪt")],
    ("am_michael", 11): [("lˈiːv æt", "lˈiːv ˌæt")],
}
# Per-line speed overrides found by tools/fix.py (whisper check); everything else uses BASE_SPEED.
SPEED = {
}

def trim(x, sr, thr_db=-48, pad_in=0.03, pad_out=0.08):
    win = int(0.01 * sr)
    e = np.sqrt(np.convolve(x.astype(np.float64) ** 2, np.ones(win) / win, "same"))
    idx = np.where(e > e.max() * 10 ** (thr_db / 20))[0]
    a = max(0, idx[0] - int(pad_in * sr)); b = min(len(x), idx[-1] + int(pad_out * sr))
    y = x[a:b].copy()
    f = int(0.008 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

def render(k, voice, idx, speed=None):
    lang = VOICES[voice]
    sp = speed or SPEED.get((voice, idx), BASE_SPEED)
    sents = next(s for i, _, s in LINES if i == idx)
    parts, sr, spans, pos = [], 24000, [], 0
    for s, gap in sents:
        ph = k.tokenizer.phonemize(s, lang)
        for a, b in list(PHONEME_FIX.items()) + PH_LINE.get((voice, idx), []): ph = ph.replace(a, b)
        y, sr = k.create(ph, voice=voice, speed=sp, lang=lang, is_phonemes=True)
        seg = trim(np.asarray(y, dtype=np.float32), sr)
        parts.append(seg)
        spans.append({"text": s, "start": (pos + int(0.03 * sr)) / sr, "end": (pos + len(seg) - int(0.08 * sr)) / sr})
        pos += len(seg)
        if gap:
            parts.append(np.zeros(int(gap * sr), np.float32)); pos += int(gap * sr)
    return np.concatenate(parts), sr, sp, spans

if __name__ == "__main__":
    from kokoro_onnx import Kokoro
    model, voices_bin, out = sys.argv[1:4]
    ov = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "all" else None
    ol = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "all" else None
    k = Kokoro(model, voices_bin)
    for voice in VOICES:
        if ov and voice != ov: continue
        os.makedirs(f"{out}/{voice}", exist_ok=True)
        meta_path = f"{out}/{voice}/lines.json"
        meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
        for idx, text, _ in LINES:
            if ol and idx != ol: continue
            y, sr, sp, spans = render(k, voice, idx)
            sf.write(f"{out}/{voice}/line_{idx:02d}.wav", y, sr, subtype="PCM_24")
            # sentence spans in line-local seconds: speech onset/offset of each rendered sentence
            meta[str(idx)] = {"text": text, "speed": sp, "sr": sr, "duration": len(y) / sr, "sentences": spans}
            print(voice, idx, sr, sp, round(len(y) / sr, 2))
        json.dump(meta, open(meta_path, "w"), indent=1, ensure_ascii=False)
