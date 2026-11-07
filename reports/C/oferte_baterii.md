# Oferte de baterii pentru prosumatorii de pe posturile cu tensiune mare

Date SINTETICE (posturi, prosumatori, profile). Ziua de calcul: 8 iulie 2025 (scenariul `demo-vara`). Generat de `uv run python -m cyberpunks.c_prosumatori.reports_c offers --scenario demo-vara`.

## De ce

- La prânz, bateria stochează energia care altfel ar urca tensiunea în rețeaua străzii și ar opri invertoarele vecinilor. Seara o descarcă, exact în orele 18-22, pentru care au existat măsuri guvernamentale de criză în aug.-oct. 2026 (deficit de seară). O singură baterie rezolvă două probleme.
- Casa Verde Baterii 2026 (Ord. 1.904/2026, MO 775/14.09.2026): grant de până la 75% din cost, cel mult 15.000 lei, pentru cel puțin 10 kWh; cost standard maxim eligibil 1.500 lei/kWh, cu montaj și invertor.
- Canal de vânzare: magazinele PPC și Flanco (preluarea a fost anunțată pe 3 nov. 2026). Venitul e pentru PPC Energie; distribuitorul (Rețele Electrice) câștigă o rețea care nu mai trece de 1,10 pu.

## Cum am calculat

- Pe profilul fiecărui prosumator fără baterie: producția din vremea reală a anului 2025 (Open-Meteo) și consumul lui, aceleași ca în simularea fizică; variantele 5, 10, 15 kWh.
- Bateria se încarcă doar în orele cu risc ale postului, cu puterea repartizată pe ele (altfel ar fi plină înainte de vârf), și se descarcă seara.
- Efectul pe tensiune: marginal (sensibilitatea rețelei în nodul cel mai expus, la ora de vârf) și pentru tot postul (simulare cu bateriile celor care acceptă: 30%, IPOTEZĂ).
- Recuperarea: (cost − grant) / economia pe an. Economia = kWh mutați de la prânz în seară × (1,56 − 0,40) lei/kWh × randament 0,9 (prețul cu taxe PPC Ore Smart+ în afara intervalelor, valoarea energiei injectate din config). Costul: 1250 lei/kWh + 2500 lei montaj (IPOTEZĂ din config).
- Oferta merge doar unde bateria coboară tensiunea postului cu cel puțin 0.0005 pu și se recuperează în cel mult 15 ani (IPOTEZĂ). Pentru fiecare prosumator e aleasă mărimea cu recuperarea cea mai scurtă.
- Venitul PPC Energie: marja de 15% din vânzare și montaj (IPOTEZĂ).

## Pe posturi

| Post | Zona | Prosumatori cu ofertă | kWh dacă acceptă 30% | Efect pe P90 al postului (pu) | Venit PPC Energie, 30% (lei) |
|---|---|---|---|---|---|
| PT-1005 | B-S1 | 8 | 20 | -0,0092 | 4500 |
| PT-1072 | IF-VOLUNTARI | 6 | 20 | -0,0101 | 4500 |
| PT-1075 | IF-CORNETU | 2 | 10 | -0,0136 | 2250 |
| PT-1076 | IF-CORNETU | 7 | 20 | -0,0091 | 4500 |
| PT-1087 | IF-OTOPENI | 3 | 10 | -0,0101 | 2250 |
| PT-1119 | IF-STEFANESTII-DE-JOS | 7 | 20 | -0,0041 | 4500 |
| PT-1131 | IF-CHITILA | 9 | 30 | -0,0103 | 6750 |
| PT-1147 | IF-TUNARI | 11 | 30 | -0,0122 | 6750 |
| PT-1252 | IF-POPESTI-LEORDENI | 16 | 50 | -0,0044 | 11250 |
| PT-1255 | B-S6 | 6 | 20 | -0,0068 | 4500 |
| PT-1263 | B-S4 | 10 | 30 | -0,0080 | 6750 |
| PT-1269 | IF-AFUMATI | 12 | 40 | -0,0147 | 9000 |
| PT-1300 | IF-STEFANESTII-DE-JOS | 11 | 30 | -0,0103 | 6750 |

## Lista pentru PPC Energie (primii 30 din 108, după efectul pe tensiune și venit)

