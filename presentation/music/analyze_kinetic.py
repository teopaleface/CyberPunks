#!/usr/bin/env python3
"""Verificările muzicii cinetice (120 BPM, 30 s). Nu putem asculta, așa că măsurăm.

    uv run python presentation/music/analyze_kinetic.py [--out presentation/music/out]

Scrie out/report_120.json, out/spectrogram_120.png, out/waveform_120.png și afișează un rezumat:
loudness (calcul propriu BS.1770 și ffmpeg), vârf real, durată, liniștea de la final, suma stem-urilor,
spectrul (2-6 kHz, zona joasă), mono sub 120 Hz, tempo-ul, eroarea fiecărei lovituri din film față de cadrul ei.
Refolosește măsurătorile din analyze.py (prima variantă), fără să-l modifice.
"""

from __future__ import annotations

# ruff: noqa: RUF046
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze as A  # măsurătorile primei variante

SR = 48_000
BPM = 120
BEAT = 60.0 / BPM
BAR = 4 * BEAT
STEP = BEAT / 4
WAV = "tura_120bpm_30s.wav"
STEMS_DIR = "stems_120"
STEMS = ("drums", "bass", "pad", "stabs", "lead", "fx")
# În ce stem stă fiecare tip de lovitură (acolo se verifică atacul ei, fără restul mixajului).
CARRIER = {"stab": "stabs", "accent": "stabs", "hold": "stabs", "big": "stabs", "press": "stabs",
           "press_big": "stabs", "soft": "stabs", "final": "stabs", "note": "lead", "lift": "lead"}


def onsets(x: np.ndarray, pad: float = 0.3) -> np.ndarray:
    """Atacurile (s), cu detectorul din analyze.py. Adăugăm 0,3 s de liniște în față, ca să se vadă și atacul
    de pe 0,0 s (detectorul are nevoie de un cadru înainte), apoi scădem la loc."""
    mono = x.mean(axis=1) if x.ndim == 2 else x
    z = np.concatenate([np.zeros(int(pad * SR)), mono])
    return A.pick_onsets(*A.onset_strength(z)) - A.detector_offset() - pad


def nearest_ms(arr: np.ndarray, t: float, tol: float = 0.03) -> float | None:
    d = arr - t
    m = np.abs(d) <= tol
    return round(float(d[m][np.argmin(np.abs(d[m]))]) * 1000, 2) if m.any() else None


def jump_db(x: np.ndarray, t: float, win: float = 0.04) -> float:
    """Cu cât crește nivelul (RMS) în primele 40 ms după lovitură față de cele 40 ms dinainte."""
    mono = x.mean(axis=1)
    i = int(round(t * SR))
    w = int(win * SR)
    before = mono[max(0, i - w):i]
    after = mono[i:i + w]
    rb = np.sqrt(np.mean(before**2)) if len(before) else 0.0
    return round(float(20 * np.log10((np.sqrt(np.mean(after**2)) + 1e-9) / (rb + 1e-9))), 1)


def hit_report(mix: np.ndarray, stems: dict, cues: dict) -> dict:
    on_mix = onsets(mix)
    on_stem = {k: onsets(stems[k]) for k in sorted(set(CARRIER.values()))}
    rows = []
    for h in cues["hits"]:
        t, car = h["time"], CARRIER[h["kind"]]
        rows.append({"name": h["name"], "time": t, "frame": h["frame"], "kind": h["kind"], "on_screen": h["on_screen"],
                     "mix_onset_error_ms": nearest_ms(on_mix, t), "carrier_stem": car,
                     "carrier_onset_error_ms": nearest_ms(on_stem[car], t),
                     "carrier_jump_db": jump_db(stems[car], t), "mix_jump_db": jump_db(mix, t)})

    def stats(key: str) -> dict:
        v = np.array([r[key] for r in rows if r[key] is not None])
        return {"detected": int(len(v)), "of": len(rows),
                "median_abs_ms": round(float(np.median(np.abs(v))), 2) if len(v) else None,
                "median_signed_ms": round(float(np.median(v)), 2) if len(v) else None,
                "max_abs_ms": round(float(np.max(np.abs(v))), 2) if len(v) else None}

    return {"detector_offset_ms": round(A.detector_offset() * 1000, 2), "tolerance_ms": 30,
            "mix": stats("mix_onset_error_ms"), "carrier": stats("carrier_onset_error_ms"), "hits": rows}


