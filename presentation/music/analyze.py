#!/usr/bin/env python3
"""Verificările muzicii (nu putem asculta, așa că măsurăm).

    uv run python presentation/music/analyze.py [--out presentation/music/out]

Scrie out/report.json, out/spectrogram.png, out/waveform.png și afișează un rezumat:
loudness (calcul propriu BS.1770 și ffmpeg), vârf real, clipping, durată, liniștea de la final,
respirația dinaintea lui „reveal”, suma stem-urilor, spectrul (2-6 kHz, zona joasă),
compatibilitatea mono și dacă atacurile cad pe grila de șaisprezecimi.
"""

from __future__ import annotations

# ruff: noqa: RUF046  # int(round(x)) rămâne: x poate fi un scalar NumPy folosit ca index
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")

import argparse
import itertools
import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

SR = 48_000
BPM = 96
BEAT = 60.0 / BPM
BAR = 4 * BEAT
STEP = BEAT / 4
STEMS = ("pad", "keys", "bass", "drums", "plucks", "fx")

_K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
_K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def read_wav(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path), "rb") as w:
        nch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 3:
        raise ValueError(f"{path}: aștept 24 de biți, am {8 * sw}")
    b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
    v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
    v = np.where(v >= 1 << 23, v - (1 << 24), v)
    return v.reshape(-1, nch) / 8388608.0, sr, sw


def k_weight(x: np.ndarray) -> np.ndarray:
    return signal.lfilter(*_K2, signal.lfilter(*_K1, x, axis=0), axis=0)


def lufs_integrated(x: np.ndarray) -> float:
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.vstack([np.zeros((1, y.shape[1])), np.cumsum(y**2, axis=0)])
    starts = np.arange(0, len(y) - blk + 1, hop)
    ms = ((c[starts + blk] - c[starts]) / blk).sum(axis=1)
    lk = -0.691 + 10 * np.log10(ms + 1e-20)
    g1 = ms[lk > -70]
    if len(g1) == 0:
        return float("-inf")
    rel = -0.691 + 10 * np.log10(g1.mean()) - 10
    g2 = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def loudness_window(x: np.ndarray, t0: float, t1: float) -> float:
    """Loudness K-ponderată (fără porți) pe o fereastră: bună pentru comparat secțiuni și stem-uri."""
    y = k_weight(x)[int(t0 * SR):int(t1 * SR)]
    ms = np.mean(y**2, axis=0).sum()
    return float(-0.691 + 10 * np.log10(ms + 1e-20))


def true_peak_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.max(np.abs(signal.resample_poly(x, 4, 1, axis=0))) + 1e-20))


def rms_db(x: np.ndarray) -> float:
    return float(10 * np.log10(np.mean(x**2) + 1e-20))


def ffmpeg_measure(path: Path) -> dict:
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    if not Path(ffmpeg).exists():
        return {"error": "ffmpeg lipsește"}
    res = {}
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-af",
                        "loudnorm=I=-16:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=False)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.DOTALL)
    if m:
        j = json.loads(m.group(0))
        res["loudnorm"] = {k: j[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh")}
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true+sample",
                        "-f", "null", "-"], capture_output=True, text=True, check=False)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    for key, pat in (("integrated_lufs", r"I:\s+(-?[\d.]+) LUFS"), ("lra_lu", r"LRA:\s+(-?[\d.]+) LU"),
                     ("true_peak_dbfs", r"True peak:\s+Peak:\s+(-?[\d.inf]+) dBFS"),
                     ("sample_peak_dbfs", r"Sample peak:\s+Peak:\s+(-?[\d.inf]+) dBFS")):
        mm = re.search(pat, tail)
        if mm:
            res.setdefault("ebur128", {})[key] = float(mm.group(1))
    p = subprocess.run([ffmpeg.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries",
                        "stream=sample_rate,channels,bits_per_sample,duration_ts,duration,codec_name",
                        "-of", "json", str(path)], capture_output=True, text=True, check=False)
    if p.returncode == 0:
        res["ffprobe"] = json.loads(p.stdout)["streams"][0]
    return res


