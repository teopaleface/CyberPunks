#!/usr/bin/env python3
"""Muzica filmului „Tura de mâine”: 30,000 s, 96 BPM, 4/4, 12 măsuri a câte 2,5 s.

Totul e sintetizat aici, în cod: pian electric FM, pad aditiv filtrat, bas sub,
kick dintr-un sinus al cărui ton coboară, hi-hat și clap din zgomot filtrat,
plucks Karplus-Strong, reverb dintr-un răspuns la impuls sintetizat.
Nu folosim sample-uri, loop-uri sau soundfont-uri. Seed fix: același fișier la fiecare rulare.

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect. Licență CC0.

Rulare, din rădăcina repo-ului:
    uv run python presentation/music/compose.py
    uv run python presentation/music/compose.py --out /tmp/muzica --no-m4a --no-analyze
"""

from __future__ import annotations

# ruff: noqa: RUF046  # int(round(x)) rămâne: x poate fi un scalar NumPy folosit ca index
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")  # cel mult 4 nuclee

import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

# ======================================================================================
# 1. GRILA, ACORDURILE ȘI HARTA CUE-URILOR (date editabile)
# ======================================================================================

SR = 48_000
BPM = 96
BEATS_PER_BAR = 4
N_BARS = 12
FPS = 30
SEED = 20261107

BEAT = 60.0 / BPM  # 0,625 s
BAR = BEATS_PER_BAR * BEAT  # 2,5 s
STEP = BEAT / 4  # o șaisprezecime: 0,15625 s
DURATION = N_BARS * BAR  # 30,0 s
N = int(round(DURATION * SR))  # 1.440.000 de eșantioane

TARGET_LUFS = -16.0
CEILING_DBTP = -1.3  # cu o marjă față de -1,0 dBTP cerut
SILENT_FROM = 29.9  # de aici până la 30,0 s: zero digital

# Tonalitatea: re major. Primele 4 măsuri stau pe si minor (relativa, „noaptea”), fără terță în pad.
# Tonica (re) nu apare ca acord decât în măsura 12: sosirea zorilor.
# Vocile se mișcă puțin: B3 și A4 rămân în pian aproape tot timpul, B4 rămâne sus în pad.
CHORDS = {
    #  nume      pian electric (de jos în sus)              pad (de jos în sus)
    "Bsus": {"keys": [], "pad": ["B2", "F#3", "C#4", "E4"]},  # si fără terță (Bm11 fără terță)
    "F#sus": {"keys": [], "pad": ["B2", "F#3", "C#4", "E4"]},  # aceleași note, alt bas: F#7sus4
    "Gmaj9": {"keys": ["D3", "B3", "D4", "F#4", "A4"], "pad": ["D3", "A3", "F#4", "B4"]},  # IV
    "Asus": {"keys": ["E3", "B3", "D4", "E4", "A4"], "pad": ["E3", "A3", "E4", "B4"]},  # V sus4 (add9)
    "F#m11": {"keys": ["C#3", "B3", "C#4", "E4", "A4"], "pad": ["C#3", "A3", "E4", "B4"]},  # iii
    "A6": {"keys": ["E3", "C#4", "E4", "F#4", "A4"], "pad": ["E3", "A3", "F#4", "C#5"]},  # V6
    "Bm9": {"keys": ["B2", "D4", "F#4", "A4", "C#5"], "pad": ["B2", "F#3", "D4", "F#4", "C#5"]},  # vi
    "Dadd9": {"keys": ["D3", "A3", "D4", "E4", "F#4", "A4"], "pad": ["D3", "A3", "E4", "F#4", "D5"]},  # I
}

# Tobe: (pas de șaisprezecime 0-15, velocity). Kick-ul cade exact pe grilă.
HATS_8 = [(0, 0.34), (2, 0.60), (4, 0.38), (6, 0.64), (8, 0.34), (10, 0.60), (12, 0.38), (14, 0.68)]
SHAKER_16 = [(s, 0.30 if s % 4 == 2 else 0.20 if s % 2 == 0 else 0.14) for s in range(16)]
DRUM_PATTERNS = {
    "reveal": {"kick": [(0, 1.0), (8, 0.62)]},
    "groove": {"kick": [(0, 1.0), (8, 0.84)], "clap": [(4, 0.70), (12, 0.74)], "hat": HATS_8},
    "full": {
        "kick": [(0, 1.0), (8, 0.86), (14, 0.30)],
        "clap": [(4, 0.72), (12, 0.76)],
        "hat": HATS_8,
        "shaker": SHAKER_16,
    },
    "full_end": {
        "kick": [(0, 1.0), (8, 0.86)],
        "clap": [(4, 0.72), (12, 0.76)],
        "hat": HATS_8,
        "shaker": [(s, v) for s, v in SHAKER_16 if s < 14],
    },
    # Mai ușor; pe „și”-ul lui 4 (ultima optime) nu cântă nimic: o mică respirație înainte de final.
    "light": {
        "kick": [(0, 0.80), (8, 0.68)],
        "clap": [(4, 0.48), (12, 0.52)],
        "hat": [(s, round(v * 0.72, 3)) for s, v in HATS_8 if s != 14],
    },
}

