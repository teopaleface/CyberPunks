# Status: Teo-ui
Actualizat: 2026-11-07 13:14
Milestone curent: M0
Gata de merge: nu

## Făcut
- 12:45 Citite: prompts/_comun.md, prompts/ui.md, memory/ (INDEX, 07, 08, 10, journal), docs/PLAN.md, docs/CONTRACTS.md, contracts.py, contracts/fixtures/.
- 12:45 `uv sync` și `make check` trec (ruff curat, 7 teste).
- 12:50 Paleta PPC verificată din CSS-ul site-urilor: ppcgroup.com `--primary-black #000f1e`, `--primary-blue #00a3e0`, `--primary-red #fa4616`; ppcenergy.ro `primary #163fe8`, `third #ff6447`; font PingLCG (proprietar, nu îl folosim). Folosim doar familia de culori (bleumarin, albastru, cald), nu valorile exacte.
- 12:52 OpenFreeMap merge fără cheie: stilurile positron, bright, liberty, dark, fiord (HTTP 200), dale vectoriale peste București (z12, 150 KB), glife Noto Sans cu ș/ț. Randat headless cu agent-browser; etichetele se pun pe numele local (`name`), altfel apare „Bucharest”.
- 12:53 Fonturi verificate pe fișierele Google Fonts (cmap): ș/ț cu virgulă (U+0219/U+021B, glife separate de ş/ţ cu sedilă), ă, â, î în toate cele 34 de candidate (Archivo, Sofia Sans, Instrument Sans, Geist, IBM Plex, Inter Tight etc.).
- 12:55 Pornite în paralel: scheletul Next.js (subagent), logoul cu Codex (3 concepte, PNG + SVG în `web/public/brand/`), 3 machete de direcție vizuală pe datele din fixture-uri (`web/design/directions/`: „Panou” HMI de dispecerat, „Mersul echipelor” orar, „Noaptea dinaintea turei”).

- 13:00 Logo: Codex a livrat 3 concepte (PNG + SVG) în `web/public/brand/`; ales A, „răsărit pe traseu” (soare care răsare în spatele traseului unei echipe). Favicon: `web/app/icon.svg`.
- 13:05 Schelet Next.js gata (subagent): Next 16.4 (Cache Components), React 19.3, Tailwind 4, shadcn/ui, MapLibre 6.16, Recharts 3.10, bun; stratul de date API → instantaneu demo → fixture-uri, cu proveniența afișabilă; 17 teste trec, build și lint curate. API-ul planificatorului răspunde deja pe 8710 (`demo-vara`).
- 13:10 Trei machete pe datele reale din fixture-uri, arătate lui Teo (`web/design/directions/`): Panou, Mersul echipelor, Noaptea dinaintea turei.
- 13:12 Conturul județelor (Natural Earth, domeniu public, nume cu diacritice) în `web/public/geo/ro-judete.json`, pentru harta mică a zonei Rețele Electrice.

## Urmează
- Aplic direcția Panou în aplicație: temă (culori, Archivo cu ș/ț), logo, antet, cifrele zilei.
- M0 la 14:30: direcția aleasă (făcut), logo (făcut), proiectul Next.js pornit (făcut), tema aplicată.
- M1 la 17:30: ecranul 1 (hartă, linia de timp a echipelor, coada „Nu sunt sigur”, alerta, detaliul lucrării) pe API și pe fixture-uri.

## Blocaje
- niciunul

