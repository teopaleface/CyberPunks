# Analiza erorilor, firul A (contoare defecte sau manipulate)

Generat de `uv run python -m cyberpunks.a_contoare.report` din `reports/A/metrics_full.json` (creat 2026-11-07T13:51:50+02:00), `reports/A/robustness.json` și ieșirile `predict`. Modele: a-lgbm@b82b20a (Londra) și a-lgbm-sgcc@b82b20a (SGCC). K = 1% din contoarele din test. Londra = etichete SINTETICE (probleme injectate de noi peste consum real); SGCC = etichete reale de furt.

## Pe scurt

- Pe furt real (SGCC), modelul pune 81% furturi reale în primele 85 de contoare, față de 4% la regula simplă și 11% la regula VEE completă. ROC-AUC 0,82 e în intervalul cinstit din literatură (0,78-0,92).
- Pe Londra, precizia@K = 1,00 NU vine dintr-o scurgere (secțiunea 1). Vine din cele 215 defecte evidente din test, care umplu primele 130 de locuri (secțiunea 2). Cifra care arată ce adaugă modelul peste reguli e cea de pe problemele subtile: 0,69 față de 0,02 la VEE.
- Slăbiciuni reale: ceasul decalat, sub-înregistrarea lentă și bypass-ul parțial (secțiunea 3). Mai sunt alarmele false la consumatorii mici, limitate prin decizia unui om (secțiunea 5), și degradarea la date lipsă (secțiunea 6).

## 1. Există scurgeri între antrenare și test?

| Verificare | Rezultat |
|---|---|
| Gospodării Londra comune antrenare / test | 0 |
| Gospodării Londra comune calibrare / test | 0 |
| Clienți SGCC comuni antrenare / test | 0 |
| Ultima zi de evaluare la antrenare (Londra) | 2013-08-24 |
| Prima zi de evaluare la test (Londra) | 2013-09-07 |
| Londra, model antrenat pe etichete amestecate: PR-AUC pe test | 0,048 (prevalența: 0,046) |
| SGCC, model antrenat pe etichete amestecate: PR-AUC pe test | 0,098 (prevalența: 0,085) |

Cu etichetele amestecate la întâmplare, modelul nu mai găsește nimic: PR-AUC cade la prevalență. Deci rezultatele vin din tiparul de consum, nu dintr-o informație strecurată în features. O nuanță: ferestrele de test (180 de zile înapoi de la ziua de evaluare) acoperă și luni din perioada de antrenare, dar pe alte gospodării. Așa lucrează și agentul în producție: se uită în trecutul contorului.
Am găsit și am reparat o scurgere din construcția datelor (secțiunea 8): injecțiile prin înmulțire lăsau valori nerotunjite, pe care modelul le învățase.

## 2. Clasamentul la mai multe K (de ce 1,00)

**Londra (sintetic), 13.028 de eșantioane, 597 cu probleme:**

| K | K / probleme | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|---|
| 50 | 0,08 | 1,00 | 0,08 | 0,64 | 0,62 |
| 100 | 0,17 | 1,00 | 0,17 | 0,61 | 0,65 |
| 130 | 0,22 | 1,00 | 0,22 | 0,61 | 0,52 |
| 200 | 0,34 | 0,93 | 0,31 | 0,56 | 0,41 |
| 300 | 0,50 | 0,90 | 0,45 | 0,48 | 0,33 |
| 400 | 0,67 | 0,81 | 0,54 | 0,40 | 0,30 |
| 597 | 1,00 | 0,64 | 0,64 | 0,31 | 0,29 |
| 1194 | 2,00 | 0,37 | 0,75 | 0,24 | 0,21 |

**SGCC (etichete reale), 8.475 de clienți, 723 cu furt:**

| K | K / furturi | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|---|
| 50 | 0,07 | 0,82 | 0,06 | 0,14 | 0,06 |
| 85 | 0,12 | 0,81 | 0,10 | 0,11 | 0,04 |
| 100 | 0,14 | 0,80 | 0,11 | 0,10 | 0,04 |
| 200 | 0,28 | 0,68 | 0,19 | 0,08 | 0,04 |
| 400 | 0,55 | 0,52 | 0,28 | 0,09 | 0,04 |
| 723 | 1,00 | 0,43 | 0,43 | 0,10 | 0,05 |
| 1446 | 2,00 | 0,30 | 0,59 | 0,10 | 0,05 |

**Londra, doar problemele subtile** (fără contor oprit, blocat, negative, goluri), 382 de probleme:

