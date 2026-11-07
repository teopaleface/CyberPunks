# Analiza erorilor, firul A (contoare defecte sau manipulate)

Generat de `uv run python -m cyberpunks.a_contoare.report` din `reports/A/metrics_full.json` (creat 2026-11-07T15:13:09+02:00), `reports/A/robustness.json` și ieșirile `predict`. Modele: a-lgbm@c670b95 (Londra) și a-lgbm-sgcc@c670b95 (SGCC). K = 1% din contoarele din test. Londra = etichete SINTETICE (probleme injectate de noi peste consum real); SGCC = etichete reale de furt.

## Pe scurt

- Pe furt real (SGCC), modelul pune 81% furturi reale în primele 85 de contoare, față de 4% la regula simplă și 11% la regula VEE completă. ROC-AUC 0,82 e în intervalul cinstit din literatură (0,78-0,92).
- Pe Londra, precizia@K = 1,00 nu vine dintr-o scurgere găsită de noi (secțiunea 1, cu verificările și limitele lor). Vine din cele 215 defecte evidente din test, care umplu primele 130 de locuri (secțiunea 2). Cifra care arată ce adaugă modelul peste reguli e cea de pe problemele subtile: 0,61 față de 0,02 la VEE.
- Slăbiciuni reale: ceasul decalat, sub-înregistrarea lentă și bypass-ul parțial (secțiunea 3). Mai sunt alarmele false la consumatorii mici, limitate prin decizia unui om (secțiunea 5), și degradarea la date lipsă (secțiunea 6).

## 1. Există scurgeri între antrenare și test?

| Verificare | Rezultat |
|---|---|
| Gospodării Londra comune antrenare / test | 0 |
| Gospodării Londra comune calibrare / test | 0 |
| Clienți SGCC comuni antrenare / test | 0 |
| Ultima zi de evaluare la antrenare (Londra) | 2013-08-24 |
| Prima zi de evaluare la test (Londra) | 2013-09-07 |
| Londra, model antrenat pe etichete amestecate: PR-AUC pe test | 0,046 (prevalența: 0,046) |
| SGCC, model antrenat pe etichete amestecate: PR-AUC pe test | 0,105 (prevalența: 0,085) |

Testul cu etichete amestecate e o verificare de bun-simț, nu o dovadă. Arată că pipeline-ul nu strecoară eticheta direct, dar nu poate prinde un artefact al datelor sintetice sau o statistică calculată și din test. De aceea am verificat de unde vine fiecare informație:
- ferestrele Londra se termină în ziua de evaluare, deci features-urile nu văd viitorul. Vecinii sunt gospodării din același set (antrenare, calibrare sau test), iar mediana lor se calculează din consumul fără injecții;
- SGCC: referința "vecinilor" (mediana zilnică) se calculează DOAR din clienții de antrenare, aceeași pentru toate seturile. Corectat după review-ul independent: înainte includea și clienții de test;
- calibrarea, pragurile conformal, alegerea features și pragurile regulii VEE folosesc doar setul de calibrare. Testul e privit o singură dată pe versiune;
- oprirea timpurie la antrenare validează pe gospodării întregi, nu pe ferestre amestecate (corectat după review);
- limite rămase: ferestrele de test (180 de zile înapoi) acoperă și luni din perioada de antrenare, pe alte gospodării, cum lucrează și agentul în producție. Etichetele Londra sunt sintetice, deci un artefact al injecției poate fi învățat; unul l-am găsit și reparat (secțiunea 8).

## 2. Clasamentul la mai multe K (de ce 1,00)

Figuri: `reports/A/figures/ranking_at_k.png` (precizie și recall pe K) și `reports/A/figures/headline_precision.png` (furt real, probleme subtile, toate problemele).

**Londra (sintetic), 13.028 de eșantioane, 597 cu probleme:**

