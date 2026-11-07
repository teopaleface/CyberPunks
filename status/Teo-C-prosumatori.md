# Status: Teo-C-prosumatori
Actualizat: 2026-11-07 17:59
Milestone curent: M4 terminat (M0 13:10, M1 13:45, M2 14:11, M3 15:40, M4 16:50)
Gata de merge: da (commit 97e4af7; `git merge Teo` făcut la 17:16, `make check` trece: 277 de teste, inclusiv `tests/test_repo_size.py`)

## QA cap-coadă (cererea de la 17:55)
- Zecimalele din textele scării sunt cu virgulă (PT-1269: „0,020 pu”, „0,001 pu”, „2,2 ori”), la fel în cererile de racordare și în raportul de baterii; datele din anunțul de întrerupere au luna în litere („9 iulie 2025”).
- Probabilitatea în texte: „peste 99%” în loc de 100%, „sub 1%” în loc de 0%.
- `extra.ladder_base_p90_pu` e în fiecare lucrare cu scară (PT-1269: 1,1768), mai mare sau egal cu P90 al modelului.
- Test nou, cap-coadă și offline (`tests/c/test_predict.py`): contractul, seriile, valoarea așteptată, câmpurile scării, fără zecimale cu punct și fără 0%/100% în texte.

## Testele C fără rețea (cererea de la 17:05)
- Cele 32 de teste din `tests/c` rulează offline: vremea vine din mostra din git `data/samples/C/weather_2025_utc.parquet` (2025, 0,15 MB), descărcările sunt blocate în `tests/c/conftest.py`. Verificat cu `data/raw/C`, `data/processed/C`, `data/interim/C` și `models/C` ascunse și rețeaua blocată (proxy invalid, `uv run --offline`): 32 trec.

## Postul pentru prezentare (legătura bilanț → C): **PT-1082**
- PT-1082, 1 Decembrie (Ilfov, sintetic). Bilanțul (`A-20250708-PT-1082`, `grid_inspection`) are `extra.phase_rebalance_input`: pierderi pe cabluri de 2,87 ori normalul, circa 77% din case pe o fază.
- C (`C-20250708-PT-1082`) folosește constatarea în scara de soluții (`extra.phase_rebalance_input_from` = `A-20250708-PT-1082`; treapta „faze” are încredere medie, nu mică). P90 cu dezechilibrul: 1,138 pu. Mutarea a 3 case −0,011 pu, o treaptă de priză −0,025 pu, ofertele de baterii −0,008 pu: împreună **1,095 pu, pentru 1.966 lei**. Fără mutarea caselor, combinația ieftină nu ajunge sub 1,10 (priza singură: 1,113; limita de export 4.542 lei: 1,114).
- Cinstit: nicio lucrare nu iese peste 1,10 pu doar din cauza dezechilibrului. Pe posturile din lista bilanțului care trec de limită, cauza principală e cantitatea de panouri pe o rețea slabă; mutarea caselor e o parte necesară a celei mai ieftine soluții, nu soluția singură.
- PT-1269 (propus de bilanț, 69% pe o fază): aceeași legătură, dar acolo e nevoie de faze + baterii + limită de export (12.439 lei).
- Figura pentru slide: `reports/C/figures/ladder_demo-vara_PT-1082.png`.

## `maine` cu prognoza reală de noiembrie (verificat la 16:45)
- 9 nov. (ziua de după demo: înnorat 78%, 484 W/m² pe panou): 0 posturi cu risc peste 50%, **0 lucrări pentru echipe**, 9 posturi urmărite, 2 cazuri cu prognoză nesigură la om. Rezumatul spune: „Soarele e slab (noiembrie, nori 78%): producția de la prânz rămâne sub nivelul la care tensiunea trece de 1,10 pu, deci nu trimit nicio echipă.”
- 8 nov. (azi pentru mâine: duminică senină și rece, 730 W/m², 8 °C): 7 posturi cu risc peste 50%, 0 lucrări pentru echipe, 16 mesaje și 5 urmăriri; rezumatul explică de ce (panourile reci produc aproape cât vara, duminica consumul e mic, în afara sezonului nu merită vizita).
- Schimbat pentru asta: în afara sezonului (noiembrie-februarie) mesajele pleacă doar de la 20% risc, iar urmărirea cere risc de 5% sau interval care atinge 1,10 pu; rezumatul numără lucrările pentru echipe și explică ziua slabă.

