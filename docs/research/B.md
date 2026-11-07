# Cercetare, firul B: furtună, risc de avarii, echipe trimise din timp

Faza 0, 7 nov. 2026, 12:47-13:02. Am lucrat cu patru subagenți în paralel, apoi am verificat direct sursele critice: API-ul figshare, arhiva Open-Meteo și headerele de cost. Ce n-am putut confirma e marcat „neverificat”.

## 1. EAGLE-I (ORNL): clienți fără curent pe comitat, la 15 minute

- **Setul:** Brelsford et al., „The Environment for Analysis of Geo-Located Energy Information's Recorded Electricity Outages 2014-2025”, figshare, versiunea 4, din 25 feb. 2026: https://doi.org/10.6084/m9.figshare.24237376.v4. Licență **CC BY 4.0**.
- **Articolul:** Brelsford et al. (2024), *Scientific Data* 11:271, https://doi.org/10.1038/s41597-024-03095-5 (text complet: https://pmc.ncbi.nlm.nih.gov/articles/PMC10915145/).
- **Fișierele:** câte un CSV pe an, de 0,6-1,4 GB (2014 are doar 78 MB și calitate slabă). Plus `MCC.csv` (clienți modelați pe comitat), `DQI.csv` (indicele de calitate) și `coverage_history.csv` (acoperirea pe stat și an). Lista completă, cu mărimi și md5, e în `src/cyberpunks/b_furtuna/manifest.py`.
- **Coloane:** `fips_code, county, state, customers_out, run_start_time`. În 2023 coloana a doua se numește `sum`. Din 2024 apare în plus `total_customers`. `state` e numele întreg al statului („Ohio”). `fips_code` are zero în față.
- **Ce înseamnă un rând:** un instantaneu la 15 minute (ciclul pornește la :00, :15, :30, :45). Ora e **UTC**. Rândurile cu zero clienți afectați lipsesc, iar articolul spune că o linie lipsă poate fi zero sau gol de colectare, fără să le deosebească.
- **MCC:** `County_FIPS, Customers`. 3.234 de comitate, situația din 2022. Numitorul pentru procentul de clienți fără curent. Un comitat absent din MCC nu e monitorizat.
- **DQI:** se calculează pe regiune FEMA și an, doar pentru 2018-2022, cu formula DQI = 0,4·S + 0,3·E + 0,2·C + 0,1·P. S e rata de succes a colectării, E e ponderea parserelor active, C e acoperirea clienților, P e precizia spațială. Autorii nu dau un prag. Regiunile 3 (PA, MD, VA, WV) și 5 (IL, IN, MI, OH) au DQI 83-93 în 2020-2022. Regiunea 7 (IA, KS, MO, NE) are 50-84.
- **Acoperirea pe stat** (`coverage_history.csv`, 2022, minim-maxim din an): NY 0,98-0,99; VA 0,96-0,97; PA 0,88-0,98; IL 0,97-0,98; MI 0,95-0,96; MO 0,95; OH 0,93; KY 0,91-0,94. De evitat: KS, NE, TX, MS, TN (sub 0,8 sau cu salturi).
- **Probleme cunoscute:** goluri când o utilitate își schimbă site-ul (erori de parser, timeout în furtunile mari), valori repetate zile la rând (hărți rămase blocate), corecții manuale nemarcate, puncte puse integral într-un comitat, valori de 1-4 clienți care sunt zgomot.

### Subsetul ales (decizia 13:00)

| Ce | Alegere | De ce |
|---|---|---|
| State | OH, PA, NY, VA, MI, IL, MO, KY | Acoperire peste 0,9; climă continentală ca a României: furtuni convective vara, gheață și zăpadă iarna |
| Comitate | 80 (10 pe stat), cu 10.000-600.000 de clienți și rânduri în cel puțin 80% din zile în 2023 și 2025; eșantion stratificat pe terțile de mărime, sămânța 42 | Cota Open-Meteo ajunge pentru circa 80 de comitate pe 3 ani |
| Ani | 2023-2025, cu 7 zile din decembrie 2022 pentru întârzieri | Cei mai recenți ani, cu acoperire bună |
| Împărțire | Antrenare 2023-2024, test 2025 (an nevăzut). Generalizare spațială: pe rând, câte un stat ținut deoparte | Testul pe timp și cel pe state nevăzute, cum cere tema |
| Unitate | Comitat × zi locală. Orele UTC sunt convertite în fusul comitatului (dat de Open-Meteo, `timezone=auto`) | O furtună de seară din Ohio să nu cadă în ziua următoare |