# Harta cue-urilor. O măsură = 16 pași de șaisprezecime. Totul de aici se poate edita:
# - chords: (pas, acord) sau (pas, None) pentru pauză în pad;
# - pad: curbe pentru nivel (0-1) și filtru (Hz), puncte (timp în bătăi 0-4, valoare);
# - keys: (pas, lungime în pași, velocity[, note explicite]); acordul vine din chords;
# - bass / sub: (pas, lungime în pași, notă, velocity);
# - drums: un nume din DRUM_PATTERNS;
# - plucks: tipul sunetului și notele (pas, lungime, notă, velocity);
# - fx: swell care se termină fix pe următoarea linie de măsură.
# Accentele din cues.json se calculează din „section”, deci se mută odată cu secțiunile.
CUE_MAP = [
    {
        "bar": 1,
        "section": "contoare",
        "screen": "negru, apoi mii de puncte (contoare): „2 milioane de contoare”",
        "music": "pad cald care urcă din liniște; ping-uri rare, sus, ca niște date; fără tobe",
        "chords": [(0, "Bsus")],
        "pad": {"level": [(0.0, 0.0), (3.6, 0.9)], "cutoff": [(0.0, 420), (4.0, 1300)]},
        "plucks": {
            "kind": "ping",
            "notes": [(4, 2, "B5", 0.42), (9, 2, "F#5", 0.36), (12, 2, "E6", 0.32), (14, 1, "C#6", 0.30),
                      (15, 1, "A5", 0.30)],
        },
    },
    {
        "bar": 2,
        "section": "citiri",
        "screen": "„192 de milioane de citiri pe zi”",
        "music": "padul continuă; ping-urile devin un șir liniștit de șaisprezecimi (fluxul de date)",
        "chords": [(0, "Bsus")],
        "pad": {"level": [(4.0, 0.88)], "cutoff": [(4.0, 1700)]},
        # Ciclu de 5 note peste 16 pași: accentele de pe timpi cad pe note diferite (F#, E, C#, B).
        "plucks": {"kind": "shimmer", "cycle": ["F#5", "A5", "B5", "C#6", "E6"], "vel": (0.17, 0.31),
                   "accent": 0.06},
    },
    {
        "bar": 3,
        "section": "zoom",
        "screen": "zoom pe un singur punct, un „0,87” uriaș",
        "music": "sclipirea se oprește fix la 5,0 s; o notă sub (F#1) și o notă de pian electric (C#5): "
                 "tensiune, spațiu",
        "chords": [(0, "F#sus")],
        "pad": {"level": [(0.0, 0.88), (0.3, 0.58)], "cutoff": [(0.0, 1700), (0.3, 1150)]},
        "keys": [(0, 29, 0.44, ["C#5"])],
        "sub": [(0, 29, "F#1", 0.80)],
    },
    {
        "bar": 4,
        "section": "problema",
        "screen": "„...nu îi spune unui tehnician unde să meargă mâine”",
        "music": "totul ține, filtrul se închide încet; ultima jumătate de timp e o respirație, aproape liniște",
        "chords": [(0, "F#sus"), (14, None)],
        "pad": {"level": [(0.0, 0.58), (2.0, 0.46), (3.4, 0.0)], "cutoff": [(0.0, 1150), (3.5, 240)]},
        "fx": [{"kind": "swell", "notes": ["B4", "D5", "F#5", "A5"], "beats": 2.0, "peak_db": -42.0}],
    },
    {
        "bar": 5,
        "section": "reveal",
        "screen": "numele produsului: „Tura de mâine”",
        "music": "pe 10,0 s armonia se deschide (Gmaj9): primul acord plin, intră kick-ul moale și basul",
        "chords": [(0, "Gmaj9")],
        "pad_attack": 0.03,
        "pad": {"level": [(0.0, 0.0), (0.0, 1.0)], "cutoff": [(0.0, 380), (1.0, 2000), (4.0, 1900)]},
        "keys": [(0, 15, 0.58)],
        "bass": [(0, 15, "G1", 0.85)],
        "drums": "reveal",
    },
    {
        "bar": 6,
        "section": "semnale",
        "screen": "trei semnale, câte unul la 1,25 s (12,5 / 13,75 / 15,0): contoare, furtună, tensiune",
        "music": "groove: kick pe 1 și 3, clap moale pe 2 și 4, hi-hat în optimi, linie de bas",
        "chords": [(0, "Asus")],
        "pad": {"level": [(0.0, 0.85)], "cutoff": [(0.0, 1800)]},
        "keys": [(0, 5, 0.52), (6, 3, 0.38), (12, 2, 0.30)],
        "bass": [(0, 6, "A1", 0.85), (6, 2, "A2", 0.50), (8, 4, "A1", 0.72), (12, 4, "G1", 0.60)],
        "drums": "groove",
    },
    {
        "bar": 7,
        "section": "pasi",
        "screen": "al treilea semnal (tensiune) pe 15,0; harta agentului și Perceive pe 16,25",
        "music": "același groove; prima notă a motivului (A4) cade pe Perceive, la 16,25",
        "chords": [(0, "F#m11")],
        "pad": {"level": [(0.0, 0.85)], "cutoff": [(0.0, 1900)]},
        "keys": [(0, 5, 0.50), (6, 3, 0.36)],
        "bass": [(0, 6, "F#1", 0.85), (6, 2, "F#2", 0.50), (8, 6, "F#1", 0.72), (14, 2, "A1", 0.55)],
        "drums": "groove",
        "plucks": {"kind": "motif", "notes": [(8, 8, "A4", 0.62)]},
    },
    {
        "bar": 8,
        "section": "harta",
        "screen": "harta: Estimate pe 17,5, Decide pe 18,75 (bilanțul postului confirmă contorul)",
        "music": "groove complet; motivul continuă: B4 pe Estimate, C#5 pe Decide; partea cea mai caldă",
        "chords": [(0, "Gmaj9")],
        "pad": {"level": [(0.0, 0.95)], "cutoff": [(0.0, 2300)]},
        "keys": [(0, 5, 0.52), (6, 2, 0.36), (10, 2, 0.32), (12, 3, 0.36)],
        "bass": [(0, 6, "G1", 0.88), (6, 2, "G2", 0.52), (8, 4, "G1", 0.74), (12, 2, "D2", 0.55),
                 (14, 2, "B1", 0.58)],
        "drums": "full",
        "plucks": {"kind": "motif", "notes": [(0, 8, "B4", 0.63), (8, 8, "C#5", 0.66)]},
    },
    {
        "bar": 9,
        "section": "harta",
        "screen": "Act pe 20,0: traseele echipelor se desenează din bazele operative",
        "music": "groove complet; vârful motivului (E5) cade pe Act, apoi melodia rămâne suspendată pe F#5",
        "chords": [(0, "Asus"), (8, "A6")],
        "pad": {"level": [(0.0, 0.95)], "cutoff": [(0.0, 2400)]},
        "keys": [(0, 5, 0.51), (6, 2, 0.36), (8, 7, 0.46)],
        "bass": [(0, 6, "A1", 0.88), (6, 2, "A2", 0.52), (8, 6, "A1", 0.74), (14, 2, "E2", 0.52)],
        "drums": "full_end",
        "plucks": {"kind": "motif", "notes": [(0, 8, "E5", 0.70), (8, 3, "C#5", 0.50), (11, 1, "E5", 0.48),
                                              (12, 10, "F#5", 0.58)]},
    },
    {
        "bar": 10,
        "section": "pauza",
        "screen": "„Nu sunt sigur.” apoi „Un om decide.”",
        "music": "tobele și basul tac: pad plus un singur acord ținut de pian electric (Bm9), spațiu",
        "chords": [(0, "Bm9")],
        "pad": {"level": [(0.0, 1.0)], "cutoff": [(0.0, 1500), (3.0, 1500), (4.0, 1900)]},
        "keys": [(0, 15, 0.50)],
    },
    {
        "bar": 11,
        "section": "metrica",
        "screen": "metrica cheie față de baseline",
        "music": "tobele revin, mai ușor; motivul revine și urcă spre final",
        "chords": [(0, "Gmaj9"), (8, "A6")],
        "pad": {"level": [(0.0, 0.85), (4.0, 1.0)], "cutoff": [(0.0, 1700), (4.0, 2900)]},
        "keys": [(0, 5, 0.48), (6, 2, 0.34), (8, 6, 0.48)],
        "bass": [(0, 6, "G1", 0.82), (6, 2, "G2", 0.48), (8, 6, "A1", 0.76), (14, 2, "C#2", 0.50)],
        "drums": "light",
        "plucks": {"kind": "motif", "notes": [(0, 4, "A4", 0.55), (4, 4, "B4", 0.58), (8, 4, "C#5", 0.61),
                                              (12, 4, "E5", 0.64)]},
        "fx": [{"kind": "swell", "notes": ["A4", "E5", "F#5", "A5"], "beats": 2.0, "peak_db": -38.0}],
    },
    {
        "bar": 12,
        "section": "final",
        "screen": "cartonul final: „CyberPunks · SmartHack XI 2026”",
        "music": "acord major de rezolvare (D add9) fix pe 27,5 s; tobele tac; sună liber, cu reverb, "
                 "liniște totală de la 29,9 s",
        "chords": [(0, "Dadd9")],
        "pad": {"level": [(0.0, 1.0), (2.0, 0.55), (3.6, 0.0)], "cutoff": [(0.0, 2900), (4.0, 900)]},
        "keys": [(0, 14, 0.60)],
        "bass": [(0, 13, "D2", 0.72)],
        "sub": [(0, 12, "D1", 0.42)],
        "plucks": {"kind": "final", "notes": [(0, 14, "F#5", 0.66)]},
    },
]

# Nivelurile pe instrumente (dB) și trimiterile spre reverb.
MIX_DB = {"pad": -2.9, "keys": 5.7, "bass": -4.9, "sub": -10.0, "kick": -2.5, "clap": 7.0, "hat": 10.0,
          "shaker": 13.5, "plucks": 8.5, "fx": 0.0}
HALL_SEND = {"pad": 0.30, "keys": 0.22, "plucks": 0.36, "fx": 0.25}
ROOM_SEND = {"clap": 0.30, "hat": 0.10, "shaker": 0.12}

STEMS = ("pad", "keys", "bass", "drums", "plucks", "fx")


# ======================================================================================
# 2. UTILITARE
# ======================================================================================

_PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    """„F#5” -> 78 (C4 = 60)."""
    letter, rest = name[0], name[1:]
    acc = 0
    while rest and rest[0] in "#b":
        acc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + _PITCH[letter] + acc


def hz(m: float) -> float:
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def bar_start(bar: int) -> float:
    return (bar - 1) * BAR


def t_step(bar: int, step: float) -> float:
    return bar_start(bar) + step * STEP


def db(x: float) -> float:
    return 10.0 ** (x / 20.0)


