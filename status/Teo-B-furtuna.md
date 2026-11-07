# Status: Teo-B-furtuna
Actualizat: 2026-11-07 13:20
Milestone curent: M0
Gata de merge: nu

## Făcut
- 12:44 Citit `memory/INDEX.md`, `07-tema-ppc.md`, `08-ppc-workshop-ai.md`, `docs/PLAN.md`, `docs/CONTRACTS.md`, `contracts.py`, fixture-urile.
- 12:46 `uv sync` și `make check` trec (7 teste).
- 12:47-13:05 Faza 0: 4 subagenți în paralel (zi reală de furtună în România; literatură și surse meteo; EAGLE-I; clienți și fiabilitate Rețele Electrice). Toți au terminat.
- 12:50 EAGLE-I verificat prin API-ul figshare: versiunea 4 (25 feb. 2026) acoperă 2014-2025, CC BY 4.0, 1,1-1,4 GB pe an.
- 13:00 Scriptul de descărcare cu sume de control (`cyberpunks.b_furtuna.download`); descărcarea EAGLE-I 2021-2025 rulează în fundal.
- 13:15 Data pentru `demo-vara` aleasă și verificată pe vremea reală (mai jos).

## Urmează
- `docs/research/B.md` (până la 14:30).
- Vremea istorică Open-Meteo pentru comitatele din SUA alese (în ritm lent, ca să lăsăm cotă și celorlalte fire).
- M1 (17:30): tabelul comitat × zi, baseline-uri, primul LightGBM, `metrics.json`, `B.jsonl` pentru `demo-vara` și `maine`.

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Data pentru `demo-vara`: 2025-07-08 (marți).** Vă rog `config/scenarios.yaml`: `date: "2025-07-08"`.
   - Banat: ANM a dat cod roșu de vijelii pentru 8 iulie, 15:00-21:00, rafale 90-110 km/h, în Timiș, Arad, Caraș-Severin, Hunedoara (toate cele 4 județe Rețele Electrice Banat). Transelectrica: rafale de 90-120 km/h, stâlpi avariați pe linia de 220 kV Reșița-Timișoara. Prefectul Timișului: circa 40.000 de consumatori afectați în 82 de localități (cumulat 7-9 iulie); 80 de echipe Rețele Electrice și contractori pe teren. Surse: https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html , https://hotnews.ro/?p=2020474 , https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/
   - București-Ilfov (zona firelor A și C): cod roșu de caniculă, cer senin toată ziua. Arhiva Open-Meteo: radiație 881 W/m² la ora 12, nori 0%, maxima 37 °C în București și 36,6 °C la Buftea. Nicio furtună în București în ziua aceea.
   - Vremea verificată (arhiva Open-Meteo, ora României): în Banat, rafale de 40-64 km/h după-amiaza (14-17), ploaie de 7-18 mm. Prognoza din 7 iulie pentru 8 iulie (ICON) dădea rafale de 68-72 km/h la Reșița, Caransebeș și Deva, iar ECMWF dădea CAPE de până la 1.960 J/kg la Timișoara.
2. **Echipe în Banat pentru `demo-vara`** (pentru firul planificator). Lucrările B din ziua asta vor fi în Banat, unde `config/crews.yaml` are o singură echipă (E-TM-1). Variante: (a) adăugați 2-3 echipe simulate `mv_grid`/`lv_grid` în Banat, eventual baze simulate la Reșița, Deva, Arad; (b) păstrați lipsa de echipe ca să arătăm escaladarea: alertă la dispecerat, cerere de întărire, decizia la om. Decizia e a planificatorului.
3. **Zonele B**: județele mari sunt împărțite în zone de mărimea unui comitat american (2.000-3.000 km²), cu ID-uri de forma `TM-LUGOJ`, `CS-RESITA`, `B-BUCURESTI`. Lista cu coordonate și clienți vine în `data/samples/B/zones_ro.yaml` (la M1).
4. **Pentru `config/economics.yaml`, cheia `storm`** (proprietar: planificatorul), surse găsite:
   - Clienții Rețele Electrice pe județ (31.12.2024, total 3.180.331), din Planul de dezvoltare RER 2026-2035, tabelele 2.1-2.3: https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf
   - Compensații automate (Ord. ANRE 46/2021): 30 lei pe client JT, 200 lei MT, 300 lei 110 kV, la depășirea a 4 h (reședințe de județ), 6 h (urban), 12 h (rural) pe vreme normală și 48 h / 72 h pe vreme deosebită: https://reteleelectrice.ro/wp-content/uploads/sinteza-standard-de-performanta.pdf . În 2024, RER a plătit circa 23 mil. lei compensații (https://www.forbes.ro/?p=458099).
   - `cost_per_customer_hour_lei` rămâne IPOTEZĂ (compensația legală nu e pe oră).
5. **Opțional pentru interfață și planificator**: harta publică de întreruperi Rețele Electrice are un serviciu ArcGIS fără autentificare, cu întreruperile active (clienți afectați, județ, coordonate, ora estimată de revenire), actualizat la 15 minute: `https://services-eu1.arcgis.com/ZugzWQbNk6XT3BMo/arcgis/rest/services/OutagesMapViewLayer/FeatureServer/0/query?where=1%3D1&outFields=*&f=json`. Bun pentru pasul "Perceive" la scenariul `maine`.

## Cum se rulează (comenzile exacte)
- `uv run python -m cyberpunks.b_furtuna.download eaglei --years 2021-2025` (descarcă și verifică md5)

## Cifre (doar din scripturi, cu comanda)
- (vine la M1)

## Decizii (cu ora)
- 12:50 Folosim EAGLE-I v4 de pe figshare (2014-2025), nu doar 2014-2022.
- 13:10 Vremea pentru antrenare: arhiva Open-Meteo pe centroizii comitatelor, agregate zilnice locale. Aceeași sursă ca la aplicarea în România (arhiva pentru `demo-vara`, prognoza pentru `maine`). Cota e mică (10.000 de apeluri pe zi și 5.000 pe oră de pe IP, partajate cu tot laptopul; un comitat-an costă 26 de apeluri), deci luăm un eșantion de comitate și descărcăm în ritm lent.
- 13:15 `demo-vara` = 2025-07-08. A doua variantă, 2026-06-30 (furtuna din București), a picat: furtuna a venit noaptea, după 20:15, arhiva meteo n-o prinde (1 mm de ploaie față de 88 l/mp măsurați la Băneasa) și nu există cifre Rețele Electrice.
