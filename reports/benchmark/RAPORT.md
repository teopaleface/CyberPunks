# Putem bate LightGBM? Benchmark pe bilanț, contoare și furtuni

Ramura `Eden`, 8 noiembrie 2026, 06:00–06:45, ora Bucureștiului. Cerut de Eden. Este un **experiment**: modelele
active din `models/release/` și comportamentul demo-ului nu s-au schimbat (sumele SHA256 din `release.json` au fost
verificate după rulare). Modelul de tensiune la prosumatori (C) nu face parte din benchmark.

## Pe scurt

**Nu am găsit niciun candidat care să bată LightGBM.** Pe fiecare problemă, candidatul fie e la egalitate
statistică (intervalul 90% al diferenței include zero), fie pierde puțin. Recomandarea: rămânem pe LightGBM peste tot.

| Problemă | Test | Candidat | Metrica principală: LightGBM → candidat | Diferența, IC 90% | Verdict |
|---|---|---|---|---|---|
| Bilanț (diagnostice SINTETICE) | testul v2, 13.200 de ferestre | CatBoost | F1 macro 0,7535 → 0,7575 | +0,0040 [−0,0032; +0,0129] | egalitate statistică |
| Bilanț (profile FeederBW reale, diagnostice SINTETICE) | 8 plecări reale nevăzute | CatBoost | F1 macro 0,7139 → 0,7048 | −0,0091 [−0,0315; +0,0037] | egalitate statistică |
| Contoare, SGCC (etichete REALE) | 20% din clienți | CatBoost | PR-AUC 0,3994 → 0,3947 | −0,0047 [−0,0170; +0,0080] | egalitate statistică |
| Contoare, LCL de bază (probleme INJECTATE) | 265 de gospodării nevăzute | CatBoost | PR-AUC subtil 0,4057 → 0,4174 | +0,0117 [−0,0335; +0,0488] | egalitate statistică |
| Contoare, LCL extins (probleme INJECTATE) | același test | CatBoost | PR-AUC subtil 0,5175 → 0,4889 | **−0,0285 [−0,0461; −0,0123]** | **CatBoost pierde** |
| Furtuni (date REALE, SUA) | anul 2025 | XGBoost | PR-AUC 0,2777 → 0,2738 | **−0,0039 [−0,0064; −0,0012]** | **XGBoost pierde** (puțin) |
| Furtuni, state nevăzute | 8 state, pe rând | XGBoost | PR-AUC mediu 0,2586 → 0,2550 | −0,0036 [−0,0076; +0,0002] | egalitate statistică |
| Furtuni + convecție (experiment separat) | anul 2025 | XGBoost | PR-AUC 0,2865 → 0,2845 | −0,0021 [−0,0047; +0,0005] | egalitate statistică |

Unde un scor mediu mai bun ascunde o scădere:
- **Bilanț, testul v2:** CatBoost are F1 macro mai mare, dar **furtul înainte de contor scade** (0,7710 → 0,7641,
  −0,0069 [−0,0220; +0,0106]); scade și pierderea tehnică (−0,0115). Câștigul vine aproape tot din „contor de client”
  (+0,0240 [+0,0087; +0,0442], singura clasă cu interval peste zero). Mai mult: pe validare, unde se aleg setările,
  CatBoost a ieșit **mai slab** (0,7612 față de 0,7685). După regula „alegem doar pe validare”, LightGBM rămâne oricum.
- **Contoare, LCL de bază:** precizia în top 1% pe anomaliile subtile crește (0,625 → 0,703), dar intervalul e foarte
  larg (+0,078 [−0,086; +0,213]); la K = 382 CatBoost e mai slab (0,471 → 0,458). Nu e câștig sigur.
- **Furtuni, 2025:** XGBoost are recall puțin mai mare la prag (0,409 → 0,427), dar pentru că dă mai multe alerte
  (15,1 → 15,9 la 100 de zone-zile). La același buget de echipe acoperă la fel de mulți clienți afectați
  (0,1671 → 0,1654, −0,0018 [−0,0121; +0,0080]).

