# Conversație, voce și WhatsApp

Starea integrată din 8 noiembrie 2026: trei conturi locale, Codex pe abonamentul existent, trei agenți ElevenLabs privați și transport direct Meta pentru WhatsApp. Două răspunsuri text reale au fost livrate și citite. O notă vocală reală prin Meta rămâne neverificată, deoarece Teo nu poate înregistra momentan. Pornire și limite: [RUNBOOK.md](RUNBOOK.md).

## Contractul conversației

Routerul `cyberpunks.channels.router.router` oferă `/api/conversation` în API-ul privat. Identitatea vine exclusiv din sesiunea verificată de gateway-ul Next și din tokenul intern al serviciului. Rolul, echipa sau drepturile dintr-un mesaj ori din corpul cererii nu conferă acces.

- POST `/chat` primește message, history, scenario și selection opțional cu connection_id, work_item_id sau case_id. Istoricul are cel mult 12 mesaje de 4.000 caractere; ultimele opt ajung la model.
- Rezultatul include reply, provider, language, provenance și o eventuală proposal. `provenance.write_executed` rămâne false. Serviciul conversației pregătește propuneri și nu confirmă operații.
- POST `/voice-session` verifică domeniul contului și emite o acreditare temporară pentru agentul privat al rolului. SDK-ul browser primește conversationToken cu connectionType=webrtc.
- Unealta client daybreak_turn folosește aceeași conversație autentificată. Agentul vocal așteaptă rezultatul verificat și rostește reply. Propunerea apare în aplicație și cere Confirm.

Acțiunile sunt create_case, record_verdict, review_work_item, approve_plan, set_availability și request_human. Backendul verifică obiectele, permisiunile și versiunile. O constatare confirmed confirmă problema observată, fără a declara reparația. no_access nu devine etichetă negativă de antrenare.

## Codex și modelele locale

Codex CLI 0.167.0 folosește autentificarea ChatGPT existentă. Nu cere o cheie OpenAI nouă. Nu există trecere automată la un API plătit separat. Modelul conversațional formulează intenții; estimările tehnice și planul aparțin modelelor locale ale echipei.

Fiecare turn pornește prin argv, fără shell intermediar, cu promptul în stdin și director temporar gol, în afara repo-ului. Autentificarea existentă este copiată într-un director temporar privat și eliminată la încheiere. Mediul procesului nu moștenește cheile ElevenLabs, Meta, tokenul intern sau parolele conturilor.

CLI folosește ignore-user-config, ignore-rules, ephemeral, sandbox read-only și schema JSON pentru intenție. Shell, patch, MCP, aplicații, pluginuri, hooks, browser, imagini, căutare, memorie și subagenți sunt dezactivate explicit. Un eveniment de unealtă neașteptat invalidează răspunsul. Există limite pentru durata și volumul procesului.

Contextul este citit din sursa completă, filtrată pentru rol. Dispecerul primește totaluri calculate pe toate lucrările, indexul de identificatori și detalii limitate explicit. Pentru explicații sau selecții concrete sunt incluse caracteristicile și dovezile obiectelor autorizate. Selecția nu acordă drepturi și nu transformă un fragment al cozii în totalul ei.

Citările modelului sunt pointeri RFC6901 și valori JSON comparate exact cu sursa. Indicii negativi sau necanonici ai listelor sunt respinși. Numerele scrise cu cifre și identificatorii recunoscuți sunt verificați față de dovezi. Verificarea nu este o garanție semantică pentru orice reformulare liberă. Afirmațiile despre starea unui caz sunt înlocuite cu texte controlate de server; întrebările despre plan rămân distincte. Rezultatele constatării sunt expuse clientului fără identificatorii interni ai verdictului.

## ElevenLabs

Trei agenți noi privați, câte unul pentru client, tehnician și dispecer, sunt salvați în configurația locală nonsecretă. Scriptul păstrează fiecare identificator imediat după creare și nu repetă orbește o creare cu rezultat necunoscut.

```sh
uv run python scripts/daybreak_channels.py preflight
uv run python scripts/daybreak_channels.py provision
uv run python scripts/daybreak_channels.py verify
```

Verificarea live recitește setările și emite tokenuri WebRTC temporare. Configurațiile cer autentificare privată, numai unealta client daybreak_turn, maximum 180 secunde pe sesiune, o conversație simultană pe agent și zece pe zi, fără burst. Înregistrarea audio este dezactivată; retenția cerută este o zi, cu ștergerea transcriptului și datelor personale activată. Valorile cerute sunt verificate prin GET.

Două probe au parcurs ASR, agentul, unealta client, Codex și audio reale. Proba finală a păstrat textul API identic, cu 15,44 secunde până la primul audio după întrebare. Microfonul și difuzorul fizic nu sunt testate; pronunția exactă rămâne neconfirmată. [Raportul și fișierele exacte](VOICE-QA.md) separă probele reale de simulări. Nu există dovadă pentru ținta p95 sub trei secunde.

## WhatsApp

Integrarea folosește direct Meta Graph, distinct de importul nativ WhatsApp ElevenLabs. Un singur expeditor verificat este asociat tehnicianului sintetic. Asocierea privată stabilește identitatea și opțiunea audio; mesajul sau modelul nu pot alege alt rol, destinatar ori număr.