def grid_report(times: np.ndarray, step: float) -> dict:
    dev = (times / step - np.round(times / step)) * step
    ok = np.abs(dev) <= 0.010
    return {"grid_s": step, "count": int(len(times)), "within_10ms": int(ok.sum()),
            "median_abs_dev_ms": round(float(np.median(np.abs(dev)) * 1000), 2) if len(dev) else None,
            "p95_abs_dev_ms": round(float(np.percentile(np.abs(dev), 95) * 1000), 2) if len(dev) else None,
            "off_grid": [round(float(t), 4) for t, k in zip(times, ok) if not k][:40]}


def tempo_estimate(mix: np.ndarray, t0: float = 6.0, t1: float = 17.5) -> dict:
    """Tempo-ul din autocorelația forței atacurilor (fereastra groove-ului). Trebuie să iasă 120 BPM."""
    seg = mix[int(t0 * SR):int(t1 * SR)].mean(axis=1)
    _t, flux = A.onset_strength(seg)
    flux = flux - flux.mean()
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    hop = A.HOP / SR
    lags = np.arange(len(ac)) * hop
    # pieptene: o perioadă bună de bătaie se repetă și la 2× și 4× (măsura); ecoul de 3/16 nu trece testul
    cand = np.flatnonzero((lags >= 60 / 180) & (lags <= 60 / 80))
    score = [ac[i] + ac[min(2 * i, len(ac) - 1)] + ac[min(4 * i, len(ac) - 1)] for i in cand]
    best = lags[cand[int(np.argmax(score))]]
    return {"window_s": [t0, t1], "method": "autocorelație cu pieptene (1×, 2×, 4×)",
            "beat_period_s": round(float(best), 4), "bpm": round(60.0 / float(best), 2)}


def per_bar(mix: np.ndarray, stems: dict, cues: dict) -> list[dict]:
    rows = []
    for b in cues["bars"]:
        row = {"bar": b["bar"], "section": b["section"], "mix": round(A.loudness_window(mix, b["start"], b["end"]), 1)}
        for k in STEMS:
            row[k] = round(A.loudness_window(stems[k], b["start"], b["end"]), 1)
        rows.append(row)
    return rows


