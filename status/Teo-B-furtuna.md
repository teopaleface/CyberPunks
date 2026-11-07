# Status: Teo-B-furtuna
Actualizat: 2026-11-07 13:13
Milestone curent: M0 gata, lucrez la M1
Gata de merge: nu (M1 vine când se termină descărcarea vremii, estimat 15:00)

## Făcut
- 12:44 Citit memoria, tema, planul, contractele, fixture-urile. `uv sync` și `make check` trec.
- 12:47-13:00 Faza 0 cu 4 subagenți în paralel: `docs/research/B.md` (EAGLE-I, Open-Meteo, ziua din România, literatura, clienții și compensațiile RER).
- 12:54-12:59 EAGLE-I v4 (2021-2025) descărcat, md5 verificat: `cyberpunks.b_furtuna.download`.
- 12:58 **Data pentru `demo-vara`: 2025-07-08**, verificată pe vremea reală (vezi cererea 1).
- 13:00 Eșantionul: 80 de comitate din 8 state SUA (OH, PA, NY, VA, MI, IL, MO, KY), cu acoperire EAGLE-I bună (`data/samples/B/us_counties.csv`).
- 13:00 Descărcarea vremii istorice (Open-Meteo, 2023-2025) pentru cele 80 de comitate pornită în fundal, în ritm de 3.300 de apeluri pe oră, ca să rămână cotă pentru celelalte fire. Gata pe la 14:55.
- 13:10 Lanțul complet merge pe datele de până acum: tabelul comitat × zi, LightGBM calibrat cu cuantile, 3 baseline-uri, test pe 2025 și pe state nevăzute, `reports/B/metrics.json`, 26 de lucrări valide pentru `demo-vara` (`outputs/work_items/demo-vara/B.jsonl`) și seriile lor. Cifrele finale vin cu toate cele 80 de comitate.

## Urmează
- 15:00 Antrenarea pe toate cele 80 de comitate, cifrele M1, `B.jsonl` pentru `demo-vara` și `maine`, merge `Teo`, „Gata de merge”.
- Până atunci: secțiunea B din `Makefile`, teste în `tests/b/`, `docs/data/B.md`.
- M2 (21:30): modelul bate baseline-urile pe test separat, cuantile calibrate, SHAP în lucrări (există deja), backtest-ul pe 8 iulie 2025.

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Data pentru `demo-vara`: 2025-07-08 (marți).** Vă rog `config/scenarios.yaml`: `date: "2025-07-08"`. Până atunci, B folosește data asta implicit.
   - Banat: ANM a dat cod roșu de vijelii pentru 8 iulie, 15:00-21:00, rafale 90-110 km/h, în Timiș, Arad, Caraș-Severin, Hunedoara (toate cele 4 județe Rețele Electrice Banat). Transelectrica: rafale de 90-120 km/h, stâlpi avariați pe linia de 220 kV Reșița-Timișoara. Prefectul Timișului: circa 40.000 de consumatori afectați în 82 de localități (cumulat 7-9 iulie); 80 de echipe Rețele Electrice și contractori pe teren. Surse: https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html , https://hotnews.ro/?p=2020474 , https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/
   - București-Ilfov (zona firelor A și C): cod roșu de caniculă, cer senin. Arhiva Open-Meteo: radiație de 881 W/m² la ora 12, nori 0%, maxima 37 °C în București și 36,6 °C la Buftea. Nicio furtună în București în ziua aceea.
   - Vremea verificată (arhiva Open-Meteo, ora României): în Banat, rafale de 40-64 km/h după-amiaza (14-17), ploaie de 7-18 mm. Prognoza ICON pentru 8 iulie dădea rafale de 68-72 km/h la Reșița, Caransebeș și Deva, iar ECMWF dădea CAPE de până la 1.960 J/kg la Timișoara.
