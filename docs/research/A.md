# Cercetare, firul A: contoare defecte sau manipulate

Faza 0, 7 nov. 2026, 12:48-13:30. Patru cercetări în paralel (subagenți), plus verificarea directă a datelor descărcate. Ce scrie "verificat de noi" am rulat noi pe fișiere. Ce scrie "neverificat" vine din rezumate sau surse secundare.

## Pe scurt: ce am decis

| Ce | Decizia | De ce |
|---|---|---|
| Date cu etichete reale | SGCC: 42.372 de clienți, consum zilnic, 3.615 marcați ca furt | Singurul set public mare cu etichete reale de furt |
| Date pentru defecte | Low Carbon London (CC BY 4.0): consum real la 30 de minute, ~1.500 de gospodării, peste care injectăm noi defecte și furturi (etichete din construcție, cu tipul) | Nu există set public cu contoare defecte etichetate; PPC spune că urmează "monitorizarea predictivă a contoarelor defecte" |
| Împărțirea | SGCC: pe clienți (stratificat), 60% antrenare, 20% calibrare, 20% test. Londra: gospodării nevăzute și perioadă ulterioară | Fără scurgeri: niciun client de test nu apare la antrenare |
| Baseline-uri | (1) regulă de tip VEE: zero cel puțin N zile sau scădere de cel puțin 50% față de propriul istoric; (2) IsolationForest pe aceleași features | Regula e ce fac azi utilitățile (verificări VEE); IsolationForest e metoda clasică fără etichete |
| Model | LightGBM cu ponderi pe clase, calibrat isotonic; interval de probabilitate Venn-ABERS; "nu sunt sigur" prin conformal Mondrian | Merge bine pe date tabelare dezechilibrate, rulează local, are SHAP exact |
| Metrica principală | Precizia@K, cu K = 1% din contoare (cam cât verifică într-o săptămână 3 echipe de contorizare într-o zonă de 10.000 de contoare). PR-AUC ca metrică secundară, ambele cu interval bootstrap | Decizia reală e "ce K contoare vizităm"; PR-AUC nu depinde de un prag și e stabilă pe clase rare |
| Reper cinstit | ROC-AUC fără scurgeri pe SGCC: cam 0,80-0,92; PR-AUC cam 0,43 la un XGBoost simplu; peste 0,95 doar cu SMOTE înainte de împărțire | Vezi secțiunea 4 |

## 1. Setul SGCC (furt, etichete reale)