def pan_gains(p: float) -> tuple[float, float]:
    """Panoramare cu putere constantă; în centru fiecare canal are câștig 1."""
    p = float(np.clip(p, -1.0, 1.0))
    return float(np.sqrt(1.0 - p)), float(np.sqrt(1.0 + p))


def sos(kind: str, freq, order: int = 2):
    return signal.butter(order, freq, kind, fs=SR, output="sos")


def add_at(buf: np.ndarray, x: np.ndarray, t0: float, gains=(1.0, 1.0)) -> None:
    """Adună sunetul x (mono sau stereo) în buf, începând de la t0 secunde."""
    i0 = int(round(t0 * SR))
    if i0 >= len(buf):
        return
    j0 = max(0, -i0)
    i0 = max(0, i0)
    n = min(len(x) - j0, len(buf) - i0)
    if n <= 0:
        return
    seg = x[j0:j0 + n]
    if seg.ndim == 1:
        buf[i0:i0 + n, 0] += seg * gains[0]
        buf[i0:i0 + n, 1] += seg * gains[1]
    else:
        buf[i0:i0 + n, 0] += seg[:, 0] * gains[0]
        buf[i0:i0 + n, 1] += seg[:, 1] * gains[1]


def curve(points, log: bool = False, default: float = 1.0) -> np.ndarray:
    """Curbă pe toată piesa din puncte (timp, valoare), cu treceri line (cosinus).
    Două puncte cu același timp fac un salt."""
    if not points:
        return np.full(N, default)
    pts = sorted(points, key=lambda p: p[0])
    tp = np.array([p[0] for p in pts], dtype=float)
    vp = np.array([p[1] for p in pts], dtype=float)
    if log:
        vp = np.log(vp)
    t = np.arange(N) / SR
    if len(tp) == 1:
        out = np.full(N, vp[0])
    else:
        i = np.clip(np.searchsorted(tp, t, side="right") - 1, 0, len(tp) - 2)
        span = tp[i + 1] - tp[i]
        frac = np.where(span > 0, (t - tp[i]) / np.where(span > 0, span, 1.0), 1.0)
        frac = np.clip(frac, 0.0, 1.0)
        w = 0.5 - 0.5 * np.cos(np.pi * frac)
        out = vp[i] + (vp[i + 1] - vp[i]) * w
    return np.exp(out) if log else out


def rng_for(*keys) -> np.random.Generator:
    """Generator determinist pentru fiecare parte, independent de ordinea randării."""
    return np.random.default_rng([SEED, *[abs(hash_str(k)) if isinstance(k, str) else int(k) for k in keys]])


def fade_tail(y: np.ndarray, ms: float = 25.0) -> np.ndarray:
    """Ultimele ms ale unui sunet scad lin la zero, ca bufferul să nu se termine brusc (fără clic)."""
    n = min(len(y), int(ms * 1e-3 * SR))
    if n > 1:
        w = 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, n))
        y[-n:] *= w if y.ndim == 1 else w[:, None]
    return y


def hash_str(s: str) -> int:
    h = 2166136261
    for ch in s.encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


# ======================================================================================
# 3. INSTRUMENTE (toate sintetizate)
# ======================================================================================


def ep_note(f0: float, vel: float, dur: float) -> np.ndarray:
    """Pian electric FM (stil Rhodes moale): purtătoare și modulator 1:1, indexul scade după atac.
    O a doua pereche, dezacordată cu 3 cenți, dă căldură; o componentă scurtă 1:3 dă atacul."""
    rel = 0.20
    n = int((dur + 6 * rel) * SR)
    t = np.arange(n) / SR
    tau = 0.45 + 1.5 * (220.0 / f0) ** 0.45  # notele joase țin mai mult
    amp = np.exp(-t / tau) * (1.0 - np.exp(-t / 0.0012))
    off = t > dur
    amp[off] *= np.exp(-(t[off] - dur) / rel)
    index = vel * (3.0 * np.exp(-t / 0.10) + 0.9 * np.exp(-t / 0.7) + 0.35)  # atac luminos, apoi moale
    w = 2 * np.pi * f0 * t
    body = np.sin(w + index * np.sin(w))
    w2 = w * 2 ** (3.0 / 1200)
    body2 = np.sin(w2 + 0.55 * index * np.sin(w2))
    bark = np.sin(w + 1.1 * vel * np.sin(3 * w)) * np.exp(-t / 0.025)
    tine = np.sin(w + 1.6 * vel * np.exp(-t / 0.02) * np.sin(7 * w)) * np.exp(-t / 0.035)  # „ding”-ul lamei
    hit = 0.15 * vel * bark + 0.30 * vel * tine
    left = (0.62 * body + 0.38 * body2 + hit) * amp
    right = (0.38 * body + 0.62 * body2 + hit) * amp
    return fade_tail(np.stack([left, right], axis=1) * vel ** 1.4)


def bass_note(f0: float, vel: float, dur: float, sub: bool = False) -> np.ndarray:
    """Bas: sinus plus armonicele 2 și 3 (ca să se audă și pe difuzoare mici). Mono."""
    rel = 0.25 if sub else 0.07
    att = 0.035 if sub else 0.006
    n = int((dur + 7 * rel) * SR)
    t = np.arange(n) / SR
    if sub:
        body = 1.0 - 0.35 * (1.0 - np.exp(-t / 2.5))
        a2, a3 = 0.30, 0.08
    else:
        body = 0.80 + 0.20 * np.exp(-t / 0.30)
        a2 = 0.30 + 0.20 * np.exp(-t / 0.10)
        a3 = 0.07 + 0.10 * np.exp(-t / 0.06)
    env = (1.0 - np.exp(-t / att)) * body
    off = t > dur
    env[off] *= np.exp(-(t[off] - dur) / rel)
    ph = 2 * np.pi * f0 * t
    return fade_tail((np.sin(ph) + a2 * np.sin(2 * ph) + a3 * np.sin(3 * ph)) * env * vel)


def kick(vel: float) -> np.ndarray:
    """Kick moale: un sinus care coboară de la ~147 Hz la 49 Hz."""
    n = int(1.1 * SR)  # destul de lung ca să se stingă singur (la 1,1 s e la -48 dB)
    t = np.arange(n) / SR
    f = 49.0 + 68.0 * np.exp(-t / 0.032) + 30.0 * np.exp(-t / 0.004)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1.0 - np.exp(-t / 0.0007)) * (0.85 * np.exp(-t / 0.20) + 0.15 * np.exp(-t / 0.04))
    y = np.tanh(2.0 * np.sin(ph) * env) / np.tanh(2.0)  # saturație moale: corp mai plin la același vârf
    return fade_tail(y * vel, 80.0)


_SOS_CLAP_BP = sos("bandpass", (800, 2000), 2)
_SOS_CLAP_LP = sos("lowpass", 3200, 2)


def clap(vel: float, rng: np.random.Generator) -> np.ndarray:
    """Clap moale (trei impulsuri de zgomot în jur de 1,2 kHz) plus un „tok” de lemn, ca un rim."""
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    env = np.zeros(n)
    for d, a in ((0.0, 1.0), (0.0085, 0.8), (0.017, 0.65)):
        m = t >= d
        env[m] += a * np.exp(-(t[m] - d) / 0.0035) * (1.0 - np.exp(-(t[m] - d) / 0.0003))
    m = t >= 0.022
    env[m] += 0.55 * np.exp(-(t[m] - 0.022) / 0.06)
    y = signal.sosfilt(_SOS_CLAP_LP, signal.sosfilt(_SOS_CLAP_BP, noise) * env)
    y /= np.max(np.abs(y)) + 1e-12
    wood = (np.sin(2 * np.pi * 410 * t) * np.exp(-t / 0.022)
            + 0.45 * np.sin(2 * np.pi * 1130 * t) * np.exp(-t / 0.012)) * (1.0 - np.exp(-t / 0.0005))
    return fade_tail((0.75 * y + 0.30 * wood) * vel, 40.0)


_SOS_HAT_HP = sos("highpass", 7500, 2)
_SOS_HAT_LP = sos("lowpass", 13500, 2)
_SOS_SHAKER_HP = sos("highpass", 6500, 2)


