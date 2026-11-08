# Machine learning — sursa comună de dovezi

Generat prin `make ml-report`. `evidence.json` reunește integral toate rapoartele JSON A, B, C, bilanț și benchmark, cu SHA256, predicții verificate și rezultatul testelor. Anexa de mai jos reunește comparațiile numerice.

## Verificare

- Scoruri recalculate din predicții: **30/30**.
- Teste pe codul curent: **NU / rulare necesară**.
- Ultima rulare: 2026-11-08T10:30:55.052037+02:00; rezultat {'tests': 208, 'failures': 0, 'errors': 0, 'skipped': 0}; cod ieșire 0.

```sh
uv sync --group bench
make ml-check   # teste + verificare cifre + raport, fără descărcări
make ml-report  # doar verificare cifre și regenerare din dovezile existente
```

Testele de cod și recalcularea scorurilor nu sunt o reantrenare. Experimentele istorice păstrează data și versiunea originală. Un test folosit repetat pentru decizii nu mai este un test final neatins.

## Datele și etichetele

| Sarcină | Intrări | Etichete | Separare / limită |
|---|---|---|---|
| Contoare LCL | consum real Londra | defecte și manipulări INJECTATE | gospodării și timp separate |
| Contoare SGCC | consum real | furt REAL | clienți separați; testul temporal este mai slab |
| Furtuni | EAGLE-I + vreme reală | întreruperi REALE, nu cauză de furtună confirmată | ani și state separate; vreme din arhivă |
| Tensiune C | vreme reală + rețele SimBench | SINTETICE, simulare fizică | topologii și timp separate |
| Bilanț v2 | rețele și măsurători simulate | cauze SINTETICE | posturi/cartiere separate |
| Bilanț FeederBW | forma consumului măsurată | cauze SINTETICE | plecări reale separate |
| Tensiune FeederBW, nou | tensiune monofazată măsurată | maxim zilnic REAL | plecări și timp separate; altă sarcină decât C |

Datele sintetice sunt permise de barem. C și bilanțul nu devin validate în teren doar prin adăugarea unei surse reale.

## Modelele livrate și metodele simple

| Problemă | Metrică | Model | Baseline |
|---|---|---:|---:|
| A | subtle_precision_at_k | 0.62500 | 0.07030 |
| A | sgcc_pr_auc | 0.39940 | 0.07950 |
| B | pr_auc | 0.27770 | 0.15070 |
| C | mae_vmax_pu | 0.00543 | 0.02275 |
| C | pr_auc_exceed | 0.95102 | 0.42749 |
| bilant | normal_mae_kwh_day | 5.39810 | 14.91780 |
| Bilanț v2 | macro-F1 | 0.75352 | 0.48130 |
| Bilanț, lot nou fixat înainte de generare | macro-F1 | 0.77539 | 0.42059 |

Scorurile experimentelor cu date extinse nu sunt automat scorurile modelului livrat.

### Audit suplimentar al bilanțului

300 posturi noi, 13200 ferestre, 60 cartiere; protocolul și SHA256 ale modelului/codului au fost fixate în commitul `3deadcc`, înainte de generarea lotului. Modelul livrat și regulile au rămas fixe; fără tuning sau selecție pe noul rezultat.

Câștigul față de regulile simple: 0.3548 macro-F1, IC90 pe cartiere [0.3163, 0.39007]. Abținere: 20.0%; exactitate pe cazurile fără abținere: 89.6%. Macro-F1 de mai sus include toate cazurile, inclusiv abținerile.

Lotul folosește același simulator și aceleași familii de topologii; distribuția defectelor diferă de harta demo. Scorul nou este o verificare separată, nu o îmbunătățire măsurată pe testul vechi și nu o validare pe cauze reale.

## Ce au schimbat datele și Optuna

| Experiment | Metrică | Înainte | După |
|---|---|---:|---:|
| A: baza | PR-AUC subtil | 0.4057 | 0.4057 |
| A: mai_multe_gospodarii | PR-AUC subtil | 0.4057 | 0.5175 |
| A: vreme | PR-AUC subtil | 0.4057 | 0.4258 |
| A: mai_multe_gospodarii_si_vreme | PR-AUC subtil | 0.4057 | 0.5111 |
| B: baza | PR-AUC | 0.2777 | 0.2777 |
| B: ore_cu_rafale | PR-AUC | 0.2777 | 0.2753 |
| B: sol_umed | PR-AUC | 0.2777 | 0.2745 |
| B: presiune | PR-AUC | 0.2777 | 0.2778 |
| B: convectie | PR-AUC | 0.2777 | 0.2865 |
| B: zapada_strat | PR-AUC | 0.2777 | 0.2785 |
| B: umiditate | PR-AUC | 0.2777 | 0.2749 |
| B: directie_rafala | PR-AUC | 0.2777 | 0.2754 |
| B: toate_noi | PR-AUC | 0.2777 | 0.2855 |
| B: rafale_sol_presiune_convectie | PR-AUC | 0.2777 | 0.2818 |
| C: baza, bucuresti_2025 | MAE pu | — | 0.00538 |
| C: baza, timisoara_2025 | MAE pu | — | 0.00539 |
| C: baza, cluj_2025 | MAE pu | — | 0.00539 |
| C: baza, iasi_2025 | MAE pu | — | 0.00534 |
| C: baza, constanta_2025 | MAE pu | — | 0.00545 |
| C: mai_multi_ani, bucuresti_2025 | MAE pu | — | 0.00538 |
| C: mai_multi_ani, timisoara_2025 | MAE pu | — | 0.00539 |
| C: mai_multi_ani, cluj_2025 | MAE pu | — | 0.00539 |
| C: mai_multi_ani, iasi_2025 | MAE pu | — | 0.00534 |
| C: mai_multi_ani, constanta_2025 | MAE pu | — | 0.00544 |
| C: mai_multe_regiuni, bucuresti_2025 | MAE pu | — | 0.00533 |
| C: mai_multe_regiuni, timisoara_2025 | MAE pu | — | 0.00534 |
| C: mai_multe_regiuni, cluj_2025 | MAE pu | — | 0.00533 |
| C: mai_multe_regiuni, iasi_2025 | MAE pu | — | 0.00528 |
| C: mai_multe_regiuni, constanta_2025 | MAE pu | — | 0.00538 |
| C: ani_si_regiuni, bucuresti_2025 | MAE pu | — | 0.00535 |
| C: ani_si_regiuni, timisoara_2025 | MAE pu | — | 0.00536 |
| C: ani_si_regiuni, cluj_2025 | MAE pu | — | 0.00535 |
| C: ani_si_regiuni, iasi_2025 | MAE pu | — | 0.00531 |
| C: ani_si_regiuni, constanta_2025 | MAE pu | — | 0.00541 |
| C: fizica_v2_fara_vant_zapada, bucuresti_2025_fizica_v2 | MAE pu | — | 0.00576 |
| C: fizica_v2_cu_vant_zapada, bucuresti_2025_fizica_v2 | MAE pu | — | 0.00546 |
| Optuna A | subtle_pr_auc | 0.51750 | 0.50570 |
| Optuna B | pr_auc | 0.27770 | 0.27630 |
| Optuna B convecție | pr_auc | 0.28650 | 0.28670 |
| Optuna C | MAE pu | 0.00533 | 0.00527 |
| Optuna bilanț v2 | macro-F1 | 0.73545 | 0.75352 |

Concluzia corectă: Optuna nu ajută uniform. A/B nu confirmă un câștig; C are un câștig mic, iar bilanțul v2 crește. Intervalele și protocoalele exacte sunt în anexă.

## CatBoost și XGBoost

### Comparațiile A/B/bilanț

Generat de `python -m cyberpunks.benchmark.report` din `reports/benchmark/*.json`. Diferențele sunt candidat − LightGBM, cu interval bootstrap 90% pe grupuri. „(include 0)” = diferență neconcludentă, nu echivalență demonstrată. Analiză exploratorie, fără corecție pentru comparații multiple.

## 1. Bilanț pe post (diagnostice SINTETICE)

### 1a. Testul v2 (300 de posturi, 13.200 de ferestre)

Etichete: SINTETICE: rețele, clienți, pierderi și toate diagnosticele sunt simulate.

| Metrica | LightGBM v2 | CatBoost | CatBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| F1 macro | 0,7535 | 0,7575 | 0,0040 [-0,0032; 0,0129] (include 0) |
| exactitate | 0,8554 | 0,8625 | |
| F1 normal | 0,9270 | 0,9301 | 0,0031 [-0,0003; 0,0064] (include 0) |
| F1 contor de client | 0,4721 | 0,4961 | 0,0240 [0,0087; 0,0442] |
| F1 **furt înainte de contor** | 0,7710 | 0,7641 | -0,0069 [-0,0220; 0,0106] (include 0) |
| F1 pierdere tehnică | 0,4882 | 0,4767 | -0,0115 [-0,0374; 0,0087] (include 0) |
| F1 client la postul greșit | 0,8713 | 0,8847 | 0,0134 [-0,0012; 0,0295] (include 0) |
| F1 contor de bilanț setat greșit | 0,9915 | 0,9931 | 0,0016 [-0,0080; 0,0146] (include 0) |

Bootstrap: cartierul postului de test (31 cartiere), 1000 de reeșantionări, 90%. Clase mai slabe la CatBoost: furt_inainte_contor, pierdere_tehnica; cu intervalul sub zero: niciuna. **Verdict CatBoost: diferență neconcludentă.**

Matricea de confuzie LightGBM (rânduri = adevărat, coloane = prezis; ordinea claselor de mai sus):

| | p:1 | p:2 | p:3 | p:4 | p:5 | p:6 |
|---|---|---|---|---|---|---|
| 1. normal | 8777 | 804 | 22 | 177 | 64 | 1 |
| 2. contor_client | 135 | 622 | 88 | 46 | 12 | 3 |
| 3. furt_inainte_contor | 34 | 140 | 584 | 32 | 4 | 0 |
| 4. pierdere_tehnica | 95 | 69 | 26 | 218 | 3 | 0 |
| 5. client_post_gresit | 50 | 94 | 0 | 9 | 799 | 0 |
| 6. contor_bilant_setat | 0 | 0 | 1 | 0 | 0 | 291 |

Matricea de confuzie CatBoost (rânduri = adevărat, coloane = prezis; ordinea claselor de mai sus):

| | p:1 | p:2 | p:3 | p:4 | p:5 | p:6 |
|---|---|---|---|---|---|---|
| 1. normal | 8853 | 691 | 39 | 195 | 67 | 0 |
| 2. contor_client | 151 | 607 | 93 | 46 | 8 | 1 |
| 3. furt_inainte_contor | 38 | 120 | 591 | 38 | 7 | 0 |
| 4. pierdere_tehnica | 98 | 60 | 29 | 220 | 4 | 0 |
| 5. client_post_gresit | 51 | 63 | 0 | 13 | 825 | 0 |
| 6. contor_bilant_setat | 0 | 0 | 1 | 0 | 2 | 289 |

### 1b. FeederBW, split pe plecarea reală (LightGBM optimizat, același buget)

Etichete: SINTETICE: rețele, clienți, pierderi și toate diagnosticele sunt simulate; REAL este doar forma importului orar al plecărilor FeederBW (Netze BW / KIT, CC BY 4.0).

| Metrica | LightGBM optimizat pe FeederBW | CatBoost | CatBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| F1 macro | 0,7139 | 0,7048 | -0,0091 [-0,0315; 0,0037] (include 0) |
| exactitate | 0,7492 | 0,7370 | |
| F1 normal | 0,8554 | 0,8452 | -0,0102 [-0,0287; 0,0049] (include 0) |
| F1 contor de client | 0,6083 | 0,5872 | -0,0211 [-0,0707; 0,0265] (include 0) |
| F1 **furt înainte de contor** | 0,4686 | 0,4573 | -0,0113 [-0,1105; 0,0270] (include 0) |
| F1 pierdere tehnică | 0,5483 | 0,5206 | -0,0277 [-0,1043; 0,0171] (include 0) |
| F1 client la postul greșit | 0,8101 | 0,8187 | 0,0086 [-0,0256; 0,0389] (include 0) |
| F1 contor de bilanț setat greșit | 0,9929 | 1,0000 | 0,0071 [0,0000; 0,0345] (include 0) |

Bootstrap: plecarea reală de test (8 plecări), 1000 de reeșantionări, 90%. Clase mai slabe la CatBoost: normal, contor_client, furt_inainte_contor, pierdere_tehnica; cu intervalul sub zero: niciuna. **Verdict CatBoost: diferență neconcludentă.**

Matricea de confuzie LightGBM (rânduri = adevărat, coloane = prezis; ordinea claselor de mai sus):

| | p:1 | p:2 | p:3 | p:4 | p:5 | p:6 |
|---|---|---|---|---|---|---|
| 1. normal | 1195 | 105 | 20 | 25 | 12 | 0 |
| 2. contor_client | 179 | 403 | 41 | 20 | 72 | 0 |
| 3. furt_inainte_contor | 31 | 67 | 97 | 40 | 1 | 1 |
| 4. pierdere_tehnica | 10 | 34 | 15 | 88 | 1 | 0 |
| 5. client_post_gresit | 22 | 1 | 4 | 0 | 241 | 0 |
| 6. contor_bilant_setat | 0 | 0 | 0 | 0 | 0 | 70 |

Matricea de confuzie CatBoost (rânduri = adevărat, coloane = prezis; ordinea claselor de mai sus):

| | p:1 | p:2 | p:3 | p:4 | p:5 | p:6 |
|---|---|---|---|---|---|---|
| 1. normal | 1201 | 107 | 20 | 27 | 2 | 0 |
| 2. contor_client | 205 | 389 | 52 | 25 | 44 | 0 |
| 3. furt_inainte_contor | 34 | 72 | 99 | 31 | 1 | 0 |
| 4. pierdere_tehnica | 9 | 39 | 17 | 82 | 1 | 0 |
| 5. client_post_gresit | 36 | 3 | 8 | 2 | 219 | 0 |
| 6. contor_bilant_setat | 0 | 0 | 0 | 0 | 0 | 70 |

Față de LightGBM cu setările v2 (fără căutare pe FeederBW): F1 macro -0,0038 [-0,0288; 0,0133] (include 0); furt înainte de contor 0,0032 [-0,1269; 0,0544] (include 0).

## 2. Contoare

### 2a. SGCC, etichete REALE de furt

Etichete: REALE (SGCC).

| Metrica | LightGBM | CatBoost | CatBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| PR-AUC | 0,3994 | 0,3947 | -0,0047 [-0,0170; 0,0080] (include 0) |
| ROC-AUC | 0,8194 | 0,8192 | |
| precizia la K=50 | 0,8200 | 0,8200 |  |
| precizia la K=85 (1%) | 0,8000 | 0,7647 | -0,0353 [-0,0941; 0,0471] (include 0) |
| precizia la K=100 | 0,8100 | 0,7800 |  |
| precizia la K=200 | 0,6600 | 0,6650 |  |
| precizia la K=400 | 0,5275 | 0,5250 |  |
| precizia la K=723 | 0,4301 | 0,4191 |  |
| precizia la K=1446 | 0,2994 | 0,2981 |  |
| Brier (scor calibrat) | 0,0633 | 0,0633 | |

Bootstrap: clientul (un rând pe client). **Verdict CatBoost: diferență neconcludentă.**

### 2b. Low Carbon London, 45 de fișiere (probleme INJECTATE)

Etichete: SINTETICE: probleme injectate peste consum REAL (LCL, CC BY 4.0).

Antrenare: 16328 eșantioane, 838 gospodării. Test: 13028 eșantioane, 265 gospodării nevăzute.

| Metrica | LightGBM | CatBoost | CatBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| **subtile: PR-AUC** | 0,4057 | 0,4174 | 0,0117 [-0,0335; 0,0488] (include 0) |
| **subtile: precizia în top 1% (K=128)** | 0,6250 | 0,7031 | 0,0781 [-0,0859; 0,2126] (include 0) |
| subtile: precizia la K=50 | 0,7600 | 0,8400 | |
| subtile: precizia la K=100 | 0,6600 | 0,7300 | |
| subtile: precizia la K=200 | 0,6200 | 0,6350 | |
| subtile: precizia la K=382 | 0,4712 | 0,4581 | |
| tot testul: PR-AUC | 0,6778 | 0,6776 | -0,0003 [-0,0225; 0,0224] (include 0) |
| tot testul: precizia la K=130 (1%) | 1,0000 | 1,0000 | 0,0000 [0,0000; 0,0077] (include 0) |
| tot testul: precizia la K=50 | 1,0000 | 1,0000 | |
| tot testul: precizia la K=100 | 1,0000 | 1,0000 | |
| tot testul: precizia la K=200 | 0,9400 | 0,9800 | |
| tot testul: precizia la K=300 | 0,8533 | 0,8833 | |
| tot testul: precizia la K=400 | 0,8100 | 0,8175 | |
| tot testul: precizia la K=597 | 0,6583 | 0,6415 | |
| tot testul: precizia la K=1194 | 0,3710 | 0,3702 | |
| manipulări (furt) vs normale: PR-AUC | 0,4627 | 0,4721 | 0,0094 [-0,0480; 0,0521] (include 0) |
| manipulări vs normale: precizia la 1% | 0,5952 | 0,6190 | 0,0238 [-0,1111; 0,1600] (include 0) |
| Brier (tot testul) | 0,0232 | 0,0224 | |

Bootstrap: gospodăriile de test. **Verdict CatBoost: diferență neconcludentă.**

### 2c. Low Carbon London extins, 168 de fișiere (probleme INJECTATE)

Etichete: SINTETICE: probleme injectate peste consum REAL; gospodăriile în plus doar la antrenare.

Antrenare: 93051 eșantioane, 4914 gospodării. Test: 13028 eșantioane, 265 gospodării nevăzute.

| Metrica | LightGBM | CatBoost | CatBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| **subtile: PR-AUC** | 0,5175 | 0,4889 | -0,0285 [-0,0461; -0,0123] |
| **subtile: precizia în top 1% (K=128)** | 0,8906 | 0,8359 | -0,0547 [-0,1181; 0,0234] (include 0) |
| subtile: precizia la K=50 | 0,9800 | 0,9600 | |
| subtile: precizia la K=100 | 0,9200 | 0,9000 | |
| subtile: precizia la K=200 | 0,7350 | 0,7100 | |
| subtile: precizia la K=382 | 0,4974 | 0,4843 | |
| tot testul: PR-AUC | 0,7344 | 0,7187 | -0,0157 [-0,0239; -0,0081] |
| tot testul: precizia la K=130 (1%) | 1,0000 | 1,0000 | 0,0000 [0,0000; 0,0000] (include 0) |
| tot testul: precizia la K=50 | 1,0000 | 1,0000 | |
| tot testul: precizia la K=100 | 1,0000 | 1,0000 | |
| tot testul: precizia la K=200 | 0,9900 | 0,9950 | |
| tot testul: precizia la K=300 | 0,9700 | 0,9400 | |
| tot testul: precizia la K=400 | 0,8850 | 0,8700 | |
| tot testul: precizia la K=597 | 0,6734 | 0,6633 | |
| tot testul: precizia la K=1194 | 0,3886 | 0,3895 | |
| manipulări (furt) vs normale: PR-AUC | 0,5847 | 0,5499 | -0,0348 [-0,0598; -0,0120] |
| manipulări vs normale: precizia la 1% | 0,7857 | 0,7698 | -0,0159 [-0,0794; 0,0238] (include 0) |
| Brier (tot testul) | 0,0193 | 0,0204 | |

Bootstrap: gospodăriile de test. **Verdict CatBoost: pierde.**

## 3. Furtuni (date REALE, SUA)

### 3a. Test 2025, an nevăzut

| Metrica | LightGBM | XGBoost | XGBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| PR-AUC | 0,2777 | 0,2738 | -0,0039 [-0,0064; -0,0012] |
| Brier (mai mic = mai bine) | 0,0841 | 0,0843 | 0,00023 [0,00003; 0,00043] |
| clienți afectați acoperiți, 8 echipe/zi | 0,1671 | 0,1654 | -0,0018 [-0,0121; 0,0080] (include 0) |
| evenimente prinse, 8 echipe/zi | 0,2153 | 0,2143 | |
| ROC-AUC | 0,7246 | 0,7236 | |
| recall la prag (prag din OOF) | 0,4094 | 0,4273 | |
| recall pe zilele severe, la prag | 0,4977 | 0,5085 | |
| alerte la 100 zone-zile | 15,08 | 15,91 | |

Referințe la același buget: aleator 0,0763, oracol 0,8855. Bootstrap pe săptămânile din 2025. **Verdict XGBoost: pierde.**

### 3b. State nevăzute (fiecare stat scos din antrenare, test pe 2025)

| Stat | Evenimente | PR-AUC LightGBM | PR-AUC XGBoost | Brier LightGBM | Brier XGBoost |
|---|---:|---:|---:|---:|---:|
| IL | 238 | 0,2062 | 0,2142 | 0,0583 | 0,0578 |
| KY | 454 | 0,2658 | 0,2731 | 0,1025 | 0,1020 |
| MI | 372 | 0,2727 | 0,2625 | 0,0837 | 0,0841 |
| MO | 353 | 0,2321 | 0,2274 | 0,0823 | 0,0827 |
| NY | 273 | 0,2368 | 0,2437 | 0,0681 | 0,0688 |
| OH | 363 | 0,2443 | 0,2361 | 0,0840 | 0,0843 |
| PA | 470 | 0,2854 | 0,2697 | 0,1048 | 0,1057 |
| VA | 491 | 0,3255 | 0,3136 | 0,1081 | 0,1085 |

Media pe 8 state: LightGBM 0,2586, XGBoost 0,2550; diferența medie -0,0036 [-0,0076; 0,0002] (include 0); XGBoost mai bun în 3 din 8 state. **Verdict XGBoost: diferență neconcludentă.**

### 3c. Experiment separat: ambele modele cu variabilele de convecție

| Metrica | LightGBM | XGBoost | XGBoost − LightGBM, IC 90% |
|---|---:|---:|---|
| PR-AUC | 0,2865 | 0,2845 | -0,0021 [-0,0047; 0,0005] (include 0) |
| Brier (mai mic = mai bine) | 0,0835 | 0,0837 | 0,00013 [-0,00003; 0,00028] (include 0) |
| clienți afectați acoperiți, 8 echipe/zi | 0,1791 | 0,1804 | 0,0013 [-0,0089; 0,0124] (include 0) |
| evenimente prinse, 8 echipe/zi | 0,2196 | 0,2210 | |
| ROC-AUC | 0,7321 | 0,7296 | |
| recall la prag (prag din OOF) | 0,4409 | 0,4200 | |
| recall pe zilele severe, la prag | 0,5300 | 0,4977 | |
| alerte la 100 zone-zile | 16,46 | 15,54 | |

Referințe la același buget: aleator 0,0763, oracol 0,8855. Bootstrap pe săptămânile din 2025. **Verdict XGBoost: diferență neconcludentă.**

Câștigul convecției, pe același test: LightGBM 0,0089 [0,0025; 0,0157], XGBoost 0,0106 [0,0041; 0,0175].


### C: aceeași simulare, buget fix

6 folduri: topologie nevăzută × test din 2025; train 2023-2024; aceleași 60000 rânduri/fold și trăsături pentru toate modelele, 300 arbori, fără tuning. Regresie mediană; baseline liniar GTI×kW/kVA. Nu se selectează un model nou pe test.

| Model | MAE (mai mic = mai bine) |
|---|---:|
| linear | 0.022742 |
| lightgbm | 0.005382 |
| catboost | 0.005561 |
| xgboost | 0.005418 |

### FeederBW: tensiuni măsurate

Plecări disjuncte și timp separat; istoricul local până ieri este disponibil inclusiv pe plecări noi. 300 arbori/model, setări fixe, zero tuning; alegere pe MAE validare.

| Model | MAE (mai mic = mai bine) |
|---|---:|
| persistence | 0.824814 |
| mean_7d | 0.731811 |
| ridge | 0.688326 |
| lightgbm | 0.707201 |
| catboost | 0.715048 |
| xgboost | 0.724285 |

Ales înaintea testului, pe validare: **xgboost**. Test: 1353 zile-plecare, 0 peste 253 V. Ridge este mai bun pe test; asta nu justifică schimbarea retroactivă a selecției. Acest experiment nu probează detectarea supratensiunilor, nici maximul spațial al C.

## Erori și limite care rămân

- Bilanț: contorul de client și pierderea tehnică rămân clasele slabe; nu există aici cauze confirmate de echipe în teren.
- C: recall scăzut pe semiurb4 la pragul 0,5. Nu mutăm pragul după ce am văzut testul; sunt necesare date operaționale.
- B: testul românesc este scurt, fără furtuni severe; nu susține un câștig de transfer. Vremea arhivată nu reproduce erorile unei prognoze.
- SGCC: rezultatul pe clienți separați este mai bun decât în separarea temporală. Nu promitem aceeași precizie în România.
- IC90 care include zero înseamnă diferență neconcludentă, nu echivalență demonstrată. Comparațiile multiple sunt exploratorii.

## Reproducere completă și date locale

`make ml-check` funcționează cu datele mici/predicțiile din Git. SGCC se verifică suplimentar când există local. Pentru reantrenare, comenzile și sursele sunt în fiecare fișă; datele mari nu sunt ascunse drept dependențe ale testelor rapide.

| Scop | Comandă | Pregătire |
|---|---|---|
| CatBoost bilanț | `make bench-bilant` | lot trainL/pop + FeederBW: vezi `reports/benchmark/RAPORT.md` |
| CatBoost contoare | `make bench-contoare` | SGCC local, LCL 168 fișiere și mostre procesate A |
| XGBoost furtuni | `make bench-furtuni` | setul B și meteo convecție |
| C, trei algoritmi | `make bench-tensiune` | `make c-weather c-sim` sau cache experiment C |
| Audit bilanț, model fixat | `make bench-bilant-holdout` | vremea C (`make c-weather`); protocolul este deja în Git |
| Tensiune măsurată, trei algoritmi | `make bench-tensiune-reala` | agregatul CC BY 4.0 inclus în Git |
| Refacere agregat FeederBW | `uv run --group bench python -m cyberpunks.benchmark.tensiune_reala --prepare` | `uv run python -m cyberpunks.a_bilant.feederbw download` |

## Anexă: toate comparațiile și verificările

Istoricul complet al trialurilor și metadatele sunt păstrate în `evidence.json`. Valorile de mai jos provin direct din surse; nu am amestecat seturi de test diferite într-un scor comun.

<details><summary>reports/A/experiments_extra.json</summary>

[Sursa](../../reports/A/experiments_extra.json) · SHA256 `d632a12699fd0c109b0d39d5ba9b5dbe05411c2f529f4c7c6b84f602011244b6`

| Câmp | Valoare |
|---|---:|
| meta.n_test | 13028 |
| rows[baza].subtle_precision_at_k | 0.625 |
| rows[baza].subtle_recall_at_k | 0.2094 |
| rows[baza].subtle_pr_auc | 0.4057 |
| rows[baza].subtle_precision_at_5pct | 0.3261 |
| rows[baza].pr_auc | 0.6778 |
| rows[baza].n_train | 16328 |
| rows[baza].households_train | 838 |
| rows[mai_multe_gospodarii].subtle_precision_at_k | 0.8906 |
| rows[mai_multe_gospodarii].subtle_recall_at_k | 0.2984 |
| rows[mai_multe_gospodarii].subtle_pr_auc | 0.5175 |
| rows[mai_multe_gospodarii].subtle_precision_at_5pct | 0.3541 |
| rows[mai_multe_gospodarii].pr_auc | 0.7344 |
| rows[mai_multe_gospodarii].n_train | 93051 |
| rows[mai_multe_gospodarii].households_train | 4914 |
| rows[mai_multe_gospodarii].delta_subtle_pr_auc_ci90 | [0.0516, 0.1569] |
| rows[vreme].subtle_precision_at_k | 0.6719 |
| rows[vreme].subtle_recall_at_k | 0.2251 |
| rows[vreme].subtle_pr_auc | 0.4258 |
| rows[vreme].subtle_precision_at_5pct | 0.3245 |
| rows[vreme].pr_auc | 0.6858 |
| rows[vreme].n_train | 16328 |
| rows[vreme].households_train | 838 |
| rows[vreme].delta_subtle_pr_auc_ci90 | [-0.008, 0.0385] |
| rows[mai_multe_gospodarii_si_vreme].subtle_precision_at_k | 0.8984 |
| rows[mai_multe_gospodarii_si_vreme].subtle_recall_at_k | 0.301 |
| rows[mai_multe_gospodarii_si_vreme].subtle_pr_auc | 0.5111 |
| rows[mai_multe_gospodarii_si_vreme].subtle_precision_at_5pct | 0.3432 |
| rows[mai_multe_gospodarii_si_vreme].pr_auc | 0.7311 |
| rows[mai_multe_gospodarii_si_vreme].n_train | 93051 |
| rows[mai_multe_gospodarii_si_vreme].households_train | 4914 |
| rows[mai_multe_gospodarii_si_vreme].delta_subtle_pr_auc_ci90 | [0.0408, 0.1562] |

</details>

<details><summary>reports/A/feature_selection.json</summary>

[Sursa](../../reports/A/feature_selection.json) · SHA256 `526cc18700992ef400c82fa5d60cbcda3450a507f0ff9d2fa7efa440d5f5cc85`

| Câmp | Valoare |
|---|---:|
| sgcc.vechi.pr_auc | 0.3749 |
| sgcc.vechi.roc_auc | 0.8127 |
| sgcc.vechi.precision_at_k | 0.7647 |
| sgcc.vechi.recall_at_k | 0.0899 |
| sgcc.nou.pr_auc | 0.4174 |
| sgcc.nou.roc_auc | 0.8382 |
| sgcc.nou.precision_at_k | 0.7059 |
| sgcc.nou.recall_at_k | 0.0829 |
| lcl.vechi.pr_auc | 0.8964 |
| lcl.vechi.roc_auc | 0.8896 |
| lcl.vechi.precision_at_k | 1 |
| lcl.vechi.recall_at_k | 0.0229 |
| lcl.vechi.auc_by_kind.clock_drift | 0.6023 |
| lcl.vechi.auc_by_kind.drift | 0.7477 |
| lcl.vechi.auc_by_kind.bypass | 0.8217 |
| lcl.vechi.auc_by_kind.h1 | 0.8868 |
| lcl.vechi.auc_by_kind.night | 0.8139 |
| lcl.vechi.auc_by_kind.h6 | 0.9071 |
| lcl.vechi.auc_benign_vs_normal.vacation | 0.4714 |
| lcl.vechi.auc_benign_vs_normal.occupancy_change | 0.6188 |
| lcl.nou.pr_auc | 0.9015 |
| lcl.nou.roc_auc | 0.8945 |
| lcl.nou.precision_at_k | 1 |
| lcl.nou.recall_at_k | 0.0229 |
| lcl.nou.auc_by_kind.clock_drift | 0.6261 |
| lcl.nou.auc_by_kind.drift | 0.7646 |
| lcl.nou.auc_by_kind.bypass | 0.823 |
| lcl.nou.auc_by_kind.h1 | 0.8899 |
| lcl.nou.auc_by_kind.night | 0.8202 |
| lcl.nou.auc_by_kind.h6 | 0.9037 |
| lcl.nou.auc_benign_vs_normal.vacation | 0.5241 |
| lcl.nou.auc_benign_vs_normal.occupancy_change | 0.6502 |
| lcl.nou_fara_sezoniere_brute.pr_auc | 0.8976 |
| lcl.nou_fara_sezoniere_brute.roc_auc | 0.8891 |
| lcl.nou_fara_sezoniere_brute.precision_at_k | 1 |
| lcl.nou_fara_sezoniere_brute.recall_at_k | 0.0229 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.clock_drift | 0.6096 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.drift | 0.7466 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.bypass | 0.8179 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.h1 | 0.8778 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.night | 0.8063 |
| lcl.nou_fara_sezoniere_brute.auc_by_kind.h6 | 0.9016 |
| lcl.nou_fara_sezoniere_brute.auc_benign_vs_normal.vacation | 0.5152 |
| lcl.nou_fara_sezoniere_brute.auc_benign_vs_normal.occupancy_change | 0.6444 |

</details>

<details><summary>reports/A/fusion_check.json</summary>

[Sursa](../../reports/A/fusion_check.json) · SHA256 `92c1263d01cf91e6b235c9ab871d2b6e59b975c44f049685451b9b3981c15f48`

| Câmp | Valoare |
|---|---:|
| demo-vara.meters | 15850 |
| demo-vara.real_problems | 865 |
| demo-vara.sigma_1pct.roc_auc_a | 0.9168 |
| demo-vara.sigma_1pct.roc_auc_fused | 0.9152 |
| demo-vara.sigma_1pct.pr_auc_a | 0.7178 |
| demo-vara.sigma_1pct.pr_auc_fused | 0.7084 |
| demo-vara.sigma_1pct.precision_at_10_a | 1 |
| demo-vara.sigma_1pct.precision_at_10_fused | 1 |
| demo-vara.sigma_1pct.precision_at_20_a | 1 |
| demo-vara.sigma_1pct.precision_at_20_fused | 1 |
| demo-vara.sigma_1pct.precision_at_50_a | 1 |
| demo-vara.sigma_1pct.precision_at_50_fused | 1 |
| demo-vara.sigma_1pct.precision_at_100_a | 1 |
| demo-vara.sigma_1pct.precision_at_100_fused | 1 |
| demo-vara.sigma_1pct.precision_at_250_a | 1 |
| demo-vara.sigma_1pct.precision_at_250_fused | 1 |
| demo-vara.sigma_1pct.confirmed_share.furt_real | 0.2124 |
| demo-vara.sigma_1pct.confirmed_share.defect_real | 0.2414 |
| demo-vara.sigma_1pct.confirmed_share.fara_problema | 0.0603 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.zero | 0.5327 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.stuck | 0.271 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.gaps | 0.0093 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.spikes | 0.0623 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.clock_drift | 0.0757 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.negative | 0.5477 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.drift | 0.0833 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h1 | 0.2843 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h2 | 0.2943 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h3 | 0.289 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h4 | 0.04 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h5 | 0.4013 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.h6 | 0.0723 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.bypass | 0.2637 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.night | 0.0363 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.vacation | 0.2377 |
| demo-vara.sigma_1pct.confirmed_share_by_kind.occupancy_change | 0.1427 |
| demo-vara.sigma_1pct.gray_zone.meters | 558 |
| demo-vara.sigma_1pct.gray_zone.real_problem_share | 0.1362 |
| demo-vara.sigma_1pct.gray_zone.confirmed | 115 |
| demo-vara.sigma_1pct.gray_zone.real_problem_share_if_confirmed | 0.1274 |
| demo-vara.sigma_1pct.gray_zone.real_problem_share_if_not_confirmed | 0.1384 |
| demo-vara.sigma_1pct.precision_at_100_doar_furt_a | 0.12 |
| demo-vara.sigma_1pct.precision_at_100_doar_furt_fused | 0.0833 |
| demo-vara.sigma_1pct.roc_auc_doar_furt_a | 0.889 |
| demo-vara.sigma_1pct.roc_auc_doar_furt_fused | 0.8895 |
| demo-vara.sigma_1pct.precision_at_100_doar_defecte_a | 0.88 |
| demo-vara.sigma_1pct.precision_at_100_doar_defecte_fused | 0.9167 |
| demo-vara.sigma_1pct.roc_auc_doar_defecte_a | 0.9173 |
| demo-vara.sigma_1pct.roc_auc_doar_defecte_fused | 0.9143 |
| demo-vara.sigma_2pct.roc_auc_a | 0.9168 |
| demo-vara.sigma_2pct.roc_auc_fused | 0.9166 |
| demo-vara.sigma_2pct.pr_auc_a | 0.7178 |
| demo-vara.sigma_2pct.pr_auc_fused | 0.7205 |
| demo-vara.sigma_2pct.precision_at_10_a | 1 |
| demo-vara.sigma_2pct.precision_at_10_fused | 1 |
| demo-vara.sigma_2pct.precision_at_20_a | 1 |
| demo-vara.sigma_2pct.precision_at_20_fused | 1 |
| demo-vara.sigma_2pct.precision_at_50_a | 1 |
| demo-vara.sigma_2pct.precision_at_50_fused | 1 |
| demo-vara.sigma_2pct.precision_at_100_a | 1 |
| demo-vara.sigma_2pct.precision_at_100_fused | 1 |
| demo-vara.sigma_2pct.precision_at_250_a | 1 |
| demo-vara.sigma_2pct.precision_at_250_fused | 1 |
| demo-vara.sigma_2pct.confirmed_share.furt_real | 0.0776 |
| demo-vara.sigma_2pct.confirmed_share.defect_real | 0.1137 |
| demo-vara.sigma_2pct.confirmed_share.fara_problema | 0.0236 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.zero | 0.244 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.stuck | 0.0907 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.gaps | 0.0093 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.spikes | 0.0293 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.clock_drift | 0.035 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.negative | 0.3057 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.drift | 0.0157 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h1 | 0.1057 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h2 | 0.098 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h3 | 0.1223 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h4 | 0 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h5 | 0.177 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.h6 | 0.0147 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.bypass | 0.0623 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.night | 0.0217 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.vacation | 0.0833 |
| demo-vara.sigma_2pct.confirmed_share_by_kind.occupancy_change | 0.041 |
| demo-vara.sigma_2pct.gray_zone.meters | 558 |
| demo-vara.sigma_2pct.gray_zone.real_problem_share | 0.1362 |
| demo-vara.sigma_2pct.gray_zone.confirmed | 42.6667 |
| demo-vara.sigma_2pct.gray_zone.real_problem_share_if_confirmed | 0.1483 |
| demo-vara.sigma_2pct.gray_zone.real_problem_share_if_not_confirmed | 0.1352 |
| demo-vara.sigma_2pct.precision_at_100_doar_furt_a | 0.12 |
| demo-vara.sigma_2pct.precision_at_100_doar_furt_fused | 0.0667 |
| demo-vara.sigma_2pct.roc_auc_doar_furt_a | 0.889 |
| demo-vara.sigma_2pct.roc_auc_doar_furt_fused | 0.89 |
| demo-vara.sigma_2pct.precision_at_100_doar_defecte_a | 0.88 |
| demo-vara.sigma_2pct.precision_at_100_doar_defecte_fused | 0.9333 |
| demo-vara.sigma_2pct.roc_auc_doar_defecte_a | 0.9173 |
| demo-vara.sigma_2pct.roc_auc_doar_defecte_fused | 0.9163 |
| demo-vara.sigma_4pct.roc_auc_a | 0.9168 |
| demo-vara.sigma_4pct.roc_auc_fused | 0.9169 |
| demo-vara.sigma_4pct.pr_auc_a | 0.7178 |
| demo-vara.sigma_4pct.pr_auc_fused | 0.7238 |
| demo-vara.sigma_4pct.precision_at_10_a | 1 |
| demo-vara.sigma_4pct.precision_at_10_fused | 1 |
| demo-vara.sigma_4pct.precision_at_20_a | 1 |
| demo-vara.sigma_4pct.precision_at_20_fused | 1 |
| demo-vara.sigma_4pct.precision_at_50_a | 1 |
| demo-vara.sigma_4pct.precision_at_50_fused | 1 |
| demo-vara.sigma_4pct.precision_at_100_a | 1 |
| demo-vara.sigma_4pct.precision_at_100_fused | 1 |
| demo-vara.sigma_4pct.precision_at_250_a | 1 |
| demo-vara.sigma_4pct.precision_at_250_fused | 1 |
| demo-vara.sigma_4pct.confirmed_share.furt_real | 0.0222 |
| demo-vara.sigma_4pct.confirmed_share.defect_real | 0.0331 |
| demo-vara.sigma_4pct.confirmed_share.fara_problema | 0.0061 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.zero | 0.073 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.stuck | 0.0057 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.gaps | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.spikes | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.clock_drift | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.negative | 0.123 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.drift | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h1 | 0.0407 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h2 | 0.0293 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h3 | 0.022 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h4 | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h5 | 0.0543 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.h6 | 0 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.bypass | 0.023 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.night | 0.0073 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.vacation | 0.0147 |
| demo-vara.sigma_4pct.confirmed_share_by_kind.occupancy_change | 0.0083 |
| demo-vara.sigma_4pct.gray_zone.meters | 558 |
| demo-vara.sigma_4pct.gray_zone.real_problem_share | 0.1362 |
| demo-vara.sigma_4pct.gray_zone.confirmed | 7.3333 |
| demo-vara.sigma_4pct.gray_zone.real_problem_share_if_confirmed | 0.2143 |
| demo-vara.sigma_4pct.gray_zone.real_problem_share_if_not_confirmed | 0.135 |
| demo-vara.sigma_4pct.precision_at_100_doar_furt_a | 0.12 |
| demo-vara.sigma_4pct.precision_at_100_doar_furt_fused | 0.1 |
| demo-vara.sigma_4pct.roc_auc_doar_furt_a | 0.889 |
| demo-vara.sigma_4pct.roc_auc_doar_furt_fused | 0.8899 |
| demo-vara.sigma_4pct.precision_at_100_doar_defecte_a | 0.88 |
| demo-vara.sigma_4pct.precision_at_100_doar_defecte_fused | 0.9 |
| demo-vara.sigma_4pct.roc_auc_doar_defecte_a | 0.9173 |
| demo-vara.sigma_4pct.roc_auc_doar_defecte_fused | 0.9167 |
| maine.meters | 15850 |
| maine.real_problems | 780 |
| maine.sigma_1pct.roc_auc_a | 0.9172 |
| maine.sigma_1pct.roc_auc_fused | 0.9166 |
| maine.sigma_1pct.pr_auc_a | 0.6887 |
| maine.sigma_1pct.pr_auc_fused | 0.697 |
| maine.sigma_1pct.precision_at_10_a | 1 |
| maine.sigma_1pct.precision_at_10_fused | 1 |
| maine.sigma_1pct.precision_at_20_a | 1 |
| maine.sigma_1pct.precision_at_20_fused | 1 |
| maine.sigma_1pct.precision_at_50_a | 1 |
| maine.sigma_1pct.precision_at_50_fused | 1 |
| maine.sigma_1pct.precision_at_100_a | 1 |
| maine.sigma_1pct.precision_at_100_fused | 1 |
| maine.sigma_1pct.precision_at_250_a | 1 |
| maine.sigma_1pct.precision_at_250_fused | 1 |
| maine.sigma_1pct.confirmed_share.furt_real | 0.1733 |
| maine.sigma_1pct.confirmed_share.defect_real | 0.2329 |
| maine.sigma_1pct.confirmed_share.fara_problema | 0.0306 |
| maine.sigma_1pct.confirmed_share_by_kind.zero | 0.498 |
| maine.sigma_1pct.confirmed_share_by_kind.stuck | 0.2887 |
| maine.sigma_1pct.confirmed_share_by_kind.gaps | 0.0107 |
| maine.sigma_1pct.confirmed_share_by_kind.spikes | 0.0057 |
| maine.sigma_1pct.confirmed_share_by_kind.clock_drift | 0.01 |
| maine.sigma_1pct.confirmed_share_by_kind.negative | 0.5257 |
| maine.sigma_1pct.confirmed_share_by_kind.drift | 0.1423 |
| maine.sigma_1pct.confirmed_share_by_kind.h1 | 0.248 |
| maine.sigma_1pct.confirmed_share_by_kind.h2 | 0.3547 |
| maine.sigma_1pct.confirmed_share_by_kind.h3 | 0.229 |
| maine.sigma_1pct.confirmed_share_by_kind.h4 | 0.025 |
| maine.sigma_1pct.confirmed_share_by_kind.h5 | 0.3253 |
| maine.sigma_1pct.confirmed_share_by_kind.h6 | 0 |
| maine.sigma_1pct.confirmed_share_by_kind.bypass | 0.2083 |
| maine.sigma_1pct.confirmed_share_by_kind.night | 0.0343 |
| maine.sigma_1pct.confirmed_share_by_kind.vacation | 0.21 |
| maine.sigma_1pct.confirmed_share_by_kind.occupancy_change | 0.09 |
| maine.sigma_1pct.gray_zone.meters | 333 |
| maine.sigma_1pct.gray_zone.real_problem_share | 0.2192 |
| maine.sigma_1pct.gray_zone.confirmed | 35.6667 |
| maine.sigma_1pct.gray_zone.real_problem_share_if_confirmed | 0.291 |
| maine.sigma_1pct.gray_zone.real_problem_share_if_not_confirmed | 0.2108 |
| maine.sigma_1pct.precision_at_100_doar_furt_a | 0.12 |
| maine.sigma_1pct.precision_at_100_doar_furt_fused | 0.0633 |
| maine.sigma_1pct.roc_auc_doar_furt_a | 0.9014 |
| maine.sigma_1pct.roc_auc_doar_furt_fused | 0.9021 |
| maine.sigma_1pct.precision_at_100_doar_defecte_a | 0.88 |
| maine.sigma_1pct.precision_at_100_doar_defecte_fused | 0.9367 |
| maine.sigma_1pct.roc_auc_doar_defecte_a | 0.9108 |
| maine.sigma_1pct.roc_auc_doar_defecte_fused | 0.9095 |
| maine.sigma_2pct.roc_auc_a | 0.9172 |
| maine.sigma_2pct.roc_auc_fused | 0.9169 |
| maine.sigma_2pct.pr_auc_a | 0.6887 |
| maine.sigma_2pct.pr_auc_fused | 0.6978 |
| maine.sigma_2pct.precision_at_10_a | 1 |
| maine.sigma_2pct.precision_at_10_fused | 1 |
| maine.sigma_2pct.precision_at_20_a | 1 |
| maine.sigma_2pct.precision_at_20_fused | 1 |
| maine.sigma_2pct.precision_at_50_a | 1 |
| maine.sigma_2pct.precision_at_50_fused | 1 |
| maine.sigma_2pct.precision_at_100_a | 1 |
| maine.sigma_2pct.precision_at_100_fused | 1 |
| maine.sigma_2pct.precision_at_250_a | 1 |
| maine.sigma_2pct.precision_at_250_fused | 1 |
| maine.sigma_2pct.confirmed_share.furt_real | 0.0475 |
| maine.sigma_2pct.confirmed_share.defect_real | 0.0976 |
| maine.sigma_2pct.confirmed_share.fara_problema | 0.0058 |
| maine.sigma_2pct.confirmed_share_by_kind.zero | 0.2297 |
| maine.sigma_2pct.confirmed_share_by_kind.stuck | 0.0667 |
| maine.sigma_2pct.confirmed_share_by_kind.gaps | 0 |
| maine.sigma_2pct.confirmed_share_by_kind.spikes | 0.0057 |
| maine.sigma_2pct.confirmed_share_by_kind.clock_drift | 0 |
| maine.sigma_2pct.confirmed_share_by_kind.negative | 0.282 |
| maine.sigma_2pct.confirmed_share_by_kind.drift | 0.0273 |
| maine.sigma_2pct.confirmed_share_by_kind.h1 | 0.0853 |
| maine.sigma_2pct.confirmed_share_by_kind.h2 | 0.0863 |
| maine.sigma_2pct.confirmed_share_by_kind.h3 | 0.0517 |
| maine.sigma_2pct.confirmed_share_by_kind.h4 | 0 |
| maine.sigma_2pct.confirmed_share_by_kind.h5 | 0.143 |
| maine.sigma_2pct.confirmed_share_by_kind.h6 | 0 |
| maine.sigma_2pct.confirmed_share_by_kind.bypass | 0.0167 |
| maine.sigma_2pct.confirmed_share_by_kind.night | 0 |
| maine.sigma_2pct.confirmed_share_by_kind.vacation | 0.077 |
| maine.sigma_2pct.confirmed_share_by_kind.occupancy_change | 0.028 |
| maine.sigma_2pct.gray_zone.meters | 333 |
| maine.sigma_2pct.gray_zone.real_problem_share | 0.2192 |
| maine.sigma_2pct.gray_zone.confirmed | 4.6667 |
| maine.sigma_2pct.gray_zone.real_problem_share_if_confirmed | 0.6389 |
| maine.sigma_2pct.gray_zone.real_problem_share_if_not_confirmed | 0.2132 |
| maine.sigma_2pct.precision_at_100_doar_furt_a | 0.12 |
| maine.sigma_2pct.precision_at_100_doar_furt_fused | 0.0733 |
| maine.sigma_2pct.roc_auc_doar_furt_a | 0.9014 |
| maine.sigma_2pct.roc_auc_doar_furt_fused | 0.9023 |
| maine.sigma_2pct.precision_at_100_doar_defecte_a | 0.88 |
| maine.sigma_2pct.precision_at_100_doar_defecte_fused | 0.9267 |
| maine.sigma_2pct.roc_auc_doar_defecte_a | 0.9108 |
| maine.sigma_2pct.roc_auc_doar_defecte_fused | 0.9098 |
| maine.sigma_4pct.roc_auc_a | 0.9172 |
| maine.sigma_4pct.roc_auc_fused | 0.9171 |
| maine.sigma_4pct.pr_auc_a | 0.6887 |
| maine.sigma_4pct.pr_auc_fused | 0.6965 |
| maine.sigma_4pct.precision_at_10_a | 1 |
| maine.sigma_4pct.precision_at_10_fused | 1 |
| maine.sigma_4pct.precision_at_20_a | 1 |
| maine.sigma_4pct.precision_at_20_fused | 1 |
| maine.sigma_4pct.precision_at_50_a | 1 |
| maine.sigma_4pct.precision_at_50_fused | 1 |
| maine.sigma_4pct.precision_at_100_a | 1 |
| maine.sigma_4pct.precision_at_100_fused | 1 |
| maine.sigma_4pct.precision_at_250_a | 1 |
| maine.sigma_4pct.precision_at_250_fused | 1 |
| maine.sigma_4pct.confirmed_share.furt_real | 0.0077 |
| maine.sigma_4pct.confirmed_share.defect_real | 0.0202 |
| maine.sigma_4pct.confirmed_share.fara_problema | 0.0007 |
| maine.sigma_4pct.confirmed_share_by_kind.zero | 0.039 |
| maine.sigma_4pct.confirmed_share_by_kind.stuck | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.gaps | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.spikes | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.clock_drift | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.negative | 0.0857 |
| maine.sigma_4pct.confirmed_share_by_kind.drift | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.h1 | 0.0173 |
| maine.sigma_4pct.confirmed_share_by_kind.h2 | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.h3 | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.h4 | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.h5 | 0.04 |
| maine.sigma_4pct.confirmed_share_by_kind.h6 | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.bypass | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.night | 0 |
| maine.sigma_4pct.confirmed_share_by_kind.vacation | 0.0103 |
| maine.sigma_4pct.confirmed_share_by_kind.occupancy_change | 0.007 |
| maine.sigma_4pct.gray_zone.meters | 333 |
| maine.sigma_4pct.gray_zone.real_problem_share | 0.2192 |
| maine.sigma_4pct.gray_zone.confirmed | 0.3333 |
| maine.sigma_4pct.gray_zone.real_problem_share_if_confirmed | 0 |
| maine.sigma_4pct.gray_zone.real_problem_share_if_not_confirmed | 0.2194 |
| maine.sigma_4pct.precision_at_100_doar_furt_a | 0.12 |
| maine.sigma_4pct.precision_at_100_doar_furt_fused | 0.09 |
| maine.sigma_4pct.roc_auc_doar_furt_a | 0.9014 |
| maine.sigma_4pct.roc_auc_doar_furt_fused | 0.9019 |
| maine.sigma_4pct.precision_at_100_doar_defecte_a | 0.88 |
| maine.sigma_4pct.precision_at_100_doar_defecte_fused | 0.91 |
| maine.sigma_4pct.roc_auc_doar_defecte_a | 0.9108 |
| maine.sigma_4pct.roc_auc_doar_defecte_fused | 0.9104 |

</details>

<details><summary>reports/A/metrics.json</summary>

[Sursa](../../reports/A/metrics.json) · SHA256 `d4abaa5c22c1f7a15d61adf5c75cf16d5f73bc63b8829a10d8680d43b1b0c554`

| Câmp | Valoare |
|---|---:|
| test_size | 21503 |
| metrics.subtle_precision_at_k | 0.625 |
| metrics.sgcc_precision_at_k | 0.8 |
| metrics.subtle_recall_at_k | 0.2094 |
| metrics.subtle_pr_auc | 0.4057 |
| metrics.subtle_roc_auc | 0.8624 |
| metrics.sgcc_recall_at_k | 0.0941 |
| metrics.sgcc_pr_auc | 0.3994 |
| metrics.sgcc_roc_auc | 0.8194 |
| metrics.precision_at_k | 1 |
| metrics.recall_at_k | 0.2178 |
| metrics.pr_auc | 0.6778 |
| metrics.roc_auc | 0.9111 |
| metrics.value_at_k_lei | 93351.2 |
| metrics.brier | 0.0232 |
| metrics.ece | 0.0038 |
| metrics.subtle_vee_precision_at_k | 0.0156 |
| metrics.subtle_vee_recall_at_k | 0.0052 |
| metrics.subtle_vee_pr_auc | 0.0587 |
| metrics.subtle_vee_roc_auc | 0.6981 |
| metrics.sgcc_vee_precision_at_k | 0.1059 |
| metrics.sgcc_vee_recall_at_k | 0.0124 |
| metrics.sgcc_vee_pr_auc | 0.0972 |
| metrics.sgcc_vee_roc_auc | 0.5557 |
| metrics.vee_precision_at_k | 0.5308 |
| metrics.vee_recall_at_k | 0.1156 |
| metrics.vee_pr_auc | 0.2635 |
| metrics.vee_roc_auc | 0.7985 |
| metrics.iforest_precision_at_k | 0.0615 |
| metrics.iforest_recall_at_k | 0.0134 |
| metrics.iforest_pr_auc | 0.179 |
| metrics.iforest_roc_auc | 0.7761 |
| metrics.sgcc_iforest_precision_at_k | 0.1647 |
| metrics.sgcc_iforest_recall_at_k | 0.0194 |
| metrics.sgcc_iforest_pr_auc | 0.1124 |
| metrics.sgcc_iforest_roc_auc | 0.5867 |
| baseline_metrics.subtle_precision_at_k | 0.0703 |
| baseline_metrics.sgcc_precision_at_k | 0.0353 |
| baseline_metrics.subtle_recall_at_k | 0.0236 |
| baseline_metrics.subtle_pr_auc | 0.0665 |
| baseline_metrics.subtle_roc_auc | 0.648 |
| baseline_metrics.sgcc_recall_at_k | 0.0041 |
| baseline_metrics.sgcc_pr_auc | 0.0795 |
| baseline_metrics.sgcc_roc_auc | 0.4958 |
| baseline_metrics.precision_at_k | 0.4615 |
| baseline_metrics.recall_at_k | 0.1005 |
| baseline_metrics.pr_auc | 0.194 |
| baseline_metrics.roc_auc | 0.697 |
| baseline_metrics.value_at_k_lei | 63586.5 |
| synthetic_share | 0.6059 |

</details>

<details><summary>reports/A/metrics_full.json</summary>

[Sursa](../../reports/A/metrics_full.json) · SHA256 `f2d042547f36a5a4e31ef7ab9efbb2f7f13dfbec72d165a50456ca0225ac25dc`

| Câmp | Valoare |
|---|---:|
| budget_share | 0.01 |
| vee_thresholds_from_calibration.sgcc.spike_days | 10 |
| vee_thresholds_from_calibration.sgcc.spike_slots | 3 |
| vee_thresholds_from_calibration.lcl.spike_days | 10 |
| vee_thresholds_from_calibration.lcl.spike_slots | 100 |
| leakage_checks.lcl_households_train_test_overlap | 0 |
| leakage_checks.lcl_households_train_cal_overlap | 0 |
| leakage_checks.lcl_households_cal_test_overlap | 0 |
| leakage_checks.sgcc_customers_train_test_overlap | 0 |
| leakage_checks.sgcc_customers_cal_test_overlap | 0 |
| leakage_checks.lcl_permutation.pr_auc_shuffled | 0.0472 |
| leakage_checks.lcl_permutation.roc_auc_shuffled | 0.4627 |
| leakage_checks.lcl_permutation.prevalence | 0.0458 |
| leakage_checks.sgcc_permutation.pr_auc_shuffled | 0.1054 |
| leakage_checks.sgcc_permutation.roc_auc_shuffled | 0.5453 |
| leakage_checks.sgcc_permutation.prevalence | 0.0853 |
| sgcc_real_labels.n | 8475 |
| sgcc_real_labels.positives | 723 |
| sgcc_real_labels.prevalence | 0.0853 |
| sgcc_real_labels.k | 85 |
| sgcc_real_labels.model.pr_auc | 0.3994 |
| sgcc_real_labels.model.roc_auc | 0.8194 |
| sgcc_real_labels.model.precision_at_k | 0.8 |
| sgcc_real_labels.model.recall_at_k | 0.0941 |
| sgcc_real_labels.model.precision_at_k_ci95 | [0.7176, 0.8824] |
| sgcc_real_labels.model.pr_auc_ci95 | [0.3616, 0.4314] |
| sgcc_real_labels.model.precision_at_budget.0.0025 | 0.9048 |
| sgcc_real_labels.model.precision_at_budget.0.0050 | 0.7857 |
| sgcc_real_labels.model.precision_at_budget.0.0100 | 0.8 |
| sgcc_real_labels.model.precision_at_budget.0.0200 | 0.7176 |
| sgcc_real_labels.model.precision_at_budget.0.0500 | 0.5118 |
| sgcc_real_labels.model.precision_at_budget.0.1000 | 0.4104 |
| sgcc_real_labels.rule.pr_auc | 0.0795 |
| sgcc_real_labels.rule.roc_auc | 0.4958 |
| sgcc_real_labels.rule.precision_at_k | 0.0353 |
| sgcc_real_labels.rule.recall_at_k | 0.0041 |
| sgcc_real_labels.rule.precision_at_k_ci95 | [0.0118, 0.1121] |
| sgcc_real_labels.rule.pr_auc_ci95 | [0.0735, 0.086] |
| sgcc_real_labels.rule.precision_at_budget.0.0025 | 0.1429 |
| sgcc_real_labels.rule.precision_at_budget.0.0050 | 0.0714 |
| sgcc_real_labels.rule.precision_at_budget.0.0100 | 0.0353 |
| sgcc_real_labels.rule.precision_at_budget.0.0200 | 0.0235 |
| sgcc_real_labels.rule.precision_at_budget.0.0500 | 0.0401 |
| sgcc_real_labels.rule.precision_at_budget.0.1000 | 0.0495 |
| sgcc_real_labels.vee.pr_auc | 0.0972 |
| sgcc_real_labels.vee.roc_auc | 0.5557 |
| sgcc_real_labels.vee.precision_at_k | 0.1059 |
| sgcc_real_labels.vee.recall_at_k | 0.0124 |
| sgcc_real_labels.vee.precision_at_k_ci95 | [0.0588, 0.2] |
| sgcc_real_labels.vee.pr_auc_ci95 | [0.0895, 0.1061] |
| sgcc_real_labels.vee.precision_at_budget.0.0025 | 0.1429 |
| sgcc_real_labels.vee.precision_at_budget.0.0050 | 0.1429 |
| sgcc_real_labels.vee.precision_at_budget.0.0100 | 0.1059 |
| sgcc_real_labels.vee.precision_at_budget.0.0200 | 0.0824 |
| sgcc_real_labels.vee.precision_at_budget.0.0500 | 0.0849 |
| sgcc_real_labels.vee.precision_at_budget.0.1000 | 0.0991 |
| sgcc_real_labels.iforest.pr_auc | 0.1124 |
| sgcc_real_labels.iforest.roc_auc | 0.5867 |
| sgcc_real_labels.iforest.precision_at_k | 0.1647 |
| sgcc_real_labels.iforest.recall_at_k | 0.0194 |
| sgcc_real_labels.iforest.precision_at_k_ci95 | [0.0941, 0.2588] |
| sgcc_real_labels.iforest.pr_auc_ci95 | [0.1005, 0.1268] |
| sgcc_real_labels.iforest.precision_at_budget.0.0025 | 0.0952 |
| sgcc_real_labels.iforest.precision_at_budget.0.0050 | 0.1905 |
| sgcc_real_labels.iforest.precision_at_budget.0.0100 | 0.1647 |
| sgcc_real_labels.iforest.precision_at_budget.0.0200 | 0.1471 |
| sgcc_real_labels.iforest.precision_at_budget.0.0500 | 0.1321 |
| sgcc_real_labels.iforest.precision_at_budget.0.1000 | 0.1238 |
| sgcc_real_labels.model_beats_rule_share | 1 |
| sgcc_real_labels.model_beats_vee_share | 1 |
| sgcc_real_labels.model_beats_iforest_share | 1 |
| sgcc_real_labels.calibration.brier | 0.0633 |
| sgcc_real_labels.calibration.ece | 0.0062 |
| sgcc_real_labels.conformal.set_coverage_normal | 0.9892 |
| sgcc_real_labels.conformal.set_coverage_problem | 0.6611 |
| sgcc_real_labels.conformal.problem_recall_sure | 0.2019 |
| sgcc_real_labels.conformal.problem_precision_sure | 0.6348 |
| sgcc_real_labels.conformal.problem_to_unsure | 0.4592 |
| sgcc_real_labels.conformal.problem_missed | 0.3389 |
| sgcc_real_labels.conformal.normal_to_problem | 0.0108 |
| sgcc_real_labels.conformal.normal_to_unsure | 0.1699 |
| sgcc_real_labels.conformal.unsure_share | 0.1946 |
| sgcc_real_labels.conformal.problem_share | 0.0271 |
| sgcc_real_labels.conformal.p_threshold_problem | 0.1002 |
| sgcc_real_labels.conformal.p_threshold_normal | 0.5542 |
| sgcc_real_labels.false_alarms_by_level[0].quintile | 1 |
| sgcc_real_labels.false_alarms_by_level[0].level_kwh_median | 0 |
| sgcc_real_labels.false_alarms_by_level[0].false_alarm_rate | 0.0037 |
| sgcc_real_labels.false_alarms_by_level[0].recall | 0.0568 |
| sgcc_real_labels.false_alarms_by_level[0].n_normal | 1604 |
| sgcc_real_labels.false_alarms_by_level[0].n_problem | 88 |
| sgcc_real_labels.false_alarms_by_level[1].quintile | 2 |
| sgcc_real_labels.false_alarms_by_level[1].level_kwh_median | 1.91 |
| sgcc_real_labels.false_alarms_by_level[1].false_alarm_rate | 0.0094 |
| sgcc_real_labels.false_alarms_by_level[1].recall | 0.1146 |
| sgcc_real_labels.false_alarms_by_level[1].n_normal | 1596 |
| sgcc_real_labels.false_alarms_by_level[1].n_problem | 96 |
| sgcc_real_labels.false_alarms_by_level[2].quintile | 3 |
| sgcc_real_labels.false_alarms_by_level[2].level_kwh_median | 5.64 |
| sgcc_real_labels.false_alarms_by_level[2].false_alarm_rate | 0.0121 |
| sgcc_real_labels.false_alarms_by_level[2].recall | 0.1322 |
| sgcc_real_labels.false_alarms_by_level[2].n_normal | 1571 |
| sgcc_real_labels.false_alarms_by_level[2].n_problem | 121 |
| sgcc_real_labels.false_alarms_by_level[3].quintile | 4 |
| sgcc_real_labels.false_alarms_by_level[3].level_kwh_median | 10.44 |
| sgcc_real_labels.false_alarms_by_level[3].false_alarm_rate | 0.0269 |
| sgcc_real_labels.false_alarms_by_level[3].recall | 0.2713 |
| sgcc_real_labels.false_alarms_by_level[3].n_normal | 1563 |
| sgcc_real_labels.false_alarms_by_level[3].n_problem | 129 |
| sgcc_real_labels.false_alarms_by_level[4].quintile | 5 |
| sgcc_real_labels.false_alarms_by_level[4].level_kwh_median | 20.88 |
| sgcc_real_labels.false_alarms_by_level[4].false_alarm_rate | 0.0843 |
| sgcc_real_labels.false_alarms_by_level[4].recall | 0.5071 |
| sgcc_real_labels.false_alarms_by_level[4].n_normal | 1412 |
| sgcc_real_labels.false_alarms_by_level[4].n_problem | 280 |
| sgcc_real_labels.ranking_at_ks[0].k | 50 |
| sgcc_real_labels.ranking_at_ks[0].k_over_positives | 0.0692 |
| sgcc_real_labels.ranking_at_ks[0].model_precision | 0.82 |
| sgcc_real_labels.ranking_at_ks[0].model_recall | 0.0567 |
| sgcc_real_labels.ranking_at_ks[0].rule_precision | 0.06 |
| sgcc_real_labels.ranking_at_ks[0].rule_recall | 0.0041 |
| sgcc_real_labels.ranking_at_ks[0].vee_precision | 0.14 |
| sgcc_real_labels.ranking_at_ks[0].vee_recall | 0.0097 |
| sgcc_real_labels.ranking_at_ks[0].iforest_precision | 0.18 |
| sgcc_real_labels.ranking_at_ks[0].iforest_recall | 0.0124 |
| sgcc_real_labels.ranking_at_ks[1].k | 85 |
| sgcc_real_labels.ranking_at_ks[1].k_over_positives | 0.1176 |
| sgcc_real_labels.ranking_at_ks[1].model_precision | 0.8 |
| sgcc_real_labels.ranking_at_ks[1].model_recall | 0.0941 |
| sgcc_real_labels.ranking_at_ks[1].rule_precision | 0.0353 |
| sgcc_real_labels.ranking_at_ks[1].rule_recall | 0.0041 |
| sgcc_real_labels.ranking_at_ks[1].vee_precision | 0.1059 |
| sgcc_real_labels.ranking_at_ks[1].vee_recall | 0.0124 |
| sgcc_real_labels.ranking_at_ks[1].iforest_precision | 0.1647 |
| sgcc_real_labels.ranking_at_ks[1].iforest_recall | 0.0194 |
| sgcc_real_labels.ranking_at_ks[2].k | 100 |
| sgcc_real_labels.ranking_at_ks[2].k_over_positives | 0.1383 |
| sgcc_real_labels.ranking_at_ks[2].model_precision | 0.81 |
| sgcc_real_labels.ranking_at_ks[2].model_recall | 0.112 |
| sgcc_real_labels.ranking_at_ks[2].rule_precision | 0.04 |
| sgcc_real_labels.ranking_at_ks[2].rule_recall | 0.0055 |
| sgcc_real_labels.ranking_at_ks[2].vee_precision | 0.1 |
| sgcc_real_labels.ranking_at_ks[2].vee_recall | 0.0138 |
| sgcc_real_labels.ranking_at_ks[2].iforest_precision | 0.15 |
| sgcc_real_labels.ranking_at_ks[2].iforest_recall | 0.0207 |
| sgcc_real_labels.ranking_at_ks[3].k | 200 |
| sgcc_real_labels.ranking_at_ks[3].k_over_positives | 0.2766 |
| sgcc_real_labels.ranking_at_ks[3].model_precision | 0.66 |
| sgcc_real_labels.ranking_at_ks[3].model_recall | 0.1826 |
| sgcc_real_labels.ranking_at_ks[3].rule_precision | 0.035 |
| sgcc_real_labels.ranking_at_ks[3].rule_recall | 0.0097 |
| sgcc_real_labels.ranking_at_ks[3].vee_precision | 0.08 |
| sgcc_real_labels.ranking_at_ks[3].vee_recall | 0.0221 |
| sgcc_real_labels.ranking_at_ks[3].iforest_precision | 0.135 |
| sgcc_real_labels.ranking_at_ks[3].iforest_recall | 0.0373 |
| sgcc_real_labels.ranking_at_ks[4].k | 400 |
| sgcc_real_labels.ranking_at_ks[4].k_over_positives | 0.5533 |
| sgcc_real_labels.ranking_at_ks[4].model_precision | 0.5275 |
| sgcc_real_labels.ranking_at_ks[4].model_recall | 0.2918 |
| sgcc_real_labels.ranking_at_ks[4].rule_precision | 0.035 |
| sgcc_real_labels.ranking_at_ks[4].rule_recall | 0.0194 |
| sgcc_real_labels.ranking_at_ks[4].vee_precision | 0.0875 |
| sgcc_real_labels.ranking_at_ks[4].vee_recall | 0.0484 |
| sgcc_real_labels.ranking_at_ks[4].iforest_precision | 0.13 |
| sgcc_real_labels.ranking_at_ks[4].iforest_recall | 0.0719 |
| sgcc_real_labels.ranking_at_ks[5].k | 723 |
| sgcc_real_labels.ranking_at_ks[5].k_over_positives | 1 |
| sgcc_real_labels.ranking_at_ks[5].model_precision | 0.4302 |
| sgcc_real_labels.ranking_at_ks[5].model_recall | 0.4302 |
| sgcc_real_labels.ranking_at_ks[5].rule_precision | 0.0498 |
| sgcc_real_labels.ranking_at_ks[5].rule_recall | 0.0498 |
| sgcc_real_labels.ranking_at_ks[5].vee_precision | 0.0996 |
| sgcc_real_labels.ranking_at_ks[5].vee_recall | 0.0996 |
| sgcc_real_labels.ranking_at_ks[5].iforest_precision | 0.1231 |
| sgcc_real_labels.ranking_at_ks[5].iforest_recall | 0.1231 |
| sgcc_real_labels.ranking_at_ks[6].k | 1446 |
| sgcc_real_labels.ranking_at_ks[6].k_over_positives | 2 |
| sgcc_real_labels.ranking_at_ks[6].model_precision | 0.2994 |
| sgcc_real_labels.ranking_at_ks[6].model_recall | 0.5989 |
| sgcc_real_labels.ranking_at_ks[6].rule_precision | 0.0519 |
| sgcc_real_labels.ranking_at_ks[6].rule_recall | 0.1037 |
| sgcc_real_labels.ranking_at_ks[6].vee_precision | 0.0996 |
| sgcc_real_labels.ranking_at_ks[6].vee_recall | 0.1992 |
| sgcc_real_labels.ranking_at_ks[6].iforest_precision | 0.1189 |
| sgcc_real_labels.ranking_at_ks[6].iforest_recall | 0.2379 |
| sgcc_real_labels.k_curve.positives | 723 |
| sgcc_real_labels.k_curve.n | 8475 |
| sgcc_real_labels.false_alarms_by_level_rule[0].quintile | 1 |
| sgcc_real_labels.false_alarms_by_level_rule[0].level_kwh_median | 0 |
| sgcc_real_labels.false_alarms_by_level_rule[0].false_alarm_rate | 0.1945 |
| sgcc_real_labels.false_alarms_by_level_rule[0].recall | 0.1364 |
| sgcc_real_labels.false_alarms_by_level_rule[0].n_normal | 1604 |
| sgcc_real_labels.false_alarms_by_level_rule[0].n_problem | 88 |
| sgcc_real_labels.false_alarms_by_level_rule[1].quintile | 2 |
| sgcc_real_labels.false_alarms_by_level_rule[1].level_kwh_median | 1.91 |
| sgcc_real_labels.false_alarms_by_level_rule[1].false_alarm_rate | 0.0263 |
| sgcc_real_labels.false_alarms_by_level_rule[1].recall | 0.0208 |
| sgcc_real_labels.false_alarms_by_level_rule[1].n_normal | 1596 |
| sgcc_real_labels.false_alarms_by_level_rule[1].n_problem | 96 |
| sgcc_real_labels.false_alarms_by_level_rule[2].quintile | 3 |
| sgcc_real_labels.false_alarms_by_level_rule[2].level_kwh_median | 5.64 |
| sgcc_real_labels.false_alarms_by_level_rule[2].false_alarm_rate | 0.0121 |
| sgcc_real_labels.false_alarms_by_level_rule[2].recall | 0.0083 |
| sgcc_real_labels.false_alarms_by_level_rule[2].n_normal | 1571 |
| sgcc_real_labels.false_alarms_by_level_rule[2].n_problem | 121 |
| sgcc_real_labels.false_alarms_by_level_rule[3].quintile | 4 |
| sgcc_real_labels.false_alarms_by_level_rule[3].level_kwh_median | 10.44 |
| sgcc_real_labels.false_alarms_by_level_rule[3].false_alarm_rate | 0.0147 |
| sgcc_real_labels.false_alarms_by_level_rule[3].recall | 0.0078 |
| sgcc_real_labels.false_alarms_by_level_rule[3].n_normal | 1563 |
| sgcc_real_labels.false_alarms_by_level_rule[3].n_problem | 129 |
| sgcc_real_labels.false_alarms_by_level_rule[4].quintile | 5 |
| sgcc_real_labels.false_alarms_by_level_rule[4].level_kwh_median | 20.88 |
| sgcc_real_labels.false_alarms_by_level_rule[4].false_alarm_rate | 0.0078 |
| sgcc_real_labels.false_alarms_by_level_rule[4].recall | 0.0036 |
| sgcc_real_labels.false_alarms_by_level_rule[4].n_normal | 1412 |
| sgcc_real_labels.false_alarms_by_level_rule[4].n_problem | 280 |
| lcl_injected.n | 13028 |
| lcl_injected.positives | 597 |
| lcl_injected.prevalence | 0.0458 |
| lcl_injected.k | 130 |
| lcl_injected.model.pr_auc | 0.6778 |
| lcl_injected.model.roc_auc | 0.9111 |
| lcl_injected.model.precision_at_k | 1 |
| lcl_injected.model.recall_at_k | 0.2178 |
| lcl_injected.model.value_at_k_lei | 93351.2 |
| lcl_injected.model.value_share_at_k | 0.65 |
| lcl_injected.model.precision_at_k_ci95 | [0.9846, 1.0] |
| lcl_injected.model.pr_auc_ci95 | [0.6187, 0.737] |
| lcl_injected.model.precision_at_budget.0.0025 | 1 |
| lcl_injected.model.precision_at_budget.0.0050 | 1 |
| lcl_injected.model.precision_at_budget.0.0100 | 1 |
| lcl_injected.model.precision_at_budget.0.0200 | 0.8889 |
| lcl_injected.model.precision_at_budget.0.0500 | 0.616 |
| lcl_injected.model.precision_at_budget.0.1000 | 0.3507 |
| lcl_injected.rule.pr_auc | 0.194 |
| lcl_injected.rule.roc_auc | 0.697 |
| lcl_injected.rule.precision_at_k | 0.4615 |
| lcl_injected.rule.recall_at_k | 0.1005 |
| lcl_injected.rule.value_at_k_lei | 63586.5 |
| lcl_injected.rule.value_share_at_k | 0.4428 |
| lcl_injected.rule.precision_at_k_ci95 | [0.2857, 0.704] |
| lcl_injected.rule.pr_auc_ci95 | [0.145, 0.2883] |
| lcl_injected.rule.precision_at_budget.0.0025 | 0.6061 |
| lcl_injected.rule.precision_at_budget.0.0050 | 0.5846 |
| lcl_injected.rule.precision_at_budget.0.0100 | 0.4615 |
| lcl_injected.rule.precision_at_budget.0.0200 | 0.3716 |
| lcl_injected.rule.precision_at_budget.0.0500 | 0.2903 |
| lcl_injected.rule.precision_at_budget.0.1000 | 0.198 |
| lcl_injected.vee.pr_auc | 0.2635 |
| lcl_injected.vee.roc_auc | 0.7985 |
| lcl_injected.vee.precision_at_k | 0.5308 |
| lcl_injected.vee.recall_at_k | 0.1156 |
| lcl_injected.vee.value_at_k_lei | 67723.9 |
| lcl_injected.vee.value_share_at_k | 0.4716 |
| lcl_injected.vee.precision_at_k_ci95 | [0.3359, 0.865] |
| lcl_injected.vee.pr_auc_ci95 | [0.2009, 0.3778] |
| lcl_injected.vee.precision_at_budget.0.0025 | 0.5455 |
| lcl_injected.vee.precision_at_budget.0.0050 | 0.6 |
| lcl_injected.vee.precision_at_budget.0.0100 | 0.5308 |
| lcl_injected.vee.precision_at_budget.0.0200 | 0.5249 |
| lcl_injected.vee.precision_at_budget.0.0500 | 0.2949 |
| lcl_injected.vee.precision_at_budget.0.1000 | 0.2302 |
| lcl_injected.iforest.pr_auc | 0.179 |
| lcl_injected.iforest.roc_auc | 0.7761 |
| lcl_injected.iforest.precision_at_k | 0.0615 |
| lcl_injected.iforest.recall_at_k | 0.0134 |
| lcl_injected.iforest.value_at_k_lei | 1803.2 |
| lcl_injected.iforest.value_share_at_k | 0.0126 |
| lcl_injected.iforest.precision_at_k_ci95 | [0.0305, 0.5894] |
| lcl_injected.iforest.pr_auc_ci95 | [0.1452, 0.2651] |
| lcl_injected.iforest.precision_at_budget.0.0025 | 0.1212 |
| lcl_injected.iforest.precision_at_budget.0.0050 | 0.0923 |
| lcl_injected.iforest.precision_at_budget.0.0100 | 0.0615 |
| lcl_injected.iforest.precision_at_budget.0.0200 | 0.2989 |
| lcl_injected.iforest.precision_at_budget.0.0500 | 0.2903 |
| lcl_injected.iforest.precision_at_budget.0.1000 | 0.2134 |
| lcl_injected.model_beats_rule_share | 1 |
| lcl_injected.model_beats_vee_share | 1 |
| lcl_injected.model_beats_iforest_share | 1 |
| lcl_injected.calibration.brier | 0.0232 |
| lcl_injected.calibration.ece | 0.0038 |
| lcl_injected.calibration.reliability[0].p_mean | 0.00290622 |
| lcl_injected.calibration.reliability[0].freq | 0.0030722 |
| lcl_injected.calibration.reliability[0].n | 1302 |
| lcl_injected.calibration.reliability[1].p_mean | 0.00631236 |
| lcl_injected.calibration.reliability[1].freq | 0.0053681 |
| lcl_injected.calibration.reliability[1].n | 1304 |
| lcl_injected.calibration.reliability[2].p_mean | 0.0090618 |
| lcl_injected.calibration.reliability[2].freq | 0.00768049 |
| lcl_injected.calibration.reliability[2].n | 1302 |
| lcl_injected.calibration.reliability[3].p_mean | 0.0096452 |
| lcl_injected.calibration.reliability[3].freq | 0.0109976 |
| lcl_injected.calibration.reliability[3].n | 1273 |
| lcl_injected.calibration.reliability[4].p_mean | 0.0100385 |
| lcl_injected.calibration.reliability[4].freq | 0.00225225 |
| lcl_injected.calibration.reliability[4].n | 1332 |
| lcl_injected.calibration.reliability[5].p_mean | 0.0116669 |
| lcl_injected.calibration.reliability[5].freq | 0.00843558 |
| lcl_injected.calibration.reliability[5].n | 1304 |
| lcl_injected.calibration.reliability[6].p_mean | 0.0131903 |
| lcl_injected.calibration.reliability[6].freq | 0.0121951 |
| lcl_injected.calibration.reliability[6].n | 164 |
| lcl_injected.calibration.reliability[7].p_mean | 0.0148202 |
| lcl_injected.calibration.reliability[7].freq | 0.0192623 |
| lcl_injected.calibration.reliability[7].n | 2440 |
| lcl_injected.calibration.reliability[8].p_mean | 0.0490664 |
| lcl_injected.calibration.reliability[8].freq | 0.0332779 |
| lcl_injected.calibration.reliability[8].n | 1202 |
| lcl_injected.calibration.reliability[9].p_mean | 0.0594223 |
| lcl_injected.calibration.reliability[9].freq | 0.058952 |
| lcl_injected.calibration.reliability[9].n | 458 |
| lcl_injected.calibration.reliability[10].p_mean | 0.124173 |
| lcl_injected.calibration.reliability[10].freq | 0.145089 |
| lcl_injected.calibration.reliability[10].n | 448 |
| lcl_injected.calibration.reliability[11].p_mean | 0.315261 |
| lcl_injected.calibration.reliability[11].freq | 0.459459 |
| lcl_injected.calibration.reliability[11].n | 37 |
| lcl_injected.calibration.reliability[12].p_mean | 0.506803 |
| lcl_injected.calibration.reliability[12].freq | 0.587097 |
| lcl_injected.calibration.reliability[12].n | 155 |
| lcl_injected.calibration.reliability[13].p_mean | 0.687087 |
| lcl_injected.calibration.reliability[13].freq | 0.633333 |
| lcl_injected.calibration.reliability[13].n | 30 |
| lcl_injected.calibration.reliability[14].p_mean | 0.959032 |
| lcl_injected.calibration.reliability[14].freq | 0.866426 |
| lcl_injected.calibration.reliability[14].n | 277 |
| lcl_injected.conformal.set_coverage_normal | 0.9903 |
| lcl_injected.conformal.set_coverage_problem | 0.6901 |
| lcl_injected.conformal.problem_recall_sure | 0.5896 |
| lcl_injected.conformal.problem_precision_sure | 0.7442 |
| lcl_injected.conformal.problem_to_unsure | 0.1005 |
| lcl_injected.conformal.problem_missed | 0.3099 |
| lcl_injected.conformal.normal_to_problem | 0.0097 |
| lcl_injected.conformal.normal_to_unsure | 0.0146 |
| lcl_injected.conformal.unsure_share | 0.0186 |
| lcl_injected.conformal.problem_share | 0.0363 |
| lcl_injected.conformal.p_threshold_problem | 0.1092 |
| lcl_injected.conformal.p_threshold_normal | 0.3333 |
| lcl_injected.venn_abers_grid_vs_exact.n | 200 |
| lcl_injected.venn_abers_grid_vs_exact.max_abs_p | 0.03645 |
| lcl_injected.venn_abers_grid_vs_exact.mean_abs_p | 0.00041 |
| lcl_injected.venn_abers_grid_vs_exact.max_abs_p0 | 0.07351 |
| lcl_injected.venn_abers_grid_vs_exact.max_abs_p1 | 0.06282 |
| lcl_injected.subtle_only.n | 12813 |
| lcl_injected.subtle_only.positives | 382 |
| lcl_injected.subtle_only.prevalence | 0.0298 |
| lcl_injected.subtle_only.k | 128 |
| lcl_injected.subtle_only.model.pr_auc | 0.4057 |
| lcl_injected.subtle_only.model.roc_auc | 0.8624 |
| lcl_injected.subtle_only.model.precision_at_k | 0.625 |
| lcl_injected.subtle_only.model.recall_at_k | 0.2094 |
| lcl_injected.subtle_only.model.value_at_k_lei | 13576.9 |
| lcl_injected.subtle_only.model.value_share_at_k | 0.2616 |
| lcl_injected.subtle_only.model.precision_at_k_ci95 | [0.4587, 0.8873] |
| lcl_injected.subtle_only.model.pr_auc_ci95 | [0.3202, 0.5157] |
| lcl_injected.subtle_only.model.precision_at_budget.0.0025 | 0.8438 |
| lcl_injected.subtle_only.model.precision_at_budget.0.0050 | 0.7969 |
| lcl_injected.subtle_only.model.precision_at_budget.0.0100 | 0.625 |
| lcl_injected.subtle_only.model.precision_at_budget.0.0200 | 0.5703 |
| lcl_injected.subtle_only.model.precision_at_budget.0.0500 | 0.3261 |
| lcl_injected.subtle_only.model.precision_at_budget.0.1000 | 0.1944 |
| lcl_injected.subtle_only.rule.pr_auc | 0.0665 |
| lcl_injected.subtle_only.rule.roc_auc | 0.648 |
| lcl_injected.subtle_only.rule.precision_at_k | 0.0703 |
| lcl_injected.subtle_only.rule.recall_at_k | 0.0236 |
| lcl_injected.subtle_only.rule.value_at_k_lei | 2602.14 |
| lcl_injected.subtle_only.rule.value_share_at_k | 0.0501 |
| lcl_injected.subtle_only.rule.precision_at_k_ci95 | [0.0155, 0.1323] |
| lcl_injected.subtle_only.rule.pr_auc_ci95 | [0.0554, 0.0849] |
| lcl_injected.subtle_only.rule.precision_at_budget.0.0025 | 0.0312 |
| lcl_injected.subtle_only.rule.precision_at_budget.0.0050 | 0.0156 |
| lcl_injected.subtle_only.rule.precision_at_budget.0.0100 | 0.0703 |
| lcl_injected.subtle_only.rule.precision_at_budget.0.0200 | 0.0742 |
| lcl_injected.subtle_only.rule.precision_at_budget.0.0500 | 0.1388 |
| lcl_injected.subtle_only.rule.precision_at_budget.0.1000 | 0.1015 |
| lcl_injected.subtle_only.vee.pr_auc | 0.0587 |
| lcl_injected.subtle_only.vee.roc_auc | 0.6981 |
| lcl_injected.subtle_only.vee.precision_at_k | 0.0156 |
| lcl_injected.subtle_only.vee.recall_at_k | 0.0052 |
| lcl_injected.subtle_only.vee.value_at_k_lei | 250 |
| lcl_injected.subtle_only.vee.value_share_at_k | 0.0048 |
| lcl_injected.subtle_only.vee.precision_at_k_ci95 | [0.0, 0.0391] |
| lcl_injected.subtle_only.vee.pr_auc_ci95 | [0.0514, 0.0702] |
| lcl_injected.subtle_only.vee.precision_at_budget.0.0025 | 0.0312 |
| lcl_injected.subtle_only.vee.precision_at_budget.0.0050 | 0.0156 |
| lcl_injected.subtle_only.vee.precision_at_budget.0.0100 | 0.0156 |
| lcl_injected.subtle_only.vee.precision_at_budget.0.0200 | 0.0234 |
| lcl_injected.subtle_only.vee.precision_at_budget.0.0500 | 0.0437 |
| lcl_injected.subtle_only.vee.precision_at_budget.0.1000 | 0.0898 |
| lcl_injected.subtle_only.iforest.pr_auc | 0.0554 |
| lcl_injected.subtle_only.iforest.roc_auc | 0.6715 |
| lcl_injected.subtle_only.iforest.precision_at_k | 0.0391 |
| lcl_injected.subtle_only.iforest.recall_at_k | 0.0131 |
| lcl_injected.subtle_only.iforest.value_at_k_lei | 1053.2 |
| lcl_injected.subtle_only.iforest.value_share_at_k | 0.0203 |
| lcl_injected.subtle_only.iforest.precision_at_k_ci95 | [0.0078, 0.093] |
| lcl_injected.subtle_only.iforest.pr_auc_ci95 | [0.0469, 0.0668] |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.0025 | 0.0625 |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.0050 | 0.0625 |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.0100 | 0.0391 |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.0200 | 0.0352 |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.0500 | 0.0686 |
| lcl_injected.subtle_only.iforest.precision_at_budget.0.1000 | 0.0757 |
| lcl_injected.subtle_only.model_beats_rule_share | 1 |
| lcl_injected.subtle_only.model_beats_vee_share | 1 |
| lcl_injected.subtle_only.model_beats_iforest_share | 1 |
| lcl_injected.subtle_only.ranking_at_ks[0].k | 50 |
| lcl_injected.subtle_only.ranking_at_ks[0].k_over_positives | 0.1309 |
| lcl_injected.subtle_only.ranking_at_ks[0].model_precision | 0.76 |
| lcl_injected.subtle_only.ranking_at_ks[0].model_recall | 0.0995 |
| lcl_injected.subtle_only.ranking_at_ks[0].rule_precision | 0.02 |
| lcl_injected.subtle_only.ranking_at_ks[0].rule_recall | 0.0026 |
| lcl_injected.subtle_only.ranking_at_ks[0].vee_precision | 0.02 |
| lcl_injected.subtle_only.ranking_at_ks[0].vee_recall | 0.0026 |
| lcl_injected.subtle_only.ranking_at_ks[0].iforest_precision | 0.06 |
| lcl_injected.subtle_only.ranking_at_ks[0].iforest_recall | 0.0079 |
| lcl_injected.subtle_only.ranking_at_ks[1].k | 100 |
| lcl_injected.subtle_only.ranking_at_ks[1].k_over_positives | 0.2618 |
| lcl_injected.subtle_only.ranking_at_ks[1].model_precision | 0.66 |
| lcl_injected.subtle_only.ranking_at_ks[1].model_recall | 0.1728 |
| lcl_injected.subtle_only.ranking_at_ks[1].rule_precision | 0.02 |
| lcl_injected.subtle_only.ranking_at_ks[1].rule_recall | 0.0052 |
| lcl_injected.subtle_only.ranking_at_ks[1].vee_precision | 0.02 |
| lcl_injected.subtle_only.ranking_at_ks[1].vee_recall | 0.0052 |
| lcl_injected.subtle_only.ranking_at_ks[1].iforest_precision | 0.04 |
| lcl_injected.subtle_only.ranking_at_ks[1].iforest_recall | 0.0105 |
| lcl_injected.subtle_only.ranking_at_ks[2].k | 128 |
| lcl_injected.subtle_only.ranking_at_ks[2].k_over_positives | 0.3351 |
| lcl_injected.subtle_only.ranking_at_ks[2].model_precision | 0.625 |
| lcl_injected.subtle_only.ranking_at_ks[2].model_recall | 0.2094 |
| lcl_injected.subtle_only.ranking_at_ks[2].rule_precision | 0.0703 |
| lcl_injected.subtle_only.ranking_at_ks[2].rule_recall | 0.0236 |
| lcl_injected.subtle_only.ranking_at_ks[2].vee_precision | 0.0156 |
| lcl_injected.subtle_only.ranking_at_ks[2].vee_recall | 0.0052 |
| lcl_injected.subtle_only.ranking_at_ks[2].iforest_precision | 0.0391 |
| lcl_injected.subtle_only.ranking_at_ks[2].iforest_recall | 0.0131 |
| lcl_injected.subtle_only.ranking_at_ks[3].k | 200 |
| lcl_injected.subtle_only.ranking_at_ks[3].k_over_positives | 0.5236 |
| lcl_injected.subtle_only.ranking_at_ks[3].model_precision | 0.62 |
| lcl_injected.subtle_only.ranking_at_ks[3].model_recall | 0.3246 |
| lcl_injected.subtle_only.ranking_at_ks[3].rule_precision | 0.08 |
| lcl_injected.subtle_only.ranking_at_ks[3].rule_recall | 0.0419 |
| lcl_injected.subtle_only.ranking_at_ks[3].vee_precision | 0.02 |
| lcl_injected.subtle_only.ranking_at_ks[3].vee_recall | 0.0105 |
| lcl_injected.subtle_only.ranking_at_ks[3].iforest_precision | 0.04 |
| lcl_injected.subtle_only.ranking_at_ks[3].iforest_recall | 0.0209 |
| lcl_injected.subtle_only.ranking_at_ks[4].k | 382 |
| lcl_injected.subtle_only.ranking_at_ks[4].k_over_positives | 1 |
| lcl_injected.subtle_only.ranking_at_ks[4].model_precision | 0.4712 |
| lcl_injected.subtle_only.ranking_at_ks[4].model_recall | 0.4712 |
| lcl_injected.subtle_only.ranking_at_ks[4].rule_precision | 0.123 |
| lcl_injected.subtle_only.ranking_at_ks[4].rule_recall | 0.123 |
| lcl_injected.subtle_only.ranking_at_ks[4].vee_precision | 0.0366 |
| lcl_injected.subtle_only.ranking_at_ks[4].vee_recall | 0.0366 |
| lcl_injected.subtle_only.ranking_at_ks[4].iforest_precision | 0.0366 |
| lcl_injected.subtle_only.ranking_at_ks[4].iforest_recall | 0.0366 |
| lcl_injected.subtle_only.k_curve.positives | 382 |
| lcl_injected.subtle_only.k_curve.n | 12813 |
| lcl_injected.ranking_at_ks[0].k | 50 |
| lcl_injected.ranking_at_ks[0].k_over_positives | 0.0838 |
| lcl_injected.ranking_at_ks[0].model_precision | 1 |
| lcl_injected.ranking_at_ks[0].model_recall | 0.0838 |
| lcl_injected.ranking_at_ks[0].rule_precision | 0.6 |
| lcl_injected.ranking_at_ks[0].rule_recall | 0.0503 |
| lcl_injected.ranking_at_ks[0].vee_precision | 0.64 |
| lcl_injected.ranking_at_ks[0].vee_recall | 0.0536 |
| lcl_injected.ranking_at_ks[0].iforest_precision | 0.1 |
| lcl_injected.ranking_at_ks[0].iforest_recall | 0.0084 |
| lcl_injected.ranking_at_ks[1].k | 100 |
| lcl_injected.ranking_at_ks[1].k_over_positives | 0.1675 |
| lcl_injected.ranking_at_ks[1].model_precision | 1 |
| lcl_injected.ranking_at_ks[1].model_recall | 0.1675 |
| lcl_injected.ranking_at_ks[1].rule_precision | 0.49 |
| lcl_injected.ranking_at_ks[1].rule_recall | 0.0821 |
| lcl_injected.ranking_at_ks[1].vee_precision | 0.55 |
| lcl_injected.ranking_at_ks[1].vee_recall | 0.0921 |
| lcl_injected.ranking_at_ks[1].iforest_precision | 0.07 |
| lcl_injected.ranking_at_ks[1].iforest_recall | 0.0117 |
| lcl_injected.ranking_at_ks[2].k | 130 |
| lcl_injected.ranking_at_ks[2].k_over_positives | 0.2178 |
| lcl_injected.ranking_at_ks[2].model_precision | 1 |
| lcl_injected.ranking_at_ks[2].model_recall | 0.2178 |
| lcl_injected.ranking_at_ks[2].rule_precision | 0.4615 |
| lcl_injected.ranking_at_ks[2].rule_recall | 0.1005 |
| lcl_injected.ranking_at_ks[2].vee_precision | 0.5308 |
| lcl_injected.ranking_at_ks[2].vee_recall | 0.1156 |
| lcl_injected.ranking_at_ks[2].iforest_precision | 0.0615 |
| lcl_injected.ranking_at_ks[2].iforest_recall | 0.0134 |
| lcl_injected.ranking_at_ks[3].k | 200 |
| lcl_injected.ranking_at_ks[3].k_over_positives | 0.335 |
| lcl_injected.ranking_at_ks[3].model_precision | 0.94 |
| lcl_injected.ranking_at_ks[3].model_recall | 0.3149 |
| lcl_injected.ranking_at_ks[3].rule_precision | 0.415 |
| lcl_injected.ranking_at_ks[3].rule_recall | 0.139 |
| lcl_injected.ranking_at_ks[3].vee_precision | 0.555 |
| lcl_injected.ranking_at_ks[3].vee_recall | 0.1859 |
| lcl_injected.ranking_at_ks[3].iforest_precision | 0.21 |
| lcl_injected.ranking_at_ks[3].iforest_recall | 0.0704 |
| lcl_injected.ranking_at_ks[4].k | 300 |
| lcl_injected.ranking_at_ks[4].k_over_positives | 0.5025 |
| lcl_injected.ranking_at_ks[4].model_precision | 0.8533 |
| lcl_injected.ranking_at_ks[4].model_recall | 0.4288 |
| lcl_injected.ranking_at_ks[4].rule_precision | 0.3333 |
| lcl_injected.ranking_at_ks[4].rule_recall | 0.1675 |
| lcl_injected.ranking_at_ks[4].vee_precision | 0.48 |
| lcl_injected.ranking_at_ks[4].vee_recall | 0.2412 |
| lcl_injected.ranking_at_ks[4].iforest_precision | 0.3267 |
| lcl_injected.ranking_at_ks[4].iforest_recall | 0.1642 |
| lcl_injected.ranking_at_ks[5].k | 400 |
| lcl_injected.ranking_at_ks[5].k_over_positives | 0.67 |
| lcl_injected.ranking_at_ks[5].model_precision | 0.81 |
| lcl_injected.ranking_at_ks[5].model_recall | 0.5427 |
| lcl_injected.ranking_at_ks[5].rule_precision | 0.3 |
| lcl_injected.ranking_at_ks[5].rule_recall | 0.201 |
| lcl_injected.ranking_at_ks[5].vee_precision | 0.4025 |
| lcl_injected.ranking_at_ks[5].vee_recall | 0.2697 |
| lcl_injected.ranking_at_ks[5].iforest_precision | 0.3025 |
| lcl_injected.ranking_at_ks[5].iforest_recall | 0.2027 |
| lcl_injected.ranking_at_ks[6].k | 597 |
| lcl_injected.ranking_at_ks[6].k_over_positives | 1 |
| lcl_injected.ranking_at_ks[6].model_precision | 0.6583 |
| lcl_injected.ranking_at_ks[6].model_recall | 0.6583 |
| lcl_injected.ranking_at_ks[6].rule_precision | 0.2931 |
| lcl_injected.ranking_at_ks[6].rule_recall | 0.2931 |
| lcl_injected.ranking_at_ks[6].vee_precision | 0.3099 |
| lcl_injected.ranking_at_ks[6].vee_recall | 0.3099 |
| lcl_injected.ranking_at_ks[6].iforest_precision | 0.3049 |
| lcl_injected.ranking_at_ks[6].iforest_recall | 0.3049 |
| lcl_injected.ranking_at_ks[7].k | 1194 |
| lcl_injected.ranking_at_ks[7].k_over_positives | 2 |
| lcl_injected.ranking_at_ks[7].model_precision | 0.371 |
| lcl_injected.ranking_at_ks[7].model_recall | 0.742 |
| lcl_injected.ranking_at_ks[7].rule_precision | 0.2102 |
| lcl_injected.ranking_at_ks[7].rule_recall | 0.4204 |
| lcl_injected.ranking_at_ks[7].vee_precision | 0.237 |
| lcl_injected.ranking_at_ks[7].vee_recall | 0.474 |
| lcl_injected.ranking_at_ks[7].iforest_precision | 0.2278 |
| lcl_injected.ranking_at_ks[7].iforest_recall | 0.4556 |
| lcl_injected.k_curve.positives | 597 |
| lcl_injected.k_curve.n | 13028 |
| lcl_injected.top_k_composition.model_top_k.stuck | 46 |
| lcl_injected.top_k_composition.model_top_k.zero | 34 |
| lcl_injected.top_k_composition.model_top_k.negative | 28 |
| lcl_injected.top_k_composition.model_top_k.gaps | 10 |
| lcl_injected.top_k_composition.model_top_k.h4 | 9 |
| lcl_injected.top_k_composition.model_top_k.h3 | 2 |
| lcl_injected.top_k_composition.model_top_k.h6 | 1 |
| lcl_injected.top_k_composition.vee_top_k.normal | 58 |
| lcl_injected.top_k_composition.vee_top_k.zero | 45 |
| lcl_injected.top_k_composition.vee_top_k.stuck | 12 |
| lcl_injected.top_k_composition.vee_top_k.negative | 10 |
| lcl_injected.top_k_composition.vee_top_k.vacation | 2 |
| lcl_injected.top_k_composition.vee_top_k.h3 | 1 |
| lcl_injected.top_k_composition.vee_top_k.occupancy_change | 1 |
| lcl_injected.top_k_composition.vee_top_k.spikes | 1 |
| lcl_injected.top_k_composition.obvious_problems_in_test | 215 |
| lcl_injected.per_kind_model[0].n | 55 |
| lcl_injected.per_kind_model[0].roc_auc_vs_normal | 0.9989 |
| lcl_injected.per_kind_model[0].flagged_share_at_5pct | 1 |
| lcl_injected.per_kind_model[1].n | 62 |
| lcl_injected.per_kind_model[1].roc_auc_vs_normal | 0.9988 |
| lcl_injected.per_kind_model[1].flagged_share_at_5pct | 0.9839 |
| lcl_injected.per_kind_model[2].n | 45 |
| lcl_injected.per_kind_model[2].roc_auc_vs_normal | 0.9936 |
| lcl_injected.per_kind_model[2].flagged_share_at_5pct | 0.9778 |
| lcl_injected.per_kind_model[3].n | 60 |
| lcl_injected.per_kind_model[3].roc_auc_vs_normal | 0.9388 |
| lcl_injected.per_kind_model[3].flagged_share_at_5pct | 0.7167 |
| lcl_injected.per_kind_model[4].n | 54 |
| lcl_injected.per_kind_model[4].roc_auc_vs_normal | 0.6478 |
| lcl_injected.per_kind_model[4].flagged_share_at_5pct | 0.0556 |
| lcl_injected.per_kind_model[5].n | 53 |
| lcl_injected.per_kind_model[5].roc_auc_vs_normal | 0.9991 |
| lcl_injected.per_kind_model[5].flagged_share_at_5pct | 1 |
| lcl_injected.per_kind_model[6].n | 54 |
| lcl_injected.per_kind_model[6].roc_auc_vs_normal | 0.7911 |
| lcl_injected.per_kind_model[6].flagged_share_at_5pct | 0.1481 |
| lcl_injected.per_kind_model[7].n | 30 |
| lcl_injected.per_kind_model[7].roc_auc_vs_normal | 0.9373 |
| lcl_injected.per_kind_model[7].flagged_share_at_5pct | 0.4333 |
| lcl_injected.per_kind_model[8].n | 18 |
| lcl_injected.per_kind_model[8].roc_auc_vs_normal | 0.9177 |
| lcl_injected.per_kind_model[8].flagged_share_at_5pct | 0.7778 |
| lcl_injected.per_kind_model[9].n | 24 |
| lcl_injected.per_kind_model[9].roc_auc_vs_normal | 0.9923 |
| lcl_injected.per_kind_model[9].flagged_share_at_5pct | 0.9583 |
| lcl_injected.per_kind_model[10].n | 25 |
| lcl_injected.per_kind_model[10].roc_auc_vs_normal | 0.9577 |
| lcl_injected.per_kind_model[10].flagged_share_at_5pct | 0.8 |
| lcl_injected.per_kind_model[11].n | 28 |
| lcl_injected.per_kind_model[11].roc_auc_vs_normal | 0.967 |
| lcl_injected.per_kind_model[11].flagged_share_at_5pct | 0.8214 |
| lcl_injected.per_kind_model[12].n | 35 |
| lcl_injected.per_kind_model[12].roc_auc_vs_normal | 0.8965 |
| lcl_injected.per_kind_model[12].flagged_share_at_5pct | 0.5714 |
| lcl_injected.per_kind_model[13].n | 21 |
| lcl_injected.per_kind_model[13].roc_auc_vs_normal | 0.8354 |
| lcl_injected.per_kind_model[13].flagged_share_at_5pct | 0.2381 |
| lcl_injected.per_kind_model[14].n | 33 |
| lcl_injected.per_kind_model[14].roc_auc_vs_normal | 0.8497 |
| lcl_injected.per_kind_model[14].flagged_share_at_5pct | 0.4848 |
| lcl_injected.per_kind_model[15].n | 255 |
| lcl_injected.per_kind_model[15].roc_auc_vs_normal | 0.5391 |
| lcl_injected.per_kind_model[15].flagged_share_at_5pct | 0.0157 |
| lcl_injected.per_kind_model[16].n | 241 |
| lcl_injected.per_kind_model[16].roc_auc_vs_normal | 0.6549 |
| lcl_injected.per_kind_model[16].flagged_share_at_5pct | 0.112 |
| lcl_injected.per_kind_vee[0].n | 55 |
| lcl_injected.per_kind_vee[0].roc_auc_vs_normal | 0.9911 |
| lcl_injected.per_kind_vee[0].flagged_share_at_5pct | 0.8909 |
| lcl_injected.per_kind_vee[1].n | 62 |
| lcl_injected.per_kind_vee[1].roc_auc_vs_normal | 0.9863 |
| lcl_injected.per_kind_vee[1].flagged_share_at_5pct | 0.8871 |
| lcl_injected.per_kind_vee[2].n | 45 |
| lcl_injected.per_kind_vee[2].roc_auc_vs_normal | 0.9624 |
| lcl_injected.per_kind_vee[2].flagged_share_at_5pct | 0.5778 |
| lcl_injected.per_kind_vee[3].n | 60 |
| lcl_injected.per_kind_vee[3].roc_auc_vs_normal | 0.7904 |
| lcl_injected.per_kind_vee[3].flagged_share_at_5pct | 0.05 |
| lcl_injected.per_kind_vee[4].n | 54 |
| lcl_injected.per_kind_vee[4].roc_auc_vs_normal | 0.5805 |
| lcl_injected.per_kind_vee[4].flagged_share_at_5pct | 0.037 |
| lcl_injected.per_kind_vee[5].n | 53 |
| lcl_injected.per_kind_vee[5].roc_auc_vs_normal | 0.9695 |
| lcl_injected.per_kind_vee[5].flagged_share_at_5pct | 0.7925 |
| lcl_injected.per_kind_vee[6].n | 54 |
| lcl_injected.per_kind_vee[6].roc_auc_vs_normal | 0.7162 |
| lcl_injected.per_kind_vee[6].flagged_share_at_5pct | 0.0185 |
| lcl_injected.per_kind_vee[7].n | 30 |
| lcl_injected.per_kind_vee[7].roc_auc_vs_normal | 0.8222 |
| lcl_injected.per_kind_vee[7].flagged_share_at_5pct | 0.2 |
| lcl_injected.per_kind_vee[8].n | 18 |
| lcl_injected.per_kind_vee[8].roc_auc_vs_normal | 0.8519 |
| lcl_injected.per_kind_vee[8].flagged_share_at_5pct | 0.0556 |
| lcl_injected.per_kind_vee[9].n | 24 |
| lcl_injected.per_kind_vee[9].roc_auc_vs_normal | 0.8411 |
| lcl_injected.per_kind_vee[9].flagged_share_at_5pct | 0.1667 |
| lcl_injected.per_kind_vee[10].n | 25 |
| lcl_injected.per_kind_vee[10].roc_auc_vs_normal | 0.5772 |
| lcl_injected.per_kind_vee[10].flagged_share_at_5pct | 0 |
| lcl_injected.per_kind_vee[11].n | 28 |
| lcl_injected.per_kind_vee[11].roc_auc_vs_normal | 0.8906 |
| lcl_injected.per_kind_vee[11].flagged_share_at_5pct | 0.0714 |
| lcl_injected.per_kind_vee[12].n | 35 |
| lcl_injected.per_kind_vee[12].roc_auc_vs_normal | 0.4872 |
| lcl_injected.per_kind_vee[12].flagged_share_at_5pct | 0 |
| lcl_injected.per_kind_vee[13].n | 21 |
| lcl_injected.per_kind_vee[13].roc_auc_vs_normal | 0.7789 |
| lcl_injected.per_kind_vee[13].flagged_share_at_5pct | 0 |
| lcl_injected.per_kind_vee[14].n | 33 |
| lcl_injected.per_kind_vee[14].roc_auc_vs_normal | 0.5936 |
| lcl_injected.per_kind_vee[14].flagged_share_at_5pct | 0.0303 |
| lcl_injected.per_kind_vee[15].n | 255 |
| lcl_injected.per_kind_vee[15].roc_auc_vs_normal | 0.7325 |
| lcl_injected.per_kind_vee[15].flagged_share_at_5pct | 0.1333 |
| lcl_injected.per_kind_vee[16].n | 241 |
| lcl_injected.per_kind_vee[16].roc_auc_vs_normal | 0.6644 |
| lcl_injected.per_kind_vee[16].flagged_share_at_5pct | 0.029 |
| lcl_injected.per_kind_rule[0].n | 55 |
| lcl_injected.per_kind_rule[0].roc_auc_vs_normal | 0.9952 |
| lcl_injected.per_kind_rule[0].flagged_share_at_5pct | 0.9818 |
| lcl_injected.per_kind_rule[1].n | 62 |
| lcl_injected.per_kind_rule[1].roc_auc_vs_normal | 0.7383 |
| lcl_injected.per_kind_rule[1].flagged_share_at_5pct | 0.2742 |
| lcl_injected.per_kind_rule[2].n | 45 |
| lcl_injected.per_kind_rule[2].roc_auc_vs_normal | 0.4717 |
| lcl_injected.per_kind_rule[2].flagged_share_at_5pct | 0.0444 |
| lcl_injected.per_kind_rule[3].n | 60 |
| lcl_injected.per_kind_rule[3].roc_auc_vs_normal | 0.4595 |
| lcl_injected.per_kind_rule[3].flagged_share_at_5pct | 0.0833 |
| lcl_injected.per_kind_rule[4].n | 54 |
| lcl_injected.per_kind_rule[4].roc_auc_vs_normal | 0.5066 |
| lcl_injected.per_kind_rule[4].flagged_share_at_5pct | 0.037 |
| lcl_injected.per_kind_rule[5].n | 53 |
| lcl_injected.per_kind_rule[5].roc_auc_vs_normal | 0.9017 |
| lcl_injected.per_kind_rule[5].flagged_share_at_5pct | 0.7547 |
| lcl_injected.per_kind_rule[6].n | 54 |
| lcl_injected.per_kind_rule[6].roc_auc_vs_normal | 0.7466 |
| lcl_injected.per_kind_rule[6].flagged_share_at_5pct | 0.1296 |
| lcl_injected.per_kind_rule[7].n | 30 |
| lcl_injected.per_kind_rule[7].roc_auc_vs_normal | 0.877 |
| lcl_injected.per_kind_rule[7].flagged_share_at_5pct | 0.4667 |
| lcl_injected.per_kind_rule[8].n | 18 |
| lcl_injected.per_kind_rule[8].roc_auc_vs_normal | 0.8726 |
| lcl_injected.per_kind_rule[8].flagged_share_at_5pct | 0.6111 |
| lcl_injected.per_kind_rule[9].n | 24 |
| lcl_injected.per_kind_rule[9].roc_auc_vs_normal | 0.8775 |
| lcl_injected.per_kind_rule[9].flagged_share_at_5pct | 0.375 |
| lcl_injected.per_kind_rule[10].n | 25 |
| lcl_injected.per_kind_rule[10].roc_auc_vs_normal | 0.4753 |
| lcl_injected.per_kind_rule[10].flagged_share_at_5pct | 0 |
| lcl_injected.per_kind_rule[11].n | 28 |
| lcl_injected.per_kind_rule[11].roc_auc_vs_normal | 0.8871 |
| lcl_injected.per_kind_rule[11].flagged_share_at_5pct | 0.6429 |
| lcl_injected.per_kind_rule[12].n | 35 |
| lcl_injected.per_kind_rule[12].roc_auc_vs_normal | 0.5257 |
| lcl_injected.per_kind_rule[12].flagged_share_at_5pct | 0.0857 |
| lcl_injected.per_kind_rule[13].n | 21 |
| lcl_injected.per_kind_rule[13].roc_auc_vs_normal | 0.7824 |
| lcl_injected.per_kind_rule[13].flagged_share_at_5pct | 0.2857 |
| lcl_injected.per_kind_rule[14].n | 33 |
| lcl_injected.per_kind_rule[14].roc_auc_vs_normal | 0.6232 |
| lcl_injected.per_kind_rule[14].flagged_share_at_5pct | 0.0303 |
| lcl_injected.per_kind_rule[15].n | 255 |
| lcl_injected.per_kind_rule[15].roc_auc_vs_normal | 0.7474 |
| lcl_injected.per_kind_rule[15].flagged_share_at_5pct | 0.3176 |
| lcl_injected.per_kind_rule[16].n | 241 |
| lcl_injected.per_kind_rule[16].roc_auc_vs_normal | 0.6243 |
| lcl_injected.per_kind_rule[16].flagged_share_at_5pct | 0.1286 |
| lcl_injected.type_accuracy.family_accuracy_on_problems | 0.8727 |
| lcl_injected.type_accuracy.n | 597 |
| lcl_injected.false_alarms_by_level[0].quintile | 1 |
| lcl_injected.false_alarms_by_level[0].level_kwh_median | 3.37 |
| lcl_injected.false_alarms_by_level[0].false_alarm_rate | 0.0503 |
| lcl_injected.false_alarms_by_level[0].recall | 0.6547 |
| lcl_injected.false_alarms_by_level[0].n_normal | 2467 |
| lcl_injected.false_alarms_by_level[0].n_problem | 139 |
| lcl_injected.false_alarms_by_level[1].quintile | 2 |
| lcl_injected.false_alarms_by_level[1].level_kwh_median | 5.8 |
| lcl_injected.false_alarms_by_level[1].false_alarm_rate | 0.0072 |
| lcl_injected.false_alarms_by_level[1].recall | 0.65 |
| lcl_injected.false_alarms_by_level[1].n_normal | 2485 |
| lcl_injected.false_alarms_by_level[1].n_problem | 120 |
| lcl_injected.false_alarms_by_level[2].quintile | 3 |
| lcl_injected.false_alarms_by_level[2].level_kwh_median | 7.45 |
| lcl_injected.false_alarms_by_level[2].false_alarm_rate | 0.0097 |
| lcl_injected.false_alarms_by_level[2].recall | 0.6774 |
| lcl_injected.false_alarms_by_level[2].n_normal | 2482 |
| lcl_injected.false_alarms_by_level[2].n_problem | 124 |
| lcl_injected.false_alarms_by_level[3].quintile | 4 |
| lcl_injected.false_alarms_by_level[3].level_kwh_median | 9.79 |
| lcl_injected.false_alarms_by_level[3].false_alarm_rate | 0.0176 |
| lcl_injected.false_alarms_by_level[3].recall | 0.6698 |
| lcl_injected.false_alarms_by_level[3].n_normal | 2499 |
| lcl_injected.false_alarms_by_level[3].n_problem | 106 |
| lcl_injected.false_alarms_by_level[4].quintile | 5 |
| lcl_injected.false_alarms_by_level[4].level_kwh_median | 16.11 |
| lcl_injected.false_alarms_by_level[4].false_alarm_rate | 0.016 |
| lcl_injected.false_alarms_by_level[4].recall | 0.713 |
| lcl_injected.false_alarms_by_level[4].n_normal | 2498 |
| lcl_injected.false_alarms_by_level[4].n_problem | 108 |
| lcl_injected.false_alarms_by_level_rule[0].quintile | 1 |
| lcl_injected.false_alarms_by_level_rule[0].level_kwh_median | 3.37 |
| lcl_injected.false_alarms_by_level_rule[0].false_alarm_rate | 0.0843 |
| lcl_injected.false_alarms_by_level_rule[0].recall | 0.3094 |
| lcl_injected.false_alarms_by_level_rule[0].n_normal | 2467 |
| lcl_injected.false_alarms_by_level_rule[0].n_problem | 139 |
| lcl_injected.false_alarms_by_level_rule[1].quintile | 2 |
| lcl_injected.false_alarms_by_level_rule[1].level_kwh_median | 5.8 |
| lcl_injected.false_alarms_by_level_rule[1].false_alarm_rate | 0.0209 |
| lcl_injected.false_alarms_by_level_rule[1].recall | 0.3167 |
| lcl_injected.false_alarms_by_level_rule[1].n_normal | 2485 |
| lcl_injected.false_alarms_by_level_rule[1].n_problem | 120 |
| lcl_injected.false_alarms_by_level_rule[2].quintile | 3 |
| lcl_injected.false_alarms_by_level_rule[2].level_kwh_median | 7.45 |
| lcl_injected.false_alarms_by_level_rule[2].false_alarm_rate | 0.0262 |
| lcl_injected.false_alarms_by_level_rule[2].recall | 0.3226 |
| lcl_injected.false_alarms_by_level_rule[2].n_normal | 2482 |
| lcl_injected.false_alarms_by_level_rule[2].n_problem | 124 |
| lcl_injected.false_alarms_by_level_rule[3].quintile | 4 |
| lcl_injected.false_alarms_by_level_rule[3].level_kwh_median | 9.79 |
| lcl_injected.false_alarms_by_level_rule[3].false_alarm_rate | 0.02 |
| lcl_injected.false_alarms_by_level_rule[3].recall | 0.3208 |
| lcl_injected.false_alarms_by_level_rule[3].n_normal | 2499 |
| lcl_injected.false_alarms_by_level_rule[3].n_problem | 106 |
| lcl_injected.false_alarms_by_level_rule[4].quintile | 5 |
| lcl_injected.false_alarms_by_level_rule[4].level_kwh_median | 16.11 |
| lcl_injected.false_alarms_by_level_rule[4].false_alarm_rate | 0.0348 |
| lcl_injected.false_alarms_by_level_rule[4].recall | 0.3148 |
| lcl_injected.false_alarms_by_level_rule[4].n_normal | 2498 |
| lcl_injected.false_alarms_by_level_rule[4].n_problem | 108 |

</details>

<details><summary>reports/A/robustness.json</summary>

[Sursa](../../reports/A/robustness.json) · SHA256 `8fce30bb271631f7f0e016bb8e25934a718b825b6089f38e34e5382c834514b6`

| Câmp | Valoare |
|---|---:|
| missing_data_curve[0].missing_days_share | 0 |
| missing_data_curve[0].precision_at_k | 1 |
| missing_data_curve[0].pr_auc | 0.6918 |
| missing_data_curve[0].roc_auc | 0.9104 |
| missing_data_curve[0].brier | 0.0232 |
| missing_data_curve[0].data_abstain_share | 0.0048 |
| missing_data_curve[0].problem_decisions | 541 |
| missing_data_curve[0].unsure_decisions | 573 |
| missing_data_curve[1].missing_days_share | 0.1 |
| missing_data_curve[1].precision_at_k | 1 |
| missing_data_curve[1].pr_auc | 0.6228 |
| missing_data_curve[1].roc_auc | 0.8838 |
| missing_data_curve[1].brier | 0.0276 |
| missing_data_curve[1].data_abstain_share | 0.0048 |
| missing_data_curve[1].problem_decisions | 660 |
| missing_data_curve[1].unsure_decisions | 845 |
| missing_data_curve[2].missing_days_share | 0.3 |
| missing_data_curve[2].precision_at_k | 1 |
| missing_data_curve[2].pr_auc | 0.5947 |
| missing_data_curve[2].roc_auc | 0.8491 |
| missing_data_curve[2].brier | 0.0327 |
| missing_data_curve[2].data_abstain_share | 0.0049 |
| missing_data_curve[2].problem_decisions | 873 |
| missing_data_curve[2].unsure_decisions | 1957 |
| missing_data_curve[3].missing_days_share | 0.5 |
| missing_data_curve[3].precision_at_k | 1 |
| missing_data_curve[3].pr_auc | 0.5585 |
| missing_data_curve[3].roc_auc | 0.8113 |
| missing_data_curve[3].brier | 0.0373 |
| missing_data_curve[3].data_abstain_share | 0.0073 |
| missing_data_curve[3].problem_decisions | 934 |
| missing_data_curve[3].unsure_decisions | 3578 |
| missing_data_curve[4].missing_days_share | 0.7 |
| missing_data_curve[4].precision_at_k | 0.9937 |
| missing_data_curve[4].pr_auc | 0.4345 |
| missing_data_curve[4].roc_auc | 0.7723 |
| missing_data_curve[4].brier | 0.06 |
| missing_data_curve[4].data_abstain_share | 0.8355 |
| missing_data_curve[4].problem_decisions | 2356 |
| missing_data_curve[4].unsure_decisions | 2653 |
| sgcc_time_split.model.pr_auc | 0.1863 |
| sgcc_time_split.model.roc_auc | 0.703 |
| sgcc_time_split.model.precision_at_k | 0.4 |
| sgcc_time_split.model.recall_at_k | 0.047 |
| sgcc_time_split.rule.pr_auc | 0.075 |
| sgcc_time_split.rule.roc_auc | 0.4658 |
| sgcc_time_split.rule.precision_at_k | 0.0353 |
| sgcc_time_split.rule.recall_at_k | 0.0041 |
| sgcc_time_split.missing_share_train_window | 0.3375 |
| sgcc_time_split.missing_share_test_window | 0.0859 |

</details>

<details><summary>reports/A/tuning_optuna.json</summary>

[Sursa](../../reports/A/tuning_optuna.json) · SHA256 `431f574b09385d0950bd0ae712c5201d7ad6895461a3867b3a1cab03fff0fd54`

| Câmp | Valoare |
|---|---:|
| n_train | 93051 |
| households_train | 4914 |
| val_subtle_pr_auc.livrat | 0.5749 |
| val_subtle_pr_auc.gasit | 0.586 |
| test.livrat.subtle_precision_at_k | 0.8906 |
| test.livrat.subtle_recall_at_k | 0.2984 |
| test.livrat.subtle_pr_auc | 0.5175 |
| test.livrat.subtle_precision_at_5pct | 0.3541 |
| test.livrat.pr_auc | 0.7344 |
| test.gasit.subtle_precision_at_k | 0.8672 |
| test.gasit.subtle_recall_at_k | 0.2906 |
| test.gasit.subtle_pr_auc | 0.5057 |
| test.gasit.subtle_precision_at_5pct | 0.3495 |
| test.gasit.pr_auc | 0.7258 |
| test.delta_subtle_pr_auc_ci90 | [-0.0218, -0.0029] |

</details>

<details><summary>reports/B/backtest_summary.json</summary>

[Sursa](../../reports/B/backtest_summary.json) · SHA256 `6db68e4474cec225bf9684c97f974a445bca71291f7ddc1cf9e9181bbe7e5797`

| Câmp | Valoare |
|---|---:|
| banat_2025_07_07_08.p_banat | 0.308 |
| banat_2025_07_07_08.p_rest | 0.068 |
| banat_2025_07_07_08.crews_banat_zone_days | 22 |
| banat_2025_07_07_08.crews_rest_zone_days | 0 |
| slobozia_2025_07_17.rank | 1 |
| slobozia_2025_07_17.zones | 26 |
| slobozia_2025_07_17.p | 0.357 |
| dobrogea_2023_11_26.p_dobrogea | 0.868 |
| dobrogea_2023_11_26.p_rest | 0.092 |
| dobrogea_2023_11_26.crews_dobrogea | 10 |
| dobrogea_2023_11_26.zones_dobrogea | 10 |

</details>

<details><summary>reports/B/experiments.json</summary>

[Sursa](../../reports/B/experiments.json) · SHA256 `252ae2667120b7024990f4a6420f3ff3a3e1d63fc11255631e9436720a3c6217`

| Câmp | Valoare |
|---|---:|
| [baza].pr_auc | 0.2777 |
| [baza].brier | 0.0841 |
| [baza].prevalence | 0.1032 |
| [fara_monotonie].pr_auc | 0.2738 |
| [fara_monotonie].brier | 0.0843 |
| [fara_monotonie].prevalence | 0.1032 |
| [fara_intarzieri].pr_auc | 0.273 |
| [fara_intarzieri].brier | 0.0844 |
| [fara_intarzieri].prevalence | 0.1032 |
| [doar_vreme].pr_auc | 0.2342 |
| [doar_vreme].brier | 0.0867 |
| [doar_vreme].prevalence | 0.1032 |
| [clima_locala].pr_auc | 0.2762 |
| [clima_locala].brier | 0.0841 |
| [clima_locala].prevalence | 0.1032 |
| [ploaie_extra].pr_auc | 0.2754 |
| [ploaie_extra].brier | 0.0843 |
| [ploaie_extra].prevalence | 0.1032 |
| [prag_2pct].pr_auc | 0.1968 |
| [prag_2pct].brier | 0.0526 |
| [prag_2pct].prevalence | 0.0601 |
| [prag_5pct].pr_auc | 0.1004 |
| [prag_5pct].brier | 0.0212 |
| [prag_5pct].prevalence | 0.0222 |
| [arbori_mai_mari].pr_auc | 0.2746 |
| [arbori_mai_mari].brier | 0.0842 |
| [arbori_mai_mari].prevalence | 0.1032 |
| [coada_rafalei].pr_auc | 0.2763 |
| [coada_rafalei].brier | 0.0842 |
| [coada_rafalei].prevalence | 0.1032 |
| [zapada_uda_viscol].pr_auc | 0.2754 |
| [zapada_uda_viscol].brier | 0.0842 |
| [zapada_uda_viscol].prevalence | 0.1032 |
| [cu_temperaturi].pr_auc | 0.2829 |
| [cu_temperaturi].brier | 0.0837 |
| [cu_temperaturi].prevalence | 0.1032 |
| [mai_putine_variabile].pr_auc | 0.2689 |
| [mai_putine_variabile].brier | 0.0847 |
| [mai_putine_variabile].prevalence | 0.1032 |

</details>

<details><summary>reports/B/experiments_extra.json</summary>

[Sursa](../../reports/B/experiments_extra.json) · SHA256 `4ce26b8f722ca44caeb39d4fd183e2d1e28e3da9551cea53c94df81274fa87f0`

| Câmp | Valoare |
|---|---:|
| meta.train_years | [2023, 2024] |
| meta.test_year | 2025 |
| meta.counties | 80 |
| meta.test_rows | 29200 |
| meta.prevalence_test | 0.1032 |
| rows[baza].pr_auc | 0.2777 |
| rows[baza].brier | 0.0841 |
| rows[ore_cu_rafale].pr_auc | 0.2753 |
| rows[ore_cu_rafale].brier | 0.0842 |
| rows[ore_cu_rafale].delta_pr_auc_ci90 | [-0.0038, -0.0003] |
| rows[sol_umed].pr_auc | 0.2745 |
| rows[sol_umed].brier | 0.0844 |
| rows[sol_umed].delta_pr_auc_ci90 | [-0.0053, -0.0007] |
| rows[presiune].pr_auc | 0.2778 |
| rows[presiune].brier | 0.084 |
| rows[presiune].delta_pr_auc_ci90 | [-0.0025, 0.0035] |
| rows[convectie].pr_auc | 0.2865 |
| rows[convectie].brier | 0.0835 |
| rows[convectie].delta_pr_auc_ci90 | [0.0025, 0.016] |
| rows[zapada_strat].pr_auc | 0.2785 |
| rows[zapada_strat].brier | 0.0841 |
| rows[zapada_strat].delta_pr_auc_ci90 | [-0.0006, 0.0024] |
| rows[umiditate].pr_auc | 0.2749 |
| rows[umiditate].brier | 0.0842 |
| rows[umiditate].delta_pr_auc_ci90 | [-0.0045, -0.0009] |
| rows[directie_rafala].pr_auc | 0.2754 |
| rows[directie_rafala].brier | 0.0842 |
| rows[directie_rafala].delta_pr_auc_ci90 | [-0.0046, -0.0] |
| rows[toate_noi].pr_auc | 0.2855 |
| rows[toate_noi].brier | 0.0836 |
| rows[toate_noi].delta_pr_auc_ci90 | [0.0001, 0.0165] |
| rows[rafale_sol_presiune_convectie].pr_auc | 0.2818 |
| rows[rafale_sol_presiune_convectie].brier | 0.0837 |
| rows[rafale_sol_presiune_convectie].delta_pr_auc_ci90 | [-0.0034, 0.0124] |

</details>

<details><summary>reports/B/metrics.json</summary>

[Sursa](../../reports/B/metrics.json) · SHA256 `fa1484c9cd8b65f2b947de4be6e6d584902b645741590ef19a6984e792e01e10`

| Câmp | Valoare |
|---|---:|
| test_size | 29200 |
| metrics.pr_auc | 0.2777 |
| metrics.roc_auc | 0.7246 |
| metrics.brier | 0.0841 |
| metrics.log_loss | 0.297 |
| metrics.precision_at_thr | 0.2803 |
| metrics.recall_at_thr | 0.4094 |
| metrics.f1_at_thr | 0.3327 |
| metrics.recall_severe_at_thr | 0.4977 |
| metrics.recall_extreme_at_thr | 0.5417 |
| metrics.alerts_per_100_zone_days | 15.0788 |
| metrics.pinball_q10 | 0.0693 |
| metrics.pinball_q50 | 0.2389 |
| metrics.pinball_q90 | 0.1439 |
| metrics.pinball_mean | 0.1507 |
| metrics.coverage_p10_p90 | 0.8079 |
| metrics.coverage_p10_p90_without_conformal | 0.722 |
| metrics.prevalence | 0.1032 |
| metrics.capacity_k | 8 |
| metrics.capacity_customers_covered | 0.1671 |
| metrics.capacity_customers_covered_gust_rule | 0.146 |
| metrics.capacity_customers_covered_clim | 0.1227 |
| metrics.capacity_customers_covered_random | 0.0763 |
| metrics.capacity_customers_covered_oracle | 0.8855 |
| metrics.decision_threshold | 0.16 |
| metrics.pr_auc_gust_rule | 0.182 |
| metrics.pr_auc_clim_month | 0.1198 |
| metrics.loso_pr_auc_mean | 0.2586 |
| metrics.loso_clim_month_pr_auc_mean | 0.1218 |
| baseline_metrics.pr_auc | 0.1507 |
| baseline_metrics.roc_auc | 0.6116 |
| baseline_metrics.brier | 0.0914 |
| baseline_metrics.log_loss | 0.3266 |
| baseline_metrics.precision_at_thr | 0.1548 |
| baseline_metrics.recall_at_thr | 0.362 |
| baseline_metrics.f1_at_thr | 0.2168 |
| baseline_metrics.recall_severe_at_thr | 0.3991 |
| baseline_metrics.recall_extreme_at_thr | 0.4167 |
| baseline_metrics.alerts_per_100_zone_days | 24.1404 |
| synthetic_share | 0 |

</details>

<details><summary>reports/B/metrics_detail.json</summary>

[Sursa](../../reports/B/metrics_detail.json) · SHA256 `ca53fc5c5f2f0ce37a488f54ad2102bb2f967ca14c0ec0e2866203603855a1dd`

| Câmp | Valoare |
|---|---:|
| main.prevalence_test | 0.103219 |
| main.test_rows | 29200 |
| main.test_events | 3014 |
| main.model.pr_auc | 0.277674 |
| main.model.roc_auc | 0.72455 |
| main.model.brier | 0.0841109 |
| main.model.log_loss | 0.297036 |
| main.model.threshold | 0.16 |
| main.model.precision_at_thr | 0.280263 |
| main.model.recall_at_thr | 0.409423 |
| main.model.recall_severe_at_thr | 0.497689 |
| main.model.recall_extreme_at_thr | 0.541667 |
| main.model.alerts_per_100_zone_days | 15.0788 |
| main.model.f1_at_thr | 0.332749 |
| main.model.pinball_q10 | 0.0692842 |
| main.model.pinball_q50 | 0.238868 |
| main.model.pinball_q90 | 0.143882 |
| main.model.pinball_mean | 0.150678 |
| main.model.coverage_p10_p90 | 0.807896 |
| main.model.coverage_p10_p90_without_conformal | 0.721964 |
| main.model.conformal_offset_log | 0.059939 |
| main.clim_month.pr_auc | 0.119776 |
| main.clim_month.roc_auc | 0.551915 |
| main.clim_month.brier | 0.0923849 |
| main.clim_month.log_loss | 0.331348 |
| main.clim_month.threshold | 0.1 |
| main.clim_month.precision_at_thr | 0.123039 |
| main.clim_month.recall_at_thr | 0.499668 |
| main.clim_month.recall_severe_at_thr | 0.526965 |
| main.clim_month.recall_extreme_at_thr | 0.541667 |
| main.clim_month.alerts_per_100_zone_days | 41.9178 |
| main.clim_month.f1_at_thr | 0.197456 |
| main.clim_month.pinball_q10 | 0.0672931 |
| main.clim_month.pinball_q50 | 0.241126 |
| main.clim_month.pinball_q90 | 0.151157 |
| main.clim_month.pinball_mean | 0.153192 |
| main.clim_month.coverage_p10_p90 | 0.811214 |
| main.gust_rule.pr_auc | 0.182035 |
| main.gust_rule.roc_auc | 0.610908 |
| main.gust_rule.brier | 0.0889944 |
| main.gust_rule.log_loss | 0.319131 |
| main.gust_rule.threshold | 0.1 |
| main.gust_rule.precision_at_thr | 0.179707 |
| main.gust_rule.recall_at_thr | 0.354346 |
| main.gust_rule.recall_severe_at_thr | 0.42681 |
| main.gust_rule.recall_extreme_at_thr | 0.458333 |
| main.gust_rule.alerts_per_100_zone_days | 20.3527 |
| main.gust_rule.f1_at_thr | 0.238473 |
| main.gust_rule_70kmh.pr_auc | 0.133325 |
| main.gust_rule_70kmh.roc_auc | 0.545546 |
| main.gust_rule_70kmh.brier | 0.111575 |
| main.gust_rule_70kmh.log_loss | 1.54147 |
| main.gust_rule_70kmh.threshold | 0.5 |
| main.gust_rule_70kmh.precision_at_thr | 0.368534 |
| main.gust_rule_70kmh.recall_at_thr | 0.11347 |
| main.gust_rule_70kmh.recall_severe_at_thr | 0.151002 |
| main.gust_rule_70kmh.recall_extreme_at_thr | 0.147727 |
| main.gust_rule_70kmh.alerts_per_100_zone_days | 3.17808 |
| main.gust_rule_70kmh.f1_at_thr | 0.173516 |
| main.clim_county_month.pr_auc | 0.150682 |
| main.clim_county_month.roc_auc | 0.611614 |
| main.clim_county_month.brier | 0.0913715 |
| main.clim_county_month.log_loss | 0.326559 |
| main.clim_county_month.threshold | 0.13 |
| main.clim_county_month.precision_at_thr | 0.154774 |
| main.clim_county_month.recall_at_thr | 0.361977 |
| main.clim_county_month.recall_severe_at_thr | 0.399076 |
| main.clim_county_month.recall_extreme_at_thr | 0.416667 |
| main.clim_county_month.alerts_per_100_zone_days | 24.1404 |
| main.clim_county_month.f1_at_thr | 0.216834 |
| train_info.rows | 58480 |
| train_info.events | 5595 |
| train_info.counties | 80 |
| train_info.years | [2023, 2024] |
| capacity.k_crews_per_day | 8 |
| capacity.zones | 80 |
| capacity.results.model.customers_covered_share | 0.1671 |
| capacity.results.model.events_caught_share | 0.2153 |
| capacity.results.model.alert_precision | 0.2223 |
| capacity.results.regula_rafala.customers_covered_share | 0.146 |
| capacity.results.regula_rafala.events_caught_share | 0.149 |
| capacity.results.regula_rafala.alert_precision | 0.1538 |
| capacity.results.climatologie_comitat_luna.customers_covered_share | 0.1227 |
| capacity.results.climatologie_comitat_luna.events_caught_share | 0.1639 |
| capacity.results.climatologie_comitat_luna.alert_precision | 0.1692 |
| capacity.results.aleator.customers_covered_share | 0.0763 |
| capacity.results.aleator.events_caught_share | 0.0946 |
| capacity.results.aleator.alert_precision | 0.0976 |
| capacity.results.oracol.customers_covered_share | 0.8855 |
| capacity.results.oracol.events_caught_share | 0.7157 |
| capacity.results.oracol.alert_precision | 0.7387 |
| decision_value.model_la_prag.alerts | 4403 |
| decision_value.model_la_prag.events_caught | 1234 |
| decision_value.model_la_prag.net_lei | 4.56639e+07 |
| decision_value.model_la_prag.net_lei_per_1000_zone_days | 1.56383e+06 |
| decision_value.regula_rafala_70kmh.alerts | 928 |
| decision_value.regula_rafala_70kmh.events_caught | 342 |
| decision_value.regula_rafala_70kmh.net_lei | 1.51612e+07 |
| decision_value.regula_rafala_70kmh.net_lei_per_1000_zone_days | 519221 |
| decision_value.climatologie_la_prag.alerts | 7049 |
| decision_value.climatologie_la_prag.events_caught | 1091 |
| decision_value.climatologie_la_prag.net_lei | 3.06738e+07 |
| decision_value.climatologie_la_prag.net_lei_per_1000_zone_days | 1.05047e+06 |
| decision_value.mereu.alerts | 29200 |
| decision_value.mereu.events_caught | 3014 |
| decision_value.mereu.net_lei | 7.45109e+07 |
| decision_value.mereu.net_lei_per_1000_zone_days | 2.55174e+06 |
| decision_value.niciodata.alerts | 0 |
| decision_value.niciodata.events_caught | 0 |
| decision_value.niciodata.net_lei | 0 |
| decision_value.niciodata.net_lei_per_1000_zone_days | 0 |
| decision_value.oracol_doar_evenimente.alerts | 3014 |
| decision_value.oracol_doar_evenimente.events_caught | 3014 |
| decision_value.oracol_doar_evenimente.net_lei | 1.45213e+08 |
| decision_value.oracol_doar_evenimente.net_lei_per_1000_zone_days | 4.97305e+06 |
| decision_value_assumptions.preposition_cost_lei_per_crew_shift | 2700 |
| decision_value_assumptions.cost_per_customer_hour_lei | 12 |
| decision_value_assumptions.restoration_speedup_hours | 2.5 |
| loso.IL.prevalence | 0.0652055 |
| loso.IL.events | 238 |
| loso.IL.model_pr_auc | 0.206221 |
| loso.IL.model_brier | 0.0583144 |
| loso.IL.clim_month_pr_auc | 0.0775175 |
| loso.IL.clim_month_brier | 0.0623916 |
| loso.IL.gust_rule_pr_auc | 0.120843 |
| loso.IL.model_recall_severe | 0.52 |
| loso.KY.prevalence | 0.124384 |
| loso.KY.events | 454 |
| loso.KY.model_pr_auc | 0.265777 |
| loso.KY.model_brier | 0.102509 |
| loso.KY.clim_month_pr_auc | 0.137206 |
| loso.KY.clim_month_brier | 0.109724 |
| loso.KY.gust_rule_pr_auc | 0.203079 |
| loso.KY.model_recall_severe | 0.504587 |
| loso.MI.prevalence | 0.101918 |
| loso.MI.events | 372 |
| loso.MI.model_pr_auc | 0.272696 |
| loso.MI.model_brier | 0.0837326 |
| loso.MI.clim_month_pr_auc | 0.132885 |
| loso.MI.clim_month_brier | 0.0908162 |
| loso.MI.gust_rule_pr_auc | 0.197256 |
| loso.MI.model_recall_severe | 0.43 |
| loso.MO.prevalence | 0.0967123 |
| loso.MO.events | 353 |
| loso.MO.model_pr_auc | 0.232151 |
| loso.MO.model_brier | 0.0822713 |
| loso.MO.clim_month_pr_auc | 0.116323 |
| loso.MO.clim_month_brier | 0.0869641 |
| loso.MO.gust_rule_pr_auc | 0.173905 |
| loso.MO.model_recall_severe | 0.5 |
| loso.NY.prevalence | 0.0747945 |
| loso.NY.events | 273 |
| loso.NY.model_pr_auc | 0.236787 |
| loso.NY.model_brier | 0.0681427 |
| loso.NY.clim_month_pr_auc | 0.0708794 |
| loso.NY.clim_month_brier | 0.070928 |
| loso.NY.gust_rule_pr_auc | 0.205018 |
| loso.NY.model_recall_severe | 0.568627 |
| loso.OH.prevalence | 0.0994521 |
| loso.OH.events | 363 |
| loso.OH.model_pr_auc | 0.244331 |
| loso.OH.model_brier | 0.0840333 |
| loso.OH.clim_month_pr_auc | 0.112102 |
| loso.OH.clim_month_brier | 0.0894383 |
| loso.OH.gust_rule_pr_auc | 0.174974 |
| loso.OH.model_recall_severe | 0.571429 |
| loso.PA.prevalence | 0.128767 |
| loso.PA.events | 470 |
| loso.PA.model_pr_auc | 0.285436 |
| loso.PA.model_brier | 0.10484 |
| loso.PA.clim_month_pr_auc | 0.138306 |
| loso.PA.clim_month_brier | 0.11364 |
| loso.PA.gust_rule_pr_auc | 0.214633 |
| loso.PA.model_recall_severe | 0.369863 |
| loso.VA.prevalence | 0.134521 |
| loso.VA.events | 491 |
| loso.VA.model_pr_auc | 0.325477 |
| loso.VA.model_brier | 0.108055 |
| loso.VA.clim_month_pr_auc | 0.189529 |
| loso.VA.clim_month_brier | 0.116499 |
| loso.VA.gust_rule_pr_auc | 0.216367 |
| loso.VA.model_recall_severe | 0.396552 |
| loso_summary.model_pr_auc_mean | 0.25861 |
| loso_summary.clim_month_pr_auc_mean | 0.121844 |
| loso_summary.gust_rule_pr_auc_mean | 0.188259 |
| loso_summary.states_model_beats_clim | 8 |
| loso_summary.states | 8 |

</details>

<details><summary>reports/B/metrics_ssen.json</summary>

[Sursa](../../reports/B/metrics_ssen.json) · SHA256 `42796e062210045c77e75dd56a3c8dda47e92c7d92f8c4e525cdb943eee9a656`

| Câmp | Valoare |
|---|---:|
| test_size | 3655 |
| metrics.pr_auc | 0.2961 |
| metrics.roc_auc | 0.6924 |
| metrics.brier | 0.0872 |
| metrics.threshold | 0.16 |
| metrics.precision_at_thr | 0.3807 |
| metrics.recall_at_thr | 0.3174 |
| metrics.recall_severe_at_thr | 0.5909 |
| metrics.recall_extreme_at_thr | 0.6897 |
| metrics.prevalence | 0.1086 |
| metrics.pr_auc_us_model_on_this_test | 0.2765 |
| metrics.pr_auc_gust_rule | 0.2471 |
| baseline_metrics.pr_auc | 0.1609 |
| baseline_metrics.roc_auc | 0.6517 |
| baseline_metrics.brier | 0.0948 |
| baseline_metrics.threshold | 0.13 |
| baseline_metrics.precision_at_thr | 0.1772 |
| baseline_metrics.recall_at_thr | 0.3753 |
| baseline_metrics.recall_severe_at_thr | 0.4015 |
| baseline_metrics.recall_extreme_at_thr | 0.3448 |
| synthetic_share | 0 |

</details>

<details><summary>reports/B/metrics_ssen_detail.json</summary>

[Sursa](../../reports/B/metrics_ssen_detail.json) · SHA256 `cb9c1cbb6a7f8cad5bc843d85c8b0d2c200ae6175a54f9c88ae9b620ebc9e59e`

| Câmp | Valoare |
|---|---:|
| test_rows | 3655 |
| test_events | 397 |
| prevalence_test | 0.1086 |
| train_rows | 14610 |
| train_events | 1313 |
| ssen_model.pr_auc | 0.2961 |
| ssen_model.roc_auc | 0.6924 |
| ssen_model.brier | 0.0872 |
| ssen_model.threshold | 0.16 |
| ssen_model.precision_at_thr | 0.3807 |
| ssen_model.recall_at_thr | 0.3174 |
| ssen_model.recall_severe_at_thr | 0.5909 |
| ssen_model.recall_extreme_at_thr | 0.6897 |
| clim_district_month.pr_auc | 0.1609 |
| clim_district_month.roc_auc | 0.6517 |
| clim_district_month.brier | 0.0948 |
| clim_district_month.threshold | 0.13 |
| clim_district_month.precision_at_thr | 0.1772 |
| clim_district_month.recall_at_thr | 0.3753 |
| clim_district_month.recall_severe_at_thr | 0.4015 |
| clim_district_month.recall_extreme_at_thr | 0.3448 |
| gust_rule.pr_auc | 0.2471 |
| gust_rule.roc_auc | 0.6445 |
| us_model_on_ssen_test.pr_auc | 0.2765 |
| us_model_on_ssen_test.roc_auc | 0.6201 |
| ssen_model_on_us_test_2025.pr_auc | 0.1591 |
| ssen_model_on_us_test_2025.roc_auc | 0.5927 |
| ssen_model_on_us_test_2025.prevalence | 0.1032 |
| us_model_on_us_test_2025_pr_auc | 0.2777 |
| romania_backtest.banat_2025_07_07_08.ssen_p_banat | 0.094 |
| romania_backtest.banat_2025_07_07_08.ssen_p_rest | 0.029 |
| romania_backtest.banat_2025_07_07_08.us.p_banat | 0.308 |
| romania_backtest.banat_2025_07_07_08.us.p_rest | 0.068 |
| romania_backtest.banat_2025_07_07_08.us.crews_banat_zone_days | 22 |
| romania_backtest.banat_2025_07_07_08.us.crews_rest_zone_days | 0 |
| romania_backtest.slobozia_2025_07_17.ssen_rank | 2 |
| romania_backtest.slobozia_2025_07_17.ssen_p | 0.124 |
| romania_backtest.slobozia_2025_07_17.us.rank | 1 |
| romania_backtest.slobozia_2025_07_17.us.zones | 26 |
| romania_backtest.slobozia_2025_07_17.us.p | 0.357 |
| romania_backtest.dobrogea_2023_11_26.ssen_p_dobrogea | 0.732 |
| romania_backtest.dobrogea_2023_11_26.ssen_p_rest | 0.218 |
| romania_backtest.dobrogea_2023_11_26.us.p_dobrogea | 0.868 |
| romania_backtest.dobrogea_2023_11_26.us.p_rest | 0.092 |
| romania_backtest.dobrogea_2023_11_26.us.crews_dobrogea | 10 |
| romania_backtest.dobrogea_2023_11_26.us.zones_dobrogea | 10 |

</details>

<details><summary>reports/B/romania_eval.json</summary>

[Sursa](../../reports/B/romania_eval.json) · SHA256 `e07b44755567e5c7113342ec2775a3194de52188300b933708abb6a6e3800955`

| Câmp | Valoare |
|---|---:|
| model_threshold | 0.16 |
| model_train_info.rows | 58480 |
| model_train_info.events | 5595 |
| model_train_info.counties | 80 |
| model_train_info.years | [2023, 2024] |
| labels.rows_ro | 7457 |
| labels.planned | 730 |
| labels.unplanned | 6727 |
| labels.unplanned_customers_pos | 5233 |
| labels.open_at_snapshot | 61 |
| assignment.median_km_to_zone | 9.3 |
| assignment.p95_km_to_zone | 31.6 |
| assignment.rows_over_60km | 2 |
| assignment.rows_per_zone.B-BUCURESTI | 1782 |
| assignment.rows_per_zone.CT-CONSTANTA | 311 |
| assignment.rows_per_zone.TM-TIMISOARA | 309 |
| assignment.rows_per_zone.AR-INEU | 257 |
| assignment.rows_per_zone.AR-ARAD | 252 |
| assignment.rows_per_zone.GR-BOLINTIN-VALE | 240 |
| assignment.rows_per_zone.HD-BRAD | 210 |
| assignment.rows_per_zone.CL-CALARASI | 201 |
| assignment.rows_per_zone.CL-OLTENITA | 200 |
| assignment.rows_per_zone.IF-BUFTEA | 170 |
| assignment.rows_per_zone.CT-MEDGIDIA | 157 |
| assignment.rows_per_zone.GR-GIURGIU | 131 |
| assignment.rows_per_zone.IL-SLOBOZIA | 129 |
| assignment.rows_per_zone.HD-PETROSANI | 120 |
| assignment.rows_per_zone.HD-DEVA | 112 |
| assignment.rows_per_zone.IL-URZICENI | 90 |
| assignment.rows_per_zone.TL-BABADAG | 88 |
| assignment.rows_per_zone.TM-LUGOJ | 81 |
| assignment.rows_per_zone.TL-TULCEA | 76 |
| assignment.rows_per_zone.TM-SANNICOLAU-MARE | 72 |
| assignment.rows_per_zone.CS-CARANSEBES | 63 |
| assignment.rows_per_zone.CT-MANGALIA | 59 |
| assignment.rows_per_zone.CS-RESITA | 55 |
| assignment.rows_per_zone.TL-MACIN | 38 |
| assignment.rows_per_zone.AR-LIPOVA | 16 |
| assignment.rows_per_zone.CS-ORAVITA | 14 |
| duration_hours.median | 1.88 |
| duration_hours.p95 | 276.7 |
| duration_hours.over_72h | 836 |
| archive.rows | 520 |
| archive.days | 20 |
| archive.zones | 26 |
| archive.events | 303 |
| archive.severe_events | 67 |
| archive.prevalence | 0.5827 |
| archive.ranking.p_model.pr_auc | 0.6556 |
| archive.ranking.p_model.roc_auc | 0.5659 |
| archive.ranking.gust_max.pr_auc | 0.6314 |
| archive.ranking.gust_max.roc_auc | 0.5563 |
| archive.ranking.zone_rate_loo.pr_auc | 0.8176 |
| archive.ranking.zone_rate_loo.roc_auc | 0.8055 |
| archive.ranking.small_zone.pr_auc | 0.5758 |
| archive.ranking.small_zone.roc_auc | 0.457 |
| archive.ranking.random.pr_auc | 0.5862 |
| archive.ranking.random.roc_auc | 0.5092 |
| archive.ranking_ci95.p_model.pr_auc | [0.5951, 0.7116] |
| archive.ranking_ci95.p_model.roc_auc | [0.5167, 0.6152] |
| archive.ranking_ci95.p_model.pr_auc_minus_base | [0.03, 0.1183] |
| archive.ranking_ci95.gust_max.pr_auc | [0.5557, 0.7091] |
| archive.ranking_ci95.gust_max.roc_auc | [0.5055, 0.6042] |
| archive.ranking_ci95.gust_max.pr_auc_minus_base | [-0.0003, 0.1049] |
| archive.ranking_ci95.small_zone.pr_auc | [0.5133, 0.6367] |
| archive.ranking_ci95.small_zone.roc_auc | [0.4298, 0.4848] |
| archive.ranking_ci95.small_zone.pr_auc_minus_base | [-0.03, 0.0233] |
| archive.pr_auc_model_vs.gust_max.diff | 0.023 |
| archive.pr_auc_model_vs.gust_max.ci95 | [-0.0081, 0.0589] |
| archive.pr_auc_model_vs.gust_max.share_a_better | 0.922 |
| archive.pr_auc_model_vs.small_zone.diff | 0.0779 |
| archive.pr_auc_model_vs.small_zone.ci95 | [0.025, 0.133] |
| archive.pr_auc_model_vs.small_zone.share_a_better | 0.998 |
| archive.pr_auc_model_vs.zone_rate_loo.diff | -0.1652 |
| archive.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.2233, -0.1013] |
| archive.pr_auc_model_vs.zone_rate_loo.share_a_better | 0 |
| archive.probabilistic.brier_model | 0.5066 |
| archive.probabilistic.brier_constant_prevalence | 0.2432 |
| archive.probabilistic.brier_us_train_rate | 0.4803 |
| archive.probabilistic.log_loss_model | 1.7169 |
| archive.probabilistic.ece_10bins | 0.5167 |
| archive.probabilistic.mean_predicted | 0.066 |
| archive.probabilistic.observed_rate | 0.5827 |
| archive.reliability[0].n | 238 |
| archive.reliability[0].observed | 0.5504 |
| archive.reliability[0].predicted | 0.0376 |
| archive.reliability[1].n | 229 |
| archive.reliability[1].observed | 0.5764 |
| archive.reliability[1].predicted | 0.0688 |
| archive.reliability[2].n | 32 |
| archive.reliability[2].observed | 0.7188 |
| archive.reliability[2].predicted | 0.1186 |
| archive.reliability[3].n | 15 |
| archive.reliability[3].observed | 0.8 |
| archive.reliability[3].predicted | 0.2069 |
| archive.reliability[4].n | 4 |
| archive.reliability[4].observed | 0.75 |
| archive.reliability[4].predicted | 0.3945 |
| archive.reliability[5].n | 2 |
| archive.reliability[5].observed | 1 |
| archive.reliability[5].predicted | 0.5797 |
| archive.at_model_threshold.threshold | 0.16 |
| archive.at_model_threshold.alerts | 21 |
| archive.at_model_threshold.tp | 17 |
| archive.at_model_threshold.fp | 4 |
| archive.at_model_threshold.fn | 286 |
| archive.at_model_threshold.tn | 213 |
| archive.at_model_threshold.precision | 0.8095 |
| archive.at_model_threshold.recall | 0.0561 |
| archive.at_model_threshold.f1 | 0.1049 |
| archive.at_model_threshold.recall_severe | 0.0299 |
| archive.at_model_threshold.false_alarm_rate | 0.0184 |
| archive.at_best_f1_threshold_in_sample.threshold | 0.05 |
| archive.at_best_f1_threshold_in_sample.alerts | 282 |
| archive.at_best_f1_threshold_in_sample.tp | 172 |
| archive.at_best_f1_threshold_in_sample.fp | 110 |
| archive.at_best_f1_threshold_in_sample.fn | 131 |
| archive.at_best_f1_threshold_in_sample.tn | 107 |
| archive.at_best_f1_threshold_in_sample.precision | 0.6099 |
| archive.at_best_f1_threshold_in_sample.recall | 0.5677 |
| archive.at_best_f1_threshold_in_sample.f1 | 0.588 |
| archive.at_best_f1_threshold_in_sample.recall_severe | 0.5672 |
| archive.at_best_f1_threshold_in_sample.false_alarm_rate | 0.5069 |
| archive.gust_rule_70kmh.threshold | 70 |
| archive.gust_rule_70kmh.alerts | 1 |
| archive.gust_rule_70kmh.tp | 1 |
| archive.gust_rule_70kmh.fp | 0 |
| archive.gust_rule_70kmh.fn | 302 |
| archive.gust_rule_70kmh.tn | 217 |
| archive.gust_rule_70kmh.precision | 1 |
| archive.gust_rule_70kmh.recall | 0.0033 |
| archive.gust_rule_70kmh.f1 | 0.0066 |
| archive.gust_rule_70kmh.recall_severe | 0.0149 |
| archive.gust_rule_70kmh.false_alarm_rate | 0 |
| archive.capacity_k3.p_model.customers_covered_share | 0.073 |
| archive.capacity_k3.p_model.events_caught_share | 0.1254 |
| archive.capacity_k3.p_model.alert_precision | 0.6333 |
| archive.capacity_k3.gust_max.customers_covered_share | 0.1078 |
| archive.capacity_k3.gust_max.events_caught_share | 0.1254 |
| archive.capacity_k3.gust_max.alert_precision | 0.6333 |
| archive.capacity_k3.small_zone.customers_covered_share | 0.0159 |
| archive.capacity_k3.small_zone.events_caught_share | 0.1056 |
| archive.capacity_k3.small_zone.alert_precision | 0.5333 |
| archive.capacity_k3.random.customers_covered_share | 0.1209 |
| archive.capacity_k3.random.events_caught_share | 0.1155 |
| archive.capacity_k3.random.alert_precision | 0.5833 |
| archive.capacity_k3.oracol.customers_covered_share | 0.6218 |
| archive.capacity_k3.oracol.events_caught_share | 0.198 |
| archive.capacity_k3.oracol.alert_precision | 1 |
| archive.capacity_k5.p_model.customers_covered_share | 0.1172 |
| archive.capacity_k5.p_model.events_caught_share | 0.2112 |
| archive.capacity_k5.p_model.alert_precision | 0.64 |
| archive.capacity_k5.gust_max.customers_covered_share | 0.1936 |
| archive.capacity_k5.gust_max.events_caught_share | 0.198 |
| archive.capacity_k5.gust_max.alert_precision | 0.6 |
| archive.capacity_k5.small_zone.customers_covered_share | 0.052 |
| archive.capacity_k5.small_zone.events_caught_share | 0.1914 |
| archive.capacity_k5.small_zone.alert_precision | 0.58 |
| archive.capacity_k5.random.customers_covered_share | 0.2089 |
| archive.capacity_k5.random.events_caught_share | 0.1881 |
| archive.capacity_k5.random.alert_precision | 0.57 |
| archive.capacity_k5.oracol.customers_covered_share | 0.7466 |
| archive.capacity_k5.oracol.events_caught_share | 0.33 |
| archive.capacity_k5.oracol.alert_precision | 1 |
| archive.rows_out_of_training_range | 20 |
| sensitivity.duration_capped_72h.rows | 520 |
| sensitivity.duration_capped_72h.days | 20 |
| sensitivity.duration_capped_72h.zones | 26 |
| sensitivity.duration_capped_72h.events | 180 |
| sensitivity.duration_capped_72h.severe_events | 22 |
| sensitivity.duration_capped_72h.prevalence | 0.3462 |
| sensitivity.duration_capped_72h.ranking.p_model.pr_auc | 0.3708 |
| sensitivity.duration_capped_72h.ranking.p_model.roc_auc | 0.5029 |
| sensitivity.duration_capped_72h.ranking.gust_max.pr_auc | 0.3737 |
| sensitivity.duration_capped_72h.ranking.gust_max.roc_auc | 0.5227 |
| sensitivity.duration_capped_72h.ranking.zone_rate_loo.pr_auc | 0.4699 |
| sensitivity.duration_capped_72h.ranking.zone_rate_loo.roc_auc | 0.6444 |
| sensitivity.duration_capped_72h.ranking.small_zone.pr_auc | 0.3217 |
| sensitivity.duration_capped_72h.ranking.small_zone.roc_auc | 0.4337 |
| sensitivity.duration_capped_72h.ranking.random.pr_auc | 0.3614 |
| sensitivity.duration_capped_72h.ranking.random.roc_auc | 0.5112 |
| sensitivity.duration_capped_72h.ranking_ci95.p_model.pr_auc | [0.3146, 0.442] |
| sensitivity.duration_capped_72h.ranking_ci95.p_model.roc_auc | [0.4462, 0.553] |
| sensitivity.duration_capped_72h.ranking_ci95.p_model.pr_auc_minus_base | [-0.0094, 0.0805] |
| sensitivity.duration_capped_72h.ranking_ci95.gust_max.pr_auc | [0.3201, 0.433] |
| sensitivity.duration_capped_72h.ranking_ci95.gust_max.roc_auc | [0.4786, 0.5635] |
| sensitivity.duration_capped_72h.ranking_ci95.gust_max.pr_auc_minus_base | [-0.0057, 0.0696] |
| sensitivity.duration_capped_72h.ranking_ci95.small_zone.pr_auc | [0.2661, 0.3874] |
| sensitivity.duration_capped_72h.ranking_ci95.small_zone.roc_auc | [0.398, 0.4729] |
| sensitivity.duration_capped_72h.ranking_ci95.small_zone.pr_auc_minus_base | [-0.0452, 0.0102] |
| sensitivity.duration_capped_72h.pr_auc_model_vs.gust_max.diff | -0.0043 |
| sensitivity.duration_capped_72h.pr_auc_model_vs.gust_max.ci95 | [-0.0432, 0.0481] |
| sensitivity.duration_capped_72h.pr_auc_model_vs.gust_max.share_a_better | 0.426 |
| sensitivity.duration_capped_72h.pr_auc_model_vs.small_zone.diff | 0.0505 |
| sensitivity.duration_capped_72h.pr_auc_model_vs.small_zone.ci95 | [0.0, 0.1057] |
| sensitivity.duration_capped_72h.pr_auc_model_vs.small_zone.share_a_better | 0.975 |
| sensitivity.duration_capped_72h.pr_auc_model_vs.zone_rate_loo.diff | -0.0992 |
| sensitivity.duration_capped_72h.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.1673, -0.027] |
| sensitivity.duration_capped_72h.pr_auc_model_vs.zone_rate_loo.share_a_better | 0.004 |
| sensitivity.duration_capped_72h.probabilistic.brier_model | 0.3059 |
| sensitivity.duration_capped_72h.probabilistic.brier_constant_prevalence | 0.2263 |
| sensitivity.duration_capped_72h.probabilistic.brier_us_train_rate | 0.2891 |
| sensitivity.duration_capped_72h.probabilistic.log_loss_model | 1.0741 |
| sensitivity.duration_capped_72h.probabilistic.ece_10bins | 0.2819 |
| sensitivity.duration_capped_72h.probabilistic.mean_predicted | 0.066 |
| sensitivity.duration_capped_72h.probabilistic.observed_rate | 0.3462 |
| sensitivity.duration_capped_72h.reliability[0].n | 238 |
| sensitivity.duration_capped_72h.reliability[0].observed | 0.3571 |
| sensitivity.duration_capped_72h.reliability[0].predicted | 0.0376 |
| sensitivity.duration_capped_72h.reliability[1].n | 229 |
| sensitivity.duration_capped_72h.reliability[1].observed | 0.3013 |
| sensitivity.duration_capped_72h.reliability[1].predicted | 0.0688 |
| sensitivity.duration_capped_72h.reliability[2].n | 32 |
| sensitivity.duration_capped_72h.reliability[2].observed | 0.5312 |
| sensitivity.duration_capped_72h.reliability[2].predicted | 0.1186 |
| sensitivity.duration_capped_72h.reliability[3].n | 15 |
| sensitivity.duration_capped_72h.reliability[3].observed | 0.4 |
| sensitivity.duration_capped_72h.reliability[3].predicted | 0.2069 |
| sensitivity.duration_capped_72h.reliability[4].n | 4 |
| sensitivity.duration_capped_72h.reliability[4].observed | 0.5 |
| sensitivity.duration_capped_72h.reliability[4].predicted | 0.3945 |
| sensitivity.duration_capped_72h.reliability[5].n | 2 |
| sensitivity.duration_capped_72h.reliability[5].observed | 0.5 |
| sensitivity.duration_capped_72h.reliability[5].predicted | 0.5797 |
| sensitivity.duration_capped_72h.at_model_threshold.threshold | 0.16 |
| sensitivity.duration_capped_72h.at_model_threshold.alerts | 21 |
| sensitivity.duration_capped_72h.at_model_threshold.tp | 9 |
| sensitivity.duration_capped_72h.at_model_threshold.fp | 12 |
| sensitivity.duration_capped_72h.at_model_threshold.fn | 171 |
| sensitivity.duration_capped_72h.at_model_threshold.tn | 328 |
| sensitivity.duration_capped_72h.at_model_threshold.precision | 0.4286 |
| sensitivity.duration_capped_72h.at_model_threshold.recall | 0.05 |
| sensitivity.duration_capped_72h.at_model_threshold.f1 | 0.0896 |
| sensitivity.duration_capped_72h.at_model_threshold.recall_severe | 0 |
| sensitivity.duration_capped_72h.at_model_threshold.false_alarm_rate | 0.0353 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.threshold | 0.05 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.alerts | 282 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.tp | 95 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.fp | 187 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.fn | 85 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.tn | 153 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.precision | 0.3369 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.recall | 0.5278 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.f1 | 0.4113 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.recall_severe | 0.4091 |
| sensitivity.duration_capped_72h.at_best_f1_threshold_in_sample.false_alarm_rate | 0.55 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.threshold | 70 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.alerts | 1 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.tp | 1 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.fp | 0 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.fn | 179 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.tn | 340 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.precision | 1 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.recall | 0.0056 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.f1 | 0.011 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.recall_severe | 0 |
| sensitivity.duration_capped_72h.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.duration_capped_72h.capacity_k3.p_model.customers_covered_share | 0.0744 |
| sensitivity.duration_capped_72h.capacity_k3.p_model.events_caught_share | 0.1389 |
| sensitivity.duration_capped_72h.capacity_k3.p_model.alert_precision | 0.4167 |
| sensitivity.duration_capped_72h.capacity_k3.gust_max.customers_covered_share | 0.1112 |
| sensitivity.duration_capped_72h.capacity_k3.gust_max.events_caught_share | 0.1278 |
| sensitivity.duration_capped_72h.capacity_k3.gust_max.alert_precision | 0.3833 |
| sensitivity.duration_capped_72h.capacity_k3.small_zone.customers_covered_share | 0.0205 |
| sensitivity.duration_capped_72h.capacity_k3.small_zone.events_caught_share | 0.1 |
| sensitivity.duration_capped_72h.capacity_k3.small_zone.alert_precision | 0.3 |
| sensitivity.duration_capped_72h.capacity_k3.random.customers_covered_share | 0.1118 |
| sensitivity.duration_capped_72h.capacity_k3.random.events_caught_share | 0.1278 |
| sensitivity.duration_capped_72h.capacity_k3.random.alert_precision | 0.3833 |
| sensitivity.duration_capped_72h.capacity_k3.oracol.customers_covered_share | 0.7168 |
| sensitivity.duration_capped_72h.capacity_k3.oracol.events_caught_share | 0.3333 |
| sensitivity.duration_capped_72h.capacity_k3.oracol.alert_precision | 1 |
| sensitivity.duration_capped_72h.capacity_k5.p_model.customers_covered_share | 0.1076 |
| sensitivity.duration_capped_72h.capacity_k5.p_model.events_caught_share | 0.1944 |
| sensitivity.duration_capped_72h.capacity_k5.p_model.alert_precision | 0.35 |
| sensitivity.duration_capped_72h.capacity_k5.gust_max.customers_covered_share | 0.186 |
| sensitivity.duration_capped_72h.capacity_k5.gust_max.events_caught_share | 0.2056 |
| sensitivity.duration_capped_72h.capacity_k5.gust_max.alert_precision | 0.37 |
| sensitivity.duration_capped_72h.capacity_k5.small_zone.customers_covered_share | 0.0713 |
| sensitivity.duration_capped_72h.capacity_k5.small_zone.events_caught_share | 0.1722 |
| sensitivity.duration_capped_72h.capacity_k5.small_zone.alert_precision | 0.31 |
| sensitivity.duration_capped_72h.capacity_k5.random.customers_covered_share | 0.2382 |
| sensitivity.duration_capped_72h.capacity_k5.random.events_caught_share | 0.2167 |
| sensitivity.duration_capped_72h.capacity_k5.random.alert_precision | 0.39 |
| sensitivity.duration_capped_72h.capacity_k5.oracol.customers_covered_share | 0.8465 |
| sensitivity.duration_capped_72h.capacity_k5.oracol.events_caught_share | 0.5444 |
| sensitivity.duration_capped_72h.capacity_k5.oracol.alert_precision | 0.98 |
| sensitivity.duration_capped_72h.rows_out_of_training_range | 20 |
| sensitivity.duration_capped_24h.rows | 520 |
| sensitivity.duration_capped_24h.days | 20 |
| sensitivity.duration_capped_24h.zones | 26 |
| sensitivity.duration_capped_24h.events | 128 |
| sensitivity.duration_capped_24h.severe_events | 16 |
| sensitivity.duration_capped_24h.prevalence | 0.2462 |
| sensitivity.duration_capped_24h.ranking.p_model.pr_auc | 0.2723 |
| sensitivity.duration_capped_24h.ranking.p_model.roc_auc | 0.5098 |
| sensitivity.duration_capped_24h.ranking.gust_max.pr_auc | 0.2817 |
| sensitivity.duration_capped_24h.ranking.gust_max.roc_auc | 0.5465 |
| sensitivity.duration_capped_24h.ranking.zone_rate_loo.pr_auc | 0.3044 |
| sensitivity.duration_capped_24h.ranking.zone_rate_loo.roc_auc | 0.5908 |
| sensitivity.duration_capped_24h.ranking.small_zone.pr_auc | 0.2347 |
| sensitivity.duration_capped_24h.ranking.small_zone.roc_auc | 0.4518 |
| sensitivity.duration_capped_24h.ranking.random.pr_auc | 0.2475 |
| sensitivity.duration_capped_24h.ranking.random.roc_auc | 0.5062 |
| sensitivity.duration_capped_24h.ranking_ci95.p_model.pr_auc | [0.2247, 0.332] |
| sensitivity.duration_capped_24h.ranking_ci95.p_model.roc_auc | [0.4611, 0.5523] |
| sensitivity.duration_capped_24h.ranking_ci95.p_model.pr_auc_minus_base | [0.0018, 0.0671] |
| sensitivity.duration_capped_24h.ranking_ci95.gust_max.pr_auc | [0.2432, 0.337] |
| sensitivity.duration_capped_24h.ranking_ci95.gust_max.roc_auc | [0.5037, 0.5892] |
| sensitivity.duration_capped_24h.ranking_ci95.gust_max.pr_auc_minus_base | [0.0127, 0.0725] |
| sensitivity.duration_capped_24h.ranking_ci95.small_zone.pr_auc | [0.1957, 0.2864] |
| sensitivity.duration_capped_24h.ranking_ci95.small_zone.roc_auc | [0.4026, 0.4974] |
| sensitivity.duration_capped_24h.ranking_ci95.small_zone.pr_auc_minus_base | [-0.0318, 0.0239] |
| sensitivity.duration_capped_24h.pr_auc_model_vs.gust_max.diff | -0.0106 |
| sensitivity.duration_capped_24h.pr_auc_model_vs.gust_max.ci95 | [-0.0386, 0.0281] |
| sensitivity.duration_capped_24h.pr_auc_model_vs.gust_max.share_a_better | 0.259 |
| sensitivity.duration_capped_24h.pr_auc_model_vs.small_zone.diff | 0.0401 |
| sensitivity.duration_capped_24h.pr_auc_model_vs.small_zone.ci95 | [-0.0065, 0.0821] |
| sensitivity.duration_capped_24h.pr_auc_model_vs.small_zone.share_a_better | 0.952 |
| sensitivity.duration_capped_24h.pr_auc_model_vs.zone_rate_loo.diff | -0.0304 |
| sensitivity.duration_capped_24h.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.0789, 0.0164] |
| sensitivity.duration_capped_24h.pr_auc_model_vs.zone_rate_loo.share_a_better | 0.1 |
| sensitivity.duration_capped_24h.probabilistic.brier_model | 0.2187 |
| sensitivity.duration_capped_24h.probabilistic.brier_constant_prevalence | 0.1856 |
| sensitivity.duration_capped_24h.probabilistic.brier_us_train_rate | 0.2082 |
| sensitivity.duration_capped_24h.probabilistic.log_loss_model | 0.7629 |
| sensitivity.duration_capped_24h.probabilistic.ece_10bins | 0.1847 |
| sensitivity.duration_capped_24h.probabilistic.mean_predicted | 0.066 |
| sensitivity.duration_capped_24h.probabilistic.observed_rate | 0.2462 |
| sensitivity.duration_capped_24h.reliability[0].n | 238 |
| sensitivity.duration_capped_24h.reliability[0].observed | 0.2563 |
| sensitivity.duration_capped_24h.reliability[0].predicted | 0.0376 |
| sensitivity.duration_capped_24h.reliability[1].n | 229 |
| sensitivity.duration_capped_24h.reliability[1].observed | 0.2096 |
| sensitivity.duration_capped_24h.reliability[1].predicted | 0.0688 |
| sensitivity.duration_capped_24h.reliability[2].n | 32 |
| sensitivity.duration_capped_24h.reliability[2].observed | 0.375 |
| sensitivity.duration_capped_24h.reliability[2].predicted | 0.1186 |
| sensitivity.duration_capped_24h.reliability[3].n | 15 |
| sensitivity.duration_capped_24h.reliability[3].observed | 0.3333 |
| sensitivity.duration_capped_24h.reliability[3].predicted | 0.2069 |
| sensitivity.duration_capped_24h.reliability[4].n | 4 |
| sensitivity.duration_capped_24h.reliability[4].observed | 0.25 |
| sensitivity.duration_capped_24h.reliability[4].predicted | 0.3945 |
| sensitivity.duration_capped_24h.reliability[5].n | 2 |
| sensitivity.duration_capped_24h.reliability[5].observed | 0.5 |
| sensitivity.duration_capped_24h.reliability[5].predicted | 0.5797 |
| sensitivity.duration_capped_24h.at_model_threshold.threshold | 0.16 |
| sensitivity.duration_capped_24h.at_model_threshold.alerts | 21 |
| sensitivity.duration_capped_24h.at_model_threshold.tp | 7 |
| sensitivity.duration_capped_24h.at_model_threshold.fp | 14 |
| sensitivity.duration_capped_24h.at_model_threshold.fn | 121 |
| sensitivity.duration_capped_24h.at_model_threshold.tn | 378 |
| sensitivity.duration_capped_24h.at_model_threshold.precision | 0.3333 |
| sensitivity.duration_capped_24h.at_model_threshold.recall | 0.0547 |
| sensitivity.duration_capped_24h.at_model_threshold.f1 | 0.094 |
| sensitivity.duration_capped_24h.at_model_threshold.recall_severe | 0 |
| sensitivity.duration_capped_24h.at_model_threshold.false_alarm_rate | 0.0357 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.threshold | 0.05 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.alerts | 282 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.tp | 67 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.fp | 215 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.fn | 61 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.tn | 177 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.precision | 0.2376 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.recall | 0.5234 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.f1 | 0.3268 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.recall_severe | 0.5 |
| sensitivity.duration_capped_24h.at_best_f1_threshold_in_sample.false_alarm_rate | 0.5485 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.threshold | 70 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.alerts | 1 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.tp | 1 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.fp | 0 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.fn | 127 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.tn | 392 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.precision | 1 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.recall | 0.0078 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.f1 | 0.0155 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.recall_severe | 0 |
| sensitivity.duration_capped_24h.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.duration_capped_24h.capacity_k3.p_model.customers_covered_share | 0.068 |
| sensitivity.duration_capped_24h.capacity_k3.p_model.events_caught_share | 0.125 |
| sensitivity.duration_capped_24h.capacity_k3.p_model.alert_precision | 0.2667 |
| sensitivity.duration_capped_24h.capacity_k3.gust_max.customers_covered_share | 0.1246 |
| sensitivity.duration_capped_24h.capacity_k3.gust_max.events_caught_share | 0.1484 |
| sensitivity.duration_capped_24h.capacity_k3.gust_max.alert_precision | 0.3167 |
| sensitivity.duration_capped_24h.capacity_k3.small_zone.customers_covered_share | 0.0242 |
| sensitivity.duration_capped_24h.capacity_k3.small_zone.events_caught_share | 0.1094 |
| sensitivity.duration_capped_24h.capacity_k3.small_zone.alert_precision | 0.2333 |
| sensitivity.duration_capped_24h.capacity_k3.random.customers_covered_share | 0.1241 |
| sensitivity.duration_capped_24h.capacity_k3.random.events_caught_share | 0.1172 |
| sensitivity.duration_capped_24h.capacity_k3.random.alert_precision | 0.25 |
| sensitivity.duration_capped_24h.capacity_k3.oracol.customers_covered_share | 0.7911 |
| sensitivity.duration_capped_24h.capacity_k3.oracol.events_caught_share | 0.4688 |
| sensitivity.duration_capped_24h.capacity_k3.oracol.alert_precision | 1 |
| sensitivity.duration_capped_24h.capacity_k5.p_model.customers_covered_share | 0.1069 |
| sensitivity.duration_capped_24h.capacity_k5.p_model.events_caught_share | 0.1797 |
| sensitivity.duration_capped_24h.capacity_k5.p_model.alert_precision | 0.23 |
| sensitivity.duration_capped_24h.capacity_k5.gust_max.customers_covered_share | 0.1935 |
| sensitivity.duration_capped_24h.capacity_k5.gust_max.events_caught_share | 0.2188 |
| sensitivity.duration_capped_24h.capacity_k5.gust_max.alert_precision | 0.28 |
| sensitivity.duration_capped_24h.capacity_k5.small_zone.customers_covered_share | 0.0915 |
| sensitivity.duration_capped_24h.capacity_k5.small_zone.events_caught_share | 0.1875 |
| sensitivity.duration_capped_24h.capacity_k5.small_zone.alert_precision | 0.24 |
| sensitivity.duration_capped_24h.capacity_k5.random.customers_covered_share | 0.2305 |
| sensitivity.duration_capped_24h.capacity_k5.random.events_caught_share | 0.1953 |
| sensitivity.duration_capped_24h.capacity_k5.random.alert_precision | 0.25 |
| sensitivity.duration_capped_24h.capacity_k5.oracol.customers_covered_share | 0.9094 |
| sensitivity.duration_capped_24h.capacity_k5.oracol.events_caught_share | 0.7031 |
| sensitivity.duration_capped_24h.capacity_k5.oracol.alert_precision | 0.9 |
| sensitivity.duration_capped_24h.rows_out_of_training_range | 20 |
| sensitivity.new_incidents_ge_1pct.rows | 520 |
| sensitivity.new_incidents_ge_1pct.days | 20 |
| sensitivity.new_incidents_ge_1pct.zones | 26 |
| sensitivity.new_incidents_ge_1pct.events | 99 |
| sensitivity.new_incidents_ge_1pct.severe_events | 15 |
| sensitivity.new_incidents_ge_1pct.prevalence | 0.1904 |
| sensitivity.new_incidents_ge_1pct.ranking.p_model.pr_auc | 0.2142 |
| sensitivity.new_incidents_ge_1pct.ranking.p_model.roc_auc | 0.507 |
| sensitivity.new_incidents_ge_1pct.ranking.gust_max.pr_auc | 0.2223 |
| sensitivity.new_incidents_ge_1pct.ranking.gust_max.roc_auc | 0.5432 |
| sensitivity.new_incidents_ge_1pct.ranking.zone_rate_loo.pr_auc | 0.2197 |
| sensitivity.new_incidents_ge_1pct.ranking.zone_rate_loo.roc_auc | 0.5798 |
| sensitivity.new_incidents_ge_1pct.ranking.small_zone.pr_auc | 0.1782 |
| sensitivity.new_incidents_ge_1pct.ranking.small_zone.roc_auc | 0.4532 |
| sensitivity.new_incidents_ge_1pct.ranking.random.pr_auc | 0.2307 |
| sensitivity.new_incidents_ge_1pct.ranking.random.roc_auc | 0.5572 |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.p_model.pr_auc | [0.1652, 0.2775] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.p_model.roc_auc | [0.4492, 0.5615] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.p_model.pr_auc_minus_base | [-0.0029, 0.0599] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.gust_max.pr_auc | [0.1698, 0.294] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.gust_max.roc_auc | [0.4844, 0.5983] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.gust_max.pr_auc_minus_base | [0.0033, 0.0788] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.small_zone.pr_auc | [0.141, 0.2348] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.small_zone.roc_auc | [0.4023, 0.5064] |
| sensitivity.new_incidents_ge_1pct.ranking_ci95.small_zone.pr_auc_minus_base | [-0.0292, 0.0219] |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.gust_max.diff | -0.0109 |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.gust_max.ci95 | [-0.0401, 0.0212] |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.gust_max.share_a_better | 0.235 |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.small_zone.diff | 0.0362 |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.small_zone.ci95 | [-0.0056, 0.0727] |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.small_zone.share_a_better | 0.959 |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.zone_rate_loo.diff | -0.0068 |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.0495, 0.0335] |
| sensitivity.new_incidents_ge_1pct.pr_auc_model_vs.zone_rate_loo.share_a_better | 0.396 |
| sensitivity.new_incidents_ge_1pct.probabilistic.brier_model | 0.1707 |
| sensitivity.new_incidents_ge_1pct.probabilistic.brier_constant_prevalence | 0.1541 |
| sensitivity.new_incidents_ge_1pct.probabilistic.brier_us_train_rate | 0.1631 |
| sensitivity.new_incidents_ge_1pct.probabilistic.log_loss_model | 0.6087 |
| sensitivity.new_incidents_ge_1pct.probabilistic.ece_10bins | 0.1328 |
| sensitivity.new_incidents_ge_1pct.probabilistic.mean_predicted | 0.066 |
| sensitivity.new_incidents_ge_1pct.probabilistic.observed_rate | 0.1904 |
| sensitivity.new_incidents_ge_1pct.reliability[0].n | 238 |
| sensitivity.new_incidents_ge_1pct.reliability[0].observed | 0.2059 |
| sensitivity.new_incidents_ge_1pct.reliability[0].predicted | 0.0376 |
| sensitivity.new_incidents_ge_1pct.reliability[1].n | 229 |
| sensitivity.new_incidents_ge_1pct.reliability[1].observed | 0.1485 |
| sensitivity.new_incidents_ge_1pct.reliability[1].predicted | 0.0688 |
| sensitivity.new_incidents_ge_1pct.reliability[2].n | 32 |
| sensitivity.new_incidents_ge_1pct.reliability[2].observed | 0.3438 |
| sensitivity.new_incidents_ge_1pct.reliability[2].predicted | 0.1186 |
| sensitivity.new_incidents_ge_1pct.reliability[3].n | 15 |
| sensitivity.new_incidents_ge_1pct.reliability[3].observed | 0.2 |
| sensitivity.new_incidents_ge_1pct.reliability[3].predicted | 0.2069 |
| sensitivity.new_incidents_ge_1pct.reliability[4].n | 4 |
| sensitivity.new_incidents_ge_1pct.reliability[4].observed | 0.25 |
| sensitivity.new_incidents_ge_1pct.reliability[4].predicted | 0.3945 |
| sensitivity.new_incidents_ge_1pct.reliability[5].n | 2 |
| sensitivity.new_incidents_ge_1pct.reliability[5].observed | 0.5 |
| sensitivity.new_incidents_ge_1pct.reliability[5].predicted | 0.5797 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.threshold | 0.16 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.alerts | 21 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.tp | 5 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.fp | 16 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.fn | 94 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.tn | 405 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.precision | 0.2381 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.recall | 0.0505 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.f1 | 0.0833 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.recall_severe | 0 |
| sensitivity.new_incidents_ge_1pct.at_model_threshold.false_alarm_rate | 0.038 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.threshold | 0.05 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.alerts | 282 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.tp | 50 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.fp | 232 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.fn | 49 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.tn | 189 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.precision | 0.1773 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.recall | 0.5051 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.f1 | 0.2625 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.recall_severe | 0.4667 |
| sensitivity.new_incidents_ge_1pct.at_best_f1_threshold_in_sample.false_alarm_rate | 0.5511 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.threshold | 70 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.alerts | 1 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.tp | 1 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.fp | 0 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.fn | 98 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.tn | 421 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.precision | 1 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.recall | 0.0101 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.f1 | 0.02 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.recall_severe | 0 |
| sensitivity.new_incidents_ge_1pct.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.p_model.customers_covered_share | 0.0577 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.p_model.events_caught_share | 0.1111 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.p_model.alert_precision | 0.1833 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.gust_max.customers_covered_share | 0.0909 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.gust_max.events_caught_share | 0.1515 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.gust_max.alert_precision | 0.25 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.small_zone.customers_covered_share | 0.0218 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.small_zone.events_caught_share | 0.101 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.small_zone.alert_precision | 0.1667 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.random.customers_covered_share | 0.1658 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.random.events_caught_share | 0.1414 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.random.alert_precision | 0.2333 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.oracol.customers_covered_share | 0.8502 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.oracol.events_caught_share | 0.5657 |
| sensitivity.new_incidents_ge_1pct.capacity_k3.oracol.alert_precision | 0.9333 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.p_model.customers_covered_share | 0.0944 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.p_model.events_caught_share | 0.1818 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.p_model.alert_precision | 0.18 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.gust_max.customers_covered_share | 0.1609 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.gust_max.events_caught_share | 0.2222 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.gust_max.alert_precision | 0.22 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.small_zone.customers_covered_share | 0.0886 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.small_zone.events_caught_share | 0.1919 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.small_zone.alert_precision | 0.19 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.random.customers_covered_share | 0.2913 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.random.events_caught_share | 0.2323 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.random.alert_precision | 0.23 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.oracol.customers_covered_share | 0.9515 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.oracol.events_caught_share | 0.798 |
| sensitivity.new_incidents_ge_1pct.capacity_k5.oracol.alert_precision | 0.79 |
| sensitivity.new_incidents_ge_1pct.rows_out_of_training_range | 20 |
| sensitivity.new_incidents_ge_2pct.rows | 520 |
| sensitivity.new_incidents_ge_2pct.days | 20 |
| sensitivity.new_incidents_ge_2pct.zones | 26 |
| sensitivity.new_incidents_ge_2pct.events | 55 |
| sensitivity.new_incidents_ge_2pct.severe_events | 15 |
| sensitivity.new_incidents_ge_2pct.prevalence | 0.1058 |
| sensitivity.new_incidents_ge_2pct.ranking.p_model.pr_auc | 0.1284 |
| sensitivity.new_incidents_ge_2pct.ranking.p_model.roc_auc | 0.5181 |
| sensitivity.new_incidents_ge_2pct.ranking.gust_max.pr_auc | 0.147 |
| sensitivity.new_incidents_ge_2pct.ranking.gust_max.roc_auc | 0.5628 |
| sensitivity.new_incidents_ge_2pct.ranking.zone_rate_loo.pr_auc | 0.1222 |
| sensitivity.new_incidents_ge_2pct.ranking.zone_rate_loo.roc_auc | 0.4923 |
| sensitivity.new_incidents_ge_2pct.ranking.small_zone.pr_auc | 0.1192 |
| sensitivity.new_incidents_ge_2pct.ranking.small_zone.roc_auc | 0.5168 |
| sensitivity.new_incidents_ge_2pct.ranking.random.pr_auc | 0.1375 |
| sensitivity.new_incidents_ge_2pct.ranking.random.roc_auc | 0.6063 |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.p_model.pr_auc | [0.0868, 0.1738] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.p_model.roc_auc | [0.4299, 0.5981] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.p_model.pr_auc_minus_base | [-0.0053, 0.062] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.gust_max.pr_auc | [0.0961, 0.2151] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.gust_max.roc_auc | [0.4906, 0.6248] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.gust_max.pr_auc_minus_base | [0.0049, 0.1041] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.small_zone.pr_auc | [0.0847, 0.1784] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.small_zone.roc_auc | [0.4467, 0.5979] |
| sensitivity.new_incidents_ge_2pct.ranking_ci95.small_zone.pr_auc_minus_base | [-0.0085, 0.0698] |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.gust_max.diff | -0.0212 |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.gust_max.ci95 | [-0.0513, 0.0066] |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.gust_max.share_a_better | 0.073 |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.small_zone.diff | 0.0082 |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.small_zone.ci95 | [-0.0477, 0.0484] |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.small_zone.share_a_better | 0.633 |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.zone_rate_loo.diff | 0.0034 |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.0562, 0.0575] |
| sensitivity.new_incidents_ge_2pct.pr_auc_model_vs.zone_rate_loo.share_a_better | 0.542 |
| sensitivity.new_incidents_ge_2pct.probabilistic.brier_model | 0.098 |
| sensitivity.new_incidents_ge_2pct.probabilistic.brier_constant_prevalence | 0.0946 |
| sensitivity.new_incidents_ge_2pct.probabilistic.brier_us_train_rate | 0.0947 |
| sensitivity.new_incidents_ge_2pct.probabilistic.log_loss_model | 0.3694 |
| sensitivity.new_incidents_ge_2pct.probabilistic.ece_10bins | 0.0515 |
| sensitivity.new_incidents_ge_2pct.probabilistic.mean_predicted | 0.066 |
| sensitivity.new_incidents_ge_2pct.probabilistic.observed_rate | 0.1058 |
| sensitivity.new_incidents_ge_2pct.reliability[0].n | 238 |
| sensitivity.new_incidents_ge_2pct.reliability[0].observed | 0.1134 |
| sensitivity.new_incidents_ge_2pct.reliability[0].predicted | 0.0376 |
| sensitivity.new_incidents_ge_2pct.reliability[1].n | 229 |
| sensitivity.new_incidents_ge_2pct.reliability[1].observed | 0.0786 |
| sensitivity.new_incidents_ge_2pct.reliability[1].predicted | 0.0688 |
| sensitivity.new_incidents_ge_2pct.reliability[2].n | 32 |
| sensitivity.new_incidents_ge_2pct.reliability[2].observed | 0.25 |
| sensitivity.new_incidents_ge_2pct.reliability[2].predicted | 0.1186 |
| sensitivity.new_incidents_ge_2pct.reliability[3].n | 15 |
| sensitivity.new_incidents_ge_2pct.reliability[3].observed | 0.0667 |
| sensitivity.new_incidents_ge_2pct.reliability[3].predicted | 0.2069 |
| sensitivity.new_incidents_ge_2pct.reliability[4].n | 4 |
| sensitivity.new_incidents_ge_2pct.reliability[4].observed | 0 |
| sensitivity.new_incidents_ge_2pct.reliability[4].predicted | 0.3945 |
| sensitivity.new_incidents_ge_2pct.reliability[5].n | 2 |
| sensitivity.new_incidents_ge_2pct.reliability[5].observed | 0.5 |
| sensitivity.new_incidents_ge_2pct.reliability[5].predicted | 0.5797 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.threshold | 0.16 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.alerts | 21 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.tp | 2 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.fp | 19 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.fn | 53 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.tn | 446 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.precision | 0.0952 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.recall | 0.0364 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.f1 | 0.0526 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.recall_severe | 0 |
| sensitivity.new_incidents_ge_2pct.at_model_threshold.false_alarm_rate | 0.0409 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.threshold | 0.09 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.alerts | 94 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.tp | 14 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.fp | 80 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.fn | 41 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.tn | 385 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.precision | 0.1489 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.recall | 0.2545 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.f1 | 0.1879 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.recall_severe | 0.2 |
| sensitivity.new_incidents_ge_2pct.at_best_f1_threshold_in_sample.false_alarm_rate | 0.172 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.threshold | 70 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.alerts | 1 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.tp | 1 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.fp | 0 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.fn | 54 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.tn | 465 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.precision | 1 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.recall | 0.0182 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.f1 | 0.0357 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.recall_severe | 0 |
| sensitivity.new_incidents_ge_2pct.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.p_model.customers_covered_share | 0.0421 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.p_model.events_caught_share | 0.0909 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.p_model.alert_precision | 0.0833 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.gust_max.customers_covered_share | 0.0879 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.gust_max.events_caught_share | 0.1636 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.gust_max.alert_precision | 0.15 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.small_zone.customers_covered_share | 0.0241 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.small_zone.events_caught_share | 0.1273 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.small_zone.alert_precision | 0.1167 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.random.customers_covered_share | 0.1416 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.random.events_caught_share | 0.1091 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.random.alert_precision | 0.1 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.oracol.customers_covered_share | 0.9288 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.oracol.events_caught_share | 0.7818 |
| sensitivity.new_incidents_ge_2pct.capacity_k3.oracol.alert_precision | 0.7167 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.p_model.customers_covered_share | 0.071 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.p_model.events_caught_share | 0.1455 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.p_model.alert_precision | 0.08 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.gust_max.customers_covered_share | 0.1686 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.gust_max.events_caught_share | 0.2182 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.gust_max.alert_precision | 0.12 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.small_zone.customers_covered_share | 0.1055 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.small_zone.events_caught_share | 0.2545 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.small_zone.alert_precision | 0.14 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.random.customers_covered_share | 0.2964 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.random.events_caught_share | 0.2364 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.random.alert_precision | 0.13 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.oracol.customers_covered_share | 0.9941 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.oracol.events_caught_share | 0.9818 |
| sensitivity.new_incidents_ge_2pct.capacity_k5.oracol.alert_precision | 0.54 |
| sensitivity.new_incidents_ge_2pct.rows_out_of_training_range | 20 |
| sensitivity.event_threshold_0_5pct.rows | 520 |
| sensitivity.event_threshold_0_5pct.days | 20 |
| sensitivity.event_threshold_0_5pct.zones | 26 |
| sensitivity.event_threshold_0_5pct.events | 378 |
| sensitivity.event_threshold_0_5pct.severe_events | 67 |
| sensitivity.event_threshold_0_5pct.prevalence | 0.7269 |
| sensitivity.event_threshold_0_5pct.ranking.p_model.pr_auc | 0.7982 |
| sensitivity.event_threshold_0_5pct.ranking.p_model.roc_auc | 0.6019 |
| sensitivity.event_threshold_0_5pct.ranking.gust_max.pr_auc | 0.7703 |
| sensitivity.event_threshold_0_5pct.ranking.gust_max.roc_auc | 0.5702 |
| sensitivity.event_threshold_0_5pct.ranking.zone_rate_loo.pr_auc | 0.8992 |
| sensitivity.event_threshold_0_5pct.ranking.zone_rate_loo.roc_auc | 0.8312 |
| sensitivity.event_threshold_0_5pct.ranking.small_zone.pr_auc | 0.7079 |
| sensitivity.event_threshold_0_5pct.ranking.small_zone.roc_auc | 0.4531 |
| sensitivity.event_threshold_0_5pct.ranking.random.pr_auc | 0.7091 |
| sensitivity.event_threshold_0_5pct.ranking.random.roc_auc | 0.4742 |
| sensitivity.event_threshold_0_5pct.ranking_ci95.p_model.pr_auc | [0.742, 0.8458] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.p_model.roc_auc | [0.5573, 0.6457] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.p_model.pr_auc_minus_base | [0.0349, 0.0998] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.gust_max.pr_auc | [0.709, 0.8294] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.gust_max.roc_auc | [0.5272, 0.6101] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.gust_max.pr_auc_minus_base | [0.0032, 0.0809] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.small_zone.pr_auc | [0.66, 0.756] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.small_zone.roc_auc | [0.4231, 0.4835] |
| sensitivity.event_threshold_0_5pct.ranking_ci95.small_zone.pr_auc_minus_base | [-0.042, 0.0074] |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.gust_max.diff | 0.0264 |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.gust_max.ci95 | [0.0072, 0.0477] |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.gust_max.share_a_better | 0.998 |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.small_zone.diff | 0.0873 |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.small_zone.ci95 | [0.0405, 0.1343] |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.small_zone.share_a_better | 1 |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.zone_rate_loo.diff | -0.1039 |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.1496, -0.0584] |
| sensitivity.event_threshold_0_5pct.pr_auc_model_vs.zone_rate_loo.share_a_better | 0 |
| sensitivity.event_threshold_0_5pct.probabilistic.brier_model | 0.6318 |
| sensitivity.event_threshold_0_5pct.probabilistic.brier_constant_prevalence | 0.1985 |
| sensitivity.event_threshold_0_5pct.probabilistic.brier_us_train_rate | 0.597 |
| sensitivity.event_threshold_0_5pct.probabilistic.log_loss_model | 2.1187 |
| sensitivity.event_threshold_0_5pct.probabilistic.ece_10bins | 0.6609 |
| sensitivity.event_threshold_0_5pct.probabilistic.mean_predicted | 0.066 |
| sensitivity.event_threshold_0_5pct.probabilistic.observed_rate | 0.7269 |
| sensitivity.event_threshold_0_5pct.reliability[0].n | 238 |
| sensitivity.event_threshold_0_5pct.reliability[0].observed | 0.6807 |
| sensitivity.event_threshold_0_5pct.reliability[0].predicted | 0.0376 |
| sensitivity.event_threshold_0_5pct.reliability[1].n | 229 |
| sensitivity.event_threshold_0_5pct.reliability[1].observed | 0.738 |
| sensitivity.event_threshold_0_5pct.reliability[1].predicted | 0.0688 |
| sensitivity.event_threshold_0_5pct.reliability[2].n | 32 |
| sensitivity.event_threshold_0_5pct.reliability[2].observed | 0.875 |
| sensitivity.event_threshold_0_5pct.reliability[2].predicted | 0.1186 |
| sensitivity.event_threshold_0_5pct.reliability[3].n | 15 |
| sensitivity.event_threshold_0_5pct.reliability[3].observed | 0.8667 |
| sensitivity.event_threshold_0_5pct.reliability[3].predicted | 0.2069 |
| sensitivity.event_threshold_0_5pct.reliability[4].n | 4 |
| sensitivity.event_threshold_0_5pct.reliability[4].observed | 1 |
| sensitivity.event_threshold_0_5pct.reliability[4].predicted | 0.3945 |
| sensitivity.event_threshold_0_5pct.reliability[5].n | 2 |
| sensitivity.event_threshold_0_5pct.reliability[5].observed | 1 |
| sensitivity.event_threshold_0_5pct.reliability[5].predicted | 0.5797 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.threshold | 0.16 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.alerts | 21 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.tp | 19 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.fp | 2 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.fn | 359 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.tn | 140 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.precision | 0.9048 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.recall | 0.0503 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.f1 | 0.0952 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.recall_severe | 0.0299 |
| sensitivity.event_threshold_0_5pct.at_model_threshold.false_alarm_rate | 0.0141 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.threshold | 0.05 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.alerts | 282 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.tp | 216 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.fp | 66 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.fn | 162 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.tn | 76 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.precision | 0.766 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.recall | 0.5714 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.f1 | 0.6545 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.recall_severe | 0.5672 |
| sensitivity.event_threshold_0_5pct.at_best_f1_threshold_in_sample.false_alarm_rate | 0.4648 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.threshold | 70 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.alerts | 1 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.tp | 1 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.fp | 0 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.fn | 377 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.tn | 142 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.precision | 1 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.recall | 0.0026 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.f1 | 0.0053 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.recall_severe | 0.0149 |
| sensitivity.event_threshold_0_5pct.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.event_threshold_0_5pct.capacity_k3.p_model.customers_covered_share | 0.0728 |
| sensitivity.event_threshold_0_5pct.capacity_k3.p_model.events_caught_share | 0.119 |
| sensitivity.event_threshold_0_5pct.capacity_k3.p_model.alert_precision | 0.75 |
| sensitivity.event_threshold_0_5pct.capacity_k3.gust_max.customers_covered_share | 0.1064 |
| sensitivity.event_threshold_0_5pct.capacity_k3.gust_max.events_caught_share | 0.119 |
| sensitivity.event_threshold_0_5pct.capacity_k3.gust_max.alert_precision | 0.75 |
| sensitivity.event_threshold_0_5pct.capacity_k3.small_zone.customers_covered_share | 0.0158 |
| sensitivity.event_threshold_0_5pct.capacity_k3.small_zone.events_caught_share | 0.0926 |
| sensitivity.event_threshold_0_5pct.capacity_k3.small_zone.alert_precision | 0.5833 |
| sensitivity.event_threshold_0_5pct.capacity_k3.random.customers_covered_share | 0.1247 |
| sensitivity.event_threshold_0_5pct.capacity_k3.random.events_caught_share | 0.1058 |
| sensitivity.event_threshold_0_5pct.capacity_k3.random.alert_precision | 0.6667 |
| sensitivity.event_threshold_0_5pct.capacity_k3.oracol.customers_covered_share | 0.6024 |
| sensitivity.event_threshold_0_5pct.capacity_k3.oracol.events_caught_share | 0.1587 |
| sensitivity.event_threshold_0_5pct.capacity_k3.oracol.alert_precision | 1 |
| sensitivity.event_threshold_0_5pct.capacity_k5.p_model.customers_covered_share | 0.1169 |
| sensitivity.event_threshold_0_5pct.capacity_k5.p_model.events_caught_share | 0.2037 |
| sensitivity.event_threshold_0_5pct.capacity_k5.p_model.alert_precision | 0.77 |
| sensitivity.event_threshold_0_5pct.capacity_k5.gust_max.customers_covered_share | 0.1932 |
| sensitivity.event_threshold_0_5pct.capacity_k5.gust_max.events_caught_share | 0.2037 |
| sensitivity.event_threshold_0_5pct.capacity_k5.gust_max.alert_precision | 0.77 |
| sensitivity.event_threshold_0_5pct.capacity_k5.small_zone.customers_covered_share | 0.0528 |
| sensitivity.event_threshold_0_5pct.capacity_k5.small_zone.events_caught_share | 0.1878 |
| sensitivity.event_threshold_0_5pct.capacity_k5.small_zone.alert_precision | 0.71 |
| sensitivity.event_threshold_0_5pct.capacity_k5.random.customers_covered_share | 0.211 |
| sensitivity.event_threshold_0_5pct.capacity_k5.random.events_caught_share | 0.1772 |
| sensitivity.event_threshold_0_5pct.capacity_k5.random.alert_precision | 0.67 |
| sensitivity.event_threshold_0_5pct.capacity_k5.oracol.customers_covered_share | 0.7241 |
| sensitivity.event_threshold_0_5pct.capacity_k5.oracol.events_caught_share | 0.2646 |
| sensitivity.event_threshold_0_5pct.capacity_k5.oracol.alert_precision | 1 |
| sensitivity.event_threshold_0_5pct.rows_out_of_training_range | 20 |
| sensitivity.event_threshold_2pct.rows | 520 |
| sensitivity.event_threshold_2pct.days | 20 |
| sensitivity.event_threshold_2pct.zones | 26 |
| sensitivity.event_threshold_2pct.events | 197 |
| sensitivity.event_threshold_2pct.severe_events | 67 |
| sensitivity.event_threshold_2pct.prevalence | 0.3788 |
| sensitivity.event_threshold_2pct.ranking.p_model.pr_auc | 0.4548 |
| sensitivity.event_threshold_2pct.ranking.p_model.roc_auc | 0.5546 |
| sensitivity.event_threshold_2pct.ranking.gust_max.pr_auc | 0.408 |
| sensitivity.event_threshold_2pct.ranking.gust_max.roc_auc | 0.5081 |
| sensitivity.event_threshold_2pct.ranking.zone_rate_loo.pr_auc | 0.6875 |
| sensitivity.event_threshold_2pct.ranking.zone_rate_loo.roc_auc | 0.7733 |
| sensitivity.event_threshold_2pct.ranking.small_zone.pr_auc | 0.3624 |
| sensitivity.event_threshold_2pct.ranking.small_zone.roc_auc | 0.4675 |
| sensitivity.event_threshold_2pct.ranking.random.pr_auc | 0.3919 |
| sensitivity.event_threshold_2pct.ranking.random.roc_auc | 0.5158 |
| sensitivity.event_threshold_2pct.ranking_ci95.p_model.pr_auc | [0.3899, 0.5182] |
| sensitivity.event_threshold_2pct.ranking_ci95.p_model.roc_auc | [0.4981, 0.6049] |
| sensitivity.event_threshold_2pct.ranking_ci95.p_model.pr_auc_minus_base | [0.0348, 0.1221] |
| sensitivity.event_threshold_2pct.ranking_ci95.gust_max.pr_auc | [0.3234, 0.4926] |
| sensitivity.event_threshold_2pct.ranking_ci95.gust_max.roc_auc | [0.459, 0.5545] |
| sensitivity.event_threshold_2pct.ranking_ci95.gust_max.pr_auc_minus_base | [-0.0196, 0.089] |
| sensitivity.event_threshold_2pct.ranking_ci95.small_zone.pr_auc | [0.3065, 0.424] |
| sensitivity.event_threshold_2pct.ranking_ci95.small_zone.roc_auc | [0.4287, 0.513] |
| sensitivity.event_threshold_2pct.ranking_ci95.small_zone.pr_auc_minus_base | [-0.0373, 0.0177] |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.gust_max.diff | 0.0458 |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.gust_max.ci95 | [0.0016, 0.0963] |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.gust_max.share_a_better | 0.981 |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.small_zone.diff | 0.0918 |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.small_zone.ci95 | [0.0465, 0.1378] |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.small_zone.share_a_better | 1 |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.zone_rate_loo.diff | -0.2363 |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.zone_rate_loo.ci95 | [-0.3066, -0.1571] |
| sensitivity.event_threshold_2pct.pr_auc_model_vs.zone_rate_loo.share_a_better | 0 |
| sensitivity.event_threshold_2pct.probabilistic.brier_model | 0.3301 |
| sensitivity.event_threshold_2pct.probabilistic.brier_constant_prevalence | 0.2353 |
| sensitivity.event_threshold_2pct.probabilistic.brier_us_train_rate | 0.3155 |
| sensitivity.event_threshold_2pct.probabilistic.log_loss_model | 1.1276 |
| sensitivity.event_threshold_2pct.probabilistic.ece_10bins | 0.3134 |
| sensitivity.event_threshold_2pct.probabilistic.mean_predicted | 0.066 |
| sensitivity.event_threshold_2pct.probabilistic.observed_rate | 0.3788 |
| sensitivity.event_threshold_2pct.reliability[0].n | 238 |
| sensitivity.event_threshold_2pct.reliability[0].observed | 0.3487 |
| sensitivity.event_threshold_2pct.reliability[0].predicted | 0.0376 |
| sensitivity.event_threshold_2pct.reliability[1].n | 229 |
| sensitivity.event_threshold_2pct.reliability[1].observed | 0.3624 |
| sensitivity.event_threshold_2pct.reliability[1].predicted | 0.0688 |
| sensitivity.event_threshold_2pct.reliability[2].n | 32 |
| sensitivity.event_threshold_2pct.reliability[2].observed | 0.5625 |
| sensitivity.event_threshold_2pct.reliability[2].predicted | 0.1186 |
| sensitivity.event_threshold_2pct.reliability[3].n | 15 |
| sensitivity.event_threshold_2pct.reliability[3].observed | 0.6 |
| sensitivity.event_threshold_2pct.reliability[3].predicted | 0.2069 |
| sensitivity.event_threshold_2pct.reliability[4].n | 4 |
| sensitivity.event_threshold_2pct.reliability[4].observed | 0.75 |
| sensitivity.event_threshold_2pct.reliability[4].predicted | 0.3945 |
| sensitivity.event_threshold_2pct.reliability[5].n | 2 |
| sensitivity.event_threshold_2pct.reliability[5].observed | 0.5 |
| sensitivity.event_threshold_2pct.reliability[5].predicted | 0.5797 |
| sensitivity.event_threshold_2pct.at_model_threshold.threshold | 0.16 |
| sensitivity.event_threshold_2pct.at_model_threshold.alerts | 21 |
| sensitivity.event_threshold_2pct.at_model_threshold.tp | 13 |
| sensitivity.event_threshold_2pct.at_model_threshold.fp | 8 |
| sensitivity.event_threshold_2pct.at_model_threshold.fn | 184 |
| sensitivity.event_threshold_2pct.at_model_threshold.tn | 315 |
| sensitivity.event_threshold_2pct.at_model_threshold.precision | 0.619 |
| sensitivity.event_threshold_2pct.at_model_threshold.recall | 0.066 |
| sensitivity.event_threshold_2pct.at_model_threshold.f1 | 0.1193 |
| sensitivity.event_threshold_2pct.at_model_threshold.recall_severe | 0.0299 |
| sensitivity.event_threshold_2pct.at_model_threshold.false_alarm_rate | 0.0248 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.threshold | 0.05 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.alerts | 282 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.tp | 114 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.fp | 168 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.fn | 83 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.tn | 155 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.precision | 0.4043 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.recall | 0.5787 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.f1 | 0.476 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.recall_severe | 0.5672 |
| sensitivity.event_threshold_2pct.at_best_f1_threshold_in_sample.false_alarm_rate | 0.5201 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.threshold | 70 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.alerts | 1 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.tp | 1 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.fp | 0 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.fn | 196 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.tn | 323 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.precision | 1 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.recall | 0.0051 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.f1 | 0.0101 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.recall_severe | 0.0149 |
| sensitivity.event_threshold_2pct.gust_rule_70kmh.false_alarm_rate | 0 |
| sensitivity.event_threshold_2pct.capacity_k3.p_model.customers_covered_share | 0.0738 |
| sensitivity.event_threshold_2pct.capacity_k3.p_model.events_caught_share | 0.1371 |
| sensitivity.event_threshold_2pct.capacity_k3.p_model.alert_precision | 0.45 |
| sensitivity.event_threshold_2pct.capacity_k3.gust_max.customers_covered_share | 0.1095 |
| sensitivity.event_threshold_2pct.capacity_k3.gust_max.events_caught_share | 0.1269 |
| sensitivity.event_threshold_2pct.capacity_k3.gust_max.alert_precision | 0.4167 |
| sensitivity.event_threshold_2pct.capacity_k3.small_zone.customers_covered_share | 0.0139 |
| sensitivity.event_threshold_2pct.capacity_k3.small_zone.events_caught_share | 0.0914 |
| sensitivity.event_threshold_2pct.capacity_k3.small_zone.alert_precision | 0.3 |
| sensitivity.event_threshold_2pct.capacity_k3.random.customers_covered_share | 0.131 |
| sensitivity.event_threshold_2pct.capacity_k3.random.events_caught_share | 0.1218 |
| sensitivity.event_threshold_2pct.capacity_k3.random.alert_precision | 0.4 |
| sensitivity.event_threshold_2pct.capacity_k3.oracol.customers_covered_share | 0.6753 |
| sensitivity.event_threshold_2pct.capacity_k3.oracol.events_caught_share | 0.2944 |
| sensitivity.event_threshold_2pct.capacity_k3.oracol.alert_precision | 0.9667 |
| sensitivity.event_threshold_2pct.capacity_k5.p_model.customers_covered_share | 0.1132 |
| sensitivity.event_threshold_2pct.capacity_k5.p_model.events_caught_share | 0.2081 |
| sensitivity.event_threshold_2pct.capacity_k5.p_model.alert_precision | 0.41 |
| sensitivity.event_threshold_2pct.capacity_k5.gust_max.customers_covered_share | 0.1975 |
| sensitivity.event_threshold_2pct.capacity_k5.gust_max.events_caught_share | 0.1878 |
| sensitivity.event_threshold_2pct.capacity_k5.gust_max.alert_precision | 0.37 |
| sensitivity.event_threshold_2pct.capacity_k5.small_zone.customers_covered_share | 0.0487 |
| sensitivity.event_threshold_2pct.capacity_k5.small_zone.events_caught_share | 0.1624 |
| sensitivity.event_threshold_2pct.capacity_k5.small_zone.alert_precision | 0.32 |
| sensitivity.event_threshold_2pct.capacity_k5.random.customers_covered_share | 0.2006 |
| sensitivity.event_threshold_2pct.capacity_k5.random.events_caught_share | 0.203 |
| sensitivity.event_threshold_2pct.capacity_k5.random.alert_precision | 0.4 |
| sensitivity.event_threshold_2pct.capacity_k5.oracol.customers_covered_share | 0.8091 |
| sensitivity.event_threshold_2pct.capacity_k5.oracol.events_caught_share | 0.4873 |
| sensitivity.event_threshold_2pct.capacity_k5.oracol.alert_precision | 0.96 |
| sensitivity.event_threshold_2pct.rows_out_of_training_range | 20 |
| max_gust_kmh_in_window | 71.3 |
| max_p_model_in_window | 0.58 |

</details>

<details><summary>reports/B/tuning.json</summary>

[Sursa](../../reports/B/tuning.json) · SHA256 `c45b31a196f3d02887aaabf0b6ca8e49bd1d4294cf6013434ce51fca5a2ac62f`

| Câmp | Valoare |
|---|---:|
| train_years | [2023, 2024] |
| counties | 80 |
| rows | 58480 |
| current.num_leaves | 15 |
| current.min_data_in_leaf | 40 |
| current.learning_rate | 0.04 |
| current.rounds | 500 |
| results[0].num_leaves | 31 |
| results[0].min_data_in_leaf | 40 |
| results[0].learning_rate | 0.02 |
| results[0].rounds | 300 |
| results[0].oof_pr_auc | 0.2916 |
| results[0].oof_brier | 0.078 |
| results[1].num_leaves | 31 |
| results[1].min_data_in_leaf | 100 |
| results[1].learning_rate | 0.02 |
| results[1].rounds | 300 |
| results[1].oof_pr_auc | 0.2916 |
| results[1].oof_brier | 0.078 |
| results[2].num_leaves | 15 |
| results[2].min_data_in_leaf | 40 |
| results[2].learning_rate | 0.04 |
| results[2].rounds | 300 |
| results[2].oof_pr_auc | 0.29 |
| results[2].oof_brier | 0.0781 |
| results[3].num_leaves | 15 |
| results[3].min_data_in_leaf | 40 |
| results[3].learning_rate | 0.02 |
| results[3].rounds | 300 |
| results[3].oof_pr_auc | 0.2899 |
| results[3].oof_brier | 0.0781 |
| results[4].num_leaves | 7 |
| results[4].min_data_in_leaf | 100 |
| results[4].learning_rate | 0.04 |
| results[4].rounds | 300 |
| results[4].oof_pr_auc | 0.2898 |
| results[4].oof_brier | 0.0781 |
| results[5].num_leaves | 15 |
| results[5].min_data_in_leaf | 100 |
| results[5].learning_rate | 0.02 |
| results[5].rounds | 300 |
| results[5].oof_pr_auc | 0.2898 |
| results[5].oof_brier | 0.0781 |
| results[6].num_leaves | 15 |
| results[6].min_data_in_leaf | 40 |
| results[6].learning_rate | 0.02 |
| results[6].rounds | 600 |
| results[6].oof_pr_auc | 0.2896 |
| results[6].oof_brier | 0.0781 |
| results[7].num_leaves | 15 |
| results[7].min_data_in_leaf | 100 |
| results[7].learning_rate | 0.02 |
| results[7].rounds | 600 |
| results[7].oof_pr_auc | 0.2896 |
| results[7].oof_brier | 0.0781 |
| results[8].num_leaves | 7 |
| results[8].min_data_in_leaf | 40 |
| results[8].learning_rate | 0.04 |
| results[8].rounds | 300 |
| results[8].oof_pr_auc | 0.2893 |
| results[8].oof_brier | 0.0781 |
| results[9].num_leaves | 7 |
| results[9].min_data_in_leaf | 40 |
| results[9].learning_rate | 0.02 |
| results[9].rounds | 600 |
| results[9].oof_pr_auc | 0.2892 |
| results[9].oof_brier | 0.0781 |
| results[10].num_leaves | 15 |
| results[10].min_data_in_leaf | 100 |
| results[10].learning_rate | 0.04 |
| results[10].rounds | 300 |
| results[10].oof_pr_auc | 0.289 |
| results[10].oof_brier | 0.0781 |
| results[11].num_leaves | 7 |
| results[11].min_data_in_leaf | 100 |
| results[11].learning_rate | 0.02 |
| results[11].rounds | 600 |
| results[11].oof_pr_auc | 0.2888 |
| results[11].oof_brier | 0.0781 |
| results[12].num_leaves | 7 |
| results[12].min_data_in_leaf | 100 |
| results[12].learning_rate | 0.04 |
| results[12].rounds | 600 |
| results[12].oof_pr_auc | 0.2888 |
| results[12].oof_brier | 0.0782 |
| results[13].num_leaves | 7 |
| results[13].min_data_in_leaf | 40 |
| results[13].learning_rate | 0.04 |
| results[13].rounds | 600 |
| results[13].oof_pr_auc | 0.2879 |
| results[13].oof_brier | 0.0782 |
| results[14].num_leaves | 31 |
| results[14].min_data_in_leaf | 40 |
| results[14].learning_rate | 0.02 |
| results[14].rounds | 600 |
| results[14].oof_pr_auc | 0.2878 |
| results[14].oof_brier | 0.0784 |
| results[15].num_leaves | 31 |
| results[15].min_data_in_leaf | 40 |
| results[15].learning_rate | 0.04 |
| results[15].rounds | 300 |
| results[15].oof_pr_auc | 0.2878 |
| results[15].oof_brier | 0.0784 |
| results[16].num_leaves | 31 |
| results[16].min_data_in_leaf | 100 |
| results[16].learning_rate | 0.02 |
| results[16].rounds | 600 |
| results[16].oof_pr_auc | 0.287 |
| results[16].oof_brier | 0.0784 |
| results[17].num_leaves | 31 |
| results[17].min_data_in_leaf | 100 |
| results[17].learning_rate | 0.04 |
| results[17].rounds | 300 |
| results[17].oof_pr_auc | 0.2865 |
| results[17].oof_brier | 0.0785 |
| results[18].num_leaves | 15 |
| results[18].min_data_in_leaf | 40 |
| results[18].learning_rate | 0.04 |
| results[18].rounds | 600 |
| results[18].oof_pr_auc | 0.285 |
| results[18].oof_brier | 0.0786 |
| results[19].num_leaves | 7 |
| results[19].min_data_in_leaf | 40 |
| results[19].learning_rate | 0.02 |
| results[19].rounds | 300 |
| results[19].oof_pr_auc | 0.2846 |
| results[19].oof_brier | 0.0784 |
| results[20].num_leaves | 7 |
| results[20].min_data_in_leaf | 100 |
| results[20].learning_rate | 0.02 |
| results[20].rounds | 300 |
| results[20].oof_pr_auc | 0.2841 |
| results[20].oof_brier | 0.0785 |
| results[21].num_leaves | 15 |
| results[21].min_data_in_leaf | 100 |
| results[21].learning_rate | 0.04 |
| results[21].rounds | 600 |
| results[21].oof_pr_auc | 0.2838 |
| results[21].oof_brier | 0.0787 |
| results[22].num_leaves | 31 |
| results[22].min_data_in_leaf | 40 |
| results[22].learning_rate | 0.04 |
| results[22].rounds | 600 |
| results[22].oof_pr_auc | 0.2783 |
| results[22].oof_brier | 0.0795 |
| results[23].num_leaves | 31 |
| results[23].min_data_in_leaf | 100 |
| results[23].learning_rate | 0.04 |
| results[23].rounds | 600 |
| results[23].oof_pr_auc | 0.2766 |
| results[23].oof_brier | 0.0796 |

</details>

<details><summary>reports/B/tuning_optuna_b_ani2023-2024.json</summary>

[Sursa](../../reports/B/tuning_optuna_b_ani2023-2024.json) · SHA256 `b28d25272212e0afbdbaaac15ff0e426b1a50fa59f1cf9a0829b7146583a3b6c`

| Câmp | Valoare |
|---|---:|
| train_years | [2023, 2024] |
| oof_pr_auc.livrat | 0.2916 |
| oof_pr_auc.gasit | 0.2925 |
| test_2025.livrat.pr_auc | 0.2777 |
| test_2025.livrat.brier | 0.0841 |
| test_2025.gasit.pr_auc | 0.2763 |
| test_2025.gasit.brier | 0.0841 |
| test_2025.delta_pr_auc_ci90 | [-0.0029, 0.0004] |

</details>

<details><summary>reports/B/tuning_optuna_b_convectie_ani2023-2024.json</summary>

[Sursa](../../reports/B/tuning_optuna_b_convectie_ani2023-2024.json) · SHA256 `fc60e4f4260007acc2891b67055ee1e4bb947c90644cf5ff9a6e22e0771cb996`

| Câmp | Valoare |
|---|---:|
| train_years | [2023, 2024] |
| oof_pr_auc.livrat | 0.306 |
| oof_pr_auc.gasit | 0.308 |
| test_2025.livrat.pr_auc | 0.2865 |
| test_2025.livrat.brier | 0.0835 |
| test_2025.gasit.pr_auc | 0.2867 |
| test_2025.gasit.brier | 0.0835 |
| test_2025.delta_pr_auc_ci90 | [-0.0031, 0.0033] |

</details>

<details><summary>reports/C/ablation_fara_fizica.json</summary>

[Sursa](../../reports/C/ablation_fara_fizica.json) · SHA256 `90d8bc09598ff2dcfd4374a446a7ff7a637dfe6b486958db1a79c1ed7dfe5d2c`

| Câmp | Valoare |
|---|---:|
| model.mae_vmax_pu | 0.0118744 |
| model.rmse_vmax_pu | 0.0184296 |
| model.coverage_p10_p90 | 0.830466 |
| model.pr_auc_exceed | 0.384164 |
| model.recall_exceed | 7.60485e-05 |
| model.precision_exceed | 0.00238663 |
| model.brier | 0.0604865 |
| model.ece_exceed | 0.0349108 |
| by_topology_mae.rural1 | 0.00590073 |
| by_topology_mae.rural2 | 0.0238795 |
| by_topology_mae.rural3 | 0.0142226 |
| by_topology_mae.semiurb4 | 0.00662404 |
| by_topology_mae.semiurb5 | 0.0105456 |
| by_topology_mae.urban6 | 0.010074 |

</details>

<details><summary>reports/C/ablation_fara_tensiune_pornire.json</summary>

[Sursa](../../reports/C/ablation_fara_tensiune_pornire.json) · SHA256 `74464d34d70cd121680ffc05f89260626d5a09d1b13b15255ab5fe1479994451`

| Câmp | Valoare |
|---|---:|
| model.mae_vmax_pu | 0.0205278 |
| model.rmse_vmax_pu | 0.0248362 |
| model.coverage_p10_p90 | 0.832636 |
| model.pr_auc_exceed | 0.727923 |
| model.recall_exceed | 0.536294 |
| model.precision_exceed | 0.798099 |
| model.brier | 0.0371338 |
| model.ece_exceed | 0.00592021 |
| by_topology_mae.rural1 | 0.0198267 |
| by_topology_mae.rural2 | 0.0185444 |
| by_topology_mae.rural3 | 0.0213693 |
| by_topology_mae.semiurb4 | 0.0218818 |
| by_topology_mae.semiurb5 | 0.0199152 |
| by_topology_mae.urban6 | 0.0216294 |

</details>

<details><summary>reports/C/error_tables.json</summary>

[Sursa](../../reports/C/error_tables.json) · SHA256 `ba780f91a910022ef48ff760a841f93705c1a38a13bef041f98fb41f0c22d2c0`

| Câmp | Valoare |
|---|---:|
| pe_topologie[0].zile_post | 54000 |
| pe_topologie[0].mae_model | 0.0044 |
| pe_topologie[0].mae_baseline | 0.02 |
| pe_topologie[0].eroare_medie_semn | 0.0006 |
| pe_topologie[0].rata_depasiri | 0 |
| pe_topologie[0].acoperire_p10_p90 | 0.823 |
| pe_topologie[1].zile_post | 54000 |
| pe_topologie[1].mae_model | 0.0061 |
| pe_topologie[1].mae_baseline | 0.0269 |
| pe_topologie[1].eroare_medie_semn | 0 |
| pe_topologie[1].rata_depasiri | 0.269 |
| pe_topologie[1].acoperire_p10_p90 | 0.871 |
| pe_topologie[1].pr_auc | 0.978 |
| pe_topologie[1].recall | 0.932 |
| pe_topologie[2].zile_post | 54000 |
| pe_topologie[2].mae_model | 0.0064 |
| pe_topologie[2].mae_baseline | 0.0254 |
| pe_topologie[2].eroare_medie_semn | -0.0009 |
| pe_topologie[2].rata_depasiri | 0.164 |
| pe_topologie[2].acoperire_p10_p90 | 0.801 |
| pe_topologie[2].pr_auc | 0.939 |
| pe_topologie[2].recall | 0.812 |
| pe_topologie[3].zile_post | 54000 |
| pe_topologie[3].mae_model | 0.0047 |
| pe_topologie[3].mae_baseline | 0.0216 |
| pe_topologie[3].eroare_medie_semn | -0.0017 |
| pe_topologie[3].rata_depasiri | 0.018 |
| pe_topologie[3].acoperire_p10_p90 | 0.866 |
| pe_topologie[3].pr_auc | 0.852 |
| pe_topologie[3].recall | 0.31 |
| pe_topologie[4].zile_post | 54000 |
| pe_topologie[4].mae_model | 0.0061 |
| pe_topologie[4].mae_baseline | 0.0214 |
| pe_topologie[4].eroare_medie_semn | -0.0024 |
| pe_topologie[4].rata_depasiri | 0.036 |
| pe_topologie[4].acoperire_p10_p90 | 0.758 |
| pe_topologie[4].pr_auc | 0.881 |
| pe_topologie[4].recall | 0.885 |
| pe_topologie[5].zile_post | 54000 |
| pe_topologie[5].mae_model | 0.0048 |
| pe_topologie[5].mae_baseline | 0.0211 |
| pe_topologie[5].eroare_medie_semn | 0.0014 |
| pe_topologie[5].rata_depasiri | 0 |
| pe_topologie[5].acoperire_p10_p90 | 0.809 |
| pe_conductor[0].zile_post | 22950 |
| pe_conductor[0].mae_model | 0.0058 |
| pe_conductor[0].mae_baseline | 0.0232 |
| pe_conductor[0].eroare_medie_semn | 0.0001 |
| pe_conductor[0].rata_depasiri | 0.164 |
| pe_conductor[0].acoperire_p10_p90 | 0.827 |
| pe_conductor[0].pr_auc | 0.959 |
| pe_conductor[0].recall | 0.916 |
| pe_conductor[1].zile_post | 79650 |
| pe_conductor[1].mae_model | 0.005 |
| pe_conductor[1].mae_baseline | 0.0209 |
| pe_conductor[1].eroare_medie_semn | 0.0005 |
| pe_conductor[1].rata_depasiri | 0.016 |
| pe_conductor[1].acoperire_p10_p90 | 0.819 |
| pe_conductor[1].pr_auc | 0.801 |
| pe_conductor[1].recall | 0.717 |
| pe_conductor[2].zile_post | 54000 |
| pe_conductor[2].mae_model | 0.0054 |
| pe_conductor[2].mae_baseline | 0.0204 |
| pe_conductor[2].eroare_medie_semn | -0.0012 |
| pe_conductor[2].rata_depasiri | 0.005 |
| pe_conductor[2].acoperire_p10_p90 | 0.788 |
| pe_conductor[2].pr_auc | 0.738 |
| pe_conductor[2].recall | 0.788 |
| pe_conductor[3].zile_post | 72900 |
| pe_conductor[3].mae_model | 0.0055 |
| pe_conductor[3].mae_baseline | 0.026 |
| pe_conductor[3].eroare_medie_semn | -0.0012 |
| pe_conductor[3].rata_depasiri | 0.184 |
| pe_conductor[3].acoperire_p10_p90 | 0.845 |
| pe_conductor[3].pr_auc | 0.979 |
| pe_conductor[3].recall | 0.902 |
| pe_conductor[4].zile_post | 94500 |
| pe_conductor[4].mae_model | 0.0056 |
| pe_conductor[4].mae_baseline | 0.0231 |
| pe_conductor[4].eroare_medie_semn | -0.0005 |
| pe_conductor[4].rata_depasiri | 0.081 |
| pe_conductor[4].acoperire_p10_p90 | 0.822 |
| pe_conductor[4].pr_auc | 0.912 |
| pe_conductor[4].recall | 0.802 |
| pe_lungime[0].zile_post | 81000 |
| pe_lungime[0].mae_model | 0.0045 |
| pe_lungime[0].mae_baseline | 0.0213 |
| pe_lungime[0].eroare_medie_semn | 0.0002 |
| pe_lungime[0].rata_depasiri | 0.012 |
| pe_lungime[0].acoperire_p10_p90 | 0.827 |
| pe_lungime[0].pr_auc | 0.842 |
| pe_lungime[0].recall | 0.31 |
| pe_lungime[1].zile_post | 81000 |
| pe_lungime[1].mae_model | 0.0052 |
| pe_lungime[1].mae_baseline | 0.0207 |
| pe_lungime[1].eroare_medie_semn | -0.0005 |
| pe_lungime[1].rata_depasiri | 0.003 |
| pe_lungime[1].acoperire_p10_p90 | 0.81 |
| pe_lungime[1].pr_auc | 0.587 |
| pe_lungime[1].recall | 0.818 |
| pe_lungime[2].zile_post | 81000 |
| pe_lungime[2].mae_model | 0.0057 |
| pe_lungime[2].mae_baseline | 0.0223 |
| pe_lungime[2].eroare_medie_semn | -0.0006 |
| pe_lungime[2].rata_depasiri | 0.057 |
| pe_lungime[2].acoperire_p10_p90 | 0.806 |
| pe_lungime[2].pr_auc | 0.878 |
| pe_lungime[2].recall | 0.805 |
| pe_lungime[3].zile_post | 81000 |
| pe_lungime[3].mae_model | 0.0063 |
| pe_lungime[3].mae_baseline | 0.0267 |
| pe_lungime[3].eroare_medie_semn | -0.001 |
| pe_lungime[3].rata_depasiri | 0.252 |
| pe_lungime[3].acoperire_p10_p90 | 0.843 |
| pe_lungime[3].pr_auc | 0.972 |
| pe_lungime[3].recall | 0.906 |
| pe_nori_zile_cu_soare[0].zile_post | 94080 |
| pe_nori_zile_cu_soare[0].mae_model | 0.0058 |
| pe_nori_zile_cu_soare[0].mae_baseline | 0.0238 |
| pe_nori_zile_cu_soare[0].eroare_medie_semn | -0.0006 |
| pe_nori_zile_cu_soare[0].rata_depasiri | 0.125 |
| pe_nori_zile_cu_soare[0].acoperire_p10_p90 | 0.798 |
| pe_nori_zile_cu_soare[0].pr_auc | 0.959 |
| pe_nori_zile_cu_soare[0].recall | 0.885 |
| pe_nori_zile_cu_soare[1].zile_post | 59520 |
| pe_nori_zile_cu_soare[1].mae_model | 0.0057 |
| pe_nori_zile_cu_soare[1].mae_baseline | 0.0236 |
| pe_nori_zile_cu_soare[1].eroare_medie_semn | -0.0007 |
| pe_nori_zile_cu_soare[1].rata_depasiri | 0.118 |
| pe_nori_zile_cu_soare[1].acoperire_p10_p90 | 0.799 |
| pe_nori_zile_cu_soare[1].pr_auc | 0.955 |
| pe_nori_zile_cu_soare[1].recall | 0.868 |
| pe_nori_zile_cu_soare[2].zile_post | 49440 |
| pe_nori_zile_cu_soare[2].mae_model | 0.0057 |
| pe_nori_zile_cu_soare[2].mae_baseline | 0.0231 |
| pe_nori_zile_cu_soare[2].eroare_medie_semn | -0.0005 |
| pe_nori_zile_cu_soare[2].rata_depasiri | 0.094 |
| pe_nori_zile_cu_soare[2].acoperire_p10_p90 | 0.803 |
| pe_nori_zile_cu_soare[2].pr_auc | 0.942 |
| pe_nori_zile_cu_soare[2].recall | 0.851 |
| pe_nori_zile_cu_soare[3].zile_post | 35040 |
| pe_nori_zile_cu_soare[3].mae_model | 0.0057 |
| pe_nori_zile_cu_soare[3].mae_baseline | 0.0226 |
| pe_nori_zile_cu_soare[3].eroare_medie_semn | -0.0003 |
| pe_nori_zile_cu_soare[3].rata_depasiri | 0.072 |
| pe_nori_zile_cu_soare[3].acoperire_p10_p90 | 0.812 |
| pe_nori_zile_cu_soare[3].pr_auc | 0.927 |
| pe_nori_zile_cu_soare[3].recall | 0.815 |
| pe_partea_difuza[0].zile_post | 84000 |
| pe_partea_difuza[0].mae_model | 0.0058 |
| pe_partea_difuza[0].mae_baseline | 0.0241 |
| pe_partea_difuza[0].eroare_medie_semn | -0.0007 |
| pe_partea_difuza[0].rata_depasiri | 0.141 |
| pe_partea_difuza[0].acoperire_p10_p90 | 0.796 |
| pe_partea_difuza[0].pr_auc | 0.963 |
| pe_partea_difuza[0].recall | 0.892 |
| pe_partea_difuza[1].zile_post | 92160 |
| pe_partea_difuza[1].mae_model | 0.0058 |
| pe_partea_difuza[1].mae_baseline | 0.0233 |
| pe_partea_difuza[1].eroare_medie_semn | -0.0006 |
| pe_partea_difuza[1].rata_depasiri | 0.105 |
| pe_partea_difuza[1].acoperire_p10_p90 | 0.799 |
| pe_partea_difuza[1].pr_auc | 0.949 |
| pe_partea_difuza[1].recall | 0.861 |
| pe_partea_difuza[2].zile_post | 32640 |
| pe_partea_difuza[2].mae_model | 0.0058 |
| pe_partea_difuza[2].mae_baseline | 0.0228 |
| pe_partea_difuza[2].eroare_medie_semn | -0.0004 |
| pe_partea_difuza[2].rata_depasiri | 0.08 |
| pe_partea_difuza[2].acoperire_p10_p90 | 0.805 |
| pe_partea_difuza[2].pr_auc | 0.93 |
| pe_partea_difuza[2].recall | 0.824 |
| pe_partea_difuza[3].zile_post | 29280 |
| pe_partea_difuza[3].mae_model | 0.0056 |
| pe_partea_difuza[3].mae_baseline | 0.0224 |
| pe_partea_difuza[3].eroare_medie_semn | -0.0003 |
| pe_partea_difuza[3].rata_depasiri | 0.061 |
| pe_partea_difuza[3].acoperire_p10_p90 | 0.818 |
| pe_partea_difuza[3].pr_auc | 0.917 |
| pe_partea_difuza[3].recall | 0.797 |
| pe_baterii[0].zile_post | 81000 |
| pe_baterii[0].mae_model | 0.0046 |
| pe_baterii[0].mae_baseline | 0.0219 |
| pe_baterii[0].eroare_medie_semn | -0.0003 |
| pe_baterii[0].rata_depasiri | 0.015 |
| pe_baterii[0].acoperire_p10_p90 | 0.828 |
| pe_baterii[0].pr_auc | 0.841 |
| pe_baterii[0].recall | 0.861 |
| pe_baterii[1].zile_post | 93150 |
| pe_baterii[1].mae_model | 0.0055 |
| pe_baterii[1].mae_baseline | 0.0232 |
| pe_baterii[1].eroare_medie_semn | -0.0007 |
| pe_baterii[1].rata_depasiri | 0.113 |
| pe_baterii[1].acoperire_p10_p90 | 0.84 |
| pe_baterii[1].pr_auc | 0.961 |
| pe_baterii[1].recall | 0.861 |
| pe_baterii[2].zile_post | 80325 |
| pe_baterii[2].mae_model | 0.0059 |
| pe_baterii[2].mae_baseline | 0.0234 |
| pe_baterii[2].eroare_medie_semn | -0.0007 |
| pe_baterii[2].rata_depasiri | 0.111 |
| pe_baterii[2].acoperire_p10_p90 | 0.805 |
| pe_baterii[2].pr_auc | 0.962 |
| pe_baterii[2].recall | 0.871 |
| pe_baterii[3].zile_post | 69525 |
| pe_baterii[3].mae_model | 0.0058 |
| pe_baterii[3].mae_baseline | 0.0224 |
| pe_baterii[3].eroare_medie_semn | -0.0002 |
| pe_baterii[3].rata_depasiri | 0.081 |
| pe_baterii[3].acoperire_p10_p90 | 0.808 |
| pe_baterii[3].pr_auc | 0.933 |
| pe_baterii[3].recall | 0.865 |
| pe_luna[0].zile_post | 29760 |
| pe_luna[0].mae_model | 0.0053 |
| pe_luna[0].mae_baseline | 0.0217 |
| pe_luna[0].eroare_medie_semn | -0 |
| pe_luna[0].rata_depasiri | 0.021 |
| pe_luna[0].acoperire_p10_p90 | 0.833 |
| pe_luna[0].pr_auc | 0.864 |
| pe_luna[0].recall | 0.785 |
| pe_luna[1].zile_post | 26880 |
| pe_luna[1].mae_model | 0.0053 |
| pe_luna[1].mae_baseline | 0.022 |
| pe_luna[1].eroare_medie_semn | -0.0001 |
| pe_luna[1].rata_depasiri | 0.038 |
| pe_luna[1].acoperire_p10_p90 | 0.835 |
| pe_luna[1].pr_auc | 0.929 |
| pe_luna[1].recall | 0.824 |
| pe_luna[2].zile_post | 29760 |
| pe_luna[2].mae_model | 0.0057 |
| pe_luna[2].mae_baseline | 0.0225 |
| pe_luna[2].eroare_medie_semn | -0.0002 |
| pe_luna[2].rata_depasiri | 0.068 |
| pe_luna[2].acoperire_p10_p90 | 0.81 |
| pe_luna[2].pr_auc | 0.934 |
| pe_luna[2].recall | 0.841 |
| pe_luna[3].zile_post | 28800 |
| pe_luna[3].mae_model | 0.0056 |
| pe_luna[3].mae_baseline | 0.0231 |
| pe_luna[3].eroare_medie_semn | -0.0006 |
| pe_luna[3].rata_depasiri | 0.099 |
| pe_luna[3].acoperire_p10_p90 | 0.812 |
| pe_luna[3].pr_auc | 0.954 |
| pe_luna[3].recall | 0.877 |
| pe_luna[4].zile_post | 29760 |
| pe_luna[4].mae_model | 0.0056 |
| pe_luna[4].mae_baseline | 0.0231 |
| pe_luna[4].eroare_medie_semn | -0.0007 |
| pe_luna[4].rata_depasiri | 0.101 |
| pe_luna[4].acoperire_p10_p90 | 0.812 |
| pe_luna[4].pr_auc | 0.955 |
| pe_luna[4].recall | 0.873 |
| pe_luna[5].zile_post | 28800 |
| pe_luna[5].mae_model | 0.0056 |
| pe_luna[5].mae_baseline | 0.0239 |
| pe_luna[5].eroare_medie_semn | -0.0006 |
| pe_luna[5].rata_depasiri | 0.132 |
| pe_luna[5].acoperire_p10_p90 | 0.803 |
| pe_luna[5].pr_auc | 0.96 |
| pe_luna[5].recall | 0.886 |
| pe_luna[6].zile_post | 29760 |
| pe_luna[6].mae_model | 0.0056 |
| pe_luna[6].mae_baseline | 0.0238 |
| pe_luna[6].eroare_medie_semn | -0.0008 |
| pe_luna[6].rata_depasiri | 0.131 |
| pe_luna[6].acoperire_p10_p90 | 0.805 |
| pe_luna[6].pr_auc | 0.96 |
| pe_luna[6].recall | 0.882 |
| pe_luna[7].zile_post | 29760 |
| pe_luna[7].mae_model | 0.0056 |
| pe_luna[7].mae_baseline | 0.0239 |
| pe_luna[7].eroare_medie_semn | -0.0009 |
| pe_luna[7].rata_depasiri | 0.136 |
| pe_luna[7].acoperire_p10_p90 | 0.803 |
| pe_luna[7].pr_auc | 0.965 |
| pe_luna[7].recall | 0.884 |
| pe_luna[8].zile_post | 28800 |
| pe_luna[8].mae_model | 0.0055 |
| pe_luna[8].mae_baseline | 0.0232 |
| pe_luna[8].eroare_medie_semn | -0.0007 |
| pe_luna[8].rata_depasiri | 0.104 |
| pe_luna[8].acoperire_p10_p90 | 0.809 |
| pe_luna[8].pr_auc | 0.948 |
| pe_luna[8].recall | 0.85 |
| pe_luna[9].zile_post | 29760 |
| pe_luna[9].mae_model | 0.0051 |
| pe_luna[9].mae_baseline | 0.022 |
| pe_luna[9].eroare_medie_semn | -0.0006 |
| pe_luna[9].rata_depasiri | 0.057 |
| pe_luna[9].acoperire_p10_p90 | 0.841 |
| pe_luna[9].pr_auc | 0.94 |
| pe_luna[9].recall | 0.837 |
| pe_luna[10].zile_post | 17280 |
| pe_luna[10].mae_model | 0.0047 |
| pe_luna[10].mae_baseline | 0.021 |
| pe_luna[10].eroare_medie_semn | -0.0002 |
| pe_luna[10].rata_depasiri | 0.014 |
| pe_luna[10].acoperire_p10_p90 | 0.874 |
| pe_luna[10].pr_auc | 0.864 |
| pe_luna[10].recall | 0.731 |
| pe_luna[11].zile_post | 14880 |
| pe_luna[11].mae_model | 0.0049 |
| pe_luna[11].mae_baseline | 0.0214 |
| pe_luna[11].eroare_medie_semn | 0 |
| pe_luna[11].rata_depasiri | 0.008 |
| pe_luna[11].acoperire_p10_p90 | 0.861 |
| pe_luna[11].pr_auc | 0.844 |
| pe_luna[11].recall | 0.777 |
| pe_zi[0].zile_post | 102240 |
| pe_zi[0].mae_model | 0.0054 |
| pe_zi[0].mae_baseline | 0.0227 |
| pe_zi[0].eroare_medie_semn | -0.0005 |
| pe_zi[0].rata_depasiri | 0.079 |
| pe_zi[0].acoperire_p10_p90 | 0.828 |
| pe_zi[0].pr_auc | 0.956 |
| pe_zi[0].recall | 0.861 |
| pe_zi[1].zile_post | 221760 |
| pe_zi[1].mae_model | 0.0055 |
| pe_zi[1].mae_baseline | 0.0228 |
| pe_zi[1].eroare_medie_semn | -0.0005 |
| pe_zi[1].rata_depasiri | 0.082 |
| pe_zi[1].acoperire_p10_p90 | 0.818 |
| pe_zi[1].pr_auc | 0.949 |
| pe_zi[1].recall | 0.867 |
| langa_prag.zile_post_intre_1_09_si_1_11 | 19165 |
| langa_prag.parte_din_test | 0.0592 |
| langa_prag.acuratete_clasificare_langa_prag | 0.685 |
| langa_prag.ratari_fn | 3547 |
| langa_prag.fn_tensiune_mediana_reala | 1.1041 |
| langa_prag.fn_parte_sub_1_115 | 0.973 |
| langa_prag.alarme_false_fp | 3432 |
| langa_prag.fp_tensiune_mediana_reala | 1.0952 |
| langa_prag.fp_parte_peste_1_09 | 0.835 |
| cele_mai_mari_200_erori.eroare_medie_absoluta | 0.0356 |
| cele_mai_mari_200_erori.parte_subestimari | 0.625 |
| cele_mai_mari_200_erori.topologii.rural2 | 101 |
| cele_mai_mari_200_erori.topologii.rural3 | 99 |
| cele_mai_mari_200_erori.conductori.TYIR_50 | 101 |
| cele_mai_mari_200_erori.conductori.AL_35_vechi | 66 |
| cele_mai_mari_200_erori.conductori.TYIR_70 | 32 |
| cele_mai_mari_200_erori.conductori.NAYY_4x150 | 1 |
| cele_mai_mari_200_erori.nori_median | 24.9 |
| cele_mai_mari_200_erori.nori_median_test | 55.3 |
| cele_mai_mari_200_erori.baterii_median | 0.411 |
| cele_mai_mari_200_erori.sens_pv_median | 0.2111 |
| cele_mai_mari_200_erori.sens_pv_median_test | 0.0293 |

</details>

<details><summary>reports/C/experiment_gti_morning.json</summary>

[Sursa](../../reports/C/experiment_gti_morning.json) · SHA256 `3c1adbd521810bc32358e6d1e9ca5229f126ef742d3e6f8a7952c971d93a7111`

| Câmp | Valoare |
|---|---:|
| model.mae_vmax_pu | 0.00535459 |
| model.coverage_p10_p90 | 0.824707 |
| model.pr_auc_exceed | 0.949219 |
| model.recall_exceed | 0.842237 |
| model.brier | 0.0152808 |
| by_topology_mae.rural1 | 0.0043298 |
| by_topology_mae.rural2 | 0.00597292 |
| by_topology_mae.rural3 | 0.00639048 |
| by_topology_mae.semiurb4 | 0.00433391 |
| by_topology_mae.semiurb5 | 0.00615019 |
| by_topology_mae.urban6 | 0.00495021 |
| mae_by_battery_share.fara | 0.00447 |
| mae_by_battery_share.sub25 | 0.00544 |
| mae_by_battery_share.25-50 | 0.00584 |
| mae_by_battery_share.peste50 | 0.00571 |

</details>

<details><summary>reports/C/experiments_extra.json</summary>

[Sursa](../../reports/C/experiments_extra.json) · SHA256 `57d481d354f6e882cd58cf0b268b25b86499d141c151ebce347c6caa204cdede`

| Câmp | Valoare |
|---|---:|
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2015 | 1300.1 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2016 | 1276.3 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2017 | 1360.6 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2018 | 1334.2 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2019 | 1335.3 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2020 | 1386.7 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2021 | 1327.7 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2022 | 1433.1 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2023 | 1378.6 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2024 | 1381.8 |
| meta.kwh_per_kwp_bucuresti.fizica_livrata.2025 | 1362.3 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2015 | 1244.6 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2016 | 1244.6 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2017 | 1277.3 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2018 | 1239.4 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2019 | 1320.8 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2020 | 1374.9 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2021 | 1285.8 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2022 | 1429.8 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2023 | 1339.1 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2024 | 1381.6 |
| meta.kwh_per_kwp_bucuresti.fizica_v2.2025 | 1334.7 |
| meta.kwh_per_kwp_bucuresti.pvgis_referinta | 1282 |
| meta.ipoteze_fizica_v2.faiman_u0 | 25 |
| meta.ipoteze_fizica_v2.faiman_u1 | 6.84 |
| meta.ipoteze_fizica_v2.vant_10m_la_panou | 0.67 |
| meta.ipoteze_fizica_v2.zapada_acopera_de_la_m | 0.03 |
| meta.ipoteze_fizica_v2.factor_gti_sub_zapada | 0.2 |
| rows[baza].train_rows | 350880 |
| rows[baza].seconds | 350 |
| rows[baza].bucuresti_2025.mae_vmax_pu | 0.00538 |
| rows[baza].bucuresti_2025.coverage_p10_p90 | 0.82283 |
| rows[baza].bucuresti_2025.brier | 0.01541 |
| rows[baza].bucuresti_2025.recall_exceed | 0.86244 |
| rows[baza].bucuresti_2025.precision_exceed | 0.85823 |
| rows[baza].bucuresti_2025.exceed_rate | 0.0812 |
| rows[baza].bucuresti_2025.pr_auc_exceed | 0.94878 |
| rows[baza].bucuresti_2025.test_rows | 324000 |
| rows[baza].timisoara_2025.mae_vmax_pu | 0.00539 |
| rows[baza].timisoara_2025.coverage_p10_p90 | 0.82046 |
| rows[baza].timisoara_2025.brier | 0.01584 |
| rows[baza].timisoara_2025.recall_exceed | 0.8627 |
| rows[baza].timisoara_2025.precision_exceed | 0.85762 |
| rows[baza].timisoara_2025.exceed_rate | 0.0829 |
| rows[baza].timisoara_2025.pr_auc_exceed | 0.94831 |
| rows[baza].timisoara_2025.test_rows | 324000 |
| rows[baza].cluj_2025.mae_vmax_pu | 0.00539 |
| rows[baza].cluj_2025.coverage_p10_p90 | 0.82219 |
| rows[baza].cluj_2025.brier | 0.01502 |
| rows[baza].cluj_2025.recall_exceed | 0.86496 |
| rows[baza].cluj_2025.precision_exceed | 0.85874 |
| rows[baza].cluj_2025.exceed_rate | 0.07931 |
| rows[baza].cluj_2025.pr_auc_exceed | 0.94842 |
| rows[baza].cluj_2025.test_rows | 324000 |
| rows[baza].iasi_2025.mae_vmax_pu | 0.00534 |
| rows[baza].iasi_2025.coverage_p10_p90 | 0.82495 |
| rows[baza].iasi_2025.brier | 0.01445 |
| rows[baza].iasi_2025.recall_exceed | 0.86592 |
| rows[baza].iasi_2025.precision_exceed | 0.86014 |
| rows[baza].iasi_2025.exceed_rate | 0.07677 |
| rows[baza].iasi_2025.pr_auc_exceed | 0.94946 |
| rows[baza].iasi_2025.test_rows | 324000 |
| rows[baza].constanta_2025.mae_vmax_pu | 0.00545 |
| rows[baza].constanta_2025.coverage_p10_p90 | 0.81825 |
| rows[baza].constanta_2025.brier | 0.01577 |
| rows[baza].constanta_2025.recall_exceed | 0.87084 |
| rows[baza].constanta_2025.precision_exceed | 0.86163 |
| rows[baza].constanta_2025.exceed_rate | 0.08577 |
| rows[baza].constanta_2025.pr_auc_exceed | 0.95175 |
| rows[baza].constanta_2025.test_rows | 324000 |
| rows[mai_multi_ani].train_rows | 1.75344e+06 |
| rows[mai_multi_ani].seconds | 1005 |
| rows[mai_multi_ani].bucuresti_2025.mae_vmax_pu | 0.00538 |
| rows[mai_multi_ani].bucuresti_2025.coverage_p10_p90 | 0.82077 |
| rows[mai_multi_ani].bucuresti_2025.brier | 0.01471 |
| rows[mai_multi_ani].bucuresti_2025.recall_exceed | 0.86031 |
| rows[mai_multi_ani].bucuresti_2025.precision_exceed | 0.87834 |
| rows[mai_multi_ani].bucuresti_2025.exceed_rate | 0.0812 |
| rows[mai_multi_ani].bucuresti_2025.pr_auc_exceed | 0.95341 |
| rows[mai_multi_ani].bucuresti_2025.test_rows | 324000 |
| rows[mai_multi_ani].timisoara_2025.mae_vmax_pu | 0.00539 |
| rows[mai_multi_ani].timisoara_2025.coverage_p10_p90 | 0.81985 |
| rows[mai_multi_ani].timisoara_2025.brier | 0.01511 |
| rows[mai_multi_ani].timisoara_2025.recall_exceed | 0.85942 |
| rows[mai_multi_ani].timisoara_2025.precision_exceed | 0.87772 |
| rows[mai_multi_ani].timisoara_2025.exceed_rate | 0.0829 |
| rows[mai_multi_ani].timisoara_2025.pr_auc_exceed | 0.95288 |
| rows[mai_multi_ani].timisoara_2025.test_rows | 324000 |
| rows[mai_multi_ani].cluj_2025.mae_vmax_pu | 0.00539 |
| rows[mai_multi_ani].cluj_2025.coverage_p10_p90 | 0.82119 |
| rows[mai_multi_ani].cluj_2025.brier | 0.01434 |
| rows[mai_multi_ani].cluj_2025.recall_exceed | 0.86457 |
| rows[mai_multi_ani].cluj_2025.precision_exceed | 0.87956 |
| rows[mai_multi_ani].cluj_2025.exceed_rate | 0.07931 |
| rows[mai_multi_ani].cluj_2025.pr_auc_exceed | 0.95327 |
| rows[mai_multi_ani].cluj_2025.test_rows | 324000 |
| rows[mai_multi_ani].iasi_2025.mae_vmax_pu | 0.00534 |
| rows[mai_multi_ani].iasi_2025.coverage_p10_p90 | 0.82414 |
| rows[mai_multi_ani].iasi_2025.brier | 0.01377 |
| rows[mai_multi_ani].iasi_2025.recall_exceed | 0.86363 |
| rows[mai_multi_ani].iasi_2025.precision_exceed | 0.87821 |
| rows[mai_multi_ani].iasi_2025.exceed_rate | 0.07677 |
| rows[mai_multi_ani].iasi_2025.pr_auc_exceed | 0.954 |
| rows[mai_multi_ani].iasi_2025.test_rows | 324000 |
| rows[mai_multi_ani].constanta_2025.mae_vmax_pu | 0.00544 |
| rows[mai_multi_ani].constanta_2025.coverage_p10_p90 | 0.81645 |
| rows[mai_multi_ani].constanta_2025.brier | 0.01508 |
| rows[mai_multi_ani].constanta_2025.recall_exceed | 0.86948 |
| rows[mai_multi_ani].constanta_2025.precision_exceed | 0.8782 |
| rows[mai_multi_ani].constanta_2025.exceed_rate | 0.08577 |
| rows[mai_multi_ani].constanta_2025.pr_auc_exceed | 0.95638 |
| rows[mai_multi_ani].constanta_2025.test_rows | 324000 |
| rows[mai_multe_regiuni].train_rows | 4.55952e+06 |
| rows[mai_multe_regiuni].seconds | 1887 |
| rows[mai_multe_regiuni].bucuresti_2025.mae_vmax_pu | 0.00533 |
| rows[mai_multe_regiuni].bucuresti_2025.coverage_p10_p90 | 0.82549 |
| rows[mai_multe_regiuni].bucuresti_2025.brier | 0.01488 |
| rows[mai_multe_regiuni].bucuresti_2025.recall_exceed | 0.8645 |
| rows[mai_multe_regiuni].bucuresti_2025.precision_exceed | 0.87189 |
| rows[mai_multe_regiuni].bucuresti_2025.exceed_rate | 0.0812 |
| rows[mai_multe_regiuni].bucuresti_2025.pr_auc_exceed | 0.95044 |
| rows[mai_multe_regiuni].bucuresti_2025.test_rows | 324000 |
| rows[mai_multe_regiuni].timisoara_2025.mae_vmax_pu | 0.00534 |
| rows[mai_multe_regiuni].timisoara_2025.coverage_p10_p90 | 0.82533 |
| rows[mai_multe_regiuni].timisoara_2025.brier | 0.01526 |
| rows[mai_multe_regiuni].timisoara_2025.recall_exceed | 0.86523 |
| rows[mai_multe_regiuni].timisoara_2025.precision_exceed | 0.87038 |
| rows[mai_multe_regiuni].timisoara_2025.exceed_rate | 0.0829 |
| rows[mai_multe_regiuni].timisoara_2025.pr_auc_exceed | 0.94995 |
| rows[mai_multe_regiuni].timisoara_2025.test_rows | 324000 |
| rows[mai_multe_regiuni].cluj_2025.mae_vmax_pu | 0.00533 |
| rows[mai_multe_regiuni].cluj_2025.coverage_p10_p90 | 0.82665 |
| rows[mai_multe_regiuni].cluj_2025.brier | 0.01449 |
| rows[mai_multe_regiuni].cluj_2025.recall_exceed | 0.86862 |
| rows[mai_multe_regiuni].cluj_2025.precision_exceed | 0.87065 |
| rows[mai_multe_regiuni].cluj_2025.exceed_rate | 0.07931 |
| rows[mai_multe_regiuni].cluj_2025.pr_auc_exceed | 0.95025 |
| rows[mai_multe_regiuni].cluj_2025.test_rows | 324000 |
| rows[mai_multe_regiuni].iasi_2025.mae_vmax_pu | 0.00528 |
| rows[mai_multe_regiuni].iasi_2025.coverage_p10_p90 | 0.82987 |
| rows[mai_multe_regiuni].iasi_2025.brier | 0.0139 |
| rows[mai_multe_regiuni].iasi_2025.recall_exceed | 0.87123 |
| rows[mai_multe_regiuni].iasi_2025.precision_exceed | 0.87298 |
| rows[mai_multe_regiuni].iasi_2025.exceed_rate | 0.07677 |
| rows[mai_multe_regiuni].iasi_2025.pr_auc_exceed | 0.95081 |
| rows[mai_multe_regiuni].iasi_2025.test_rows | 324000 |
| rows[mai_multe_regiuni].constanta_2025.mae_vmax_pu | 0.00538 |
| rows[mai_multe_regiuni].constanta_2025.coverage_p10_p90 | 0.82101 |
| rows[mai_multe_regiuni].constanta_2025.brier | 0.01516 |
| rows[mai_multe_regiuni].constanta_2025.recall_exceed | 0.8743 |
| rows[mai_multe_regiuni].constanta_2025.precision_exceed | 0.87373 |
| rows[mai_multe_regiuni].constanta_2025.exceed_rate | 0.08577 |
| rows[mai_multe_regiuni].constanta_2025.pr_auc_exceed | 0.95366 |
| rows[mai_multe_regiuni].constanta_2025.test_rows | 324000 |
| rows[ani_si_regiuni].train_rows | 5.96208e+06 |
| rows[ani_si_regiuni].seconds | 1265 |
| rows[ani_si_regiuni].bucuresti_2025.mae_vmax_pu | 0.00535 |
| rows[ani_si_regiuni].bucuresti_2025.coverage_p10_p90 | 0.83034 |
| rows[ani_si_regiuni].bucuresti_2025.brier | 0.01447 |
| rows[ani_si_regiuni].bucuresti_2025.recall_exceed | 0.84135 |
| rows[ani_si_regiuni].bucuresti_2025.precision_exceed | 0.90517 |
| rows[ani_si_regiuni].bucuresti_2025.exceed_rate | 0.0812 |
| rows[ani_si_regiuni].bucuresti_2025.pr_auc_exceed | 0.95397 |
| rows[ani_si_regiuni].bucuresti_2025.test_rows | 324000 |
| rows[ani_si_regiuni].timisoara_2025.mae_vmax_pu | 0.00536 |
| rows[ani_si_regiuni].timisoara_2025.coverage_p10_p90 | 0.82931 |
| rows[ani_si_regiuni].timisoara_2025.brier | 0.01481 |
| rows[ani_si_regiuni].timisoara_2025.recall_exceed | 0.84152 |
| rows[ani_si_regiuni].timisoara_2025.precision_exceed | 0.90514 |
| rows[ani_si_regiuni].timisoara_2025.exceed_rate | 0.0829 |
| rows[ani_si_regiuni].timisoara_2025.pr_auc_exceed | 0.95347 |
| rows[ani_si_regiuni].timisoara_2025.test_rows | 324000 |
| rows[ani_si_regiuni].cluj_2025.mae_vmax_pu | 0.00535 |
| rows[ani_si_regiuni].cluj_2025.coverage_p10_p90 | 0.83081 |
| rows[ani_si_regiuni].cluj_2025.brier | 0.01401 |
| rows[ani_si_regiuni].cluj_2025.recall_exceed | 0.8457 |
| rows[ani_si_regiuni].cluj_2025.precision_exceed | 0.90519 |
| rows[ani_si_regiuni].cluj_2025.exceed_rate | 0.07931 |
| rows[ani_si_regiuni].cluj_2025.pr_auc_exceed | 0.95412 |
| rows[ani_si_regiuni].cluj_2025.test_rows | 324000 |
| rows[ani_si_regiuni].iasi_2025.mae_vmax_pu | 0.00531 |
| rows[ani_si_regiuni].iasi_2025.coverage_p10_p90 | 0.83337 |
| rows[ani_si_regiuni].iasi_2025.brier | 0.01354 |
| rows[ani_si_regiuni].iasi_2025.recall_exceed | 0.8469 |
| rows[ani_si_regiuni].iasi_2025.precision_exceed | 0.90598 |
| rows[ani_si_regiuni].iasi_2025.exceed_rate | 0.07677 |
| rows[ani_si_regiuni].iasi_2025.pr_auc_exceed | 0.95435 |
| rows[ani_si_regiuni].iasi_2025.test_rows | 324000 |
| rows[ani_si_regiuni].constanta_2025.mae_vmax_pu | 0.00541 |
| rows[ani_si_regiuni].constanta_2025.coverage_p10_p90 | 0.82593 |
| rows[ani_si_regiuni].constanta_2025.brier | 0.01476 |
| rows[ani_si_regiuni].constanta_2025.recall_exceed | 0.85199 |
| rows[ani_si_regiuni].constanta_2025.precision_exceed | 0.90573 |
| rows[ani_si_regiuni].constanta_2025.exceed_rate | 0.08577 |
| rows[ani_si_regiuni].constanta_2025.pr_auc_exceed | 0.95713 |
| rows[ani_si_regiuni].constanta_2025.test_rows | 324000 |
| rows[fizica_v2_fara_vant_zapada].train_rows | 350880 |
| rows[fizica_v2_fara_vant_zapada].seconds | 308 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.mae_vmax_pu | 0.00576 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.coverage_p10_p90 | 0.80711 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.brier | 0.01558 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.recall_exceed | 0.8746 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.precision_exceed | 0.84899 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.exceed_rate | 0.0796 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.pr_auc_exceed | 0.94607 |
| rows[fizica_v2_fara_vant_zapada].bucuresti_2025_fizica_v2.test_rows | 324000 |
| rows[fizica_v2_cu_vant_zapada].train_rows | 350880 |
| rows[fizica_v2_cu_vant_zapada].seconds | 326 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.mae_vmax_pu | 0.00546 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.coverage_p10_p90 | 0.82913 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.brier | 0.01478 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.recall_exceed | 0.87902 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.precision_exceed | 0.85868 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.exceed_rate | 0.0796 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.pr_auc_exceed | 0.94997 |
| rows[fizica_v2_cu_vant_zapada].bucuresti_2025_fizica_v2.test_rows | 324000 |

</details>

<details><summary>reports/C/metrics.json</summary>

[Sursa](../../reports/C/metrics.json) · SHA256 `2cdac7e2bd1cda76fd31940dd70aabfe2d956f23393cbfa2d19eb4dcb1f10576`

| Câmp | Valoare |
|---|---:|
| test_size | 324000 |
| metrics.mae_vmax_pu | 0.00543 |
| metrics.rmse_vmax_pu | 0.007 |
| metrics.pinball_mean | 0.0017 |
| metrics.coverage_p10_p90 | 0.82131 |
| metrics.interval_width_pu | 0.01806 |
| metrics.pr_auc_exceed | 0.95102 |
| metrics.roc_auc_exceed | 0.99525 |
| metrics.brier | 0.01503 |
| metrics.ece_exceed | 0.00317 |
| metrics.recall_exceed | 0.86513 |
| metrics.precision_exceed | 0.86893 |
| metrics.exceed_rate | 0.08117 |
| metrics.sunny_mae_vmax_pu | 0.00574 |
| metrics.sunny_pr_auc_exceed | 0.95218 |
| metrics.sunny_recall_exceed | 0.86729 |
| metrics.surrogate_seconds_300_posts_day | 0.0476 |
| metrics.surrogate_seconds_300_posts_hourly_series | 0.5601 |
| metrics.powerflow_seconds_300_posts_day_pandapower | 66.5554 |
| baseline_metrics.mae_vmax_pu | 0.02275 |
| baseline_metrics.rmse_vmax_pu | 0.02768 |
| baseline_metrics.pinball_mean | 0.00691 |
| baseline_metrics.coverage_p10_p90 | 0.78752 |
| baseline_metrics.interval_width_pu | 0.06914 |
| baseline_metrics.pr_auc_exceed | 0.42749 |
| baseline_metrics.roc_auc_exceed | 0.88311 |
| baseline_metrics.brier | 0.05836 |
| baseline_metrics.ece_exceed | 0.01334 |
| baseline_metrics.recall_exceed | 0.2564 |
| baseline_metrics.precision_exceed | 0.60464 |
| baseline_metrics.exceed_rate | 0.08117 |
| baseline_metrics.sunny_mae_vmax_pu | 0.02342 |
| baseline_metrics.sunny_pr_auc_exceed | 0.43566 |
| baseline_metrics.sunny_recall_exceed | 0.26007 |
| synthetic_share | 1 |

</details>

<details><summary>reports/C/metrics_detail.json</summary>

[Sursa](../../reports/C/metrics_detail.json) · SHA256 `619e0d20bd401034cf7c4fbf2f9895d14d5aa807605261770cf4a6bc077534f2`

| Câmp | Valoare |
|---|---:|
| test_rows | 324000 |
| model.mae_vmax_pu | 0.00542571 |
| model.rmse_vmax_pu | 0.00699671 |
| model.pinball_mean | 0.00170026 |
| model.coverage_p10_p90 | 0.821315 |
| model.interval_width_pu | 0.0180613 |
| model.brier | 0.0150345 |
| model.recall_exceed | 0.865128 |
| model.precision_exceed | 0.868928 |
| model.exceed_rate | 0.0811698 |
| model.pr_auc_exceed | 0.951016 |
| model.roc_auc_exceed | 0.995255 |
| model.ece_exceed | 0.00316604 |
| model_uncalibrated.mae_vmax_pu | 0.00542571 |
| model_uncalibrated.rmse_vmax_pu | 0.00699671 |
| model_uncalibrated.pinball_mean | 0.00195945 |
| model_uncalibrated.coverage_p10_p90 | 0.428136 |
| model_uncalibrated.interval_width_pu | 0.00747812 |
| model_uncalibrated.brier | 0.0164548 |
| model_uncalibrated.recall_exceed | 0.827978 |
| model_uncalibrated.precision_exceed | 0.905782 |
| model_uncalibrated.exceed_rate | 0.0811698 |
| model_uncalibrated.pr_auc_exceed | 0.955341 |
| model_uncalibrated.roc_auc_exceed | 0.995642 |
| model_uncalibrated.ece_exceed | 0.0122627 |
| baseline.mae_vmax_pu | 0.0227457 |
| baseline.rmse_vmax_pu | 0.0276779 |
| baseline.pinball_mean | 0.00690604 |
| baseline.coverage_p10_p90 | 0.787522 |
| baseline.interval_width_pu | 0.0691414 |
| baseline.brier | 0.0583641 |
| baseline.recall_exceed | 0.256398 |
| baseline.precision_exceed | 0.604645 |
| baseline.exceed_rate | 0.0811698 |
| baseline.pr_auc_exceed | 0.427486 |
| baseline.roc_auc_exceed | 0.883108 |
| baseline.ece_exceed | 0.0133418 |
| model_sunny_days.mae_vmax_pu | 0.00574284 |
| model_sunny_days.rmse_vmax_pu | 0.0073607 |
| model_sunny_days.pinball_mean | 0.00178628 |
| model_sunny_days.coverage_p10_p90 | 0.801264 |
| model_sunny_days.interval_width_pu | 0.0181593 |
| model_sunny_days.brier | 0.019908 |
| model_sunny_days.recall_exceed | 0.867286 |
| model_sunny_days.precision_exceed | 0.869701 |
| model_sunny_days.exceed_rate | 0.108905 |
| model_sunny_days.pr_auc_exceed | 0.952182 |
| model_sunny_days.roc_auc_exceed | 0.993647 |
| model_sunny_days.ece_exceed | 0.00401241 |
| baseline_sunny_days.mae_vmax_pu | 0.0234159 |
| baseline_sunny_days.rmse_vmax_pu | 0.0287131 |
| baseline_sunny_days.pinball_mean | 0.00716106 |
| baseline_sunny_days.coverage_p10_p90 | 0.77831 |
| baseline_sunny_days.interval_width_pu | 0.0691414 |
| baseline_sunny_days.brier | 0.0776798 |
| baseline_sunny_days.recall_exceed | 0.260066 |
| baseline_sunny_days.precision_exceed | 0.605242 |
| baseline_sunny_days.exceed_rate | 0.108905 |
| baseline_sunny_days.pr_auc_exceed | 0.435657 |
| baseline_sunny_days.roc_auc_exceed | 0.853344 |
| baseline_sunny_days.ece_exceed | 0.025358 |
| by_topology.rural1.model.mae_vmax_pu | 0.00439009 |
| by_topology.rural1.model.rmse_vmax_pu | 0.00554237 |
| by_topology.rural1.model.pinball_mean | 0.00138492 |
| by_topology.rural1.model.coverage_p10_p90 | 0.823259 |
| by_topology.rural1.model.interval_width_pu | 0.0147335 |
| by_topology.rural1.model.brier | 4.97594e-05 |
| by_topology.rural1.model.recall_exceed | 0 |
| by_topology.rural1.model.precision_exceed | 0 |
| by_topology.rural1.model.exceed_rate | 0 |
| by_topology.rural1.model.ece_exceed | 0.00037568 |
| by_topology.rural1.baseline.mae_vmax_pu | 0.0200184 |
| by_topology.rural1.baseline.rmse_vmax_pu | 0.0231366 |
| by_topology.rural1.baseline.pinball_mean | 0.00583164 |
| by_topology.rural1.baseline.coverage_p10_p90 | 0.889574 |
| by_topology.rural1.baseline.interval_width_pu | 0.0716844 |
| by_topology.rural1.baseline.brier | 0.000518379 |
| by_topology.rural1.baseline.recall_exceed | 0 |
| by_topology.rural1.baseline.precision_exceed | 0 |
| by_topology.rural1.baseline.exceed_rate | 0 |
| by_topology.rural1.baseline.ece_exceed | 0.0204687 |
| by_topology.rural1.rows | 54000 |
| by_topology.rural2.model.mae_vmax_pu | 0.006108 |
| by_topology.rural2.model.rmse_vmax_pu | 0.00785308 |
| by_topology.rural2.model.pinball_mean | 0.00190688 |
| by_topology.rural2.model.coverage_p10_p90 | 0.871389 |
| by_topology.rural2.model.interval_width_pu | 0.0225668 |
| by_topology.rural2.model.brier | 0.0334365 |
| by_topology.rural2.model.recall_exceed | 0.932109 |
| by_topology.rural2.model.precision_exceed | 0.897952 |
| by_topology.rural2.model.exceed_rate | 0.269222 |
| by_topology.rural2.model.pr_auc_exceed | 0.978007 |
| by_topology.rural2.model.roc_auc_exceed | 0.99224 |
| by_topology.rural2.model.ece_exceed | 0.017679 |
| by_topology.rural2.baseline.mae_vmax_pu | 0.026944 |
| by_topology.rural2.baseline.rmse_vmax_pu | 0.0333089 |
| by_topology.rural2.baseline.pinball_mean | 0.00837994 |
| by_topology.rural2.baseline.coverage_p10_p90 | 0.667852 |
| by_topology.rural2.baseline.interval_width_pu | 0.0663411 |
| by_topology.rural2.baseline.brier | 0.177657 |
| by_topology.rural2.baseline.recall_exceed | 0.229192 |
| by_topology.rural2.baseline.precision_exceed | 0.630941 |
| by_topology.rural2.baseline.exceed_rate | 0.269222 |
| by_topology.rural2.baseline.pr_auc_exceed | 0.593369 |
| by_topology.rural2.baseline.roc_auc_exceed | 0.83358 |
| by_topology.rural2.baseline.ece_exceed | 0.138426 |
| by_topology.rural2.rows | 54000 |
| by_topology.rural3.model.mae_vmax_pu | 0.00643305 |
| by_topology.rural3.model.rmse_vmax_pu | 0.00831898 |
| by_topology.rural3.model.pinball_mean | 0.00203024 |
| by_topology.rural3.model.coverage_p10_p90 | 0.800963 |
| by_topology.rural3.model.interval_width_pu | 0.0206577 |
| by_topology.rural3.model.brier | 0.0336262 |
| by_topology.rural3.model.recall_exceed | 0.812443 |
| by_topology.rural3.model.precision_exceed | 0.896182 |
| by_topology.rural3.model.exceed_rate | 0.163704 |
| by_topology.rural3.model.pr_auc_exceed | 0.938966 |
| by_topology.rural3.model.roc_auc_exceed | 0.988288 |
| by_topology.rural3.model.ece_exceed | 0.0164495 |
| by_topology.rural3.baseline.mae_vmax_pu | 0.0254231 |
| by_topology.rural3.baseline.rmse_vmax_pu | 0.0310449 |
| by_topology.rural3.baseline.pinball_mean | 0.00776488 |
| by_topology.rural3.baseline.coverage_p10_p90 | 0.72363 |
| by_topology.rural3.baseline.interval_width_pu | 0.0676962 |
| by_topology.rural3.baseline.brier | 0.113529 |
| by_topology.rural3.baseline.recall_exceed | 0.38586 |
| by_topology.rural3.baseline.precision_exceed | 0.592599 |
| by_topology.rural3.baseline.exceed_rate | 0.163704 |
| by_topology.rural3.baseline.pr_auc_exceed | 0.457425 |
| by_topology.rural3.baseline.roc_auc_exceed | 0.84456 |
| by_topology.rural3.baseline.ece_exceed | 0.0636644 |
| by_topology.rural3.rows | 54000 |
| by_topology.semiurb4.model.mae_vmax_pu | 0.00465115 |
| by_topology.semiurb4.model.rmse_vmax_pu | 0.00596833 |
| by_topology.semiurb4.model.pinball_mean | 0.00146402 |
| by_topology.semiurb4.model.coverage_p10_p90 | 0.865685 |
| by_topology.semiurb4.model.interval_width_pu | 0.0168593 |
| by_topology.semiurb4.model.brier | 0.00745789 |
| by_topology.semiurb4.model.recall_exceed | 0.309959 |
| by_topology.semiurb4.model.precision_exceed | 0.977564 |
| by_topology.semiurb4.model.exceed_rate | 0.0182222 |
| by_topology.semiurb4.model.pr_auc_exceed | 0.852085 |
| by_topology.semiurb4.model.roc_auc_exceed | 0.997446 |
| by_topology.semiurb4.model.ece_exceed | 0.00760922 |
| by_topology.semiurb4.baseline.mae_vmax_pu | 0.0215864 |
| by_topology.semiurb4.baseline.rmse_vmax_pu | 0.0255177 |
| by_topology.semiurb4.baseline.pinball_mean | 0.00635151 |
| by_topology.semiurb4.baseline.coverage_p10_p90 | 0.840778 |
| by_topology.semiurb4.baseline.interval_width_pu | 0.0697559 |
| by_topology.semiurb4.baseline.brier | 0.0175911 |
| by_topology.semiurb4.baseline.recall_exceed | 0 |
| by_topology.semiurb4.baseline.precision_exceed | 0 |
| by_topology.semiurb4.baseline.exceed_rate | 0.0182222 |
| by_topology.semiurb4.baseline.pr_auc_exceed | 0.210645 |
| by_topology.semiurb4.baseline.roc_auc_exceed | 0.76357 |
| by_topology.semiurb4.baseline.ece_exceed | 0.01542 |
| by_topology.semiurb4.rows | 54000 |
| by_topology.semiurb5.model.mae_vmax_pu | 0.00612603 |
| by_topology.semiurb5.model.rmse_vmax_pu | 0.00761213 |
| by_topology.semiurb5.model.pinball_mean | 0.00190988 |
| by_topology.semiurb5.model.coverage_p10_p90 | 0.757759 |
| by_topology.semiurb5.model.interval_width_pu | 0.0180449 |
| by_topology.semiurb5.model.brier | 0.0153031 |
| by_topology.semiurb5.model.recall_exceed | 0.884874 |
| by_topology.semiurb5.model.precision_exceed | 0.619443 |
| by_topology.semiurb5.model.exceed_rate | 0.0358704 |
| by_topology.semiurb5.model.pr_auc_exceed | 0.881132 |
| by_topology.semiurb5.model.roc_auc_exceed | 0.992939 |
| by_topology.semiurb5.model.ece_exceed | 0.0169608 |
| by_topology.semiurb5.baseline.mae_vmax_pu | 0.0213654 |
| by_topology.semiurb5.baseline.rmse_vmax_pu | 0.025688 |
| by_topology.semiurb5.baseline.pinball_mean | 0.00642303 |
| by_topology.semiurb5.baseline.coverage_p10_p90 | 0.813463 |
| by_topology.semiurb5.baseline.interval_width_pu | 0.0696034 |
| by_topology.semiurb5.baseline.brier | 0.0338698 |
| by_topology.semiurb5.baseline.recall_exceed | 0 |
| by_topology.semiurb5.baseline.precision_exceed | 0 |
| by_topology.semiurb5.baseline.exceed_rate | 0.0358704 |
| by_topology.semiurb5.baseline.pr_auc_exceed | 0.114778 |
| by_topology.semiurb5.baseline.roc_auc_exceed | 0.851043 |
| by_topology.semiurb5.baseline.ece_exceed | 0.0237566 |
| by_topology.semiurb5.rows | 54000 |
| by_topology.urban6.model.mae_vmax_pu | 0.00484592 |
| by_topology.urban6.model.rmse_vmax_pu | 0.00620999 |
| by_topology.urban6.model.pinball_mean | 0.00150563 |
| by_topology.urban6.model.coverage_p10_p90 | 0.808833 |
| by_topology.urban6.model.interval_width_pu | 0.0155059 |
| by_topology.urban6.model.brier | 0.000333778 |
| by_topology.urban6.model.recall_exceed | 0 |
| by_topology.urban6.model.precision_exceed | 0 |
| by_topology.urban6.model.exceed_rate | 0 |
| by_topology.urban6.model.ece_exceed | 0.00256587 |
| by_topology.urban6.baseline.mae_vmax_pu | 0.0211369 |
| by_topology.urban6.baseline.rmse_vmax_pu | 0.0260152 |
| by_topology.urban6.baseline.pinball_mean | 0.00668522 |
| by_topology.urban6.baseline.coverage_p10_p90 | 0.789833 |
| by_topology.urban6.baseline.interval_width_pu | 0.0697676 |
| by_topology.urban6.baseline.brier | 0.00701957 |
| by_topology.urban6.baseline.recall_exceed | 0 |
| by_topology.urban6.baseline.precision_exceed | 0 |
| by_topology.urban6.baseline.exceed_rate | 0 |
| by_topology.urban6.baseline.ece_exceed | 0.0579764 |
| by_topology.urban6.rows | 54000 |
| seconds | 336.5 |
| hourly.test_hours | 572245 |
| hourly.mae_vmax_pu | 0.00493682 |
| hourly.mae_vmax_daylight_pu | 0.00519357 |
| hourly.coverage_p10_p90_raw | 0.4976 |
| hourly.coverage_p10_p90 | 0.804238 |
| hourly.coverage_p10_p90_daylight | 0.789945 |
| hourly.cqr_margin_mean_pu | 0.00385631 |
| speed.surrogate_seconds_300_posts_day | 0.0475952 |
| speed.surrogate_seconds_300_posts_hourly_series | 0.560071 |
| speed.powerflow_seconds_300_posts_day_pandapower | 66.5554 |

</details>

<details><summary>reports/C/powerflow_bench.json</summary>

[Sursa](../../reports/C/powerflow_bench.json) · SHA256 `3035f804dfc897d6f9a1a9fd2fd7675d405318c4661b62a53e35d66b59eaabb0`

| Câmp | Valoare |
|---|---:|
| topologies.rural1.lv_buses | 14 |
| topologies.rural1.pv_kw | 0 |
| topologies.rural1.snapshots | 100 |
| topologies.rural1.max_abs_diff_pu | 5.28436e-10 |
| topologies.rural1.pandapower_ms_per_snapshot_median | 8.09048 |
| topologies.rural1.vectorized_ms_per_snapshot | 0.00121958 |
| topologies.rural1.iterations | 4 |
| topologies.rural1.vmax_range_pu | [1.0195177787605305, 1.0596045205924398] |
| topologies.rural1.year_hours | 8760 |
| topologies.rural1.vectorized_s_per_year | 0.0023 |
| topologies.rural1.pandapower_s_per_year_est | 70.9 |
| topologies.rural1.iterations_year | 4 |
| topologies.rural2.lv_buses | 96 |
| topologies.rural2.pv_kw | 213 |
| topologies.rural2.snapshots | 100 |
| topologies.rural2.max_abs_diff_pu | 5.15876e-08 |
| topologies.rural2.pandapower_ms_per_snapshot_median | 8.8091 |
| topologies.rural2.vectorized_ms_per_snapshot | 0.00490708 |
| topologies.rural2.iterations | 7 |
| topologies.rural2.vmax_range_pu | [1.0110165609142996, 1.0829105382825213] |
| topologies.rural2.year_hours | 8760 |
| topologies.rural2.vectorized_s_per_year | 0.0568 |
| topologies.rural2.pandapower_s_per_year_est | 77.2 |
| topologies.rural2.iterations_year | 8 |
| topologies.rural3.lv_buses | 128 |
| topologies.rural3.pv_kw | 0 |
| topologies.rural3.snapshots | 100 |
| topologies.rural3.max_abs_diff_pu | 1.07808e-08 |
| topologies.rural3.pandapower_ms_per_snapshot_median | 8.15238 |
| topologies.rural3.vectorized_ms_per_snapshot | 0.00527708 |
| topologies.rural3.iterations | 5 |
| topologies.rural3.vmax_range_pu | [1.0113266600239648, 1.050652212666799] |
| topologies.rural3.year_hours | 8760 |
| topologies.rural3.vectorized_s_per_year | 0.0473 |
| topologies.rural3.pandapower_s_per_year_est | 71.4 |
| topologies.rural3.iterations_year | 5 |
| topologies.semiurb4.lv_buses | 43 |
| topologies.semiurb4.pv_kw | 176 |
| topologies.semiurb4.snapshots | 100 |
| topologies.semiurb4.max_abs_diff_pu | 1.68593e-08 |
| topologies.semiurb4.pandapower_ms_per_snapshot_median | 10.8201 |
| topologies.semiurb4.vectorized_ms_per_snapshot | 0.00203375 |
| topologies.semiurb4.iterations | 6 |
| topologies.semiurb4.vmax_range_pu | [1.0178969903551465, 1.0646831880873047] |
| topologies.semiurb4.year_hours | 8760 |
| topologies.semiurb4.vectorized_s_per_year | 0.0172 |
| topologies.semiurb4.pandapower_s_per_year_est | 94.8 |
| topologies.semiurb4.iterations_year | 7 |
| topologies.semiurb5.lv_buses | 110 |
| topologies.semiurb5.pv_kw | 226 |
| topologies.semiurb5.snapshots | 100 |
| topologies.semiurb5.max_abs_diff_pu | 4.21011e-10 |
| topologies.semiurb5.pandapower_ms_per_snapshot_median | 9.10002 |
| topologies.semiurb5.vectorized_ms_per_snapshot | 0.00638167 |
| topologies.semiurb5.iterations | 8 |
| topologies.semiurb5.vmax_range_pu | [1.0143775713217897, 1.0844978728037526] |
| topologies.semiurb5.year_hours | 8760 |
| topologies.semiurb5.vectorized_s_per_year | 0.061 |
| topologies.semiurb5.pandapower_s_per_year_est | 79.7 |
| topologies.semiurb5.iterations_year | 8 |
| topologies.urban6.lv_buses | 58 |
| topologies.urban6.pv_kw | 137 |
| topologies.urban6.snapshots | 100 |
| topologies.urban6.max_abs_diff_pu | 6.92189e-09 |
| topologies.urban6.pandapower_ms_per_snapshot_median | 8.12627 |
| topologies.urban6.vectorized_ms_per_snapshot | 0.00263042 |
| topologies.urban6.iterations | 5 |
| topologies.urban6.vmax_range_pu | [1.0027394068845459, 1.0479541520326396] |
| topologies.urban6.year_hours | 8760 |
| topologies.urban6.vectorized_s_per_year | 0.017 |
| topologies.urban6.pandapower_s_per_year_est | 71.2 |
| topologies.urban6.iterations_year | 6 |

</details>

<details><summary>reports/C/tuning_optuna_mai_multe_regiuni.json</summary>

[Sursa](../../reports/C/tuning_optuna_mai_multe_regiuni.json) · SHA256 `d36f4218c114be7022b36477ef4d1473288517c2f62b41f588908480d5e86421`

| Câmp | Valoare |
|---|---:|
| train_rows | 4.55952e+06 |
| val_mae_pu.livrat | 0.005322 |
| val_mae_pu.gasit | 0.005205 |
| test_2025.livrat.bucuresti_2025.mae_vmax_pu | 0.00533 |
| test_2025.livrat.bucuresti_2025.coverage_p10_p90 | 0.82549 |
| test_2025.livrat.bucuresti_2025.brier | 0.01488 |
| test_2025.livrat.bucuresti_2025.recall_exceed | 0.8645 |
| test_2025.livrat.bucuresti_2025.precision_exceed | 0.87189 |
| test_2025.livrat.bucuresti_2025.exceed_rate | 0.0812 |
| test_2025.livrat.bucuresti_2025.pr_auc_exceed | 0.95044 |
| test_2025.livrat.bucuresti_2025.test_rows | 324000 |
| test_2025.livrat.timisoara_2025.mae_vmax_pu | 0.00534 |
| test_2025.livrat.timisoara_2025.coverage_p10_p90 | 0.82533 |
| test_2025.livrat.timisoara_2025.brier | 0.01526 |
| test_2025.livrat.timisoara_2025.recall_exceed | 0.86523 |
| test_2025.livrat.timisoara_2025.precision_exceed | 0.87038 |
| test_2025.livrat.timisoara_2025.exceed_rate | 0.0829 |
| test_2025.livrat.timisoara_2025.pr_auc_exceed | 0.94995 |
| test_2025.livrat.timisoara_2025.test_rows | 324000 |
| test_2025.livrat.cluj_2025.mae_vmax_pu | 0.00533 |
| test_2025.livrat.cluj_2025.coverage_p10_p90 | 0.82665 |
| test_2025.livrat.cluj_2025.brier | 0.01449 |
| test_2025.livrat.cluj_2025.recall_exceed | 0.86862 |
| test_2025.livrat.cluj_2025.precision_exceed | 0.87065 |
| test_2025.livrat.cluj_2025.exceed_rate | 0.07931 |
| test_2025.livrat.cluj_2025.pr_auc_exceed | 0.95025 |
| test_2025.livrat.cluj_2025.test_rows | 324000 |
| test_2025.livrat.iasi_2025.mae_vmax_pu | 0.00528 |
| test_2025.livrat.iasi_2025.coverage_p10_p90 | 0.82987 |
| test_2025.livrat.iasi_2025.brier | 0.0139 |
| test_2025.livrat.iasi_2025.recall_exceed | 0.87123 |
| test_2025.livrat.iasi_2025.precision_exceed | 0.87298 |
| test_2025.livrat.iasi_2025.exceed_rate | 0.07677 |
| test_2025.livrat.iasi_2025.pr_auc_exceed | 0.95081 |
| test_2025.livrat.iasi_2025.test_rows | 324000 |
| test_2025.livrat.constanta_2025.mae_vmax_pu | 0.00538 |
| test_2025.livrat.constanta_2025.coverage_p10_p90 | 0.82101 |
| test_2025.livrat.constanta_2025.brier | 0.01516 |
| test_2025.livrat.constanta_2025.recall_exceed | 0.8743 |
| test_2025.livrat.constanta_2025.precision_exceed | 0.87373 |
| test_2025.livrat.constanta_2025.exceed_rate | 0.08577 |
| test_2025.livrat.constanta_2025.pr_auc_exceed | 0.95366 |
| test_2025.livrat.constanta_2025.test_rows | 324000 |
| test_2025.gasit.bucuresti_2025.mae_vmax_pu | 0.00527 |
| test_2025.gasit.bucuresti_2025.coverage_p10_p90 | 0.81776 |
| test_2025.gasit.bucuresti_2025.brier | 0.01463 |
| test_2025.gasit.bucuresti_2025.recall_exceed | 0.86164 |
| test_2025.gasit.bucuresti_2025.precision_exceed | 0.87596 |
| test_2025.gasit.bucuresti_2025.exceed_rate | 0.0812 |
| test_2025.gasit.bucuresti_2025.pr_auc_exceed | 0.95163 |
| test_2025.gasit.bucuresti_2025.test_rows | 324000 |
| test_2025.gasit.timisoara_2025.mae_vmax_pu | 0.00528 |
| test_2025.gasit.timisoara_2025.coverage_p10_p90 | 0.81573 |
| test_2025.gasit.timisoara_2025.brier | 0.01501 |
| test_2025.gasit.timisoara_2025.recall_exceed | 0.86039 |
| test_2025.gasit.timisoara_2025.precision_exceed | 0.8736 |
| test_2025.gasit.timisoara_2025.exceed_rate | 0.0829 |
| test_2025.gasit.timisoara_2025.pr_auc_exceed | 0.95084 |
| test_2025.gasit.timisoara_2025.test_rows | 324000 |
| test_2025.gasit.cluj_2025.mae_vmax_pu | 0.00528 |
| test_2025.gasit.cluj_2025.coverage_p10_p90 | 0.81727 |
| test_2025.gasit.cluj_2025.brier | 0.01414 |
| test_2025.gasit.cluj_2025.recall_exceed | 0.86422 |
| test_2025.gasit.cluj_2025.precision_exceed | 0.87608 |
| test_2025.gasit.cluj_2025.exceed_rate | 0.07931 |
| test_2025.gasit.cluj_2025.pr_auc_exceed | 0.95215 |
| test_2025.gasit.cluj_2025.test_rows | 324000 |
| test_2025.gasit.iasi_2025.mae_vmax_pu | 0.00524 |
| test_2025.gasit.iasi_2025.coverage_p10_p90 | 0.82082 |
| test_2025.gasit.iasi_2025.brier | 0.01363 |
| test_2025.gasit.iasi_2025.recall_exceed | 0.86688 |
| test_2025.gasit.iasi_2025.precision_exceed | 0.87622 |
| test_2025.gasit.iasi_2025.exceed_rate | 0.07677 |
| test_2025.gasit.iasi_2025.pr_auc_exceed | 0.95239 |
| test_2025.gasit.iasi_2025.test_rows | 324000 |
| test_2025.gasit.constanta_2025.mae_vmax_pu | 0.00533 |
| test_2025.gasit.constanta_2025.coverage_p10_p90 | 0.81459 |
| test_2025.gasit.constanta_2025.brier | 0.01491 |
| test_2025.gasit.constanta_2025.recall_exceed | 0.87045 |
| test_2025.gasit.constanta_2025.precision_exceed | 0.87803 |
| test_2025.gasit.constanta_2025.exceed_rate | 0.08577 |
| test_2025.gasit.constanta_2025.pr_auc_exceed | 0.95476 |
| test_2025.gasit.constanta_2025.test_rows | 324000 |

</details>

<details><summary>reports/bilant/comparatie_v2_feederbw.json</summary>

[Sursa](../../reports/bilant/comparatie_v2_feederbw.json) · SHA256 `e79c5c7dce7e6c7118ace2884a6541f2e68cffe1de93654ed4008798b42287ae`

| Câmp | Valoare |
|---|---:|
| v2.diagnosis.macro_f1 | 0.753521 |
| v2.diagnosis.accuracy | 0.855379 |
| v2.diagnosis.f1_by_class.normal | 0.927017 |
| v2.diagnosis.f1_by_class.contor_client | 0.472106 |
| v2.diagnosis.f1_by_class.furt_inainte_contor | 0.770957 |
| v2.diagnosis.f1_by_class.pierdere_tehnica | 0.488242 |
| v2.diagnosis.f1_by_class.client_post_gresit | 0.87132 |
| v2.diagnosis.f1_by_class.contor_bilant_setat | 0.991482 |
| v2.normal.mae_kwh_day | 5.39814 |
| v2.normal.mape_pct | 14.5983 |
| v2.normal.bias_kwh_day | 1.1922 |
| v2.normal.coverage_p10_p90 | 0.880914 |
| v2.normal.interval_width_kwh_day | 17.944 |
| v2.normal.pinball_mean | 1.85699 |
| feederbw.diagnosis.macro_f1 | 0.589503 |
| feederbw.diagnosis.accuracy | 0.7125 |
| feederbw.diagnosis.f1_by_class.normal | 0.832171 |
| feederbw.diagnosis.f1_by_class.contor_client | 0.319782 |
| feederbw.diagnosis.f1_by_class.furt_inainte_contor | 0.432279 |
| feederbw.diagnosis.f1_by_class.pierdere_tehnica | 0.27027 |
| feederbw.diagnosis.f1_by_class.client_post_gresit | 0.743811 |
| feederbw.diagnosis.f1_by_class.contor_bilant_setat | 0.938704 |
| feederbw.normal.mae_kwh_day | 8.81308 |
| feederbw.normal.mape_pct | 23.8334 |
| feederbw.normal.bias_kwh_day | -1.12049 |
| feederbw.normal.coverage_p10_p90 | 0.694635 |
| feederbw.normal.interval_width_kwh_day | 16.9189 |
| feederbw.normal.pinball_mean | 2.63874 |

</details>

<details><summary>reports/bilant/feederbw_optuna.json</summary>

[Sursa](../../reports/bilant/feederbw_optuna.json) · SHA256 `b56a32b5c9e3e64b46231947fd1cf76fbb682dec6d66a70aea0d145792babe80`

| Câmp | Valoare |
|---|---:|
| posts.train | 170 |
| posts.validation | 65 |
| posts.test | 65 |
| windows.train | 7310 |
| windows.validation | 2795 |
| windows.test | 2795 |
| class_counts.train.normal | 3804 |
| class_counts.train.contor_client | 1606 |
| class_counts.train.furt_inainte_contor | 564 |
| class_counts.train.pierdere_tehnica | 512 |
| class_counts.train.client_post_gresit | 640 |
| class_counts.train.contor_bilant_setat | 184 |
| class_counts.validation.normal | 1367 |
| class_counts.validation.contor_client | 721 |
| class_counts.validation.furt_inainte_contor | 145 |
| class_counts.validation.pierdere_tehnica | 224 |
| class_counts.validation.client_post_gresit | 154 |
| class_counts.validation.contor_bilant_setat | 184 |
| class_counts.test.normal | 1357 |
| class_counts.test.contor_client | 715 |
| class_counts.test.furt_inainte_contor | 237 |
| class_counts.test.pierdere_tehnica | 148 |
| class_counts.test.client_post_gresit | 268 |
| class_counts.test.contor_bilant_setat | 70 |
| seed | 2.02611e+07 |
| validation.baseline_macro_f1 | 0.625362 |
| validation.optuna_macro_f1 | 0.640498 |
| test.baseline.macro_f1 | 0.708584 |
| test.baseline.accuracy | 0.747048 |
| test.baseline.f1_by_class.normal | 0.853117 |
| test.baseline.f1_by_class.contor_client | 0.61035 |
| test.baseline.f1_by_class.furt_inainte_contor | 0.454106 |
| test.baseline.f1_by_class.pierdere_tehnica | 0.543131 |
| test.baseline.f1_by_class.client_post_gresit | 0.797891 |
| test.baseline.f1_by_class.contor_bilant_setat | 0.992908 |
| test.optuna.macro_f1 | 0.713931 |
| test.optuna.accuracy | 0.749195 |
| test.optuna.f1_by_class.normal | 0.855404 |
| test.optuna.f1_by_class.contor_client | 0.608302 |
| test.optuna.f1_by_class.furt_inainte_contor | 0.468599 |
| test.optuna.f1_by_class.pierdere_tehnica | 0.548287 |
| test.optuna.f1_by_class.client_post_gresit | 0.810084 |
| test.optuna.f1_by_class.contor_bilant_setat | 0.992908 |
| test.delta_macro_f1 | 0.00534672 |
| test.delta_macro_f1_bootstrap90_by_real_feeder | [-0.006177916164162922, 0.01768754638659322] |
| seconds | 390.3 |

</details>

<details><summary>reports/bilant/feederbw_release_pop.json</summary>

[Sursa](../../reports/bilant/feederbw_release_pop.json) · SHA256 `e7f5bf4f641f8a5e11fa4d5f3d43eb38a6be67debc52273888289f217d64b745`

| Câmp | Valoare |
|---|---:|
| test_windows | 13200 |
| diagnosis.macro_f1 | 0.589503 |
| diagnosis.accuracy | 0.7125 |
| diagnosis.f1_by_class.normal | 0.832171 |
| diagnosis.f1_by_class.contor_client | 0.319782 |
| diagnosis.f1_by_class.furt_inainte_contor | 0.432279 |
| diagnosis.f1_by_class.pierdere_tehnica | 0.27027 |
| diagnosis.f1_by_class.client_post_gresit | 0.743811 |
| diagnosis.f1_by_class.contor_bilant_setat | 0.938704 |
| normal.mae_kwh_day | 8.81308 |
| normal.mape_pct | 23.8334 |
| normal.bias_kwh_day | -1.12049 |
| normal.coverage_p10_p90 | 0.694635 |
| normal.interval_width_kwh_day | 16.9189 |
| normal.pinball_mean | 2.63874 |

</details>

<details><summary>reports/bilant/fusion_v2_comparison_trainL.json</summary>

[Sursa](../../reports/bilant/fusion_v2_comparison_trainL.json) · SHA256 `60cf27c22337c011ce513d4f014a1f5678f472e73ddab678e6fff7d0943c6f74`

| Câmp | Valoare |
|---|---:|
| validation_objective.A_singur | 0.153095 |
| validation_objective.regula_v1 | 0.17119 |
| validation_objective.regula_reglata | 0.210952 |
| validation_objective.invatata | 0.367143 |
| test_sim_multi_day.A_singur.precision_at_10 | 0.8 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_10 | 2 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_10 | 4966.48 |
| test_sim_multi_day.A_singur.precision_at_20 | 0.64375 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_20 | 7.125 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_20 | 7917.45 |
| test_sim_multi_day.A_singur.precision_at_50 | 0.4425 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_50 | 27.875 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_50 | 11716.2 |
| test_sim_multi_day.A_singur.precision_at_100 | 0.31375 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_100 | 68.625 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_100 | 13817.9 |
| test_sim_multi_day.A_singur.roc_auc | 0.905538 |
| test_sim_multi_day.regula_v1.precision_at_10 | 0.775 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_10 | 2.25 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_10 | 6986.36 |
| test_sim_multi_day.regula_v1.precision_at_20 | 0.61875 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_20 | 7.625 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_20 | 9590.32 |
| test_sim_multi_day.regula_v1.precision_at_50 | 0.405 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_50 | 29.75 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_50 | 12395.3 |
| test_sim_multi_day.regula_v1.precision_at_100 | 0.2875 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_100 | 71.25 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_100 | 15584.7 |
| test_sim_multi_day.regula_v1.roc_auc | 0.901273 |
| test_sim_multi_day.regula_reglata.precision_at_10 | 0.7625 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_10 | 2.375 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_10 | 7502.1 |
| test_sim_multi_day.regula_reglata.precision_at_20 | 0.65 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_20 | 7 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_20 | 10300 |
| test_sim_multi_day.regula_reglata.precision_at_50 | 0.4 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_50 | 30 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_50 | 12477.5 |
| test_sim_multi_day.regula_reglata.precision_at_100 | 0.275 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_100 | 72.5 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_100 | 14875.8 |
| test_sim_multi_day.regula_reglata.roc_auc | 0.864814 |
| test_sim_multi_day.invatata.precision_at_10 | 0.7875 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_10 | 2.125 |
| test_sim_multi_day.invatata.value_lei_per_day_at_10 | 6688.71 |
| test_sim_multi_day.invatata.precision_at_20 | 0.7 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_20 | 6 |
| test_sim_multi_day.invatata.value_lei_per_day_at_20 | 10689 |
| test_sim_multi_day.invatata.precision_at_50 | 0.47 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_50 | 26.5 |
| test_sim_multi_day.invatata.value_lei_per_day_at_50 | 16231.9 |
| test_sim_multi_day.invatata.precision_at_100 | 0.31875 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_100 | 68.125 |
| test_sim_multi_day.invatata.value_lei_per_day_at_100 | 18901.5 |
| test_sim_multi_day.invatata.roc_auc | 0.759289 |
| test_real_a_demo.A_singur.roc_auc | 0.916682 |
| test_real_a_demo.A_singur.precision_at_10 | 1 |
| test_real_a_demo.A_singur.precision_at_100 | 1 |
| test_real_a_demo.A_singur.precision_at_300 | 1 |
| test_real_a_demo.A_singur.precision_at_500 | 0.962 |
| test_real_a_demo.A_singur.precision_at_865 | 0.649711 |
| test_real_a_demo.regula_v1.roc_auc | 0.916199 |
| test_real_a_demo.regula_v1.precision_at_10 | 1 |
| test_real_a_demo.regula_v1.precision_at_100 | 1 |
| test_real_a_demo.regula_v1.precision_at_300 | 1 |
| test_real_a_demo.regula_v1.precision_at_500 | 0.874 |
| test_real_a_demo.regula_v1.precision_at_865 | 0.643931 |
| test_real_a_demo.regula_reglata.roc_auc | 0.889794 |
| test_real_a_demo.regula_reglata.precision_at_10 | 1 |
| test_real_a_demo.regula_reglata.precision_at_100 | 1 |
| test_real_a_demo.regula_reglata.precision_at_300 | 0.99 |
| test_real_a_demo.regula_reglata.precision_at_500 | 0.86 |
| test_real_a_demo.regula_reglata.precision_at_865 | 0.634682 |
| test_real_a_demo.invatata.roc_auc | 0.809441 |
| test_real_a_demo.invatata.precision_at_10 | 0.8 |
| test_real_a_demo.invatata.precision_at_100 | 0.78 |
| test_real_a_demo.invatata.precision_at_300 | 0.603333 |
| test_real_a_demo.invatata.precision_at_500 | 0.556 |
| test_real_a_demo.invatata.precision_at_865 | 0.398844 |
| a_sim_auc_train | 0.909293 |
| a_sim_auc_test | 0.905538 |
| test_days | 8 |
| seconds | 33.3 |

</details>

<details><summary>reports/bilant/fusion_v2_comparison_trainLA.json</summary>

[Sursa](../../reports/bilant/fusion_v2_comparison_trainLA.json) · SHA256 `6eb32f74518ae33de57b98789e6ca7d5d3e2e52e6042163d240a847e7ac9f42e`

| Câmp | Valoare |
|---|---:|
| validation_objective.A_singur | 0.902083 |
| validation_objective.regula_v1 | 0.865417 |
| validation_objective.regula_reglata | 0.940417 |
| validation_objective.invatata | 0.995833 |
| test_sim_multi_day.A_singur.precision_at_10 | 0.8 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_10 | 2 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_10 | 4966.48 |
| test_sim_multi_day.A_singur.precision_at_20 | 0.64375 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_20 | 7.125 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_20 | 7917.45 |
| test_sim_multi_day.A_singur.precision_at_50 | 0.4425 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_50 | 27.875 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_50 | 11716.2 |
| test_sim_multi_day.A_singur.precision_at_100 | 0.31375 |
| test_sim_multi_day.A_singur.wasted_trips_per_day_at_100 | 68.625 |
| test_sim_multi_day.A_singur.value_lei_per_day_at_100 | 13817.9 |
| test_sim_multi_day.A_singur.roc_auc | 0.905538 |
| test_sim_multi_day.regula_v1.precision_at_10 | 0.775 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_10 | 2.25 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_10 | 6986.36 |
| test_sim_multi_day.regula_v1.precision_at_20 | 0.61875 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_20 | 7.625 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_20 | 9590.32 |
| test_sim_multi_day.regula_v1.precision_at_50 | 0.405 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_50 | 29.75 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_50 | 12395.3 |
| test_sim_multi_day.regula_v1.precision_at_100 | 0.2875 |
| test_sim_multi_day.regula_v1.wasted_trips_per_day_at_100 | 71.25 |
| test_sim_multi_day.regula_v1.value_lei_per_day_at_100 | 15584.7 |
| test_sim_multi_day.regula_v1.roc_auc | 0.901273 |
| test_sim_multi_day.regula_reglata.precision_at_10 | 0.9 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_10 | 1 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_10 | 8277.79 |
| test_sim_multi_day.regula_reglata.precision_at_20 | 0.68125 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_20 | 6.375 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_20 | 10443.7 |
| test_sim_multi_day.regula_reglata.precision_at_50 | 0.4625 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_50 | 26.875 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_50 | 13594.8 |
| test_sim_multi_day.regula_reglata.precision_at_100 | 0.33375 |
| test_sim_multi_day.regula_reglata.wasted_trips_per_day_at_100 | 66.625 |
| test_sim_multi_day.regula_reglata.value_lei_per_day_at_100 | 17484.2 |
| test_sim_multi_day.regula_reglata.roc_auc | 0.9065 |
| test_sim_multi_day.invatata.precision_at_10 | 1 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_10 | 0 |
| test_sim_multi_day.invatata.value_lei_per_day_at_10 | 8336.01 |
| test_sim_multi_day.invatata.precision_at_20 | 0.95 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_20 | 1 |
| test_sim_multi_day.invatata.value_lei_per_day_at_20 | 12857.2 |
| test_sim_multi_day.invatata.precision_at_50 | 0.76 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_50 | 12 |
| test_sim_multi_day.invatata.value_lei_per_day_at_50 | 18710.3 |
| test_sim_multi_day.invatata.precision_at_100 | 0.50875 |
| test_sim_multi_day.invatata.wasted_trips_per_day_at_100 | 49.125 |
| test_sim_multi_day.invatata.value_lei_per_day_at_100 | 21824.1 |
| test_sim_multi_day.invatata.roc_auc | 0.865852 |
| test_real_a_demo.A_singur.roc_auc | 0.916682 |
| test_real_a_demo.A_singur.precision_at_10 | 1 |
| test_real_a_demo.A_singur.precision_at_100 | 1 |
| test_real_a_demo.A_singur.precision_at_300 | 1 |
| test_real_a_demo.A_singur.precision_at_500 | 0.962 |
| test_real_a_demo.A_singur.precision_at_865 | 0.649711 |
| test_real_a_demo.regula_v1.roc_auc | 0.916199 |
| test_real_a_demo.regula_v1.precision_at_10 | 1 |
| test_real_a_demo.regula_v1.precision_at_100 | 1 |
| test_real_a_demo.regula_v1.precision_at_300 | 1 |
| test_real_a_demo.regula_v1.precision_at_500 | 0.874 |
| test_real_a_demo.regula_v1.precision_at_865 | 0.643931 |
| test_real_a_demo.regula_reglata.roc_auc | 0.91939 |
| test_real_a_demo.regula_reglata.precision_at_10 | 1 |
| test_real_a_demo.regula_reglata.precision_at_100 | 1 |
| test_real_a_demo.regula_reglata.precision_at_300 | 1 |
| test_real_a_demo.regula_reglata.precision_at_500 | 0.96 |
| test_real_a_demo.regula_reglata.precision_at_865 | 0.649711 |
| test_real_a_demo.invatata.roc_auc | 0.846771 |
| test_real_a_demo.invatata.precision_at_10 | 1 |
| test_real_a_demo.invatata.precision_at_100 | 0.99 |
| test_real_a_demo.invatata.precision_at_300 | 0.883333 |
| test_real_a_demo.invatata.precision_at_500 | 0.78 |
| test_real_a_demo.invatata.precision_at_865 | 0.563006 |
| a_sim_auc_train | 0.912238 |
| a_sim_auc_test | 0.905538 |
| test_days | 8 |
| seconds | 96.9 |

</details>

<details><summary>reports/bilant/fusion_v2_params.json</summary>

[Sursa](../../reports/bilant/fusion_v2_params.json) · SHA256 `c4785002da13c0c055c3ee21788c17aa3b860c0592898d3988cf8a894549cbb9`

| Câmp | Valoare |
|---|---:|
| test_pop_sim_precision_at_10.A_singur | 0.8 |
| test_pop_sim_precision_at_10.regula_v1 | 0.775 |
| test_pop_sim_precision_at_10.regula_reglata | 0.9 |
| test_real_a_auc.A_singur | 0.916682 |
| test_real_a_auc.regula_v1 | 0.916199 |
| test_real_a_auc.regula_reglata | 0.91939 |

</details>

<details><summary>reports/bilant/metrics.json</summary>

[Sursa](../../reports/bilant/metrics.json) · SHA256 `0074f4fc47798ac3e21917edf8b4478141f8f1e4249e3d61effe53f9a2986798`

| Câmp | Valoare |
|---|---:|
| test_size | 77969 |
| metrics.normal_mae_kwh_day | 5.3981 |
| metrics.normal_mape_pct | 14.5983 |
| metrics.normal_bias_kwh_day | 1.1922 |
| metrics.normal_coverage_p10_p90 | 0.8809 |
| metrics.normal_interval_width_kwh_day | 17.944 |
| metrics.normal_pinball_mean | 1.857 |
| metrics.procent_fix_mae_kwh_day | 20.6194 |
| metrics.procent_fix_coverage_p10_p90 | 0.8228 |
| metrics.procent_fix_interval_width_kwh_day | 72.7697 |
| metrics.normal_test_days | 77969 |
| metrics.normal_test_posts | 300 |
| metrics.normal_mean_loss_kwh_day | 36.9673 |
| metrics.normal_median_loss_pct_throughput | 3.8025 |
| metrics.diagnoza_v1_macro_f1 | 0.7037 |
| metrics.diagnoza_v1_accuracy | 0.8217 |
| metrics.diagnoza_v1_abstain_rate | 0.1256 |
| metrics.diagnoza_v1_macro_f1_fara_abtineri | 0.7486 |
| metrics.diagnoza_v1_value_at_10_posts | 0.8472 |
| metrics.diagnoza_v1_f1_normal | 0.9123 |
| metrics.diagnoza_v1_f1_contor_client | 0.3841 |
| metrics.diagnoza_v1_f1_furt_inainte_contor | 0.6694 |
| metrics.diagnoza_v1_f1_pierdere_tehnica | 0.5053 |
| metrics.diagnoza_v1_f1_client_post_gresit | 0.7581 |
| metrics.diagnoza_v1_f1_contor_bilant_setat | 0.9932 |
| metrics.martor_windows | 6946 |
| metrics.martor_rule_recall_contor_post | 0.9844 |
| metrics.martor_rule_false_alarms | 0 |
| metrics.martor_model_only_f1_contor_post | 0.9922 |
| metrics.martor_with_rule_f1_contor_post | 0.9921 |
| metrics.diagnoza_v1_macro_f1_fara_martor | 0.7029 |
| metrics.martor_normal_diff_median_pct | 0.0606 |
| metrics.diagnoza_varianta_v2 | 1 |
| metrics.diagnoza_macro_f1 | 0.7535 |
| metrics.diagnoza_accuracy | 0.8554 |
| metrics.diagnoza_abstain_rate | 0.1452 |
| metrics.diagnoza_macro_f1_fara_abtineri | 0.8155 |
| metrics.diagnoza_value_at_10_posts | 0.847 |
| metrics.diagnoza_f1_normal | 0.927 |
| metrics.diagnoza_f1_contor_client | 0.4721 |
| metrics.diagnoza_f1_furt_inainte_contor | 0.771 |
| metrics.diagnoza_f1_pierdere_tehnica | 0.4882 |
| metrics.diagnoza_f1_client_post_gresit | 0.8713 |
| metrics.diagnoza_f1_contor_bilant_setat | 0.9915 |
| metrics.diagnoza_macro_f1_fara_martor | 0.7536 |
| metrics.diagnoza_test_windows | 13200 |
| metrics.fuziune_sgcc_precision_at_10 | 0.0275 |
| metrics.fuziune_sgcc_wasted_trips_per_day_at_10 | 9.725 |
| metrics.fuziune_sgcc_value_lei_per_day_at_10 | 432.957 |
| metrics.fuziune_sgcc_wasted_trips_avoided_per_day_at_10 | 0.025 |
| metrics.fuziune_sgcc_precision_at_20 | 0.0175 |
| metrics.fuziune_sgcc_wasted_trips_per_day_at_20 | 19.65 |
| metrics.fuziune_sgcc_value_lei_per_day_at_20 | 448.671 |
| metrics.fuziune_sgcc_wasted_trips_avoided_per_day_at_20 | 0.075 |
| metrics.fuziune_sgcc_precision_at_50 | 0.012 |
| metrics.fuziune_sgcc_wasted_trips_per_day_at_50 | 49.4 |
| metrics.fuziune_sgcc_value_lei_per_day_at_50 | 548.664 |
| metrics.fuziune_sgcc_wasted_trips_avoided_per_day_at_50 | 0.15 |
| metrics.fuziune_sgcc_precision_at_100 | 0.01 |
| metrics.fuziune_sgcc_wasted_trips_per_day_at_100 | 99 |
| metrics.fuziune_sgcc_value_lei_per_day_at_100 | 707.419 |
| metrics.fuziune_sgcc_wasted_trips_avoided_per_day_at_100 | 0.25 |
| metrics.fuziune_sgcc_roc_auc | 0.8151 |
| metrics.fuziune_sgcc_benign_in_top20_per_day | 0.925 |
| metrics.fuziune_a_real_meters | 15850 |
| metrics.fuziune_a_real_positives | 865 |
| metrics.fuziune_a_real_roc_auc_a | 0.9167 |
| metrics.fuziune_a_real_roc_auc_fused | 0.9194 |
| metrics.fuziune_a_real_precision_at_10_a | 1 |
| metrics.fuziune_a_real_precision_at_10_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_10_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_10_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_10_a | 807.05 |
| metrics.fuziune_a_real_value_lei_at_10_fused | 633.461 |
| metrics.fuziune_a_real_precision_at_20_a | 1 |
| metrics.fuziune_a_real_precision_at_20_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_20_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_20_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_20_a | 2696.46 |
| metrics.fuziune_a_real_value_lei_at_20_fused | 1712.83 |
| metrics.fuziune_a_real_precision_at_50_a | 1 |
| metrics.fuziune_a_real_precision_at_50_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_50_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_50_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_50_a | 8936.94 |
| metrics.fuziune_a_real_value_lei_at_50_fused | 6404.82 |
| metrics.fuziune_a_real_precision_at_100_a | 1 |
| metrics.fuziune_a_real_precision_at_100_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_100_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_100_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_100_a | 18291.7 |
| metrics.fuziune_a_real_value_lei_at_100_fused | 15930.7 |
| metrics.fuziune_a_real_precision_at_200_a | 1 |
| metrics.fuziune_a_real_precision_at_200_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_200_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_200_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_200_a | 39278.3 |
| metrics.fuziune_a_real_value_lei_at_200_fused | 38347.3 |
| metrics.fuziune_a_real_precision_at_300_a | 1 |
| metrics.fuziune_a_real_precision_at_300_fused | 1 |
| metrics.fuziune_a_real_wasted_trips_at_300_a | 0 |
| metrics.fuziune_a_real_wasted_trips_at_300_fused | 0 |
| metrics.fuziune_a_real_value_lei_at_300_a | 48357.8 |
| metrics.fuziune_a_real_value_lei_at_300_fused | 48566.7 |
| metrics.fuziune_a_real_precision_at_500_a | 0.962 |
| metrics.fuziune_a_real_precision_at_500_fused | 0.96 |
| metrics.fuziune_a_real_wasted_trips_at_500_a | 19 |
| metrics.fuziune_a_real_wasted_trips_at_500_fused | 20 |
| metrics.fuziune_a_real_value_lei_at_500_a | 60493.1 |
| metrics.fuziune_a_real_value_lei_at_500_fused | 59996.8 |
| metrics.fuziune_a_real_unsure_meters | 558 |
| metrics.fuziune_a_real_unsure_true_rate | 0.1362 |
| metrics.fuziune_a_real_unsure_resolved | 3 |
| metrics.fuziune_a_real_unsure_resolved_true_rate | 0.3333 |
| metrics.fuziune_harta_A_singur_precision_at_10 | 0.8 |
| metrics.fuziune_harta_A_singur_wasted_trips_per_day_at_10 | 2 |
| metrics.fuziune_harta_A_singur_value_lei_per_day_at_10 | 4966.48 |
| metrics.fuziune_harta_A_singur_precision_at_20 | 0.6437 |
| metrics.fuziune_harta_A_singur_wasted_trips_per_day_at_20 | 7.125 |
| metrics.fuziune_harta_A_singur_value_lei_per_day_at_20 | 7917.45 |
| metrics.fuziune_harta_A_singur_precision_at_50 | 0.4425 |
| metrics.fuziune_harta_A_singur_wasted_trips_per_day_at_50 | 27.875 |
| metrics.fuziune_harta_A_singur_value_lei_per_day_at_50 | 11716.2 |
| metrics.fuziune_harta_A_singur_precision_at_100 | 0.3137 |
| metrics.fuziune_harta_A_singur_wasted_trips_per_day_at_100 | 68.625 |
| metrics.fuziune_harta_A_singur_value_lei_per_day_at_100 | 13817.9 |
| metrics.fuziune_harta_A_singur_roc_auc | 0.9055 |
| metrics.fuziune_harta_v1_precision_at_10 | 0.775 |
| metrics.fuziune_harta_v1_wasted_trips_per_day_at_10 | 2.25 |
| metrics.fuziune_harta_v1_value_lei_per_day_at_10 | 6986.36 |
| metrics.fuziune_harta_v1_precision_at_20 | 0.6188 |
| metrics.fuziune_harta_v1_wasted_trips_per_day_at_20 | 7.625 |
| metrics.fuziune_harta_v1_value_lei_per_day_at_20 | 9590.32 |
| metrics.fuziune_harta_v1_precision_at_50 | 0.405 |
| metrics.fuziune_harta_v1_wasted_trips_per_day_at_50 | 29.75 |
| metrics.fuziune_harta_v1_value_lei_per_day_at_50 | 12395.3 |
| metrics.fuziune_harta_v1_precision_at_100 | 0.2875 |
| metrics.fuziune_harta_v1_wasted_trips_per_day_at_100 | 71.25 |
| metrics.fuziune_harta_v1_value_lei_per_day_at_100 | 15584.7 |
| metrics.fuziune_harta_v1_roc_auc | 0.9013 |
| metrics.fuziune_harta_v2_precision_at_10 | 0.9 |
| metrics.fuziune_harta_v2_wasted_trips_per_day_at_10 | 1 |
| metrics.fuziune_harta_v2_value_lei_per_day_at_10 | 8277.79 |
| metrics.fuziune_harta_v2_precision_at_20 | 0.6813 |
| metrics.fuziune_harta_v2_wasted_trips_per_day_at_20 | 6.375 |
| metrics.fuziune_harta_v2_value_lei_per_day_at_20 | 10443.7 |
| metrics.fuziune_harta_v2_precision_at_50 | 0.4625 |
| metrics.fuziune_harta_v2_wasted_trips_per_day_at_50 | 26.875 |
| metrics.fuziune_harta_v2_value_lei_per_day_at_50 | 13594.8 |
| metrics.fuziune_harta_v2_precision_at_100 | 0.3337 |
| metrics.fuziune_harta_v2_wasted_trips_per_day_at_100 | 66.625 |
| metrics.fuziune_harta_v2_value_lei_per_day_at_100 | 17484.2 |
| metrics.fuziune_harta_v2_roc_auc | 0.9065 |
| metrics.fuziune_harta_real_A_singur_roc_auc | 0.9167 |
| metrics.fuziune_harta_real_A_singur_precision_at_10 | 1 |
| metrics.fuziune_harta_real_A_singur_precision_at_100 | 1 |
| metrics.fuziune_harta_real_A_singur_precision_at_300 | 1 |
| metrics.fuziune_harta_real_A_singur_precision_at_500 | 0.962 |
| metrics.fuziune_harta_real_v1_roc_auc | 0.9162 |
| metrics.fuziune_harta_real_v1_precision_at_10 | 1 |
| metrics.fuziune_harta_real_v1_precision_at_100 | 1 |
| metrics.fuziune_harta_real_v1_precision_at_300 | 1 |
| metrics.fuziune_harta_real_v1_precision_at_500 | 0.874 |
| metrics.fuziune_harta_real_v2_roc_auc | 0.9194 |
| metrics.fuziune_harta_real_v2_precision_at_10 | 1 |
| metrics.fuziune_harta_real_v2_precision_at_100 | 1 |
| metrics.fuziune_harta_real_v2_precision_at_300 | 1 |
| metrics.fuziune_harta_real_v2_precision_at_500 | 0.96 |
| metrics.fuziune_harta_v2_wasted_trips_avoided_per_day_at_10 | 1 |
| metrics.fuziune_harta_v2_wasted_trips_avoided_per_day_at_20 | 0.75 |
| metrics.fuziune_harta_v2_wasted_trips_avoided_per_day_at_50 | 1 |
| metrics.fuziune_harta_v2_wasted_trips_avoided_per_day_at_100 | 2 |
| metrics.invizibil_share_invisible_to_meters | 0.4827 |
| metrics.invizibil_lost_kwh_day_meters | 1891.79 |
| metrics.invizibil_lost_kwh_day_theft | 594.804 |
| metrics.invizibil_lost_kwh_day_technical | 861.442 |
| metrics.invizibil_lost_kwh_day_wrong_post | 308.695 |
| metrics.cauze_post_furt_inainte_contor_windows | 794 |
| metrics.cauze_post_furt_inainte_contor_found | 0.7594 |
| metrics.cauze_post_furt_inainte_contor_right_cause | 0.6159 |
| metrics.cauze_post_furt_inainte_contor_energy_found_share | 0.8692 |
| metrics.cauze_post_pierdere_tehnica_windows | 411 |
| metrics.cauze_post_pierdere_tehnica_found | 0.6423 |
| metrics.cauze_post_pierdere_tehnica_right_cause | 0.5012 |
| metrics.cauze_post_pierdere_tehnica_energy_found_share | 0.8589 |
| metrics.cauze_post_contor_bilant_setat_windows | 292 |
| metrics.cauze_post_contor_bilant_setat_found | 0.9863 |
| metrics.cauze_post_contor_bilant_setat_right_cause | 0.9829 |
| metrics.cauze_post_client_post_gresit_windows | 952 |
| metrics.cauze_post_client_post_gresit_found | 0.5819 |
| metrics.cauze_post_client_post_gresit_right_cause | 0.5441 |
| metrics.cauze_post_client_post_gresit_energy_found_share | 0.7532 |
| metrics.cauze_post_energy_found_share | 0.8362 |
| metrics.cauze_post_lei_per_month_found | 24662.5 |
| metrics.cauze_post_false_alarm_share_of_found | 0.179 |
| metrics.fuziune_precision_at_10 | 0.13 |
| metrics.fuziune_wasted_trips_per_day_at_10 | 8.7 |
| metrics.fuziune_value_lei_per_day_at_10 | 1050.73 |
| metrics.fuziune_wasted_trips_avoided_per_day_at_10 | 0.275 |
| metrics.fuziune_precision_at_20 | 0.0787 |
| metrics.fuziune_wasted_trips_per_day_at_20 | 18.425 |
| metrics.fuziune_value_lei_per_day_at_20 | 1181.34 |
| metrics.fuziune_wasted_trips_avoided_per_day_at_20 | 0.3 |
| metrics.fuziune_precision_at_50 | 0.043 |
| metrics.fuziune_wasted_trips_per_day_at_50 | 47.85 |
| metrics.fuziune_value_lei_per_day_at_50 | 1416.56 |
| metrics.fuziune_wasted_trips_avoided_per_day_at_50 | 0.15 |
| metrics.fuziune_precision_at_100 | 0.0282 |
| metrics.fuziune_wasted_trips_per_day_at_100 | 97.175 |
| metrics.fuziune_value_lei_per_day_at_100 | 1682.13 |
| metrics.fuziune_wasted_trips_avoided_per_day_at_100 | 0.2 |
| metrics.fuziune_roc_auc | 0.9118 |
| metrics.fuziune_benign_in_top20_per_day | 0.775 |
| metrics.fuziune_info_a_sim_noise_sd | 2 |
| metrics.fuziune_info_a_sim_auc | 0.9053 |
| metrics.fuziune_info_eval_days | 40 |
| metrics.fuziune_info_meters | 24147 |
| metrics.fuziune_info_positives_per_day | 9.925 |
| metrics.fuziune_info_benign_share | 0.0412 |
| baseline_metrics.normal_mae_kwh_day | 14.9178 |
| baseline_metrics.normal_mape_pct | 40.3424 |
| baseline_metrics.normal_bias_kwh_day | 3.6878 |
| baseline_metrics.normal_coverage_p10_p90 | 0.8632 |
| baseline_metrics.normal_interval_width_kwh_day | 197.661 |
| baseline_metrics.normal_pinball_mean | 9.4169 |
| baseline_metrics.diagnoza_macro_f1 | 0.4813 |
| baseline_metrics.diagnoza_accuracy | 0.7804 |
| baseline_metrics.diagnoza_value_at_10_posts | 0.7709 |
| baseline_metrics.diagnoza_f1_normal | 0.9006 |
| baseline_metrics.diagnoza_f1_contor_client | 0.16 |
| baseline_metrics.diagnoza_f1_furt_inainte_contor | 0.3397 |
| baseline_metrics.diagnoza_f1_pierdere_tehnica | 0.2729 |
| baseline_metrics.diagnoza_f1_client_post_gresit | 0.3444 |
| baseline_metrics.diagnoza_f1_contor_bilant_setat | 0.8705 |
| baseline_metrics.fuziune_sgcc_precision_at_10 | 0.025 |
| baseline_metrics.fuziune_sgcc_wasted_trips_per_day_at_10 | 9.75 |
| baseline_metrics.fuziune_sgcc_value_lei_per_day_at_10 | 125.921 |
| baseline_metrics.fuziune_sgcc_precision_at_20 | 0.0138 |
| baseline_metrics.fuziune_sgcc_wasted_trips_per_day_at_20 | 19.725 |
| baseline_metrics.fuziune_sgcc_value_lei_per_day_at_20 | 125.921 |
| baseline_metrics.fuziune_sgcc_precision_at_50 | 0.009 |
| baseline_metrics.fuziune_sgcc_wasted_trips_per_day_at_50 | 49.55 |
| baseline_metrics.fuziune_sgcc_value_lei_per_day_at_50 | 450.346 |
| baseline_metrics.fuziune_sgcc_precision_at_100 | 0.0075 |
| baseline_metrics.fuziune_sgcc_wasted_trips_per_day_at_100 | 99.25 |
| baseline_metrics.fuziune_sgcc_value_lei_per_day_at_100 | 538.865 |
| baseline_metrics.fuziune_sgcc_roc_auc | 0.8027 |
| baseline_metrics.fuziune_sgcc_benign_in_top20_per_day | 0.9 |
| baseline_metrics.fuziune_harta_v2_precision_at_10 | 0.8 |
| baseline_metrics.fuziune_harta_v2_precision_at_20 | 0.6437 |
| baseline_metrics.fuziune_harta_v2_precision_at_50 | 0.4425 |
| baseline_metrics.fuziune_harta_v2_precision_at_100 | 0.3137 |
| baseline_metrics.cauze_post_furt_inainte_contor_found | 0 |
| baseline_metrics.cauze_post_furt_inainte_contor_right_cause | 0 |
| baseline_metrics.cauze_post_furt_inainte_contor_energy_found_share | 0 |
| baseline_metrics.cauze_post_pierdere_tehnica_found | 0 |
| baseline_metrics.cauze_post_pierdere_tehnica_right_cause | 0 |
| baseline_metrics.cauze_post_pierdere_tehnica_energy_found_share | 0 |
| baseline_metrics.cauze_post_contor_bilant_setat_found | 0 |
| baseline_metrics.cauze_post_contor_bilant_setat_right_cause | 0 |
| baseline_metrics.cauze_post_client_post_gresit_found | 0 |
| baseline_metrics.cauze_post_client_post_gresit_right_cause | 0 |
| baseline_metrics.cauze_post_client_post_gresit_energy_found_share | 0 |
| baseline_metrics.cauze_post_energy_found_share | 0 |
| baseline_metrics.cauze_post_lei_per_month_found | 0 |
| baseline_metrics.fuziune_precision_at_10 | 0.1025 |
| baseline_metrics.fuziune_wasted_trips_per_day_at_10 | 8.975 |
| baseline_metrics.fuziune_value_lei_per_day_at_10 | 824.204 |
| baseline_metrics.fuziune_precision_at_20 | 0.0638 |
| baseline_metrics.fuziune_wasted_trips_per_day_at_20 | 18.725 |
| baseline_metrics.fuziune_value_lei_per_day_at_20 | 920.739 |
| baseline_metrics.fuziune_precision_at_50 | 0.04 |
| baseline_metrics.fuziune_wasted_trips_per_day_at_50 | 48 |
| baseline_metrics.fuziune_value_lei_per_day_at_50 | 1176.87 |
| baseline_metrics.fuziune_precision_at_100 | 0.0263 |
| baseline_metrics.fuziune_wasted_trips_per_day_at_100 | 97.375 |
| baseline_metrics.fuziune_value_lei_per_day_at_100 | 1370.3 |
| baseline_metrics.fuziune_roc_auc | 0.9053 |
| baseline_metrics.fuziune_benign_in_top20_per_day | 0.95 |
| synthetic_share | 1 |

</details>

<details><summary>reports/bilant/plan_b.json</summary>

[Sursa](../../reports/bilant/plan_b.json) · SHA256 `27c2f800692dc09ec2fc18290becd56b59adb8bd9ab5eb0369cdd83857d85e44`

| Câmp | Valoare |
|---|---:|
| posts | 287 |
| capture_top20pct_model | 0.303443 |
| capture_top20pct_random | 0.198085 |
| capture_top20pct_biggest | 0.225916 |
| lei_year_per_meter_model_top20pct | 2997.37 |
| lei_year_per_meter_random | 1961.81 |

</details>

<details><summary>reports/bilant/v2_comparison.json</summary>

[Sursa](../../reports/bilant/v2_comparison.json) · SHA256 `735ac466c5565ca615b3c3d4f106d7c30cb1ad0dd8b32bb22991ac9b8151220d`

| Câmp | Valoare |
|---|---:|
| test_windows | 13200 |
| train_posts_v1 | 300 |
| train_windows_v2 | 132000 |
| train_posts_v2 | 3000 |
| v1.macro_f1 | 0.703729 |
| v1.f1_normal | 0.912323 |
| v1.f1_contor_client | 0.384083 |
| v1.f1_furt_inainte_contor | 0.669393 |
| v1.f1_pierdere_tehnica | 0.505348 |
| v1.f1_client_post_gresit | 0.758074 |
| v1.f1_contor_bilant_setat | 0.993151 |
| doar_mai_multe_posturi.macro_f1 | 0.717491 |
| doar_mai_multe_posturi.f1_normal | 0.869717 |
| doar_mai_multe_posturi.f1_contor_client | 0.367254 |
| doar_mai_multe_posturi.f1_furt_inainte_contor | 0.759021 |
| doar_mai_multe_posturi.f1_pierdere_tehnica | 0.442344 |
| doar_mai_multe_posturi.f1_client_post_gresit | 0.871741 |
| doar_mai_multe_posturi.f1_contor_bilant_setat | 0.994872 |
| mai_multe_posturi_si_trasaturi_noi.macro_f1 | 0.735448 |
| mai_multe_posturi_si_trasaturi_noi.f1_normal | 0.908472 |
| mai_multe_posturi_si_trasaturi_noi.f1_contor_client | 0.445985 |
| mai_multe_posturi_si_trasaturi_noi.f1_furt_inainte_contor | 0.761665 |
| mai_multe_posturi_si_trasaturi_noi.f1_pierdere_tehnica | 0.429379 |
| mai_multe_posturi_si_trasaturi_noi.f1_client_post_gresit | 0.870613 |
| mai_multe_posturi_si_trasaturi_noi.f1_contor_bilant_setat | 0.996575 |
| v2_cautare_optuna.macro_f1 | 0.753521 |
| v2_cautare_optuna.f1_normal | 0.927017 |
| v2_cautare_optuna.f1_contor_client | 0.472106 |
| v2_cautare_optuna.f1_furt_inainte_contor | 0.770957 |
| v2_cautare_optuna.f1_pierdere_tehnica | 0.488242 |
| v2_cautare_optuna.f1_client_post_gresit | 0.87132 |
| v2_cautare_optuna.f1_contor_bilant_setat | 0.991482 |
| validation_macro_f1_v2 | 0.76846 |
| validation_macro_f1_v1_settings | 0.751707 |
| seconds | 1272.1 |

</details>

<details><summary>reports/bilant/v2_params.json</summary>

[Sursa](../../reports/bilant/v2_params.json) · SHA256 `d1a671bdddf2bd1088933def3867562a8eee39d577eb0e8e0c5707d985818b41`

| Câmp | Valoare |
|---|---:|

</details>

<details><summary>reports/bilant/weave_check.json</summary>

[Sursa](../../reports/bilant/weave_check.json) · SHA256 `a2a51e16ba203c82c28bfd8b4ac3fe233588443dbbc7a6aa9357cd02f8d2cb75`

| Câmp | Valoare |
|---|---:|
| weave_posts | 41973 |
| sim_posts | 300 |
| factor_incarcare_weave_median | 0.565008 |
| pondere_noapte_weave_median | 0.170002 |
| seara_fata_de_zi_weave_median | 1.55176 |
| factor_incarcare_sim_median | 0.513814 |
| pondere_noapte_sim_median | 0.162889 |
| seara_fata_de_zi_sim_median | 3.66604 |
| peak_hour_mode_weave | 18 |
| peak_hour_mode_sim | 19 |

</details>

<details><summary>reports/benchmark/bilant_feederbw.json</summary>

[Sursa](../../reports/benchmark/bilant_feederbw.json) · SHA256 `ccb265dd074b25258f3e495be6ae3ee7b2f59ccec9cc23826734290f649c5e12`

| Câmp | Valoare |
|---|---:|
| windows.train | 7310 |
| windows.validation | 2795 |
| windows.test | 2795 |
| posts.train | 170 |
| posts.validation | 65 |
| posts.test | 65 |
| reference_check.tuned_macro_f1_reproduced | 0.71393 |
| reference_check.tuned_macro_f1_report | 0.71393 |
| reference_check.test_windows | 2795 |
| reference_check.report_test_windows | 2795 |
| validation_macro_f1.lightgbm_tuned | 0.6405 |
| validation_macro_f1.catboost_tuned | 0.62691 |
| lightgbm_tuned.test.macro_f1 | 0.71393 |
| lightgbm_tuned.test.accuracy | 0.74919 |
| lightgbm_tuned.test.f1_by_class.normal | 0.8554 |
| lightgbm_tuned.test.f1_by_class.contor_client | 0.6083 |
| lightgbm_tuned.test.f1_by_class.furt_inainte_contor | 0.4686 |
| lightgbm_tuned.test.f1_by_class.pierdere_tehnica | 0.54829 |
| lightgbm_tuned.test.f1_by_class.client_post_gresit | 0.81008 |
| lightgbm_tuned.test.f1_by_class.contor_bilant_setat | 0.99291 |
| catboost.test.macro_f1 | 0.70483 |
| catboost.test.accuracy | 0.73703 |
| catboost.test.f1_by_class.normal | 0.84518 |
| catboost.test.f1_by_class.contor_client | 0.58717 |
| catboost.test.f1_by_class.furt_inainte_contor | 0.45727 |
| catboost.test.f1_by_class.pierdere_tehnica | 0.52063 |
| catboost.test.f1_by_class.client_post_gresit | 0.81869 |
| catboost.test.f1_by_class.contor_bilant_setat | 1 |
| delta_catboost_minus_lightgbm_tuned.macro_f1.delta | -0.00911 |
| delta_catboost_minus_lightgbm_tuned.macro_f1.ci90 | [-0.03146, 0.00372] |
| delta_catboost_minus_lightgbm_tuned.macro_f1.share_positive | 0.099 |
| delta_catboost_minus_lightgbm_tuned.macro_f1.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.macro_f1.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_normal.delta | -0.01022 |
| delta_catboost_minus_lightgbm_tuned.f1_normal.ci90 | [-0.02867, 0.00493] |
| delta_catboost_minus_lightgbm_tuned.f1_normal.share_positive | 0.127 |
| delta_catboost_minus_lightgbm_tuned.f1_normal.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_normal.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_client.delta | -0.02113 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_client.ci90 | [-0.07073, 0.02654] |
| delta_catboost_minus_lightgbm_tuned.f1_contor_client.share_positive | 0.207 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_client.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_client.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_furt_inainte_contor.delta | -0.01132 |
| delta_catboost_minus_lightgbm_tuned.f1_furt_inainte_contor.ci90 | [-0.1105, 0.02698] |
| delta_catboost_minus_lightgbm_tuned.f1_furt_inainte_contor.share_positive | 0.343 |
| delta_catboost_minus_lightgbm_tuned.f1_furt_inainte_contor.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_furt_inainte_contor.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_pierdere_tehnica.delta | -0.02765 |
| delta_catboost_minus_lightgbm_tuned.f1_pierdere_tehnica.ci90 | [-0.10428, 0.01714] |
| delta_catboost_minus_lightgbm_tuned.f1_pierdere_tehnica.share_positive | 0.219 |
| delta_catboost_minus_lightgbm_tuned.f1_pierdere_tehnica.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_pierdere_tehnica.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_client_post_gresit.delta | 0.00861 |
| delta_catboost_minus_lightgbm_tuned.f1_client_post_gresit.ci90 | [-0.02563, 0.03889] |
| delta_catboost_minus_lightgbm_tuned.f1_client_post_gresit.share_positive | 0.646 |
| delta_catboost_minus_lightgbm_tuned.f1_client_post_gresit.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_client_post_gresit.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_bilant_setat.delta | 0.00709 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_bilant_setat.ci90 | [0.0, 0.03448] |
| delta_catboost_minus_lightgbm_tuned.f1_contor_bilant_setat.share_positive | 0.568 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_bilant_setat.groups | 8 |
| delta_catboost_minus_lightgbm_tuned.f1_contor_bilant_setat.n_boot | 1000 |
| delta_catboost_minus_lightgbm_tuned.classes_worse_ci_below_zero | [] |
| theft_before_meter.lightgbm.f1 | 0.4686 |
| theft_before_meter.lightgbm.recall | 0.40928 |
| theft_before_meter.lightgbm.precision | 0.54802 |
| theft_before_meter.lightgbm.n_true | 237 |
| theft_before_meter.lightgbm.missed_as.contor_client | 67 |
| theft_before_meter.lightgbm.missed_as.pierdere_tehnica | 40 |
| theft_before_meter.lightgbm.missed_as.normal | 31 |
| theft_before_meter.lightgbm.missed_as.contor_bilant_setat | 1 |
| theft_before_meter.lightgbm.missed_as.client_post_gresit | 1 |
| theft_before_meter.catboost.f1 | 0.45727 |
| theft_before_meter.catboost.recall | 0.41772 |
| theft_before_meter.catboost.precision | 0.5051 |
| theft_before_meter.catboost.n_true | 237 |
| theft_before_meter.catboost.missed_as.contor_client | 72 |
| theft_before_meter.catboost.missed_as.normal | 34 |
| theft_before_meter.catboost.missed_as.pierdere_tehnica | 31 |
| theft_before_meter.catboost.missed_as.client_post_gresit | 1 |
| seconds_total | 588 |

</details>

<details><summary>reports/benchmark/bilant_holdout.json</summary>

[Sursa](../../reports/benchmark/bilant_holdout.json) · SHA256 `772e524b852596d73d8c2e548fd4f1170ddcc0116ab316fe214eae3a54c00378`

| Câmp | Valoare |
|---|---:|
| protocol.seed | 2.02611e+09 |
| protocol.posts | 300 |
| protocol.topologies | 6 |
| rows | 13200 |
| posts | 300 |
| class_counts.normal | 7613 |
| class_counts.contor_client | 3891 |
| class_counts.client_post_gresit | 670 |
| class_counts.pierdere_tehnica | 403 |
| class_counts.furt_inainte_contor | 347 |
| class_counts.contor_bilant_setat | 276 |
| model.macro_f1 | 0.775395 |
| model.f1_normal | 0.913423 |
| model.f1_contor_client | 0.778311 |
| model.f1_furt_inainte_contor | 0.597914 |
| model.f1_pierdere_tehnica | 0.535783 |
| model.f1_client_post_gresit | 0.828753 |
| model.f1_contor_bilant_setat | 0.998185 |
| baseline.macro_f1 | 0.420591 |
| baseline.f1_normal | 0.805198 |
| baseline.f1_contor_client | 0.283953 |
| baseline.f1_furt_inainte_contor | 0.189441 |
| baseline.f1_pierdere_tehnica | 0.254642 |
| baseline.f1_client_post_gresit | 0.223844 |
| baseline.f1_contor_bilant_setat | 0.766467 |
| delta_macro_f1.delta | 0.3548 |
| delta_macro_f1.ci90 | [0.3163, 0.39007] |
| delta_macro_f1.share_positive | 1 |
| delta_macro_f1.groups | 60 |
| delta_macro_f1.n_boot | 1000 |
| abstain_share | 0.200076 |
| confident_accuracy | 0.896202 |

</details>

<details><summary>reports/benchmark/bilant_holdout_protocol.json</summary>

[Sursa](../../reports/benchmark/bilant_holdout_protocol.json) · SHA256 `f2261229bd0379a6d8ea9c419de3e125a696d19e1b6fdc61b722605f4817d856`

| Câmp | Valoare |
|---|---:|
| seed | 2.02611e+09 |
| posts | 300 |
| topologies | 6 |

</details>

<details><summary>reports/benchmark/bilant_v2.json</summary>

[Sursa](../../reports/benchmark/bilant_v2.json) · SHA256 `0245037c2c104d4486b40b2352a0ae86adc65f75150c8a55a4589e60600b5f75`

| Câmp | Valoare |
|---|---:|
| reference_check.macro_f1_reproduced | 0.75352 |
| reference_check.macro_f1_report | 0.75352 |
| reference_check.test_windows | 13200 |
| reference_check.report_test_windows | 13200 |
| reference_check.retrained_identical_labels_share | 1 |
| reference_check.retrained_macro_f1 | 0.75352 |
| lightgbm.validation_macro_f1 | 0.76846 |
| lightgbm.test.macro_f1 | 0.75352 |
| lightgbm.test.accuracy | 0.85538 |
| lightgbm.test.f1_by_class.normal | 0.92702 |
| lightgbm.test.f1_by_class.contor_client | 0.47211 |
| lightgbm.test.f1_by_class.furt_inainte_contor | 0.77096 |
| lightgbm.test.f1_by_class.pierdere_tehnica | 0.48824 |
| lightgbm.test.f1_by_class.client_post_gresit | 0.87132 |
| lightgbm.test.f1_by_class.contor_bilant_setat | 0.99148 |
| lightgbm.abstain_share | 0.14515 |
| catboost.validation_macro_f1 | 0.76122 |
| catboost.test.macro_f1 | 0.75748 |
| catboost.test.accuracy | 0.8625 |
| catboost.test.f1_by_class.normal | 0.93013 |
| catboost.test.f1_by_class.contor_client | 0.49612 |
| catboost.test.f1_by_class.furt_inainte_contor | 0.76406 |
| catboost.test.f1_by_class.pierdere_tehnica | 0.47671 |
| catboost.test.f1_by_class.client_post_gresit | 0.88472 |
| catboost.test.f1_by_class.contor_bilant_setat | 0.99313 |
| catboost.abstain_share | 0.16833 |
| catboost_default_untuned.test.macro_f1 | 0.72098 |
| catboost_default_untuned.test.accuracy | 0.81773 |
| catboost_default_untuned.test.f1_by_class.normal | 0.89851 |
| catboost_default_untuned.test.f1_by_class.contor_client | 0.42962 |
| catboost_default_untuned.test.f1_by_class.furt_inainte_contor | 0.75498 |
| catboost_default_untuned.test.f1_by_class.pierdere_tehnica | 0.3887 |
| catboost_default_untuned.test.f1_by_class.client_post_gresit | 0.86256 |
| catboost_default_untuned.test.f1_by_class.contor_bilant_setat | 0.99148 |
| delta_catboost_minus_lightgbm.macro_f1.delta | 0.00396 |
| delta_catboost_minus_lightgbm.macro_f1.ci90 | [-0.00315, 0.01285] |
| delta_catboost_minus_lightgbm.macro_f1.share_positive | 0.802 |
| delta_catboost_minus_lightgbm.macro_f1.groups | 31 |
| delta_catboost_minus_lightgbm.macro_f1.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_normal.delta | 0.00312 |
| delta_catboost_minus_lightgbm.f1_normal.ci90 | [-0.00031, 0.00637] |
| delta_catboost_minus_lightgbm.f1_normal.share_positive | 0.929 |
| delta_catboost_minus_lightgbm.f1_normal.groups | 31 |
| delta_catboost_minus_lightgbm.f1_normal.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_contor_client.delta | 0.02401 |
| delta_catboost_minus_lightgbm.f1_contor_client.ci90 | [0.00869, 0.04422] |
| delta_catboost_minus_lightgbm.f1_contor_client.share_positive | 0.999 |
| delta_catboost_minus_lightgbm.f1_contor_client.groups | 31 |
| delta_catboost_minus_lightgbm.f1_contor_client.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_furt_inainte_contor.delta | -0.0069 |
| delta_catboost_minus_lightgbm.f1_furt_inainte_contor.ci90 | [-0.02203, 0.01064] |
| delta_catboost_minus_lightgbm.f1_furt_inainte_contor.share_positive | 0.255 |
| delta_catboost_minus_lightgbm.f1_furt_inainte_contor.groups | 31 |
| delta_catboost_minus_lightgbm.f1_furt_inainte_contor.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_pierdere_tehnica.delta | -0.01154 |
| delta_catboost_minus_lightgbm.f1_pierdere_tehnica.ci90 | [-0.03745, 0.00873] |
| delta_catboost_minus_lightgbm.f1_pierdere_tehnica.share_positive | 0.193 |
| delta_catboost_minus_lightgbm.f1_pierdere_tehnica.groups | 31 |
| delta_catboost_minus_lightgbm.f1_pierdere_tehnica.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_client_post_gresit.delta | 0.0134 |
| delta_catboost_minus_lightgbm.f1_client_post_gresit.ci90 | [-0.00122, 0.02955] |
| delta_catboost_minus_lightgbm.f1_client_post_gresit.share_positive | 0.935 |
| delta_catboost_minus_lightgbm.f1_client_post_gresit.groups | 31 |
| delta_catboost_minus_lightgbm.f1_client_post_gresit.n_boot | 1000 |
| delta_catboost_minus_lightgbm.f1_contor_bilant_setat.delta | 0.00165 |
| delta_catboost_minus_lightgbm.f1_contor_bilant_setat.ci90 | [-0.00799, 0.0146] |
| delta_catboost_minus_lightgbm.f1_contor_bilant_setat.share_positive | 0.55 |
| delta_catboost_minus_lightgbm.f1_contor_bilant_setat.groups | 31 |
| delta_catboost_minus_lightgbm.f1_contor_bilant_setat.n_boot | 1000 |
| delta_catboost_minus_lightgbm.classes_worse_ci_below_zero | [] |
| theft_before_meter.lightgbm.f1 | 0.77096 |
| theft_before_meter.lightgbm.recall | 0.73552 |
| theft_before_meter.lightgbm.precision | 0.80999 |
| theft_before_meter.lightgbm.n_true | 794 |
| theft_before_meter.lightgbm.missed_as.contor_client | 140 |
| theft_before_meter.lightgbm.missed_as.normal | 34 |
| theft_before_meter.lightgbm.missed_as.pierdere_tehnica | 32 |
| theft_before_meter.lightgbm.missed_as.client_post_gresit | 4 |
| theft_before_meter.catboost.f1 | 0.76406 |
| theft_before_meter.catboost.recall | 0.74433 |
| theft_before_meter.catboost.precision | 0.78486 |
| theft_before_meter.catboost.n_true | 794 |
| theft_before_meter.catboost.missed_as.contor_client | 120 |
| theft_before_meter.catboost.missed_as.pierdere_tehnica | 38 |
| theft_before_meter.catboost.missed_as.normal | 38 |
| theft_before_meter.catboost.missed_as.client_post_gresit | 7 |
| seconds_total | 1239.9 |

</details>

<details><summary>reports/benchmark/contoare.json</summary>

[Sursa](../../reports/benchmark/contoare.json) · SHA256 `e25023c63957ff95005389d1f2f50085362caf37250864d99878dd8d36aa8d3a`

| Câmp | Valoare |
|---|---:|
| sgcc_real_labels.n_test | 8475 |
| sgcc_real_labels.positives_test | 723 |
| sgcc_real_labels.k_main | 85 |
| sgcc_real_labels.reference_report.pr_auc | 0.3994 |
| sgcc_real_labels.reference_report.precision_at_85 | 0.8 |
| sgcc_real_labels.lightgbm.pr_auc | 0.39942 |
| sgcc_real_labels.lightgbm.roc_auc | 0.81943 |
| sgcc_real_labels.lightgbm.precision_at_k.50 | 0.82 |
| sgcc_real_labels.lightgbm.precision_at_k.85 | 0.8 |
| sgcc_real_labels.lightgbm.precision_at_k.100 | 0.81 |
| sgcc_real_labels.lightgbm.precision_at_k.200 | 0.66 |
| sgcc_real_labels.lightgbm.precision_at_k.400 | 0.5275 |
| sgcc_real_labels.lightgbm.precision_at_k.723 | 0.43015 |
| sgcc_real_labels.lightgbm.precision_at_k.1446 | 0.29945 |
| sgcc_real_labels.lightgbm.recall_at_k.50 | 0.05671 |
| sgcc_real_labels.lightgbm.recall_at_k.85 | 0.09405 |
| sgcc_real_labels.lightgbm.recall_at_k.100 | 0.11203 |
| sgcc_real_labels.lightgbm.recall_at_k.200 | 0.18257 |
| sgcc_real_labels.lightgbm.recall_at_k.400 | 0.29184 |
| sgcc_real_labels.lightgbm.recall_at_k.723 | 0.43015 |
| sgcc_real_labels.lightgbm.recall_at_k.1446 | 0.59889 |
| sgcc_real_labels.lightgbm.calibration.brier | 0.06331 |
| sgcc_real_labels.lightgbm.calibration.ece | 0.00619 |
| sgcc_real_labels.catboost.pr_auc | 0.3947 |
| sgcc_real_labels.catboost.roc_auc | 0.81923 |
| sgcc_real_labels.catboost.precision_at_k.50 | 0.82 |
| sgcc_real_labels.catboost.precision_at_k.85 | 0.76471 |
| sgcc_real_labels.catboost.precision_at_k.100 | 0.78 |
| sgcc_real_labels.catboost.precision_at_k.200 | 0.665 |
| sgcc_real_labels.catboost.precision_at_k.400 | 0.525 |
| sgcc_real_labels.catboost.precision_at_k.723 | 0.41909 |
| sgcc_real_labels.catboost.precision_at_k.1446 | 0.29806 |
| sgcc_real_labels.catboost.recall_at_k.50 | 0.05671 |
| sgcc_real_labels.catboost.recall_at_k.85 | 0.0899 |
| sgcc_real_labels.catboost.recall_at_k.100 | 0.10788 |
| sgcc_real_labels.catboost.recall_at_k.200 | 0.18396 |
| sgcc_real_labels.catboost.recall_at_k.400 | 0.29046 |
| sgcc_real_labels.catboost.recall_at_k.723 | 0.41909 |
| sgcc_real_labels.catboost.recall_at_k.1446 | 0.59613 |
| sgcc_real_labels.catboost.calibration.brier | 0.06334 |
| sgcc_real_labels.catboost.calibration.ece | 0.00505 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.pr_auc.delta | -0.00472 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.pr_auc.ci90 | [-0.01705, 0.00797] |
| sgcc_real_labels.delta_catboost_minus_lightgbm.pr_auc.share_positive | 0.286 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.pr_auc.groups | 8475 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.pr_auc.n_boot | 1000 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.precision_at_85.delta | -0.03529 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.precision_at_85.ci90 | [-0.09412, 0.04706] |
| sgcc_real_labels.delta_catboost_minus_lightgbm.precision_at_85.share_positive | 0.25 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.precision_at_85.groups | 8475 |
| sgcc_real_labels.delta_catboost_minus_lightgbm.precision_at_85.n_boot | 1000 |
| sgcc_real_labels.seconds_total | 55.9 |
| sgcc_real_labels.reference_check.reproduced.pr_auc | 0.39942 |
| sgcc_real_labels.reference_check.reproduced.precision_at_85 | 0.8 |
| lcl_baza.reference_report.subtle_precision_at_k | 0.625 |
| lcl_baza.reference_report.subtle_pr_auc | 0.4057 |
| lcl_baza.reference_report.pr_auc | 0.6778 |
| lcl_baza.n_train | 16328 |
| lcl_baza.households_train | 838 |
| lcl_baza.n_test | 13028 |
| lcl_baza.positives_test | 597 |
| lcl_baza.households_test | 265 |
| lcl_baza.n_subtle | 12813 |
| lcl_baza.positives_subtle | 382 |
| lcl_baza.k_main | 130 |
| lcl_baza.k_top1pct_subtle | 128 |
| lcl_baza.full_test.lightgbm.pr_auc | 0.67785 |
| lcl_baza.full_test.lightgbm.roc_auc | 0.9111 |
| lcl_baza.full_test.lightgbm.precision_at_k.50 | 1 |
| lcl_baza.full_test.lightgbm.precision_at_k.100 | 1 |
| lcl_baza.full_test.lightgbm.precision_at_k.130 | 1 |
| lcl_baza.full_test.lightgbm.precision_at_k.200 | 0.94 |
| lcl_baza.full_test.lightgbm.precision_at_k.300 | 0.85333 |
| lcl_baza.full_test.lightgbm.precision_at_k.400 | 0.81 |
| lcl_baza.full_test.lightgbm.precision_at_k.597 | 0.65829 |
| lcl_baza.full_test.lightgbm.precision_at_k.1194 | 0.37102 |
| lcl_baza.full_test.lightgbm.recall_at_k.50 | 0.08375 |
| lcl_baza.full_test.lightgbm.recall_at_k.100 | 0.1675 |
| lcl_baza.full_test.lightgbm.recall_at_k.130 | 0.21776 |
| lcl_baza.full_test.lightgbm.recall_at_k.200 | 0.31491 |
| lcl_baza.full_test.lightgbm.recall_at_k.300 | 0.42881 |
| lcl_baza.full_test.lightgbm.recall_at_k.400 | 0.54271 |
| lcl_baza.full_test.lightgbm.recall_at_k.597 | 0.65829 |
| lcl_baza.full_test.lightgbm.recall_at_k.1194 | 0.74204 |
| lcl_baza.full_test.lightgbm.calibration.brier | 0.02322 |
| lcl_baza.full_test.lightgbm.calibration.ece | 0.00383 |
| lcl_baza.full_test.catboost.pr_auc | 0.67758 |
| lcl_baza.full_test.catboost.roc_auc | 0.9119 |
| lcl_baza.full_test.catboost.precision_at_k.50 | 1 |
| lcl_baza.full_test.catboost.precision_at_k.100 | 1 |
| lcl_baza.full_test.catboost.precision_at_k.130 | 1 |
| lcl_baza.full_test.catboost.precision_at_k.200 | 0.98 |
| lcl_baza.full_test.catboost.precision_at_k.300 | 0.88333 |
| lcl_baza.full_test.catboost.precision_at_k.400 | 0.8175 |
| lcl_baza.full_test.catboost.precision_at_k.597 | 0.64154 |
| lcl_baza.full_test.catboost.precision_at_k.1194 | 0.37018 |
| lcl_baza.full_test.catboost.recall_at_k.50 | 0.08375 |
| lcl_baza.full_test.catboost.recall_at_k.100 | 0.1675 |
| lcl_baza.full_test.catboost.recall_at_k.130 | 0.21776 |
| lcl_baza.full_test.catboost.recall_at_k.200 | 0.32831 |
| lcl_baza.full_test.catboost.recall_at_k.300 | 0.44389 |
| lcl_baza.full_test.catboost.recall_at_k.400 | 0.54774 |
| lcl_baza.full_test.catboost.recall_at_k.597 | 0.64154 |
| lcl_baza.full_test.catboost.recall_at_k.1194 | 0.74037 |
| lcl_baza.full_test.catboost.calibration.brier | 0.02243 |
| lcl_baza.full_test.catboost.calibration.ece | 0.00353 |
| lcl_baza.subtle.lightgbm.pr_auc | 0.40573 |
| lcl_baza.subtle.lightgbm.roc_auc | 0.86238 |
| lcl_baza.subtle.lightgbm.precision_at_k.50 | 0.76 |
| lcl_baza.subtle.lightgbm.precision_at_k.100 | 0.66 |
| lcl_baza.subtle.lightgbm.precision_at_k.128 | 0.625 |
| lcl_baza.subtle.lightgbm.precision_at_k.200 | 0.62 |
| lcl_baza.subtle.lightgbm.precision_at_k.382 | 0.4712 |
| lcl_baza.subtle.lightgbm.recall_at_k.50 | 0.09948 |
| lcl_baza.subtle.lightgbm.recall_at_k.100 | 0.17277 |
| lcl_baza.subtle.lightgbm.recall_at_k.128 | 0.20942 |
| lcl_baza.subtle.lightgbm.recall_at_k.200 | 0.32461 |
| lcl_baza.subtle.lightgbm.recall_at_k.382 | 0.4712 |
| lcl_baza.subtle.lightgbm.precision_top1pct | 0.625 |
| lcl_baza.subtle.catboost.pr_auc | 0.41742 |
| lcl_baza.subtle.catboost.roc_auc | 0.8642 |
| lcl_baza.subtle.catboost.precision_at_k.50 | 0.84 |
| lcl_baza.subtle.catboost.precision_at_k.100 | 0.73 |
| lcl_baza.subtle.catboost.precision_at_k.128 | 0.70312 |
| lcl_baza.subtle.catboost.precision_at_k.200 | 0.635 |
| lcl_baza.subtle.catboost.precision_at_k.382 | 0.45812 |
| lcl_baza.subtle.catboost.recall_at_k.50 | 0.10995 |
| lcl_baza.subtle.catboost.recall_at_k.100 | 0.1911 |
| lcl_baza.subtle.catboost.recall_at_k.128 | 0.2356 |
| lcl_baza.subtle.catboost.recall_at_k.200 | 0.33246 |
| lcl_baza.subtle.catboost.recall_at_k.382 | 0.45812 |
| lcl_baza.subtle.catboost.precision_top1pct | 0.70312 |
| lcl_baza.tamper_only.lightgbm.pr_auc | 0.4627 |
| lcl_baza.tamper_only.lightgbm.precision_at_k | 0.59524 |
| lcl_baza.tamper_only.catboost.pr_auc | 0.47206 |
| lcl_baza.tamper_only.catboost.precision_at_k | 0.61905 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.pr_auc.delta | -0.00027 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.pr_auc.ci90 | [-0.02245, 0.02238] |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.pr_auc.share_positive | 0.457 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.pr_auc.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.pr_auc.n_boot | 1000 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.precision_at_130.delta | 0 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.precision_at_130.ci90 | [0.0, 0.00769] |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.precision_at_130.share_positive | 0.077 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.precision_at_130.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.full_test.precision_at_130.n_boot | 1000 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.pr_auc.delta | 0.01169 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.pr_auc.ci90 | [-0.03353, 0.0488] |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.pr_auc.share_positive | 0.627 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.pr_auc.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.pr_auc.n_boot | 1000 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.precision_at_128.delta | 0.07812 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.precision_at_128.ci90 | [-0.08594, 0.2126] |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.precision_at_128.share_positive | 0.656 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.precision_at_128.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.subtle.precision_at_128.n_boot | 1000 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.pr_auc.delta | 0.00936 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.pr_auc.ci90 | [-0.04804, 0.05208] |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.pr_auc.share_positive | 0.567 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.pr_auc.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.pr_auc.n_boot | 1000 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.delta | 0.02381 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.ci90 | [-0.11111, 0.16] |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.share_positive | 0.564 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.groups | 265 |
| lcl_baza.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.n_boot | 1000 |
| lcl_baza.per_kind.lightgbm[0].n | 55 |
| lcl_baza.per_kind.lightgbm[0].roc_auc_vs_normal | 0.9989 |
| lcl_baza.per_kind.lightgbm[0].flagged_share_at_5pct | 1 |
| lcl_baza.per_kind.lightgbm[1].n | 62 |
| lcl_baza.per_kind.lightgbm[1].roc_auc_vs_normal | 0.9988 |
| lcl_baza.per_kind.lightgbm[1].flagged_share_at_5pct | 0.9839 |
| lcl_baza.per_kind.lightgbm[2].n | 45 |
| lcl_baza.per_kind.lightgbm[2].roc_auc_vs_normal | 0.9936 |
| lcl_baza.per_kind.lightgbm[2].flagged_share_at_5pct | 0.9778 |
| lcl_baza.per_kind.lightgbm[3].n | 60 |
| lcl_baza.per_kind.lightgbm[3].roc_auc_vs_normal | 0.9388 |
| lcl_baza.per_kind.lightgbm[3].flagged_share_at_5pct | 0.7167 |
| lcl_baza.per_kind.lightgbm[4].n | 54 |
| lcl_baza.per_kind.lightgbm[4].roc_auc_vs_normal | 0.6478 |
| lcl_baza.per_kind.lightgbm[4].flagged_share_at_5pct | 0.0556 |
| lcl_baza.per_kind.lightgbm[5].n | 53 |
| lcl_baza.per_kind.lightgbm[5].roc_auc_vs_normal | 0.9991 |
| lcl_baza.per_kind.lightgbm[5].flagged_share_at_5pct | 1 |
| lcl_baza.per_kind.lightgbm[6].n | 54 |
| lcl_baza.per_kind.lightgbm[6].roc_auc_vs_normal | 0.7911 |
| lcl_baza.per_kind.lightgbm[6].flagged_share_at_5pct | 0.1481 |
| lcl_baza.per_kind.lightgbm[7].n | 30 |
| lcl_baza.per_kind.lightgbm[7].roc_auc_vs_normal | 0.9373 |
| lcl_baza.per_kind.lightgbm[7].flagged_share_at_5pct | 0.4333 |
| lcl_baza.per_kind.lightgbm[8].n | 18 |
| lcl_baza.per_kind.lightgbm[8].roc_auc_vs_normal | 0.9177 |
| lcl_baza.per_kind.lightgbm[8].flagged_share_at_5pct | 0.7778 |
| lcl_baza.per_kind.lightgbm[9].n | 24 |
| lcl_baza.per_kind.lightgbm[9].roc_auc_vs_normal | 0.9923 |
| lcl_baza.per_kind.lightgbm[9].flagged_share_at_5pct | 0.9583 |
| lcl_baza.per_kind.lightgbm[10].n | 25 |
| lcl_baza.per_kind.lightgbm[10].roc_auc_vs_normal | 0.9577 |
| lcl_baza.per_kind.lightgbm[10].flagged_share_at_5pct | 0.8 |
| lcl_baza.per_kind.lightgbm[11].n | 28 |
| lcl_baza.per_kind.lightgbm[11].roc_auc_vs_normal | 0.967 |
| lcl_baza.per_kind.lightgbm[11].flagged_share_at_5pct | 0.8214 |
| lcl_baza.per_kind.lightgbm[12].n | 35 |
| lcl_baza.per_kind.lightgbm[12].roc_auc_vs_normal | 0.8965 |
| lcl_baza.per_kind.lightgbm[12].flagged_share_at_5pct | 0.5714 |
| lcl_baza.per_kind.lightgbm[13].n | 21 |
| lcl_baza.per_kind.lightgbm[13].roc_auc_vs_normal | 0.8354 |
| lcl_baza.per_kind.lightgbm[13].flagged_share_at_5pct | 0.2381 |
| lcl_baza.per_kind.lightgbm[14].n | 33 |
| lcl_baza.per_kind.lightgbm[14].roc_auc_vs_normal | 0.8497 |
| lcl_baza.per_kind.lightgbm[14].flagged_share_at_5pct | 0.4848 |
| lcl_baza.per_kind.lightgbm[15].n | 255 |
| lcl_baza.per_kind.lightgbm[15].roc_auc_vs_normal | 0.5391 |
| lcl_baza.per_kind.lightgbm[15].flagged_share_at_5pct | 0.0157 |
| lcl_baza.per_kind.lightgbm[16].n | 241 |
| lcl_baza.per_kind.lightgbm[16].roc_auc_vs_normal | 0.6549 |
| lcl_baza.per_kind.lightgbm[16].flagged_share_at_5pct | 0.112 |
| lcl_baza.per_kind.catboost[0].n | 55 |
| lcl_baza.per_kind.catboost[0].roc_auc_vs_normal | 0.9991 |
| lcl_baza.per_kind.catboost[0].flagged_share_at_5pct | 1 |
| lcl_baza.per_kind.catboost[1].n | 62 |
| lcl_baza.per_kind.catboost[1].roc_auc_vs_normal | 0.9968 |
| lcl_baza.per_kind.catboost[1].flagged_share_at_5pct | 0.9677 |
| lcl_baza.per_kind.catboost[2].n | 45 |
| lcl_baza.per_kind.catboost[2].roc_auc_vs_normal | 0.9953 |
| lcl_baza.per_kind.catboost[2].flagged_share_at_5pct | 0.9556 |
| lcl_baza.per_kind.catboost[3].n | 60 |
| lcl_baza.per_kind.catboost[3].roc_auc_vs_normal | 0.9386 |
| lcl_baza.per_kind.catboost[3].flagged_share_at_5pct | 0.7 |
| lcl_baza.per_kind.catboost[4].n | 54 |
| lcl_baza.per_kind.catboost[4].roc_auc_vs_normal | 0.6389 |
| lcl_baza.per_kind.catboost[4].flagged_share_at_5pct | 0.037 |
| lcl_baza.per_kind.catboost[5].n | 53 |
| lcl_baza.per_kind.catboost[5].roc_auc_vs_normal | 0.9962 |
| lcl_baza.per_kind.catboost[5].flagged_share_at_5pct | 0.9623 |
| lcl_baza.per_kind.catboost[6].n | 54 |
| lcl_baza.per_kind.catboost[6].roc_auc_vs_normal | 0.7961 |
| lcl_baza.per_kind.catboost[6].flagged_share_at_5pct | 0.2407 |
| lcl_baza.per_kind.catboost[7].n | 30 |
| lcl_baza.per_kind.catboost[7].roc_auc_vs_normal | 0.9375 |
| lcl_baza.per_kind.catboost[7].flagged_share_at_5pct | 0.3333 |
| lcl_baza.per_kind.catboost[8].n | 18 |
| lcl_baza.per_kind.catboost[8].roc_auc_vs_normal | 0.9189 |
| lcl_baza.per_kind.catboost[8].flagged_share_at_5pct | 0.7222 |
| lcl_baza.per_kind.catboost[9].n | 24 |
| lcl_baza.per_kind.catboost[9].roc_auc_vs_normal | 0.994 |
| lcl_baza.per_kind.catboost[9].flagged_share_at_5pct | 0.875 |
| lcl_baza.per_kind.catboost[10].n | 25 |
| lcl_baza.per_kind.catboost[10].roc_auc_vs_normal | 0.9749 |
| lcl_baza.per_kind.catboost[10].flagged_share_at_5pct | 0.8 |
| lcl_baza.per_kind.catboost[11].n | 28 |
| lcl_baza.per_kind.catboost[11].roc_auc_vs_normal | 0.9732 |
| lcl_baza.per_kind.catboost[11].flagged_share_at_5pct | 0.7857 |
| lcl_baza.per_kind.catboost[12].n | 35 |
| lcl_baza.per_kind.catboost[12].roc_auc_vs_normal | 0.9055 |
| lcl_baza.per_kind.catboost[12].flagged_share_at_5pct | 0.5714 |
| lcl_baza.per_kind.catboost[13].n | 21 |
| lcl_baza.per_kind.catboost[13].roc_auc_vs_normal | 0.8367 |
| lcl_baza.per_kind.catboost[13].flagged_share_at_5pct | 0.2857 |
| lcl_baza.per_kind.catboost[14].n | 33 |
| lcl_baza.per_kind.catboost[14].roc_auc_vs_normal | 0.8603 |
| lcl_baza.per_kind.catboost[14].flagged_share_at_5pct | 0.4242 |
| lcl_baza.per_kind.catboost[15].n | 255 |
| lcl_baza.per_kind.catboost[15].roc_auc_vs_normal | 0.6531 |
| lcl_baza.per_kind.catboost[15].flagged_share_at_5pct | 0.0431 |
| lcl_baza.per_kind.catboost[16].n | 241 |
| lcl_baza.per_kind.catboost[16].roc_auc_vs_normal | 0.6658 |
| lcl_baza.per_kind.catboost[16].flagged_share_at_5pct | 0.1328 |
| lcl_baza.seconds | 34.1 |
| lcl_baza.reference_check.reproduced.subtle_precision_at_k | 0.625 |
| lcl_baza.reference_check.reproduced.subtle_pr_auc | 0.40573 |
| lcl_baza.reference_check.reproduced.pr_auc | 0.67785 |
| lcl_extins.reference_report.subtle_precision_at_k | 0.8906 |
| lcl_extins.reference_report.subtle_pr_auc | 0.5175 |
| lcl_extins.reference_report.pr_auc | 0.7344 |
| lcl_extins.n_train | 93051 |
| lcl_extins.households_train | 4914 |
| lcl_extins.n_test | 13028 |
| lcl_extins.positives_test | 597 |
| lcl_extins.households_test | 265 |
| lcl_extins.n_subtle | 12813 |
| lcl_extins.positives_subtle | 382 |
| lcl_extins.k_main | 130 |
| lcl_extins.k_top1pct_subtle | 128 |
| lcl_extins.full_test.lightgbm.pr_auc | 0.73441 |
| lcl_extins.full_test.lightgbm.roc_auc | 0.91783 |
| lcl_extins.full_test.lightgbm.precision_at_k.50 | 1 |
| lcl_extins.full_test.lightgbm.precision_at_k.100 | 1 |
| lcl_extins.full_test.lightgbm.precision_at_k.130 | 1 |
| lcl_extins.full_test.lightgbm.precision_at_k.200 | 0.99 |
| lcl_extins.full_test.lightgbm.precision_at_k.300 | 0.97 |
| lcl_extins.full_test.lightgbm.precision_at_k.400 | 0.885 |
| lcl_extins.full_test.lightgbm.precision_at_k.597 | 0.67337 |
| lcl_extins.full_test.lightgbm.precision_at_k.1194 | 0.38861 |
| lcl_extins.full_test.lightgbm.recall_at_k.50 | 0.08375 |
| lcl_extins.full_test.lightgbm.recall_at_k.100 | 0.1675 |
| lcl_extins.full_test.lightgbm.recall_at_k.130 | 0.21776 |
| lcl_extins.full_test.lightgbm.recall_at_k.200 | 0.33166 |
| lcl_extins.full_test.lightgbm.recall_at_k.300 | 0.48744 |
| lcl_extins.full_test.lightgbm.recall_at_k.400 | 0.59296 |
| lcl_extins.full_test.lightgbm.recall_at_k.597 | 0.67337 |
| lcl_extins.full_test.lightgbm.recall_at_k.1194 | 0.77722 |
| lcl_extins.full_test.lightgbm.calibration.brier | 0.01926 |
| lcl_extins.full_test.lightgbm.calibration.ece | 0.00245 |
| lcl_extins.full_test.catboost.pr_auc | 0.71869 |
| lcl_extins.full_test.catboost.roc_auc | 0.91812 |
| lcl_extins.full_test.catboost.precision_at_k.50 | 1 |
| lcl_extins.full_test.catboost.precision_at_k.100 | 1 |
| lcl_extins.full_test.catboost.precision_at_k.130 | 1 |
| lcl_extins.full_test.catboost.precision_at_k.200 | 0.995 |
| lcl_extins.full_test.catboost.precision_at_k.300 | 0.94 |
| lcl_extins.full_test.catboost.precision_at_k.400 | 0.87 |
| lcl_extins.full_test.catboost.precision_at_k.597 | 0.66332 |
| lcl_extins.full_test.catboost.precision_at_k.1194 | 0.38945 |
| lcl_extins.full_test.catboost.recall_at_k.50 | 0.08375 |
| lcl_extins.full_test.catboost.recall_at_k.100 | 0.1675 |
| lcl_extins.full_test.catboost.recall_at_k.130 | 0.21776 |
| lcl_extins.full_test.catboost.recall_at_k.200 | 0.33333 |
| lcl_extins.full_test.catboost.recall_at_k.300 | 0.47236 |
| lcl_extins.full_test.catboost.recall_at_k.400 | 0.58291 |
| lcl_extins.full_test.catboost.recall_at_k.597 | 0.66332 |
| lcl_extins.full_test.catboost.recall_at_k.1194 | 0.77889 |
| lcl_extins.full_test.catboost.calibration.brier | 0.02039 |
| lcl_extins.full_test.catboost.calibration.ece | 0.00243 |
| lcl_extins.subtle.lightgbm.pr_auc | 0.5175 |
| lcl_extins.subtle.lightgbm.roc_auc | 0.87239 |
| lcl_extins.subtle.lightgbm.precision_at_k.50 | 0.98 |
| lcl_extins.subtle.lightgbm.precision_at_k.100 | 0.92 |
| lcl_extins.subtle.lightgbm.precision_at_k.128 | 0.89062 |
| lcl_extins.subtle.lightgbm.precision_at_k.200 | 0.735 |
| lcl_extins.subtle.lightgbm.precision_at_k.382 | 0.49738 |
| lcl_extins.subtle.lightgbm.recall_at_k.50 | 0.12827 |
| lcl_extins.subtle.lightgbm.recall_at_k.100 | 0.24084 |
| lcl_extins.subtle.lightgbm.recall_at_k.128 | 0.29843 |
| lcl_extins.subtle.lightgbm.recall_at_k.200 | 0.38482 |
| lcl_extins.subtle.lightgbm.recall_at_k.382 | 0.49738 |
| lcl_extins.subtle.lightgbm.precision_top1pct | 0.89062 |
| lcl_extins.subtle.catboost.pr_auc | 0.48895 |
| lcl_extins.subtle.catboost.roc_auc | 0.8726 |
| lcl_extins.subtle.catboost.precision_at_k.50 | 0.96 |
| lcl_extins.subtle.catboost.precision_at_k.100 | 0.9 |
| lcl_extins.subtle.catboost.precision_at_k.128 | 0.83594 |
| lcl_extins.subtle.catboost.precision_at_k.200 | 0.71 |
| lcl_extins.subtle.catboost.precision_at_k.382 | 0.48429 |
| lcl_extins.subtle.catboost.recall_at_k.50 | 0.12565 |
| lcl_extins.subtle.catboost.recall_at_k.100 | 0.2356 |
| lcl_extins.subtle.catboost.recall_at_k.128 | 0.2801 |
| lcl_extins.subtle.catboost.recall_at_k.200 | 0.37173 |
| lcl_extins.subtle.catboost.recall_at_k.382 | 0.48429 |
| lcl_extins.subtle.catboost.precision_top1pct | 0.83594 |
| lcl_extins.tamper_only.lightgbm.pr_auc | 0.58475 |
| lcl_extins.tamper_only.lightgbm.precision_at_k | 0.78571 |
| lcl_extins.tamper_only.catboost.pr_auc | 0.54992 |
| lcl_extins.tamper_only.catboost.precision_at_k | 0.76984 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.pr_auc.delta | -0.01572 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.pr_auc.ci90 | [-0.02389, -0.00806] |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.pr_auc.share_positive | 0 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.pr_auc.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.pr_auc.n_boot | 1000 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.precision_at_130.delta | 0 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.precision_at_130.ci90 | [0.0, 0.0] |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.precision_at_130.share_positive | 0 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.precision_at_130.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.full_test.precision_at_130.n_boot | 1000 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.pr_auc.delta | -0.02855 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.pr_auc.ci90 | [-0.04615, -0.01235] |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.pr_auc.share_positive | 0.002 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.pr_auc.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.pr_auc.n_boot | 1000 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.precision_at_128.delta | -0.05469 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.precision_at_128.ci90 | [-0.11811, 0.02344] |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.precision_at_128.share_positive | 0.129 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.precision_at_128.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.subtle.precision_at_128.n_boot | 1000 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.pr_auc.delta | -0.03482 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.pr_auc.ci90 | [-0.05982, -0.01199] |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.pr_auc.share_positive | 0.007 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.pr_auc.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.pr_auc.n_boot | 1000 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.delta | -0.01587 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.ci90 | [-0.07937, 0.02381] |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.share_positive | 0.164 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.groups | 265 |
| lcl_extins.delta_catboost_minus_lightgbm.tamper_only.precision_at_126.n_boot | 1000 |
| lcl_extins.per_kind.lightgbm[0].n | 55 |
| lcl_extins.per_kind.lightgbm[0].roc_auc_vs_normal | 0.9996 |
| lcl_extins.per_kind.lightgbm[0].flagged_share_at_5pct | 1 |
| lcl_extins.per_kind.lightgbm[1].n | 62 |
| lcl_extins.per_kind.lightgbm[1].roc_auc_vs_normal | 0.9998 |
| lcl_extins.per_kind.lightgbm[1].flagged_share_at_5pct | 1 |
| lcl_extins.per_kind.lightgbm[2].n | 45 |
| lcl_extins.per_kind.lightgbm[2].roc_auc_vs_normal | 0.9944 |
| lcl_extins.per_kind.lightgbm[2].flagged_share_at_5pct | 0.9333 |
| lcl_extins.per_kind.lightgbm[3].n | 60 |
| lcl_extins.per_kind.lightgbm[3].roc_auc_vs_normal | 0.9443 |
| lcl_extins.per_kind.lightgbm[3].flagged_share_at_5pct | 0.7667 |
| lcl_extins.per_kind.lightgbm[4].n | 54 |
| lcl_extins.per_kind.lightgbm[4].roc_auc_vs_normal | 0.6334 |
| lcl_extins.per_kind.lightgbm[4].flagged_share_at_5pct | 0.1111 |
| lcl_extins.per_kind.lightgbm[5].n | 53 |
| lcl_extins.per_kind.lightgbm[5].roc_auc_vs_normal | 1 |
| lcl_extins.per_kind.lightgbm[5].flagged_share_at_5pct | 1 |
| lcl_extins.per_kind.lightgbm[6].n | 54 |
| lcl_extins.per_kind.lightgbm[6].roc_auc_vs_normal | 0.8094 |
| lcl_extins.per_kind.lightgbm[6].flagged_share_at_5pct | 0.2778 |
| lcl_extins.per_kind.lightgbm[7].n | 30 |
| lcl_extins.per_kind.lightgbm[7].roc_auc_vs_normal | 0.9341 |
| lcl_extins.per_kind.lightgbm[7].flagged_share_at_5pct | 0.4333 |
| lcl_extins.per_kind.lightgbm[8].n | 18 |
| lcl_extins.per_kind.lightgbm[8].roc_auc_vs_normal | 0.9051 |
| lcl_extins.per_kind.lightgbm[8].flagged_share_at_5pct | 0.7778 |
| lcl_extins.per_kind.lightgbm[9].n | 24 |
| lcl_extins.per_kind.lightgbm[9].roc_auc_vs_normal | 0.9906 |
| lcl_extins.per_kind.lightgbm[9].flagged_share_at_5pct | 0.9583 |
| lcl_extins.per_kind.lightgbm[10].n | 25 |
| lcl_extins.per_kind.lightgbm[10].roc_auc_vs_normal | 0.9769 |
| lcl_extins.per_kind.lightgbm[10].flagged_share_at_5pct | 0.84 |
| lcl_extins.per_kind.lightgbm[11].n | 28 |
| lcl_extins.per_kind.lightgbm[11].roc_auc_vs_normal | 0.9746 |
| lcl_extins.per_kind.lightgbm[11].flagged_share_at_5pct | 0.8214 |
| lcl_extins.per_kind.lightgbm[12].n | 35 |
| lcl_extins.per_kind.lightgbm[12].roc_auc_vs_normal | 0.9146 |
| lcl_extins.per_kind.lightgbm[12].flagged_share_at_5pct | 0.5714 |
| lcl_extins.per_kind.lightgbm[13].n | 21 |
| lcl_extins.per_kind.lightgbm[13].roc_auc_vs_normal | 0.849 |
| lcl_extins.per_kind.lightgbm[13].flagged_share_at_5pct | 0.2381 |
| lcl_extins.per_kind.lightgbm[14].n | 33 |
| lcl_extins.per_kind.lightgbm[14].roc_auc_vs_normal | 0.905 |
| lcl_extins.per_kind.lightgbm[14].flagged_share_at_5pct | 0.4848 |
| lcl_extins.per_kind.lightgbm[15].n | 255 |
| lcl_extins.per_kind.lightgbm[15].roc_auc_vs_normal | 0.4888 |
| lcl_extins.per_kind.lightgbm[15].flagged_share_at_5pct | 0.0157 |
| lcl_extins.per_kind.lightgbm[16].n | 241 |
| lcl_extins.per_kind.lightgbm[16].roc_auc_vs_normal | 0.6481 |
| lcl_extins.per_kind.lightgbm[16].flagged_share_at_5pct | 0.1494 |
| lcl_extins.per_kind.catboost[0].n | 55 |
| lcl_extins.per_kind.catboost[0].roc_auc_vs_normal | 0.9996 |
| lcl_extins.per_kind.catboost[0].flagged_share_at_5pct | 1 |
| lcl_extins.per_kind.catboost[1].n | 62 |
| lcl_extins.per_kind.catboost[1].roc_auc_vs_normal | 0.9996 |
| lcl_extins.per_kind.catboost[1].flagged_share_at_5pct | 0.9839 |
| lcl_extins.per_kind.catboost[2].n | 45 |
| lcl_extins.per_kind.catboost[2].roc_auc_vs_normal | 0.9978 |
| lcl_extins.per_kind.catboost[2].flagged_share_at_5pct | 0.9778 |
| lcl_extins.per_kind.catboost[3].n | 60 |
| lcl_extins.per_kind.catboost[3].roc_auc_vs_normal | 0.9483 |
| lcl_extins.per_kind.catboost[3].flagged_share_at_5pct | 0.7667 |
| lcl_extins.per_kind.catboost[4].n | 54 |
| lcl_extins.per_kind.catboost[4].roc_auc_vs_normal | 0.6268 |
| lcl_extins.per_kind.catboost[4].flagged_share_at_5pct | 0.1111 |
| lcl_extins.per_kind.catboost[5].n | 53 |
| lcl_extins.per_kind.catboost[5].roc_auc_vs_normal | 0.9993 |
| lcl_extins.per_kind.catboost[5].flagged_share_at_5pct | 1 |
| lcl_extins.per_kind.catboost[6].n | 54 |
| lcl_extins.per_kind.catboost[6].roc_auc_vs_normal | 0.8221 |
| lcl_extins.per_kind.catboost[6].flagged_share_at_5pct | 0.2037 |
| lcl_extins.per_kind.catboost[7].n | 30 |
| lcl_extins.per_kind.catboost[7].roc_auc_vs_normal | 0.938 |
| lcl_extins.per_kind.catboost[7].flagged_share_at_5pct | 0.4 |
| lcl_extins.per_kind.catboost[8].n | 18 |
| lcl_extins.per_kind.catboost[8].roc_auc_vs_normal | 0.9128 |
| lcl_extins.per_kind.catboost[8].flagged_share_at_5pct | 0.7778 |
| lcl_extins.per_kind.catboost[9].n | 24 |
| lcl_extins.per_kind.catboost[9].roc_auc_vs_normal | 0.9923 |
| lcl_extins.per_kind.catboost[9].flagged_share_at_5pct | 0.875 |
| lcl_extins.per_kind.catboost[10].n | 25 |
| lcl_extins.per_kind.catboost[10].roc_auc_vs_normal | 0.9732 |
| lcl_extins.per_kind.catboost[10].flagged_share_at_5pct | 0.8 |
| lcl_extins.per_kind.catboost[11].n | 28 |
| lcl_extins.per_kind.catboost[11].roc_auc_vs_normal | 0.9717 |
| lcl_extins.per_kind.catboost[11].flagged_share_at_5pct | 0.8571 |
| lcl_extins.per_kind.catboost[12].n | 35 |
| lcl_extins.per_kind.catboost[12].roc_auc_vs_normal | 0.9141 |
| lcl_extins.per_kind.catboost[12].flagged_share_at_5pct | 0.5143 |
| lcl_extins.per_kind.catboost[13].n | 21 |
| lcl_extins.per_kind.catboost[13].roc_auc_vs_normal | 0.8408 |
| lcl_extins.per_kind.catboost[13].flagged_share_at_5pct | 0.1905 |
| lcl_extins.per_kind.catboost[14].n | 33 |
| lcl_extins.per_kind.catboost[14].roc_auc_vs_normal | 0.8988 |
| lcl_extins.per_kind.catboost[14].flagged_share_at_5pct | 0.4545 |
| lcl_extins.per_kind.catboost[15].n | 255 |
| lcl_extins.per_kind.catboost[15].roc_auc_vs_normal | 0.5298 |
| lcl_extins.per_kind.catboost[15].flagged_share_at_5pct | 0.0196 |
| lcl_extins.per_kind.catboost[16].n | 241 |
| lcl_extins.per_kind.catboost[16].roc_auc_vs_normal | 0.6596 |
| lcl_extins.per_kind.catboost[16].flagged_share_at_5pct | 0.166 |
| lcl_extins.seconds | 130.6 |
| lcl_extins.reference_check.reproduced.subtle_precision_at_k | 0.89062 |
| lcl_extins.reference_check.reproduced.subtle_pr_auc | 0.5175 |
| lcl_extins.reference_check.reproduced.pr_auc | 0.73441 |
| seconds_total | 220.9 |

</details>

<details><summary>reports/benchmark/furtuni.json</summary>

[Sursa](../../reports/benchmark/furtuni.json) · SHA256 `cfd075cc1e4642bbae87b5b25493b215c18b10d0cf4a0bf9999e6588405464de`

| Câmp | Valoare |
|---|---:|
| monotone_constraints.gust_max | 1 |
| monotone_constraints.wind_max | 1 |
| monotone_constraints.gust_prev | 1 |
| monotone_constraints.gust_max_2d | 1 |
| monotone_constraints.precip | 1 |
| monotone_constraints.precip_48h | 1 |
| monotone_constraints.precip_7d | 1 |
| monotone_constraints.precip_hours | 0 |
| monotone_constraints.snow | 1 |
| monotone_constraints.snow_3d | 1 |
| monotone_constraints.ice_proxy | 1 |
| monotone_constraints.doy_sin | 0 |
| monotone_constraints.doy_cos | 0 |
| monotone_constraints.log_customers | 0 |
| monotone_constraints.log_density | 0 |
| xgboost_grid[0].max_depth | 4 |
| xgboost_grid[0].min_child_weight | 4 |
| xgboost_grid[0].learning_rate | 0.04 |
| xgboost_grid[0].rounds | 300 |
| xgboost_grid[0].oof_pr_auc | 0.2905 |
| xgboost_grid[0].oof_brier | 0.078 |
| xgboost_grid[1].max_depth | 4 |
| xgboost_grid[1].min_child_weight | 10 |
| xgboost_grid[1].learning_rate | 0.04 |
| xgboost_grid[1].rounds | 300 |
| xgboost_grid[1].oof_pr_auc | 0.2901 |
| xgboost_grid[1].oof_brier | 0.078 |
| xgboost_grid[2].max_depth | 5 |
| xgboost_grid[2].min_child_weight | 4 |
| xgboost_grid[2].learning_rate | 0.02 |
| xgboost_grid[2].rounds | 600 |
| xgboost_grid[2].oof_pr_auc | 0.2901 |
| xgboost_grid[2].oof_brier | 0.0781 |
| xgboost_grid[3].max_depth | 5 |
| xgboost_grid[3].min_child_weight | 4 |
| xgboost_grid[3].learning_rate | 0.02 |
| xgboost_grid[3].rounds | 300 |
| xgboost_grid[3].oof_pr_auc | 0.29 |
| xgboost_grid[3].oof_brier | 0.0781 |
| xgboost_grid[4].max_depth | 5 |
| xgboost_grid[4].min_child_weight | 4 |
| xgboost_grid[4].learning_rate | 0.04 |
| xgboost_grid[4].rounds | 300 |
| xgboost_grid[4].oof_pr_auc | 0.2898 |
| xgboost_grid[4].oof_brier | 0.0781 |
| xgboost_grid[5].max_depth | 4 |
| xgboost_grid[5].min_child_weight | 4 |
| xgboost_grid[5].learning_rate | 0.02 |
| xgboost_grid[5].rounds | 600 |
| xgboost_grid[5].oof_pr_auc | 0.2896 |
| xgboost_grid[5].oof_brier | 0.0781 |
| xgboost_grid[6].max_depth | 3 |
| xgboost_grid[6].min_child_weight | 4 |
| xgboost_grid[6].learning_rate | 0.02 |
| xgboost_grid[6].rounds | 600 |
| xgboost_grid[6].oof_pr_auc | 0.289 |
| xgboost_grid[6].oof_brier | 0.0781 |
| xgboost_grid[7].max_depth | 5 |
| xgboost_grid[7].min_child_weight | 10 |
| xgboost_grid[7].learning_rate | 0.02 |
| xgboost_grid[7].rounds | 300 |
| xgboost_grid[7].oof_pr_auc | 0.2889 |
| xgboost_grid[7].oof_brier | 0.0781 |
| xgboost_grid[8].max_depth | 5 |
| xgboost_grid[8].min_child_weight | 10 |
| xgboost_grid[8].learning_rate | 0.02 |
| xgboost_grid[8].rounds | 600 |
| xgboost_grid[8].oof_pr_auc | 0.2889 |
| xgboost_grid[8].oof_brier | 0.0781 |
| xgboost_grid[9].max_depth | 4 |
| xgboost_grid[9].min_child_weight | 10 |
| xgboost_grid[9].learning_rate | 0.02 |
| xgboost_grid[9].rounds | 600 |
| xgboost_grid[9].oof_pr_auc | 0.2885 |
| xgboost_grid[9].oof_brier | 0.0781 |
| xgboost_grid[10].max_depth | 5 |
| xgboost_grid[10].min_child_weight | 10 |
| xgboost_grid[10].learning_rate | 0.04 |
| xgboost_grid[10].rounds | 300 |
| xgboost_grid[10].oof_pr_auc | 0.2884 |
| xgboost_grid[10].oof_brier | 0.0782 |
| xgboost_grid[11].max_depth | 3 |
| xgboost_grid[11].min_child_weight | 4 |
| xgboost_grid[11].learning_rate | 0.04 |
| xgboost_grid[11].rounds | 300 |
| xgboost_grid[11].oof_pr_auc | 0.2879 |
| xgboost_grid[11].oof_brier | 0.0782 |
| xgboost_grid[12].max_depth | 3 |
| xgboost_grid[12].min_child_weight | 4 |
| xgboost_grid[12].learning_rate | 0.04 |
| xgboost_grid[12].rounds | 600 |
| xgboost_grid[12].oof_pr_auc | 0.2879 |
| xgboost_grid[12].oof_brier | 0.0782 |
| xgboost_grid[13].max_depth | 3 |
| xgboost_grid[13].min_child_weight | 10 |
| xgboost_grid[13].learning_rate | 0.02 |
| xgboost_grid[13].rounds | 600 |
| xgboost_grid[13].oof_pr_auc | 0.2879 |
| xgboost_grid[13].oof_brier | 0.0782 |
| xgboost_grid[14].max_depth | 3 |
| xgboost_grid[14].min_child_weight | 10 |
| xgboost_grid[14].learning_rate | 0.04 |
| xgboost_grid[14].rounds | 300 |
| xgboost_grid[14].oof_pr_auc | 0.2874 |
| xgboost_grid[14].oof_brier | 0.0782 |
| xgboost_grid[15].max_depth | 3 |
| xgboost_grid[15].min_child_weight | 10 |
| xgboost_grid[15].learning_rate | 0.04 |
| xgboost_grid[15].rounds | 600 |
| xgboost_grid[15].oof_pr_auc | 0.2866 |
| xgboost_grid[15].oof_brier | 0.0783 |
| xgboost_grid[16].max_depth | 4 |
| xgboost_grid[16].min_child_weight | 4 |
| xgboost_grid[16].learning_rate | 0.02 |
| xgboost_grid[16].rounds | 300 |
| xgboost_grid[16].oof_pr_auc | 0.2862 |
| xgboost_grid[16].oof_brier | 0.0783 |
| xgboost_grid[17].max_depth | 4 |
| xgboost_grid[17].min_child_weight | 4 |
| xgboost_grid[17].learning_rate | 0.04 |
| xgboost_grid[17].rounds | 600 |
| xgboost_grid[17].oof_pr_auc | 0.2862 |
| xgboost_grid[17].oof_brier | 0.0785 |
| xgboost_grid[18].max_depth | 4 |
| xgboost_grid[18].min_child_weight | 10 |
| xgboost_grid[18].learning_rate | 0.02 |
| xgboost_grid[18].rounds | 300 |
| xgboost_grid[18].oof_pr_auc | 0.286 |
| xgboost_grid[18].oof_brier | 0.0783 |
| xgboost_grid[19].max_depth | 4 |
| xgboost_grid[19].min_child_weight | 10 |
| xgboost_grid[19].learning_rate | 0.04 |
| xgboost_grid[19].rounds | 600 |
| xgboost_grid[19].oof_pr_auc | 0.2859 |
| xgboost_grid[19].oof_brier | 0.0785 |
| xgboost_grid[20].max_depth | 5 |
| xgboost_grid[20].min_child_weight | 4 |
| xgboost_grid[20].learning_rate | 0.04 |
| xgboost_grid[20].rounds | 600 |
| xgboost_grid[20].oof_pr_auc | 0.2831 |
| xgboost_grid[20].oof_brier | 0.079 |
| xgboost_grid[21].max_depth | 3 |
| xgboost_grid[21].min_child_weight | 4 |
| xgboost_grid[21].learning_rate | 0.02 |
| xgboost_grid[21].rounds | 300 |
| xgboost_grid[21].oof_pr_auc | 0.2821 |
| xgboost_grid[21].oof_brier | 0.0786 |
| xgboost_grid[22].max_depth | 3 |
| xgboost_grid[22].min_child_weight | 10 |
| xgboost_grid[22].learning_rate | 0.02 |
| xgboost_grid[22].rounds | 300 |
| xgboost_grid[22].oof_pr_auc | 0.282 |
| xgboost_grid[22].oof_brier | 0.0786 |
| xgboost_grid[23].max_depth | 5 |
| xgboost_grid[23].min_child_weight | 10 |
| xgboost_grid[23].learning_rate | 0.04 |
| xgboost_grid[23].rounds | 600 |
| xgboost_grid[23].oof_pr_auc | 0.281 |
| xgboost_grid[23].oof_brier | 0.079 |
| reference_check.report.pr_auc | 0.2777 |
| reference_check.report.brier | 0.0841 |
| reference_check.report.capacity_customers_covered | 0.1671 |
| reference_check.reproduced.pr_auc | 0.2777 |
| reference_check.reproduced.brier | 0.0841 |
| reference_check.reproduced.capacity_customers_covered | 0.1671 |
| test_2025.lightgbm.pr_auc | 0.277674 |
| test_2025.lightgbm.roc_auc | 0.72455 |
| test_2025.lightgbm.brier | 0.0841109 |
| test_2025.lightgbm.log_loss | 0.297036 |
| test_2025.lightgbm.threshold | 0.16 |
| test_2025.lightgbm.precision_at_thr | 0.280263 |
| test_2025.lightgbm.recall_at_thr | 0.409423 |
| test_2025.lightgbm.recall_severe_at_thr | 0.497689 |
| test_2025.lightgbm.recall_extreme_at_thr | 0.541667 |
| test_2025.lightgbm.alerts_per_100_zone_days | 15.0788 |
| test_2025.lightgbm.f1_at_thr | 0.332749 |
| test_2025.xgboost.pr_auc | 0.273816 |
| test_2025.xgboost.roc_auc | 0.723568 |
| test_2025.xgboost.brier | 0.0843366 |
| test_2025.xgboost.log_loss | 0.297587 |
| test_2025.xgboost.threshold | 0.14 |
| test_2025.xgboost.precision_at_thr | 0.277168 |
| test_2025.xgboost.recall_at_thr | 0.427339 |
| test_2025.xgboost.recall_severe_at_thr | 0.508475 |
| test_2025.xgboost.recall_extreme_at_thr | 0.556818 |
| test_2025.xgboost.alerts_per_100_zone_days | 15.9144 |
| test_2025.xgboost.f1_at_thr | 0.336249 |
| test_2025.capacity.k_crews_per_day | 8 |
| test_2025.capacity.zones | 80 |
| test_2025.capacity.results.lightgbm.customers_covered_share | 0.1671 |
| test_2025.capacity.results.lightgbm.events_caught_share | 0.2153 |
| test_2025.capacity.results.lightgbm.alert_precision | 0.2223 |
| test_2025.capacity.results.xgboost.customers_covered_share | 0.1654 |
| test_2025.capacity.results.xgboost.events_caught_share | 0.2143 |
| test_2025.capacity.results.xgboost.alert_precision | 0.2212 |
| test_2025.capacity.results.aleator.customers_covered_share | 0.0763 |
| test_2025.capacity.results.aleator.events_caught_share | 0.0946 |
| test_2025.capacity.results.aleator.alert_precision | 0.0976 |
| test_2025.capacity.results.oracol.customers_covered_share | 0.8855 |
| test_2025.capacity.results.oracol.events_caught_share | 0.7157 |
| test_2025.capacity.results.oracol.alert_precision | 0.7387 |
| test_2025.delta_xgboost_minus_lightgbm.pr_auc.delta | -0.00386 |
| test_2025.delta_xgboost_minus_lightgbm.pr_auc.ci90 | [-0.00641, -0.00117] |
| test_2025.delta_xgboost_minus_lightgbm.pr_auc.share_positive | 0.011 |
| test_2025.delta_xgboost_minus_lightgbm.pr_auc.groups | 53 |
| test_2025.delta_xgboost_minus_lightgbm.pr_auc.n_boot | 1000 |
| test_2025.delta_xgboost_minus_lightgbm.brier.delta | 0.00023 |
| test_2025.delta_xgboost_minus_lightgbm.brier.ci90 | [3e-05, 0.00043] |
| test_2025.delta_xgboost_minus_lightgbm.brier.share_positive | 0.965 |
| test_2025.delta_xgboost_minus_lightgbm.brier.groups | 53 |
| test_2025.delta_xgboost_minus_lightgbm.brier.n_boot | 1000 |
| test_2025.delta_xgboost_minus_lightgbm.customers_covered_share.delta | -0.00176 |
| test_2025.delta_xgboost_minus_lightgbm.customers_covered_share.ci90 | [-0.01212, 0.00805] |
| test_2025.delta_xgboost_minus_lightgbm.customers_covered_share.share_positive | 0.401 |
| test_2025.delta_xgboost_minus_lightgbm.customers_covered_share.groups | 53 |
| test_2025.delta_xgboost_minus_lightgbm.customers_covered_share.n_boot | 1000 |
| test_2025.oof_pr_auc_train.lightgbm | 0.2916 |
| test_2025.oof_pr_auc_train.xgboost | 0.2905 |
| test_2025.thresholds_from_train_oof.lightgbm | 0.16 |
| test_2025.thresholds_from_train_oof.xgboost | 0.14 |
| test_2025.test_rows | 29200 |
| test_2025.test_events | 3014 |
| test_2025.train_rows | 58480 |
| unseen_states.per_state.IL.events | 238 |
| unseen_states.per_state.IL.prevalence | 0.0652 |
| unseen_states.per_state.IL.lightgbm_pr_auc | 0.20622 |
| unseen_states.per_state.IL.xgboost_pr_auc | 0.21415 |
| unseen_states.per_state.IL.lightgbm_brier | 0.05831 |
| unseen_states.per_state.IL.xgboost_brier | 0.05779 |
| unseen_states.per_state.KY.events | 454 |
| unseen_states.per_state.KY.prevalence | 0.1244 |
| unseen_states.per_state.KY.lightgbm_pr_auc | 0.26578 |
| unseen_states.per_state.KY.xgboost_pr_auc | 0.27308 |
| unseen_states.per_state.KY.lightgbm_brier | 0.10251 |
| unseen_states.per_state.KY.xgboost_brier | 0.10196 |
| unseen_states.per_state.MI.events | 372 |
| unseen_states.per_state.MI.prevalence | 0.1019 |
| unseen_states.per_state.MI.lightgbm_pr_auc | 0.2727 |
| unseen_states.per_state.MI.xgboost_pr_auc | 0.26252 |
| unseen_states.per_state.MI.lightgbm_brier | 0.08373 |
| unseen_states.per_state.MI.xgboost_brier | 0.08409 |
| unseen_states.per_state.MO.events | 353 |
| unseen_states.per_state.MO.prevalence | 0.0967 |
| unseen_states.per_state.MO.lightgbm_pr_auc | 0.23215 |
| unseen_states.per_state.MO.xgboost_pr_auc | 0.22741 |
| unseen_states.per_state.MO.lightgbm_brier | 0.08227 |
| unseen_states.per_state.MO.xgboost_brier | 0.08265 |
| unseen_states.per_state.NY.events | 273 |
| unseen_states.per_state.NY.prevalence | 0.0748 |
| unseen_states.per_state.NY.lightgbm_pr_auc | 0.23679 |
| unseen_states.per_state.NY.xgboost_pr_auc | 0.24373 |
| unseen_states.per_state.NY.lightgbm_brier | 0.06814 |
| unseen_states.per_state.NY.xgboost_brier | 0.06879 |
| unseen_states.per_state.OH.events | 363 |
| unseen_states.per_state.OH.prevalence | 0.0995 |
| unseen_states.per_state.OH.lightgbm_pr_auc | 0.24433 |
| unseen_states.per_state.OH.xgboost_pr_auc | 0.23612 |
| unseen_states.per_state.OH.lightgbm_brier | 0.08403 |
| unseen_states.per_state.OH.xgboost_brier | 0.08429 |
| unseen_states.per_state.PA.events | 470 |
| unseen_states.per_state.PA.prevalence | 0.1288 |
| unseen_states.per_state.PA.lightgbm_pr_auc | 0.28544 |
| unseen_states.per_state.PA.xgboost_pr_auc | 0.2697 |
| unseen_states.per_state.PA.lightgbm_brier | 0.10484 |
| unseen_states.per_state.PA.xgboost_brier | 0.10566 |
| unseen_states.per_state.VA.events | 491 |
| unseen_states.per_state.VA.prevalence | 0.1345 |
| unseen_states.per_state.VA.lightgbm_pr_auc | 0.32548 |
| unseen_states.per_state.VA.xgboost_pr_auc | 0.31359 |
| unseen_states.per_state.VA.lightgbm_brier | 0.10806 |
| unseen_states.per_state.VA.xgboost_brier | 0.10845 |
| unseen_states.states | 8 |
| unseen_states.lightgbm_pr_auc_mean | 0.25861 |
| unseen_states.xgboost_pr_auc_mean | 0.25504 |
| unseen_states.states_xgboost_better | 3 |
| unseen_states.delta_mean_pr_auc.delta | -0.00357 |
| unseen_states.delta_mean_pr_auc.ci90 | [-0.00765, 0.00018] |
| unseen_states.delta_mean_pr_auc.share_positive | 0.06 |
| unseen_states.delta_mean_pr_auc.groups | 53 |
| unseen_states.delta_mean_pr_auc.n_boot | 500 |
| unseen_states.reference_report_lightgbm_pr_auc_mean | 0.2586 |
| convection_experiment.train_years | [2023, 2024] |
| convection_experiment.test_rows | 29200 |
| convection_experiment.with_convection.lightgbm.pr_auc | 0.286529 |
| convection_experiment.with_convection.lightgbm.roc_auc | 0.732091 |
| convection_experiment.with_convection.lightgbm.brier | 0.0835305 |
| convection_experiment.with_convection.lightgbm.log_loss | 0.295024 |
| convection_experiment.with_convection.lightgbm.threshold | 0.15 |
| convection_experiment.with_convection.lightgbm.precision_at_thr | 0.276472 |
| convection_experiment.with_convection.lightgbm.recall_at_thr | 0.440942 |
| convection_experiment.with_convection.lightgbm.recall_severe_at_thr | 0.530046 |
| convection_experiment.with_convection.lightgbm.recall_extreme_at_thr | 0.575758 |
| convection_experiment.with_convection.lightgbm.alerts_per_100_zone_days | 16.4623 |
| convection_experiment.with_convection.lightgbm.f1_at_thr | 0.339854 |
| convection_experiment.with_convection.xgboost.pr_auc | 0.284451 |
| convection_experiment.with_convection.xgboost.roc_auc | 0.72963 |
| convection_experiment.with_convection.xgboost.brier | 0.0836592 |
| convection_experiment.with_convection.xgboost.log_loss | 0.295534 |
| convection_experiment.with_convection.xgboost.threshold | 0.17 |
| convection_experiment.with_convection.xgboost.precision_at_thr | 0.279039 |
| convection_experiment.with_convection.xgboost.recall_at_thr | 0.42004 |
| convection_experiment.with_convection.xgboost.recall_severe_at_thr | 0.497689 |
| convection_experiment.with_convection.xgboost.recall_extreme_at_thr | 0.534091 |
| convection_experiment.with_convection.xgboost.alerts_per_100_zone_days | 15.5377 |
| convection_experiment.with_convection.xgboost.f1_at_thr | 0.33532 |
| convection_experiment.with_convection.capacity.k_crews_per_day | 8 |
| convection_experiment.with_convection.capacity.zones | 80 |
| convection_experiment.with_convection.capacity.results.lightgbm.customers_covered_share | 0.1791 |
| convection_experiment.with_convection.capacity.results.lightgbm.events_caught_share | 0.2196 |
| convection_experiment.with_convection.capacity.results.lightgbm.alert_precision | 0.2267 |
| convection_experiment.with_convection.capacity.results.xgboost.customers_covered_share | 0.1804 |
| convection_experiment.with_convection.capacity.results.xgboost.events_caught_share | 0.221 |
| convection_experiment.with_convection.capacity.results.xgboost.alert_precision | 0.2281 |
| convection_experiment.with_convection.capacity.results.aleator.customers_covered_share | 0.0763 |
| convection_experiment.with_convection.capacity.results.aleator.events_caught_share | 0.0946 |
| convection_experiment.with_convection.capacity.results.aleator.alert_precision | 0.0976 |
| convection_experiment.with_convection.capacity.results.oracol.customers_covered_share | 0.8855 |
| convection_experiment.with_convection.capacity.results.oracol.events_caught_share | 0.7157 |
| convection_experiment.with_convection.capacity.results.oracol.alert_precision | 0.7387 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.pr_auc.delta | -0.00208 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.pr_auc.ci90 | [-0.00473, 0.00052] |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.pr_auc.share_positive | 0.092 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.pr_auc.groups | 53 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.pr_auc.n_boot | 1000 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.brier.delta | 0.00013 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.brier.ci90 | [-3e-05, 0.00028] |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.brier.share_positive | 0.908 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.brier.groups | 53 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.brier.n_boot | 1000 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.customers_covered_share.delta | 0.00125 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.customers_covered_share.ci90 | [-0.00885, 0.01243] |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.customers_covered_share.share_positive | 0.511 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.customers_covered_share.groups | 53 |
| convection_experiment.with_convection.delta_xgboost_minus_lightgbm.customers_covered_share.n_boot | 1000 |
| convection_experiment.convection_gain_per_model.lightgbm.pr_auc_base | 0.27767 |
| convection_experiment.convection_gain_per_model.lightgbm.pr_auc_convection | 0.28653 |
| convection_experiment.convection_gain_per_model.lightgbm.delta.delta | 0.00885 |
| convection_experiment.convection_gain_per_model.lightgbm.delta.ci90 | [0.00249, 0.01568] |
| convection_experiment.convection_gain_per_model.lightgbm.delta.share_positive | 0.991 |
| convection_experiment.convection_gain_per_model.lightgbm.delta.groups | 53 |
| convection_experiment.convection_gain_per_model.lightgbm.delta.n_boot | 1000 |
| convection_experiment.convection_gain_per_model.xgboost.pr_auc_base | 0.27382 |
| convection_experiment.convection_gain_per_model.xgboost.pr_auc_convection | 0.28445 |
| convection_experiment.convection_gain_per_model.xgboost.delta.delta | 0.01063 |
| convection_experiment.convection_gain_per_model.xgboost.delta.ci90 | [0.00409, 0.01753] |
| convection_experiment.convection_gain_per_model.xgboost.delta.share_positive | 0.997 |
| convection_experiment.convection_gain_per_model.xgboost.delta.groups | 53 |
| convection_experiment.convection_gain_per_model.xgboost.delta.n_boot | 1000 |
| convection_experiment.reference_report.lightgbm_base | 0.2777 |
| convection_experiment.reference_report.lightgbm_convection | 0.2865 |
| seconds_total | 259.8 |

</details>

<details><summary>reports/benchmark/tensiune.json</summary>

[Sursa](../../reports/benchmark/tensiune.json) · SHA256 `b9784bf2d58c590e1fec93e11b472fc76f872ec68c6b76b5a6acb27b419983ea`

| Câmp | Valoare |
|---|---:|
| test_rows | 324000 |
| test.linear.mae_pu | 0.0227422 |
| test.linear.rmse_pu | 0.0276863 |
| test.linear.by_topology_mae.rural1 | 0.0199675 |
| test.linear.by_topology_mae.rural2 | 0.0269798 |
| test.linear.by_topology_mae.rural3 | 0.0254446 |
| test.linear.by_topology_mae.semiurb4 | 0.0215645 |
| test.linear.by_topology_mae.semiurb5 | 0.0213731 |
| test.linear.by_topology_mae.urban6 | 0.0211234 |
| test.linear.delta_mae_vs_lightgbm.delta | 0.01736 |
| test.linear.delta_mae_vs_lightgbm.ci90 | [0.01591, 0.01879] |
| test.linear.delta_mae_vs_lightgbm.share_positive | 1 |
| test.linear.delta_mae_vs_lightgbm.groups | 6 |
| test.linear.delta_mae_vs_lightgbm.n_boot | 1000 |
| test.lightgbm.mae_pu | 0.00538174 |
| test.lightgbm.rmse_pu | 0.00690474 |
| test.lightgbm.by_topology_mae.rural1 | 0.00451737 |
| test.lightgbm.by_topology_mae.rural2 | 0.00589672 |
| test.lightgbm.by_topology_mae.rural3 | 0.00630089 |
| test.lightgbm.by_topology_mae.semiurb4 | 0.00455755 |
| test.lightgbm.by_topology_mae.semiurb5 | 0.0063061 |
| test.lightgbm.by_topology_mae.urban6 | 0.0047118 |
| test.lightgbm.delta_mae_vs_lightgbm.delta | 0 |
| test.lightgbm.delta_mae_vs_lightgbm.ci90 | [0.0, 0.0] |
| test.lightgbm.delta_mae_vs_lightgbm.share_positive | 0 |
| test.lightgbm.delta_mae_vs_lightgbm.groups | 6 |
| test.lightgbm.delta_mae_vs_lightgbm.n_boot | 1000 |
| test.catboost.mae_pu | 0.00556105 |
| test.catboost.rmse_pu | 0.00722922 |
| test.catboost.by_topology_mae.rural1 | 0.0044724 |
| test.catboost.by_topology_mae.rural2 | 0.00663288 |
| test.catboost.by_topology_mae.rural3 | 0.00662407 |
| test.catboost.by_topology_mae.semiurb4 | 0.00476017 |
| test.catboost.by_topology_mae.semiurb5 | 0.00625293 |
| test.catboost.by_topology_mae.urban6 | 0.00462385 |
| test.catboost.delta_mae_vs_lightgbm.delta | 0.00018 |
| test.catboost.delta_mae_vs_lightgbm.ci90 | [-1e-05, 0.00038] |
| test.catboost.delta_mae_vs_lightgbm.share_positive | 0.931 |
| test.catboost.delta_mae_vs_lightgbm.groups | 6 |
| test.catboost.delta_mae_vs_lightgbm.n_boot | 1000 |
| test.xgboost.mae_pu | 0.00541758 |
| test.xgboost.rmse_pu | 0.00698067 |
| test.xgboost.by_topology_mae.rural1 | 0.00458193 |
| test.xgboost.by_topology_mae.rural2 | 0.00613854 |
| test.xgboost.by_topology_mae.rural3 | 0.00656256 |
| test.xgboost.by_topology_mae.semiurb4 | 0.00439361 |
| test.xgboost.by_topology_mae.semiurb5 | 0.0061993 |
| test.xgboost.by_topology_mae.urban6 | 0.00462951 |
| test.xgboost.delta_mae_vs_lightgbm.delta | 4e-05 |
| test.xgboost.delta_mae_vs_lightgbm.ci90 | [-8e-05, 0.00015] |
| test.xgboost.delta_mae_vs_lightgbm.share_positive | 0.676 |
| test.xgboost.delta_mae_vs_lightgbm.groups | 6 |
| test.xgboost.delta_mae_vs_lightgbm.n_boot | 1000 |

</details>

<details><summary>reports/benchmark/tensiune_reala.json</summary>

[Sursa](../../reports/benchmark/tensiune_reala.json) · SHA256 `2a9bb29d7c3872f0c57dfe6e9709305ed811a932ee77469482b8b6348925603e`

| Câmp | Valoare |
|---|---:|
| split.train.rows | 9869 |
| split.validation.rows | 736 |
| split.test.rows | 1353 |
| validation_mae_volts.persistence | 0.840165 |
| validation_mae_volts.mean_7d | 0.720032 |
| validation_mae_volts.ridge | 0.674835 |
| validation_mae_volts.lightgbm | 0.672164 |
| validation_mae_volts.catboost | 0.673622 |
| validation_mae_volts.xgboost | 0.668609 |
| test.persistence.mae_volts | 0.824814 |
| test.persistence.rmse_volts | 1.11324 |
| test.persistence.p95_absolute_error_volts | 2.3666 |
| test.persistence.delta_mae_vs_persistence_by_feeder.delta | 0 |
| test.persistence.delta_mae_vs_persistence_by_feeder.ci90 | [0.0, 0.0] |
| test.persistence.delta_mae_vs_persistence_by_feeder.share_positive | 0 |
| test.persistence.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.persistence.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.persistence.by_feeder_mae.2 | 0.988486 |
| test.persistence.by_feeder_mae.6 | 0.605338 |
| test.persistence.by_feeder_mae.8 | 0.73137 |
| test.persistence.by_feeder_mae.12 | 1.04598 |
| test.persistence.by_feeder_mae.25 | 0.622099 |
| test.persistence.by_feeder_mae.26 | 1.07037 |
| test.persistence.by_feeder_mae.34 | 1.04752 |
| test.persistence.by_feeder_mae.36 | 0.566763 |
| test.mean_7d.mae_volts | 0.731811 |
| test.mean_7d.rmse_volts | 0.965487 |
| test.mean_7d.p95_absolute_error_volts | 1.98157 |
| test.mean_7d.delta_mae_vs_persistence_by_feeder.delta | -0.093 |
| test.mean_7d.delta_mae_vs_persistence_by_feeder.ci90 | [-0.12356, -0.06362] |
| test.mean_7d.delta_mae_vs_persistence_by_feeder.share_positive | 0 |
| test.mean_7d.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.mean_7d.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.mean_7d.by_feeder_mae.2 | 0.905188 |
| test.mean_7d.by_feeder_mae.6 | 0.594911 |
| test.mean_7d.by_feeder_mae.8 | 0.639321 |
| test.mean_7d.by_feeder_mae.12 | 0.896029 |
| test.mean_7d.by_feeder_mae.25 | 0.539259 |
| test.mean_7d.by_feeder_mae.26 | 0.896523 |
| test.mean_7d.by_feeder_mae.34 | 0.935772 |
| test.mean_7d.by_feeder_mae.36 | 0.519527 |
| test.ridge.mae_volts | 0.688326 |
| test.ridge.rmse_volts | 0.918801 |
| test.ridge.p95_absolute_error_volts | 1.84618 |
| test.ridge.delta_mae_vs_persistence_by_feeder.delta | -0.13649 |
| test.ridge.delta_mae_vs_persistence_by_feeder.ci90 | [-0.16624, -0.10655] |
| test.ridge.delta_mae_vs_persistence_by_feeder.share_positive | 0 |
| test.ridge.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.ridge.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.ridge.by_feeder_mae.2 | 0.823342 |
| test.ridge.by_feeder_mae.6 | 0.558329 |
| test.ridge.by_feeder_mae.8 | 0.611438 |
| test.ridge.by_feeder_mae.12 | 0.8457 |
| test.ridge.by_feeder_mae.25 | 0.512187 |
| test.ridge.by_feeder_mae.26 | 0.88413 |
| test.ridge.by_feeder_mae.34 | 0.875416 |
| test.ridge.by_feeder_mae.36 | 0.462527 |
| test.lightgbm.mae_volts | 0.707201 |
| test.lightgbm.rmse_volts | 0.948888 |
| test.lightgbm.p95_absolute_error_volts | 1.89571 |
| test.lightgbm.delta_mae_vs_persistence_by_feeder.delta | -0.11761 |
| test.lightgbm.delta_mae_vs_persistence_by_feeder.ci90 | [-0.15853, -0.07857] |
| test.lightgbm.delta_mae_vs_persistence_by_feeder.share_positive | 0 |
| test.lightgbm.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.lightgbm.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.lightgbm.by_feeder_mae.2 | 0.802516 |
| test.lightgbm.by_feeder_mae.6 | 0.596972 |
| test.lightgbm.by_feeder_mae.8 | 0.678284 |
| test.lightgbm.by_feeder_mae.12 | 0.876532 |
| test.lightgbm.by_feeder_mae.25 | 0.553747 |
| test.lightgbm.by_feeder_mae.26 | 0.872479 |
| test.lightgbm.by_feeder_mae.34 | 0.909321 |
| test.lightgbm.by_feeder_mae.36 | 0.443984 |
| test.catboost.mae_volts | 0.715048 |
| test.catboost.rmse_volts | 0.956809 |
| test.catboost.p95_absolute_error_volts | 2.00668 |
| test.catboost.delta_mae_vs_persistence_by_feeder.delta | -0.10977 |
| test.catboost.delta_mae_vs_persistence_by_feeder.ci90 | [-0.15732, -0.06591] |
| test.catboost.delta_mae_vs_persistence_by_feeder.share_positive | 0 |
| test.catboost.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.catboost.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.catboost.by_feeder_mae.2 | 0.78857 |
| test.catboost.by_feeder_mae.6 | 0.59256 |
| test.catboost.by_feeder_mae.8 | 0.745443 |
| test.catboost.by_feeder_mae.12 | 0.861637 |
| test.catboost.by_feeder_mae.25 | 0.542108 |
| test.catboost.by_feeder_mae.26 | 0.872779 |
| test.catboost.by_feeder_mae.34 | 0.959771 |
| test.catboost.by_feeder_mae.36 | 0.453416 |
| test.xgboost.mae_volts | 0.724285 |
| test.xgboost.rmse_volts | 0.968599 |
| test.xgboost.p95_absolute_error_volts | 1.95562 |
| test.xgboost.delta_mae_vs_persistence_by_feeder.delta | -0.10053 |
| test.xgboost.delta_mae_vs_persistence_by_feeder.ci90 | [-0.15656, -0.04697] |
| test.xgboost.delta_mae_vs_persistence_by_feeder.share_positive | 0.003 |
| test.xgboost.delta_mae_vs_persistence_by_feeder.groups | 8 |
| test.xgboost.delta_mae_vs_persistence_by_feeder.n_boot | 1000 |
| test.xgboost.by_feeder_mae.2 | 0.809623 |
| test.xgboost.by_feeder_mae.6 | 0.609343 |
| test.xgboost.by_feeder_mae.8 | 0.810547 |
| test.xgboost.by_feeder_mae.12 | 0.893155 |
| test.xgboost.by_feeder_mae.25 | 0.53802 |
| test.xgboost.by_feeder_mae.26 | 0.85483 |
| test.xgboost.by_feeder_mae.34 | 0.930453 |
| test.xgboost.by_feeder_mae.36 | 0.42954 |
| test_days_above_253V | 0 |
| test_rows | 1353 |

</details>

<details><summary>data/samples/C/feederbw_voltage_daily.json</summary>

[Sursa](../../data/samples/C/feederbw_voltage_daily.json) · SHA256 `0a19973b3cfb4a9438b4f13b4429d7ef73d60770dcf89f86c64eadefa531101d`

| Câmp | Valoare |
|---|---:|
| quality.1.raw_rows | 1.05254e+06 |
| quality.1.invalid_rows | 0 |
| quality.1.duplicate_timestamps | 0 |
| quality.1.days | 732 |
| quality.1.accepted_days | 730 |
| quality.1.excluded_days | 2 |
| quality.2.raw_rows | 1.05245e+06 |
| quality.2.invalid_rows | 1 |
| quality.2.duplicate_timestamps | 0 |
| quality.2.days | 732 |
| quality.2.accepted_days | 730 |
| quality.2.excluded_days | 2 |
| quality.3.raw_rows | 1.05236e+06 |
| quality.3.invalid_rows | 0 |
| quality.3.duplicate_timestamps | 0 |
| quality.3.days | 732 |
| quality.3.accepted_days | 729 |
| quality.3.excluded_days | 3 |
| quality.4.raw_rows | 1.05237e+06 |
| quality.4.invalid_rows | 0 |
| quality.4.duplicate_timestamps | 0 |
| quality.4.days | 732 |
| quality.4.accepted_days | 729 |
| quality.4.excluded_days | 3 |
| quality.5.raw_rows | 1.05259e+06 |
| quality.5.invalid_rows | 1 |
| quality.5.duplicate_timestamps | 0 |
| quality.5.days | 732 |
| quality.5.accepted_days | 730 |
| quality.5.excluded_days | 2 |
| quality.6.raw_rows | 1.05162e+06 |
| quality.6.invalid_rows | 0 |
| quality.6.duplicate_timestamps | 0 |
| quality.6.days | 732 |
| quality.6.accepted_days | 727 |
| quality.6.excluded_days | 5 |
| quality.7.raw_rows | 1.05231e+06 |
| quality.7.invalid_rows | 2 |
| quality.7.duplicate_timestamps | 0 |
| quality.7.days | 732 |
| quality.7.accepted_days | 729 |
| quality.7.excluded_days | 3 |
| quality.8.raw_rows | 1.04724e+06 |
| quality.8.invalid_rows | 3 |
| quality.8.duplicate_timestamps | 0 |
| quality.8.days | 732 |
| quality.8.accepted_days | 723 |
| quality.8.excluded_days | 9 |
| quality.9.raw_rows | 1.04819e+06 |
| quality.9.invalid_rows | 1 |
| quality.9.duplicate_timestamps | 0 |
| quality.9.days | 732 |
| quality.9.accepted_days | 723 |
| quality.9.excluded_days | 9 |
| quality.10.raw_rows | 1.04533e+06 |
| quality.10.invalid_rows | 18 |
| quality.10.duplicate_timestamps | 0 |
| quality.10.days | 732 |
| quality.10.accepted_days | 721 |
| quality.10.excluded_days | 11 |
| quality.11.raw_rows | 1.05024e+06 |
| quality.11.invalid_rows | 3 |
| quality.11.duplicate_timestamps | 0 |
| quality.11.days | 732 |
| quality.11.accepted_days | 726 |
| quality.11.excluded_days | 6 |
| quality.12.raw_rows | 1.05252e+06 |
| quality.12.invalid_rows | 2 |
| quality.12.duplicate_timestamps | 0 |
| quality.12.days | 732 |
| quality.12.accepted_days | 730 |
| quality.12.excluded_days | 2 |
| quality.13.raw_rows | 1.04705e+06 |
| quality.13.invalid_rows | 2 |
| quality.13.duplicate_timestamps | 0 |
| quality.13.days | 732 |
| quality.13.accepted_days | 720 |
| quality.13.excluded_days | 12 |
| quality.14.raw_rows | 1.04705e+06 |
| quality.14.invalid_rows | 2 |
| quality.14.duplicate_timestamps | 0 |
| quality.14.days | 732 |
| quality.14.accepted_days | 720 |
| quality.14.excluded_days | 12 |
| quality.15.raw_rows | 1.05214e+06 |
| quality.15.invalid_rows | 6 |
| quality.15.duplicate_timestamps | 0 |
| quality.15.days | 732 |
| quality.15.accepted_days | 727 |
| quality.15.excluded_days | 5 |
| quality.16.raw_rows | 1.0515e+06 |
| quality.16.invalid_rows | 1 |
| quality.16.duplicate_timestamps | 0 |
| quality.16.days | 732 |
| quality.16.accepted_days | 727 |
| quality.16.excluded_days | 5 |
| quality.17.raw_rows | 1.05147e+06 |
| quality.17.invalid_rows | 1 |
| quality.17.duplicate_timestamps | 0 |
| quality.17.days | 732 |
| quality.17.accepted_days | 728 |
| quality.17.excluded_days | 4 |
| quality.18.raw_rows | 1.05225e+06 |
| quality.18.invalid_rows | 0 |
| quality.18.duplicate_timestamps | 0 |
| quality.18.days | 732 |
| quality.18.accepted_days | 729 |
| quality.18.excluded_days | 3 |
| quality.19.raw_rows | 1.0526e+06 |
| quality.19.invalid_rows | 0 |
| quality.19.duplicate_timestamps | 0 |
| quality.19.days | 732 |
| quality.19.accepted_days | 730 |
| quality.19.excluded_days | 2 |
| quality.20.raw_rows | 1.05029e+06 |
| quality.20.invalid_rows | 2 |
| quality.20.duplicate_timestamps | 0 |
| quality.20.days | 732 |
| quality.20.accepted_days | 723 |
| quality.20.excluded_days | 9 |
| quality.21.raw_rows | 1.0525e+06 |
| quality.21.invalid_rows | 1 |
| quality.21.duplicate_timestamps | 0 |
| quality.21.days | 732 |
| quality.21.accepted_days | 730 |
| quality.21.excluded_days | 2 |
| quality.22.raw_rows | 1.05147e+06 |
| quality.22.invalid_rows | 2 |
| quality.22.duplicate_timestamps | 0 |
| quality.22.days | 732 |
| quality.22.accepted_days | 727 |
| quality.22.excluded_days | 5 |
| quality.23.raw_rows | 1.048e+06 |
| quality.23.invalid_rows | 4 |
| quality.23.duplicate_timestamps | 0 |
| quality.23.days | 732 |
| quality.23.accepted_days | 724 |
| quality.23.excluded_days | 8 |
| quality.24.raw_rows | 1.03591e+06 |
| quality.24.invalid_rows | 6 |
| quality.24.duplicate_timestamps | 0 |
| quality.24.days | 732 |
| quality.24.accepted_days | 622 |
| quality.24.excluded_days | 110 |
| quality.25.raw_rows | 1.04794e+06 |
| quality.25.invalid_rows | 0 |
| quality.25.duplicate_timestamps | 0 |
| quality.25.days | 732 |
| quality.25.accepted_days | 724 |
| quality.25.excluded_days | 8 |
| quality.26.raw_rows | 1.05161e+06 |
| quality.26.invalid_rows | 1 |
| quality.26.duplicate_timestamps | 0 |
| quality.26.days | 732 |
| quality.26.accepted_days | 728 |
| quality.26.excluded_days | 4 |
| quality.27.raw_rows | 1.04548e+06 |
| quality.27.invalid_rows | 4 |
| quality.27.duplicate_timestamps | 0 |
| quality.27.days | 732 |
| quality.27.accepted_days | 714 |
| quality.27.excluded_days | 18 |
| quality.28.raw_rows | 1.0524e+06 |
| quality.28.invalid_rows | 6 |
| quality.28.duplicate_timestamps | 0 |
| quality.28.days | 732 |
| quality.28.accepted_days | 729 |
| quality.28.excluded_days | 3 |
| quality.29.raw_rows | 1.05242e+06 |
| quality.29.invalid_rows | 2 |
| quality.29.duplicate_timestamps | 0 |
| quality.29.days | 732 |
| quality.29.accepted_days | 730 |
| quality.29.excluded_days | 2 |
| quality.30.raw_rows | 1.04159e+06 |
| quality.30.invalid_rows | 54 |
| quality.30.duplicate_timestamps | 0 |
| quality.30.days | 732 |
| quality.30.accepted_days | 702 |
| quality.30.excluded_days | 30 |
| quality.31.raw_rows | 1.04143e+06 |
| quality.31.invalid_rows | 52 |
| quality.31.duplicate_timestamps | 0 |
| quality.31.days | 732 |
| quality.31.accepted_days | 702 |
| quality.31.excluded_days | 30 |
| quality.32.raw_rows | 1.05259e+06 |
| quality.32.invalid_rows | 0 |
| quality.32.duplicate_timestamps | 0 |
| quality.32.days | 732 |
| quality.32.accepted_days | 730 |
| quality.32.excluded_days | 2 |
| quality.33.raw_rows | 1.05233e+06 |
| quality.33.invalid_rows | 2 |
| quality.33.duplicate_timestamps | 0 |
| quality.33.days | 732 |
| quality.33.accepted_days | 730 |
| quality.33.excluded_days | 2 |
| quality.34.raw_rows | 972992 |
| quality.34.invalid_rows | 6 |
| quality.34.duplicate_timestamps | 0 |
| quality.34.days | 732 |
| quality.34.accepted_days | 348 |
| quality.34.excluded_days | 384 |
| quality.35.raw_rows | 1.05179e+06 |
| quality.35.invalid_rows | 5 |
| quality.35.duplicate_timestamps | 0 |
| quality.35.days | 732 |
| quality.35.accepted_days | 725 |
| quality.35.excluded_days | 7 |
| quality.36.raw_rows | 1.05219e+06 |
| quality.36.invalid_rows | 2 |
| quality.36.duplicate_timestamps | 0 |
| quality.36.days | 732 |
| quality.36.accepted_days | 729 |
| quality.36.excluded_days | 3 |
| quality.37.raw_rows | 1.05249e+06 |
| quality.37.invalid_rows | 2 |
| quality.37.duplicate_timestamps | 0 |
| quality.37.days | 732 |
| quality.37.accepted_days | 730 |
| quality.37.excluded_days | 2 |
| quality.38.raw_rows | 1.00036e+06 |
| quality.38.invalid_rows | 76 |
| quality.38.duplicate_timestamps | 0 |
| quality.38.days | 732 |
| quality.38.accepted_days | 433 |
| quality.38.excluded_days | 299 |
| quality.39.raw_rows | 1.05212e+06 |
| quality.39.invalid_rows | 0 |
| quality.39.duplicate_timestamps | 0 |
| quality.39.days | 732 |
| quality.39.accepted_days | 729 |
| quality.39.excluded_days | 3 |
| quality.40.raw_rows | 1.04031e+06 |
| quality.40.invalid_rows | 4 |
| quality.40.duplicate_timestamps | 0 |
| quality.40.days | 732 |
| quality.40.accepted_days | 699 |
| quality.40.excluded_days | 33 |

</details>

### Recalcularea predicțiilor

| Verificare | Raportat | Recalculat | OK |
|---|---:|---:|---|
| bilant_v2/lightgbm/macro_f1 | 0.753520 | 0.753521 | True |
| bilant_v2/catboost/macro_f1 | 0.757480 | 0.757477 | True |
| bilant_feederbw/lightgbm_tuned/macro_f1 | 0.713930 | 0.713931 | True |
| bilant_feederbw/catboost/macro_f1 | 0.704830 | 0.704825 | True |
| bilant_holdout/model/macro_f1 | 0.775395 | 0.775395 | True |
| bilant_holdout/baseline/macro_f1 | 0.420591 | 0.420591 | True |
| lcl_baza/full_test/lightgbm/pr_auc | 0.677850 | 0.677850 | True |
| lcl_baza/full_test/catboost/pr_auc | 0.677580 | 0.677581 | True |
| lcl_baza/subtle/lightgbm/pr_auc | 0.405730 | 0.405732 | True |
| lcl_baza/subtle/catboost/pr_auc | 0.417420 | 0.417418 | True |
| lcl_extins/full_test/lightgbm/pr_auc | 0.734410 | 0.734412 | True |
| lcl_extins/full_test/catboost/pr_auc | 0.718690 | 0.718694 | True |
| lcl_extins/subtle/lightgbm/pr_auc | 0.517500 | 0.517503 | True |
| lcl_extins/subtle/catboost/pr_auc | 0.488950 | 0.488953 | True |
| sgcc/lightgbm/pr_auc | 0.399420 | 0.399422 | True |
| sgcc/catboost/pr_auc | 0.394700 | 0.394702 | True |
| furtuni_test2025/lightgbm/pr_auc | 0.277674 | 0.277674 | True |
| furtuni_test2025/xgboost/pr_auc | 0.273816 | 0.273816 | True |
| furtuni_convectie_test/lightgbm/pr_auc | 0.286529 | 0.286529 | True |
| furtuni_convectie_test/xgboost/pr_auc | 0.284451 | 0.284451 | True |
| tensiune/linear/mae_pu | 0.022742 | 0.022742 | True |
| tensiune/lightgbm/mae_pu | 0.005382 | 0.005382 | True |
| tensiune/catboost/mae_pu | 0.005561 | 0.005561 | True |
| tensiune/xgboost/mae_pu | 0.005418 | 0.005418 | True |
| tensiune_reala/persistence/mae_volts | 0.824814 | 0.824814 | True |
| tensiune_reala/mean_7d/mae_volts | 0.731811 | 0.731811 | True |
| tensiune_reala/ridge/mae_volts | 0.688326 | 0.688326 | True |
| tensiune_reala/lightgbm/mae_volts | 0.707201 | 0.707201 | True |
| tensiune_reala/catboost/mae_volts | 0.715048 | 0.715048 | True |
| tensiune_reala/xgboost/mae_volts | 0.724285 | 0.724285 | True |