| Prosumator (cod sintetic) | Post | kWp | Baterie (kWh) | kWh stocați la prânz | Efect pe tensiune (pu) | kWh mutați pe an | Economie (lei/an) | Cost / grant (lei) | Recuperare (ani) | Venit PPC (lei) |
|---|---|---|---|---|---|---|---|---|---|---|
| PT-1087-P10 | PT-1087 | 10 | 10 | 10,0 | 0,0078 | 1303 | 1512 | 15000 / 11250 | 2,5 | 2250 |
| PT-1087-P16 | PT-1087 | 5 | 10 | 10,0 | 0,0070 | 702 | 814 | 15000 / 11250 | 4,6 | 2250 |
| PT-1147-P19 | PT-1147 | 5 | 10 | 10,0 | 0,0063 | 454 | 527 | 15000 / 11250 | 7,1 | 2250 |
| PT-1269-P17 | PT-1269 | 5 | 10 | 10,0 | 0,0061 | 732 | 849 | 15000 / 11250 | 4,4 | 2250 |
| PT-1072-P30 | PT-1072 | 8 | 10 | 10,0 | 0,0061 | 696 | 808 | 15000 / 11250 | 4,6 | 2250 |
| PT-1072-P34 | PT-1072 | 3 | 10 | 9,6 | 0,0060 | 575 | 667 | 15000 / 11250 | 5,6 | 2250 |
| PT-1147-P33 | PT-1147 | 6 | 10 | 10,0 | 0,0060 | 684 | 793 | 15000 / 11250 | 4,7 | 2250 |
| PT-1076-P16 | PT-1076 | 6 | 10 | 10,0 | 0,0054 | 1187 | 1376 | 15000 / 11250 | 2,7 | 2250 |
| PT-1076-P25 | PT-1076 | 12 | 10 | 10,0 | 0,0054 | 525 | 609 | 15000 / 11250 | 6,2 | 2250 |
| PT-1072-P10 | PT-1072 | 6 | 10 | 10,0 | 0,0054 | 444 | 515 | 15000 / 11250 | 7,3 | 2250 |
| PT-1255-P33 | PT-1255 | 12 | 10 | 10,0 | 0,0052 | 630 | 731 | 15000 / 11250 | 5,1 | 2250 |
| PT-1005-P24 | PT-1005 | 12 | 10 | 10,0 | 0,0050 | 848 | 984 | 15000 / 11250 | 3,8 | 2250 |
| PT-1300-P22 | PT-1300 | 12 | 10 | 10,0 | 0,0050 | 294 | 341 | 15000 / 11250 | 11,0 | 2250 |
| PT-1131-P13 | PT-1131 | 5 | 10 | 10,0 | 0,0049 | 549 | 637 | 15000 / 11250 | 5,9 | 2250 |
| PT-1076-P31 | PT-1076 | 5 | 10 | 10,0 | 0,0049 | 495 | 574 | 15000 / 11250 | 6,5 | 2250 |
| PT-1075-P08 | PT-1075 | 6 | 10 | 10,0 | 0,0049 | 448 | 520 | 15000 / 11250 | 7,2 | 2250 |
| PT-1147-P31 | PT-1147 | 5 | 10 | 10,0 | 0,0046 | 409 | 474 | 15000 / 11250 | 7,9 | 2250 |
| PT-1252-P15 | PT-1252 | 5 | 10 | 10,0 | 0,0046 | 464 | 538 | 15000 / 11250 | 7,0 | 2250 |
| PT-1252-P28 | PT-1252 | 5 | 10 | 10,0 | 0,0046 | 550 | 638 | 15000 / 11250 | 5,9 | 2250 |
| PT-1005-P09 | PT-1005 | 12 | 10 | 10,0 | 0,0042 | 1349 | 1565 | 15000 / 11250 | 2,4 | 2250 |
| PT-1005-P32 | PT-1005 | 6 | 10 | 10,0 | 0,0042 | 823 | 954 | 15000 / 11250 | 3,9 | 2250 |
| PT-1147-P24 | PT-1147 | 5 | 10 | 10,0 | 0,0041 | 584 | 678 | 15000 / 11250 | 5,5 | 2250 |
| PT-1131-P23 | PT-1131 | 10 | 10 | 10,0 | 0,0041 | 682 | 791 | 15000 / 11250 | 4,7 | 2250 |
| PT-1269-P41 | PT-1269 | 3 | 10 | 9,4 | 0,0040 | 489 | 568 | 15000 / 11250 | 6,6 | 2250 |
| PT-1269-P29 | PT-1269 | 12 | 10 | 10,0 | 0,0040 | 955 | 1108 | 15000 / 11250 | 3,4 | 2250 |
| PT-1147-P04 | PT-1147 | 3 | 10 | 8,8 | 0,0040 | 570 | 661 | 15000 / 11250 | 5,7 | 2250 |
| PT-1005-P02 | PT-1005 | 5 | 10 | 10,0 | 0,0040 | 945 | 1096 | 15000 / 11250 | 3,4 | 2250 |
| PT-1076-P03 | PT-1076 | 5 | 10 | 10,0 | 0,0039 | 861 | 999 | 15000 / 11250 | 3,8 | 2250 |
| PT-1072-P25 | PT-1072 | 8 | 10 | 10,0 | 0,0038 | 1317 | 1527 | 15000 / 11250 | 2,5 | 2250 |
| PT-1300-P36 | PT-1300 | 3 | 10 | 8,4 | 0,0037 | 919 | 1066 | 15000 / 11250 | 3,5 | 2250 |

## Textul ofertei (șablon, fără date personale; cifrele sunt medianele listei)

> Panourile dumneavoastră produc la prânz mai mult decât consumați. În zilele cu soare puternic, tensiunea din rețeaua străzii crește până când invertoarele se opresc singure. O baterie de 10 kWh ar stoca circa 10 kWh la prânz și i-ar folosi seara, când energia e cea mai scumpă și sistemul are cea mai mare nevoie de ea. Cu grantul Casa Verde Baterii 2026, costul dumneavoastră scade la circa 3.750 lei și se recuperează în circa 5 ani. Detalii în magazinele PPC și Flanco.

Total: 108 oferte pe 13 posturi, venit potențial 243.000 lei dacă acceptă toți (72.900 lei la 30%).
