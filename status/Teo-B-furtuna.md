# Status: Teo-B-furtuna
Actualizat: 2026-11-07 18:10
Milestone curent: **B FINAL** (17:35). Modelul nu se mai schimbă; repar doar bug-uri, dacă apar.
Gata de merge: da (commit 4cee835), B FINAL (reparație de date, modelul neschimbat)

## Făcut
- 12:44 Citit memoria, tema, planul, contractele, fixture-urile. `uv sync` și `make check` trec.
- 12:47-13:00 Faza 0 cu 4 subagenți în paralel: `docs/research/B.md` (EAGLE-I, Open-Meteo, ziua din România, literatura, clienții și compensațiile RER).
- 12:54-12:59 EAGLE-I v4 (2021-2025) descărcat, md5 verificat: `cyberpunks.b_furtuna.download`.
- 12:58 **Data pentru `demo-vara`: 2025-07-08**, verificată pe vremea reală (vezi cererea 1).
- 13:00 Eșantionul: 80 de comitate din 8 state SUA (OH, PA, NY, VA, MI, IL, MO, KY), cu acoperire EAGLE-I bună (`data/samples/B/us_counties.csv`).
- 13:00 Descărcarea vremii istorice (Open-Meteo, 2023-2025) pentru cele 80 de comitate pornită în fundal, în ritm de 3.300 de apeluri pe oră, ca să rămână cotă pentru celelalte fire. Gata pe la 14:55.
- 13:10 Lanțul complet merge pe datele de până acum: tabelul comitat × zi, LightGBM calibrat cu cuantile, 3 baseline-uri, test pe 2025 și pe state nevăzute, `reports/B/metrics.json`, 26 de lucrări valide pentru `demo-vara` (`outputs/work_items/demo-vara/B.jsonl`) și seriile lor. Cifrele finale vin cu toate cele 80 de comitate.

- 13:20 Merge `Teo` (data `demo-vara` în config). Cache Open-Meteo pe disc: arhiva permanent, prognoza 3 ore; dacă rețeaua pică, agentul folosește ultima copie și o scrie în `data_quality.input_issues`. Fereastra pornește acum la începutul furtunii (planificatorul adaugă cele 60 de minute), iar `expected_value_lei` = exact `score × value_if_true_lei`.
- 13:25 Teste B (17, fără rețea): vreme lipsă, valori imposibile, zonă în afara antrenării, rafale extreme, surse meteo în dezacord, lipsa vremii orare, cache și rețea picată. Secțiunea B din `Makefile`. `docs/data/B.md`.
- 13:28 Analiza erorilor (`reports/B/error_analysis.md`), experimente (`reports/B/experiments.json`), backtest pe 6-10 iulie 2025 (`reports/B/backtest_romania.md`). Începutul furtunii se estimează după prima oră cu ploaie sau rafală foarte puternică: 15:00 la Timișoara și Reșița, 17:00 la Deva (codul roșu ANM: 15-21).
- 13:30 **Modelul e livrat în git** (`models/release/b_model.joblib`, 1,1 MB), ca planificatorul să poată apela `run()` fără să refacă datele.

- 13:35-13:54 Calibrare conformală a cuantilelor (acoperirea P10-P90 pe 2025: 82%, față de 62% fără). Evaluare cu echipe puține și în lei. Verificare pe evenimente reale cunoscute din SUA: gheața din Michigan (feb. 2023), tornadele din 31 martie 2023, Helene (sept. 2024). Al doilea caz în backtest: Slobozia, 17 iulie 2025. Figuri cu paletă validată pentru daltonism. Model card generat din metrici. Termenele ANRE verificate în sursa primară (cererea 8). Test cap-coadă cu planificatorul (cererea 11).
- 13:54 **Temperaturile și radiația au fost scoase din model.** Pe 36 de comitate, PR-AUC pe 2025 scade de la 0,258 la 0,250 (−3%). În schimb, pe 8 iulie 2025 riscul mediu e 0,31 în Banat față de 0,07 în Dobrogea și 0,04 în Muntenia (înainte: 0,34 față de 0,11), iar nicio zonă cu caniculă nu mai trece de prag. Cifra finală vine din `reports/B/experiments.json`, varianta `cu_temperaturi`.