def band_db(freqs: np.ndarray, psd: np.ndarray, lo: float, hi: float) -> float:
    m = (freqs >= lo) & (freqs < hi)
    return float(10 * np.log10(np.trapezoid(psd[m], freqs[m]) + 1e-30))


def spectrum_checks(mix: np.ndarray, groove: tuple[float, float]) -> dict:
    mono = mix.mean(axis=1)
    seg = mono[int(groove[0] * SR):int(groove[1] * SR)]
    f, p = signal.welch(seg, fs=SR, nperseg=8192, noverlap=6144)
    pdb = 10 * np.log10(p + 1e-30)
    bands = {name: band_db(f, p, lo, hi) for name, lo, hi in (
        ("sub_20_60", 20, 60), ("bass_60_120", 60, 120), ("lowmid_120_300", 120, 300),
        ("mid_300_2k", 300, 2000), ("presence_2k_6k", 2000, 6000), ("air_6k_16k", 6000, 16000))}
    ref = bands["mid_300_2k"]
    return {
        "window_s": list(groove),
        "bands_db_rel_mid": {k: round(v - ref, 2) for k, v in bands.items()},
        "spectrum": (f, pdb),
    }


def third_octave(mix: np.ndarray, window: tuple[float, float]) -> dict:
    """Benzi de 1/3 de octavă. „Aspru” = o bandă din 2-6,3 kHz care iese cu peste 3 dB deasupra pantei
    potrivite pe 500 Hz-10 kHz. „Boomy” = 125-250 Hz mult peste 500 Hz-1 kHz."""
    mono = mix.mean(axis=1)[int(window[0] * SR):int(window[1] * SR)]
    f, p = signal.welch(mono, fs=SR, nperseg=16384, noverlap=12288)
    centers = 1000.0 * 2.0 ** (np.arange(-17, 14) / 3.0)
    lv = np.array([band_db(f, p, c / 2 ** (1 / 6), c * 2 ** (1 / 6)) for c in centers])
    sel = (centers >= 500) & (centers <= 10000)
    slope, icpt = np.polyfit(np.log2(centers[sel]), lv[sel], 1)
    resid = lv - (slope * np.log2(centers) + icpt)
    hb = (centers >= 1900) & (centers <= 6400)
    lowmid = lv[(centers >= 120) & (centers <= 260)].mean() - lv[(centers >= 490) & (centers <= 1010)].mean()
    bump = lv[1:-1] - 0.5 * (lv[:-2] + lv[2:])  # cât iese o bandă peste media vecinelor (vârf îngust)
    cb = centers[1:-1]
    hb2 = (cb >= 1900) & (cb <= 6400)
    return {
        "max_local_bump_2k_6k_db": round(float(bump[hb2].max()), 2),
        "max_local_bump_2k_6k_at_hz": round(float(cb[hb2][np.argmax(bump[hb2])]), 0),
        "window_s": list(window),
        "slope_db_per_octave_500_10k": round(float(slope), 2),
        "max_excess_2k_6k_db": round(float(resid[hb].max()), 2),
        "max_excess_2k_6k_at_hz": round(float(centers[hb][np.argmax(resid[hb])]), 0),
        "lowmid_125_250_minus_500_1k_db": round(float(lowmid), 2),
        "bands_db": {f"{c:.0f}": round(float(v - lv.max()), 1) for c, v in zip(centers, lv)},
    }


def mono_checks(mix: np.ndarray) -> dict:
    l, r = mix[:, 0], mix[:, 1]
    side = 0.5 * (l - r)
    mid = 0.5 * (l + r)
    lp = signal.butter(4, 120, "lowpass", fs=SR, output="sos")
    side_lo = signal.sosfilt(lp, side)
    mid_lo = signal.sosfilt(lp, mid)
    corr = float(np.sum(l * r) / np.sqrt(np.sum(l**2) * np.sum(r**2)))
    return {
        "lr_correlation": round(corr, 3),
        "side_below_120_vs_mid_below_120_db": round(rms_db(side_lo) - rms_db(mid_lo), 1),
        "mono_vs_stereo_loudness_db": round(lufs_integrated(np.stack([mid, mid], 1)) - lufs_integrated(mix), 2),
    }


