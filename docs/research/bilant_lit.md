# Bilanț pe post: cercetare din literatură și surse publice

Data: 2026-11-07. Ce nu am găsit scriu clar „negăsit". Cifrele fără URL sunt marcate IPOTEZĂ.
Sursele PDF mari le-am citit local (text extras), nu doar din rezumate.

---

## 1. România / ANRE: CPT și contoare de balanță

### 1.1 Cât CPT are Rețele Electrice (date reale, ale lor)

Sursă principală: Planul de dezvoltare Rețele Electrice România 2026-2035 (variantă de consultare), cap. 2.3
https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf

CPT total înregistrat, procent din energia consumată (tabelele 2.16, 2.26, 2.38 din plan):

| Zonă | 2021 | 2022 | 2023 | 2024 | 2025 (plan) |
|---|---|---|---|---|---|
| Muntenia | 8,99% (825 GWh) | 9,03% | 9,08% | 9,05% (825 GWh) | 8,93% (795 GWh) |
| Banat | 8,87% (508 GWh) | 9,10% | 9,18% | 9,11% (488 GWh) | 8,96% |
| Dobrogea | 8,58% (482 GWh) | 7,56% | 8,17% | 7,98% (439 GWh) | 8,09% |

Cât din CPT e pe joasă tensiune (JT), 2024 (aceleași tabele):
- Muntenia: 65,46% din pierderi sunt pe JT; JT primește 56% din energie.
- Banat: 65,09% din pierderi pe JT; JT are 50% din energie.
- Dobrogea: 50,01% din pierderi pe JT (52,46% în 2025 plan); JT are 50% din energie.

