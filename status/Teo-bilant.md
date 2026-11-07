# Status: Teo-bilant
Actualizat: 2026-11-07 13:45
Milestone curent: M1 făcut, lucrez la M2
Gata de merge: da (commit 545dd7b)

## Făcut
- Faza 0: `docs/research/bilant.md` (rezumat), `bilant_lit.md` (CPT RER, NTL, client la postul greșit, cu surse), `bilant_faze.md` (fazele: formula ajustată pe 768 de rulări `runpp_3ph`).
- Lumea simulată (`a_bilant/world.py`, `problems.py`): posturile din registrul C, calculul de rețea al lui C, pierderile pe fiecare cablu din curenți, corecția de faze, contorul de bilanț, contoarele clienților (bidirecționale la prosumatori, goluri, erori), tensiunea în contor; 5 probleme ascunse din tabelul conceptului.
- Setul (`a_bilant/dataset.py`): 300 de posturi `train` (sintetice noi) + cele 300 din registrul C (`pop`, test pe rețele nevăzute), 373 de zile (2024-07-01 … 2025-07-08, ziua demo). Rulează în ~1 minut pe 4 procese.
- Modelul 1, pierderea normală (`a_bilant/normal.py`): LightGBM cuantile P10/P50/P90 + interval calibrat (conformal); două variante, cu istoricul postului și fără (post nou). Baseline-uri: procent fix și formula fizică I²R.
- `reports/bilant/metrics.json` (ModelReport valid, `source: A`, `model_id: bilant-normal-lgbm`), `reports/bilant/normal_loss.png`, teste în `tests/bilant/` (8, trec), secțiunea Bilanț în Makefile.

## Urmează (M2, 21:30)
- Modelul 2, diagnosticul cauzei (clasificator pe fereastra de 14 zile) față de tabelul de reguli din concept; potrivirea clientului (tensiune și curbă).
- `fuse.fuse`, cifra „cu bilanț față de fără” (precizia în primele K, deplasări degeaba), `predict.run` → `outputs/work_items/demo-vara/A_bilant.jsonl` + serii.

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Posturi diferite la A și la C.** A folosește posturile lui (`data/samples/A/posts.csv`, PT-0001…, ~400) și contoarele `MTR-*` legate de ele; registrul comun e al lui C (PT-1001…PT-1300). Ca fuziunea bilanț + A să găsească aceleași posturi, A trebuie să-și lege contoarele de `post_id`-urile lui C. Până atunci `fuse` leagă un post A necunoscut de cel mai apropiat post din registrul C, marcat ca legătură aproximativă.
2. Când C publică `posts.py`/`load_posts()` și A are `inject.py`/`predict.py` în `Teo`, vă rog merge în `Teo`. Până atunci registrul vine dintr-o copie (`data/samples/bilant/posts_C_registry_copy.csv`).
3. `memory/journal.md`: „Bilanț M1: pierderea normală simulată are mediana 3,8% din energia care trece prin post (reper RER: CPT 8,66% în 2023, 63,54% pe JT, inclusiv pierderile comerciale); modelul cu istoric greșește cu 5,2 kWh/zi față de 14,7 la formula fizică.”

## Cum se rulează (comenzile exacte)
- `make bilant-data` (sau `uv run python -m cyberpunks.a_bilant.dataset --workers 4`); cere meteo C în `data/raw/C` (`make c-weather`).
- `make bilant-eval` (sau `uv run python -m cyberpunks.a_bilant.evaluate`)
- `make bilant-test`

## Cifre (doar din scripturi, cu comanda)
Comanda: `uv run python -m cyberpunks.a_bilant.dataset && uv run python -m cyberpunks.a_bilant.evaluate`. Test: 61.123 de zile curate pe 300 de posturi nevăzute (registrul C). SIMULARE.
- Pierderea normală, eroarea medie (MAE): **5,18 kWh/zi** (14,6% din pierderea medie de 35,6 kWh/zi), acoperirea intervalului P10-P90: 83,6%.
- Fără istoricul postului: 12,36 kWh/zi, acoperire 83,7%.
- Baseline formula fizică I²R: 14,72 kWh/zi; procent fix: 19,75 kWh/zi.
- Pierderea normală simulată: mediana 3,8% din energia care trece prin post.

## Decizii (cu ora)
- 13:35: lucrez pe registrul de posturi al lui C; calculul de rețea al lui C e echilibrat, deci fazele le adaug cu formula din `bilant_faze.md`.
- 13:45: calibrare ×2,5 (±35% între posturi) a pierderilor din SimBench, ca mediana să fie ~3-4% (IPOTEZĂ, sub CPT-ul RER care include și furtul).
- 13:50: două modele de pierdere normală (cu istoric, fără istoric), nu unul cu augmentare (augmentarea strica modelul principal: 6,2 în loc de 5,2 kWh/zi).
