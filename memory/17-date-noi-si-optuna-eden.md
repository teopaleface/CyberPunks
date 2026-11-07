# Date noi, variabile meteo noi și Optuna (ramura Eden, 7-8 nov. 2026)

Cerut de Eden, sâmbătă seara. Totul e **experiment pe ramura `Eden`**: modelele livrate
(`models/release/`) și cifrele din `reports/*/metrics.json` nu s-au schimbat. Teo decide ce se preia.

Regula pentru toate: căutarea (variante, Optuna) vede doar antrenarea; testul livrat se folosește la final,
cu interval bootstrap 90% al diferenței față de modelul livrat. Varianta de bază reproduce exact cifrele livrate.

## A, contoare (`reports/A/experiments_extra.json`, `tuning_optuna.json`)

- Date noi: toate cele 168 de fișiere Low Carbon London (Std și ToU, ~4.900 de gospodării la antrenare, față de 838).
  Testul rămâne cel livrat. Precizia@1% pe problemele subtile **0,625 -> 0,891**, PR-AUC subtil 0,406 -> 0,518,
  interval [+0,05, +0,16]. **Cel mai mare câștig al nopții.**
- Vreme (grade-zile la Londra, sensibilitatea la frig): 0,625 -> 0,672, dar intervalul trece prin zero. Fără câștig sigur.
- Optuna (30 de încercări, validare pe gospodării ținute deoparte): mai bun pe validare, mai slab pe test
  (interval [-0,022, -0,003]). Parametrii livrați rămân.
- Sumele de control pentru toate fișierele: `data/samples/A/checksums_lcl_all.sha256` (manifestul livrat neschimbat).

## B, furtună (`reports/B/experiments_extra.json`, `tuning_optuna_*.json`)

- Variabile noi pentru cele 80 de comitate: ERA5 orar (rafale pe ore, sol, presiune, zăpadă, rouă, umiditate,
  direcție, strat limită, apă precipitabilă) și CAPE, lifted index din prognozele istorice GFS (arhiva ERA5 din
  Open-Meteo nu are CAPE). Cost: ~7.400 de apeluri Open-Meteo. Cod: `b_furtuna/extra_weather.py`.
- **Convecția ajută**: PR-AUC pe 2025 0,2777 -> 0,2865, interval [+0,003, +0,016]; confirmat și pe validarea
  out-of-fold a anilor de antrenare (0,2916 -> 0,3060). Solul, orele cu rafale, umiditatea, direcția: nu ajută.
- Optuna (60 de încercări, cu și fără convecție): fără câștig pe test. Parametrii livrați rămân.
- Pentru aplicarea în România, prognoza GFS cu CAPE e în Open-Meteo (`models=gfs_seamless`). Neintegrat.
- Anii 2021-2022: EAGLE-I descărcat și procesat (`data/interim/B/eaglei_hourly/`), cod gata în `more_years.py`;
  vremea nedescărcată (cerea ~9.800 de apeluri după 02:00). Oprit la decizia lui Eden (01:05).
- Limită: ERA5 nu are stratul limită și apa precipitabilă în ian.-iun. 2024.

## C, prosumatori (`reports/C/experiments_extra.json`, `tuning_optuna_mai_multe_regiuni.json`)

- Vreme nouă: București 2015-2026 și Timișoara, Cluj, Iași, Constanța 2019-2026, cu vânt, strat de zăpadă,
  umiditate. Paștele ortodox 2015-2022 adăugat în calendar.
- Modelul antrenat doar pe București merge la fel în celelalte 4 regiuni (MAE ~0,0054 pu peste tot).
- Mai mulți ani: PR-AUC 0,949 -> 0,953. Mai multe regiuni: MAE 0,00538 -> 0,00533 pu. Câștiguri mici: modelul era
  deja aproape de plafon.
- Fizica v2 (răcirea panourilor de vânt, modelul Faiman; panouri sub zăpadă): randament mai aproape de PVGIS
  (~1.314 față de 1.348 kWh/kWp, PVGIS 1.282). Cu etichetele v2, modelul are nevoie de vânt și zăpadă ca trăsături:
  MAE 0,00576 -> 0,00546, acoperire 0,81 -> 0,83. Parametrii fizicii v2 sunt IPOTEZĂ.
- Optuna (30 de încercări): MAE pe 2025 0,00533 -> 0,00527 pu, PR-AUC 0,950 -> 0,952, aceeași direcție în toate cele 5 regiuni. Câștig mic, dar constant; singurul loc unde Optuna a ajutat.

## Ce aș propune echipei

1. A: reantrenarea cu toate cele 168 de fișiere LCL (câștig mare, sigur).
2. B: variabilele de convecție, cu prognoza GFS pentru România.
3. Optuna: nu schimbăm parametrii; în prezentare, „verificat cu Optuna, modelele erau deja aproape de optim”.