## Reproducerea referinței LightGBM

Înainte de orice comparație, scorul LightGBM din rapoartele existente a fost refăcut cu codul existent. **Toate
cifrele coincid exact**, deci nu există diferențe de date, split sau pipeline de explicat.

| Referință | Raport existent | Reprodus | Sursă |
|---|---:|---:|---|
| Bilanț v2, F1 macro (pachetul `models/release/bilant-v2`) | 0,75352 | 0,75352 | `reports/bilant/v2_comparison.json` |
| Bilanț v2 reantrenat din `v2_params.json` | — | 0,75352, etichete identice 100% | aceleași ferestre `trainL` |
| FeederBW, LightGBM cu setările v2 | 0,70858 | 0,70858 | `reports/bilant/feederbw_optuna.json` |
| FeederBW, LightGBM optimizat (40 de încercări) | 0,71393 | 0,71393 | idem |
| SGCC, PR-AUC / precizia la K=85 | 0,3994 / 0,800 | 0,3994 / 0,800 | `reports/A/metrics_full.json` |
| LCL de bază, PR-AUC / subtil / top 1% subtil | 0,6778 / 0,4057 / 0,625 | identice | `reports/A/metrics_full.json` |
| LCL extins, PR-AUC / subtil / top 1% subtil | 0,7344 / 0,5175 / 0,8906 | identice | `reports/A/experiments_extra.json` |
| Furtuni 2025, PR-AUC / Brier / clienți acoperiți | 0,2777 / 0,0841 / 0,1671 | identice | `reports/B/metrics.json` |
| Furtuni, state nevăzute, PR-AUC mediu | 0,2586 | 0,2586 | `reports/B/metrics.json` |
| Furtuni cu convecție, PR-AUC (bază / convecție) | 0,2777 / 0,2865 | identice | `reports/B/experiments_extra.json` |

## Reguli respectate

- **Aceleași intrări, etichete și exemple de test** pentru ambele modele în fiecare comparație. Codul de pregătire,
  ferestrele, calibrarea și metricile sunt refolosite din `a_bilant`, `a_contoare`, `b_furtuna`. Nu am schimbat
  niciun fișier din aceste module.
- **Buget de căutare comparabil și ales doar pe antrenare/validare:**
  - bilanț v2: LightGBM, 40 de încercări Optuna (`v2.py`). CatBoost, 40 de încercări Optuna, cu același obiectiv
    (F1 macro pe argmax) și aceeași validare (20% din cartierele `trainL`, `v2.split_by_cluster`);
  - FeederBW: LightGBM, 40 de încercări (`feederbw.tune`). CatBoost, 40 de încercări, cu același obiectiv
    (F1 macro după regulile de decizie) și aceleași 8 plecări de validare;
  - contoare: **zero încercări pentru ambele**. LightGBM folosește setările livrate (Optuna cu 30 de încercări nu le-a
    bătut, `reports/A/tuning_optuna.json`). CatBoost folosește setările echivalente, fixate înainte de a vedea testul:
    pas 0,03, 3.000 de arbori cu oprire după 100, 80% din rânduri și coloane, clase echilibrate, adâncime 6, L2 = 3;
  - furtuni: LightGBM, grila de 24 de configurații pe PR-AUC OOF (`b_furtuna/tune.py`). XGBoost, o grilă de 24 de
    configurații cu aceeași structură (adâncime 3/4/5 × greutate minimă 4/10 × pas 0,02/0,04 × 300/600 de arbori),
    aleasă pe PR-AUC OOF din 2023–2024. A ieșit: adâncime 4, greutate minimă 4, pas 0,04, 300 de arbori
    (OOF 0,2905, față de 0,2916 la LightGBM).
- **Aceleași reguli după clasificare** la bilanț (`v2.full_decision`: abținere, regula perechii, regula contorului
  martor). **Aceeași calibrare**: Venn-ABERS și conformal pe setul de calibrare la contoare; izotonic pe OOF
  (5 fold-uri pe săptămâni) la furtuni. **Aceleași constrângeri monotone** la furtuni, iar pragul de alertă este
  ales din OOF-ul calibrat.
