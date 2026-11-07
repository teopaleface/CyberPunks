# Datele firului C: prosumatori și tensiune prea mare în posturile de transformare

Tot ce intră în modelul C, de unde vine, ce e real și ce e sintetic, și cum se reface din nimic.

## Pe scurt

- **Real și public:** vremea (Open-Meteo, CC BY 4.0), pozițiile a 191 de posturi din OpenStreetMap (ODbL), topologiile și profilele de consum SimBench (ODbL), cifrele ANRE folosite la calibrare.
- **SINTETIC:** fiecare post de transformare din demo (rețeaua din spate, prosumatorii, bateriile, priza, codul PT-xxxx), 109 din cele 300 de poziții și toate etichetele (tensiunea maximă, kWh pierduți), care vin din simularea fizică. Câmpul `synthetic` e `true` în fiecare lucrare și în fiecare serie.
- **Nicio dată personală.** Nu există clienți reali, adrese sau consumuri reale.

## Surse

| Sursa | Ce luăm | Licență, atribuire | Cum se descarcă | Fișier (în afara git) |
|---|---|---|---|---|
| Open-Meteo Historical Weather API (ERA5) | vremea orară 2023-01-01 → 2026-11-06 la 44,45 N 26,05 E: radiație globală, directă, difuză, pe panou înclinat 30° spre sud (GTI), temperatură, nori | CC BY 4.0, „Weather data by Open-Meteo.com” | `make c-weather` | `data/raw/C/openmeteo_archive_utc_2023-01-01_2026-11-06.json` |
| Open-Meteo Forecast API | prognoza pentru scenariul `maine` | CC BY 4.0 | automat în `predict.py` | `data/raw/C/openmeteo_forecast_utc_<zi-1>_<zi+1>.json` |
| OpenStreetMap, prin Overpass API | posturi de distribuție (`power=substation` minor_distribution / distribution / fără subtip, `power=transformer`, stâlpi cu transformator) în bbox-ul demo (44,25-44,65 N, 25,85-26,40 E) | ODbL, „© OpenStreetMap contributors” | automat în `population.py` dacă fișierul lipsește | `data/raw/C/osm_power_bbox.json` |
| SimBench 1.6.3 (pachetul Python) | 6 rețele de joasă tensiune (`1-LV-rural1/2/3`, `1-LV-semiurb4/5`, `1-LV-urban6`, scenariul 0, fără întrerupătoare), profilele de consum H0 și G la 15 minute (2016) | date ODbL, cod BSD; Meinecke et al., Energies 13(12):3290, 2020 | instalat cu `uv sync` | în pachet |
| PVGIS 5.3 (JRC) | doar ca verificare: producția anuală pe kWp în Ilfov (1.282 kWh/kWp, 2005-2023) | reutilizare cu citarea sursei | descărcat o dată în faza 0 | `data/raw/C/pvgis_seriescalc_v5_3_44.45_26.05.json` |
| ANRE (prin News.ro), 30 iun. 2026 | calibrare: 6,4 kW media pe prosumator persoană fizică, 127.084 din 359.378 au baterii | citat în `docs/research/C.md` | — | — |

Sumele de control ale descărcărilor sunt în `data/samples/C/checksums.sha256` (prognoza se schimbă zilnic, deci suma ei se schimbă la fiecare descărcare).

Convenții de timp: totul e în UTC, „ora care se încheie” (valoarea de la ora H e media intervalului H-1..H, ca la Open-Meteo). Ziua locală (Europe/Bucharest) se calculează din începutul orei.

## Cum se construiesc datele (pașii, în ordine)

