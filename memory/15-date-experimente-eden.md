# Datele și experimentele A, B și C de pe Eden

Actualizat: 8 noiembrie 2026, 00:50, ora Bucureștiului. Pentru ceilalți agenți: acesta este un rezumat al datelor adăugate local și al experimentelor de pe ramura `Eden`, publicată până la commitul `d4e69be`. Rezultatele experimentale nu înlocuiesc automat modelele livrate și nu au fost integrate cu ramura `Teo`.

## Ce se găsește pe GitHub și ce rămâne local

- Pe `origin/Eden` sunt codul experimentelor, rapoartele JSON, sumele de control și eșantioanele deja urmărite în `data/samples/`. Pe alte ramuri ele apar numai după integrarea commiturilor respective.
- Descărcările și datele generate se află pe calculatorul Eden în `data/raw/`, `data/interim/` și `data/processed/`. Aceste directoare sunt ignorate de Git și **nu au fost încărcate**. La verificare, ocupau aproximativ 11 GB, 0,9 GB și respectiv 8,7 GB. O clonă nouă nu le conține.
- Datele sunt amestec de surse reale, date meteo și simulări. În A, problemele injectate peste profilurile reale sunt **sintetice**; în C, rețelele și etichetele rezultate din simularea fizică sunt **sintetice**.
- SGCC nu are licență explicită și documentația proiectului spune să nu îl redistribuim. Licența datelor Powercut/RER nu este precizată. Nu încărcați aceste date înainte de clarificarea drepturilor. Pentru sursele permise, păstrați atribuirea din `docs/data/A.md`, `docs/data/B.md` și `docs/data/C.md`.
- Sumele pentru fișierele Londra sunt în `data/samples/A/checksums_lcl_all.sha256`; pentru C în `data/samples/C/checksums.sha256`. O sumă de control nu conține datasetul.

## A — contoare

- Date suplimentare: toate cele 168 de fișiere Low Carbon London în `data/raw/A/lcl/`, față de 45 folosite la baza experimentului; temperatura Londrei în `data/raw/A/london_daily_temperature.json`. Sursa LCL este CC BY 4.0; vezi atribuirea în `docs/data/A.md`. SGCC rămâne separat în `data/raw/A/sgcc/`.
- Experiment: `src/cyberpunks/a_contoare/experiments_extra.py`, rezultate în `reports/A/experiments_extra.json`. Gospodăriile suplimentare au intrat doar la antrenare; testul păstrează gospodării nevăzute și perioada septembrie 2013–februarie 2014. Problemele sunt injectate sintetic peste consum real.
- Pe probleme subtile, PR-AUC a crescut de la **0,4057 la 0,5175** cu mai multe gospodării; intervalul bootstrap de 90% pentru diferență este [0,0516; 0,1569]. Vremea singură a dat 0,4258, cu interval al diferenței care include zero. Nu prezentați aceste rezultate drept performanța modelului deja livrat.
- Optuna: `reports/A/tuning_optuna.json`. Parametrii găsiți au scăzut PR-AUC pe test de la 0,5175 la 0,5057; nu există motiv din acest test să fie promovați.
- Reproducere: `uv sync`, apoi `uv run python -m cyberpunks.a_contoare.download --only lcl --lcl-files 168` și `uv run python -m cyberpunks.a_contoare.experiments_extra`. Descărcarea este mare și serverul poate limita cererile. Temperatura se descarcă automat dacă lipsește. Pentru pașii de bază și condițiile de licență, vezi `docs/data/A.md` și opțiunile din `download.py`.

## B — furtuni