2. **Echipe în Banat pentru `demo-vara`** (pentru planificator). Lucrările B din ziua asta sunt în Banat, unde `config/crews.yaml` are o singură echipă (E-TM-1). Variante: (a) adăugați 2-3 echipe simulate `mv_grid`/`lv_grid` în Banat, eventual baze simulate la Reșița, Deva, Arad; (b) păstrați lipsa de echipe ca să arătăm escaladarea: alertă la dispecerat, cerere de întărire, decizia la om. Decizia e a planificatorului.
3. **Ce trimite B, ca să știe planificatorul și interfața**: câte un WorkItem pentru fiecare dintre cele 26 de zone, în fiecare scenariu (harta de risc completă). `recommended_action` e `preposition_crew` (risc peste prag), `human_review` (abstain, cu motiv: vreme lipsă, zonă în afara datelor de antrenare, de exemplu Bucureștiul cu 1 mil. de clienți, sau surse meteo în dezacord) ori `no_action`. `prediction.score` e P(vârf ≥ 1% din clienții zonei); `interval_low`/`interval_high` vin din dezacordul modelelor meteo. `point_estimate` și `point_interval` sunt clienții la vârf **dacă** se produce avaria (P50, P10-P90). `time_window` începe cu 3 ore înainte de începutul estimat al furtunii. `impact.safety_flag` = rafale ≥ 75 km/h (lucru la înălțime periculos). `extra` are `storm_onset`, `gust_max_kmh`, `precip_48h_mm`, `zone_customers`, `decision_threshold`, `validation_note`.
4. **ID-urile zonelor B**: `B-BUCURESTI`, `IF-BUFTEA`, `GR-GIURGIU`, `GR-BOLINTIN-VALE`, `CT-CONSTANTA`, `CT-MEDGIDIA`, `CT-MANGALIA`, `TL-TULCEA`, `TL-BABADAG`, `TL-MACIN`, `CL-CALARASI`, `CL-OLTENITA`, `IL-SLOBOZIA`, `IL-URZICENI`, `TM-TIMISOARA`, `TM-LUGOJ`, `TM-SANNICOLAU-MARE`, `AR-ARAD`, `AR-INEU`, `AR-LIPOVA`, `CS-RESITA`, `CS-CARANSEBES`, `CS-ORAVITA`, `HD-DEVA`, `HD-PETROSANI`, `HD-BRAD`. Coordonatele și clienții: `data/samples/B/zones_ro.yaml`.
5. **Pentru `config/economics.yaml`, cheia `storm`** (proprietar: planificatorul), surse găsite:
   - Clienții Rețele Electrice pe județ (31.12.2024, total 3.180.331), din Planul de dezvoltare RER 2026-2035, tabelele 2.1-2.3: https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf
   - Compensații automate (Ord. ANRE 46/2021): 30 lei pe client JT, 200 lei MT, 300 lei 110 kV, la depășirea a 4 h (reședințe de județ), 6 h (urban), 12 h (rural) pe vreme normală și 48 h / 72 h pe vreme deosebită: https://reteleelectrice.ro/wp-content/uploads/sinteza-standard-de-performanta.pdf . În 2024, RER a plătit circa 23 mil. lei compensații (https://www.forbes.ro/?p=458099).
   - `cost_per_customer_hour_lei` rămâne IPOTEZĂ (compensația legală nu e pe oră).
6. **Opțional pentru interfață și planificator**: harta publică de întreruperi Rețele Electrice are un serviciu ArcGIS fără autentificare, cu întreruperile active (clienți afectați, județ, coordonate, ora estimată de revenire), actualizat la 15 minute: `https://services-eu1.arcgis.com/ZugzWQbNk6XT3BMo/arcgis/rest/services/OutagesMapViewLayer/FeatureServer/0/query?where=1%3D1&outFields=*&f=json`. Bun pentru pasul "Perceive" la scenariul `maine`.
7. **Cota Open-Meteo e comună pentru tot laptopul** (10.000 de apeluri pe zi, 5.000 pe oră, pe IP). B folosește circa 3.300 pe oră până la 14:55, apoi foarte puțin. Dacă alt fir are nevoie de mult, să-mi spună.

## Cum se rulează (comenzile exacte)
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
- Prevalența evenimentului (vârf ≥ 1% din clienți), 2023, comitatele cu 10.000-600.000 de clienți din cele 8 state: 8,7% din zilele-comitat; ≥ 5%: 2,1%; ≥ 10%: 0,85%. (calcul ad-hoc din `eaglei.py`, de mutat într-un script la M1)
- Metricile modelului: vin la M1 (acum sunt pe doar 9 comitate și nu au valoare).

## Decizii (cu ora)
- 12:50 Folosim EAGLE-I v4 de pe figshare (2014-2025), nu doar 2014-2022.
- 12:56 Vremea pentru antrenare: arhiva Open-Meteo pe centroizii comitatelor, agregate zilnice locale. Aceeași sursă ca la aplicarea în România (arhiva pentru `demo-vara`, prognoza pentru `maine`). Cota e mică, deci luăm un eșantion de 80 de comitate și descărcăm în ritm lent.
- 12:58 `demo-vara` = 2025-07-08. A doua variantă, 2026-06-30 (furtuna din București), a picat: furtuna a venit noaptea, după 20:15, arhiva n-o prinde (1 mm de ploaie față de 88 l/mp măsurați la Băneasa) și nu există cifre Rețele Electrice.
- 13:00 Antrenare 2023-2024, test 2025 (an nevăzut), plus leave-one-state-out (zone fără istoric, ca în România).
- 13:03 Evenimentul = vârful zilei ≥ 1% din clienții zonei. Recall-ul se raportează separat pentru ≥ 5% și ≥ 10%.
- 13:05 Codul meteo nu intră în model: arhiva nu are niciodată coduri de furtună (95-99), prognoza le are.
- 13:06 Model în doi pași: P(eveniment) calibrat (izotonic, cu fold-uri pe săptămâni) și cuantilele vârfului doar în zilele cu eveniment („dacă se întâmplă, cât de mare”). Valoarea = P × clienți P50 × 2,5 h × 12 lei (`economics.yaml`, `storm`).
- 13:08 Județele mari sunt împărțite în 26 de zone de mărimea unui comitat american. Clienții pe zonă sunt o aproximare, etichetată ca atare în fiecare lucrare. Cifrele RER pe județ au o anomalie (Giurgiu are 1,22 clienți pe locuitor, Ilfov 0,23): le folosim ca atare și o semnalăm.
