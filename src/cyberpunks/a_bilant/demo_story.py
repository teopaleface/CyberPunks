"""Posturile pentru prezentare (scenariul demo-vara), alese automat și verificate cu adevărul din construcție.

    uv run python -m cyberpunks.a_bilant.demo_story      # după predict; scrie reports/bilant/demo_posts.md

1. A și bilanțul se confirmă reciproc: contorul suspect explică lipsa de la post (scorul A e simulat).
2. Dezechilibrul de faze găsit de bilanț, intrare pentru treapta `phase_rebalance` a scării de tensiune (C).
3. Contorul postului setat greșit (×2): lipsa e doar pe hârtie.
4. Clientul trecut la postul greșit: un post cu lipsă, vecinul cu surplus.
"""

from __future__ import annotations

import json

import pandas as pd

from cyberpunks.a_bilant import world
from cyberpunks.common.paths import DATA_PROCESSED, OUTPUTS, REPORTS


def main(scenario: str = "demo-vara") -> None:
    items = [json.loads(x) for x in (OUTPUTS / "work_items" / scenario / "A_bilant.jsonl").read_text().splitlines() if x.strip()]
    by = {x["asset_id"]: x for x in items}
    plans = json.loads((DATA_PROCESSED / "bilant" / "pop" / "plans.json").read_text())
    fm = pd.read_parquet(DATA_PROCESSED / "bilant" / "fusion_meters_pop.parquet")
    D = int(fm["day"].max())
    fm["rank_a"] = fm.groupby("day")["a"].rank(ascending=False)
    fm["rank_f"] = fm.groupby("day")["fused"].rank(ascending=False)
    md = [f"# Posturile pentru prezentare ({scenario})", "", "SIMULARE pe date publice, gândită pentru datele PPC. Fiecare caz e verificat cu problema ascunsă de noi (adevărul din construcție). Comanda: `uv run python -m cyberpunks.a_bilant.demo_story`.", ""]

    def bad_meters(pid: str) -> set[int]:
        return {p["customer"] for p in plans[pid]["problems"] if p["kind"] in ("meter_fault", "meter_tamper")}

    # 1. confirmarea: contorul suspect corect, cu scăderea cea mai apropiată de lipsa postului
    cands = []
    for x in items:
        e = x["extra"]
        if x["prediction"]["label"] != "contor_client" or "suspect_meter" not in e:
            continue
        c = int(e["suspect_meter"][-3:])
        if c not in bad_meters(x["asset_id"]):
            continue
        r = x["prediction"]["point_estimate"]
        cands.append((abs(abs(e["suspect_meter_drop_kwh_day"]) - abs(r)) / max(abs(r), 1), x))
    md += ["## 1. Contorul și bilanțul se confirmă", ""]
    if cands:
        _, x = min(cands, key=lambda t: t[0])
        e = x["extra"]
        pid = x["asset_id"]
        c = int(e["suspect_meter"][-3:])
        kind = next(p for p in plans[pid]["problems"] if p.get("customer") == c and p["kind"] in ("meter_fault", "meter_tamper"))
        row = fm[(fm["post_id"] == pid) & (fm["customer"] == c) & (fm["day"] == D)]
        md += [
            f"- **{pid}**, lucrarea `{x['work_item_id']}`: {x['explanation']['summary_ro']}",
            f"- Contorul suspect: `{e['suspect_meter']}` ({e['suspect_meter_reason_ro']}), consum dispărut ~{abs(e['suspect_meter_drop_kwh_day']):.1f} kWh/zi; lipsa peste normal la post: ~{x['prediction']['point_estimate']:.1f} kWh/zi.",
            f"- Adevărul: contorul are problema `{kind['params']['type']}` ({kind['kind']}) din ziua {kind['onset_day']} a simulării. Recomandarea: {x['recommended_action']} (întâi citirea la distanță).",
        ]
        if len(row):
            rr = row.iloc[0]
            md.append(f"- Scorul de tip A (SIMULAT, calibrat la ROC-AUC 0,907) {rr['a']:.2f} devine {rr['fused']:.2f} cu bilanțul; locul în lista zilei: {int(rr['rank_a'])} → {int(rr['rank_f'])} din {int((fm['day'] == D).sum())} contoare.")
    md.append("")

    # 2. fazele: pierdere tehnică cu dezechilibru real
    md += ["## 2. Dezechilibrul de faze, intrare pentru scara de soluții (C)", ""]
    tech = []
    for x in items:
        if x["prediction"]["label"] != "pierdere_tehnica" or "phase_rebalance_input" not in x["extra"]:
            continue
        p = next((p for p in plans[x["asset_id"]]["problems"] if p["kind"] == "technical"), None)
        if p and p["params"].get("mode") == "unbalance":
            tech.append((x["impact"]["expected_value_lei"], x, p))
    if tech:
        _, x, p = max(tech, key=lambda t: t[0])
        pri = x["extra"]["phase_rebalance_input"]
        sh = sorted(p["params"]["shares"], reverse=True)
        md += [
            f"- **{x['asset_id']}**, lucrarea `{x['work_item_id']}`: {x['explanation']['summary_ro']}",
            f"- Bilanțul vede pierderea pe cabluri de {pri['loss_ratio_vs_normal']:.1f} ori normalul și estimează că faza cea mai încărcată are ~{pri['max_phase_share_est']:.0%} din case.",
            f"- Adevărul: din ziua {p['onset_day']}, casele sunt împărțite {sh[0]:.0%} / {sh[1]:.0%} / {sh[2]:.0%} pe faze (u = {world.unbalance_u(sh):.2f}).",
            "- Pentru C: `extra.phase_rebalance_input` e intrarea treptei `phase_rebalance` (mută câteva case pe altă fază, o oră de lucru). Aceeași mutare scade și pierderile, și tensiunea pe faza încărcată.",
        ]
    md.append("")

    # 3. contorul postului setat greșit
    md += ["## 3. Contorul postului setat greșit", ""]
    cfg = [x for x in items if x["prediction"]["label"] == "contor_bilant_setat" and any(p["kind"] == "balance_meter_config" for p in plans[x["asset_id"]]["problems"])]
    allcfg = [x for x in items if x["prediction"]["label"] == "contor_bilant_setat"]
    if cfg:
        x = max(cfg, key=lambda w: abs(w["prediction"]["point_estimate"]))
        on = next(p["onset_day"] for p in plans[x["asset_id"]]["problems"] if p["kind"] == "balance_meter_config")
        md += [
            f"- **{x['asset_id']}**: {x['explanation']['summary_ro']}",
            f"- Adevărul: raportul de transformare greșit din ziua {on}. Toate cele {len(allcfg)} posturi marcate așa au chiar această problemă: {len(cfg) == len(allcfg)}.",
        ]
    md.append("")

    # 4. clientul la postul greșit
    md += ["## 4. Clientul trecut la postul greșit", ""]
    for pid, pl in plans.items():
        don = next((p for p in pl["problems"] if p["kind"] == "wrong_post_donor"), None)
        if not don or not don["params"].get("receiver"):
            continue
        rcv = don["params"]["receiver"]
        if rcv in by and by[rcv]["prediction"]["label"] == "client_post_gresit":
            x = by[rcv]
            md += [
                f"- **{rcv}** (lucrarea `{x['work_item_id']}`): {x['explanation']['summary_ro']}",
                f"- Adevărul: clientul `{pid}-C{don['customer']:03d}` e legat fizic la {pid}, dar din ziua {don['onset_day']} apare în bază la {rcv}. {pid} are lipsă, {rcv} are surplus. Corecția se face în birou, fără deplasare.",
                f"- {pid} în lista zilei: {by[pid]['prediction']['label'] + ' (' + by[pid]['recommended_action'] + ')' if pid in by else 'fără lucrare (lipsa e sub pragul de incertitudine)'}.",
            ]
            break
    md.append("")
    n_true = sum(1 for x in items if plans[x["asset_id"]]["problems"])
    md += ["## Lista zilei, pe scurt", "", f"- {len(items)} lucrări de bilanț; {n_true} sunt pe posturi care chiar au cel puțin o problemă ascunsă.", "- Acțiuni: " + ", ".join(f"{k} {int(v)}" for k, v in pd.Series([x["recommended_action"] for x in items]).value_counts().items()) + "."]
    (REPORTS / "bilant" / "demo_posts.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
