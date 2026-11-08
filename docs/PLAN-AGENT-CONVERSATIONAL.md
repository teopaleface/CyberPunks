# Plan pentru agentul Daybreak cu trei tipuri de cont

Data: 7 noiembrie 2026. Stare: plan de produs și implementare, cerut de Teo. Funcțiile noi de mai jos nu sunt încă implementate sau testate. Interfața va fi în engleză; documentația și discuțiile echipei rămân în română.

Daybreak leagă clientul care semnalează o problemă, dispecerul care decide intervenția și tehnicianul care verifică în teren. Toți lucrează pe același caz, cu drepturi diferite. Modelul ML antrenat de echipă rulează local și produce estimările. LLM-ul înțelege conversația și cere acțiuni verificate de aplicație.

Prima versiune trebuie să funcționeze din toate cele trei conturi, prin text și prin voce în browser. Catalogul include 68 de cazuri pe roluri și 12 situații comune. Cele 16 cazuri marcate P0 formează versiunea pentru hackathon; restul au o etapă și o dependență clară.

## 1. Rezultatul urmărit

Un client spune că invertorul se oprește la prânz. Agentul identifică punctul de consum din cont, înregistrează sesizarea și consultă evaluarea tehnică potrivită. Dispecerul vede cauza estimată, datele disponibile și propunerea de intervenție. După aprobare, tehnicianul vede lucrarea și raportează verbal ce a găsit. Clientul primește starea verificată a propriului caz.

La fiecare pas putem arăta cine a cerut acțiunea, ce date și predicție au susținut-o, cine a aprobat și ce s-a salvat. Predicția, aprobarea, constatarea și confirmarea rezolvării sunt lucruri diferite.

### Deciziile pentru această propunere

- Exact trei roluri de cont: client, tehnician și dispecer. În interfață: Customer, Technician și Dispatcher.
- Un singur produs, un singur circuit al cazului și aceleași acțiuni pentru voce, text și butoane.
- Trei configurații conversaționale, câte una pentru fiecare rol, peste același serviciu de acțiuni. Configurația o alege serverul din contul autentificat.
- Operatorul de relații cu clienții este o vedere restrânsă a rolului dispecer. Nu adăugăm un al patrulea tip de cont. Permisiunea de a aproba planuri este distinctă și nu vine implicit cu această vedere.
- În demo, apelul înseamnă o conversație cu microfonul din site. Apelurile telefonice reale sunt o extindere separată.
- Modelul propriu rămâne modelul ML pentru energie. Un model de conversație extern îl poate folosi prin acțiunile aplicației, conform temei PPC.
- Noua funcție nu schimbă antrenarea, pragurile sau cifrele modelelor aflate în lucru în alte fire.

## 2. Ce există și ce trebuie construit

Situație verificată în codul local la redactare, nu printr-un test nou pe site-ul public.

| Componentă | Ce există | Ce lipsește pentru cele trei conturi |
|---|---|---|
| Modele locale | A pentru contoare, B pentru furtună, C pentru tensiune și bilanț pe post | Un adaptor care dă conversației doar rezultatele permise și suficient de recente |
| Planificator | Lucrări, prioritizare, trasee, ordine PDF, revizuire și aprobarea planului/listelor | Propuneri legate de caz și de versiunea planului; simulările cu resurse schimbate sunt funcții noi |
| Constatare din teren | API pentru confirmed, not_found, other_problem și no_access; jurnal și etichete pentru reantrenare | Legătura cu tehnicianul autentificat, confirmarea acțiunii, evitarea dublurilor și actualizarea cazului |
| Autentificare web | Conturi și sesiuni în Cloudflare KV, cu emulare locală | Rol, organizație, echipă autorizată și legătura clientului cu punctele de consum |
| Aprobări din site | Alegeri salvate separat pe utilizator în KV | Un rezultat operațional comun, văzut de toate rolurile; alegerile personale nu echivalează cu aprobarea planificatorului |
| API Python | Validarea intrărilor și blocarea rulărilor concurente | Autorizare pe rol și pe obiect; identitatea operatorului trebuie stabilită pe server |
| Acțiuni web | Rulare, revizuire, aprobare, cu rezultat afișat | Aplicarea acelorași drepturi inclusiv pe acțiunile existente; eliminarea interpretării unei aprobări doar locale drept aprobare operațională |
| Site public | Configurația Cloudflare citește planul demo salvat | Nu rulează modelele Python de pe calculator; accesul operațional la ele cere o legătură separată |
| Voce și text conversațional | Nu există încă integrarea ElevenLabs în dependențele aplicației | Sesiuni private, interfață, acțiuni, limite de consum, teste și revenire la text |
| Portal client și ecran tehnician | Consola este orientată spre dispecer | Două ecrane simple și proiecții ale datelor potrivite rolului |

Surse locale: [contractele](CONTRACTS.md), [planul existent](PLAN.md), [API-ul](../src/cyberpunks/api/app.py), [conturile](../web/lib/server/accounts.ts), [aprobările din site](../web/app/api/aprobari/route.ts), [acțiunile web](../web/lib/data/actions.ts), [constatările](../src/cyberpunks/planner/feedback.py) și [configurația publicării](../web/wrangler.jsonc).

## 3. Cele trei conturi

### Client

Prima pagină arată punctul de consum propriu, cazul activ și următorul pas. Clientul poate descrie problema, răspunde la întrebări, verifica starea și transmite disponibilitatea pentru acces. Vede o explicație destinată lui, fără date despre vecini, suspiciuni de fraudă sau planurile tuturor echipelor.

Contul poate avea mai multe puncte de consum autorizate. Când alegerea nu este clară, agentul întreabă. O adresă spusă în conversație nu dovedește dreptul asupra unui punct de consum.

### Tehnician

Prima pagină arată lucrarea curentă, următoarea oprire și ce trebuie raportat. Tehnicianul vede doar lucrările echipei sale, în domeniul său autorizat. Poate înregistra constatări și cere ajutor; nu își poate atribui singur alte echipe sau aproba planul global.

Vocea este folosită când omul este oprit și poate vorbi în siguranță. Produsul nu presupune că lucrează la instalație sau conduce în timpul conversației.

### Dispecer

Prima pagină arată ce cere o decizie, capacitatea disponibilă și schimbările importante. Dispecerul vede planul din zona sa, explicațiile și constatările, poate aproba sau amâna o intervenție și urmărește executarea.

Vederea de operator de relații cu clienții poate căuta un caz autorizat, pregăti un răspuns și înregistra o sesizare. Nu primește automat toate drepturile dispecerului de rețea.

### Reguli de acces

| Resursă sau acțiune | Client | Tehnician | Dispecer |
|---|---|---|---|
| Datele punctului propriu | Da, variantă pentru client | Doar dacă are lucrare atribuită | În zona și organizația autorizate |
| Sesizare nouă | Pentru propriul punct | Constatare pe lucrarea proprie | În domeniul autorizat |
| Starea cazului | Doar cazul propriu | Cazul lucrării atribuite | Cazurile din domeniul autorizat |
| Predicție și motive tehnice | Rezumat verificat, fără informații interne | Detalii necesare lucrării | Detalii și comparații tehnice |
| Traseu | Fără traseul echipei | Doar al echipei proprii | Echipele din domeniul autorizat |
| Constatare de teren | Poate spune că simptomul persistă; nu validează inspecția | Da, cu confirmare | O vede și poate cere clarificări |
| Aprobare sau schimbare de plan | Nu | Nu | Da, cu permisiunea explicită |
| Date despre alte puncte de consum | Nu | Doar minimul necesar lucrării | Doar în domeniul autorizat |
| Schimbare de rol, echipă sau apartenență | Nu | Nu | Nu prin conversație sau editarea profilului |