HOP = 48  # 1 ms


def onset_strength(mono: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Flux spectral cu pas de 1 ms; cadrul de referință trece printr-un filtru de maxim pe frecvență
    (ca în SuperFlux), ca bătăile lente dintre voci și tremolo-ul să nu pară atacuri."""
    nfft = 1024
    _f, t, z = signal.stft(mono, fs=SR, nperseg=nfft, noverlap=nfft - HOP, boundary=None, padded=False)
    mag = np.log1p(100 * np.abs(z))
    ref = ndimage.maximum_filter1d(mag, size=3, axis=0)
    lag = 3
    flux = np.maximum(0.0, mag[:, lag:] - ref[:, :-lag]).sum(axis=0)
    return t, np.concatenate([np.zeros(lag), flux])


def pick_onsets(t: np.ndarray, flux: np.ndarray) -> np.ndarray:
    hop_s = HOP / SR
    loc = ndimage.maximum_filter1d(flux, size=2 * int(0.03 / hop_s) + 1)
    mean = ndimage.uniform_filter1d(flux, size=int(0.25 / hop_s))
    thr = 1.6 * mean + 0.05 * np.percentile(flux, 99.5)
    return t[(flux == loc) & (flux > thr)]


_OFFSET: list[float] = []


def detector_offset() -> float:
    """Întârzierea detectorului, măsurată pe un tren de clicuri sintetice cu momente cunoscute."""
    if not _OFFSET:
        rng = np.random.default_rng(1)
        known = np.arange(0.5, 3.6, 0.3125)
        x = np.zeros(int(4 * SR))
        ln = int(0.03 * SR)
        for tk in known:
            i = int(round(tk * SR))
            x[i:i + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / (0.004 * SR)) * 0.3
        det = pick_onsets(*onset_strength(x))
        _OFFSET.append(float(np.median([det[np.argmin(np.abs(det - k))] - k for k in known])))
    return _OFFSET[0]


def onsets(x: np.ndarray) -> np.ndarray:
    mono = x.mean(axis=1) if x.ndim == 2 else x
    return pick_onsets(*onset_strength(mono)) - detector_offset()


def grid_report(times: np.ndarray, accents: dict, events: dict | None = None) -> dict:
    dev = (times / STEP - np.round(times / STEP)) * STEP
    ok10 = np.abs(dev) <= 0.010
    ok_frame = np.abs(dev) <= 1 / 60  # jumătate de cadru la 30 fps
    named = {}
    for name, v in accents.items():
        if name in ("silence_start", "silent_from", "pad_in"):
            continue
        items = v if isinstance(v, list) else [v]
        res = []
        for it in items:
            tt = it["time"]
            near = times[np.abs(times - tt) <= 0.03]
            res.append({"time": tt, "onset_error_ms": round(float((near[np.argmin(np.abs(near - tt))] - tt) * 1000), 1)
                        if len(near) else None})
        named[name] = res
    rep = {
        "detector_offset_ms": round(detector_offset() * 1000, 2),
        "count": int(len(times)),
        "within_10ms_of_16th_grid": int(ok10.sum()),
        "within_half_frame_of_16th_grid": int(ok_frame.sum()),
        "median_abs_dev_ms": round(float(np.median(np.abs(dev)) * 1000), 2) if len(dev) else None,
        "p95_abs_dev_ms": round(float(np.percentile(np.abs(dev), 95) * 1000), 2) if len(dev) else None,
        "off_grid_onsets": [round(float(tt), 4) for tt, ok in zip(times, ok10) if not ok],
        "accents": named,
    }
    if events:
        sched = np.array(sorted({t for ts in events.values() for t in ts}))
        err = [float(times[np.argmin(np.abs(times - s))] - s) for s in sched if np.min(np.abs(times - s)) <= 0.025]
        rep["scheduled_hits"] = int(len(sched))
        rep["scheduled_hits_detected"] = int(len(err))
        rep["detected_minus_scheduled_median_ms"] = round(float(np.median(err)) * 1000, 2) if err else None
        rep["detected_minus_scheduled_p95_abs_ms"] = round(float(np.percentile(np.abs(err), 95)) * 1000, 2) if err \
            else None
    return rep


def plots(out: Path, mix: np.ndarray, cues: dict, spec: tuple[np.ndarray, np.ndarray]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dur = len(mix) / SR
    bars = cues["bars"]
    bg, fg, grid_c, accent = "#0e0f12", "#e8e6e1", "#3a3d45", "#f2b34a"

    # waveform cu linii de măsură
    fig, ax = plt.subplots(figsize=(16, 5.2), dpi=130, facecolor=bg)
    ax.set_facecolor(bg)
    mono = mix.mean(axis=1)
    px = 3000
    edges = np.linspace(0, len(mono), px + 1).astype(int)
    lo = np.array([mono[a:b].min() for a, b in itertools.pairwise(edges)])
    hi = np.array([mono[a:b].max() for a, b in itertools.pairwise(edges)])
    tt = (edges[:-1] + edges[1:]) / 2 / SR
    ax.fill_between(tt, lo, hi, color="#8fb8de", linewidth=0)
    y = k_weight(mix)
    win = int(0.4 * SR)
    c = np.concatenate([[0], np.cumsum((y**2).sum(axis=1))])
    idx = np.arange(0, len(mono) - win, int(0.05 * SR))
    mom = -0.691 + 10 * np.log10((c[idx + win] - c[idx]) / win + 1e-20)
    ax2 = ax.twinx()
    ax2.plot((idx + win / 2) / SR, mom, color=accent, linewidth=1.1, label="loudness momentană (LUFS)")
    ax2.set_ylim(-60, 0)
    ax2.tick_params(colors=fg, labelsize=8)
    ax2.set_ylabel("LUFS momentan (400 ms)", color=accent, fontsize=9)
    for b in bars:
        ax.axvline(b["start"], color=grid_c, linewidth=0.8)
        ax.text(b["start"] + 0.05, 0.97, f"{b['bar']}\n{b['section']}", color=fg, fontsize=7.5, va="top",
                transform=ax.get_xaxis_transform())
    acc = cues["accents"]
    ax.axvspan(acc["silence_start"]["time"], acc["reveal"]["time"], color="#ffffff", alpha=0.08)
    ax.axvspan(acc["silent_from"]["time"], dur, color="#ffffff", alpha=0.08)
    ax.set_xlim(0, dur)
    ax.set_ylim(-1, 1)
    ax.set_xticks(np.arange(0, dur + 0.01, 2.5))
    ax.tick_params(colors=fg, labelsize=8)
    ax.set_xlabel("secunde (o linie = o măsură de 2,5 s = 75 de cadre)", color=fg, fontsize=9)
    ax.set_title("Tura de mâine — formă de undă (mono), loudness momentană, linii de măsură", color=fg,
                 fontsize=11, loc="left")
    for s in list(ax.spines.values()) + list(ax2.spines.values()):
        s.set_color(grid_c)
    fig.tight_layout()
    fig.savefig(out / "waveform.png", facecolor=bg)
    plt.close(fig)

    # spectrogramă (frecvență logaritmică) plus spectrul mediu al groove-ului
    fig = plt.figure(figsize=(16, 7.5), dpi=130, facecolor=bg)
    gs = fig.add_gridspec(1, 2, width_ratios=[5, 1.1], wspace=0.04)
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor(bg)
    f, t, z = signal.stft(mono, fs=SR, nperseg=4096, noverlap=4096 - 480)
    s_db = 20 * np.log10(np.abs(z) + 1e-9)
    s_db -= s_db.max()
    keep = (f >= 20) & (f <= 20000)
    mesh = ax.pcolormesh(t, f[keep], s_db[keep], shading="auto", cmap="magma", vmin=-95, vmax=0, rasterized=True)
    ax.set_yscale("log")
    ax.set_ylim(25, 20000)
    ax.axhspan(2000, 6000, color="#5ad1ff", alpha=0.06)
    for b in bars:
        ax.axvline(b["start"], color="#ffffff", alpha=0.35, linewidth=0.8)
        ax.text(b["start"] + 0.05, 21000, f"{b['bar']} {b['section']}", color=fg, fontsize=7, rotation=0,
                va="bottom")
    ax.set_xlim(0, dur)
    ax.set_xticks(np.arange(0, dur + 0.01, 2.5))
    ax.tick_params(colors=fg, labelsize=8)
    ax.set_ylabel("Hz", color=fg)
    ax.set_xlabel("secunde", color=fg)
    ax.set_title("Spectrogramă (dB față de maxim); banda 2-6 kHz e marcată", color=fg, fontsize=11, loc="left",
                 pad=22)
    cb = fig.colorbar(mesh, ax=ax, pad=0.01, fraction=0.025)
    cb.ax.tick_params(colors=fg, labelsize=7)
    ax3 = fig.add_subplot(gs[1], sharey=ax)
    ax3.set_facecolor(bg)
    fs, pdb = spec
    k = (fs >= 20) & (fs <= 20000)
    ax3.plot(pdb[k] - pdb[k].max(), fs[k], color="#8fb8de", linewidth=1)
    ax3.axhspan(2000, 6000, color="#5ad1ff", alpha=0.10)
    ax3.set_xlim(-90, 3)
    ax3.tick_params(colors=fg, labelsize=7, labelleft=False)
    ax3.set_xlabel("dB (spectru mediu,\nmăsurile 6-9)", color=fg, fontsize=8)
    for a in (ax, ax3):
        for s in a.spines.values():
            s.set_color(grid_c)
    fig.savefig(out / "spectrogram.png", facecolor=bg, bbox_inches="tight")
    plt.close(fig)


def hyperframes_beats(path: Path, cues: dict) -> dict:
    """Detectorul extern de beat-uri (`npx hyperframes@0.9.19 beats --json`), comparat cu grila de 96 BPM.
    Rulează pe o copie temporară, ca să nu scrie nimic în repo."""
    import tempfile

    npx = shutil.which("npx")
    if not npx:
        return {"ran": False, "reason": "npx lipsește"}
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / path.name
        shutil.copy(path, local)
        try:
            p = subprocess.run([npx, "-y", "hyperframes@0.9.19", "beats", "--json", local.name], cwd=tmp,
                               capture_output=True, text=True, timeout=300, check=False)
        except (OSError, subprocess.SubprocessError) as e:
            return {"ran": False, "reason": str(e)}
    try:
        j = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ran": True, "ok": False, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
    beats = np.array(j.get("beatTimes", []), dtype=float)
    dev = beats - np.round(beats / BEAT) * BEAT
    # secțiunile fără atacuri ritmice (zoom, problema, pauza) nu au ce urmări: le raportăm separat
    calm = {b["bar"] for b in cues["bars"] if b["section"] in ("zoom", "problema", "pauza")}
    bar_of = (np.floor(np.round(beats / BEAT) * BEAT / BAR) + 1).astype(int)
    rhythmic = np.array([b not in calm for b in bar_of])
    rd = dev[rhythmic]
    return {
        "ran": True, "ok": bool(j.get("ok")), "bpm_detected": j.get("bpm"), "beats_detected": int(len(beats)),
        "rhythmic_sections": {"count": int(rhythmic.sum()),
                              "median_offset_ms": round(float(np.median(rd)) * 1000, 1) if len(rd) else None,
                              "spread_after_offset_ms": round(float(np.max(np.abs(rd - np.median(rd)))) * 1000, 1)
                              if len(rd) else None},
        "calm_sections_max_drift_ms": round(float(np.max(np.abs(dev[~rhythmic]))) * 1000, 1)
        if (~rhythmic).any() else None,
        "beat_times": beats.tolist(),
    }


def run(out: Path, verbose: bool = True, hyperframes: bool = False) -> dict:
    out = Path(out)
    say = print if verbose else (lambda *a, **k: None)
    mix, sr, sw = read_wav(out / "tura_96bpm_30s.wav")
    cues = json.loads((out / "cues.json").read_text(encoding="utf-8"))
    rep: dict = {}
    rep["format"] = {"sample_rate": sr, "bits": 8 * sw, "channels": mix.shape[1], "samples": len(mix),
                     "duration_s": len(mix) / sr, "exact_30s": len(mix) == 30 * sr}
    rep["loudness"] = {"integrated_lufs_internal": round(lufs_integrated(mix), 2),
                       "true_peak_dbtp_internal": round(true_peak_db(mix), 2),
                       "sample_peak_dbfs": round(float(20 * np.log10(np.max(np.abs(mix)) + 1e-20)), 2),
                       "clipped_samples": int(np.sum(np.abs(mix) >= 0.99999))}
    rep["ffmpeg"] = ffmpeg_measure(out / "tura_96bpm_30s.wav")
    acc = cues["accents"]
    s0, r0 = acc["silence_start"]["time"], acc["reveal"]["time"]
    gap = mix[int(s0 * SR) + int(0.005 * SR):int(r0 * SR)]
    gap_nofx = gap - read_wav(out / "stems" / "fx.wav")[0][int(s0 * SR) + int(0.005 * SR):int(r0 * SR)]
    tail = mix[int(29.9 * SR):]
    rep["silences"] = {
        "last_100ms_max_abs": float(np.max(np.abs(tail))),
        "last_100ms_is_digital_zero": bool(np.all(tail == 0)),
        "breath_window_s": [round(s0, 4), round(r0, 4)],
        "breath_rms_dbfs": round(rms_db(gap), 1),
        "breath_peak_dbfs": round(float(20 * np.log10(np.max(np.abs(gap)) + 1e-20)), 1),
        "breath_rms_without_fx_dbfs": round(rms_db(gap_nofx), 1),
        "level_29_0_to_29_5_rms_dbfs": round(rms_db(mix[int(29.0 * SR):int(29.5 * SR)]), 1),
        "level_29_5_to_29_9_rms_dbfs": round(rms_db(mix[int(29.5 * SR):int(29.9 * SR)]), 1),
    }
    stems = {k: read_wav(out / "stems" / f"{k}.wav")[0] for k in STEMS}
    ssum = sum(stems.values())
    err = np.max(np.abs(ssum - mix))
    rep["stems"] = {"max_abs_diff_sum_vs_mix": float(err), "max_diff_lsb_24bit": round(float(err * 8388608), 2),
                    "sum_matches_mix": bool(err * 8388608 <= 8)}
    sections = [(b["bar"], b["section"], b["start"], b["end"]) for b in cues["bars"]]
    per_bar = []
    for bar, sec, a, b in sections:
        row = {"bar": bar, "section": sec, "mix": round(loudness_window(mix, a, b), 1)}
        for k in STEMS:
            row[k] = round(loudness_window(stems[k], a, b), 1)
        per_bar.append(row)
    rep["loudness_per_bar_lufs_ungated"] = per_bar
    spec = spectrum_checks(mix, (12.5, 22.5))
    rep["spectrum"] = {k: v for k, v in spec.items() if k != "spectrum"}
    rep["third_octave_groove"] = third_octave(mix, (12.5, 22.5))
    rep["third_octave_whole"] = third_octave(mix, (0.0, 29.9))
    rep["mono"] = mono_checks(mix)
    ev = cues.get("events")
    rep["onsets"] = {"mix": grid_report(onsets(mix), acc, ev),
                     "drums_stem": grid_report(onsets(stems["drums"]), {}, {k: ev[k] for k in ("kick", "clap", "hat")}
                                               if ev else None),
                     "plucks_stem": grid_report(onsets(stems["plucks"]), {}, {"plucks": ev["plucks"]} if ev else None)}
    plots(out, mix, cues, spec["spectrum"])
    if hyperframes:
        rep["hyperframes_beats"] = hyperframes_beats(out / "tura_96bpm_30s.wav", cues)
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ff = rep["ffmpeg"]
    say("— verificări —")
    say(f"  format: {sr} Hz, {8 * sw} biți, {mix.shape[1]} canale, {len(mix)} eșantioane = {len(mix) / sr:.6f} s")
    say(f"  loudness: {rep['loudness']['integrated_lufs_internal']} LUFS (intern), "
        f"ffmpeg loudnorm I={ff.get('loudnorm', {}).get('input_i')} TP={ff.get('loudnorm', {}).get('input_tp')}, "
        f"ebur128 {ff.get('ebur128')}")
    say(f"  vârf real intern {rep['loudness']['true_peak_dbtp_internal']} dBTP, "
        f"eșantioane tăiate: {rep['loudness']['clipped_samples']}")
    say(f"  liniște: ultimele 100 ms zero digital = {rep['silences']['last_100ms_is_digital_zero']}; "
        f"respirația {s0:.4f}-{r0:.4f} s: RMS {rep['silences']['breath_rms_dbfs']} dBFS "
        f"(fără fx {rep['silences']['breath_rms_without_fx_dbfs']}), vârf {rep['silences']['breath_peak_dbfs']} dBFS")
    say(f"  stem-uri: diferența maximă față de mixaj {rep['stems']['max_diff_lsb_24bit']} LSB")
    say(f"  spectru (măsurile 6-9, dB față de 300-2k): {rep['spectrum']['bands_db_rel_mid']}")
    for key in ("third_octave_groove", "third_octave_whole"):
        t3 = rep[key]
        say(f"  1/3 octavă {t3['window_s']}: pantă {t3['slope_db_per_octave_500_10k']} dB/oct; vârf îngust în 2-6 kHz "
            f"(bandă față de vecine) {t3['max_local_bump_2k_6k_db']} dB la {t3['max_local_bump_2k_6k_at_hz']:.0f} Hz; "
            f"exces față de pantă {t3['max_excess_2k_6k_db']} dB la {t3['max_excess_2k_6k_at_hz']:.0f} Hz; "
            f"125-250 Hz față de 500-1k: {t3['lowmid_125_250_minus_500_1k_db']} dB")
    say(f"  mono: {rep['mono']}")
    for name, o in rep["onsets"].items():
        say(f"  atacuri ({name}): {o['count']} găsite, {o['within_10ms_of_16th_grid']} la ±10 ms de grila de 1/16, "
            f"mediana abaterii {o['median_abs_dev_ms']} ms, p95 {o['p95_abs_dev_ms']} ms; lovituri din partitură "
            f"regăsite {o.get('scheduled_hits_detected')}/{o.get('scheduled_hits')}, "
            f"eroare mediană {o.get('detected_minus_scheduled_median_ms')} ms")
    say(f"  accente: {json.dumps(rep['onsets']['mix']['accents'], ensure_ascii=False)}")
    hf = rep.get("hyperframes_beats")
    if hf and hf.get("ran"):
        say(f"  hyperframes beats: {hf.get('bpm_detected')} BPM, {hf.get('beats_detected')} beat-uri; în secțiunile "
            f"ritmice: {hf['rhythmic_sections']}; deriva maximă în secțiunile calme {hf.get('calm_sections_max_drift_ms')} ms")
    say("  loudness pe măsuri (LUFS, fără porți):")
    for row in per_bar:
        say("   " + "  ".join(f"{k}={v}" for k, v in row.items()))
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "out")
    ap.add_argument("--hyperframes", action="store_true", help="rulează și `npx hyperframes@0.9.19 beats`")
    a = ap.parse_args()
    run(a.out, hyperframes=a.hyperframes)
