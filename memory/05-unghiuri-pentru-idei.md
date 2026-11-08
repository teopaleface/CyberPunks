# Direcții de proiect, după tema anunțată

Rescris pe 7 nov. 2026, după anunțarea temei (`07-tema-ppc.md`). Varianta de dinainte de temă e în istoricul git. Încă nu e o decizie: echipa alege, iar alegerea intră în `journal.md`.

Actualizare 12:06, după PDF-ul oficial: exemplele PPC descriu aproape cuvânt cu cuvânt direcția A ("ce clienți trebuie verificați", "detecție de anomalii cu etichete puține", "ranking sub constrângeri de capacitate", "un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață"). A trece pe primul loc la relevanță. C rămâne alternativa mai originală.

Filtrul: model ML propriu cu test separat și baseline, agent care face acțiuni, date publice sau sintetice, relevanță credibilă pentru PPC. Am evitat să copiem proiecte pe care PPC le are deja în producție (lista în `08-ppc-workshop-ai.md`).

## Comparație rapidă

| Direcție | Firma PPC | Relevanță PPC (25) | Calitate ML (25) | Agent (25) | Robustețe (10) | Date publice |
|---|---|---|---|---|---|---|
| A. Contoare defecte sau manipulate, plus echipele de verificare | Rețele Electrice | Foarte bună: PPC a spus că e următorul pas | Bună: etichete reale și sintetice | Foarte bună: capacitate de echipe, cost pe vizită | Foarte bună: datele lipsă sunt chiar semnalul | Da (licența SGCC neclară) |
| B. Furtună în 24 de ore: risc de avarii și echipe trimise din timp | Rețele Electrice | Bună: reziliență, SAIDI/SAIFI | Bună | Foarte bună | Foarte bună: evenimente rare | Da, dar din SUA |
| C. Prosumatorii ridică tensiunea: posturi de transformare în pericol mâine | Rețele Electrice, plus PPC Energy | Foarte bună: 359.378 de prosumatori, invertoare care se opresc, reguli de racordare înăsprite | Foarte bună: etichete din simulare fizică, test pe o rețea nevăzută | Foarte bună: acțiuni pe mai multe firme PPC | Foarte bună: incertitudinea prognozei meteo | Da (SimBench, licență ODbL) |
| D. Baterie și parc solar la prețuri negative | PPC Renewables | Bună: au baterii în România și JV de 1,5 GW | Bună: prețuri reale românești | Foarte bună: plan orar cu constrângeri de baterie | Foarte bună: vârfuri și prețuri negative rare | Da (Energy-Charts, doar uz necomercial) |
| E. Parc eolian: prognoză și decizie | PPC Renewables | Medie: PPC are deja proiectul în dezvoltare | Foarte bună | Medie | Bună | Da |
| F. Stații de încărcare: cerere și defecte | PPC Blue | Medie | Bună | Bună | Medie | Da, din SUA și UK |
| G. Risc de neplată sau programarea consumului în orele ieftine | PPC Energy | Medie: suprapunere cu AI Claims Agent și myEnergy Coach | Slabă spre medie: doar date sintetice sau din altă țară | Bună | Medie | Parțial |

## A. Contoare defecte sau manipulate, plus echipele de verificare (recomandată, prima)

- Problema PPC: au peste 2 milioane de contoare care trimit 96 de citiri pe zi. În prezentare au scris că urmează "anomaly detection on meter behaviour, predictive monitoring of faulty meters". În Grecia au avut loturi întregi de contoare defecte (până la 250.000 de puncte). Detectarea fraudei există deja (Energy Anomaly Detection, în producție), deci accentul nostru e pe contoare defecte, pe manipulare și pe decizia de după: pe cine trimiți să verifice, azi.
- Perceive: consumul pe fiecare contor (la 15 sau 30 de minute, sau zilnic), golurile din date, comparația cu vecinii de pe același post de transformare.
- Estimate: modelul dă pentru fiecare contor o probabilitate pentru normal, defect (blocat, zero, goluri, salturi, derivă) sau suspect de manipulare, plus energia și banii pierduți pe lună.
- Decide: pragul vine din bani. Trimitem o echipă dacă probabilitatea înmulțită cu valoarea recuperată depășește costul vizitei. Echipele au capacitate limitată pe zi și pe zonă. Încredere mare: ordin de lucru. Încredere medie: cerem o citire de la distanță. Încredere mică: lista de urmărire.
- Act: lista zilnică de verificări pe fiecare echipă, grupată pe zone, ordine de lucru, alertă pentru cazurile critice, raport săptămânal. Un LLM poate scrie explicația pentru tehnician, verificată în cod față de cifre.
- Date: setul SGCC (42.372 de clienți, consum zilnic 2014-2016, 3.615 marcați ca furt, circa 25% valori lipsă) și contoarele din Londra (Low Carbon London, la 30 de minute) cu defecte injectate de noi, etichetate din construcție.
- Baseline: o regulă simplă (consum zero mai mult de N zile, sau scădere peste 50% față de propriul istoric). Model: gradient boosting pe caracteristici calculate din serie, eventual o rețea 1D. Metrici: PR-AUC și precizie în primele K contoare, unde K e capacitatea echipelor. Asta leagă direct modelul de decizie.
- Robustețe: golurile din date intră în model ca semnal. Contorul cu prea puțin istoric primește "nu știu" și ajunge la om. Testăm separat tipurile rare de defecte.
- Explicabilitate: pentru fiecare contor, primele motive în cuvinte simple ("consum zero 9 zile după un istoric stabil", "cu 70% sub vecinii de pe același post").
- Etică: nu acuzăm automat pe nimeni de furt. Omul decide. ID-uri pseudonimizate, jurnal pentru fiecare decizie, notă despre EU AI Act (infrastructura critică e "high risk").
- Costuri: modelul rulează pe CPU, în câteva secunde. Se potrivește cu platforma lor (S3, Spark): scorare zilnică după vârful de date de la 4 dimineața.
- În plus: manipularea contoarelor se leagă de numele echipei, CyberPunks.
- Riscul: repo-ul GitHub cu setul SGCC nu are licență explicită. Folosim datele din Londra plus sintetice ca bază și SGCC doar ca validare, cu sursa citată. Sau luăm copia de pe Kaggle, dacă are licență.

