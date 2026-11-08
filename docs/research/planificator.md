# Cercetare: planificatorul (faza 0)

Scris de firul planificator pe 7 nov. 2026, între 12:50 și 14:15, cu trei subagenți de cercetare în paralel. Regula: o cifră intră în `config/economics.yaml` doar cu sursă. Altfel are eticheta IPOTEZĂ și motivul. Etichetele din config:

- **SURSĂ**: cifra apare în documentul citat.
- **PROXY**: o cifră reală folosită ca aproximare (de exemplu un tarif reglementat în locul costului intern).
- **CALCUL**: derivată din surse, cu formula scrisă.
- **IPOTEZĂ**: fără sursă găsită, aleasă cu motiv; se variază la analiza de sensibilitate.

Am folosit doar ce am citit în documentul însuși. Rezumatele motorului de căutare au avut greșeli (de exemplu cifre din Republica Moldova prezentate ca românești), așa că nu le-am folosit ca sursă.

## 1. Ipotezele economice, verificate

| Cheie în `config/economics.yaml` | Înainte | Acum | Stare | Sursa |
|---|---|---|---|---|
| `energy.retail_price_lei_per_kwh` | 1,56 | 1,56 | SURSĂ | PPC Energie, comunicat 18.03.2026, "PPC Ore Smart+": "în afara intervalelor prețul standard final, cu toate taxele incluse este de 1,56 lei/kWh" (0,98 în intervalele Smart) [S1] |
| `energy.loss_cost_lei_per_kwh` | 0,55 | **0,70** | PROXY | Prețul PZU OPCOM: 575,22 lei/MWh în 2025 (raport anual) [S2]; ≈726 lei/MWh medie ponderată ian.-oct. 2026, calculată din rapoartele lunare [S3]. Prețul CPT recunoscut de ANRE în tarife nu l-am găsit |
| `meters.inspection_visit_cost_lei` | 180 | **250** | PROXY | Tarif Rețele Electrice, Zona Muntenia 2026, poz. 18, "citire date de măsurare la cererea clientului": 246,89 lei fără TVA [S4]. E prețul pentru client al unei deplasări la contor, nu costul intern |
| `meters.remote_reading_cost_lei` | 2 | 2 | IPOTEZĂ | Telecitirea nu se taxează (același tarif, poz. 17), deci costul marginal e mic |
| `meters.detection_horizon_days` | 90 | 90 | IPOTEZĂ | La casnici, intervalul maxim de citire e de 3 luni (Legea 123/2012, art. 45 alin. 10, după presă; un articol spune 6 luni, contradicție nelămurită) |
| `meters.recalculation_cap_years` | - | 3 | SURSĂ | Ord. ANRE 190/2020, art. 12 alin. (1): recalcularea consumului "nu poate depăși 3 ani" [S5]. E plafonul de recuperare, nu orizontul pierderii |
| `meters.service_time_min` | 40 | 40 | IPOTEZĂ | Nicio cifră publică despre durata unui control |
| `storm.preposition_cost_lei_per_crew_shift` | 1.500 | **2.700** | CALCUL | 3 oameni × 8 h × 58,1 lei/h (câștig mediu brut iulie 2026: 9.709 lei) × 1,0225 (CAM) × 1,75 (spor de ore suplimentare, minim 75%, Codul muncii art. 123 alin. 2 [S6]) + ~200 lei vehicul. Interval 1.500 (tură normală) - 4.100 (salariul mediu din energie, ~15.000 lei brut, agregatori) |
| `storm.cost_per_customer_hour_lei` | 12 | 12 | CALCUL | VoLL casnic România 4,52 €/kWh (euro 2015), CEPA pentru ACER 2018, tabelul G.1 [S7] × 0,23 kWh/h (IPOTEZĂ, ≈2.000 kWh/an) × 5,34 lei/€ ≈ 5,5 lei; cu 15% clienți non-casnici ≈ 15 lei. Interval 5,5-15. Un VoLL aprobat de ANRE nu există (ACER îl arăta "Pending" în 2021) |
| `storm.restoration_speedup_hours` | 2,5 | 2,5 | IPOTEZĂ | N-am găsit un studiu verificabil; cifrele "30-50%" de pe bloguri n-au sursă. De variat 1-4 h |
| `storm.compensation_lei_per_customer_lv` | - | 30 | SURSĂ | Ord. ANRE 46/2021, Anexa 1: 30 lei JT, 200 lei MT, 300 lei la 110 kV, pentru fiecare depășire; plată automată (art. 36) [S8] |
| `storm.restoration_limit_hours` | - | 6 / 4 / 12 / 48 / 72 | SURSĂ | Ord. ANRE 46/2021, art. 15 alin. (1): urban 6 h, reședință de județ 4 h, rural 12 h, vreme deosebită 48 h (intravilan) și 72 h (extravilan) [S8] |
| `voltage.tap_change_visit_cost_lei` | 450 | 450 | IPOTEZĂ | Nicio cifră publică. Comutatorul fără sarcină cere scoaterea transformatorului din tensiune |
| `voltage.measurement_campaign_cost_lei` | 300 | 300 | IPOTEZĂ | Nicio cifră publică |
| `voltage.lost_pv_value_lei_per_kwh` | 0,40 | 0,40 | IPOTEZĂ | În intervalul 0,348 (energia activă PPC Ore Smart+ la prânz [S1]) - 0,73 (PZU 2026). Prosumatorii până la 200 kW sunt compensați la prețul energiei active din contract (Legea 160/2026, art. 73^1 alin. 3) [S9] |
| `voltage.overvoltage_limit_pu` | 1,10 | 1,10 | SURSĂ | Ord. ANRE 228/2018, Tabelul 2P: protecția de maximă tensiune 1,1 Un, mediată la 10 minute; treapta instantanee 1,15 Un, 0,5 s [S10] |
| `voltage.planned_outage_hours` | - | 1,0 | IPOTEZĂ | Durata întreruperii scurte pentru schimbarea prizei |
| `outages.planned_notice_working_days_lv` | - | 2 | SURSĂ | Ord. ANRE 46/2021, art. 12 alin. (2) lit. c): JT, minimum 2 zile lucrătoare, prin presă și pe site [S8] |
| `outages.planned_notice_working_days_mv` | - | 5 | SURSĂ | art. 12 alin. (2) lit. b) |
| `outages.planned_max_hours` | - | 8 | SURSĂ | art. 13 alin. (1) |
| `crew.cost_lei_per_person_hour` | - | 59,4 | CALCUL | 9.709 lei / 167 h × 1,0225 (CAM). Salariul din energie e mai mare, deci cifra e prudentă |
| `travel.*` (viteze, factorul de drum, cost pe km) | - | - | IPOTEZĂ | Viteze 22 km/h urban și 45 km/h extraurban, factor de drum 1,35, 1,2 lei/km |

