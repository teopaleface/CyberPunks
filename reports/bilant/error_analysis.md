# Analiza erorilor: bilanț pe post

SIMULARE pe date publice, gândită pentru datele PPC. Test: cele 300 de posturi din registrul C (rețele nevăzute la antrenare). Comanda: `make bilant-eval`.

## 1. Pierderea normală

Pe tipuri de rețea:

| topologia SimBench | zile | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 | mae_relativ |
|---|---|---|---|---|---|
| rural1 | 7192 | 4.56 | 26.86 | 0.94 | 0.17 |
| rural2 | 19280 | 9.19 | 60.12 | 0.81 | 0.15 |
| rural3 | 12015 | 5.99 | 51.40 | 0.87 | 0.12 |
| semiurb4 | 10775 | 2.58 | 12.76 | 0.93 | 0.20 |
| semiurb5 | 16779 | 5.23 | 37.52 | 0.84 | 0.14 |
| urban6 | 11928 | 1.34 | 12.50 | 0.99 | 0.11 |

Pe luni (vara are prosumatori care injectează, iarna are încălzire):

| luna | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 |
|---|---|---|---|
| 1 | 6.66 | 47.18 | 0.88 |
| 2 | 5.95 | 42.97 | 0.87 |
| 3 | 5.76 | 38.86 | 0.85 |
| 4 | 5.38 | 32.99 | 0.86 |
| 5 | 5.37 | 32.51 | 0.88 |
| 6 | 5.21 | 30.60 | 0.90 |
| 7 | 5.48 | 27.75 | 0.96 |
| 8 | 4.03 | 30.52 | 0.91 |
| 9 | 4.30 | 32.04 | 0.90 |
| 10 | 3.97 | 32.80 | 0.91 |
| 11 | 4.89 | 34.94 | 0.87 |
| 12 | 7.22 | 47.30 | 0.86 |

- Cea mai mare parte a erorii e o abatere fixă pe post: media erorii pe post are abaterea standard 7.68 kWh/zi, iar eroarea zilnică totală are MAE 5.30. Abaterea vine din „vârsta” rețelei (factorul necunoscut de ±35% din simulare), pe care istoricul postului o prinde doar parțial.
- 46 posturi au o abatere medie peste 5 kWh/zi. Acolo, o problemă mică (un contor de 3-4 kWh/zi) se pierde în eroare. De aceea fuziunea folosește creșterea lipsei, nu nivelul ei.
- Eroarea relativă cea mai mare o are topologia semiurb4 (20% din pierderea medie), cea mai mică urban6 (11%). Iarna (decembrie-ianuarie) eroarea crește odată cu încărcarea, pentru că pierderea crește cu pătratul ei.

## 2. Diagnosticul cauzei

Corect, după cât timp a trecut de la apariția problemei (fereastra are 14 zile):

| de când există problema | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| 0-3 zile | 231 | 0.51 | 0.14 |
| 4-7 | 257 | 0.55 | 0.15 |
| 8-14 | 327 | 0.57 | 0.24 |
| 15-30 | 445 | 0.58 | 0.29 |
| 31-90 | 833 | 0.54 | 0.38 |
| peste 90 | 1262 | 0.45 | 0.25 |

Corect, după mărimea lipsei reale:

| lipsa reală | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| sub 2 kWh/zi | 273 | 0.27 | 0.01 |
| 2-5 | 492 | 0.41 | 0.06 |
| 5-10 | 489 | 0.43 | 0.10 |
| 10-25 | 844 | 0.41 | 0.23 |
| peste 25 | 1257 | 0.71 | 0.51 |

Confuziile cele mai dese:

- pierdere normală → contor de client defect sau manipulat: 1085 ferestre
- client trecut la postul greșit în bază → contor de client defect sau manipulat: 344 ferestre
- client trecut la postul greșit în bază → pierdere normală: 254 ferestre
- contor de client defect sau manipulat → pierdere normală: 230 ferestre
- furt înainte de contor → contor de client defect sau manipulat: 199 ferestre
- pierdere normală → pierdere tehnică (cablu, faze dezechilibrate): 134 ferestre
- pierdere normală → client trecut la postul greșit în bază: 116 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → pierdere normală: 101 ferestre

