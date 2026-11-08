# Contractul comun pentru implementarea agentică

Arhivat. Referință a împărțirii inițiale; pentru cele cinci sarcini folosește compact/manifest.json și contractele din cod.

Stare: cerințe de interfață propuse, nu module implementate. Sarcina 01 fixează numele și semnăturile exacte în cod și în schema JSON. Coordonatorul le verifică înaintea lansării implementărilor consumatoare. Versiunea inițială va fi `agentic-v1`. Modificările ulterioare se fac într-un singur loc și se anunță tuturor consumatorilor.

## Ce reutilizăm

`Actor`, cele șase acțiuni operaționale și validatoarele lor vin din `cyberpunks.operations.models`. Citirea și pregătirea folosesc `OperationsService.context` și `OperationsService.prepare`; confirmarea și citirea comenzii păstrează contractele existente. `ConversationService`, proxy-urile web și uneltele vocale sunt conectate exclusiv de 00.

Conversația actuală rămâne compatibilă: `reply`, `proposal`, `provider` și proveniența existentă își păstrează sensul. Datele agentice sunt aditive. O sarcină care a generat un raport nu pretinde că a executat o intervenție. Nici sarcina, nici un fișier de raport nu pot confirma o operație.

## Obiectele comune

- `TaskRequest` descrie scopul dintr-o listă permisă: analiza cozii, rezumatul traseului aprobat, rezumatul cazului sau pregătirea unei operații existente. Are scenariu, selecție autorizabilă, limbă și format dorit. Nu acceptă actor, rol, destinatar liber, HTML sau comenzi.
- `ScopeStamp` este calculat pe server din identitatea și apartenența curente. Se leagă de organizație, utilizator și domeniul curent; valoarea venită de la client nu este de încredere.
- `SnapshotRef` identifică scenariul, data datelor, momentul citirii, versiunea planului și marcajele de date istorice/sintetice. Un `AuthorizedSnapshot` include sursa completă deja filtrată și dovada domeniului. Construcția lui dintr-un mesaj este interzisă.
- `EvidenceRef` leagă o afirmație de un câmp verificat sau de un rezultat calculat de o funcție cunoscută. Pentru rezultate derivate păstrează versiunea sursei și proveniența calculului. Ieșirea liberă a LLM-ului nu este dovadă.
- `QueueAnalysis` include identificatorii sursei, rezultatele per caz și totalurile. Fiecare rezultat separă recomandarea, motivul, incertitudinea, blocajul și efectul încă neexecutat. Marcajul complet se obține numai dacă mulțimea rezultatelor este identică sursei.
- `TaskView` este proiecția publică, fără context brut, semnături private sau date nepermise. Are proprietar verificat intern, stare, progres, rezultat, eventualul identificator al propunerii și referințe la artefacte autorizate. Durata și pașii sunt limitate.
- `ReportData` are variante stricte pentru dispecer, tehnician și client. Include proveniența și numai datele permise rolului. Nu conține HTML liber. `RenderedPage` este un PNG verificat, cu dimensiuni, hash, ordine în raport și text accesibil.
- `DeliveryRequest` este construit de server pentru solicitantul verificat, cu referință la raport și dovada ferestrei valide de mesagerie. Nu este un obiect pe care LLM-ul îl poate popula cu un număr arbitrar.

Acoperirea analizei păstrează separat identificatorii așteptați, citiți și analizați, paginile, erorile, omisiunile și dublurile. Versiunile cazurilor și predicțiilor se păstrează alături de versiunea operațională completă. O schimbare de versiune între pagini cere reluare sau marcarea explicită a instantaneului vechi. Numărul 25 din exemplu nu este limita de analiză, chiar dacă planificatorul are o limită distinctă de revizuire umană pe zi.

Pentru pagini PNG multiple se fixează un identificator stabil per pagină și operație de livrare, legat de hash-ul octeților persistați. Registrul Meta existent are chei pe eveniment și tip; 00 îl extinde controlat pentru pagini de imagine după cerințele 09. Nu se creează un al doilea registru de livrare.

Sarcina 01 fixează limitele de volum și schemele Python/JSON/TypeScript compatibile. Folosește `extra=forbid` pentru intrări și variante discriminate pentru scopuri și rezultate, cu tratarea erorilor conform convențiilor existente. Structurile de mai sus sunt propuneri de denumiri, nu importuri care există deja.

## Interfețele între module

