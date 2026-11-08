# Agent care decide și execută prin mai multe canale

## Cererea din 8 noiembrie 2026

Teo relatează că un mentor de business a considerat utilă ideea unui agent care ia decizii pentru utilizator. Acesta este feedback de produs transmis de Teo, nu o confirmare a regulamentului sau un acord al juriului.

Teo cere un plan pentru comportament agentic, folosind telefonul și WhatsApp în funcție de cont. Exemplele lui: tehnicianul întreabă ce traseu are, dispecerul întreabă ce sarcini are, iar mesajele pot primi rapoarte mai lizibile, generate ca HTML și transformate în imagine. Cererea curentă este planificarea, nu implementarea sau activarea unor servicii.

## Planul propus

[Planul pentru decizii și execuție](../docs/PLAN-AGENTIC.md) completează catalogul anterior de 80 de cazuri. Agentul coordonează funcții limitate ale aplicației, folosește predicțiile locale și regulile planificatorului, produce analiza întregii cozi și verifică efectul după operațiile confirmate. Propunerea păstrează confirmarea în aplicație pentru schimbări operaționale; confirmarea direct în WhatsApp, aprobarea în grup și simularea capacității au contracte noi și etape separate.

Prima versiune recomandată acoperă cele trei roluri în site și tehnicianul pe numărul WhatsApp deja asociat. Celelalte roluri pe telefon cer numere verificate sau o legare sigură din cont; nu se schimbă rolul prin conversație. Apelul WhatsApp singur nu este presupus că deschide fereastra de mesagerie. Rapoartele PNG sunt propuse, nu implementate sau trimise în această etapă.

Estimarea din plan este 4–7,5 ore pentru implementare și verificare, orientativă, fără aprobare externă și fără promisiune de finalizare. Prioritatea este analiza completă, o operație confirmată și traseul telefonic; imaginea se amână dacă ar consuma timpul verificării.

## Dovezi și limite

Planul se bazează pe codul local, documentele operaționale, tema oficială PPC și documentația Meta/ElevenLabs. Au fost verificate legăturile și coerența documentelor, fără retestarea serviciilor live, apeluri, mesaje, modificări de conturi sau deploy. Demonstrația vizuală din chat descrie comportamentul propus și nu este o interfață implementată. Datele istorice și identitățile sintetice își păstrează etichetele.

## Prompturi pentru lucru în paralel

Teo a cerut apoi pregătirea cât mai multor prompturi pentru implementare paralelă, ca să scurteze timpul. Pachetul este în [docs/agentic-prompts](../docs/agentic-prompts/README.md): 19 prompturi, dintre care un coordonator, 14 joburi de implementare, două de verificare și două revizii independente. Contractele se îngheață înaintea consumatorilor; fiecare job are fișiere proprii, iar coordonatorul conectează fișierele centrale. La limita sesiunii se folosesc maximum trei copii simultan, pe lângă coordonator.

Două analize delegate read-only, pentru împărțirea modulelor și criteriile de acceptanță, au fost încorporate și închise. Au clarificat că sursa operațională conține deja toate lucrările, coada human_review diferă de toate lucrările, citirea unei comenzi poate reconcilia, paginile PNG cer identificatori de livrare separați și proxy-ul JSON nu transportă implicit imaginea. Reluarea V1 cere identitate reverificată, nu doar actor salvat.

Manifestul pachetului a fost verificat pentru 19 sarcini, 83 de căi deținute fără suprapunere, dependențe fără cicluri și legături locale valide. Aceste verificări privesc prompturile. Implementarea agentică, serviciile și trimiterile externe nu au fost pornite de această cerere.

## Predare pentru brainstorming, 8 noiembrie 2026

Teo cere publicarea contextului și planului pe `main`, ca un alt coleg să poată propune mai multe idei. În firul principal a cerut și prompturi pentru implementare în paralel. La această predare, prompturile sunt cerute, nu confirmate ca finalizate; implementarea noului plan nu este dovedită.

### Punctul de plecare al colegului

