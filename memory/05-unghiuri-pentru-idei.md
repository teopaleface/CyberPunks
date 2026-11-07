# Direcții posibile, legate de problemele PPC

Nu e o decizie. Tema reală vine la deschidere. Lista asta ne ajută să recunoaștem repede ce vrea PPC și ce date putem folosi. Pentru fiecare: problema lor, ce am putea construi în 24 de ore, ce date avem.

## 1. Consum mutat în orele ieftine (Ore Smart)

- Problema lor: au tarife dinamice (0,98 față de 1,56 lei/kWh) și vor clienți care își mută consumul când produc regenerabilele.
- Demo: un planificator care spune "pornește mașina de spălat sâmbătă la 12" și arată câți lei economisești pe lună, pe baza curbei de consum la 15 minute.
- Date: curbe sintetice la 15 minute, prețurile Ore Smart+, producția solară de la Transelectrica.
- Atenție: myEnergy Coach există deja. Trebuie să facem altceva decât el (de exemplu, programare automată, nu doar sfaturi).

## 2. Energie plus electrocasnice (Flanco)

- Problema lor: au cumpărat Flanco pe 3 nov. 2026 și vor să vândă energie și aparate împreună, ca în Grecia.
- Demo: din consumul clientului, aplicația vede că frigiderul vechi costă X lei pe an și propune un model din Flanco care se amortizează în N luni.
- Date: consum sintetic, consum tipic pe aparat, prețuri publice de pe site-ul Flanco.
- De ce contează: e știre de acum 4 zile. Juriul PPC sigur se gândește la asta.

## 3. Prognoza producției din regenerabile

- Problema lor: portofoliu mare de eolian și solar, care produce intermitent.
- Demo: prognoză pe 24-48 de ore pentru un parc eolian sau solar din vreme, comparată cu producția reală din România.
- Date: Open-Meteo (vânt, radiație), Transelectrica (producție reală eoliană și solară la nivel de țară).

## 4. Baterii: când încarci și când descarci

- Problema lor: construiesc baterii mari (Corugea 40 MW / 80 MWh, JV cu Metlen de 1,5 GW).
- Demo: optimizator care decide orele de încărcare și descărcare din prețurile PZU și prognoza solară, cu profitul estimat.
- Date: prețuri PZU (ENTSO-E, dacă primim token; altfel fișierele OPCOM), Open-Meteo.

## 5. Rețea: avarii și mentenanță

- Problema lor: mentenanță predictivă, inspecții cu drone, rețea bidirecțională din cauza prosumatorilor, reziliență.
- Demo: hartă cu zonele de risc din rețea, din vreme (vânt, gheață, căldură) și vârsta echipamentelor. Sau detectarea defectelor pe imagini cu izolatori.
- Date: Open-Meteo, seturi publice de imagini (de căutat), date de rețea sintetice.
- Riscul: fără date reale de la Rețele Electrice, demo-ul poate părea fals. Merge doar dacă PPC dă date.

## 6. Încărcare mașini electrice (PPC blue)

- Problema lor: peste 1.400 de puncte în România, țintă 2.000. Partenerii sunt Dedeman, Penny, Selgros, OSCAR pe A7, aeroportul Otopeni.
- Demo: programare inteligentă a încărcării în orele cu mult solar, sau recomandare de stație după traseu și preț.

## 7. Aplicația myPPC și relația cu clienții

- Problema lor: note mici după migrarea din iulie (3,1 și 2,3), plângeri la logare și facturi lipsă. KPI-urile sunt adopția digitală și factura electronică. Pierd cotă de piață (16% la 14%).
- Demo: asistent care explică factura în cuvinte simple ("de ce am plătit mai mult luna asta"), sau un flux de înscriere la factura electronică în 3 pași.
- În plus: PPC folosește deja Claude Enterprise intern, deci o soluție pe Claude le e familiară.

## 8. Centre de date și AI cu energie curată

- Problema lor: construiesc un centru de date de 300 MW pentru AWS. Stassis vrea ca AI să nu crească factura clienților.
- Demo: un planificator care mută sarcinile de calcul în orele cu energie verde și ieftină, cu CO2 economisit.
- Date: Transelectrica (mixul de producție), Electricity Maps.

## 9. Securitate cibernetică (se potrivește cu numele echipei)

- Problema lor: platforma GIS nouă cere "cele mai avansate standarde de securitate cibernetică". Rețeaua are tot mai multe puncte de telecontrol și contoare conectate.
- Demo: detectarea anomaliilor în datele de la contoare (furt de energie, contoare defecte, atac), care leagă și "detectarea pierderilor" pomenită de Stassis.

## Ce câștigă la juriu (din regulament și din ce știm despre PPC)

- Maxim 10 minute de prezentare. Demo care merge, pe date reale sau clar etichetate ca sintetice.
- Legătura directă cu o problemă pe care PPC a spus-o public, cu cifrele lor.
- O cifră de impact: lei economisiți, MW, minute de avarie evitate.
- Repo-ul pe GitHub, cu acces pentru juriu.
