# Calitate ML pe baremul PPC, 8 noiembrie 2026

**20/25, estimare neoficială pe `origin/main` la `68d62bf`.** Tema PPC enumeră cinci aspecte, fără puncte individuale. Pentru această evaluare am folosit câte cinci puncte pe aspect. Am verificat commitul de pe remote și am rulat codul dintr-o copie temporară. Modelele și rapoartele A, B, C și bilanț sunt identice cu cele de la `cfc097a`, baza evaluării de la 06:00.

| Aspect | Puncte | Dovezi și limite |
|---|---:|---|
| Date | 3/5 | Surse citate și etichete sintetice marcate. A activ are consum real și probleme injectate. C și bilanțul au etichete simulate. Datele sintetice sunt permise, iar etichetele de teren lipsesc pentru sarcinile respective. |
| Model | 5/5 | Modele proprii antrenate și livrate, cod de antrenare, intrări motivate, calibrare și metrici potrivite. |
| Test separat | 3/5 | Separări pe gospodării și timp (A), ani și state (B), topologie și timp (C), posturi (bilanț). Pentru v2 bilanț, Optuna folosește validarea, iar păstrarea v2 depinde și de același test pe care se raportează scorul. Testul principal B folosește vremea din arhivă. Testul românesc e scurt și fără furtuni severe. |
| Baseline | 5/5 | Comparații pe aceleași seturi cu reguli de contoare, rafală și climatologie, regresie simplă, I²R și reguli de diagnostic. |
| Analiza erorilor | 4/5 | Analize pe tip de defect, vreme, topologie și cauză. Se văd cazurile ratate și încercările de corecție. Scăderea la schimbarea datelor se vede la SGCC și Powercut, iar limitele pentru C și bilanț sunt măsurate în simulare. |

## Rezultate și verificări

- A activ, Londra cu probleme injectate, top 128 pe testul fără defecte evidente: precizie **0,625** față de **0,0703** la regula simplă și **0,0156** la VEE. Recall **0,209**. Am aplicat modelul livrat pe eșantioanele de test pregătite local. Reperul separat SGCC, pe etichete reale de furt: PR-AUC **0,3994** față de **0,0795** la regula simplă, reprodus prin reantrenare din trăsăturile pregătite local. Precizia în top 1% scade de la 0,80 la 0,40 pe evaluarea suplimentară cu separare în timp, conform `reports/A/robustness.json`.
- B, SUA 2025: **0,2777 PR-AUC** față de **0,1820** la rafală și **0,1507** la climatologie. Am reantrenat B cu datele din Git, inclusiv evaluarea pe cele opt state ținute pe rând deoparte. Toate metricile din raportul de bază coincid. Modelul livrat obține aceeași valoare PR-AUC. Testul Powercut are 520 de zone-zile, fără furtuni severe. Pe incidente noi ≥1%, PR-AUC **0,214** față de **0,222** la rafală, cu intervalul diferenței care include zero. Sursă: `reports/B/romania_eval.md`.
- C: **0,00543 vs 0,02275 pu** MAE și **0,951 vs 0,427** PR-AUC pe 324.000 de zile-post simulate. Test pe topologii și perioade ținute deoparte. Recall-ul coboară la 31% pe topologia semiurb4, la pragul 0,5. Cifre citite din rapoarte, fără rerularea antrenării C.
- Bilanț v2: am aplicat pachetul livrat pe 13.200 de ferestre sintetice pregătite local. **0,75352 vs 0,48135** F1 macro față de tabelul de reguli. F1 este **0,47** la contorul de client și **0,49** la pierderea tehnică. MAE raportată pentru pierderea normală **5,40 vs 14,92 kWh/zi** față de I²R. FeederBW are profile măsurate și cauze simulate în experimentul de diagnostic. `presentation/demo-script.md` spune încă 0,71 față de 0,48. Raportul v2 și proba pe modelul livrat susțin 0,75 față de 0,48.
- **195/195 teste** din `tests/a`, `tests/b`, `tests/c`, `tests/bilant` au trecut cu mediul Python din worktree-ul Eden. Prima încercare cu mediul vechi al checkoutului principal s-a oprit la colectare din cauza `optuna` lipsă.

## Dovezi suplimentare pe Eden

**Până la 22/25 dacă benchmarkul de la `Eden` local, `6540d62`, este inclus în predare.** Compară CatBoost și XGBoost cu LightGBM pe aceleași partiții și raportează intervale pe grupuri. Adaugă dovezi pentru alegerea modelului și incertitudinea diferențelor. Concluzia rămâne LightGBM pentru demo. Benchmarkul este în afara lui `origin/main` și `origin/Eden` la verificare. Am citit raportul și am refăcut rezultatele de referință descrise mai sus, fără a reantrena candidații. `reports/benchmark/RAPORT.md`.