- Citește acest document, [planul agentic](../docs/PLAN-AGENTIC.md), [starea implementării](14-agent-conversational.md) și [tema PPC](07-tema-ppc.md). Catalogul anterior este în [planul conversațional](../docs/PLAN-AGENT-CONVERSATIONAL.md).
- Propune mai multe sarcini pe care utilizatorul le poate delega cap-coadă, separat pentru dispecer, tehnician și client. Exemplele lui Teo sunt analiza a 25 de tichete, traseul cerut prin apel și raportul WhatsApp ca imagine. Acestea sunt puncte de plecare, nu o listă închisă.
- Pentru fiecare idee explică problema, cererea utilizatorului, datele și modelul folosit, ce decide agentul, ce execută, când cere confirmare și cum verifică rezultatul. Spune ce există deja și ce trebuie construit.
- Compară ideile după utilitate pentru PPC, dovada folosirii modelului ML propriu, efort, dependențe externe și claritatea unui demo de cinci minute. Recomandă o ordine de lucru; estimările sunt propuneri, nu rezultate măsurate.
- Explorează cum poate informația din teren să schimbe recomandarea, păstrând separat predicția inițială, decizia omului și motivul. LLM-ul nu inventează probabilități și nu înlocuiește modelul antrenat.
- Identifică sarcini independente care pot fi implementate în paralel și dependențele dintre ele. Brainstormingul nu autorizează activarea serviciilor, plăți, mesaje, schimbări de cont sau deploy.

Feedbackul de business susține direcția de produs. Încadrarea în tema PPC rămâne interpretarea echipei din documentul oficial, fără confirmare separată a mentorilor asupra regulamentului.

## Simplificare acceptată

Teo a considerat excesive cele 19 prompturi și a acceptat reducerea la cinci sarcini. Pachetul activ este docs/agentic-prompts/compact, cu integrarea și verificarea la coordonator. Primele trei joburi rulează după fixarea contractelor; al patrulea ocupă primul loc liber. Vechile prompturi sunt referință, nu joburi suplimentare. Implementarea nu a fost pornită.

## Implementare locală autorizată, 2026-11-08 05:18 București

Teo a cerut explicit începerea implementării. Cele patru joburi de implementare și integrarea au fost executate, cu maximum trei copii simultan; toate delegările sunt închise. Codul local include analiza întregii cozi, sarcini persistente și reluare autorizată, pregătire legată de versiuni, observație pasivă a efectului, carduri în conversație și rapoarte PNG conectate la registrul/workerul Meta. Confirmarea rămâne în aplicație.

Verificări: 689 de lucrări, toate cele 25 de cazuri analizate, 262 de probe Python trecute, apoi 35 de regresii afectate repetate; 239 probe web trecute și șapte probe runtime web omise. TypeScript, lint și build Next izolat cu webpack trec. Codex real a parcurs două ture, cu task complet și confirmare necesară, fără efect operațional. Chromium real produce PNG, Meta este simulat în probe. Layoutul componentei reale a fost verificat static la 360 px.

Corecții confirmate: proprietatea nullable task_goal trebuie inclusă în required pentru schema structurată Codex; observația nu poate apela command care reconciliază; raportul și sarcina se invalidează și când se schimbă versiunea cazului fără schimbarea planului; paginile PNG se persistă atomic înaintea trimiterii. Pentru build izolat folosiți cwd web și dependențe rezolvabile în acea rădăcină; symlinkul din afara rădăcinii a fost refuzat de Turbopack.

Nu au fost repornite serviciile demo, publicată aplicația, schimbate conturi/configurații private sau trimise apeluri/mesaje Meta. Activarea și proba fizică nouă pe telefon rămân separate. Detalii în docs/operations/AGENTIC-ACCEPTANCE.md.


## Activare autorizată, 8 noiembrie, 05:57

