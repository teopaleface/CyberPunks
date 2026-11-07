"""Assemble the Daybreak film audio: VO timeline on the music grid, music cut, ducking, SFX, mix.
usage: python build.py <audio_dir> [voice ...]      (first voice = main; default af_heart am_michael bm_george)

Outputs (main voice af_heart):
  vo/vo_<voice>.wav            processed full VO track, 48 kHz stereo (no music)
  sfx_stem.wav                 procedural SFX only (no music)
  timing.json / timing_<voice>.json
  local/music_cut.wav          the POWER cut (commercial, local only)
  local/daybreak_mix.wav/.m4a  final mix (commercial, local only); alternates: local/daybreak_mix_<voice>.*
"""
import sys, os, json, re, subprocess, tempfile
import numpy as np, soundfile as sf, scipy.signal as ss, pyloudnorm as pyln
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music
from lines import LINES

SR = 48000
P, BAR, D = music.P, music.BAR, music.D
ROOT = sys.argv[1]
VOICES = sys.argv[2:] or ["af_heart", "am_michael", "bm_george"]
VO_LUFS = -16.0          # per-line loudness before the final gain
MUSIC_POST_LUFS = -20.0  # loudness of the post-drop music (unducked) before the final gain
INTRO_LIFT_DB = 2.0      # the intro is ~10 dB softer than the verse; lift it a little under the opening lines
DUCK_PRE, DUCK_POST, DUCK_DROP = -10.0, -12.0, -12.0
TARGET_LUFS, CEIL_DBTP = -14.0, -1.2

# ---------------------------------------------------------------- schedule
# gap rules (seconds between the end of one line's speech and the start of the next)
#   key: line index of the *next* line -> (min, target, max, snap)
#   snap: "grid" = speech onset on the half-beat grid (downbeat preferred), "free" = 10 ms grid
RULES = {
    1: (1.8, 2.1, 2.7, "grid"),      # music before line 1
    2: (0.7, 1.05, 1.6, "grid"), 3: (0.7, 1.05, 1.6, "grid"), 4: (0.7, 1.05, 1.6, "grid"),
    5: (0.55, 0.75, 1.1, "grid"),
    "hold": (0.95, 1.1, 1.4),          # silence after line 5 before the drop (line 6 = drop)
    7: (1.1, 1.5, 2.0, "grid"),        # after the drop: the planet unfolds into the map
    8: (0.25, 0.3, 0.42, "free"), 9: (0.25, 0.3, 0.42, "free"),
    10: (0.7, 1.0, 1.5, "grid"), 11: (0.7, 1.0, 1.5, "grid"), 12: (0.7, 1.0, 1.5, "grid"),
    13: (0.8, 1.2, 1.8, "bar"),        # final title on a downbeat
}

def snap_bonus(t):
    """small cost by grid position: downbeat 0, beat 0.008, half-beat 0.025"""
    b = t / P
    if abs(b - round(b)) > 1e-6: return 0.025
    return 0.0 if int(round(b)) % 4 == 0 else 0.008

def candidates(lo, hi, snap):
    if snap == "free": return list(np.round(np.arange(lo, hi + 1e-9, 0.01), 4))
    step = BAR if snap == "bar" else P / 2
    k0, k1 = int(np.ceil(lo / step - 1e-9)), int(np.floor(hi / step + 1e-9))
    return [k * step for k in range(k0, k1 + 1)]

RELAX = [1.0, 1.15, 1.3, 1.5, 1.8]   # if a half has no solution, widen its gap ranges step by step

def schedule(dur):
    """dur[i] = speech length of line i (onset -> offset). Returns speech onsets in film seconds.
    The two halves (before / after the drop) are solved and relaxed independently."""
    for relax in RELAX:
        pre = _pre(dur, relax)
        if pre: break
    for relax in RELAX:
        post = _post(dur, relax)
        if post: break
    return pre + post if pre and post else None

def _rule(i, relax):
    lo, tg, hi, *sn = RULES[i]
    return lo / relax, tg, hi * relax, (sn[0] if sn else None)

