# Direcții de proiect, după tema anunțată

Rescris pe 7 nov. 2026, după anunțarea temei (`07-tema-ppc.md`). Varianta de dinainte de temă e în istoricul git. Încă nu e o decizie: echipa alege, iar alegerea intră în `journal.md`.

Filtrul: model ML propriu cu test separat și baseline, agent care face acțiuni, date publice sau sintetice, relevanță credibilă pentru PPC. Am evitat să copiem proiecte pe care PPC le are deja în producție (lista în `08-ppc-workshop-ai.md`).

## Comparație rapidă

| Direcție | Firma PPC | Relevanță PPC (25) | Calitate ML (25) | Agent (25) | Robustețe (10) | Date publice |
|---|---|---|---|---|---|---|
| A. Contoare defecte sau manipulate, plus echipele de verificare | Rețele Electrice | Foarte bună: PPC a spus că e următorul pas | Bună: etichete reale și sintetice | Foarte bună: capacitate de echipe, cost pe vizită | Foarte bună: datele lipsă sunt chiar semnalul | Da |
| B. Furtună în 24 de ore: risc de avarii și echipe trimise din timp | Rețele Electrice | Bună: reziliență, SAIDI/SAIFI | Bună | Foarte bună | Foarte bună: evenimente rare | Da, dar din SUA |
| C. Parc eolian: prognoză și decizie | PPC Renewables | Medie: PPC are deja proiectul în dezvoltare | Foarte bună | Medie | Bună | Da |
| D. Stații de încărcare: cerere și defecte | PPC Blue | Medie | Bună | Bună | Medie | Da, din SUA și UK |
| E. Risc de neplată sau programarea consumului în orele ieftine | PPC Energy | Medie: suprapunere cu AI Claims Agent și myEnergy Coach | Slabă spre medie: doar date sintetice sau din altă țară | Bună | Medie | Parțial |

## A. Contoare defecte sau manipulate, plus echipele de verificare (recomandată)

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

## C. Parc eolian: prognoză și decizie

- PPC are deja prognoza producției eoliene în dezvoltare (proiectul 08) și Smart Sentry în producție. E credibil, dar ne compară cu munca lor.
- Agent: ajustarea poziției pe piața intraday, programarea mentenanței în ferestrele fără vânt, încărcarea bateriilor.
- Date: SCADA de turbine publice (de exemplu setul de pe Kaggle din Turcia, la 10 minute), vremea istorică de la Open-Meteo, PVGIS pentru solar.

## D. Stații de încărcare PPC Blue: cerere și defecte

- Model: cererea pe stație și oră, sau detectarea stațiilor defecte din sesiuni scurte sau eșuate.
- Agent: prioritizează mentenanța, recomandă prețuri mai mici la vârful solar, alertează.
- Date: ACN-Data (Caltech, cont gratuit), datele deschise din Palo Alto, Boulder sau Dundee.

## E. PPC Energy: neplată sau consum mutat în orele ieftine

- Riscul de neplată completează AI Claims Agent, dar nu există date publice de facturare la energie, deci ar fi doar sintetice.
- Programarea consumului în orele Ore Smart se suprapune cu myEnergy Coach.

## Lecții de aplicat oricare ar fi direcția

- Codul și modelul nostru decid, LLM-ul doar formulează (lecția R Systems, cerința PPC).
- Împărțirea train / test pe timp, ca să nu "vadă viitorul".
- Fiecare decizie are prag justificat, încredere și explicație, și ajunge în jurnal.
- Demo de 5 minute: o zi din viața agentului, de la date la lista de acțiuni, cu un caz explicat până la capăt.