Rolurile și apartenențele se atribuie printr-o procedură administrativă. Câmpul actual team, pe care utilizatorul și-l poate edita, rămâne o informație de profil până când există o asociere verificată pe server. Nu îl folosim pentru autorizare.

## 4. Priorități

- P0: funcționează în prima versiune, din toate cele trei conturi. Include drepturile, starea comună, jurnalul, vocea și textul.
- P1: după trecerea testelor P0, cu datele și adaptoarele deja disponibile.
- P2: dezvoltare după hackathon sau dacă rămâne timp măsurat. Include simulări suplimentare, integrarea fotografiilor și lucrul fără conexiune.
- P3: integrare cu sisteme reale, telefonie, notificări externe sau comenzi asupra echipamentelor. Cere acces și aprobare separate înainte de activare.

Toate rândurile de mai jos sunt cerințe propuse. Existența unui API parțial nu înseamnă că întregul caz este deja implementat.

## 5. Catalogul tehnicianului

| ID | Cererea sau situația | Rezultatul verificabil | Model sau date necesare | Etapă |
|---|---|---|---|---|
| T01 | "Ce am de făcut în tura mea?" | Lista lucrărilor atribuite, pe planul curent, cu orele din plan | Plan și apartenență verificată la echipă | P0 |
| T02 | "De ce verificăm acest contor sau post?" | Explicație din predicție, motive și calitatea datelor | A, bilanț sau C, după lucrare | P0 |
| T03 | "Care este următoarea oprire?" | Oprirea din traseul aprobat, cu ora planificată, fără a pretinde poziție GPS în timp real | Traseu aprobat și versiune de plan | P0 |
| T04 | "Am verificat. Defect confirmat." | Constatare confirmată de om, salvată o dată, legată de lucrare și predicție | API de constatare; etichetă pentru evaluare ulterioară | P0 |
| T05 | "Nu am avut acces la contor." | Rezultat no_access; cazul rămâne de rezolvat și ajunge la dispecer | Constatare și coadă comună | P0 |
| T06 | "Contorul de aici are alt identificator." | Neconcordanță înregistrată, fără constatare pe activul greșit | Registrul activelor și lucrarea atribuită | P1 |
| T07 | "Am găsit altă problemă decât cea estimată." | Rezultat other_problem și solicitare de analiză la dispecer | Predicție inițială și constatare structurată | P1 |
| T08 | "Am măsurat aceste valori." | Măsurători cu unitate, moment și proveniență; valorile imposibile cer corectare | Schema de măsurători; adaptor ML pentru o reevaluare validă | P1 |
| T09 | "Am observat o situație periculoasă." | Escaladare prioritară către om și aplicarea procedurii aprobate, fără instrucțiuni improvizate de manevră | Semnal uman de pericol; nu se așteaptă scorul ML | P1 |
| T10 | "Am început / am oprit / am terminat vizita." | Stare și timp înregistrate; terminarea vizitei nu înseamnă automat problemă rezolvată | Starea operațională nouă | P1 |
| T11 | "Întârziem la următoarea lucrare." | Întârziere și cerere de revizuire; clientului nu i se inventează o oră nouă | Plan și stare de teren | P1 |
| T12 | "Nu avem echipamentul necesar." | Blocaj explicit și solicitare către dispecer | Inventar și competențe; integrare nouă dacă lipsesc | P2 |
| T13 | "Drumul este blocat. Avem nevoie de alt traseu." | Propunere de traseu recalculat, aprobată înainte să înlocuiască lista | Replanificare și date rutiere disponibile | P2 |
| T14 | "Deschide ordinul de lucru." | Documentul echipei proprii, pentru planul corect | PDF existent și filtrare de acces | P1 |
| T15 | "Atașez o fotografie a situației." | Atașament legat de caz, fără diagnostic vizual automat pretins | Stocare și control de acces la media | P2 |
| T16 | "Nu am semnal. Păstrează nota pentru mai târziu." | Ciornă locală marcată netrimisă, apoi sincronizare cu confirmare | Stocare locală protejată și evitarea dublurilor | P2 |
| T17 | "Am greșit constatarea de mai devreme." | Rectificare ca eveniment nou, cu motiv; istoricul rămâne | Versiune de constatare și jurnal | P1 |
| T18 | "Predau lucrarea colegului." | Cerere de predare; schimbarea atribuirii este validată de dispecer | Apartenență și atribuire verificată | P2 |
| T19 | "Vreau să discut cu dispecerul." | Cerere de contact în coada potrivită; transfer numai dacă integrarea există | Coada comună; telefonie doar în P3 | P1 |
| T20 | "Fă rezumatul turei." | Lucrări vizitate, constatări, blocaje și ce rămâne deschis | Evenimentele echipei, fără estimări inventate | P1 |

## 6. Catalogul dispecerului

| ID | Cererea sau situația | Rezultatul verificabil | Model sau date necesare | Etapă |
|---|---|---|---|---|
| D01 | "Ce necesită o decizie din partea mea?" | Rezumat scurt al planului, cozii și schimbărilor, cu data și sursa | Plan, cazuri și alerte actuale | P0 |
| D02 | "De ce acest caz este înaintea celuilalt?" | Comparație între estimare, încredere, impact, cost și constrângeri | A, B, C sau bilanț și regulile planificatorului | P0 |
| D03 | "Arată lucrările de tensiune din zona mea." | Listă și hartă filtrate după date autorizate | Metadatele lucrărilor | P1 |
| D04 | "Aprob / resping / amân această intervenție." | Revizuire confirmată, motiv salvat și rezultatul replanificării | Revizuirea existentă, cu identitate și control de versiune | P0 |
| D05 | "Aprob planul sau lista acestei echipe." | Aprobare operațională legată de versiunea exactă, vizibilă celorlalte roluri | API de aprobare; nu alegerea personală din KV | P0 |
| D06 | "A apărut o sesizare nouă. Ce știm despre ea?" | Caz legat de punct/post și de o evaluare existentă validă sau de o cerere explicită de date | Asociere punct-post; A/C/bilanț după simptome și date | P0 |
| D07 | "La ce posturi merită verificat bilanțul mai întâi?" | Clasament din pierdere peste normal, încredere, valoare și cost | Modelul de bilanț și regulile actuale | P1 |
| D08 | "Unde este riscul cel mai mare de furtună?" | Zone și intervale de risc, cu prognoza și incertitudinea | B și vremea folosită de predicție | P1 |
| D09 | "Unde propunem poziționarea echipelor înaintea furtunii?" | Propunere fezabilă înainte de intervalul de risc și cerere de aprobare | B, capacitate și planificator | P1 |
| D10 | "Ce soluție de tensiune are costul cel mai mic și efect suficient?" | Compararea soluțiilor calculate și ipotezelor; nicio manevră fizică automată | C și calculul de rețea, cu intrări complete | P1 |
| D11 | "Ce rămâne neacoperit dacă avem mai puține echipe?" | Variantă separată de plan și diferențe față de planul activ | Adaptor nou de simulare a capacității | P2 |
| D12 | "Această echipă nu mai este disponibilă." | Schimbare confirmată a disponibilității și propunere de replanificare | Atribuiri și resurse versionate; extensie nouă | P2 |
| D13 | "A apărut un eveniment urgent după aprobarea planului." | Caz nou, reevaluare și diferențe explicate înaintea noii aprobări | Date noi și adaptor de ingestie; siguranța merge direct la om | P2 |
| D14 | "Echipa întârzie; ce se schimbă pentru restul zilei?" | Lucrări afectate și variantă de plan, fără promisiuni fictive | Stare de teren și recalculare | P2 |
| D15 | "Clientul poate permite accesul doar într-un anumit interval." | Cerere de fereastră compatibilă cu competențe, timp și capacitate | Disponibilitate client și verificare în planificator | P1 |
| D16 | "Punctul pare asociat cu postul greșit." | Cerere de verificare a datelor, fără corecție automată a registrului | Asociere punct-post și dovezi | P1 |
| D17 | "Modelul nu este sigur sau lipsesc date." | Caz în analiza unui om, cu ce lipsește și următorul pas; fără scor inventat | Indicatori de calitate și abstain | P0 |
| D18 | "Aprobă acest grup de lucrări." | Previzualizare a listei exacte; rezultatul fiecărui caz și eventualele conflicte sunt explicite | Aprobare pe obiect și controlul versiunilor | P2 |
| D19 | "Pregătește predarea de tură." | Raport din cazuri deschise, riscuri, aprobări și blocaje | Evenimentele din domeniul autorizat | P1 |
| D20 | "Ce s-a confirmat din ce a estimat modelul?" | Predicții comparate cu constatări disponibile; cazurile fără acces rămân fără verdict tehnic | Predicții și etichete verificate, fără reantrenare instantanee | P1 |
| D21 | "Pregătește informarea clienților afectați." | Mesaj verificat, cu destinatari autorizați și statut de ciornă sau simulare | Plan aprobat și permisiuni de contact; trimiterea externă este P3 | P1 |
| D22 | "Ajută operatorul să răspundă acestui client." | Rezumat destinat clientului și sesizare înregistrată, cu permisiuni restrânse | Proiecția cazului pentru client și drept de relații clienți | P2 |
| D23 | "Constatarea contrazice predicția. Ce facem?" | Caz pentru verificare și posibilă etichetare; datele nu se repară automat | Predicție, constatare și controlul calității etichetelor | P1 |
| D24 | "De unde provin aceste cifre și cât de recente sunt?" | Proveniență, versiune, data predicției și starea serviciului | Metadatele rularii și jurnal | P1 |

