# Plan pentru agentul Daybreak care decide și execută

Data: 8 noiembrie 2026. Stare: propunere de produs și implementare. Teo a cerut acest plan după o discuție cu un mentor de business, care a considerat utilă ideea unui agent care ia decizii pentru utilizator. Părerea mentorului privește produsul; nu reprezintă o confirmare a interpretării regulamentului PPC.

Daybreak primește o sarcină, caută datele necesare, folosește modelele noastre pentru evaluare, alege pașii permiși și verifică rezultatul. Omul poate vorbi cu el din aplicație, printr-un apel WhatsApp sau prin mesaje. Agentul pregătește singur analiza și documentele. Pentru schimbări care afectează intervenții, trasee sau constatări, prezintă efectul și cere confirmarea persoanei autorizate.

Beneficiul urmărit este ca dispecerul să revizuiască o propunere pentru întreaga coadă, iar tehnicianul să obțină traseul și să raporteze din teren fără să caute prin ecrane. Timpul economisit trebuie măsurat; nu avem încă un rezultat comparativ.

Acest plan completează [catalogul celor trei conturi](PLAN-AGENT-CONVERSATIONAL.md). Pentru noul comportament, ordinea livrării și canalele externe, propunerea de față înlocuiește etapele vechi care nu mai corespund implementării. Interfața rămâne în engleză, iar conversația răspunde în limba utilizatorului. Documentația rămâne în română.

## 1. Ce există și ce condiționează livrarea

Codul actual are trei roluri, drepturi verificate pe server, modele locale, planificator, propuneri cu confirmare și un istoric al operațiilor. Există fotografii private la constatări și corecții umane care păstrează predicția originală. Aceste componente se reutilizează.

Conversația actuală produce un răspuns sau pregătește o singură operație. Primește implicit detalii despre șase lucrări și acceptă cel mult opt lucrări într-o comparație detaliată. Această selecție nu ajunge pentru analiza individuală a celor 25 de cazuri din exemplul lui Teo. Este necesară o funcție care parcurge întreaga coadă autorizată și păstrează dovada acoperirii.

Mesageria WhatsApp existentă trimite text și, în fluxul vocal, audio. Trimiterea imaginilor de raport este de construit. Apelurile WhatsApp sunt conectate la ElevenLabs, cu acces la serviciul Daybreak prin SIP, adică legătura care transportă apelul către agent. Integrarea rămâne direct Meta pentru mesaje și ElevenLabs pentru voce.

Limitele care contează înaintea implementării:

- Numărul WhatsApp verificat este asociat tehnicianului demonstrativ. Pentru dispecer și client pe telefon trebuie asociate alte numere verificate sau construită o legare sigură din contul autentificat. Un mesaj de tipul „acum sunt dispecer” nu schimbă identitatea. Același număr demonstrativ nu dovedește trei identități independente.
- Memoria proiectului consemnează un apel real care a verificat legătura audio și probe API care au obținut răspunsuri operaționale. Răspunsul complet pe date, prin apelul fizic, și zgomotul sălii trebuie verificate împreună înainte să prezentăm întregul flux drept testat pe telefon.
- Datele operaționale din demo sunt istorice, pentru 8 iulie 2025. Conturile, asocierile și sesizările demonstrative sunt sintetice. Fiecare raport păstrează aceste etichete, separat de momentul generării.
- Serviciile operaționale și tunelurile depind de calculatorul local. O aplicație publică autentificată nu dovedește că operațiunile locale sunt accesibile de pe telefon. Legătura de confirmare trebuie verificată cap-coadă.
- Există abonamentul conversațional și integrarea vocală. Creditele disponibile, limitele contului și tarifele aplicabile se verifică înaintea probelor consumatoare. Planul nu presupune cumpărarea unui număr, schimbarea abonamentului sau activarea unei plăți.

Situația de mai sus rezultă din codul și documentația locală citite pentru plan. Nu este o nouă verificare a serviciilor live.

## 2. Ce face agentul pentru fiecare cont

### Dispecerul deleagă analiza și pregătirea deciziilor

Cerere principală: „Analizează toate cazurile care așteaptă revizuire. Recomandă ce facem cu fiecare și explică de ce.”

