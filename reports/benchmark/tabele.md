# Tabelele benchmarkului (generate)

Generat de `python -m cyberpunks.benchmark.report` din `reports/benchmark/*.json`. Diferențele sunt candidat − LightGBM, cu interval bootstrap 90% pe grupuri. „(include 0)” = diferența nu e sigură.

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

Bootstrap: cartierul postului de test (31 cartiere), 1000 de reeșantionări, 90%. Clase mai slabe la CatBoost: furt_inainte_contor, pierdere_tehnica; cu intervalul sub zero: niciuna. **Verdict CatBoost: la egalitate statistică.**

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

Bootstrap: plecarea reală de test (8 plecări), 1000 de reeșantionări, 90%. Clase mai slabe la CatBoost: normal, contor_client, furt_inainte_contor, pierdere_tehnica; cu intervalul sub zero: niciuna. **Verdict CatBoost: la egalitate statistică.**

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

Bootstrap: clientul (un rând pe client). **Verdict CatBoost: la egalitate statistică.**

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

Bootstrap: gospodăriile de test. **Verdict CatBoost: la egalitate statistică.**

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

Media pe 8 state: LightGBM 0,2586, XGBoost 0,2550; diferența medie -0,0036 [-0,0076; 0,0002] (include 0); XGBoost mai bun în 3 din 8 state. **Verdict XGBoost: la egalitate statistică.**

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

Referințe la același buget: aleator 0,0763, oracol 0,8855. Bootstrap pe săptămânile din 2025. **Verdict XGBoost: la egalitate statistică.**

Câștigul convecției, pe același test: LightGBM 0,0089 [0,0025; 0,0157], XGBoost 0,0106 [0,0041; 0,0175].