## B. Furtună în 24 de ore: risc de avarii și echipe trimise din timp

- Problema PPC: reziliența rețelei (spusă de Daniel Albu), indicatorii de întreruperi SAIDI 35 de minute și SAIFI 0,90 în S1 2026, sistemul nou de gestionare a echipelor (WFM).
- Model: câți clienți rămân fără curent pe zonă în următoarele 24 de ore, din prognoza meteo. Baseline: persistență sau media istorică.
- Agent: mută echipele în zonele cu risc înainte de furtună, în limita capacității, trimite alerte, face raport.
- Date: EAGLE-I (întreruperi în SUA pe comitat, la 15 minute, 2014-2024) și vremea istorică de la Open-Meteo. Slăbiciunea: datele sunt din SUA. Pentru demo am mapa rezultatele pe județele din Muntenia, Banat și Dobrogea, cu date sintetice etichetate ca atare.

## C. Prosumatorii ridică tensiunea: posturi de transformare în pericol mâine (alternativa, mai originală)

Găsită la a doua căutare, 7 nov. 2026.

- Problema: la 30 iunie 2026, ANRE avea 359.378 de prosumatori racordați (324.535 persoane fizice, 34.843 firme), cu 4.019 MW instalați și 127.084 cu baterii (ANRE prin News.ro, verificat de firul C pe 7 nov.). La prânz, energia injectată ridică tensiunea în rețeaua de joasă tensiune cu până la 10%, iar invertoarele se opresc singure. Știrile PRO TV spun că zeci de mii de panouri se deconectează automat la orele de vârf. Prosumatorii nu sunt împrăștiați uniform: la un alt distribuitor, peste 40% din posturi nu au niciun prosumator, iar altele sunt aglomerate. Guvernul pregătește condiții mai stricte de racordare. Rețele Electrice a pomenit prosumatorii explicit la platforma GIS nouă, iar Daniel Albu a spus că rețeaua devine bidirecțională. Problema nu e în portofoliul AI al PPC.
- Perceive: prognoza meteo pe mâine (radiație, temperatură, de la Open-Meteo), câți prosumatori și ce putere are fiecare post, consumul tipic pe zi și oră.
- Estimate: modelul nostru prezice, pentru fiecare post de transformare, tensiunea maximă și încărcarea de mâine, pe ore, cu interval de încredere.
- Decide: pragul e cel din standard (tensiune în ±10% față de nominal, deci peste 1,10 în unități relative înseamnă problemă). Decide pentru fiecare post: nimic, prevenție sau intervenție, după risc și încredere.
- Act, pe trei firme PPC: (1) Rețele Electrice primește lista posturilor cu risc pe mâine și reglajul recomandat (priza transformatorului, setările invertoarelor). (2) PPC Energy le trimite prosumatorilor de pe acele posturi un mesaj: "mâine între 11 și 15 pornește mașina de spălat și boilerul", legat de oferta Ore Smart, așa că energia se consumă local. (3) Pentru planul de investiții: clasamentul posturilor de modernizat și un răspuns la cererile noi de racordare (aprobat, aprobat cu limită de injecție sau studiu).
- Date: SimBench (rețele de joasă tensiune de referință, cu profile reale de consum și fotovoltaic la 15 minute pe un an, licență ODbL pentru date, cod BSD, pachet Python `simbench` 1.6.3) plus pandapower (calcul de circulație de puteri, versiunea 3.5.6). Generăm scenarii cu tot mai mulți prosumatori, calculăm tensiunile cu fizica rețelei, iar rezultatele devin etichete. Vremea din România vine de la Open-Meteo și PVGIS.
- Baseline: o regulă simplă, puterea prosumatorilor raportată la puterea transformatorului. Model: gradient boosting care învață să înlocuiască simularea (milisecunde în loc de minute). Test: pe o rețea pe care modelul n-a văzut-o deloc, ca să arătăm că merge pe posturi noi.
- Robustețe: prognoza meteo incertă (zile înnorate parțial), date lipsă de la contoare, rețele cu structură nouă.
- Explicabilitate: "postul 1432: 38 de prosumatori, 410 kW, duminică cu soare 900 W/m² și consum mic, deci 1,12 la ora 13".
- Etică: nu deconectăm pe nimeni automat. Agentul recomandă, dispecerul decide. Mesajele către clienți sunt opționale.
- Costuri: modelul rulează pe CPU, iar simularea grea se face o singură dată, offline.
- Riscul: echipa trebuie să învețe repede pandapower. Simularea pe un an întreg poate dura zeci de minute, deci începem cu o singură rețea mică.

