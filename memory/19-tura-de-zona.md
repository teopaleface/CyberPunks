# Tura de zonă: când pleacă echipa la o lucrare

Implementat de Tudor pe 8 nov. 2026, ~03:30, după răspunsul mentorului PPC (`10-raspunsuri-mentor.md`). Cod: `src/cyberpunks/planner/dispatch.py`,
setările în `config/planner.yaml`, secțiunea `dispatch`. Teste: `tests/planner/test_dispatch.py`.

## Ce a spus mentorul

Se evaluează urgența. Dacă nu e ceva de tipul risc de incendiu, lucrarea așteaptă sfârșitul săptămânii, până se adună mai multe
lucrări în aceeași zonă (exemplul lui: clientul cu contorul defect). Dar nicio lucrare nu are voie să treacă de termenul legal,
orice s-ar fi stricat.

## Cum funcționează

Pasul nou stă între reguli (`decide.py`) și trasee (`routing.py`). Atinge doar vizitele obișnuite: `R-A-VISIT`, `R-A-VISIT-MEDIUM`,
`R-A-VISIT-NO-REMOTE`, `R-BILANT-VISIT`, `R-BILANT-GRID`. **Nu se amână niciodată:** siguranța (`R-SAFETY`, de exemplu șunt cu
risc de incendiu), furtunile (B), tensiunea (C, cu preaviz propriu) și ce a aprobat un om.

Pentru fiecare vizită amânabilă, în ordine:

1. **Termenul legal** (`R-LEGAL-DEADLINE`): dacă azi e ultima zi sigură, lucrarea pleacă azi și e obligatorie. Ultima zi sigură
   e termenul minus o zi lucrătoare de rezervă, pentru o echipă care nu termină la timp. Termenul: contor defect, 10 zile
   lucrătoare de la sesizare (5 zile peste 100 kW), după Rețele Electrice și standardul ANRE (articolul exact e de confirmat).
   Pentru celelalte lucrări (manipulare, pierdere la post) nu știm de un termen legal, deci folosim o limită internă tot de 10 zile.
   Termenul curge de la `extra.registered_at` (prima sesizare, păstrată de la o zi la alta), altfel de la `created_at`.
2. **Tura de zonă** (`R-WEEKLY-TOUR`): vineri, iar dacă vinerea e sărbătoare, ultima zi lucrătoare dinainte. Ce nu a încăput
   într-o tură trecută pleacă la prima ocazie, nu mai așteaptă încă o săptămână.
3. **Așteptarea e prea scumpă** (`R-WAIT-COSTLY`): pierderea până la tură (valoarea așteptată / 90 de zile × zilele de așteptare)
   depășește 55 lei, cât economisește în medie tura pe o vizită. Lucrarea pleacă acum.
4. **Zona e plină** (`R-ZONE-FULL`): lucrările din aceeași celulă de ~5 km umplu 75% dintr-o tură, deci drumul se împarte deja.
5. **Pe drum** (`R-ON-THE-WAY`): o lucrare care pleacă oricum azi, cu aceeași abilitate, e la cel mult 3 km. Lucrarea intră
   opțional, iar solverul o ia doar dacă ocolul merită.
6. Altfel, **amânată** (`R-WEEKLY-BATCH`, decizia `deferred`). Motivul scrie ziua turei, termenul și costul așteptării.

Dacă o lucrare cu termenul în pericol nu încape nicăieri, dispecerul primește o alertă critică (`R-LEGAL-DEADLINE-NO-CREW`).
Rezumatul pasului ajunge în `run.json`, sub cheia `dispatch`.

## Ce economisește și de ce (lume SINTETICĂ)

Comanda: `uv run python -m cyberpunks.planner.batching_benchmark`. Rezultatul e în `reports/planner/weekly_batching.{md,json}`.
Simularea: 4 săptămâni, 40 de contoare semnalate pe zi în București-Ilfov, aceleași lucrări, reguli, echipe și solver.

| | a doua zi | tura de zonă |
|---|---:|---:|
| Vizite făcute | 116 | 116 |
| Zile-echipă pe teren | 34 | **26 (−24%)** |
| Opriri pe zi-echipă | 3,4 | 4,5 |
| Kilometri | 2.403 | **1.923 (−20%)** |
| Costul drumului | 12.863 lei | 10.638 lei (−2.225 lei) |
| Costul așteptării (energie pierdută) | 2.007 lei | 4.263 lei (+2.257 lei) |
| Așteptare medie / maximă (zile lucrătoare) | 1 / 1 | 3,2 / 6 |
| Depășiri de termen | 0 | **0** |

**De ce scade costul.** Drumul de la bază până în zonă e partea scumpă a unei vizite, cam 21 km dus-întors. Când așteaptă
câteva zile, lucrările din aceeași zonă se adună. O echipă le face apoi pe toate într-un singur drum: 4,5 opriri pe zi
în loc de 3,4.

**Câștigul real vine din zilele-echipă, nu din motorină.** Banii economisiți pe drum (~2.200 lei) sunt cam cât pierde
așteptarea (~2.260 lei): contorul defect sau manipulat pierde energie până la vizită. Câștigul net vine din cele **8 zile-echipă
eliberate** în 4 săptămâni (−24%). Echipele nu costă mai puțin, dar în acele zile fac altă muncă: avarii, branșamente,
lucrări urgente. Le socotim la 950 lei pe zi-echipă (8 h × 2 oameni × 59,4 lei/h), adică ~7.600 lei. Net: ~7.570 lei
în 4 săptămâni, ~65 lei pe vizită.

**De ce nu se încalcă legea.** Termenul se verifică la fiecare rulare, cu o zi lucrătoare de rezervă. Tura de vineri lasă
oricum cel mult ~5 zile lucrătoare de așteptare față de un termen de 10. Testul `test_waiting_never_passes_the_deadline`
încearcă toate combinațiile de zi a sesizării și zi a planului.

## Actualizare după regula tipurilor de echipe (8 nov., ~04:15)

Cu echipele împărțite în IT/MT și JT (`20-tipuri-de-echipe.md`), aceeași simulare dă: km −21% (2.403 → 1.891), zile-echipă
34 → 28 (−18%), 0 termene depășite, net ~5.510 lei în 4 săptămâni. Așteptarea maximă a urcat la 9 zile lucrătoare.
Cauza: vinerea, cele 4 echipe JT din București fac ~20–22 de vizite, iar săptămâna aduce ~29. O lucrare din 10 nov. nu a
încăput nici pe 13, nici pe 20 nov. și a plecat obligatoriu pe 23 nov., în ultima zi sigură. Garda termenului a funcționat,
dar o singură zi de tură pe săptămână e la limita capacității. De încercat `tour_weekdays: [3, 4]` (joi și vineri).

## Limite și ce mai e de făcut

- Cifrele vin dintr-o lume sintetică: arată ordinul de mărime, nu date PPC.
- Pragul de 55 de lei din `max_waiting_cost_lei` vine din prima rulare a simulării. În rularea finală tura economisește ~85 lei
  pe vizită, deci pragul e prudent.
- `CORECTURI.md` P0-M2 spune că mutarea mai devreme o decide dispecerul. Aici o face agentul (`R-WAIT-COSTLY`), cu motivul scris.
  Dacă vrem altfel, regula se poate transforma în propunere către dispecer.
- Site-ul tot spune „Planul de mâine”. Redenumirea din P0-M2 („Urgent azi” / „Tura de vineri”) nu e făcută.
- Testele vechi ale planificatorului rulează cu amânarea oprită (`tests/planner/conftest.py`), pentru că ele verifică
  mecanica traseelor.
