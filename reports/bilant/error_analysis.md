# Analiza erorilor: bilanț pe post

SIMULARE pe date publice, gândită pentru datele PPC. Test: cele 300 de posturi din registrul C (rețele nevăzute la antrenare). Comanda: `make bilant-eval`.

## 1. Pierderea normală

Pe tipuri de rețea:

| topologia SimBench | zile | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 | mae_relativ |
|---|---|---|---|---|---|
| rural1 | 7192 | 4.62 | 26.86 | 0.94 | 0.17 |
| rural2 | 19280 | 9.07 | 60.08 | 0.81 | 0.15 |
| rural3 | 12015 | 6.60 | 51.32 | 0.87 | 0.13 |
| semiurb4 | 10775 | 2.62 | 12.72 | 0.93 | 0.21 |
| semiurb5 | 16779 | 5.46 | 37.56 | 0.84 | 0.15 |
| urban6 | 11928 | 1.13 | 12.32 | 0.99 | 0.09 |

Pe luni (vara are prosumatori care injectează, iarna are încălzire):

| luna | mae_kwh | pierdere_medie_kwh | acoperire_p10_p90 |
|---|---|---|---|
| 1 | 6.76 | 47.11 | 0.88 |
| 2 | 6.09 | 42.90 | 0.87 |
| 3 | 5.85 | 38.81 | 0.86 |
| 4 | 5.55 | 32.96 | 0.86 |
| 5 | 5.53 | 32.49 | 0.87 |
| 6 | 5.14 | 30.61 | 0.90 |
| 7 | 5.10 | 27.71 | 0.94 |
| 8 | 4.15 | 30.51 | 0.91 |
| 9 | 4.36 | 32.01 | 0.90 |
| 10 | 4.03 | 32.76 | 0.91 |
| 11 | 4.93 | 34.86 | 0.88 |
| 12 | 7.33 | 47.22 | 0.86 |

- Cea mai mare parte a erorii e o abatere fixă pe post: media erorii pe post are abaterea standard 7.89 kWh/zi, iar eroarea zilnică totală are MAE 5.40. Abaterea vine din „vârsta” rețelei (factorul necunoscut de ±35% din simulare), pe care istoricul postului o prinde doar parțial.
- 48 posturi au o abatere medie peste 5 kWh/zi. Acolo, o problemă mică (un contor de 3-4 kWh/zi) se pierde în eroare. De aceea fuziunea folosește creșterea lipsei, nu nivelul ei.
- Eroarea relativă cea mai mare o are topologia semiurb4 (21% din pierderea medie), cea mai mică urban6 (9%). Iarna (decembrie-ianuarie) eroarea crește odată cu încărcarea, pentru că pierderea crește cu pătratul ei.

## 2. Diagnosticul cauzei

Corect, după cât timp a trecut de la apariția problemei (fereastra are 14 zile):

| de când există problema | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| 0-3 zile | 231 | 0.65 | 0.14 |
| 4-7 | 257 | 0.70 | 0.15 |
| 8-14 | 327 | 0.73 | 0.24 |
| 15-30 | 445 | 0.76 | 0.28 |
| 31-90 | 833 | 0.78 | 0.39 |
| peste 90 | 1262 | 0.76 | 0.25 |

Corect, după mărimea lipsei reale:

| lipsa reală | ferestre | corect_model | corect_reguli |
|---|---|---|---|
| sub 2 kWh/zi | 273 | 0.44 | 0.02 |
| 2-5 | 492 | 0.67 | 0.06 |
| 5-10 | 489 | 0.65 | 0.12 |
| 10-25 | 844 | 0.75 | 0.23 |
| peste 25 | 1257 | 0.89 | 0.50 |

Confuziile cele mai dese:

- pierdere normală → contor de client defect sau manipulat: 804 ferestre
- pierdere normală → pierdere tehnică (cablu, faze dezechilibrate): 177 ferestre
- furt înainte de contor → contor de client defect sau manipulat: 140 ferestre
- contor de client defect sau manipulat → pierdere normală: 135 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → pierdere normală: 95 ferestre
- client trecut la postul greșit în bază → contor de client defect sau manipulat: 94 ferestre
- contor de client defect sau manipulat → furt înainte de contor: 88 ferestre
- pierdere tehnică (cablu, faze dezechilibrate) → contor de client defect sau manipulat: 69 ferestre

