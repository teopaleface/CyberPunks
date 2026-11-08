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
