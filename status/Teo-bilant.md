# Status: Teo-bilant
Actualizat: 2026-11-07 14:04
Milestone curent: M2 făcut, lucrez la M3
Gata de merge: da (commit 488d3d3)

## Făcut
- M1: lumea simulată, modelul pierderii normale (cu istoric și fără), baseline-uri, `reports/bilant/metrics.json`.
- M2:
  - Registrul vine acum din `cyberpunks.c_prosumatori.posts` (copia locală ștearsă). Defectele de contor vin din generatorul lui A (`a_contoare.inject.inject`), cu o punte orar ↔ jumătăți de oră.
  - Diagnosticul cauzei (`a_bilant/windows.py`, `diagnose.py`): LightGBM multiclasă pe ferestre de 14 zile (lipsa peste normal, saltul, legătura cu Σ P², noaptea, raportul post/clienți, surplusul vecinului, contoarele cu consum dispărut, tensiunea contorului), cu „nu sunt sigur” (probabilitate < 50%, egalitate, interval prea larg). Baseline: tabelul de reguli din concept.
  - Fuziunea (`a_bilant/fuse.py`, `fuse(items, scenario, date)`): raport de verosimilitate între creșterea lipsei la post și lipsa estimată de A la contor; `extra.fusion` (BilantFusion), scor și valoare recalculate, explicația spune confirmarea sau infirmarea.
  - Cifra „cu bilanț față de fără” (`a_bilant/fusion_eval.py`), figura `reports/bilant/fusion_with_vs_without.png`.
  - `predict.run(scenario, date)` → `outputs/work_items/<s>/A_bilant.jsonl` (98 de lucrări valide pentru demo-vara), 98 de serii valide, starea posturilor `outputs/bilant/<s>/posts_<data>.json` (citită de `fuse`). Dintr-o clonă curată reface singur lotul și modelele.
  - Teste: 12 în `tests/bilant/`; `make check`: 168 trec.

## Urmează (M3)
- Analiza erorilor (`reports/bilant/error_analysis.md`), teste de robustețe (contor de post lipsă, ore dublate, Wh în loc de kWh, goluri), planul B (`reports/bilant/plan_b.md`, 56-67% contoare inteligente).
- Diagnosticul clientului la postul greșit (F1 0,32, cel mai slab) și pierderea tehnică (0,36).
- Postul pentru prezentare unde dezechilibrul găsit de bilanț e intrarea pentru `phase_rebalance` la C.

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Planificatorul:** citește `A_bilant.jsonl` (sursa A, `asset_type: transformer_post`). Acțiuni folosite: `remote_reading` (51), `inspect_on_site` (17), `human_review` (12), `grid_inspection` (11), `office_correction` (7). Înainte de decizie: `from cyberpunks.a_bilant.fuse import fuse; items = fuse(items, scenario, date)` (regula `R-FUSION-BILANT`). Fără starea bilanțului pentru scenariu și dată, `fuse` nu schimbă nimic. Ordinea: `cyberpunks.a_bilant.predict.run(scenario, date)` înainte de `fuse`.
2. **A, legarea contoarelor de registrul C:** azi lucrările A au `extra.post_id` PT-0001…, deci toate cele 249 de contoare din `A.jsonl` sunt „legătură aproximativă” și `fuse` le lasă scorul neschimbat (doar o notă). Când A pune `post_id` din registrul C, fuziunea are efect. Ca să fie și o confirmare reală (nu doar aceleași ID-uri), contoarele lui A ar trebui să fie clienții acelorași posturi din simulare. Propun: A citește curbele clienților mei (`data/processed/bilant/pop`, `PT-xxxx-Cnnn`) pentru câteva posturi demo. Pot pregăti eu un export mic dacă A vrea.
3. **C, scara de soluții:** lucrările `pierdere_tehnica` au `extra.phase_rebalance_input` (`loss_ratio_vs_normal`, `max_phase_share_est`). Exemplu: PT-1269, pierderi de 2,2 ori normalul, o fază cu ~68% din case. C îl poate folosi ca intrare pentru treapta `phase_rebalance`.
4. **Interfața:** seria are `value` = ieșit din post, `expected` = suma clienților, `low`/`high` = suma clienților + pierderea normală P10/P90, `flag` = `lipsa_peste_normal` sau `surplus_sub_normal`. `extra.lei_per_month`, `extra.suspect_meter`, `extra.neighbor_surplus_post`.

## Cum se rulează (comenzile exacte)
- `make bilant-data` (~1 minut, 4 procese; cere meteo C în `data/raw/C`, `make c-weather`)
- `make bilant-eval` (~4 minute: modelele, `reports/bilant/metrics.json`, figurile)
- `make bilant-predict` (lucrările, seriile, starea pentru demo-vara)
- `make bilant-test`

## Cifre (doar din scripturi, cu comanda)
Comanda: `make bilant-data bilant-eval`. Test: cele 300 de posturi din registrul C, rețele nevăzute la antrenare. SIMULARE pe date publice.
- **Cu bilanț față de fără** (contoare verificate pe zi, problemele apărute în ultimele 2-12 zile; scorurile A sunt simulate la ROC-AUC 0,907, cel raportat de A): în primele 10, precizia crește de la 9,2% la **15,0%**, deplasările degeaba scad de la 9,1 la 8,5 pe zi, iar valoarea recuperată crește de la 424 la **874 lei pe zi**. În primele 20: de la 6,6% la 10,6%, de la 636 la 1.111 lei pe zi.
- **Pierderea normală**: MAE 5,05 kWh/zi (14,7% din 34,4 kWh/zi), acoperirea P10-P90 88,6%. Fără istoric: 12,0. Formula fizică: 14,6. Procent fix: 19,1.
- **Diagnosticul**: F1 macro 0,61 față de 0,46 la reguli; exactitate 0,71 față de 0,62. Pe clase: contor de post setat 0,99, normal 0,83, contor client 0,58, furt înainte de contor 0,56, tehnică 0,36, post greșit 0,32. Se abține în 18,8% din ferestre (F1 macro 0,64 pe restul). Primele 10 posturi după valoarea estimată prind 74% din energia lipsă (reguli: 69%).

## Decizii (cu ora)
- 13:35: registrul C; fazele cu formula din `bilant_faze.md`.
- 13:45: calibrare ×2,5 (±35%) a pierderilor SimBench (mediana 3,8%, sub CPT-ul RER).
- 13:50: două modele de pierdere normală (cu istoric, fără istoric).
- 14:00: fuziunea compară creșterea lipsei de la post (ultimele 7 zile față de e-34..e-14) cu lipsa contorului, nu nivelul: abaterea fixă a postului față de model se anulează. Cu nivelul, câștigul era aproape zero (9,2% → 9,2%).
- 14:00: contorul de post setat greșit valorează 2 deplasări (500 lei, IPOTEZĂ), nu energia „lipsă”, care e doar pe hârtie.
- 14:00: contoarele de client: întâi citire la distanță, cum cere conceptul; la fața locului doar când nu știm care contor e.
- 14:04: legătura contor A → post după poziție nu schimbă scorul (contoarele lui A nu sunt în lumea bilanțului; altfel le-am coborî scorul fără motiv).