- **Bootstrap 90% pe grupuri** (1.000 de reeșantionări; 500 la statele nevăzute): cartierul postului (31) la bilanț
  v2; plecarea reală (8) la FeederBW; clientul la SGCC; gospodăria (265) la LCL; săptămâna ISO din 2025 (53) la furtuni.
  Diferența este întotdeauna candidat − LightGBM.

## Detalii pe problemă

Tabelele complete, cu F1 pe fiecare clasă, ambele matrice de confuzie, toate valorile K, statele una câte una și
calibrarea, sunt în [`tabele.md`](tabele.md), generat din JSON.

### 1. Bilanț pe post (CatBoost vs LightGBM v2)

**Toate diagnosticele sunt SINTETICE**: rețelele, clienții, pierderile, furtul și defectele vin din simulator. Pe
FeederBW, **numai forma importului orar** al celor 38 de plecări germane (Netze BW / KIT, CC BY 4.0) e măsurată
real; scara, clienții, PV, vremea (București) și toate etichetele rămân simulate.

| | Testul v2: LightGBM | Testul v2: CatBoost | FeederBW: LightGBM optimizat | FeederBW: CatBoost |
|---|---:|---:|---:|---:|
| F1 macro | 0,7535 | 0,7575 | 0,7139 | 0,7048 |
| F1 normal | 0,9270 | 0,9301 | 0,8554 | 0,8452 |
| F1 contor de client | 0,4721 | 0,4961 | 0,6083 | 0,5872 |
| **F1 furt înainte de contor** | **0,7710** | **0,7641** | **0,4686** | **0,4573** |
| recall furt / precizie furt | 0,736 / 0,810 | 0,744 / 0,785 | 0,409 / 0,548 | 0,418 / 0,505 |
| F1 pierdere tehnică | 0,4882 | 0,4767 | 0,5483 | 0,5206 |
| F1 client la postul greșit | 0,8713 | 0,8847 | 0,8101 | 0,8187 |
| F1 contor de bilanț setat greșit | 0,9915 | 0,9931 | 0,9929 | 1,0000 |
| F1 macro pe validare | 0,7685 | 0,7612 | 0,6405 | 0,6269 |

- Furtul înainte de contor: pe ambele teste, CatBoost are recall puțin mai mare, dar precizie mai mică. F1 scade cu
  −0,0069 [−0,0220; +0,0106] pe testul v2 și cu −0,0113 [−0,1105; +0,0270] pe FeederBW. Furturile ratate ajung în
  principal la „contor de client” (v2: 140 la LightGBM, 120 la CatBoost; FeederBW: 67 și 72).
- Pe FeederBW, cu numai 8 plecări de test, intervalele sunt foarte largi. CatBoost e sub LightGBM optimizat pe patru
  clase și peste el pe două, fără nicio diferență sigură. Față de LightGBM cu setările v2, fără căutare pe FeederBW,
  diferența e −0,0038 [−0,0288; +0,0133].
- Fără căutare, CatBoost cu setările implicite de pornire dă doar 0,7210 pe testul v2: căutarea contează mult.
- Abținerea („nu sunt sigur”) pe testul v2: 14,5% din ferestre la LightGBM și 16,8% la CatBoost.
- Setările CatBoost alese: v2 `iterations 1000, lr 0,049, depth 6, l2 0,36, rsm 0,61, subsample 0,87,
  class_weight_power 0,59`; FeederBW `700, 0,072, 6, 3,58, 0,98, 0,80, 0,72`. Istoricul complet al încercărilor e în JSON.

### 2. Contoare (CatBoost vs LightGBM)