- „Nu sunt sigur”: modelul se abține în 14.5% din ferestre. Acolo ar fi avut dreptate în 43% din cazuri, iar în rest în 93%. Abținerea scoate deci cazurile grele și le trimite la om.
- Problemele foarte noi (0-3 zile) se văd greu: fereastra are încă puține zile cu problemă. Cele foarte vechi (peste 90 de zile) intră treptat în istoricul postului, care învață „normalul” cu tot cu problemă. Pe date reale, istoricul trebuie învățat doar din perioade verificate (după vizita echipei), nu din toate zilele.
- Cele mai dese confuzii sunt între contorul de client și pierderea normală, în ambele sensuri. Cauza e mărimea: un contor de client lipsește adesea doar câțiva kWh pe zi, cât eroarea pierderii normale (vezi tabelul pe mărimi). Sub 2 kWh/zi, modelul are dreptate doar în 44% din cazuri.
- Clientul la postul greșit se confundă cel mai des cu contorul de client: la postul cu lipsă, un client „dispare” din bază, iar semnătura seamănă cu un contor oprit. Le desparte vecinul cu surplus egal, dar semnalul dispare când vecinul are și el o problemă sau când surplusul e mic față de eroarea pierderii normale.
- Contorul de post setat greșit (×2) e prins aproape mereu: raportul post/clienți e un semnal foarte curat.

## 3. Fuziunea cu A (cu bilanț față de fără)

Regula din producție: bilanțul doar confirmă (urcă scorul), nu coboară niciodată un contor găsit de A.

### Pe mai multe zile, scoruri A simulate (lotul train)

- Contoarele cu problemă reală urcă în clasament după fuziune în 35% din cazuri.
- Cele care nu urcă au de obicei o lipsă mică: 163 din 397 au sub 2 kWh/zi consum dispărut. Creșterea lipsei la post nu se deosebește atunci de zgomot (incertitudinea pe 7 zile e de câțiva kWh/zi).

### Ziua demo, scorurile reale ale lui A (lotul pop)

- Din 865 contoare cu problemă reală, bilanțul confirmă 32%; din 14985 fără problemă, confirmă 29%. Bilanțul confirmă deci de 1.1 ori mai des un contor cu problemă reală.

Pe tipuri de problemă (cele care nu schimbă totalul zilei, ca profilul inversat sau ceasul decalat, nu pot fi confirmate de bilanț):

| tipul problemei (A) | contoare | confirmate |
|---|---|---|
| negative | 84 | 0.44 |
| zero | 82 | 0.24 |
| spikes | 80 | 0.23 |
| gaps | 69 | 0.23 |
| clock_drift | 66 | 0.30 |
| drift | 64 | 0.45 |
| h3 | 60 | 0.37 |
| stuck | 59 | 0.10 |
| h5 | 49 | 0.43 |
| h6 | 46 | 0.28 |
| night | 46 | 0.35 |
| bypass | 43 | 0.49 |
| h4 | 42 | 0.33 |
| h1 | 41 | 0.24 |
| h2 | 34 | 0.41 |

- De ce câștigul e mic cu scorurile reale: A e deja foarte precis în vârful listei (100% în primele 200 de contoare), iar defectele lui A apar pe posturi cu câte 3-4 contoare cu probleme deodată (5,5% din contoare). Creșterea lipsei de la post e suma lor, deci nu spune care contor e de vină. Mai mult, curbele de consum ale lui A (Londra) nu sunt curbele clienților din lumea bilanțului; cele două lumi împart doar contorul cu problemă și ziua în care a apărut.
- Limită: scorurile din testul pe mai multe zile sunt simulate (`fusion_eval.py`).

## 4. Unde ajută bilanțul și unde nu (sinteză cinstită)

### Unde ajută

