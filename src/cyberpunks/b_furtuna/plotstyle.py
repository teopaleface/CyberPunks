"""Stilul comun al figurilor B (paleta validată pentru daltonism, marcaje subțiri, grilă discretă).

Culori categoriale în ordine fixă: modelul e mereu albastru (slotul 1), apoi baseline-urile. Paleta
#2a78d6, #eb6834, #1baf7a, #eda100 trece verificarea CVD (cel mai mic ΔE între vecini 9,1); aqua și galben au
contrast sub 3:1 pe fundal deschis, deci au mereu etichete vizibile (legendă cu valori, tabel în raport).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
NEUTRAL = "#8c8b86"
MODEL = "#2a78d6"  # slotul 1, albastru
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # model, apoi baseline-urile, în ordine fixă

# rampă secvențială dintr-o singură nuanță (portocaliu, slotul 2): deschis = risc mic, închis = risc mare
RISK_CMAP = LinearSegmentedColormap.from_list("risc", ["#fdf0e8", "#f9c4a6", "#f08a5a", "#d95926", "#9a3a12", "#5c210a"])

FEATURE_RO = {
    "gust_max": "rafala maximă",
    "wind_max": "vântul maxim",
    "gust_prev": "rafala din ajun",
    "gust_max_2d": "rafala maximă pe 2 zile",
    "precip": "ploaia zilei",
    "precip_48h": "ploaia pe 48 h",
    "precip_7d": "ploaia pe 7 zile",
    "precip_hours": "ore cu precipitații",
    "snow": "zăpada nouă",
    "snow_3d": "zăpada pe 3 zile",
    "ice_proxy": "ploaie sub 0 °C (polei)",
    "tmax": "temperatura maximă",
    "tmin": "temperatura minimă",
    "t_range": "diferența zi-noapte",
    "srad": "radiația solară",
    "doy_sin": "sezonul (sin)",
    "doy_cos": "sezonul (cos)",
    "log_customers": "mărimea zonei",
    "log_density": "densitatea clienților",
}


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_2,
        "axes.titlecolor": TEXT,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "xtick.color": TEXT_2,
        "ytick.color": TEXT_2,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 2.0,
        "font.size": 9,
    })