Teo a cerut publicarea și testele live. Site-ul public este conectat la serviciul operațional existent prin intrarea restrânsă 8723 și o legătură HTTPS autentificată. Publicarea `39da5489-2891-453f-b8bd-6dbc84bcd661` include agentul; conturile și registrele au fost păstrate. Circuitul complet sintetic al celor trei roluri, analiza celor 25, confirmarea unică, fotografiile private și două imagini cu callback de livrare au fost verificate pe serviciile reale. Vocea a completat circuitul la a doua probă, dar testul strict al reproducerii identice a textului nu a trecut; prima probă a avut timeout. Apelul fizic este încă neconfirmat. Backendul și tunelurile depind de calculatorul pornit. Detalii: `docs/operations/AGENTIC-ACCEPTANCE.md`.


## Apelul fizic, PDF și regresii agentice, 8 noiembrie 10:19

Apelul fizic al lui Teo a ajuns la ElevenLabs, dar ambele cereri HTTP spre Daybreak au primit 530. Serviciul local 8722 răspundea, iar originea temporară publică nu mai era accesibilă. Tunelul a fost înlocuit și adresa uneltei recitită. Proba reală repetată a apelat unealta și a rostit răspunsul operațional în 21,57 secunde total. Teo nu poate retesta momentan telefonul; întreruperea și sunetul fizic nu sunt reconfirmate. Comanda verify verifică acum și sănătatea originii publice plus refuzul 401 al endpointului neautentificat; testul 530 nu mai poate trece numai pe baza configurației SIP.

Au fost refăcute și legătura workspace-ului și callbackul Meta, acesta din urmă după restaurarea unicului ingress/worker. Setările Workerului au fost actualizate păstrând celelalte bindings. Acceptanța live pentru cele trei roluri, coada completă de 25, accesul la task și traseul aprobat a trecut din nou. Legăturile rămân temporare și depind de procesele locale, nu reprezintă găzduire permanentă.

Rapoartele WhatsApp sunt implicit un singur PDF A4. Cererea explicită de imagine/PNG păstrează PNG-ul. PDF-ul folosește HTML fix verificat, Chromium offline fără scripturi, numere de pagină fizice și text de confirmare; octeții, hash-ul și manifestul se persistă atomic. Manifestul este obligatoriu înainte de transport. Actorul, fereastra și versiunile se reverifică. Un rezultat necunoscut nu este retrimis. Proba reală a PDF-ului tehnicianului are două pagini, hash egal cu octeții salvați și callback Meta delivered. Este un follow-up de test autorizat, legat de un mesaj real anterior cu timestampul original, nu un mesaj de intrare inventat.

Auditul a identificat cinci defecte, acum corectate: observarea concurentă returna 409 după un efect reușit; needs_reconciliation nu mai putea observa ulterior succesul; propunerea expirată era încă descrisă ca așteptând Confirm; următoarea oprire putea avea deja constatare; raportul tehnicianului omitea locul. Cele 45 de probe noi de regresie trec fără xfail. Testele de PDF acoperă paginare fizică la text lung, toate rândurile în ordine, manifest atomic, timeout fără dubluri și reluare fără rerandare. Probele afectate agentic/canale au trecut după integrare; lint și diff-check trec.


### PDF de teren revizuit, 8 noiembrie 10:31

Teo a cerut un aspect și un limbaj mai uman pentru PDF-ul primit, inclusiv denumirea fișierului. Fișa tehnicianului are acum titlul „Fișa de traseu”, ore HH:MM, durate în ore/minute, distanțe cu virgulă, număr de opriri și timpul total la intervenții calculat în cod. Formulele de cost și scorurile sunt înlocuite în fișa de teren cu explicații scurte, obținute determinist din tiparele verificate; motivul necunoscut este păstrat exact, iar riscul meteo nu este reformulat drept problemă de bilanț. Cazurile de siguranță rămân vizibile. Datele istorice și sintetice sunt etichetate.

PDF-ul real cu șase opriri încape pe o pagină și a fost inspectat după randare. Numele transmis prin Meta este Daybreak-Traseu-8-iulie-2025.pdf, fără identificator de task ori hash. Octeții și hash-ul persistă în registrul privat. Testele afectate de randare/transport și cele două probe noi de prezentare trec; lint și verificarea diferențelor trec. Meta a acceptat documentul nou; livrarea nu este încă reconfirmată.

