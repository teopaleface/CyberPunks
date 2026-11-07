# Analiza erorilor: modelul C (tensiunea maximă pe post)

Toate cifrele vin din predicțiile de test pe **rețele nevăzute** (fiecare topologie SimBench prezisă de modele care n-au văzut-o) și **luni nevăzute** (antrenare înainte de 2025-01-01, test 2025-01-01 → 2026-11-06): 324.000 de zile-post. Datele sunt SINTETICE (posturi, rețele, prosumatori), vremea e reală.

Comenzile care refac cifrele:

```
make c-eval                                                   # reports/C/metrics.json, metrics_detail.json, predicțiile de test
uv run python -m cyberpunks.c_prosumatori.error_analysis      # reports/C/error_tables.json (tabelele de mai jos)
uv run python -m cyberpunks.c_prosumatori.evaluate --ablation fara_fizica            # reports/C/ablation_fara_fizica.json
uv run python -m cyberpunks.c_prosumatori.evaluate --ablation fara_tensiune_pornire  # reports/C/ablation_fara_tensiune_pornire.json
```

## Pe scurt

- Eroarea medie (MAE) e 0,0054 pu față de 0,0227 la baseline, pe fiecare tip de rețea, lună și vreme. Nu există o felie în care baseline-ul să fie mai bun.
- Modelul greșește cel mai mult pe **rețelele rurale lungi și slabe** (cablu torsadat TYIR 50, aluminiu vechi), pe **posturile cu baterii** și **lângă prag** (1,09-1,11 pu).
- Ratările sunt depășiri la limită: mediana tensiunii reale la ratări e 1,104 pu, iar 97% sunt sub 1,115 pu. Alarmele false sunt aproape de prag: mediana e 1,095 pu, iar 84% sunt peste 1,09 pu.
- Ce am schimbat după analiză: calibrarea izotonică (eroarea de calibrare ECE de la 0,012 la 0,003), lărgirea conformală a intervalelor, pe grupe de rețea (acoperirea P10-P90 de la 43% la 82% la modelul zilnic și de la 50% la 80% la cel orar (80,4%)) și repararea prizei în simulare (vezi mai jos).

## 1. Rețele rurale lungi

| Drumul maxim de la post | Zile-post | MAE model | MAE baseline | Acoperire P10-P90 | Rata depășirilor | PR-AUC |
|---|---|---|---|---|---|---|
| scurt (sfertul cel mai scurt) | 81.000 | 0,0045 | 0,0213 | 86,1% | 1,2% | 0,842 |
| mediu | 81.000 | 0,0052 | 0,0207 | 82,7% | 0,3% | 0,587 |
| lung | 81.000 | 0,0057 | 0,0223 | 77,9% | 5,7% | 0,878 |
| foarte lung | 81.000 | 0,0063 | 0,0267 | 77,1% | 25,2% | 0,972 |

| Conductor | MAE model | MAE baseline | Rata depășirilor | PR-AUC | Recall |
|---|---|---|---|---|---|
| NAYY 4x150 (cablu gros) | 0,0050 | 0,0209 | 1,6% | 0,801 | 71,7% |
| NAYY 4x95 | 0,0054 | 0,0204 | 0,5% | 0,738 | 78,8% |
| TYIR 70 (torsadat) | 0,0056 | 0,0231 | 8,1% | 0,912 | 80,2% |
| TYIR 50 (torsadat subțire) | 0,0055 | 0,0260 | 18,4% | 0,979 | 90,2% |
| Al 35 vechi | 0,0058 | 0,0232 | 16,4% | 0,959 | 91,6% |

Ce înseamnă: pe rețelele lungi eroarea crește cu 40% (de la 0,0045 la 0,0063 pu), iar intervalul acoperă mai puțin (77% față de 86%). Cele mai mari 200 de erori sunt toate pe rural2 și rural3, aproape toate pe TYIR 50, Al 35 sau TYIR 70, în zile mai senine decât media (nori 25% față de 55%) și pe posturi la care panourile ridică tensiunea mult (sensibilitate mediană 0,21 pu, față de 0,03 pu în tot testul). 62% dintre ele sunt subestimări. Pe rețelele scurte depășirile sunt rare, deci PR-AUC e mai mic acolo, deși eroarea e mică.