## 7. Catalogul clientului

| ID | Cererea sau situația | Rezultatul verificabil | Model sau date necesare | Etapă |
|---|---|---|---|---|
| C01 | "Pentru care dintre locuințele mele discutăm?" | Selecție numai din punctele autorizate; contextul rămâne legat de acel punct | Legătura cont-punct, verificată pe server | P0 |
| C02 | "Invertorul se oprește la prânz." | Sesizare cu simptom, interval și punct de consum; evaluare C dacă există intrările necesare | Date de tensiune/rețea; textul singur nu înlocuiește modelul | P0 |
| C03 | "Ce se întâmplă cu sesizarea mea?" | Starea reală, ultimul eveniment și următorul pas cunoscut | Cazul propriu și varianta destinată clientului | P0 |
| C04 | "Pot permite accesul mâine între aceste ore." | Disponibilitate salvată și cerere către dispecer; confirmarea vizitei apare numai după validare | Fereastră client, caz și planificator | P0 |
| C05 | "Mai am un detaliu despre problemă." | Completarea cazului existent, cu păstrarea istoricului | Caz și întrebări specifice simptomului | P1 |
| C06 | "Contorul pare blocat sau afișează neobișnuit." | Sesizare și verificarea datelor A, dacă există; descrierea nu produce acuzații | A și datele contorului propriu | P1 |
| C07 | "Nu am curent acum." | Sesizare de întrerupere; confirmare de avarie doar dintr-o sursă operațională autorizată | Registru de incidente; B este prognoză, nu dovadă de avarie curentă | P1 |
| C08 | "Există o întrerupere programată la mine?" | Intervalul aprobat și sursa lui, sau lipsa unei informații confirmate | Notificări operaționale și punct autorizat | P1 |
| C09 | "Când ajunge echipa sau revine curentul?" | Fereastră confirmată dacă există; altfel răspuns că ora nu este cunoscută | Programare aprobată ori sursă autorizată de estimare | P1 |
| C10 | "Nu mai pot permite accesul atunci." | Cerere de reprogramare, cu versiunea programării; noua oră nu este promisă înainte de validare | Disponibilitate și plan curent | P1 |
| C11 | "Am trimis deja aceeași problemă." | Găsirea cazului activ și completarea lui, fără a genera a doua intervenție | Deducere de dubluri pe punct, simptom și interval | P1 |
| C12 | "Vreau să retrag sesizarea." | Retragere cerută și explicată; un caz cu semnal de pericol rămâne pentru verificare umană | Stare de caz și regulă de siguranță | P1 |
| C13 | "Prefer să primesc actualizări în aplicație." | Preferință de contact salvată, separată de aprobarea intervenției | Preferințe ale contului; canal extern doar după integrare | P1 |
| C14 | "Ce arată măsurătorile de la mine?" | Rezumat al datelor proprii existente, cu unități și interval | Date autorizate de consum/tensiune | P2 |
| C15 | "Cât de sigură este explicația?" | Formulare fidelă nivelului de încredere și datelor disponibile | Predicție validă și proiecție pentru client | P1 |
| C16 | "Pot ajuta prin mutarea consumului sau folosirea bateriei?" | Opțiune voluntară, justificată de calculele disponibile; acceptarea nu pornește o comandă fizică | C și scenariu valid; integrarea cu echipamente este P3 | P2 |
| C17 | "Nu accept această acțiune voluntară." | Refuz înregistrat fără a închide sau penaliza sesizarea de rețea | Preferință separată de starea sesizării | P2 |
| C18 | "Nu aveți măsurători pentru punctul meu." | Caz în așteptarea datelor sau la om; fără diagnostic sau probabilitate inventată | Calitatea datelor și coada dispecerului | P0 |
| C19 | "Ați ales altă adresă sau alt contor." | Oprirea acțiunii și reverificarea legăturii autorizate, fără mutarea automată pe alt client | Registru cont-punct și confirmare de identitate | P1 |
| C20 | "Problema a dispărut / a reapărut." | Confirmare a simptomului rezolvat ori redeschidere legată de cazul inițial | Istoric de caz; confirmarea clientului nu rescrie constatarea tehnică | P1 |
| C21 | "Dă-mi un rezumat al cazului meu." | Rezumat sau document numai cu informațiile proprii destinate clientului | Proiecția autorizată și export protejat | P2 |
| C22 | "Vreau să vorbesc cu un om." | Cerere pentru operator/dispecer, cu starea ei; nu se pretinde un transfer care nu există | Coada comună; transferul telefonic este P3 | P1 |
| C23 | "Mă puteți suna când se schimbă situația?" | Preferință și permisiune de contact; apel efectuat doar cu integrarea activă și autorizată | Contact verificat și telefonie | P3 |
| C24 | "Am o problemă cu factura, contractul sau plata." | Delimitarea responsabilității și îndrumare către furnizor, fără inventarea datelor comerciale | Contacte oficiale configurate și verificate înainte de utilizare | P1 |

## 8. Situații comune tuturor rolurilor

Aceste 12 comportamente sunt condiții ale primei versiuni, nu funcții opționale care pot lipsi dintr-un cont.

