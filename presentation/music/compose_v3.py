#!/usr/bin/env python3
"""Muzica filmului „Tura de mâine”, varianta 3 (scenariul nou, mai simplu): 36,000 s, 120 BPM, 4/4, 18 măsuri de 2,0 s.

O bătaie = 0,5 s = exact 15 cadre la 30 fps; o măsură = 2,0 s = 60 de cadre. Toate loviturile cad pe cadre întregi.
Aceeași paletă ca varianta cinetică (compose_kinetic.py): kick acordat, clap, hi-hat, bas din fierăstrău filtrat,
pad cu sidechain, acorduri scurte („stab”), motivul pe coarda ciupită, risere. Se schimbă forma și harta loviturilor:
un cârlig întunecat (fa diez minor, peste o notă ținută în bas), o întrebare urmată de aer, trei probleme care urcă
câte o treaptă, apoi la major pe „Tura de mâine face planul.”, produsul, momentul uman, drop-ul și logoul.

Instrumentele vin din compose_kinetic.py, uneltele (reverb, limitator, loudness, WAV, m4a) din compose.py.
Niciunul nu se modifică. Totul e sintetizat în cod, fără sample-uri. Seed fix: același fișier, bit cu bit.

Muzică originală compusă în cod de echipa CyberPunks pentru acest proiect. Licență CC0.

Rulare, din rădăcina repo-ului:
    uv run python presentation/music/compose_v3.py
    uv run python presentation/music/compose_v3.py --no-determinism   # o singură randare
"""

from __future__ import annotations

# ruff: noqa: RUF046  # int(round(x)) rămâne: x poate fi un scalar NumPy folosit ca index
import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "4")  # cel mult 4 nuclee

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose as C  # unelte: răspuns la impuls, limitator, loudness, WAV, m4a (nu le modificăm)
import compose_kinetic as K  # instrumentele variantei cinetice (nu le modificăm)

# ======================================================================================
# 1. GRILA
# ======================================================================================

SR = C.SR  # 48 kHz
BPM = 120
BEATS_PER_BAR = 4
N_BARS = 18
FPS = 30
SEED = 20261136

BEAT = 60.0 / BPM  # 0,5 s = 15 cadre
BAR = BEATS_PER_BAR * BEAT  # 2,0 s = 60 de cadre
STEP = BEAT / 4  # o șaisprezecime: 0,125 s
DURATION = N_BARS * BAR  # 36,0 s
N = int(round(DURATION * SR))  # 1.728.000 de eșantioane
assert N == 1_728_000

TARGET_LUFS = -16.0
CEILING_DBTP = -1.3  # marjă față de -1,0 dBTP cerut
FADE_FROM = 34.4
SILENT_FROM = 35.9  # de aici până la 36,0 s: zero digital
AIR = (6.0, 7.75)  # „Dar unde?”: rămâne doar acordul suspendat

WAV_NAME = "tura_v3_36s.wav"
M4A_NAME = "tura_v3_36s.m4a"
MP4_NAME = "tura_v3_36s_asculta.mp4"
CUES_NAME = "cues_v3.json"
STEMS_DIR = "stems_v3"
STEMS = ("drums", "bass", "pad", "stabs", "lead", "fx")

# ======================================================================================
# 2. ARMONIA, LOVITURILE, MĂSURILE (date editabile)
# ======================================================================================

# Cârligul stă în fa diez minor, peste un fa diez ținut în bas (pedală): F#m, D/F#, Bm/F#. Întrebarea: Dmaj9,
# apoi „Dar unde?” pe un mi suspendat (Esus4 cu nona), lăsat fără răspuns. Problemele urcă pe aceeași formă de acord
# (în cvarte) câte o treaptă: Bm11, C#m7, Dmaj7#11; riserul stă pe mi (Esus4, E). Pe 12,0 mi-ul se rezolvă în la
# major: întrebarea primește răspuns. Produsul: A, E/G#, F#m9, Dmaj9 (I, V6, vi, IV). Momentul uman pornește pe
# F#m9 (cadență întreruptă: V merge spre vi, nu spre I). Build-ul pe mi, drop-ul pe la; finalul IV, V, I pe logo.
CHORDS = {
    #  nume        bas      pad (de jos în sus)                        stab (de jos în sus)
    "F#m": ("F#1", ["C#3", "F#3", "A3", "C#4"], ["F#3", "A3", "C#4", "F#4"]),
    "D/F#": ("F#1", ["D3", "F#3", "A3", "C#4"], ["D3", "A3", "C#4", "F#4"]),
    "Bm/F#": ("F#1", ["D3", "F#3", "B3", "C#4"], ["B2", "F#3", "B3", "D4", "F#4"]),
    "Dmaj9": ("D2", ["F#3", "A3", "C#4", "E4", "A4"], ["D3", "A3", "E4", "F#4", "C#5"]),
    "Esus_air": ("E1", [], ["E4", "A4", "B4", "F#5"]),
    "Bm11": ("B1", ["D3", "A3", "B3", "E4", "F#4"], ["B3", "E4", "A4", "D5", "F#5"]),
    "C#m7": ("C#2", ["E3", "G#3", "B3", "E4", "G#4"], ["C#4", "F#4", "B4", "E5", "G#5"]),
    "Dmaj7#11": ("D2", ["F#3", "A3", "C#4", "E4", "G#4"], ["D4", "G#4", "C#5", "F#5", "A5"]),
    "Esus4": ("E1", ["E3", "A3", "B3", "E4", "A4"], ["E3", "B3", "E4", "A4", "B4"]),
    "E": ("E1", ["E3", "G#3", "B3", "E4", "G#4"], ["E3", "B3", "E4", "G#4", "B4"]),
    "A": ("A1", ["E3", "A3", "C#4", "E4", "B4"], ["A3", "E4", "B4", "C#5", "E5"]),
    "E/G#": ("G#1", ["E3", "G#3", "B3", "E4", "B4"], ["G#3", "E4", "F#4", "B4", "E5"]),
    "F#m9": ("F#1", ["E3", "A3", "C#4", "E4", "G#4"], ["F#3", "C#4", "E4", "G#4", "C#5"]),
    "Afinal": ("A1", ["A2", "E3", "A3", "C#4", "E4", "B4", "C#5"],
               ["A2", "E3", "A3", "C#4", "E4", "B4", "C#5", "E5"]),
}
BIG_A = ["A2", "E3", "A3", "C#4", "E4", "B4", "E5"]  # acordul mare de pe 12,0 și 29,0

# Când se schimbă acordul (secunde). Basul și padul urmează lista; stab-urile o folosesc când nu au note proprii.
TIMELINE = [
    (0.0, "F#m"), (1.0, "D/F#"), (2.0, "Bm/F#"), (4.0, "Dmaj9"), (6.0, "Esus_air"),
    (8.0, "Bm11"), (9.0, "C#m7"), (10.0, "Dmaj7#11"), (11.0, "Esus4"), (11.5, "E"),
    (12.0, "A"), (14.0, "E/G#"), (15.0, "F#m9"), (16.0, "Dmaj9"),
    (18.0, "A"), (19.0, "E/G#"), (20.0, "F#m9"), (21.0, "Dmaj9"), (22.0, "Esus4"), (22.5, "E"),
    (23.0, "F#m9"), (25.0, "Bm11"), (26.0, "Dmaj9"), (27.0, "Esus4"), (28.0, "E"),
    (29.0, "A"), (30.0, "Dmaj9"), (31.0, "Esus4"), (31.5, "E"), (32.0, "Afinal"),
]

