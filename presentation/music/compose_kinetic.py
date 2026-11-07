#!/usr/bin/env python3
"""Muzica nouă a filmului „Tura de mâine” (varianta cinetică): 30,000 s, 120 BPM, 4/4, 15 măsuri a câte 2,0 s.

O bătaie = 0,5 s = exact 15 cadre la 30 fps; o măsură = 2,0 s = 60 de cadre.
Pop/house electronic, curat: kick pe fiecare timp, clap pe 2 și 4, hi-hat strâns, pad cu sidechain,
acorduri scurte („stab”) din fierăstraie sintetizate, bas care se mișcă, un motiv de 4 note pe pașii agentului.

Totul e sintetizat aici, în cod (numpy și scipy). Din compose.py (prima variantă, 96 BPM) refolosim doar
unelte: reverb, ecou, limitator, loudness, coarda Karplus-Strong, scrierea WAV. compose.py nu se schimbă.
Fără sample-uri, loop-uri sau soundfont-uri. Seed fix: același fișier, bit cu bit, la fiecare rulare.

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect. Licență CC0.

Rulare, din rădăcina repo-ului:
    uv run python presentation/music/compose_kinetic.py
    uv run python presentation/music/compose_kinetic.py --determinism   # randează de două ori și compară
"""

from __future__ import annotations

# ruff: noqa: RUF046  # int(round(x)) rămâne: x poate fi un scalar NumPy folosit ca index
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")  # cel mult 4 nuclee

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose as C  # uneltele primei variante; nu le modificăm

# ======================================================================================
# 1. GRILA
# ======================================================================================

SR = C.SR  # 48 kHz
BPM = 120
BEATS_PER_BAR = 4
N_BARS = 15
FPS = 30
SEED = 20261120

BEAT = 60.0 / BPM  # 0,5 s = 15 cadre
BAR = BEATS_PER_BAR * BEAT  # 2,0 s = 60 de cadre
STEP = BEAT / 4  # o șaisprezecime: 0,125 s
DURATION = N_BARS * BAR  # 30,0 s
N = int(round(DURATION * SR))  # 1.440.000 de eșantioane
assert N == C.N, "uneltele din compose.py (curve, reverb, pingpong) lucrează pe exact 30 s"

TARGET_LUFS = -16.0
CEILING_DBTP = -1.3  # marjă față de -1,0 dBTP cerut
FADE_FROM = 28.9
SILENT_FROM = 29.9  # de aici până la 30,0 s: zero digital

WAV_NAME = "tura_120bpm_30s.wav"
M4A_NAME = "tura_120bpm_30s.m4a"
STEMS_DIR = "stems_120"
STEMS = ("drums", "bass", "pad", "stabs", "lead", "fx")

# ======================================================================================
# 2. ARMONIA, LOVITURILE, SECȚIUNILE (date editabile)
# ======================================================================================

# La major. Cârligul (0-6 s) pornește din fa diez minor (problema), urcă pe acorduri paralele în cvarte
# (si, do diez, re, mi: aceeași formă mutată pe treptele gamei) și se oprește pe mi (dominanta).
# Groove-ul: A - E/G# - F#m9 - Dmaj9 (I - V6 - vi - IV), cu acorduri împinse pe timpul 4 (13,5 și 15,5).
# „Nu sunt sigur” cade pe F#m9 (minor), „Aprobă” pe Dmaj9 (luminos), build-ul pe mi, drop-ul pe la.
# Finalul: Dmaj9 (24,0) - E (25,0) - A add9 (26,0): IV - V - I, rezolvarea pe logo.
CHORDS = {
    #  nume       bas      pad (de jos în sus)                        stab (de jos în sus)
    "A": ("A1", ["E3", "A3", "C#4", "E4", "B4"], ["A3", "E4", "B4", "C#5", "E5"]),
    "E/G#": ("G#1", ["E3", "G#3", "B3", "E4", "B4"], ["G#3", "E4", "F#4", "B4", "E5"]),
    "F#m9": ("F#1", ["E3", "A3", "C#4", "E4", "G#4"], ["F#3", "C#4", "E4", "G#4", "C#5"]),
    "Dmaj9": ("D2", ["F#3", "A3", "C#4", "E4", "A4"], ["D3", "A3", "E4", "F#4", "C#5"]),
    "Dmaj7#11": ("D2", ["F#3", "A3", "C#4", "E4", "G#4"], ["D4", "G#4", "C#5", "F#5", "A5"]),
    "A/C#": ("C#2", ["E3", "A3", "C#4", "E4", "B4"], ["C#4", "E4", "A4", "B4", "E5"]),
    "E": ("E1", ["E3", "G#3", "B3", "E4", "G#4"], ["E3", "B3", "E4", "G#4", "B4"]),
    "Esus4": ("E1", ["E3", "A3", "B3", "E4", "A4"], ["E3", "B3", "E4", "A4", "B4"]),
    "Bm11": ("B1", ["D3", "A3", "B3", "E4", "F#4"], ["B3", "E4", "A4", "D5", "F#5"]),
    "C#m7": ("C#2", ["E3", "G#3", "B3", "E4", "G#4"], ["C#4", "F#4", "B4", "E5", "G#5"]),
    "Afinal": ("A1", ["A2", "E3", "A3", "C#4", "E4", "B4", "C#5"],
               ["A2", "E3", "A3", "C#4", "E4", "B4", "C#5", "E5"]),
}

# Când se schimbă acordul (secunde). Basul și padul urmează lista; stab-urile o folosesc când nu au note proprii.
TIMELINE = [
    (0.0, "F#m9"), (1.5, "E/G#"), (2.0, "Dmaj9"),
    (3.0, "Bm11"), (3.5, "C#m7"), (4.0, "Dmaj7#11"), (4.5, "Esus4"),
    (6.0, "A"), (8.0, "E/G#"), (10.0, "F#m9"), (12.0, "Dmaj9"), (13.5, "A/C#"), (15.5, "E"),
    (17.5, "F#m9"), (19.0, "Dmaj9"), (20.0, "Esus4"), (21.5, "E"),
    (22.0, "A"), (24.0, "Dmaj9"), (25.0, "Esus4"), (25.5, "E"), (26.0, "Afinal"),
]