| ID | Situație | Comportament așteptat |
|---|---|---|
| X01 | Microfon refuzat, zgomot, voce indisponibilă sau minute epuizate | Text și butoane pentru aceleași acțiuni; starea cazului se păstrează |
| X02 | Număr de lucrare, adresă, unitate sau dată auzite greșit | Agentul cere clarificare și arată selecția; nu ghicește obiectul unei scrieri |
| X03 | Omul întrerupe agentul sau spune "nu, anulează" | O ciornă neconfirmată se anulează; o acțiune deja salvată cere rectificare explicită |
| X04 | Utilizatorul cere date sau acțiuni din alt rol | Refuz pe server înainte de citire sau scriere, inclusiv la cereri directe către API |
| X05 | Textul cere ignorarea regulilor sau vine dintr-o notă malițioasă | Textul este conținut; nu modifică drepturi, acțiuni permise, roluri sau destinații de rețea |
| X06 | Model lipsă, date vechi, scor mic ori prognoză de altă dată | Stare explicită, sursă și timp; analiza merge la om când datele nu susțin decizia |
| X07 | Răspuns pierdut, retry, refresh sau reconectare | Aceeași comandă nu dublează sesizarea, constatarea, aprobarea sau notificarea |
| X08 | Două persoane modifică simultan același caz sau plan | Una dintre versiuni este refuzată ca depășită; se afișează diferența și se cere reconfirmare |
| X09 | Sesiune expirată sau logout în timpul conversației | Nu se execută alte acțiuni; dialogul se oprește și datele private se golesc din ecran |
| X10 | Limba conversației diferă de limba interfeței | Interfața rămâne în engleză; agentul poate răspunde în română sau engleză, cu aceleași valori verificate |
| X11 | API-ul nu știe dacă o scriere a fost finalizată | Stare în verificare; se caută comanda înainte de retry, fără mesaj fals de succes |
| X12 | Se schimbă contul, punctul de consum sau scenariul | Contextul privat nu se reutilizează în alt cont; scenariul și planul sunt reverificate |

## 9. Modelul local și rolul LLM-ului

### Cine inițiază conversația

În P0, fiecare dintre cele trei roluri pornește conversația din cont. Același circuit poate primi ulterior apeluri și poate iniția apeluri la evenimente, cu regulile de mai jos. Acestea sunt variante de canal pentru cazurile din catalog, nu funcții deja active.

| Direcție | Când are sens | Cazuri din catalog | Activare |
|---|---|---|---|
| Clientul contactează agentul | Sesizare, stare, disponibilitate sau cerere pentru om | C02, C03, C04, C22 | Browser în P0; telefon în P3 |
| Tehnicianul contactează agentul | Briefing, motivul lucrării, constatare și blocaj | T01-T05, T19 | Browser în P0; telefon în P3 |
| Dispecerul contactează agentul | Rezumat, comparație, analiză și aprobare | D01, D02, D04-D06 | Browser în P0; telefon în P3 |
| Agentul contactează dispecerul de serviciu | Risc nou peste un prag justificat, lipsă de capacitate sau semnal de pericol | D08, D09, D13, D17, X06 | Alertă în aplicație în P1/P2; apel în P3 |
| Agentul contactează echipa | O lucrare nouă sau o schimbare aprobată necesită confirmare de primire | T01, T03, T18, D14 | Notificare internă propusă în P1/P2; apel în P3 |
| Agentul contactează clientul | Stabilirea accesului, schimbarea unei programări sau răspuns la o cerere de apel | C04, C10, C23, D21 | Stare în aplicație în P0/P1; contact extern în P3 |

Alerta automată folosește un eveniment verificat, un destinatar autorizat și o regulă explicită, nu doar decizia liberă a LLM-ului. Se evită apelurile repetate pentru același eveniment, se respectă preferințele și ferestrele de contact, iar confirmarea de primire este separată de executarea lucrării.

Pentru P3 se testează și număr greșit, altă persoană la telefon, lipsă de răspuns, mesagerie vocală, conexiune întreruptă, retragerea permisiunii de contact și eșecul transferului către om. Până la verificarea identității nu se divulgă date despre client sau rețea. Retry-urile au limită și condiție de oprire; un apel fără răspuns nu echivalează cu o informare confirmată.

### Ce poate decide fiecare componentă

| Componentă | Responsabilitate |
|---|---|
| LLM | Extrage intenția, cere clarificări, alege o acțiune permisă și formulează răspunsul din rezultatele ei |
| A | Estimează problema de contor pe baza intrărilor și versiunii antrenate |
| B | Estimează riscul de avarie legat de vreme; nu certifică o avarie curentă sau ora revenirii energiei |
| C | Estimează tensiunea și efectele variantelor pentru intrări compatibile cu modelul |
| Bilanț | Estimează pierderea normală și cauza probabilă din datele potrivite |
| Codul de decizie | Verifică date, încredere, costuri, capacitate, competențe, program și condiții de aprobare |
| Omul autorizat | Aprobă intervențiile care cer decizie umană, declară constatări și clarifică situațiile nesigure |

Descrierea clientului nu devine automat un set de intrări ML. Mai întâi se identifică activul și se caută măsurătorile și topologia necesare. Dacă lipsesc, se înregistrează sesizarea și cererea de date. Un scor nu este inventat din text.

O predicție existentă poate fi folosită numai când se potrivește activul, intervalul, scenariul, versiunea datelor și limita de vechime definită pentru model. Se spune când a fost calculată. Recalcularea este o acțiune locală explicită, cu stare de progres, nu o rulare a tuturor modelelor la fiecare replică.

Acțiunile fără predicție, cum ar fi autentificarea, o sesizare nouă sau un semnal uman de pericol, nu primesc un identificator ML fictiv. Legătura cu predicția apare când există o evaluare validă. Predicțiile contradictorii sau cu încredere mică trimit cazul la analiză.

Constatările se păstrează pentru controlul calității și reantrenare ulterioară. no_access nu este o etichetă negativă despre existența defectului. other_problem nu confirmă clasa prezisă. Etichetele necesită reguli specifice fiecărui model și verificare înainte de antrenare.

## 10. Arhitectura propusă

### Demo local cu voce în browser

1. Utilizatorul se autentifică în aplicația web.
2. Serverul citește rolul și domeniul autorizat. Returnează numai configurația conversațională a acelui rol și acreditarea temporară pentru sesiunea vocală.
3. Browserul discută cu ElevenLabs pentru audio și conversație. Funcțiile înregistrate în browser cer acțiuni de la serverul Daybreak prin sesiunea aplicației.
4. Serverul Daybreak verifică din nou drepturile și proprietatea obiectului, validează parametrii și construiește cererea internă către serviciul Python local.
5. Serviciul Python citește sau execută acțiunea autorizată, folosește modelele locale când este necesar și returnează un rezultat structurat.
6. Browserul actualizează ecranul și întoarce agentului rezultatul minim necesar. Agentul anunță succesul numai după confirmarea salvării.

