# PPC România: probleme reale 2026 pe cele 4 companii

Rezumatul unui document de research primit de Teo ("PPC România: probleme reale 2026 pe cele 4 companii pentru SmartHack XI", 13 pagini, scanat). Teo l-a aprobat ca sursă de lucru la 14:30. Originalul și paginile ca imagini sunt local, în `materiale/` (nu intră în git). NU e verificat de noi; documentul spune singur că unele cifre diferă între surse. În prezentare, fiecare cifră merge cu data și sursa ei.

## Ce confirmă pentru proiect

- B (întreruperi și compensații automate, problema D1) și C (tensiune pe posturi cu prosumatori, D4) sunt pe lista problemelor NEACOPERITE de cele 9 proiecte AI PPC.
- "Detecție de fraudă / consum anormal" e capcană: există deja (02 Energy Anomaly Detection, în producție). "Contoare defecte" e pasul următor anunțat de PPC. Pierderile în rețea (CPT, D3) sunt exact ce face bilanțul pe post.
- Alte capcane din document: mentenanța predictivă a turbinelor și panourilor (01 Smart Sentry, în producție), prognoza consumului la 15 minute (05, în producție) și a producției eoliene (08, în dezvoltare), clasificarea reclamațiilor (07 ReClassAI) și rutarea documentelor (03 LegalRoute), recuperarea restanțelor (06 AI Claims Agent, în dezvoltare).

## Context 2026 (din document)

- PZU (OPCOM) merge la 15 minute din 1 octombrie 2025. Plafonarea prețului la energie s-a încheiat la 1 iulie 2025.
- Prețuri negative la prânz și limitări preventive ale producției eoliene în Dobrogea.
- August-octombrie 2026: măsuri guvernamentale de criză pentru deficitul de seară (18-22).
- Legea 160/2026, în vigoare din 26 iulie 2026, schimbă compensarea prosumatorilor (≤200 kW: compensare cantitativă până la 31 dec. 2030). Pragul de schimbare a regimului apare contradictoriu în presă (200, 400 sau 900 kW): de verificat în textul legii.
- Mesaj pentru prezentare: "2026 e anul în care problemele din Europa de Vest au devenit românești": prețuri negative la prânz, deficit de seară 18-22, rețea de joasă tensiune saturată de prosumatori.

## B: întreruperi și compensații

- RER plătește circa 85% din compensațiile automate naționale (raportul ANRE pe 2024). Cifrele absolute diferă între surse (14,6 mil. lei RER Muntenia; 16,5 din 18 mil.; 23 din 26,2-26,7 mil.). Nu le amestecăm: folosim doar procentul sau o singură sursă cu anul.
- Standardul de repunere în funcțiune: 8 h urban, 12 h rural, 48 h pe vreme rea. Compensația: 30 lei pe depășire la JT, 200 lei la MT (reteleelectrice.ro).
- Muntenia 2024: SAIDI neplanificat 95,14 min, SAIFI neplanificat 2,29. Banat și Dobrogea: SAIDI 79,9 min, SAIFI 2,3-2,55.
- 2025-2029: ANRE leagă rentabilitatea distribuitorului de un indicator compus (calitate, integrarea surselor regenerabile, digitalizare).
- Atenție: firul B a găsit separat, în Ord. ANRE 46/2021, praguri de 4/6/12 h pe vreme normală și 48/72 h pe vreme deosebită. Documentul spune 8/12/48 h. Diferența trebuie lămurită din sursa primară înainte de prezentare.

## C: prosumatori și tensiune

- ANRE, 31 aug. 2026: 385.791 de prosumatori, 4.281,86 MW, din care 151.040 cu stocare. Înlocuiește 359.378 (30 iunie) peste tot, cu data.
- Pe județe (ANRE, aug. 2026): Ilfov e primul din țară cu 21.647 de prosumatori (303,81 MW), Timiș are 18.262 (205,62 MW), București 8.307 (134,94 MW). Toate trei sunt în zona RER. Harta C e în Ilfov: argument direct.
- Puterea medie a unei gospodării prosumatoare: circa 6,4 kW (pentru generarea posturilor).
- Compensația pentru nerespectarea curbei de tensiune: 70 lei pentru persoane fizice la JT, pe perioada de monitorizare. Planul RER pomenește posturi noi pentru reclamațiile de tensiune.
- Treapta 4 (baterii): bateria încărcată la prânz și descărcată seara rezolvă două probleme deodată: supratensiunea de la prânz și deficitul de seară (18-22).
- Problemă transversală: impactul hub-urilor de încărcare PPC Blue asupra rețelei RER (B4 + D4) există doar pentru că PPC deține ambele companii.

## Bilanț pe post: pierderi (CPT)

- CPT Muntenia: 10,78% (2018), 8,66% (2023); nivelul recunoscut de ANRE 8,97%; 63,54% din CPT e la joasă tensiune (Plan RER 2024-2033).
- RER: circa 3.900 de intervenții neautorizate în 2025, circa 700 în ian.-feb. 2026, circa 10 GWh estimați sustrași (Digi24). Comparații: DEER 2.071 de cazuri în 2025, Distribuție Oltenia circa 1.680.
- Pentru model: prosumatorii complică bilanțul pe post (fluxuri în ambele sensuri). Bilanțul folosește și energia injectată (contoare bidirecționale), iar simularea are posturi cu prosumatori.

## A: contoare

- Gradul de integrare a contoarelor inteligente la 31 dec. 2025: 66,85% Dobrogea, 58,81% Muntenia, 56,45% Banat (infobuz). Argument real pentru "datele lipsă" la robustețe.
- RER: 3.180.331 de utilizatori (Muntenia 1.506.549, Banat 967.682, Dobrogea 706.100). 2 mil. de contoare inteligente, țintă 2,164 mil. (67%) la final de 2026.

## Comparația companiilor (tabelul din document)

- PPC Renewables: probleme foarte măsurabile și cele mai bune date publice (ENTSO-E, OPCOM la 15 minute, CARE to Compare, imagini PV), dar cea mai mare suprapunere cu portofoliul AI PPC.
- Rețele Electrice: problemele cele mai măsurabile oficial (SAIDI, SAIFI, compensații ANRE în lei, CPT), dar date publice slabe pentru România (agregate anuale); seturile străine (SGCC, Londra) sunt bune. Potrivire foarte bună cu Perceive-Estimate-Decide-Act și foarte ușor de explicat.
- PPC Energy: date slabe (majoritatea sintetice), suprapunere mare (3 din 5 probleme).
- PPC Blue: zero suprapunere cu portofoliul, dar date mai ales străine (SUA, UK; Open Charge Map pentru România).
- Lipsesc date publice despre restanțele PPC Energy, curtailment-ul PPC Renewables și rata de succes a transmisiei contoarelor RER. Valorile punctuale din presă (de exemplu 60.976 lei/MWh pe piața de echilibrare) sunt evenimente, nu medii.