- 16:10 **Cererile orchestratorului de la 15:50:**
  - (1) Teste de robustețe cap-coadă prin `predict.run()`, cu răspunsuri Open-Meteo sintetice (`tests/b/test_b_robustness.py`): vreme lipsă pentru o zonă (merge la om, celelalte nu sunt afectate); valori imposibile (rafală de 900 km/h, ploaie negativă: curățate, notate, la om); zonă fără istoric pe furtună (Bucureștiul, la om) și pe vreme calmă (rămâne liniștită); prognoză cu interval prea larg (jumătate din membrii ensemble liniștiți, jumătate violenți: intervalul trece de 0,35, la om). B are acum 28 de teste, iar repo-ul 263.
  - (2) `maine` pe prognoza reală (8 nov. 2026): zi liniștită, rafale de 7-27 km/h, fără ploaie; risc de 1-6% pe toate cele 26 de zone; 0 echipe recomandate. Fraza nouă: „Vreme liniștită: rafale de până la X km/h, fără ploaie. Echipele rămân la lucrările obișnuite.”
  - Schimbare de regulă găsită la (2): Bucureștiul mergea la om în fiecare zi doar pentru că e mai mare decât orice comitat din antrenare. Acum o zonă în afara antrenării merge la om doar pe vreme periculoasă (rafale ≥ 50 km/h în 2 zile, ploaie ≥ 15 mm în 48 h, zăpadă ≥ 3 cm sau polei). Vremea în afara antrenării merge la om mereu. Rezultat: `maine` are 0 zone la om (înainte 1), `demo-vara` are 0 la om și 12 echipe, toate în Banat.

- 16:35 **Al treilea caz în backtest, de iarnă: viscolul din Dobrogea, 26-27 nov. 2023.** ANM a dat cod portocaliu de viscol, cu rafale de 75-85 km/h, iar Rețele Electrice Dobrogea a raportat circa 61.000 de clienți din 99 de localități fără curent la o actualizare. Pe 26 noiembrie, riscul mediu e 0,87 în Dobrogea față de 0,09 în rest, iar toate cele 10 zone din Dobrogea primesc echipă. Scorurile din lucrări sunt plafonate la 0,99: calibrarea dădea 1,00, iar un model nu e niciodată sigur.
- 16:45 **`docs/QA-JURIU.md` (sarcina de echipă de la 16:20):** 30 de întrebări probabile ale juriului, fiecare cu un răspuns de 2-3 propoziții, cu cifra și fișierul din care vine. Acoperă datele, train/test, metodele simple, precizia@K a lui A, transferul SUA-România, intervalele, agentul, bilanțul, etica, costurile și ce trebuie confirmat cu PPC. Fișierul se încheie cu „Puncte slabe”, 9 puncte de reparat: integrarea cu S3, Spark și NiFi nedescrisă; valoarea netă a agentului pe ziua demo; cifrele care nu se potrivesc între fișierele lui A; textul „False” din `reports/bilant/demo_posts.md` etc. Cifrele celorlalte fire au fost verificate direct în fișiere.
- Planificatorul a preluat cererile 9 și 10: `storm.customers_helped_per_crew_shift: 500` și `storm.preposition_min_score: 0.15`. B folosește deja plafonul: la Timișoara, pe 8 iulie, valoarea dacă se produce avaria e 15.000 lei.