def hat(vel: float, rng: np.random.Generator, decay: float = 0.032) -> np.ndarray:
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    y = signal.sosfilt(_SOS_HAT_LP, signal.sosfilt(_SOS_HAT_HP, rng.standard_normal(n)))
    env = (1.0 - np.exp(-t / 0.0004)) * np.exp(-t / decay)
    return fade_tail(y * env * vel / 3.0)


def shaker(vel: float, rng: np.random.Generator) -> np.ndarray:
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    y = signal.sosfilt(_SOS_HAT_LP, signal.sosfilt(_SOS_SHAKER_HP, rng.standard_normal(n)))
    env = (1.0 - np.exp(-t / 0.006)) * np.exp(-t / 0.045)
    return fade_tail(y * env * vel / 3.0)


_SOS_PLUCK_HP = sos("highpass", 90, 1)
_SOS_PLUCK_LP = sos("lowpass", 4500, 2)


def ks_pluck(f0: float, vel: float, length: float, t60: float, bright: float, rng: np.random.Generator,
             damp_at: float | None = None, damp_tau: float = 0.12) -> np.ndarray:
    """Coardă Karplus-Strong: un puls scurt (plus puțin zgomot) într-o buclă de întârziere cu filtru.
    Întârzierea fracționară (Lagrange, 4 coeficienți) ține acordajul exact la 48 kHz.
    Calculul merge pe blocuri mai scurte decât bucla, deci e vectorizat."""
    period = SR / f0
    total = period - 0.5  # media pe 2 eșantioane adaugă 0,5 eșantioane de întârziere
    d_int = int(np.floor(total)) - 1
    delta = total - d_int  # între 1 și 2: zona cea mai precisă a interpolatorului
    lag = np.ones(4)
    for k in range(4):
        for m in range(4):
            if m != k:
                lag[k] *= (delta - m) / (k - m)
    h = np.convolve([0.5, 0.5], lag)
    w0 = 2 * np.pi * f0 / SR
    mag = abs(np.sum(h * np.exp(-1j * w0 * np.arange(len(h)))))
    g = min(10.0 ** (-3.0 / (t60 * f0)) / mag, 0.9995)
    hg = h * g

    n = int(length * SR)
    pad = d_int + len(h) + 2
    y = np.zeros(n + pad)
    x = np.zeros(n + pad)
    burst_len = int(round(period))
    # Excitația: un puls „de deget” (fereastră Hann) plus puțin zgomot. Pulsul dă o cădere netedă și
    # previzibilă a armonicelor (fără vârfuri întâmplătoare de la o notă la alta); lățimea lui = luminozitatea.
    width = max(4, int(round(period * (0.32 - 0.35 * bright))))
    pulse = np.zeros(burst_len)
    pulse[:min(width, burst_len)] = np.hanning(width + 2)[1:-1][:burst_len]
    noise = rng.standard_normal(burst_len)
    a = 0.15 + 0.8 * (1.0 - bright)
    noise = signal.lfilter([1 - a], [1, -a], noise)
    noise = signal.lfilter([1 - a], [1, -a], noise[::-1])[::-1]
    ex = pulse / (np.max(pulse) + 1e-12) + 0.25 * noise / (np.max(np.abs(noise)) + 1e-12)
    ex -= ex.mean()
    ex /= np.max(np.abs(ex)) + 1e-12
    x[pad:pad + burst_len] = ex
    block = d_int
    for s in range(pad, n + pad, block):
        e = min(s + block, n + pad)
        acc = x[s:e].copy()
        for k in range(len(hg)):
            o = d_int + k
            acc += hg[k] * y[s - o:e - o]
        y[s:e] = acc
    out = y[pad:]
    out = signal.sosfilt(_SOS_PLUCK_LP, signal.sosfilt(_SOS_PLUCK_HP, out))
    t = np.arange(n) / SR
    out *= 1.0 - np.exp(-t / 0.005)  # atac moale (5 ms): tot ciupit, dar fără vârf ascuțit
    if damp_at is not None:
        m = t > damp_at
        out[m] *= np.exp(-(t[m] - damp_at) / damp_tau)
    ref = np.sqrt(np.mean(out[: int(0.04 * SR)] ** 2)) + 1e-12
    return fade_tail(out * (vel / (3.0 * ref)), 40.0)


def glass(f0: float, vel: float, t60: float, length: float) -> np.ndarray:
    """Clopoțel moale (aproape sinus), pentru dublura la octavă a motivului."""
    n = int(length * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f0 * t) + 0.05 * np.sin(2 * np.pi * 2.0 * f0 * t)
         + 0.04 * np.sin(2 * np.pi * 3.01 * f0 * t))
    return fade_tail(y * np.exp(-6.9078 * t / t60) * (1.0 - np.exp(-t / 0.002)) * vel, 40.0)


_SOS_AIR = sos("bandpass", (4500, 11000), 2)


def swell(notes: list[str], length: float, rng: np.random.Generator) -> np.ndarray:
    """Un val foarte discret (ton + aer) care crește exponențial și se taie fix la final."""
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for i, name in enumerate(notes):
        f = hz(midi(name))
        for c, cents in enumerate((-5.0, 5.0)):
            ph = rng.uniform(0, 2 * np.pi)
            out[:, c] += np.sin(2 * np.pi * f * 2 ** (cents / 1200) * t + ph) / (1 + 0.3 * i)
    out /= np.max(np.abs(out)) + 1e-12
    air = np.stack([signal.sosfilt(_SOS_AIR, rng.standard_normal(n)) for _ in range(2)], axis=1)
    air /= np.max(np.abs(air)) + 1e-12
    x = t / length
    env = (np.exp(4.5 * x) - 1.0) / (np.exp(4.5) - 1.0)
    tail = int(0.003 * SR)
    env[-tail:] *= np.linspace(1.0, 0.0, tail)
    return (out + 0.30 * air) * env[:, None]


