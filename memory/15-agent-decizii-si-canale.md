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