Ingressul Meta și workerul rulează separat, câte un proces. Verificarea porturilor din vechiul supervisor putea refuza repornirea după oprire din cauza portului încă rezervat temporar; pornirea independentă a fost verificată prin listener și mesajul de singleton al workerului. Nu s-au schimbat conturile sau asocierile.

### Strat LLM pentru decizii operaționale, 8 noiembrie 2026

Teo a cerut explicit ca LLM-ul să aleagă și să poată aplica decizii, nu doar să citească explicațiile planificatorului. Captura transmisă arăta și un refuz de ștergere lângă rezultatul unei operații anterioare, afișare care putea sugera o schimbare greșită.

Noua sarcină recommend_queue trimite întreaga coadă autorizată către LLM. Acesta alege approve, reject, defer sau abținere pentru fiecare lucrare și oferă un motiv cu dovezi exacte. Predicțiile ML sunt păstrate. Codul verifică acoperirea exactă, cifrele, incertitudinea, capacitatea, riscul și versiunea sursei. Inferența are timp limitat și un claim persistent; rezultatul conține furnizorul și modelul folosite. O propunere se pregătește din recomandarea salvată, nu din decizia trimisă de browser. Confirmarea existentă execută planificatorul real. Schimbarea planului impune o analiză nouă; aprobarea în grup și ștergerea arbitrară nu sunt adăugate.

Interfața oferă Recommend decisions și Review & apply. O cerere nouă elimină imediat cardul rezultatului anterior și propunerea activă, inclusiv la refuz sau eroare; istoricul și drafturile persistente rămân. Probele UI verifică separat că un simplu „da” nu confirmă.

Copia proaspătă a datelor live a inclus 1305 fișiere cu hash-uri identice sursei, fără configurări de automatizare. Prima probă cu furnizorul real Codex, gpt-6.1-sol, a acoperit toate cele 25 de cazuri în aproximativ 70 de secunde: șapte amânări și 18 abțineri pentru evaluări insuficiente. Pe copia izolată, una dintre amânări a fost pregătită și aplicată prin planificator; confirmarea repetată a returnat aceeași comandă. Această probă locală nu dovedește încă fluxul live al versiunii noi.

La publicarea frontendului a fost identificată o regresie de configurare: checkoutul izolat de release păstra o adresă temporară veche a API-ului, iar deploy-ul suprascria adresa curentă din Worker. Legătura a fost restaurată și recitită, păstrând celelalte bindings. Comanda de deploy verifică acum sănătatea API-ului și refuzul 401 pentru citirea neautentificată, înainte de publicare. Acceptanța pentru trei sesiuni independente, coada completă, izolarea taskurilor și traseul aprobat a trecut separat pe localhost:3870 și pe site-ul public. Proba LLM prin UI local rămâne în curs la momentul acestei note.

### Acceptanță finală 2026-11-08 11:05

Proba finală în interfața locală, 127.0.0.1:3870, a trecut cu LLM-ul real: toate cele 25 de cazuri, șapte amânări propuse și 18 abțineri pentru dovezi insuficiente. Sarcina reală salvată a fost redeschisă după restartul browserului, o recomandare a fost pregătită din rezultatul salvat și Confirm a aplicat amânarea prin planificator. Refuzul ștergerii nu a păstrat vechiul Saved. Interfața la 390 px nu are depășire orizontală; capturile rezultatului și ale versiunii mobile au fost inspectate. Aprobarea planului rezultat a fost verificată separat, cu aceeași comandă la confirmare repetată, ca traseele de demonstrație să rămână utilizabile. Cele trei roluri au trecut din nou acceptanța locală.

Proba reală a descoperit și un refuz excesiv al verificării dovezilor: o abținere nu putea explica de ce predicția salvată este inutilizabilă. Acum numai explicația unei abțineri poate cita exact acele intrări. Verificarea numerelor și a afirmațiilor despre efecte rămâne activă, iar aceleași dovezi nu pot justifica o acțiune. Cele două regresii noi trec; 87 de probe de recomandări/API și 38 de probe pe integrarea main, inclusiv trasarea existentă, au trecut. Codul funcției și corecțiile sunt în main.