def make_ir(length: float, rt60: tuple[float, float, float], predelay: float, seed: int,
            early: bool = True) -> np.ndarray:
    """Răspuns la impuls sintetizat: zgomot în 3 benzi, fiecare cu altă durată a cozii
    (acutele mor mai repede), plus câteva reflexii timpurii. Stereo decorelat."""
    n = int(length * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    bands = (sos("lowpass", 350, 4), sos("bandpass", (350, 3000), 2), sos("highpass", 3000, 4))
    ir = np.zeros((n, 2))
    for ch in range(2):
        acc = np.zeros(n)
        for band, rt in zip(bands, rt60):
            acc += signal.sosfilt(band, rng.standard_normal(n)) * np.exp(-6.9078 * t / rt)
        ir[:, ch] = acc * (1.0 - np.exp(-t / 0.018))
    ir /= np.sqrt(np.sum(ir**2, axis=0, keepdims=True))
    if early:
        taps = [(0.0071, 0.42, 0), (0.0113, 0.36, 1), (0.0167, 0.30, 0), (0.0211, 0.27, 1),
                (0.0293, 0.22, 0), (0.0347, 0.20, 1), (0.0419, 0.16, 0), (0.0487, 0.14, 1)]
        for d, gain, ch in taps:
            i = int(d * SR)
            ir[i:i + 3, ch] += 0.12 * gain * np.array([0.5, 1.0, 0.5])
    pd = int(predelay * SR)
    ir = np.vstack([np.zeros((pd, 2)), ir])[:n]
    ir /= np.sqrt(np.sum(ir**2, axis=0, keepdims=True))
    return ir


_SOS_REV_HP = sos("highpass", 250, 2)
_SOS_REV_LP = sos("lowpass", 6500, 2)


def reverb(x: np.ndarray, ir: np.ndarray, send: float) -> np.ndarray:
    if send <= 0:
        return np.zeros_like(x)
    mono = 0.5 * (x[:, 0] + x[:, 1]) * send
    mono = signal.sosfilt(_SOS_REV_LP, signal.sosfilt(_SOS_REV_HP, mono))
    wet_l = signal.fftconvolve(mono, ir[:, 0])[:N]
    wet_r = signal.fftconvolve(mono, ir[:, 1])[:N]
    return np.stack([wet_l, wet_r], axis=1)


_SOS_DELAY_LP = sos("lowpass", 3800, 1)


def pingpong(x: np.ndarray, delay: float, feedback: float, repeats: int, wet: float) -> np.ndarray:
    """Delay stânga-dreapta discret, fiecare ecou puțin mai întunecat."""
    mono = 0.5 * (x[:, 0] + x[:, 1])
    d = int(round(delay * SR))
    out = np.zeros_like(x)
    sig = mono
    for i in range(1, repeats + 1):
        sig = signal.sosfilt(_SOS_DELAY_LP, sig)
        if i * d >= N:
            break
        out[i * d:, (i - 1) % 2] += wet * feedback ** (i - 1) * sig[: N - i * d]
    return out


def duck_curve(kicks: list[tuple[float, float]], depth: float) -> np.ndarray:
    """Sidechain ușor, calculat din momentele kick-ului (nu din audio)."""
    env = np.zeros(N)
    ln = int(0.6 * SR)
    tt = np.arange(ln) / SR
    shape = (1.0 - np.exp(-tt / 0.004)) * np.exp(-tt / 0.12)
    shape /= shape.max()
    for t0, v in kicks:
        i0 = int(round(t0 * SR))
        i1 = min(N, i0 + ln)
        env[i0:i1] = np.maximum(env[i0:i1], v * shape[: i1 - i0])
    return 1.0 - depth * env


# ======================================================================================
# 4. PARTITURA: din harta cue-urilor în evenimente
# ======================================================================================


def chord_timeline() -> list[tuple[float, float, str | None, dict]]:
    segs = []
    for cue in CUE_MAP:
        for step, name in cue.get("chords", []):
            segs.append((t_step(cue["bar"], step), name, cue, step))
    segs.sort(key=lambda s: s[0])
    out = []
    for i, (t0, name, cue, step) in enumerate(segs):
        t1 = segs[i + 1][0] if i + 1 < len(segs) else DURATION
        out.append((t0, t1, name, {"cue": cue, "step": step}))
    return out


def chord_at(timeline, t: float) -> str | None:
    name = None
    for t0, t1, nm, _ in timeline:
        if t0 <= t + 1e-9:
            name = nm
    return name


def build_score() -> dict:
    timeline = chord_timeline()
    score = {k: [] for k in ("keys", "bass", "sub", "kick", "clap", "hat", "shaker", "plucks", "fx")}
    hum = rng_for("humanize")
    for cue in CUE_MAP:
        b = cue["bar"]
        # pian electric
        for item in cue.get("keys", []):
            step, length, vel = item[:3]
            t0 = t_step(b, step)
            names = item[3] if len(item) > 3 else CHORDS[chord_at(timeline, t0)]["keys"]
            notes = sorted(midi(nm) for nm in names)
            on_bar = step == 0
            shift = 0.0 if on_bar else float(np.clip(hum.normal(0, 0.003), -0.006, 0.006))
            roll = 0.0025 if on_bar else 0.004  # acordul e rulat ușor, de jos în sus
            for i, m in enumerate(notes):
                v = vel * float(np.clip(1 + hum.normal(0, 0.04), 0.9, 1.1)) * (0.85 if m < 55 else 1.0)
                score["keys"].append({"t": t0 + shift + i * roll, "m": m, "vel": v, "dur": length * STEP - 0.03})
        # bas și sub
        for step, length, name, vel in cue.get("bass", []):
            shift = 0.0 if step in (0, 8) else float(np.clip(hum.normal(0, 0.002), -0.004, 0.004))
            score["bass"].append({"t": t_step(b, step) + shift, "m": midi(name), "vel": vel,
                                      "dur": length * STEP - 0.025})
        for step, length, name, vel in cue.get("sub", []):
            score["sub"].append({"t": t_step(b, step), "m": midi(name), "vel": vel, "dur": length * STEP})
        # tobe
        pat = DRUM_PATTERNS.get(cue.get("drums") or "", {})
        for step, vel in pat.get("kick", []):
            score["kick"].append({"t": t_step(b, step), "vel": vel})
        for step, vel in pat.get("clap", []):
            score["clap"].append({"t": t_step(b, step) + float(np.clip(hum.normal(0, 0.0015), -0.003, 0.003)),
                                      "vel": vel})
        for step, vel in pat.get("hat", []):
            score["hat"].append({"t": t_step(b, step) + float(np.clip(hum.normal(0, 0.0025), -0.005, 0.005)),
                                     "vel": vel * float(np.clip(1 + hum.normal(0, 0.08), 0.8, 1.2))})
        for step, vel in pat.get("shaker", []):
            swing = 0.03 * 2 * STEP if step % 2 else 0.0  # swing de 53% pe șaisprezecimi
            score["shaker"].append({"t": t_step(b, step) + swing + float(np.clip(hum.normal(0, 0.002), -0.004,
                                                                                   0.004)),
                                        "vel": vel * float(np.clip(1 + hum.normal(0, 0.08), 0.8, 1.2))})
        # plucks
        pl = cue.get("plucks")
        if pl:
            kind = pl["kind"]
            if kind == "shimmer":
                lo, hi = pl["vel"]
                cyc = pl["cycle"]
                for step in range(16):
                    v = lo + (hi - lo) * step / 15 + (pl["accent"] if step % 4 == 0 else 0.0)
                    score["plucks"].append({"t": t_step(b, step), "m": midi(cyc[step % len(cyc)]), "vel": v,
                                                "dur": STEP, "kind": kind, "idx": step})
            else:
                for j, (step, length, name, vel) in enumerate(pl["notes"]):
                    exact = kind in ("motif", "final", "ping") or step % 4 == 0
                    shift = 0.0 if exact else float(np.clip(hum.normal(0, 0.003), -0.005, 0.005))
                    score["plucks"].append({"t": t_step(b, step) + shift, "m": midi(name), "vel": vel,
                                                "dur": length * STEP, "kind": kind, "idx": j})
        # fx
        for fx in cue.get("fx", []):
            end = bar_start(b) + BAR
            score["fx"].append({"kind": fx["kind"], "t": end - fx["beats"] * BEAT, "end": end, "notes": fx["notes"],
                                    "peak_db": fx["peak_db"], "bar": b})
    score["timeline"] = timeline
    return score


# ======================================================================================
# 5. RANDARE PE INSTRUMENTE
# ======================================================================================


def pad_events(timeline) -> list[dict]:
    """Notele padului. O notă comună cu acordul următor nu se reia: ține mai departe (legato)."""
    events = []
    active: dict[int, tuple[float, float]] = {}
    for t0, _t1, name, meta in timeline:
        cue, step = meta["cue"], meta["step"]
        notes = set() if name is None else {midi(nm) for nm in CHORDS[name]["pad"]}
        reattack = step == 0 and "pad_attack" in cue
        attack = cue.get("pad_attack", 0.20)
        for m in list(active):
            if m not in notes or reattack:
                start, att = active.pop(m)
                events.append({"m": m, "t0": start, "t1": t0, "att": att, "rel": 0.06 if name is None else 0.45})
        for m in notes:
            if m not in active:
                first = t0 < 1e-9
                active[m] = (t0, 0.01 if first else attack)
    for m, (start, att) in active.items():
        events.append({"m": m, "t0": start, "t1": DURATION, "att": att, "rel": 0.45})
    return events


def render_pad(score: dict) -> np.ndarray:
    lvl_pts, cut_pts = [], []
    for cue in CUE_MAP:
        p = cue.get("pad", {})
        b0 = bar_start(cue["bar"])
        lvl_pts += [(b0 + beat * BEAT, v) for beat, v in p.get("level", [])]
        cut_pts += [(b0 + beat * BEAT, v) for beat, v in p.get("cutoff", [])]
    level = curve(lvl_pts, default=1.0)
    cutoff = curve(cut_pts, log=True, default=1500.0)
    t_all = np.arange(N) / SR
    cutoff *= 1.0 + 0.07 * np.sin(2 * np.pi * 0.11 * t_all)  # mișcare lentă, abia simțită
    out = np.zeros((N, 2))
    rng = rng_for("pad")
    voices = ((-7.0, -0.85), (0.0, 0.0), (7.0, 0.85))  # cenți, panoramare
    for ev in pad_events(score["timeline"]):
        f0 = hz(ev["m"])
        i0 = int(round(ev["t0"] * SR))
        i_off = int(round(ev["t1"] * SR))
        i1 = min(N, i_off + int(ev["rel"] * 7 * SR))
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        dur = (i_off - i0) / SR
        env = 1.0 - np.exp(-tt / ev["att"])
        off = tt > dur
        env[off] *= np.exp(-(tt[off] - dur) / ev["rel"])
        inv_fc = 1.0 / cutoff[i0:i1]
        k_max = max(1, int(5000.0 / f0))
        sig_l = np.zeros(i1 - i0)
        sig_r = np.zeros(i1 - i0)
        for k in range(1, k_max + 1):
            x = (k * f0 * inv_fc) ** 2
            gk = (k ** -1.5) / np.sqrt(1.0 + x * x)  # filtru trece-jos de 12 dB/octavă, pe armonică
            for cents, p in voices:
                ph = rng.uniform(0, 2 * np.pi)
                s = np.sin(2 * np.pi * k * f0 * 2 ** (cents / 1200) * tt + ph) * gk
                gl, gr = pan_gains(p)
                sig_l += s * gl
                sig_r += s * gr
        out[i0:i1, 0] += sig_l * env
        out[i0:i1, 1] += sig_r * env
    out *= level[:, None]
    return out * 0.030


def render_keys(score: dict, gain_db: float = 0.0) -> np.ndarray:
    out = np.zeros((N, 2))
    for ev in score["keys"]:
        y = ep_note(hz(ev["m"]), ev["vel"], ev["dur"])
        add_at(out, y, ev["t"], pan_gains((ev["m"] - 62) / 40.0))
    t = np.arange(N) / SR
    trem = 0.06 * np.sin(2 * np.pi * (BPM / 60.0 * 3.0) * t)  # tremolo stereo discret, în triolete de optimi
    out[:, 0] *= 1.0 + trem
    out[:, 1] *= 1.0 - trem
    out = signal.sosfilt(sos("highpass", 90, 2), out, axis=0)
    out = signal.sosfilt(sos("lowpass", 4800, 2), out, axis=0)
    out = np.tanh(1.5 * out * 0.11 * db(gain_db)) / 1.5  # puțină saturație caldă
    return out


def render_bass(score: dict) -> tuple[np.ndarray, np.ndarray]:
    bass = np.zeros((N, 2))
    sub = np.zeros((N, 2))
    for ev in score["bass"]:
        add_at(bass, bass_note(hz(ev["m"]), ev["vel"], ev["dur"]), ev["t"])
    for ev in score["sub"]:
        add_at(sub, bass_note(hz(ev["m"]), ev["vel"], ev["dur"], sub=True), ev["t"])
    lp = sos("lowpass", 420, 2)
    bass = signal.sosfilt(lp, bass, axis=0) * 0.30
    sub = signal.sosfilt(lp, sub, axis=0) * 0.30
    return bass, sub


def render_drums(score: dict) -> dict[str, np.ndarray]:
    parts = {k: np.zeros((N, 2)) for k in ("kick", "clap", "hat", "shaker")}
    for ev in score["kick"]:
        add_at(parts["kick"], kick(ev["vel"]), ev["t"])
    for i, ev in enumerate(score["clap"]):
        add_at(parts["clap"], clap(ev["vel"], rng_for("clap", i)), ev["t"], pan_gains(-0.08))
    for i, ev in enumerate(score["hat"]):
        add_at(parts["hat"], hat(ev["vel"], rng_for("hat", i)), ev["t"], pan_gains(0.22))
    for i, ev in enumerate(score["shaker"]):
        add_at(parts["shaker"], shaker(ev["vel"], rng_for("shaker", i)), ev["t"], pan_gains(-0.30))
    parts["kick"] *= 0.42
    parts["clap"] *= 0.10
    parts["hat"] *= 0.055
    parts["shaker"] *= 0.045
    return parts


PLUCK_STYLE = {
    #  kind:      t60 (s), luminozitate, dublura glass (dB sau None), delay
    "ping": {"t60": 0.9, "bright": 0.35, "glass": None, "delay": 0.0},
    "shimmer": {"t60": 0.32, "bright": 0.30, "glass": None, "delay": 0.0},
    "motif": {"t60": 1.8, "bright": 0.38, "glass": -14.0, "delay": 0.16},
    "counter": {"t60": 1.5, "bright": 0.34, "glass": -18.0, "delay": 0.18},
    "final": {"t60": 2.8, "bright": 0.36, "glass": -10.0, "delay": 0.10},
}


def render_plucks(score: dict) -> tuple[np.ndarray, np.ndarray]:
    dry = np.zeros((N, 2))
    to_delay = np.zeros((N, 2))
    golden = 0.6180339887
    for j, ev in enumerate(score["plucks"]):
        st = PLUCK_STYLE[ev["kind"]]
        f0 = hz(ev["m"])
        if ev["kind"] == "shimmer":
            p = 0.45 if ev["idx"] % 2 else -0.45
            length, damp = 0.6, None
        elif ev["kind"] == "ping":
            p = ((j * golden) % 1.0) * 1.3 - 0.65
            length, damp = 1.6, None
        elif ev["kind"] == "final":
            p, length, damp = 0.05, 2.5, None
        else:
            p = 0.15 if ev["kind"] == "counter" else (-0.12 if ev["idx"] % 2 else 0.12)
            length = ev["dur"] + 1.2
            damp = ev["dur"] + 0.05
        y = ks_pluck(f0, ev["vel"], length, st["t60"], st["bright"], rng_for("pluck", j), damp_at=damp,
                     damp_tau=0.22 if ev["kind"] == "motif" else 0.15)
        if st["glass"] is not None:
            gl = glass(2 * f0, ev["vel"] * db(st["glass"]) * 1.2, st["t60"] * 0.7, length)
            y = y + gl[: len(y)]
        g = pan_gains(p)
        add_at(dry, y, ev["t"], g)
        if st["delay"] > 0:
            add_at(to_delay, y * st["delay"], ev["t"], g)
    echoes = pingpong(to_delay, delay=3 * STEP, feedback=0.30, repeats=5, wet=1.0)
    return dry * 0.12, echoes * 0.12


def render_fx(score: dict) -> np.ndarray:
    out = np.zeros((N, 2))
    for i, ev in enumerate(score["fx"]):
        if ev["kind"] == "swell":
            y = swell(ev["notes"], ev["end"] - ev["t"], rng_for("swell", i))
            add_at(out, y * db(ev["peak_db"]), ev["t"])
    return out


# ======================================================================================
# 6. MIXAJ, MASTER, VERIFICĂRI DE BAZĂ
# ======================================================================================

_K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
_K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def lufs_integrated(x: np.ndarray) -> float:
    """Loudness integrată după ITU-R BS.1770-4 (filtru K, blocuri de 400 ms, porți -70 și -10)."""
    y = signal.lfilter(*_K1, x, axis=0)
    y = signal.lfilter(*_K2, y, axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.vstack([np.zeros((1, y.shape[1])), np.cumsum(y**2, axis=0)])
    starts = np.arange(0, len(y) - blk + 1, hop)
    ms = ((c[starts + blk] - c[starts]) / blk).sum(axis=1)
    lk = -0.691 + 10 * np.log10(ms + 1e-20)
    g1 = ms[lk > -70]
    if len(g1) == 0:
        return -np.inf
    rel = -0.691 + 10 * np.log10(g1.mean()) - 10
    g2 = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def true_peak_db(x: np.ndarray) -> float:
    up = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(up)) + 1e-20))


