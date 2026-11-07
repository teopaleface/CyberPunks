---
format: 1920x1080, 30 fps
duration: ~31 s
product: Daybreak (fostul „Tura de mâine”, decizia lui Teo din 7 nov.)
language: engleză pe ecran, cel mult 5 cuvinte pe cadru
audience: juriul PPC la SmartHack XI 2026 și oricine nu știe nimic despre rețele
music: „POWER” (instrumental), doar în exportul local; exportul versionat are altă muzică
status: DOAR STRUCTURA. Filmul e oprit până aprobă Teo cadrele statice.
---

# Daybreak: structura filmului (varianta 4)

Ce e aici: ordinea scenelor, textul de pe ecran, ce informație duce fiecare scenă și de unde vine fiecare afirmație.

Ce nu e aici: culorile, logoul, imaginile și obiectele 3D. Le alege Teo din cadrele generate în firul lateral (`presentation/frames-codex/v1/`, `presentation/brand-lab/r2/`). Până atunci nu fixăm nimic din aspect în scene. Logoul cu soarele peste traseu e respins: pe cadre apare doar cuvântul „Daybreak”.

Povestea urmează cele 10 cadre din `presentation/frames-codex/v1/FRAMES.md` (problema → cine o are → produsul → cum merge → încrederea → rezultatul → pentru cine e). Textele de mai jos sunt copiate de acolo. Ce propun să se schimbe e la final, în „Observații pentru firul lateral”.

| # | Cadrul | Textul de pe ecran | Ce află privitorul | Sursa afirmației |
|---|---|---|---|---|
| 1 | f01 | `Storm hits Banat.` | S-a întâmplat ceva real, azi-vară. | Cod roșu ANM de vijelii pe 8 iulie 2025, în toate cele 4 județe Rețele Electrice Banat (`docs/research/B.md`, secțiunea 3) |
| 2 | f02 | `Homes go dark.` | Oamenii rămân fără curent. | Prefectul Timișului: circa 40.000 de consumatori afectați, cumulat 7-9 iulie 2025 (`docs/research/B.md`, pressalert.ro). Fără cifră pe ecran |
| 3 | f03 | `Where do crews go first?` | Problema dispecerului: echipele sunt puține, lucrările multe. | Tema PPC (`memory/07-tema-ppc.md`) |
| 4 | f04 | `Fallen poles.` / `Stolen power.` / `Too much sun.` | Trei feluri de lucrări pentru aceleași echipe. | Problemele B (furtuna), A (contoarele) și C (prosumatorii) |
| 5 | f05 | `Daybreak` / `Tomorrow's crews, planned tonight.` | Numele și promisiunea. | Agentul face planul seara, pentru dimineața următoare |
| 6 | f06 | `One click. Every crew planned.` | Cum se folosește: un buton. | Butonul „Rulează agentul” din consolă |
| 7 | f07 | `Every crew knows where to go.` | Rezultatul planului: fiecare echipă are traseul ei. | Planul pentru 8 iulie 2025 (`outputs/demo/plans/demo-vara/plan.json`) |
| 8 | f08 | `Not sure? It asks you.` | Omul rămâne la decizie. | Coada „Nu sunt sigur” din consolă (regula R-LOW-CONFIDENCE) |
| 9 | f09 | `+49%` / `more value. Same crews.` / `30-day simulation` | Dovada, cu cifra noastră. | `reports/planner/agent_eval.json` prin `presentation/scripts/cifre_film.py` (nu se scrie de mână) |
| 10 | f10 | `Daybreak` / `For Rețele Electrice dispatchers` / `CyberPunks · SmartHack 2026` | Pentru cine e și cine l-a făcut. | — |

## Cifra din cadrul 9

- Acum: +49% (agentul 1.051.842 lei față de 706.556 lei la „primul venit, primul servit”, cea mai bună strategie simplă; 30 de zile, sămânța 7, 120 de contoare).
- Comanda care o refăce: `uv run python -m cyberpunks.planner.evaluate --days 30 --seed 7 --meters 120`.
- E provizorie: se recitește din `reports/` după 21:30, la fiecare export.

## Ritmul (pentru când repornim filmul)

Fără aliniere până la aprobare. Ca plan: în „POWER” tobele intră la 9,47 s, iar după ele o măsură are 3,12 s. Numele cade pe intrarea tobelor, iar fiecare cadru de după nume ține câte o măsură:

| Cadrele | Timp |
|---|---|
| f01-f04 (cârligul și problemele, pe intro și pe creștere) | 0-9,47 s |
| f05 numele, pe intrarea tobelor | 9,47-12,59 s |
| f06 un clic | 12,59-15,71 s |
| f07 harta | 15,71-18,83 s |
| f08 „Not sure?”, pe pauza piesei; clicul pe Approve aduce înapoi tobele | 18,83-21,94 s |
| f09 cifra | 21,94-25,06 s |
| f10 finalul, ținut cel puțin 3 s | 25,06-~31 s |

Tranzițiile: aceeași direcție peste tot (spre stânga), tăieturi din mers, fără cadre goale la tăietură (intrarea începe deja la jumătatea drumului), cursorul mare apasă butoanele din cadrele 6 și 8.

## Observații pentru firul lateral (textele din FRAMES.md)

1. f07 are 6 cuvinte (`Every crew knows where to go.`), peste regula de 5. Propun `Every crew knows where.`
2. f09: nota de subsol ar trebui să spună și cu ce comparăm: `30-day simulation vs. first come, first served`. Cifra e provizorie până după 21:30.
3. f08: în consolă butoanele sunt Aprobă, Respinge și Amână. `Skip` nu există; ar merge `Later` (Amână) sau `Reject` (Respinge).
4. f01: data `July 8, 2025` (subtitlu mic) ar arăta că ziua e reală. E opțională.
5. f10: numele oficial e SmartHack XI 2026.