Legătura publică și canalele au rămas disponibile după încărcarea codului. Verificarea SIP/TLS și a instrumentului public a trecut fără apel fizic ori mesaj nou. Sunetul și întreruperea pe telefon nu sunt reconfirmate în această probă.

### Trei roluri pe același număr, 2026-11-08 11:28

Teo a cerut explicit ca propriul număr verificat să poată demonstra clientul, dispecerul și tehnicianul în același apel WhatsApp de aproximativ un minut. Această autorizare nouă permite numai un mod demo privat, cu trei actori sintetici preautorizați din conturile locale autentificate; nu generalizează schimbarea rolului prin conversație pentru apelanți obișnuiți. Legătura telefonică inițială rămâne neschimbată și este reverificată la fiecare replică. Fereastra demo este de trei ore, păstrată în configurația privată, fără număr ori identități în repo. Schimbarea rolului separă istoricul; actorii, organizația și scenariul sunt validate înainte de citire. Confirmarea operațiilor rămâne în aplicație.

Pentru întrebările scurte ale demonstrației, funcțiile folosesc contextul complet autorizat, fără inferența lungă: clientul cu stâlp căzut primește recomandarea de siguranță și o propunere urgentă către operator; dispecerul primește numărul cozii și semnalele de siguranță; tehnicianul primește numai opririle aprobate ale echipei și echipamentul explicit din sursă. Lipsa echipamentului este spusă, nu înlocuită cu o listă inventată. Formularea de siguranță este verificată în ghidul DSU, pagina 2: https://app.dsu.mai.gov.ro/uploads/GHID_SIGURANTA_final_logo_nou_3e032274bd.pdf . Identificatorii tehnici ai contorului nu sunt citiți în răspunsul scurt; locul verificat și detaliile din ordin sunt păstrate.

Copia proaspătă a datelor operaționale conține 1305 fișiere cu hash-uri identice. Testele celor două module și probele furnizorului trec. Testul public, cu același identificator de sesiune și același apelant autorizat, a întors cele trei roluri în 0,9–1,3 secunde pe replică, fără comenzi sau modificări ale planului. În proba reală a furnizorului cu sursă SIP, fără instrumente simulate, toate cele trei invocări HTTP au reușit și agentul a continuat cu răspunsul verificat, nu doar cu o confirmare de ascultare. Timpul instrumentului a fost 1,15–1,63 secunde. Datele verificate atunci: 25 tichete în coadă, două semnale de siguranță, cinci opriri rămase pentru tehnician, următoarea în Sectorul 6. Semnalul de siguranță nu este prezentat ca o clasificare de prioritate existentă în sursă.

Agentul de apel existent a fost actualizat și recitit; identitatea lui, instrumentul, sursa SIP, lista apelanților, confidențialitatea, TLS și criptarea media sunt verificate. Nu a fost pornit niciun apel telefonic și nu a fost trimis mesaj WhatsApp. Răspunsurile furnizorului au fost inspectate ca text; auzul fizic, recunoașterea vocii reale și întreruperea rămân pentru apelul lui Teo. Durata de aproximativ un minut este scenariul de probă, nu o măsurare a apelului fizic.

### Corecția apelului real și acțiuni vocale simple, 8 noiembrie 11:54

Apelul fizic raportat de Teo a expus două goluri ale probelor inițiale: transcrierea a recunoscut „TPC” în loc de „PPC”, iar tăcerea a fost transmisă ca „...”. Parserul cerea marca exactă și păstra rolul de tehnician; preambulul obligatoriu și reangajarea vocală produceau „Verific informațiile” la tăcere. Parserul acceptă acum declarația simplă de rol și variantele ASR, exclusiv pentru actorii preautorizați ai apelantului privat. Punctuația și marcajele de tăcere nu ajung la conversație; preambulul este oprit, iar configurarea reală a furnizorului a fost recitită. Proba furnizorului pentru tăcere a terminat fără răspuns vocal textual. Sunetul fizic și întreruperea nu au fost retestate.

