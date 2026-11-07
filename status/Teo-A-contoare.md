# Status: Teo-A-contoare
Actualizat: 2026-11-07 14:15
Milestone curent: M2 gata (14:10), M3 în mare parte gata; M1 gata la 13:33
Gata de merge: da (commit ea3ccff)

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

- 14:00 Contoarele stau acum pe posturile din registrul comun al lui C (PT-1001..PT-1300): 15.850 de contoare integrate = 58,81% din cei 27.045 de clienți ai celor 300 de posturi (gradul de integrare Muntenia la 31.12.2025, din memory/12). Posturile mele PT-0001..PT-0400 sunt scoase; `data/samples/A/meters.csv` are `post_id` din registru.
- 13:45 M2: 10 features noi (alese pe calibrare), regula VEE completă ca al doilea baseline, metrici pe problemele subtile, praguri conformal noi (1% / 30%), experimente de robustețe (`reports/A/robustness.json`), 10 teste de robustețe.
- 14:00 Precizia@K = 1,00 verificată (cerința orchestratorului de la 13:55): fără scurgeri, explicată mai jos la Cifre.

- 14:10 `reports/A/error_analysis.md` și `reports/A/model_card.md`, generate de `make a-report` din cifrele scripturilor (nicio cifră scrisă de mână); `select_features.py` arată alegerea features pe calibrare.
- 14:07 Review independent pornit la Codex (scurgeri, calibrare, bug-uri, afirmații nesusținute); repar ce găsește.

## Urmează (M2-M3)
- Reparațiile din review-ul Codex.
- Texte mai clare pentru dispecer: zona gri, procentele absurde la istoric scurt, factori cu valoarea 0, numere cu virgulă; contoarele sigure din afara primelor 150 rămân cu acțiunea lor (capacitatea o decide planificatorul).
- Figura de calibrare cu bin-uri pe tot intervalul 0-1.

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Făcut: contoarele A folosesc `post_id` din registrul C (`data/samples/C/posts.csv`); citesc CSV-ul direct, ca să nu import pandapower prin `posts.py`. Dacă C schimbă registrul, regenerez cu `uv run python -m cyberpunks.a_contoare.topology`.
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
Comanda: `uv run python -m cyberpunks.a_contoare.evaluate --retrain` (cifrele de mai jos) și `make a-robustness`. K = 1% din contoarele din test; intervalele sunt bootstrap 95%.
- SGCC, etichete reale de furt, 8.475 de clienți nevăzuți (723 cu furt), precizia@K / PR-AUC / ROC-AUC:
  - modelul: 0,812 [0,74-0,91] / 0,405 / 0,820;
  - regula simplă: 0,035 / 0,080 / 0,496; regula VEE completă: 0,106 / 0,097 / 0,556; IsolationForest: 0,188 / 0,105 / 0,554.
- Londra, probleme injectate (sintetic), 13.028 de eșantioane (597 cu probleme):
  - modelul: 1,00 / 0,676 / 0,910; regula simplă: 0,52 / 0,20 / 0,70; regula VEE (pragurile alese pe calibrare): 0,61 / 0,27 / 0,80.
- Doar problemele subtile (fără zero, blocat, negative, goluri): modelul 0,688 / 0,403; VEE 0,016 / 0,059; regula simplă 0,062 / 0,065.
- **De ce precizia@K = 1,00 pe Londra:**
  - K = 130 e doar 22% din cele 597 de probleme. Testul are 215 defecte evidente; primele 130 sunt 117 evidente (blocat 44, oprit 33, negative 29, goluri 11) și 13 furturi (h4, h6, h3). La VEE, 48 din primele 130 sunt contoare normale.
  - La K mai mare, modelul scade: 0,93 (K = 200), 0,90 (300), 0,81 (400), 0,645 (597 = numărul de probleme), 0,37 (1.194). VEE la K = 597: 0,31.
  - SGCC: 0,82 (K = 50) -> 0,43 (K = 723 = numărul de furturi).
  - Scurgeri: nicio gospodărie sau client în două seturi; testul începe la 7.09.2013, după ultima zi de antrenare (24.08.2013). Cu etichete amestecate la întâmplare, PR-AUC cade la prevalență: 0,048 (prevalență 0,046) pe Londra, 0,098 (0,085) pe SGCC.
- Robustețe la date lipsă (populația demo, adevărul cunoscut): PR-AUC 0,68 / 0,62 / 0,58 / 0,54 la 0 / 10 / 30 / 50% zile lipsă. La 70%, agentul se abține din lipsă de date la 83% din contoare.
- SGCC pe timp (antrenare pe ferestrele din 2015, test pe clienți nevăzuți în 2016): ROC-AUC 0,71, regula 0,47.
- Conformal pe testul Londra: acoperire 99,1% la normal (țintă 99%), 68,8% la probleme (țintă 70%). 2,2% din eșantioane sunt "nu sunt sigur".
- Calibrarea pe populația demo (adevărul injectat): ECE 0,003; media scorurilor 0,053, față de prevalența 0,053.
- Demo (`A_summary.json`): 15.850 de contoare evaluate; `demo-vara` dă 267 de lucrări (148 de vizite, 2 citiri la distanță, 40 de urmărit, 77 la om); `maine` dă 281. Precizia vizitelor față de adevăr e 0,99-1,00, din același motiv ca mai sus: primele 150 sunt mai ales defecte evidente cu pierderi mari.

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
- 13:45 Features noi alese pe setul de calibrare, nu pe test; testul a fost privit o singură dată pe versiune.
- 13:50 Conformal: alpha_normal 1%, alpha_problem 30% (zona gri 0,12-0,30, cu 16-26% probleme reale), alese pe calibrare și verificate pe test și pe demo.
- 14:00 Contoarele pe registrul comun C, cu 58,81% din clienți ca grad de integrare (sursă: memory/12).
- 14:12 Nu combin SGCC și Londra într-un singur model: povestea rămâne clară (modelul agentului pe Londra, aceleași features verificate pe furt real în SGCC), iar un model comun ar putea învăța „ce set de date e” în loc de tipar.
