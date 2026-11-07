# Reproducerea Daybreak dintr-o clonă curată

Verificat pe 7 nov. 2026, 16:05-16:38, de firul A, la cererea orchestratorului. Ramura `Teo`, commit `791c94c` (identic cu `origin/Teo`), pe un MacBook M5 Max (36 GB, macOS), cu Python 3.12 prin uv. Am rulat fiecare pas separat și am măsurat cât durează. Pașii care folosesc modelele au rulat **fără internet** (proxy inexistent și `UV_OFFLINE=1`), ca să se vadă ce cere rețeaua și ca să nu consum cota Open-Meteo.

**Rezultatul.** Tot lanțul merge cap-coadă în **32 de minute și jumătate**: descărcări, antrenarea și evaluarea celor patru modele (A, B, C, bilanț), lucrările pentru `demo-vara`, agentul (`cyberpunks run`) și evaluarea agentului.
- Toate ieșirile sunt valide: A 518 lucrări, bilanț 79, B 26, C 41, planul.
- Agentul a pus 34 de lucrări în traseele a 8 echipe (319 km, OR-Tools în 10 s), 451 de citiri la distanță și 25 de cazuri la dispecer.
- Au picat două pași:
  - `make check`, din cauza a 9 teste ale firului C care cer internet;
  - `make a-data`, din cauza serverului din Londra (reparat în `Teo-A-contoare`, commit `905374d`).
- Vremea de la Open-Meteo (B, C, bilanț) am luat-o din datele deja descărcate de fire; mai jos e cât costă refacerea ei.

## Ce îți trebuie