# Loviturile filmului. Fiecare începe fix pe cadru (timp × 30 = cadru întreg).
# Tipuri: stab = acord scurt (cu un kick scurt dedesubt); accent = acord mai mare (kick, clap, uneori crash);
# hold = acord ținut până la 6,0 (cu riser); big = lovitură mare (boom, crash, clap); press = buton apăsat
# (acord foarte scurt și clap strâns); press_big = apăsare cu crash; note = o notă din motiv;
# lift = patru note în șaisprezecimi și o rafală scurtă; soft = acord moale, energia scade; final = logoul.
# note=None: notele vin din acordul de la acel moment (TIMELINE).
HITS = [
    # timp, nume, pe ecran, tip, note
    (0.0, "un_scor", "„Un scor”", "stab", ["F#3", "C#4", "E4", "A4", "C#5"]),
    (0.5, "de_087", "„de 0,87”", "stab", ["A3", "E4", "G#4", "C#5", "E5"]),
    (1.5, "nu_e", "„nu e”", "stab", ["G#3", "B3", "E4", "B4", "F#5"]),
    (2.0, "un_plan", "„un plan.” (apoi aer până la 3,0)", "accent", ["D3", "A3", "E4", "F#4", "C#5", "A5"]),
    (3.0, "contoare", "„Contoare.” (contorul 3D intră)", "stab", None),
    (3.5, "furtuni", "„Furtuni.” (norul de furtună)", "stab", None),
    (4.0, "tensiune", "„Tensiune.” (panoul solar)", "stab", None),
    (4.5, "aceleasi_echipe", "„Aceleași echipe.” (cele patru obiecte)", "hold",
     ["E3", "E4", "A4", "D5", "G#5", "B5"]),
    (6.0, "consola", "consola urcă: intră groove-ul", "big", None),
    (8.0, "spre_buton", "camera zboară spre „Rulează agentul”", "accent", None),
    (9.0, "apasat", "butonul „Rulează agentul” e APĂSAT", "press", ["G#3", "E4", "B4"]),
    (9.5, "perceive", "„Perceive ✓”", "note", ["B4"]),
    (10.0, "estimate", "„Estimate ✓”", "note", ["C#5"]),
    (10.5, "decide", "„Decide ✓”", "note", ["E5"]),
    (11.0, "act", "„Act ✓”", "note", ["A5"]),
    (11.5, "harta", "harta: traseele se desenează", "lift", ["E5", "F#5", "A5", "C#6"]),
    (13.5, "scor_087", "lucrarea: scorul 0,87 și bilanțul postului", "accent", None),
    (15.5, "tensiune_fix", "cazul de tensiune: soluția cea mai ieftină", "accent", None),
    (17.5, "nu_sunt_sigur", "cardul „Nu sunt sigur” (energia scade 1,5 s)", "soft", None),
    (19.0, "aproba", "„Aprobă” APĂSAT (energia revine)", "press_big", None),
    (22.0, "drop", "pastila neagră umple ecranul; cifra urcă 22,0-23,5", "big",
     ["A2", "E3", "A3", "C#4", "E4", "B4", "E5"]),
    (24.0, "al_doilea_rand", "al doilea rând de text", "accent", None),
    (26.0, "final", "logoul: soarele răsare peste traseu", "final", None),
]

# Ce se întâmplă în fiecare măsură (pentru cues_120.json și grafice).
BARS = {
    1: ("cârlig", "„Un scor de 0,87 nu e un plan.”", "acorduri scurte pe fiecare cuvânt; fără tobe continue"),
    2: ("cârlig", "„un plan.”, aer, „Contoare.” „Furtuni.”", "lovitură mare și sub care coboară, apoi liniște"),
    3: ("cârlig", "„Tensiune.” „Aceleași echipe.”", "acordul de pe 4,5 ține; riser 5,0-6,0"),
    4: ("groove", "consola urcă", "intră kick-ul pe fiecare timp, clap, hi-hat, bas, pad cu sidechain"),
    5: ("groove", "spre buton; APĂSAT; Perceive", "accent pe 8,0; apăsarea pe 9,0; prima notă a motivului"),
    6: ("groove", "Estimate, Decide, Act; harta", "motivul urcă (C#5, E5, A5); umplutură pe 11,5"),
    7: ("groove", "scorul 0,87 și bilanțul (13,5)", "intră arpegiul și hi-hat-ul deschis; acord împins pe 13,5"),
    8: ("groove", "soluția cea mai ieftină (15,5)", "acord împins pe 15,5"),
    9: ("groove", "„Nu sunt sigur” (17,5)", "de pe 17,5 tobele se rup, filtrul se închide"),
    10: ("groove", "„Aprobă” (19,0)", "pe 19,0 totul revine"),
    11: ("build", "spre pastila neagră", "rafală de snare, riser, filtrul se deschide"),
    12: ("drop", "pastila neagră; cifra urcă", "lovitura mare; arpegiul numără până la 23,5"),
    13: ("drop", "al doilea rând (24,0)", "accent; IV - V spre final"),
    14: ("final", "logoul (26,0)", "acordul de la major; tobele se opresc"),
    15: ("final", "logoul rămâne", "coada se stinge; zero digital de la 29,9"),
}

# Nivelurile (dB) pe instrumente și trimiterile spre reverb.
MIX_DB = {"kick": -1.5, "boom": -3.0, "clap": 3.5, "roll": 0.0, "hat": -1.0, "ohat": -4.0, "crash": -7.0,
          "bass": 2.0, "subdrop": 3.0, "pad": -6.0, "stabs": 13.0, "lead": 9.0, "arp": 9.0, "fx": 7.0}
HALL_SEND = {"stabs": 0.22, "lead": 0.30, "pad": 0.18, "fx": 0.25, "crash": 0.10}
ROOM_SEND = {"clap": 0.22, "roll": 0.18, "hat": 0.06, "ohat": 0.08}

# ======================================================================================
# 3. UTILITARE ȘI INSTRUMENTE (toate sintetizate)
# ======================================================================================

midi, hz, db, pan_gains, add_at, curve, fade_tail = C.midi, C.hz, C.db, C.pan_gains, C.add_at, C.curve, C.fade_tail


def rng(*keys) -> np.random.Generator:
    """Generator determinist pentru fiecare sunet, independent de ordinea randării."""
    return np.random.default_rng([SEED, *[C.hash_str(k) if isinstance(k, str) else int(k) for k in keys]])


def sos(kind: str, freq, order: int = 2):
    return signal.butter(order, freq, kind, fs=SR, output="sos")


def early_rms(y: np.ndarray, ms: float = 40.0) -> float:
    return float(np.sqrt(np.mean(y[: int(ms * 1e-3 * SR)] ** 2)) + 1e-12)