### Ce schimbă asta pentru firele A, B, C

- A: vizita costă 250 lei (nu 180), energia pierdută valorează 0,70 lei/kWh pentru distribuitor (nu 0,55).
- B: o tură suplimentară costă 2.700 lei (nu 1.500). Pragul de rentabilitate pentru o echipă trimisă din timp crește.
- C: neschimbat, plus regula de preaviz (mai jos).

## 2. Reguli ANRE care intră direct în decizie

Toate din Ordinul ANRE nr. 46/2021, Standardul de performanță pentru serviciul de distribuție, Monitorul Oficial 649 din 1 iulie 2021, citit din Monitorul Oficial [S8]. Ordinele 64/2022 și 20/2025 îl modifică; sinteza Rețele Electrice făcută după 64/2022 are aceleași sume. Textul Ord. 20/2025 nu l-am putut citi.

1. **Preaviz pentru o întrerupere planificată** (art. 12 alin. 2): 2 zile lucrătoare pentru joasă tensiune, 5 pentru medie tensiune, 15 pentru clienți mari și vulnerabili. Anunțul spune data, ora și durata.
   - **Consecință în planificator (regula `R-C-TAP-NOTICE`)**: schimbarea prizei unui transformator cere o întrerupere scurtă. Pentru un plan făcut azi pe mâine nu există preavizul legal, deci agentul nu trimite echipa mâine. Programează întreruperea la prima zi lucrătoare permisă, generează anunțul (demo, nu se trimite) și, pentru mâine, trimite mesajul către prosumatori (consumul mutat la prânz).
2. **Durata maximă a unei întreruperi planificate** (art. 13): 8 ore; cel mult 4 pe an în urban și 8 în rural.
3. **Durata maximă de restabilire după o avarie** (art. 15): 6 h urban, 4 h în reședințele de județ, 12 h rural; la vreme deosebită 48 h intravilan și 72 h extravilan. Peste termen, distribuitorul plătește automat 30 lei fiecărui client JT (Anexa 1, art. 36), cu plafon de 50 lei pe lună.
   - **Consecință (regula `R-B-PREPOSITION`)**: o echipă trimisă din timp scurtează restabilirea și reduce riscul de compensații. Valoarea o calculează firul B; planificatorul compară valoarea așteptată cu costul turei (2.700 lei).

