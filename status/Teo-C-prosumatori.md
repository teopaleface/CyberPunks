# Status: Teo-C-prosumatori
Actualizat: 2026-11-07 16:09
Milestone curent: M3 în lucru (M2 terminat la 14:11; M3 aproape gata: analiza erorilor, investiții, racordări, teste)
Gata de merge: da (commit 3bb7a48; `make check` trece; reproductibilitate verificată dintr-o clonă curată)

## Făcut
- M0 (13:10): calcul de rețea vectorizat verificat față de pandapower, prima rețea simulată, `docs/research/C.md`.
- M1 (13:45):
  - **Bug găsit și reparat:** pandapower 3.x ignoră priza transformatorului dacă `tap_changer_type` lipsește (SimBench îl lasă gol). Acum e `Ratio`, cu test. Toate simulările refăcute.
  - Populația demo: 300 de posturi (191 pe poziții reale OSM, 109 sintetice în Ilfov), 150 în București, 150 în Ilfov, simulate orar 2023-01 → 2026-11.
  - Lotul de antrenare: 480 de posturi sintetice × 33.744 de ore, 80 s pe 4 procese.
  - Model: LightGBM cuantile P10/P50/P90 ale tensiunii maxime zilnice, clasificator calibrat izotonic pentru P(> 1,10 pu), intervale lărgite conformal, model pentru kWh pierduți, model orar pentru serie. Baseline: regresie liniară pe soare × kW/kVA.
  - Evaluare pe **rețele nevăzute** (leave-one-topology-out) **și luni nevăzute** (antrenare < 2025, test 2025-2026): `reports/C/metrics.json` valid, `metrics_detail.json` pe topologii, 4 figuri în `reports/C/figures/`.
  - Lucrări valide: `demo-vara` (2025-07-08): 41 de lucrări, 18 posturi cu risc peste 50%; `maine` (2026-11-08): 33 de lucrări (duminică senină și rece: panourile reci produc aproape cât vara), doar mesaje și urmărire, motivul scris în `C_summary.json`.
  - **Backtest pe ziua demo:** simularea fizică dă 15 posturi peste 1,10 pu pe 8 iulie 2025; modelul le-a dat probabilitate peste 50% exact acestora (înainte de reparația prizei; după reparație: 18 semnalate, verific la M2).
  - Registrul posturilor pentru A și bilanț: `cyberpunks.c_prosumatori.posts.load_posts()`, `posts.build_post(post_id)` (rețeaua identică cu simularea C), mostra în git la `data/samples/C/posts.csv`.
  - Regulile de decizie: costul prizei include întreruperea (clienți × 1 h × 12 lei), preaviz de 2 zile lucrătoare (`extra.earliest_tap_date`, `planned_outage_notified: false`, `outage_notice_ro`), măsurători doar dacă valoarea în sezon acoperă 300 lei, `expected_value_lei` = exact `score × value_if_true_lei`.
  - `predict.run()` merge dintr-o clonă curată: modelul în `models/release/C/` (9 MB, comprimat), registrul și mostra pentru cazuri similare în `data/samples/C/`.
  - Teste: `tests/c/` (calcul față de pandapower, priză, decizii, intrări greșite, rețele noi, prognoză nesigură).

- 14:00 **Scara de soluții** (`remedies.py`), în `extra.remedy_options` (contractul `RemedyOption`) pentru posturile cu P90 peste 1,10 pu. Efectul fiecărei trepte vine din simularea fizică a postului în ziua țintă (24 de ore), nu e ghicit:
  - `phase_rebalance`: dezechilibrul pe faze estimat analitic pe sensibilitatea rețelei (casele ≤ 5 kWp monofazate, IPOTEZĂ), plafonat la 0,02 pu (EN 50160: dezechilibru ≤ 2%); încredere mică, fazele reale le poate confirma bilanțul;
  - `adjust_tap`: o treaptă (verificată față de rețeaua refăcută, diferență sub 5e-4 pu), cu verificarea tensiunii minime de iarnă;
  - `notify_customers`: participare 10/20/30% simulată (consum mutat din seară în orele cu risc), opriri evitate, textul de grup; P90 după soluție la participarea minimă;
  - `offer_battery`: 5/10/15 kWh pe profilul fiecărui prosumator, bateria încărcată în orele cu risc, recuperarea cu grantul Casa Verde Baterii 2026; `reports/C/oferte_baterii.md` (108 oferte pe 13 posturi pe 8 iulie 2025);
  - `export_limit`: cea mai blândă limită care aduce P90 sub limită, costul include energia neinjectată în sezon;
  - `transformer_upgrade`: post nou (transformator mai mare, rețea împărțită în două).
  - Alegerea C: cea mai ieftină combinație (până la 3 trepte, măcar una cu încredere medie sau mare) care aduce P90 sub 1,098 pu; motivul spune și de ce nu treptele mai ieftine. `recommended_action` = acțiunea principală.
  - Pe 8 iulie 2025: 7 × priză, 4 × rebalansare pe faze, 2 × limită de export, 20 de mesaje, 8 urmăriri. `predict.run` durează circa 6,5 s.

