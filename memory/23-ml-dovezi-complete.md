# ML: date reale suplimentare, test nou și raport comun — 8 noiembrie 2026

Cerut de Eden: completarea tehnică a ML pentru baremul de 25 puncte. Lucrat pe `Eden`, în worktree-ul `evaluare-ml`.
Intrarea comună este `reports/ml/README.md`, generată de `make ml-report`; `evidence.json` reunește integral
rapoartele JSON și sumele SHA256. `make ml-check` execută testele ML și recalculează scorurile din predicții.

## Ce s-a adăugat

- **FeederBW are tensiuni reale**, nu doar putere/consum. Din arhiva 001–040 am extras `voltage_one_phase_V`:
  28.216 zile acceptate, 40 plecări. Zi acceptată: minimum 95% minute distincte, citiri finite între 150 și 300 V;
  fără interpolare. Agregatele mici și atribuirea autorilor sunt în Git, CC BY 4.0, DOI 10.5281/zenodo.17831177.
- Experiment nou: maximul zilnic al tensiunii la plecare, ziua următoare, din istoricul ultimelor șapte zile.
  Plecări disjuncte 24/8/8 și perioade separate: train înainte de iulie 2024, validare iulie–septembrie 2024,
  test octombrie 2024–martie 2025. 9.869 / 736 / 1.353 exemple. XGBoost ales pe validare, fără selecție pe test:
  MAE test **0,724 V**, persistență **0,825 V**, medie 7 zile **0,732 V**, Ridge **0,688 V**, LightGBM **0,707 V**,
  CatBoost **0,715 V**. Ridge este mai bun pe test; nu schimbăm retroactiv alegerea.
- Limita: **zero depășiri de 253 V în test** (doar cinci în întregul agregat). Experimentul nu validează
  detectarea supratensiunilor și nici maximul spațial al rețelei calculat de modelul C.
- Comparație nouă C: șase topologii ținute pe rând deoparte × timp nevăzut; aceeași selecție de 60.000 exemple
  train/fold, 300 arbori, fără tuning. MAE: liniar **0,022742**, LightGBM **0,005382**, CatBoost **0,005561**,
  XGBoost **0,005418 pu**. Intervalele diferențelor candidaților includ zero. Este regresia medianei la buget fix,
  nu pachetul complet C calibrat. Predicții publice pe fiecare topologie, sub limita de 5 MB/fișier.
- Audit nou bilanț: protocolul, seedul și hashurile modelului/codului au fost fixate în commitul **3deadcc**,
  la **10:26:53 București**, înainte de generare. 300 posturi sintetice noi, 13.200 ferestre, 60 cartiere;
  modelul livrat, fără antrenare/selecție/reglaje pe test. Macro-F1 **0,77539 vs 0,42059** reguli; diferență
  **0,35480**, IC90 **[0,31630; 0,39007]** pe cartiere. Abținere **20,0%**, exactitate fără abțineri **89,6%**.
  Macro-F1 include toate cazurile. Aceleași familii de topologii și același simulator; distribuție diferită de
  harta demo, deci scorurile nu reprezintă o creștere pe același test și nu sunt validare în teren.

## Reparații și interpretare

- CatBoost producea SIGSEGV când testul său era încărcat după alte extensii native în suita ML completă.
  Testul interfeței reale rulează acum într-un proces separat, cu timeout și verificarea codului de ieșire.
  Citirea versiunilor pentru rapoarte folosește metadata pachetelor, fără importul inutil al extensiilor native.
- Teste noi pentru scurgerea datelor viitoare, zile lipsă, duplicate care falsifică acoperirea zilnică,
  etichete reale mari păstrate, separări pe plecări/timp și detectarea cifrelor raportate greșit.
- Bootstrap fără date/statistici finite dă o eroare explicită, în locul unui interval aparent valid.
- **IC care include zero = rezultat neconcludent, nu echivalență demonstrată.** Corectat raportul benchmark.
- **Optuna nu ajută uniform**, nu „nu ajută deloc”: A scade, B aproape neschimbat, C crește puțin,
  bilanț v2 crește de la 0,73545 la 0,75352 după setările optimizate.
- Modelele din `models/release/` rămân cele existente. Rezultatele suplimentare sunt dovezi, nu o promovare
  automată bazată pe consultarea testelor. Nu putem garanta punctajul juriului sau fabrica etichete reale lipsă.

La 10:30 au trecut 208 teste ML + protecția de mărime. Verificarea din copie fără datele mari locale este
consemnată în jurnal și în raportul generat după terminarea ei.