**Cine l-a publicat.** Datele vin de la State Grid Corporation of China. Le-a pus public grupul lui Zibin Zheng, în repo-ul [`henryRDlab/ElectricityTheftDetection`](https://github.com/henryRDlab/ElectricityTheftDetection). README-ul cere citarea articolului: Zheng, Yang, Niu, Dai, Zhou, *Wide and Deep Convolutional Neural Networks for Electricity-Theft Detection to Secure Smart Grids*, IEEE Transactions on Industrial Informatics 14(4):1606-1615, 2018, DOI [10.1109/TII.2017.2785963](https://ieeexplore.ieee.org/document/8233155/).

**Licența.**
- Repo-ul GitHub nu are licență: API-ul GitHub întoarce `"license": null`. Singura condiție scrisă e citarea articolului.
- Copia de pe Kaggle ([`bensalem14/sgcc-dataset`](https://www.kaggle.com/datasets/bensalem14/sgcc-dataset), reîncărcată de altcineva în 2023) declară ODbL. Declarația o face cel care a reîncărcat, nu SGCC, deci nu o putem folosi ca licență de la sursă.
- Pe Zenodo, Mendeley, IEEE DataPort și Hugging Face nu am găsit copii cu licență explicită.

**Cum îl folosim.** Ca date publice pentru cercetare, cu citare:
1. Nu punem datele brute în repo-ul public.
2. Scriptul `uv run python -m cyberpunks.a_contoare.download --only sgcc` le descarcă din repo-ul original și verifică sumele SHA-256.
3. În repo rămân doar scorurile și metricile agregate, niciun rând din date.

Risc rămas: drepturile SGCC nu sunt clarificate formal. Pentru un hackathon, cu citare și fără redistribuire, riscul e mic.

**Structura, verificată de noi pe fișier** (`data.csv`, SHA-256 `99f8fd31…`):
- 42.372 de rânduri și 1.036 de coloane: `CONS_NO`, `FLAG` și 1.034 de coloane de zile.
- Perioada: 2014-01-01 - 2016-10-31. Ar fi 1.035 de zile, dar lipsește coloana pentru 2016-09-18.
- Coloanele de zile sunt în ordine alfabetică (`2014/1/1`, `2014/1/10`, `2014/1/11`…), nu cronologică. Le sortăm la încărcare.
- `FLAG`: 38.757 normali și 3.615 cu furt (8,53%). Nu există ID-uri sau rânduri duplicate.
- Valori lipsă: 25,64%. Zerouri: 13,21%. Nicio valoare negativă. Maximul e 800.003 (o valoare imposibilă), iar percentila 99 e 69,8.
- **Golurile se schimbă mult în timp:** în 2014-2015 lipsesc 30-42% din valori pe trimestru, în 2016 doar 1,4-1,8%. Deci golurile țin mai ales de colectarea datelor, nu de clienți. O împărțire pe timp ar învăța diferența de colectare, nu furtul.
- Clienții cu furt au mai multe goluri (31,5% față de 25,1%), mai puține zerouri (8,3% față de 13,7%) și consum median mai **mare** (7,0 față de 4,4 kWh/zi). Consumul mic nu înseamnă furt în acest set. Asta contează pentru etică: modelul nu trebuie să penalizeze consumatorii mici.
- Eticheta e una pe client, fără dată. Nu știm când a început frauda. Etichetele vin din inspecții, deci un fraudulos neprins apare ca normal (zgomot în etichete).
- Unitatea (kWh pe zi) nu e declarată explicit în surse. Valorile mediane (4-7) se potrivesc cu kWh/zi pentru o gospodărie.

## 2. Contoarele din Londra (Low Carbon London)

**Licența:** Creative Commons Attribution 4.0 (CC BY 4.0), pe [London Datastore](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d). Autor: UK Power Networks. Textul de atribuire pe care îl folosim: "Contains data from UK Power Networks, Low Carbon London project, via London Datastore, CC BY 4.0. Faults and theft patterns were injected synthetically by team CyberPunks."

**Fișierele.** Platforma s-a mutat; vechiul link face redirect.

| fișier | format | mărime | URL direct | HTTP (7 nov.) |
|---|---|---|---|---|
| LCL-FullData | zip, 1 CSV | 801.674.949 B; ~10 GB despachetat, ~167 mil. rânduri | `https://data.london.gov.uk/download/vqm0d/3527bf39-d93e-4071-8451-df2ade1ea4f2/LCL-FullData.zip` | 200, acceptă intervale |
| Partitioned LCL Data | zip, 168 CSV | 795.722.689 B; 8,54 GB despachetat | `https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip` | 200, acceptă intervale |

**Conținutul** (verificat pe mostre):
- 5.567 de gospodării, noiembrie 2011 - februarie 2014, câte o citire la 30 de minute.
- Coloane: `LCLid, stdorToU, DateTime, KWH/hh (per half hour)`. Valorile au spații (`" 0.069 "`), unele rânduri au textul `Null`, iar ~690 de rânduri pe fișier sunt duplicate exacte (la miezul nopții). Ora e locală, fără fus orar.
- Fișierele 0-134 au gospodăriile cu tarif fix (Std), în ordinea ID-ului. Fișierele 135-167 au cele ~1.100 de gospodării cu tarif dinamic (ToU, în 2013).
- Fiecare gospodărie e contiguă și sortată în timp. Rar, una e tăiată între două fișiere vecine.

**Ce luăm.** Serverul acceptă cereri pe intervale de octeți, deci citim doar directorul arhivei și scoatem fișierele 0-44 (Std, ~1.500 de gospodării, ~212 MB descărcat în loc de 796 MB). Scriptul verifică CRC-ul fiecărui fișier și scrie sumele SHA-256 în `data/samples/A/checksums_lcl.sha256`, care intră în git. Serverul limitează cererile (HTTP 429), așa că scriptul așteaptă și reîncearcă.

**Alternative, dacă LCL nu merge:** GoiEner (Zenodo 7362093, 25.559 de clienți din Spania, orar; licența e neclară, CC-BY-SA sau CC BY), IDEAL (Edinburgh DataShare, 255 de locuințe, CC BY 4.0).

## 3. Modele de manipulare și de defect (pentru date sintetice etichetate)

**Furtul: atacurile h1-h6** din Jokar, Arianpoo, Leung 2016 (IEEE TSG, DOI 10.1109/TSG.2015.2425222). Formulele vin din două lucrări care reproduc tabelul original: Nabil et al. 2018 ([arXiv 1809.01774](https://arxiv.org/pdf/1809.01774)) și [arXiv 2010.09212](https://arxiv.org/pdf/2010.09212). Articolul original nu l-am putut deschide. Fiecare atac se aplică pe o zi de 48 de semiore:

| atac | formulă | parametri | ce înseamnă |
|---|---|---|---|
| h1 | α·x_t | α ~ U(0,1; 0,8), fix pe zi | raportează constant mai puțin |
| h2 | β_t·x_t | β_t ~ U(0,1; 0,8) la fiecare pas | reducere aleatoare |
| h3 | x_t = 0 pe [t_i, t_f] | t_i ~ U[0, 42], durata ~ U[8, 48] semiore (minimum 4 ore) | oprește contorul câteva ore pe zi |
| h4 | E(x), media zilei | - | profil aplatizat, totalul rămâne |
| h5 | β_t·E(x) | β_t ~ U(0,1; 0,8) | profil aplatizat și redus |
| h6 | x_{48-t} | - | ziua inversată; totalul rămâne (atac pe tariful orar) |

h4 și h6 nu scad totalul zilei; contează doar la tarife pe ore (ca PPC Ore Smart+). Adăugăm două tipare din practică: **bypass parțial** x·(1-p), p ~ U(0,2; 0,6) (o fază ocolită ≈ 1/3), cu instalare treptată pe 1-30 de zile; **furt de noapte** (orele 0-6 reduse cu 30-90%). Parametrii acestor două sunt aleși de noi.

**Defectele (fără intenție).** Familiile de verificări VEE (Validation, Estimation, Editing) din Oracle Utilities MDM ([lista](https://docs.oracle.com/en/industries/utilities/rate-cloud/264/rcs-user-guides/Topics/D1_BG_About_IMD_Validations.html), [spike check](https://docs.oracle.com/en/industries/utilities/rate-cloud/264/rcs-user-guides/Topics/D1_AG_VEE_IntervalSpikeCheck.html), [high/low check](https://docs.oracle.com/en/industries/utilities/rate-cloud/264/rcs-user-guides/Topics/D1_AG_VEE_HighLowCheck.html)) și din tutorialul VEE Oncor/ERCOT (consecutive zeros, spike check, sum check, reverse rotation, time change):

| defect | formulă de injectare | parametri | zilnic? | la 30 min? |
|---|---|---|---|---|
| contor oprit | x_t = 0 | de la o zi până la final | da | da |
| valoare blocată | x_t = ultima valoare bună, constantă | idem | da | da |
| goluri de comunicație | x_t lipsă pe 1-10 zile, 1-4 episoade; uneori vârf la revenire = suma golului | - | da | da |
| salturi false | 1-4 semiore pe săptămână × 10-80 | plafon 50 kWh | slab | da |
| ceas decalat | profilul mutat cu 1-4 semiore | - | nu | da |
| citiri negative | x_t → -\|x_t\| pentru 30-100% din semiore | polaritate inversată | da | da |
| sub-înregistrare | x·(1 - δ·t/T) | δ ~ U(0,2; 0,6) pe perioadă (accelerat; în realitate ~2-10% pe an) | lent | greu |

**Schimbări normale (nu sunt probleme), ca exemple grele:** concediu (7-21 de zile la nivelul de standby) și schimbarea ocupanților (nivel ×0,45-0,8 sau ×1,25-1,7, cu profil ușor schimbat). Un model bun nu trebuie să trimită echipa la cineva plecat în concediu.

**Cât de des apar (pentru ratele de injectare).** Cifrele publice sunt slabe: FPL (Florida, 2013) raporta 0,14% din contoare fără comunicație într-o zi (neverificat, din rezumat); defectele sub 1% pe an la contoare noi (sursă slabă); pierderile comerciale în România, ~3% din energia intrată în distribuție (neverificat). Alegem rate mai mari decât în realitate (câteva procente), ca modelul să aibă exemple, și raportăm separat ce înseamnă la prevalența reală.

## 4. Rezultate raportate pe SGCC (reper cinstit)

| lucrare | model | metrică | valoare | protocol | scurgeri? |
|---|---|---|---|---|---|
| Zheng 2018 (din surse secundare) | Wide & Deep CNN | AUC / MAP@100 | ~0,78-0,80 / ~0,95 | neverificat | neverificat |
| [Finardi 2020](https://arxiv.org/pdf/2002.06219) | CNN 2D | AUC / MAP@100 | 0,898 / 0,977 (50% antrenare); 0,922 / 0,979 (80%) | k-fold stratificat | fără SMOTE; alegerea epocii nedescrisă |
| Finardi 2020 | atenție + convoluții dilatate | AUC / MAP@100 / F1 | 0,925 / 0,992 / 0,606 | idem | idem |
| [Sensors 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10610588/) | RF / W&D / HyAttn / propus | AUC | 0,804 / 0,862 / 0,907 / 0,923 | 5 subseturi stratificate | nespecificat |
| [Mervecaliskann](https://github.com/Mervecaliskann/electricity-theft-detection) (nerevizuit) | XGBoost | ROC-AUC / PR-AUC | 0,824 / 0,429 | holdout 20% | declarat fără scurgeri |
| [WITS](https://ajic.wits.ac.za/article/view/20652) | fuziune 1D+2D + SMOTE | AUC | 0,967 | neclar | SMOTE pe tot setul |

Cifrele peste 0,95 vin din lucrări cu SMOTE pe tot setul sau cu protocol neclar; le tratăm ca suspecte. Un interval realist, fără scurgeri: ROC-AUC 0,80-0,92 și PR-AUC în jur de 0,43 (față de 0,085 la întâmplare). Un ROC-AUC cinstit de 0,82-0,90 e mai credibil decât 0,97. Critici publicate despre scurgeri în evaluare: [audit 2026](https://www.sciencedirect.com/science/article/pii/S2590123026041204) (doar rezumatul, pagina a dat 403).

## 5. Calibrare și "nu sunt sigur" (conformal)

**Calibrarea.** În scikit-learn 1.9, `CalibratedClassifierCV(cv="prefit")` nu mai există; varianta corectă, testată în mediul nostru: `CalibratedClassifierCV(FrozenEstimator(model), method="isotonic").fit(X_cal, y_cal)`. Calibrăm un singur scor binar pentru planificator, `p_problemă = P(defect) + P(manipulare)`, pe setul de calibrare (separat de antrenare). Măsurăm Brier = medie((p - y)²), ECE pe bin-uri pe cuantile și diagrama de calibrare.

**Intervalul de probabilitate** (`interval_low`, `interval_high`): Venn-ABERS inductiv. Pentru un scor s, potrivim două regresii izotone pe calibrare plus punctul (s, 0), respectiv (s, 1), și obținem p0 ≤ p1. Scorul calibrat e p1 / (1 - p0 + p1). Calculăm pe o grilă de ~200 de cuantile și interpolăm (10.000 de puncte în ~0,4 s). Intervalul arată incertitudinea calibrării, nu a modelului; cazurile neclare le prinde conformal-ul.

**"Nu sunt sigur" prin conformal Mondrian** (pe clase). Pe calibrare, scorul de neconformitate e s_i = 1 - p(clasa adevărată). Pentru fiecare clasă c, pragul q_c e cuantila de ordin ⌈(n_c + 1)(1 - α)⌉ / n_c. Pentru un contor nou, mulțimea de predicție conține clasele c cu 1 - p_c ≤ q_c:
- {normal} → nicio acțiune;
- {problemă} → lucrare pentru echipă;
- {normal, problemă} sau mulțime goală → `abstain=True`, "nu sunt sigur", decide un om.

Garanția, într-o propoziție: dacă datele noi seamănă cu cele de calibrare, mulțimea conține clasa adevărată în cel puțin 1 - α din cazuri, pe fiecare clasă. Alegem α după câte cazuri pot verifica oamenii pe zi și raportăm rata de abținere; un test pe date sintetice grele a trimis 89% din cazuri la om la α = 0,1, deci α se fixează după măsurare.

**Pachete:** MAPIE 1.6.0, crepes 0.9.1 și venn-abers 1.5.4 există pentru Python 3.12, dar implementarea manuală are ~50 de linii și nu adaugă dependențe. O scriem noi.

## Surse

- SGCC: https://github.com/henryRDlab/ElectricityTheftDetection ; https://ieeexplore.ieee.org/document/8233155/ ; https://www.kaggle.com/api/v1/datasets/view/bensalem14/sgcc-dataset ; https://arxiv.org/pdf/2002.06219 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC10610588/ ; https://ajic.wits.ac.za/article/view/20652 ; https://github.com/Mervecaliskann/electricity-theft-detection
- Low Carbon London: https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d ; https://creativecommons.org/licenses/by/4.0/ ; https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london ; https://zenodo.org/record/7362093 ; https://datashare.ed.ac.uk/handle/10283/3647
- Atacuri și defecte: https://arxiv.org/pdf/1809.01774 ; https://arxiv.org/pdf/2010.09212 ; https://dblp.org/rec/journals/tsg/JokarAL16.html ; https://dblp.org/rec/journals/tsg/PunmiyaC19 ; https://docs.oracle.com/en/industries/utilities/rate-cloud/264/rcs-user-guides/Topics/D1_BG_About_IMD_Validations.html ; https://www.ercot.com/files/docs/2013/11/11/04a_oncor_ams_vee_tutorial_with_estimation_examples_110413.pdf ; https://www.aemo.com.au/-/media/files/electricity/nem/retail_and_metering/load_tables/metrology-procedure-part-b-v61.pdf ; https://www.floridapsc.com/library/FILINGS/2013/04142-2013/04142-2013.pdf
- Calibrare și conformal: https://arxiv.org/abs/2107.07511 (Angelopoulos & Bates) ; https://arxiv.org/abs/1211.0025 (Vovk & Petej, Venn-ABERS) ; https://scikit-learn.org/stable/modules/calibration.html ; https://scikit-learn.org/stable/modules/generated/sklearn.frozen.FrozenEstimator.html
