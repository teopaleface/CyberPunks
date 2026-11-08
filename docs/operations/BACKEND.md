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

SQLite păstrează `connections`, `cases`, `proposals`, `commands`, `events` și `command_recoveries`. Propunerea expiră după zece minute și este legată de utilizator, întreaga apartenență verificată, scenariu, versiunea planului și versiunile cazurilor afectate. Identitatea este verificată din nou înainte de confirmare și de recuperarea comenzii. Un alt utilizator nu poate confirma propunerea. Comanda poate fi citită de emitentul cu apartenență neschimbată sau de dispecerul autorizat explicit pentru recuperare, în aceeași organizație și scenariu.

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

## Contractul recuperării după schimbarea apartenenței

Permisiune nouă explicită pentru dispecer: `recover_commands`. Nu este dedusă din rol și nu se acordă vechiului tehnician. Provizionarea pentru conturi noi o include; conturile existente trebuie autorizate separat de serverul care gestionează apartenențele.

`context.pending_commands` include comenzile proprii și, pentru dispecerul cu această permisiune, comenzile în așteptare din aceeași organizație și scenariu. Fiecare rând include `command_id`, `proposal_id`, `action`, `status`, `created_at`, `can_recover`, `recovery_action`. Valorile recuperării sunt `retrieve`, `cancel`, `manual_review`, `requires_dispatcher`.

`GET /api/operations/commands/{id}` recuperează pentru dispecer numai efectul deja publicat, integral sau parțial, pe baza manifestului existent. Nu recalculează o acțiune și nu publică un rezultat doar pregătit după revocare. Dacă nu există efect publicat, întoarce comanda încă în așteptare și `recovery: {effect_status,allowed_decisions:["cancel"],requires_confirmation:true}`.

Anularea explicită, numai fără efect publicat: `POST /api/operations/commands/{id}/recover`, corp `{decision:"cancel",reason:"..."}`. Este permisă numai dispecerului cu `recover_commands`; marchează comanda `cancelled`, fără executarea acțiunii. Confirmarea inițială rămâne imuabilă. Un manifest corupt/conflictual cere verificare manuală și nu poate fi anulat prin această cale.


Recuperările au audit durabil în `command_recoveries`, cu `confirmed_by` și `reconciled_by` separate. Evenimentul rezultat păstrează `actor_id` și rolul emitentului inițial, plus dispecerul și ID-ul recuperării. Comenzile confirmate înaintea acestei corecții se pot recupera din identitatea emitentului păstrată deja în SQLite; rolul istoric neînregistrat apare `null`, fără a inventa apartenențe sau a le reinstaura. Propunerea și parametrii ei nu sunt rescriși.

Un simplu GET al unei comenzi fără efect publicat nu o anulează și nu o execută. Pentru butonul de recuperare, UI folosește `pending_commands[].recovery_action`: `retrieve` apelează GET-ul existent; `cancel` arată motivul și confirmarea explicită, apoi apelează POST-ul nou; `manual_review` și `requires_dispatcher` nu execută nimic. Comenzile terminale se recitesc idempotent și nu adaugă recuperări duplicate. După finalizare sau anulare, `pending_commands` nu mai include comanda și o operație independentă poate fi confirmată.

Verificarea corecției: suita completă `uv run pytest tests/operations tests/runtime -x` a trecut 40 de probe pe o copie completă a rulării izolate curente. Apoi `uv run pytest tests/operations/test_recovery.py -x` a trecut opt probe, inclusiv două probe suplimentare pentru comenzile vechi fără rol salvat. Sunt acoperite publicarea integrală și parțială, revocarea apartenenței, descoperirea după restart, refuzurile pentru alte organizații/tehnicieni/dispeceri fără permisiune, lipsa reapelării planificatorului, auditul separat, anularea explicită fără efect, refuzul adoptării unei propuneri neconfirmate și deblocarea operației următoare. Nu au fost modificate conturi sau procesele live de integrare.

## Deschiderea unei propuneri dintr-un link autentificat

Contract implementat: `GET /api/operations/proposals/{proposal_id}`, prin `OperationsService.proposal(actor, proposal_id)`. Răspunsul 200 este exact propunerea publică întoarsă de prepare: `proposal_id`, `action`, `data`, `scenario`, `plan_version`, `created_at`, `expires_at`, `requires_confirmation`, `summary`. Nu include `actor_signature`, rânduri interne sau identitatea salvată a actorului.

