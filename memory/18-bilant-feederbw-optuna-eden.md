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
- Separare pe sursa REALĂ: 24 plecări la antrenare, 8 la validare, 8 la test; cartierele și perechile client-post
  greșit rămân împreună. OOF pentru normal tot pe plecări reale. Perioadă comună 2024-04-02–2025-03-30.
- Optuna alege setările doar pe validare, după macro-F1 inclusiv regulile folosite la test. Baza este LightGBM
  cu setările v2, reantrenat pe aceleași date și trăsături. Bootstrap pe plecări reale, nu ferestre suprapuse.
- Proveniență: `data/samples/bilant/feederbw_manifest.json`; raportul va fi `reports/bilant/feederbw_optuna.json`.
  Datele și modelele mari rămân în directoarele ignorate de Git.
- Alternative verificate: Weave are agregate de contoare, nu bilanț complet; nu are licență clară în repo.
  Cauca, Columbia (Mendeley `yzyj46xpmy/4`), are defecte de transformator, nu bilanț energetic.
  Porsgrunn, Norvegia (Mendeley `jv3rz8k35r/1`), are modele de rețea și AMI, dar nu verdicte de pierderi reale;
  candidat pentru o simulare viitoare cu topologie reală, fără a-l prezenta ca bilanț măsurat.

Rezultatele se completează după rulare.
