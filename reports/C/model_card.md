# Fișa modelului C: tensiunea maximă pe posturile de transformare cu prosumatori

Echipa CyberPunks, SmartHack XI 2026 (tema PPC). Firul C. Toate datele de antrenare și de test sunt SINTETICE (rețele, prosumatori, etichete), vremea e reală.

## Ce face

Pentru fiecare post de transformare MT/JT și pentru ziua de mâine, estimează **tensiunea maximă din rețeaua de joasă tensiune** (P10, P50, P90, pe zi și oră cu oră) și **probabilitatea ca ea să treacă de 1,10 pu**, pragul la care invertoarele prosumatorilor se opresc (Ord. ANRE 228/2018 cu modificările din Ord. 132/2020, Tabelul 2P) și limita de 100% din standardul de performanță (Ord. ANRE 46/2021). Agentul transformă estimarea în lucrări pentru echipele Rețele Electrice și în mesaje sau oferte pentru prosumatori (PPC Energie).

De ce un model, nu calculul de rețea direct: Rețele Electrice are peste 26.000 de posturi, iar modelul detaliat al rețelei de joasă tensiune lipsește la cele mai multe (licitația pentru GIS-ul nou e din aprilie 2026). Modelul folosește doar ce există în GIS și în avizele de racordare (kVA, prosumatori, kW, baterii, lungimea și rezistența rețelei, priza) plus prognoza meteo. Pe 300 de posturi, o zi se estimează în 0,07-0,09 s, față de 62-87 s cu pandapower, care ar cere și rețeaua detaliată a fiecărui post.

## Versiunea

- `model_id`: `c-surrogate`; `model_version`: `c-lgbm@<commit>` (scris în fiecare lucrare și în `models/release/C/bundle.json`).
- Componente: LightGBM 4.7 regresie cuantilă (P10, P50, P90) pentru tensiunea maximă zilnică; LightGBM clasificator (constrângeri monotone) pentru P(> 1,10 pu), calibrat izotonic; lărgire conformală a intervalului, pe patru grupe de rețea; model pentru kWh pierduți; model orar (P10, P50, P90) pentru grafic, tot cu lărgire conformală.
- Antrenare: `make c-train` (circa 3 minute pe 4 nuclee). Ziua demo (2025-07-08) și cele 3 zile dinainte și de după sunt scoase din antrenare.

## Datele

- 480 de posturi sintetice, variante ale celor 6 rețele de joasă tensiune SimBench (ODbL): transformator 100-630 kVA, cinci tipuri de conductor, linii de 0,6-2 ori mai lungi, priza −2..+2, prosumatori 3-15 kWp (media circa 6,8 kW, apropiată de 6,4 kW pe gospodărie după ANRE), baterii la circa 35% dintre ei.
- Vremea reală, orară, la București-Ilfov: Open-Meteo (ERA5), 2023-01-01 → 2026-11-06. Consumul din profilele SimBench, pe calendarul românesc.
- Etichetele: circulație de puteri orară pentru fiecare post (pandapower 3.5.6 construiește rețeaua; un calcul vectorizat pe matricea lui dă aceleași tensiuni, cu diferență sub 1e-7 pu, `make c-bench`). Inclusiv cascada de opriri a invertoarelor.
- 674.880 de zile-post de antrenare și test; 8,1% dintre ele trec de 1,10 pu.
- Detalii și surse: `docs/data/C.md`, `docs/research/C.md`.

## Evaluarea

Test pe **rețele nevăzute** (leave-one-topology-out pe cele 6 topologii) și **luni nevăzute** (antrenare înainte de 2025-01-01, test 2025-01-01 → 2026-11-06): 324.000 de zile-post. Comanda: `make c-eval` (sau `uv run python -m cyberpunks.c_prosumatori.evaluate`). Rezultatul: `reports/C/metrics.json` (contractul `ModelReport`) și `metrics_detail.json`.

| Metrica | Model | Baseline (regresie liniară pe soare × kW/kVA) |
|---|---|---|
| MAE tensiune maximă (pu) | **0,0054** | 0,0227 |
| RMSE (pu) | 0,0070 | 0,0277 |
| Acoperirea intervalului P10-P90 (ținta 80%) | **82,1%** | 78,8% (de 4 ori mai lat) |
| Lățimea medie a intervalului (pu) | 0,018 | 0,069 |
| PR-AUC depășiri peste 1,10 pu | **0,951** | 0,428 |
| Recall / precizie la pragul 0,5 | 86,5% / 86,9% | 25,6% / 60,5% |
| Brier | 0,015 | 0,058 |
| Eroarea de calibrare (ECE) | 0,003 | 0,013 |

