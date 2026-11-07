# Status: Teo-planificator
Actualizat: 2026-11-07 13:25
Milestone curent: M2 în lucru (ordine de lucru PDF gata, evaluarea agentului în lucru)
Gata de merge: da (commit bb493e4, plus acest status)

## Făcut
- 12:45 Citit instrucțiunile, memoria, planul, contractele, fixture-urile. `uv sync` și `make check` trec.
- 12:53 **API-ul pe http://127.0.0.1:8710/api** (commit 274daed). `make api` sau `make api-dev`. Documentație: http://127.0.0.1:8710/docs.
- 12:58 **M0**: `docs/research/planificator.md` (3 subagenți), `config/economics.yaml` cu etichete SURSĂ / PROXY / CALCUL / IPOTEZĂ, `config/planner.yaml` cu pragurile.
- 13:11 **M1**: `uv run cyberpunks run --scenario demo-vara` merge cap-coadă (commit 272aa87): validare și carantină, reguli cu `rule_id` și praguri, trasee OR-Tools (cu rezerva greedy), jurnal, alerte, notificări (demo), raportul zilei, om în buclă (`POST /api/review/{id}` și `cyberpunks review`). 35 de teste trec, ruff curat. `git merge Teo` făcut (7da2ee6).

## Răspuns la cererile orchestratorului (13:20)
- `git merge Teo` făcut (57aa6de). Data `demo-vara` = 2025-07-08 e folosită.
- Interfața: test nou `test_plan_totals_are_consistent`: `summary.total_km` = suma traseelor, `expected_value_lei` = suma lucrărilor alocate, numărătorile = decizii, fiecare alocare e exact într-un traseu. Costul folosit la decizie e acum uniform în `Decision.threshold`: `cost_lei` (total), `action_cost_lei`, `travel_cost_lei`, `travel_km_est`, `outage_cost_lei` (unde există), pe lângă cheile vechi (`visit_cost_lei`, `preposition_cost_lei`, `tap_cost_lei`).
- `Route.depart_at` și `Route.return_at` sunt completate; la furtună `return_at` e `null` (echipa rămâne în zonă).
- B: 3 echipe simulate noi în Banat (`E-AR-1` Arad, `E-RS-1` Reșița, `E-DV-1` Deva; `lv_grid`+`mv_grid`, 3 oameni) cu baze simulate (`D-ARD`, `D-RES`, `D-DEV`). Plafonul de echipe trimise din timp pe regiune: 3. Clienții RER pe județ (31.12.2024) sunt în `config/area.yaml` (`customers_by_county`), totalul și compensațiile MT/IT în `config/economics.yaml` (`storm`).
- B, două schimbări de logică după ce am citit `status/Teo-B-furtuna.md`: (1) echipa trebuie să ajungă cu 60 de minute înainte de `extra.storm_onset` (dacă lipsește, înainte de `time_window.start`); (2) la B, `safety_flag` (rafale ≥ 75 km/h) nu mai face lucrarea obligatorie: devine avertisment pentru echipă („nu lucrează la înălțime până scade vântul”). Pentru A și C, `safety_flag` rămâne prioritate maximă și alertă critică. Lucrările `no_action` trec tot prin pragul de cost; dacă agentul trimite totuși echipă, motivul spune că modelul a recomandat altceva.
- C: cheile `complaint_compensation_lei` (70), `complaint_compensation_lei_legal` (130), `quality_limit_95pct_pu` (1,05), `ore_smart_midday` sunt în `config/economics.yaml` (`voltage`).
- Bug reparat: o rulare nouă prelua decizia omului din rularea veche. Acum deciziile omului se reaplică doar la replanificare și rămân în `history/`.
- Modul `auto` (implicit în `POST /api/run`): dacă niciun model nu are încă ieșiri pentru data scenariului, planul rulează pe exemple (`contracts/fixtures/`), cu sursele marcate `degraded` și nota în alerte. Când apar ieșirile A, B, C pentru 2025-07-08, ele au prioritate.

