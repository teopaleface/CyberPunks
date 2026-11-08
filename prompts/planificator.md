# Firul Planificator: agentul (decizie, trasee, acțiuni, jurnal, API)

Branch: `Teo-planificator`. Status: `status/Teo-planificator.md`.

## Ce deții

`src/cyberpunks/planner/`, `src/cyberpunks/api/`, `src/cyberpunks/cli.py`, `config/` (toate fișierele), `tests/planner/`, `reports/planner/`, `docs/research/planificator.md`, `outputs/demo/`, secțiunea planificatorului din `Makefile`, `status/Teo-planificator.md`.

## De ce contează

Agentul valorează 25 de puncte: "un flux complet și automat, de la date la model, la decizie și la acțiune, cu un strat de decizie justificat". Robustețea (10) și explicabilitatea (10) trec tot prin tine: carantina intrărilor greșite, sursele lipsă, "nu sunt sigur" trimis la om, urmărirea fiecărei decizii până la predicție. Interfața depinde de API-ul tău.

## Faza 0: cercetare (cel mult 45 de minute, subagenți în paralel), scrisă în `docs/research/planificator.md`

1. Verifică și citează ipotezele din `config/economics.yaml`: costul unei vizite de verificare a contorului, prețul energiei pierdute pentru distribuitor (CPT), costul unui client-oră întrerupt, compensațiile ANRE pentru întreruperi lungi, cât anunță distribuitorul înainte de o întrerupere planificată, câte intervenții face o echipă pe zi. Înlocuiește "IPOTEZĂ" cu sursa unde găsești și păstrează eticheta unde nu găsești.
2. OR-Tools: rutare cu ferestre de timp, abilități, depouri multiple și noduri opționale cu penalitate (prize-collecting VRP). Timpul de rezolvare pe 100-300 de noduri.
3. Cum arată un ordin de lucru la un distribuitor din România (câmpuri) și ce înseamnă "citire la distanță la cerere" în contorizarea inteligentă.

## Ce construiești

- Încărcare și validare: citești `outputs/work_items/<scenariu>/{A,B,C}.jsonl`. Ce nu trece de contract intră în carantină (decizie `rejected_invalid`, cu motiv). Dacă lipsește o sursă, planul merge mai departe cu celelalte (`sources_status`: `missing` sau `degraded`).
- Stratul de decizie, în cod (nu în LLM), cu reguli numite (`rule_id`) și cu pragurile scrise în fiecare decizie:
  - `abstain` → `human_review`;
  - valoarea netă = `expected_value_lei` − costul (vizită plus deplasare); sub prag → `deferred` sau o acțiune ieftină (A: `remote_reading`; C: `notify_customers` sau `watchlist`);
  - încredere medie → acțiune ieftină sau urmărire; încredere mare → echipă;
  - `safety_flag` → prioritate maximă și alertă critică;
  - B: `preposition_crew` în fereastra de timp, înainte de începutul furtunii, cu numărul de echipe limitat pe regiune;
  - C: `adjust_tap` cere întrerupere planificată, deci notificare a clienților cu timpul de anunț cerut de reguli, sau `watchlist` plus `notify_customers`.
- Optimizarea: OR-Tools, prize-collecting VRP cu ferestre de timp, abilități (`metering`, `lv_grid`, `mv_grid`), depouri, durate de serviciu, deplasare din distanța haversine × `road_factor` la viteza medie din config. Soluție de rezervă greedy dacă solverul nu termină în N secunde.
- Acțiuni: `plan.json` (`Plan`), `audit.jsonl` (`AuditRecord` pentru fiecare decizie, cu `prediction_id`, `model_version`, `rule_id`, praguri), ordine de lucru PDF pe echipă (fpdf2, cu un font cu diacritice românești inclus în repo, licență OFL), alerte (JSON), notificări (texte în română, `demo_only`, nu se trimite nimic în afară), raportul zilei `report.md` cu cifre. Căile sunt în `docs/CONTRACTS.md`.
- `uv run cyberpunks run --scenario demo-vara` rulează TOT automat: predicțiile A, B, C (importă `cyberpunks.<a_contoare|b_furtuna|c_prosumatori>.predict.run`; până există, folosește `contracts/fixtures/`), apoi planul, acțiunile și jurnalul, și afișează timpii pe etape (Perceive, Estimate, Decide, Act). Fără intervenție manuală între pași.
- Om în buclă: API pentru revizuire (aprobă, respinge, amână), scrisă în jurnal cu `actor: human`, apoi replanificare.
- Evaluarea agentului (`reports/planner/agent_eval.json` plus `reports/planner/README.md`): simulare pe mai multe zile, comparând planificatorul cu strategii simple (top-K după scor, primul venit, aleator, o singură sursă): valoarea capturată, km, lucrări urgente ratate, vizite inutile. E dovada pentru cele 25 de puncte ale agentului.
- API FastAPI pe portul 8710, exact după contractul din `docs/CONTRACTS.md`, cu CORS pentru http://localhost:3710. Pornire: `make api` (adaugă ținta în secțiunea ta din Makefile).
- `outputs/demo/`: un instantaneu complet al scenariului demo (plan, lucrări, serii, jurnal, metrici), în git, ca interfața și juriul să meargă și fără să ruleze modelele.
- LLM opțional și oprit implicit: textele vin din șabloane cu cifrele verificate în cod (lecția R Systems din `memory/09-rsystems-workshop.md`: codul decide, modelul formulează).

## Dependențe și termene

- Până la 16:00: API-ul servește `contracts/fixtures/`, ca interfața să lucreze pe date reale ca formă.
- Până la 17:30 lucrezi pe fixture-uri; apoi treci pe ieșirile reale ale firelor A, B, C, pe măsură ce apar în `Teo`.
- Data scenariului `demo-vara` o anunță firul B până la 15:00 (o pune orchestratorul în `config/scenarios.yaml`; dacă vrei s-o pui tu, e fișierul tău, dar anunță în status).

## Milestones (ora României)

- 14:30 M0: `docs/research/planificator.md`, `config/economics.yaml` verificat parțial, schelet `planner/` și `api/`.
- 16:00 API pe fixture-uri.
- 17:30 M1: `cyberpunks run` cap-coadă pe fixture-uri: validare, decizii, plan simplu (greedy), jurnal.
- 21:30 M2: OR-Tools, ordine de lucru PDF, alerte, notificări, review uman, date reale de la A, B, C.
- 03:00 M3: evaluarea agentului, teste de robustețe (intrări greșite, surse lipsă, solver care nu termină) în `tests/planner/`, `outputs/demo/` complet.
- 08:00 M4: curățenie, documentație, timpii măsurați pentru demo.
