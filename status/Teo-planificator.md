# Status: Teo-planificator
Actualizat: 2026-11-07 13:48
Milestone curent: M2 aproape gata (lipsesc doar ieșirile reale A, B, C, care nu există încă în `Teo`); extinderea din 13:45 implementată
Gata de merge: da (commit 6bdb0f5, plus acest status)

## Făcut
- 12:53 API pe http://127.0.0.1:8710/api (`make api`, documentație la `/docs`).
- 12:58 M0: `docs/research/planificator.md`, `config/economics.yaml` cu etichete SURSĂ / PROXY / CALCUL / IPOTEZĂ, `config/planner.yaml`.
- 13:11 M1: `uv run cyberpunks run --scenario demo-vara` cap-coadă (validare, carantină, reguli cu `rule_id`, OR-Tools cu rezervă greedy, jurnal, alerte, notificări, raport, om în buclă).
- 13:20 Cererile orchestratorului de la 13:20: echipe în Banat, `depart_at`/`return_at`, costul folosit în `threshold`, testul de totaluri, furtuna după `storm_onset`, `safety_flag` la B ca avertisment.
- 13:25 Ordinele de lucru PDF, câte unul pe echipă (Noto Sans OFL, diacritice verificate vizual).
- 13:31 Evaluarea agentului (`reports/planner/agent_eval.json`) și măsurarea solverului (`reports/planner/solver_benchmark.json`); cifrele mai jos.
- 13:31 Prag etic la contoare: echipa merge la ușa unui client doar dacă scorul e cel puțin 0,5; sub prag, citire la distanță.
- 13:44 Extinderea (decizia lui Teo de la 13:45): `A_bilant.jsonl` citit lângă `A.jsonl`, fuziunea cu `R-FUSION-BILANT` în jurnal, reguli pentru acțiunile noi, lista pe echipe după lei pe oră, scara de soluții C (`R-REMEDY-LADDER`), cu completările de la 14:00 (mesaj țintit din `message_preview_ro`, oferta de baterii pentru PPC Energie).
- 13:46 API pentru extindere (rutele de mai jos). 56 de teste trec, ruff curat. `git merge Teo` făcut după fiecare anunț (ultimul: documentul de research).

## Pentru firul Interfață (rute noi, toate cu `?scenario=`)
- `GET /api/posts` → listă de posturi pentru hartă: `{post_id, lat, lon, zone_id, label, loss_lei_month, loss_kwh_day, color: verde|galben|rosu|necunoscut, diagnosis, bilant_score, bilant_work_item_id, bilant_decision, bilant_rule_id, voltage_p90_pu, c_work_item_id, c_decision, c_rule_id, meters_flagged, meter_work_item_ids, synthetic}`, ordonată după lei pierduți. Pragurile culorilor: `config/planner.yaml` (`posts`: galben de la 200 lei/lună, roșu de la 600).
- `GET /api/posts/{post_id}` → același rezumat plus `work_items` (fiecare cu `decision`) și `series_ids` (pentru `GET /api/series/{id}`).
- `POST /api/routes/{crew_id}/approve` `{reviewer, note}` → aprobarea listei unei echipe (jurnal `route_approve`, `actor: human`, pe fiecare oprire). `GET /api/approvals` → `[{crew_id, reviewer, ts, plan_id, work_item_ids, stale}]`.
- `POST /api/verdict/{id}` `{outcome: confirmed|not_found|other_problem|no_access, reviewer, note}` → `{audit, label}`; `GET /api/labels` → etichetele pentru reantrenare.
- `GET /api/rules` → `{rules: {rule_id: explicație}, thresholds, economics}`.
- `GET /api/remedies` → scara C pe fiecare post: `{post_id, work_item_id, label, chosen: [acțiuni], cost_lei, p90_before_pu, p90_after_pu, why_not_cheaper: [texte], invest, feasible, battery: {...} | null, inverter_trips_avoided}`.
- În plan, ordinea deciziilor: întâi verificările de la distanță și corecțiile din birou, apoi lista pe echipe (`rank` = ordinea după lei pe oră de lucru, în `threshold.lei_per_work_hour`), apoi restul.
- Rutele de mai înainte rămân la fel (vezi `docs/CONTRACTS.md` și `/docs`).