- `git`, `make` și [uv](https://docs.astral.sh/uv/). uv instalează singur Python 3.12.
- ~10 GB liberi: date brute 6,1 GB (A 2,3 GB, B 3,8 GB, C 18 MB), date procesate 1,2 GB, mediul Python 1 GB.
- Internet pentru descărcări: GitHub (SGCC), London Datastore (Low Carbon London), figshare (EAGLE-I), PyPI (la `uv sync`).
- Cota gratuită Open-Meteo pentru vreme: 10.000 de apeluri pe zi. Refacerea vremii lui B consumă ~7.300 (detalii mai jos).

## Comenzile, în ordine

Duratele sunt măsurate în clona curată. „Fără internet” înseamnă că pasul a mers cu rețeaua blocată.

| # | Comanda | Durată | Rețea | Ce produce |
|---|---|---|---|---|
| 1 | `git clone --branch Teo https://github.com/teopaleface/CyberPunks.git && cd CyberPunks` | vezi problema 6 | internet | repo-ul (365 MB cu istoricul) |
| 2 | `uv sync` | 0:01 (cu cache-ul uv plin) | internet | mediul Python (1 GB); pe o mașină nouă durează câteva minute |
| 3 | `make check` | 1:50 | fără internet | lint și teste: 248 trec, 9 pică fără internet (problema 1) |
| 4 | `make a-data` | 3:39 | internet | SGCC (52 MB) și 45 de fișiere Londra (~212 MB, prin cereri pe intervale), verificate cu SHA-256; features și eșantioane |
| 5 | `make a-train` | 1:25 | fără internet | `models/A/` |
| 6 | `make a-evaluate` | 0:18 | fără internet | `reports/A/metrics.json`, `metrics_full.json`, figuri |
| 7 | `make a-robustness a-select a-predict a-figures a-fusion a-report` | 1:51 | fără internet | robustețe, alegerea features, `outputs/work_items/<s>/A.jsonl`, figuri, fuziune, analiza erorilor, model card |
| 8 | `make b-data` | 4:08 | internet | EAGLE-I 2023-2025 (3,8 GB, md5 verificat), tabelele pe ore |
| 9 | gazetteer-ul recensământului SUA, de mână, în `data/raw/B/census/` | - | internet | vezi problema 3; aici copiat din firul B |
| 10 | `make b-weather` | ~2 h (nerulat) | internet + cota Open-Meteo | vremea pe 80 de comitate; aici copiată din cache-ul firului B (problema 4) |
| 11 | `make b-dataset` | 0:01 | fără internet | `data/processed/B/us_county_day.parquet` |
| 12 | `make b-reports` | 3:00 | fără internet | `reports/B/metrics.json`, experimente, analiza erorilor, backtest România, model card |
| 13 | `uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara` | sub 0:01 | fără internet | `B.jsonl`: 26 de zone, 12 echipe recomandate, 1 caz la om |
| 14 | `make c-weather` | nerulat | internet + cota Open-Meteo | arhiva meteo 2023-2026; aici copiată din cache-ul firului C |
| 15 | `make c-sim` | 1:14 | fără internet | simularea fizică a celor 480 de posturi de antrenare (4 procese) |
| 16 | `make c-population` | 0:47 | fără internet | cele 300 de posturi demo, simulate |
| 17 | `make c-train` | 2:51 | fără internet | `models/C/bundle.joblib` |
| 18 | `uv run python -m cyberpunks.c_prosumatori.predict --scenario demo-vara` | 0:06 | fără internet | `C.jsonl` (41 de lucrări), seriile, scara de soluții |
| 19 | `make c-eval` | 6:00 | fără internet | `reports/C/metrics.json`, `metrics_detail.json`, figuri |
| 20 | `make bilant-data` | 1:00 | fără internet | lumea simulată a bilanțului (600 de posturi, 4 procese) |
| 21 | `make bilant-eval` | 2:03 | fără internet | `reports/bilant/metrics.json`, figuri, planul B, analiza erorilor (problema 5) |
| 22 | `make bilant-predict` | 0:05 | fără internet | `A_bilant.jsonl` (79), seriile, starea pentru fuziune |
| 23 | `uv run cyberpunks run --scenario demo-vara` | 0:26 | fără internet | `outputs/plans/demo-vara/`: planul, jurnalul, alertele, mesajele, ordinele de lucru PDF, raportul |
| 24 | `uv run cyberpunks validate outputs/work_items/demo-vara/*.jsonl` și `uv run cyberpunks validate --as plan outputs/plans/demo-vara/plan.json` | sub 0:01 | fără internet | toate valide |
| 25 | `make agent-eval` | 1:42 | fără internet | `reports/planner/agent_eval.json` și `.md` (agentul față de strategii simple) |

Total măsurat: 32:33, fără `b-weather` și `c-weather`. Scenariul `maine` nu l-am rulat, pentru că cere prognoza live de la Open-Meteo pentru B și C.

**Demo fără date și fără modele**, din instantaneul din git: `make demo-offline`, sau `CYBERPUNKS_API_SOURCE=demo make api` (vezi `status/Teo-planificator.md`). Lucrările A se pot face și fără descărcări: `make a-predict` (modelul din `models/release/A/`, profilele din `data/samples/A/`).

## Ce am copiat din datele firelor (fără să consum cota Open-Meteo)

| Fir | Fișiere copiate | Cum se refac | Cost |
|---|---|---|---|
| B | `data/raw/B/openmeteo/` (8,5 MB) | `make b-weather` | jurnalul de costuri (`ledger.csv`): 102 cereri, ~7.300 de apeluri echivalente (arhivă 6.643, ensemble 416, prognoze istorice 130, prognoză 117), adică ~73% din cota zilnică gratuită; ~2 ore în ritmul configurat (3.300 pe oră) |
| B | `data/raw/B/census/` (776 KB) | de mână, URL-ul din `docs/data/B.md` | - |
| C | `data/raw/C/*.json` (18 MB): arhiva meteo 2023-2026 pentru un punct, prognozele, prognozele istorice, PVGIS, posturile OSM | `make c-weather` (arhiva); restul din scripturile firului C | arhiva e o singură cerere lungă; costul în apeluri echivalente nu l-am măsurat |
| Bilanț | folosește vremea firului C (`data/raw/C`) | `make c-weather` | inclus mai sus |

## Probleme găsite (și cine le repară)

1. **C: 9 teste cer internet** (`tests/c/test_connection.py` ×5, `test_decisions.py` ×1, `test_remedies.py` ×3). Când lipsește `data/raw/C`, `weather.archive()` descarcă vremea de la Open-Meteo. Într-o clonă curată fără internet, `make check` pică. Cu internet, testele consumă cotă la fiecare rulare. Repară firul C: o mostră mică de vreme în `data/samples/C/` pentru teste, sau teste sărite când datele lipsesc.
2. **A: serverul din Londra a ignorat cererea pe interval** (HTTP 200 în loc de 206) după 15 fișiere. Descărcarea s-a oprit, iar antrenarea a mers mai departe pe 44 din 45 de fișiere, cu alte cifre și fără avertisment. **Reparat** în `Teo-A-contoare`, commit `905374d`: reîncercare fără să descarce toată arhiva, raport cu fișierele lipsă, iar antrenarea refuză un set incomplet. Are 3 teste.
3. **B: gazetteer-ul recensământului se descarcă de mână.** Juriul are un pas nescris în Makefile. Repară firul B: descărcarea în `make b-data`, sau fișierul de 776 KB în `data/samples/B/` (date publice ale guvernului SUA).
4. **B: vremea pentru comitate durează ~2 ore și ia ~73% din cota zilnică Open-Meteo.** Repară firul B: tabelul procesat de vreme în git, ca juriul să poată sări `b-weather`, plus o notă în README.
5. **Bilanț: ordinea pașilor.** Raportul din `make bilant-eval` scrie „PT-1269: rulează întâi make bilant-predict”, deci secțiunea cu postul demo rămâne goală în ordinea documentată (data → eval → predict). Repară firul bilanț: inversează ordinea în `docs/data/bilant.md`, sau raportul să nu depindă de predicții.
6. **Repo-ul are 365 MB**, din care ~112 MB sunt două arhive `.zip` din `presentation/assets/` și ~52 MB piste audio `.wav`. În plus, `models/release/C/bundle.joblib` (9 MB) apare de 4 ori în istoric. Clona de pe GitHub a mers cu ~120 KB/s și s-a blocat la 14 MB, așa că am folosit o clonă locală a aceleiași ramuri. Decide orchestratorul (și firul prezentare), înainte ca repo-ul să devină public: binarele mari scoase din istoric sau mutate în Git LFS.
7. **`uv sync` pe o mașină nouă** descarcă ~1 GB de pachete. Aici a durat o secundă, pentru că cache-ul uv era plin. Nemăsurat la rece.
8. **Scenariul `maine`** cere prognoza live de la Open-Meteo pentru B și C. Nu l-am rulat, ca să nu consum cota înainte de 02:00.

## Cum am rulat

Scriptul de măsurare a pornit de la o clonă locală completă (`git clone --no-local --branch Teo`). Pentru pașii cu modele a blocat rețeaua (`HTTPS_PROXY=http://127.0.0.1:9`, `UV_OFFLINE=1`). A rulat fiecare comandă din tabel cu jurnal separat și durată. Jurnalele nu sunt în git: erau în `/tmp/cp-clean-logs/`.
