# Bilanț pe post: date, ipoteze, comenzi

**Simulare pe date publice, gândită pentru datele PPC.** Nicio cifră de aici nu e măsurată pe rețeaua Rețele Electrice. Problemele din date sunt ascunse de noi și etichetate din construcție.

## Comenzile, în ordine (dintr-o clonă curată)

Verificat pe 7 nov. 2026 într-o clonă curată a branch-ului (vezi „Verificarea dintr-o clonă curată” mai jos).

```bash
uv sync
make c-weather          # meteo Open-Meteo 2023-2026 în data/raw/C (firul C), o singură dată, ~30 s, rețea
make bilant-data        # lumea simulată: 600 de posturi, 373 de zile, ~1 minut, 4 procese
                        # (lotul hărții citește outputs/work_items/demo-vara/A_ground_truth.csv; dacă lipsește,
                        #  rulează singur `cyberpunks.a_contoare.predict --scenario demo-vara`)
make bilant-eval        # ~6 minute: modelele (models/bilant/), reports/bilant/metrics.json, figurile, planul B,
                        # analiza erorilor
make bilant-predict     # outputs/work_items/demo-vara/A_bilant.jsonl, seriile, starea pentru fuziune
                        # (citește A.jsonl, dacă există, ca să nu dubleze lucrările lui A), apoi
                        # reports/bilant/demo_posts.md și reports/bilant/headline.md (au nevoie de lucrări)
make bilant-test        # testele firului (tests/bilant/)
```

Varianta v2 (7 nov., 22:10-23:00; v1 rămâne rezervă și nu se șterge):

```bash
make bilant-v2          # 2 loturi mari de ~3.000 de posturi (trainL: diagnostic; trainLA: fuziune, cu defectele de
                        # contor ca la A, apărute în ultimele 60 de zile), căutarea Optuna; ~30 de minute, 8 procese
make bilant-eval        # folosește v2 dacă există reports/bilant/v2_params.json și lotul trainL, altfel v1
make bilant-predict
```

Ce intră în git din v2: doar setările (`reports/bilant/v2_params.json`, `reports/bilant/fusion_v2_params.json`) și comparațiile (`v2_comparison.json`, `fusion_v2_comparison_*.json`). Modelul de diagnostic v2 are ~34 MB și loturile mari ~1 GB: rămân în afara git (regula de 5 MB) și se refac din comenzi.

Validare: `uv run cyberpunks validate reports/bilant/metrics.json outputs/work_items/demo-vara/A_bilant.jsonl`.

`cyberpunks.a_bilant.predict.run(scenario, date)` reface singur lotul și modelele dacă lipsesc (așa îl apelează planificatorul).

Ce iese și unde:

| Fișier | Ce e |
|---|---|
| `reports/bilant/metrics.json` | ModelReport (sursa A, `bilant-lgbm`): pierderea normală, diagnosticul, fuziunea, cauzele de post |
| `reports/bilant/headline.md` | cifrele pentru prezentare, generate din `metrics.json` și din lucrarea postului demo (de `make bilant-predict`) |
| `reports/bilant/model_card.md`, `error_analysis.md`, `plan_b.md`, `demo_posts.md` | fișa modelului, erorile, planul B, posturile pentru demo |
| `reports/bilant/*.png` | figurile |
| `outputs/work_items/<s>/A_bilant.jsonl`, `outputs/series/<s>/A-*-PT-*.json` | lucrările și seriile pentru planificator și interfață |
| `outputs/bilant/<s>/posts_<data>.json` | starea fiecărui post, citită de `fuse.fuse` |

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
5. Contorul de balanță al postului (pe joasă tensiune): energia netă ieșită spre clienți (consum minus injecția prosumatorilor), cu o eroare fixă N(0; 0,07%). La jumătate din posturi (IPOTEZĂ) există și un **contor martor** (Codul de măsurare ANRE, Ord. 103/2015: măsoară în paralel, pe aceleași circuite), cu eroarea lui fixă N(0; 0,07%), neatins de setarea greșită a contorului de balanță. Diferența normală dintre ele are abaterea standard ~0,1%, cât a spus mentorul PPC. Regula din `martor.py`: diferența pe ultimele 3 zile peste 0,5% (clasa de exactitate) înseamnă contor de balanță defect sau setat greșit. Pragul de 0,1-0,5% nu se aplică bilanțului post − clienți, unde pierderea normală e de câteva procente.
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