| K | K / probleme | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|---|
| 50 | 0,08 | 1,00 | 0,08 | 0,64 | 0,60 |
| 100 | 0,17 | 1,00 | 0,17 | 0,55 | 0,49 |
| 130 | 0,22 | 1,00 | 0,22 | 0,53 | 0,46 |
| 200 | 0,34 | 0,95 | 0,32 | 0,56 | 0,41 |
| 300 | 0,50 | 0,83 | 0,42 | 0,48 | 0,33 |
| 400 | 0,67 | 0,81 | 0,54 | 0,40 | 0,30 |
| 597 | 1,00 | 0,64 | 0,64 | 0,31 | 0,29 |
| 1194 | 2,00 | 0,37 | 0,74 | 0,24 | 0,21 |

**SGCC (etichete reale), 8.475 de clienți, 723 cu furt:**

| K | K / furturi | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|---|
| 50 | 0,07 | 0,82 | 0,06 | 0,14 | 0,06 |
| 85 | 0,12 | 0,81 | 0,10 | 0,11 | 0,04 |
| 100 | 0,14 | 0,79 | 0,11 | 0,10 | 0,04 |
| 200 | 0,28 | 0,65 | 0,18 | 0,08 | 0,04 |
| 400 | 0,55 | 0,53 | 0,29 | 0,09 | 0,04 |
| 723 | 1,00 | 0,42 | 0,42 | 0,10 | 0,05 |
| 1446 | 2,00 | 0,29 | 0,59 | 0,10 | 0,05 |

**Londra, doar problemele subtile** (fără contor oprit, blocat, negative, goluri), 382 de probleme:

| K | Precizie model | Recall model | Precizie VEE | Precizie regulă simplă |
|---|---|---|---|---|
| 50 | 0,78 | 0,10 | 0,02 | 0,02 |
| 100 | 0,65 | 0,17 | 0,02 | 0,02 |
| 128 | 0,61 | 0,20 | 0,02 | 0,06 |
| 200 | 0,62 | 0,32 | 0,02 | 0,07 |
| 382 | 0,46 | 0,46 | 0,03 | 0,12 |

**Ce ocupă primele 130 de locuri.** Model: contor blocat 42, contor oprit 33, citiri negative 30, goluri de comunicație 11, profil zilnic aplatizat 9, consum zero la aceleași ore în fiecare zi 3, profil zilnic inversat în timp 2. Regula VEE: normal 58, contor oprit 45, contor blocat 12, citiri negative 10, concediu 2, consum zero la aceleași ore în fiecare zi 1, schimbare de ocupare 1, salturi false izolate 1.

Concluzia: K = 130 e doar 22% din probleme, iar testul are 215 defecte evidente. Orice clasificator care le recunoaște umple vârful listei doar cu probleme reale. VEE le recunoaște și el, dar își strică lista cu contoare normale care au salturi sau scăderi naturale. Diferența reală dintre model și reguli se vede la K mai mare și pe problemele subtile. Acolo regulile sunt aproape oarbe, iar modelul ține peste 60% precizie până la K = 200.

## 3. Pe tipuri de problemă (Londra, test)

| Tip | Familie | n | ROC-AUC model | În primele 5% (model) | ROC-AUC VEE | În primele 5% (VEE) |
|---|---|---|---|---|---|---|
| contor oprit (consum zero) | faulty | 55 | 1,00 | 100% | 0,99 | 91% |
| contor blocat (valoare repetată) | faulty | 62 | 1,00 | 98% | 0,99 | 89% |
| goluri de comunicație (date lipsă) | faulty | 45 | 0,99 | 93% | 0,96 | 58% |
| salturi false izolate | faulty | 60 | 0,93 | 72% | 0,79 | 5% |
| ceas decalat (profil mutat) | faulty | 54 | 0,65 | 7% | 0,58 | 0% |
| citiri negative (polaritate inversată) | faulty | 53 | 1,00 | 100% | 0,97 | 79% |
| subînregistrare progresivă (contor îmbătrânit) | faulty | 54 | 0,78 | 15% | 0,72 | 2% |
| consum raportat redus constant | tamper | 30 | 0,93 | 40% | 0,82 | 20% |
| consum redus cu factor aleator pe jumătate de oră | tamper | 18 | 0,91 | 67% | 0,85 | 6% |
| consum zero la aceleași ore în fiecare zi | tamper | 24 | 1,00 | 96% | 0,84 | 17% |
| profil zilnic aplatizat (media zilei) | tamper | 25 | 0,96 | 80% | 0,58 | 0% |
| profil aplatizat și redus aleator | tamper | 28 | 0,97 | 82% | 0,89 | 7% |
| profil zilnic inversat în timp | tamper | 35 | 0,90 | 57% | 0,49 | 0% |
| bypass parțial, cu instalare treptată | tamper | 21 | 0,83 | 14% | 0,78 | 0% |
| consum de noapte redus (00:00-06:00) | tamper | 33 | 0,85 | 45% | 0,59 | 3% |
| concediu (consum de așteptare) | benign | 255 | 0,54 | 2% | 0,73 | 13% |
| schimbare de ocupare (nivel nou, formă ușor diferită) | benign | 241 | 0,65 | 12% | 0,66 | 3% |

