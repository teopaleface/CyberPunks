# Backtest în România: furtuna din Banat, 6-10 iulie 2025

Generat de `uv run python -m cyberpunks.b_furtuna.backtest`. Pentru fiecare zi, agentul rulează în seara de dinainte, la 18:00, cu vremea zilei din arhiva Open-Meteo (aceeași sursă ca la antrenare). Incertitudinea vine din trei modele de prognoză (ICON, ECMWF IFS, GFS). Model: `b-lgbm@409ba59`, prag 0.16.

**Limita:** nu avem istoricul de avarii Rețele Electrice. Comparăm cu presa: ce zone, ce zi, ce ordin de mărime. Modelul e validat pe date externe (SUA, EAGLE-I) și trebuie calibrat pe istoricul RER.

## Ce a scris presa

| Ziua | Unde | Ce s-a întâmplat | Sursa |
|---|---|---|---|
| 2025-07-07 | Caraș-Severin | Furtună la Reșița (rețeaua de tramvai ruptă) și la Caransebeș (acoperiș smuls, rafale de peste 80 km/h). | https://tvrinfo.ro/?p=548910 |
| 2025-07-08 | Timiș, Arad, Caraș-Severin, Hunedoara | ANM: cod roșu de vijelii 15:00-21:00, rafale de 90-110 km/h. Transelectrica: rafale de 90-120 km/h, stâlpi avariați pe linia de 220 kV Reșița-Timișoara. | https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html ; https://hotnews.ro/?p=2020474 |
| 2025-07-07..09 | Timiș (și Banat) | Prefectul Timișului: circa 40.000 de consumatori afectați în 82 de localități, cumulat; 80 de echipe Rețele Electrice și contractori pe teren în Timiș, Arad, Hunedoara, Caraș-Severin. | https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/ |
| 2025-07-08 | București, Ilfov, Giurgiu, Ialomița, Călărași | ANM: cod roșu de caniculă (38-41 °C); nicio furtună raportată. | https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html |

## Ce ar fi recomandat agentul

| Ziua | Banat: P medie | Banat: echipe recomandate | Banat: la om | Restul (14 zone): P medie | Restul: echipe recomandate | Clienți așteptați în Banat (Σ P × P50) |
|---|---|---|---|---|---|---|
| 06.07 | 0.10 | 2 din 12 | 0 | 0.11 | 4 din 14 | 1.631 |
| 07.07 | 0.31 | 11 din 12 | 0 | 0.13 | 5 din 14 | 6.661 |
| 08.07 | 0.34 | 10 din 12 | 0 | 0.11 | 3 din 14 | 11.209 |
| 09.07 | 0.08 | 0 din 12 | 0 | 0.15 | 5 din 14 | 1.548 |
| 10.07 | 0.08 | 0 din 12 | 0 | 0.07 | 1 din 14 | 1.230 |

### 07.07.2025: primele 8 zone după risc

| Zona | Județ | P | interval | Recomandare | Rafală (km/h) | Ploaie 48 h (mm) | Început estimat | Clienți la vârf (P50) |
|---|---|---|---|---|---|---|---|---|
| AR-INEU | Arad | 0.57 | 0.26-0.62 | RecommendedAction.preposition_crew | 78.5 | 0.2 | 17:00 | 1.449 |
| CS-CARANSEBES | Caraș-Severin | 0.36 | 0.26-0.36 | RecommendedAction.preposition_crew | 68.0 | 0.0 | 18:00 | 1.033 |
| CS-ORAVITA | Caraș-Severin | 0.36 | 0.22-0.36 | RecommendedAction.preposition_crew | 70.9 | 0.0 | 17:00 | 877 |
| CS-RESITA | Caraș-Severin | 0.36 | 0.22-0.36 | RecommendedAction.preposition_crew | 74.5 | 0.0 | 17:00 | 1.257 |
| HD-BRAD | Hunedoara | 0.31 | 0.26-0.31 | RecommendedAction.preposition_crew | 56.2 | 0.4 | 18:00 | 1.848 |
| AR-LIPOVA | Arad | 0.31 | 0.26-0.36 | RecommendedAction.preposition_crew | 65.5 | 0.2 | 17:00 | 1.181 |
| TM-LUGOJ | Timiș | 0.31 | 0.20-0.31 | RecommendedAction.preposition_crew | 84.6 | 0.0 | 17:00 | 2.421 |
| AR-ARAD | Arad | 0.27 | 0.20-0.27 | RecommendedAction.preposition_crew | 72.0 | 0.2 | 16:00 | 3.600 |

### 08.07.2025: primele 8 zone după risc

| Zona | Județ | P | interval | Recomandare | Rafală (km/h) | Ploaie 48 h (mm) | Început estimat | Clienți la vârf (P50) |
|---|---|---|---|---|---|---|---|---|
| HD-DEVA | Hunedoara | 0.62 | 0.26-0.62 | RecommendedAction.preposition_crew | 57.2 | 14.2 | 17:00 | 3.300 |
| CS-CARANSEBES | Caraș-Severin | 0.62 | 0.36-0.62 | RecommendedAction.preposition_crew | 64.4 | 7.2 | 16:00 | 1.385 |
| CS-RESITA | Caraș-Severin | 0.50 | 0.22-0.50 | RecommendedAction.preposition_crew | 58.0 | 12.5 | 15:00 | 2.687 |
| AR-INEU | Arad | 0.50 | 0.19-0.50 | RecommendedAction.preposition_crew | 41.4 | 19.3 | 15:00 | 2.595 |
| CS-ORAVITA | Caraș-Severin | 0.28 | 0.21-0.36 | RecommendedAction.preposition_crew | 70.2 | 6.2 | 15:00 | 1.372 |
| AR-LIPOVA | Arad | 0.28 | 0.09-0.28 | RecommendedAction.preposition_crew | 39.6 | 15.9 | 14:00 | 1.683 |
| TM-LUGOJ | Timiș | 0.27 | 0.13-0.27 | RecommendedAction.preposition_crew | 40.0 | 11.8 | 15:00 | 3.670 |
| HD-BRAD | Hunedoara | 0.26 | 0.13-0.27 | RecommendedAction.preposition_crew | 59.4 | 8.6 | 16:00 | 2.228 |

## Verdict (calculat)

- Pe 7 și 8 iulie, riscul mediu în Banat a fost 0.32, față de 0.12 în Muntenia și Dobrogea (caniculă, fără furtuni raportate). Ordinea regiunilor e aceeași ca în presă.
- Echipe recomandate în Banat pe 7-8 iulie: 21 zone-zi; în restul țării: 8 zone-zi.
- Rafalele din arhivă în Banat pe 7-8 iulie: 40-85 km/h, față de 90-120 km/h măsurate: modelele meteo netezesc vijeliile. Modelul a învățat pe aceeași vreme netezită, deci poate ordona zonele, dar mărimea locală a vijeliei rămâne incertă.
- Ordin de mărime: presa dă circa 40.000 de consumatori afectați în Timiș în trei zile (cumulat). Coloana „clienți așteptați” e suma vârfurilor așteptate pe zonele din Banat, deci se compară doar ca ordin de mărime.

![Risc pe zone](fig_backtest_zones.png)

