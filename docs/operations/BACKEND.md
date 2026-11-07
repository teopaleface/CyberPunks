# Backend operațional

Contract implementat în acest task. Nu se modifică API-ul vechi sau serverele pornite.

- Router: `cyberpunks.operations.router.router`, prefix `/api/operations`.
- Identitate: `cyberpunks.operations.models.Actor`; dependență comună `cyberpunks.operations.auth.require_actor`, alias `get_actor`.
- Erori de domeniu: `OperationError(status_code, code, message)`, mesaj sigur în engleză.
- Serviciu: `OperationsService.context/prepare/confirm/command`, fabrică `get_service()`.
- Date izolate: `DAYBREAK_OPERATIONS_OUTPUTS`, implicit `outputs/operations-runtime/data`. SQLite: `DAYBREAK_OPERATIONS_DB`, implicit `outputs/operations/operations.sqlite3`.
- Organizația sintetică provisionată: **`daybreak-demo`**. Punct: **`CONN-DEMO-001`**. Clientul primește `connection_ids: ["CONN-DEMO-001"]`. Tehnicianul primește echipa din `service.demo_bindings()` sau `GET /api/operations/demo-bindings`, apel doar server-la-server ca dispecer. Dispecerul primește `permissions: ["approve_plan", "review_work_item", "create_case"]`.
- `demo_bindings()` alege determinist o oprire atribuită unui post real din planul complet, preferând C atribuit, apoi contor A atribuit, cu predicție pentru același contor. Nu se folosesc ID-uri de post presupuse. Asocierea sintetică rămâne fixă după provisionare; replanificarea nu schimbă punctul clientului.
- Date acțiuni: `create_case: {connection_id,symptom,symptom_type?:voltage|meter|outage|other}`; `record_verdict: {work_item_id,outcome:confirmed|not_found|other_problem|no_access,case_id?}`; `review_work_item: {work_item_id,decision:approve|reject|defer,note?}`; `approve_plan: {plan_id,crew_id?,note?}`; `set_availability: {case_id,start,end}` cu date ISO și fus; `request_human: {case_id?|connection_id?,reason,priority?:normal|urgent}`. Toate acceptă `idempotency_key?`, `case_version?`, `plan_version?`.
- Serverul fixează automat versiunile curente în propunere. Parametrii de identitate nu se acceptă în date.

## Persistență și confirmare

SQLite păstrează `connections`, `cases`, `proposals`, `commands`, `events`. Propunerea expiră după zece minute și este legată de utilizator, întreaga apartenență verificată, scenariu, versiunea planului și versiunile cazurilor afectate. Identitatea este verificată din nou înainte de confirmare și de recuperarea comenzii. Un alt utilizator nu poate confirma propunerea și nu poate citi comanda emitentului.

Propunerile neconfirmate nu schimbă cazuri, planul, etichetele sau jurnalul deciziilor. Parametrii necunoscuți, inclusiv roluri sau identități strecurate în date, sunt refuzați. Refuzul unui obiect din alt domeniu produce 404, fără conținut privat. Organizațiile și scenariile neprovisionate nu primesc planul global.

Aceeași confirmare întoarce aceeași comandă. `data.idempotency_key` este opțional; reutilizarea cheii cu altă cerere produce conflict. Sesizările active identice pe același punct și tip de simptom sunt deduplicate, inclusiv cu o cheie nouă. O propunere fără cheie identică se reutilizează cât este valabilă și înainte de confirmare.

Versiunea planului este hash-ul planului și al intrărilor/deciziilor/aprobărilor/etichetelor sale. O aprobare cere permisiunea explicită `approve_plan`; revizuirea cere `review_work_item`. Tehnicianul poate constata doar lucrările aflate în traseul curent al echipei sale. Aprobarea integrală și aprobarea listei unei echipe apelează funcțiile reale ale planificatorului. Revizuirea aplică decizia și recalculează efectiv planul, inclusiv PDF-urile. Verdictul apelează funcția existentă și produce etichetă legată de predicție. `no_access` și `other_problem` au etichetă `null`. `confirmed` nu confirmă reparația și nu închide cazul.

Efectele pe fișiere se calculează într-un director privat al comenzii, sub directorul bazei SQLite. Manifestul rezultat este salvat înainte de publicare. Fiecare fișier are hash anterior și rezultat; ștergerile au rezultat `null`. Publicarea repetată folosește manifestul și nu reapelază planificatorul. Intrările nemodificate sunt verificate din nou la reconciliere. Ștergerea unui ordin de lucru vechi este reluată în siguranță, la fel ca scrierile.

