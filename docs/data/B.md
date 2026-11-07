# Datele firului B: furtună, risc de avarii

Tot ce folosește modelul B e public. Nicio dată de antrenare nu e sintetică. Singurele date sintetice sunt cele generate în teste (`tests/b/test_b_predict_rules.py`), etichetate ca atare, și servesc doar la verificarea regulilor de decizie.

## Surse

| Sursă | Ce luăm | Licență, citare | Unde ajunge |
|---|---|---|---|
| EAGLE-I, ORNL (figshare v4, 25 feb. 2026) | Clienți fără curent pe comitat, la 15 minute, 2023-2025 (descărcăm și 2021-2022) | CC BY 4.0. Brelsford et al. (2024), *Scientific Data* 11:271, https://doi.org/10.1038/s41597-024-03095-5; setul: https://doi.org/10.6084/m9.figshare.24237376.v4 | `data/raw/B/eaglei/` (circa 1,2-1,4 GB pe an, în afara git) |
| EAGLE-I MCC | Clienți modelați pe comitat (2022), numitorul procentului | idem | idem |
| EAGLE-I coverage_history, DQI | Acoperirea pe stat și an, indicele de calitate pe regiune FEMA | idem | idem |
| Open-Meteo Historical Weather API (archive) | 10 variabile zilnice pe centroidul fiecărui comitat, 2022-12-25 – 2025-12-31; aceleași pentru zonele din România (backtest, `demo-vara`) | CC BY 4.0, „Weather data by Open-Meteo.com”, https://open-meteo.com/en/license. Gratuit, necomercial | `data/raw/B/openmeteo/us/` și `data/raw/B/openmeteo/cache/` |
| Open-Meteo Forecast, Ensemble (ICON-EPS), Historical Forecast (ICON, ECMWF IFS, GFS) | Prognoza pentru `maine`, incertitudinea, dezacordul modelelor pentru zilele trecute | idem | `data/raw/B/openmeteo/cache/` |
| US Census Bureau, 2024 Gazetteer (comitate) | Centroidul (punctul interior) și suprafața fiecărui comitat | domeniu public: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip (md5 886d8dbb34f7f8b18b615002e8cf7dc5) | `data/samples/B/2024_Gaz_counties_national.zip` (în git) |
| Planul de dezvoltare Rețele Electrice România 2026-2035, tabelele 2.1-2.3 | Clienții (utilizatorii) pe județ la 31.12.2024 și suprafața județelor | document public: https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf | `data/samples/B/zones_ro.yaml` |
| Recensământul 2021 (INS), prin Wikipedia | Populația județelor și a orașelor principale, pentru împărțirea clienților pe zone | INS; URL pe fiecare zonă în YAML | `data/samples/B/zones_ro.yaml` |
| Presa (a1.ro, HotNews, Pressalert, TVR Info) | Faptele despre furtuna din Banat, 7-9 iulie 2025, pentru backtest | citate cu URL în `reports/B/backtest_romania.md` | doar în raport |

## Calea scurtă pentru juriu: fără descărcări, fără Open-Meteo

```bash
uv sync
make b-repro      # reface reports/B/metrics.json din data/samples/B/us_county_day.parquet (~3 min, 4 nuclee)
make b-test       # testele B, fără rețea
```

Tabelul comitat × zi și vremea procesată sunt în git, deci cifrele din `reports/B/metrics.json` se refac identic, fără cei ~4 GB de EAGLE-I și fără cele ~7.300 de apeluri Open-Meteo. Am verificat pe 7 nov., la 17:14: 28 din 28 de metrici sunt identice. Backtestul din România (`backtest.py`) și lucrările (`predict.py`) au nevoie de rețea pentru vremea din România, dar doar câteva sute de apeluri.

## Fișierele mici din git

- `data/samples/B/us_county_day.parquet` (~3 MB): tabelul comitat × zi folosit la antrenare și test, cu vremea, variabilele și țintele. E derivat din EAGLE-I (CC BY 4.0, Brelsford et al. 2024) și Open-Meteo (CC BY 4.0, „Weather data by Open-Meteo.com”). Se reface cu `make b-data b-dataset`.
- `data/samples/B/us_county_day_summary.json`: ce a scos curățarea și câte evenimente sunt pe an.
- `data/samples/B/us_weather_daily.parquet` (~0,9 MB): vremea zilnică Open-Meteo pentru cele 80 de comitate, 2022-12-25 – 2025-12-31. Se reface cu `make b-weather`.
- `data/samples/B/2024_Gaz_counties_national.zip` (141 KB): lista comitatelor de la US Census Bureau (2024 Gazetteer, domeniu public; md5 886d8dbb34f7f8b18b615002e8cf7dc5), cu centroizii și suprafața. Sursa: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip

- `data/samples/B/us_counties.csv`: cele 80 de comitate din eșantion (FIPS, stat, coordonate, suprafață, clienți MCC, acoperirea EAGLE-I în 2023 și 2025). Se refac cu `uv run python -m cyberpunks.b_furtuna.us_sample --per-state 10 --check-years 2023,2025` (sămânța 42).
- `data/samples/B/zones_ro.yaml`: cele 26 de zone din România (11 județe), cu coordonatele orașului principal, populația lui și clienții pe județ.
- `src/cyberpunks/b_furtuna/manifest.py`: lista fișierelor EAGLE-I, cu mărimea și md5.