- Pe topologii: MAE între 0,0044 și 0,0064 pu (baseline 0,0200-0,0269). Reper din literatură, pe aceleași 6 rețele, leave-one-grid-out: RMSE 0,0134 pu pe noduri (BOOST-RPF, arXiv:2603.21977; altă sarcină, același ordin de mărime).
- Modelul orar (seria din grafic): MAE 0,0049 pu, acoperire P10-P90 79,7% după lărgirea conformală calibrată doar pe perioada de antrenare (49,8% înainte).
- Backtest pe ziua demo (8 iulie 2025, populația de 300 de posturi): simularea fizică dă 16 posturi peste 1,10 pu; modelul le dă probabilitate peste 50% tuturor celor 16, plus 2 posturi aflate la 1,097 pu. MAE în ziua aceea: 0,0052 pu.
- Ablații (aceeași evaluare): fără trăsăturile fizice din topologie, MAE 0,0119 pu și PR-AUC 0,384 (sub baseline); fără tensiunea de pornire și priză, MAE 0,0205 pu. Modelul are nevoie de topologia din GIS și de priza fiecărui post.
- Analiza erorilor: `reports/C/error_analysis.md`.

## Explicabilitatea

Fiecare lucrare are 3-5 motive din contribuțiile SHAP ale modelului P50 (TreeSHAP), grupate și spuse simplu, cu cifrele postului (de exemplu „315 kW de panouri pe un transformator de 250 kVA (44 prosumatori)”, „soare 956 W/m² pe panou la prânz”), cazuri similare din simulare și o frază din șablon. Pentru fiecare post cu depășire, scara de soluții arată efectul simulat al fiecărei măsuri și de ce nu s-a ales una mai ieftină.

## Robustețe

- Intrări greșite (kVA zero sau lipsă, puteri negative, mai mulți prosumatori decât clienți, priză imposibilă, coordonate în afara zonei): lucrare cu `abstain` și motiv, trimisă la om (`C-R1-INTRARE-GRESITA`). Bateria lipsă e considerată 0 și notată.
- Rețele în afara plajei de antrenare (de exemplu mai mulți kW pe kVA decât s-a văzut): `abstain`, `C-R2-RETEA-NOUA`.
- Prognoză nesigură (nori variabili) cu intervalul peste limită: `abstain`, `C-R3-PROGNOZA-INCERTA`. La prognoză, intervalul se lărgește cu trei variante de radiație.
- Ore meteo lipsă sau imposibile: completate prin interpolare și notate în `data_quality.input_issues`.
- Teste: `tests/c/` (`make c-test`).

## Limite

- Etichetele vin din simulare pe rețele sintetice, variante a 6 topologii germane. Pe rețele reale, precizia trebuie verificată cu măsurători (campaniile de 7 zile din Ord. 46/2021 sunt calea firească).
- Rezoluție orară (normele cer medii pe 10 minute); simulare echilibrată pe faze; tensiunea pe MT la post e estimată.
- Rețelele lungi și slabe și posturile cu baterii au erori mai mari (vezi analiza erorilor).
- În noiembrie, o zi senină și rece poate da depășiri (panourile reci produc aproape cât vara, iar duminica consumul e mic). Modelul le vede; agentul nu trimite echipe în afara sezonului, ci mesaje și urmărire.

## Folosire responsabilă

- Sistem de sprijin pentru dispecer, nu de comandă automată: deciziile cu impact (întreruperi planificate pentru priză, limitarea injecției, investiții) le aprobă un om. Planificatorul jurnalizează fiecare decizie până la predicția care a produs-o.
- EU AI Act: infrastructură critică, deci risc ridicat: supraveghere umană, jurnal, documentație (fișa asta), date de calitate.
- Fără date personale: posturile, clienții și prosumatorii sunt sintetici; mesajele către clienți sunt de grup, pe post sau stradă.

## Contextul (cifre publice)

ANRE, 31 aug. 2026: 385.791 de prosumatori, 4.281,86 MW, 151.040 cu stocare. Ilfov e primul județ din țară, cu 21.647 de prosumatori (303,81 MW); București are 8.307 (134,94 MW). Problema tensiunii pe posturile cu prosumatori nu e acoperită de portofoliul AI declarat de PPC.