Eșantionul e în `data/samples/B/us_counties.csv`. Comanda: `uv run python -m cyberpunks.b_furtuna.us_sample --per-state 10 --check-years 2023,2025`.

### Pragul pentru „eveniment semnificativ”

Calculat pe 2023, pe comitatele din cele 8 state cu 10.000-600.000 de clienți (zile UTC, 182.865 de zile-comitat):

| Vârful zilei (% din clienți) | Zile-comitat | Ponderea din toate zilele |
|---|---|---|
| ≥ 0,5% | 24.847 | 13,6% |
| ≥ 1% | 15.979 | 8,7% |
| ≥ 2% | 9.381 | 5,1% |
| ≥ 5% | 3.807 | 2,1% |
| ≥ 10% | 1.550 | 0,85% |

**Decizie:** evenimentul principal înseamnă că vârful zilei e de cel puțin 1% din clienți, ca în temă. Pentru o zonă din România cu 100.000 de clienți, asta înseamnă 1.000 de clienți fără curent în același timp, adică mai multe linii de medie tensiune căzute. Raportăm separat recall-ul pe evenimentele severe (≥ 5%) și extreme (≥ 10%).

## 2. Vremea istorică și prognoza: Open-Meteo

- **Arhiva** (https://archive-api.open-meteo.com/v1/archive), modelul implicit `best_match`: ERA5 (0,25°, din 1940), ERA5-Land (0,1°) și ECMWF IFS (9 km, din 2017). Docs: https://open-meteo.com/en/docs/historical-weather-api
- **Variabilele zilnice pe care le folosim**, aceleași la antrenare și în România: `weather_code, temperature_2m_max, temperature_2m_min, precipitation_sum, rain_sum, snowfall_sum, precipitation_hours, wind_speed_10m_max, wind_gusts_10m_max, shortwave_radiation_sum`. Cu `timezone=auto`, zilele sunt locale.
- **CAPE** (instabilitatea atmosferei) nu există în arhivă. Există în Historical Forecast API și în prognoză. Nu-l folosim la antrenare.
- **Mai multe locații într-o cerere:** liste separate prin virgulă la `latitude` și `longitude`, iar răspunsul e o listă. Coordonatele se aliniază la grila modelului.
- **Cota gratuită** (https://open-meteo.com/en/pricing, https://open-meteo.com/en/terms): 600 de apeluri pe minut, 5.000 pe oră, 10.000 pe zi, doar uz necomercial, pe adresă IP. Costul real vine în antetul `X-RateLimit-Cost`. Le-am măsurat:
  - arhivă, 1 locație, 1.103 zile, 10 variabile zilnice: **78,8 apeluri**;
  - arhivă, 11 locații, 3 zile, 5 variabile orare: 11;
  - prognoze trecute, 6 locații, 2 modele: 6.
  - Formula care se potrivește: max(1, variabile/10) × max(1, zile/14) × locații.
  - **Consecința:** 80 de comitate pe 3 ani costă circa 6.300 de apeluri. Le descărcăm în ritm de 3.300 pe oră, ca să rămână cotă pentru celelalte fire, iar fiecare cerere e scrisă în `data/raw/B/openmeteo/ledger.csv`.
- **Prognoze trecute** (https://historical-forecast-api.open-meteo.com/v1/forecast): ICON din 24 nov. 2022, IFS 0,25° din feb. 2024, GFS din mar. 2021. Le folosim pentru backtest-ul din România („ce știa agentul cu o zi înainte”).
- **Ensemble** (https://ensemble-api.open-meteo.com/v1/ensemble): ICON-EPS cu 40 de membri, ECMWF IFS ENS cu 51, GEFS cu 31. Are `wind_gusts_10m`. E scump: cererea de test cu 122 de serii a costat 12,2 apeluri. Îl folosim doar pentru incertitudinea scenariului `maine`, pe zonele românești.
- **Rezerve fără cotă** (neutilizate deocamdată):
  - NOAA GSOD, stații zilnice cu rafală maximă, vânt maxim, ploaie, strat de zăpadă și semnalizări de tunete și grindină, câte o arhivă de circa 104 MB pe an: https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/
  - NOAA Storm Events, cu tipul evenimentului pe comitat sau pe zonă de prognoză: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
- **De ce Open-Meteo și nu GSOD la antrenare:** aceeași sursă la antrenare și la aplicare (arhiva pentru `demo-vara`, prognoza pentru `maine`). Modelul învață relația dintre vremea dată de model și avarii, adică exact ce primește în producție. Prețul e că rafalele convective sunt subestimate în modele (vezi secțiunea 3).

## 3. Ziua reală din România: 8 iulie 2025 (scenariul `demo-vara`)

**Presa:**
- ANM a dat **cod roșu de vijelii** pentru 8 iulie 2025, între 15:00 și 21:00, cu rafale de 90-110 km/h, în 10 județe din vest și nord-vest, printre care toate cele 4 județe Rețele Electrice Banat: Timiș, Arad, Caraș-Severin, Hunedoara. În aceeași zi, cod roșu de caniculă în 15 județe și București, inclusiv Giurgiu, Ilfov, Ialomița, Călărași (maxime de 38-41 °C). Sursă: https://a1.ro/news/vremea/cod-rosu-de-vijelii-puternice-in-10-judete-din-tara-ce-zone-sunt-afectate-de-ploaia-torentiala-grindina-si-vant-dupa-canicula-id1139539.html
- Transelectrica: „rafale de vânt cu viteze cuprinse între 90 și 120 km/h”, mai mulți stâlpi avariați pe linia de 220 kV Reșița-Timișoara (comunicat din 9 iulie 2025). Sursă: https://hotnews.ro/?p=2020474
- Prefectul Timișului, pe 10 iulie: „Dintr-un total de 82 localități și un număr de aproximativ 40.000 de consumatori afectați”, din care la ora 12:00 mai rămăseseră circa 500 de consumatori în 14 localități. Același articol: „80 de echipe de tehnicieni ai Rețele Electrice România și ai contractorilor societății sunt în teren” în Timiș, Arad, Hunedoara și Caraș-Severin. Cifrele sunt cumulate pentru 7-9 iulie și vin de la prefect, nu de la distribuitor. Sursă: https://www.pressalert.ro/2025/07/stalpi-de-inalta-tensiune-doborati-de-furtunile-din-ultimele-zile-in-timis/
- În ziua de dinainte, 7 iulie, furtuna a lovit Reșița (a rupt rețeaua de tramvai) și Caransebeș (rafale de peste 80 km/h). Sursă: https://tvrinfo.ro/?p=548910

**Vremea, verificată de noi** (Open-Meteo, ora României):

| Loc | 7 iulie, rafala maximă (km/h, ora) | 8 iulie, rafala maximă | 8 iulie, ploaie | 8 iulie, radiația la 12 |
|---|---|---|---|---|
| Timișoara | 72 (16) | 50 (14) | 14,5 mm | 532 W/m² |
| Lugoj | 85 (17) | 40 (14) | 11,8 mm | 640 W/m² |
| Reșița | 75 (17) | 58 (15) | 12,5 mm | 739 W/m² |
| Caransebeș | 68 (18) | 64 (16) | 7,2 mm | 722 W/m² |
| Arad | 72 (16) | 53 (14) | 18,2 mm | 766 W/m² |
| Deva | 64 (19) | 57 (17) | 14,2 mm | 817 W/m² |
| București | 39 (21) | 34 (21) | 0 mm | 881 W/m², nori 0% |
| Constanța | 46 (15) | 41 (13) | 0 mm | 896 W/m² |

- Prognoza din 7 iulie pentru 8 iulie (Historical Forecast API) dădea rafale de 68-72 km/h la Reșița, Caransebeș și Deva (ICON), CAPE de până la 1.960 J/kg la Timișoara și 1.830 la Arad (ECMWF), plus ploi de 7-13 mm. Un agent care rula seara pe 7 iulie avea motive să trimită echipe în Banat înainte de ora 15:00.
- **Limita, spusă cinstit:** arhiva și prognozele dau rafale de 40-72 km/h, iar măsurătorile au fost de 90-120 km/h. Modelele meteo netezesc rafalele convective. Modelul nostru învață exact din vremea „netezită”, deci e consecvent, dar intensitatea locală a unei vijelii rămâne incertă.
- **București-Ilfov**, zona firelor A și C: cer senin toată ziua, 37 °C, deci soare puternic la prânz pentru prosumatori.

**Alternative respinse:**
- 30 iunie 2026, București: furtuna a venit noaptea, după 20:15. Arhiva n-o prinde (1 mm de ploaie, față de 88 l/mp măsurați la Băneasa) și nu există cifre Rețele Electrice, ci doar „cu circa 1560% peste media zilnică”.
- 26 iulie 2025, Banat: fără cifre de clienți afectați.
- 17 septembrie 2017, Timișoara: 91 de localități, dar e din toamnă și are cifre E-Distribuție vechi.

## 4. Ce spune literatura (repere cinstite)

| Lucrare | Sarcina și datele | Rezultat |
|---|---|---|
| arXiv 2510.03959 (2025), Michigan, EAGLE-I | Alertă timpurie pentru furtunile de vară, comitat × oră, cu 48 h înainte; antrenare vara 2021, test vara 2022 | Pe test, PR-AUC 0,059 la o prevalență de 0,050 și ROC-AUC 0,56. Predicția pe termen scurt din date deschise e grea |
| Proiect de pe GitHub, nerecenzat (Chumpz0/Capstone-Power-Outage-Prediction) | Regulă fără ML: rata familiei de furtună × istoricul comitatului, an de test 2024 | PR-AUC 0,469. Reper minim pentru noi |
| Arora și Ceferino (2023), NHESS, https://nhess.copernicus.org/articles/23/1665/2023/ | Avarii la uragane pe orașe, RF și GAM | RF R² = 0,48 pe test. Arborii nu extrapolează peste ce au văzut, iar modelele liniare depășesc numărul de clienți în 19,8% din orașe |
| Cerrai, Wanik, Anagnostou et al. (2019), IEEE Access (UConn OPM) | Furtuni în Connecticut, arbori plus prognoze meteo, leave-one-storm-out | Eroarea procentuală mediană scade de la 130% la 59% |
| He et al. (2017), Risk Analysis | Quantile regression forests față de BART, 89 de furtuni | QRF dă intervale mai bune. Precedent direct pentru cuantile |
| Do et al. (2023), Nature Communications, https://pmc.ncbi.nlm.nih.gov/articles/PMC10147900 | PowerOutage.us 2018-2020, comitat × zi, descriptiv | 13% din zilele-comitat au avut o avarie de cel puțin 8 h; 62% dintre ele au coincis cu un eveniment meteo |

**Ce rezultă pentru noi:**
- PR-AUC se raportează întotdeauna lângă prevalență și lângă baseline-uri: climatologia (rata istorică pe comitat și lună) și regula pe rafală.
- Extremele sunt rare și subestimate, deci folosim cuantile (P10/P50/P90) și raportăm separat recall-ul pe evenimentele de cel puțin 5% și 10%.
- Testul se face pe un an nevăzut și pe state nevăzute, ca să evităm scurgerea de informație: arXiv 2512.22699 testează pe un eveniment din perioada de antrenare.

## 5. Zona Rețele Electrice: clienți, fiabilitate, compensații

- **Clienți pe județ** (31.12.2024), din Planul de dezvoltare RER 2026-2035, tabelele 2.1-2.3 (https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf). Total 3.180.331. București 1.061.381; Ilfov 126.526; Giurgiu 318.642; Constanța 351.735; Tulcea 103.832; Călărași 129.626; Ialomița 120.907; Timiș 371.306; Arad 223.282; Caraș-Severin 149.668; Hunedoara 223.426. Pe regiuni: Muntenia 1.506.549, Banat 967.682, Dobrogea 706.100. Planul are și km de linii MT aeriene pe județ, utili mai târziu pentru vulnerabilitate.
- **Mărimea zonelor:** județele au 3.500-8.700 km², adică de 2-4 ori mai mult decât un comitat american tipic. Le împărțim în 26 de zone de circa 2.000-3.000 km², numite după orașul principal (`data/samples/B/zones_ro.yaml`). Clienții pe zonă se aproximează din populația orașului plus o parte egală din restul județului și sunt etichetați „APROXIMARE”.
- **Fiabilitate, 2024:** sursele dau cifre diferite, așa că nu le amestecăm.
  - Documentul de research aprobat de Teo (`memory/12-probleme-reale-ppc-2026.md`, neverificat): Muntenia, SAIDI neplanificat 95,14 min și SAIFI neplanificat 2,29; Banat și Dobrogea, SAIDI 79,9 min și SAIFI 2,3-2,55.
  - Economica, pe cifre ANRE: SAIDI neplanificat Banat 105 min, Dobrogea 80, Muntenia 74 (https://www.economica.net/romanii-au-stat-fara-electricitate-in-medie-aproape-patru-ore-in-2024-situatie-putin-mai-buna-fata-de-anul-precedent-care-este-situatia-pentru-fiecare-zona-din-tara_856544.html).
  - Diferența vine probabil din definiții (cu sau fără evenimentele meteo deosebite și forța majoră). Neverificat.
  - PPC, semestrul I 2026, pentru toată distribuția din România: SAIDI 35 min, SAIFI 0,90 (https://www.economica.net/ppc-si-a-prezentat-rezultatele-pentru-semstrul-i-din-2026-si-a-anuntat-ce-profit-pe-tot-anul-tinteste-si-ce-dividende-a-pregatit_965752.html/amp).
  - Din 2025 până în 2029, ANRE leagă rentabilitatea distribuitorului de un indicator compus (calitate, regenerabile, digitalizare), după documentul de research (neverificat).
  - Partea din SAIDI cauzată de vremea extremă nu e publică.
- **Termenele de restabilire și compensațiile**, din sursa primară (verificată la 13:40): Ordinul ANRE nr. 46/2021, Monitorul Oficial, Partea I, nr. 649 din 1 iulie 2021, standardul, art. 15 alin. (1) și anexa nr. 1. Text: https://www.ppcenergy.ro/wp-content/uploads/ord-46-2021.pdf
  - Întrerupere **neplanificată**, vreme normală: 4 h în municipiile reședință de județ (fără zonele lor rurale), 6 h în restul mediului urban, 12 h în mediul rural.
  - Întrerupere neplanificată, condiții meteorologice deosebite: 48 h dacă avariile sunt în zona intravilană, 72 h dacă sunt în extravilan.
  - Termenele curg din momentul în care distribuitorul a aflat de întrerupere (art. 15 alin. (2)).
  - Întrerupere **planificată**: 8 h, indiferent de zonă (anexa 1, rândul 2). Cele „8 h urban” din alte surse sunt fie termenul pentru întreruperile planificate, fie standardul vechi.
  - Compensația la depășire, pentru fiecare dintre aceste termene: 30 lei la JT, 200 lei la MT, 300 lei la 110 kV.
  - Sinteza RER, care include completarea prin Ord. ANRE 64/2022, dă aceleași termene: https://reteleelectrice.ro/wp-content/uploads/sinteza-standard-de-performanta.pdf
- **Cât plătește RER:** circa 85% din compensațiile automate plătite la nivel național, după raportul ANRE pe 2024 (preluat în `memory/12-probleme-reale-ppc-2026.md`). Sumele absolute diferă între surse, așa că folosim doar procentul.
- Compensația legală nu e un cost pe oră, deci costul pe client-oră din `config/economics.yaml` rămâne IPOTEZĂ.
- **De ce contează pentru PPC:** întreruperile și compensațiile automate (problema D1 din documentul de research) sunt pe lista problemelor neacoperite de cele 9 proiecte AI ale PPC. Furtunile sunt cauza lor cea mai vizibilă, iar termenul de 48 h pe vreme deosebită e cel pe care echipele trimise din timp îl apără.
- **Harta publică de întreruperi** RER (https://www.reteleelectrice.ro/intreruperi/) e alimentată de un serviciu ArcGIS fără autentificare, cu întreruperile active: clienți afectați, județ, coordonate, ora estimată de revenire. Nu are istoric, dar e o sursă posibilă de calibrare dacă e arhivată la 15 minute.

## 6. Designul modelului (rezultat din cercetare)

- **Tabelul:** comitat × zi locală, din EAGLE-I (vârful clienților fără curent, clienți-ore) plus vremea zilnică Open-Meteo pe centroidul comitatului.
- **Features:** rafala maximă, vântul maxim, ploaia (pe zi și pe 48 h), ploaia pe 7 zile ca aproximare a solului îmbibat, ninsoarea, temperaturile, ploaia înghețată (precipitații la temperaturi în jur de 0 °C), radiația, codul meteo, vremea din ziua precedentă, luna (frunzișul). Despre zonă, doar mărimi normalizate: logaritmul numărului de clienți și densitatea lor pe km². Fără istoricul avariilor zonei, pe care nu-l avem pentru România.
- **Ținte:** P(vârf ≥ 1% din clienți), cu probabilitatea calibrată; vârful procentual, prin cuantilele P10/P50/P90.
- **Baseline-uri:** climatologia (rata pe lună din anii de antrenare, pe comitat și global) și regula pe rafală (rafala maximă ≥ 70 km/h înseamnă eveniment).
- **Model:** LightGBM, clasificare cu calibrare izotonică pe un set separat de validare, plus regresie cuantilă. Cel mult 4 nuclee.
- **Metrici:** PR-AUC (principala, lângă prevalență), Brier, ROC-AUC, pierderea pinball pe cuantile, acoperirea intervalului P10-P90 și recall pe evenimentele severe și extreme.