- „Nu sunt sigur”: modelul se abține în 15.1% din ferestre. Acolo ar fi avut dreptate în 23% din cazuri, iar în rest în 87%. Abținerea scoate deci cazurile grele și le trimite la om.
- Problemele foarte noi (0-3 zile) se văd greu: fereastra are încă puține zile cu problemă. Cele foarte vechi (peste 90 de zile) intră treptat în istoricul postului, care învață „normalul” cu tot cu problemă. Pe date reale, istoricul trebuie învățat doar din perioade verificate (după vizita echipei), nu din toate zilele.
- Cele mai dese confuzii sunt între contorul de client și pierderea normală, în ambele sensuri. Cauza e mărimea: un contor de client lipsește adesea doar câțiva kWh pe zi, cât eroarea pierderii normale (vezi tabelul pe mărimi). Sub 2 kWh/zi, modelul are dreptate doar în 27% din cazuri.
- Clientul la postul greșit se confundă cel mai des cu contorul de client: la postul cu lipsă, un client „dispare” din bază, iar semnătura seamănă cu un contor oprit. Le desparte vecinul cu surplus egal, dar semnalul dispare când vecinul are și el o problemă sau când surplusul e mic față de eroarea pierderii normale.
- Contorul de post setat greșit (×2) e prins aproape mereu: raportul post/clienți e un semnal foarte curat.

## 3. Fuziunea cu A (cu bilanț față de fără)

Regula din producție: bilanțul doar confirmă (urcă scorul), nu coboară niciodată un contor găsit de A.

### Pe mai multe zile, scoruri A simulate (lotul train)

- Contoarele cu problemă reală urcă în clasament după fuziune în 39% din cazuri.
- Cele care nu urcă au de obicei o lipsă mică: 163 din 397 au sub 2 kWh/zi consum dispărut. Creșterea lipsei la post nu se deosebește atunci de zgomot (incertitudinea pe 7 zile e de câțiva kWh/zi).

### Ziua demo, scorurile reale ale lui A (lotul pop)

- Din 865 contoare cu problemă reală, bilanțul confirmă 33%; din 14985 fără problemă, confirmă 30%. Bilanțul confirmă deci de 1.1 ori mai des un contor cu problemă reală.

Pe tipuri de problemă (cele care nu schimbă totalul zilei, ca profilul inversat sau ceasul decalat, nu pot fi confirmate de bilanț):

| tipul problemei (A) | contoare | confirmate |
|---|---|---|
| negative | 84 | 0.43 |
| zero | 82 | 0.26 |
| spikes | 80 | 0.24 |
| gaps | 69 | 0.23 |
| clock_drift | 66 | 0.32 |
| drift | 64 | 0.48 |
| h3 | 60 | 0.40 |
| stuck | 59 | 0.10 |
| h5 | 49 | 0.45 |
| h6 | 46 | 0.28 |
| night | 46 | 0.37 |
| bypass | 43 | 0.47 |
| h4 | 42 | 0.36 |
| h1 | 41 | 0.29 |
| h2 | 34 | 0.38 |

- De ce câștigul e mic cu scorurile reale: A e deja foarte precis în vârful listei (100% în primele 200 de contoare), iar defectele lui A apar pe posturi cu câte 3-4 contoare cu probleme deodată (5,5% din contoare). Creșterea lipsei de la post e suma lor, deci nu spune care contor e de vină. Mai mult, curbele de consum ale lui A (Londra) nu sunt curbele clienților din lumea bilanțului; cele două lumi împart doar contorul cu problemă și ziua în care a apărut.
- Limită: scorurile din testul pe mai multe zile sunt simulate (`fusion_eval.py`).

