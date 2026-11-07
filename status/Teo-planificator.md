# Status: Teo-planificator
Actualizat: 2026-11-07 13:25
Milestone curent: M0
Gata de merge: nu

## Făcut
- 12:45 Citit instrucțiunile, memoria, planul, contractele, fixture-urile. `uv sync` și `make check` trec.
- 13:20 **API-ul servește fixture-urile pe http://127.0.0.1:8710/api** (commit 274daed). Pornire: `make api` (sau `make api-dev`, cu reîncărcare). Documentație interactivă: http://127.0.0.1:8710/docs. CORS pentru http://localhost:3710 și http://127.0.0.1:3710. 13 teste în `tests/planner/test_api_fixtures.py`.
- 13:25 Cercetarea din faza 0: 2 din 3 subagenți au terminat (ordinul de lucru și citirea la distanță; costurile cu energia și contoarele).

## Pentru firul Interfață (forma răspunsurilor)
- Toate rutele din `docs/CONTRACTS.md` există. Parametrul `scenario` are implicit `demo-vara`.
- `GET /api/health` → `{status, version, planner_version, contract_version, scenario, mode, sources_status}`. `mode` e `live` (ultima rulare), `demo` (instantaneul din `outputs/demo/`) sau `fixtures`.
- `GET /api/work-items/{id}` → câmpurile `WorkItem` plus cheia `decision` (`Decision` sau `null`).
- `GET /api/series/{id}` → `Series`. În modul `fixtures`, seriile sunt generate ilustrativ (titlul conține "(ilustrativ)", `synthetic: true`), ca să puteți construi graficele: A consum zilnic cu `expected`, B rafale P10-P90 cu prag, C tensiune P10-P90 cu limita 1,10.
- `GET /api/metrics` → `{A, B, C, planner}`; fiecare e `ModelReport` sau `null` până când firele A, B, C își scriu `reports/<X>/metrics.json`. Nu pun cifre inventate.
- În plus față de contract: `GET /api/quarantine` (intrările respinse, cu motive), `GET /api/alerts`, `GET /api/notifications`, `GET /api/report` (raportul zilei, markdown).
- `POST /api/run` și `POST /api/review/{id}` răspund 503 până la M1 (17:30), când agentul rulează cap-coadă.
- Structura `outputs/demo/` (rezerva fără API) va fi identică cu `outputs/`: `plans/<s>/{plan.json, audit.jsonl, work_items.jsonl, quarantine.jsonl, alerts.json, notifications.json, report.md, work_orders/<crew>.pdf}`, `series/<s>/<id>.json`, `reports/{A,B,C,planner}/...`.

## Urmează
- `docs/research/planificator.md` și `config/economics.yaml` cu surse (M0, 14:30).
- Stratul de decizie, regulile cu `rule_id`, planul greedy, jurnalul, `cyberpunks run` cap-coadă pe fixture-uri (M1, 17:30).

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Niciuna încă.

## Cum se rulează (comenzile exacte)
- `uv sync && make check`
- `make api` → http://127.0.0.1:8710/api/health
- `make test-planner`

## Cifre (doar din scripturi, cu comanda)
- Încă nimic.

## Decizii (cu ora)
- 12:50 Faza 0 cu 3 subagenți de cercetare în paralel; partea OR-Tools o măsor direct cu codul real al solverului.
- 13:15 API-ul citește, în ordine: ultima rulare (`outputs/`), instantaneul `outputs/demo/`, apoi `contracts/fixtures/`. Așa interfața merge în orice stare a proiectului.
- 13:15 `GET /work-items/{id}` întoarce `WorkItem` cu cheia `decision` adăugată (nu un obiect separat), ca tipul din interfață să fie `WorkItem & {decision}`.
- 13:15 Validarea parametrilor din URL (scenariu, ID lucrare, echipă) cu expresii regulate, ca nimeni să nu poată citi fișiere din afara `outputs/`.