def limiter_gain(mix: np.ndarray, ceiling_db: float, lookahead_ms: float = 3.0,
                 release_ms: float = 60.0) -> np.ndarray:
    """Limitator de vârf real: calculează doar un câștig în timp, aplicat identic pe toate stem-urile,
    ca suma stem-urilor să rămână exact mixajul."""
    up = signal.resample_poly(mix, 4, 1, axis=0)
    pk = np.max(np.abs(up), axis=1)[: 4 * len(mix)].reshape(len(mix), 4).max(axis=1)
    req = np.minimum(1.0, db(ceiling_db) / np.maximum(pk, 1e-12))
    if req.min() >= 1.0:
        return np.ones(len(mix))
    L = int(lookahead_ms * 1e-3 * SR)
    m = ndimage.minimum_filter1d(req, size=2 * L + 1, mode="nearest")
    s = ndimage.uniform_filter1d(m, size=2 * L + 1, mode="nearest")
    rel = float(np.exp(-1.0 / (release_ms * 1e-3 * SR)))
    g = np.empty(len(s))
    cur = 1.0
    for i, v in enumerate(s.tolist()):
        cur = v if v < cur else v + (cur - v) * rel
        g[i] = cur
    return np.minimum(g, req)


def breath_env(reopen: bool = True) -> np.ndarray:
    """Respirația dinaintea lui „reveal”: totul (în afară de swell) tace de la jumătatea ultimului timp.
    reopen=False: rămâne închis (pentru partea de dinainte de reveal, cu tot cu coada ei de reverb)."""
    reveal = section_time("reveal")
    silence = reveal - BEAT / 2
    pts = [(0.0, 1.0), (silence - 0.24, 1.0), (silence, 0.0), (reveal, 0.0)]
    return curve(pts + ([(reveal, 1.0)] if reopen else [(DURATION, 0.0)]), default=1.0)