| | SGCC (REAL) LightGBM | SGCC CatBoost | LCL bază LightGBM | LCL bază CatBoost | LCL extins LightGBM | LCL extins CatBoost |
|---|---:|---:|---:|---:|---:|---:|
| PR-AUC, tot testul | 0,3994 | 0,3947 | 0,6778 | 0,6776 | 0,7344 | 0,7187 |
| precizia la K = 1% | 0,800 (K=85) | 0,765 | 1,000 (K=130) | 1,000 | 1,000 | 1,000 |
| **PR-AUC subtil** | — | — | 0,4057 | 0,4174 | **0,5175** | **0,4889** |
| **precizia în top 1% subtil (K=128)** | — | — | 0,625 | 0,703 | 0,891 | 0,836 |
| manipulări (furt) vs normale, PR-AUC | — | — | 0,4627 | 0,4721 | 0,5847 | 0,5499 |
| Brier, scor calibrat | 0,0633 | 0,0633 | 0,0232 | 0,0224 | 0,0193 | 0,0204 |

- **SGCC (etichete reale) și LCL (etichete sintetice) sunt raportate separat**; nu le amestecăm.
- LCL extins: CatBoost pierde sigur la PR-AUC subtil (−0,0285 [−0,0461; −0,0123]), la PR-AUC pe tot testul
  (−0,0157 [−0,0239; −0,0081]) și la furt față de normale (−0,0348 [−0,0598; −0,0120]). Pe setul mic de bază
  diferențele nu se disting de zero. Câștigul mare pentru A rămâne cel din datele în plus, nu cel din schimbarea
  algoritmului.
- Valorile K sunt cele din `a_contoare.evaluate`: SGCC 50, 85, 100, 200, 400, 723, 1.446; LCL 50, 100, 130, 200,
  300, 400, 597, 1.194; subtile 50, 100, 128, 200, 382.
- Pe LCL extins, ambele modele ating aproape plafonul de 3.000 de arbori (LightGBM 2.971, CatBoost 2.999), deci
  ambele s-ar putea îmbunătăți cu mai mulți arbori. Plafonul e același pentru amândouă și nu a fost schimbat.

### 3. Furtuni (XGBoost vs LightGBM)

Date REALE: EAGLE-I (ORNL, CC BY 4.0) și Open-Meteo, 80 de comitate din 8 state SUA. Antrenare 2023–2024, test
2025: 29.200 de zone-zile, dintre care 3.014 cu eveniment. Buget: 8 echipe pe zi (10% din comitate).

| | 2025 LightGBM | 2025 XGBoost | Convecție LightGBM | Convecție XGBoost |
|---|---:|---:|---:|---:|
| PR-AUC | 0,2777 | 0,2738 | 0,2865 | 0,2845 |
| Brier | 0,08411 | 0,08434 | 0,08353 | 0,08366 |
| **clienți afectați acoperiți, 8 echipe/zi** | **0,1671** | **0,1654** | 0,1791 | 0,1804 |
| evenimente prinse, 8 echipe/zi | 0,2153 | 0,2143 | 0,2196 | 0,2210 |
| recall pe zilele severe, la prag | 0,498 | 0,509 | 0,530 | 0,498 |

- Pe 2025, XGBoost pierde puțin la PR-AUC (−0,0039 [−0,0064; −0,0012]) și la Brier (+0,00023 [+0,00003;
  +0,00043]; mai mare înseamnă mai rău). La clienții acoperiți diferența include zero.
- State nevăzute: XGBoost e mai bun în 3 state din 8 (IL, KY, NY) și mai slab în 5 (PA −0,016, VA −0,012). Media
  0,2586 → 0,2550, diferența −0,0036 [−0,0076; +0,0002].
- Convecția (CAPE, lifted index, apa precipitabilă, punctul de rouă, stratul limită) ajută **ambele** modele:
  LightGBM +0,0089 [+0,0025; +0,0157], XGBoost +0,0106 [+0,0041; +0,0175]. Între ele, cu convecție, diferența
  include zero. Acest experiment este separat de testul principal: tabelul cu convecție e local, nu în git.
- Modelul de severitate (cuantilele P10/P50/P90) a rămas neschimbat și nu face parte din comparație.

## Timpi de antrenare și inferență

