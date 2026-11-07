# Planul pentru marți 08.07.2025

Scenariu: `demo-vara`. Plan `PLAN-demo-vara-20250708-172556-fd43`, generat la 2026-11-07 17:25 de `planner@0.1.0+a23ffdb`.
Activele și echipele din demo sunt sintetice, plasate pe hartă reală. Nimic nu a fost trimis în afară.

## Pe scurt

- Lucrări primite: 689 (689 valide, 0 în carantină).
- În trasee: 20, cu 8 echipe și 291,8 km; valoare așteptată 71.803 lei.
- Citiri la distanță: 504. Mesaje (demo): 48. La om: 25. Amânate: 122.

## Contextul zilei

- Contoare și posturi: 630 lucrări; 17 în trasee, 504 verificări de la distanță sau corecții în birou, 17 la dispecer.
- Furtună: 26 zone analizate, cel mai mare risc 58%; 3 echipe trimise din timp.
- Tensiune: 33 posturi cu risc din 300 (soare pe panou până la 956 W/m² la prânz, 35 °C): 15 posturi rămân la urmărire (15 sub prag sau sub limită chiar și în scenariul pesimist), 18 primesc mesaje către prosumatori, 0 primesc echipă.

## Sursele

| Sursă | Stare | De unde | Valide | Respinse |
|---|---|---|---|---|
| A (contoare) | ok | modelul nostru | 532 | 0 |
| A, bilanț pe post | ok | modelul nostru | 98 | 0 |
| B (furtună) | ok | modelul nostru | 26 | 0 |
| C (tensiune) | ok | modelul nostru | 33 | 0 |

## Întâi: verificări de la distanță și corecții în birou

