# Contractele dintre fire

Sursa de adevăr e `src/cyberpunks/common/contracts.py`. Schemele JSON din `contracts/*.schema.json` se generează din el (`make schemas`). Exemple valide, ilustrative: `contracts/fixtures/` (`make fixtures`). Proprietar: orchestratorul.

Validare: `uv run cyberpunks validate <fișier>` (sau `--as work_item|plan|audit|model_report|series`).

## Convenții

- Ora: ISO 8601 cu fus orar, Europe/Bucharest (`+02:00` iarna, `+03:00` vara).
- Bani în lei, energie în kWh, tensiune în unități relative (pu, 1.0 = nominal).
- Coordonate WGS84. Validatorul respinge punctele din afara României.
- ID-ul unei lucrări: `<sursă>-<YYYYMMDD>-<asset_id>`, de exemplu `A-20260712-MTR-004217`.

## Fișierele

| Fișier | Cine scrie | Contract |
|---|---|---|
| `outputs/work_items/<scenariu>/A.jsonl` (și `B`, `C`) | firele A, B, C | `WorkItem`, câte unul pe linie |
| `outputs/series/<scenariu>/<work_item_id>.json` | firele A, B, C | `Series` (graficul din detaliul lucrării) |
| `outputs/plans/<scenariu>/plan.json` | planificatorul | `Plan` |
| `outputs/plans/<scenariu>/audit.jsonl` | planificatorul (și API-ul la decizia omului) | `AuditRecord` |
| `outputs/plans/<scenariu>/work_orders/<crew_id>.pdf` | planificatorul | PDF |
| `outputs/plans/<scenariu>/report.md` | planificatorul | raport zilnic |
| `reports/<A|B|C>/metrics.json` | firele A, B, C | `ModelReport` |
| `reports/planner/agent_eval.json` | planificatorul | liber, documentat în `reports/planner/README.md` |
| `outputs/demo/` | planificatorul | instantaneu complet al scenariului demo, în git |

Scenariile sunt în `config/scenarios.yaml`: `demo-vara` (zi reală de vară cu furtuni, data o alege firul B) și `maine` (prognoza reală).

## WorkItem (ce trimite fiecare model planificatorului)

| Câmp | Ce înseamnă |
|---|---|
| `source`, `kind` | A → `meter_inspection`, B → `storm_prepositioning`, C → `voltage_mitigation` |
| `asset_id`, `asset_type` | contor, zonă (județ sau localitate) sau post de transformare |
| `location` | lat, lon, `zone_id`, județ, etichetă |
| `target_date`, `time_window` | ziua și, unde contează, fereastra (B: înainte de furtună; C: la prânz) |
| `prediction` | `model_id`, `model_version`, `prediction_id` (uuid), `label`, `score` (probabilitate calibrată), interval, `point_estimate` cu unitate și interval, `confidence`, `abstain` cu motiv |
| `impact` | `value_if_true_lei`, `expected_value_lei` (= score × valoare), clienți afectați, urgență în ore, `safety_flag`, cheia de ipoteze din `config/economics.yaml` |
| `effort` | durata, abilitatea echipei (`metering`, `lv_grid`, `mv_grid`), mărimea echipei, dacă cere întrerupere planificată |
| `explanation` | 1-8 factori (`label_ro` în cuvinte simple, contribuția SHAP), cazuri similare, o frază din șablon |
| `data_quality` | cota de date lipsă, problemele găsite la intrare și cum au fost tratate, `synthetic`, sursele citate |
| `recommended_action` | ce recomandă modelul; planificatorul decide final |
| `extra` | câmpuri specifice sursei (de exemplu `series_ref`) |

Reguli verificate automat: litera din ID = sursa; `kind` potrivit sursei; `abstain=True` cere `human_review` și un motiv; scorul stă în interval.

## Plan și jurnal (ce produce agentul)

- `Plan`: rezumatul zilei, traseele pe echipe (opriri cu ora estimată și km), o decizie pentru fiecare lucrare (`assigned`, `deferred`, `human_review`, `remote_action`, `notify`, `rejected_invalid`) cu `reason_ro`, `rule_id`, pragurile folosite, rangul și `audit_id`; alerte; notificări (doar demo, nu se trimite nimic); starea surselor (`ok`, `missing`, `degraded`).
- `AuditRecord`: o linie pentru fiecare decizie a agentului sau a omului, cu `prediction_id`, `model_version`, `rule_id`, praguri și amprenta intrărilor. Așa se urmărește orice decizie până la predicția care a produs-o.

## API (firul planificator, http://127.0.0.1:8710/api, CORS pentru http://localhost:3710)

| Metodă și cale | Răspuns |
|---|---|
| `GET /health` | `{status, version, sources_status}` |
| `GET /scenarios` | lista din `config/scenarios.yaml` |
| `POST /run` `{scenario, date?}` | rulează agentul cap-coadă; `{plan_id, timings: {perceive, estimate, decide, act}}` în secunde |
| `GET /plan?scenario=` | `Plan` |
| `GET /work-items?scenario=&source=` | listă de `WorkItem` |
| `GET /work-items/{id}?scenario=` | `WorkItem` plus decizia lui |
| `GET /series/{id}?scenario=` | `Series` |
| `GET /audit?scenario=&work_item_id=` | listă de `AuditRecord` |
| `POST /review/{id}` `{decision: approve|reject|defer, note, reviewer}` | `AuditRecord` cu `actor: human`; planul se recalculează |
| `GET /metrics` | `{A, B, C: ModelReport, planner: {...}}` |
| `GET /work-orders/{crew_id}.pdf?scenario=` | PDF-ul ordinului de lucru |

Până la ora 16:00 API-ul servește `contracts/fixtures/`. Interfața are rezervă: dacă API-ul nu răspunde, citește `outputs/demo/` sau fixture-urile.

## Cum se cere o schimbare

Scrie în `status/<branch>.md`, la "Cereri către orchestrator": ce câmp, de ce, un exemplu. Orchestratorul schimbă `contracts.py`, regenerează schemele și fixture-urile, face merge în `Teo` și anunță toate firele.