Măsurați pe Mac-ul lui Eden (arm64, 15 nuclee), cu numărul de fire al pipeline-ului existent, același pentru
ambele modele: 8 la bilanț v2, 4 la FeederBW, contoare și furtuni. **Atenție:** rulările s-au suprapus parțial
(bilanț v2 în paralel cu contoarele, furtunile și FeederBW), deci timpii sunt **orientativi**. Inferența la bilanț
include regulile de după model.

| Problemă | LightGBM: antrenare | Candidat: antrenare | LightGBM: inferență pe test | Candidat: inferență pe test | Căutarea candidatului |
|---|---:|---:|---:|---:|---:|
| Bilanț v2 (132.000 / 13.200 de ferestre) | 47,2 s | 25,1 s | 0,665 s | 0,016 s | 916 s (40 de încercări) |
| FeederBW (7.310 / 2.795) | 26,2 s | 5,1 s | 0,322 s | 0,006 s | 468 s (40 de încercări) |
| SGCC (25.422 / 8.475; 15% din antrenare pentru oprire) | 5,4 s | 5,1 s | 0,070 s | 0,004 s | — |
| LCL de bază (16.328 / 13.028) | 14,3 s | 7,6 s | 0,519 s | 0,008 s | — |
| LCL extins (93.051 / 13.028) | 63,3 s | 52,0 s | 2,328 s | 0,013 s | — |
| Furtuni 2025 (OOF + calibrare + final / 29.200) | 11,7 s | 2,7 s | 0,043 s | 0,013 s | 77 s (24 de configurații) |

Antrenarea la contoare include calibrarea. Timpul căutării LightGBM nu a fost măsurat din nou: v2 a durat 1.272 s
în total, inclusiv ferestrele (`reports/bilant/v2_comparison.json`). Singurul avantaj clar al candidaților este
viteza: CatBoost prezice de 17–180 de ori mai repede, iar XGBoost se antrenează de circa 4 ori mai repede pe
furtuni. Pentru volumele din demo, timpii LightGBM sunt deja sub o secundă la inferență, deci acest avantaj nu
schimbă decizia.

## Comenzi de reproducere

```bash
uv sync --group bench                      # LightGBM 4.7.0, CatBoost 1.2.10, XGBoost 3.4.1 (grup separat)
make bench-bilant                          # sau:
uv run --group bench python -m cyberpunks.benchmark.bilant v2 --trials 40        # ~20 min
uv run --group bench python -m cyberpunks.benchmark.bilant feederbw --trials 40  # ~10 min
uv run --group bench python -m cyberpunks.benchmark.contoare                     # ~4 min
uv run --group bench python -m cyberpunks.benchmark.furtuni                      # ~4,5 min
uv run python -m cyberpunks.benchmark.report                                     # reface tabele.md din JSON
make bench-test                                                                   # testele benchmarkului
```

Datele necesare, toate în directoarele locale ignorate de Git:
- bilanț: `data/processed/bilant/windows_trainL.parquet`, lotul `pop`, lotul `feederbw_import_v1`. Se refac cu
  `make bilant-v2`, respectiv cu `python -m cyberpunks.a_bilant.feederbw download|prepare|tune`;
- contoare: `data/raw/A/sgcc/data.csv` și eșantioanele din `data/interim/A/extra/`. Se refac cu
  `python -m cyberpunks.a_contoare.download --only lcl --lcl-files 168` și
  `python -m cyberpunks.a_contoare.experiments_extra`;
- furtuni: `data/samples/B/us_county_day.parquet` (în git); pentru convecție, `data/processed/B/us_extra_daily.parquet`
  (`python -m cyberpunks.b_furtuna.extra_weather build`).

Ferestrele testului v2 construite cu modelele normalului din pachetul livrat sunt salvate în
`data/processed/benchmark/windows_pop_release_v2.parquet` și se refac automat dacă lipsesc. Jurnalele rulărilor sunt
în `logs/benchmark/`, care nu intră în Git.

## Fișiere livrate