Teo a autorizat explicit simplificarea cu acțiuni și PDF. Două opțiuni private, inactive implicit, permit numai apelantului verificat să înregistreze un incident clar de client și să solicite un raport PDF. Înregistrarea trece prin pregătire, confirmare și observarea comenzii persistate. Stâlpul căzut creează o cerere urgentă internă sintetică, fără contact extern ori repartizare de echipă; întreruperea creează o sesizare sintetică. Formulările negative, citatele, ipotezele, întrebările și „da” nu execută. Aprobarea intervențiilor și planurilor rămâne în aplicația autentificată.

Cererea explicită de PDF folosește actorul demo selectat, fără schimbarea legăturii WhatsApp text. Se păstrează un mesaj WhatsApp real și timestampul său original; apelul nu deschide o fereastră de mesagerie. Documentul este înghețat în registrul durabil cu versiune și hash, iar identitatea, fereastra și sursa se reverifică înainte de trimitere. Rezultatele necunoscute nu sunt retrimise. Clientul primește raportul celei mai recente sesizări proprii, iar fișa tehnicianului folosește opririle aprobate rămase și locurile din sursă.

Proba publică a înregistrat o sesizare de întrerupere și a răspuns pentru toate cele trei roluri în aproximativ 1–1,4 secunde pe replică. Pregătirea și trimiterea PDF au durat aproximativ 14 secunde; callbackurile Meta au ajuns la delivered și read, cu hash identic cu octeții păstrați. Testul furnizorului vocal a apelat instrumentul real și a continuat cu răspunsul pentru fiecare rol, inclusiv înregistrarea urgentă; cererea explicită de PDF a trecut separat. Aceste probe nu verifică microfonul, auzul sau întreruperea pe telefon.

La 11:52 Teo a interzis explicit orice push viitor. Nu se mai execută push fără o instrucțiune nouă explicită care revocă această regulă. Corecțiile ulterioare rămân locale; serviciul local poate fi actualizat în limitele autorizării existente.

### Bucla la schimbarea rolului în apelul fizic, 8 noiembrie 12:04

Noul apel real a înregistrat „Ă, sunt dispecer”, apoi răspunsurile „Dispecer PPC” și „Aleg rolul de dispecer PPC”. Toate trei erau respinse de parserul prea strict. Întrebarea de clarificare oferea opțiuni pe care parserul nu le accepta ca răspuns scurt, astfel că utilizatorul rămânea în buclă. Nu era o lipsă a rolurilor preautorizate.

Corecția acceptă interjecții și legături conversaționale înaintea declarației, alegerea explicită a rolului și numele scurt al rolului. Se aplică exclusiv profilului demo privat verificat. Declarațiile negative, citatele, ipotezele și rolurile multiple rămân respinse, iar apelanții obișnuiți nu primesc drepturi noi. Rolul singur răspunde direct cu situația tichetelor sau traseul; clientul este întrebat ce s-a întâmplat, fără un tur LLM pentru selectarea rolului.

Regresia reproduce exact cele trei formulări din transcriere și parcurge client, dispecer, tehnician și cererea PDF în aceeași sesiune. Cele patru teste au eșuat înainte și au trecut după corecție. Proba publică a parcurs toate patru plus reformulările, fără buclă, păstrând același identificator de conversație. Cele două formulări scurte de dispecer au întors numărul real al cozii. Serviciul de apel a fost reîncărcat separat, fără schimbarea planului și fără push. Prevenție: fiecare opțiune oferită într-o întrebare trebuie acceptată ca răspuns, iar proba de voce trebuie să includă interjecții ASR și întregul traseu în aceeași sesiune, nu numai întrebări ideale independente.

### Cereri întrerupte, execuție automată și lucru separat de voce, 8 noiembrie 12:40