# Loviturile filmului. Fiecare începe fix pe cadru (timp × 30 = cadru întreg). note=None: din acordul momentului.
# Tipuri: soft_low = acord jos și moale; storm = acord întunecat + boom acordat pe fa diez + tunet îndepărtat (zgomot
# filtrat, sintetizat); heavy = lovitură grea + sub care coboară o octavă (curentul se duce); pulse = intră pulsul
# (kick moale, hi-hat, acord scurt); sus = acordul suspendat, singur în aer; pickup = două lovituri mici de snare;
# step = acord + kick + tom acordat pe fundamentală (fiecare cu o treaptă mai sus); build = rafală de snare și riser;
# lift = acordul mare de la major, groove-ul pornește; accent = acord + kick + clap + crash mic; press = buton
# apăsat (acord foarte scurt, clap strâns); note = o notă din motiv; accent_note = ultima notă a motivului + accent;
# fill = umplutură ușoară; soft = acord moale și filtrat, tobele ies; card = o notă moale; press_big = apăsare
# cu crash, tobele revin; drop = lovitura mare; final = logoul.
HITS = [
    # timp, nume, pe ecran, tip, note
    (0.0, "data", "„8 iulie 2025.”", "soft_low", None),
    (1.0, "vijelie", "„Vijelie în Banat.” (norul de furtună 3D intră)", "storm", None),
    (2.0, "fara_curent", "„Zeci de mii de case fără curent.” (apoi pad întunecat până la 4,0)", "heavy", None),
    (4.0, "echipele", "„Mâine dimineață pleacă echipele.” (casca intră)", "pulse", None),
    (6.0, "dar_unde", "„Dar unde?” (totul tace, rămâne un acord suspendat)", "sus", None),
    (7.75, "pickup", "două lovituri mici de snare spre 8,0", "pickup", None),
    (8.0, "stalpi", "„Stâlpi căzuți.” (stâlpul 3D)", "step", None),
    (9.0, "curent_furat", "„Curent furat.” (al doilea obiect 3D)", "step", None),
    (10.0, "prea_mult_soare", "„Prea mult soare.” (panoul solar)", "step", None),
    (11.0, "riser", "riser și rafală de snare spre 12,0", "build", None),
    (12.0, "tura_de_maine", "„Tura de mâine face planul.” (soarele logoului răsare)", "lift", BIG_A),
    (15.0, "consola", "consola apare", "accent", None),
    (16.0, "ruleaza", "CLIC pe „Rulează agentul”", "press", ["F#4", "A4", "E5"]),
    (16.5, "traseu_1", "traseele echipelor se desenează (1/4)", "note", ["B4"]),
    (17.0, "traseu_2", "traseele (2/4)", "note", ["C#5"]),
    (17.5, "traseu_3", "traseele (3/4)", "note", ["E5"]),
    (18.0, "fiecare_echipa", "„Fiecare echipă știe unde merge.” (4/4)", "accent_note", ["A5"]),
    (22.0, "umplutura", "umplutură ușoară spre 23,0", "fill", None),
    (23.0, "dispecerul", "„Când nu e sigur, întreabă dispecerul.” (tobele ies)", "soft", None),
    (25.0, "cardul", "cardul real apare", "card", ["F#5"]),
    (26.0, "aproba", "CLIC pe „Aprobă” (tobele revin)", "press_big", None),
    (27.0, "build", "build: rafală de snare și riser spre 29,0", "build", None),
    (29.0, "drop", "pastila neagră umple ecranul: „Aceleași echipe.”", "drop", BIG_A),
    (30.0, "castig", "„Aproape cu jumătate mai mult câștig.”", "accent", None),
    (32.0, "final", "logoul: soarele răsare peste traseu", "final", None),
]

# Ce se întâmplă în fiecare măsură (pentru cues_v3.json și grafice).
BARS = {
    1: ("cârlig", "„8 iulie 2025.” „Vijelie în Banat.”", "acord jos și moale; boom acordat și tunet pe 1,0"),
    2: ("cârlig", "„Zeci de mii de case fără curent.”", "lovitura grea, sub care coboară; pad întunecat, fără tobe"),
    3: ("întrebare", "„Mâine dimineață pleacă echipele.”", "intră un puls ușor: kick moale pe 1 și 3, hi-hat"),
    4: ("întrebare", "„Dar unde?”", "totul tace; doar un acord suspendat până la 7,75; două snare spre 8,0"),
    5: ("probleme", "„Stâlpi căzuți.” „Curent furat.”", "lovituri pe 8,0 și 9,0, fiecare cu o treaptă mai sus"),
    6: ("probleme", "„Prea mult soare.”; riser", "a treia treaptă pe 10,0; riser și rafală 11,0-12,0"),
    7: ("răspuns", "„Tura de mâine face planul.”", "la major: groove-ul pornește (kick pe fiecare timp, clap pe 2 și 4)"),
    8: ("produs", "consola apare (15,0)", "accent pe 15,0"),
    9: ("produs", "CLIC „Rulează agentul”; traseele", "clic pe 16,0; motivul urcă pe 16,5, 17,0, 17,5"),
    10: ("produs", "„Fiecare echipă știe unde merge.”", "a patra notă și accent pe 18,0; intră arpegiul"),
    11: ("produs", "harta cu traseele", "cald și sigur"),
    12: ("produs / uman", "umplutură (22,0); „întreabă dispecerul” (23,0)", "umplutură ușoară; pe 23,0 tobele ies"),
    13: ("uman", "cardul real (25,0)", "pad filtrat, o notă moale pe 25,0"),
    14: ("uman / build", "CLIC „Aprobă” (26,0); build (27,0)", "tobele revin; rafală și riser de la 27,0"),
    15: ("build / drop", "pastila neagră (29,0)", "build până fix la 29,0; drop"),
    16: ("drop", "„Aproape cu jumătate mai mult câștig.” (30,0)", "accent; IV, V spre final"),
    17: ("final", "logoul (32,0)", "acordul de la major; tobele se opresc"),
    18: ("final", "logoul rămâne pe negru", "coada se stinge; zero digital de la 35,9"),
}

SECTIONS = [
    ("cârlig", 0.0, 4.0, "întunecat și rar: trei lovituri, apoi pad ținut, fără tobe"),
    ("întrebare", 4.0, 8.0, "puls ușor de la 4,0; de la 6,0 la 7,75 doar acordul suspendat"),
    ("probleme", 8.0, 12.0, "trei lovituri care urcă; riser 11,0-12,0"),
    ("răspuns", 12.0, 15.0, "la major, groove-ul pornește"),
    ("produs", 15.0, 23.0, "consola, clicul, motivul de 4 note, cald până la 23,0"),
    ("uman", 23.0, 27.0, "tobele ies, pad filtrat; pe 26,0 tobele revin"),
    ("build", 27.0, 29.0, "rafală de snare și riser, cu măsură"),
    ("drop", 29.0, 32.0, "lovitura mare, apoi accentul de pe 30,0"),
    ("final", 32.0, DURATION, "logoul; coada se stinge; zero digital de la 35,9"),
]