- 14:11 M2 complet:
  - modelul orar are acum interval conformal: acoperire P10-P90 80,4% pe rețele nevăzute (49,8% înainte), calibrat imbricat doar pe antrenare, MAE 0,0049 pu;
  - calibrare: ECE 0,003 (model) față de 0,013 (baseline); `reports/C/figures/reliability.png`;
  - modelul bate baseline-ul pe fiecare topologie, lună, tip de vreme și tip de rețea (`reports/C/error_tables.json`).
- 14:11 M3, mare parte:
  - `reports/C/error_analysis.md`: rețele rurale lungi (MAE 0,0063 față de 0,0045 pe cele scurte), zile noroase (recall 81,5% față de 88,5%), baterii (acoperire 77%), lângă prag (ratările au mediana 1,104 pu), ce am încercat;
  - `connection.py`: cererile de racordare -> aprobat / aprobat cu limită de injecție / studiu, cu modelul și calculul de rețea, comparat cu regula simplă de 3%; `uv run python -m cyberpunks.c_prosumatori.connection --post PT-1020 --kwp 25`;
  - `reports/C/investitii.md`: posturile de modernizat, ordonate după lei pierduți pe an, cu cea mai ieftină soluție din scară;
  - `reports/C/model_card.md` (ciornă completă), cifrele ANRE din 31 aug. 2026 în documentație și în rezumatul C;
  - teste noi: `tests/c/test_remedies.py`, `tests/c/test_connection.py`.
- 14:30 Ablații: fără trăsăturile fizice din topologie MAE 0,0119 pu (de 2,2 ori mai mare) și PR-AUC 0,384 (sub baseline); fără tensiunea de pornire și priză MAE 0,0205. Modelul are nevoie de topologia din GIS și de priza fiecărui post.
- 14:38 Interval conformal pe grupe de rețea: acoperire 82,1%, rural3 de la 73% la 80%. `reports/C/README.md`: C pe o pagină, pentru prezentare.
- 14:20-14:39 Review independent de cod (Codex): 8 probleme reale, toate reparate în 71d74ed, cu teste:
  - cascada de opriri ale invertoarelor era plafonată la 10 pe oră (subestima energia pierdută);
  - energia pierdută la oprire contabilizată consecvent cu bateria (invertor hibrid, IPOTEZĂ notată);
  - intervalul orar era calibrat și cu reziduuri din perioada de test (scurgere de informație); acum doar din antrenare;
  - o margine conformală negativă ar fi putut încrucișa cuantilele;
  - mesajele de grup: energia mutată se păstrează exact; bateriile: economia ține cont de limita de putere și de pierderi;
  - fereastra care se termină la miezul nopții.
  - 14:52 Lanțul refăcut: cifrele modelului zilnic neschimbate (tensiunea maximă nu depindea de corecturi); intervalul orar 79,7%, apoi 80,4% după runda 2; energia pierdută cu circa 10% mai mare (cascada fără plafon).