| K | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|
| 50 | 0,72 | 0,09 | 0,02 | 0,02 |
| 100 | 0,76 | 0,20 | 0,02 | 0,02 |
| 128 | 0,69 | 0,23 | 0,02 | 0,06 |
| 200 | 0,61 | 0,32 | 0,02 | 0,07 |
| 382 | 0,46 | 0,46 | 0,03 | 0,12 |

**Ce ocupă primele 130 de locuri.** Model: contor blocat 44, contor oprit 33, citiri negative 29, goluri de comunicație 11, profil zilnic aplatizat 8, profil zilnic inversat în timp 3, consum zero la aceleași ore în fiecare zi 2. Regula VEE: normal 48, contor oprit 45, citiri negative 21, contor blocat 12, concediu 2, consum zero la aceleași ore în fiecare zi 1, schimbare de ocupare 1.

Concluzia: K = 130 e doar 22% din probleme, iar testul are 215 defecte evidente. Orice clasificator care le recunoaște umple vârful listei doar cu probleme reale. VEE le recunoaște și el, dar își strică lista cu contoare normale care au salturi sau scăderi naturale. Diferența reală dintre model și reguli se vede la K mai mare și pe problemele subtile. Acolo regulile sunt aproape oarbe, iar modelul ține peste 60% precizie până la K = 200.

## 3. Pe tipuri de problemă (Londra, test)

| Tip | Familie | n | ROC-AUC model | În primele 5% (model) | ROC-AUC VEE | În primele 5% (VEE) |
|---|---|---|---|---|---|---|
| contor oprit (consum zero) | faulty | 55 | 1,00 | 100% | 0,99 | 91% |
| contor blocat (valoare repetată) | faulty | 62 | 1,00 | 98% | 0,99 | 89% |
| goluri de comunicație (date lipsă) | faulty | 45 | 0,99 | 96% | 0,96 | 58% |
| salturi false izolate | faulty | 60 | 0,94 | 70% | 0,79 | 5% |
| ceas decalat (profil mutat) | faulty | 54 | 0,67 | 7% | 0,58 | 0% |
| citiri negative (polaritate inversată) | faulty | 53 | 1,00 | 98% | 0,97 | 79% |
| subînregistrare progresivă (contor îmbătrânit) | faulty | 54 | 0,78 | 11% | 0,72 | 2% |
| consum raportat redus constant | tamper | 30 | 0,91 | 37% | 0,82 | 20% |
| consum redus cu factor aleator pe jumătate de oră | tamper | 18 | 0,91 | 78% | 0,85 | 6% |
| consum zero la aceleași ore în fiecare zi | tamper | 24 | 1,00 | 96% | 0,84 | 17% |
| profil zilnic aplatizat (media zilei) | tamper | 25 | 0,98 | 80% | 0,58 | 0% |
| profil aplatizat și redus aleator | tamper | 28 | 0,97 | 82% | 0,89 | 7% |
| profil zilnic inversat în timp | tamper | 35 | 0,91 | 63% | 0,49 | 0% |
| bypass parțial, cu instalare treptată | tamper | 21 | 0,80 | 24% | 0,78 | 0% |
| consum de noapte redus (00:00-06:00) | tamper | 33 | 0,85 | 42% | 0,59 | 3% |
| concediu (consum de așteptare) | benign | 255 | 0,54 | 2% | 0,73 | 13% |
| schimbare de ocupare (nivel nou, formă ușor diferită) | benign | 241 | 0,64 | 11% | 0,66 | 3% |

**Unde greșește:** ceas decalat (profil mutat) (ROC-AUC 0,67); subînregistrare progresivă (contor îmbătrânit) (ROC-AUC 0,78); bypass parțial, cu instalare treptată (ROC-AUC 0,80). Ceasul decalat mută consumul cu 30-120 de minute, la fel de mult cât variază obiceiurile unei case de la o săptămână la alta. Deriva lentă și bypass-ul cu instalare treptată seamănă, în primele săptămâni, cu o scădere normală de consum. Pentru ceasul decalat am adăugat decalajul profilului zilei (`profile_lag`, `profile_lag_gain`), iar pentru derivă panta față de vecini (`peer_ratio_slope`). Pe calibrare, ceasul decalat a urcat de la 0% la 12% în primele 5%, iar deriva de la 10% la 20%. Rămân puncte slabe, spuse deschis. Ceasul decalat nu schimbă energia totală, deci contează doar la tarifele pe ore.

## 4. Schimbări normale care NU trebuie semnalate