# Nivelurile (dB) pe instrumente și trimiterile spre reverb (ca în varianta cinetică, plus tom-ul și tunetul).
MIX_DB = dict(K.MIX_DB) | {"boom": -4.5, "tom": -1.0, "rumble": 9.0}  # boom-ul cu 1,5 dB sub varianta 2: mai puțină limitare
HALL_SEND = dict(K.HALL_SEND)
ROOM_SEND = dict(K.ROOM_SEND)

# ======================================================================================
# 3. UTILITARE PE 36 s ȘI SUNETELE NOI
# ======================================================================================

midi, hz, db, pan_gains, add_at, fade_tail = C.midi, C.hz, C.db, C.pan_gains, C.add_at, C.fade_tail
sos = K.sos


def rng(*keys) -> np.random.Generator:
    """Generator determinist pentru fiecare sunet, independent de ordinea randării."""
    return np.random.default_rng([SEED, *[C.hash_str(k) if isinstance(k, str) else int(k) for k in keys]])


def curve(points, log: bool = False) -> np.ndarray:
    """Ca C.curve, dar pe 36 s: curbă din puncte (timp, valoare), cu treceri line; două puncte la același timp = salt."""
    pts = sorted(points, key=lambda p: p[0])
    tp = np.array([p[0] for p in pts], dtype=float)
    vp = np.array([p[1] for p in pts], dtype=float)
    if log:
        vp = np.log(vp)
    t = np.arange(N) / SR
    i = np.clip(np.searchsorted(tp, t, side="right") - 1, 0, len(tp) - 2)
    span = tp[i + 1] - tp[i]
    frac = np.clip(np.where(span > 0, (t - tp[i]) / np.where(span > 0, span, 1.0), 1.0), 0.0, 1.0)
    out = vp[i] + (vp[i + 1] - vp[i]) * (0.5 - 0.5 * np.cos(np.pi * frac))
    return np.exp(out) if log else out


_SOS_REV_HP = sos("highpass", 250, 2)
_SOS_REV_LP = sos("lowpass", 6500, 2)
_SOS_DELAY_LP = sos("lowpass", 3800, 1)


def reverb(x: np.ndarray, ir: np.ndarray, send: float) -> np.ndarray:
    """Ca C.reverb (aceleași filtre pe trimitere), pentru orice lungime."""
    mono = signal.sosfilt(_SOS_REV_LP, signal.sosfilt(_SOS_REV_HP, 0.5 * (x[:, 0] + x[:, 1]) * send))
    return np.stack([signal.fftconvolve(mono, ir[:, c])[: len(x)] for c in range(2)], axis=1)


def pingpong(x: np.ndarray, delay: float, feedback: float, repeats: int) -> np.ndarray:
    """Ca C.pingpong: ecou stânga-dreapta, fiecare repetiție puțin mai întunecată."""
    sig = 0.5 * (x[:, 0] + x[:, 1])
    d = int(round(delay * SR))
    out = np.zeros_like(x)
    for i in range(1, repeats + 1):
        sig = signal.sosfilt(_SOS_DELAY_LP, sig)
        if i * d >= len(x):
            break
        out[i * d:, (i - 1) % 2] += feedback ** (i - 1) * sig[: len(x) - i * d]
    return out


def pump(times, depth: float, release: float = 0.16, attack: float = 0.003) -> np.ndarray:
    """Sidechain calculat din momentele kick-ului: câștigul coboară la kick și revine lin."""
    env = np.zeros(N)
    ln = int(0.5 * SR)
    tt = np.arange(ln) / SR
    shape = (1.0 - np.exp(-tt / attack)) * np.exp(-tt / release)
    shape /= shape.max()
    for t0, v in times:
        i0 = int(round(t0 * SR))
        i1 = min(N, i0 + ln)
        env[i0:i1] = np.maximum(env[i0:i1], v * shape[: i1 - i0])
    return 1.0 - depth * env


_SOS_RUMBLE = sos("lowpass", 240, 4)
_SOS_RUMBLE_MOD = sos("lowpass", 5.0, 2)
_SOS_CRACKLE = sos("bandpass", (350, 1400), 2)


def rumble(length: float, vel: float, rng_: np.random.Generator) -> np.ndarray:
    """Tunet îndepărtat, sintetizat: zgomot sub 240 Hz care se rostogolește (modulație lentă, întâmplătoare,
    dar fixată de seed) și se stinge în ~1,5 s, plus o pânză mai sus (350-1400 Hz), mult mai încet. Fără sample-uri."""
    n = int(length * SR)
    t = np.arange(n) / SR
    low = signal.sosfilt(_SOS_RUMBLE, rng_.standard_normal((n, 2)), axis=0)
    mid = signal.sosfilt(_SOS_CRACKLE, rng_.standard_normal((n, 2)), axis=0)
    mod = signal.sosfilt(_SOS_RUMBLE_MOD, rng_.standard_normal(n))
    mod = 1.0 + 0.55 * mod / (np.max(np.abs(mod)) + 1e-12)
    env = (1.0 - np.exp(-t / 0.012)) * (0.65 * np.exp(-t / 0.55) + 0.35 * np.exp(-t / 1.3))
    y = (low / np.std(low) + 0.18 * mid / np.std(mid)) * (env * mod)[:, None]
    return fade_tail(y * vel / (np.max(np.abs(y)) + 1e-12), 120.0)


def tom_sound(f0: float, vel: float, rng_: np.random.Generator) -> np.ndarray:
    """Tom acordat pe fundamentala acordului (kick-ul cinetic, mai acut și fără clic): treptele se aud și în tobe."""
    return K.kick_sound(vel, rng_, tune=f0, decay=0.2, length=0.6, click=0.0, drive=1.5)


def grid(t0: float, t1: float, step: float) -> list[float]:
    """Momentele t0, t0 + step, ... mai mici decât t1 (fiecare cade exact pe un eșantion)."""
    k = int(np.ceil((t1 - t0) / step - 1e-9))
    return [round(t0 + i * step, 6) for i in range(max(0, k))]


def beat_in_bar(t: float) -> int:
    return int(round((t % BAR) / BEAT))


def chord_at(t: float) -> str:
    name = TIMELINE[0][1]
    for t0, nm in TIMELINE:
        if t0 <= t + 1e-9:
            name = nm
    return name


def drone(f0: float, dur: float, vel: float, att: float = 0.35, cutoff: float = 300.0) -> np.ndarray:
    """Notă joasă ținută, care crește încet (fără atac): fundalul întunecat de sub pad, 2,0-4,0 s."""
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    saw = K.saw_additive(f0, n, cutoff)[:, 0]
    y = 0.42 * saw / (np.std(saw) + 1e-12) + 0.7 * np.sin(2 * np.pi * f0 * t)
    return fade_tail(y * K.envelope(n, dur, att, 1.0, 1.0, 0.15) * vel, 30.0)


# ======================================================================================
# 4. PARTITURA: din HITS, TIMELINE și secțiuni, în evenimente
# ======================================================================================

