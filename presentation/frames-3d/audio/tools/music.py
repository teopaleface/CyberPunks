"""Build the POWER cut for the film (local only: the output contains the commercial song).

Grid of the original instrumental (measured with tools/music.py analyse):
  77.00 BPM, beat P = 0.779212 s, bar = 3.116846 s, drum drop (verse bar 1 downbeat) T0 = 25.0388 s.
  Intro = 8 bars before T0 (song starts on a downbeat at 0.104 s); verse 1 = 16 bars; the hook
  downbeat (verse bar 17) is at T0 + 16 bars = 74.908 s.

Cut layout (all edits on downbeats, 8 ms linear crossfades ending just before the transient):
  film 0 ............ intro bar 2 (7 bars before the drop, short fade-in)
  film D = 7 bars ... drum drop = start of VO line 6
  then verse bars 1..K-2, then verse bars 15-16 (the turnaround into the hook),
  then the hook downbeat at post-drop bar K as a final "button" that rings out
  (decay + closing low-pass + a little reverb), so the music ends on a phrase start.
"""
import numpy as np, soundfile as sf, scipy.signal as ss

P = 0.7792115287978996
BAR = 4 * P
T0 = 25.038768119201233
PRE_BARS = 7
D = PRE_BARS * BAR          # film time of the drop
RING = 3.0                  # seconds of ring-out after the button
XF = 0.008                  # crossfade length (linear; bars are near-identical loops)
PRE = 0.008                 # edit point sits this far before the downbeat transient


def _ring_out(x, sr):
    """x: stereo audio starting at the hook downbeat. Decay + closing low-pass + reverb tail."""
    n = int(RING * sr); x = x[:n].copy(); t = np.arange(n) / sr
    # gain: hold 0.10 s, then -17.6 dB/s (-12 dB at beat 2), cosine to silence over the last 0.4 s
    db = np.where(t < 0.10, 0.0, -17.6 * (t - 0.10))
    g = 10 ** (db / 20) * np.where(t > RING - 0.4, 0.5 + 0.5 * np.cos(np.pi * (t - (RING - 0.4)) / 0.4), 1.0)
    # closing low-pass 16 kHz -> 900 Hz over 2.2 s (STFT mask, smooth)
    nfft, hop = 2048, 256
    out = np.zeros_like(x)
    for c in range(2):
        f, tt, Z = ss.stft(x[:, c], sr, nperseg=nfft, noverlap=nfft - hop, boundary="zeros")
        fc = 16000 * (900 / 16000) ** np.clip(tt / 2.2, 0, 1)
        H = 1 / np.sqrt(1 + (f[:, None] / fc[None, :]) ** 4)
        _, y = ss.istft(Z * H, sr, nperseg=nfft, noverlap=nfft - hop, boundary=True)
        out[:, c] = y[:n]
    dry = out * g[:, None]
    # reverb: the first 0.55 s of the hit through a decorrelated stereo noise IR (RT60 2.4 s, damped)
    rng = np.random.default_rng(7)
    ni = int(2.6 * sr); ti = np.arange(ni) / sr
    env = 10 ** (-3 * ti / 2.4)
    b, a = ss.butter(2, 5500 / (sr / 2))
    ir = np.stack([ss.lfilter(b, a, rng.standard_normal(ni)) * env for _ in range(2)], 1)
    ir[: int(0.012 * sr)] = 0  # pre-delay
    ir /= np.sqrt((ir ** 2).sum(0))
    src = x[: int(0.55 * sr)] * np.hanning(int(1.1 * sr))[int(0.55 * sr):, None] ** 0.5
    wet = np.stack([ss.fftconvolve(src[:, c], ir[:, c])[:n] for c in range(2)], 1)
    wet *= 10 ** (-15 / 20) * np.where(t > RING - 0.6, 0.5 + 0.5 * np.cos(np.pi * (t - (RING - 0.6)) / 0.6), 1.0)[:, None]
    return dry + wet