1. **Vremea** (`weather.py`): arhiva Open-Meteo în UTC. Producția pe kWp: `GTI/1000 × 0,86 × (1 − 0,0037 × (T_celulă − 25))`, cu `T_celulă = T_aer + 0,03125 × GTI`. Dă 1.362-1.382 kWh/kWp pe an pentru un panou spre sud; cu orientările mixte ale caselor (factor mediu 0,92) iese circa 1.270, aproape de PVGIS (1.282).
2. **Consumul** (`profiles.py`): profilele SimBench mediate pe oră și normate (suma pe 2016 = 1). Fiecare zi țintă ia ziua din 2016 cu aceeași zi a săptămânii, cât mai aproape de aceeași dată. Sărbătorile legale românești (inclusiv Paștele și Rusaliile ortodoxe) se tratează ca duminici. Consumul anual al unei case: lognormal, media postului în jur de 2.500 kWh (**IPOTEZĂ**: case din Ilfov, peste media națională).
3. **Posturile sintetice** (`grids.py`): fiecare post e o variantă a unei topologii SimBench:
   - transformator 20/0,4 kV de 100-630 kVA (tipurile SimBench; 100 kVA e IPOTEZĂ);
   - conductor: NAYY 150 sau 95 (cablu), TYIR 70 sau 50 (torsadat aerian), Al 35 vechi, cu probabilități pe tip de zonă (IPOTEZĂ);
   - linii de 0,6-2 ori mai lungi decât în SimBench;
   - priza pe MT −2..+2, legată de tensiunea pe MT, ca tensiunea fără sarcină pe JT să rămână între 0,99 și 1,075 pu (IPOTEZĂ). Comutatorul e declarat `Ratio`, altfel pandapower 3.x ignoră priza;
   - prosumatori: o parte din case, 3-15 kWp (media circa 6,8 kW, calibrată pe ANRE), invertoare de 85-100% din kWp, orientări mixte; uneori și o firmă cu 15-50 kWp;
   - baterii la o parte din prosumatori (în jur de 35%, ANRE), 5/10/15 kWh, autoconsum;
   - tensiunea pe MT variază în timpul zilei (urcă la soare, scade la consum), cu coeficienți pe care modelul nu îi vede;
   - limite de realism: rețelele în care panourile ar ridica tensiunea cu peste 25% la soare plin sau consumul mediu ar coborî-o cu peste 4% se îmblânzesc (mai puțini prosumatori, linii mai scurte).
4. **Etichetele din fizică** (`powerflow.py`, `simulate.py`): pandapower construiește matricea de admitanțe a fiecărui post; calculul vectorizat (Z-bus) rezolvă toate orele deodată și dă aceleași tensiuni ca `pandapower.runpp` (diferență maximă 5e-8 pu, `make c-bench`). Pentru fiecare oră: tensiunea maximă și minimă pe JT, încărcarea transformatorului, exportul. În orele cu depășiri se simulează cascada de opriri ale invertoarelor (se oprește cel mai expus, se recalculează), iar energia lor e „kWh pierduți” (limită de sus: un invertor oprit rămâne oprit toată ora).
5. **Lotul de antrenare**: 480 de posturi (80 pe topologie), plaje largi de parametri, 33.744 de ore fiecare. Circa 80 de secunde pe 4 procese.
6. **Populația demo** (`population.py`): 300 de posturi, 191 pe poziții OSM și 109 sintetice în jurul localităților din Ilfov. Zona: în raza de 8,5 km de centru, cel mai apropiat sector; în afară, cea mai apropiată localitate din Ilfov. Topologia după tipul zonei (urban, semiurban, rural). Parametri realiști: puțini prosumatori la blocurile din București, mulți la casele din Ilfov. Registrul e în git: `data/samples/C/posts_population.csv` (scurt) și `posts_population_full.csv` (tot ce trebuie pentru `predict.py`).
7. **Trăsăturile** (`features.py`): ce poate ști distribuitorul (GIS, avize de racordare, prognoza meteo), fără rețeaua detaliată a fiecărei case. Lista și eticheta în română a fiecărei trăsături sunt în `features.py` (`FEATURE_LABELS_RO`).

## Scara de soluții și rapoartele (după model)