# Padul: nivel 0-1 și frecvența de tăiere (Hz), puncte (timp, valoare). Două puncte cu același timp fac un salt.
# 1,0-2,0: intră încet, foarte închis (furtuna); 2,0-4,0: padul întunecat ținut; 6,0-8,0: tace (aerul);
# 11-12: se deschide; 23,0: se închide (momentul uman); 27-28,875: se deschide (build); 28,875-29,0: o
# șaisprezecime de gol înainte de drop.
PAD_LEVEL = [(0.0, 0.0), (1.0, 0.0), (1.9, 0.55), (2.0, 0.55), (2.0, 1.0), (3.9, 0.9), (4.0, 0.7), (5.95, 0.75),
             (6.0, 0.0), (8.0, 0.0), (8.0, 0.8), (11.0, 0.85), (11.95, 1.0), (23.0, 1.0), (23.06, 0.85),
             (26.0, 0.85), (26.0, 1.0), (28.85, 1.0), (28.875, 0.0), (29.0, 0.0), (29.0, 1.0), (32.0, 1.0),
             (32.0, 0.95), (34.0, 0.65), (35.6, 0.0)]
PAD_CUTOFF = [(0.0, 300.0), (1.0, 300.0), (2.0, 420.0), (2.0, 680.0), (3.9, 520.0), (4.0, 900.0), (6.0, 1000.0),
              (8.0, 1100.0), (11.0, 1300.0), (11.95, 4500.0), (12.0, 2300.0), (18.0, 2600.0), (23.0, 2600.0),
              (23.08, 450.0), (26.0, 480.0), (26.0, 2400.0), (27.0, 1800.0), (28.875, 7000.0), (29.0, 3000.0),
              (32.0, 3400.0), (35.9, 700.0)]

# În build-uri basul se subțiază (filtru trece-sus care urcă spre 200 Hz); pe lovitura următoare revine tot.
BASS_HP = [(0.0, 18.0), (11.5, 18.0), (11.95, 180.0), (12.0, 180.0), (12.0, 18.0), (28.0, 18.0), (28.875, 200.0),
           (29.0, 200.0), (29.0, 18.0), (DURATION, 18.0)]

# Aerul de la „Dar unde?”: tot ce a sunat înainte de 6,0 (cu reverb și ecou) se oprește în 6 ms. Pe 7,75 se
# redeschide. Acordul suspendat are stratul lui, care nu trece prin poartă.
GATE_AIR = [(0.0, 1.0), (AIR[0] - 0.006, 1.0), (AIR[0], 0.0), (AIR[1], 0.0), (AIR[1], 1.0), (DURATION, 1.0)]
# „Când nu e sigur, întreabă dispecerul.”: tobele ies pe 23,0 (în 50 ms) și revin fix pe 26,0.
GATE_DRUMS = [(0.0, 1.0), (23.0, 1.0), (23.05, 0.0), (26.0, 0.0), (26.0, 1.0), (DURATION, 1.0)]

# Basul: (pas de șaisprezecime în măsură, interval față de fundamentală, velocity, lungime în pași)
BASS_OFFBEAT, BASS_ROLLING, BASS_DRIVE = K.BASS_OFFBEAT, K.BASS_ROLLING, K.BASS_DRIVE
BASS_EIGHTHS = tuple((s, 0, 1.0 if s % 4 == 0 else 0.72, 1.6) for s in range(0, 16, 2))  # optimi pe fundamentală
ARP_IDX = K.ARP_IDX


def stab(S: dict, t: float, name: str, notes, vel: float, dur: float, **opt) -> None:
    S["stab"].append({"t": t, "name": name, "notes": list(notes), "vel": vel, "dur": dur, **opt})