**Unde greșește:** ceas decalat (profil mutat) (ROC-AUC 0,65); subînregistrare progresivă (contor îmbătrânit) (ROC-AUC 0,78); bypass parțial, cu instalare treptată (ROC-AUC 0,83). Ceasul decalat mută consumul cu 30-120 de minute, la fel de mult cât variază obiceiurile unei case de la o săptămână la alta. Deriva lentă și bypass-ul cu instalare treptată seamănă, în primele săptămâni, cu o scădere normală de consum. Pentru ceasul decalat am adăugat decalajul profilului zilei (`profile_lag`, `profile_lag_gain`), iar pentru derivă panta față de vecini (`peer_ratio_slope`); efectul lor e în secțiunea 8. Rămân puncte slabe, spuse deschis. Ceasul decalat nu schimbă energia totală, deci contează doar la tarifele pe ore.

## 4. Schimbări normale care NU trebuie semnalate

| Schimbare | n | Alarme false model (primele 5%) | Regula simplă | VEE |
|---|---|---|---|---|
| concediu (consum de așteptare) | 255 | 2% | 32% | 13% |
| schimbare de ocupare (nivel nou, formă ușor diferită) | 241 | 12% | 13% | 3% |

Concediul și schimbarea ocupanților arată ca o scădere de consum. Regula simplă trimite echipa la mulți dintre cei plecați în concediu. Modelul a învățat diferența: concediul are consum de așteptare (frigiderul merge), iar profilul zilei păstrează forma casei.

## 5. Pe nivel de consum (etică: consumul mic nu e dovadă de furt)

| Chintila de consum | Londra: kWh/zi | Alarme false model | Recall model | Alarme false regulă | SGCC: kWh/zi | Alarme false model SGCC | Alarme false regulă SGCC |
|---|---|---|---|---|---|---|---|
| 1 | 3,4 | 5% | 63% | 8% | 0,0 | 0% | 19% |
| 2 | 5,8 | 1% | 64% | 2% | 1,9 | 1% | 3% |
| 3 | 7,5 | 1% | 69% | 3% | 5,6 | 1% | 1% |
| 4 | 9,8 | 2% | 65% | 2% | 10,4 | 3% | 1% |
| 5 | 16,1 | 1% | 69% | 4% | 20,9 | 9% | 1% |

Figura: `reports/A/figures/false_alarms_by_consumption.png`.

Alarmă falsă = un contor fără problemă ajunge în primele 5% din clasament. Pe Londra, casele cu cel mai mic consum primesc de câteva ori mai multe alarme false decât celelalte. La ele, o scădere sau câteva zile cu zero înseamnă mai puțini kWh absoluți, iar zgomotul relativ e mai mare. Pe SGCC, tiparul e invers: furturile reale sunt la consumatori mari, iar alarmele false ale modelului cresc spre chintila de sus. Regula simplă face greșeala opusă și mult mai mare: pe SGCC trimite echipa la 19,4% dintre consumatorii cei mai mici fără problemă, modelul la 0,4%. Consumul mic poate însemna o locuință goală sau sărăcie energetică. De aceea, în agent:
- un furt suspectat la un contor din chintila de jos a consumului NU merge direct la vizită. Merge la un om, cu motivul scris (`extra.low_consumption_guard`, `abstain_reason`);
- nivelul de consum rămâne feature, pentru că din el se calculează și valoarea pierderii. În schimb, rata de alarme false pe chintile se verifică la fiecare evaluare (tabelul de mai sus).