## Verificarea de realism cu date reale (Weave, UK)

`uv run python -m cyberpunks.a_bilant.weave_check` descarcă mostra Weave (o zi, 2024-02-12, ~38 MB, în `data/raw/bilant/weave/`, în afara git; sha256 `b4f4717e929d7c9bf1cbc1d8bf99c954cede6b2237fb0d6810820f2d22e8729c`) și compară forma zilnică a curbelor a ~42.000 de posturi reale din UK cu cele 300 de posturi simulate (`reports/bilant/weave_check.md`, `.png`). Weave e folosit doar ca reper pentru formă, citat; licența nu e declarată, deci nu intră în antrenare și nu dă etichete. Fișierul complet (~700 MB) nu e descărcat. Folosirea Weave pentru profilele de încărcare din simulare rămâne o îmbunătățire viitoare.

## Experiment separat cu date reale FeederBW (ramura Eden, 8 nov. 2026)

Sursa: **Netze BW și KIT, FeederBW**, [Zenodo, versiunea fixată 1.0](https://zenodo.org/records/17831177),
CC BY 4.0. Citare: Treutlein et al., *Scientific Data* 13, 1283 (2026),
[doi:10.1038/s41597-026-08152-9](https://doi.org/10.1038/s41597-026-08152-9).
Datasetul complet conține 200 de plecări JT din Germania, aprilie 2023–martie 2025, la un minut.
Experimentul folosește primul lot oficial, plecările 1–40 (~1,7 GB comprimat).

**Reală este numai forma importului orar.** Puterea netă măsurată se agregă la oră (minimum 45 de minute
valide), exportul se taie la zero, iar forma se normalizează și se scalează la clienții simulatorului.
Golurile se completează numai din trecut: aceeași oră din săptămâna precedentă, apoi ultima valoare.
Rețelele, clienții, scara energiei, PV, pierderile și toate etichetele rămân **SINTETICE**.
Vremea este cea din București; nu pretindem sincronizare cu vremea germană. FeederBW nu oferă perechea
contor de balanță / total complet al contoarelor clienților sau verdicte reale de furt și defect.

```bash
uv run python -m cyberpunks.a_bilant.feederbw download
uv run python -m cyberpunks.a_bilant.feederbw prepare --workers 4
uv run python -m cyberpunks.a_bilant.feederbw tune --trials 40 --workers 4
```

În rularea din 8 nov., **38 de plecări sunt valide**; 34 și 38 sunt excluse pentru peste 10% ore lipsă
(1.272 și respectiv 1.171 din 8.712). Au fost completate cauzal 1.068 de ore din cele 331.056 ale surselor
valide. Exportul a fost tăiat în 20.418 ore. Manifestul păstrează verificările pentru fiecare sursă.

Antrenare / validare / test pe **22 / 8 / 8 plecări reale distincte** (170 / 65 / 65 posturi simulate), seed fix; toate copiile sintetice
ale aceleiași plecări, cartierele și perechile de clienți mutați rămân în aceeași parte. Perioada comună:
2 aprilie 2024–30 martie 2025. Testul este spațial, nu pe date din viitor. Normalul folosește parametrii
existenți, cu predicții out-of-fold pe plecări reale pentru antrenarea diagnosticului. Optuna caută cele 8
setări LightGBM ale diagnosticului după macro-F1 pe validare, cu aceleași reguli de pereche și martor folosite
la test. Comparația de bază reantrenează setările v2 pe exact aceleași rânduri și trăsături. Nu se promovează
automat rezultatul în modelul livrat. Intervalul bootstrap 90% re-eșantionează plecări reale, nu ferestre.

Date: `data/raw/bilant/feederbw/`, lotul și predicțiile: `data/processed/bilant/feederbw_import_v1/`,
modele: `models/bilant/experiments/feederbw_*` (toate în afara Git). Proveniența, splitul și SHA256:
`data/samples/bilant/feederbw_manifest.json`. Raport: `reports/bilant/feederbw_optuna.json`.
Aceste rezultate nu măsoară performanța pe pierderi reale sau pe date PPC.

Rezultatul celor 40 de încercări: F1 macro test **0,70858 → 0,71393**; diferență +0,00535,
interval bootstrap 90% **[-0,00618; +0,01769]** pe plecări reale. Câștigul nu este confirmat statistic;
modelul FeederBW a fost retras din rularea implicită la cererea utilizatorului și rămâne disponibil pentru comparații.
Rezumat: `reports/bilant/feederbw_optuna.md`.

Pachetul activ este `models/release/bilant-v2/`: diagnosticul v2 anterior, refăcut din setările salvate,
și modelele P10/P50/P90 warm/cold corespunzătoare. `predict` le încarcă direct și într-o clonă curată.
Pachetul FeederBW rămâne în `models/release/bilant/` doar pentru comparații, nu este încărcat la predicție.
Ambele pachete au sume SHA256 în `release.json`. Cifrele din `reports/bilant/metrics.json` sunt din
evaluarea istorică; v2 reconstruit reproduce F1 și eroarea pierderii normale din acea evaluare.
Fuziunea cu modelul FeederBW nu a fost validată separat. Datele și etichetele de bilanț rămân sintetice.

Verificare suplimentară a candidatului FeederBW pe harta simulată: F1 macro **0,58950** pe 13.200 de ferestre,
eroare medie a pierderii normale **8,81 kWh/zi**, acoperire P10–P90 **0,695**. Pe aceleași 13.200 de ferestre,
v2 reconstruit obține F1 **0,75352**, MAE **5,40 kWh/zi** și acoperire **0,881**. Comparația pereche, cu etichete
sintetice, este în `reports/bilant/comparatie_v2_feederbw.json`; reproducere:
`uv run python -m cyberpunks.a_bilant.feederbw compare-v2`. Rezultatul separat FeederBW:
`reports/bilant/feederbw_release_pop.json`,
`uv run python -m cyberpunks.a_bilant.feederbw evaluate-feederbw`.

## Adaptarea pe date PPC

- Lumea simulată se înlocuiește cu datele reale: contorul de balanță la 15 minute, contoarele clienților, lista client → post, GIS-ul. Modelele și trăsăturile rămân.
- Eticheta pierderii normale e lipsa măsurată în perioadele verificate. Etichetele diagnosticului vin din verdictele echipelor după vizită (`feedback.py`).
- De întrebat la mentor: câte posturi au azi contor de balanță (concentratorul de date nu e contor de balanță)? Cât de bună e lista client → post?

## Verificarea dintr-o clonă curată (7 nov. 2026, 16:10)

`git clone --branch Teo-bilant` într-un director gol, apoi exact comenzile de mai sus, de la `uv sync` la `make bilant-test`. Toate au mers fără intervenție, în ~10 minute. Rezultatul:
- `reports/bilant/metrics.json`: toate cele 142 de cifre identice cu cele din repo;
- `A_bilant.jsonl` pentru demo-vara: aceleași 78 de lucrări, cu aceleași acțiuni;
- testele firului trec (25).

Lucrările depind de `A.jsonl`: bilanțul nu dublează posturile unde A are deja lucrări. Cu altă versiune a lui A, numărul de lucrări de bilanț se poate schimba, dar metricile nu.