Intrarea publică este exclusiv GET și POST `/api/conversation/whatsapp/webhook`, prin aplicația `cyberpunks.webhook_runtime`. Workspace-ul, consola, conturile și documentația API nu sunt expuse prin tunel. Verificarea inițială folosește tokenul privat; evenimentele cer HMAC SHA-256 pe corpul brut cu App Secret Meta. Numărul destinație și expeditorul sunt verificate înaintea acceptării.

POST salvează intrarea în SQLite înaintea confirmării HTTP și nu așteaptă Codex, transcrierea sau trimiterea. Un singur proces separat, cu lock exclusiv, citește coada durabilă. După restart recuperează munca întreruptă; un POST cu rezultat necunoscut rămâne pentru reconciliere și nu este retrimis automat.

Textul și notele vocale folosesc aceeași conversație. Media se descarcă numai prin identificatorul Meta, cu domenii, tipuri și dimensiuni limitate, fără redirecționări arbitrare. Transcrierea și sinteza folosesc ElevenLabs. Pentru nota vocală, răspunsul text verificat este păstrat înaintea TTS. Opțiunea audio activată pentru expeditorul verificat permite un răspuns OGG/Opus cu audio.voice=true. Eșecul TTS, conversiei sau uploadului păstrează textul, fără repetarea Codex ori duplicarea trimiterii.

Registrul de ieșire păstrează separat părțile text/audio. failed, delivered și read primite din callback nu sunt șterse de un răspuns HTTP ulterior. Citirea statusurilor și alegerea stării cozii sunt în aceeași tranzacție, coordonată cu callbackul. Un callback care rezolvă textul după timeout permite reluarea părții audio încă netrimise, inclusiv după restart; textul nu se trimite din nou. Un rezultat unknown nerezolvat rămâne blocat pentru reconciliere.

După ultima dintre cele trei încercări limitate, o eroare conversațională sau de verificare poate produce un singur mesaj controlat RO/EN: nu pot verifica acum răspunsul, încearcă din nou sau consultă aplicația. Rezultatul este marcat server-fallback, fără propunere, TTS sau acțiune. Nu expune textul respins ori eroarea furnizorului. Identitatea, domeniul, fereastra de răspuns și flagurile sunt reverificate înainte de trimitere. Erorile de autorizare rămân fără răspuns; un timeout al trimiterii nu este reîncercat orbește.

## Confirmarea propunerilor WhatsApp

O propunere nu este o comandă executată. Contextul autentificat include cel mult zece propuneri proprii, încă valide, în pending_proposals. Draft requests și Open din aplicație recitesc obiectul exact prin GET `/api/operations/proposals/{UUID}`. Emitentul, apartenența, permisiunile, expirarea și versiunile sunt reverificate. Propunerile străine, expirate, confirmate sau depășite sunt refuzate.

Dacă administratorul configurează DAYBREAK_PUBLIC_APP_ORIGIN ca origine HTTPS verificată, mesajul oferă `/workspace?proposal=UUID`. Identificatorul se păstrează prin autentificare; nu există destinație externă liberă sau token de confirmare. Fără origine publică, propunerea se găsește în aplicația locală din Draft requests. Numai Confirm execută operația.

## Configurare și verificare

Fișierele private ignorate sunt sub outputs/runtime, cu permisiuni 0600: channels.env, meta-whatsapp.env și whatsapp-bindings.json. Cheile, tokenurile, parolele, cookie-urile și expeditorii personali nu intră în repo, prompturi sau rapoarte publice. channels.json păstrează identificatorii agenților, fără chei.

Meta cere DAYBREAK_WHATSAPP_ENABLED=1 și DAYBREAK_WHATSAPP_SEND_ENABLED=1 pentru procesare și răspuns. Scriptul de configurare verifică aplicația dedicată, păstrează callbackurile străine și activează răspunsurile numai după recitirea callbackului, câmpurilor și asocierii WABA. Nu trimite mesaje de probă automat.

```sh
uv run python scripts/daybreak_whatsapp_setup.py check
uv run python scripts/daybreak_whatsapp_setup.py serve
uv run python scripts/daybreak_channels.py whatsapp-status
uv run pytest tests/channels
```

Testele folosesc furnizori simulați și o copie completă izolată a datelor, cu minimum 600 de lucrări. Sunt acoperite scope/auth, dovezi, istoric, confirmări separate, TTS indisponibil, conversie/upload, callbackuri în ambele ordini, reluare după restart, lipsa duplicatelor și feedback sigur. Probele reale sunt separate: Codex pe toate cele trei roluri, două sesiuni audio browser și două răspunsuri text Meta livrate/citite. O încercare text intermediară a fost respinsă pentru dovezi; retrimiterea a trecut. Nota vocală Meta reală și hardware-ul audio rămân neverificate.

Surse oficiale: [Codex non-interactive](https://developers.openai.com/codex/noninteractive), [autentificare Codex](https://developers.openai.com/codex/auth), [ElevenLabs client tools](https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools), [autentificare ElevenLabs](https://elevenlabs.io/docs/eleven-agents/customization/authentication), [SDK Meta pentru webhooks](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/webhooks/start/) și [subscriere WABA](https://www.postman.com/meta/whatsapp-business-platform/request/26gui66/subscribe-to-a-waba). Flagurile au fost confruntate cu CLI-ul instalat și configurațiile live.