Ultimele transcrieri reale au arătat HTTP 429 la întrebarea tehnicianului, urmat de refuzul raportului. Un apel anterior păstra în lucru o conversație lentă pe limita comună a apelantului. Identitatea rolului era salvată abia după răspuns, astfel că primul eșec lăsa noul apel fără rolul demo selectat și cererea PDF ajungea la răspunsul generic al LLM-ului. Altă formulare reală, „Ă, acuma schimbăm rolul. Sunt dispecer PPC”, cerea extinderea prefixului conversațional. Transcrierea „Pot să le rezolv pe între mine?” și cererea explicită de a rezolva toate cazurile nu aveau flux de execuție.

Acum rolul verificat se salvează înainte de așteptări; limita este separată pe conversație, iar întrebarea nouă din același apel poate anula o inferență veche. PDF-ul și analiza/executarea cozii au joburi SQLite durabile, independente de durata apelului. Răspunsul vocal confirmă numai punerea în lucru; livrarea ori efectul se declară după verificarea rezultatului real. Joburile au preluare atomică, perioadă reînnoită de procesare și token care împiedică un proces expirat să suprascrie rezultatul. Un rezultat incert se păstrează pentru reconciliere, fără repetare automată.

Teo a cerut explicit executarea automată a tichetelor pentru propriul demo. Opțiunea privată allow_queue_actions este inactivă implicit și a fost activată numai pentru apelantul verificat. LLM-ul analizează coada întreagă, păstrând predicțiile și verificările existente. Se aplică numai recomandările validate, cu reverificarea identității și a dovezilor la fiecare caz, versiune curentă și cheie stabilă. Comenzile reușite sunt recitite. Abținerile, lipsa dovezilor și constrângerile de siguranță/capacitate nu devin închideri fictive. La cererea autorizată, planul rezultat este aprobat prin operația existentă a dispecerului, pentru ca tehnicianul să aibă traseul disponibil.

Testele pe copia completă proaspătă au reprodus cele trei eșecuri și au trecut după corecție. Testele de joburi, execuție, anulare, roluri și conversație au trecut. Integrarea cu LLM simulat și operații reale pe copia izolată verifică aplicarea și aprobarea planului. Proba publică cu LLM real a evaluat 25 de tichete, a aplicat șase amânări și a păstrat 19 pentru evaluare; toate cele șase comenzi și aprobarea planului sunt succeeded. Operația completă a durat 128,3 s, inclusiv analiza și replanificările seriale. Ea rulează separat de conversație, nu este prezentată ca încheiată într-un minut. Tehnicianul a primit apoi cinci opriri aprobate în circa 1,1 s după cererea HTTP. PDF-ul a fost pregătit și trimis separat în circa 14 s.

Răspunsurile de punere în coadă și status dintr-o sesiune verificată neschimbată nu mai așteaptă blocarea planificatorului. Orice efect ori trimitere face din nou autorizarea completă; schimbarea configurației sau asocierii invalidează scurtătura. Un test blochează citirea planificatorului și verifică păstrarea răspunsului vocal și lipsa unui duplicat. Furnizorul este configurat cu turn_eagerness eager. Înregistrarea audio rămâne oprită; inspecția a folosit transcrierile și timpii, nu ascultarea unei înregistrări. Microfonul, auzul și întreruperea pe telefon după corecție rămân de verificat. Fără push.

### Pregătire pentru prezentare, 8 noiembrie 12:57

Teo a cerut o verificare completă după eșecurile succesive, fără promisiunea că testele automate garantează telefonul fizic. Copia proaspătă are 1305 fișiere cu hash identic și o copie de siguranță SQLite făcută read-only. Corecțiile au verificări pentru formulări naturale, roluri, întrerupere, status, reluare și rezultat incert. Familia de reguli rapide pentru cereri are peste 150 de exemple pozitive și negative; o întrebare de livrare nu mai declanșează un raport nou, iar pronumele precum „rezolvă-le” cer context de coadă stabilit de server.

Cererile reformulate ori reluate după reconectare pot fi legate durabil de același job activ, numai cu actor și conținut operațional identice. Aliasurile cererilor persistă, astfel că reluarea nu creează o a doua operație. Un handler care încă raportează running nu este marcat done; rezultatele incerte rămân pentru reconciliere și vocea nu spune că procesarea continuă la nesfârșit. Statusul poate recupera ultima operație proprie dintr-un apel anterior. Livrarea raportului se recitește pasiv din registrul Meta, nu rămâne blocată la starea accepted.