## 6. Pe date lipsă (contoare care nu comunică)

| Zile lipsă | Precizia@K | PR-AUC | ROC-AUC | Abțineri din lipsă de date | Decizii 'problemă' | Decizii 'nu sunt sigur' |
|---|---|---|---|---|---|---|
| 0% | 1,00 | 0,68 | 0,91 | 0% | 547 | 535 |
| 10% | 1,00 | 0,61 | 0,88 | 0% | 696 | 849 |
| 30% | 1,00 | 0,58 | 0,85 | 0% | 904 | 2162 |
| 50% | 1,00 | 0,55 | 0,82 | 1% | 988 | 3757 |
| 70% | 0,95 | 0,34 | 0,76 | 84% | 3195 | 2038 |

La 31 dec. 2025, gradul de integrare a contoarelor inteligente era 66,85% în Dobrogea, 58,81% în Muntenia și 56,45% în Banat (infobuz, rezumat în `memory/12-probleme-reale-ppc-2026.md`, neverificat de noi). Datele incomplete sunt deci situația obișnuită. De aceea am pus pe posturi doar 58,81% din clienți ca fiind contoare cu date. Experimentul ascunde zile întregi la întâmplare pe populația demo. Calitatea scade treptat, nu se prăbușește. Când datele nu mai ajung (sub 60 de zile în 180), agentul spune "nu sunt sigur" și trimite la om, în loc să ghicească.

**SGCC pe timp.** Features pe ferestre de un an; antrenare pe ferestrele care se termină la 31.10.2015, test pe clienți nevăzuți cu ferestre care se termină la 31.10.2016: precizia@K 0,33, PR-AUC 0,19, ROC-AUC 0,70 (regula: ROC-AUC 0,47). Scăderea față de împărțirea pe clienți are două cauze. Golurile din fereastra de antrenare (34%) aproape dispar în cea de test (9%), iar eticheta SGCC nu are dată: nu știm dacă furtul era activ în fereastră. De aceea raportăm ca rezultat principal împărțirea pe clienți, pe toată perioada, ca în literatură. Varianta pe timp e un test de robustețe.

## 7. Calibrare și "nu sunt sigur"

|  | Londra (test) | SGCC (test) |
|---|---|---|
| Brier | 0,023 | 0,063 |
| ECE | 0,004 | 0,007 |
| Acoperirea mulțimii, normale (garanție: >= 99%) | 99% | 99% |
| Acoperirea mulțimii, probleme (garanție: >= 70%) | 70% | 65% |
| Probleme recunoscute SIGUR (mulțimea = {problemă}) | 60% | 19% |
| Precizia deciziilor "problemă" | 75% | 62% |
| Probleme trimise la om (zona gri) | 9% | 46% |
| Probleme ratate (declarate normale) | 30% | 35% |
| Contoare normale declarate "problemă" | 1% | 1% |
| Contoare normale trimise la om (zona gri) | 2% | 17% |
| Toate cazurile "nu sunt sigur" | 2% | 19% |

**Ce ajunge efectiv la echipă și la om, pe demo** (lucrările emise față de adevărul injectat; ultimele două coloane: ce parte din TOATE contoarele normale):

| Scenariu | Lucrări pentru echipă | Din ele, probleme reale | Lucrări la om | Din ele, probleme reale | Contoare normale la echipă | Contoare normale la om |
|---|---|---|---|---|---|---|
| demo-vara | 386 | 94% | 138 | 23% | 0% | 1% |
| maine | 364 | 91% | 199 | 28% | 0% | 1% |

**Pe populațiile demo** (adevărul injectat, nevăzut de model):

