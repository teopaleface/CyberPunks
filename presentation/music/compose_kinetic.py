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
import compose as C  # noqa: E402  uneltele primei variante; nu le modificăm

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
MIX_DB = {"kick": 0.0, "boom": -3.0, "clap": -4.0, "roll": -7.0, "hat": -13.0, "ohat": -17.0, "crash": -15.0,
          "bass": -2.0, "subdrop": -3.0, "pad": -9.0, "stabs": -3.0, "lead": -6.0, "arp": -15.0, "fx": -14.0}
HALL_SEND = {"stabs": 0.22, "lead": 0.30, "pad": 0.18, "fx": 0.25, "crash": 0.10}
ROOM_SEND = {"clap": 0.22, "roll": 0.18, "hat": 0.06, "ohat": 0.08}
