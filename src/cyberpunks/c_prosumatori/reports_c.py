"""Rapoartele firului C în reports/C/: ofertele de baterii pentru PPC Energie (și, mai târziu, investițiile).

    uv run python -m cyberpunks.c_prosumatori.reports_c offers --scenario demo-vara
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from cyberpunks.c_prosumatori import remedies
from cyberpunks.c_prosumatori.explain import MONTHS_RO, fmt
from cyberpunks.common.paths import OUTPUTS, REPORTS

OUT = REPORTS / "C"


def _lei(x: float) -> str:
    """Sumă în lei cu punct la mii, ca în română (3.750)."""
    return f"{x:,.0f}".replace(",", ".")


def _items(scenario: str) -> list[dict]:
    p = OUTPUTS / "work_items" / scenario / "C.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def battery_offers(scenario: str = "demo-vara", top: int = 30) -> str:
    offers = pd.read_csv(OUTPUTS / "work_items" / scenario / "C_battery_offers.csv")
    items = {it["asset_id"]: it for it in _items(scenario)}
    c = remedies.cfg()
    a = remedies.ASSUMPTIONS
    d = pd.Timestamp(offers["target_date"].iloc[0]).date()
    lines = [
        "# Oferte de baterii pentru prosumatorii de pe posturile cu tensiune mare",
        "",
        (f"Date SINTETICE (posturi, prosumatori, profile). Ziua de calcul: {d.day} {MONTHS_RO[d.month - 1]} {d.year} (scenariul `{scenario}`). "
        f"Generat de `uv run python -m cyberpunks.c_prosumatori.reports_c offers --scenario {scenario}`."),
        "",
        "## De ce",
        "",
        ("- La prânz, bateria stochează energia care altfel ar urca tensiunea în rețeaua străzii și ar opri invertoarele vecinilor. "
        "Seara o descarcă, exact în orele 18-22, pentru care au existat măsuri guvernamentale de criză în aug.-oct. 2026 (deficit de seară). "
        "O singură baterie rezolvă două probleme."),
        ("- Casa Verde Baterii 2026 (Ord. 1.904/2026, MO 775/14.09.2026): grant de până la 75% din cost, cel mult 15.000 lei, "
        f"pentru cel puțin {c['afm_min_kwh']} kWh; cost standard maxim eligibil 1.500 lei/kWh, cu montaj și invertor."),
        ("- Canal de vânzare: magazinele PPC și Flanco (preluarea a fost anunțată pe 3 nov. 2026). Venitul e pentru PPC Energie; "
        "distribuitorul (Rețele Electrice) câștigă o rețea care nu mai trece de 1,10 pu."),
        "",
        "## Cum am calculat",
        "",
        ("- Pe profilul fiecărui prosumator fără baterie: producția din vremea reală a anului 2025 (Open-Meteo) și consumul lui, aceleași ca în "
        f"simularea fizică; variantele {', '.join(str(x) for x in c['battery_sizes_kwh'])} kWh."),
        ("- Bateria se încarcă doar în orele cu risc ale postului, cu puterea repartizată pe ele (altfel ar fi plină înainte de vârf), "
        "și se descarcă seara."),
        ("- Efectul pe tensiune: marginal (sensibilitatea rețelei în nodul cel mai expus, la ora de vârf) și pentru tot postul "
        f"(simulare cu bateriile celor care acceptă: {a['battery_accept_share']:.0%}, IPOTEZĂ)."),
        (f"- Recuperarea: (cost − grant) / economia pe an. Economia = kWh mutați de la prânz în seară × ({fmt(c['retail_price'])} − "
        f"{fmt(c['export_value'])}) lei/kWh × randament {fmt(a['battery_eta'], 1)} (prețul cu taxe PPC Ore Smart+ în afara intervalelor, "
        "valoarea energiei injectate din config). Costul: "
        f"{c['battery_price_lei_per_kwh']:.0f} lei/kWh + {c['battery_installation_cost_lei']:.0f} lei montaj (IPOTEZĂ din config)."),
        (f"- Oferta merge doar unde bateria coboară tensiunea postului cu cel puțin {a['battery_min_effect_pu']} pu și se recuperează în cel mult "
        f"{a['battery_max_payback_years']:.0f} ani (IPOTEZĂ). Pentru fiecare prosumator e aleasă mărimea cu recuperarea cea mai scurtă."),
        f"- Venitul PPC Energie: marja de {a['battery_margin_share']:.0%} din vânzare și montaj (IPOTEZĂ).",
        "",
        "## Pe posturi",
        "",
        "| Post | Zona | Prosumatori cu ofertă | kWh dacă acceptă 30% | Efect pe P90 al postului (pu) | Venit PPC Energie, 30% (lei) |",
        "|---|---|---|---|---|---|",
    ]
    for pid, g in offers.groupby("post_id", sort=False):
        it = items.get(pid, {})
        opt = next((o for o in it.get("extra", {}).get("remedy_options", []) if o["action"] == "offer_battery"), {})
        zone = it.get("location", {}).get("zone_id", "")
        lines.append(f"| {pid} | {zone} | {len(g)} | {opt.get('battery_kwh_total', 0):.0f} | {fmt(opt.get('effect_pu', 0.0), 4)} | "
                     f"{opt.get('revenue_lei', 0):.0f} |")
    best = offers.sort_values(["dv_peak_pu", "revenue_lei"], ascending=False).head(top)
    lines += [
        "",
        f"## Lista pentru PPC Energie (primii {len(best)} din {len(offers)}, după efectul pe tensiune și venit)",
        "",
        "| Prosumator (cod sintetic) | Post | kWp | Baterie (kWh) | kWh stocați la prânz | Efect pe tensiune (pu) | kWh mutați pe an | Economie (lei/an) | Cost / grant (lei) | Recuperare (ani) | Venit PPC (lei) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in best.iterrows():
        lines.append(f"| {r.prosumer} | {r.post_id} | {r.kwp:.0f} | {r.size_kwh:.0f} | {fmt(r.noon_kwh_absorbed, 1)} | {fmt(r.dv_peak_pu, 4)} | "
                     f"{r.shifted_kwh_year:.0f} | {r.saving_lei_year:.0f} | {r.cost_lei:.0f} / {r.grant_lei:.0f} | {fmt(r.payback_years, 1)} | {r.revenue_lei:.0f} |")
    med = offers.median(numeric_only=True)
    net = med["cost_lei"] - med["grant_lei"]
    total = offers.revenue_lei.sum()
    lines += [
        "",
        "## Textul ofertei (șablon, fără date personale; cifrele sunt medianele listei)",
        "",
        (f"> Panourile dumneavoastră produc la prânz mai mult decât consumați. În zilele cu soare puternic, tensiunea din rețeaua străzii crește "
        f"până când invertoarele se opresc singure. O baterie de {med['size_kwh']:.0f} kWh ar stoca circa {med['noon_kwh_absorbed']:.0f} kWh la prânz "
        f"și i-ar folosi seara, când energia e cea mai scumpă și sistemul are cea mai mare nevoie de ea. Cu grantul Casa Verde Baterii 2026, "
        f"costul dumneavoastră scade la circa {_lei(net)} lei și se recuperează în circa {med['payback_years']:.0f} ani. "
        "Detalii în magazinele PPC și Flanco."),
        "",
        (f"Total: {len(offers)} oferte pe {offers.post_id.nunique()} posturi, venit potențial {_lei(total)} lei dacă acceptă toți "
        f"({_lei(total * a['battery_accept_share'])} lei la {a['battery_accept_share']:.0%})."),
        "",
    ]
    text = "\n".join(lines)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "oferte_baterii.md").write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["offers"])
    ap.add_argument("--scenario", default="demo-vara")
    args = ap.parse_args()
    if args.what == "offers":
        print(battery_offers(args.scenario)[:1500])
