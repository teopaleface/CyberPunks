# Status: Teo-A-contoare
Actualizat: 2026-11-07 14:16
Milestone curent: M2 gata (14:10), M3 în mare parte gata; M1 gata la 13:33
Gata de merge: da (commit f77f935)

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
- 14:00-14:14 Review independent (Codex, gpt-6.1-sol): 12 probleme găsite, toate tratate (commit f77f935). Cele mai importante: referința vecinilor SGCC calcula și din clienții de test (acum doar antrenare); conformal se potrivea pe scorul deja calibrat (acum pe scorul brut, garanția e validă); cuantila conformal cu o poziție prea sus; acoperirea mulțimii era numită „recunoaștere sigură”; unitatea suspectă se repara în tăcere (acum merge la om); oprirea timpurie amesteca gospodăriile. Runda 2 (verificarea reparațiilor) rulează.

## Urmează (M2-M3)
- Runda 2 a review-ului: verific reparațiile.
- Lustruire pentru prezentare (figuri), M4: README-ul secțiunii, curățenie.

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
Comenzile: `make a-evaluate` (sau `uv run python -m cyberpunks.a_contoare.evaluate --retrain`), `make a-robustness`, `make a-report`. Toate tabelele sunt în `reports/A/error_analysis.md`. K = 1% din contoarele din test; intervalele sunt bootstrap 95%. Cifrele de mai jos sunt după reparațiile din review.
- SGCC, etichete reale de furt, 8.475 de clienți nevăzuți (723 cu furt), precizia@K / PR-AUC / ROC-AUC:
  - modelul: 0,812 [0,73-0,88] / 0,397 / 0,818;
  - regula simplă: 0,035 / 0,080 / 0,496; regula VEE completă: 0,106 / 0,097 / 0,556; IsolationForest: 0,165 / 0,111 / 0,587.
- Londra, probleme injectate (sintetic), 13.028 de eșantioane (597 cu probleme):
  - modelul: 1,00 / 0,671 / 0,910; regula simplă: 0,46 / 0,19 / 0,70; regula VEE: 0,53 / 0,26 / 0,80.
  - Doar problemele subtile: modelul 0,61 / 0,40; VEE 0,02 / 0,06.
- De ce 1,00: K = 130 e 22% din probleme, iar cele 215 defecte evidente umplu vârful listei. La K = 597 (numărul de probleme), precizia e 0,64; tabelul pe K e în `error_analysis.md`, secțiunea 2.
- Scurgeri: nicio gospodărie sau client în două seturi; testul cu etichete amestecate dă PR-AUC 0,046 (prevalența 0,046) pe Londra și 0,106 (0,085) pe SGCC. E o verificare de bun-simț; proveniența fiecărei informații e în secțiunea 1.
- Conformal pe test, Londra:
  - acoperirea mulțimii: 99% la normale, 70% la probleme (țintele);
  - ca decizii: 60% din probleme recunoscute sigur, cu precizie de 75%;
  - 1% din contoarele normale sunt declarate „problemă”, 2% trimise la om.
- Demo (adevărul injectat): 15.850 de contoare.
  - `demo-vara`: 391 de lucrări (235 de vizite, 15 citiri la distanță, 24 de urmărit, 117 la om); `maine`: 408.
  - Lucrările pentru echipă sunt 97-99% probleme reale; cele la om, 11-23%.
  - Din contoarele normale, 0% ajung la echipă și 1% la om.
- Robustețe la zile lipsă: PR-AUC 0,68 / 0,61 / 0,58 / 0,55 la 0 / 10 / 30 / 50%. SGCC pe timp: ROC-AUC 0,70 (regula: 0,47).
- Calibrare: ECE 0,004 pe testul Londra, 0,004-0,005 pe demo. Venn-ABERS pe grilă față de calculul exact: abatere medie 0,0002, maximă 0,017.

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
- 14:10 Conformal pe scorul brut al modelului, nu pe cel calibrat (cerință din review: garanția split conformal). Pragurile, traduse în probabilități, apar doar în explicații.
- 14:10 Unitate suspectă (valori de ~1.000 de ori prea mari): scorăm după împărțire, dar decide un om. Poate fi și un defect (multiplicator greșit).
- 14:10 Lucrările sigure își păstrează acțiunea până la 250 pe zi, după valoare. Urmărirea rămâne doar pentru valoare sub 20% dintr-o vizită. Tăierea pe capacitate o face planificatorul.