Ținta/prognoza de CPT pe JT, Muntenia (fig. 2.18 din plan; „raportul dintre pierderile de pe nivel și energia care intră pe nivel"):
JT 10,90% (2025), 10,69% (2026), 10,47% (2027), 10,20% (2028), 9,92% (2029). MT 2,84% → 2,75%. IT 0,55% → 0,53%.
Pentru Banat și Dobrogea figurile 2.20 și 2.22 sunt imagini; cifrele nu s-au putut extrage (negăsit în text).

Concluzie pentru noi: pe JT, pierderea totală (tehnică + comercială) e cam 10-11% din energia care intră în rețeaua de JT, în Muntenia. Asta e media pe operator, nu pe post.

### 1.2 Cât e nontehnic

- Planul separă pe JT „CPT tehnic" și „CPT comercial", dar împărțirea e în grafice-imagine (fig. 2.19, 2.21, 2.23). Procentele: negăsit.
- Energie furată identificată și facturată în 2024 (plan, cap. 2.3): Muntenia 1.393,977 MWh; Banat 582,434 MWh; Dobrogea 316,372 MWh.
  Raportat la CPT 2024 (825 / 488 / 439 GWh) sunt doar cam 0,17% / 0,12% / 0,07% din CPT. Adică: furtul DEPISTAT e mic; cât furt există în realitate nu se știe din documentul public. (Calcul propriu din cifrele de mai sus.)
- Planul spune că CPT tehnic are ponderea cea mai mare în amprenta de carbon a companiei (cap. 2.x, secțiunea GES), deci partea tehnică e majoritară în CPT total, fără procent.
- Context general: studiile din altă parte vorbesc de NTL „până la 40%" în Brazilia, India, Malaezia, Liban (nu România): https://ar5iv.arxiv.org/html/1606.00626

### 1.3 Ținte ANRE și metodologie

- Metodologia de stabilire a tarifelor pentru perioada a V-a este în Ordinul ANRE 67/2024 (MO 948/20.IX.2024): https://www.reteleelectrice.ro/wp-content/uploads/ordinul-anre-67-2024.pdf (am citit textul).
  - Art. 118: ținta CPT util propusă pe JT pentru primul an trebuie să fie mai mică decât media celor mai mici două valori realizate în perioada a IV-a.
  - Art. 119 alin. 6: pe JT, ținta scade liniar cu cel puțin 15% din punctul de referință până la sfârșitul perioadei a V-a (MT: cel puțin 6%). ANRE reduce cu prioritate CPT pe JT (alin. 3).
  - Art. 118 alin. 6: operatorul trebuie să împartă ținta în CPT util tehnic și CPT util comercial.
  - Ținta numerică exactă pe operator (% pe JT) pentru 2025-2029: negăsită în textele publice citite; ea ține de ordinele anuale ANRE.
- Ordinul 169/2018 (varianta anterioară): https://reteleelectrice.ro/content/dam/e-distributie/energia_electrica-in-casa-ta/2024/legislatie-secundara/ordin-169-2018/Metodologie-de-stabilire-a-tarifelor.pdf (nu l-am putut descărca ca text; nu citez cifre din el).

### 1.4 Prețul la care se recunoaște CPT

- Regula (Ord. 67/2024, art. 126 alin. 3): prețul recunoscut pentru CPT = minimul dintre prețul realizat de operator și un preț de referință = media prețurilor operatorilor majorată cu 5%. Dezechilibrele se limitează la 5% din cantitate.
- Valoare lei/MWh a energiei CPT: negăsită. Ce există public e componenta de tarif, nu prețul de achiziție. Exemplu, tarife valabile din 1 ian 2026, operatorul Distribuție Energie Electrică România (Electrica, NU Rețele Electrice), MO 1173/18.XII.2025, Ordin 78/2025:
  https://www.reteleelectrice.ro/wp-content/uploads/ordinul-nr-78-2025.pdf
  - JT: tarif 240,02 lei/MWh, din care non-CPT 139,45; CPT util 80,60; CPT util suplimentar capitalizat 19,97.
  - MT: 83,36 total, CPT util 31,86. IT: 31,96 total, CPT util 7,15.
  - Cum componenta CPT pe JT e cam 100,57 lei/MWh (80,60 + 19,97) la o energie distribuită pe JT, ea include și volumul de CPT, nu doar prețul. Nu o folosim ca preț al energiei.

### 1.5 Contoare de balanță și SMI în România

- Planul de dezvoltare 2026-2035 (sursa de la 1.1) cere ca infrastructura SMI să permită „cel puțin un contor pentru balanță la fiecare post de transformare, pentru identificarea pierderilor tehnice și nontehnice prin analiza balanțelor de energie"; funcția e declarată obligatorie, iar contoarele de balanță sunt „componente necesare".
- Planul menționează și „instalarea grupurilor de măsurare pentru balanță pe liniile de MT, în posturile de transformare, pentru identificarea zonelor cu CPT ridicat". Calendarul SMI e conform Ordinului ANRE 177.
- Proiect pilot: Bărăbanț, Alba Iulia, 8 posturi de transformare, 1.342 consumatori (1.142 monofazați, 200 trifazați), 8 contoare de balanță trifazate semidirecte, 8 concentratoare. Scop declarat: pierderi comerciale mai mici pe JT; fără cifră de reducere.
  https://alba24.ro/cetatenii-unui-cartier-din-alba-iulia-vor-beneficia-de-contoare-inteligente-pentru-masurarea-energiei-electrice-941430.html
- Rețele Electrice avea de gând să ajungă la cca 1,7 milioane de contoare inteligente până la sfârșitul lui 2024 (presă, neconfirmat de documentul oficial): https://adevarul.ro/economie/numarul-contoarelor-inteligente-instalate-de-2359965.html
- Câte posturi au deja contor de balanță: negăsit.
- Contoarele „semidirecte" au transformatoare de curent: de aici riscul de raport TC greșit (ex. 2x) din ipotezele noastre de diagnostic.

---

## 2. Practica DSO europeni și pierderile tehnice normale pe JT

### 2.1 Bilanț pe post la DSO europeni

- Pentru e-distribuzione, i-DE, EDP, Endesa „balance de energía por centro de transformación": negăsit într-un document public cu metodă și cifre în căutările făcute. Nu inventăm.
- Ce am găsit în schimb:
  - ComEd (SUA): contoare cu transformator greșit în GIS, estimat 193.000 de contoare, aproape 5% din clienți; s-au folosit date AMI și nepotriviri de întreruperi. https://www.tdworld.com/smart-utility/article/20966749/comed-corrects-meter-transformer-mismatches
  - Siemens EnergyIP Analytics și Itron Grid Connectivity vând exact detecția legăturilor contor-transformer și fază din date AMI (surse de tip vendor, fără cifre de acuratețe verificate): https://assets.new.siemens.com/siemens/assets/api/uuid:e9193aad-139d-47f7-b60c-365b6ee78408/emdg-b10132-00-4aus-onepager-eipas-144.pdf
  - UK: proiectul Losses Investigation (WPD/National Grid) a urmărit pierderile tehnice pe JT și informația minimă pentru a le prezice: https://www.westernpower.co.uk/innovation/projects/losses-investigation (cifre JT din raportul de închidere: negăsite).
  - Glauner et al. spun că bilanțul de energie e o metodă clasică, dar cere topologie corectă și citirea simultană a transformatorului, feederelor și contoarelor; în rețele care se schimbă, cu infrastructură defectă, dă bilanțuri greșite: https://ar5iv.arxiv.org/html/1606.00626. Exact de asta modelul nostru învață pierderea normală a fiecărui post și nu presupune zero.

### 2.2 Pierderi tehnice tipice

- Pierderi tehnice pe toată distribuția în UK: 5,8-6,6% din energia livrată: https://nationalgrid.co.uk/innovation/projects/losses-investigation (valoare pentru toată distribuția, nu doar JT).
- Transformatoarele de distribuție și cablurile: 4-6% (UE, manual de capacitare): https://capacity4dev.europa.eu/sites/default/files/fiche_5.5_grid_loss.pdf (acoperă transformator + cabluri, nu doar JT).
- Un singur studiu (Sri Lanka) dă 2,6% pierdere tehnică JT într-o zonă: https://dl.lib.uom.lk/items/d9438cb6-17ca-48e9-936b-a732a2b29125. Nu e comparabil direct.
- Realitatea RER: CPT total pe JT cam 10-11% (secțiunea 1.1), incluzând partea comercială. Dacă tehnicul JT tipic e 3-6% (IPOTEZĂ, interval din sursele de mai sus), restul de 4-7 puncte ar fi comercial + erori de măsură. Asta e o ordine de mărime, nu o măsurătoare.
- Pierderi fixe (fier din transformator) vs variabile (cupru): fixe cam 1/4-1/3 din pierderile tehnice, după o sursă secundară din căutare (fără URL verificat → IPOTEZĂ).

### 2.3 Cum cresc pierderile cu sarcina

- Pierderea în cupru ∝ I² · R; pierderea în fier e aproape constantă. Pierdere post/zi = P0·24 h + Pk·Σ(S_t/S_n)²·Δt.
- Factor de pierderi din factor de sarcină (relație empirică Buller-Woodrow 1928): LsF = 0,3·LF + 0,7·LF²; coeficienții variază (0,1-0,3), iar la transformatoare de distribuție apare 0,15/0,85 (Hoebel). Surse: https://en.wikipedia.org/wiki/Load-loss_factor și https://interchange.puc.texas.gov/Documents/52195_453_1171541.PDF. O sursă blog dă 5-15% eroare față de calculul din măsurători (nesigură).
- Valori calculate de noi din formulă: LF 0,3 → 0,153; LF 0,5 → 0,325; LF 0,7 → 0,553.
- Cu date la 15 min nu mai avem nevoie de aproximare: LsF = media(P²)/max(P)² din profilul real (sursa: aceeași pagină Wikipedia, metoda directă).

---

## 3. Literatură NTL: bilanț + scoruri pe client

1. Glauner et al. 2017, „The Challenge of Non-Technical Loss Detection Using AI: A Survey", IJCIS 10: 760-775. Două familii: sisteme expert și ML. Precizia se raportează rar, des doar acuratețea și recall-ul; AUC apare într-o singură lucrare. Exemple din lucrările citate: SVM recall 0,53-0,77; SOM (2K clienți) precizie 0,85; NN (22K clienți) precizie 0,65, recall 0,29. https://ar5iv.arxiv.org/html/1606.00626 și https://arxiv.org/pdf/1606.00626
2. Glauner et al. 2016, „Large-Scale Detection of NTL in Imbalanced Data Sets": avem mult mai mulți clienți normali decât cu pierderi; acuratețea e înșelătoare. https://www.arxiv.org/pdf/1602.08350v1
3. Jokar, Arianpoo, Leung 2016, IEEE Trans. Smart Grid 7(1): 216-226. Cea mai apropiată de ideea noastră: contoarele de transformator aleg zonele cu risc, apoi anomaliile de consum aleg clienții; combinația cu transformator + detector de anomalii face metoda robustă la schimbări nevinovate de consum. Test pe 5000 de clienți; cifre de detecție/fals pozitiv: negăsite fără textul complet. https://dblp.dagstuhl.de/rec/journals/tsg/JokarAL16.html
4. Revizuiri: Guarda et al. (MDPI Energies 2023) clasifică metodele în bazate pe rețea, pe date, hibride: https://www.mdpi.com/1996-1073/16/4/2054. Messinis & Hatziargyriou 2018, „Review of non-technical loss detection methods" (EPSR): nu am găsit rezumatul sau cifre; apare doar ca titlu la https://www.peeref.com/works/20961113. Nagi et al. (SVM + fuzzy, 2010): recall 0,72 pe cca 100K clienți, via Glauner (sursa 1).
5. Câștig de precizie din combinarea bilanț + scor client: NEGĂSIT în nicio lucrare găsită. Nu avem o cifră publică „+X puncte de precizie". Formulăm ca IPOTEZĂ de produs (bilanțul reduce spațiul de căutare la posturile cu exces, deci precizia pe client crește), de măsurat noi pe date sintetice.

---

## 4. Client mapat la post greșit / fază greșită

- Pezeshki & Wolfs, AUPEC 2012: corelație între seria de tensiune a clientului și a transformatorului; scopul era estimarea pierderilor din dezechilibru. Precizie numerică din rezumat: negăsită. https://espace.curtin.edu.au/handle/20.500.11937/45952?show=full. O lucrare înrudită (ISGT Europe 2012) a identificat corect faza la 75 de consumatori pe un feeder: https://espace.curtin.edu.au/handle/20.500.11937/22236
- Short 2013 și Olivier 2018: negăsite (nu confirm conținutul).
- Comparație din 2022 (ar5iv 2204.06372, 6 feedere europene, 20 de zile de date): corelație Pearson de tensiune cu referință transformator = 100% pentru contoare clasa 0,2s la 0,2s; 97,2% la 0,5s; 95,0% la rezoluție de tensiune 1,0 V. Cu referință client trifazat scade la 62,8% în cel mai prost caz; K-means 52,5-71%; corelație de putere 39-97%. Tensiunea bate puterea. https://ar5iv.labs.arxiv.org/html/2204.06372 . Rezoluția de timp (15 min / orar) nu e declarată; negăsită.
- National Grid UK (teren): 83% acuratețe la validare, posibil mai mare din referințe de tensiune greșite la unele stații; clusteringul depinde de numărul de contoare pe fază. https://nationalgrid.co.uk/downloads-view-reciteme/628641
- Pereche contor-transformer din consum (regresie/LASSO pe contorul transformatorului): nu am găsit o sursă cu cifre. Ideea (IPOTEZĂ): dacă un client e mapat greșit, suma contoarelor postului A nu explică profilul orar al postului A, iar adăugarea lui din postul B îl explică; se testează cu regresie nenegativă pe 15 min.
- Rata erorilor de mapare în GIS: singura cifră găsită e ComEd, ~5% din baza de clienți (initial, 193.000 de contoare); sursele mai spun „erori extinse de conectivitate în GIS" (FortisBC/PwC, https://www.awesense.com/case-studies/project-greenlight/). „Câteva % până la 10%+": nu am găsit sursă pentru limita de sus.
- Tensiunea la contor nu e disponibilă dacă nu e activat profilul de tensiune; de verificat dacă setul de date îl are.

---

## 5. Dezechilibrul de faze și pierderile

- Formula: pierderea pe faze = R_f·(I_a² + I_b² + I_c²); în neutru = R_n·I_n², cu I_n = suma vectorială (fazori) a curenților de fază. La aceeași sumă de curenți, I_a²+I_b²+I_c² e minim când sunt egali: pierderea în plus = R_f·3·(σ de curent)² + R_n·I_n². (Deducere proprie din I²R.)
- Fang & Ma 2020, IET GTD 14(4): 675-681 (Univ. Bath): curenții dezechilibrați cresc pierderile de fază cu „aproximativ 33%"; pe linii până la 33% din pierderile de conductoare, în transformatoare până la 27% din pierderile în cupru; la WPD, mai mult de 50% din rețelele JT au dezechilibru notabil, iar faza cea mai încărcată o depășește pe cea mai slabă cu peste 50% în mod frecvent. Atenție: „până la" e maxim, nu valoare tipică. https://doi.org/10.1049/iet-gtd.2019.1036 (PDF la https://kh.aquaenergyexpo.com/wp-content/uploads/2023/03/Assessment-Of-Additional-Phase-Energy-Losses-Caused-By-Phase-Imbalance-For-Data-Scarce-LV-Networks.pdf)
- Alte cifre (din rezumate de căutare, sursă secundară): transformator de 200 kVA: pierderile de 6,23% la dezechilibrul cel mai mare față de 0,22% la cel mai mic, https://jurnalelektro.petra.ac.id/index.php/elk/article/view/16701 (studiu indonezian, nu l-am citit integral).
- Remediu: reechilibrarea (mutarea clienților monofazați între faze) reduce pierderea în plus; un articol din Bosnia a redus factorul de dezechilibru și pierderile pe o rețea JT reală (cifră %: negăsită). Un calcul de load-flow pe feeder e necesar pentru economia exactă.
- Pentru model: dezechilibrul crește pierderea tehnică a postului. Dacă un post cu dezechilibru mare iese cu exces de bilanț, o parte e tehnică și nu furt. De aceea măsurăm dezechilibrul (max/min curent pe fază) la contorul de balanță.

---

## Ce folosim în model

1. Ținta de bilanț: pierdere totală JT în Muntenia ≈ 10,9% (2025) → 9,9% (2029) din energia care intră pe JT (Plan Rețele Electrice, fig. 2.18, secțiunea 1.1). Folosim ca plafon de plauzibilitate pentru media pe operator, nu pentru un post.
2. Pierdere normală a unui post: model = P0·24 + k·Σ(S_t/S_n)²·Δt, cu P0 și k învățate pe istoricul postului (formă I²R, secțiunea 2.3). Pierderea tehnică JT inițială, ca prior: 3-6% din energia postului (IPOTEZĂ din intervalele din 2.2; de calibrat pe date).
3. Factor de pierderi: LsF = 0,3·LF + 0,7·LF² doar când avem doar zilnic; cu 15 min folosim media(P²)/max(P)² (secțiunea 2.3).
4. Dezechilibru: pierdere în plus de faze, trecută ca variabilă în model (ex. (Imax−Imin)/Imedie). Ca ordine de mărime, maximum 33% din pierderile de conductoare (Fang & Ma 2020), tipic mult mai mic (IPOTEZĂ: 5-15% din pierderea tehnică, nesprijinit de o sursă).
5. Pragul de alarmă: reziduu = (energie post − Σ contoare) − pierdere prezisă; alarmă la reziduu > 3σ din istoricul postului (IPOTEZĂ), cu cel puțin 2-3 zile consecutive ca să tăiem zgomotul.
6. Diagnostic de cauză (reguli, IPOTEZĂ):
   - Salt brusc, constant, de factor ~2 (sau 0,5) față de istoric și de suma contoarelor → raport TC greșit pe contorul de balanță.
   - Reziduu dintr-un post pozitiv și în alt post vecin negativ de aceeași mărime → client mapat la post greșit (cerem și regresia de la secțiunea 4).
   - Exces lent crescător, concentrat pe o fază → furt înainte de contor sau bypass; dezechilibru de faze mare fără exces → pierdere tehnică.
   - Contor client cu consum plat sau zero față de vecini → contor defect.
7. Mapare client-post: verificare prin corelația seriei de tensiune cu referința de transformator (acuratețe 95-100% în cazul bun, 83% în teren; secțiunea 4); se folosește doar dacă datele conțin tensiune. Altfel, regresia nenegativă pe consum (IPOTEZĂ).
8. Rata de erori de mapare pentru datele sintetice: 5% din clienți (ComEd, secțiunea 4); eticheta „sintetic" obligatorie în date.
9. Nu promitem câștig de precizie din combinarea bilanț + scor client: nu există cifră publică (secțiunea 3); o măsurăm pe simulare.
10. Furt depistat: 2024 la RER doar 316-1.394 MWh pe regiune; folosim ca ordin de mărime pentru rata de furt depistat în simulare, nu pentru cea reală (secțiunea 1.2).
11. Mesaj către jurați: Rețele Electrice cere deja, în planul oficial, contor de balanță în fiecare PT (secțiunea 1.5); produsul nostru e stratul de analiză care folosește datele acelea.
