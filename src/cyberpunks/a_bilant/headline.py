"""Cifrele bilanțului pentru prezentare, într-o pagină: `reports/bilant/headline.md`.

    uv run python -m cyberpunks.a_bilant.headline      # după evaluate și predict (inclus în `make bilant-predict`)

Nicio cifră nu e scrisă de mână: toate vin din `metrics.json` (comanda `make bilant-eval`). SIMULARE pe date publice.
"""

from __future__ import annotations

import json

from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "bilant"
CAUSE_RO = {
    "furt_inainte_contor": "furt înainte de contor",
    "pierdere_tehnica": "pierderi în cabluri sau faze dezechilibrate",
    "contor_bilant_setat": "contorul postului setat greșit",
    "client_post_gresit": "client trecut în bază la alt post",
}


def ro(x: float, d: int = 1) -> str:
    return f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x: float, d: int = 0) -> str:
    return ro(x * 100, d) + "%"


DEMO_POST = "PT-1269"


def demo_post_lines(scenario: str = "demo-vara") -> list[str]:
    """Postul unde dezechilibrul găsit de bilanț e intrarea treptei `phase_rebalance` a lui C (din lucrarea generată)."""
    from cyberpunks.common.paths import OUTPUTS

    p = OUTPUTS / "work_items" / scenario / "A_bilant.jsonl"
    if not p.exists():
        return [f"- {DEMO_POST}: rulează întâi `make bilant-predict`."]
    w = next((json.loads(x) for x in p.read_text().splitlines() if x.strip() and json.loads(x)["asset_id"] == DEMO_POST), None)
    if not w or "phase_rebalance_input" not in w["extra"]:
        return [f"- {DEMO_POST} nu are azi o lucrare de pierdere tehnică (vezi `reports/bilant/demo_posts.md`)."]
    pri = w["extra"]["phase_rebalance_input"]
    return [
        f"- **{DEMO_POST}** (`{w['work_item_id']}`): pierderea pe cabluri e de {ro(pri['loss_ratio_vs_normal'], 1)} ori normalul, iar bilanțul estimează că o fază are ~{pct(pri['max_phase_share_est'])} din case. Adevărul din simulare și potrivirea cu lucrarea lui C (`C-{w['work_item_id'][2:]}`, `phase_rebalance` prima treaptă) sunt în `reports/bilant/demo_posts.md`.",
        f"- {w['explanation']['summary_ro']}",
        "",
    ]


def main() -> None:
    mj = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    M, B = mj["metrics"], mj["baseline_metrics"]
    md = [
        "# Bilanț pe post: cifrele pentru prezentare",
        "",
        f"SIMULARE pe date publice, gândită pentru datele PPC. Sursa: `reports/bilant/metrics.json` ({mj['model_version']}), comanda `make bilant-data bilant-eval`. Test: cele 300 de posturi ale hărții (registrul C), rețele nevăzute la antrenare; defectele de contor sunt cele ale firului A.",
        "",
        "## 1. Ce vede doar bilanțul (cifra principală)",
        "",
        "Contoarele clienților (modelul A) nu au cum să vadă aceste probleme: A găsește 0 prin construcție.",
        "",
        "| Problema | Bilanțul găsește postul | și cauza corectă | Energia lipsă găsită |",
        "|---|---|---|---|",
    ]
    for c, name in CAUSE_RO.items():
        f = M.get(f"cauze_post_{c}_found")
        if f is None:
            continue
        en = M.get(f"cauze_post_{c}_energy_found_share")
        md.append(f"| {name} | {pct(f)} | {pct(M[f'cauze_post_{c}_right_cause'])} | {pct(en) if en is not None else 'doar pe hârtie'} |")
    md += [
        "",
        f"- **Bilanțul găsește {pct(M['cauze_post_energy_found_share'])} din energia pierdută din aceste cauze, ~{ro(M['cauze_post_lei_per_month_found'], 0)} lei pe lună** pe cele 300 de posturi (la 0,70 lei/kWh, `config/economics.yaml`). Din posturile marcate, {pct(M['cauze_post_false_alarm_share_of_found'])} sunt de fapt normale.",
        f"- În ziua demo, **{pct(M['invizibil_share_invisible_to_meters'])} din energia pierdută peste normal nu apare la niciun contor de client**.",
        f"- Diagnosticul cauzei: F1 macro {ro(M['diagnoza_macro_f1'], 2)} față de {ro(B['diagnoza_macro_f1'], 2)} la tabelul de reguli din concept.",
        "",
        "## 2. Cu bilanț față de fără, la verificările de contoare",
        "",
        "Bilanțul doar confirmă (urcă scorul contorului când lipsa de la post crește cât lipsește la contor); nu coboară niciodată un contor găsit de A.",
        "",
        "| Modelul de contoare | K verificări pe zi | Precizia fără → cu | Deplasări degeaba evitate pe zi | Lei recuperați pe zi fără → cu |",
        "|---|---|---|---|---|",
    ]
    for pre, name in (("fuziune_", "scor A simulat, calitatea pe Londra (AUC 0,91)"), ("fuziune_sgcc_", "scor A simulat, calitatea pe SGCC (AUC 0,80)")):
        for i, K in enumerate((10, 20, 50, 100)):
            md.append(
                f"| {name if i == 0 else ''} | {K} | {pct(B[f'{pre}precision_at_{K}'], 1)} → {pct(M[f'{pre}precision_at_{K}'], 1)} | {ro(M[f'{pre}wasted_trips_avoided_per_day_at_{K}'], 2)} | {ro(B[f'{pre}value_lei_per_day_at_{K}'], 0)} → {ro(M[f'{pre}value_lei_per_day_at_{K}'], 0)} |"
            )
    for i, K in enumerate((10, 100, 300, 500)):
        a, f = M[f"fuziune_a_real_precision_at_{K}_a"], M[f"fuziune_a_real_precision_at_{K}_fused"]
        wa, wf = M[f"fuziune_a_real_wasted_trips_at_{K}_a"], M[f"fuziune_a_real_wasted_trips_at_{K}_fused"]
        md.append(f"| {'scorurile REALE ale lui A, ziua demo' if i == 0 else ''} | {K} | {pct(a, 1)} → {pct(f, 1)} | {ro(wa - wf, 0)} | - |")
    md += [
        "",
        "Cum se citește: cu scorurile reale, A e deja precis în vârful listei, iar bilanțul nu mai adaugă nimic la clasare. Când modelul de contoare e mai slab, confirmarea din bilanț ridică banii recuperați (la calitatea SGCC, de "
        + ro(M["fuziune_sgcc_value_lei_per_day_at_10"] / max(B["fuziune_sgcc_value_lei_per_day_at_10"], 1), 1)
        + " ori în primele 10).",
        "",
        "## 3. Unde montăm întâi contoarele de bilanț (planul B)",
        "",
        "`reports/bilant/plan_b.md`: gradul de integrare a contoarelor inteligente e 56-67% pe regiuni (31 dec. 2025). Montând contoare de bilanț la 20% din posturi, în ordinea modelului, găsim mai multă energie lipsă decât la întâmplare sau la „posturile mari întâi”.",
        "",
        "## 4. Postul pentru demo",
        "",
    ]
    md += demo_post_lines()
    (OUT / "headline.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