- Datele suplimentare includ EAGLE-I și vreme pentru SUA, variabile meteo orare suplimentare și ani suplimentari pregătiți de scripturile din `src/cyberpunks/b_furtuna/`. Datele pentru România sunt în `data/raw/B/romania/`; inventarul și limitele sunt în `memory/14-date-furtuni-eden.md`.
- Experiment SUA: `reports/B/experiments_extra.json`, antrenare 2023–2024, test 2025 pe 80 de comitate. PR-AUC de bază 0,2777; cu grupul de variabile de convecție 0,2865, diferență cu interval bootstrap 90% [0,0025; 0,0160]. Grupul include CAPE și lifted index, dar și alte variabile: experimentul nu izolează contribuția fiecăreia. Rezultatul este experimental; modelul livrat nu a fost schimbat.
- Optuna pe datele livrate: `reports/B/tuning_optuna_b_ani2023-2024.json`; PR-AUC pe 2025 0,2777 la bază față de 0,2763 pentru parametrii găsiți. Nu s-a demonstrat un câștig.
- Test România: `reports/B/romania_eval.md` și `.json`; Powercut, 26 de zone, 18 octombrie–6 noiembrie 2026, fără furtuni în interval. Pe eticheta „incidente noi ≥1%”, PR-AUC 0,214 față de 0,222 pentru rafală. Etichetele și licența au limite, iar acest test nu stabilește performanța pe furtuni reale. Tabelul derivat rămâne local în `data/processed/B/`.
- Pentru reproducere, citiți întâi `docs/data/B.md`, apoi antetele `extra_weather.py` și `more_years.py`: descărcările meteo suplimentare pot însemna mii de cereri. Comenzile de construire și evaluare sunt în `src/cyberpunks/b_furtuna/experiments_extra.py`. Pe Mac-ul Eden, LightGBM a avut nevoie de `DYLD_LIBRARY_PATH=.venv/lib/python3.12/site-packages/sklearn/.dylibs`.

## C — prosumatori

- Date suplimentare: vreme Open-Meteo pentru București 2015–2026 și pentru Timișoara, Cluj, Iași și Constanța 2019–2026, local în `data/raw/C/extra/`; simulările sunt în `data/processed/C/`. Datele meteo sunt reale, dar rețelele și etichetele sunt **sintetice**.
- Experiment: `src/cyberpunks/c_prosumatori/experiments_extra.py`, raport `reports/C/experiments_extra.json`. Testul folosește zile din 2025 încolo și topologii nevăzute. În București, PR-AUC pentru depășiri este 0,94878 la bază, 0,95341 cu mai mulți ani și 0,95044 cu mai multe regiuni; acestea sunt rezultate pe simulări, nu validare pe rețele reale.
- Varianta de fizică v2 include ipoteze despre răcirea panourilor de vânt și acoperirea cu zăpadă. Ea schimbă etichetele, deci comparați doar variantele v2 între ele; ipotezele și metricile sunt în raport. Modelul livrat nu a fost schimbat.
- Reproducere: `uv sync`, apoi `uv run python -m cyberpunks.c_prosumatori.experiments_extra sim` și `uv run python -m cyberpunks.c_prosumatori.experiments_extra eval`. Scriptul `sim` citește direct cele cinci fișiere meteo din `data/raw/C/extra/`; ele trebuie procurate înainte de rulare, nu sunt descărcate automat de această comandă. Sumele și numele lor sunt în `data/samples/C/checksums.sha256`. Simulările cer spațiu și timp; vezi și `docs/data/C.md`.

## Integrare și verificări

- Lucrați pe ramura proprie; nu presupuneți că `main` sau `Teo` conține experimentele Eden. Pentru integrare, inspectați diferențele și conflictele înainte de merge. O verificare anterioară a semnalat conflicte în `memory/INDEX.md` și `memory/journal.md`; starea trebuie reverificată la integrare.
- Rapoartele sunt rezultate de experimente, nu dovada că întregul produs a fost retestat. La verificarea anterioară Ruff a trecut, iar pytest a fost întrerupt după 72%; nu afirmați că suita completă a trecut.
- Nu există încă o destinație stabilită pentru distribuirea seturilor mari. Dacă este necesar transferul lor, alegeți împreună un spațiu potrivit și verificați licențele înainte de publicare.