def plots(out: Path, mix: np.ndarray, cues: dict, spec: tuple[np.ndarray, np.ndarray]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dur = len(mix) / SR
    bg, fg, grid_c, accent, hit_c = "#0e0f12", "#e8e6e1", "#3a3d45", "#f2b34a", "#5ad1ff"
    spans = [(17.5, 19.0, "energie mai mică"), (20.0, 22.0, "build"), (cues["accents"]["silent_from"]["time"], dur, "")]

    # formă de undă, loudness momentană, linii de măsură, loviturile filmului
    fig, ax = plt.subplots(figsize=(18, 6.2), dpi=130, facecolor=bg)
    ax.set_facecolor(bg)
    mono = mix.mean(axis=1)
    edges = np.linspace(0, len(mono), 3601).astype(int)
    lo = np.array([mono[a:b].min() for a, b in itertools.pairwise(edges)])
    hi = np.array([mono[a:b].max() for a, b in itertools.pairwise(edges)])
    ax.fill_between((edges[:-1] + edges[1:]) / 2 / SR, lo, hi, color="#8fb8de", linewidth=0)
    y = A.k_weight(mix)
    win = int(0.4 * SR)
    c = np.concatenate([[0], np.cumsum((y**2).sum(axis=1))])
    idx = np.arange(0, len(mono) - win, int(0.05 * SR))
    mom = -0.691 + 10 * np.log10((c[idx + win] - c[idx]) / win + 1e-20)
    ax2 = ax.twinx()
    ax2.plot((idx + win / 2) / SR, mom, color=accent, linewidth=1.1)
    ax2.set_ylim(-60, 0)
    ax2.tick_params(colors=fg, labelsize=8)
    ax2.set_ylabel("LUFS momentan (400 ms)", color=accent, fontsize=9)
    for b in cues["bars"]:
        ax.axvline(b["start"], color=grid_c, linewidth=0.9)
        ax.text(b["start"] + 0.04, 0.985, f"{b['bar']} {b['section']}", color=fg, fontsize=7.2, va="top",
                transform=ax.get_xaxis_transform())
    for a, b, label in spans:
        ax.axvspan(a, b, color="#ffffff", alpha=0.07)
        if label:
            ax.text((a + b) / 2, 0.90, label, color=fg, fontsize=7, ha="center", transform=ax.get_xaxis_transform())
    for h in cues["hits"]:
        ax.axvline(h["time"], ymin=0.0, ymax=0.16, color=hit_c, linewidth=1.0)
        ax.text(h["time"] + 0.03, 0.01, f"{h['time']:g} {h['name']}", color=hit_c, fontsize=6.3, rotation=90,
                va="bottom", transform=ax.get_xaxis_transform())
    ax.set_xlim(0, dur)
    ax.set_ylim(-1, 1)
    ax.set_xticks(np.arange(0, dur + 0.01, 2.0))
    ax.tick_params(colors=fg, labelsize=8)
    ax.set_xlabel("secunde (o linie = o măsură de 2,0 s = 60 de cadre; o bătaie = 15 cadre)", color=fg, fontsize=9)
    ax.set_title("Tura de mâine, 120 BPM: formă de undă (mono), loudness momentană, măsuri și loviturile filmului",
                 color=fg, fontsize=11, loc="left")
    for s in list(ax.spines.values()) + list(ax2.spines.values()):
        s.set_color(grid_c)
    fig.tight_layout()
    fig.savefig(out / "waveform_120.png", facecolor=bg)
    plt.close(fig)

    # spectrogramă cu frecvență logaritmică și spectrul mediu al groove-ului
    fig = plt.figure(figsize=(18, 7.5), dpi=130, facecolor=bg)
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
    for b in cues["bars"]:
        ax.axvline(b["start"], color="#ffffff", alpha=0.35, linewidth=0.8)
        ax.text(b["start"] + 0.04, 21000, f"{b['bar']} {b['section']}", color=fg, fontsize=6.8, va="bottom")
    for h in cues["hits"]:
        ax.plot([h["time"], h["time"]], [25, 34], color=hit_c, linewidth=1.4)
    ax.set_xlim(0, dur)
    ax.set_xticks(np.arange(0, dur + 0.01, 2.0))
    ax.tick_params(colors=fg, labelsize=8)
    ax.set_ylabel("Hz", color=fg)
    ax.set_xlabel("secunde (liniile albe = măsuri de 2,0 s; liniuțele albastre jos = loviturile filmului)", color=fg)
    ax.set_title("Spectrogramă (dB față de maxim); banda 2-6 kHz e marcată", color=fg, fontsize=11, loc="left", pad=22)
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
    ax3.set_xlabel("dB (spectru mediu,\ngroove 6-17,5 s)", color=fg, fontsize=8)
    for a in (ax, ax3):
        for s in a.spines.values():
            s.set_color(grid_c)
    fig.savefig(out / "spectrogram_120.png", facecolor=bg, bbox_inches="tight")
    plt.close(fig)


def run(out: Path, verbose: bool = True, determinism: dict | None = None) -> dict:
    out = Path(out)
    say = print if verbose else (lambda *a, **k: None)
    mix, sr, sw = A.read_wav(out / WAV)
    cues = json.loads((out / "cues_120.json").read_text(encoding="utf-8"))
    stems = {k: A.read_wav(out / STEMS_DIR / f"{k}.wav")[0] for k in STEMS}
    rep: dict = {}
    rep["format"] = {"sample_rate": sr, "bits": 8 * sw, "channels": mix.shape[1], "samples": len(mix),
                     "duration_s": len(mix) / sr, "exact_30s": len(mix) == 30 * sr}
    rep["loudness"] = {"integrated_lufs_internal": round(A.lufs_integrated(mix), 2),
                       "true_peak_dbtp_internal": round(A.true_peak_db(mix), 2),
                       "sample_peak_dbfs": round(float(20 * np.log10(np.max(np.abs(mix)) + 1e-20)), 2),
                       "clipped_samples": int(np.sum(np.abs(mix) >= 0.99999))}
    rep["ffmpeg"] = A.ffmpeg_measure(out / WAV)
    seg = {"cârlig 0-6": (0.0, 6.0), "groove 6-17,5": (6.0, 17.5), "Nu sunt sigur 17,5-19": (17.5, 19.0),
           "Aprobă 19-20": (19.0, 20.0), "build 20-22": (20.0, 22.0), "drop 22-26": (22.0, 26.0),
           "final 26-29,9": (26.0, 29.9)}
    rep["sections_lufs_ungated"] = {k: round(A.loudness_window(mix, a, b), 1) for k, (a, b) in seg.items()}
    tail = mix[int(29.9 * SR):]
    rep["silences"] = {
        "last_100ms_is_digital_zero": bool(np.all(tail == 0)),
        "last_100ms_max_abs": float(np.max(np.abs(tail))),
        "level_29_0_to_29_5_rms_dbfs": round(A.rms_db(mix[int(29.0 * SR):int(29.5 * SR)]), 1),
        "level_29_5_to_29_9_rms_dbfs": round(A.rms_db(mix[int(29.5 * SR):int(29.9 * SR)]), 1),
        "air_after_un_plan": {"hit_2_0_to_2_3_rms_dbfs": round(A.rms_db(mix[int(2.0 * SR):int(2.3 * SR)]), 1),
                              "air_2_5_to_3_0_rms_dbfs": round(A.rms_db(mix[int(2.5 * SR):int(3.0 * SR)]), 1)},
    }
    ssum = sum(stems.values())
    err = float(np.max(np.abs(ssum - mix)))
    rep["stems"] = {"names": list(STEMS), "max_abs_diff_sum_vs_mix": err, "max_diff_lsb_24bit": round(err * 8388608, 2),
                    "sum_matches_mix": bool(err * 8388608 <= 8)}
    rep["loudness_per_bar_lufs_ungated"] = per_bar(mix, stems, cues)
    spec = A.spectrum_checks(mix, (6.0, 17.5))
    rep["spectrum_groove"] = {k: v for k, v in spec.items() if k != "spectrum"}
    rep["third_octave_groove"] = A.third_octave(mix, (6.0, 17.5))
    rep["third_octave_drop"] = A.third_octave(mix, (22.0, 26.0))
    rep["third_octave_whole"] = A.third_octave(mix, (0.0, 29.9))
    rep["mono"] = A.mono_checks(mix)
    rep["tempo"] = tempo_estimate(mix)
    rep["hits"] = hit_report(mix, stems, cues)
    on_mix = onsets(mix)
    rep["onsets_grid"] = {"mix_16th": grid_report(on_mix, STEP), "mix_32nd": grid_report(on_mix, STEP / 2),
                          "drums_32nd": grid_report(onsets(stems["drums"]), STEP / 2)}
    if determinism is not None:
        rep["determinism"] = determinism
    plots(out, mix, cues, spec["spectrum"])
    (out / "report_120.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ff = rep["ffmpeg"]
    say("— verificări (120 BPM) —")
    say(f"  format: {sr} Hz, {8 * sw} biți, {mix.shape[1]} canale, {len(mix)} eșantioane = {len(mix) / sr:.6f} s")
    say(f"  loudness: {rep['loudness']['integrated_lufs_internal']} LUFS (intern), ffmpeg ebur128 {ff.get('ebur128')}, "
        f"loudnorm {ff.get('loudnorm')}")
    say(f"  vârf real intern {rep['loudness']['true_peak_dbtp_internal']} dBTP, tăiate: {rep['loudness']['clipped_samples']}")
    say(f"  secțiuni (LUFS fără porți): {rep['sections_lufs_ungated']}")
    say(f"  liniște: {rep['silences']}")
    say(f"  stem-uri: diferența maximă față de mixaj {rep['stems']['max_diff_lsb_24bit']} LSB")
    say(f"  spectru groove (dB față de 300-2k): {rep['spectrum_groove']['bands_db_rel_mid']}")
    for key in ("third_octave_groove", "third_octave_drop", "third_octave_whole"):
        t3 = rep[key]
        say(f"  1/3 oct {t3['window_s']}: pantă {t3['slope_db_per_octave_500_10k']} dB/oct; vârf îngust 2-6 kHz "
            f"{t3['max_local_bump_2k_6k_db']} dB la {t3['max_local_bump_2k_6k_at_hz']:.0f} Hz; exces față de pantă "
            f"{t3['max_excess_2k_6k_db']} dB la {t3['max_excess_2k_6k_at_hz']:.0f} Hz; 125-250 față de 500-1k "
            f"{t3['lowmid_125_250_minus_500_1k_db']} dB")
    say(f"  mono: {rep['mono']}; tempo: {rep['tempo']}")
    hr = rep["hits"]
    say(f"  lovituri: mixaj {hr['mix']}; stem-ul purtător {hr['carrier']}")
    for r in hr["hits"]:
        say(f"    {r['time']:5.1f} s  cadrul {r['frame']:3d}  {r['name']:<16} mix {r['mix_onset_error_ms']} ms, "
            f"{r['carrier_stem']} {r['carrier_onset_error_ms']} ms, salt {r['carrier_jump_db']} dB")
    for k, g in rep["onsets_grid"].items():
        say(f"  grilă {k}: {g['within_10ms']}/{g['count']} la ±10 ms, mediana {g['median_abs_dev_ms']} ms; "
            f"în afara grilei: {g['off_grid'][:12]}")
    say("  loudness pe măsuri (LUFS, fără porți):")
    for row in rep["loudness_per_bar_lufs_ungated"]:
        say("   " + "  ".join(f"{k}={v}" for k, v in row.items()))
    if determinism is not None:
        say(f"  determinism: identic = {determinism['identical']}")
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE / "out")
    a = ap.parse_args()
    old = a.out / "report_120.json"
    det = json.loads(old.read_text(encoding="utf-8")).get("determinism") if old.exists() else None
    run(a.out, determinism=det)  # păstrăm rezultatul ultimei verificări de determinism, dacă există