def end_env() -> np.ndarray:
    return curve([(0.0, 1.0), (28.9, 1.0), (SILENT_FROM - 0.04, 0.0), (DURATION, 0.0)], default=1.0)


def gate_plucks() -> np.ndarray:
    """Sclipirea se oprește fix la începutul zoom-ului (5,0 s), cu tot cu ecoul ei."""
    stop = section_time("zoom")
    nxt = min(e["t"] for e in SCORE_CACHE["plucks"] if e["t"] > stop) - 0.01
    return curve([(0.0, 1.0), (stop - 0.006, 1.0), (stop, 0.0), (nxt, 0.0), (nxt, 1.0)], default=1.0)


def mono_below(x: np.ndarray, fc: float = 120.0) -> np.ndarray:
    mid = 0.5 * (x[:, 0] + x[:, 1])
    side = 0.5 * (x[:, 0] - x[:, 1])
    side = signal.sosfilt(sos("highpass", fc, 2), side)
    return np.stack([mid + side, mid - side], axis=1)


def section_time(name: str) -> float:
    for cue in CUE_MAP:
        if cue["section"] == name:
            return bar_start(cue["bar"])
    raise KeyError(name)


SCORE_CACHE: dict = {}


def render_all(verbose: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    score = build_score()
    SCORE_CACHE.clear()
    SCORE_CACHE.update(score)
    say = print if verbose else (lambda *a, **k: None)

    say("· pad");      pad = render_pad(score) * db(MIX_DB["pad"])
    say("· keys");     keys = render_keys(score, MIX_DB["keys"])
    say("· bas");      bass, sub = render_bass(score)
    say("· tobe");     drums = render_drums(score)
    say("· plucks");   plucks_dry, plucks_echo = render_plucks(score)
    say("· fx");       fx = render_fx(score) * db(MIX_DB["fx"])

    # sidechain ușor de la kick
    kicks = [(e["t"], e["vel"]) for e in score["kick"]]
    pad *= duck_curve(kicks, 0.22)[:, None]
    keys *= duck_curve(kicks, 0.08)[:, None]
    bass *= duck_curve(kicks, 0.45)[:, None]
    bass *= db(MIX_DB["bass"])
    sub *= db(MIX_DB["sub"])
    for k in drums:
        drums[k] *= db(MIX_DB[k])
    plucks_dry *= db(MIX_DB["plucks"])
    plucks_echo *= db(MIX_DB["plucks"])

    say("· reverb")
    hall = make_ir(3.0, (2.3, 2.0, 1.1), 0.022, SEED + 11)
    room = make_ir(0.9, (0.55, 0.45, 0.28), 0.006, SEED + 12, early=False)
    hall_duck = duck_curve(kicks, 0.12)[:, None]
    # Ce sună înainte de reveal (uscat + reverb) se stinge în respirație și nu mai revine.
    # Ce începe la reveal are reverb-ul lui. Reverb-ul e liniar, deci împărțirea e exactă.
    cut = int(round(section_time("reveal") * SR))
    closed = breath_env(reopen=False)[:, None]

    def with_reverb(x: np.ndarray, ir: np.ndarray, send: float, duck: np.ndarray | float = 1.0) -> np.ndarray:
        pre, post = x.copy(), x.copy()
        pre[cut:] = 0.0
        post[:cut] = 0.0
        return (pre + reverb(pre, ir, send) * duck) * closed + post + reverb(post, ir, send) * duck

    stems = {
        "pad": with_reverb(pad, hall, HALL_SEND["pad"], hall_duck),
        "keys": with_reverb(keys, hall, HALL_SEND["keys"], hall_duck),
        "bass": with_reverb(bass + sub, hall, 0.0),
        "drums": drums["kick"] + drums["clap"] + drums["hat"] + drums["shaker"]
        + reverb(drums["clap"], room, ROOM_SEND["clap"])
        + reverb(drums["hat"], room, ROOM_SEND["hat"])
        + reverb(drums["shaker"], room, ROOM_SEND["shaker"]),
        "plucks": plucks_dry + plucks_echo + reverb(plucks_dry + plucks_echo, hall, HALL_SEND["plucks"]),
        "fx": fx + reverb(fx, hall, HALL_SEND["fx"]),
    }
    stems["plucks"] *= gate_plucks()[:, None]

    # Master liniar și cauzal (fără pre-ecou), aplicat identic pe fiecare stem: suma rămâne mixajul.
    hp = sos("highpass", 25, 2)
    br, en = breath_env(), end_env()
    for name in STEMS:
        x = mono_below(stems[name])
        x = signal.sosfilt(hp, x, axis=0)
        if name != "fx":
            x = x * br[:, None]  # zero exact în respirație
        x = x * en[:, None]
        stems[name] = x
    return stems, score


def master(stems: dict[str, np.ndarray], verbose: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    mix = sum(stems[k] for k in STEMS)
    gain_db = TARGET_LUFS - lufs_integrated(mix)
    info = {}
    for _ in range(4):
        g_static = db(gain_db)
        lim = limiter_gain(mix * g_static, CEILING_DBTP)
        out = mix * g_static * lim[:, None]
        lufs = lufs_integrated(out)
        info = {"gain_db": gain_db, "lufs": lufs, "tp": true_peak_db(out), "max_gr_db": float(-20 * np.log10(lim.min()))}
        if abs(lufs - TARGET_LUFS) < 0.05:
            break
        gain_db += TARGET_LUFS - lufs
    if verbose:
        print(f"· master: câștig {info['gain_db']:+.2f} dB, {info['lufs']:.2f} LUFS, vârf real {info['tp']:.2f} dBTP, "
              f"limitare maximă {info['max_gr_db']:.2f} dB")
    g_static = db(info["gain_db"])
    final = {k: stems[k] * g_static * lim[:, None] for k in STEMS}
    zero_from = int(round(SILENT_FROM * SR))
    for k in STEMS:
        final[k][zero_from:] = 0.0
    return final, info


# ======================================================================================
# 7. FIȘIERE: WAV 24 de biți, cues.json, m4a, efecte separate
# ======================================================================================


def write_wav24(path: Path, x: np.ndarray) -> None:
    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    if x.shape[0] < x.shape[1]:
        x = x.T
    q = np.clip(np.round(x * 8388608.0), -8388608, 8388607).astype("<i4")
    raw = np.ascontiguousarray(q).view(np.uint8).reshape(-1, 4)[:, :3]
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(raw.tobytes())


def quantize24(x: np.ndarray) -> np.ndarray:
    return np.clip(np.round(x * 8388608.0), -8388608, 8388607) / 8388608.0


def cues_json(score: dict, info: dict) -> dict:
    def fr(t: float) -> dict:
        return {"time": round(t, 6), "frame": round(t * FPS, 3), "frame_int": int(round(t * FPS))}

    bars = []
    for cue in CUE_MAP:
        t0 = bar_start(cue["bar"])
        chords = [name for _, name in cue.get("chords", []) if name]
        bars.append({"bar": cue["bar"], "start": t0, "end": t0 + BAR, "frame": int(round(t0 * FPS)),
                     "section": cue["section"], "on_screen": cue["screen"], "music": cue["music"],
                     "chords": chords})
    beats = []
    for b in range(1, N_BARS + 1):
        for k in range(BEATS_PER_BAR):
            t = bar_start(b) + k * BEAT
            beats.append({"time": round(t, 6), "bar": b, "beat": k + 1, "frame": round(t * FPS, 3),
                          "downbeat": k == 0})
    reveal = section_time("reveal")
    first_ping = min(e["t"] for e in score["plucks"])
    accents = {
        "pad_in": fr(0.0),
        "first_ping": fr(first_ping),
        "shimmer": fr(section_time("citiri")),
        "zoom": fr(section_time("zoom")),
        "shimmer_stop": fr(section_time("zoom")),
        "silence_start": fr(reveal - BEAT / 2),
        "reveal": fr(reveal),
        "signals": [fr(section_time("semnale") + k * BEAT) for k in (0, 2, 4)],
        "steps": [fr(section_time("pasi") + k * BEAT) for k in (2, 4, 6, 8)],
        "map": fr(section_time("harta")),
        "breakdown": fr(section_time("pauza")),
        "metric": fr(section_time("metrica")),
        "final_hit": fr(section_time("final")),
        "silent_from": fr(SILENT_FROM),
    }
    return {
        "title": "Tura de mâine (muzica filmului de 30 s)",
        "file": "tura_96bpm_30s.wav",
        "bpm": BPM,
        "time_signature": "4/4",
        "key": "re major (începe pe si minor)",
        "sample_rate": SR,
        "fps": FPS,
        "duration_seconds": DURATION,
        "bar_seconds": BAR,
        "beat_seconds": BEAT,
        "sixteenth_seconds": STEP,
        "bars": bars,
        "beats": beats,
        "accents": accents,
        "notes": {
            "signals": "cele trei semnale, din 2 în 2 timpi (12,5 / 13,75 / 15,0); fiecare cade pe un kick",
            "steps": "Perceive, Estimate, Decide, Act; notele motivului (A4, B4, C#5, E5) cad exact pe acești timpi",
            "silence_start": "de aici până la reveal e aproape liniște; doar swell-ul din stem-ul fx",
        },
        "events": score_events(score),
        "master": {"lufs_integrated_internal": round(info["lufs"], 2), "true_peak_dbtp_internal": round(info["tp"], 2),
                   "gain_db": round(info["gain_db"], 2)},
        "license": "CC0: muzică originală compusă în cod de echipa CyberPunks, fără sample-uri",
    }


def score_events(score: dict) -> dict:
    """Momentele exacte ale loviturilor din partitură (secunde), utile la montaj și la verificarea grilei."""
    def uniq(ts):
        return sorted({round(float(t), 4) for t in ts})

    keys_hits, seen = [], set()
    for ev in sorted(score["keys"], key=lambda e: e["t"]):
        k = round(ev["t"] / STEP)
        if k not in seen:  # primul ton al fiecărui acord (restul vin la +4-5 ms, rulat)
            seen.add(k)
            keys_hits.append(ev["t"])
    return {
        "kick": uniq(e["t"] for e in score["kick"]),
        "clap": uniq(e["t"] for e in score["clap"]),
        "hat": uniq(e["t"] for e in score["hat"]),
        "bass": uniq(e["t"] for e in score["bass"] + score["sub"]),
        "keys": uniq(keys_hits),
        "plucks": uniq(e["t"] for e in score["plucks"]),
    }


def sfx_reveal() -> np.ndarray:
    """Swell separat, mai prezent decât cel din mixaj: o măsură (2,5 s). Pus la 7,5 s, se termină fix la 10,0 s."""
    n = int(BAR * SR)
    rng = rng_for("sfx_reveal")
    sw = swell(["B4", "D5", "F#5", "A5", "D6"], 1.6, rng)
    out = np.zeros((n, 2))
    out[n - len(sw):] = sw
    hall = make_ir(2.0, (1.6, 1.4, 0.8), 0.015, SEED + 21)
    wet = np.stack([signal.fftconvolve(out.mean(axis=1), hall[:, c])[:n] for c in range(2)], axis=1)
    # coada reverb-ului se oprește odată cu sunetul uscat, ca totul să se termine pe 10,0 s
    t = np.arange(n) / SR
    wet *= np.clip((t - (BAR - 1.6)) / 1.6, 0.0, 1.0)[:, None] ** 2
    y = out + 0.35 * wet
    y[-int(0.003 * SR):] *= np.linspace(1.0, 0.0, int(0.003 * SR))[:, None]
    return y / np.max(np.abs(y)) * db(-14.0)


def sfx_tick() -> np.ndarray:
    """Un tic scurt și moale de interfață (90 ms), cu atacul pe primul eșantion."""
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 1250 * t) * np.exp(-t / 0.006)
         + 0.5 * np.sin(2 * np.pi * 2500 * t) * np.exp(-t / 0.0025)
         + 0.35 * np.sin(2 * np.pi * 320 * t) * np.exp(-t / 0.012))
    y *= 1.0 - np.exp(-t / 0.0002)
    y = signal.sosfilt(sos("lowpass", 6000, 2), y)
    y = y / np.max(np.abs(y)) * db(-12.0)
    return np.stack([y, y], axis=1)