O întrerupere întoarce comanda cu `status: reconciling`, fără rezultat de succes. Interfața recuperează prin `GET /commands/{command_id}` sau repetă confirmarea aceleiași propuneri. Până la reconciliere, altă confirmare primește conflict. Schimbarea cazului, evenimentul și finalizarea comenzii împart aceeași tranzacție SQLite. Fișierele planificatorului nu împart tranzacția cu SQLite. Scrierile noului runtime trebuie să treacă exclusiv prin operații, iar vechile POST-uri trebuie blocate de runtime. API-ul vechi poate rămâne pornit, folosind propriile date.

O cerere de om se salvează în coada comună `context.human_requests`. Nu trimite mesaj sau apel. Disponibilitatea este `requested`, fără programare confirmată. Următoarea oprire apare tehnicianului numai când planul sau lista sa are aprobare valabilă.

## Date și proiecții

Contextul clientului exclude lucrările brute, traseele, motivele interne și scorurile de fraudă. El primește propriile cazuri și evaluarea compatibilă cu simptomul. Evaluarea C este legată exact de postul provisionat, fără alegerea unui vecin sau a unui contor arbitrar. Pentru simptome fără evaluare compatibilă, date lipsă, abținere sau versiune incompletă, răspunsul are `status: needs_data` și `score: null`. Evaluarea păstrează ID-ul predicției, modelul, versiunea, activul, ziua și sursa. Ziua istorică este explicită; nu este o diagnoză a rețelei din momentul conversației.

Contextul tehnicianului include numai traseul și lucrările echipei curente. Dispecerul vede scenariul provisionat al organizației sale. Apartenențele sintetice nu sunt un registru real de clienți PPC. Provizionarea nu acceptă adrese libere ca dovadă de proprietate și nu se schimbă la replanificare.

## Verificare locală

`uv run pytest tests/operations` folosește toate intrările rulării locale complete, generează un plan separat prin planificatorul real și copiază acea stare pentru fiecare probă. Nu folosește mostrele din `data/samples` sau `contracts/fixtures`. Pentru o altă rulare completă: `DAYBREAK_OPERATIONS_TEST_DATA=/cale/absoluta/data uv run pytest tests/operations`.

Probele verifică API-ul public operațional și serviciul: autentificarea înainte de parsarea identității, roluri și organizații, izolarea clientului și echipei, confirmare separată, stare comună în trei roluri și două instanțe de serviciu, deduplicare, expirare, schimbare de apartenență, versiuni concurente, aprobarea reală, revizuirea cu recalculare, eliminarea PDF-urilor vechi, constatări, reluare după publicare parțială, recuperare după pierderea răspunsului, sursă demo doar citibilă și proveniența predicției. Aceste probe nu verifică vocea, browserul sau servicii externe.


## Corecția legăturii caz-evaluare-lucrare

Implementat: asocierea nouă preferă un C atribuit, apoi un contor A atribuit. Pe rularea completă din integrare nu există C atribuit, astfel povestea demonstrabilă pe trei roluri folosește simptomul `meter` și contorul A ales determinist. Simptomul `voltage` folosește exclusiv C la postul autorizat; dacă C nu este atribuit, cazul nu apare arbitrar pe o lucrare A a tehnicianului. `assessment.work_item_id` și `case.work_item_id` sunt ID-ul exact al evaluării compatibile. Lipsa unei evaluări lasă `case.work_item_id: null`. Un verdict A nu actualizează un caz C de la același post.

Asocierile deja provisionate rămân neschimbate. Pentru noua logică se folosește o bază SQLite nouă și conturi sintetice noi, fără rescrierea celor existente. `demo_bindings()` poate fi apelat pe noua stare pentru ID-urile actuale.

Integrarea conversației trebuie să facă o proiecție autorizată după selecție și să păstreze un rezumat al celor 689 de lucrări. Contextul brut complet pentru dispecer depășește 100 KB; o limită de 100 KB fără această proiecție ar bloca conversația dispecerului. Formularul de disponibilitate trebuie să trimită ora ISO cu fusul dispozitivului, nu valoarea brută `datetime-local`.


Evaluările salvate care nu mai corespund predicției curente apar ca `stale`, fără probabilitate curentă. O constatare pe un caz legat de o predicție înlocuită este refuzată cu 409 și cere reevaluare umană, în loc să confirme predicția veche printr-o lucrare nouă.

## Rezultatul verificării acestui task

Pe copia completă a rulării izolate `20261107-225356-433121`, cu 689 de lucrări valide, comanda `DAYBREAK_OPERATIONS_TEST_DATA=/Users/teo/Projects/CyberPunks/outputs/operations-runtime/runs/20261107-225356-433121/data uv run pytest tests/operations tests/runtime -x` a trecut: 32 de probe, dintre care 28 operaționale și patru de autorizare a runtime-ului. Ruff, verificarea formatării și compilarea Python au trecut. Avertismentele rămase provin din Starlette/httpx și SWIG. Nu s-a făcut commit, staging, publicare, trimitere externă sau modificare a conturilor/datei operaționale folosite de integrare. Testele au scris numai în directoarele temporare proprii.
