# Status: Teo-A-contoare
Actualizat: 2026-11-07 13:33
Milestone curent: M1 gata (13:33); lucrez la M2
Gata de merge: da (commit 9c42400)

## Făcut
- 13:30 M0: `docs/research/A.md`, date descărcate cu sume de control (SGCC, 45 de fișiere Low Carbon London).
- M1, cap-coadă:
  - features (`features.py`): 19 zilnice și 11 din citirile la 30 de minute, fiecare cu motiv și explicație în română;
  - baseline-uri: regula simplă VEE (zero ≥ 7 zile sau scădere ≥ 50%) și IsolationForest;
  - modele: `a-lgbm` (Londra, normal / defect / manipulare) și `a-lgbm-sgcc` (SGCC, furt real); calibrare Venn-ABERS, "nu sunt sigur" prin conformal Mondrian;
  - evaluare pe test separat, cu `reports/A/metrics.json` valid, `metrics_full.json` și 4 figuri;
  - `predict`: lucrări și serii valide pentru `demo-vara` (2025-07-08) și `maine`, fiecare cu SHAP, cazuri similare, valoare în lei și motivul abținerii.
- Topologie sintetică: 400 de posturi (187 din OpenStreetMap) și 10.000 de contoare în București-Ilfov, cu zone din poligoanele reale.
- `predict.run()` merge și fără date descărcate, din `models/release/A/` și `data/samples/A/demo_pack.npy.xz` (2,7 MB). Cu sau fără datele complete dă aceleași lucrări (verificat).
- Am găsit și reparat un artefact: injecțiile prin înmulțire dădeau valori nerotunjite, iar modelul semnala 46% din contoarele demo. După rotunjirea la 0,001 kWh semnalează 5-6%.
- `git merge Teo` făcut de două ori (ultima la 13:28); `make check` trece (114 teste, ruff curat).

## Urmează (M2, până la 21:30)
- Features raportate la vecini (scăderea și panta față de post), ca sezonul să nu mai pară problemă: în iulie, 11% din contoarele demo ies "nu sunt sigur", față de 5% pe testul de toamnă.
- Features noi pentru ce prindem slab: decalajul de ceas (corelație cu decalaj), deriva lentă față de vecini.
- O regulă VEE completă (goluri, salturi, negative, valori repetate) ca al doilea baseline, mai corect decât regula simplă.
- Încercare: un singur model antrenat pe Londra + SGCC; îl păstrez doar dacă nu strică niciun test.
- Analiza erorilor (pe tipuri, pe consum, pe goluri), teste de robustețe, model card.

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Registrul de posturi al lui C (`data/samples/C/posts.csv`) încă nu există în `Teo`. Când apare, leg cele 10.000 de contoare de aceleași `post_id` (azi au posturile mele, `PT-0001`..`PT-0400`, în `data/samples/A/posts.csv`). Încape la M2 dacă registrul apare până pe la 19:00.
- Pentru firul bilanț: API-ul public pe care îl importă rămâne la fel. `inject.py`: `inject`, `sample_kind`, `sample_and_inject`, `Injection`, `KIND_*`, `PARAMS`. `lcl.py`: `load_lcl`, `daily_from_halfhours`, `build_samples`, `kind_probs`, `value_lei`. Am adăugat `lcl.quantize(hh)` și `lcl.economics()`. **Sfat:** după orice injecție, rotunjiți cu `quantize()`, altfel modelul învață valorile nerotunjite în loc de tipar (ni s-a întâmplat).
- Opțional, pentru planificator: componenta fixă a valorii unui contor defect e azi o vizită evitată (`meters.inspection_visit_cost_lei`, CALCUL). Dacă vreți altă cifră, adăugați `meters.faulty_meter_fixed_value_lei` în `config/economics.yaml`; o citesc automat.

