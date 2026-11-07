#!/usr/bin/env python3
"""Verificările variantei 3 (120 BPM, 36 s). Nu putem asculta, așa că măsurăm.

    uv run python presentation/music/analyze_v3.py [--out presentation/music/out]

Scrie out/report_v3.json, out/spectrogram_v3.png, out/waveform_v3.png și afișează un rezumat: loudness (calcul
propriu BS.1770 și ffmpeg), vârf real, tăieri, durată, liniștea de la final, aerul de la „Dar unde?” (6,0-7,75),
tobele scoase pe 23,0-26,0, suma stem-urilor, spectrul (2-6 kHz, zona joasă), mono sub 120 Hz, tempo-ul și eroarea
fiecărei lovituri din film față de cadrul ei. Fiecare cerință primește „trece” sau „nu trece” în `checks`.
Refolosește măsurătorile din analyze.py și analyze_kinetic.py, fără să le modifice.
"""

from __future__ import annotations

# ruff: noqa: RUF046
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")

import argparse
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze as A  # măsurătorile primei variante
import analyze_kinetic as AK  # detectorul de atacuri și grila variantei cinetice

SR = 48_000
BPM = 120
BEAT = 60.0 / BPM
BAR = 4 * BEAT
STEP = BEAT / 4
DURATION = 36.0
WAV = "tura_v3_36s.wav"
CUES = "cues_v3.json"
REPORT = "report_v3.json"
MP4 = "tura_v3_36s_asculta.mp4"
STEMS_DIR = "stems_v3"
STEMS = ("drums", "bass", "pad", "stabs", "lead", "fx")
AIR = (6.0, 7.75)
HOOK_HITS = (0.0, 1.0, 2.0)
HIT_WIN = 0.3  # nivelul unei lovituri = RMS pe primele 300 ms
TOL_MS = 10.0
SECTIONS = {"cârlig 0-4": (0.0, 4.0), "puls 4-6": (4.0, 6.0), "aer 6-7,75": AIR, "probleme 8-12": (8.0, 12.0),
            "răspuns 12-15": (12.0, 15.0), "produs 15-23": (15.0, 23.0), "uman 23-26": (23.0, 26.0),
            "Aprobă 26-27": (26.0, 27.0), "build 27-29": (27.0, 29.0), "drop 29-32": (29.0, 32.0),
            "final 32-35,9": (32.0, 35.9)}


def hit_report(mix: np.ndarray, stems: dict, cues: dict) -> dict:
    """Pentru fiecare lovitură: atacul cel mai apropiat (±30 ms) în mixaj și în stem-ul care o poartă."""
    on_mix = AK.onsets(mix)
    on_stem = {k: AK.onsets(stems[k]) for k in sorted({h["carrier_stem"] for h in cues["hits"]})}
    rows = []
    for h in cues["hits"]:
        t, car = h["time"], h["carrier_stem"]
        em, ec = AK.nearest_ms(on_mix, t), AK.nearest_ms(on_stem[car], t)
        rows.append({"name": h["name"], "time": t, "frame": h["frame"], "frame_exact": h["frame_exact"],
                     "picture_hit": h["picture_hit"], "kind": h["kind"], "on_screen": h["on_screen"],
                     "mix_onset_error_ms": em, "carrier_stem": car, "carrier_onset_error_ms": ec,
                     "carrier_jump_db": AK.jump_db(stems[car], t), "mix_jump_db": AK.jump_db(mix, t),
                     "within_10ms": em is not None and ec is not None and abs(em) <= TOL_MS and abs(ec) <= TOL_MS})

    def stats(key: str) -> dict:
        v = np.array([r[key] for r in rows if r[key] is not None])
        return {"detected": int(len(v)), "of": len(rows),
                "median_abs_ms": round(float(np.median(np.abs(v))), 2) if len(v) else None,
                "median_signed_ms": round(float(np.median(v)), 2) if len(v) else None,
                "max_abs_ms": round(float(np.max(np.abs(v))), 2) if len(v) else None}

    return {"detector_offset_ms": round(A.detector_offset() * 1000, 2), "search_window_ms": 30,
            "tolerance_ms": TOL_MS, "mix": stats("mix_onset_error_ms"), "carrier": stats("carrier_onset_error_ms"),
            "all_within_10ms": all(r["within_10ms"] for r in rows), "hits": rows}