| Scenariu | Contoare | Prevalență reală | Scor mediu | Brier | ECE | PR-AUC |
|---|---|---|---|---|---|---|
| demo-vara | 15850 | 0,055 | 0,051 | 0,024 | 0,005 | 0,71 |
| maine | 15850 | 0,049 | 0,052 | 0,025 | 0,004 | 0,68 |

Scorul e o probabilitate calibrată (Venn-ABERS pe o grilă de cuantile; abaterea față de calculul exact, pe 200 de scoruri de test: maximum 0,0174). Scorul mediu e aproape egal cu prevalența reală, deci planificatorul poate înmulți scorul cu valoarea în lei.

Conformal lucrează pe scorul brut al modelului, cu pragurile alese pe calibrare (alpha 1% pentru normal, 30% pentru problemă). Funcția de scor (modelul și features) e aleasă fără etichetele de calibrare. Totuși, garanția formală cere rânduri interschimbabile, iar la Londra setul de calibrare are mai multe ferestre din aceeași gospodărie. De aceea prezentăm acoperirea ca EMPIRICĂ, măsurată pe test (tabelul de mai sus), nu ca garanție. Acoperirea privește MULȚIMEA: "conține clasa reală". Nu e același lucru cu "recunoscut sigur". O problemă din zona gri e acoperită (mulțimea are ambele clase), dar merge la om, nu la echipă. În probabilitate calibrată, zona gri e între 14% și 34% pe Londra. Pe SGCC e mai largă, pentru că etichetele reale sunt mai zgomotoase.

## 8. Ce am încercat ca să corectăm (în ordine)

1. **Artefactul de rotunjire** (commit `a1b25d4`). Prima versiune semnala aproape jumătate din contoarele demo. Cauza: atacurile prin înmulțire (α·x, β·x, deriva) dădeau valori cu multe zecimale, iar contoarele reale trimit 3 zecimale. Modelul învățase "valori nerotunjite = furt". Corecția: rotunjim la 0,001 kWh după orice injecție. Aceeași lecție am transmis-o firului bilanț.
2. **Zgomotul din populația demo.** Zgomotul pe fiecare jumătate de oră ștergea valorile repetate naturale (frigiderul noaptea), deci orice contor părea manipulat. L-am înlocuit cu un factor pe zi.
3. **Sezonul și tipurile slabe.** În iulie, consumul scade natural față de primăvară, iar modelul vedea scăderi peste tot. Am adăugat 10 features: scăderea și panta raportate la vecinii de pe post (`max_drop_peer`, `peer_ratio_slope`), care scot vremea și sezonul, decalajul profilului zilei, forma distribuției, golurile separate și ritmul săptămânal. Le-am ales pe o validare din setul de antrenare (gospodării ținute deoparte), nu pe calibrare și nu pe test (`select_features.py`): PR-AUC SGCC 0,38 -> 0,43, ROC-AUC 0,82 -> 0,84; Londra PR-AUC 0,90 -> 0,90; ROC-AUC pe tip, față de contoarele normale: ceasul decalat 0,60 -> 0,63, deriva 0,74 -> 0,77, furtul de noapte 0,81 -> 0,81. Fără features sezoniere brute, PR-AUC 0,90 și ceasul decalat 0,61, deci le-am păstrat. Costul: concediul seamănă puțin mai mult cu o problemă (ROC-AUC față de contoarele normale 0,48 -> 0,54; 0,5 = de nedeosebit, deci mai mic e mai bine aici). Validarea are prevalența de antrenare (aproape jumătate probleme), deci cifrele absolute nu se compară cu testul; contează doar diferența dintre variante.
4. **Un baseline mai corect.** Pe lângă regula simplă cerută (zero >= 7 zile sau scădere >= 50%), am construit regula VEE completă: zero, valori repetate, goluri, negative, salturi, scădere. Pragurile de salt le-am ales pe calibrare, ca să-i dăm cea mai bună șansă.
5. **Pragurile pentru "nu sunt sigur".** Cu 5% / 20%, aproape orice scor peste 0,08 devenea "problemă", iar zona gri era goală. Cu 1% / 30% (pe demo: demo-vara: deciziile "problemă" au precizie 87%, iar în zona gri sunt 14% probleme reale; maine: deciziile "problemă" au precizie 68%, iar în zona gri sunt 22% probleme reale), zona gri chiar merită privirea unui om.
6. **Paza pentru consum mic** (secțiunea 5).

