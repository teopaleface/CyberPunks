# Două tipuri de echipe: IT/MT și JT

Regula dată de Tudor pe 8 nov. 2026, ~04:00. Există două tipuri de echipe care pot fi trimise la lucrări:

- **echipe de înaltă și medie tensiune** (`it_mt`): abilitățile `hv_grid`, `mv_grid`;
- **echipe de joasă tensiune** (`jt`): abilitățile `lv_grid`, `metering`.

Fiecare tip ia **doar** lucrările specializării lui.

## Cum e în cod

- `config/crews.yaml`: secțiunea `crew_types` definește cele două tipuri și abilitățile lor. Fiecare echipă are `type: it_mt`
  sau `type: jt` și nu își mai scrie singură abilitățile. `Settings.load` (`planner/settings.py`, `load_crews`) refuză trei
  situații: o echipă cu `skills`, un tip necunoscut și o abilitate pusă la două tipuri. Așa nu mai poate exista o echipă
  „mixtă”, cum erau înainte E-BV-3 (JT + MT) sau E-DV-1 (contoare + JT + MT).
- Potrivirea lucrare-echipă nu s-a schimbat: lucrarea cere o abilitate (`effort.crew_skill`), iar echipa trebuie să o aibă.
  Ce s-a schimbat e că abilitățile echipei vin acum dintr-un singur tip.
- Cine ce face:
  - contoare (A), bilanț, inspecții JT la post și treptele C (priză, faze, analizor; firul C le marchează `lv_grid`) → JT;
  - furtunile B pe zone mari (`mv_grid`, de la 2.000 de clienți) → IT/MT; furtunile pe zone mici (`lv_grid`) → JT.
- O lucrare care cere abilități de la ambele tipuri (de exemplu o combinație C cu o treaptă JT și una MT) nu mai intră la o
  singură echipă. Motivul spune că trebuie împărțită în două lucrări și că decide dispecerul. Lipsa unei echipe de tipul cerut
  se spune explicit: „Nicio echipă de înaltă și medie tensiune…”.
- Ordinele de lucru PDF scriu tipul echipei, iar interfața web citește tipul din config (`web/lib/data/files.ts`).
- Teste: `tests/planner/test_crew_types.py`.

## Echipele (SIMULATE), după regulă

| Tip | Echipe |
|---|---|
| JT | E-BV-1, E-BV-2, E-BE-1, **E-BE-2** (3 oameni), E-CT-2, **E-DV-1** (3 oameni) |
| IT/MT | E-BV-3, E-CT-1, E-TM-1, E-AR-1, E-RS-1 |

Două alegeri ale mele, de confirmat:

- **E-BE-2** era JT + MT. A devenit JT: treptele C (priza, fazele) cer 3 oameni de joasă tensiune, iar în București toate
  celelalte echipe JT au 2 oameni.
- **E-DV-1** făcea de toate. A devenit JT: altfel Banatul nu avea nicio echipă de joasă tensiune pentru furtunile pe zone mici.

## De întrebat

- Schimbarea prizei la postul MT/JT o face, în realitate, o echipă JT sau una MT? Firul C o marchează `lv_grid`, pentru că
  întreruperea îi afectează pe clienții JT. Dacă e lucru MT, schimbarea e de un rând în `c_prosumatori/actions.py`.
- Câte echipe de fiecare tip are o zonă reală?