| Schimbare | n | Alarme false model (primele 5%) | Regula simplă | VEE |
|---|---|---|---|---|
| concediu (consum de așteptare) | 255 | 2% | 32% | 13% |
| schimbare de ocupare (nivel nou, formă ușor diferită) | 241 | 11% | 13% | 3% |

Concediul și schimbarea ocupanților arată ca o scădere de consum. Regula simplă trimite echipa la mulți dintre cei plecați în concediu. Modelul a învățat diferența: concediul are consum de așteptare (frigiderul merge), iar profilul zilei păstrează forma casei.

## 5. Pe nivel de consum (etică: consumul mic nu e dovadă de furt)

| Chintila de consum | Londra: kWh/zi | Alarme false model | Recall model | Alarme false regulă | SGCC: kWh/zi | Alarme false model SGCC |
|---|---|---|---|---|---|---|
| 1 | 3,4 | 5% | 63% | 8% | 0,0 | 1% |
| 2 | 5,8 | 1% | 67% | 2% | 1,9 | 1% |
| 3 | 7,5 | 1% | 69% | 3% | 5,6 | 1% |
| 4 | 9,8 | 2% | 66% | 2% | 10,4 | 3% |
| 5 | 16,1 | 1% | 67% | 4% | 20,9 | 8% |

Alarmă falsă = un contor fără problemă ajunge în primele 5% din clasament. Pe Londra, casele cu cel mai mic consum primesc de câteva ori mai multe alarme false decât celelalte. La ele, o scădere sau câteva zile cu zero înseamnă mai puțini kWh absoluți, iar zgomotul relativ e mai mare. Pe SGCC, tiparul e invers: furturile reale sunt la consumatori mari, iar alarmele false cresc spre chintila de sus. Consumul mic poate însemna o locuință goală sau sărăcie energetică. De aceea, în agent:
- un furt suspectat la un contor din chintila de jos a consumului NU merge direct la vizită. Merge la un om, cu motivul scris (`extra.low_consumption_guard`, `abstain_reason`);
- nivelul de consum rămâne feature, pentru că din el se calculează și valoarea pierderii. În schimb, rata de alarme false pe chintile se verifică la fiecare evaluare (tabelul de mai sus).

## 6. Pe date lipsă (contoare care nu comunică)

| Zile lipsă | Precizia@K | PR-AUC | ROC-AUC | Abțineri din lipsă de date | Decizii 'problemă' | Decizii 'nu sunt sigur' |
|---|---|---|---|---|---|---|
| 0% | 1,00 | 0,68 | 0,91 | 0% | 383 | 335 |
| 10% | 1,00 | 0,62 | 0,87 | 0% | 460 | 533 |
| 30% | 1,00 | 0,58 | 0,84 | 0% | 488 | 1965 |
| 50% | 1,00 | 0,54 | 0,79 | 1% | 636 | 4179 |
| 70% | 1,00 | 0,48 | 0,77 | 83% | 477 | 1815 |

La 31 dec. 2025, gradul de integrare a contoarelor inteligente era 66,85% în Dobrogea, 58,81% în Muntenia și 56,45% în Banat (infobuz, rezumat în `memory/12-probleme-reale-ppc-2026.md`, neverificat de noi). Datele incomplete sunt deci situația obișnuită. De aceea am pus pe posturi doar 58,81% din clienți ca fiind contoare cu date. Experimentul ascunde zile întregi la întâmplare pe populația demo. Calitatea scade treptat, nu se prăbușește. Când datele nu mai ajung (sub 60 de zile în 180), agentul spune "nu sunt sigur" și trimite la om, în loc să ghicească.

**SGCC pe timp.** Features pe ferestre de un an; antrenare pe ferestrele care se termină la 31.10.2015, test pe clienți nevăzuți cu ferestre care se termină la 31.10.2016: precizia@K 0,38, PR-AUC 0,20, ROC-AUC 0,71 (regula: ROC-AUC 0,47). Scăderea față de împărțirea pe clienți are două cauze. Golurile din fereastra de antrenare (34%) aproape dispar în cea de test (9%), iar eticheta SGCC nu are dată: nu știm dacă furtul era activ în fereastră. De aceea raportăm ca rezultat principal împărțirea pe clienți, pe toată perioada, ca în literatură. Varianta pe timp e un test de robustețe.

## 7. Calibrare și "nu sunt sigur"

|  | Londra (test) | SGCC (test) |
|---|---|---|
| Brier | 0,022 | 0,063 |
| ECE | 0,003 | 0,006 |
| Acoperire conformal, normale (țintă 99%) | 99% | 99% |
| Acoperire conformal, probleme (țintă 70%) | 69% | 64% |
| Cazuri 'nu sunt sigur' | 2% | 18% |