| Producător | Interfață de înghețat în 01 | Consumatori |
|---|---|---|
| 02 | Citire completă autorizată și verificarea versiunii/domeniului | 03, 05, 06, 12 |
| 03 | Analiză deterministă a unui snapshot complet, fără efecte operaționale | 05, 06 |
| 04 | Creare, preluare, tranziție și reluare de sarcină privată | 05, 09, 10, 12 |
| 05 | Pornire/continuare limitată de sarcină și proiecția rezultatului | 00, 10, 12 |
| 06 | Construire de `ReportData` din rezultate verificate și domeniu actual | 07, 11 |
| 07 | Randare HTML escapata și text accesibil din `ReportData` | 08 |
| 08 | Randare locală în PNG, cu limite și rețea blocată | 09, 12 |
| 09 | Pregătire/livrare reconciliabilă prin registrul Meta existent | 00, 10 |
| 10 | Continuare din apel sau mesaje, legată de identitate și sarcină | 00 |
| 11 | Carduri de sarcină/rezultat prin proprietăți și callbacks tipizate | 00 |
| 12 | Router privat și client web prin autentificarea existentă | 00, 11 |
| 17 | Verificarea unică a dovezilor și calculelor | 05, 06 |
| 18 | Pregătire operațională și observație pasivă a efectului | 05, 00 |

Modelele conversaționale rămân în procesul izolat. 05 primește o interfață de planificare injectată și instrucțiuni de sarcină structurate. Extinderea adaptorului actual al furnizorului și a schemei turnului este făcută de 00 după contractul stabilit de 01; 05 nu presupune că vechea schemă acceptă deja noi unelte.

## Stări și reluare

Stările publice propuse sunt `queued`, `running`, `needs_information`, `awaiting_confirmation`, `executing`, `completed`, `failed`, `cancelled` și `needs_reconciliation`. Sarcina 01 definește tranzițiile admise și separă finalizarea analizei de finalizarea operației confirmate.

O confirmare validă existentă poate fi observată de sarcină, apoi rezultatul este recitit fără a executa confirmarea încă o dată. Reluarea cere un actor actual autorizat; un actor salvat nu reactivează apartenența veche. Operațiile și trimiterile cu rezultat necunoscut rămân pentru reconciliere.

Observația fără efect și recuperarea sunt funcții distincte. Metoda existentă de citire a comenzii poate relua reconcilierea; nu poate fi reutilizată implicit ca un instrument pasiv al agentului. 01 fixează interfața de status fără efecte, iar 00 conectează recuperarea numai la calea autorizată existentă. Cererile GET agentice nu execută și nu recuperează comenzi.

Reluarea din prima versiune cere o nouă cerere autentificată sau o asociere telefonică reverificată prin sursa de adevăr. Păstrarea actorului în bază nu autorizează un worker după restart. Dacă nu există reautorizare curentă disponibilă, sarcina rămâne în așteptare până la reluarea autorizată. Tranzacțiile SQLite nu rămân deschise în timpul apelurilor LLM sau HTTP.

Coordonarea în șase pași poate depăși timpul unei cereri HTTP sau al uneltei vocale. Startul și continuarea au bugete mai scurte decât termenul transportului și întorc progres durabil; nu rezolvăm problema doar crescând timeouturile. Proxy-ul conversației are căi permise explicit și răspuns JSON. 12 livrează clientul JSON și un gateway privat separat pentru PNG; 00 actualizează controlat lista de căi, fără a elimina filtrarea ei.

Versiunea se reverifică înaintea recomandării prezentate drept actuale, înaintea producerii sau accesării artefactului și înaintea operațiilor. Imaginea veche rămâne un instantaneu etichetat; accesul la aplicație nu o transformă retroactiv într-o stare actuală.

## Verificarea contractului

01 predă exemple generate din copia completă, cu identități sintetice și câmpuri private eliminate, plus probe de round-trip pentru schema publică. Aceste exemple sunt pentru compatibilitate de interfață și șabloane. Ele nu înlocuiesc setul complet în testele de analiză și integrare.

Coerența copiei se verifică prin lista completă a intrărilor și versiunilor, cu numere și hash-uri față de sursa read-only, nu doar printr-un prag de minimum 600 de lucrări.

Toți consumatorii folosesc aceleași scheme. Un raport, card sau mesaj care nu se poate lega de sursa verificată este refuzat. Codul nou este opțional până la integrarea și verificarea 00, fără fallback care declară succes artificial.