## Pentru firul Bilanț (te rog transmite)
- Citesc `outputs/work_items/<s>/A_bilant.jsonl` și apelez `cyberpunks.a_bilant.predict.run(scenario, date)` la fel ca la A. Fuziunea: `cyberpunks.a_bilant.fuse.fuse(items, scenario, date)`; păstrez o lucrare fuzionată doar dacă trece contractul, `extra["fusion"]` e `BilantFusion` valid și verificările de sens (aceeași dată, același activ, `expected_value_lei` = scor × valoare). Altfel rămâne lucrarea A originală, cu alertă.
- Pentru lucrările la nivel de post citesc din `extra`: `post_excess_loss_lei_month` (culoarea de pe hartă), `post_excess_loss_kwh_day`. Diagnosticul vine din `prediction.label`; am texte în română pentru `contor_defect`, `furt_inainte_de_contor`, `pierdere_tehnica`, `post_gresit`, `contor_post_x2` (alte etichete apar cu `_` înlocuit prin spațiu).
- Reguli: `office_correction` → coada biroului (15 lei, fără deplasare); `remote_reading` → verificări de la distanță; `grid_inspection` → echipa `lv_grid` (cost 486 lei, tariful RER ca PROXY) dacă valoarea acoperă deplasarea; `inspect_on_site` la post → echipa de contoare; `watchlist`, `human_review`. Pentru `grid_inspection`, `effort.crew_skill` trebuie să fie `lv_grid`.
- Etichete pentru reantrenare: `outputs/plans/<s>/labels.jsonl`, câte o linie pe verdict: `work_item_id, prediction_id, model_id, model_version, predicted_label, score, outcome, label (1 = confirmat, 0 = nimic găsit, null = altceva), reviewer, ts`.

## Pentru firul C (te rog transmite)
- Scara: o treaptă singură folosește `p90_after_pu`; la combinații adun efectele (`P90 = P90 inițial + Σ effect_pu`), cel mult 3 trepte, doar `combinable: true`; `transformer_upgrade` doar singur. P90 inițial = `prediction.point_interval[1]`. Aleg cea mai ieftină combinație sub 1,10 pu; la egalitate, mai puține trepte și încredere mai mare.
- Folosesc `cost_lei` exact cum îl trimiteți. Costurile din config, ca să le folosiți la calcul: `config/economics.yaml`, secțiunea `remedies` (fazele 300 lei, participarea 10/20/30%, baterii 1.250 lei/kWh + 2.500 lei montaj, plafonul AFM 1.500 lei/kWh, limita de export 50 lei, transformator nou 80.000 lei, ultimele ca IPOTEZĂ).
- `adjust_tap` și `phase_rebalance` cer întrerupere planificată, deci preaviz ANRE: pentru mâine se programează mai târziu, iar mâine pleacă doar mesajele. `planned_outage_notified: true` în `extra` dacă întreruperea e deja anunțată.
- `message_preview_ro` intră neschimbat în notificare (audiență `prosumatori`, `demo_only`). `battery_kwh_total`, `revenue_lei`, `payback_years`, `customers_targeted` intră în lista pentru PPC Energie din raportul zilei. `participation_rate` apare în explicație („la 20% participare”).

## Urmează
- Instantaneul `outputs/demo/` și `reports/planner/README.md` (metoda evaluării), apoi trecerea pe ieșirile reale A, B, C și bilanț când apar în `Teo`.
- Prima pagină a PDF-ului (acum rămâne pe jumătate goală când prima oprire nu încape).

## Blocaje
- Niciunul. Ieșirile reale ale modelelor nu există încă în `Teo`; până atunci planul rulează pe exemple, marcat ca atare.

## Cereri către orchestrator
- Transmite secțiunile pentru Bilanț și C.
- Pragurile de repunere din `config/economics.yaml` (`storm.restoration_limit_hours`: 6 / 4 / 12 h, 48 / 72 h) vin din sursa primară: subagentul meu a citit Ord. ANRE 46/2021, art. 15 alin. (1), din Monitorul Oficial 649/2021, cu citat în `docs/research/planificator.md`. Cele „8 h” din documentul de research sunt durata maximă a unei întreruperi planificate (art. 13 alin. 1), nu termenul de repunere.

