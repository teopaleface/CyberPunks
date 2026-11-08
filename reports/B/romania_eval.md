# Modelul B pe avarii reale din România (Powercut, oct.–nov. 2026)

Rulat pe 7 noiembrie 2026 cu `python -m cyberpunks.b_furtuna.romania_eval`. Cifrele vin din `reports/B/romania_eval.json`. Datele sunt **reale, nu sintetice**. Datele brute și tabelul pe zone și zile rămân locale: licența RER din Powercut nu e precizată.

## Ce s-a testat

- **Modelul**: `models/release/b_model.joblib` (`b-lgbm@409ba59`, antrenat pe SUA 2023–2024, prag 16%), fără reantrenare.
- **Avariile**: arhiva Powercut pe 30 de zile (feed-ul Rețele Electrice). Am păstrat 5.233 de incidente neplanificate cu număr de clienți. Colectarea începe pe 17 oct., deci am evaluat 20 de zile întregi, **18 oct.–6 nov. 2026**, pe 26 de zone. Rezultă 520 de zone-zile.
- **Eticheta**, ca la antrenare: vârful clienților fără curent în același timp ajunge la cel puțin 1% din clienții zonei. Fiecare incident e atribuit zonei cu centrul cel mai apropiat. Distanța mediană e de 9 km, iar p95 de 32 km. Aceasta este o aproximare.
- **Vremea**: arhiva Open-Meteo, aceeași sursă ca la antrenare. Am verificat separat și Historical Forecast.
- **Repere de comparație**: regula pe rafală (scorul e rafala și pragul e 70 km/h), mărimea zonei, rata zonei din celelalte săptămâni (folosește istoric românesc pe care modelul nu îl are) și un scor aleator. Intervalele de încredere de 95% vin din bootstrap pe zile, cu 2.000 de eșantioane.

## Problema principală: eticheta

Powercut nu măsoară același lucru ca EAGLE-I. La 836 de incidente durata depășește 72 de ore, iar p95 e de 277 de ore. Probabil sunt incidente rămase deschise în feed. Cu eticheta brută, 58% din zone-zile ar fi „eveniment”, deși fereastra a fost liniștită: rafala maximă a fost de 71 km/h, iar o singură zonă-zi a trecut de 70 km/h. De aceea am raportat și variante mai robuste. Varianta cea mai curată este **„incidente noi ≥ 1%”**: suma clienților din incidentele care încep în ziua respectivă. Ea nu depinde de orele de încheiere.

## Rezultate (vremea din arhivă)

| Etichetă | Prevalență | PR-AUC model [IC 95%] | PR-AUC rafală | PR-AUC rata zonei | ROC-AUC model | Brier model / constant | ECE |
|---|---|---|---|---|---|---|---|
| Vârf simultan ≥1% (brut) | 0,583 | 0,656 [0,595–0,712] | 0,631 | 0,818 | 0,566 | 0,507 / 0,243 | 0,517 |
| Vârf, durată plafonată la 72 h | 0,346 | 0,371 [0,315–0,442] | 0,374 | 0,470 | 0,503 | 0,306 / 0,226 | 0,282 |
| Vârf, durată plafonată la 24 h | 0,246 | 0,272 [0,225–0,332] | 0,282 | 0,304 | 0,510 | 0,219 / 0,186 | 0,185 |
| **Incidente noi ≥1%** | **0,190** | **0,214 [0,165–0,278]** | **0,222** | **0,220** | **0,507** | **0,171 / 0,154** | **0,133** |
| Incidente noi ≥2% | 0,106 | 0,128 [0,087–0,174] | 0,147 | 0,122 | 0,518 | 0,098 / 0,095 | 0,052 |

Diferența de PR-AUC dintre model și rafală, cu bootstrap pereche: **+0,023 [−0,008; +0,059]** pe eticheta brută și **−0,011 [−0,040; +0,021]** pe incidente noi. În ambele cazuri intervalul conține zero.

**La pragul de 16%**, pe incidentele noi ≥1%, modelul dă 21 de alerte din 520. Precizia e 0,24, recall-ul 0,05 și F1 0,08. Regula de 70 km/h dă o singură alertă, cu F1 0,02. Pragul cu cel mai bun F1 pe aceste date e 5%, cu F1 0,26. Această cifră e optimistă, pentru că pragul a fost ales pe aceleași date.

**Calibrare**: media prezisă e 0,075. Frecvența observată e 0,19 pe incidente noi și 0,58 pe eticheta brută. Modelul subestimează avariile de zi cu zi din România, mai ales sub probabilitatea de 10%.

**Cu echipe puține** (3 zone pe zi, incidente noi), modelul prinde 5,8% din clienții afectați, regula pe rafală 9,1%, alegerea aleatoare 16,6%, iar oracolul 85%.

**Cuantilele în zilele cu eveniment** (incidente noi): acoperirea P10–P90 e de 79%, cu ținta de 80%. Vârful median observat e de 2,2%, iar P50 median prezis e de 1,9%. MAE pentru P50 e de 2,1 puncte procentuale.

**Historical Forecast** în loc de arhivă: PR-AUC scade puțin, de la 0,656 la 0,637 pe eticheta brută. Diferența nu e importantă.

## Cazuri confirmate de furtună (vremea din arhivă)

| Ziua | Județ | Ce s-a întâmplat | Probabilitatea modelului pe zone | Peste 16%? |
|---|---|---|---|---|
| 7 iul. 2025 | Caraș-Severin | furtună la Reșița și Caransebeș | 0,36 / 0,36 / 0,36 | da |
| 8 iul. 2025 | Caraș-Severin | cod roșu, rafale de 90–120 km/h | 0,50 / 0,62 / 0,28 | da |
| 8 iul. 2025 | Timiș | circa 40.000 de consumatori afectați cumulat | 0,21 / 0,27 / 0,13 | da (2 din 3 zone) |
| 5 ian. 2026 | Hunedoara | circa 5.500 de clienți (≈2,5% din județ) | 0,07 / 0,06 / 0,04 | **nu** |

## Ce înseamnă

1. **Pe avariile obișnuite din România modelul nu e mai bun decât întâmplarea.** ROC-AUC e în jur de 0,50–0,57, iar PR-AUC e foarte aproape de prevalență, de rafala simplă și de rata zonei. Fereastra a fost însă fără furtuni, deci testul măsoară avariile de zi cu zi, pentru care modelul nu a fost construit. **Acest test nu poate confirma și nici infirma performanța pe furtuni.**
2. **Pe furtunile reale verificate**, modelul trece pragul în episodul din Banat din iulie 2025. Ratează episodul de iarnă din Hunedoara, unde rafalele din arhivă au fost de 25–37 km/h. E probabil un eveniment cu zăpadă sau chiciură pe care variabilele zilnice nu îl prind.
3. **Calibrarea nu se transferă din SUA**: probabilitățile sunt prea mici pentru România. Înainte să folosim cifrele în lei, avem nevoie de recalibrare pe date românești.
4. **20 de zone-zile ies din intervalul de antrenare**, toate la București (mărime și densitate).
5. **Ce ar ajuta**: o arhivă Powercut mai lungă, care să prindă furtuni de primăvară și vară, cu descărcare zilnică începând de acum. Mai sunt necesare filtrarea incidentelor „blocate”, ca la EAGLE-I, granițele reale ale zonelor (OSM sau SIRUTA) și recalibrarea izotonică pe zilele românești, cu validare pe săptămâni.