- 17:15 **Cererile de reproducere de la 17:05, rezolvate:**
  - (1) Lista comitatelor de la recensământ e în git: `data/samples/B/2024_Gaz_counties_national.zip`, 141 KB, domeniu public, md5 verificat. Nu se mai descarcă de mână.
  - (2) Vremea procesată e în git (`data/samples/B/us_weather_daily.parquet`, 0,9 MB), la fel și tabelul comitat × zi (`data/samples/B/us_county_day.parquet`, 3,1 MB). Ambele sunt derivate din EAGLE-I și Open-Meteo, cu licențele CC BY 4.0 citate.
  - **`make b-repro`** reface metricile fără descărcări și fără Open-Meteo, în circa 3 minute. Verificat: 28 din 28 de metrici identice cu `reports/B/metrics.json`. `make b-weather` și `make b-dataset` sunt acum opționale. `docs/data/B.md` are calea scurtă.
  - Regula de la 17:15 (fișiere sub 5 MB; modelul în git doar la versiunea finală): toate fișierele B sunt sub 5 MB, iar `tests/test_repo_size.py` trece. Modelul nu l-am mai urcat; în git rămâne cel de la M1.

- 17:35 **B FINAL** (decizia lui Teo de la 17:25): renunțăm la vremea pe 2021-2022. Procesul care aștepta ora 02:05 a fost oprit înainte să descarce ceva. În fișa modelului, 2021-2022 apare ca îmbunătățire viitoare, limitată de cota Open-Meteo, alături de calibrarea pe istoricul RER, evaluarea pe prognoza din ziua de dinainte și zăpadă. Fișa modelului, `docs/data/B.md` și `docs/QA-JURIU.md` au cifrele finale, verificate una câte una față de `reports/B/`. Experimentele finale includ și `zapada_uda_viscol` (0,275, nu ajută). Corectură: pe 17 iulie, Slobozia e pe locul 1 din 26, la egalitate cu Oravița (aceeași probabilitate, 0,357).
- **Modelul din git e cel final:** `models/release/b_model.joblib`, ultima schimbare în 803c29c (15:05), `b-lgbm@c5c8344`.

- 18:05 **Reparație de date (QA cap-coadă, 17:55):** seriile lucrărilor B au acum `expected`, adică riscul zilei estimat de model, cu vremea de până la acea oră (0-1, pe toate orele zilei țintă; curba nu scade). La ora 23:00, valoarea e exact scorul din lucrare: diferența e 0,0000 pe toate cele 26 de serii, în ambele scenarii. Exemplu, Timișoara pe 8 iulie: 0,11 noaptea, 0,19 la 14:00, apoi 0,36 la 15:00, când începe ploaia de furtună, și 0,43 de la 16:00. Fereastra seriei e acum ziua țintă, de la 00:00 până a doua zi la 06:00. Seriile pentru `demo-vara` și `maine` sunt regenerate și valide. Am adăugat un test. Modelul e neschimbat (ultima schimbare: 803c29c).
- 18:05 **Orele sunt corecte: ora României (+03:00 vara)**, pentru că vremea e cerută de la Open-Meteo cu fusul Europe/Bucharest. În arhivă, la Timișoara, rafala maximă e de 50 km/h la 14:00 (47 km/h la 12:00), iar ploaia de furtună începe la 15:00. Explicația pentru juriu e în `docs/QA-JURIU.md`, întrebarea 31: arhiva netezește vijeliile; furtuna reală a avut 90-120 km/h; ICON dădea 68-72 km/h la Reșița, Caransebeș și Deva; ANM avea cod roșu pentru 15:00-21:00; riscul modelului urcă exact la 15:00.