Pe topologii, acoperirea intervalului varia între 73% (rural3, semiurb5) și 88% (rural1, semiurb4) cu o singură margine conformală. Cu margini pe patru grupe de rețea (după cât ridică panourile tensiunea în cel mai expus punct) intervalul se lărgește pe rețelele slabe și se strânge pe cele puternice: acoperirea totală e 82,1%, pe topologii între 76% (semiurb5) și 87% (rural2), iar rural3 urcă de la 73% la 80%.

## 2. Zile parțial înnorate

Doar zilele cu producție de peste 0,5 kW/kWp la prânz:

| Nori la prânz | Zile-post | MAE model | Acoperire | Rata depășirilor | PR-AUC | Recall |
|---|---|---|---|---|---|---|
| senin (sub 20%) | 94.080 | 0,0058 | 78,6% | 12,5% | 0,959 | 88,5% |
| puțini nori (20-50%) | 59.520 | 0,0057 | 78,6% | 11,8% | 0,955 | 86,8% |
| parțial noros (50-80%) | 49.440 | 0,0057 | 79,3% | 9,4% | 0,942 | 85,1% |
| noros (peste 80%) | 35.040 | 0,0057 | 79,7% | 7,2% | 0,927 | 81,5% |

Ce înseamnă: eroarea pe tensiune nu crește cu norii (modelul vede radiația pe panou, nu doar procentul de nori), dar depășirile se prind mai greu în zilele noroase (recall 81,5% față de 88,5%). Explicația probabilă: în zilele cu nori, vârful de producție e scurt (o oră senină între nori), iar trăsăturile zilnice (maximul și suma radiației) nu îl surprind la fel de bine. Pentru `maine`, prognoza adaugă incertitudine: agentul lărgește intervalul cu trei variante de radiație și trimite la om cazurile nesigure (regula `C-R3-PROGNOZA-INCERTA`).

## 3. Posturi cu baterii

| Panouri cu baterie | Zile-post | MAE model | Acoperire | Rata depășirilor | PR-AUC |
|---|---|---|---|---|---|
| fără | 81.000 | 0,0046 | 86,7% | 1,5% | 0,841 |
| sub 25% | 93.150 | 0,0055 | 80,4% | 11,3% | 0,961 |
| 25-50% | 80.325 | 0,0059 | 77,1% | 11,1% | 0,962 |
| peste 50% | 69.525 | 0,0058 | 79,3% | 8,1% | 0,933 |

Ce înseamnă: bateriile adaugă incertitudine (eroarea crește de la 0,0046 la 0,0059 pu, acoperirea scade la 77%), pentru că starea lor de încărcare la prânz depinde de ziua de dinainte, pe care modelul nu o vede. O baterie de autoconsum se umple dimineața și nu mai ajută la vârf: de aceea rata depășirilor scade puțin chiar și la peste 50% panouri cu baterie (8,1% față de 11%). Aceeași observație stă la baza treptei 4 din scara de soluții: bateria oferită se încarcă doar în orele cu risc.

## 4. Lângă prag

- 5,9% din zilele-post de test (19.165) au tensiunea reală între 1,09 și 1,11 pu; acolo clasificarea e corectă în 68,5% din cazuri.
- 3.547 de ratări (depășiri neprinse la pragul 0,5): mediana tensiunii reale 1,104 pu, 97,3% sub 1,115 pu.
- 3.432 de alarme false: mediana 1,095 pu, 83,5% peste 1,09 pu.

Ce înseamnă: greșelile sunt aproape toate la câteva miimi de pu de limită. Agentul tratează zona asta separat: dacă intervalul P10-P90 trece peste 1,10 și probabilitatea e între 0,2 și 0,5, recomandă măsurători, nu o echipă.

## 5. Luna și ziua săptămânii

