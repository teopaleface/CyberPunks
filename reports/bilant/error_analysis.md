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
| 0-3 zile | 231 | 0.59 | 0.14 |
| 4-7 | 257 | 0.62 | 0.15 |
| 8-14 | 327 | 0.64 | 0.24 |
| 15-30 | 445 | 0.67 | 0.29 |
| 31-90 | 833 | 0.61 | 0.38 |
| peste 90 | 1262 | 0.51 | 0.25 |

Corect, după mărimea lipsei reale:

| lipsa reală | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| sub 2 kWh/zi | 273 | 0.30 | 0.01 |
| 2-5 | 492 | 0.47 | 0.06 |
| 5-10 | 489 | 0.47 | 0.10 |
| 10-25 | 844 | 0.51 | 0.23 |
| peste 25 | 1257 | 0.78 | 0.51 |

Confuziile cele mai dese:

- pierdere normală → contor de client defect sau manipulat: 976 ferestre
- client trecut la postul greșit în bază → contor de client defect sau manipulat: 284 ferestre
- contor de client defect sau manipulat → pierdere normală: 220 ferestre
- client trecut la postul greșit în bază → pierdere normală: 206 ferestre
- furt înainte de contor → contor de client defect sau manipulat: 188 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → pierdere normală: 104 ferestre
- pierdere normală → pierdere tehnică (cablu, faze dezechilibrate): 94 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → contor de client defect sau manipulat: 84 ferestre

- „Nu sunt sigur”: modelul se abține în 13.1% din ferestre. Acolo ar fi avut dreptate în 27% din cazuri, iar în rest în 89%. Abținerea scoate deci cazurile grele și le trimite la om.
- Problemele foarte noi (0-3 zile) se văd greu: fereastra are încă puține zile cu problemă. Cele foarte vechi (peste 90 de zile) intră treptat în istoricul postului, care învață „normalul” cu tot cu problemă. Pe date reale, istoricul trebuie învățat doar din perioade verificate (după vizita echipei), nu din toate zilele.
- Cele mai dese confuzii sunt între contorul de client și pierderea normală, în ambele sensuri. Cauza e mărimea: un contor de client lipsește adesea doar câțiva kWh pe zi, cât eroarea pierderii normale (vezi tabelul pe mărimi). Sub 2 kWh/zi, modelul are dreptate doar în 30% din cazuri.
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

## 4. Unde ajută bilanțul și unde nu (sinteză cinstită)

### Unde ajută

- **Cauzele pe care contoarele nu le văd deloc.** Doar contoarele (modelul A) găsesc 0 din aceste probleme, prin construcție: nu au cum să vadă un branșament direct, un cablu care pierde sau un contor de post setat greșit. Bilanțul găsește postul în: furt înainte de contor 74% (cauza corectă 55%), pierdere tehnică 65% (42%), contorul postului setat greșit 99% (99%), client la postul greșit 50% (30%) din ferestrele de test.
- Energia: bilanțul găsește 85% din energia lipsă din aceste cauze, adică ~25.010 lei pe lună pe cele 300 de posturi ale hărții (la 0,70 lei/kWh). Din posturile marcate, 13% sunt de fapt normale.
- Pe ziua demo, 48% din energia pierdută peste normal nu apare la niciun contor de client.
- Diagnosticul cauzei bate tabelul de reguli din concept: F1 macro 0,67 față de 0,48. Clientul la postul greșit: 0,57 (reguli 0,34), după trăsătura „oglindă” (lipsa la un post și surplusul la vecin, zi de zi) și legarea celor două capete ale perechii. Pierderea tehnică: 0,46 (reguli 0,28).
- Planul B (unde montăm întâi contoarele de bilanț): `reports/bilant/plan_b.md`.
- Când modelul de contoare e mai slab (calitatea SGCC, AUC 0,80), confirmarea din bilanț ridică lei recuperați în primele 10 verificări pe zi de la 126 la 456.

### Unde nu ajută

- **Clasarea contoarelor găsite deja de A.** Cu scorurile reale ale lui A, precizia în primele 10-300 contoare e 100% cu și fără bilanț. La K = 500 bilanțul nu ajută (93,0% fără, 90,6% cu). Cu scoruri simulate de calitatea lui A pe Londra, câștigul e mic: în primele 10, de la 10,2% la 12,2%, adică 0,20 deplasări degeaba evitate pe zi.
- Pierderea tehnică veche (peste 60 de zile) sau mică (sub 10 kWh/zi) scapă des: istoricul postului o învață ca normală, iar comparația cu luna trecută nu mai vede saltul. Am încercat și comparația cu normalul fără istoric (doar GIS): pierderea tehnică a urcat puțin, F1 macro a scăzut puțin, deci n-am păstrat-o în model.
- De ce: un post are adesea mai multe contoare cu probleme deodată, iar lipsa de la post e suma lor, deci nu arată care contor e de vină. Problemele mici (sub 2 kWh/zi) se pierd în zgomotul pierderii normale. Tipurile care nu schimbă totalul zilei (profil inversat, ceas decalat, salturi) nu se văd deloc în bilanț.
- **Să coboare scorul unui contor** pe un post fără lipsă: pe scorurile reale ale lui A asta strica lista (AUC 0,918 → 0,907), așa că fuziunea doar confirmă.
- **Să rezolve „nu sunt sigur” al lui A:** pe ziua demo, 0 din 5 cazuri corecte. Funcția e oprită.
- Contorul de client în lumea cu defectele lui A: F1 0,38. Multe tipuri ale lui A au lipsă mică sau zero la totalul zilei.

