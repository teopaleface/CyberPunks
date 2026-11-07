# Status: Teo-A-contoare
Actualizat: 2026-11-07 13:38
Milestone curent: M1 (M0 gata la 13:38)
Gata de merge: nu

## Făcut
- 12:45 Citit instrucțiunile, memoria, planul, contractele. `uv sync` și `make check` merg.
- 13:30 M0: `docs/research/A.md` (SGCC: licență, structură verificată, reper din literatură; Londra: CC BY 4.0; atacurile h1-h6 și defectele VEE; calibrare și conformal).
- 13:35 Date descărcate cu sume de control: SGCC (42.372 de clienți, 3.615 cu furt) și 45 de fișiere Low Carbon London (~1.500 de gospodării, 30 min). Sumele LCL în `data/samples/A/checksums_lcl.sha256`.
- 13:20 Generatorul de defecte și furturi injectate (`inject.py`, 7 defecte, 8 tipuri de furt, 2 schimbări normale), 54 de teste.
- 13:35 Features (`features.py`): 19 zilnice + 11 din citirile la 30 de minute, fiecare cu motiv și explicație în română.

## Urmează
- SGCC: baseline-uri (regulă VEE, IsolationForest) și primul LightGBM, pe clienți nevăzuți.
- Londra: eșantioane cu defecte injectate, model normal / defect / manipulare.
- Topologia sintetică București-Ilfov (în lucru, subagent), apoi `predict` pentru `demo-vara` și `maine`.
- M1 (17:30): `reports/A/metrics.json` valid, `A.jsonl` valid pentru ambele scenarii.

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Niciuna deocamdată.

## Cum se rulează (comenzile exacte)
- `uv run python -m cyberpunks.a_contoare.download` (SGCC + 45 de fișiere LCL, ~260 MB descărcat, verifică SHA-256)

## Cifre (doar din scripturi, cu comanda)
- Încă nimic din model.

## Decizii (cu ora)
- 12:48 Faza 0 cu 4 subagenți de cercetare în paralel.
- 13:05 Londra: doar fișierele 0-44 (tarif fix), prin cereri pe intervale de octeți, nu toată arhiva de 796 MB.
- 13:30 SGCC se împarte pe clienți, nu pe timp: golurile scad de la ~35% (2014-2015) la ~1,5% (2016), deci o împărțire pe timp ar învăța schimbarea de colectare, nu furtul.
- 13:30 Metrica principală: precizia@K cu K = 1% din contoare (cam cât verifică 3 echipe de contorizare într-o săptămână, la 10.000 de contoare); PR-AUC secundară.
- 13:30 Calibrare isotonic (FrozenEstimator în scikit-learn 1.9), interval Venn-ABERS, "nu sunt sigur" prin conformal Mondrian; implementate de noi, fără pachete noi.