def build_score() -> dict:
    S: dict = {k: [] for k in ("boom", "tom", "roll", "hat", "ohat", "crash", "bass", "drone", "subdrop", "stab",
                               "lead", "arp", "riser", "rumble")}
    kicks: dict[float, dict] = {}
    claps: dict[float, dict] = {}

    def kick(t: float, vel: float, **opt) -> None:
        if t not in kicks or kicks[t]["vel"] < vel:
            kicks[t] = {"t": t, "vel": vel, **opt}

    def clap(t: float, vel: float, **opt) -> None:
        if t not in claps or claps[t]["vel"] < vel:
            claps[t] = {"t": t, "vel": vel, **opt}

    # ---- kick: puls pe 1 și 3 (4-6 moale, 8-11 mai ferm), apoi kick pe fiecare timp în groove ----
    for t in grid(4.0, 6.0, 2 * BEAT):
        kick(t, 0.6, decay=0.12)
    for t in grid(8.0, 11.5, 2 * BEAT):
        kick(t, 0.85)
    for t in grid(12.0, 23.0, BEAT) + grid(26.0, 28.75, BEAT) + grid(29.0, 32.0, BEAT):
        kick(t, 0.95 if beat_in_bar(t) == 0 else 0.9)
    # ---- clap pe 2 și 4, doar în groove ----
    for t in grid(12.0, 23.0, BEAT) + grid(26.0, 28.0, BEAT) + grid(29.0, 32.0, BEAT):
        if beat_in_bar(t) in (1, 3):
            clap(t, 0.8)

    # ---- hi-hat ----
    for t in grid(4.0, 6.0, STEP):
        s = int(round((t % BEAT) / STEP))
        if s == 2:
            S["hat"].append({"t": t, "vel": 0.45})
        elif s in (1, 3) and t >= 5.0:
            S["hat"].append({"t": t, "vel": 0.18})
    for t in grid(8.0, 11.0, STEP):
        s = int(round((t % BEAT) / STEP))
        if s == 2:
            S["hat"].append({"t": t, "vel": 0.5})
        elif s in (1, 3):
            S["hat"].append({"t": t, "vel": 0.2})
    for t in grid(11.0, 12.0, STEP):
        S["hat"].append({"t": t, "vel": 0.25 + 0.25 * (t - 11.0)})
    for t in grid(12.25, 23.0, BEAT) + grid(26.25, 27.0, BEAT) + grid(29.25, 32.0, BEAT):
        S["hat"].append({"t": t, "vel": 0.62 if t < 29.0 else 0.55})
    for t in grid(14.0, 22.0, STEP):
        s = int(round((t % BEAT) / STEP))
        if s in (1, 3):
            S["hat"].append({"t": t, "vel": 0.24 if s == 1 else 0.3})
    for t in grid(27.0, 28.875, STEP):
        S["hat"].append({"t": t, "vel": 0.25 + 0.15 * (t - 27.0)})
    for t in grid(18.25, 22.0, BEAT) + grid(29.25, 32.0, BEAT):
        S["ohat"].append({"t": t, "vel": 0.5})

    # ---- snare: pickup-ul spre 8,0, riserul 11-12, umplutura 22-23, build-ul 27-29, spre logo ----
    S["roll"] += [{"t": 7.75, "vel": 0.3}, {"t": 7.875, "vel": 0.42}]
    for t in grid(11.0, 11.5, BEAT / 2):
        S["roll"].append({"t": t, "vel": 0.34 + 0.2 * (t - 11.0)})
    for t in grid(11.5, 12.0, STEP):
        S["roll"].append({"t": t, "vel": 0.45 + 0.6 * (t - 11.5)})
    for t in grid(22.0, 22.5, BEAT / 2):
        S["roll"].append({"t": t, "vel": 0.3 + 0.12 * (t - 22.0)})
    for t in grid(22.5, 23.0, STEP):
        S["roll"].append({"t": t, "vel": 0.36 + 0.4 * (t - 22.5)})
    for t in grid(27.0, 28.0, BEAT / 2):
        S["roll"].append({"t": t, "vel": 0.34 + 0.18 * (t - 27.0)})
    for t in grid(28.0, 28.875, STEP):
        S["roll"].append({"t": t, "vel": 0.52 + 0.4 * (t - 28.0)})
    for t, v in ((31.75, 0.45), (31.875, 0.6)):
        S["roll"].append({"t": t, "vel": v})

    # ---- loviturile filmului ----
    for t, name, _screen, kind, notes in HITS:
        nts = notes if notes is not None else CHORDS[chord_at(t)][2]
        if kind == "soft_low":
            stab(S, t, name, nts, 0.85, 0.55, amp_tau=0.5, sustain=0.12, cut_hi=1700.0, cut_lo=380.0, cut_tau=0.16,
                 release=0.3)
            kick(t, 0.5, decay=0.1)
        elif kind == "storm":
            stab(S, t, name, nts, 0.9, 0.8, amp_tau=0.8, sustain=0.25, cut_hi=2100.0, cut_lo=330.0, cut_tau=0.28,
                 release=0.4)
            S["boom"].append({"t": t, "vel": 0.8, "tune": hz(midi("F#1")), "decay": 0.9, "length": 2.2})
            S["rumble"].append({"t": t, "vel": 0.6, "length": 2.8})
        elif kind == "heavy":
            stab(S, t, name, nts, 1.05, 0.5, amp_tau=0.5, cut_hi=3200.0, cut_lo=480.0, cut_tau=0.12)
            kick(t, 0.95)
            clap(t, 0.75)
            S["boom"].append({"t": t, "vel": 0.56, "tune": hz(midi("F#1")), "decay": 0.45, "length": 1.4})
            S["crash"].append({"t": t, "vel": 0.55, "length": 2.0, "decay": 0.7})
            S["subdrop"].append({"t": t, "f0": hz(midi("F#2")), "f1": hz(midi("F#1")), "length": 1.6, "vel": 0.9})
        elif kind == "pulse":
            stab(S, t, name, nts, 0.7, 0.14, cut_hi=4200.0)
            S["hat"].append({"t": t, "vel": 0.4})
        elif kind == "sus":
            stab(S, t, name, nts, 0.2, 1.45, amp_tau=0.55, sustain=0.35, cut_hi=2600.0, cut_lo=900.0, cut_tau=0.35,
                 release=0.3, air=True)
        elif kind in ("pickup", "build"):
            pass  # snare-ul și riserele sunt scrise mai sus și mai jos
        elif kind == "step":
            stab(S, t, name, nts, 0.95, 0.2, cut_hi=5200.0)
            kick(t, 0.95)
            S["tom"].append({"t": t, "vel": 0.6, "f0": hz(midi(CHORDS[chord_at(t)][0]) + 12)})
        elif kind in ("lift", "drop"):
            stab(S, t, name, BIG_A, 1.05 if kind == "lift" else 1.08, 0.45, amp_tau=0.5, cut_hi=6500.0)
            kick(t, 1.0)
            clap(t, 0.95)
            S["boom"].append({"t": t, "vel": 0.52 if kind == "lift" else 0.7, "tune": hz(midi("A1")), "decay": 0.5,
                              "length": 1.4})
            S["crash"].append({"t": t, "vel": 0.9 if kind == "lift" else 0.95, "length": 2.4, "decay": 0.9})
            if kind == "lift":  # soarele logoului: trei clopoței pe la major
                for nm, v in (("A5", 0.45), ("C#6", 0.38), ("E6", 0.32)):
                    S["lead"].append({"t": t, "name": f"{name}_clopotel", "m": midi(nm), "vel": v, "dur": 1.2})
        elif kind == "accent":
            stab(S, t, name, nts, 1.0, 0.3, amp_tau=0.4, cut_hi=6000.0)
            kick(t, 1.0)
            clap(t, 0.85)
            S["crash"].append({"t": t, "vel": 0.4, "length": 1.2, "decay": 0.35})
        elif kind == "press":
            stab(S, t, name, nts, 0.8, 0.05, amp_tau=0.06, cut_hi=3800.0, cut_tau=0.03)
            clap(t, 0.7, tail=0.04)
        elif kind == "note":
            S["lead"].append({"t": t, "name": name, "m": midi(nts[0]), "vel": 0.9, "dur": 0.42})
        elif kind == "accent_note":
            S["lead"].append({"t": t, "name": name, "m": midi(nts[0]), "vel": 0.95, "dur": 0.7})
            stab(S, t, name, CHORDS[chord_at(t)][2], 1.0, 0.3, amp_tau=0.4, cut_hi=6000.0)
            kick(t, 1.0)
            clap(t, 0.85)
            S["crash"].append({"t": t, "vel": 0.5, "length": 1.6, "decay": 0.5})
        elif kind == "fill":
            S["ohat"].append({"t": t, "vel": 0.45})
        elif kind == "soft":
            stab(S, t, name, nts, 0.75, 0.9, amp_tau=0.6, sustain=0.2, cut_hi=1900.0, cut_lo=500.0, cut_tau=0.2,
                 release=0.25)
        elif kind == "card":
            S["lead"].append({"t": t, "name": name, "m": midi(nts[0]), "vel": 0.6, "dur": 0.8})
        elif kind == "press_big":
            stab(S, t, name, nts, 1.0, 0.25, amp_tau=0.35, cut_hi=6000.0)
            kick(t, 1.0)
            clap(t, 0.9)
            S["crash"].append({"t": t, "vel": 0.6, "length": 1.8, "decay": 0.6})
        elif kind == "final":
            stab(S, t, name, CHORDS["Afinal"][2], 0.85, 2.6, sustain=0.22, amp_tau=0.9, cut_hi=5200.0, cut_lo=1100.0,
                 cut_tau=0.6, release=0.7)
            kick(t, 0.95)
            S["boom"].append({"t": t, "vel": 0.65, "tune": hz(midi("A1")), "decay": 0.5, "length": 1.4})
            S["crash"].append({"t": t, "vel": 0.75, "length": 3.2, "decay": 1.1})
            for nm, v in (("A5", 0.5), ("C#6", 0.42), ("E6", 0.36)):
                S["lead"].append({"t": t, "name": f"{name}_clopotel", "m": midi(nm), "vel": v, "dur": 1.6})
        else:
            raise ValueError(f"tip necunoscut: {kind}")

    # ---- arpegiul: după motiv (18,5-22,0) și în drop (29,0-31,75, o octavă mai sus, mai încet) ----
    for t in grid(18.5, 22.0, STEP) + grid(29.0, 31.75, STEP):
        tones = sorted(midi(nm) for nm in CHORDS[chord_at(t)][2])[-4:]
        s = int(round((t % BEAT) / STEP))
        up = t >= 29.0
        S["arp"].append({"t": t, "m": tones[ARP_IDX[s]] + (12 if up else 0),
                         "vel": (0.42 if s == 0 else 0.3) if up else (0.5 if s == 0 else 0.36), "gain_db": 0.0})

    # ---- basul ----
    for t, vel, dur, peak in ((0.0, 0.75, 0.85, 650.0), (1.0, 0.85, 0.9, 800.0)):
        S["bass"].append({"t": t, "m": midi("F#1"), "vel": vel, "dur": dur, "cut_peak": peak, "cut_tau": 0.12})
    S["drone"].append({"t": 2.0, "f0": hz(midi("F#1")), "dur": 1.95, "vel": 0.55})
    S["bass"].append({"t": 4.0, "m": midi("D2"), "vel": 0.7, "dur": 0.4, "cut_peak": 700.0})

    def lay(t0: float, t1: float, pattern, scale: float = 1.0, **opt) -> None:
        for b0 in grid(0.0, DURATION, BAR):
            for step, iv, vel, ln in pattern:
                t = round(b0 + step * STEP, 6)
                if t0 - 1e-9 <= t < t1 - 1e-9:
                    S["bass"].append({"t": t, "m": midi(CHORDS[chord_at(t)][0]) + iv, "vel": vel * scale,
                                      "dur": ln * STEP - 0.01, **opt})

    lay(4.0, 6.0, BASS_OFFBEAT, 0.7, cut_peak=700.0)
    lay(8.0, 12.0, BASS_EIGHTHS, cut_peak=1100.0)
    lay(12.0, 15.0, BASS_OFFBEAT)
    lay(15.0, 22.5, BASS_ROLLING)
    lay(22.5, 23.0, BASS_OFFBEAT)
    for t, nm, dur in ((23.0, "F#1", 1.95), (25.0, "B1", 0.95)):
        S["bass"].append({"t": t, "m": midi(nm), "vel": 0.6, "dur": dur, "cut_peak": 420.0, "cut_base": 180.0,
                          "cut_tau": 0.3})
    lay(26.0, 28.0, BASS_ROLLING)
    lay(28.0, 28.875, BASS_EIGHTHS)
    lay(29.0, 32.0, BASS_DRIVE)
    S["bass"].append({"t": 32.0, "m": midi("A1"), "vel": 0.72, "dur": 2.3, "cut_peak": 800.0, "cut_tau": 0.3,
                      "release": 0.4})

    # ---- risere (se taie fix pe lovitura următoare); build-ul de la 27,0 e mai reținut decât în varianta 2 ----
    S["riser"] += [
        {"kind": "noise", "t0": 11.0, "t1": 12.0, "f0": 600.0, "f1": 7000.0, "vel": 0.6},
        {"kind": "pitch", "t0": 11.0, "t1": 12.0, "notes": ["E3", "B3"], "semis": 7.0, "vel": 0.42},
        {"kind": "noise", "t0": 27.0, "t1": 29.0, "f0": 300.0, "f1": 8000.0, "vel": 0.85},
        {"kind": "pitch", "t0": 27.0, "t1": 29.0, "notes": ["E3", "B3", "E4"], "semis": 12.0, "vel": 0.55},
    ]
    S["kick"] = sorted(kicks.values(), key=lambda e: e["t"])
    S["clap"] = sorted(claps.values(), key=lambda e: e["t"])
    for k in ("hat", "ohat", "roll", "stab", "lead", "arp", "bass", "crash", "boom", "tom"):
        S[k].sort(key=lambda e: e["t"])
    return S