def rms_db(x: np.ndarray, t0: float, t1: float) -> float:
    return round(A.rms_db(x[int(round(t0 * SR)):int(round(t1 * SR))]), 1)


def air_report(mix: np.ndarray, stems: dict) -> dict:
    """Aerul de la „Dar unde?”: toată fereastra 6,0-7,75 (cu atacul acordului) față de fiecare lovitură din cârlig."""
    air_rms = rms_db(mix, *AIR)
    air_lufs = round(A.loudness_window(mix, *AIR), 1)
    hooks = []
    for t in HOOK_HITS:
        h_rms, h_lufs = rms_db(mix, t, t + HIT_WIN), round(A.loudness_window(mix, t, t + HIT_WIN), 1)
        hooks.append({"time": t, "rms_dbfs": h_rms, "lufs_ungated": h_lufs, "air_below_db_rms": round(h_rms - air_rms, 1),
                      "air_below_db_lufs": round(h_lufs - air_lufs, 1)})
    i0, i1 = int(round(AIR[0] * SR)), int(round(AIR[1] * SR))
    others = {k: float(np.max(np.abs(stems[k][i0 + int(0.001 * SR):i1]))) for k in STEMS if k != "stabs"}
    return {"window_s": list(AIR), "air_rms_dbfs": air_rms, "air_lufs_ungated": air_lufs,
            "air_after_attack_6_3_to_7_75_rms_dbfs": rms_db(mix, 6.3, AIR[1]),
            "hook_hits": hooks, "min_gap_db": min(min(h["air_below_db_rms"], h["air_below_db_lufs"]) for h in hooks),
            "other_stems_max_abs_6_001_to_7_75": others,
            "only_the_suspended_chord": all(v == 0.0 for v in others.values())}


