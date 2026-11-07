"""Transcribe VO lines with whisper.cpp and compare with the script.
usage: python check.py <vo_dir> <out_json> [voice ...]
Writes per-word timestamps (line-local seconds) for every line into out_json."""
import sys, os, re, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import LINES, VOICES
WHISPER = "/opt/homebrew/bin/whisper-cli"
MODEL = os.path.expanduser("~/.cache/whisper-models/ggml-large-v3-turbo.bin")
NUM = {"11": "eleven", "556": "five hundred and fifty six", "30": "thirty", "%": " percent"}

# True homophones whisper cannot tell apart from audio alone (same phonemes in Kokoro's output).
HOMOPHONES = {"cruise": "crews", "polls": "poles"}

def norm(t):
    t = t.lower().replace("%", " percent").replace("-", " ").replace("’", "'")
    for k, v in NUM.items(): t = re.sub(rf"\b{k}\b", v, t)
    return [HOMOPHONES.get(w, w) for w in re.findall(r"[a-z']+", t)]

def transcribe(path, prompt):
    with tempfile.TemporaryDirectory() as d:
        w = f"{d}/a.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-af",
                        "adelay=300:all=1,apad=pad_dur=0.5", "-ar", "16000", "-ac", "1", w], check=True)
        subprocess.run([WHISPER, "-m", MODEL, "-f", w, "-l", "en", "-ml", "1", "-sow", "-oj",
                        "-of", f"{d}/o", "-np", "-dtw", "large.v3.turbo"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segs = json.load(open(f"{d}/o.json"))["transcription"]
    words = [(s["text"].strip(), s["offsets"]["from"] / 1000 - 0.3, s["offsets"]["to"] / 1000 - 0.3)
             for s in segs if s["text"].strip()]
    return words

vo, out = sys.argv[1], sys.argv[2]
voices = sys.argv[3:] or list(VOICES)
res = json.load(open(out)) if os.path.exists(out) else {}
bad = []
for v in voices:
    res.setdefault(v, {})
    for idx, text, _ in LINES:
        if os.environ.get("CHECK_LINES") and str(idx) not in os.environ["CHECK_LINES"].split(","): continue
        words = transcribe(f"{vo}/{v}/line_{idx:02d}.wav", text)
        heard = " ".join(w for w, _, _ in words)
        ok = norm(heard) == norm(text)
        res[v][str(idx)] = {"text": text, "heard": heard, "ok": ok, "words": words}
        print(("OK  " if ok else "BAD "), v, idx, "|", heard)
        if not ok: bad.append((v, idx, heard))
json.dump(res, open(out, "w"), indent=1)
print("BAD:", bad)