# ======================================================================================
# 5. RANDARE PE STEM-URI, MIXAJ, MASTER
# ======================================================================================


def render_pad() -> np.ndarray:
    """Pad: cinci fierăstraie dezacordate pe notă, filtrate (ca în varianta cinetică), de la 1,0 s.
    O notă comună cu acordul următor ține (legato); un acord fără note de pad (aerul) oprește tot."""
    ends = [t for t, _ in TIMELINE[1:]] + [DURATION]
    segs = [(t0, nm) for (t0, nm), _t1 in zip(TIMELINE, ends) if t0 >= 1.0 - 1e-9]
    events, active = [], {}
    for t0, nm in segs:
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
        env = K.envelope(n, (i_off - i0) / SR, 0.02, 1.0, 1.0, 0.25)
        for cents, p in K.PAD_VOICES:
            y = K.polyblep_saw(hz(m) * 2.0 ** (cents / 1200.0), n, float(r.uniform())) * env
            gl, gr = pan_gains(p)
            out[i0:i1, 0] += y * gl
            out[i0:i1, 1] += y * gr
    out = K.stft_lowpass(out, curve(PAD_CUTOFF, log=True))
    out = signal.sosfilt(sos("highpass", 140, 2), out, axis=0)  # padul lasă loc basului și kick-ului
    return out * curve(PAD_LEVEL)[:, None] * (0.5 / len(K.PAD_VOICES))


def render_drums(S: dict, room: np.ndarray, hall: np.ndarray) -> np.ndarray:
    parts = {k: np.zeros((N, 2)) for k in ("kick", "boom", "tom", "clap", "roll", "hat", "ohat", "crash")}
    for i, e in enumerate(S["kick"]):
        opt = {k: e[k] for k in ("decay",) if k in e}
        add_at(parts["kick"], K.kick_sound(e["vel"], rng("kick", i), **opt), e["t"])
    for i, e in enumerate(S["boom"]):
        add_at(parts["boom"], K.kick_sound(e["vel"], rng("boom", i), tune=e["tune"], decay=e["decay"],
                                           length=e["length"], click=0.0, drive=1.6), e["t"])
    for i, e in enumerate(S["tom"]):
        add_at(parts["tom"], tom_sound(e["f0"], e["vel"], rng("tom", i)), e["t"], pan_gains(0.15 * (i - 1)))
    for i, e in enumerate(S["clap"]):
        add_at(parts["clap"], K.clap_sound(e["vel"], rng("clap", i), tail=e.get("tail", 0.10)), e["t"],
               pan_gains(-0.06))
    for i, e in enumerate(S["roll"]):
        add_at(parts["roll"], K.clap_sound(e["vel"], rng("roll", i), tail=0.06, body=0.45, air=0.3,
                                           flams=K.SNARE_FLAMS), e["t"], pan_gains(0.12 * np.sin(1.7 * i)))
    for i, e in enumerate(S["hat"]):
        add_at(parts["hat"], K.hat_sound(e["vel"], rng("hat", i)), e["t"], pan_gains(0.25))
    for i, e in enumerate(S["ohat"]):
        add_at(parts["ohat"], K.hat_sound(e["vel"], rng("ohat", i), decay=0.11, length=0.42), e["t"],
               pan_gains(-0.2))
    for i, e in enumerate(S["crash"]):
        add_at(parts["crash"], K.crash_sound(e["vel"], rng("crash", i), e["length"], e["decay"]), e["t"])
    for k in parts:
        parts[k] *= db(MIX_DB[k])
    out = sum(parts.values())
    for k in ("clap", "roll", "hat", "ohat"):
        out = out + reverb(parts[k], room, ROOM_SEND[k])
    return out + reverb(parts["crash"], hall, HALL_SEND["crash"])


def render_bass(S: dict, kicks) -> np.ndarray:
    bass = np.zeros((N, 2))
    for e in S["bass"]:
        opt = {k: e[k] for k in ("cut_peak", "cut_base", "cut_tau", "release") if k in e}
        add_at(bass, K.bass_sound(hz(e["m"]), e["vel"], e["dur"], **opt), e["t"])
    for e in S["drone"]:
        add_at(bass, drone(e["f0"], e["dur"], e["vel"]), e["t"])
    pumped = [(t, v) for t, v in kicks if t >= 8.0 - 1e-9]  # în cârlig și în puls basul lovește odată cu kick-ul
    bass = signal.sosfilt(sos("lowpass", 3000, 2), bass, axis=0) * pump(pumped, 0.75, release=0.09)[:, None]
    bass = K.stft_lowpass(bass, curve(BASS_HP, log=True), highpass=True)  # build: basul se subțiază
    drop = np.zeros((N, 2))
    for e in S["subdrop"]:
        add_at(drop, K.sub_drop(e["f0"], e["f1"], e["length"], e["vel"]), e["t"])
    return bass * db(MIX_DB["bass"]) * 0.35 + drop * db(MIX_DB["subdrop"]) * 0.35


