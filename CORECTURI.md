# Corecturi Daybreak înainte de jurizare

SmartHack 2026, 7 noiembrie. Lista tuturor problemelor găsite pe site-ul live
(https://daybreak.ghiseateodor245.workers.dev), fiecare cu ce trebuie schimbat și cum verifici că e gata.

Poate fi dat ca atare unui agent de cod (Claude Code) în repo-ul care face deploy-ul site-ului
(CyberPunks, nu folderul local `web/`, care are rutele vechi `/bilant`, `/diagnostic`, `/clasament`).

## Reguli pentru toate corecturile

1. **Nu inventa cifre.** Orice număr de pe site vine dintr-o rulare a agentului sau dintr-un raport de evaluare
   (`reports/A|B|C/...`). Dacă o cifră nu există încă, se calculează din cod sau rămâne scrisă ca „de măsurat”.
2. **O singură sursă de adevăr.** Landing-ul, consola (`/app`), `/rulare`, `/modele`, `/jurnal` citesc aceeași
   rulare (același `PLAN-...`, același instantaneu). Nicio cifră copiată de mână în componente.
3. **Fiecare corectură = un commit separat**, cu mesaj clar (ex. `fix(coada): arata cele doua cauze la abtinere`).
   Juriul PPC punctează istoricul de commit-uri.
4. După fiecare corectură, rulează verificarea din secțiunea „Gata când” și bifează.

Prioritate: **P0** = azi, înainte de orice altceva · **P1** = înainte de pitch · **P2** = dacă rămâne timp.

---

## P0-M. Răspunsuri de la mentor (7 noiembrie, seara)

Acestea schimbă premise din tot site-ul, deci au prioritate peste restul listei.

### P0-M1. Contoarele citesc la 5 minute, nu la 15

**Ce a spus mentorul.** Datele din contoare se înregistrează la 5 minute.

**Ce faci.**
- Înlocuiește peste tot „la 15 minute” cu „la 5 minute” (hero, „Cum funcționează”, „Global”, features, pagina de etică din P1-2).
  Caută: `15 min`, `15 minute`, `96 citiri`.
- Volumul din P1-3 devine **2 mil. contoare × 288 citiri/zi ≈ 576 mil. rânduri pe zi** (de 3× mai mult). Măsurătoarea de scalare
  se face pe acest volum.
- Bilanțul pe post se calculează pe intervale de 5 minute (sau agregat la oră, dar spus explicit).
- Datele publice din demo nu sunt la 5 minute (Londra e la 30 min, SGCC e zilnic). Scrie asta pe `/modele` și pe pagina de date:
  „în demo, date la 30 min / zilnice; în producție, 5 min”. Nu pretinde că modelele au fost antrenate la 5 minute.

**Gata când.**
- [ ] Căutarea după `15 min` în cod nu mai găsește nimic despre contoare.
- [ ] Rezoluția datelor din demo e scrisă separat de rezoluția din producție.

### P0-M2. Echipele nu pleacă automat a doua zi

**Ce a spus mentorul.** Se evaluează urgența problemei. Dacă nu e ceva de tipul risc de incendiu, se așteaptă până la sfârșitul
săptămânii.

**De ce contează.** Tot site-ul e construit pe „unde merg **mâine** echipele” (titlu, hero, „Planul de mâine”, „Echipele de mâine”,
„agentul îl reevaluează mâine”). Pentru PPC asta nu e procesul real.

**Ce faci.**
- Agentul împarte lucrările în două: **urgent** (risc de incendiu sau de siguranță: supratensiune, nul întrerupt, asimetrie mare
  de tensiune, încălzire) → echipă cât mai repede; **planificat** → intră în tura de la sfârșitul săptămânii.
- Fiecare lucrare arată clasa de urgență și motivul ei, scris (ex. „tensiune 1,18 față de nominal timp de 40 min: risc de incendiu”).
- Pentru lucrările planificate, agentul arată **cât costă așteptarea** până la tura de vineri (lei pierduți pe zi × zile rămase).
  Dacă așteptarea costă mai mult decât o deplasare în plus, propune mutarea mai devreme, iar decizia e a dispecerului.
- Redenumește: „Planul de mâine” → „Planul săptămânii” (cu o listă separată „Urgent azi”), „Echipele de mâine” → „Tura de vineri”,
  „reevaluează mâine” → „reevaluează la următoarea rulare”. Tagline: ceva de tipul „Ce e urgent azi, ce intră în tura săptămânii”.
- Simularea de câștig (35.077 lei/zi față de 23.552 lei/zi) se reface pe o săptămână, cu lucrările planificate grupate vineri.

**Gata când.**
- [ ] Niciun titlu sau buton nu mai spune că echipele pleacă automat mâine.
- [ ] Fiecare lucrare are urgent / planificat, cu motivul.
- [ ] Lucrările planificate arată costul așteptării până la sfârșitul săptămânii.

### P0-M3. Contorul defect la client: urgența se evaluează din dialog, nu din ce spune clientul

**Ce a spus mentorul.** Exemplul de lucrare care așteaptă până la sfârșitul săptămânii e clientul cu contorul defect.

**Ce e important.** De obicei clientul nu știe sigur cât de gravă e situația. Poate spune „nu merge contorul” când de fapt
e un risc de incendiu, sau poate suna panicat pentru ceva care poate aștepta. Deci trebuie să putem evalua **obiectiv**
situația din dialogul cu el, nu să-i preluăm verdictul.

**De investigat** (înainte să stabilim cum punem prioritățile în trasee):
- Ce întrebări îi punem clientului ca să separăm „poate aștepta” de „urgent”. Exemple: miroase a ars, se aude bâzâit sau
  pocnituri, e cald carcasa contorului, sunt scântei, a sărit siguranța, afișajul e stins sau arată o eroare,
  de când a început, mai are curent în casă.
- Cum combinăm răspunsurile cu ce vedem noi în date: contorul mai trimite citiri la 5 minute, tensiunea e în limite,
  sunt alarme de la contor, are vecini pe același post cu aceeași problemă.
- Cine pune clasa de urgență (operatorul call center, dispecerul, agentul ca propunere) și cum se înregistrează motivul.
- Dacă dialogul poate fi structurat (formular cu întrebări fixe) ca agentul să primească răspunsuri comparabile.

Până nu avem răspunsurile, pe site scriem că **regula de prioritizare e o propunere de validat cu PPC**, nu procesul lor.

### P0-M4. Ce se întâmplă dacă echipa nu termină la timp

**Întrebare deschisă.** Dacă o lucrare durează mai mult decât era estimat, echipa:
- **rămâne** la locul cu problema până o rezolvă, iar restul traseului se mută, sau
- **pleacă mai departe** la următorii din program, iar lucrarea neterminată se reprogramează?

Răspunsul schimbă felul în care agentul face traseele: cât timp de rezervă lasă între lucrări, dacă pune lucrările lungi
la final, ce se întâmplă cu lucrările rămase nefăcute (se reiau cu prioritate săptămâna următoare?) și dacă agentul trebuie să
refacă traseul în timpul zilei.

### P0-M5. Acordul clientului pentru acces, fără întâlnire fizică

**Ideea.** Acordul pentru vizită îl luăm la distanță. Procesul verbal se face tot la fața locului, pentru lucrarea în sine.
De verificat cu mentorul / juridicul PPC înainte să apară pe site ca proces sigur.

**Ce trebuie să conțină acordul la distanță.**
- **Identificarea clientului:** din contul lui din aplicația PPC sau cu cod OTP prin SMS pe numărul din contract
  (un simplu „da” la SMS e mai slab).
- **La ce își dă acordul:** data, intervalul orar, motivul pe înțeles („verificare contor”), numele sau legitimația echipei.
- **Cine va fi prezent:** clientul sau o persoană desemnată de el (familie, vecin), cu numele scris.
- **Dovada:** data, ora, canalul și textul exact acceptat, salvate în `/jurnal` (cu hash de audit, ca restul deciziilor).
- **Opțiuni pentru client:** să poată muta programarea sau refuza.

Acordul dat așa e semnătură electronică simplă (eIDAS); pentru o programare de vizită ar trebui să ajungă.

**Ce nu înlocuiește acordul.** Echipa nu intră într-o locuință goală pe baza unui SMS (risc de violare de domiciliu).
Trebuie să fie de față clientul sau persoana desemnată. Dacă contorul e la firidă sau pe stâlp, accesul în casă nu mai e necesar.

**Procesul verbal, la fața locului.**
- Se face la intervenție (verificare, înlocuire contor, constatare), semnat de persoana prezentă, pe tabletă, cu poze înainte și după.
- Clientul primește copia pe email sau în aplicație.
- Dacă refuză să semneze, se notează în procesul verbal.
- La suspiciune de furt, constatarea are reguli mai stricte (cine e de față, cum se contestă): de aflat cum face PPC azi.

**Fluxul în Daybreak.**
1. Agentul propune lucrarea planificată pentru tura săptămânii.
2. Clientul primește SMS sau notificare cu intervalul și motivul; confirmă cu OTP sau desemnează pe cineva.
3. Acordul intră în jurnal. Fără confirmare, lucrarea nu intră în traseu și agentul pune altă lucrare în loc.
4. La fața locului: legitimarea echipei, proces verbal pe tabletă cu poze, copie trimisă clientului.
5. Nu e nimeni acasă → „acces imposibil”, reprogramare. La risc de incendiu, echipa poate deconecta din exterior, fără să intre.

**Regulă de comunicare.** În mesajul către client nu apare niciodată „suspiciune de furt”, doar „verificare contor”
(se leagă de pagina de etică, P1-2).

**Gata când.**
- [ ] Fluxul de acord e descris pe site (pagina de etică sau a lucrării) ca propunere de validat cu PPC.
- [ ] O lucrare din demo arată starea acordului (cerut / confirmat / refuzat / acces imposibil) și apare în `/jurnal`.

### Alte întrebări pentru mentor

1. Cât durează în mod normal fiecare tip de lucrare (contor defect, verificare furt, problemă de tensiune)?
2. Câte ore are o tură și câte echipe sunt pe zonă? Echipele sunt specializate pe tipuri de lucrări?
3. „Sfârșitul săptămânii” înseamnă o zi fixă (vineri) sau lucrările se împart pe mai multe zile?
4. Ce semnale folosește PPC azi ca să decidă că ceva e risc de incendiu sau de siguranță?
5. Există termene legale sau din standardul de performanță ANRE pentru intervenții, după tipul problemei?
6. Clientul trebuie să fie acasă (contor în interior)? Cum se programează vizita cu el?
7. Cât timp e contorul defect, cum se facturează consumul (estimat)?
8. Contoarele trimit alarme proprii (deschidere capac, eroare internă, lipsă tensiune) și le putem folosi?
9. Are PPC azi un flux de programare sau de acord pentru vizită prin aplicație sau SMS?
10. Există un model de proces verbal pe care îl folosesc echipele (și se semnează pe hârtie sau pe tabletă)?
11. Ce procent din contoare sunt în interiorul locuinței și ce procent la firidă sau pe stâlp?

---

## P0. Credibilitate (Calitatea ML 25p, Demo 5p)

### P0-1. Cifrele diferă între pagini

**Problema.** Landing-ul și consola arată rulări diferite:

| Ce | Landing (`/`) | Consolă (`/app`) și `/rulare` |
| --- | --- | --- |
| Verificări la distanță | 485 | 504 |
| Lucrări la echipe / în trasee | 32 | 20 |
| Km de drum | 224 km (8 echipe) | 292 km |
| Lucrări pe surse A / B / C | 622 / 26 / 41 | 630 / 26 / 33 |
| Valoarea planului | 185.794 lei | (alt total pe consolă: 71.803 lei) |

Landing-ul pare să citească un JSON extras o dată (vezi `scripts/extract-daybreak.py`, `src/data/daybreak.json`),
iar consola citește ultima rulare.

**Ce faci.**
- Alege rularea de demo (scenariul `demo-vara`, 8 iulie 2025) și fixeaz-o ca instantaneu.
- Landing-ul citește din același instantaneu ca și consola (sau regenerează JSON-ul landing-ului din același `PLAN-...`).
- Aceeași definiție peste tot: „la echipe” = lucrări în trasee. Dacă landing-ul numără altceva, redenumește eticheta.
- Dacă butonul „Rulează agentul” poate produce o rulare nouă în timpul demo-ului, landing-ul trebuie să o urmeze
  sau să scrie explicit „rularea din <dată, oră>”.

**Gata când.**
- [ ] Toate cifrele din tabelul de mai sus sunt identice pe `/`, `/app`, `/rulare`.
- [ ] Un test sau script compară cifrele landing-ului cu cele din rulare și pică dacă diferă.
- [ ] Pe fiecare pagină apare id-ul planului sau data rulării de unde vin cifrele.

### P0-2. „Precizie peste 99%” e cifra de titlu

**Problema.** Pe `/modele` (tabelul de performanță, „Scoruri rapide”), pe `/rulare` („Precizie contoare peste 0,99”)
și pe paginile lucrărilor („Precizie la selecție peste 99%”), modelul A apare cu 1,00. Propria analiză a erorilor
spune că vine din 215 defecte evidente care umplu primele locuri. Un juriu va citi 99% ca scurgere de date.

**Ce faci.**
- Cifra principală a modelului A devine **precizia în primele K pe furturi reale (SGCC): 0,80 față de baseline**,
  iar a doua cifră **precizia pe anomalii subtile: 0,63 față de 0,07**.
- 1,00 pe Londra rămâne doar în tabelul complet, cu o notă de o frază: „vine din defectele evidente din test; vezi analiza erorilor”.
- Caută în cod toate aparițiile: `peste 99%`, `peste 0,99`, `precision_at_k` folosit ca metrică principală.

**Gata când.**
- [ ] Niciun card, titlu sau „scor rapid” nu mai arată 99% / 1,00 pentru modelul A.
- [ ] `/rulare` → „Scoruri model” arată 0,80 (SGCC) cu baseline-ul lui.
- [ ] Nota despre 1,00 există lângă tabelul complet.

### P0-3. Baseline-ul pe SGCC are trei valori

**Problema.** Același baseline apare ca **3,5%** (tabelul de performanță), **4%** (rezumatul analizei erorilor,
„regula simplă”) și **0,11 / 11%** (detaliile modelului, „regula simplă”), plus 0,16 pentru Isolation Forest.

**Ce faci.**
- Stabilește un singur baseline principal pentru SGCC și numește-l explicit (ex. „regula VEE: 0,11”).
- Celelalte (regula zero-consum 0,035, Isolation Forest 0,16) apar doar în tabelul complet, cu numele lor.
- Textul din analiza erorilor („față de 4% la regula simplă”) se aliniază la aceleași nume și valori.

**Gata când.**
- [ ] Căutarea după „SGCC” pe `/modele` dă o singură valoare pentru fiecare baseline numit.
- [ ] Peste tot unde scrie „regula simplă” e clar care regulă e.

### P0-4. Contradicție pe `/coada` („Nu sunt sigur”)

**Problema.** La PT-1182: textul spune „Modelul nu e sigur: două cauze aproape la egalitate”, dar indicatorul
arată „peste 99% scorul modelului”. În lista cazurilor, coloana „Încredere” arată 94–99% la abțineri.
Un caz trimis la om pentru că modelul nu e sigur nu poate afișa încredere de 99%.

**Ce faci.**
- Pentru motivul „Abțineri model”: în locul indicatorului, afișează **primele două cauze cu probabilitățile lor**
  (ex. „Furt înainte de contor 46% · Contor defect 41%”) și diferența dintre ele.
- Redenumește ce e acum „scorul modelului” în ce este de fapt (scor de anomalie / „cât de sigur e că e o problemă”)
  și separă-l de „cât de sigur e pe cauză”. Pe ecran apar amândouă, cu etichete diferite.
- Coloana „Încredere” din listă arată încrederea pe cauză (cea mică), nu scorul de anomalie.

**Gata când.**
- [ ] Niciun caz din „Abțineri model” nu afișează o singură cifră mare de încredere fără cele două cauze.
- [ ] Textul motivului și cifrele afișate spun același lucru.
- [ ] Verificat și pe mobil (375 px).

---

## P1. Criterii care lipsesc sau sunt slabe

### P1-1. Modelul de bilanț lipsește de pe `/modele` (Idee 25p, ML 25p)

**Problema.** Bilanțul pe post e chiar ideea punctată de PPC, iar agentul folosește `bilant-diagnoza-lgbm`
(apare pe `/coada`, în jurnal ca `R-FUSION-BILANT`). Pe `/modele` sunt doar A, B, C.
„Toate cele trei rapoarte sunt publicate” sugerează că al patrulea nu există.

**Ce faci.**
- Card complet pe `/modele` pentru modelul de bilanț, în același format ca A, B, C: set de test separat,
  baseline (ex. „lipsă > X% din energia ieșită”), metrica principală, toate metricile, matricea de confuzie
  pe cele 5 cauze (contor defect, furt înainte de contor, problemă tehnică, client la post greșit, contor de post setat greșit),
  analiza erorilor, comanda de reproducere.
- Dacă raportul nu există, se generează din codul de evaluare. Nu se scriu cifre de mână.
- Filtru nou pe `/modele`: „Bilanț”.

**Gata când.**
- [ ] `/modele` are 4 modele, iar bilanțul are baseline, test separat, analiza erorilor și comandă de reproducere.
- [ ] Comanda de reproducere rulează și dă aceleași cifre.

### P1-2. Pagina „Date și etică” (Siemens: Etică și responsabilitate)

**Problema.** Explicarea deciziilor e bună, dar despre protecția datelor nu există nimic pe site.
Consumul la 15 minute e dată personală (arată când e cineva acasă), iar sistemul poate indica „furt” la un client.

**Ce faci.** O pagină nouă (`/etica` sau o secțiune în `/demo`, cu link în sidebar) care spune, scurt:
- **Ce date folosim și de ce:** consum la 15 min, legătura client → post, vreme, preț. Nimic în plus (minimizare).
- **Pseudonimizare:** contoarele apar ca `MTR-…`, fără nume sau adresă în aplicație.
- **Acces:** cine vede ce (dispecer, echipă de teren, administrator).
- **Păstrare:** cât timp ținem datele brute și jurnalul.
- **Unde rulează:** în infrastructura PPC; în demo, date sintetice și publice (Londra CC BY 4.0, SGCC, OSM ODbL).
- **Om în buclă:** modelul nu acuză pe nimeni de furt. Trimite o verificare. Decizia și eventuala sancțiune sunt ale unui om.
  Clientul poate contesta.
- **Erori cunoscute:** alarmele false la consumatorii mici (din analiza erorilor A, secțiunea 5) și ce facem cu ele.
- **Jurnal și audit:** fiecare decizie are regulă, versiune de model și hash de audit; export JSONL.
- Cadrul legal amintit pe nume, fără a pretinde conformitate certificată: GDPR, AI Act (sistem de sprijin la decizie, cu supraveghere umană).

**Gata când.**
- [ ] Pagina există, are link din sidebar și din footer, și se citește în sub 2 minute.
- [ ] Fiecare afirmație corespunde cu ce face codul (ex. dacă scrie „pseudonimizat”, în UI chiar nu apar nume).

### P1-3. Pagina „Cost și scalare” (Siemens: Sustenabilitate)

**Problema.** Site-ul spune „peste 2 milioane de contoare la 15 minute”, dar nu spune cât costă să rulezi asta,
cine îl întreține și cum crește.

**Ce faci.** O secțiune sau un slide, cu cifre **măsurate**, nu estimate din burtă:
- **Volum:** 2 mil. contoare × 96 citiri/zi ≈ 192 mil. rânduri pe zi.
- **Timp de rulare azi:** 689 lucrări în ~24 s (din `/rulare`: estimare 15 s, decizie 7,8 s). Măsoară și pe un eșantion mai mare
  (ex. 10×, 100× contoare) și scrie cum crește.
- **Infrastructură:** modele LightGBM pe CPU, rulare zilnică pe lot (noaptea), site pe Cloudflare Workers.
  Cost lunar estimat **de calculat** din timpul măsurat × prețul unei mașini.
- **Cost față de câștig:** costul lunar de infrastructură față de câștigul net din simulare (35.077 lei/zi față de 23.552 lei/zi la regula simplă).
- **Întreținere:** cât de des reantrenăm, cum urmărim deriva (ex. calibrare ECE, rata de confirmare pe teren),
  ce face agentul dacă un model e oprit (cade pe reguli simple).

**Gata când.**
- [ ] Fiecare cifră are sursa (măsurătoare, raport, preț public).
- [ ] Există cel puțin o măsurătoare de scalare, nu doar rularea de 689 lucrări.

### P1-4. Pitch: o singură problemă principală (Idee 25p, Inovație Siemens)

**Problema.** Trei surse de lucrări (contoare, furtună, tensiune) diluează povestea „bilanț pe post”.

**Ce faci.**
- Landing și pitch: deschid cu **problema PPC**: energia pierdută peste cota recunoscută de ANRE și unde să trimiți echipele.
- Bilanțul pe post e soluția principală; furtuna și tensiunea apar ca „același agent merge și pentru…”.
- Un slide / bloc „Ce e nou”, maxim 3 puncte: confirmare încrucișată contor + bilanț; decizia în lei cu abținere; un agent pentru toate sursele.
- Un bloc „Ce trebuie confirmat cu PPC”: există contor de bilanț în posturi și în ce procent; lista client → post e de încredere;
  planul B (estimarea energiei intrate din clienți și din modelul rețelei).

**Gata când.**
- [ ] Primul ecran al landing-ului și primul slide numesc problema PPC în lei.
- [ ] „Ce e nou” și „Ce trebuie confirmat cu PPC” apar pe site.

---

## P2. Calitate și finisare

### P2-1. Robustețe arătată live (Robustețe 10p)

**Problema.** Carantina există, dar în demo arată „0 în carantină”; nimic nu demonstrează că funcționează.

**Ce faci.**
- Un comutator „Strică datele” pe `/rulare` (doar în demo) care injectează: o coordonată în afara țării, un scor imposibil,
  un contor blocat, 30% citiri lipsă la un post. Rularea arată ce a intrat în carantină și ce a ajuns la om.
- Un grafic pe `/modele`: metrica principală pe măsură ce cresc datele lipsă (0%, 10%, 30%, 50%).

**Gata când.**
- [ ] Cu comutatorul pornit, carantina arată > 0 și fiecare caz are motivul scris.
- [ ] Graficul de degradare există și vine din cod de evaluare.

### P2-2. Bucla de învățare din verdict (Agentul 25p)

**Problema.** Conceptul spune „echipa notează ce a găsit, modelul învață din verdict”. Pe site nu se vede.

**Ce faci.** Pe pagina unei lucrări: un buton „Închide cu verdict” (confirmat / nu s-a găsit nimic / altă cauză).
Verdictul apare în jurnal și se vede efectul: scor recalibrat, prag ajustat sau caz adăugat la „Cazuri similare”.
Dacă reantrenarea nu e implementată, scrie exact ce se întâmplă cu verdictul (ex. „intră în setul de reantrenare de vineri”).

**Gata când.**
- [ ] Un verdict dat în demo apare în `/jurnal` cu actorul „Om” și efectul lui.

### P2-3. Jargon pe ecranele dispecerului (Explicabilitate 10p, Utilitate Siemens)

**Ce faci.** Pe `/app`, `/coada`, `/lucrari/*`: înainte de PR-AUC, pu, SHAP, MAE, o frază simplă.
Exemple: „pu” → „tensiune față de nominal (1,10 = cu 10% peste)”; SHAP → „Ce a cântărit cel mai mult”.
Termenii tehnici rămân pe `/modele`.

**Gata când.**
- [ ] Pe ecranele dispecerului, orice termen tehnic are explicația lângă el.

### P2-4. `/jurnal`

- Tabelul iese din ecran la ~800 px lățime (coloana „Pragul” tăiată). Pe ecrane înguste: coloane secundare ascunse
  sau rândul transformat în card; tabelul nu împinge pagina lateral.
- Antetul rulării arată un șir tehnic brut (`scenariu demo-vara, data 2025-07-08, surse A=ok/model, A_bilant=ok/model, …`).
  Rescrie-l: „Scenariul de vară, 8 iulie 2025. Toate cele 4 surse au răspuns.”
- Filtrele (Sursa, Actor, Decizia) apar goale; afișează „Toate” ca valoare implicită.

**Gata când.**
- [ ] La 800 px și la 375 px, `/jurnal` nu are scroll orizontal pe pagină.
- [ ] Antetul e o frază, filtrele arată „Toate”.

### P2-5. Landing: cazul cu 0 lei

**Problema.** În „Bilanțul pe post”, cazul „PT-1241, Contorul de post setat greșit” arată **0 lei pe lună**,
ceea ce pare o eroare.

**Ce faci.** Explică de ce e 0 (contorul de post greșit nu înseamnă energie pierdută, ci un bilanț fals; valoarea e în
alarmele false evitate) sau alege alt exemplu pentru această cauză.

**Gata când.**
- [ ] Niciun card de pe landing nu arată 0 lei fără explicație.

### P2-6. README și repository (Demo și repository 5p)

- `web/README.md` descrie paginile vechi (`/bilant`, `/diagnostic`, `/clasament`, `/agent`). Actualizează lista de rute
  cu cele reale: `/app`, `/coada`, `/posturi`, `/lucrari`, `/jurnal`, `/alerte`, `/modele`, `/rulare`, `/demo`.
- README-ul principal: cum instalezi, cum rulezi agentul, cum refaci fiecare cifră (aceleași comenzi ca pe `/modele`),
  de unde vin datele și licențele lor, ce e sintetic.
- Verifică pe o mașină curată că pașii din README chiar merg.
- Commit-uri mici, fiecare corectură din acest fișier separat.

**Gata când.**
- [ ] Un coleg care n-a lucrat la proiect rulează README-ul de la zero și obține aceleași cifre.

---

## Verificare finală, pe criterii

| Criteriu | Corecturi | Bifat |
| --- | --- | --- |
| PPC · Ideea și relevanța (25) | P1-1, P1-4, P2-5 | [ ] |
| PPC · Calitatea ML (25) | P0-2, P0-3, P1-1 | [ ] |
| PPC · Robustețe (10) | P2-1 | [ ] |
| PPC · Agentul (25) | P2-2 | [ ] |
| PPC · Explicabilitate (10) | P0-4, P2-3 | [ ] |
| PPC · Demo și repository (5) | P0-1, P2-4, P2-6 | [ ] |
| Siemens · Inovație și creativitate | P1-4 | [ ] |
| Siemens · Utilitate practică | P2-3, P2-4 | [ ] |
| Siemens · Etică și responsabilitate | P1-2, P0-4 | [ ] |
| Siemens · Sustenabilitate | P1-3 | [ ] |

Ultimul pas: o trecere completă prin demo, ca o zi a dispecerului (deschide `/app`, vede cazurile la om, aprobă lista,
deschide o lucrare, vede jurnalul), pe desktop și pe telefon, fără nicio cifră care să difere între ecrane.