MAE rămâne între 0,0047 și 0,0057 pu în fiecare lună. Vara modelul subestimează puțin (eroarea medie cu semn între −0,0006 și −0,0009 pu în iunie-septembrie). Zilele libere și cele lucrătoare au aceeași eroare (0,0054 și 0,0055 pu).

## 6. Ce am încercat și ce a rămas

| Încercare | Rezultat | Decizie |
|---|---|---|
| Probabilitatea brută a clasificatorului | Brier 0,0165, ECE 0,0123 | înlocuită |
| Calibrare izotonică pe predicții din topologii nevăzute | Brier 0,0150, ECE 0,0032 | păstrată |
| Intervale P10-P90 brute | acoperire 42,8% (zilnic), 49,8% (orar) pe rețele nevăzute | prea înguste |
| Lărgire conformală (CQR) din reziduuri pe topologii nevăzute, o margine globală | acoperire 80,9% (zilnic), pe topologii 73-88% | înlocuită |
| Lărgire conformală pe grupe de rețea (patru grupe după cât ridică panourile tensiunea) | acoperire 82,1% (zilnic), pe topologii 76-87%; rural3 de la 73% la 80% | păstrată |
| Model orar, lărgire conformală calibrată imbricat: doar perioada de antrenare, fără topologia testată (după două runde de review Codex: prima variantă folosea și reziduuri din perioada de test) | acoperire 80,4% (49,8% fără lărgire) | păstrată |
| Constrângeri monotone (mai mult soare / kW / rețea mai slabă nu pot coborî tensiunea) | LightGBM le acceptă doar la clasificator, nu la cuantile | păstrate la clasificator |
| Simularea cu priza ignorată (bug pandapower 3.x: `tap_changer_type` gol în SimBench) | modelul învăța priza ca pe un zgomot; estimarea „după priză” nu se mișca | reparat; simulări refăcute |
| Fără trăsăturile fizice din topologie (sensibilitățile rețelei, estimarea liniară a tensiunii, rezistența) | MAE 0,0119 pu (de 2,2 ori mai mare); PR-AUC 0,384, sub baseline (0,428); pe rural2 MAE 0,0239 față de 0,0061 | trăsăturile rămân: fără ele modelul nu se transferă pe rețele noi |
| Fără tensiunea de pornire și priză | MAE 0,0205 pu (de 3,8 ori mai mare); PR-AUC 0,728 | rămân: sunt cel mai important semnal |
| Radiația de dimineață (6-11) ca trăsătură, pentru bateriile care se umplu înainte de prânz (`reports/C/experiment_gti_morning.json`) | MAE 0,00535 față de 0,00543; pe posturile cu baterii doar 1-2% mai bine; recall 84,2% față de 86,5%, Brier 0,0153 față de 0,0150 | neadoptată: clasificarea, care decide lucrările, iese mai slabă; incertitudinea bateriilor vine din starea lor de încărcare, pe care nu o știm |

Ce înseamnă ablațiile pentru PPC: modelul are nevoie de două lucruri pe care distribuitorul le poate avea, dar nu le are peste tot azi. Primul e topologia rețelei de joasă tensiune, din care se calculează cât ridică panourile tensiunea în cel mai expus punct; asta aduce GIS-ul nou, pentru care Rețele Electrice a lansat licitația în aprilie 2026. Al doilea e priza și tensiunea pe medie tensiune la fiecare post. Fără ele, eroarea se dublează, respectiv aproape se împătrește.

## 7. Limite cunoscute

- Rezoluția e orară; normele vorbesc de medii pe 10 minute. Vârfurile scurte (un nor care trece) sunt netezite.
- Simularea e echilibrată pe faze. Dezechilibrul (prosumatori monofazați) se estimează analitic doar în scara de soluții, plafonat la 2%.
- „kWh pierduți” sunt o limită de sus: un invertor oprit rămâne oprit toată ora.
- Rețelele sunt variante a 6 topologii SimBench (germane). Rețelele românești reale pot avea alte forme; testul pe topologii nevăzute arată cât scade precizia pe o formă nouă.
- Tensiunea pe medie tensiune la post e estimată (eroare de 0,004 pu în simulare); în realitate poate fi mai nesigură.