- **Scara de soluții** (`remedies.py`): pentru fiecare post cu P90 peste 1,10 pu, simularea fizică a postului în ziua țintă se rulează de bază și cu fiecare soluție; efectul (în pu) se aplică peste P90 al modelului. Treptele: 3 case mutate pe altă fază (dezechilibru estimat analitic, plafonat la 0,02 pu după EN 50160), o treaptă de priză, mesaje de grup (participare 10/20/30%, consumul mutat din seară, aceeași energie), baterii 5/10/15 kWh pe profilul fiecărui prosumator, limită de export, post nou. Costurile vin din `config/economics.yaml` (secțiunile `voltage` și `remedies`).
- **Ofertele de baterii** (`reports_c.py offers`): pe profilul anual (2025) al fiecărui prosumator de pe posturile cu risc; economia = energia livrată seara × prețul de cumpărare − energia PV folosită la încărcare × valoarea ei; grantul Casa Verde Baterii 2026 din config.
- **Investițiile** (`reports_c.py investments`): modelul pe toate zilele din 2025 pentru fiecare post, apoi scara pe cea mai însorită zi de referință.
- **Cererile de racordare** (`connection.py`): modelul înainte și după racordare pe cele mai însorite 15 zile din sezonul 2025 și pe tot anul, plus calculul de rețea pentru limita de injecție.

## Împărțirea pentru evaluare

- **Rețele nevăzute:** leave-one-topology-out pe cele 6 topologii SimBench. Fiecare topologie e prezisă de modele antrenate doar pe celelalte 5.
- **Luni nevăzute:** antrenare pe zilele dinainte de 2025-01-01, test pe 2025-01-01 → 2026-11-06.
- **Calibrarea** (izotonică pentru probabilitate, conformal pentru interval) folosește tot predicții pe topologii nevăzute, făcute doar pe topologiile de antrenare ale fold-ului.
- **Ziua demo** (`demo-vara`, 2025-07-08) și cele 3 zile dinainte și de după sunt scoase din antrenarea modelului final.

## Comenzile exacte

```
uv sync
make c-all          # tot: vreme, simulare, populație, model, lucrări, evaluare (circa 15 minute, 4 nuclee)
# sau pas cu pas:
make c-weather      # Open-Meteo 2023-2026
make c-bench        # verificare față de pandapower și timpi
make c-sim          # 480 de posturi de antrenare
make c-population   # 300 de posturi demo
make c-train        # models/C/bundle.joblib
make c-predict      # outputs/work_items/{demo-vara,maine}/C.jsonl și seriile
make c-eval         # reports/C/metrics.json, metrics_detail.json, figurile
make c-test
uv run cyberpunks validate outputs/work_items/demo-vara/C.jsonl
uv run python -m cyberpunks.c_prosumatori.evaluate --rescore --hourly   # și modelul orar (circa 12 minute)
uv run python -m cyberpunks.c_prosumatori.evaluate --speed-only         # viteza față de pandapower
uv run python -m cyberpunks.c_prosumatori.evaluate --ablation fara_fizica
uv run python -m cyberpunks.c_prosumatori.error_analysis                # reports/C/error_tables.json
uv run python -m cyberpunks.c_prosumatori.reports_c investments         # reports/C/investitii.md
uv run python -m cyberpunks.c_prosumatori.connection --post PT-1020 --kwp 25
```

Dintr-o clonă curată, `predict.py` merge și fără pașii grei: modelul e în `models/release/C/`, registrul posturilor în `data/samples/C/posts.csv`, mostra pentru cazurile similare în `data/samples/C/similar_cases.parquet`; vremea se descarcă de la Open-Meteo.

## Ce iese

| Fișier | Contract | În git |
|---|---|---|
| `outputs/work_items/<scenariu>/C.jsonl` | `WorkItem` | nu (îl copiază planificatorul în `outputs/demo/`) |
| `outputs/series/<scenariu>/<id>.json` | `Series` | nu |
| `outputs/work_items/<scenariu>/C_summary.json` | liber: câte posturi, câte lucrări pe acțiune, vremea, motivul în cuvinte | nu |
| `reports/C/metrics.json` | `ModelReport` | da |
| `reports/C/metrics_detail.json` | liber: pe topologie, zile cu soare, model necalibrat | da |
| `reports/C/figures/*.png` | — | da |
| `reports/C/powerflow_bench.json` | liber: verificarea față de pandapower | da |
| `outputs/work_items/<scenariu>/C_battery_offers.csv` | liber: ofertele de baterii pe prosumator | nu |
| `reports/C/oferte_baterii.md`, `investitii.md`, `error_analysis.md`, `model_card.md`, `README.md` | rapoarte | da |