| Fișier | Conținut |
|---|---|
| `reports/benchmark/bilant_v2.json`, `bilant_feederbw.json` | metrici, F1 pe clase, matrice de confuzie, diferențe cu IC 90%, furtul, setări, istoricul Optuna, timpi, versiuni |
| `reports/benchmark/contoare.json` | SGCC, LCL de bază, LCL extins: PR-AUC, precizia la toate valorile K, subtile, furt, calibrare, detecție pe tipuri, diferențe, timpi |
| `reports/benchmark/furtuni.json` | test 2025, capacitate, state nevăzute, experimentul cu convecție, grila XGBoost, timpi |
| `reports/benchmark/predictions/bilant_v2_test.parquet` | 13.200 de ferestre: clasa adevărată (SINTETICĂ), etichetele și probabilitățile ambelor modele, cartierul |
| `reports/benchmark/predictions/bilant_feederbw_test.parquet` | 2.795 de ferestre, plecarea reală, etichetele și probabilitățile |
| `reports/benchmark/predictions/contoare_lcl_{baza,extins}_test.parquet` | 13.028 de eșantioane: gospodăria, tipul injectat, scorurile calibrate și brute |
| `reports/benchmark/predictions/furtuni_test2025.parquet`, `furtuni_convectie_test.parquet` | 29.200 de zone-zile: eveniment, clienți afectați, probabilitățile, comitatele alese la 8 echipe |
| `data/processed/benchmark/contoare_sgcc_test.parquet` | **numai local**: SGCC nu are licență explicită de redistribuire |
| `reports/benchmark/tabele.md` | toate tabelele, generate |
| `src/cyberpunks/benchmark/` | codul (`common`, `bilant`, `contoare`, `furtuni`, `report`); teste în `tests/benchmark/` |

## Ce lipsește, limite și abateri

- **Nu lipsesc date.** FeederBW, setul LCL extins (168 de fișiere) și variabilele de convecție erau disponibile local.
  Nu am folosit anii 2021–2022 la furtuni: vremea pentru ei nu a fost descărcată, iar protocolul livrat folosește
  oricum 2023–2024.
- Bilanțul rămâne evaluat pe diagnostice SINTETICE. Niciun rezultat de aici nu este validare pe pierderi măsurate
  sau pe date PPC. Fuziunea bilanț + contoare nu a fost comparată.
- Optuna pentru LightGBM v2 a rulat înainte, cu aceeași validare și 40 de încercări. Am păstrat setările ei, nu am
  repetat căutarea. Spațiile de căutare nu sunt identice între algoritmi, pentru că parametrii diferă, dar au aceleași
  dimensiuni și același număr de încercări.
- La furtuni, LightGBM folosește constrângerile monotone cu metoda „advanced”. XGBoost are numai metoda standard.
  Constrângerea (+1 / 0 pe fiecare variabilă) este aceeași, verificată de testul `test_xgboost_respects_monotone_constraint`.
- FeederBW are numai 8 plecări de test: intervalele sunt largi, iar o diferență de ordinul a 0,01 nu se poate detecta.
- Timpii sunt orientativi, din cauza rulărilor suprapuse.
- Metadatele `environment.threads_per_model: 12` din JSON-uri vin dintr-o constantă nefolosită, scoasă după rulare
  (commitul `6930be8`). Numărul real de fire e `timing_s.threads`. Câmpul `environment.git` arată commitul de la
  sfârșitul rulării; codul modelelor era deja cel din commiturile `3ffe7d3`, `1a70c45` și `74bd711`.
- Pentru modelul de tensiune la prosumatori (C) nu s-a rulat nimic, conform cererii.

## Verdict pe candidați

- **CatBoost la bilanț: respins.** Egalitate statistică pe ambele teste, F1 mai mic pe validare și furtul înainte de
  contor ușor mai slab pe ambele teste. Nu înlocuim LightGBM v2.
- **CatBoost la contoare: respins.** Egalitate pe SGCC și LCL de bază; pierde sigur pe setul LCL extins, care este
  direcția recomandată pentru A.
- **XGBoost la furtuni: respins.** Pierde puțin pe 2025, e la egalitate pe statele nevăzute și cu convecție. Singurul
  avantaj este antrenarea mai rapidă. Convecția ajută ambele modele, deci rămâne recomandată, independent de algoritm.