## Urmează
- Nimic planificat: **B FINAL**. Repar doar bug-uri, dacă le găsește cineva la testare. Sunt liber pentru alte sarcini ale echipei.

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Data pentru `demo-vara`: 2025-07-08 (marți).** REZOLVAT de orchestrator la 13:20 (`config/scenarios.yaml`).
   - Banat: ANM a dat cod roșu de vijelii pentru 8 iulie, 15:00-21:00, rafale 90-110 km/h, în Timiș, Arad, Caraș-Severin, Hunedoara (toate cele 4 județe Rețele Electrice Banat). Transelectrica: rafale de 90-120 km/h, stâlpi avariați pe linia de 220 kV Reșița-Timișoara. Prefectul Timișului: circa 40.000 de consumatori afectați în 82 de localități (cumulat 7-9 iulie); 80 de echipe Rețele Electrice și contractori pe teren. Surse: https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html , https://hotnews.ro/?p=2020474 , https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/
   - București-Ilfov (zona firelor A și C): cod roșu de caniculă, cer senin. Arhiva Open-Meteo: radiație de 881 W/m² la ora 12, nori 0%, maxima 37 °C în București și 36,6 °C la Buftea. Nicio furtună în București în ziua aceea.
   - Vremea verificată (arhiva Open-Meteo, ora României): în Banat, rafale de 40-64 km/h după-amiaza (14-17), ploaie de 7-18 mm. Prognoza ICON pentru 8 iulie dădea rafale de 68-72 km/h la Reșița, Caransebeș și Deva, iar ECMWF dădea CAPE de până la 1.960 J/kg la Timișoara.
2. **Echipe în Banat pentru `demo-vara`** (pentru planificator). Lucrările B din ziua asta sunt în Banat, unde `config/crews.yaml` are o singură echipă (E-TM-1). Variante: (a) adăugați 2-3 echipe simulate `mv_grid`/`lv_grid` în Banat, eventual baze simulate la Reșița, Deva, Arad; (b) păstrați lipsa de echipe ca să arătăm escaladarea: alertă la dispecerat, cerere de întărire, decizia la om. Decizia e a planificatorului.
3. **Ce trimite B, ca să știe planificatorul și interfața**: câte un WorkItem pentru fiecare dintre cele 26 de zone, în fiecare scenariu (harta de risc completă). `recommended_action` e `preposition_crew` (risc peste prag), `human_review` (abstain, cu motiv: vreme lipsă, zonă în afara datelor de antrenare, de exemplu Bucureștiul cu 1 mil. de clienți, sau surse meteo în dezacord) ori `no_action`. `prediction.score` e P(vârf ≥ 1% din clienții zonei); `interval_low`/`interval_high` vin din dezacordul modelelor meteo. `point_estimate` și `point_interval` sunt clienții la vârf **dacă** se produce avaria (P50, P10-P90). `time_window` începe cu 3 ore înainte de începutul estimat al furtunii. `impact.safety_flag` = rafale ≥ 75 km/h (lucru la înălțime periculos). `extra` are `storm_onset`, `gust_max_kmh`, `precip_48h_mm`, `zone_customers`, `decision_threshold`, `validation_note`.
4. **ID-urile zonelor B**: `B-BUCURESTI`, `IF-BUFTEA`, `GR-GIURGIU`, `GR-BOLINTIN-VALE`, `CT-CONSTANTA`, `CT-MEDGIDIA`, `CT-MANGALIA`, `TL-TULCEA`, `TL-BABADAG`, `TL-MACIN`, `CL-CALARASI`, `CL-OLTENITA`, `IL-SLOBOZIA`, `IL-URZICENI`, `TM-TIMISOARA`, `TM-LUGOJ`, `TM-SANNICOLAU-MARE`, `AR-ARAD`, `AR-INEU`, `AR-LIPOVA`, `CS-RESITA`, `CS-CARANSEBES`, `CS-ORAVITA`, `HD-DEVA`, `HD-PETROSANI`, `HD-BRAD`. Coordonatele și clienții: `data/samples/B/zones_ro.yaml`.
5. **Pentru `config/economics.yaml`, cheia `storm`** (proprietar: planificatorul), surse găsite:
   - Clienții Rețele Electrice pe județ (31.12.2024, total 3.180.331), din Planul de dezvoltare RER 2026-2035, tabelele 2.1-2.3: https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf
   - Compensații automate (Ord. ANRE 46/2021): 30 lei pe client JT, 200 lei MT, 300 lei 110 kV, la depășirea a 4 h (reședințe de județ), 6 h (urban), 12 h (rural) pe vreme normală și 48 h / 72 h pe vreme deosebită (vezi cererea 8). RER plătește circa 85% din compensațiile automate naționale (raportul ANRE pe 2024); folosim doar procentul, nu sumele absolute.
   - `cost_per_customer_hour_lei` rămâne IPOTEZĂ (compensația legală nu e pe oră).
