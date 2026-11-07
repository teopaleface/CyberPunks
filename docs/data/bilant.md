# Bilanț pe post: date, ipoteze, comenzi

**Simulare pe date publice, gândită pentru datele PPC.** Nicio cifră de aici nu e măsurată pe rețeaua Rețele Electrice. Problemele din date sunt ascunse de noi și etichetate din construcție.

## Comenzile, în ordine (dintr-o clonă curată)

```bash
uv sync
make c-weather          # meteo Open-Meteo 2023-2026 în data/raw/C (firul C), o singură dată
make bilant-data        # lumea simulată: 600 de posturi, 373 de zile (~1 minut, 4 procese)
make bilant-eval        # modelele, reports/bilant/metrics.json, figurile, planul B, analiza erorilor (~5 minute)
make bilant-predict     # outputs/work_items/demo-vara/A_bilant.jsonl, seriile, starea pentru fuziune
uv run python -m cyberpunks.a_bilant.demo_story   # reports/bilant/demo_posts.md
make bilant-test
```

`cyberpunks.a_bilant.predict.run(scenario, date)` reface singur lotul și modelele dacă lipsesc.

## Sursele

| Ce | Sursa | Licență |
|---|---|---|
| Rețelele de joasă tensiune (6 topologii) și profilele de consum | SimBench `1-LV-*`, prin firul C (`cyberpunks.c_prosumatori.grids`, `profiles`) | ODbL |
| Variantele sintetice ale rețelelor (transformator, conductori, lungimi, prosumatori, baterii) | firul C, din seed | sintetic |
| Pozițiile posturilor de pe hartă | registrul C (`cyberpunks.c_prosumatori.posts`), OpenStreetMap | ODbL |
| Meteo orară București-Ilfov, 2024-07-01 … 2025-07-08 | Open-Meteo archive (firul C, `weather.archive`) | CC BY 4.0 |
| Calculul de rețea | firul C, `powerflow.GridModel` (Z-bus vectorizat pe matricea pandapower) | cod propriu |
| Defectele și manipulările de contor | firul A, `a_contoare.inject.inject` (zero, stuck, negative, h1, bypass) | cod propriu |
| Reperele de pierderi (CPT) | Plan RER 2024-2033 și 2026-2035, Ord. ANRE 67/2024 (`docs/research/bilant_lit.md`) | public |

## Lumea simulată (`src/cyberpunks/a_bilant/world.py`)

Pentru fiecare post, fiecare oră:

1. Consumul fiecărui client: profil SimBench × consum anual (firul C), cu variație proprie (lognormală, σ = 0,25, IPOTEZĂ). Producția panourilor și bateriile sunt ca la C.
2. Calculul de rețea al lui C dă tensiunile. Din ele, curentul pe fiecare cablu și pierderea `|I|²·R`.
3. Corecțiile pierderii pe cabluri:
   - fazele: `× (1 + 1,09·(D + 9S/(0,18·N)))`, ajustată pe 768 de rulări `pandapower.runpp_3ph` (`docs/research/bilant_faze.md`); D = Σ(3p−1)², S = Σp(1−p), p = cota de case pe fază, N = numărul de case;
   - variația din interiorul orei: × 1,3 (IPOTEZĂ);
   - calibrarea: × 2,5, cu ±35% între posturi (lognormală; IPOTEZĂ). Acoperă ce nu are SimBench: branșamente, îmbinări vechi, conductori îmbătrâniți. Cu ea, mediana pierderii tehnice ajunge la 3,8% din energia care trece prin post. Reperul: CPT Muntenia 8,66% în 2023, din care 63,54% pe joasă tensiune; CPT-ul include și pierderile comerciale.
4. Consumul propriu al contoarelor, nemăsurat: 1,5 W pe contor (IPOTEZĂ; IEC 62053-21 permite până la 2 W).
5. Contorul de bilanț al postului (pe joasă tensiune): energia netă ieșită spre clienți (consum minus injecția prosumatorilor), cu o eroare fixă N(0; 0,2%) (clasa 0,5S, IPOTEZĂ).
6. Contoarele clienților: energia netă (bidirecționale la prosumatori), cu eroare fixă N(0; 0,4%) (clasa 1, IPOTEZĂ), rotunjite la 0,001 kWh. 3% din contoare au 1-3 goluri de comunicație de 1-5 zile, completate din aceeași oră de acum 7 zile.
7. Tensiunea măsurată în contor: tensiunea nodului plus zgomot N(0; 0,002 pu). Posturile din același cartier au o variație comună pe medie tensiune (AR(1)).
8. Comportamente benigne, care schimbă consumul real: concediu (3% din clienți, 7-21 de zile la 15% din consum) și ocupare schimbată (1%, ×0,5 sau ×1,5 permanent).

## Problemele ascunse (`problems.py`)

Primele 60 de zile sunt curate (istoricul postului). Apoi:

| Clasă | Ce simulăm | Cât de des (IPOTEZĂ) |
|---|---|---|
| contor de client | defect (zero, blocat, negativ) sau manipulat (h1, bypass), din generatorul lui A | 1,2% din contoare |
| furt înainte de contor | 0,3-2 kW medii nemăsurați, constant sau cu profil de casă, de la o zi | 30% din problemele de post |
| pierdere tehnică | o fază ia 55-80% din case, sau rezistență ×1,8-3,5 (îmbinare degradată) | 30% |
| client la postul greșit | un client al postului X apare în bază la vecinul Y | 25% |
| contorul postului setat greșit | numără exact ×2 | 15% |

O problemă de post apare la 40% din posturile de antrenare și la 25% din posturile hărții.

## Loturile (`dataset.py`)

- `train`: 300 de posturi sintetice noi, 50 pe topologie, grupate câte 5 în „cartiere” (vecinii).
- `pop`: cele 300 de posturi din registrul C (harta). Vecinii sunt cele mai apropiate 3 posturi. Rețelele nu se văd la antrenare.
- Ieșiri în `data/processed/bilant/<lot>/` (în afara git): `daily.parquet`, `vcorr.parquet`, `posts.parquet`, `hourly.npz`, `cust_daily.npz`, `plans.json` (adevărul), `neighbors.json`, `meta.json`.

## Intrări greșite și date lipsă (`inputs.py`)

Contorul de post lipsă trece postul pe planul B. Orele dublate se curăță. Unitățile Wh se convertesc în kWh. Polaritatea inversată se corectează. Orele lipsă (sub 10% din zi) se completează din ziua precedentă; peste 10%, ziua iese din bilanț. Fiecare corecție apare în `data_quality.input_issues`. În demo, PT-1003 (Wh), PT-1007 (fără contor de post) și PT-1011 (ore dublate) sunt cazuri de test simulate.

## Ce se schimbă pe date PPC

- Lumea simulată se înlocuiește cu datele reale: contorul de bilanț la 15 minute, contoarele clienților, lista client → post, GIS-ul. Modelele și trăsăturile rămân.
- Eticheta pierderii normale e lipsa măsurată în perioadele verificate. Etichetele diagnosticului vin din verdictele echipelor după vizită (`feedback.py`).
- De întrebat la mentor: câte posturi au azi contor de bilanț (concentratorul de date nu e contor de bilanț)? Cât de bună e lista client → post?