def build(full_path, K):
    """Return (cut stereo float32 @48k, sr, edits, total_seconds). K = post-drop bar of the button."""
    assert 2 <= K <= 16
    x, sr = sf.read(full_path, dtype="float32")
    S = lambda t: int(round(t * sr))
    segs = [  # (film_start, orig_start, orig_end)
        (0.0, T0 - PRE_BARS * BAR, T0 + (K - 2) * BAR),
        (D + (K - 2) * BAR, T0 + 14 * BAR, T0 + 16 * BAR),
    ]
    if K == 16:  # contiguous, no splice needed
        segs = [(0.0, T0 - PRE_BARS * BAR, T0 + 16 * BAR)]
    button_film = D + K * BAR
    total = button_film + RING
    out = np.zeros((S(total), 2), np.float32)
    xf = S(XF)
    edits = []
    ramp = np.linspace(0, 1, xf, dtype=np.float32)[:, None]  # linear: the looped bars are correlated
    for i, (fs, o0, o1) in enumerate(segs):
        a = S(fs - PRE) if i else 0
        b = S(o0 - PRE) if i else S(o0)
        L = S(o1 - PRE) - b
        if i:  # crossfade window ends 8 ms before the downbeat, so the new bar's transient is intact
            out[a - xf: a] = out[a - xf: a] * (1 - ramp) + x[b - xf: b] * ramp
            edits.append({"film_s": round(fs, 4), "from_orig_s": round(prev_o1, 4), "to_orig_s": round(o0, 4)})
        out[a: a + L] = x[b: b + L]
        prev_end, prev_o1 = b + L, o1
    # button: hook downbeat (orig T0 + 16 bars) ringing out; the source continues from verse bar 16
    hb = S(T0 + 16 * BAR - PRE)
    a = S(button_film - PRE)
    if prev_end != hb:
        out[a - xf: a] = out[a - xf: a] * (1 - ramp) + x[hb - xf: hb] * ramp
    tail = _ring_out(x[hb: hb + S(RING)], sr)
    m = min(len(tail), len(out) - a)
    out[a: a + m] = tail[:m]
    # gentle fade-in at film 0 (we enter the intro at bar 2)
    fi = S(0.25); out[:fi] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi)))[:, None]
    info = {
        "source_original_s": [round(T0 - PRE_BARS * BAR, 4)],
        "segments": [{"film_start_s": round(fs, 4), "orig_start_s": round(o0, 4), "orig_end_s": round(o1, 4)} for fs, o0, o1 in segs]
                    + [{"film_start_s": round(button_film, 4), "orig_start_s": round(T0 + 16 * BAR, 4), "orig_end_s": round(T0 + 16 * BAR + RING, 4), "note": "hook downbeat, ring-out"}],
        "edits": edits, "button_s": round(button_film, 4), "drop_s": round(D, 4),
        "bpm": round(60 / P, 3), "beat_s": P, "bar_s": BAR, "total_s": round(total, 4),
    }
    return out, sr, info


def grid(K):
    """Analytic beat grid of the cut in film seconds (constant 77 BPM, film 0 = downbeat)."""
    n_beats = int(round((D + K * BAR) / P))
    return [{"t": round(i * P, 4), "bar": i // 4 - PRE_BARS, "beat": i % 4 + 1} for i in range(n_beats + 1)]


def detect(cut, sr, K):
    """Detect beats in the cut (librosa), then refine each to the nearest onset peak. Returns
    per-grid-beat detected times (None where the intro is too soft to find a beat)."""
    import librosa
    m = cut.mean(1)
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    tempo, frames = librosa.beat.beat_track(y=y, sr=22050, hop_length=256, start_bpm=77, tightness=400)
    bt = librosa.frames_to_time(frames, sr=22050, hop_length=256)
    hop = 64
    oenv = librosa.onset.onset_strength(y=m, sr=sr, hop_length=hop, n_fft=2048, lag=1, max_size=1)
    ot = librosa.frames_to_time(np.arange(len(oenv)), sr=sr, hop_length=hop)
    res = []
    for g in grid(K):
        near = bt[np.abs(bt - g["t"]) < 0.12]
        if len(near) == 0:
            res.append(None); continue
        k = (ot > g["t"] - 0.05) & (ot < g["t"] + 0.05)
        res.append(round(float(ot[k][np.argmax(oenv[k])]), 4))
    return float(np.atleast_1d(tempo)[0]), res
