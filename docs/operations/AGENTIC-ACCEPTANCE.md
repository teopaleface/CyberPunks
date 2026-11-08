# Acceptanța locală și live a agentului Daybreak

8 noiembrie 2026. Agentul este activ pe site-ul public. Secțiunile inițiale descriu verificarea locală, înainte de restart și publicare; probele reale, versiunea live și limitele actuale sunt în secțiunea de activare de la final.

## Comportamentul livrat

Conversația poate cere analiza întregii cozi, raportul traseului aprobat sau raportul unui caz. Modelul conversațional alege o intenție structurată; aplicația execută pașii autorizați, folosește predicțiile locale și persistă rezultatul. Procesul modelului rămâne fără shell, MCP sau acces general la calculator.

Analiza selectează explicit coada `human_review` din sursa completă. Produce câte un rezultat pentru fiecare caz, cu motive, incertitudine și dovezi. O limită regională de echipe produce recomandarea de a cere întăriri, nu o repartizare fictivă. Evaluarea indisponibilă produce abținere. Recomandările nu aplică decizii operaționale.

Sarcinile se păstrează într-o bază privată, cu apartenența emitentului, versiunea planului și cererea inițială. Claim-ul cu termen și token împiedică două execuții simultane. Reluarea cere o cerere autentificată actuală. Un plan sau caz schimbat invalidează afișarea rezultatului ca informație curentă.

Pregătirea folosește operațiile existente, cu versiunile exacte ale planului și cazului. Confirmarea rămâne în aplicația autentificată. Observația efectului citește rezultatul salvat fără să cheme metoda care poate reconcilia. O operație confirmată care schimbă planul rămâne observabilă ca efect istoric, fără a prezenta recomandările vechi drept actuale.

Interfața arată recomandări și motive, cu dovezile tehnice în secțiuni care se deschid la cerere. Review deschide formularul existent. Referința ultimei sarcini din sesiune se poate restaura, după reverificarea accesului și versiunii. Schimbarea contului/scenariului izolează starea.

Rapoartele folosesc HTML fix, texte escapate și Chromium izolat pentru PNG. Pe WhatsApp, o cerere explicită de raport dintr-un mesaj autorizat poate pregăti paginile. Registrul existent păstrează atomic raportul complet, octeții, hash-urile și identificatori separați per pagină. Identitatea, fereastra de mesagerie și versiunile se verifică înaintea uploadului și trimiterii. Rezultatul necunoscut nu provoacă retrimitere automată. Eșecul imaginii păstrează textul verificat și explică faptul că imaginea nu a putut fi pregătită.

## Date și verificări

Referința operațională istorică completă a fost copiată separat, fără configurații de trimitere. Au fost comparate hash-urile celor 1.302 fișiere cu sursa read-only. Contextul conține 689 de lucrări și 25 de cazuri în coada de revizuire. Datele sunt pentru 8 iulie 2025; identitățile și sesizările de verificare sunt sintetice. Aceasta nu este o citire a unor măsurători curente din rețea.

- Regresia Python pentru agentic, canale, operații și runtime a trecut toate cele 262 de probe. Sunt incluse acoperirea întregii cozi, autorizarea, confirmarea prin planificatorul real, traseul aprobat, efectele repetate, reluarea și refuzul datelor vechi. După ajustarea implicită a datelor rapoartelor și a fixture-ului portabil au fost repetate cele 35 de probe afectate, toate trecute.
- Web: 239 de probe trecute, șapte probe ale conturilor din runtime-ul privat omise fiindcă acel mediu nu a fost activat pentru această execuție. TypeScript și ESLint pe fișierele afectate trec.
- Build Next de producție reușit într-o copie separată, cu `--webpack`. Directorul de build al demonstrației a rămas separat. Turbopack a refuzat inițial symlinkul către dependențe din afara rădăcinii copiei; aceasta a fost o limită a izolării folosite pentru build.
- Probă cu Codex real pe abonamentul existent, două ture: prima a întors o sarcină completă cu toate cele 25 de cazuri, iar a doua a explicat că schimbările cer Confirm. Nu s-a executat o operație în aceste ture. Extensia schemei JSON cere explicit și proprietatea nullable `task_goal`; omiterea ei din lista required a fost corectată înaintea probei reușite.
- Randare reală a PNG-urilor și transport Meta simulat, cu pagini multiple, timeout necunoscut, retry și verificarea versiunii cazului înaintea rețelei. Proba integrată a workerului a produs un PNG real și l-a trimis clientului HTTP simulat, fără dublarea conversației.
- După ajustarea lizibilității PNG și a mesajului de rezervă au trecut și probele afectate de randare/livrare.
- Afișare statică a componentei reale la 360 px, pe rezultatul complet de 25 de cazuri, cu stiluri proprii și fără depășire orizontală. Aceasta nu înlocuiește o probă nouă autentificată a întregului site pe telefon.