## Pașii, de la zero

```bash
uv sync
make b-data       # EAGLE-I 2023-2025: descărcare cu md5 (~4 GB), apoi comitat × oră (~15 s)
make b-weather    # opțional (vremea e în git): Open-Meteo, ~7.300 de apeluri, ~2 ore
make b-dataset    # tabelul comitat × zi: data/processed/B/us_county_day.parquet
make b-evaluate   # antrenare 2023-2024, test 2025, state nevăzute -> reports/B/metrics.json, figuri, model
make b-predict    # lucrările pentru demo-vara și maine -> outputs/work_items/<scenariu>/B.jsonl
uv run python -m cyberpunks.b_furtuna.error_analysis   # reports/B/error_analysis.md
uv run python -m cyberpunks.b_furtuna.backtest         # reports/B/backtest_romania.md
make b-test       # testele B, fără rețea
```

- **Cota Open-Meteo:** planul gratuit dă 10.000 de apeluri pe zi, 5.000 pe oră și 600 pe minut, pe adresa IP. Costul fiecărei cereri e scris în `data/raw/B/openmeteo/ledger.csv`, din antetul `X-RateLimit-Cost`. Descărcarea se reia de unde a rămas (câte un fișier pe comitat). Ritmul se schimbă cu `--calls-per-hour`.
- **Cache:** arhiva și prognozele trecute se păstrează permanent, iar prognoza și ensemble-ul 3 ore. Dacă Open-Meteo nu răspunde, agentul folosește ultima copie salvată și scrie asta în `data_quality.input_issues` al fiecărei lucrări.

## Prelucrarea și regulile de curățare

1. **EAGLE-I → comitat × oră (UTC)** (`eaglei.py`): pentru fiecare comitat și oră, vârful instantaneelor de 15 minute, suma lor (pentru clienți-ore) și numărul de instantanee. În 2023 coloana `sum` e redenumită `customers_out`.
2. **Ora locală:** fusul orar al fiecărui comitat vine din răspunsul Open-Meteo (`timezone=auto`). Orele UTC sunt convertite înainte de agregarea pe zi, ca o furtună de seară să rămână în ziua ei.
3. **Comitat × zi** (`dataset.py`): vârful zilei (`out_max`), clienții-ore (suma instantaneelor × 0,25 h) și orele cu clienți afectați. Zilele fără niciun rând primesc 0.
4. **Reguli de curățare**, numărate în `data/processed/B/us_county_day_summary.json`:
   - un comitat-an cu rânduri EAGLE-I în mai puțin de 50% din zile e scos: acolo lipsa unui rând nu înseamnă zero;
   - un vârf mai mare decât numărul de clienți MCC (care e modelat) e tăiat la 100%;
   - același vârf de cel puțin 0,5% din clienți, 4 zile la rând, e o hartă înghețată: zilele acelea sunt scoase;
   - o valoare meteo imposibilă (de exemplu rafală negativă sau peste 250 km/h, ploaie peste 500 mm/zi) devine lipsă, iar o zi cu minima peste maximă are valorile inversate (`features.clean_weather`).
5. **Ținte:**
   - `event`: vârful zilei e de cel puțin 1% din clienți;
   - `severe`: cel puțin 5%;
   - `extreme`: cel puțin 10%;
   - `y_log_pct` = log(1 + vârful în procente), ținta cuantilelor.
6. **Features** (`features.py`, aceeași funcție pentru SUA și România):
   - vânt: rafala maximă, vântul maxim, rafala din ajun, maximul pe 2 zile;
   - ploaie: pe zi, pe 48 h, pe 7 zile, plus orele cu precipitații;
   - iarnă: zăpada pe zi și pe 3 zile, ploaia la minima sub 0,5 °C (risc de polei);
   - temperaturile și radiația;
   - sezonul (sin/cos din ziua anului);
   - zona: logaritmul clienților și al densității.
   - Codul meteo e scos, pentru că arhiva nu are niciodată codurile de furtună cu descărcări, iar prognoza le are.

## Zonele din România

- Clienții pe județ sunt oficiali (RER, 31.12.2024; total 3.180.331).
- Clienții unei zone se calculează ca (populația orașului principal + restul populației județului, împărțit egal la zonele județului) / populația județului. E o APROXIMARE și apare în fiecare lucrare, la `data_quality.input_issues`.
- Suprafața unei zone e suprafața județului împărțită la numărul de zone.
- **Anomalie cunoscută:** Giurgiu are 1,22 clienți RER pe locuitor, iar Ilfov doar 0,23. Probabil zonele de rețea RER nu urmează exact granițele județelor. Folosim cifrele ca atare și semnalăm anomalia în lucrări.
- Bucureștiul (1,06 mil. de clienți, peste 4.000 pe km²) iese din ce a văzut modelul la antrenare (comitate cu 10.000-600.000 de clienți). Pentru el agentul spune „nu sunt sigur” și trimite decizia la om.