## Făcut
- M0: calcul de rețea vectorizat (Z-bus pe matricea pandapower), aceleași tensiuni ca `runpp` (diferență sub 1e-7 pu), un an de ore în sub 0,1 s; cercetarea în `docs/research/C.md`.
- M1: 480 de posturi sintetice de antrenare și 300 de posturi demo (191 pe poziții OSM), simulate orar 2023-2026; LightGBM cuantile + clasificator calibrat + model orar; evaluare pe rețele nevăzute × luni nevăzute; registrul de posturi pentru A și bilanț (`posts.load_posts()`, `data/samples/C/posts.csv`).
- M2: intervale conformale (pe grupe de rețea), calibrare izotonică, SHAP, scara de soluții (6 trepte simulate pe rețeaua postului), ofertele de baterii (`reports/C/oferte_baterii.md`).
- M3: analiza erorilor și ablații (`reports/C/error_analysis.md`), cererile de racordare (`connection.py`), raportul de investiții (`reports/C/investitii.md`), teste de robustețe (intrări greșite, rețele noi, prognoză lipsă sau nesigură).
- M4: fișa modelului cu cifrele finale, inclusiv pe topologii (`reports/C/model_card.md`), `docs/data/C.md` cu comenzile verificate, C pe o pagină (`reports/C/README.md`), reproductibilitate verificată dintr-o clonă curată.
- Două runde de review independent (Codex): 8 + 6 probleme, toate reparate, cu teste.
- Bug găsit: pandapower 3.x ignoră priza dacă `tap_changer_type` lipsește (SimBench); reparat, toate simulările refăcute.

## Urmează
- Doar reparații, dacă apar la integrare. Modelul din `models/release/C/` nu se mai schimbă.

## Blocaje
- niciunul

## Cereri către orchestrator
1. Interfață: la C, `explanation.top_factors[].contribution` e în log-odds pe P(tensiune > 1,10 pu) (`extra.factors_unit`), deci poate fi mare (de exemplu +11); cât mută fiecare grup tensiunea, în pu, e în `extra.voltage_contributions_pu`.
2. Planificator: P90 de pornire al scării e `extra.ladder_base_p90_pu` (P90 model + dezechilibrul estimat, cel mult 0,02 pu); `p90_after_pu` din opțiuni pornește de la el. Dacă bilanțul a dat dezechilibrul, `extra.phase_rebalance_input_from` are lucrarea lui și treapta „faze” are încredere medie. C citește `outputs/work_items/<scenariu>/A_bilant.jsonl` dacă există (bilanțul rulează înaintea lui C în `cyberpunks run`).
3. Modelul C are 4 versiuni în istoricul git (8,7 MB fiecare), notate pentru curățenia de la final. Regula de la 17:15 e respectată: modelul local e identic cu cel din git, deci nu mai fac commit în `models/release/`; dacă modelul s-ar schimba, o singură dată, la versiunea finală. Cel mai mare fișier C urmărit în afară de model: `data/samples/C/similar_cases.parquet` (0,35 MB).

## Cum se rulează (comenzile exacte)
- Tot lanțul: `make c-all` (circa 15-25 de minute, cel mult 4 nuclee). Pas cu pas: `make c-weather c-sim c-population c-train c-predict c-eval`; `make c-bench`; `make c-test`.
- Lucrările: `uv run python -m cyberpunks.c_prosumatori.predict --scenario demo-vara` (sau `--scenario maine --date 2026-11-09`); funcția `cyberpunks.c_prosumatori.predict.run(scenario, date) -> Path`.
- Dintr-o clonă curată, `predict` merge și fără pașii grei (model în `models/release/C/`, registru și mostre în `data/samples/C/`).
- Rapoarte: `uv run python -m cyberpunks.c_prosumatori.reports_c offers --scenario demo-vara`, `... reports_c investments`, `uv run python -m cyberpunks.c_prosumatori.error_analysis`.
- Racordări: `uv run python -m cyberpunks.c_prosumatori.connection --post PT-1020 --kwp 25`.
- Detalii: `docs/data/C.md`.