Agentul citește coada completă, verifică disponibilitatea predicțiilor și separă riscul tehnic de incertitudinea cauzei. Folosește regulile planificatorului pentru priorități și fezabilitate. Pentru fiecare caz produce recomandarea, motivele, ce informație lipsește și ce ar schimba aplicarea recomandării. Le arată separat pe cele care cer judecata unui om.

Rezultatul este o listă de lucru persistentă, legată de versiunea datelor, cu acoperire explicită. La exemplul cu 25 de cazuri, trebuie să existe 25 de rezultate, inclusiv cazurile pentru care răspunsul este „nu pot recomanda încă”. Agentul rostește un rezumat scurt și oferă raportul complet în aplicație sau, la cerere, pe WhatsApp.

Dispecerul poate întreba „De ce acesta înaintea celuilalt?”, poate modifica selecția și poate cere pregătirea revizuirii unui caz. După confirmare, serviciul aplică decizia prin planificator, recalculează și recitește rezultatul. Aprobarea unei intervenții și aprobarea planului rezultat rămân pași distincți când regulile existente le cer.

„Avem o echipă mai puțin. Arată ce rămâne neacoperit” este o extensie ulterioară. Cere un adaptor de simulare a capacității, nu doar o reformulare a răspunsului. Varianta simulată nu înlocuiește planul activ înaintea aprobării.

### Tehnicianul primește traseul și transmite constatarea

Cerere principală, prin apel: „Ce traseu am și de ce merg la următoarea oprire?”

Agentul identifică echipa autorizată, citește traseul aprobat și explică următoarea oprire din predicția lucrării. Spune orele planificate ca ore planificate. Nu pretinde poziție GPS sau estimare de trafic în timp real.

La „Trimite-mi și traseul pe WhatsApp”, pregătește un rezumat vizual pentru același utilizator verificat. Trimiterea cerută este permisă numai dacă asocierea contului, canalul de mesaje și fereastra de răspuns sunt valide. Un apel singur nu este tratat drept mesaj care deschide acea fereastră.

La „Nu am avut acces” sau „Am găsit altă problemă”, agentul pregătește constatarea, cere clarificări dacă lucrarea nu este identificată și oferă confirmarea în aplicație. După salvare verifică starea și face vizibil blocajul pentru dispecer. Fotografii se pot atașa prin fluxul privat deja existent din aplicație. Primirea și asocierea fotografiilor direct din WhatsApp este o extensie separată.

Tehnicianul poate cere o reevaluare, dar nu poate aproba singur planul global. O constatare de defect nu declară reparația, iar lipsa accesului nu dovedește că predicția a fost greșită.

### Clientul deschide și urmărește cazul propriu

Cerere principală: „Invertorul se oprește la prânz. Înregistrează problema și spune-mi care este pasul următor.”

Agentul identifică punctul autorizat, cere doar informația necesară și pregătește sesizarea. După confirmare o înregistrează fără dubluri. Caută o evaluare ML validă pentru acel punct; dacă nu există date suficiente, solicită date sau analiză umană. Descrierea verbală nu este transformată într-o predicție tehnică inventată.

Clientul poate transmite disponibilitatea pentru acces și poate verifica starea. Primește o explicație potrivită lui, fără traseele echipelor, fotografii interne ori suspiciuni despre alți clienți. O fereastră cerută de client nu devine programare confirmată înaintea validării.

## 3. Cât decide singur

Agentul trebuie să poată termina singur sarcinile pentru care are date și drepturi. Confirmarea se cere la efectul operațional, nu între fiecare pas de analiză.

| Nivel | Agentul face | Limita |
|---|---|---|
| Automat în sarcina cerută | Citește date autorizate, consultă predicții, calculează priorități prin reguli, compară, produce recomandări și generează rapoarte private | Păstrează sursa, data și versiunea; nu schimbă intervenția activă |
| Automat după confirmare | Execută operația exactă aprobată, verifică efectul, actualizează starea comună și pregătește pasul următor | Aprobarea nu se extinde la alte cazuri, alți destinatari sau o altă versiune a planului |
| Delegare configurată ulterior | Reface automat analiza când apar date noi și produce alerte interne după reguli aprobate | Mandat cu acțiuni, domeniu, durată și limite explicite, care poate fi revocat |
| Decizie rezervată omului | Aprobă schimbarea intervenției sau planului, validează constatarea și justifică o corecție | Agentul prezintă dovezile și efectele înaintea confirmării |