## D. Baterie și parc solar la prețuri negative

Găsită la a doua căutare, 7 nov. 2026.

- Problema: în 2026, România are tot mai des prețuri negative la prânz (de exemplu 27 aprilie, ore întregi negative) și vârfuri mari seara (29 iunie: medie de 224 €/MWh, peste 800 €/MWh seara). Unele parcuri solare se opresc la prețuri negative. PPC are baterii în România (Corugea 40 MW / 80 MWh, Fântânele-Vest), un JV de 1,5 GW de baterii cu Metlen și peste 1,6 GW de regenerabile. Portofoliul lor AI prognozează consumul și producția, dar nu prețul și nici decizia bateriei.
- Perceive: prețurile din ultimele zile, prognoza meteo, producția solară și eoliană din România.
- Estimate: modelul nostru prognozează prețul pe mâine pe fiecare interval, cu interval de încredere (cuantile).
- Decide: planul de încărcare și descărcare, cu limitele bateriei (putere, capacitate, cicluri pe zi, randament) și cu decizia de a opri parcul când prețul e negativ. Când încrederea e mică, ia varianta prudentă.
- Act: planul pe mâine, alerte pentru intervalele cu risc, raport cu banii câștigați față de strategia simplă.
- Date: Energy-Charts (Fraunhofer ISE), API fără cheie: prețuri pentru România la 15 minute în 2026 (orare în 2024) și producția pe tipuri (eolian, solar, baterii). Verificat pe 7 nov. Licența spune "private and internal use only", deci e bine pentru un hackathon, dar trebuie spus. Alternativ, ENTSO-E cu token.
- Baseline: prețul de ieri la aceeași oră. Strategia simplă pentru baterie: încarcă la prânz, descarcă seara.
- Robustețe: vârfuri de preț, zile cu prețuri negative, date lipsă.
- Explicabilitate: "încarc la 13:00 pentru că prognoza dă -5 €/MWh, cu soare puternic și consum mic de weekend".
- Riscul: prognoza prețului e grea, iar trading-ul e domeniul PPC Trading, care poate pune întrebări grele.
- Notă: pe 27 aprilie, Energy-Charts arată un minim de -1 €/MWh, iar presa a scris -97,5 €/MWh. De verificat înainte să folosim cifra în prezentare.

## E. Parc eolian: prognoză și decizie

- PPC are deja prognoza producției eoliene în dezvoltare (proiectul 08) și Smart Sentry în producție. E credibil, dar ne compară cu munca lor.
- Agent: ajustarea poziției pe piața intraday, programarea mentenanței în ferestrele fără vânt, încărcarea bateriilor.
- Date: SCADA de turbine publice (de exemplu setul de pe Kaggle din Turcia, la 10 minute), vremea istorică de la Open-Meteo, PVGIS pentru solar.

## F. Stații de încărcare PPC Blue: cerere și defecte

- Model: cererea pe stație și oră, sau detectarea stațiilor defecte din sesiuni scurte sau eșuate.
- Agent: prioritizează mentenanța, recomandă prețuri mai mici la vârful solar, alertează.
- Date: ACN-Data (Caltech, cont gratuit), datele deschise din Palo Alto, Boulder sau Dundee.

## G. PPC Energy: neplată sau consum mutat în orele ieftine

- Riscul de neplată completează AI Claims Agent, dar nu există date publice de facturare la energie, deci ar fi doar sintetice.
- Programarea consumului în orele Ore Smart se suprapune cu myEnergy Coach.