def render_stabs(S: dict, air: bool) -> np.ndarray:
    dry = np.zeros((N, 2))
    keys = ("cut_hi", "cut_lo", "cut_tau", "amp_tau", "sustain", "release")
    for i, e in enumerate(S["stab"]):
        if bool(e.get("air", False)) != air:
            continue
        y = K.stab_sound(e["notes"], e["vel"], e["dur"], rng("stab", i), **{k: e[k] for k in keys if k in e})
        add_at(dry, y, e["t"])
    dry = signal.sosfilt(sos("highpass", 110, 2), dry, axis=0)
    return dry * db(MIX_DB["stabs"]) * 0.25


def render_lead(S: dict) -> tuple[np.ndarray, np.ndarray]:
    lead = np.zeros((N, 2))
    for i, e in enumerate(S["lead"]):
        add_at(lead, K.lead_sound(hz(e["m"]), e["vel"], e["dur"], rng("lead", i)), e["t"],
               pan_gains(0.1 if i % 2 else -0.1))
    arp = np.zeros((N, 2))
    for i, e in enumerate(S["arp"]):
        add_at(arp, K.arp_sound(hz(e["m"]), e["vel"] * db(e["gain_db"]), rng("arp", i)), e["t"],
               pan_gains(0.35 * np.sin(2 * np.pi * i / 7.0)))
    return lead * db(MIX_DB["lead"]) * 0.25, arp * db(MIX_DB["arp"]) * 0.25


def render_fx(S: dict) -> np.ndarray:
    out = np.zeros((N, 2))
    for i, e in enumerate(S["riser"]):
        ln = e["t1"] - e["t0"]
        if e["kind"] == "noise":
            y = K.riser_noise(ln, e["f0"], e["f1"], rng("riser", i))
        else:
            y = K.riser_pitch(e["notes"], ln, e["semis"], rng("riser", i))
        add_at(out, y * e["vel"], e["t0"])
    out *= db(MIX_DB["fx"]) * 0.5
    storm = np.zeros((N, 2))
    for i, e in enumerate(S["rumble"]):
        add_at(storm, rumble(e["length"], e["vel"], rng("rumble", i)), e["t"])
    return out + storm * db(MIX_DB["rumble"]) * 0.25