Context pentru furtună: SAIDI neplanificat 2024 (minute pe client): Muntenia 74,6, Banat 95,1, Dobrogea 79,9 (pagina Rețele Electrice) [S11].

## 3. Ordinul de lucru: ce câmpuri are

Rețele Electrice nu își publică formularele interne. Modelul credibil găsit e instrucțiunea proprie de securitate a altui operator, DEER (grupul Electrica), IP-SSM-01, care urmează normele de sector [S12]:

- Formele de organizare a lucrului (art. 74): autorizație de lucru (AL), instrucțiuni tehnice interne de protecție a muncii (ITI-PM), atribuții de serviciu (AS), dispoziție verbală (DV), proces-verbal (PV).
- Rolurile (art. 75-79): emitent (dispune lucrarea, grupa V), admitent (face separarea, minim grupa IV), șef de lucrare (conduce formația, minim grupa III), executanți.
- La contoare: Ord. ANRE 121/2015 cere o notă de constatare (tip contor, serie, index) și un proces-verbal semnat de client; dacă clientul lipsește, se fac fotografii (art. 34) [S13].
- Modelul internațional IEC CIM (pachetul Work: `Work`, `WorkTask`, `Crew`) are numărul ordinului, ETA-ul echipei, durata și legătura cu activul [S14].

**Câmpurile din PDF-ul nostru** (`outputs/plans/<s>/work_orders/<echipă>.pdf`), marcat "DEMO, date sintetice, nu e un document oficial":

| Parte | Câmpuri |
|---|---|
| Antet | număr și dată ordin; echipa, baza, zona; emitent: "agentul propune, dispecerul aprobă"; șef de lucrare și executanți (de completat, cu grupa de autorizare); intervalul turei; rezumatul zilei (opriri, km, ore) |
| Pe fiecare oprire | ordinea și ora estimată de sosire; tipul lucrării; locul (etichetă, zonă, coordonate); activul (contor, zonă, post de transformare); de ce (factorii modelului în cuvinte simple, scorul, încrederea); acțiunea cerută, în pași; durata; măsurile anterioare (de exemplu citirea la distanță); ID-ul predicției și versiunea modelului |
| Siguranță | forma de organizare (DV/AS la contoare simple, AL la post cu scoatere de sub tensiune); întrerupere planificată (da/nu, interval, clienți, anunțul demo); separare și legare la pământ (de bifat); echipament de protecție; alerta de siguranță, dacă există |
| De completat pe teren | index, starea sigiliilor, constatări (capac, șunt, racord direct, nimic), fotografii, măsurători la post (tensiunea pe faze, priza înainte și după), rezultat (rezolvat, reprogramat, escaladat), ora de început și de sfârșit |
| Semnături | șef de lucrare, executanți, client (sau "absent / refuză") la contor, admitent la post |

## 4. Citirea la distanță la cerere

- Contorul inteligent comunică (PLC sau GPRS) cu sistemul central al operatorului (HES/MDMS, termenul din Ord. ANRE 94/2021) prin protocolul DLMS/COSEM. Curba de consum se înregistrează la 15 minute (Ord. ANRE 145/2014, anexa 1, funcția 2), adică 96 de valori pe zi, trimise de obicei o dată pe zi [S15].
- **Citirea la cerere**: operatorul trimite o comandă și primește pe loc indexul, tensiunea și jurnalul de evenimente, fără deplasare. Latența (secunde-minute) nu are sursă; o tratăm ca IPOTEZĂ.
- E obligatorie: Recomandarea 2012/148/UE cere sistemelor de contorizare inteligentă "să permită citirea de la distanță a contoarelor de către operator" (lit. c) și "să prevină și să detecteze fraudele" (lit. i) [S16]; Ord. ANRE 145/2014 o are ca funcție obligatorie (nr. 3), alături de detectarea accesului neautorizat (nr. 9).
- Exemplul din practică: i-DE (Iberdrola) citește zilnic evenimentele de deschidere a capacului, filtrează intervențiile de mentenanță și trimite inspecții doar pentru restul [S17]. Același flux îl face agentul nostru.
- Rețele Electrice: peste 2 milioane de contoare inteligente în 2025, cu acoperire de 60% în București-Ilfov-Giurgiu (Business Forum, martie 2025) [S18]; peste 1,6 milioane trimit date zilnice furnizorilor (Agerpres, dec. 2024).
- **Cum o folosește planificatorul**: e acțiunea ieftină (2 lei) pentru contoarele unde vizita nu se justifică încă: încredere medie, valoare sub costul vizitei sau echipe pline. Dacă citirea confirmă problema, contorul intră a doua zi în traseu. O citire eșuată (contor offline) e și ea un semnal: cazul urcă la vizită.