def plots(out: Path, mix: np.ndarray, cues: dict, spec: tuple[np.ndarray, np.ndarray]) -> dict:
    """Desenează graficele. Întoarce poziția axei timpului în waveform_v3.png (pentru linia din copia mp4)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dur = len(mix) / SR
    bg, fg, grid_c, accent, hit_c = "#0e0f12", "#e8e6e1", "#3a3d45", "#f2b34a", "#5ad1ff"
    spans = [(AIR[0], AIR[1], "aer"), (23.0, 26.0, "fără tobe"), (27.0, 29.0, "build"),
             (cues["accents"]["silent_from"]["time"], dur, "")]

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
        ax.text(b["start"] + 0.04, 0.985, f"{b['bar']} {b['section']}", color=fg, fontsize=6.6, va="top",
                transform=ax.get_xaxis_transform())
    for a, b, label in spans:
        ax.axvspan(a, b, color="#ffffff", alpha=0.07)
        if label:
            ax.text((a + b) / 2, 0.90, label, color=fg, fontsize=7, ha="center", transform=ax.get_xaxis_transform())
    for h in cues["hits"]:
        ax.axvline(h["time"], ymin=0.0, ymax=0.16, color=hit_c, linewidth=1.0)
        ax.text(h["time"] + 0.03, 0.01, f"{h['time']:g} {h['name']}", color=hit_c, fontsize=6.0, rotation=90,
                va="bottom", transform=ax.get_xaxis_transform())
    ax.set_xlim(0, dur)
    ax.set_ylim(-1, 1)
    ax.set_xticks(np.arange(0, dur + 0.01, 2.0))
    ax.tick_params(colors=fg, labelsize=8)
    ax.set_xlabel("secunde (o linie = o măsură de 2,0 s = 60 de cadre; o bătaie = 15 cadre)", color=fg, fontsize=9)
    ax.set_title("Tura de mâine, varianta 3 (36 s, 120 BPM): formă de undă, loudness momentană, măsuri, loviturile "
                 "filmului", color=fg, fontsize=11, loc="left")
    for s in list(ax.spines.values()) + list(ax2.spines.values()):
        s.set_color(grid_c)
    fig.tight_layout()
    pos = ax.get_position()
    w_px, h_px = (fig.get_size_inches() * fig.dpi).round().astype(int)
    axes = {"width_px": int(w_px), "height_px": int(h_px), "x0": float(pos.x0), "x1": float(pos.x1),
            "y0": float(1.0 - pos.y1), "y1": float(1.0 - pos.y0), "t0": 0.0, "t1": float(dur)}
    fig.savefig(out / "waveform_v3.png", facecolor=bg)
    plt.close(fig)

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
        ax.text(b["start"] + 0.04, 21000, f"{b['bar']}", color=fg, fontsize=6.8, va="bottom")
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
    ax3.set_xlabel("dB (spectru mediu,\ngroove 12-23 s)", color=fg, fontsize=8)
    for a in (ax, ax3):
        for s in a.spines.values():
            s.set_color(grid_c)
    fig.savefig(out / "spectrogram_v3.png", facecolor=bg, bbox_inches="tight")
    plt.close(fig)
    return axes


def checks(rep: dict) -> dict:
    """Cerințele lui Teo, fiecare cu valoarea măsurată și „trece” / „nu trece”."""
    ff = rep["ffmpeg"].get("ebur128", {})
    lufs = ff.get("integrated_lufs", rep["loudness"]["integrated_lufs_internal"])
    tp = max(ff.get("true_peak_dbfs", -99.0), rep["loudness"]["true_peak_dbtp_internal"])
    bumps = {k: rep[k]["max_local_bump_2k_6k_db"] for k in ("third_octave_groove", "third_octave_drop",
                                                            "third_octave_whole")}
    c = {
        "loudness_-16_lufs_pm_0.5": {"value": lufs, "pass": abs(lufs + 16.0) <= 0.5},
        "true_peak_max_-1.0_dbtp": {"value": tp, "pass": tp <= -1.0},
        "no_clipping": {"value": rep["loudness"]["clipped_samples"], "pass": rep["loudness"]["clipped_samples"] == 0},
        "mono_below_120hz": {"value_db_side_vs_mid": rep["mono"]["side_below_120_vs_mid_below_120_db"],
                             "pass": rep["mono"]["side_below_120_vs_mid_below_120_db"] <= -30.0},
        "no_harsh_2k_6k_peaks": {"max_local_bump_db": bumps, "limit_db": 3.0,
                                 "pass": all(v <= 3.0 for v in bumps.values())},
        "hits_within_10ms": {"mix_max_abs_ms": rep["hits"]["mix"]["max_abs_ms"],
                             "carrier_max_abs_ms": rep["hits"]["carrier"]["max_abs_ms"],
                             "detected": f"{rep['hits']['mix']['detected']}/{rep['hits']['mix']['of']}",
                             "pass": rep["hits"]["all_within_10ms"]},
        "air_6_0_to_7_75_at_least_15db_below_hook_hits": {"min_gap_db": rep["air"]["min_gap_db"],
                                                          "pass": rep["air"]["min_gap_db"] >= 15.0},
        "duration_exactly_36_000s": {"samples": rep["format"]["samples"], "pass": rep["format"]["exact_36s"]},
        "digital_silence_from_35_9": {"pass": rep["silences"]["last_100ms_is_digital_zero"]},
        "stems_sum_to_mix": {"max_diff_lsb": rep["stems"]["max_diff_lsb_24bit"], "pass": rep["stems"]["sum_matches_mix"]},
    }
    if "determinism" in rep:
        c["two_renders_byte_identical"] = {"files": len(rep["determinism"]["files"]),
                                           "pass": rep["determinism"]["identical"]}
    c["all_pass"] = all(v["pass"] for v in c.values())
    return c


def run(out: Path, verbose: bool = True, determinism: dict | None = None) -> dict:
    out = Path(out)
    say = print if verbose else (lambda *a, **k: None)
    mix, sr, sw = A.read_wav(out / WAV)
    cues = json.loads((out / CUES).read_text(encoding="utf-8"))
    stems = {k: A.read_wav(out / STEMS_DIR / f"{k}.wav")[0] for k in STEMS}
    rep: dict = {}
    rep["format"] = {"sample_rate": sr, "bits": 8 * sw, "channels": mix.shape[1], "samples": len(mix),
                     "duration_s": len(mix) / sr, "exact_36s": len(mix) == int(DURATION * sr) and sr == SR}
    rep["loudness"] = {"integrated_lufs_internal": round(A.lufs_integrated(mix), 2),
                       "true_peak_dbtp_internal": round(A.true_peak_db(mix), 2),
                       "sample_peak_dbfs": round(float(20 * np.log10(np.max(np.abs(mix)) + 1e-20)), 2),
                       "clipped_samples": int(np.sum(np.abs(mix) >= 0.99999))}
    rep["ffmpeg"] = A.ffmpeg_measure(out / WAV)
    rep["sections_lufs_ungated"] = {k: round(A.loudness_window(mix, a, b), 1) for k, (a, b) in SECTIONS.items()}
    tail = mix[int(35.9 * SR):]
    rep["silences"] = {
        "last_100ms_is_digital_zero": bool(np.all(tail == 0)),
        "last_100ms_max_abs": float(np.max(np.abs(tail))),
        "level_34_0_to_35_0_rms_dbfs": rms_db(mix, 34.0, 35.0),
        "level_35_0_to_35_9_rms_dbfs": rms_db(mix, 35.0, 35.9),
        "drums_stem_23_06_to_25_99_max_abs": float(np.max(np.abs(stems["drums"][int(23.06 * SR):int(25.99 * SR)]))),
    }
    rep["air"] = air_report(mix, stems)
    ssum = sum(stems.values())
    err = float(np.max(np.abs(ssum - mix)))
    rep["stems"] = {"names": list(STEMS), "max_abs_diff_sum_vs_mix": err, "max_diff_lsb_24bit": round(err * 8388608, 2),
                    "sum_matches_mix": bool(err * 8388608 <= 8)}
    rep["loudness_per_bar_lufs_ungated"] = AK.per_bar(mix, stems, cues)
    spec = A.spectrum_checks(mix, (12.0, 23.0))
    rep["spectrum_groove"] = {k: v for k, v in spec.items() if k != "spectrum"}
    rep["third_octave_groove"] = A.third_octave(mix, (12.0, 23.0))
    rep["third_octave_drop"] = A.third_octave(mix, (29.0, 32.0))
    rep["third_octave_whole"] = A.third_octave(mix, (0.0, 35.9))
    rep["mono"] = A.mono_checks(mix)
    rep["tempo"] = AK.tempo_estimate(mix, 12.0, 23.0)
    rep["hits"] = hit_report(mix, stems, cues)
    on_mix = AK.onsets(mix)
    rep["onsets_grid"] = {"mix_16th": AK.grid_report(on_mix, STEP), "mix_32nd": AK.grid_report(on_mix, STEP / 2),
                          "drums_32nd": AK.grid_report(AK.onsets(stems["drums"]), STEP / 2)}
    if determinism is not None:
        rep["determinism"] = determinism
    rep["plot_axes"] = plots(out, mix, cues, spec["spectrum"])
    rep["checks"] = checks(rep)
    (out / REPORT).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ff = rep["ffmpeg"]
    say("— verificări (varianta 3, 36 s) —")
    say(f"  format: {sr} Hz, {8 * sw} biți, {mix.shape[1]} canale, {len(mix)} eșantioane = {len(mix) / sr:.6f} s")
    say(f"  loudness: {rep['loudness']['integrated_lufs_internal']} LUFS (intern), ffmpeg ebur128 {ff.get('ebur128')}, "
        f"loudnorm {ff.get('loudnorm')}")
    say(f"  vârf real intern {rep['loudness']['true_peak_dbtp_internal']} dBTP, tăiate: {rep['loudness']['clipped_samples']}")
    say(f"  secțiuni (LUFS fără porți): {rep['sections_lufs_ungated']}")
    say(f"  liniște: {rep['silences']}")
    say(f"  aer: {rep['air']}")
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
        say(f"    {r['time']:6.3f} s  cadrul {r['frame_exact']:6.1f}  {r['name']:<16} mix {r['mix_onset_error_ms']} ms, "
            f"{r['carrier_stem']} {r['carrier_onset_error_ms']} ms, salt {r['carrier_jump_db']} dB"
            f"{'' if r['within_10ms'] else '  <-- NU'}")
    for k, g in rep["onsets_grid"].items():
        say(f"  grilă {k}: {g['within_10ms']}/{g['count']} la ±10 ms, mediana {g['median_abs_dev_ms']} ms; "
            f"în afara grilei: {g['off_grid'][:12]}")
    say("  loudness pe măsuri (LUFS, fără porți):")
    for row in rep["loudness_per_bar_lufs_ungated"]:
        say("   " + "  ".join(f"{k}={v}" for k, v in row.items()))
    say("  cerințe: " + ", ".join(f"{k}={'trece' if v['pass'] else 'NU TRECE'}"
                                   for k, v in rep["checks"].items() if k != "all_pass"))
    say(f"  toate cerințele: {'trec' if rep['checks']['all_pass'] else 'NU trec toate'}")
    return rep


def add_listening_copy(out: Path, mp4: Path, verbose: bool = True) -> dict:
    """Verifică copia de ascultat (codec, durată) și o trece în report_v3.json."""
    ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    entries = "stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,duration,sample_rate:format=duration"
    p = subprocess.run([ffprobe, "-v", "error", "-show_entries", entries, "-of", "json", str(mp4)],
                       capture_output=True, text=True, check=True)
    info = json.loads(p.stdout)
    streams = {s["codec_type"]: s for s in info["streams"]}
    res = {"file": mp4.name, "format_duration_s": float(info["format"]["duration"]),
           "video": streams.get("video"), "audio": streams.get("audio")}
    res["exact_36s"] = (abs(res["format_duration_s"] - DURATION) < 0.0015
                        and int(streams["video"]["nb_frames"]) == int(DURATION * 30)
                        and abs(float(streams["audio"]["duration"]) - DURATION) < 0.0015)
    rp = out / REPORT
    rep = json.loads(rp.read_text(encoding="utf-8"))
    rep["listening_copy"] = res
    rep["checks"]["listening_copy_exactly_36s"] = {"pass": res["exact_36s"]}
    rep["checks"]["all_pass"] = all(v["pass"] for k, v in rep["checks"].items() if k != "all_pass")
    rp.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if verbose:
        print(f"  copia de ascultat: {res['format_duration_s']} s, video {streams['video']['codec_name']} "
              f"{streams['video']['width']}x{streams['video']['height']} {streams['video']['nb_frames']} cadre, "
              f"audio {streams['audio']['codec_name']} {streams['audio']['duration']} s -> "
              f"{'exact 36,0 s' if res['exact_36s'] else 'NU e exact 36,0 s'}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE / "out")
    a = ap.parse_args()
    old = a.out / REPORT
    det = json.loads(old.read_text(encoding="utf-8")).get("determinism") if old.exists() else None
    run(a.out, determinism=det)  # păstrăm rezultatul ultimei verificări de determinism, dacă există
    if (a.out / MP4).exists():
        add_listening_copy(a.out, a.out / MP4)