def render_all(verbose: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    say = print if verbose else (lambda *a, **k: None)
    S = build_score()
    kicks = [(e["t"], e["vel"]) for e in S["kick"]]
    hall = C.make_ir(2.4, (1.9, 1.6, 0.9), 0.02, SEED + 1)
    room = C.make_ir(0.8, (0.5, 0.42, 0.25), 0.006, SEED + 2, early=False)
    say("· tobe")
    drums = render_drums(S, room, hall)
    say("· bas")
    bass = render_bass(S, kicks)
    say("· pad")
    pad = render_pad() * pump(kicks, 0.6, release=0.16)[:, None] * db(MIX_DB["pad"])
    say("· stab-uri")
    stabs = render_stabs(S, air=False)
    air = render_stabs(S, air=True)
    say("· motiv și arpegiu")
    lead, arp = render_lead(S)
    say("· risere și tunet")
    fx = render_fx(S)
    say("· reverb și ecou")
    stab_echo = pingpong(stabs * 0.16, 3 * STEP, 0.3, 4)
    lead_echo = pingpong(lead * 0.22, 3 * STEP, 0.32, 4)
    air_echo = pingpong(air * 0.16, 3 * STEP, 0.3, 4)
    stems = {
        "drums": drums,
        "bass": bass,
        "pad": pad + reverb(pad, hall, HALL_SEND["pad"]),
        "stabs": stabs + stab_echo + reverb(stabs + stab_echo, hall, HALL_SEND["stabs"]),
        "lead": lead + arp + lead_echo + reverb(lead + lead_echo + arp, hall, HALL_SEND["lead"]),
        "fx": fx + reverb(fx, hall, HALL_SEND["fx"]),
    }
    air_wet = air + air_echo + reverb(air + air_echo, hall, HALL_SEND["stabs"])
    # Liniar și cauzal, identic pe fiecare stem: sub 120 Hz totul e mono, fără infrasunete. Abia apoi porțile
    # (aerul de la 6,0, tobele care ies pe 23,0), ca filtrele să nu mai lase nimic să sune în liniște.
    hp = sos("highpass", 25, 2)

    def finish(x: np.ndarray) -> np.ndarray:
        return signal.sosfilt(hp, C.mono_below(x, 120.0), axis=0)

    gate = curve(GATE_AIR)
    gate_drums = curve(GATE_DRUMS)
    en = curve([(0.0, 1.0), (FADE_FROM, 1.0), (SILENT_FROM - 0.04, 0.0), (DURATION, 0.0)])
    for k in STEMS:
        stems[k] = finish(stems[k]) * gate[:, None]
    stems["drums"] = stems["drums"] * gate_drums[:, None]
    stems["stabs"] = stems["stabs"] + finish(air_wet)
    for k in STEMS:
        stems[k] = stems[k] * en[:, None]
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
# 6. FIȘIERE: WAV 24 de biți, stem-uri, cues_v3.json, m4a, copia de ascultat (mp4)
# ======================================================================================

LAYERS = {
    "soft_low": "acord jos și moale (fa diez minor) + bas fa diez + kick foarte moale",
    "storm": "acord întunecat (re peste fa diez) + boom acordat pe fa diez + tunet îndepărtat (zgomot sintetizat)",
    "heavy": "acord greu (si minor peste fa diez) + kick + boom + clap + crash + sub care coboară o octavă",
    "pulse": "acord scurt (Dmaj9) + hi-hat; pulsul: kick moale pe 1 și 3, hi-hat pe contratimp, bas ușor",
    "sus": "acordul suspendat (mi, la, si, fa diez), singur; tot restul tace până la 7,75",
    "pickup": "două lovituri mici de snare (7,75 și 7,875)",
    "step": "acord în cvarte + kick + tom acordat pe fundamentală (si, do diez, re: câte o treaptă mai sus)",
    "build": "rafală de snare (optimi, apoi șaisprezecimi) + riser din zgomot + riser tonal",
    "lift": "la major mare + kick + boom + clap + crash + trei clopoței; groove-ul pornește",
    "accent": "acord mare + kick + clap + crash mic",
    "press": "acord foarte scurt + clap strâns (clicul)",
    "note": "o notă din motiv (coardă ciupită + clopoțel)",
    "accent_note": "ultima notă a motivului (la) + acord mare + kick + clap + crash",
    "fill": "umplutură ușoară de snare (optimi, apoi șaisprezecimi) + hi-hat deschis",
    "soft": "acord moale și filtrat (F#m9); tobele ies până la 26,0",
    "card": "o notă moale (fa diez) din motiv",
    "press_big": "acord + kick + clap + crash; tobele revin",
    "drop": "la major mare + kick + boom + clap + crash",
    "final": "A add9 mare + kick + boom + crash + clopoței; tobele se opresc",
}
# În ce stem stă fiecare tip de lovitură (acolo se verifică atacul ei, fără restul mixajului).
CARRIER = {"soft_low": "stabs", "storm": "stabs", "heavy": "stabs", "pulse": "stabs", "sus": "stabs",
           "pickup": "drums", "step": "stabs", "build": "drums", "lift": "stabs", "accent": "stabs", "press": "stabs",
           "note": "lead", "accent_note": "lead", "fill": "drums", "soft": "stabs", "card": "lead",
           "press_big": "stabs", "drop": "stabs", "final": "stabs"}


# Pickup-ul de pe 7,75 e o șaisprezecime muzicală (cadrul 232,5), nu o lovitură din imagine: nu-l mutăm pe un cadru
# întreg, ar ieși de pe grilă cu 17 ms. Restul loviturilor cad pe cadre întregi (se verifică mai jos).
MUSICAL_ONLY = {"pickup"}


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
        picture = kind not in MUSICAL_ONLY
        assert not picture or abs(t * FPS - round(t * FPS)) < 1e-9, f"{name}: {t} s nu cade pe un cadru întreg"
        hits.append({"name": name, "time": t, "frame": frame_of(t), "frame_exact": round(t * FPS, 6),
                     "picture_hit": picture, "on_screen": screen, "kind": kind, "music": LAYERS[kind],
                     "carrier_stem": CARRIER[kind],
                     "chord": chord_at(t), "notes": notes if notes is not None else CHORDS[chord_at(t)][2]})
    return {
        "title": "Tura de mâine, varianta 3 (muzica filmului de 36 s, scenariul nou)",
        "file": WAV_NAME,
        "bpm": BPM,
        "time_signature": "4/4",
        "key": "la major (cârligul în fa diez minor, peste pedală de fa diez)",
        "sample_rate": SR,
        "fps": FPS,
        "duration_seconds": DURATION,
        "duration_frames": frame_of(DURATION),
        "bar_seconds": BAR,
        "bar_frames": 60,
        "beat_seconds": BEAT,
        "beat_frames": 15,
        "sixteenth_seconds": STEP,
        "sections": [{"name": n, "start": a, "end": b, "frame_start": frame_of(a), "frame_end": frame_of(b),
                      "note": d} for n, a, b, d in SECTIONS],
        "air_window": {"start": AIR[0], "end": AIR[1], "frame_start": frame_of(AIR[0]), "frame_end": frame_of(AIR[1]),
                       "note": "doar acordul suspendat de pe 6,0; tot restul tace (cu tot cu reverb)"},
        "drums_out": {"start": 23.0, "end": 26.0, "note": "momentul uman: fără tobe"},
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
            "boom": uniq(e["t"] for e in S["boom"]),
            "tom": uniq(e["t"] for e in S["tom"]),
            "stab": uniq(e["t"] for e in S["stab"]),
            "lead": uniq(e["t"] for e in S["lead"]),
            "arp": uniq(e["t"] for e in S["arp"]),
            "bass": uniq(e["t"] for e in S["bass"]),
            "risers": [{"start": e["t0"], "end": e["t1"], "kind": e["kind"]} for e in S["riser"]],
            "storm_rumble": uniq(e["t"] for e in S["rumble"]),
        },
        "stems": list(STEMS),
        "master": {"lufs_integrated_internal": round(info["lufs"], 2), "true_peak_dbtp_internal": round(info["tp"], 2),
                   "gain_db": round(info["gain_db"], 2), "max_limiting_db": round(info["max_gr_db"], 2)},
        "license": "CC0: muzică originală compusă în cod de echipa CyberPunks, fără sample-uri",
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_to(out: Path, verbose: bool = True, m4a: bool = True) -> dict:
    """Randează, masterizează și scrie mixajul, stem-urile și cues_v3.json. Întoarce amprentele fișierelor."""
    stems, S = render_all(verbose)
    final, info = master(stems, verbose)
    final = {k: C.quantize24(v) for k, v in final.items()}
    mix = sum(final[k] for k in STEMS)  # multipli de 2^-23: suma e exactă
    assert mix.shape == (N, 2)
    (out / STEMS_DIR).mkdir(parents=True, exist_ok=True)
    C.write_wav24(out / WAV_NAME, mix)
    for k in STEMS:
        C.write_wav24(out / STEMS_DIR / f"{k}.wav", final[k])
    (out / CUES_NAME).write_text(json.dumps(cues_json(S, info), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = [out / WAV_NAME, out / CUES_NAME] + [out / STEMS_DIR / f"{k}.wav" for k in STEMS]
    if m4a and C.encode_m4a(out / WAV_NAME, out / M4A_NAME):
        files.append(out / M4A_NAME)
    return {str(p.relative_to(out)): sha256(p) for p in files}


def listening_copy(out: Path, playhead: dict | None = None, verbose: bool = True) -> Path | None:
    """Copia de ascultat pentru Teo: graficul formei de undă + muzica, H.264 + AAC, exact 36,0 s.
    Dacă știm unde e axa timpului în imagine, o linie albă arată unde a ajuns muzica."""
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    if not Path(ffmpeg).exists():
        print("! ffmpeg lipsește: sar peste mp4")
        return None
    png, dst = out / "waveform_v3.png", out / MP4_NAME
    width = 1920
    if playhead:  # pozițiile vin din grafic (fracții din lățime și înălțime)
        h_img = int(round(width * playhead["height_px"] / playhead["width_px"] / 2) * 2)
        x0, x1 = playhead["x0"] * width, playhead["x1"] * width
        y0, y1 = int(playhead["y0"] * h_img), int(playhead["y1"] * h_img)
        vf = (f"[0:v]scale={width}:{h_img}:flags=lanczos[bg];color=c=white:s=3x{y1 - y0}:r={FPS}[ph];"
              f"[bg][ph]overlay=x='{x0:.2f}+{x1 - x0:.2f}*t/{DURATION:g}-1':y={y0}:shortest=1,format=yuv420p[v]")
        vargs = ["-filter_complex", vf, "-map", "[v]", "-map", "1:a"]
    else:
        vargs = ["-vf", f"scale={width}:-2:flags=lanczos,format=yuv420p"]
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
           "-i", str(out / WAV_NAME), *vargs, "-t", f"{DURATION:g}", "-r", str(FPS), "-c:v", "libx264",
           "-preset", "medium", "-crf", "20", "-tune", "stillimage", "-c:a", "aac", "-b:a", "256k", "-ar", str(SR),
           "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)
    if verbose:
        print(f"· copia de ascultat: {dst.name}")
    return dst


# ======================================================================================
# 7. CLI
# ======================================================================================


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Randează muzica variantei 3 a filmului „Tura de mâine” (36 s, 120 BPM).")
    ap.add_argument("--out", type=Path, default=HERE / "out", help="dosarul de ieșire (implicit: music/out)")
    ap.add_argument("--no-m4a", action="store_true", help="fără previzualizarea AAC")
    ap.add_argument("--no-analyze", action="store_true", help="fără verificări, grafice și copia mp4")
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
        det = {"renders": 2, "identical": all(same.values()), "files": same, "sha256": dict(hashes)}
        if verbose:
            print(f"· determinism: {'identic bit cu bit' if det['identical'] else 'DIFERIT'} ({len(same)} fișiere)")
    if not args.no_analyze:
        import analyze_v3

        rep = analyze_v3.run(out, verbose=verbose, determinism=det)
        mp4 = listening_copy(out, rep.get("plot_axes"), verbose)
        if mp4 is not None:
            analyze_v3.add_listening_copy(out, mp4, verbose=verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