## 5. Optimizarea traseelor cu OR-Tools

Problema e o rutare cu colectare de premii (prize-collecting VRP) cu ferestre de timp. Fiecare lucrare e un nod opțional: dacă rămâne nefăcută, solverul plătește o penalitate egală cu prioritatea ei (în bani). Solverul alege ce face și în ce ordine, ca suma penalităților plus costul drumurilor să fie minimă. Cum se leagă fiecare cerință de API-ul OR-Tools (`ortools.constraint_solver.pywrapcp`, versiunea 9.15 din `uv.lock`):

| Cerință | În OR-Tools |
|---|---|
| Noduri opționale cu penalitate | `routing.AddDisjunction([index], penalitate)` [S19] |
| Ferestre de timp, durata lucrării, tura | dimensiunea "Time" (`AddDimension`), cu durata de lucru adăugată la timpul de drum și `CumulVar(index).SetRange(start, end)` [S20] |
| Depouri multiple | `RoutingIndexManager(n, nr_echipe, starts, ends)`: fiecare echipă pleacă și se întoarce la baza ei [S21] |
| Abilități (`metering`, `lv_grid`, `mv_grid`) și mărimea echipei | `routing.VehicleVar(index).SetValues([-1] + echipe_potrivite)` (-1 = lucrare nefăcută) |
| Echipa de furtună rămâne în zonă | nodul B e ultimul din traseu: drumul de la el la bază costă 0 |
| Siguranță | penalitate foarte mare plus premiul real (între două cazuri obligatorii îl alege pe cel mai valoros); rezolvare în două faze: întâi doar cazurile obligatorii (intră câte încap), apoi toate lucrările, pornind de la traseele lor (`ReadAssignmentFromRoutes`) |
| Oprire | după 200 de soluții (`solution_limit`), ca planul să fie același la fiecare rulare; `time_limit` de 60 s e doar o plasă. Cu o limită de 10 s, planul real ieșea puțin diferit de la o rulare la alta, după cât de ocupat era calculatorul. Prima soluție `PATH_CHEAPEST_ARC`, apoi `GUIDED_LOCAL_SEARCH` [S22] |
| Rezerva | inserare greedy, în ordinea priorității, cu aceleași restricții: dacă OR-Tools nu dă soluție sau dacă dă una mai slabă decât greedy (comparate după cazurile obligatorii făcute, apoi după premii minus drum) |

Drumul dintre două puncte: distanța haversine × factorul de drum (1,35), cu viteza urbană pe primii 10 km și cea extraurbană după (config).

**Măsurat** (`uv run python -m cyberpunks.planner.benchmark`, `reports/planner/solver_benchmark.json`, 16:39, lucrări sintetice, 11 echipe, câte 3 semințe), cu setările din config (200 de soluții, exact funcția folosită de agent): OR-Tools termină în 0,5-0,7 s la 100 de lucrări, 1,2-1,3 s la 200 și 2,0-2,2 s la 300. Față de inserarea greedy aduce cu 2,9-7,4% mai multă valoare netă la 100 de lucrări, 5,6-7,1% la 200 și 7,2-12,5% la 300. Încă 30 de secunde de căutare adaugă 0-0,9% la 100 de lucrări, 0,4-2,6% la 200 și 0-6,2% la 300: prețul unui plan care iese la fel la fiecare rulare. Pe planul real din 8 iulie 2025 (697 de lucrări, 293 candidate pentru echipe, 12 obligatorii), cele două faze durează 7,6 s; cu 300 sau 400 de soluții, valoarea nu mai crește.

## 6. Ce n-am găsit (riscuri cunoscute)

- Prețul CPT recunoscut de ANRE în tarifele 2025-2026 și rata pierderilor Rețele Electrice în %.
- Costul intern al unei vizite (folosim tariful reglementat ca aproximare).
- Durata și costul schimbării prizei la un transformator MT/JT.
- Un studiu verificabil despre cât scurtează restabilirea o echipă trimisă din timp.
- Consumul orar mediu oficial al unei gospodării; salariul oficial INS pe CAEN 35.
- Textul Ord. ANRE 20/2025 (modifică standardul de performanță) și textul legii despre intervalul de citire (3 sau 6 luni).
- Formularele oficiale Rețele Electrice (autorizație de lucru, foaie de manevră).
- Latența citirii la cerere, într-un document oficial.

## Surse