Ruta este doar de citire. Nu pregătește din nou, nu confirmă, nu anulează și nu recuperează comenzi. Numai emitentul original, în aceeași organizație, cu apartenența și permisiunile neschimbate și obiectele încă în domeniul său, poate citi propunerea. Dispecerul cu `recover_commands` nu poate deschide propunerea altui emitent. Identificatorul din link nu acordă drepturi. Antetele de serviciu și actorul verificat se transmit la fel ca la prepare/confirm.

Erori: 401 fără autentificarea de serviciu; 404 pentru alt emitent, organizație sau obiect ieșit din domeniu; 403 `membership_changed` la revocare/schimbare de rol, echipă sau permisiuni; 409 `proposal_expired` după expirare; 409 `proposal_consumed` după orice confirmare anterioară, inclusiv comandă în reconciliere sau anulată ulterior; 409 `stale_plan`/`stale_case` dacă versiunile s-au schimbat. Propunerile expirate sau consumate nu sunt întoarse ca propuneri confirmabile. Citirea nu execută confirmarea sau recuperarea și nu schimbă regulile existente ale acestor acțiuni.

Web poate folosi `/workspace?proposal=<id>` după autentificare, apoi acest GET. Confirmarea rămâne exclusiv butonul care apelează POST-ul existent `/proposals/{id}/confirm`. Pentru rularea locală fără URL public, `context.pending_proposals` permite găsirea ID-ului după autentificare, conform contractului de mai jos.

Verificarea noului GET: `uv run pytest tests/operations/test_proposal_read.py -x` a trecut 14 probe pe datele complete copiate izolat. Sunt verificate egalitatea cu propunerea originală după restart, lipsa oricărei executări/scrieri operaționale, alt emitent/organizație/dispecer, promovarea sau revocarea apartenenței, expirarea, confirmarea deja executată/în reconciliere/anulată, schimbarea planului și autentificarea de serviciu. Corecția proiecției verdictului către client și recuperarea comenzilor rămân păstrate.

Suita extinsă `uv run pytest tests/operations tests/runtime -x` a trecut 54 de probe înainte de un eșec din domeniul runtime/channels: `tests/runtime/test_runtime_auth.py::test_whatsapp_handshake_uses_native_verification_not_app_bearer` a primit 403, cu 200 așteptat. Acest task nu modifică acel test, runtime-ul sau configurarea WhatsApp. Nu s-au modificat conturi, baza runtime, configurații sau procese. Fără staging/commit.

Regresia operațională verificată separat după acel eșec: `uv run pytest tests/operations -x` a trecut toate cele 50 de probe. Ruff, formatarea și `git diff --check` trec.

## Descoperirea propunerilor fără link public

Contract implementat pentru web: `GET /api/operations/context` include `pending_proposals`, o listă cu cel mult zece propuneri proprii, cele mai recente primele. Fiecare element are exact `proposal_id`, `action`, `summary`, `scenario`, `created_at`, `expires_at`, `requires_confirmation: true`. Butonul Open poate citi `GET /api/operations/proposals/{proposal_id}` după autentificare; apoi folosește confirmarea explicită existentă. Nu este necesar un URL public sau publicarea site-ului.

Lista include numai emitentul curent, aceeași organizație/scenariu și semnătura apartenenței actuale. Se verifică din nou rolul, permisiunile, expirarea, versiunile planului/cazurilor și domeniul obiectelor. Propunerile confirmate, expirate, vechi sau revocate sunt excluse. Nici dispecerul cu `recover_commands` nu vede propunerile altui utilizator. Citirea nu execută, nu confirmă, nu anulează și nu recuperează nimic. Se verifică o fereastră mărginită de maximum 50 dintre cele mai recente propuneri neconfirmate cu apartenență corespunzătoare, pentru a întoarce maximum zece valide. Nu se expun datele interne sau parametrii compleți ai propunerilor în listă. GET-ul individual și regulile sale rămân neschimbate.

Verificarea descoperirii locale: `uv run pytest tests/operations/test_proposal_read.py -x` a trecut 20 de probe, inclusiv șase noi pentru descoperire după restart fără efecte, izolarea emitentului/apartenenței, excluderea propunerilor expirate sau confirmate, versiunile cazului/planului și limita/ordinea celor zece propuneri. `uv run pytest tests/operations -x` a trecut toate cele 56 de probe. Ruff, formatarea și `git diff --check` trec. În acest follow-up au fost modificate numai `service.py`, `test_proposal_read.py` și acest document. Verdictul public pentru client și recuperarea comenzilor sunt păstrate. Nu au fost modificate conturi, runtime, configurații sau indexul Git.
