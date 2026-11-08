# Acceptanța locală a agentului Daybreak

8 noiembrie 2026. Implementarea este verificată local. Serviciile existente de demo nu au fost repornite, nu s-a publicat aplicația și nu s-au trimis mesaje sau apeluri de probă prin Meta.

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

Din rădăcina proiectului, cu datele complete pregătite:

```sh
uv run pytest tests/agentic tests/channels tests/operations tests/runtime -x -q
```

`DAYBREAK_OPERATIONS_TEST_DATA` poate indica rădăcina unei alte copii complete, care conține `plans/demo-vara/inputs`. Testele construiesc și copiază separat starea planificatorului. Furnizorii din probele automate sunt simulați, exceptând proba Codex reală descrisă separat mai sus.

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