- [S1] PPC Energie, comunicat de presă, 18.03.2026, "PPC Energie lansează noua ofertă cu tarif dinamic PPC Ore Smart +": https://www.ppcenergy.ro/wp-content/uploads/Comunicat-de-presa-PPC-Energie-lanseaza-noua-oferta-PPC-Ore-Smart-.pdf
- [S2] OPCOM, Raport anual de sinteză 2025, secțiunea PZU: https://opcom.ro/uploads/doc/rapoarte/Anual/RS_2025_RO.pdf
- [S3] OPCOM, rapoarte de piață lunare ian.-oct. 2026 (R_2601 ... R_2610), de exemplu: https://opcom.ro/uploads/doc/rapoarte/lunar/R_2610_RO.pdf
- [S4] Rețele Electrice, Servicii de rețea, Zona Muntenia, 2026: https://www.reteleelectrice.ro/wp-content/uploads/tarife-servicii-rem-2026_14e276.pdf
- [S5] Ord. ANRE 190/2020, MO 1030/2020: https://legeaz.net/monitorul-oficial-1030-2020/ordin-anre-190-2020
- [S6] Codul muncii (Legea 53/2003), art. 123: https://www.rubinian.com/codul-muncii-titlul-3-capitolul-1-sectiunea-2-articolul-123
- [S7] CEPA pentru ACER, "Study on the estimation of the value of lost load of electricity supply in Europe", iulie 2018, Anexa G: https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/Infrastructure_and_network%20development/Infrastructure/Documents/CEPA%20study%20on%20the%20Value%20of%20Lost%20Load%20in%20the%20electricity%20supply.pdf
- [S8] Ord. ANRE 46/2021, Standardul de performanță pentru serviciul de distribuție, MO 649/1.VII.2021: https://www.ppcenergy.ro/wp-content/uploads/ord-46-2021.pdf ; sinteza Rețele Electrice: https://reteleelectrice.ro/wp-content/uploads/sinteza-standard-de-performanta.pdf
- [S9] Legea 160/2026 pentru modificarea Legii 123/2012, MO 603/23.07.2026: https://lege5.ro/Gratuit/ge4dsnrtgq2di/legea-nr-160-2026-pentru-modificarea-si-completarea-legii-energiei-electrice-si-a-gazelor-naturale-nr-123-2012
- [S10] Ord. ANRE 228/2018, Norma tehnică pentru racordarea prosumatorilor: https://reteleelectrice.ro/wp-content/uploads/ordinul-anre-228-2018.pdf
- [S11] Rețele Electrice, indicatori de performanță: https://www.reteleelectrice.ro/en/?p=18659 ; Muntenia 2025: https://www.reteleelectrice.ro/wp-content/uploads/muntenia-anexa-2-2025.pdf
- [S12] DEER, IP-SSM-01, instrucțiune proprie de securitate și sănătate în muncă: https://www.distributie-energie.ro/wp-content/uploads/2021/07/DEER-IP-SSM-01.pdf
- [S13] Ord. ANRE 121/2015, MO 594/2015: https://legeaz.net/monitorul-oficial-594-2015/ordinul-anre-121-2015/anexa-procedura
- [S14] IEC CIM, WorkTask: https://zepben.github.io/evolve/docs/cim/cim100/TC57CIM/IEC61968/Work/WorkTask
- [S15] Ord. ANRE 145/2014, anexa 1: https://legeaz.net/monitorul-oficial-931-2014/ordinul-anre-145-2014/anexa-1-functionalitati-ale-sistemelor-de-masurare-inteligenta-smi-a-energiei ; Ord. ANRE 94/2021: https://www.ppcenergy.ro/wp-content/uploads/ord-94-2021.pdf
- [S16] Recomandarea Comisiei 2012/148/UE: https://eur-lex.europa.eu/legal-content/RO/TXT/?uri=CELEX:32012H0148
- [S17] e.DSO, cazul i-DE, detectarea manipulării: https://edsoforsmartgrids.eu/content/uploads/2024/10/27.-e.dso-success-case_i-de_tamper-detection-final.pdf
- [S18] Business Forum, 17.03.2025: https://businessforum.ro/energy/20250317/retele-electrice-romania-to-reach-2-million-smart-meters-in-romania-1568
- [S19] OR-Tools, Penalties and Dropping Visits: https://developers.google.com/optimization/routing/penalties
- [S20] OR-Tools, Vehicle Routing with Time Windows: https://developers.google.com/optimization/routing/vrptw
- [S21] OR-Tools, Routing tasks (start and end locations): https://developers.google.com/optimization/routing/routing_tasks
- [S22] OR-Tools, Routing options: https://developers.google.com/optimization/routing/routing_options