În prima versiune, confirmarea schimbărilor rămâne în aplicația autentificată. Un „da” rostit în apel sau primit în WhatsApp nu execută operația. Butoanele de confirmare direct în WhatsApp pot fi adăugate ulterior, după implementarea legării de propunerea exactă și reverificarea identității, versiunii și expirării.

O aprobare pentru un grup de lucrări cere un contract nou pentru întregul grup. Nu trimitem pe rând 25 de aprobări vechi: prima replanificare le-ar putea invalida pe celelalte. Până când acel contract este implementat, agentul analizează toate cazurile, iar revizuirile se confirmă individual pe starea actuală.

## 4. Modelul propriu rămâne baza deciziei

Modelele noastre estimează starea tehnică. Regulile și planificatorul transformă estimările în acțiuni fezabile. Modelul conversațional alege ce funcție autorizată să ceară, explică rezultatul și coordonează pașii. Nu înlocuiește scorurile ML cu propria părere.

Fiecare recomandare tehnică păstrează predicția, versiunea modelului, data intrărilor, regula aplicată, constrângerea relevantă și motivul. Dacă predicția lipsește sau este invalidă, rezultatul spune asta și indică următorul pas permis. O cerere de siguranță ajunge la om fără a aștepta inventarea unui scor.

Agentul poate semnala o contradicție între predicție și constatarea de teren. Corecția autorizată păstrează rezultatul inițial și motivul schimbării. Nu rescrie probabilități, nu reantrenează automat modelul și nu transformă o corecție operațională într-o etichetă ML fără verificare.

Tema PPC permite coordonarea prin LLM și include recomandările, prioritizarea și rapoartele între acțiuni. Fluxul automat de la date la predicție, decizie și raport continuă să existe; omul preia excepțiile și aprobările cu impact. Aceasta este interpretarea de proiectare din [tema oficială](../materiale/Smarthack_XI_2026_Tema_PPC.pdf), nu o aprobare formală a juriului.

## 5. Telefon, WhatsApp și aplicație

### Apelul de pe telefon

Prima versiune folosește apelul WhatsApp existent, fără număr telefonic nou. Agentul confirmă scurt că verifică, cere datele reale și răspunde numai după primirea rezultatului. Pentru sarcini mai lungi spune că pregătește raportul și oferă continuarea în aplicație. Trimiterea pe WhatsApp urmează regulile de mesagerie de mai jos.

Răspunsul vocal începe cu informația utilă: următoarea oprire, decizia necesară sau blocajul. Detaliile și lista completă merg în raport. O eroare a serviciului produce un răspuns explicit și revenire la text. Agentul nu rămâne la „verific” fără rezultat ori stare de eroare.

Apelurile telefonice obișnuite, din afara WhatsApp, sunt o etapă ulterioară cu furnizor, număr, tarife și identitate de apelant verificate separat. Nu le includem implicit în capabilitatea existentă. Convorbirea nu se înregistrează implicit.

### Mesajele și notele vocale

Textul și nota vocală pornesc aceeași sarcină și folosesc același serviciu de operații. La o notă vocală, transcrierea precedă analiza; răspunsul verificat poate fi și rostit, conform preferinței existente. Dacă sinteza audio eșuează, textul rămâne disponibil.