6. **Opțional pentru interfață și planificator**: harta publică de întreruperi Rețele Electrice are un serviciu ArcGIS fără autentificare, cu întreruperile active (clienți afectați, județ, coordonate, ora estimată de revenire), actualizat la 15 minute: `https://services-eu1.arcgis.com/ZugzWQbNk6XT3BMo/arcgis/rest/services/OutagesMapViewLayer/FeatureServer/0/query?where=1%3D1&outFields=*&f=json`. Bun pentru pasul "Perceive" la scenariul `maine`.
12. **Pentru `docs/REPRODUCERE.md`** (orchestratorul): la B, calea scurtă e `make b-repro`, fără descărcări și fără Open-Meteo, circa 3 minute. Calea completă e `make b-data b-weather b-dataset b-reports b-predict`.
7. **Cota Open-Meteo e comună pentru tot laptopul** (10.000 de apeluri pe zi, 5.000 pe oră, pe IP). B folosește circa 3.300 pe oră până la 14:55, apoi foarte puțin. Dacă alt fir are nevoie de mult, să-mi spună.
8. **Răspuns la întrebarea de la 14:40, termenele de repunere: corecte sunt 4/6/12 h pe vreme normală și 48/72 h pe vreme deosebită. Cele 8/12/48 h din documentul de research sunt greșite pentru întreruperile neplanificate.** Am verificat sursa primară: Ordinul ANRE nr. 46/2021, Monitorul Oficial, Partea I, nr. 649 din 1 iulie 2021, art. 15 alin. (1) din standard (text: https://www.ppcenergy.ro/wp-content/uploads/ord-46-2021.pdf).
   - Întrerupere neplanificată, vreme normală: 4 h în municipiile reședință de județ (fără zonele rurale din componența lor), 6 h în restul mediului urban, 12 h în mediul rural.
   - Întrerupere neplanificată, condiții meteorologice deosebite: 48 h pentru avarii în intravilan, 72 h pentru avarii în extravilan.
   - Termenele curg din momentul în care distribuitorul a aflat de întrerupere (alin. (2)).
   - Întrerupere planificată: 8 h, indiferent de zonă (anexa 1, rândul 2). De aici vin, probabil, cele „8 h” din document, sau din standardul vechi, care avea 8 h urban și 18 h rural.
   - Compensații (anexa 1): 30 lei pe depășire la JT, 200 lei la MT, 300 lei la 110 kV, la fel pentru toate termenele.
   - Sinteza Rețele Electrice, care include completarea prin Ord. ANRE 64/2022, dă aceleași termene: https://reteleelectrice.ro/wp-content/uploads/sinteza-standard-de-performanta.pdf
   - Pentru planificator: `restoration_limit_hours` din `config/economics.yaml` (4/6/12/48/72) e corect; ca sursă se poate cita „Ord. ANRE 46/2021, MO 649/1.07.2021, art. 15 alin. (1)”. Ar trebui adăugat `planned: 8`, cu sursa „anexa 1, rândul 2”.
9. **Sugestie pentru `config/economics.yaml`, cheia `storm`** (planificatorul decide): valoarea unei echipe trimise din timp presupune acum că o echipă scurtează întreruperea pentru toți clienții afectați, oricât de mare e avaria. Cu ipotezele de acum, pe anul de test, „trimite mereu” iese mai bine decât orice regulă (vezi `reports/B/metrics_detail.json`, `decision_value`). Un plafon pe tură ar face valoarea realistă, de exemplu `customers_helped_per_crew_shift: <N>  # IPOTEZĂ`. Dacă cheia există, B o folosește deja în `value_if_true_lei`; dacă nu, B lasă calculul ca acum.
10. **(ACTUALIZAT 16:15) Același efect și pe `maine`, o zi liniștită de noiembrie**: CT-CONSTANTA are 5% risc, dar valoarea așteptată (5.442 lei) trece de tura de 2.700 lei, deci regula de cost a planificatorului ar trimite o echipă acolo pe vânt de 22 km/h. Cererea 9 (plafonul pe echipă, transmisă de orchestrator la 15:50) sau pragul B rezolvă cazul. (ACTUALIZAT 15:05, cu modelul final) Sugestie pentru regula de furtună a planificatorului: pe `demo-vara`, planificatorul trimite acum 3 echipe în Banat (Timișoara 43%, Arad 36%, Lugoj 36%), dar și 3 echipe la zone cu risc mic, pentru care B a recomandat `no_action`: CT-CONSTANTA (9,3%), GR-BOLINTIN-VALE (5,7%), IF-BUFTEA (5,7%). Motivul planificatorului: „Modelul a recomandat nicio acțiune; decide pragul de cost”. În ziua codului roșu din Banat, demo-ul ar arăta echipe trimise la 5,7% risc în Ilfov. Detaliile inițiale: (`rule_storm`, `config/planner.yaml`): cu valorile din config, și o zonă cu 9% risc într-o zi liniștită iese „rentabilă” (de exemplu Mangalia, pe 8 noiembrie: 9% × circa 46.000 lei, adică peste 4.000 lei, față de 2.700 lei tura), așa că agentul ar trimite echipe pe vânt de 25 km/h. Propunere: trimitem echipă doar dacă `prediction.score ≥ extra.decision_threshold` (pragul B, ales pe validare ca cel mai bun F1, acum circa 0,16) **și** valoarea netă e pozitivă. Sub prag: urmărire, plus alertă dacă scorul ≥ 0,4. Pragul e în fiecare lucrare B, la `extra.decision_threshold`, iar B îl respectă deja în `recommended_action`.

11. **Test cap-coadă pe `demo-vara` (13:49, pe ramura B, cu codul planificatorului din `Teo`): important pentru povestea demo-ului.** `uv run cyberpunks run --scenario demo-vara` merge. B dă 26 de lucrări valide, carantina 0, iar Bucureștiul merge la om.
   - Planificatorul pune singura echipă din Banat (E-TM-1) la Timișoara (40%). Deva și Ineu (57%), Reșița și Lugoj (46%) rămân „amânate, fără capacitate” și primesc doar alertă.
   - Echipele libere din București și Constanța pleacă spre GR-GIURGIU (15%), GR-BOLINTIN-VALE (15%) și CT-CONSTANTA (14%): risc din caniculă, fără furtună, dar cu valoarea așteptată peste costul turei.
   - Pe scurt: în ziua codului roșu din Banat, agentul trimite 3 din 4 echipe la caniculă în Muntenia și Dobrogea. Remediile sunt la planificator: echipe simulate în Banat (cererea 2) și pragul B (cererea 10). La B: verific pe datele complete cât din risc vine din temperaturi (experimentul `fara_temperaturi`) și, dacă pierderea e mică, scot temperaturile din model.

## Cum se rulează (comenzile exacte)
Pentru planificator: `from cyberpunks.b_furtuna.predict import run; run("demo-vara", None)` scrie `outputs/work_items/demo-vara/B.jsonl` și `outputs/series/demo-vara/B-*.json`. Folosește modelul din git și vremea Open-Meteo (cu cache: o a doua rulare în 3 ore nu mai consumă din cotă). O rulare durează 2-5 s.
```
uv run python -m cyberpunks.b_furtuna.download eaglei --years 2023-2025   # EAGLE-I, cu md5
uv run python -m cyberpunks.b_furtuna.eaglei hourly --years 2023-2025     # comitat × oră
uv run python -m cyberpunks.b_furtuna.us_sample --per-state 10            # eșantionul (deja în git)
uv run python -m cyberpunks.b_furtuna.openmeteo us-history                # vremea, ~6.300 de apeluri Open-Meteo
uv run python -m cyberpunks.b_furtuna.dataset                             # tabelul comitat × zi
uv run python -m cyberpunks.b_furtuna.evaluate                            # antrenare, test, reports/B/metrics.json
uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara        # outputs/work_items/demo-vara/B.jsonl
uv run python -m cyberpunks.b_furtuna.predict --scenario maine
```
Din Python: `from cyberpunks.b_furtuna.predict import run; run("demo-vara", None)`.

## Cifre (doar din scripturi, cu comanda)
FINALE M1, model `b-lgbm@c5c8344` (`models/release/b_model.joblib`). Comanda: `make b-reports` sau `uv run python -m cyberpunks.b_furtuna.evaluate`.
- Date: 80 de comitate din 8 state SUA. Antrenare pe 2023-2024: 58.480 de zile-comitat, 5.595 de evenimente. Test pe 2025, an nevăzut: 29.200 de zile-comitat, 3.014 evenimente (prevalență 10,3%).
- **PR-AUC (metrica principală): model 0,278**, față de regula pe rafală 0,182, climatologia pe comitat și lună 0,151 și climatologia pe lună 0,120.
- ROC-AUC: model 0,725, față de 0,612 (climatologia pe comitat și lună) și 0,611 (rafală).
- Brier: model 0,0841, față de 0,0914 (climatologia pe comitat și lună), 0,0924 (climatologia pe lună) și 0,0890 (rafală).
- La pragul de 0,16 (ales pe OOF): precizie 28%, recall 41%. Recall pe evenimentele severe (≥ 5%): 50%, față de 40% pentru climatologie; pe cele extreme (≥ 10%): 54%, față de 42%.
- **State nevăzute** (leave-one-state-out, 8 state, anul 2025): PR-AUC mediu 0,259, față de climatologie 0,122 și rafală 0,188. **Modelul bate ambele metode simple în 8 din 8 state.**
- **Cuantile:** P10-P90 acoperă 80,8% din vârfurile reale în 2025 (ținta 80%; fără calibrarea conformală, 72,2%). Pinball mediu (scara log): 0,151.
- Echipe puține (8 pe zi pentru 80 de zone, în zonele cu scorul cel mai mare): acoperă 16,7% din clienții afectați, față de 14,6% (rafală), 12,3% (climatologie), 7,6% (la întâmplare) și 88,6% (oracol).
- Experimente (`reports/B/experiments.json`):
  - cu temperaturi: 0,283; fără mărimea zonei: 0,234; fără constrângeri monotone: 0,274; fără vremea din zilele precedente: 0,273;
  - clima locală 0,276, coada rafalei 0,276, ploaie extra 0,275: nu ajută;
  - prag de 2%: 0,197 (prevalență 6,0%); prag de 5%: 0,100 (prevalență 2,2%).
- Analiza erorilor (`reports/B/error_analysis.md`):
  - 61% din evenimente apar în zile fără semnal meteo puternic.
  - Pe zile cu vânt ≥ 60 km/h: PR-AUC 0,45, recall 73%. Pe ploaie abundentă: 0,39, recall 81%. Pe polei: 0,31. Pe zăpadă: 0,12, recall 12% (punctul slab).
  - Din 121 de evenimente extreme ratate, 85% au rafale sub 60 km/h în arhivă.
- Backtest România (`uv run python -m cyberpunks.b_furtuna.backtest`):
  - 7-8 iulie 2025: riscul mediu e 0,31 în Banat, față de 0,07 în Muntenia și Dobrogea. 22 de zone-zi cu echipă recomandată în Banat, 0 în rest.
  - 17 iulie 2025 (Slobozia, cod roșu): IL-SLOBOZIA e pe locul 1 din 26 de zone (P = 0,36), cu începutul furtunii estimat la 20:00.
- Lucrări: `demo-vara` (8 iulie 2025): 12 echipe recomandate, toate în Banat, iar Bucureștiul la om. `maine` (8 nov. 2026): 0 echipe, Bucureștiul la om (în afara datelor de antrenare).

## Decizii (cu ora)
- 12:50 Folosim EAGLE-I v4 de pe figshare (2014-2025), nu doar 2014-2022.
- 12:56 Vremea pentru antrenare: arhiva Open-Meteo pe centroizii comitatelor, agregate zilnice locale. Aceeași sursă ca la aplicarea în România (arhiva pentru `demo-vara`, prognoza pentru `maine`). Cota e mică, deci luăm un eșantion de 80 de comitate și descărcăm în ritm lent.
- 12:58 `demo-vara` = 2025-07-08. A doua variantă, 2026-06-30 (furtuna din București), a picat: furtuna a venit noaptea, după 20:15, arhiva n-o prinde (1 mm de ploaie față de 88 l/mp măsurați la Băneasa) și nu există cifre Rețele Electrice.
- 13:00 Antrenare 2023-2024, test 2025 (an nevăzut), plus leave-one-state-out (zone fără istoric, ca în România).
- 13:03 Evenimentul = vârful zilei ≥ 1% din clienții zonei. Recall-ul se raportează separat pentru ≥ 5% și ≥ 10%.
- 13:05 Codul meteo nu intră în model: arhiva nu are niciodată coduri de furtună (95-99), prognoza le are.
- 13:06 Model în doi pași: P(eveniment) calibrat (izotonic, cu fold-uri pe săptămâni) și cuantilele vârfului doar în zilele cu eveniment („dacă se întâmplă, cât de mare”). Valoarea = P × clienți P50 × 2,5 h × 12 lei (`economics.yaml`, `storm`).
- 13:08 Județele mari sunt împărțite în 26 de zone de mărimea unui comitat american. Clienții pe zonă sunt o aproximare, etichetată ca atare în fiecare lucrare. Cifrele RER pe județ au o anomalie (Giurgiu are 1,22 clienți pe locuitor, Ilfov 0,23): le folosim ca atare și o semnalăm.
- 13:21 Pragul rămâne 1%: la 2% și 5%, ponderea evenimentelor cu semnal meteo clar nu crește (38-41%), iar lift-ul față de prevalență urcă puțin, de la 2,5x la 3x, deci nu merită o țintă mai greu de explicat.
- 13:22 Cache Open-Meteo, ca rulările repetate ale planificatorului și ale interfeței să nu consume cota comună, iar demo-ul să meargă și fără internet.
- 13:26 Modelul livrat în `models/release/` (permis în git), comprimat.
- 13:27 În explicații, factorul „sezon” apare doar când crește riscul, iar fraza pornește de la factorii cu cea mai mare contribuție SHAP. Pe 8 iulie, în Ialomița și Călărași riscul vine din caniculă (38 °C, minima de 22 °C), nu din vânt. Lăsăm așa: în datele din SUA, zilele foarte calde chiar aduc avarii (suprasarcină, furtuni de după-amiază). Explicația spune deschis ce a contat.
- 15:00 Hiperparametrii au fost aleși doar pe anii de antrenare (`reports/B/tuning.json`, 24 de configurații): 31 de frunze, minimum 100 de cazuri pe frunză, rata 0,02, 300 de runde (PR-AUC OOF 0,292). Cu 600 de runde ieșea mai prost, din cauza supraînvățării.
- 15:05 Decizia de a scoate temperaturile e confirmată pe datele complete: costă 1,9% din PR-AUC (0,283 față de 0,278), dar riscul urmărește furtuna. Zilele asemănătoare se caută acum după aceleași pericole ca modelul.
- 15:08 Repararea unui test picat (`make check` trecea prin `tail`, deci commitul 803c29c a intrat cu un test picat; reparat în d3aa9ea). Acum `make check` trece: 222 de teste.
