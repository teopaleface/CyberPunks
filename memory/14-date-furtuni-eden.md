# Date pentru testarea furtunilor pe Eden

7 noiembrie 2026. Datele descărcate se află local în `data/raw/B/romania/` și sunt ignorate de Git. Sunt date reale sau prognoze, nu date sintetice. Manifestele din directoare indică URL-urile, fișierele și erorile.

- Powercut: instantaneu al arhivei de 30 de zile și datele curente, la 7 noiembrie. Arhiva include mai multe țări. Metadatele nu precizează licența datelor RER.
- DEER: 22 de rapoarte PDF cu indicatori, extrase din pagina de date de consum. Distribuție Oltenia: tabelul D.1 pentru 2022. PDF-urile trebuie extrase și verificate înainte de testare.
- ANM: 480 de arhive climatice, 160 de stații pentru fiecare din 2024, 2025 și 2026, validate ca ZIP. Mai există instantaneu cu stațiile curente și modelul WRF `M650.nc`.
- Open-Meteo: 52 de fișiere Previous Runs pentru 26 de zone, pentru intervalele 6–10 iulie 2025 și 4–6 ianuarie 2026, și 52 de fișiere ECMWF Single Runs pentru inițializările din 7 iulie 2025 și 4 ianuarie 2026 la 12 UTC. Arhiva IFS include hindcast, iar Previous Runs are orizont de 24 de ore față de fiecare oră. Datele includ doar rafale și precipitații.
- România OpenStreetMap, extras Geofabrik din 6 noiembrie 2026, SIRUTA 2025 și un index NOAA GFS. Indexul NOAA nu conține datele GRIB.
- Nu au fost descărcate seriile complete ERA5, CERRA, NOAA GFS și ESWD. Două resurse RER și pagina Oltenia 2025 au eșuat la descărcare din cauza redirectărilor sau certificatului. Datele nu au fost încă unite într-un set de antrenare ori de test.