- 15:00 Figura scării de soluții pentru prezentare: `reports/C/figures/ladder_demo-vara_PT-1252.png`.
- 15:05 Clonă curată (`git clone` + `uv sync` + `predict --scenario demo-vara`): 41 de lucrări valide în circa un minut, fără pașii grei.
- 15:08 Experiment din analiza erorilor (radiația de dimineață, pentru baterii): neadoptat, clasificarea iese mai slabă; notat.
- 15:10 Cap-coadă cu agentul (`uv run cyberpunks run --scenario demo-vara`): C 41 de lucrări valide, 0 respinse; 13 decizii `R-REMEDY-LADDER` cu motivele scării; priza și rebalansarea programate mai târziu (preaviz), mesajele trimise acum.
- 15:12 Runda 2 de review Codex: 6 probleme, toate reparate în 55a6d6a, cu teste: calibrarea seriei orare devine imbricată (modelele de calibrare nu văd topologia testată), aceeași corecție de interval la evaluare și la predicție, ablația fără fizică nu mai folosește sensibilitatea la grupare, aceeași convenție de randament pentru baterii, raportul de investiții nu cade pe un rezultat gol, anul cerut schimbă chiar datele. Codex confirmă că cele 8 corecturi din runda 1 sunt corecte.
- 14:55 Rezervă pentru lipsa prognozei: ultima copie salvată, apoi clima medie a perioadei (incertitudine mare, cazurile de lângă prag la om); testat cu rețeaua tăiată.

## Urmează
- Notă pentru orchestrator: modelul C are 4 versiuni în istoricul git (8,7 MB fiecare); nu mai adaug altele decât dacă modelul se schimbă.
- M4: comenzi reproductibile verificate dintr-o clonă curată, curățenie.

## Blocaje
- niciunul

- 15:55 Clona curată a scos la iveală o dependență fragilă: populația cerea OpenStreetMap (Overpass a căzut cu 502). Acum `make c-population` refolosește registrul din git (aceleași coduri PT pentru toate firele), cu parametrii scriși la precizie completă (rețeaua se reface identic); OSM doar la `--from-osm`, cu două servere și reîncercări. În `posts.csv`, lat/lon au acum 5 zecimale (înainte 4); codurile, zonele și topologiile sunt aceleași.

- 16:00 **Reproductibilitate verificată dintr-o clonă curată**: `make c-weather c-sim c-population c-train c-predict c-eval` refac `reports/C/metrics.json`; 29 din 30 de cifre identice, ECE diferă la a cincea zecimală (LightGBM pe mai multe fire). Lucrările `demo-vara` și `maine` ies valide.

- 16:15 QA în interfață (localhost:3710, lucrarea C-20250708-PT-1252): graficul orar, motivele, cazurile similare și scara de soluții apar bine. Problemă găsită și reparată la C: contribuțiile motivelor erau în pu (0,003) și se vedeau „+0,00”. Acum sunt SHAP pe clasificator, în log-odds (de exemplu +11,45, +0,71), cum cere contractul („contribuția la scor”); motivul fizic spune cauza („de la 1,036 pu fără sarcină, panourile ridică tensiunea cu 0,073 pu la soarele zilei”).

## Cereri către orchestrator
00. Pentru interfață: la lucrările C, `explanation.top_factors[].contribution` e acum în log-odds pe P(tensiune > 1,10 pu) (`extra.factors_unit`); cât mută fiecare grup tensiunea, în pu, e în `extra.voltage_contributions_pu`. Valorile pot fi mari (de exemplu +11), deci bara ar trebui scalată la maximul lucrării.
0. Pentru planificator, despre scară: P90 de pornire al scării e `extra.ladder_base_p90_pu` = P90 al modelului (`prediction.point_interval[1]`, calcul echilibrat) + dezechilibrul estimat pe faze (cel mult 0,02 pu). `p90_after_pu` din fiecare opțiune pornește de la el; combinațiile se aproximează adunând `effect_pu`. Alegerea mea e în `extra.ladder_choice` și `extra.ladder_reason_ro`.
1. Pentru planificator (`config/economics.yaml`), chei noi pentru scara de soluții, toate IPOTEZĂ până găsim surse:
   - `voltage.notify_participation_rates: [0.10, 0.20, 0.30]`
   - `voltage.phase_rebalance_cost_lei: 350` (o echipă de 2, o oră plus deplasarea)
   - `voltage.export_limit_cost_lei: 150` (setare de la distanță sau vizită scurtă la invertor)
   - `voltage.transformer_upgrade_cost_lei: 120000` (post nou sau transformator mai mare)
   - `battery.price_lei_per_kwh_installed: 2500`, `battery.ppc_margin_share: 0.15`, `battery.cycle_value_lei_per_kwh: 0.6` (energia mutată de la prânz în seara cu deficit)
   Până atunci codul C folosește aceleași valori ca implicite, cu eticheta IPOTEZĂ.