În prima versiune răspundem persoanei care a cerut informația. Notificările nesolicitate și informarea altor destinatari cer o funcție și permisiuni distincte. WhatsApp permite răspunsuri fără șablon în cele 24 de ore de la ultimul mesaj al utilizatorului; în afara ferestrei cere șabloane aprobate. Un apel nu este presupus că deschide această fereastră. Regula se verifică înaintea fiecărei trimiteri, conform [politicii WhatsApp](https://whatsappbusiness.com/policy/).

Identitatea, cazul selectat și sarcina în curs sunt comune între canale numai după verificarea contului. Nu copiem automat toate transcrierile și nu tratăm istoricul conversației ca dovadă că o acțiune a reușit. Utilizatorul poate relua o propunere proprie prin aplicație; o schimbare de plan obligă agentul să o reevalueze.

### Raportul vizual în WhatsApp

Propunerea este să generăm un document HTML dintr-un șablon fix și date verificate, apoi să îl transformăm în PNG. API-ul Meta are mesaje de imagine, inclusiv trimitere pe baza unui identificator media, documentate în [colecția oficială](https://www.postman.com/meta/whatsapp-business-platform/request/w8epkqd/send-reply-to-image-message-by-url). Generarea HTML și transformarea în imagine sunt componente noi Daybreak.

Sunt suficiente trei șabloane inițiale:

- Traseul tehnicianului, cu opriri în ordine, ore planificate, motivul intervenției și blocaje.
- Lista dispecerului, cu recomandări prioritare și cazuri care cer judecată umană. Cele 25 de cazuri nu sunt înghesuite într-o singură imagine; rezumatul trimite la lista completă autentificată, iar detaliile pot fi paginate.
- Starea clientului, cu ultimul pas confirmat și următorul pas cunoscut.

Imaginea folosește designul PPC existent și limba conversației. Arată momentul generării, data scenariului și starea de propunere sau aprobare. Textul accesibil și un link separat însoțesc imaginea. Butoanele desenate într-un PNG nu pot confirma nimic.

Șablonul primește numai câmpuri permise rolului. Textele sunt escapate; nu se execută HTML, scripturi sau adrese furnizate de utilizator ori generate liber de LLM. Randarea nu accesează rețeaua sau fișiere arbitrare. Pornim fără hartă externă pentru a evita o dependență de chei și tile-uri; harta aprobată rămâne în aplicație.

Raportul este un instantaneu. Dacă planul se schimbă, imaginea veche nu poate fi actualizată pe telefon; linkul recitește starea actuală. Documentele nu sunt publicate ca URL-uri media deschise. Se încarcă prin API-ul Meta și se trimit numai destinatarului verificat. Nu promitem revocarea unei imagini deja descărcate de acesta.

## 6. Componentele noi și ordinea lor

### Coordonator de sarcini

Construim un coordonator în serviciul aplicației. El primește o intenție structurată de la modelul conversațional, verifică dacă funcția este permisă, o execută și întoarce rezultatul pentru următorul pas. Conversația poate continua astfel mai multe operații de citire și pregătire.

Procesul LLM rămâne izolat, fără shell sau acces general la calculator. Caracterul agentic vine din funcțiile aplicației pe care le poate solicita, nu din eliminarea protecțiilor procesului. Se extind schema de intenții și validarea; modificarea promptului singur nu este suficientă.

Prima listă de funcții include citirea cozii complete, citirea lucrării și dovezilor, citirea traseului aprobat, analiza cozii, generarea raportului și pregătirea operațiilor existente. Simularea capacității și aprobarea în grup se adaugă separat. Funcțiile calculează totalurile și diferențele; LLM-ul nu inventează calcule și nu primește dreptul de a modifica date autoritare.

### Starea unei sarcini

O sarcină păstrează utilizatorul verificat, canalul, scopul, obiectele permise, versiunea datelor, pașii executați și rezultatele. Stările propuse sunt în lucru, cere informații, așteaptă confirmare, execută, finalizată, eșuată sau necesită reconciliere. Confirmarea și jurnalul operației existente rămân sursa efectelor reale.

Se propun limite inițiale de maximum șase pași de coordonare LLM pentru o cerere interactivă și un timp maxim configurabil. Parcurgerea a 25 de cazuri este o funcție de lucru în fundal, nu 25 de ture LLM succesive. Refolosim predicțiile valide pentru scenariul respectiv; nu pornim toate modelele lente la fiecare întrebare despre traseu.

La expirarea timpului, sarcina rămâne vizibilă și nu se declară finalizată. După restart se reia din rezultatul durabil. O trimitere WhatsApp cu rezultat necunoscut intră în reconciliere, fără retrimitere automată. Predicțiile și drepturile se reverifică la fiecare pas care le folosește.

### Recomandări și rapoarte cu dovezi

Analiza citește toate paginile din coada autorizată și produce câte un rezultat pentru fiecare caz. Verificarea finală compară mulțimea de cazuri citite cu rezultatele. Orice omisiune împiedică afirmația că analiza cozii este completă.

Valorile derivate, precum totalurile și diferențele între variante, sunt calculate de funcții și intră în dovezile răspunsului. Se păstrează verificarea cifrelor și a surselor, extinsă pentru aceste rezultate. Numerele din voce, text, HTML și PNG provin din aceeași structură verificată.

### Confirmare și efect real

Înainte de Confirm se arată operația exactă, obiectul, motivul și efectul așteptat. La confirmare se reverifică identitatea, drepturile, versiunea și valabilitatea propunerii. După execuție, coordonatorul recitește planul sau cazul. Răspunsul descrie efectul efectiv, inclusiv refuzul, lipsa unei echipe sau necesitatea altei aprobări.

O comandă repetată întoarce același rezultat și nu execută încă o dată efectul. O cădere între execuție și răspuns se tratează prin recuperarea existentă, nu prin refacerea operației pe baza conversației.

## 7. Livrare în etape

Estimările sunt ore de lucru pentru implementare și verificare, fără timpi de aprobare externă. Sunt orientative și nu au fost măsurate pe noul flux.

| Etapă | Livrabil | Estimare | Condiție de încheiere |
|---|---|---|---|
| 1 | Coordonator limitat și analiza întregii cozi | 1,5–2,5 ore | Fiecare caz are rezultat și sursă, fără schimbarea planului |
| 2 | Un flux complet de revizuire și unul de constatare | 0,75–1,5 ore | Confirmarea produce efect verificat și vizibil în celelalte conturi |
| 3 | Raport HTML transformat în PNG și trimitere la cerere | 0,75–1,5 ore | Imagine lizibilă primită pe telefon, cu aceeași stare ca aplicația |
| 4 | Verificare integrată, probe de eșec și repetiție demo | 1–2 ore | Criteriile de acceptanță trec, cu limitele externe declarate |

Total orientativ: 4–7,5 ore pentru prima versiune, pornind de la componentele existente. Păstrăm timp pentru testare înaintea termenului PPC de 12:00, București. Dacă timpul disponibil nu ajunge, păstrăm analiza completă, o operație confirmată și traseul telefonic; amânăm imaginea înainte să reducem corectitudinea sau verificările.

Prima versiune acoperă toate cele trei roluri în aplicație și tehnicianul pe numărul WhatsApp deja asociat. Dispecerul și clientul prin apeluri și mesaje se adaugă după legarea identităților lor și testarea independentă. Nu declarăm trei roluri testate pe WhatsApp folosind aceeași asociere de tehnician.

După prima versiune: simularea capacității, schimbări de plan în grup cu reguli proprii, confirmări securizate în WhatsApp, fotografii primite prin WhatsApp, declanșare automată la evenimente și notificări autorizate. Telefonia obișnuită și conectarea la sisteme PPC reale sunt etape separate.

## 8. Cum verificăm că funcționează

Dezvoltarea folosește o copie completă, proaspătă și izolată a stării de referință. Copia nu include secrete sau setări care pot trimite mesaje. Identitățile și datele adăugate pentru test sunt etichetate sintetice. Probele furnizorilor simulați, probele API reale și probele fizice de pe telefon sunt raportate separat.

Acceptanța primei versiuni cere:

1. Analiza unei cozi de 25 de cazuri întoarce exact 25 de rezultate, fără dubluri sau omisiuni. Totalurile se potrivesc sursei complete, inclusiv când sunt necesare mai multe pagini.
2. Fiecare recomandare tehnică are predicție validă și regulă, sau spune explicit ce lipsește. Încrederea în cauză rămâne separată de probabilitatea existenței unei probleme.
3. Un caz cu limită de capacitate nu devine repartizat doar fiindcă LLM-ul recomandă aprobarea. Un caz incert nu își pierde semnalul de siguranță prin rezumare.
4. Revizuirea confirmată apelează planificatorul real, iar răspunsul descrie rezultatul real. Modificarea invalidantă a planului cere o propunere nouă.
5. Traseul din voce, text și imagine coincide cu traseul aprobat al tehnicianului. Planul neaprobat nu este prezentat drept instrucțiune de plecare.
6. Constatarea se salvează o dată și ajunge la dispecer; clientul primește numai starea permisă. Nici confirmarea defectului, nici lipsa accesului nu închid automat cazul.
7. O adresă sau o declarație verbală de rol nu acordă acces. Revocarea apartenenței oprește inclusiv o sarcină sau propunere începută anterior.
8. Un „da” ambiguu, un mesaj citat sau o înregistrare din istoric nu confirmă. Confirmarea repetată nu dublează efectul, iar propunerile unui alt utilizator sunt refuzate.
9. Imaginea nu taie textul pe un telefon de 360 px; raportul lung este paginat. Textele speciale nu devin HTML executabil, iar datele altui rol nu apar în document.
10. Pierderea LLM-ului, vocii sau randării produce un răspuns controlat. Textul rămâne disponibil când audio sau imaginea eșuează. Un rezultat necunoscut de trimitere nu provoacă duplicate.
11. Se testează cel puțin o conversație cu două ture prin unealta reală, apoi apelul WhatsApp fizic și primirea imaginii. Într-o probă separată se verifică zgomotul și sfârșitul vorbirii.
12. Măsurăm aceeași sarcină făcută manual și cu agentul: timpul până la lista revizuită, timpul până la primul răspuns util și erorile observate. Raportăm probele individuale; nu prezentăm o singură măsurare drept garanție statistică.

Nu trimitem probe către terți sau clienți reali. Verificarea funcțiilor publicate, dacă se aprobă publicarea, se face și pe live; rezultatul local singur nu închide acceptanța.

## 9. Costuri și fiabilitate

Analiza și generarea documentelor reutilizează modelele și infrastructura existente. Folosirea conversației rămâne supusă limitelor abonamentului. Vocea consumă credite ElevenLabs, iar taxele Meta se verifică pentru canal și țară. Nu atribuim un cost numeric fără credit și tarif confirmate. [Documentația ElevenLabs](https://elevenlabs.io/docs/eleven-agents/whatsapp/troubleshooting) distinge taxarea serviciului vocal de taxarea Meta.

Se păstrează limite de durată, concurență și volum de răspuns. Raportul PNG se generează la cerere sau când aduce informație utilă, fără o imagine nouă pentru fiecare replică. Întrebările simple despre traseu folosesc direct datele verificate, fără rularea unui flux lung de analiză.

Pentru demo, calculatorul, API-ul, workerul Meta și serviciul de apeluri trebuie să rămână active. Restarturile componentelor se fac separat, după verificarea supravegherii proceselor. Pentru utilizare permanentă este necesară găzduire stabilă și o rută HTTPS verificată pentru confirmare; acestea cer o decizie de publicare separată.

## 10. Demo recomandat

În cinci minute demonstrăm un circuit comun, folosind conturi sintetice și scenariul istoric etichetat:

1. Dispecerul cere analiza cozii. Agentul produce recomandări pentru toate cazurile și explică unul incert sau blocat de capacitate.
2. Dispecerul confirmă revizuirea unui caz. Vedem efectul real și, când este necesar, aprobă planul rezultat.
3. Tehnicianul sună pe WhatsApp și cere traseul aprobat. Cere apoi rezumatul vizual; dacă fereastra de mesagerie nu este deschisă, trimite întâi un mesaj în chat.
4. Tehnicianul raportează o constatare și o confirmă în aplicație. Dispecerul vede actualizarea, iar clientul vede starea permisă a aceluiași caz.

Dacă imaginea sau canalul extern nu trece acceptanța, demo-ul folosește raportul autentificat din aplicație și declară limita. O machetă nu este prezentată drept mesaj livrat, iar o propunere nu este prezentată drept intervenție executată.

## Surse pentru implementare

- [Contractele existente ale conversației](operations/CHANNELS.md), [operațiile și confirmarea](operations/BACKEND.md), [pornirea și apelurile](operations/RUNBOOK.md).
- [Coordonarea actuală](../src/cyberpunks/channels/conversation.py), [intențiile acceptate](../src/cyberpunks/channels/models.py), [izolarea furnizorului](../src/cyberpunks/channels/codex.py), [apelurile WhatsApp](../src/cyberpunks/channels/whatsapp_calls.py), [transportul mesajelor](../src/cyberpunks/channels/whatsapp_transport.py).
- [Regulile planificatorului](../src/cyberpunks/planner/decide.py) și [agentul de planificare](../src/cyberpunks/planner/agent.py).
- [Legătura SIP ElevenLabs](https://elevenlabs.io/docs/eleven-agents/phone-numbers/sip-trunking), [limitele integrării WhatsApp](https://elevenlabs.io/docs/eleven-agents/whatsapp/troubleshooting), [politica de mesagerie WhatsApp](https://whatsappbusiness.com/policy/) și [mesajele de imagine din colecția Meta](https://www.postman.com/meta/whatsapp-business-platform/request/w8epkqd/send-reply-to-image-message-by-url), consultate la 8 noiembrie 2026.