## 9. Fuziunea cu bilanțul pe post (verificare pe testul A)

Am aplicat formula de fuziune a firului bilanț (`cyberpunks.a_bilant.fuse.combine_arrays`, doar confirmare, neschimbată) pe populația demo. Bilanțul fiecărui post e construit din adevărul injectat: energia nemăsurată de contoarele postului, plus zgomotul pierderilor normale, cu abaterea sigma = 1%, 2% sau 4% din consumul postului. Rezultatele sunt mediate pe 3 trageri ale zgomotului (`reports/A/fusion_check.json`, `uv run python -m cyberpunks.a_contoare.fusion_check`).

| Scenariu | Sigma bilanț | Precizia@10 | Precizia@100 | PR-AUC | Furturi confirmate | Defecte confirmate | Fără problemă, confirmate |
|---|---|---|---|---|---|---|---|
| demo-vara | 1% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,707 -> 0,707 | 21% | 24% | 6% |
| demo-vara | 2% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,707 -> 0,715 | 8% | 11% | 2% |
| demo-vara | 4% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,707 -> 0,716 | 2% | 3% | 1% |
| maine | 1% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,679 -> 0,688 | 17% | 23% | 3% |
| maine | 2% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,679 -> 0,688 | 5% | 10% | 1% |
| maine | 4% | 1,00 -> 1,00 | 1,00 -> 1,00 | 0,679 -> 0,687 | 1% | 2% | 0% |

**Unde ajută și unde nu** (demo-vara, bilanț precis, sigma 1%, ce parte din fiecare tip e confirmată):
- defectele care pierd multă energie: contor oprit 53%, citiri negative 55%, valoare blocată 27%. Pe acestea modelul le pune oricum în vârful listei, deci precizia în primele 10-100 nu se schimbă;
- furtul: consum redus constant 28%, oprire pe ore 29%, bypass 26%. Pierderea unui contor (câțiva kWh/zi) e mică față de zgomotul postului;
- tiparele care nu schimbă energia nu pot fi confirmate: profil aplatizat 4%, profil inversat 7%, ceas decalat 8%, goluri 1%, salturi 6%. E corect că fuziunea doar confirmă și nu coboară scorul;
- riscul: bilanțul confirmă POSTUL, nu contorul. Pe un post cu energie lipsă, și vecinii fără problemă cu o scădere naturală sunt confirmați: concediu 24%, schimbarea ocupanților 14%;
- în zona gri a lui A (537 de contoare, 14% probleme reale), cele confirmate au 14% probleme reale, deci confirmarea nu le separă. Asta susține decizia bilanțului de a nu rezolva automat cazurile nesigure.

## 10. Limite cunoscute

- Etichetele din Londra sunt sintetice: modelul învață tiparele pe care le-am injectat noi. Le-am făcut realiste, cu parametri din literatură, intensități mici, instalare treptată și schimbări normale ca exemple grele, dar un furt real poate arăta altfel. Pe etichete reale, SGCC dă un reper mai modest.
- SGCC are o etichetă pe client, fără dată, și vine din altă țară și altă rețea. Îl folosim ca dovadă că aceleași features merg pe furt real, nu ca model pentru București.
- Prevalența (3% defecte, 2% furturi) e o ipoteză. Precizia depinde de ea: la o prevalență reală mai mică, precizia la același K scade.
- Valoarea în lei folosește ipotezele din `config/economics.yaml` (energia pierdută 0,70 lei/kWh, o vizită de 250 de lei, orizont de 90 de zile).
- Tipul exact al defectului (blocat sau oprit) nu e prezis direct. Modelul dă familia (defect sau manipulare), iar factorii SHAP și cazurile similare arată tipul probabil.