**Pe populațiile demo** (adevărul injectat, nevăzut de model):

| Scenariu | Contoare | Prevalență reală | Scor mediu | Brier | ECE | PR-AUC |
|---|---|---|---|---|---|---|
| demo-vara | 15850 | 0,055 | 0,053 | 0,025 | 0,003 | 0,71 |
| maine | 15850 | 0,049 | 0,050 | 0,024 | 0,003 | 0,70 |

Scorul e o probabilitate calibrată. Scorul mediu e aproape egal cu prevalența reală, deci planificatorul poate înmulți scorul cu valoarea în lei. Pragurile conformal (1% pentru normal, 30% pentru problemă) sunt alese pe calibrare. Între ele e zona gri (scoruri de aproximativ 0,12-0,30), unde modelul spune "nu sunt sigur" și decide un om. Pe SGCC, zona gri e mai mare: etichetele reale sunt mai zgomotoase.

## 8. Ce am încercat ca să corectăm (în ordine)

1. **Artefactul de rotunjire** (commit `a1b25d4`). Prima versiune semnala aproape jumătate din contoarele demo. Cauza: atacurile prin înmulțire (α·x, β·x, deriva) dădeau valori cu multe zecimale, iar contoarele reale trimit 3 zecimale. Modelul învățase "valori nerotunjite = furt". Corecția: rotunjim la 0,001 kWh după orice injecție. Aceeași lecție am transmis-o firului bilanț.
2. **Zgomotul din populația demo.** Zgomotul pe fiecare jumătate de oră ștergea valorile repetate naturale (frigiderul noaptea), deci orice contor părea manipulat. L-am înlocuit cu un factor pe zi.
3. **Sezonul și tipurile slabe.** În iulie, consumul scade natural față de primăvară, iar modelul vedea scăderi peste tot. Am adăugat 10 features: scăderea și panta raportate la vecinii de pe post (`max_drop_peer`, `peer_ratio_slope`), care scot vremea și sezonul, decalajul profilului zilei, forma distribuției, golurile separate și ritmul săptămânal. Le-am ales pe setul de calibrare, nu pe test (`select_features.py`): PR-AUC SGCC 0,42 -> 0,46, precizia@K 0,78 -> 0,82; Londra PR-AUC 0,71 -> 0,72; în primele 5%: ceasul decalat 0% -> 12%, deriva 10% -> 20%, furtul de noapte 46% -> 55%. Fără features sezoniere brute, PR-AUC a rămas 0,72, dar ceasul decalat a scăzut la 6%, deci le-am păstrat.
4. **Un baseline mai corect.** Pe lângă regula simplă cerută (zero >= 7 zile sau scădere >= 50%), am construit regula VEE completă: zero, valori repetate, goluri, negative, salturi, scădere. Pragurile de salt le-am ales pe calibrare, ca să-i dăm cea mai bună șansă.
5. **Pragurile pentru "nu sunt sigur".** Cu 5% / 20%, aproape orice scor peste 0,08 devenea "problemă", iar zona gri era goală. Cu 1% / 30% (pe demo: demo-vara: deciziile "problemă" au precizie 79%, iar în zona gri sunt 15% probleme reale; maine: deciziile "problemă" au precizie 69%, iar în zona gri sunt 22% probleme reale), zona gri chiar merită privirea unui om.
6. **Paza pentru consum mic** (secțiunea 5).

## 9. Limite cunoscute

- Etichetele din Londra sunt sintetice: modelul învață tiparele pe care le-am injectat noi. Le-am făcut realiste, cu parametri din literatură, intensități mici, instalare treptată și schimbări normale ca exemple grele, dar un furt real poate arăta altfel. Pe etichete reale, SGCC dă un reper mai modest.
- SGCC are o etichetă pe client, fără dată, și vine din altă țară și altă rețea. Îl folosim ca dovadă că aceleași features merg pe furt real, nu ca model pentru București.
- Prevalența (3% defecte, 2% furturi) e o ipoteză. Precizia depinde de ea: la o prevalență reală mai mică, precizia la același K scade.
- Valoarea în lei folosește ipotezele din `config/economics.yaml` (energia pierdută 0,70 lei/kWh, o vizită de 250 de lei, orizont de 90 de zile).
- Tipul exact al defectului (blocat sau oprit) nu e prezis direct. Modelul dă familia (defect sau manipulare), iar factorii SHAP și cazurile similare arată tipul probabil.
