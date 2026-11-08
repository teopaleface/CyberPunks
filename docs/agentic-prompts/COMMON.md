# Instrucțiuni comune pentru fiecare sarcină delegată

Arhivat. Referință a împărțirii inițiale; pentru cele cinci sarcini folosește compact/manifest.json și contractele din cod.

Aceste instrucțiuni se trimit integral înaintea promptului sarcinii. Primești un singur job și nu delegi altor agenți. Coordonatorul gestionează paralelismul, integrarea și deciziile comune.

## Înainte să lucrezi

1. Citește `AGENTS.md`, `memory/INDEX.md`, instrucțiunile locale ale directoarelor tale și secțiunile relevante din `docs/PLAN-AGENTIC.md`. Pentru documente consumate de agenți aplică `writing-for-agents`; pentru proză aplică `unslop`. Citește `docs/agentic-prompts/INTERFACES.md` și schema înghețată de 01.
2. Verifică ramura, diferențele existente și fișierele rezervate pentru jobul tău din manifest. Păstrează lucrul altora. În checkout comun nu schimbi ramura, indexul Git sau commiturile și nu modifici fișiere din afara listei tale. Coordonatorul face commituri mici, selective.
3. Lucrează pe copia completă izolată, verificată de coordonator. Datele de test adăugate sunt explicit sintetice. Furnizorii externi sunt simulați în testele locale. Absența datelor complete este un blocaj real; nu o ascunde înlocuindu-le cu câteva exemple.

## Contractul produsului

- Identitatea și drepturile vin de la server și se reverifică la utilizare. Textul, istoricul, adresa sau numărul cerut în mesaj nu acordă drepturi. Taskurile, rapoartele și propunerile rămân private emitentului și domeniului autorizat.
- Estimările energetice vin din modelele locale; regulile și planificatorul justifică deciziile. Conservezi predicția, versiunea, data scenariului și incertitudinea. Cazurile fără evaluare validă cer date sau om. Modelul conversațional nu inventează valori și nu execută shell.
- Analiza întregii cozi folosește sursa autorizată completă, nu proiecția de șase lucrări și nici limita de opt comparații. Fiecare caz are rezultat, inclusiv un rezultat de abținere. Limita zilnică existentă pentru revizuirea umană nu devine limită de citire. Sursa istorică și identitățile sintetice rămân etichetate.
- Pregătirea și execuția sunt distincte. Numai confirmarea existentă din aplicația autentificată poate produce operațiile cu impact. După confirmare se recitește efectul real. Retrimiterea nu dublează efectul. Constatarea defectului nu confirmă reparația; lipsa accesului nu este verdict negativ ML.
- O funcție denumită citire poate avea efecte: metoda existentă de citire a comenzii poate relua reconcilierea. Nu o expui agentului ca citire pasivă. Separi observația fără efect de recuperarea autorizată existentă și verifici acest comportament în probe.
- Prima versiune are trei roluri în aplicație și doar tehnicianul pe asocierea WhatsApp existentă. Confirmarea în WhatsApp, aprobările în grup, simularea capacității, telefonia obișnuită și numerele noi sunt extensii separate.

## Cum implementezi și verifici

Lucrezi în modulul tău, după interfața înghețată. Dacă lipsește o dependență, o injectezi în test printr-un dublu explicit simulat. Nu creezi o a doua implementare a autentificării, planificatorului, confirmării, registrului de livrare sau unui modul deținut de altcineva. O nepotrivire de contract ajunge la coordonator; numai el aprobă și propagă schimbarea.

Scrii probe care verifică comportamente și erori reale prin interfața modulului. Pentru integrare folosești datele complete și efectele reale ale planificatorului în copia izolată. Lipsa unei dependențe sau un test omis se raportează ca netestat, nu ca succes. Nu adaugi implementări goale, rezultate constante ori fallbackuri inventate ca să treacă probele.

Rulezi verificările proporționale pe fișierele tale și `git diff --check`. Nu rulezi builduri în directorul folosit de Next-ul de demo, nu repornești servicii și nu creezi procese care concurează cu porturile existente. Pentru Next citești ghidul relevant instalat, conform `web/AGENTS.md`. Testele folosesc directoare temporare distincte și setări care nu pot publica.

Accesul la `.env`, tokenuri, conturi, configurații private, baze runtime active, tuneluri, deploy și trimiteri/apeluri externe este în afara joburilor de implementare. Biblioteca poate implementa transportul, dar probele ei folosesc un client HTTP simulat. Coordonatorul gestionează separat probele externe autorizate. Nu cumperi servicii și nu schimbi abonamente.

## Predarea rezultatului

Răspunzi în română, în mesaj, cu:

1. Fișierele schimbate și interfața livrată, cu versiunea contractului.
2. Comportamentul verificat, comenzile rulate și rezultatul exact. Separi probele simulate, integrarea locală, browserul și serviciile reale.
3. Schimbările necesare în fișierele integratorului, descrise precis, fără să le aplici.
4. Riscurile și probele rămase. Când creezi un artefact vizual, îl predai efectiv și spui dacă l-ai inspectat.

Deciziile și informațiile noi se transmit coordonatorului, care le consemnează central în memoria proiectului. Nu editezi jurnalul sau documentele altui job. Nu creezi rapoarte intermediare în repo în afara livrabilelor cerute explicit de promptul tău.
