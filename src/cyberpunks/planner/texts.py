"""Formatarea cifrelor în română și șabloanele de text. Codul decide, șabloanele formulează (fără LLM)."""

from __future__ import annotations

from datetime import date, datetime

ZILE = ["luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică"]


def num(x: float, decimals: int = 0) -> str:
    """1234.5 -> '1.234,5' (separatorii românești)."""
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def lei(x: float) -> str:
    return f"{num(round(x))} lei"


def pct(x: float) -> str:
    return f"{round(100 * x)}%"


def hhmm(t: datetime) -> str:
    return t.strftime("%H:%M")


def zi(d: date) -> str:
    return f"{ZILE[d.weekday()]} {d:%d.%m.%Y}"


SOURCE_RO = {"A": "contoare", "B": "furtună", "C": "tensiune"}
ACTION_RO = {
    "inspect_on_site": "verificare la fața locului",
    "remote_reading": "citire la distanță la cerere",
    "watchlist": "urmărire, fără vizită",
    "human_review": "decizia unui om",
    "preposition_crew": "echipă trimisă din timp în zonă",
    "adjust_tap": "schimbarea prizei transformatorului",
    "measurement_campaign": "analizor de calitate a energiei montat la post",
    "notify_customers": "mesaj către prosumatori",
    "no_action": "nicio acțiune",
    "office_correction": "corecție în birou",
    "grid_inspection": "inspecție de rețea",
    "phase_rebalance": "mutarea unor case pe altă fază",
    "offer_battery": "ofertă de baterii",
    "export_limit": "limită de injecție",
    "transformer_upgrade": "transformator nou",
    "remedy": "treptele alese",
}
SKILL_RO = {"metering": "contorizare", "lv_grid": "joasă tensiune", "mv_grid": "medie tensiune"}