## Propunerile unui coleg din echipă (7 nov., în jur de 12:15)

Din două capturi de ecran trimise de Teo (textul colegului e parțial, capturile încep și se termină la mijloc). Teo a spus că sună foarte bine. Evaluarea de mai jos e a mea.

### H. BlueFlow (PPC Blue): stația pare liberă acum, dar va fi plină când ajungi

- Ideea colegului: modelul estimează congestia la o stație în ora următoare, cu probabilitate și incertitudine. Motorul de decizie găsește o stație alternativă cu locuri libere și verifică dacă redirecționarea merită. Agentul creează o alertă operațională și o notificare cu stația recomandată. Operatorul vede motivul predicției. Demo: "Stația A, 3 din 4 puncte ocupate, 87% probabilitate de ocupare completă" (valoare ilustrativă). Colegul notează corect că ar fi "prototip validat pe date externe, nu model calibrat pentru PPC".
- Date (verificat prin căutare, 7 nov.): UrbanEV, Shenzhen, 1.682 de stații publice, 24.798 de puncte de încărcare, ocupare orară sept. 2022-feb. 2023, cu vreme, prețuri și distanțe între zone. Licență CC0. GitHub: https://github.com/IntelligentSystemsLab/UrbanEV, Dryad: https://datadryad.org/dataset/doi:10.5061/dryad.np5hqc04z, articol: Scientific Data 12, 523 (2025), DOI 10.1038/s41597-025-04874-4. Alternative: ACN-Data (Caltech), Palo Alto.
- Puncte tari: cele mai bune date publice dintre toate variantele (licență liberă, multe stații, ocupare gata calculată). Demo ușor de înțeles în 5 minute. PDF-ul PPC pomenește explicit sesiunile de încărcare și locațiile stațiilor.
- Puncte slabe: e o funcție pentru șoferi, mai mult decât o decizie zilnică a colegilor PPC, iar PDF-ul pune accent pe deciziile colegilor. În România sunt mai puține mașini electrice decât în Shenzhen, deci juriul poate întreba cât de des apare congestia la PPC Blue. Decizia "trimite șoferul la altă stație" e subțire pentru cele 25 de puncte ale agentului.
- Cum o facem mai puternică: o mutăm spre operatorul PPC Blue. Agentul decide reduceri de preț în orele aglomerate (UrbanEV are prețuri), programează mentenanța stațiilor defecte în orele cu cerere mică, ordonată după venitul pierdut, și ține cont de puterea maximă a racordului fiecărei stații.

### I. Solar Recovery (PPC Renewables): pierderi neexplicate în parcurile solare

- Ideea colegului: modelul învață legătura dintre radiație, temperatură, poziția soarelui și producție. Agentul compară producția estimată cu cea reală, calculează energia pierdută și pregătește tichete de mentenanță, ordonate după valoarea recuperabilă. Pentru echipele de operare și mentenanță ale parcurilor. Riscul, spus de coleg: PPC are deja Smart Sentry, deci diferența trebuie să vină din deciziile economice.
- Date: NREL PVDAQ (multe sisteme fotovoltaice, cu senzori meteo, licență CC BY), un set cu defecte de umbrire etichetate (acoperiș de 4 kW din Réunion, Data in Brief 2023, pe Zenodo), PVGIS și Open-Meteo. Defectele se pot și injecta sintetic.
- Evaluare: structura e aceeași ca la A (anomalie, apoi lucrări ordonate pentru echipe cu capacitate limitată) și se potrivește cu PDF-ul ("ce echipamente riscă să se defecteze", "SCADA de la invertoare"). Riscul real e suprapunerea cu Smart Sentry.

### J. FlexShift (PPC Energie): ce aparate programezi și când

- Ideea colegului: modelul estimează profilul de consum, agentul propune sau programează în simulare un program mai ieftin pe tarifele diferențiate.
- Evaluare: se suprapune cu myEnergy Coach și cu ofertele Ore Smart, pe care PPC le are deja. Relevanță mai mică.

### Ordinea mea după propuneri

1. A (contoare): cea mai apropiată de exemplele din PDF.
2. I (Solar Recovery) și H (BlueFlow, varianta pentru operator), apropiate. H are cele mai bune date și cel mai ușor demo. I are relevanța mai mare.
3. C (prosumatori): cea mai originală, dar cea mai grea tehnic.

## Lecții de aplicat oricare ar fi direcția

- Codul și modelul nostru decid, LLM-ul doar formulează (lecția R Systems, cerința PPC).
- Împărțirea train / test pe timp, ca să nu "vadă viitorul".
- Fiecare decizie are prag justificat, încredere și explicație, și ajunge în jurnal.
- Demo de 5 minute: o zi din viața agentului, de la date la lista de acțiuni, cu un caz explicat până la capăt.
