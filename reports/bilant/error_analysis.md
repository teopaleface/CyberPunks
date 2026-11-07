# Analiza erorilor: bilanț pe post

SIMULARE pe date publice, gândită pentru datele PPC. Test: cele 300 de posturi din registrul C (rețele nevăzute la antrenare). Comanda: `make bilant-eval`.

## 1. Pierderea normală

Pe tipuri de rețea:

| topologia SimBench | zile | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 | mae_relativ |
|---|---|---|---|---|---|
| rural1 | 6945 | 4.67 | 26.89 | 0.93 | 0.17 |
| rural2 | 13150 | 8.55 | 54.23 | 0.82 | 0.16 |
| rural3 | 7698 | 6.66 | 54.04 | 0.87 | 0.12 |
| semiurb4 | 9100 | 2.79 | 13.32 | 0.92 | 0.21 |
| semiurb5 | 12780 | 4.70 | 36.32 | 0.85 | 0.13 |
| urban6 | 8413 | 1.37 | 11.65 | 0.98 | 0.12 |

Pe luni (vara are prosumatori care injectează, iarna are încălzire):

| luna | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 |
|---|---|---|---|
| 1 | 6.19 | 42.34 | 0.88 |
| 2 | 5.68 | 38.14 | 0.87 |
| 3 | 5.83 | 36.50 | 0.85 |
| 4 | 5.52 | 31.91 | 0.87 |
| 5 | 5.47 | 31.90 | 0.89 |
| 6 | 5.97 | 33.12 | 0.87 |
| 7 | 5.30 | 30.48 | 0.89 |
| 8 | 4.03 | 30.50 | 0.91 |
| 9 | 4.33 | 31.99 | 0.90 |
| 10 | 3.84 | 31.46 | 0.91 |
| 11 | 4.58 | 32.06 | 0.88 |
| 12 | 6.78 | 42.83 | 0.87 |

- Cea mai mare parte a erorii e o abatere fixă pe post: media erorii pe post are abaterea standard 7.17 kWh/zi, iar eroarea zilnică totală are MAE 5.05. Abaterea vine din „vârsta” rețelei (factorul necunoscut de ±35% din simulare), pe care istoricul postului o prinde doar parțial.
- 46 posturi au o abatere medie peste 5 kWh/zi. Acolo, o problemă mică (un contor de 3-4 kWh/zi) se pierde în eroare. De aceea fuziunea folosește creșterea lipsei, nu nivelul ei.
- Eroarea relativă cea mai mare o are topologia semiurb4 (21% din pierderea medie), cea mai mică urban6 (12%). Iarna (decembrie-ianuarie) eroarea crește odată cu încărcarea, pentru că pierderea crește cu pătratul ei.

## 2. Diagnosticul cauzei

Corect, după cât timp a trecut de la apariția problemei (fereastra are 14 zile):

| de când există problema | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| 0-3 zile | 146 | 0.55 | 0.10 |
| 4-7 | 173 | 0.62 | 0.17 |
| 8-14 | 319 | 0.64 | 0.31 |
| 15-30 | 711 | 0.61 | 0.32 |
| 31-90 | 2117 | 0.54 | 0.25 |
| peste 90 | 2664 | 0.46 | 0.17 |

Corect, după mărimea lipsei reale:

| lipsa reală | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| sub 2 kWh/zi | 471 | 0.31 | 0.02 |
| 2-5 | 1062 | 0.40 | 0.05 |
| 5-10 | 1462 | 0.56 | 0.12 |
| 10-25 | 1679 | 0.50 | 0.27 |
| peste 25 | 1456 | 0.67 | 0.46 |

Confuziile cele mai dese:

- contor de client defect sau manipulat → pierdere normală: 1179 ferestre
- pierdere normală → contor de client defect sau manipulat: 680 ferestre
- client trecut la postul greșit în bază → contor de client defect sau manipulat: 411 ferestre
- contor de client defect sau manipulat → furt înainte de contor: 267 ferestre
- client trecut la postul greșit în bază → pierdere normală: 214 ferestre
- furt înainte de contor → contor de client defect sau manipulat: 209 ferestre
- pierdere normală → pierdere tehnică (cablu, faze dezechilibrate): 157 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → pierdere normală: 125 ferestre

- „Nu sunt sigur”: modelul se abține în 18.8% din ferestre. Acolo ar fi avut dreptate în 45% din cazuri, iar în rest în 77%. Abținerea scoate deci cazurile grele și le trimite la om.
- Problemele foarte noi (0-3 zile) se văd greu: fereastra are încă puține zile cu problemă. Cele foarte vechi (peste 90 de zile) intră treptat în istoricul postului, care învață „normalul” cu tot cu problemă. Pe date reale, istoricul trebuie învățat doar din perioade verificate (după vizita echipei), nu din toate zilele.
- Cele mai dese confuzii sunt între contorul de client și pierderea normală, în ambele sensuri. Cauza e mărimea: un contor de client lipsește adesea doar câțiva kWh pe zi, cât eroarea pierderii normale (vezi tabelul pe mărimi). Sub 2 kWh/zi, modelul are dreptate doar în 31% din cazuri.
- Clientul la postul greșit se confundă cel mai des cu contorul de client: la postul cu lipsă, un client „dispare” din bază, iar semnătura seamănă cu un contor oprit. Le desparte vecinul cu surplus egal, dar semnalul dispare când vecinul are și el o problemă sau când surplusul e mic față de eroarea pierderii normale.
- Contorul de post setat greșit (×2) e prins aproape mereu: raportul post/clienți e un semnal foarte curat.

## 3. Fuziunea cu A (cu bilanț față de fără)

- Contoarele cu problemă reală urcă în clasament după fuziune în 58% din cazuri.
- Cele care nu urcă au de obicei o lipsă mică: 179 din 455 au sub 2 kWh/zi consum dispărut. Creșterea lipsei la post nu se deosebește atunci de zgomot (incertitudinea pe 7 zile e de câțiva kWh/zi).
- Consumul scăzut real (concediu, ocupare schimbată, cu consumul scăzut la mai puțin de jumătate și fără defect): 3463 rânduri contor-zi. Mediana rangului lor trece de la 6514 la 10180 după fuziune (rang mai mare = mai jos în listă); în primele 20 pe zi ajung 0.3 fără bilanț și 0.4 cu bilanț.
- Furtul înainte de contor ridică scorul tuturor contoarelor cu scădere de pe acel post, chiar dacă nu sunt de vină. De aceea fuziunea compară mărimea: urcă doar contorul a cărui scădere se potrivește cu lipsa.
- Limită: scorurile A sunt simulate (vezi `fusion_eval.py`). Cifra se reface cu scorurile reale ale lui A când contoarele lui sunt legate de posturile registrului C.

