# Status: Teo-C-prosumatori
Actualizat: 2026-11-07 13:12
Milestone curent: M1 (M0 terminat la 13:10)
Gata de merge: da (commit cb66431, M0: cod de simulare, cercetare, teste; nu atinge fișiere comune în afară de secțiunea C din Makefile)

## Făcut
- 12:45 Citit instrucțiunile, memoria, planul, contractele. `uv sync` și `make check` trec.
- 12:50-13:00 Faza 0 cu 3 subagenți în paralel: date publice (Open-Meteo, PVGIS, OSM), norme și cifre românești (ANRE, Ord. 46/2021, Ore Smart+), literatura despre modele surogat. Totul în `docs/research/C.md`.
- 13:00 Calcul de rețea vectorizat (Z-bus pe matricea de admitanțe din pandapower): aceleași tensiuni ca `pandapower.runpp` (diferență sub 1e-7 pu) pe toate cele 6 topologii SimBench, un an de ore în 0,002-0,06 s față de 71-95 s cu pandapower.
- 13:02 Prima rețea simulată pe un an (rural3, 52 de prosumatori, 346 kWp): 1.107 ore peste 1,10 pu, 2,7% din energia PV pierdută prin oprirea invertoarelor.
- 13:03 Lotul de antrenare simulat: 480 de posturi sintetice × 33.744 de ore (2023-01-01 → 2026-11-06) în 77 s pe 4 procese. 8,9% din zilele-post depășesc 1,10 pu.
- Teste noi în `tests/c/` (calculul vectorizat față de pandapower, trăsăturile posturilor).

## Urmează (M1, 17:30)
- Realism: scot variantele absurde (creștere liniară de tensiune peste 25% la soare plin).
- Populația de circa 300 de posturi pe hartă (194 de poziții reale din OSM plus poziții sintetice în Ilfov).
- Trăsături, baseline (regresie liniară pe radiație × kW pe kVA), primul LightGBM, test pe topologii nevăzute și luni nevăzute, `reports/C/metrics.json`.
- `predict.py`: `C.jsonl` și serii valide pentru `demo-vara` și `maine`.

## Blocaje
- niciunul. Am nevoie de data pentru `demo-vara` de la firul B până la 15:00 (până atunci folosesc o zi senină din iulie 2025 ca rezervă).

## Cereri către orchestrator
1. `memory/` și prezentarea: cifrele ANRE mai noi sunt **4.019 MW** (nu circa 3.800) și **127.084 de prosumatori cu baterii** (nu peste 101.000), la 30 iun. 2026. Sursa: ANRE prin News.ro, https://startupcafe.ro/romani-panouri-solare-cati-prosumatori-racordare-retelele-electrice-romania-105065. Detalii în `docs/research/C.md`.
2. `config/economics.yaml`, secțiunea `voltage` (o deține planificatorul), chei noi cu sursă:
   - `complaint_compensation_lei: 70` (persoană fizică; 130 lei persoană juridică), Ord. ANRE 46/2021, anexa 4.
   - `quality_limit_95pct_pu: 1.05` (România, de la 1.01.2022: 95% din mediile pe 10 min sub +5%), Ord. ANRE 46/2021, art. 25(2).
   - `ore_smart_midday: "11:00-14:59, 1 martie - 31 octombrie"` (PPC Ore Smart+).
   Până atunci codul C folosește aceleași valori ca implicite, cu sursa în comentariu.
3. Firul B: data pentru `demo-vara`, cât mai devreme.

## Cum se rulează (comenzile exacte)
- `make c-weather` (descarcă meteo; sumele de control în `data/samples/C/checksums.sha256`)
- `make c-bench` (verificare față de pandapower și timpi, scrie `reports/C/powerflow_bench.json`)
- `uv run python -m cyberpunks.c_prosumatori.simulate one` (prima rețea, un an)
- `make c-sim` (lotul de antrenare, cel mult 4 procese, circa 80 s)
- `make c-test`

## Cifre (doar din scripturi, cu comanda)
- Diferența maximă față de pandapower: 5,2e-08 pu; pandapower 8-11 ms pe oră simulată; vectorizat 0,001-0,006 ms (`make c-bench`).
- Lot de antrenare: 675.360 de zile-post, 8,85% peste 1,10 pu, 49,6% peste 1,05 pu (`make c-sim`, apoi analiza din `daily.parquet`).

## Decizii (cu ora)
- 12:47 Simulările rulează cu cel mult 4 procese.
- 12:58 Rezoluție orară (meteo Open-Meteo e orară). Normele cer medii pe 10 minute: aproximare scrisă în model card.
- 13:00 Etichetele vin din calculul vectorizat pe matricea pandapower, verificat față de `pandapower.runpp`; fără el, 480 de posturi × 4 ani ar fi luat circa 10 ore.
- 13:00 Producția PV din meteo românesc (Open-Meteo, panou spre sud la 30°, calibrat pe PVGIS 1.282 kWh/kWp), nu din profilele germane SimBench (circa 650 kWh/kWp).
- 13:05 Pragul de risc 1,10 pu (deconectarea invertoarelor, limita de 100%); orele peste 1,05 pu se raportează separat (limita românească de 95%).
- 13:08 Priza și tensiunea pe MT sunt legate: tensiunea fără sarcină pe JT rămâne între 0,99 și 1,075 pu (IPOTEZĂ).