## Cum se rulează (comenzile exacte)
- `uv sync && make check`
- `uv run cyberpunks run --scenario demo-vara` (sau `--mode fixtures`, `--date YYYY-MM-DD`)
- `uv run cyberpunks review A-20261109-MTR-027710 approve --note "verificat"`
- `make api` → http://127.0.0.1:8710/api/health
- `uv run python -m cyberpunks.planner.evaluate` (evaluarea agentului, ~2 min)
- `uv run python -m cyberpunks.planner.benchmark` (solverul, ~6 min)

## Cifre (doar din scripturi, cu comanda)
- Evaluarea agentului, 30 de zile SINTETICE (lume cu adevărul cunoscut, scoruri calibrate), aceleași 11 echipe și restricții (`uv run python -m cyberpunks.planner.evaluate`): valoare netă pe zi: agentul 35.061 lei; primul venit 23.552; top-K după scor 23.255; aleator 18.203; doar contoare 5.459. Km pe zi: agentul 352, top-K 511. Urgențe ratate (furtuni reale și cazuri de siguranță fără echipă): agentul 19,6%, top-K 26,8%, doar contoare 85,7%.
- Ablații pe aceleași zile: fără pragul etic 40.806 lei/zi (dar 46% vizite fără problemă la contoare, față de 37% cu prag); trasee greedy în loc de OR-Tools 34.384 lei/zi.
- Robustețe: cu un model supra-încrezător (10 zile), agentul 20.683 lei/zi față de 14.011 la top-K.
- Sensibilitate: avantajul agentului față de top-K rămâne între +48% și +77% când variem costul pe client-oră (5,5-15 lei), tura de furtună (1.500-4.100 lei) și vizita (180-340 lei).
- Solverul (`uv run python -m cyberpunks.planner.benchmark`): pe 100, 200 și 300 de lucrări candidate (11 echipe), OR-Tools aduce cu 3-19% mai multă valoare netă decât greedy, în 1,4-9 s; 30 de secunde în plus adaugă sub 1%.

## Decizii (cu ora)
- 12:50 Faza 0 cu 3 subagenți de cercetare în paralel.
- 12:53 API-ul citește, în ordine: ultima rulare (`outputs/`), instantaneul `outputs/demo/`, apoi `contracts/fixtures/`.
- 12:58 Vizita la contor 250 lei (tariful RER 2026, PROXY), energia pierdută 0,70 lei/kWh (PZU 2026), tura de furtună 2.700 lei (CALCUL).
- 13:05 Echipa de furtună rămâne în zonă: nodul B e ultimul din traseu, drumul înapoi costă 0.
- 13:09 Fiecare lucrare lăsată afară are motivul ei (`R-CAPACITY`, `R-TIME-WINDOW`, `R-B-TOO-LATE`, `R-NOT-WORTH-TRIP`, `R-NO-CREW`) și, unde există, o rezervă (citire la distanță la A, mesaj la C).
- 13:10 Pentru scenariile istorice, momentul deciziei e seara dinainte, la 18:00 (contează la preavizul ANRE).
- 13:18 Premiul din trasee = valoarea așteptată − costul acțiunii; factorul de urgență scos (lăsa echipele goale, văzut în simulare).
- 13:18 Contoare cu încredere medie: echipă doar cu o marjă de 25% din costul vizitei (`R-A-VISIT-MEDIUM`).
- 13:23 La B, `safety_flag` (rafale) e avertisment pentru echipă, nu lucrare obligatorie. Plafonul de echipe de furtună pe regiune: 3.
- 13:31 Pragul etic (`meters.visit_min_score: 0.5`): costă ~5.700 lei/zi în simulare, dar scutește clienții la care e mai probabil să nu fie nicio problemă. Ablația e în raport, ca juriul să vadă compromisul.
- 13:40 La bilanț, pragul etic nu se aplică lucrărilor la nivel de post (nu e ușa unui client); se aplică contoarelor găsite de bilanț.
- 13:42 Scara C: efectele treptelor combinate se adună; o treaptă singură folosește `p90_after_pu` calculat de C. Treptele cu echipă care cer întrerupere (`adjust_tap`, `phase_rebalance`) au nevoie de preaviz ANRE.
- 13:44 Lista pe echipe se ordonează după lei pe oră de lucru (valoarea netă / (durata + drumul estimat)); OR-Tools alege tot după valoare, în limita turei.