def _pre(dur, relax):
    rule = lambda i: _rule(i, relax)
    # pre-drop DP over lines 1..5, line 5 must end with the 'hold' before D
    lo, tg, hi, sn = rule(1)
    states = {t: ((t - tg) ** 2 + snap_bonus(t), [t]) for t in candidates(lo, hi, sn)}
    for i in range(2, 6):
        lo, tg, hi, sn = rule(i); new = {}
        for t0, (c0, path) in states.items():
            end = t0 + dur[i - 1]
            for t in candidates(end + lo, end + hi, sn):
                c = c0 + (t - end - tg) ** 2 + snap_bonus(t)
                if t not in new or c < new[t][0]: new[t] = (c, path + [t])
        states = new
    hlo, htg, hhi = RULES["hold"]; hlo /= relax; hhi *= relax
    pre = [(c + 3 * (D - t - dur[5] - htg) ** 2, p) for t, (c, p) in states.items() if hlo <= D - t - dur[5] <= hhi]
    return min(pre)[1] if pre else None

def _post(dur, relax):
    rule = lambda i: _rule(i, relax)
    states = {D: (0.0, [D])}   # line 6 at the drop
    for i in range(7, 14):
        lo, tg, hi, sn = rule(i); new = {}
        for t0, (c0, path) in states.items():
            end = t0 + dur[i - 1]
            for t in candidates(end + lo, end + hi, sn):
                if sn == "bar" and (t - D) / BAR < 2: continue
                c = c0 + (t - end - tg) ** 2 + (snap_bonus(t) if sn != "free" else 0)
                if t not in new or c < new[t][0]: new[t] = (c, path + [t])
        states = new
    return min(states.values())[1] if states else None