## Cifre (doar din scripturi, cu comanda)
- Rețele nevăzute × luni nevăzute, 324.000 de zile-post (`make c-eval`):
  - MAE tensiune maximă **0,0054 pu** față de **0,0227** (baseline); RMSE 0,0070 față de 0,0277.
  - Depășiri peste 1,10 pu: PR-AUC **0,951** față de 0,428; recall 86,5% față de 25,6%; precizie 86,9% față de 60,5%; Brier 0,015 față de 0,058; ECE 0,003 față de 0,013.
  - Acoperirea P10-P90: **82,1%** (ținta 80%); pe topologii 75,8-87,1%. Modelul orar: MAE 0,0049 pu, acoperire 80,4%.
  - Ablații: fără trăsăturile fizice din topologie MAE 0,0119 și PR-AUC 0,384; fără tensiunea de pornire și priză MAE 0,0205.
- Viteza (`evaluate --speed-only`): 300 de posturi pe o zi în 0,05-0,09 s față de 62-87 s cu pandapower.
- Ziua demo, 8 iulie 2025: simularea fizică dă 16 posturi peste 1,10 pu; modelul le dă probabilitate peste 50% tuturor celor 16, plus 2 aflate la 1,097 pu. 33 de lucrări C: 8 × priză, 4 × faze, 2 × limită de export, 19 mesaje; 113 oferte de baterii pe 14 posturi.
- Reproductibilitate: dintr-o clonă curată, 29 din 30 de cifre din `metrics.json` identice (ECE diferă la a cincea zecimală).

## Decizii (cu ora)
- 12:47 Simulările rulează cu cel mult 4 procese.
- 12:58 Rezoluție orară; normele cer medii pe 10 minute (aproximare scrisă în fișa modelului).
- 13:00 Etichetele vin din calculul vectorizat pe matricea pandapower, verificat față de `runpp`.
- 13:00 Producția PV din meteo românesc (Open-Meteo, calibrat pe PVGIS), nu din profilele germane SimBench.
- 13:05 Pragul de risc 1,10 pu; orele peste 1,05 pu se raportează separat.
- 13:08 Priza și tensiunea pe MT sunt legate (tensiunea fără sarcină pe JT 0,99-1,075 pu, IPOTEZĂ).
- 13:14 Limite de realism: rețelele cu creștere liniară de peste 25% la soare plin se îmblânzesc.
- 13:16 `demo-vara` = 2025-07-08 (firul B); ziua și ±3 zile sunt scoase din antrenarea modelului final.
- 13:20 LightGBM nu acceptă constrângeri monotone la cuantile: le păstrez doar la clasificator.
- 13:27 Reparat bug-ul prizei (pandapower 3.x), refăcut tot lanțul.
- 13:35 În afara sezonului PV o vizită pentru priză nu se justifică: în noiembrie agentul trimite mesaje și urmărește.
- 13:42 Modelul C intră în git (`models/release/C`) doar la milestone-uri; după 15:00 nu mai adaug versiuni.
- 14:00 Dezechilibrul pe faze se estimează analitic și se plafonează la 0,02 pu (EN 50160); P90 de pornire al scării îl include.
- 14:38 Margini conformale pe patru grupe de rețea (după sensibilitatea la PV).
- 15:08 Radiația de dimineață ca trăsătură: neadoptată (clasificarea iese mai slabă).
- 15:55 Populația se reface din registrul din git (aceleași coduri PT pentru toate firele); OSM doar la `--from-osm`.
- 16:15 Motivele lucrărilor explică scorul (SHAP pe clasificator, log-odds).
- 16:45 În afara sezonului: mesaje doar de la 20% risc; urmărire de la 5% risc sau interval care atinge 1,10 pu.
- 16:47 Scara folosește dezechilibrul găsit de bilanț (`phase_rebalance_input`) când există; treapta „faze” are atunci încredere medie.