Această variantă folosește mecanismul [client tools și întoarcerea rezultatului în conversație](https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools). Configurația trebuie să aștepte rezultatul acțiunii. Codul care cere API-ul aplicației urmează modelul prezentat în [React SDK](https://elevenlabs.io/docs/eleven-agents/libraries/react). Se validează exact comportamentul versiunii SDK instalate înainte de implementare.

Pentru demo, Python rămâne legat la interfața locală. În acest circuit nu este necesar să publicăm un URL către model pentru ElevenLabs. Serviciul de voce este în cloud; modelul ML și deciziile de energie rulează local. Aceasta nu este o soluție care funcționează integral fără internet.

Sesiunile vocale se creează pe server, fără cheia ElevenLabs în browser, prin [acreditări temporare](https://elevenlabs.io/docs/eleven-agents/customization/authentication). Pentru WebRTC se verifică și se folosește [tokenul de conversație](https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-webrtc-token); URL-ul semnat pentru WebSocket nu se confundă cu acest token. Un agent public identificat doar prin ID nu este suficient pentru date private.

### Securitatea acțiunilor

- Rolul, identitatea, organizația, echipa și punctele autorizate vin din sesiunea verificată. Câmpurile reviewer și approver ale API-ului existent se completează din această identitate, nu din textul LLM-ului.
- Rolul selectat în interfață, un parametru în URL, un obiect modificat în browser sau o instrucțiune vocală nu acordă permisiuni.
- Fiecare acțiune verifică și rolul, și obiectul concret. Lista de funcții disponibilă LLM-ului este un ajutor pentru conversație, nu protecția datelor.
- Butoanele și acțiunile web vechi trec prin același control. O protecție doar a noului chat ar lăsa căi de ocolire.
- API-ul Python nu se expune în rețea cu actualele drepturi implicite. Pentru orice acces din afara calculatorului sunt necesare autentificarea serviciului și transmiterea verificată a identității și domeniului.
- Exporturile, PDF-urile, seriile, harta și jurnalul folosesc aceeași filtrare. Un client nu primește planul global pentru a fi filtrat ulterior în browser.
- Sesiunile și acțiunile private nu folosesc cache comun între conturi. Se verifică protecția cererilor care modifică date, inclusiv originea lor.
- Oprirea conversației nu revocă o comandă deja confirmată. Logout-ul revocă dreptul la următoarea acțiune.

### După demo

Pentru acces din site-ul public, serverul web public trebuie legat de un serviciu Python accesibil și protejat. localhost de pe Cloudflare nu înseamnă calculatorul lui Teo. Abia după alegerea și verificarea acelei infrastructuri se poate pretinde că cele trei conturi execută acțiuni pe site-ul public.

Apelurile reale fără browser vor folosi un adaptor de telefonie și [webhook tools](https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools), cu identitatea apelantului verificată, drepturi legate de conversație și protecție împotriva repetării cererilor. Numărul de telefon declarat sau identificarea apelantului nu înlocuiesc autentificarea. Transferul către un om, numerele și apelurile proactive se verifică în integrarea concretă înainte de activare.

## 11. Datele și sursa comună de adevăr

Planul și predicțiile existente rămân sursa tehnică pentru priorități și trasee. Se adaugă un registru operațional comun pentru sesizări, legături între conturi și active, evenimente, confirmări și rezultatele comenzilor.

Pentru rularea locală propunem SQLite, deținut de serviciul Python, cu tranzacții pentru registrul nou. Conturile pot folosi în continuare adaptorul existent, cu rolurile și apartenențele verificate pe server. Nu introducem în această etapă o migrare a conturilor live sau o nouă bază Cloudflare. Stocarea locală nu se prezintă ca infrastructură gata de producție.

| Obiect nou | Date esențiale și regulă |
|---|---|
| Identitate operațională | Utilizator, organizație, rol și permisiuni; modificabilă doar prin administrare |
| Apartenență la echipă | Tehnician, echipă, interval de valabilitate și domeniu |
| Punct de consum autorizat | Legătura cont-punct-contor-post, cu proveniență și stare de verificare |
| Caz | ID, solicitant, punct, tip, simptom, interval, stare, versiune și marcaj sintetic |
| Evaluare | Legătura cu predicția, versiunea modelului, activ, interval, sursă, vechime și limitări |
| Legătură caz-lucrare | Poate exista mai mult de un caz pe aceeași lucrare sau un caz cu mai multe lucrări; fără identitate artificială unu-la-unu |
| Disponibilitate client | Ferestre cerute, stare de cerere și eventual programarea confirmată |
| Propunere de acțiune | Obiecte și versiuni exacte, rezumat, expirare și confirmare legată de utilizator |
| Comandă | ID unic, cheie de evitare a dublurilor, emitent, parametri validați, stare și rezultat |
| Eveniment de caz | Cine, când, ce a schimbat, predicție și aprobare dacă există, vizibilitate pe rol |
| Constatare | Lucrare, tehnician autorizat, rezultat, observații, versiune și eventual rectificare |

Schimbarea cazului și evenimentul său se salvează în aceeași tranzacție. Efectele în planificator și jurnalul existent folosesc identificatorul comenzii și o evidență a pașilor de executat, pentru reconciliere după o întrerupere. Nu pretindem o tranzacție unică între SQLite, fișierele planului și un serviciu extern. Până când efectul este verificat, rezultatul rămâne în așteptare sau în verificare.

Alegerile personale din KV și aprobările păstrate doar într-un cookie nu devin aprobări operaționale. Nu se copiază automat în planificator. Interfața le delimitează până la înlocuirea traseului vechi cu serviciul comun.

## 12. Stările cazului și ale intervenției

### Cazul clientului

Deschis, în evaluare, așteaptă date, așteaptă o decizie, intervenție aprobată, vizită programată, în verificare după vizită, rezolvat sau închis cu explicație. Redeschiderea creează un eveniment și păstrează legătura cu istoricul.

### Vizita tehnicianului

Atribuită, începută, blocată, finalizată. Separat se salvează constatarea tehnică: confirmată, neidentificată la verificare, altă problemă sau fără acces.

### Reguli care previn concluzii greșite

- Înregistrarea unei sesizări nu aprobă automat deplasarea.
- Disponibilitatea declarată de client nu rezervă automat un interval.
- Predicția unei furtuni nu confirmă o avarie.
- Aprobarea unui plan nu dovedește că echipa a primit sau executat lucrarea.
- Constatarea confirmed confirmă problema estimată, nu reparația. Rezolvarea cere o constatare distinctă de remediere sau verificare și, când se aplică, verificarea ulterioară a simptomului.
- no_access păstrează cazul deschis și solicită următorul pas.
- Un alt defect observat nu modifică automat baza de active și nu declanșează o manevră.
- O constatare falsă sau rectificată nu trebuie să devină o etichetă de antrenare fără verificare.

În P0, un caz poate rămâne corect în starea în verificare după vizită. Nu forțăm închiderea lui pentru a face demonstrația să pară complet rezolvată.

## 13. Contractele acțiunilor conversaționale

Un singur serviciu de acțiuni deservește vocea, textul și interfața. Nu se oferă LLM-ului shell, SQL, scriere liberă de fișiere, URL-uri arbitrare sau un instrument generic care poate apela orice API.

| Acțiune conceptuală | Rol | Comportament |
|---|---|---|
| Citește contextul propriu | Toate | Returnează domeniul permis, selecția activă, data și sursa datelor |
| Citește cazurile proprii | Toate | Filtrare pe proprietar, atribuire sau domeniu |
| Citește lucrarea și explicația | Tehnician, dispecer | Predicție, motive și plan, numai pentru obiecte autorizate |
| Citește următoarea oprire | Tehnician | Traseul aprobat al echipei proprii |
| Pregătește sesizarea | Client, dispecer cu permisiune | Validează punctul și caută dubluri; întoarce o ciornă |
| Citește evaluarea tehnică | Dispecer; rezumat limitat pentru celelalte roluri | Refolosește o evaluare compatibilă sau cere date/rulare locală |
| Pregătește constatarea | Tehnician | Leagă rezultatul de lucrarea atribuită și de versiunea văzută |
| Pregătește revizuirea | Dispecer autorizat | Previzualizează aprobarea, respingerea sau amânarea |
| Pregătește aprobarea planului/listei | Dispecer autorizat | Leagă propunerea de versiunea exactă și de consecințele cunoscute |
| Pregătește disponibilitatea de acces | Client | Salvează o cerere; nu promite programarea |
| Cere analiza unui om | Toate | Creează cererea în coada potrivită și întoarce starea reală |
| Confirmă și execută propunerea | Toate, în limitele rolului | Verifică identitatea, confirmarea, expirarea și versiunile, apoi execută o singură dată |
| Citește rezultatul comenzii | Emitent sau dispecer autorizat | Permite reconcilierea după timeout sau reconectare |

Pentru citiri, rezultatul include data, sursa, domeniul și datele strict necesare. Pentru evaluări include identificatorul predicției și versiunea modelului. Pentru scrieri include identificatorul comenzii, starea, ID-ul evenimentului și noua versiune a cazului sau planului.

Erorile disting lipsa autentificării, lipsa dreptului, obiectul inexistent în domeniul permis, versiunea schimbată, datele insuficiente, serviciul indisponibil și rezultatul încă necunoscut. Un răspuns gol sau un cod de transport reușit nu este automat succes operațional.

### Confirmarea omului

1. Agentul pregătește o propunere. Serverul întoarce un identificator, obiectul exact, rezumatul și versiunile.
2. Interfața arată ce se schimbă și oferă Confirm, Edit și Cancel. Agentul citește același rezumat.
3. În P0, scrierile se confirmă prin buton. Aceasta face acceptarea verificabilă și evită confundarea unui "da" din alt context cu aprobarea unei operații.
4. Confirmarea doar prin voce intră în P1, cu testarea legăturii dintre replica utilizatorului și propunerea activă, fără a accepta simpla afirmație a LLM-ului că omul ar fi aprobat.
5. Serverul execută numai dacă propunerea este încă valabilă și permisiunile sunt neschimbate. Orice schimbare materială cere o propunere și o confirmare noi.

Acțiunile de citire și explicație nu cer confirmare. O sesizare declarată periculoasă intră imediat în coada unui om, fără a aștepta calculul ML; agentul nu conduce o intervenție electrică.

## 14. Experiența de conversație

Fiecare ecran are un singur punct de intrare conversațional, cu Talk to Daybreak și Type instead. Arată când ascultă, când așteaptă rezultatul și când răspunde. Butonul End oprește captura și conversația.

Agentul pune câte o întrebare, confirmă identificatorii ambigui și răspunde scurt. Explicația completă și proveniența se pot deschide în ecran. În text sunt disponibile aceleași acțiuni și aceleași confirmări.

După o scriere, apare un rezultat cu obiectul modificat, momentul și starea lui. Conversația nu spune "am trimis echipa", "am sunat" sau "am rezolvat" când există doar o ciornă, o aprobare sau un mesaj simulat.

Progresul lung folosește o stare vizibilă. După salvare, celelalte conturi recitesc cazul sau primesc evenimentul; propunerea inițială este actualizare prin recitire periodică la două secunde pe ecranele active. O conexiune permanentă pentru actualizări se adaugă doar dacă există un motiv măsurat.

Înainte de prima conversație se explică faptul că vocea și textul conversației sunt procesate de serviciul de voce. În demo se folosesc identități și puncte sintetice. Se reduc datele trimise către LLM: nu întregul jurnal, datele altor clienți sau toate seriile brute. Retenția conversațiilor și posibilitatea de a dezactiva stocarea se verifică în contul și planul concret înaintea datelor reale.

## 15. Date pentru testarea celor trei conturi

### Conturi și domenii propuse

| Cont sintetic | Rol | Asociere verificată | Ce trebuie să poată demonstra |
|---|---|---|---|
| DEMO-DSP-01 | Dispecer | Organizația și zona demo | Vede sesizarea, evaluarea, planul și constatarea; aprobă o intervenție |
| DEMO-TECH-01 | Tehnician | O echipă existentă în planul ales | Vede lucrarea atribuită, motivul și traseul; salvează constatarea |
| DEMO-CUST-01 | Client | Un punct de consum sintetic, cu legătură verificată la un post din scenariu | Creează sesizarea, declară disponibilitatea și urmărește rezultatul |

Acestea sunt identificatoare propuse, nu conturi create. Parolele și cheile nu intră în document, repo, capturi sau mesaje de jurnal. Adresa și credențialele de test se stabilesc privat la implementare.

Se adaugă obiecte sintetice care nu aparțin celor trei identități, pentru testele de acces interzis: alt punct, alt caz, altă echipă și altă organizație. Nu este obligatoriu să existe un al patrulea cont conectat ca să verificăm aceste refuzuri.

### Datele de pornire

- La implementare se ia o copie proaspătă, numai în citire, a datelor folosite de aplicația relevantă, fără secrete sau setări de publicare. Dacă datele live nu pot fi obținute, limita se raportează înaintea verificării.
- Datele tehnice sunt seturile publice/sintetice complete ale scenariului ales. Obiectele noi pentru cele trei conturi sunt etichetate clar ca sintetice, cu generator reproductibil.
- Nu se copiază utilizatori reali, hash-uri de parole sau sesiuni din KV-ul public pentru a construi demo-ul. Se folosesc identități de test generate separat.
- Scenariul istoric demo-vara are data de 8 iulie 2025. Dacă îl folosim, toate conturile arată explicit acea dată de simulare. Nu prezentăm acele valori ca măsurători de azi.
- Pentru scenariul maine se folosesc predicțiile și vremea potrivite datei respective, cu apartenențe și clienți sintetici. Nu amestecăm prognoza de mâine cu tensiunile unui scenariu istoric.
- Scrierile se fac într-o stare de test izolată, copiată din datele de pornire. Resetarea are domeniu limitat la această stare; nu șterge conturi, planuri sau istoric existente.
- Adaptarea datelor pentru demo nu schimbă datele de test ale modelelor, pragurile sau rapoartele de performanță.

### Sesiunile de browser

Trei file obișnuite în același profil împart cookie-ul de autentificare și nu demonstrează trei conturi simultane. Testul automat local folosește trei contexte de browser cu sesiuni independente. Testarea manuală poate folosi autentificări succesive cu logout, dacă nu este necesară observarea simultană.

Nu se deschide un al doilea profil Helium gol pentru a ocoli limitele mediului. Pentru verificarea locală se folosește mecanismul de QA local permis de proiect. Pentru site-ul public se urmează fluxul existent cu Helium și autentificarea reală, după o publicare autorizată.

## 16. Scenarii demonstrabile cap-coadă

### Scenariul principal cu toate cele trei conturi

1. Clientul sintetic selectează punctul propriu și spune în română sau engleză că invertorul se oprește la prânz.
2. Agentul cere intervalul lipsă, pregătește sesizarea și clientul o confirmă. Apare numărul cazului.
3. Dispecerul vede același caz, cu același identificator, și solicită explicația. Sistemul arată evaluarea C compatibilă sau execută evaluarea locală dacă adaptorul și intrările o permit. Se văd modelul, data și caracterul sintetic al activului.
4. Dispecerul verifică propunerea de intervenție, fereastra și competențele, apoi confirmă aprobarea. Clientul vede noua stare, fără acces la planul global.
5. Tehnicianul vede lucrarea atribuită, întreabă de ce a fost aleasă și raportează că problema estimată s-a confirmat. Confirmă constatarea din ecran.
6. Dispecerul vede constatarea legată de predicție. Clientul vede că vizita a confirmat problema și care este următorul pas. Nu declarăm remedierea dacă ea nu a fost înregistrată.
7. Dacă remedierea și verificarea sunt implementate în P1, se poate demonstra și închiderea justificată. Altfel se încheie explicit în starea în verificare după vizită.

Lucrarea este selectată din datele complete ale scenariului, pentru un post și o echipă compatibile. Dacă planificatorul nu poate include cazul în capacitatea curentă, rezultatul corect este o cerere de analiză sau programare. Nu forțăm o atribuire doar pentru povestea demo-ului.

### Scenariul de contor

Modelul A și bilanțul susțin o verificare. Tehnicianul explică ce a găsit, iar dispecerul vede dacă predicția s-a confirmat. O a doua rulare folosește no_access și demonstrează că problema nu se transformă într-un exemplu negativ de antrenare sau într-un caz rezolvat.

### Scenariul de furtună

Dispecerul cere zonele prioritare și motivul poziționării echipelor. Sistemul folosește B, vremea și constrângerile planului. Alerta se arată în aplicație. Un apel telefonic proactiv nu este mimat drept apel real.

### Scenariul de robustețe

Clientul cere date despre alt punct și primește refuz. Apoi un caz fără măsurători merge la om. La o constatare repetată sau la pierderea răspunsului, apare un singur eveniment. Dacă planul se schimbă înainte de confirmare, vechea propunere este refuzată și explicată.

## 17. Plan de implementare

Estimările sunt propuneri de efort, nu timpi măsurați sau o promisiune de livrare. Se reestimează după prima integrare verticală. Cu termenul PPC din 8 noiembrie la 12:00, se păstrează minimum două ore pentru validare și pregătirea prezentării. Nicio extensie P1/P2 nu consumă această rezervă.

| Ordine | Livrabil | Dependențe | Buget orientativ | Condiție de trecere |
|---|---|---|---|---|
| 0 | Preflight de acces, date, versiuni SDK și capacitate ElevenLabs | Contul și mediul local | 20-30 min | Un dialog de test, costul/minutele disponibile cunoscute, fără modificare de plan plătit |
| 1 | Identități, roluri, apartenențe și protecția tuturor acțiunilor existente | Decizia de acces și date sintetice | 60-90 min | Clientul și tehnicianul nu pot folosi acțiunile dispecerului nici direct prin API |
| 2 | Registrul comun, versiuni, propuneri și comenzi fără dubluri | Pasul 1 | 60-90 min | O sesizare și o constatare sunt vizibile celor autorizați și rezistă unui retry |
| 3 | Adaptoare pentru modele, plan, aprobări și constatări | Pasul 2 și API-urile existente | 45-75 min | Din text se execută o acțiune reală legată de o predicție locală, cu rezultat verificabil |
| 4 | Cele trei ecrane și conversația text | Pașii 1-3 | 45-75 min | Toate cele trei conturi parcurg scenariul principal prin text |
| 5 | Sesiuni private de voce și acțiuni în browser | Pasul 4 și preflight ElevenLabs | 45-75 min | Vocea folosește exact același circuit de autorizare, confirmare și rezultat |
| 6 | Teste automate și verificarea conversației reale | Pașii 1-5 | 90-120 min | Scenariul comun, accesul, datele lipsă, retry și expirarea sesiunii trec |
| 7 | Demo cronometrat, ghid de pornire și variantă de rezervă | Pasul 6 | 30-45 min | Echipa îl reproduce și poate explica predicția, decizia și rezultatul |

Bugetul însumat este aproximativ 6 h 35 min până la 10 h, fără întârzieri de acces sau infrastructură. Prima verificare de integrare stabilește dacă acest buget este realist. Dacă nu încape, se păstrează toate cele trei roluri și circuitul comun, se reduce personalizarea vizuală și se taie mai întâi P1/P2. Vocea rămâne un criteriu de livrare; dacă accesul la ElevenLabs o blochează, se raportează explicit această limită, iar textul permite continuarea testelor funcționale.

Ordinea nu autorizează acum publicarea, crearea unor resurse plătite, schimbarea secretelor, modificarea conturilor reale sau apelarea unor persoane. Acest document planifică munca; implementarea și activarea serviciilor sunt pași ulteriori.

### Împărțirea muncii dacă implementarea va fi delegată

| Domeniu | Responsabilitate | Predare necesară |
|---|---|---|
| Identitate și acces | Roluri, apartenențe și protecția citirilor/scrierilor | Politica de acces și teste de refuz |
| Cazuri și acțiuni | Registru, comenzi, adaptoare la modele și planificator | Schemele validate și răspunsurile operațiilor |
| Interfață și voce | Cele trei ecrane, sesiuni vocale, text și confirmare | Scenariul comun folosind acțiunile reale |
| Integrare și QA | Date complete, sesiuni independente și demonstrația | Dovezi pentru toate cele trei roluri și limitele rămase |

Aceasta este o împărțire propusă, nu lansarea unor agenți sau fire. La implementare se ține cont de proprietarii actuali ai modulelor și de modificările necomise. Se fixează întâi contractele, apoi se dau domenii fără suprapunere. Modelele și interfața deja în lucru nu se rescriu în paralel de un nou fir.

## 18. Matricea de testare

Testele verifică comportamentul prin serviciul de acțiuni și API-ul aplicației, apoi câteva trasee reale de browser. Nu verifică fraza exactă aleasă de LLM sau organizarea internă a funcțiilor. Testele funcționale pot folosi un adaptor vocal determinist, marcat ca atare; acesta nu dovedește că ElevenLabs sau microfonul funcționează.

Există deja teste pentru rularea agentului, revizuire și date invalide în [testele planificatorului](../tests/planner/test_agent.py) și pentru stratul de date în [testele web](../web/lib/data/data.test.ts). Se reutilizează aceste puncte de verificare; se adaugă contractul comun de acțiuni și traseul cu trei sesiuni. Nu se creează câte o logică separată de test pentru fiecare canal.

| ID | Probă | Rezultat cerut |
|---|---|---|
| QA01 | Autentificare pe fiecare rol | Ecranul și acțiunile permise corespund rolului stabilit de server |
| QA02 | Înregistrare și editare profil | Utilizatorul nu se poate promova singur la tehnician/dispecer și nu poate atribui echipe |
| QA03 | Client cere alt punct/caz | Nicio dată privată returnată, nici prin ID ghicit sau export |
| QA04 | Client aprobă planul prin cerere directă | Refuz și niciun efect în plan, KV operațional sau jurnalul deciziilor |
| QA05 | Tehnician cere altă echipă sau altă lucrare | Refuz și niciun efect |
| QA06 | Dispecer cere altă organizație sau zonă | Refuz înainte de citire/scriere |
| QA07 | Apel direct la butoanele/acțiunile web vechi | Aceleași restricții ca în conversație |
| QA08 | API Python accesat fără identitatea de serviciu cerută | Refuz; niciun traseu nou nu publică implicit API-ul actual |
| QA09 | Caz creat de client | Același ID și eveniment apar la dispecer; alt client nu le vede |
| QA10 | Sesizare fără punct autorizat | Nu se atașează arbitrar la o adresă sau alt cont |
| QA11 | Dublură de sesizare/retry | Un singur caz sau completare explicită a celui existent |
| QA12 | Sesizare cu intrări suficiente pentru C | Predicție reală compatibilă, ID, versiune și explicație verificată |
| QA13 | Date insuficiente, model lipsă sau abstain | Nicio probabilitate inventată; caz la om sau în așteptarea datelor |
| QA14 | Predicție veche, activ sau scenariu diferit | Nu este folosită ca evaluare curentă validă |
| QA15 | Comparație de priorități | Cifrele și motivele corespund modelului și codului de decizie |
| QA16 | Ciornă neconfirmată | Nicio scriere operațională |
| QA17 | Confirmare după schimbarea planului/cazului | Conflict de versiune și propunere nouă, fără aprobare pe date vechi |
| QA18 | Confirmare pentru alt utilizator sau după expirare | Refuz și niciun efect |
| QA19 | Aprobare în planificator | Vizibilă în starea comună; alegerea doar personală sau în cookie nu este suficientă |
| QA20 | Disponibilitate cerută de client | Cerere salvată; programarea nu devine confirmată fără capacitate și aprobare |
| QA21 | Constatare confirmed | Un eveniment legat de lucrare și predicție; fără închidere automată ca reparat |
| QA22 | Constatare no_access | Caz deschis, următor pas către dispecer, fără etichetă negativă de defect |
| QA23 | Constatare other_problem sau rectificată | Clasa prezisă nu este confirmată arbitrar; istoricul rămâne |
| QA24 | Două constatări/aprobări concurente | Fără suprascriere tăcută, dublare sau atribuire imposibilă |
| QA25 | Timeout după scriere | Rezultatul se recuperează după ID-ul comenzii înainte de repetare |
| QA26 | Cădere între registru și efectul în planificator | Stare în verificare și reconciliere, fără succes fals |
| QA27 | Cerere de ignorare a regulilor, inclusiv într-o notă | Nu schimbă permisiunile și nu execută acțiuni arbitrare |
| QA28 | Logout sau expirare în conversație | Următoarea acțiune este refuzată și contextul privat este golit |
| QA29 | Microfon refuzat sau serviciu vocal indisponibil | Textul și butoanele permit aceleași operații |
| QA30 | Conversație reală română și engleză | Identificatorii, datele și unitățile sunt păstrate; rezultatul corespunde acțiunii |
| QA31 | Întrerupere și anulare | Nicio scriere dintr-o propunere neconfirmată; scrierea deja salvată nu dispare |
| QA32 | Trei sesiuni independente pe același scenariu | Modificările autorizate se văd în celelalte conturi, fără schimbarea identității lor |
| QA33 | Schimbare de cont, punct sau scenariu | Fără date din vechiul context și fără aprobări reutilizate |
| QA34 | Plan salvat / demo / API indisponibil | Sursa este afișată; nu se pretinde executarea unei acțiuni reale pe un instantaneu |
| QA35 | Furtună estimată și întrebare despre avarie curentă | Agentul distinge prognoza de incidentul confirmat și nu inventează ora revenirii |
| QA36 | Semnal uman de pericol | Ajunge la om fără a aștepta modelul; fără instrucțiuni electrice improvizate |
| QA37 | Mesaj sau apel extern în modul demo | Niciun mesaj/apel real; starea este explicit simulată sau ciornă |
| QA38 | Jurnal, capturi și răspunsuri către client | Fără chei, tokenuri, hash-uri, date despre vecini sau suspiciuni interne |
| QA39 | Reproducere din stare de test curată | Aceleași conturi sintetice, date de scenariu și rezultate funcționale |
| QA40 | Telefon și desktop | Ecranele, confirmările, erorile și oprirea microfonului sunt lizibile și utilizabile |

Se rulează verificările Python și web relevante pentru modulele schimbate, verificarea tipurilor, lint și build. După trecerea lor se face testul real al vocii și al scenariului în trei sesiuni. Rezultatul local nu dovedește funcționarea pe site-ul public.

## 19. Măsurători și condiții de acceptare

### Condiții obligatorii

- Toate cele 16 cazuri P0 pot fi parcurse prin cele trei roluri, cu dovezi ale rezultatului în aplicație.
- Testele de acces nu permit nicio citire sau scriere în afara domeniului autorizat.
- Fiecare recomandare tehnică folosită la o decizie are predicție validă și explicație; cazurile fără suport sunt tratate explicit ca atare.
- Fiecare scriere are utilizator verificat, confirmare, comandă și rezultat recuperabil. Retrimiterea aceleiași comenzi nu dublează efectul.
- Confirmarea defectului, repararea și închiderea cazului nu sunt confundate.
- Cele trei conturi văd starea comună potrivită drepturilor lor. Nu există trei istorice personale care par sincronizate doar în conversație.
- Vocea este verificată cu serviciul real, microfon și difuzor, iar textul rămâne disponibil. Un test simulat al LLM-ului nu satisface această condiție.
- Nu există publicare sau contact extern accidental în test.

### Ținte de performanță propuse

| Măsură | Țintă inițială | Cum se măsoară |
|---|---|---|
| Citire simplă din serviciul local | p95 sub 1 secundă, fără inferență lungă | Cel puțin 30 de cereri, cu număr de probe și mediu raportate |
| Sfârșitul replicii până la începutul răspunsului vocal, fără acțiune lungă | p95 sub 3 secunde | Minimum 10 replici reale; se raportează și latența de rețea observată |
| Salvarea unei acțiuni până la afișarea în alt cont | p95 sub 3 secunde pe ecranele active | Timestamp de eveniment și momentul afișării, în trei sesiuni |
| Înregistrarea constatării | Mai rapidă decât formularul folosit ca referință | Aceleași cinci situații, voce și formular, cu erori și corectări numărate |
| Fluxul principal | Trei rulări consecutive fără corectarea manuală a datelor | Una în engleză, una în română și una cu o situație dificilă |

Acestea sunt ținte de produs, nu rezultate deja obținute. Pentru evaluarea reală se păstrează toate probele, erorile și numărul mic de măsurători. Nu se extrapolează economii lunare sau un ROI PPC dintr-un demo sintetic.

## 20. Costuri, acces și limite de activare

Înainte de implementarea vocii se verifică accesul la ElevenLabs, posibilitatea de a crea trei configurații private, creditele/minutele și modelul conversațional care poate apela acțiuni. Disponibilitatea lor nu a fost verificată în cont în această etapă de planificare.

Bugetul se stabilește din consumul pe o conversație de test și tariful contului la acel moment. Se aplică limită de durată pe sesiune, număr de sesiuni simultane și consum total pentru test. Nu estimăm costul doar dintr-un preț public care poate exclude modelul sau telefonia. Nu se schimbă planul plătit fără autorizare.

P0 folosește calculatorul existent pentru modele și vocea prin internet. Numerele telefonice, SMS, emailurile, apelurile reale, controlul invertoarelor, integrarea cu registrul clienților și infrastructura de găzduire sunt P3. Fiecare are propriile dependențe și verificări. O funcție neconectată apare ca indisponibilă sau simulată, nu ca efect executat.

## 21. Prezentarea de cinci minute

| Interval propus | Ce vede juriul |
|---|---|
| 0:00-0:30 | Problema de energie și cele trei roluri care lucrează astăzi separat |
| 0:30-1:15 | Clientul raportează simptomul și apare cazul comun |
| 1:15-2:30 | Dispecerul consultă modelul local, explică decizia și aprobă propunerea |
| 2:30-3:20 | Tehnicianul primește lucrarea și raportează verbal constatarea |
| 3:20-4:00 | Cazul se actualizează pentru client și dispecer; vedem legătura cu predicția |
| 4:00-4:30 | Un refuz de acces sau un caz fără date arată comportamentul robust |
| 4:30-5:00 | Metricile reale ale modelelor, rezultatul măsurat al agentului și limitele demo-ului |

Se aleg un scenariu principal și o singură situație dificilă. Catalogul complet rămâne pentru întrebări și dezvoltare. Cazurile de contor și furtună se arată separat dacă timpul permite, fără a ascunde modelul local în spatele conversației.

Rezerva este același circuit prin text și o înregistrare a unei rulări reale, dacă realizarea ei este aprobată ulterior. Înregistrarea se prezintă ca înregistrare. Nu înlocuiește dovada funcționării live când se afirmă acest lucru.

## 22. Definiția livrării

Livrarea înseamnă trei roluri funcționale, circuitul P0 complet, teste și ghid reproductibil, cu sursele datelor și limitele păstrate vizibile. Pentru fiecare etapă se raportează separat dovada locală, vocea reală și funcționarea pe site-ul public, dacă acesta a fost publicat și verificat.

La începerea implementării se revalidează contextul din repo, datele, proprietarii activi ai modulelor și accesul la servicii. Acest plan nu mută firele existente și nu acordă acces suplimentar unor agenți sau utilizatori.