## Cum se rulează (comenzile exacte)
- Lucrările, fără descărcări (~10 s): `make a-predict` sau `uv run python -m cyberpunks.a_contoare.predict --scenario demo-vara` (și `--scenario maine`, `--date YYYY-MM-DD`).
- Din cod: `from cyberpunks.a_contoare.predict import run; run("demo-vara", None)` -> `outputs/work_items/demo-vara/A.jsonl`.
- Tot de la zero (~5 min): `make a-all` (descărcare, features, antrenare, evaluare, lucrări). Evaluarea singură: `uv run python -m cyberpunks.a_contoare.evaluate --retrain`.
- Teste: `make a-test`.
- Ieșiri în plus: `outputs/work_items/<s>/A_summary.json` (cifrele zilei) și `A_ground_truth.csv` (ce am injectat, doar pentru evaluarea agentului, nu pentru decizii).
- Câmpuri în `extra`: `series_ref`, `p_faulty`, `p_tamper`, `conformal`, `post_id`, `estimated_kwh_lost_per_day`, `rule_vee_fired`, `smart_meter` (false = contorul nu comunică acum), `comm_down`, `level_kwh_day`, `low_consumption_guard`.

## Cifre (doar din scripturi, cu comanda)
Comanda: `uv run python -m cyberpunks.a_contoare.evaluate --retrain`. K = 1% din contoarele din test; intervalele sunt bootstrap 95%.
- SGCC, etichete reale de furt, 8.475 de clienți nevăzuți (723 cu furt):
  - modelul: precizia@K 0,765 [0,66-0,86], PR-AUC 0,367, ROC-AUC 0,802;
  - regula simplă: 0,035 / 0,080 / 0,496; IsolationForest: 0,129 / 0,098 / 0,547.
  - Reper din literatură, fără scurgeri: ROC-AUC 0,78-0,92.
- Londra, probleme injectate (sintetic), 13.028 de eșantioane din gospodării nevăzute, sept. 2013 - feb. 2014 (597 cu probleme):
  - modelul: precizia@K 1,00, PR-AUC 0,669, ROC-AUC 0,907; regula simplă: 0,52 / 0,20 / 0,70.
  - Valoarea capturată în primele 130 de vizite: model față de regulă (lei), în `metrics_full.json`.
- Pe tipuri, modelul prinde aproape tot la contor oprit, blocat, goluri, negative și h3. Slab: ceas decalat (AUC 0,63), sub-înregistrare (0,78), bypass (0,76).
- Alarme false la concediu: 4% (regula: 32%).
- Etică: alarmele false sunt mai multe la chintila de jos a consumului (5,2% față de 1-1,6%). De aceea furtul suspectat la consum mic merge întâi la un om.
- Demo (`A_summary.json`, adevărul injectat): pe `demo-vara`, 249 de lucrări și 97% din vizitele recomandate sunt probleme reale; pe `maine`, 264 de lucrări.

## Decizii (cu ora)
- 12:48 Faza 0 cu 4 subagenți de cercetare în paralel.
- 13:05 Londra: doar fișierele 0-44, prin cereri pe intervale de octeți.
- 13:30 SGCC se împarte pe clienți, nu pe timp: golurile scad de la ~35% (2014-2015) la ~1,5% (2016).
- 13:30 Metrica principală: precizia@K, K = 1% (cam o săptămână de vizite pentru 3 echipe la 10.000 de contoare); PR-AUC secundară.
- 13:12 Două modele: `a-lgbm` (Londra, folosit de agent) și `a-lgbm-sgcc` (SGCC, etichete reale). `metrics.json` descrie `a-lgbm`; cheile `sgcc_*` sunt ale modelului SGCC.
- 13:16 Rotunjire la 0,001 kWh după injecții (artefactul descris mai sus).
- 13:20 Valoarea unui contor defect = energia lipsă + o vizită evitată (din config, nu din cod).
- 13:25 Pachetul demo în git (2,7 MB, profile CC BY 4.0), ca `predict.run()` să meargă la planificator fără descărcări.
- 13:25 Etică: furtul suspectat în chintila de jos a consumului merge la om, nu direct la vizită.