## Pentru firul Interfață
- API-ul servește acum planul real al agentului (calculat din fixture-uri până apar ieșirile A, B, C); `GET /api/health` → `mode: live`.
- `POST /api/run` `{scenario, date?, mode?}` → `{plan_id, timings: {perceive, estimate, decide, act}, summary, sources_status, solver}`. `mode`: `auto` (implicit, rulează modelele A, B, C), `existing`, `fixtures`.
- `POST /api/review/{id}?scenario=demo-vara` `{decision: approve|reject|defer, note, reviewer}` → `AuditRecord` cu `actor: human`; planul se recalculează pe loc. `GET /api/audit?work_item_id=` arată urma completă: agent → om → agent.
- `GET /api/work-items/{id}` → `WorkItem` + cheia `decision` (`Decision` sau `null`).
- `GET /api/series/{id}`: serii ilustrative doar în modul `fixtures`; în modul `live` vin din ieșirile A, B, C (404 până apar).
- `GET /api/metrics` → `{A, B, C, planner}`, fiecare `ModelReport` sau `null`. Fără cifre inventate.
- În plus față de contract: `GET /api/quarantine`, `/api/alerts`, `/api/notifications`, `/api/report` (markdown).
- Regulile (`rule_id`) și ce înseamnă fiecare: `RULE_CATALOG` din `src/cyberpunks/planner/decide.py` (le pot expune și prin `GET /api/rules`, dacă vreți).
- Structura `outputs/demo/` (rezerva fără API) va fi identică cu `outputs/`: `plans/<s>/{plan.json, audit.jsonl, work_items.jsonl, quarantine.jsonl, alerts.json, notifications.json, report.md, run.json, work_orders/<crew>.pdf}`, `series/<s>/<id>.json`, `reports/{A,B,C,planner}/...`.

## Pentru firele A, B, C (orchestratorul, te rog transmite)
- Valori noi în `config/economics.yaml` (cu surse): vizita la contor 250 lei (nu 180), energia pierdută 0,70 lei/kWh (nu 0,55), tura de furtună 2.700 lei (nu 1.500). Cheile au rămas aceleași.
- Planificatorul importă `cyberpunks.<a_contoare|b_furtuna|c_prosumatori>.predict.run(scenario, date) -> Path`. Dacă funcția lipsește sau dă eroare, folosește ultima ieșire din `outputs/work_items/<s>/`.
- Respinse în carantină (în plus față de contract): `target_date` diferit de data planului, data din ID diferită de `target_date`, ID care nu se termină cu `asset_id`, punct în afara zonei Rețele Electrice, `expected_value_lei` diferit de `score × value_if_true_lei` (toleranță 2%), ID duplicat.
- Câmpuri opționale citite din `extra`: A: `smart_meter: false` dacă contorul nu se poate citi de la distanță (implicit se poate). C: `planned_outage_notified: true` dacă întreruperea pentru priză a fost deja anunțată.
- C: schimbarea prizei cere preaviz de 2 zile lucrătoare (Ord. ANRE 46/2021, art. 12), așa că pentru mâine agentul o programează mai târziu și trimite mesaj către prosumatori. Costul ei include întreruperea (clienți × 1 h × 12 lei). `value_if_true_lei` ar trebui să acopere sezonul, nu doar o zi.
- B: echipa trebuie să ajungă cu 60 de minute înainte de `time_window.start`; tura începe la 08:30 (după instructaj). O fereastră care începe dimineața devreme nu poate fi acoperită.

## Urmează (M2, apoi M3)
- Gata: ordinele de lucru PDF (`outputs/plans/<s>/work_orders/<echipă>.pdf`, `GET /api/work-orders/{crew_id}.pdf`), Noto Sans (OFL) cu diacritice, câte un bloc pe oprire cu motive, pași, siguranță (AL/DV), câmpuri de completat și urmărirea până la predicție.
- În lucru: evaluarea agentului pe 30 de zile sintetice (`reports/planner/agent_eval.json`), măsurarea solverului pe 100-300 de lucrări, `outputs/demo/`.
- Evaluarea agentului pe mai multe zile față de strategii simple (`reports/planner/agent_eval.json`).
- Trecerea pe ieșirile reale A, B, C când apar în `Teo`.