def encode_m4a(wav: Path, m4a: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    if not Path(ffmpeg).exists():
        print("! ffmpeg lipsește: sar peste m4a")
        return False
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "256k",
           "-movflags", "+faststart", str(m4a)]
    subprocess.run(cmd, check=True)
    return True


# ======================================================================================
# 8. CLI
# ======================================================================================


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Randează muzica filmului „Tura de mâine” (30 s, 96 BPM).")
    ap.add_argument("--out", type=Path, default=here / "out", help="dosarul de ieșire (implicit: music/out)")
    ap.add_argument("--no-m4a", action="store_true", help="nu face previzualizarea AAC")
    ap.add_argument("--no-sfx", action="store_true", help="nu scrie sfx_reveal.wav și sfx_tick.wav")
    ap.add_argument("--no-analyze", action="store_true", help="nu rula verificările și graficele")
    ap.add_argument("--hyperframes", action="store_true",
                    help="la verificări rulează și `npx hyperframes@0.9.19 beats` (are nevoie de npx și internet)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    out: Path = args.out
    verbose = not args.quiet

    stems, score = render_all(verbose)
    final, info = master(stems, verbose)
    final = {k: quantize24(v) for k, v in final.items()}
    mix = sum(final[k] for k in STEMS)
    assert mix.shape == (N, 2)

    (out / "stems").mkdir(parents=True, exist_ok=True)
    write_wav24(out / "tura_96bpm_30s.wav", mix)
    for k in STEMS:
        write_wav24(out / "stems" / f"{k}.wav", final[k])
    (out / "cues.json").write_text(json.dumps(cues_json(score, info), ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    if not args.no_sfx:
        write_wav24(out / "sfx_reveal.wav", sfx_reveal())
        write_wav24(out / "sfx_tick.wav", sfx_tick())
    if not args.no_m4a:
        encode_m4a(out / "tura_96bpm_30s.wav", out / "tura_96bpm_30s.m4a")
    if verbose:
        print(f"· scris în {out}")
    if not args.no_analyze:
        sys.path.insert(0, str(here))
        import analyze

        analyze.run(out, verbose=verbose, hyperframes=args.hyperframes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
