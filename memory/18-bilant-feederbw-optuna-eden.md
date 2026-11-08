# Bilanț: date reale FeederBW și optimizare Optuna (Eden)

Cerut de utilizator la 8 noiembrie 2026: găsește un dataset real pentru bilanț și optimizează LightGBM cu Optuna.
Lucrarea este pe ramura `Eden`, ca experimentele anterioare. Modelele livrate nu se înlocuiesc automat.

- Sursa aleasă: **FeederBW**, Netze BW / Karlsruhe Institute of Technology,
  https://zenodo.org/records/17831177, versiune fixată 1.0, licență **CC BY 4.0**.
  Citare: Treutlein et al., *Scientific Data* 13, 1283 (2026), https://doi.org/10.1038/s41597-026-08152-9.
- Set complet: 200 de plecări JT din Germania, măsurători la minut, aprilie 2023–martie 2025.
  Experimentul descarcă primul lot oficial: plecările 1–40, ~1,7 GB comprimat, cu verificare MD5 de la editor.
- **Limită esențială:** sursa NU oferă perechi complete contor-post / contoare-clienți sau verdicte de furt/defect.
  Se folosește numai **forma importului orar real**, după tăierea exportului și normalizare; scara, clienții,
  rețeaua, PV, pierderile și toate etichetele rămân **SINTETICE**. Vremea este cea din București.
- Cod: `src/cyberpunks/a_bilant/feederbw.py`; comenzi `download`, `prepare`, `tune --trials 40 --workers 4`.
- Din 40 de surse, 38 sunt valide. Plecările 34 și 38 au 1.272 și respectiv 1.171 ore lipsă din 8.712 (>10%)
  și sunt excluse. Cele valide au 1.068 ore completate din trecut din 331.056; 20.418 ore cu export sunt tăiate.
- Separare pe sursa REALĂ: 22 plecări la antrenare, 8 la validare, 8 la test (170 / 65 / 65 posturi simulate); cartierele și perechile client-post
  greșit rămân împreună. OOF pentru normal tot pe plecări reale. Perioadă comună 2024-04-02–2025-03-30.
- Optuna alege setările doar pe validare, după macro-F1 inclusiv regulile folosite la test. Baza este LightGBM
  cu setările v2, reantrenat pe aceleași date și trăsături. Bootstrap pe plecări reale, nu ferestre suprapuse.
- Proveniență: `data/samples/bilant/feederbw_manifest.json`; raportul va fi `reports/bilant/feederbw_optuna.json`.
  Datele și modelele mari rămân în directoarele ignorate de Git.
- Alternative verificate: Weave are agregate de contoare, nu bilanț complet; nu are licență clară în repo.
  Cauca, Columbia (Mendeley `yzyj46xpmy/4`), are defecte de transformator, nu bilanț energetic.
  Porsgrunn, Norvegia (Mendeley `jv3rz8k35r/1`), are modele de rețea și AMI, dar nu verdicte de pierderi reale;
  candidat pentru o simulare viitoare cu topologie reală, fără a-l prezenta ca bilanț măsurat.

## Rezultatul final

- 40 de încercări Optuna, 390,3 secunde pentru antrenare, ferestre, căutare și test.
- Ferestre train / validare / test: 7.310 / 2.795 / 2.795; toate cele șase clase prezente.
- F1 macro validare: **0,62536 → 0,64050**.
- F1 macro test: **0.70858 → 0.71393**. Exactitate: 0,74705 → 0,74919.
- Diferență F1 test: **+0.00535**; bootstrap 90% pe cele 8 plecări reale:
  **[-0.00618; +0.01769]**. Intervalul include zero: **câștigul nu este confirmat statistic**.
- F1 pe furt înainte de contor: 0,4541 → 0,4686; client la postul greșit: 0,7979 → 0,8101;
  contor de client: 0,6104 → 0,6083 (ușor mai slab). Nu afirmăm îmbunătățire pe toate clasele.
- Parametrii aleși și matricele de confuzie sunt în `reports/bilant/feederbw_optuna.json`.
- Model experimental: `models/bilant/experiments/feederbw_optuna.txt` și `.json`;
  modelele normalului: `feederbw_normal_warm_*` și `feederbw_normal_cold_*` în același director.
  Predicțiile testului și istoricul celor 40 de încercări sunt în lotul local (`test_predictions.parquet`, `trials.csv`).
- SHA256 arhivă: `86dc8139d04db6f7b0150b78f767413d14966a34b07a3af3be208069f9972ec4`.
- Verificări: 31 de teste în `tests/bilant` trecute, Ruff pe modul și teste trecut, `git diff --check` trecut.
  Modelul salvat a fost reîncărcat: aceleași 2.795 de predicții de test; toate cele 40 de încercări sunt COMPLETE.
- Decizie: păstrăm rezultatul ca experiment; modelul livrat și parametrii săi nu se înlocuiesc.
  Scorul 0,754 din experimentul v2 anterior este pe alt test; nu îl comparăm direct cu acest 0,714.