## Blocaje
- Niciunul.

## Cereri către orchestrator
- Transmite firelor A, B, C secțiunea de mai sus.

## Cum se rulează (comenzile exacte)
- `uv sync && make check`
- `uv run cyberpunks run --scenario demo-vara` (sau `--mode fixtures`, `--date YYYY-MM-DD`)
- `uv run cyberpunks review A-20261109-MTR-027710 approve --note "verificat"`
- `make api` → http://127.0.0.1:8710/api/health
- `make test-planner`

## Cifre (doar din scripturi, cu comanda)
- Pe fixture-uri (`uv run cyberpunks run --scenario demo-vara --mode fixtures`): 7 lucrări, 3 în trasee (3 echipe, 84,2 km), 1 citire la distanță, 1 la om, OR-Tools în 0,1 s. Cifre ilustrative: fixture-urile nu sunt ieșiri de model.

## Decizii (cu ora)
- 12:50 Faza 0 cu 3 subagenți de cercetare în paralel; partea OR-Tools o măsor cu solverul real.
- 12:53 API-ul citește, în ordine: ultima rulare (`outputs/`), instantaneul `outputs/demo/`, apoi `contracts/fixtures/`.
- 12:53 `GET /work-items/{id}` întoarce `WorkItem` cu cheia `decision` adăugată, ca tipul din interfață să fie `WorkItem & {decision}`.
- 12:53 Parametrii din URL (scenariu, ID, echipă) se validează cu expresii regulate, ca să nu se poată citi fișiere din afara `outputs/`.
- 12:58 Vizita la contor: tariful reglementat Rețele Electrice 2026 (246,89 lei) ca PROXY, rotunjit la 250. Energia pierdută: PZU 2026 (0,70). Tura de furtună: calcul din salariu × spor de ore suplimentare (2.700).
- 13:05 Prioritatea în trasee = valoarea netă × factorul de urgență (24 h / urgency_hours, minim 0,25) × 3 la siguranță. Penalitatea OR-Tools pentru o lucrare nefăcută = prioritatea, în bani.
- 13:05 Echipa de furtună rămâne în zonă: nodul B e ultimul din traseu, drumul înapoi costă 0. Tura suplimentară e în costul de 2.700 lei.
- 13:08 Analizorul de tensiune nu are fereastră strictă (înregistrează mai multe zile), doar priza și furtuna au.
- 13:09 O lucrare lăsată afară are motivul ei: echipe pline (`R-CAPACITY`), nimeni nu ajunge la timp (`R-TIME-WINDOW` / `R-B-TOO-LATE`), drumul dus-întors costă mai mult decât valoarea (`R-NOT-WORTH-TRIP`), fără echipă potrivită (`R-NO-CREW`). Unde există, se aplică rezerva: citire la distanță (A) sau mesaj către prosumatori (C).
- 13:10 Pentru scenariile istorice, momentul deciziei e seara dinainte, la 18:00 (contează la preavizul ANRE).
- 13:10 Modul `existing` nu cade pe fixture-uri: o sursă fără ieșire e `missing`. Doar `auto` folosește fixture-urile, cât timp modelele nu există.
- 13:18 Prioritatea din trasee = valoarea așteptată − costul acțiunii (fără factorul de urgență). Factorul de urgență micșora premiul sub costul drumului și solverul lăsa echipele goale (văzut în simulare).
- 13:18 Contoare cu încredere medie: echipă doar dacă valoarea netă trece de o marjă de 25% din costul vizitei (`R-A-VISIT-MEDIUM`); altfel citire la distanță. Când echipele sunt pline, rezerva e tot citirea la distanță.
- 13:23 La B, `safety_flag` (rafale) e avertisment pentru echipă, nu lucrare obligatorie; altfel 10 zone cu rafale ar fi golit toate echipele.
- 13:23 Plafonul de echipe de furtună pe regiune: 3 (Banat are acum 4 echipe de medie tensiune).