- `A-20250708-PT-1255` (`R-BILANT-REMOTE`): Bilanțul postului PT-1255: contor defect sau manipulat la un client de sub post (probabilitate 96%), lipsă peste normal ~1.753 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-PT-1201` (`R-BILANT-REMOTE`): Bilanțul postului PT-1201: contor defect sau manipulat la un client de sub post (probabilitate 98%), lipsă peste normal ~1.287 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-MTR-011050` (`R-CAPACITY-REMOTE`): Vizita merita (3.218 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-010957` (`R-CAPACITY-REMOTE`): Vizita merita (2.927 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-PT-1293` (`R-SAFETY-OVER-CAP`): Risc pentru siguranța oamenilor (La post lipsesc ~52.7 kWh/zi peste pierderea normală (5.7% din energie), 14 din 14 zile peste P90, scor 96%): intră primul în traseu, oricare ar fi costul. Azi sunt deja 12 cazuri de siguranță obligatorii (cota zilei, cele cu scorul cel mai mare): acesta păstrează prioritatea triplă, fără să fie obligatoriu. Nu a încăput în turele de mâine: citire la distanță acum, apoi primul în planul următor.
- `A-20250708-PT-1282` (`R-BILANT-REMOTE`): Bilanțul postului PT-1282: contor defect sau manipulat la un client de sub post (probabilitate 100%), lipsă peste normal ~990 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-PT-1076` (`R-BILANT-REMOTE`): Bilanțul postului PT-1076: contor defect sau manipulat la un client de sub post (probabilitate 91%), lipsă peste normal ~1.063 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-MTR-013202` (`R-CAPACITY-REMOTE`): Vizita merita (2.006 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-PT-1147` (`R-BILANT-REMOTE`): Bilanțul postului PT-1147: contor defect sau manipulat la un client de sub post (probabilitate 92%), lipsă peste normal ~816 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-MTR-011600` (`R-CAPACITY-REMOTE`): Vizita merita (1.712 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-PT-1105` (`R-BILANT-REMOTE`): Bilanțul postului PT-1105: contor defect sau manipulat la un client de sub post (probabilitate 98%), lipsă peste normal ~648 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-PT-1041` (`R-BILANT-REMOTE`): Bilanțul postului PT-1041: contor defect sau manipulat la un client de sub post (probabilitate 99%), lipsă peste normal ~624 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-MTR-005227` (`R-CAPACITY-REMOTE`): Vizita merita (1.499 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-PT-1029` (`R-BILANT-REMOTE`): Bilanțul postului PT-1029: contor defect sau manipulat la un client de sub post (probabilitate 100%), lipsă peste normal ~591 lei pe lună. Întâi verificări de la distanță (2 lei): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.
- `A-20250708-MTR-011678` (`R-CAPACITY-REMOTE`): Vizita merita (1.429 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-001432` (`R-CAPACITY-REMOTE`): Vizita merita (1.410 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-012854` (`R-CAPACITY-REMOTE`): Vizita merita (1.342 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-009079` (`R-CAPACITY-REMOTE`): Vizita merita (1.276 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-012444` (`R-CAPACITY-REMOTE`): Vizita merita (1.299 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-005569` (`R-CAPACITY-REMOTE`): Vizita merita (1.223 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-010959` (`R-CAPACITY-REMOTE`): Vizita merita (1.200 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-MTR-011508` (`R-CAPACITY-REMOTE`): Vizita merita (1.190 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- `A-20250708-PT-1097` (`R-SAFETY-OVER-CAP`): Risc pentru siguranța oamenilor (La post lipsesc ~21.6 kWh/zi peste pierderea normală (3.0% din energie), 14 din 14 zile peste P90, scor 98%): intră primul în traseu, oricare ar fi costul. Azi sunt deja 12 cazuri de siguranță obligatorii (cota zilei, cele cu scorul cel mai mare): acesta păstrează prioritatea triplă, fără să fie obligatoriu. Nu a încăput în turele de mâine: citire la distanță acum, apoi primul în planul următor.
- `A-20250708-MTR-007525` (`R-SAFETY-OVER-CAP`): Risc pentru siguranța oamenilor (98% din intervale repetă exact valoarea anterioară, scor 96%): intră primul în traseu, oricare ar fi costul. Azi sunt deja 12 cazuri de siguranță obligatorii (cota zilei, cele cu scorul cel mai mare): acesta păstrează prioritatea triplă, fără să fie obligatoriu. Nu a încăput în turele de mâine: citire la distanță acum, apoi primul în planul următor.
- `A-20250708-MTR-004609` (`R-CAPACITY-REMOTE`): Vizita merita (1.043 lei valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi (2 lei), vizita în planul următor.
- … și încă 479 (toate sunt în `plan.json` și în consolă).

## Lista pe echipe, după lei pe oră de lucru

| Rang | Lucrare | Lei pe oră | Decizie | Echipa |
|---|---|---|---|---|
| 1 | `A-20250708-PT-1081` | 1.534 | în traseu | E-BE-1 |
| 2 | `A-20250708-PT-1132` | 1.487 | în traseu | E-BE-1 |
| 3 | `A-20250708-PT-1114` | 1.151 | în traseu | E-BV-2 |
| 4 | `A-20250708-PT-1247` | 1.143 | în traseu | E-BE-1 |
| 5 | `A-20250708-PT-1261` | 970 | în traseu | E-BV-1 |
| 6 | `A-20250708-PT-1064` | 604 | în traseu | E-BV-1 |
| 7 | `A-20250708-PT-1195` | 574 | în traseu | E-BV-1 |
| 8 | `A-20250708-PT-1115` | 489 | în traseu | E-BV-2 |
| 9 | `A-20250708-PT-1141` | 350 | în traseu | E-BV-2 |
| 10 | `A-20250708-PT-1194` | 302 | citire la distanță | - |
| 11 | `A-20250708-MTR-005889` | 0 | în traseu | E-BV-2 |
| 12 | `A-20250708-MTR-015138` | 0 | în traseu | E-BE-1 |
| 13 | `A-20250708-PT-1269` | 5.806 | în traseu | E-BE-2 |
| 14 | `A-20250708-MTR-010957` | - | citire la distanță | - |
| 15 | `A-20250708-PT-1082` | 3.070 | în traseu | E-BV-3 |
| 16 | `A-20250708-MTR-011050` | - | citire la distanță | - |
| 17 | `A-20250708-MTR-013202` | - | citire la distanță | - |
| 18 | `A-20250708-MTR-011600` | - | citire la distanță | - |
| 19 | `A-20250708-PT-1012` | 2.028 | în traseu | E-BV-3 |
| 20 | `A-20250708-PT-1293` | 1.786 | citire la distanță | - |
| 21 | `A-20250708-MTR-005569` | - | citire la distanță | - |
| 22 | `A-20250708-PT-1155` | 1.641 | în traseu | E-BE-2 |
| 23 | `A-20250708-MTR-012444` | - | citire la distanță | - |
| 24 | `A-20250708-MTR-011508` | - | citire la distanță | - |
| 25 | `A-20250708-MTR-010959` | - | citire la distanță | - |
| 26 | `A-20250708-MTR-011678` | - | citire la distanță | - |
| 27 | `A-20250708-MTR-012854` | - | citire la distanță | - |
| 28 | `A-20250708-MTR-001432` | - | citire la distanță | - |
| 29 | `A-20250708-MTR-005227` | - | citire la distanță | - |
| 30 | `A-20250708-MTR-009079` | - | citire la distanță | - |
| 31 | `A-20250708-MTR-004609` | - | citire la distanță | - |
| 32 | `A-20250708-PT-1292` | 1.222 | amânat | - |
| 33 | `A-20250708-MTR-007525` | 1.213 | citire la distanță | - |
| 34 | `A-20250708-MTR-007153` | - | citire la distanță | - |
| 35 | `A-20250708-PT-1033` | 1.087 | amânat | - |
| 36 | `A-20250708-MTR-003279` | - | citire la distanță | - |
| 37 | `A-20250708-MTR-004011` | - | citire la distanță | - |
| 38 | `A-20250708-MTR-009261` | - | citire la distanță | - |
| 39 | `A-20250708-MTR-003577` | - | citire la distanță | - |
| 40 | `A-20250708-MTR-004141` | - | citire la distanță | - |
| 41 | `A-20250708-MTR-009172` | - | citire la distanță | - |
| 42 | `A-20250708-MTR-001909` | - | citire la distanță | - |
| 43 | `A-20250708-MTR-010265` | - | citire la distanță | - |
| 44 | `A-20250708-PT-1038` | 845 | amânat | - |
| 45 | `A-20250708-MTR-013345` | - | citire la distanță | - |
| 46 | `A-20250708-MTR-003404` | - | citire la distanță | - |
| 47 | `A-20250708-MTR-002399` | - | citire la distanță | - |
| 48 | `A-20250708-MTR-003965` | - | citire la distanță | - |
| 49 | `A-20250708-MTR-002178` | - | citire la distanță | - |
| 50 | `A-20250708-MTR-000258` | - | citire la distanță | - |

Lista o aprobă un om (consola: aprobă traseul echipei); verdictul de după vizită intră în jurnal ca etichetă pentru reantrenare.

## Traseele

### E-BV-1 (baza D-BUC-V): 4 opriri, 64,0 km, 140 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 09:00 | PT-1195, Clinceni (sintetic) | bilanț pe post | `R-SAFETY` |
| 2 | 10:45 | Contor MTR-011921, PT-1223, Domnești (sintetic) | verificare contor | `R-A-VISIT` |
| 3 | 11:39 | PT-1064, Otopeni (sintetic) | bilanț pe post | `R-SAFETY` |
| 4 | 13:45 | PT-1261, Sector 6 (sintetic) | bilanț pe post | `R-SAFETY` |

### E-BV-2 (baza D-BUC-V): 5 opriri, 42,0 km, 101 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 08:36 | Contor MTR-008597, PT-1165, Sector 6 (sintetic) | verificare contor | `R-A-VISIT` |
| 2 | 09:18 | PT-1115, Popești-Leordeni (sintetic) | bilanț pe post | `R-SAFETY` |
| 3 | 11:07 | PT-1141, Sector 3 (sintetic) | bilanț pe post | `R-SAFETY` |
| 4 | 12:46 | PT-1114, Sector 4 (sintetic) | bilanț pe post | `R-SAFETY` |
| 5 | 14:16 | Contor MTR-005889, PT-1114, Sector 4 (sintetic) | verificare contor | `R-SAFETY` |

### E-BV-3 (baza D-BUC-V): 2 opriri, 74,8 km, 142 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 09:03 | PT-1012, Mogoșoaia (sintetic) | bilanț pe post | `R-BILANT-GRID` |
| 2 | 12:07 | PT-1082, 1 Decembrie (sintetic) | bilanț pe post | `R-BILANT-GRID` |

### E-BE-1 (baza D-BUC-E): 4 opriri, 26,4 km, 72 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 08:36 | PT-1081, Sector 3 (sintetic) | bilanț pe post | `R-SAFETY` |
| 2 | 10:11 | PT-1247, Sector 3 (sintetic) | bilanț pe post | `R-SAFETY` |
| 3 | 12:07 | PT-1132, Glina (sintetic) | bilanț pe post | `R-SAFETY` |
| 4 | 13:49 | Contor MTR-015138, PT-1287, Popești-Leordeni (sintetic) | verificare contor | `R-SAFETY` |

### E-BE-2 (baza D-BUC-E): 2 opriri, 38,1 km, 90 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 08:52 | PT-1155, Sector 3 (sintetic) | bilanț pe post | `R-BILANT-GRID` |
| 2 | 11:30 | PT-1269, Afumați (sintetic) | bilanț pe post | `R-BILANT-GRID` |

### E-TM-1 (baza D-TM): 1 oprire, 0,0 km, 0 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 14:00 | Zona Timișoara (Timiș) | echipă trimisă din timp | `R-B-PREPOSITION` |

### E-AR-1 (baza D-ARD): 1 oprire, 1,9 km, 5 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 14:00 | Zona Arad (Arad) | echipă trimisă din timp | `R-B-PREPOSITION` |

### E-RS-1 (baza D-RES): 1 oprire, 44,7 km, 73 min de drum

| # | Sosire | Lucrare | Ce | Regula |
|---|---|---|---|---|
| 1 | 14:00 | Zona Oravița (Caraș-Severin) | echipă trimisă din timp | `R-B-PREPOSITION` |

## La om ("nu sunt sigur")

- `B-20250708-AR-INEU`: Încrederea modelului e mică (scor 58%). Decide un om.
- `B-20250708-TM-LUGOJ`: Rafale de 85 km/h în ziua de dinainte; 12 mm de ploaie în 48 de ore. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 6.342 clienți fără curent. Valoarea așteptată 5.457 lei depășește costul turei (3.040 lei) cu 2.417 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-AR-LIPOVA`: 16 mm de ploaie în 48 de ore; sezonul de vară: frunziș bogat, furtuni convective. Furtuna e așteptată de la 14:00 (fereastra 14:00-20:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 3.751 clienți fără curent. Valoarea așteptată 5.457 lei depășește costul turei (2.956 lei) cu 2.501 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-CS-RESITA`: 12 mm de ploaie în 48 de ore; rafale de 74 km/h în ziua de dinainte. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 4.825 clienți fără curent. Valoarea așteptată 5.457 lei depășește costul turei (2.702 lei) cu 2.755 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-CS-CARANSEBES`: Sezonul de vară: frunziș bogat, furtuni convective; 7 mm de ploaie în 48 de ore. Furtuna e așteptată de la 16:00 (fereastra 16:00-22:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 2.950 clienți fără curent. Valoarea așteptată 5.457 lei depășește costul turei (2.945 lei) cu 2.512 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-HD-DEVA`: 14 mm de ploaie în 48 de ore; sezonul de vară: frunziș bogat, furtuni convective. Furtuna e așteptată de la 17:00 (fereastra 17:00-23:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 6.737 clienți fără curent. Valoarea așteptată 5.457 lei depășește costul turei (2.719 lei) cu 2.738 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-TM-SANNICOLAU-MARE`: 12 mm de ploaie în 48 de ore; sezonul de vară: frunziș bogat, furtuni convective. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 36%; în scenariul pesimist (P90), 4.180 clienți fără curent. Valoarea așteptată 5.358 lei depășește costul turei (3.119 lei) cu 2.239 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `B-20250708-HD-BRAD`: Sezonul de vară: frunziș bogat, furtuni convective; 9 mm de ploaie în 48 de ore. Furtuna e așteptată de la 16:00 (fereastra 16:00-22:00). Probabilitate de avarii 27%; în scenariul pesimist (P90), 4.039 clienți fără curent. Valoarea așteptată 4.119 lei depășește costul turei (2.947 lei) cu 1.172 lei. Dar în regiunea Banat plafonul e de 3 echipe trimise din timp (config), iar ele merg unde aduc cea mai mare valoare netă de la baza fiecăreia: Zona Arad (Arad), Zona Oravița (Caraș-Severin), Zona Timișoara (Timiș). Cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.
- `A-20250708-PT-1182`: Modelul nu e sigur: două cauze aproape la egalitate. E risc pentru oameni: decide un om azi.
- `A-20250708-PT-1238`: Modelul nu e sigur: cauza cea mai probabilă are sub 50%. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-004149`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-003459`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-000121`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-010557`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-000963`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-004514`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-005573`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-004473`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-008329`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-005865`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-010160`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-015308`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-015211`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-009232`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.
- `A-20250708-MTR-004652`: Modelul nu e sigur: consum mic: poate fi o locuință goală sau sărăcie energetică, nu furt; un om verifică înainte să trimitem echipa. E risc pentru oameni: decide un om azi.

## Alerte

- **critical** 103 cazuri cu risc de siguranță. Intră primele în trasee, oricare ar fi costul: PT-1293, Sector 3 (sintetic), PT-1097, Sector 1 (sintetic), Contor MTR-007525, PT-1145, Sector 2 (sintetic), PT-1098, 1 Decembrie (sintetic), PT-1194, Ștefăneștii de Jos (sintetic), PT-1154, Sector 5 (sintetic) și încă 97.
- **critical** 20 cazuri de siguranță de decis azi. Modelul nu e sigur, dar e risc pentru oameni: Contor MTR-013553, PT-1255, Sector 6 (sintetic), Contor MTR-005980, PT-1116, Tunari (sintetic), Contor MTR-005165, PT-1101, Sector 4 (sintetic), PT-1182, Sector 3 (sintetic), PT-1238, Chitila (sintetic), Contor MTR-004149, PT-1081, Sector 3 (sintetic) și încă 14.
- **warning** Risc de avarii: Zona Oravița (Caraș-Severin). Rafale de vânt de 70 km/h; sezonul de vară: frunziș bogat, furtuni convective. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 50%; în scenariul pesimist (P90), 2.455 clienți fără curent.
- **warning** Risc de avarii: Zona Timișoara (Timiș). 15 mm de ploaie în 48 de ore; sezonul de vară: frunziș bogat, furtuni convective. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 43%; în scenariul pesimist (P90), 14.693 clienți fără curent.
- **warning** Risc de avarii: Zona Ineu (Arad) (model nesigur, decide dispecerul). 19 mm de ploaie în 48 de ore; rafale de 78 km/h în ziua de dinainte. Furtuna e așteptată de la 15:00 (fereastra 15:00-21:00). Probabilitate de avarii 58%; în scenariul pesimist (P90), 4.886 clienți fără curent.
- **critical** Întăriri necesare: 1 cazuri de siguranță nu încap în turele de mâine. Au primit o citire la distanță și trec primele în planul următor. Propun ore suplimentare sau echipe din alte baze: PT-1194, Ștefăneștii de Jos (sintetic).
- **critical** Întăriri necesare: 7 zone de furtună fără echipă. Plafonul de echipe trimise din timp e atins în Banat. Valoare așteptată 36.762 lei: Zona Lugoj (Timiș), Zona Sânnicolau Mare (Timiș), Zona Lipova (Arad), Zona Reșița (Caraș-Severin), Zona Caransebeș (Caraș-Severin), Zona Deva (Hunedoara) și încă 1. Propun echipe din alte regiuni sau contractori; dispecerul aprobă zonele din coada „nu sunt sigur”.
- **info** 25 lucrări așteaptă decizia unui om. Valoare așteptată totală 50.102 lei. Aprobă, respinge sau amână din consolă.
- **warning** 181 lucrări n-au încăput în turele de mâine. Valoare așteptată 144.869 lei. Ce s-a putut, trece pe citire la distanță; restul rămâne pentru planul următor.
- **info** Contextul zilei. Contoare și posturi: 630 lucrări; 17 în trasee, 504 verificări de la distanță sau corecții în birou, 17 la dispecer. Furtună: 26 zone analizate, cel mai mare risc 58%; 3 echipe trimise din timp. Tensiune: 33 posturi cu risc din 300 (soare pe panou până la 956 W/m² la prânz, 35 °C): 15 posturi rămân la urmărire (15 sub prag sau sub limită chiar și în scenariul pesimist), 18 primesc mesaje către prosumatori, 0 primesc echipă.

## Scara de soluții pentru tensiune

| Post | Aleasă | Cost | P90 înainte → după | De ce nu una mai ieftină |
|---|---|---|---|---|
| PT-1269, Afumați (sintetic) | phase_rebalance, offer_battery, export_limit | 12.439 lei | 1,177 → 1,094 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,175 pu; cu oferta de baterii singură (24 lei), tensiunea ajunge doar la 1,162 pu; cu mesajele către clienții Ore Smart și oferta de baterii (27 lei, la 10% participare), tensiunea ajunge doar la 1,160 pu |
| PT-1076, Cornetu (sintetic) | phase_rebalance, offer_battery, export_limit | 8.587 lei | 1,161 → 1,094 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,159 pu; cu oferta de baterii singură (14 lei), tensiunea ajunge doar la 1,152 pu; cu mesajele către clienții Ore Smart și oferta de baterii (17 lei, la 10% participare), tensiunea ajunge doar la 1,150 pu |
| PT-1300, Ștefăneștii de Jos (sintetic) | phase_rebalance, offer_battery, export_limit | 9.812 lei | 1,155 → 1,099 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,153 pu; cu oferta de baterii singură (22 lei), tensiunea ajunge doar la 1,145 pu; cu mesajele către clienții Ore Smart și oferta de baterii (25 lei, la 10% participare), tensiunea ajunge doar la 1,143 pu |
| PT-1147, Tunari (sintetic) | phase_rebalance, adjust_tap, offer_battery | 1.978 lei | 1,150 → 1,095 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,148 pu; cu oferta de baterii singură (22 lei), tensiunea ajunge doar la 1,138 pu; cu mesajele către clienții Ore Smart și oferta de baterii (25 lei, la 10% participare), tensiunea ajunge doar la 1,136 pu |
| PT-1131, Chitila (sintetic) | phase_rebalance, export_limit | 9.069 lei | 1,155 → 1,096 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,154 pu; cu oferta de baterii singură (18 lei), tensiunea ajunge doar la 1,145 pu; cu mesajele către clienții Ore Smart și oferta de baterii (21 lei, la 10% participare), tensiunea ajunge doar la 1,143 pu |
| PT-1075, Cornetu (sintetic) | phase_rebalance, adjust_tap, offer_battery | 1.960 lei | 1,151 → 1,099 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,149 pu; cu oferta de baterii singură (4 lei), tensiunea ajunge doar la 1,138 pu; cu mesajele către clienții Ore Smart și oferta de baterii (7 lei, la 10% participare), tensiunea ajunge doar la 1,135 pu |
| PT-1072, Voluntari (sintetic) | phase_rebalance, adjust_tap, offer_battery | 2.196 lei | 1,146 → 1,095 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,145 pu; cu oferta de baterii singură (12 lei), tensiunea ajunge doar la 1,136 pu; cu mesajele către clienții Ore Smart și oferta de baterii (15 lei, la 10% participare), tensiunea ajunge doar la 1,135 pu |
| PT-1005, Sector 1 (sintetic) | notify_customers, export_limit | 9.975 lei | 1,140 → 1,099 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,138 pu; cu oferta de baterii singură (16 lei), tensiunea ajunge doar la 1,130 pu; cu mesajele către clienții Ore Smart și oferta de baterii (19 lei, la 10% participare), tensiunea ajunge doar la 1,129 pu |
| PT-1255, Sector 6 (sintetic) | phase_rebalance, adjust_tap, offer_battery | 2.196 lei | 1,140 → 1,098 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,139 pu; cu oferta de baterii singură (12 lei), tensiunea ajunge doar la 1,133 pu; cu mesajele către clienții Ore Smart și oferta de baterii (15 lei, la 10% participare), tensiunea ajunge doar la 1,132 pu |
| PT-1119, Ștefăneștii de Jos (sintetic) | phase_rebalance, adjust_tap | 1.956 lei | 1,132 → 1,096 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,131 pu; cu oferta de baterii singură (14 lei), tensiunea ajunge doar la 1,128 pu; cu mesajele către clienții Ore Smart și oferta de baterii (17 lei, la 10% participare), tensiunea ajunge doar la 1,127 pu |
| PT-1087, Otopeni (sintetic) | phase_rebalance, adjust_tap | 1.956 lei | 1,141 → 1,100 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,138 pu; cu oferta de baterii singură (6 lei), tensiunea ajunge doar la 1,131 pu; cu mesajele către clienții Ore Smart și oferta de baterii (9 lei, la 10% participare), tensiunea ajunge doar la 1,128 pu |
| PT-1263, Sector 4 (sintetic) | adjust_tap, offer_battery | 1.658 lei | 1,134 → 1,100 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,133 pu; cu oferta de baterii singură (20 lei), tensiunea ajunge doar la 1,126 pu; cu mesajele către clienții Ore Smart și oferta de baterii (23 lei, la 10% participare), tensiunea ajunge doar la 1,125 pu |
| PT-1252, Popești-Leordeni (sintetic) | phase_rebalance, adjust_tap | 1.956 lei | 1,133 → 1,091 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,131 pu; cu oferta de baterii singură (32 lei), tensiunea ajunge doar la 1,129 pu; cu mesajele către clienții Ore Smart și oferta de baterii (35 lei, la 10% participare), tensiunea ajunge doar la 1,127 pu |
| PT-1082, 1 Decembrie (sintetic) | phase_rebalance, adjust_tap, offer_battery | 1.966 lei | 1,138 → 1,095 pu | cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,136 pu; cu oferta de baterii singură (10 lei), tensiunea ajunge doar la 1,130 pu; cu mesajele către clienții Ore Smart și oferta de baterii (13 lei, la 10% participare), tensiunea ajunge doar la 1,128 pu |

### Pentru PPC Energie: oferte de baterii

- PT-1269, Afumați (sintetic): 40 kWh, 12 prosumatori, venit estimat 9.000 lei, recuperare ~5,8 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1076, Cornetu (sintetic): 20 kWh, 7 prosumatori, venit estimat 4.500 lei, recuperare ~4,7 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1300, Ștefăneștii de Jos (sintetic): 30 kWh, 11 prosumatori, venit estimat 6.750 lei, recuperare ~3,7 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1147, Tunari (sintetic): 30 kWh, 11 prosumatori, venit estimat 6.750 lei, recuperare ~7,4 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1075, Cornetu (sintetic): 10 kWh, 2 prosumatori, venit estimat 2.250 lei, recuperare ~7,5 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1072, Voluntari (sintetic): 20 kWh, 6 prosumatori, venit estimat 4.500 lei, recuperare ~5,3 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1255, Sector 6 (sintetic): 20 kWh, 6 prosumatori, venit estimat 4.500 lei, recuperare ~6,4 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1263, Sector 4 (sintetic): 30 kWh, 10 prosumatori, venit estimat 6.750 lei, recuperare ~6,1 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).
- PT-1082, 1 Decembrie (sintetic): 20 kWh, 5 prosumatori, venit estimat 4.500 lei, recuperare ~5,2 ani. Canal: magazinele PPC (demo, nu s-a trimis nimic).

### Investiții (raportul firului C)

Niciun post nu are nevoie de investiție.

## Coada biroului de date (corecții fără deplasare)

- `A-20250708-PT-1073`: Bilanțul postului PT-1073: client trecut la postul greșit în bază (probabilitate 100%), lipsă peste normal ~367 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1165`: Bilanțul postului PT-1165: client trecut la postul greșit în bază (probabilitate 99%), lipsă peste normal ~282 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1212`: Bilanțul postului PT-1212: client trecut la postul greșit în bază (probabilitate 100%), lipsă peste normal ~242 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1186`: Bilanțul postului PT-1186: client trecut la postul greșit în bază (probabilitate 100%), lipsă peste normal ~144 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1018`: Bilanțul postului PT-1018: client trecut la postul greșit în bază (probabilitate 100%), lipsă peste normal ~125 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1101`: Bilanțul postului PT-1101: client trecut la postul greșit în bază (probabilitate 98%), lipsă peste normal ~118 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.
- `A-20250708-PT-1204`: Bilanțul postului PT-1204: client trecut la postul greșit în bază (probabilitate 91%), lipsă peste normal ~120 lei pe lună. Corecție în baza de date (clientul la postul corect), fără deplasare (15 lei): intră în coada biroului de date.

Fuziunea cu bilanțul pe post: ok, 530 contoare confirmate.

## Regulile folosite

| Regula | Decizii |
|---|---|
| `R-CAPACITY-REMOTE` | 174 |
| `R-A-REMOTE-FIRST` | 116 |
| `R-SAFETY-OVER-CAP` | 91 |
| `R-ABSTAIN-DATA` | 61 |
| `R-BILANT-REMOTE` | 51 |
| `R-ABSTAIN-WATCH` | 48 |
| `R-HUMAN-QUEUE-FULL` | 25 |
| `R-ABSTAIN` | 17 |
| `R-C-WATCH` | 15 |
| `R-REMEDY-LADDER` | 14 |
| `R-B-BELOW-THRESHOLD` | 14 |
| `R-A-WATCH` | 14 |
| `R-SAFETY` | 11 |
| `R-BILANT-OFFICE` | 7 |
| `R-CAPACITY` | 7 |
| `R-B-REGION-CAP` | 7 |
| `R-BILANT-GRID` | 4 |
| `R-C-NOTIFY` | 4 |
| `R-B-PREPOSITION` | 3 |
| `R-A-VISIT` | 2 |
| `R-SAFETY-NO-CREW` | 1 |
| `R-LOW-CONFIDENCE` | 1 |
| `R-B-BELOW-COST` | 1 |
| `R-BILANT-WATCH` | 1 |

## Cum a lucrat agentul

- Timpi (secunde): Perceive 0.01, Estimate 15.40, Decide 7.81, Act 0.00.
- Optimizator: ortools (SUCCESS), 293 lucrări candidate, 11 echipe, 7.67 s.
- Ipotezele de cost: `config/economics.yaml` (cu sursele); pragurile: `config/planner.yaml`.
- Fiecare decizie are în jurnal (`audit.jsonl`) ID-ul predicției, versiunea modelului, regula și pragurile.