## Cereri către orchestrator
0. Te rog notează în `memory/journal.md` deciziile de design de mai jos (13:00 paleta validată, 13:14 direcția Panou), eu n-am voie acolo.
1. Fixture-uri de serii (`Series`), câte una pe sursă, pentru lucrările din fixture-uri: `A-20261109-MTR-004217` (consum zilnic 60 de zile cu cele 9 zile de zero, `expected` = normalul), `B-20261109-CT-MEDGIDIA` (rafale orare 48 h și riscul, fereastra 12:00–20:00), `C-20261109-PT-1432` (tensiune 15 min pe 24 h, P10/P50/P90, `thresholds: {limita_tensiune_pu: 1.10}`), etichetate `synthetic: true`, generate de `contracts/make_fixtures.py` (de exemplu `contracts/fixtures/series_<id>.json`). Fără ele, detaliul lucrării n-are grafic până la API.
2. Planul din fixture-uri are decizii doar pentru 4 din 8 lucrări. Pentru interfață ar ajuta câte o decizie pentru fiecare tip: `B-20261109-CT-MEDGIDIA` (assigned, echipă CT, `preposition_crew`), `B-20261109-IF-SNAGOV` (deferred), `C-20261109-PT-0877` (notify), `A-20261109-MTR-BAD` (rejected_invalid), plus `remote_action` pentru un contor. Interfața tratează oricum lucrările fără decizie („neplanificate”).
3. Către planificator (prin tine): structura lui `outputs/demo/`. Propunerea mea, pe care interfața o citește deja ca rezervă: `outputs/demo/<scenariu>/plan.json`, `audit.jsonl`, `work_items/{A,B,C}.jsonl`, `series/<work_item_id>.json`, `run.json` (timpii ultimei rulări: `{plan_id, timings: {perceive, estimate, decide, act}}`), plus `outputs/demo/metrics/{A,B,C}.json`. Dacă alege altă structură, să o scrie în `docs/CONTRACTS.md`.
4. Către planificator: interfața cheamă API-ul de pe server (Next.js), deci CORS nu e necesar, dar nu strică.
5. `contracts/fixtures/plan_example.json` nu se potrivește cu el însuși: `summary.total_km` = 31,4, dar traseele adună 29,0 + 4,8 = 33,8 km; `summary.expected_value_lei` = 2.741,2, dar lucrările alocate adună 1.239,75 + 746,2 + 912,0 = 2.897,95 lei. Juriul poate observa. Planificatorul să verifice în cod că rezumatul e suma traseelor și a deciziilor (un test).
6. Către planificator: în `Route` ar ajuta `depart_at` și `return_at` (acum interfața le deduce din `eta` și `total_travel_min`), iar costul vizitei folosit la decizie să apară în `Decision.threshold` (de exemplu `visit_cost_lei: 180`), ca interfața să nu-l citească din `config/economics.yaml`.
7. API-ul trimite `scenario_id` la `GET /scenarios`, iar `docs/CONTRACTS.md` nu spune numele câmpului. Interfața acceptă ambele (`scenario_id` și `id`).

## Cum se rulează (comenzile exacte)
- (după schelet) `make web` → http://localhost:3710

## Cifre (doar din scripturi, cu comanda)
- niciuna (interfața doar afișează cifrele firelor)

## Decizii (cu ora)
- 12:48 Faza 0 cu subagenți în paralel: scheletul Next.js separat de direcția vizuală, ca M0 să prindă ora 14:30.
- 12:50 Trimiterea la PPC rămâne discretă: familia bleumarin + albastru + o culoare caldă, fără valorile lor exacte și fără fontul PingLCG, ca să nu pară produs oficial.
- 12:54 Logoul: Codex desenează doar semnul (fără text), iar numele „Tura de mâine” îl scriem cu fontul interfeței, ca diacriticele să fie sigur corecte.
- 13:00 Culorile surselor, validate cu scriptul pentru daltonism (abilitatea dataviz): temă deschisă A `#2C6FD9`, B `#A23C9E`, C `#D99100`; temă închisă A `#3B82F0`, B `#B84FC0`, C `#C4880A`. Violetul inițial pentru B a picat testul (ΔE 0,9 față de albastru la deuteranopie); mov-prună trece (10,7).
- 13:14 Direcția aleasă: Panou (HMI de dispecerat, temă deschisă). De ce: vorbește limba dispecerilor Rețele Electrice (gri în repaus, culoare doar pentru ce contează; ziua echipelor ca schemă monofilară), se vede bine pe proiector, iar linia de timp a echipelor e ideea memorabilă. Iau de la „Noaptea dinaintea turei” ferestrele de timp (furtuna, soarele) pe linia de timp a echipelor și de la „Mersul echipelor” orele mari, înguste. Temele închise se spală pe proiector, deci „Noaptea” rămâne doar idee pentru video.
- 12:55 Culorile surselor sunt aceleași în toate direcțiile: A Contoare albastru, B Furtună violet, C Tensiune chihlimbar; markerii poartă și litera, ca să nu depindem doar de culoare.