Auditul a reprodus o propunere vocală salvată care rămânea descrisă ca pregătită după schimbarea planului. Acum versiunea și expirarea sunt verificate înainte de redarea unei propuneri neexecutate; un efect deja executat își păstrează afirmația istorică verificată. Limita conversației numără cererile fără să țină ocupat apelul pe durata furnizorului; inferențele generale au capacitate separată, iar timeoutul primește un răspuns explicit.

Proba finală a furnizorului vocal real a parcurs, cu aceeași sesiune de server, clientul, formularea „Ă, acuma schimbăm rolul”, situația dispecerului, lucrările tehnicianului și „Îmi dai și mie raportul?”. S-a verificat apoi coalescența cu „Trimite-mi raportul pe WhatsApp”, livrarea efectivă și statusul într-o sesiune nouă. Timpii instrumentului au fost aproximativ 1,2–1,6 s pentru roluri/date și 0,5 s pentru punerea raportului în lucru. Verificarea livrării a răspuns în 0,22 s; acestea nu sunt durate de audio end-to-end. Scriptul read-only daybreak_voice_readiness.py --provider verifică rolurile, expirarea, ruta aprobată, joburile, fereastra reală WhatsApp, accesul public și setările reale ale furnizorului; nu trimite și nu pornește joburi.

Starea curentă a cozii poate fi diferită după operații autorizate; preflight-ul a văzut 24 de cazuri și cinci opriri aprobate, fără joburi în așteptare, active sau incerte. Două teste vechi presupuneau permanent 25 de cazuri; acum verifică numărul și identificatorii din copia completă curentă, fără să modifice datele pentru test. PDF-ul nou este livrat și hash-ul corespunde octeților salvați. A fost solicitată o singură probă fizică pentru auz, întrerupere și primirea PDF-ului; nu este consemnată încă o confirmare umană după această versiune. Fără push, fără schimbarea modelului ML ori a bugetului de optimizare al planificatorului.

### Întreruperea legăturii publice în apelul fizic, 8 noiembrie 13:40

Teo a auzit din nou „serviciul de conversație nu este disponibil”. Transcrierea furnizorului arată HTTP 502 la ambele cereri din apel, după aproximativ 5,3 și 16 s. În aceleași momente, tunelul QUIC a pierdut repetat conexiunea și a anulat cereri spre serviciul local; acesta răspundea în continuare. Sunt dovezi despre transport și transcriere, fără ascultarea unei înregistrări audio.

Tunelul pentru apeluri a fost înlocuit cu unul pornit explicit prin HTTP2/TCP. Noua origine a trecut verificarea publică și refuzul 401 înainte de configurarea uneltei existente; identitatea agentului, numărul, secretul și toate cele trei roluri private au rămas aceleași. S-a oprit numai vechiul tunel pentru apeluri, după recitirea configurației reale Meta/ElevenLabs. API-ul, serviciul vocal, workerul și celelalte două tuneluri nu au fost repornite. Runbookul cere acum explicit HTTP2 pentru pornirea ulterioară și probe repetate, nu o singură citire de sănătate.

Noua legătură a trecut 24 de cereri publice repetate, inclusiv întrebări autentificate, pe durata de circa un minut, fără 502 sau erori în tunel. Durata maximă a unei cereri din serie a fost 3,21 s. Furnizorul real a folosit unealta publică pentru client, dispecer, tehnician și cererea de PDF în aceeași sesiune de server, fără buclă de rol; instrumentul a răspuns în aproximativ 0,45–1,55 s. Meta a confirmat livrarea PDF-ului, iar verificarea stării a răspuns în 0,60 s. Aceste durate nu măsoară sunetul de la microfon la difuzor. Preflight-ul cu furnizor a trecut. Apelul fizic după schimbarea transportului rămâne de retestat. Fără push.
