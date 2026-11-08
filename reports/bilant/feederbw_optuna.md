# Bilanț: FeederBW și Optuna

**Profile de import reale; rețele, pierderi și toate etichetele SINTETICE.**

Sursa: [FeederBW, Netze BW/KIT](https://zenodo.org/records/17831177), CC BY 4.0. [Treutlein et al., Scientific Data 13, 1283 (2026)](https://doi.org/10.1038/s41597-026-08152-9).

38 de plecări valide din primul lot de 40; plecările 34 și 38 excluse pentru peste 10% ore lipsă. 22 / 8 / 8 plecări reale la antrenare / validare / test; 170 / 65 / 65 posturi simulate. Test spațial pe aceeași perioadă 2024-04-02–2025-03-30, fără test în viitor.

| Scor | Setări v2 actuale, reantrenate | Optuna, 40 de încercări |
|---|---:|---:|
| F1 macro validare | 0.62536 | 0.64050 |
| F1 macro test | 0.70858 | 0.71393 |
| Exactitate test | 0.74705 | 0.74919 |

Diferența F1 test: +0.00535; interval bootstrap 90% [-0.00618; +0.01769], 1.000 de re-eșantionări pe plecări reale. **Nu există un câștig statistic confirmat.** După o activare temporară, la cererea utilizatorului, modelul FeederBW a fost retras din rularea implicită și păstrat pentru comparații.

Nu se compară direct cu scorul 0,754 al v2 anterior: alte rețele, alte profile și alt test. FeederBW nu are perechi complete contor de post / total clienți sau verdicte de furt și defect. Forma importului (după tăierea exportului) este normalizată și scalată; clienții, PV și pierderile sunt simulate. Vremea este cea din București, nu vremea germană.

Pe aceleași 13.200 de ferestre ale hărții simulate, v2 reconstruit obține F1 macro **0,75352**, iar candidatul FeederBW **0,58950**. Eroarea pierderii normale este 5,40 față de 8,81 kWh/zi. V2 reproduce valorile din evaluarea istorică. Detalii și rezultate pe clase: `comparatie_v2_feederbw.json`. Fuziunea cu scorul A nu a fost evaluată în această comparație.

Cod și comenzi: `docs/data/bilant.md`. Parametri, clase, suporturi și matrice de confuzie: `feederbw_optuna.json`. Proveniență și SHA256: `data/samples/bilant/feederbw_manifest.json`.

Verificat: 31 de teste bilanț, Ruff și verificarea spațiilor Git.