# ---------------------------------------------------------------- helpers
def load_line(voice, idx):
    y, sr = sf.read(f"{ROOT}/vo/{voice}/line_{idx:02d}.wav", dtype="float64")
    return ss.resample_poly(y, SR // 1000 * 1, sr // 1000) if sr != SR else y

NUM = {"11": "eleven", "556": "five hundred and fifty six", "30": "thirty"}
HOMO = {"cruise": "crews", "polls": "poles"}
def ntoks(t):
    t = t.lower().replace("%", " percent").replace("-", " ")
    for k, v in NUM.items(): t = re.sub(rf"\b{k}\b", v, t)
    return [HOMO.get(w, w) for w in re.findall(r"[a-z']+", t)]

def word_times(voice, idx, meta, asr, y_local):
    """per-word (text, start, end) in line-local seconds.
    Sentence edges are exact (we rendered each sentence and know its speech span). Internal word
    boundaries = mean of (a) whisper.cpp word boundaries and (b) a letter-weighted prior with
    phrase-final lengthening, then snapped to a real pause or a clear energy dip within 60 ms."""
    sents = meta["sentences"]
    wh = asr[voice][str(idx)]["words"]
    toks = []   # whisper words expanded to normalized tokens with proportional sub-spans
    for w, a, b in wh:
        n = ntoks(w); L = sum(len(x) for x in n) or 1; pos = a
        for x in n:
            d = (b - a) * len(x) / L; toks.append([x, pos, pos + d]); pos += d
    hop = int(0.005 * SR); win = int(0.010 * SR)
    e = np.sqrt(np.convolve(y_local ** 2, np.ones(win) / win, "same"))[::hop]
    edb = 20 * np.log10(e + 1e-9); thr = edb.max() - 38
    out, k = [], 0
    for s in sents:
        sw = s["text"].split(); b0, b1 = s["start"], s["end"]
        wb = []   # whisper spans per script word
        for w in sw:
            n = len(ntoks(w)); tt = toks[k:k + n]; k += n; wb.append((tt[0][1], tt[-1][2]))
        a0, a1 = wb[0][0], wb[-1][1]
        whb = [b0 + (x[1] - a0) * (b1 - b0) / max(a1 - a0, 1e-3) for x in wb[:-1]]
        wt = np.array([len(re.sub(r"[^A-Za-z]", "", w)) * (1.25 if j == len(sw) - 1 else 1.15 if w.endswith(",") else 1.0)
                       for j, w in enumerate(sw)], float)
        prb = list(b0 + np.cumsum(wt)[:-1] / wt.sum() * (b1 - b0))
        bnds = [0.5 * x + 0.5 * y for x, y in zip(whb, prb)]
        starts, ends = [b0] + bnds, bnds + [b1]
        for j, bnd in enumerate(bnds):
            i0 = max(0, int((bnd - 0.06) * SR / hop)); i1 = min(len(edb), int((bnd + 0.06) * SR / hop))
            seg = edb[i0:i1]
            if len(seg) < 3: continue
            quiet = np.where(seg < thr)[0]
            if len(quiet) >= 6:
                ends[j] = (i0 + quiet[0]) * hop / SR; starts[j + 1] = (i0 + quiet[-1]) * hop / SR
            elif np.median(seg) - seg.min() >= 6:
                ends[j] = starts[j + 1] = (i0 + int(np.argmin(seg))) * hop / SR
        for j in range(1, len(sw)):          # monotonic, every word at least 60 ms
            starts[j] = max(starts[j], starts[j - 1] + 0.06); ends[j - 1] = min(ends[j - 1], starts[j]); ends[j - 1] = max(ends[j - 1], starts[j - 1] + 0.06)
        out += [(w, a, b) for w, a, b in zip(sw, starts, ends)]
    assert k == len(toks), (voice, idx, k, len(toks))
    return [(w, round(a, 3), round(b, 3)) for w, a, b in out]

def ffmpeg_vo_chain(y):
    """light broadcast VO chain: HPF, small low-mid dip, gentle presence, 2:1 compression."""
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/i.wav", y.astype(np.float32), SR, subtype="FLOAT")
        af = ("highpass=f=75:poles=2,"
              "equalizer=f=280:t=q:w=1.1:g=-1.5,"
              "equalizer=f=3200:t=q:w=1.3:g=1.5,"
              "highshelf=f=8500:g=1.0,"
              "acompressor=threshold=0.08:ratio=2.5:attack=4:release=120:knee=4:makeup=1,"
              "deesser=i=0.25:m=0.5:f=0.5")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{d}/i.wav", "-af", af,
                        "-c:a", "pcm_f32le", f"{d}/o.wav"], check=True)
        return sf.read(f"{d}/o.wav", dtype="float64")[0]

def raised(n):
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, max(n, 2)))

def true_peak_db(x):
    up = ss.resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.abs(up).max() + 1e-12)

