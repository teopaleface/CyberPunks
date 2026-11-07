# Cercetare C: prosumatori și tensiune prea mare în posturile de transformare

Faza 0, 7 nov. 2026, 12:45-13:30. Trei cercetări în paralel (date publice, norme și cifre românești, literatură ML), plus măsurători proprii pe SimBench. Fiecare cifră are sursa lângă ea. Ce nu are sursă e marcat **IPOTEZĂ**.

## 1. Problema, cu cifrele publice

- **359.378 de prosumatori** la 30 iunie 2026 (324.535 persoane fizice, 34.843 juridice), **4.019 MW** instalați (2.067 MW persoane fizice, 1.952 MW juridice), **127.084 cu baterii**. Sursa: ANRE prin News.ro, în https://startupcafe.ro/romani-panouri-solare-cati-prosumatori-racordare-retelele-electrice-romania-105065 (13 aug. 2026). Documentul ANRE primar nu l-am găsit.
  - Corectură față de plan: planul spunea „circa 3.800 MW” și „peste 101.000 cu baterii”. Cifrele de mai sus sunt mai noi.
  - Medii calculate din aceste cifre: 6,4 kW pe prosumator persoană fizică, 56 kW pe persoană juridică.
- Creștere: 44.000 (ian. 2023), 107.001 (nov. 2023), 198.756 (sfârșit 2024), 359.378 (iun. 2026). Surse: https://hotnews.ro/?p=15210, https://www.economica.net/?p=812499.
- **Ilfov e pe primul loc**: 13.405 prosumatori și 183 MW la sfârșitul lui 2024. Sursa: https://www.economica.net/?p=812499. Pentru București n-am găsit cifra.
- Rețele Electrice: circa 136.000 km de rețea și peste 26.000 de posturi de transformare; licitație de circa 45 mil. lei pentru un GIS nou. Sursa: https://www.energynomics.ro/en/retele-electrice-romania-launches-a-tender-of-approximately-45-million-lei-for-digitalization.
- Invertoarele se opresc la 253 V (1,10 Un), „de mai multe ori pe zi”, spun prosumatorii; ANRE avertizează că unii ridică ilegal pragurile (amendă 2.000-4.000 lei). Sursa: https://economedia.ro/?p=263330 (30 mai 2025).
- Tensiunea poate urca de la 230 V la 260-270 V la injecție mare. Sursa: https://hotnews.ro/?p=15210 (26 feb. 2024). Același articol spune că reglarea ploturilor transformatorului e azi „singura soluție” folosită.
- Peste 30.000 de prosumatori (10%) ar fi deconectați la prânz. Sursă slabă (articol sponsorizat): https://startupcafe.ro/peste-300-000-de-prosumatori-in-romania-de-ce-modelul-actual-trebuie-sa-evolueze-pentru-a-si-depasi-vulnerabilitatile-98006.
- Distribuție Oltenia a verificat 460 de invertoare; circa 60% nu aveau protecțiile setate corect. Sursa: https://playtech.ro/2025/conflict-intre-prosumatori-si-distribuitori-cine-controleaza-productia-de-energie-solara-in-romania/.
- Știrile PRO TV: titlul „Zeci de mii de panouri fotovoltaice din România sunt deconectate automat în orele de vârf” (https://stirileprotv.ro/stiri-despre/retea-electrica/; articolul nu l-am citit).

## 2. Norme: limita de tensiune și ce se întâmplă la depășire

| Regula | Valoare | Sursa |
|---|---|---|
| EN 50160, JT | 95% din mediile pe 10 min dintr-o săptămână în ±10% Un; toate în +10% / −15% | SR EN 50160, citată în Ord. ANRE 46/2021, art. 25(1) |
| **România, de la 1.01.2022, JT** | **95% din mediile pe 10 min între +5% și −10% Un**; 100% în +10% / −15% | Ord. ANRE 46/2021, art. 25(2), https://www.ppcenergy.ro/wp-content/uploads/ord-46-2021.pdf |
| Supratensiune (definiție) | peste 110% din tensiunea de referință | Ord. ANRE 46/2021, art. 1 |
| Invertor, protecție pe medie de 10 min | 1,10 Un | Tabelul 2P, Ord. ANRE 132/2020 (copie în condițiile tehnice DEER: https://www.distributie-energie.ro/wp-content/uploads/2022/05/CONDITII-TEHNICE-GENERATOARE-Versiune8.pdf) |
| Invertor, treapta rapidă U> | 1,15 Un, 0,5 s | același tabel |
| Reclamație despre calitatea tensiunii | răspuns în 20 de zile; monitorizare minimum 7 zile; costul îl suportă operatorul | Ord. ANRE 46/2021, art. 28 |
| Compensație la reclamație întemeiată sau termen depășit | 70 lei persoană fizică, 130 lei persoană juridică (JT) | Ord. ANRE 46/2021, anexa 4, rândurile 9 și 16 |

Ce folosim în cod:
- Pragul de risc: **1,10 pu** (deconectarea invertoarelor și limita de 100% din standard). Este și cheia `voltage.overvoltage_limit_pu` din `config/economics.yaml`.
- Raportăm separat orele peste **1,05 pu**: în România, mai mult de 5% din timp peste 1,05 pu înseamnă calitate a tensiunii sub standard.
- Simularea e orară (meteo orar). Normele vorbesc de medii pe 10 minute; ora e o aproximare, scrisă în model card.
- Q(U) sau P(U) la invertoare: n-am găsit nicio normă românească care să le ceară. Nici limitarea injecției în avizul de racordare (ATR) n-am găsit-o scrisă. Legea 160/2026 (în vigoare din 26 iulie 2026) a schimbat regulile pentru prosumatori; ANRE are în dezbatere un ordin nou de racordare.

## 3. Ce poate face distribuitorul (acțiunile din `recommended_action`)

| Acțiune | Ce face | Cost și timp | Sursa |
|---|---|---|---|
| `adjust_tap` | Comutatorul transformatorului MT/JT se mută cu o treaptă (2,5%) în jos. Comutatorul e fără sarcină, deci postul se scoate de sub tensiune: întrerupere planificată scurtă. | Plaja tipică ±2×2,5%. Costul vizitei: 450 lei, **IPOTEZĂ** (`config/economics.yaml`) | Practica: hotnews.ro/?p=15210; tehnic: https://eepower.com/technical-articles/distribution-transformers-and-voltage-regulationpart-4-on-and-off-load-tap-changers/ |
| `measurement_campaign` | Analizor de calitate a energiei montat la post, minimum 7 zile | 300 lei, **IPOTEZĂ** | Ord. ANRE 46/2021, art. 28(3) |
| `notify_customers` | Mesaj PPC Energy către prosumatorii postului: consumul mutat la prânz | fără echipă | Oferta PPC Ore Smart+ (mai jos) |
| `watchlist` | Postul rămâne urmărit, fără vizită | zero | — |
| Investiție (raport separat) | transformator cu comutator sub sarcină (OLTC), cablu mai gros, transformator nou, baterie comunitară | mari; n-am găsit cifre românești | Fraunhofer, 40 de rețele JT germane: https://publica.fraunhofer.de/handle/publica/392685 (rezumat) |

Atenție la `adjust_tap`: priza coborâtă vara poate da subtensiune iarna seara, la consum mare. De aceea regula din cod verifică și marja de jos.

**PPC Ore Smart+** (lansată 18 martie 2026): preț redus noaptea 00:00-05:59, tot weekendul și **zilnic 11:00-14:59 între 1 martie și 31 octombrie**. Energie activă 0,348 lei/kWh fără taxe în intervale, 0,823 lei/kWh în rest; cu taxe în București 0,98 față de 1,56 lei/kWh. Sursa: https://www.bursa.ro/ppc-8222energie-mai-ieftina-in-weekend-prin-ore-smart+8221-27196856 și comunicatul PPC Energie. Pentru clienți casnici cu contor inteligent; dacă se aplică și prosumatorilor n-am găsit. Consecință: mesajul „mutați consumul la prânz” citează oferta doar între martie și octombrie. În noiembrie mesajul nu promite preț redus la prânz.

## 4. Date publice verificate (descărcate în `data/raw/C/`, în afara git)

| Sursa | Ce am luat | Licență | Fișier, sha256 (primele 16) |
|---|---|---|---|
| Open-Meteo Historical Weather (ERA5), punctul 44,45 N 26,05 E | radiație globală, directă, difuză, pe plan înclinat 30° spre sud (GTI), temperatură, nori; orar, 2023-01-01 → 2026-11-06, 33.744 ore, fără goluri | CC BY 4.0 | `openmeteo_archive_2023-01-01_2026-11-06.json`, `78fb9e0515ceb5ce` |
| Open-Meteo Historical Forecast | prognoze arhivate, iul. 2024 și ian. 2025 (eroarea prognozei) | CC BY 4.0 | `openmeteo_histfc_2024-07.json` `a5b43173cff188b8`, `openmeteo_histfc_2025-01.json` `f766076c9a94408a` |
| Open-Meteo Forecast | prognoza pentru 8 și 9 nov. 2026 | CC BY 4.0 | `openmeteo_forecast_2026-11-08_2026-11-09.json`, `eede96ddf1356e1a` |
| PVGIS 5.3 (JRC), 1 kWp, 30°, sud, pierderi 14% | producție orară 2005-2023 | reutilizare cu citarea sursei (JRC) | `pvgis_seriescalc_v5_3_44.45_26.05.json`, `9e48ea60bc7165e5` |
| OpenStreetMap (Overpass), bbox demo | `power=substation`, `power=transformer`, stâlpi cu transformator | ODbL, „© OpenStreetMap contributors” | `osm_power_bbox.json`, `7eee4df3925d73d1` |

Ce am aflat din ele:
- Open-Meteo dă ora locală, iar valoarea de la ora H e media orei H-1..H. `azimuth=0` înseamnă sud. Punctul real al grilei: 44,464 N, 26,089 E. Toate posturile primesc aceeași serie meteo (grilă de circa 11 km).
- Radiația globală orară maximă: 932 W/m² în iunie, 488 W/m² în noiembrie.
- Eroarea prognozei arhivate (radiație globală, ore cu soare): MAE 38 W/m² în iul. 2024, 22 W/m² în ian. 2025. E o limită de jos a erorii pentru ziua următoare.
- PVGIS: **1.282 kWh/kWp pe an** în medie în Ilfov (1.149-1.379), maxim orar 896 W/kWp. SimBench folosește profile germane (circa 650 kWh/kWp pe an în profilele normate), deci producția o calculăm din meteo românesc.
- Prognoza Open-Meteo: 8 nov. senin (GTI 726 W/m² la ora 13, 8,5 °C), 9 nov. acoperit (GTI 457-484 W/m² la prânz). Chiar în noiembrie, o zi senină dă radiație pe panou de circa 0,7 din vârful de vară, iar consumul e altul; deci scenariul `maine` nu e automat „zero lucrări”.
- OSM: 266 de elemente, din care **194** sunt posturi de distribuție plauzibile (`substation` minor_distribution, distribution, yes sau fără subtip; `transformer` distribution sau fără subtip; stâlpi cu transformator), după ce scoatem stațiile de 110 kV și peste, punctele termice (`heat-exchanger`), tracțiunea și generarea. 110 sunt la mai puțin de 6 km de centru, 144 între 6 și 15 km, 12 mai departe. Completăm până la circa 300 cu poziții sintetice în localitățile din Ilfov, etichetate sintetic.
- Consum casnic românesc: n-am găsit o cifră oficială recentă. Peste jumătate dintre casnici consumă circa 55 kWh pe lună (ANRE 2020, https://www.bursa.ro/ anre); 1.674 kWh pe gospodărie în 2014 (https://www.wall-street.ro/special/casa-ta-verde/201281/). Pentru casele din Ilfov folosim 1.500-4.000 kWh pe an, medie circa 2.500: **IPOTEZĂ** (case cu aer condiționat, mai mari decât media națională).

## 5. SimBench și pandapower (măsurat de noi)

- `simbench` 1.6.3 și `pandapower` 3.5.6. Rețele de joasă tensiune: 6 topologii (`1-LV-rural1/2/3`, `1-LV-semiurb4/5`, `1-LV-urban6`), fiecare în 3 scenarii (0 azi, 1 și 2 viitor) și cu sau fără întrerupătoare (`sw` / `no_sw`). Date ODbL, cod BSD.
- Profile la 15 minute pentru 2016 (35.136 de pași): consum casnic H0-A, B, C, G, L, consum comercial G1, G4, G5, G6, fotovoltaic PV1-PV8, normate.
- Fiecare rețea are un singur transformator 20/0,4 kV, sursa e rețeaua de medie tensiune la 1,025 pu, comutatorul e pe partea de MT (±2 trepte de 2,5%).

| Topologie (scenariul 0) | Noduri JT | Linii, km | Cea mai lungă linie, km | Transformator, kVA | Consumatori | PV, kW |
|---|---|---|---|---|---|---|
| rural1 | 14 | 0,56 | 0,137 | 160 | 13 | 160 |
| rural2 | 96 | 1,47 | 0,075 | 250 | 99 | 145 |
| rural3 | 128 | 2,35 | 0,140 | 400 | 118 | 190 |
| semiurb4 | 43 | 0,75 | 0,060 | 400 | 41 | 6 |
| semiurb5 | 110 | 1,79 | 0,098 | 630 | 104 | 137 |
| urban6 | 58 | 1,08 | 0,078 | 630 | 111 | 57 |

**Viteza, măsurată** (`uv run python -m cyberpunks.c_prosumatori.powerflow`, scrie `reports/C/powerflow_bench.json`; pandapower fără numba, mașina împărțită cu alte 5 fire). Pentru fiecare topologie: un post sintetic cu prosumatori, 100 de instantanee aleatoare rezolvate cu `pandapower.runpp` și cu calculul vectorizat, apoi un an de ore (8.760) cu calculul vectorizat.

| Topologie | Noduri JT | Diferența maximă față de pandapower, pu | pandapower, ms pe oră | Vectorizat, ms pe oră | Un an, vectorizat, s | Un an, pandapower (estimat), s |
|---|---|---|---|---|---|---|
| rural1 | 14 | 5,3e-10 | 8,1 | 0,0012 | 0,002 | 71 |
| rural2 | 96 | 5,2e-08 | 8,8 | 0,0049 | 0,057 | 77 |
| rural3 | 128 | 1,1e-08 | 8,2 | 0,0053 | 0,047 | 71 |
| semiurb4 | 43 | 1,7e-08 | 10,8 | 0,0020 | 0,017 | 95 |
| semiurb5 | 110 | 4,2e-10 | 9,1 | 0,0064 | 0,061 | 80 |
| urban6 | 58 | 6,9e-09 | 8,1 | 0,0026 | 0,017 | 71 |

Concluzie: calculul vectorizat dă aceleași tensiuni ca pandapower (diferențe sub 1e-7 pu) și rezolvă un an de ore în sub o zecime de secundă. Asta face posibilă simularea a sute de posturi pe aproape 4 ani de meteo orară (33.744 de ore) în câteva minute, pe 4 nuclee.

**Prima rețea simulată** (`uv run python -m cyberpunks.c_prosumatori.simulate one`): post sintetic pe topologia rural3, 630 kVA, cablu torsadat TYIR 50, linii de 1,79 ori mai lungi, 52 de prosumatori cu 346 kWp, priza pe −1. Pe 2025: tensiunea maximă 1,143 pu, 232 de zile și 1.107 ore peste 1,10 pu, 11.842 kWh fotovoltaici pierduți prin oprirea invertoarelor (2,7% din producție). Simularea celor 8.760 de ore a durat 0,18 s.

## 6. Literatura despre modele surogat (ce putem afirma)

| Referință | Cifre | Ce luăm |
|---|---|---|
| Okoyomon, Goebel, *BOOST-RPF: Boosted Sequential Trees for Radial Power Flow*, 2026, arXiv:2603.21977 | Aceleași 6 rețele JT (rural1-3, semiurb4-5, urban6). RMSE tensiune pe rețele văzute 7,3e-4 pu (XGBoost); **pe rețea nevăzută (leave-one-grid-out) 0,0134 pu în medie (0,0064-0,0215)**, de circa 16 ori mai mare. MLP global inutilizabil pe rețele nevăzute; GNN 0,029 pu. | Reperul direct pentru testul nostru pe rețele nevăzute. Preprint, nerecenzat. |
| Balduin et al., *Evaluating Different Machine Learning Techniques as Surrogate for Low Voltage Grids*, 2020, arXiv:2006.12389 | Regresia liniară și rețelele neuronale merg bine indiferent de topologie | Baseline-ul liniar e serios, nu formalitate |
| Pareek, Misra, Deka, *Learning Power Flow with Confidence*, arXiv:2308.07867 | Proces gaussian, eroare sub 1e-3 pu, de peste 120 de ori mai rapid (rețele de transport) | Riscul de depășire legat de incertitudine |
| Romano, Patterson, Candès, *Conformalized Quantile Regression*, 2019, arXiv:1905.03222 | Acoperire garantată pe eșantioane finite | Recalibrăm intervalele P10-P90 pe rețele lăsate deoparte |
| Meinecke et al., *SimBench*, Energies 13(12):3290, 2020, https://doi.org/10.3390/en13123290 | Seturi JT-MT-ÎT, serii de un an la 15 min | Sursa rețelelor |
| Demirel et al., 2024, arXiv:2404.02763 | SimBench plus pandapower pentru PV mic în JT | SimBench e practică acceptată |
| VDE-AR-N 4105 (Germania) | Generatoarele pot ridica tensiunea cu cel mult 3% la punctul de racord | Regula de screening pentru cererile de racordare |

Ce înseamnă pentru noi:
- Cifrele de accelerare din literatură (145x, 400x) sunt pe rețele de transport. Nu le preluăm; raportăm doar ce măsurăm.
- Pe rețele nevăzute promitem cel mult ce arată literatura (ordinul 0,01 pu). Arătăm deschis scăderea de la rețele văzute la nevăzute.
- Juriul va aștepta: tabel leave-one-topology-out pe fiecare rețea, acoperirea reală a intervalelor P10-P90 (ținta 80%), PR-AUC și recall pe depășiri, curba de calibrare, Brier.
- Fără recalibrare, intervalele vor acoperi sub 80% pe rețele noi. Le recalibrăm pe predicții făcute pe topologii nevăzute (out-of-fold pe grupuri).

## 7. Deciziile de proiectare care rezultă

1. **Rezoluție orară.** Meteo e orară; profilele SimBench de 15 minute se mediază pe oră.
2. **Calculul de rețea**: pandapower construiește matricea de admitanțe a fiecărei rețele (transformator cu priză, linii, magnetizare). Pe ea rulăm un calcul vectorizat (metoda Z-bus, punct fix) pentru toate orele deodată. Îl verificăm pe instantanee aleatoare față de `pandapower.runpp`.
3. **Producția PV** din Open-Meteo: GTI × putere instalată × randament (cu pierderi la temperatură), cu orientări diferite pe case. Consumul din profilele SimBench, aliniat pe ziua săptămânii și scalat la consum românesc.
4. **Posturile** sunt variante sintetice ale celor 6 topologii: transformator 100-630 kVA, linii scurtate sau lungite, priză, tensiunea din MT, câți prosumatori, ce puteri (3-15 kWp, media pe persoană fizică 6,4 kW după ANRE), câți au baterii (35% după ANRE).
5. **Ținta**: tensiunea maximă pe post (orară și zilnică), încărcarea transformatorului, kWh pierduți prin oprirea invertoarelor (simulăm cascada de opriri).
6. **Testul**: rețele nevăzute (topologii întregi lăsate deoparte, ca în BOOST-RPF) și luni nevăzute (antrenare pe 2023-2024, test pe 2025-2026).
7. **Baseline**: regresie liniară pe radiație × kW instalați pe kVA, plus regula de creștere a tensiunii (ΔU ≈ R·P/U², pragul de 3% din VDE-AR-N 4105) ca referință fizică.
8. **Acțiunile** și valoarea: 70 lei pe reclamație evitată (Ord. 46/2021) plus kWh fotovoltaici salvați × 0,40 lei (**IPOTEZĂ** din `config/economics.yaml`); mesajul către prosumatori citează Ore Smart+ doar martie-octombrie.

## 8. De verificat mai târziu

- Textele consolidate ale Ord. ANRE 228/2018, 132/2020 și 19/2022 (PDF-urile Rețele Electrice n-au mers).
- Dacă Ord. 46/2021 a fost modificat la limita de +5%.
- Prosumatori pe distribuitori în 2026; costul real al unei reglări de priză și al unei campanii de măsurători.