## Repetarea probelor

Din rădăcina proiectului:

```sh
uv run playwright install --only-shell chromium
uv run pytest tests/agentic tests/channels tests/operations tests/runtime -x -q
```

Testele folosesc implicit cele 689 de predicții publice și sintetice din `data/local-runtime`. `DAYBREAK_OPERATIONS_TEST_DATA` poate indica rădăcina unei alte copii complete, care conține `plans/demo-vara/inputs`. Testele refac planul în spațiul temporar pytest și lucrează pe copii separate. Furnizorii din probele automate sunt simulați, exceptând proba Codex reală descrisă separat mai sus.

Din directorul `web`:

```sh
bun test
bunx tsc --noEmit
```

Buildurile se rulează într-o copie separată a sursei și datelor, cu dependențele instalate sau rezolvabile în acea copie. Comenzile Next trebuie să aibă directorul de lucru `web`, nu rădăcina repo-ului.

## Ce rămâne pentru activare și proba externă

Încărcarea codului nou în serviciul API și workerul folosit la demo cere o fereastră de pornire coordonată, cu păstrarea bazelor, callbackurilor și tunelurilor existente. Nu se reprovisionează conturile și nu se pornește al doilea worker pe același registru.

După activare se verifică separat: cele trei sesiuni web nominale, răspunsul operațional prin apel WhatsApp fizic, o cerere explicită de raport în chat și imaginea primită pe telefon. Zgomotul sălii și timpul comparat cu lucrul manual nu sunt măsurate de această execuție.

Asocierea telefonică existentă rămâne a tehnicianului. Nu s-au adăugat identități telefonice pentru dispecer/client. Confirmarea în WhatsApp sau prin voce, aprobarea în grup, simularea capacității și telefonia obișnuită rămân în afara primei versiuni.


## Activare live, 8 noiembrie 2026, 05:57 București

Teo a autorizat explicit publicarea și probele live. Interfața este publicată la https://daybreak.ghiseateodor245.workers.dev, versiunea `39da5489-2891-453f-b8bd-6dbc84bcd661`, din codul de activare `d5a4a93` și corecția `c4e6e2a`. Modificările neterminate ale landingului nu au fost incluse. Conturile, parolele, asocierile și bazele existente au fost păstrate.

API-ul 8720, serviciul de apeluri 8722 și unicul worker Meta au încărcat codul nou. Intrarea restrânsă 8723 expune doar rutele permise, cere acreditarea serverului și identitatea verificată; citirile consolei cer dispecerul organizației demo și dreptul de consolă. Nu expune documentația, webhookul sau scrierile vechi. Adresa temporară a legăturii și acreditarea sunt păstrate privat, inclusiv secretul Workerului.

Cloudflare nu acceptă `redirect: error`; proba reală a identificat eroarea și transportul folosește acum `manual`, cu refuzul răspunsurilor redirecționate. JSON-ul autorizat se transmite fără o a doua parsare și serializare la marginea rețelei. Deschiderea asistentului nu mai citește întregul plan pentru cifrele din meniu. Răspunsurile ne-JSON produc un mesaj controlat; reîncărcarea accesului este o citire explicită. Harta pe mobil folosește coloane suprapuse și zone proprii de derulare. Citirile de acces simultane folosesc aceeași cerere în curs: înainte, intervalul de două secunde putea invalida continuu toate răspunsurile care durau mai mult, blocând restaurarea conversației.

### Probe live efectuate

