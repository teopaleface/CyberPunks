# Status: Teo-A-contoare
Actualizat: 2026-11-07 16:16
Milestone curent: M4 gata; sarcina de reproducere în lucru (clona curată rulează)
Gata de merge: da (commit 68c1d1c)

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
- 14:00-14:14 Review independent (Codex, gpt-6.1-sol): 12 probleme găsite, toate tratate (commit f77f935). Cele mai importante: referința vecinilor SGCC calcula și din clienții de test (acum doar antrenare); conformal se potrivea pe scorul deja calibrat (acum pe scorul brut, garanția e validă); cuantila conformal cu o poziție prea sus; acoperirea mulțimii era numită „recunoaștere sigură”; unitatea suspectă se repara în tăcere (acum merge la om); oprirea timpurie amesteca gospodăriile. Runda 2 (14:16-14:22): 9 din 12 confirmate, 3 completate (commit f4aee2e). Features se aleg acum pe o validare din antrenare, nu pe calibrare. Acoperirea conformal e descrisă ca empirică, pentru că ferestrele de calibrare repetă gospodăriile. Împărțirile sunt doar pe gospodării. Furtul sigur nu mai cade din listă.

- 15:12 M3: figurile pentru prezentare în `reports/A/figures/`. `headline_precision.png`: furt real 0,81 față de 0,04 / 0,11, probleme subtile 0,61 față de 0,06 / 0,02. `ranking_at_k.png`: precizie și recall pe toată lista. `false_alarms_by_consumption.png`: pe SGCC, regula simplă trimite echipa la 19,4% dintre consumatorii foarte mici fără problemă, modelul la 0,4%. Paleta e validată cu scriptul dataviz.
- 15:18 Verificarea fuziunii cu bilanțul pe testul A (`fusion_check.py`, `reports/A/fusion_check.json`, `error_analysis.md` secțiunea 9); observațiile sunt mai jos, la „Cereri către orchestrator”.
- 15:24 M4: verificat dintr-o clonă curată (GitHub): `uv sync` în 25 s; `make a-predict` dă aceleași 524 / 563 de lucrări din pachetul din git; `make a-test` trece (89 de teste); `make a-all` de la zero în 7 minute. Metricile și lucrările au ieșit IDENTICE cu cele din repo. Model card-ul (`reports/A/model_card.md`) și comenzile (`docs/data/A.md`) sunt la zi.

- 16:15 Procentele absurde: în ieșirile actuale nu mai există niciunul (0 peste 1.000% în A.jsonl demo-vara și maine). Consola arăta un instantaneu vechi. Am adăugat totuși protecții: numitor minim de 0,1 kWh (consumul de noapte, scăderea față de istoric și vecini) și plafon la afișare în `label_ro` ("de peste 10 ori"), plus testul `test_labels_never_show_absurd_percentages` pe toate features-urile. Lucrările demo-vara sunt regenerate (532). Numele produsului în model card și `report.py` e acum Daybreak.
- Cifrele după refacere: SGCC precizia@K 0,80, PR-AUC 0,40; Londra 1,00 / 0,68; problemele subtile 0,63. Venn-ABERS pe grilă față de calculul exact: abaterea maximă 0,036 (grila are acum și puncte egal distanțate).

## Urmează
- **Sunt liber** (M0-M4 gata). Pot ajuta la B sau la alt fir; scrieți-mi direct în thread.
- La cerere: reparații pe A dacă planificatorul sau interfața au nevoie de ceva în lucrări sau în serii.

## Urmează (vechi, rezolvat)
- Lustruire pentru prezentare (figuri), M4: README-ul secțiunii, curățenie.
- Când îmi cereți: legarea cu fuziunea bilanțului (nu schimb nimic din partea mea, doar verific împreună).

## Blocaje
- Niciunul.

## Cereri către orchestrator
- **Pentru planificator (text absurd în jurnal):** în `outputs/demo/plans/demo-vara/audit.jsonl` apare „valoarea așteptată (20 lei) nu acoperă vizita (365 lei; scorul ar trebui să fie peste 1004%)”. Un scor peste 100% nu există. Când nici la scor 100% valoarea nu acoperă vizita, textul ar trebui să spună „nici sigur nu acoperă costul vizitei”.
- **Observații pentru firul bilanț** (fuziunea verificată pe testul A: populația demo, adevărul injectat; formula `fuse.combine_arrays` neschimbată; bilanțul postului construit din energia nemăsurată, cu zgomotul pierderilor normale sigma = 1 / 2 / 4% din consumul postului):
  - Vârful listei nu se schimbă: precizia@10 și @100 rămân 1,00, pentru că defectele evidente sunt deja primele. PR-AUC crește puțin (0,707 → 0,715 pe demo-vara, 0,679 → 0,688 pe maine, la sigma 2%).
  - **Ajută la** defectele care pierd multă energie: la sigma 1%, contor oprit 53% confirmate, citiri negative 55%, valoare blocată 27%. Pe acestea însă A le prinde oricum.
  - **Ajută puțin la furt:** 21-29% confirmate la sigma 1%, 5-11% la 2%. Pierderea unui singur contor (câțiva kWh/zi) e mică față de zgomotul postului (2% din ~1.000 kWh/zi).
  - **Nu poate ajuta** la tiparele care nu schimbă energia: profil aplatizat 4%, profil inversat 7%, ceas decalat 8%, goluri 1%, salturi 6%. Bine că fuziunea doar confirmă și nu coboară scorul.
  - **Risc:** bilanțul confirmă POSTUL, nu contorul. Pe un post cu energie lipsă, vecinii fără problemă cu o scădere naturală sunt confirmați și ei: concediu 24%, schimbarea ocupanților 14% la sigma 1%. Sugestie: când mai multe contoare marcate de A stau pe același post, lipsa postului să se împartă între ele (suma lipsurilor estimate față de E), nu să confirme fiecare contor separat.
  - În zona gri a lui A, cele confirmate au tot ~14% probleme reale (demo-vara), deci confirmarea nu le separă. Asta susține `RESOLVE_ABSTAIN = False`.
  - Pe ce merge bine: fuziunea ridică defectele confirmate. La precizia@100 calculată doar pe defecte, 0,90 → 0,94; doar pe furt, 0,10 → 0,05, pentru că defectele urcă peste furturi.
- Informare pentru planificator și interfață: A trimite acum ~520-560 de lucrări pe zi (înainte ~250-280). Sunt cele mai valoroase 250, plus toate furturile sigure, plus zona gri și datele insuficiente (la om). Planificatorul alege după capacitate; `extra.selection` spune de ce a intrat fiecare (`action`, `watch`, `unsure`, `data`).
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
  - `demo-vara`: 524 de lucrări (371 de vizite, 15 citiri la distanță, 138 la om); `maine`: 563 (356 de vizite, 8 citiri, 199 la om).
  - Lucrările pentru echipă sunt 91-94% probleme reale. Toate furturile sigure apar acum în listă (241-269 pe zi), chiar și cele cu valoare mică, pentru siguranță; capacitatea zilei o aplică planificatorul.
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
- 14:20 Alegerea features pe validare din antrenare (gospodării ținute deoparte), ca funcția de scor să nu vadă etichetele de calibrare (runda 2 a review-ului).
- 14:22 Toate furturile sigure intră în listă, chiar peste plafonul de 250 (siguranța înaintea plafonului).
- 15:24 M4 închis după verificarea din clona curată (cifre identice). Liber pentru alt fir.