def saw_additive(f0, n: int, fc, voices=((0.0, 0.0),), rng_: np.random.Generator | None = None,
                 q: float = 0.9, floor: float = 1e-4) -> np.ndarray:
    """Fierăstrău limitat în bandă (sumă de armonice) trecut printr-un filtru trece-jos de 24 dB/octavă
    (două secțiuni de ordinul 2, factor de calitate q) a cărui frecvență de tăiere fc se mișcă în timp.
    f0 și fc pot fi scalari sau vectori de n eșantioane (glissando, anvelopa filtrului).
    O armonică se calculează doar cât timp filtrul o lasă peste `floor` (aprox. -80 dB): rapid și fără aliasing.
    voices: (cenți, panoramare) pentru vocile dezacordate. Întoarce stereo (n, 2)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), (n,))
    f0 = np.broadcast_to(np.asarray(f0, dtype=float), (n,))
    out = np.zeros((n, 2))
    norm = 1.0 / np.sqrt(len(voices))
    for cents, pan in voices:
        f = f0 * 2.0 ** (cents / 1200.0)
        phi = 0.0 if rng_ is None else float(rng_.uniform(0.0, 2.0 * np.pi))
        x = 2.0 * np.pi * np.cumsum(f) / SR - 2.0 * np.pi * f[0] / SR + phi
        acc = np.zeros(n)
        kmax = int(0.45 * SR / float(f.max()))
        for k in range(1, kmax + 1):
            rmax = (1.0 / (floor * k)) ** 0.25
            active = np.flatnonzero(fc * rmax > k * f)
            if active.size == 0:
                break  # pragul crește cu k: nici armonicele de deasupra nu mai trec
            m = int(active[-1]) + 1
            r2 = (k * f[:m] / fc[:m]) ** 2
            g = 1.0 / ((1.0 - r2) ** 2 + r2 / (q * q))
            acc[:m] += np.sin(k * x[:m]) * (g / k)
        gl, gr = pan_gains(pan)
        out[:, 0] += acc * gl * norm
        out[:, 1] += acc * gr * norm
    return out


def polyblep_saw(f: float, n: int, phase0: float) -> np.ndarray:
    """Fierăstrău cu corecție polyBLEP (aliasing mic), ieftin pentru notele lungi ale padului."""
    dt = f / SR
    ph = (phase0 + dt * np.arange(n)) % 1.0
    y = 2.0 * ph - 1.0
    m = ph < dt
    u = ph[m] / dt
    y[m] -= u + u - u * u - 1.0
    m = ph > 1.0 - dt
    u = (ph[m] - 1.0) / dt
    y[m] -= u * u + u + u + 1.0
    return y


def stft_lowpass(x: np.ndarray, fc_curve: np.ndarray, nfft: int = 2048, hop: int = 256,
                 highpass: bool = False) -> np.ndarray:
    """Filtru trece-jos (sau trece-sus) de 24 dB/octavă cu frecvența de tăiere variabilă, aplicat în domeniul
    STFT (tăierea se mișcă lent, deci cadrele de 43 ms nu se aud)."""
    f, tt, z = signal.stft(x.T, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    fc_t = np.interp(tt, np.arange(len(fc_curve)) / SR, fc_curve)
    r = f[:, None] / fc_t[None, :]
    if highpass:
        r = 1.0 / np.maximum(r, 1e-6)
    z = z * (1.0 / np.sqrt(1.0 + r**8))[None]
    _, y = signal.istft(z, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    return y.T[: len(x)]


def envelope(n: int, dur: float, att: float, decay: float, sustain: float, release: float) -> np.ndarray:
    t = np.arange(n) / SR
    env = (1.0 - np.exp(-t / att)) * (sustain + (1.0 - sustain) * np.exp(-t / decay))
    off = t > dur
    env[off] *= np.exp(-(t[off] - dur) / release)
    return env


STAB_VOICES = ((-11.0, -0.6), (0.0, 0.0), (11.0, 0.6))


def stab_sound(notes, vel: float, dur: float, rng_: np.random.Generator, cut_hi: float = 5200.0,
               cut_lo: float = 650.0, cut_tau: float = 0.085, amp_tau: float = 0.28, sustain: float = 0.0,
               release: float = 0.07, voices=STAB_VOICES) -> np.ndarray:
    """Acord scurt („stab”): fierăstraie dezacordate, filtrul se închide repede (sunet ciupit), atac de ~1 ms."""
    n = int((dur + 7 * release + 0.02) * SR)
    t = np.arange(n) / SR
    fc = cut_lo + (cut_hi - cut_lo) * np.exp(-t / cut_tau)
    y = np.zeros((n, 2))
    for nm in notes:
        f = hz(midi(nm))
        y += saw_additive(f, n, np.minimum(fc, 0.45 * SR), voices, rng_)
    y *= envelope(n, dur, 0.0008, amp_tau, sustain, release)[:, None] / np.sqrt(len(notes))
    return fade_tail(y * (vel / (3.0 * early_rms(y))), 20.0)


def bass_sound(f0: float, vel: float, dur: float, cut_peak: float = 1300.0, cut_base: float = 240.0,
               cut_tau: float = 0.06, release: float = 0.03) -> np.ndarray:
    """Bas: fierăstrău filtrat cu anvelopă (mișcarea), plus sinusul fundamentalei (greutatea). Mono."""
    n = int((dur + 7 * release) * SR)
    t = np.arange(n) / SR
    fc = cut_base + (cut_peak - cut_base) * np.exp(-t / cut_tau)
    saw = saw_additive(f0, n, fc)[:, 0]
    sub = np.sin(2.0 * np.pi * f0 * t)
    y = (0.75 * saw + 0.6 * sub) * envelope(n, dur, 0.0025, 0.12, 0.78, release)
    y = np.tanh(1.4 * y) / np.tanh(1.4)  # puțină saturație: armonice care se aud și pe difuzoare mici
    return fade_tail(y * vel, 8.0)


_SOS_CLICK = sos("bandpass", (1200, 4200), 2)


def kick_sound(vel: float, rng_: np.random.Generator, tune: float = 55.0, decay: float = 0.19,
               length: float = 0.46, click: float = 0.10, drive: float = 2.2) -> np.ndarray:
    """Kick: un sinus care coboară repede de la ~650 Hz la nota la (55 Hz), saturat ușor, plus un clic scurt."""
    n = int(length * SR)
    t = np.arange(n) / SR
    f = tune + 170.0 * np.exp(-t / 0.026) + 420.0 * np.exp(-t / 0.0035)
    ph = 2.0 * np.pi * (np.cumsum(f) - f[0]) / SR
    amp = (1.0 - np.exp(-t / 0.0004)) * (0.9 * np.exp(-t / decay) + 0.1 * np.exp(-t / 0.015))
    y = np.tanh(drive * np.sin(ph) * amp) / np.tanh(drive)
    if click > 0:
        nz = signal.sosfilt(_SOS_CLICK, rng_.standard_normal(n))
        y = y + click * nz / (np.max(np.abs(nz[: int(0.004 * SR)])) + 1e-12) * np.exp(-t / 0.0012)
    return fade_tail(y * vel, 40.0)


_SOS_CLAP_BP = sos("bandpass", (800, 1900), 2)
_SOS_CLAP_PRES = sos("bandpass", (2600, 5200), 2)
_SOS_CLAP_AIR = sos("highpass", 7500, 2)


CLAP_FLAMS = ((0.0, 1.0), (0.007, 0.85), (0.013, 0.7), (0.019, 0.6))
SNARE_FLAMS = ((0.0, 1.0),)


def clap_sound(vel: float, rng_: np.random.Generator, tail: float = 0.10, body: float = 0.32,
               air: float = 0.22, length: float = 0.5, flams=CLAP_FLAMS, presence: float = 0.32) -> np.ndarray:
    """Clap/snare: impulsuri de zgomot (primul fix pe timp), coadă scurtă, corp tonal la 190 Hz.
    Clap-ul are patru impulsuri; snare-ul din rafale doar unul (ca să rămână precis și la 32-imi)."""
    n = int(length * SR)
    t = np.arange(n) / SR
    noise = rng_.standard_normal(n)
    env = np.zeros(n)
    for d, a in flams:
        m = t >= d
        env[m] += a * np.exp(-(t[m] - d) / 0.0028) * (1.0 - np.exp(-(t[m] - d) / 0.0002))
    d_last = flams[-1][0]
    m = t >= d_last
    env[m] += 0.5 * np.exp(-(t[m] - d_last) / tail)
    mid = signal.sosfilt(_SOS_CLAP_BP, noise)
    pres = signal.sosfilt(_SOS_CLAP_PRES, noise)
    hi = signal.sosfilt(_SOS_CLAP_AIR, noise)
    y = (mid / (np.std(mid) + 1e-12) + presence * pres / (np.std(pres) + 1e-12)
         + air * hi / (np.std(hi) + 1e-12)) * env
    y /= np.max(np.abs(y)) + 1e-12
    tone = (np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045) + 0.5 * np.sin(2 * np.pi * 340 * t) * np.exp(-t / 0.025))
    y = y + body * tone * (1.0 - np.exp(-t / 0.0005))
    return fade_tail(y * vel, 30.0)


_SOS_HAT_HP = sos("highpass", 6000, 2)
_SOS_HAT_LP = sos("lowpass", 14000, 2)
_SOS_CRASH_HP = sos("highpass", 4800, 2)
_SOS_CRASH_LP = sos("lowpass", 15000, 2)
_METAL = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)  # șase oscilatoare dreptunghiulare, ca la cinelele analogice


def metal(n: int, scale: float, rng_: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    y = sum(np.sign(np.sin(2 * np.pi * f * scale * t + rng_.uniform(0, 2 * np.pi))) for f in _METAL)
    return y / len(_METAL)


def hat_sound(vel: float, rng_: np.random.Generator, decay: float = 0.026, length: float = 0.14) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    x = 0.55 * rng_.standard_normal(n) + 0.9 * metal(n, 1.0, rng_)
    y = signal.sosfilt(_SOS_HAT_LP, signal.sosfilt(_SOS_HAT_HP, x))
    y *= (1.0 - np.exp(-t / 0.0003)) * np.exp(-t / decay)
    return fade_tail(y * vel / (np.max(np.abs(y)) + 1e-12), 10.0)


def crash_sound(vel: float, rng_: np.random.Generator, length: float = 2.2, decay: float = 0.8) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for c in range(2):
        x = 0.7 * rng_.standard_normal(n) + 0.6 * metal(n, 1.55 + 0.03 * c, rng_)
        y = signal.sosfilt(_SOS_CRASH_LP, signal.sosfilt(_SOS_CRASH_HP, x))
        out[:, c] = y * (1.0 - np.exp(-t / 0.0012)) * (0.45 * np.exp(-t / 0.09) + 0.55 * np.exp(-t / decay))
    return fade_tail(out * vel / (np.max(np.abs(out)) + 1e-12), 80.0)


def riser_noise(length: float, f0: float, f1: float, rng_: np.random.Generator, bw_oct: float = 0.8,
                power: float = 1.5) -> np.ndarray:
    """Riser din zgomot: o bandă care urcă exponențial de la f0 la f1, cu volum crescător; se taie fix la final."""
    n = int(round(length * SR))
    x = rng_.standard_normal((2, n + 4096))
    nfft, hop = 2048, 256
    f, tt, z = signal.stft(x, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    u = np.clip(tt / length, 0.0, 1.0) ** power
    fc = f0 * (f1 / f0) ** u
    lf = np.log2(np.maximum(f, 1.0)[:, None] / fc[None, :])
    z = z * np.exp(-0.5 * (lf / bw_oct) ** 2)[None]
    _, y = signal.istft(z, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    y = y[:, :n].T
    t = np.arange(n) / SR
    env = (t / length) ** 2.2
    k = int(0.002 * SR)
    env[-k:] *= np.linspace(1.0, 0.0, k)
    return y / (np.max(np.abs(y)) + 1e-12) * env[:, None]


def riser_pitch(notes, length: float, semitones: float, rng_: np.random.Generator) -> np.ndarray:
    """Riser tonal: un acord de fierăstraie care urcă (glissando) și se deschide; se taie fix la final."""
    n = int(round(length * SR))
    u = np.arange(n) / n
    fc = 350.0 * (6500.0 / 350.0) ** (u**1.3)
    out = np.zeros((n, 2))
    for nm in notes:
        f = hz(midi(nm)) * 2.0 ** (semitones / 12.0 * u**1.6)
        out += saw_additive(f, n, fc, ((-16.0, -0.85), (0.0, 0.0), (16.0, 0.85)), rng_)
    env = u**2.5
    k = int(0.002 * SR)
    env[-k:] *= np.linspace(1.0, 0.0, k)
    return out * env[:, None] / (np.max(np.abs(out)) + 1e-12)


def sub_drop(f_start: float, f_end: float, length: float, vel: float, tau: float = 0.22,
             decay: float = 0.5) -> np.ndarray:
    """Sub care coboară (un sinus a cărui notă cade o octavă), pentru „un plan.”."""
    n = int(length * SR)
    t = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-t / tau)
    ph = 2.0 * np.pi * (np.cumsum(f) - f[0]) / SR
    amp = (1.0 - np.exp(-t / 0.003)) * np.exp(-t / decay)
    y = np.tanh(1.5 * (np.sin(ph) + 0.22 * np.sin(2 * ph)) * amp) / np.tanh(1.5)
    return fade_tail(y * vel, 60.0)


def lead_sound(f0: float, vel: float, dur: float, rng_: np.random.Generator) -> np.ndarray:
    """Motivul: coardă ciupită Karplus-Strong (din compose.py) + un fierăstrău scurt filtrat + clopoțel la octavă."""
    length = dur + 1.2
    ks = C.ks_pluck(f0, 1.0, length, 1.3, 0.62, rng_, damp_at=dur, damp_tau=0.25)
    n = len(ks)
    t = np.arange(n) / SR
    fc = 900.0 + 5200.0 * np.exp(-t / 0.05)
    saw = saw_additive(f0, n, fc, ((-7.0, -0.3), (7.0, 0.3)), rng_)
    saw *= envelope(n, dur, 0.0008, 0.22, 0.0, 0.08)[:, None]
    gl = C.glass(2.0 * f0, 1.0, 1.1, length)[:n]
    y = (0.55 * ks / early_rms(ks))[:, None] + 0.5 * saw / early_rms(saw) + (0.22 * gl / early_rms(gl))[:, None]
    return fade_tail(y * (vel / (3.0 * early_rms(y))), 40.0)


def arp_sound(f0: float, vel: float, rng_: np.random.Generator) -> np.ndarray:
    """Notă scurtă de arpegiu (fierăstrău ciupit)."""
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    fc = 600.0 + 2800.0 * np.exp(-t / 0.035)
    y = saw_additive(f0, n, fc, ((-6.0, -0.3), (6.0, 0.3)), rng_)
    y *= envelope(n, 0.09, 0.0008, 0.07, 0.0, 0.04)[:, None]
    return fade_tail(y * (vel / (3.0 * early_rms(y))), 15.0)


def pump(times: list[tuple[float, float]], depth: float, release: float = 0.16, attack: float = 0.003) -> np.ndarray:
    """Sidechain calculat din momentele kick-ului (nu din audio): câștigul coboară la kick și revine lin."""
    env = np.zeros(N)
    ln = int(0.5 * SR)
    tt = np.arange(ln) / SR
    shape = (1.0 - np.exp(-tt / attack)) * np.exp(-tt / release)
    shape /= shape.max()
    for t0, v in times:
        i0 = int(round(t0 * SR))
        i1 = min(N, i0 + ln)
        if i0 < N:
            env[i0:i1] = np.maximum(env[i0:i1], v * shape[: i1 - i0])
    return 1.0 - depth * env


# ======================================================================================
# 4. PARTITURA: din HITS, TIMELINE și secțiuni, în evenimente
# ======================================================================================

# Padul (de la 4,5 s): nivel 0-1 și frecvența de tăiere (Hz), puncte (timp, valoare). Două puncte cu același
# timp fac un salt. 17,5-19,0: filtrul se închide („Nu sunt sigur”); 20-21,75: se deschide (build);
# 21,75-22,0: o optime de gol înainte de drop.
PAD_LEVEL = [(0.0, 0.0), (4.5, 0.0), (5.98, 0.8), (6.0, 1.0), (17.5, 1.0), (17.56, 0.75), (19.0, 0.75),
             (19.02, 1.0), (21.72, 1.0), (21.75, 0.0), (22.0, 0.0), (22.0, 1.0), (26.0, 1.0), (26.0, 1.15),
             (28.0, 0.7), (29.6, 0.0)]
PAD_CUTOFF = [(0.0, 400.0), (4.5, 450.0), (5.98, 2400.0), (6.0, 1900.0), (12.0, 2300.0), (17.5, 2500.0),
              (17.6, 420.0), (19.0, 450.0), (19.0, 2400.0), (20.0, 1800.0), (21.75, 7000.0), (22.0, 3000.0),
              (26.0, 3400.0), (29.9, 700.0)]

# În build basul se subțiază (filtru trece-sus care urcă până la 200 Hz); pe 22,0 revine tot.
BASS_HP = [(0.0, 18.0), (20.0, 18.0), (21.75, 200.0), (22.0, 200.0), (22.0, 18.0), (DURATION, 18.0)]

# Basul: (pas de șaisprezecime în măsură, interval față de fundamentală, velocity, lungime în pași)
BASS_OFFBEAT = ((2, 0, 0.95, 1.7), (6, 12, 0.8, 1.7), (10, 0, 0.95, 1.7), (14, 12, 0.8, 1.7))
BASS_ROLLING = ((2, 0, 1.0, 0.9), (3, 12, 0.6, 0.8), (6, 0, 0.95, 0.9), (7, 12, 0.6, 0.8),
                (10, 0, 1.0, 0.9), (11, 12, 0.6, 0.8), (14, 0, 0.95, 0.9), (15, 7, 0.65, 0.8))
BASS_DRIVE = ((2, 0, 1.0, 1.8), (6, 0, 0.95, 1.8), (10, 0, 1.0, 1.8), (14, 0, 0.95, 1.8))
ARP_IDX = (0, 2, 1, 3)  # arpegiul: cele 4 note de sus ale acordului, în ordinea jos, sus-mijloc, mijloc, sus
COUNT_UP = ["A3", "B3", "C#4", "E4", "F#4", "A4", "B4", "C#5", "E5", "F#5", "A5", "B5"]  # cifra care urcă


def chord_at(t: float) -> str:
    name = TIMELINE[0][1]
    for t0, nm in TIMELINE:
        if t0 <= t + 1e-9:
            name = nm
    return name


def grid(t0: float, t1: float, step: float) -> list[float]:
    """Momentele t0, t0 + step, ... mai mici decât t1 (fiecare cade exact pe un eșantion)."""
    k = int(np.ceil((t1 - t0) / step - 1e-9))
    return [round(t0 + i * step, 6) for i in range(max(0, k))]


def is_beat(t: float, every: float) -> bool:
    return abs(t / every - round(t / every)) < 1e-9


def build_score() -> dict:
    S: dict = {k: [] for k in ("boom", "roll", "hat", "ohat", "crash", "bass", "subdrop", "stab", "lead", "arp",
                               "riser")}
    kicks: dict[float, dict] = {}
    claps: dict[float, dict] = {}

    def kick(t: float, vel: float, **opt) -> None:
        if t not in kicks or kicks[t]["vel"] < vel:
            kicks[t] = {"t": t, "vel": vel, **opt}

    def clap(t: float, vel: float, **opt) -> None:
        if t not in claps or claps[t]["vel"] < vel:
            claps[t] = {"t": t, "vel": vel, **opt}

    # ---- groove: kick pe fiecare timp, clap pe 2 și 4 ----
    for t in grid(6.0, 17.5, BEAT) + grid(19.0, 22.0, BEAT) + grid(22.0, 26.0, BEAT):
        kick(t, 0.95 if is_beat(t, BAR) else 0.9)
    kick(18.0, 0.55)  # „Nu sunt sigur”: un singur kick moale (jumătate de tempo)
    for t in grid(6.0, 17.5, BEAT) + grid(19.0, 20.0, BEAT) + grid(22.0, 26.0, BEAT):
        if int(round((t % BAR) / BEAT)) in (1, 3):
            clap(t, 0.8)
    clap(18.5, 0.42)

    # ---- hi-hat: închis pe contratimp, ghost-uri în șaisprezecimi, deschis din a doua jumătate ----
    for t in (3.25, 3.75, 4.25):
        S["hat"].append({"t": t, "vel": 0.34})
    for i, t in enumerate(grid(4.75, 6.0, STEP)):
        S["hat"].append({"t": t, "vel": 0.2 + 0.03 * i})
    for t in grid(6.25, 12.0, BEAT):
        S["hat"].append({"t": t, "vel": 0.62})
    for t in grid(10.0, 17.5, STEP) + grid(19.0, 20.0, STEP):
        s = int(round((t % BEAT) / STEP))
        if s in (1, 3):
            S["hat"].append({"t": t, "vel": 0.24 if s == 1 else 0.3})
    for t in grid(20.0, 21.75, STEP):  # build: toate șaisprezecimile, tot mai tare
        S["hat"].append({"t": t, "vel": 0.25 + 0.22 * (t - 20.0)})
    for t in grid(12.25, 17.5, BEAT) + grid(19.25, 20.0, BEAT) + grid(22.25, 26.0, BEAT):
        S["ohat"].append({"t": t, "vel": 0.5})

    # ---- rafale de snare: spre consolă, pe hartă, build-ul, spre logo ----
    for i, t in enumerate(grid(5.5, 6.0, STEP)):
        S["roll"].append({"t": t, "vel": 0.32 + 0.12 * i})
    for i, t in enumerate(grid(11.5, 12.0, STEP)):
        S["roll"].append({"t": t, "vel": 0.38 + 0.12 * i})
    for t in grid(20.0, 21.0, BEAT / 2):
        S["roll"].append({"t": t, "vel": 0.42 + 0.16 * (t - 20.0)})
    for t in grid(21.0, 21.5, STEP):
        S["roll"].append({"t": t, "vel": 0.6 + 0.3 * (t - 21.0)})
    for t in grid(21.5, 22.0, STEP / 2):
        S["roll"].append({"t": t, "vel": 0.78 + 0.44 * (t - 21.5)})
    for t, v in ((25.75, 0.45), (25.875, 0.6)):
        S["roll"].append({"t": t, "vel": v})

    # ---- loviturile filmului ----
    for t, name, _screen, kind, notes in HITS:
        nts = notes if notes is not None else CHORDS[chord_at(t)][2]
        if kind == "stab":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 0.95, "dur": 0.16})
            kick(t, 0.55, decay=0.06)  # scurt: nu bate cu nota de bas
        elif kind == "accent":
            short = t < 6.0  # „un plan.”: scurt, ca după el să rămână aer până la 3,0
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 1.0, "dur": 0.22 if short else 0.3,
                              "amp_tau": 0.3 if short else 0.4, "cut_hi": 6000.0})
            kick(t, 1.0)
            clap(t, 0.85)
            if t >= 6.0:
                S["crash"].append({"t": t, "vel": 0.4, "length": 1.2, "decay": 0.35})
        elif kind == "hold":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 1.0, "dur": 1.42, "sustain": 0.4,
                              "amp_tau": 0.35, "cut_lo": 1300.0, "cut_tau": 0.45, "release": 0.03})
            kick(t, 1.0)
            clap(t, 0.9)
            S["crash"].append({"t": t, "vel": 0.35, "length": 1.4, "decay": 0.4})
        elif kind == "big":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 1.05, "dur": 0.4, "amp_tau": 0.45,
                              "cut_hi": 6500.0})
            kick(t, 1.0)
            clap(t, 0.95)
            S["boom"].append({"t": t, "vel": 0.62})
            S["crash"].append({"t": t, "vel": 0.9, "length": 2.4, "decay": 0.9})
        elif kind == "press":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 0.8, "dur": 0.05, "amp_tau": 0.06,
                              "cut_hi": 3800.0, "cut_tau": 0.03})
            clap(t, 0.7, tail=0.04)
        elif kind == "press_big":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 1.0, "dur": 0.25, "amp_tau": 0.35,
                              "cut_hi": 6000.0})
            kick(t, 1.0)
            clap(t, 0.9)
            S["crash"].append({"t": t, "vel": 0.6, "length": 1.8, "decay": 0.6})
        elif kind == "note":
            S["lead"].append({"t": t, "name": name, "m": midi(nts[0]), "vel": 0.9, "dur": 0.42})
        elif kind == "lift":
            for i, nm in enumerate(nts):
                S["lead"].append({"t": t + i * STEP, "name": name if i == 0 else f"{name}_{i}", "m": midi(nm),
                                  "vel": 0.5 + 0.1 * i, "dur": 0.1})
        elif kind == "soft":
            S["stab"].append({"t": t, "name": name, "notes": nts, "vel": 0.75, "dur": 0.9, "amp_tau": 0.6,
                              "sustain": 0.2, "cut_hi": 1900.0, "cut_lo": 500.0, "cut_tau": 0.2, "release": 0.25})
        elif kind == "final":
            S["stab"].append({"t": t, "name": name, "notes": CHORDS["Afinal"][2], "vel": 1.1, "dur": 2.6,
                              "sustain": 0.3, "amp_tau": 1.0, "cut_hi": 5200.0, "cut_lo": 1100.0, "cut_tau": 0.6,
                              "release": 0.7})
            kick(t, 1.0)
            S["boom"].append({"t": t, "vel": 0.75})
            S["crash"].append({"t": t, "vel": 0.85, "length": 3.2, "decay": 1.1})
            for nm, v in (("A5", 0.5), ("C#6", 0.42), ("E6", 0.36)):
                S["lead"].append({"t": t, "name": "final_bell", "m": midi(nm), "vel": v, "dur": 1.6})
        else:
            raise ValueError(f"tip necunoscut: {kind}")
    S["subdrop"].append({"t": 2.0, "f0": hz(midi("D2")), "f1": hz(midi("D1")), "length": 1.0, "vel": 0.9})

    # ---- arpegiul (din măsura 7) și cifra care urcă (22,0-23,5) ----
    for t in grid(12.0, 17.5, STEP) + grid(19.0, 21.75, STEP):
        tones = sorted(midi(nm) for nm in CHORDS[chord_at(t)][2])[-4:]
        s = int(round((t % BEAT) / STEP))
        S["arp"].append({"t": t, "m": tones[ARP_IDX[s]] + (12 if t >= 21.0 else 0), "vel": 0.5 if s == 0 else 0.36,
                         "gain_db": 0.0})
    for i, (t, nm) in enumerate(zip(grid(22.0, 23.5, STEP), COUNT_UP)):
        S["arp"].append({"t": t, "m": midi(nm), "vel": 0.55 + 0.03 * i, "gain_db": 4.0})
    S["lead"].append({"t": 23.5, "name": "cifra_gata", "m": midi("C#6"), "vel": 0.7, "dur": 0.3})

    # ---- basul ----
    for t, nm in ((0.0, "F#1"), (0.5, "F#1"), (1.5, "G#1"), (3.0, "B1"), (3.5, "C#2"), (4.0, "D2")):
        S["bass"].append({"t": t, "m": midi(nm), "vel": 0.9, "dur": 0.2, "cut_peak": 1500.0})
    S["bass"].append({"t": 4.5, "m": midi("E1"), "vel": 0.85, "dur": 1.42, "cut_peak": 900.0, "cut_tau": 0.25})

    def lay(t0: float, t1: float, pattern) -> None:
        for b0 in grid(0.0, DURATION, BAR):
            for step, iv, vel, ln in pattern:
                t = round(b0 + step * STEP, 6)
                if t0 - 1e-9 <= t < t1 - 1e-9:
                    S["bass"].append({"t": t, "m": midi(CHORDS[chord_at(t)][0]) + iv, "vel": vel,
                                      "dur": ln * STEP - 0.01})

    lay(6.0, 10.0, BASS_OFFBEAT)
    lay(10.0, 17.5, BASS_ROLLING)
    lay(19.0, 21.75, BASS_ROLLING)
    lay(22.0, 26.0, BASS_DRIVE)
    S["bass"].append({"t": 17.5, "m": midi("F#1"), "vel": 0.6, "dur": 1.45, "cut_peak": 420.0, "cut_base": 180.0,
                      "cut_tau": 0.3})
    S["bass"].append({"t": 26.0, "m": midi("A1"), "vel": 0.95, "dur": 2.3, "cut_peak": 800.0, "cut_tau": 0.3,
                      "release": 0.4})

    # ---- risere (se taie fix pe lovitura următoare) ----
    S["riser"] += [
        {"kind": "noise", "t0": 5.0, "t1": 6.0, "f0": 500.0, "f1": 7000.0, "vel": 0.8},
        {"kind": "pitch", "t0": 5.0, "t1": 6.0, "notes": ["E3", "B3"], "semis": 7.0, "vel": 0.5},
        {"kind": "noise", "t0": 11.5, "t1": 12.0, "f0": 1500.0, "f1": 6000.0, "vel": 0.35},
        {"kind": "noise", "t0": 20.0, "t1": 22.0, "f0": 300.0, "f1": 9000.0, "vel": 1.0},
        {"kind": "pitch", "t0": 20.0, "t1": 22.0, "notes": ["E3", "B3", "E4"], "semis": 12.0, "vel": 0.7},
    ]
    S["kick"] = sorted(kicks.values(), key=lambda e: e["t"])
    S["clap"] = sorted(claps.values(), key=lambda e: e["t"])
    for k in ("hat", "ohat", "roll", "stab", "lead", "arp", "bass", "crash", "boom"):
        S[k].sort(key=lambda e: e["t"])
    return S


# ======================================================================================
# 5. RANDARE PE STEM-URI, MIXAJ, MASTER
# ======================================================================================

PAD_VOICES = ((-14.0, -0.9), (-5.0, -0.35), (0.0, 0.0), (5.0, 0.35), (14.0, 0.9))


def render_pad() -> np.ndarray:
    """Pad: cinci fierăstraie dezacordate pe notă, filtrate; o notă comună cu acordul următor ține (legato)."""
    segs = []
    for i, (t0, nm) in enumerate(TIMELINE):
        t1 = TIMELINE[i + 1][0] if i + 1 < len(TIMELINE) else DURATION
        if t0 >= 4.5 - 1e-9:
            segs.append((t0, t1, nm))
    events, active = [], {}
    for t0, _t1, nm in segs:
        notes = {midi(x) for x in CHORDS[nm][1]}
        for m in list(active):
            if m not in notes:
                events.append((m, active.pop(m), t0))
        for m in sorted(notes):
            active.setdefault(m, t0)
    events += [(m, s, DURATION) for m, s in active.items()]
    out = np.zeros((N, 2))
    r = rng("pad")
    for m, t0, t1 in sorted(events):
        i0, i_off = int(round(t0 * SR)), int(round(t1 * SR))
        i1 = min(N, i_off + int(1.75 * SR))
        n = i1 - i0
        env = envelope(n, (i_off - i0) / SR, 0.02, 1.0, 1.0, 0.25)
        for cents, p in PAD_VOICES:
            y = polyblep_saw(hz(m) * 2.0 ** (cents / 1200.0), n, float(r.uniform())) * env
            gl, gr = pan_gains(p)
            out[i0:i1, 0] += y * gl
            out[i0:i1, 1] += y * gr
    out = stft_lowpass(out, curve(PAD_CUTOFF, log=True))
    out = signal.sosfilt(sos("highpass", 140, 2), out, axis=0)  # padul lasă loc basului și kick-ului
    return out * curve(PAD_LEVEL)[:, None] * (0.5 / len(PAD_VOICES))


def render_drums(S: dict, room: np.ndarray, hall: np.ndarray) -> np.ndarray:
    parts = {k: np.zeros((N, 2)) for k in ("kick", "boom", "clap", "roll", "hat", "ohat", "crash")}
    for i, e in enumerate(S["kick"]):
        opt = {k: e[k] for k in ("decay",) if k in e}
        add_at(parts["kick"], kick_sound(e["vel"], rng("kick", i), **opt), e["t"])
    for i, e in enumerate(S["boom"]):
        add_at(parts["boom"], kick_sound(e["vel"], rng("boom", i), tune=46.0, decay=0.6, length=1.6, click=0.0,
                                         drive=1.6), e["t"])
    for i, e in enumerate(S["clap"]):
        add_at(parts["clap"], clap_sound(e["vel"], rng("clap", i), tail=e.get("tail", 0.10)), e["t"], pan_gains(-0.06))
    for i, e in enumerate(S["roll"]):
        add_at(parts["roll"], clap_sound(e["vel"], rng("roll", i), tail=0.06, body=0.45, air=0.3,
                                                     flams=SNARE_FLAMS), e["t"],
               pan_gains(0.12 * np.sin(1.7 * i)))
    for i, e in enumerate(S["hat"]):
        add_at(parts["hat"], hat_sound(e["vel"], rng("hat", i)), e["t"], pan_gains(0.25))
    for i, e in enumerate(S["ohat"]):
        add_at(parts["ohat"], hat_sound(e["vel"], rng("ohat", i), decay=0.11, length=0.42), e["t"], pan_gains(-0.2))
    for i, e in enumerate(S["crash"]):
        add_at(parts["crash"], crash_sound(e["vel"], rng("crash", i), e["length"], e["decay"]), e["t"])
    for k in parts:
        parts[k] *= db(MIX_DB[k])
    out = sum(parts.values())
    for k in ("clap", "roll", "hat", "ohat"):
        out = out + C.reverb(parts[k], room, ROOM_SEND[k])
    return out + C.reverb(parts["crash"], hall, HALL_SEND["crash"])


def render_bass(S: dict, kicks) -> tuple[np.ndarray, np.ndarray]:
    bass = np.zeros((N, 2))
    for e in S["bass"]:
        opt = {k: e[k] for k in ("cut_peak", "cut_base", "cut_tau", "release") if k in e}
        add_at(bass, bass_sound(hz(e["m"]), e["vel"], e["dur"], **opt), e["t"])
    groove_kicks = [(t, v) for t, v in kicks if t >= 6.0 - 1e-9]  # în cârlig basul lovește odată cu kick-ul
    bass = signal.sosfilt(sos("lowpass", 3000, 2), bass, axis=0) * pump(groove_kicks, 0.75, release=0.09)[:, None]
    bass = stft_lowpass(bass, curve(BASS_HP, log=True), highpass=True)  # build: basul se subțiază, drop-ul revine
    drop = np.zeros((N, 2))
    for e in S["subdrop"]:
        add_at(drop, sub_drop(e["f0"], e["f1"], e["length"], e["vel"]), e["t"])
    return bass * db(MIX_DB["bass"]) * 0.35, drop * db(MIX_DB["subdrop"]) * 0.35


def render_stabs(S: dict) -> np.ndarray:
    dry = np.zeros((N, 2))
    keys = ("cut_hi", "cut_lo", "cut_tau", "amp_tau", "sustain", "release")
    for i, e in enumerate(S["stab"]):
        y = stab_sound(e["notes"], e["vel"], e["dur"], rng("stab", i), **{k: e[k] for k in keys if k in e})
        add_at(dry, y, e["t"])
    dry = signal.sosfilt(sos("highpass", 110, 2), dry, axis=0)
    return dry * db(MIX_DB["stabs"]) * 0.25


def render_lead(S: dict) -> tuple[np.ndarray, np.ndarray]:
    lead = np.zeros((N, 2))
    for i, e in enumerate(S["lead"]):
        add_at(lead, lead_sound(hz(e["m"]), e["vel"], e["dur"], rng("lead", i)), e["t"],
               pan_gains(0.1 if i % 2 else -0.1))
    arp = np.zeros((N, 2))
    for i, e in enumerate(S["arp"]):
        add_at(arp, arp_sound(hz(e["m"]), e["vel"] * db(e["gain_db"]), rng("arp", i)), e["t"],
               pan_gains(0.35 * np.sin(2 * np.pi * i / 7.0)))
    return lead * db(MIX_DB["lead"]) * 0.25, arp * db(MIX_DB["arp"]) * 0.25


def render_fx(S: dict) -> np.ndarray:
    out = np.zeros((N, 2))
    for i, e in enumerate(S["riser"]):
        ln = e["t1"] - e["t0"]
        if e["kind"] == "noise":
            y = riser_noise(ln, e["f0"], e["f1"], rng("riser", i))
        else:
            y = riser_pitch(e["notes"], ln, e["semis"], rng("riser", i))
        add_at(out, y * e["vel"], e["t0"])
    return out * db(MIX_DB["fx"]) * 0.5


def render_all(verbose: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    say = print if verbose else (lambda *a, **k: None)
    S = build_score()
    kicks = [(e["t"], e["vel"]) for e in S["kick"]]
    hall = C.make_ir(2.4, (1.9, 1.6, 0.9), 0.02, SEED + 1)
    room = C.make_ir(0.8, (0.5, 0.42, 0.25), 0.006, SEED + 2, early=False)
    say("· tobe")
    drums = render_drums(S, room, hall)
    say("· bas")
    bass, drop = render_bass(S, kicks)
    say("· pad")
    pad = render_pad() * pump(kicks, 0.6, release=0.16)[:, None] * db(MIX_DB["pad"])
    say("· stab-uri")
    stabs = render_stabs(S)
    say("· motiv și arpegiu")
    lead, arp = render_lead(S)
    say("· risere")
    fx = render_fx(S)
    say("· reverb și ecou")
    stab_echo = C.pingpong(stabs * 0.16, delay=3 * STEP, feedback=0.3, repeats=4, wet=1.0)
    lead_echo = C.pingpong(lead * 0.22, delay=3 * STEP, feedback=0.32, repeats=4, wet=1.0)
    stems = {
        "drums": drums,
        "bass": bass + drop,
        "pad": pad + C.reverb(pad, hall, HALL_SEND["pad"]),
        "stabs": stabs + stab_echo + C.reverb(stabs + stab_echo, hall, HALL_SEND["stabs"]),
        "lead": lead + arp + lead_echo + C.reverb(lead + lead_echo + arp, hall, HALL_SEND["lead"]),
        "fx": fx + C.reverb(fx, hall, HALL_SEND["fx"]),
    }
    # Liniar și cauzal, identic pe fiecare stem: sub 120 Hz totul e mono, fără infrasunete, finalul se stinge.
    hp = sos("highpass", 25, 2)
    en = curve([(0.0, 1.0), (FADE_FROM, 1.0), (SILENT_FROM - 0.04, 0.0), (DURATION, 0.0)])
    for k in STEMS:
        x = signal.sosfilt(hp, C.mono_below(stems[k], 120.0), axis=0)
        stems[k] = x * en[:, None]
    return stems, S


def master(stems: dict[str, np.ndarray], verbose: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    """Un câștig static până la -16 LUFS, apoi limitatorul de vârf real din compose.py. Amândouă se aplică
    identic pe toate stem-urile, deci suma stem-urilor rămâne exact mixajul."""
    mix = sum(stems[k] for k in STEMS)
    gain_db = TARGET_LUFS - C.lufs_integrated(mix)
    info: dict = {}
    lim = np.ones(N)
    for _ in range(6):
        lim = C.limiter_gain(mix * db(gain_db), CEILING_DBTP)
        out = mix * db(gain_db) * lim[:, None]
        lufs = C.lufs_integrated(out)
        info = {"gain_db": gain_db, "lufs": lufs, "tp": C.true_peak_db(out),
                "max_gr_db": float(-20 * np.log10(lim.min())),
                "limited_ms": float(np.sum(lim < 0.999) / SR * 1000)}
        if abs(lufs - TARGET_LUFS) < 0.03:
            break
        gain_db += TARGET_LUFS - lufs
    if verbose:
        print(f"· master: câștig {info['gain_db']:+.2f} dB, {info['lufs']:.2f} LUFS, vârf real {info['tp']:.2f} dBTP, "
              f"limitare maximă {info['max_gr_db']:.2f} dB, {info['limited_ms']:.0f} ms limitate")
    final = {k: stems[k] * db(info["gain_db"]) * lim[:, None] for k in STEMS}
    z = int(round(SILENT_FROM * SR))
    for k in STEMS:
        final[k][z:] = 0.0
    return final, info


# ======================================================================================
# 6. FIȘIERE: WAV 24 de biți, stem-uri, cues_120.json, m4a
# ======================================================================================


def frame_of(t: float) -> int:
    return int(round(t * FPS))


def cues_json(S: dict, info: dict) -> dict:
    def uniq(ts):
        return sorted({round(float(t), 6) for t in ts})

    bars = []
    for b in range(1, N_BARS + 1):
        t0 = (b - 1) * BAR
        sec, screen, music = BARS[b]
        chords = [nm for t, nm in TIMELINE if t0 - 1e-9 <= t < t0 + BAR - 1e-9]
        bars.append({"bar": b, "start": t0, "end": t0 + BAR, "frame_start": frame_of(t0),
                     "frame_end": frame_of(t0 + BAR), "section": sec, "on_screen": screen, "music": music,
                     "chord_at_start": chord_at(t0), "chord_changes": chords})
    beats = [{"time": round(i * BEAT, 6), "frame": i * 15, "bar": i // 4 + 1, "beat": i % 4 + 1,
              "downbeat": i % 4 == 0} for i in range(N_BARS * BEATS_PER_BAR)]
    hits = []
    for t, name, screen, kind, notes in HITS:
        layers = {"stab": "stab + kick scurt + bas", "accent": "stab mare + kick + clap (+ crash în groove)",
                  "hold": "acord ținut + kick + clap + crash mic; riser 5,0-6,0", "big": "stab + kick + boom + clap + crash",
                  "press": "stab foarte scurt + clap strâns", "press_big": "stab + kick + clap + crash",
                  "note": "o notă din motiv (coardă ciupită + clopoțel)", "lift": "4 note în șaisprezecimi + rafală",
                  "soft": "acord moale, filtrat; tobele se rup până la 19,0",
                  "final": "A add9 mare + kick + boom + crash + clopoței; tobele se opresc"}[kind]
        if name == "un_plan":
            layers = "stab mare + kick + clap + sub care coboară o octavă (re); apoi aer până la 3,0"
        hits.append({"name": name, "time": t, "frame": frame_of(t), "frame_exact": round(t * FPS, 6),
                     "on_screen": screen, "kind": kind, "music": layers, "chord": chord_at(t),
                     "notes": notes if notes is not None else CHORDS[chord_at(t)][2]})
    return {
        "title": "Tura de mâine, varianta cinetică (muzica filmului de 30 s)",
        "file": WAV_NAME,
        "bpm": BPM,
        "time_signature": "4/4",
        "key": "la major (cârligul pornește din fa diez minor)",
        "sample_rate": SR,
        "fps": FPS,
        "duration_seconds": DURATION,
        "bar_seconds": BAR,
        "bar_frames": 60,
        "beat_seconds": BEAT,
        "beat_frames": 15,
        "sixteenth_seconds": STEP,
        "sections": [
            {"name": "cârlig", "start": 0.0, "end": 6.0, "note": "acorduri pe cuvinte, fără kick continuu"},
            {"name": "groove", "start": 6.0, "end": 20.0, "note": "kick pe fiecare timp, clap pe 2 și 4"},
            {"name": "energie mai mică", "start": 17.5, "end": 19.0, "note": "„Nu sunt sigur”: filtru închis"},
            {"name": "build", "start": 20.0, "end": 22.0, "note": "rafală de snare și riser până fix la 22,0"},
            {"name": "drop", "start": 22.0, "end": 26.0, "note": "mai rar, dar tot plin de energie"},
            {"name": "final", "start": 26.0, "end": DURATION, "note": "logoul; zero digital de la 29,9"},
        ],
        "chords": [{"time": t, "frame": frame_of(t), "chord": nm} for t, nm in TIMELINE],
        "bars": bars,
        "beats": beats,
        "hits": hits,
        "accents": {h["name"]: {"time": h["time"], "frame": h["frame"]} for h in hits}
        | {"fade_start": {"time": FADE_FROM, "frame": frame_of(FADE_FROM)},
           "silent_from": {"time": SILENT_FROM, "frame": frame_of(SILENT_FROM)}},
        "events": {
            "kick": uniq(e["t"] for e in S["kick"]),
            "clap": uniq(e["t"] for e in S["clap"]),
            "snare_roll": uniq(e["t"] for e in S["roll"]),
            "hat_closed": uniq(e["t"] for e in S["hat"]),
            "hat_open": uniq(e["t"] for e in S["ohat"]),
            "crash": uniq(e["t"] for e in S["crash"]),
            "stab": uniq(e["t"] for e in S["stab"]),
            "lead": uniq(e["t"] for e in S["lead"]),
            "arp": uniq(e["t"] for e in S["arp"]),
            "bass": uniq(e["t"] for e in S["bass"]),
            "risers": [{"start": e["t0"], "end": e["t1"], "kind": e["kind"]} for e in S["riser"]],
        },
        "stems": list(STEMS),
        "master": {"lufs_integrated_internal": round(info["lufs"], 2), "true_peak_dbtp_internal": round(info["tp"], 2),
                   "gain_db": round(info["gain_db"], 2), "max_limiting_db": round(info["max_gr_db"], 2)},
        "license": "CC0: muzică originală compusă în cod de echipa CyberPunks, fără sample-uri",
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_to(out: Path, verbose: bool = True, m4a: bool = True) -> dict:
    """Randează, masterizează și scrie mixajul, stem-urile și cues_120.json. Întoarce amprentele fișierelor."""
    stems, S = render_all(verbose)
    final, info = master(stems, verbose)
    final = {k: C.quantize24(v) for k, v in final.items()}
    mix = sum(final[k] for k in STEMS)  # multipli de 2^-23: suma e exactă
    assert mix.shape == (N, 2)
    (out / STEMS_DIR).mkdir(parents=True, exist_ok=True)
    C.write_wav24(out / WAV_NAME, mix)
    for k in STEMS:
        C.write_wav24(out / STEMS_DIR / f"{k}.wav", final[k])
    (out / "cues_120.json").write_text(json.dumps(cues_json(S, info), ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    files = [out / WAV_NAME, out / "cues_120.json"] + [out / STEMS_DIR / f"{k}.wav" for k in STEMS]
    if m4a and C.encode_m4a(out / WAV_NAME, out / M4A_NAME):
        files.append(out / M4A_NAME)
    return {str(p.relative_to(out)): sha256(p) for p in files}


# ======================================================================================
# 7. CLI
# ======================================================================================


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Randează muzica cinetică a filmului „Tura de mâine” (30 s, 120 BPM).")
    ap.add_argument("--out", type=Path, default=HERE / "out", help="dosarul de ieșire (implicit: music/out)")
    ap.add_argument("--no-m4a", action="store_true", help="fără previzualizarea AAC")
    ap.add_argument("--no-analyze", action="store_true", help="fără verificări și grafice")
    ap.add_argument("--no-determinism", action="store_true",
                    help="nu mai randa a doua oară (verificarea că două randări dau aceiași octeți)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    verbose = not args.quiet

    hashes = render_to(out, verbose, m4a=not args.no_m4a)
    if verbose:
        print(f"· scris în {out}")
    det = None
    if not args.no_determinism:
        if verbose:
            print("· a doua randare (determinism)")
        with tempfile.TemporaryDirectory() as tmp:
            again = render_to(Path(tmp), verbose=False, m4a=not args.no_m4a)
        same = {k: hashes[k] == again.get(k) for k in hashes}
        det = {"renders": 2, "identical": all(same.values()), "files": same,
               "sha256": {k: v for k, v in hashes.items()}}
        if verbose:
            print(f"· determinism: {'identic bit cu bit' if det['identical'] else 'DIFERIT'} ({len(same)} fișiere)")
    if not args.no_analyze:
        import analyze_kinetic

        analyze_kinetic.run(out, verbose=verbose, determinism=det)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