- Trei sesiuni independente autentificate; izolarea clientului, refuzul operațiilor de dispecer pentru celelalte roluri și revocarea prin logout.
- Analiza exactă a celor 25 de cazuri, accesul numai la propria sarcină, traseul aprobat și raportul sesizării selectate. Două ture Codex reale ca dispecer, fără execuție implicită.
- Sarcină de aprobare a planului curent, confirmare repetată cu aceeași comandă și reluare pasivă a rezultatului.
- Circuit complet etichetat sintetic pe site-ul public: creare de sesizare după Confirm, evaluare locală reală, vizibilitate în toate rolurile, aprobare prin planificator, constatare comună fără reparație fictivă și refuzul propunerii învechite. Conversațiile Codex au răspuns pentru toate cele trei roluri. Raport: `outputs/runtime/acceptance-live.json`.
- Încărcare, citire și ștergere a propriului draft fotografic sintetic; clientul primește 403. Raport: `outputs/runtime/agentic-live-photos.json`.
- Două pagini PNG reale, trimise prin transportul și registrul existente către numărul deja asociat. Callbackurile semnate le-au marcat `delivered`. Proba a folosit mesajul real anterior și momentul lui original, fără să inventeze o nouă fereastră de mesagerie. Nu este o probă nouă a recepției unui mesaj de raport.
- Serviciile reale ElevenLabs și unealta HTTP a apelului au răspuns cu oprirea verificată în 18,04 secunde total, dintre care 12,73 secunde unealta. Nu s-a inițiat un apel fizic.
- Vocea din browser a parcurs ASR → unealtă autenticată pe site-ul public → Codex → răspuns audio, cu context neschimbat. Prima probă a eșuat cu indisponibilitate; diagnosticul separat a confirmat un timeout Codex. A doua a completat circuitul, dar comparația strictă a textului a rămas nereușită: agentul a omis salutul și a spus cifra 5 ca „cinci”, fără schimbarea informației. Cele două probe nu se raportează drept acceptanță vocală strictă trecută. Audio nu a fost ascultat manual.

Probe automate afectate: 33 pentru agentic/intrare, cinci pentru imagini, 241 web trecute cu șapte omise în rularea globală; după eliminarea citirii planului la deschiderea asistentului au trecut și cele opt probe de rutare ajustate. TypeScript, lint, verificarea diferențelor și buildul Cloudflare izolat trec. Fișierele de build folosesc dependențe proprii, fără symlink către alt checkout; construirea finală Next folosește Turbopack, conform configurației de stiluri a proiectului. Buildul webpack intermediar compilase codul, dar nu procesase utilitarele Tailwind; verificarea vizuală a respins acea variantă înainte de acceptanța finală.

Proba vizuală finală în Helium, pe publicarea finală: 25 de rezultate în componenta reală la 1440 px și 390 px, restaurate după reîncărcare pe mobil, fără alerte sau depășire orizontală. Stilurile Geist/Tailwind și ascunderea meniului lateral pe mobil au fost verificate prin randare și proprietăți calculate. Harta hidratată nu mai depășește lățimea ecranului. Raport: `outputs/runtime/agentic-live-task-browser.json`. Cele 23 de stări/pagini verificate pentru cele trei roluri au trecut și în rularea vizuală finală, fără alerte sau depășire laterală; inventar în `outputs/runtime/agentic-live-browser.json`. Cinci citiri consecutive ale contextului public au răspuns cu JSON și HTTP 200.

### Limite operaționale

Site-ul este publicat, dar calculele și canalele rulează încă pe calculatorul lui Teo. Calculatorul și tunelurile trebuie să rămână pornite. Aceasta nu este o migrare a backendului pe găzduire permanentă. O publicare viitoare din configurația implicită `web/wrangler.jsonc` ar reveni la datele demo: păstrați configurația de release privată, cu `DATA_SOURCE=api`, `API_BASE` și originea HTTPS exactă din `outputs/runtime/workspace-origin.txt`, plus secretul Workerului. Nu copiați acreditarea în Git.

Apelul fizic, întreruperea prin voce și microfonul/difuzorul din sală așteaptă proba lui Teo, cerută în conversație. Nu este raportată primirea pe telefon numai din acceptarea Meta; pentru cele două PNG-uri există separat callbackul de livrare.