- **Cauzele pe care contoarele nu le văd deloc.** Doar contoarele (modelul A) găsesc 0 din aceste probleme, prin construcție: nu au cum să vadă un branșament direct, un cablu care pierde sau un contor de post setat greșit. Bilanțul găsește postul în: furt înainte de contor 76% (cauza corectă 62%), pierdere tehnică 64% (50%), contorul postului setat greșit 99% (98%), client la postul greșit 58% (54%) din ferestrele de test.
- Energia: bilanțul găsește 84% din energia lipsă din aceste cauze, adică ~24.663 lei pe lună pe cele 300 de posturi ale hărții (la 0,70 lei/kWh). Din posturile marcate, 18% sunt de fapt normale.
- Pe ziua demo, 48% din energia pierdută peste normal nu apare la niciun contor de client.
- Diagnosticul cauzei bate tabelul de reguli din concept: F1 macro 0,75 față de 0,48. Clientul la postul greșit: 0,87 (reguli 0,34), după trăsătura „oglindă” (lipsa la un post și surplusul la vecin, zi de zi) și legarea celor două capete ale perechii. Pierderea tehnică: 0,49 (reguli 0,27).
- Planul B (unde montăm întâi contoarele de balanță): `reports/bilant/plan_b.md`.
- Când modelul de contoare e mai slab (calitatea SGCC, AUC 0,80), confirmarea din bilanț ridică lei recuperați în primele 10 verificări pe zi de la 126 la 433.
- **Fuziunea v2 pe harta de test** (defectele lui A, scoruri A simulate, regula reglată automat pe un lot separat de 3.000 de posturi): precizia în primele 10 contoare pe zi 80% doar cu A, 78% cu regula v1, 90% cu regula v2; în primele 50: 44% → 46%. Deplasări degeaba evitate pe zi: 1,0 (K = 10), 1,0 (K = 50).

### Unde nu ajută

- **Clasarea contoarelor găsite deja de A.** Cu scorurile reale ale lui A, precizia în primele 10-300 contoare e 100% cu și fără bilanț. La K = 500 bilanțul nu ajută (96,2% fără, 96,0% cu). Cu scoruri simulate de calitatea lui A pe Londra, câștigul e mic: în primele 10, de la 10,2% la 13,0%, adică 0,28 deplasări degeaba evitate pe zi.
- **Cu scorurile reale ale lui A**, regula v2 nu strică și nici nu adaugă mult: AUC 0,917 doar cu A, 0,919 cu v2 (v1: 0,916); în primele 500: 96,2% → 96,0%. Câștigul din testul simulat nu se poate confirma pe scorurile reale, pentru că acolo A e deja aproape perfect în vârful listei.
- **Fuziunea învățată** (LightGBM pe trăsăturile contorului și ale postului) a ieșit foarte bună pe testul simulat (precizie 1,00 în primele 10), dar e un artefact: scorul A simulat e construit din scăderea consumului și din zilele cu zero, pe care modelul le vede și ele, așa că modelul „ghicește” construcția scorului. Pe scorurile reale ale lui A cade la AUC ~0,85. Am respins-o (`reports/bilant/fusion_v2_comparison_trainLA.json`).
- Pierderea tehnică veche (peste 60 de zile) sau mică (sub 10 kWh/zi) scapă des: istoricul postului o învață ca normală, iar comparația cu luna trecută nu mai vede saltul. Am încercat și comparația cu normalul fără istoric (doar GIS): pierderea tehnică a urcat puțin, F1 macro a scăzut puțin, deci n-am păstrat-o în model.
- De ce: un post are adesea mai multe contoare cu probleme deodată, iar lipsa de la post e suma lor, deci nu arată care contor e de vină. Problemele mici (sub 2 kWh/zi) se pierd în zgomotul pierderii normale. Tipurile care nu schimbă totalul zilei (profil inversat, ceas decalat, salturi) nu se văd deloc în bilanț.
- **Să coboare scorul unui contor** pe un post fără lipsă: pe scorurile reale ale lui A asta strica lista (AUC 0,918 → 0,907), așa că fuziunea doar confirmă.
- **Să rezolve „nu sunt sigur” al lui A:** pe ziua demo, 0 din 5 cazuri corecte. Funcția e oprită.
- Contorul de client în lumea cu defectele lui A: F1 0,47. Multe tipuri ale lui A au lipsă mică sau zero la totalul zilei.