2. Firul `Teo-bilant`: `grids.py` s-a schimbat azi (priza declarată `Ratio`, `build_realistic`, `spec_from_row`). Rețeaua unui post se obține cu `posts.build_post(post_id)`; nu reconstruiți din coloanele simple, folosiți `spec_*`.
3. Modelul C din git (`models/release/C/bundle.joblib`, 9 MB) se actualizează doar la milestone-uri, ca istoricul să nu crească.

## Cum se rulează (comenzile exacte)
- `make c-all` (tot lanțul, circa 15 minute, 4 nuclee) sau pas cu pas:
- `make c-weather`, `make c-bench`, `make c-sim`, `make c-population`, `make c-train`, `make c-predict`, `make c-eval`, `make c-test`
- `uv run python -m cyberpunks.c_prosumatori.predict --scenario demo-vara` (sau `--scenario maine --date 2026-11-09`)
- Funcția: `cyberpunks.c_prosumatori.predict.run(scenario, date) -> Path`
- Detalii: `docs/data/C.md`

## Cifre (doar din scripturi, cu comanda)
- Rețele nevăzute × luni nevăzute, 324.000 de zile-post (`make c-eval`):
  - MAE tensiune maximă: **0,0054 pu** (model) față de **0,0227 pu** (baseline); RMSE 0,0070 față de 0,0277.
  - Depășiri peste 1,10 pu: PR-AUC **0,951** față de **0,428**; recall 86,5% față de 25,6%; precizie 86,9% față de 60,5%; Brier 0,015 față de 0,058.
  - Acoperirea intervalului P10-P90: **82,1%** (ținta 80%), lățime medie 0,018 pu; margini conformale pe patru grupe de rețea (pe topologii 76-87%).
  - Eroarea de calibrare (ECE): 0,003 față de 0,013 la baseline. Modelul orar: MAE 0,0049 pu, acoperire 80,4%.
  - Ablații: fără trăsăturile fizice din topologie MAE 0,0119 și PR-AUC 0,384; fără tensiunea de pornire și priză MAE 0,0205 (`reports/C/ablation_*.json`).
  - Pe topologii, MAE model 0,0044-0,0064 pu, baseline 0,0200-0,0269.
  - Reper din literatură: BOOST-RPF (arXiv:2603.21977), aceleași 6 rețele, leave-one-grid-out, RMSE 0,0134 pu pe noduri (altă sarcină, același ordin de mărime).
- Viteza (`uv run python -m cyberpunks.c_prosumatori.evaluate --speed-only`): 300 de posturi pe o zi în 0,05-0,09 s față de 62-87 s cu pandapower (fără să ceară modelul detaliat al rețelei).
- Calcul vectorizat față de pandapower: diferență maximă 5,2e-08 pu (`make c-bench`).

## Decizii (cu ora)
- 12:47 Simulările rulează cu cel mult 4 procese.
- 12:58 Rezoluție orară; normele cer medii pe 10 minute (aproximare scrisă în model card).
- 13:00 Etichetele vin din calculul vectorizat pe matricea pandapower, verificat față de `runpp`.
- 13:00 Producția PV din meteo românesc (Open-Meteo, calibrat pe PVGIS), nu din profilele germane SimBench.
- 13:05 Pragul de risc 1,10 pu; orele peste 1,05 pu se raportează separat.
- 13:08 Priza și tensiunea pe MT sunt legate (tensiunea fără sarcină pe JT 0,99-1,075 pu, IPOTEZĂ).
- 13:14 Limite de realism: rețelele cu creștere liniară de peste 25% la soare plin se îmblânzesc.
- 13:16 `demo-vara` = 2025-07-08 (firul B); ziua și ±3 zile sunt scoase din antrenarea modelului final.
- 13:20 LightGBM nu acceptă constrângeri monotone la cuantile: le păstrez doar la clasificator.
- 13:27 Reparat bug-ul prizei (pandapower 3.x), refăcut tot lanțul.
- 13:35 În afara sezonului PV (martie-septembrie, IPOTEZĂ) o vizită pentru priză nu se justifică: în noiembrie agentul trimite mesaje și urmărește.
- 13:42 Modelul C intră în git (`models/release/C`) doar la milestone-uri.