def limit(x, ceil_db):
    """look-ahead peak limiter with a 4x oversampled (true-peak) detector; 3 ms look-ahead, 80 ms release."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceil = 10 ** (ceil_db / 20); n = len(x)
    up = np.abs(ss.resample_poly(x, 4, 1, axis=0)).max(1)
    up = np.pad(up, (0, max(0, 4 * n - len(up))))[: 4 * n]
    need = np.minimum(1.0, ceil / np.maximum(up.reshape(n, 4).max(1), 1e-12))
    la = int(0.003 * SR)
    g = uniform_filter1d(minimum_filter1d(need, 2 * la + 1, mode="nearest"), la, mode="nearest")
    rel = 1 - np.exp(-1 / (0.08 * SR)); env = np.empty(n); cur = 1.0
    for i in range(n):
        v = g[i]
        cur = v if v < cur else cur + rel * (v - cur)
        env[i] = cur
    return x * env[:, None], 20 * np.log10(env.min())

# ---------------------------------------------------------------- SFX (procedural, subtle)
rng = np.random.default_rng(11)
def bp(x, lo, hi, order=2):
    b, a = ss.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band"); return ss.lfilter(b, a, x)
def sfx_tick():
    n = int(0.06 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 2500, 6500) * np.exp(-t / 0.004) * 0.6
    s += np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.012) * 0.35
    return s / np.abs(s).max()
def sfx_tock():
    n = int(0.18 * SR); t = np.arange(n) / SR
    f = 620 + 260 * np.exp(-t / 0.02); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.05) + 0.25 * np.sin(2.43 * ph) * np.exp(-t / 0.025)
    s += bp(rng.standard_normal(n), 1500, 5000) * np.exp(-t / 0.002) * 0.3
    s *= np.minimum(1, t / 0.0015)
    return s / np.abs(s).max()
def sfx_click():
    n = int(0.05 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for t0, amp in [(0.0, 1.0), (0.011, 0.55)]:
        i = int(t0 * SR); m = n - i; tt = np.arange(m) / SR
        s[i:] += bp(rng.standard_normal(m), 1800, 7000) * np.exp(-tt / 0.0025) * amp
        s[i:] += np.sin(2 * np.pi * 3400 * tt) * np.exp(-tt / 0.004) * 0.3 * amp
    return s / np.abs(s).max()
def sfx_whoosh(dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for c in range(2):
        x = rng.standard_normal(n)
        f, tt, Z = ss.stft(x, SR, nperseg=1024, noverlap=768)
        fc = 350 * (4500 / 350) ** (tt / dur) ; bw = 0.9
        H = np.exp(-0.5 * (np.log(np.maximum(f[:, None], 1) / fc[None, :]) / bw) ** 2)
        _, y = ss.istft(Z * H, SR, nperseg=1024, noverlap=768); out[:, c] = y[:n]
    env = (t / dur) ** 2.6 * np.minimum(1, (dur - t) / 0.04)
    pan = np.linspace(-0.35, 0.35, n)
    out[:, 0] *= env * np.sqrt(0.5 - pan / 2) * 1.414; out[:, 1] *= env * np.sqrt(0.5 + pan / 2) * 1.414
    return out / np.abs(out).max()

def place(buf, s, t, gain_db, pan=0.0):
    i = int(round(t * SR)); s = s if s.ndim == 2 else np.stack([s * np.sqrt(0.5 - pan / 2) * 1.414, s * np.sqrt(0.5 + pan / 2) * 1.414], 1)
    m = min(len(s), len(buf) - i)
    if m > 0: buf[i:i + m] += s[:m] * 10 ** (gain_db / 20)

# ---------------------------------------------------------------- main
def build_voice(voice, main):
    meta = json.load(open(f"{ROOT}/vo/{voice}/lines.json"))
    asr = json.load(open(f"{ROOT}/vo/asr.json"))
    on = {i: meta[str(i)]["sentences"][0]["start"] for i, _, _ in LINES}
    off = {i: meta[str(i)]["sentences"][-1]["end"] for i, _, _ in LINES}
    dur = {i: off[i] - on[i] for i in on}
    sched = schedule(dur)
    assert sched, "no schedule"
    onset = dict(zip(range(1, 14), sched))
    K = int(round((onset[13] - D) / BAR))
    end13 = onset[13] + dur[13]
    while D + K * BAR < end13 + 1.2: K += 1          # button: first downbeat >= 1.2 s after the last word
    assert K <= 16
    cut, sr, minfo = music.build(f"{ROOT}/local/power_instrumental_full.wav", K)
    total = minfo["total_s"]; N = int(round(total * SR)); N = min(N, len(cut)); cut = cut[:N].astype(np.float64)

    # --- VO: per-line loudness, placement, chain
    meter = pyln.Meter(SR)
    vo = np.zeros(N); lines_out = []
    for idx, text, _ in LINES:
        y = load_line(voice, idx)
        y *= 10 ** ((VO_LUFS - meter.integrated_loudness(np.pad(y, (0, int(0.5 * SR))))) / 20)
        start_file = onset[idx] - on[idx]
        i = int(round(start_file * SR)); vo[i:i + len(y)] += y
        words = word_times(voice, idx, meta[str(idx)], asr, y)
        lines_out.append({"index": idx, "text": text, "file": f"vo/{voice}/line_{idx:02d}.wav",
                          "file_start": round(start_file, 3),
                          "start": round(onset[idx], 3), "end": round(onset[idx] + dur[idx], 3),
                          "words": [{"word": w, "start": round(start_file + a, 3), "end": round(start_file + b, 3)} for w, a, b in words]})
    vo = ffmpeg_vo_chain(vo)[:N]
    vo = np.pad(vo, (0, N - len(vo)))
    # VO peak control: shave the plosive peaks 4.5 dB so the master limiter barely touches the voice
    vo = limit(vo[:, None], true_peak_db(vo) - 4.5)[0][:, 0]

    # --- music level and ducking automation
    post = cut[int(D * SR): int((D + 8 * BAR) * SR)]
    cut *= 10 ** ((MUSIC_POST_LUFS - meter.integrated_loudness(post)) / 20)
    g_db = np.zeros(N)
    t = np.arange(N) / SR
    g_db += np.where(t < D, INTRO_LIFT_DB, 0.0)
    # speech regions (merge if < 0.5 s apart)
    spans = sorted((l["start"], l["end"], l["index"]) for l in lines_out)
    merged = []
    for s, e, i in spans:
        if merged and s - merged[-1][1] < 0.5: merged[-1][1] = e; merged[-1][2].append(i)
        else: merged.append([s, e, [i]])
    duck = np.zeros(N)
    for s, e, ids in merged:
        depth = DUCK_DROP if 6 in ids and len(ids) == 1 else (DUCK_PRE if s < D else DUCK_POST)
        if ids[0] == 6:   # let the drum drop hit at full level, then tuck under "Daybreak plans it for you"
            a0, a1 = s + 0.05, s + 0.20
        else:
            a0, a1 = s - 0.20, s
        r0, r1 = e + 0.05, e + 0.30
        i0, i1, i2, i3 = (int(round(x * SR)) for x in (a0, a1, r0, r1))
        seg = np.zeros(i3 - i0)
        seg[: i1 - i0] = depth * raised(i1 - i0)
        seg[i1 - i0: i2 - i0] = depth
        seg[i2 - i0:] = depth * (1 - raised(i3 - i2))
        duck[i0:i3] = np.minimum(duck[i0:i3], seg)
    g_db += duck
    music_bed = cut * 10 ** (g_db / 20)[:, None]
    # music bus: the instrumental is mastered with sharp transients (~20 dB crest); shave 2.5 dB
    music_bed = limit(music_bed, true_peak_db(music_bed) - 2.5)[0]

    # --- SFX
    sfx = np.zeros((N, 2))
    l5 = onset[5]
    for k in range(int(np.ceil(l5 / P)), int(np.floor((D - 0.5 * P) / P)) + 1):   # clock ticks on the beats into the drop
        place(sfx, sfx_tick(), k * P, -33, pan=0.15 if k % 2 else -0.15)
    place(sfx, sfx_whoosh(1.0), D - 1.0, -27)
    w7 = next(l for l in lines_out if l["index"] == 7)["words"]
    tp = next(w for w in w7 if w["word"].startswith("problems"))["start"]
    for j, pan in enumerate([-0.3, 0.25, 0.05]):                                     # pins "tock" as problems light up
        place(sfx, sfx_tock(), tp + j * P / 2, -31 - 2 * j, pan)
    w10 = next(l for l in lines_out if l["index"] == 10)["words"]
    t_click = w10[-1]["end"] + 0.15                                                  # cursor clicks Approve
    place(sfx, sfx_click(), t_click, -30, 0.1)

    # --- mix, loudness, true-peak limiting
    mix = music_bed + vo[:, None] + sfx
    L = meter.integrated_loudness(mix); G = TARGET_LUFS - L; mix *= 10 ** (G / 20)
    print("  final gain %+.2f dB | TP after gain: music %.2f vo %.2f sfx %.2f mix %.2f" % (
        G, true_peak_db(music_bed) + G, true_peak_db(vo) + G, true_peak_db(sfx) + G, true_peak_db(mix)))
    pk = np.abs(mix).max(1); thr = 10 ** ((CEIL_DBTP - 0.1) / 20)
    over = np.where(pk > thr)[0] / SR
    if len(over):
        hist = np.unique(np.round(over, 1)); print("  overs before limiting: %.2f%% of samples, at" % (100 * len(over) / N), hist[:30])
    gr = 0.0
    for _ in range(3):
        if true_peak_db(mix) <= CEIL_DBTP: break
        mix, gr = limit(mix, CEIL_DBTP - 0.1)
        L = meter.integrated_loudness(mix); G += TARGET_LUFS - L; mix *= 10 ** ((TARGET_LUFS - L) / 20)
    L = meter.integrated_loudness(mix)   # final, for the log
    tag = "" if main else f"_{voice}"
    os.makedirs(f"{ROOT}/local", exist_ok=True)
    sf.write(f"{ROOT}/local/daybreak_mix{tag}.wav", mix.astype(np.float32), SR, subtype="PCM_24")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{ROOT}/local/daybreak_mix{tag}.wav",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", f"{ROOT}/local/daybreak_mix{tag}.m4a"], check=True)
    vo_st = np.stack([vo, vo], 1) * 10 ** (G / 20)   # same gain as in the mix (stems are pre-master-limiter)
    sf.write(f"{ROOT}/vo/vo_{voice}.wav", vo_st.astype(np.float32), SR, subtype="PCM_24")
    if main:
        sf.write(f"{ROOT}/local/music_cut.wav", cut.astype(np.float32), SR, subtype="PCM_24")
        sf.write(f"{ROOT}/local/music_bed_ducked.wav", (music_bed * 10 ** (G / 20)).astype(np.float32), SR, subtype="PCM_24")
        sf.write(f"{ROOT}/sfx_stem.wav", (sfx * 10 ** (G / 20)).astype(np.float32), SR, subtype="PCM_24")

    # --- beats (detected in the cut, on the analytic 77 BPM grid)
    tempo, det = music.detect(cut.astype(np.float32), SR, K)
    beats = []
    for g, dt in zip(music.grid(K), det):
        beats.append({"t": g["t"], "detected": dt, "bar": g["bar"], "beat": g["beat"], "downbeat": g["beat"] == 1})
    timing = {
        "voice": voice, "units": "seconds, film time (t=0 = first sample of the mix)",
        "total_duration": round(N / SR, 3), "sample_rate": SR,
        "music": {"track": "Kanye West - POWER (instrumental), local only", "bpm": round(60 / P, 3),
                  "beat_s": round(P, 6), "bar_s": round(BAR, 6), "drop": round(D, 3),
                  "drop_note": "drum drop = start of VO line 6", "button": minfo["button_s"],
                  "button_note": "hook downbeat; the music rings out to the end",
                  "edits": minfo["edits"], "segments": minfo["segments"],
                  "beat_detection": {"librosa_tempo": round(tempo, 2), "detected": sum(d is not None for d in det), "of": len(det)},
                  "beats": beats},
        "lines": lines_out,
        "sfx": ([{"type": "tick", "t": round(k * P, 3)} for k in range(int(np.ceil(l5 / P)), int(np.floor((D - 0.5 * P) / P)) + 1)]
                + [{"type": "whoosh", "start": round(D - 1.0, 3), "end": round(D, 3)}]
                + [{"type": "pin_tock", "t": round(tp + j * P / 2, 3)} for j in range(3)]
                + [{"type": "cursor_click", "t": round(t_click, 3)}]),
    }
    json.dump(timing, open(f"{ROOT}/timing{tag}.json", "w"), indent=1, ensure_ascii=False)
    print(voice, "K", K, "total", round(N / SR, 2), "LUFS", round(L, 2), "TP", round(true_peak_db(mix), 2), "limiter GR dB", round(gr, 2))
    for l in lines_out: print(f"  {l['index']:2d} {l['start']:6.2f}-{l['end']:6.2f}  {l['text']}")

for n, v in enumerate(VOICES):
    build_voice(v, n == 0)
