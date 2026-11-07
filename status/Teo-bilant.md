# Status: Teo-bilant
Actualizat: 2026-11-07 13:31
Milestone curent: M0
Gata de merge: nu

## Făcut
- Citit: _comun.md, bilant.md, memory (INDEX, 07, 08, 11), PLAN, CONTRACTS, contracts.py, fixture-uri, codul C (powerflow, grids, profiles, simulate), codul A pe branch-ul lui (inject, topology, predict; doar citit).
- `uv sync` și `ruff` trec.

## Urmează
- Faza 0 (≤30 min, subagenți în paralel): bilanțul pe post la distribuitori, CPT ANRE, literatura NTL pe zonă, clientul la postul/faza greșită, dezechilibrul de faze în calculul lui C → `docs/research/bilant.md`.
- M1 (17:30): lumea simulată pe posturile lui C cu probleme ascunse, baseline-uri, modelul pierderii normale (LightGBM cuantile), `reports/bilant/metrics.json`.

## Blocaje
- Niciunul încă.

## Cereri către orchestrator
1. **Posturi diferite la A și la C.** A folosește posturile lui (`data/samples/A/posts.csv`, PT-0001…, ~400) și contoarele `MTR-*` legate de ele; registrul comun e al lui C (`posts_population.csv`, PT-1001…PT-1300). Ca fuziunea bilanț + A să găsească aceleași posturi, A trebuie să-și lege contoarele de `post_id`-urile lui C (sau C să adopte lista lui A). Până se decide, `fuse` citește `extra.post_id` din lucrările A și, dacă postul nu e în registrul lui C, îl leagă de cel mai apropiat post din registru (după coordonate), marcat în `extra.fusion` ca legătură aproximativă.
2. Când C publică `posts.py`/`load_posts()` și A are `inject.py` în `Teo`, vă rog merge în `Teo`; le folosesc prin import.

## Cum se rulează (comenzile exacte)
- (urmează)

## Cifre (doar din scripturi, cu comanda)
- (urmează)

## Decizii (cu ora)
- 13:31: lucrez pe registrul de posturi al lui C (copie citită din `Teo-C-prosumatori` până ajunge în `Teo`); calculul de rețea al lui C e echilibrat (secvență pozitivă), deci dezechilibrul de faze îl aproximez (detalii în cercetare).
