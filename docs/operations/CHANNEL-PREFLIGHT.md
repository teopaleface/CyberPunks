# Preflight canale

Acesta este raportul etapei inițiale din 7 noiembrie. Activarea ulterioară directă prin Meta, probele text reale și limitele actuale sunt în [RUNBOOK.md](RUNBOOK.md). Mențiunile de mai jos despre WhatsApp inactiv sau lipsa mesajelor descriu momentul preflightului. Cele zero numere conectate se referă la integrarea nativă ElevenLabs.

Starea finală verificată local la 7 noiembrie 2026: exact trei agenți Daybreak noi și privați sunt creați, verificați prin GET și primesc tokenuri WebRTC temporare. Contul are exact zero numere WhatsApp conectate. Codul este gata pentru reîncărcarea API-ului de către root.

## Dovezi ElevenLabs

- Cheia existentă reală a fost găsită în /Users/teo/projects/ailabs/.env.local și păstrată numai în outputs/runtime/channels.env, permisiuni 0600, ignorat de Git. Fișierul privat are prioritate față de mediul procesului, care conținea un ID de cheie neutilizabil.
- Preflightul inițial cu ID a fost respins HTTP 400 api_key_id_used_as_api_key. Cheia reală a fost respinsă inițial HTTP 403 ip_not_allowed. Root a remediat restricția IP cu autorizarea explicită a utilizatorului. Acest task nu a schimbat lista IP, permisiuni sau facturare.
- După remediere: GET /v1/user/subscription HTTP 200, vocile disponibile citite, GET /v1/convai/whatsapp-accounts HTTP 200 cu forma {items: []}. Numărul verificat de numere conectate este exact 0; nu o presupunere dintr-o eroare.
- Exact trei agenți noi, pentru customer, technician și dispatcher. ID-urile nonsecrete sunt în outputs/runtime/channels.json. Provisionarea salvează fiecare ID imediat și îl reutilizează la reluare. Niciun agent vechi nu a fost modificat.
- GET real pentru fiecare confirmă autentificare privată, o singură unealtă client daybreak_turn cu expects_response=true, 180 secunde/sesiune, o sesiune simultană/agent, maximum 10/zi și bursting=false.
- GET confirmă record_voice=false, retention_days=1, delete_audio=true și delete_transcript_and_pii=true.
- Pentru fiecare rol s-a emis un token temporar WebRTC, apoi verificarea completă a fost repetată cu succes. Niciun token sau cheie nu a fost afișat ori pus în Git.
- API-ul contului a respins English + Flash v2.5 cu HTTP 400 input_invalid înainte de creare. Agenții creați au baza ro, Flash v2.5 multilingv, salut în engleză și instrucțiune de rostire exactă a răspunsului RO/EN al serviciului. Pronunția și comutarea între limbi trebuie verificate cu audio real.

## Dovezi Codex și teste

- Codex CLI 0.167.0 este conectat prin ChatGPT. Nu se folosește cheie OpenAI și nu există trecere ascunsă la API plătit.
- Turnuri reale verificate: salut în română, dispecer cu 689 lucrări și 25 human_review, cerere adversarială de citire a fișierelor și schimbare a rolului refuzată cu action=null și fără unelte.
- După răspunsul implicit de 1-2 propoziții, maximum 40 cuvinte, și proiecția redusă: un turn real al dispecerului a durat 8,40 secunde, 13 cuvinte, 26.179 input tokens, proiecție 37.164 bytes. Dovezile au fost verificate și write_executed=false. Aceste probe nu sunt p95.
- La tehnician, o probă a fost respinsă corect pentru pointer de dovadă inexistent; repetarea reală a întors un răspuns scurt verificat despre următoarea oprire aprobată. Nu se ascund erorile de verificare și nu se substituie răspunsuri simulate.
- `.venv/bin/pytest tests/channels -q`: 60/60 trecute, pe o copie proaspătă a tuturor intrărilor scenariului. Furnizorul simulat din teste este etichetat explicit.
- Sunt acoperite autentificarea înainte de actor, izolarea organizațiilor și obiectelor, propuneri fără confirmare automată, surse/versiuni, conflictul de plan în timpul inferenței, timeout și curățarea procesului izolat, limitele, text/audio WhatsApp, media semnată, deduplicare și reluare după eșec.
- Regresiile P1 la API demonstrează că o stare reală access_blocked citată de model nu poate susține o afirmație falsă de reparație sau închidere. Răspunsul vine din starea controlată de server, în RO/EN. confirmed descrie defectul, fără a dovedi reparația. Istoricul acceptă 12 mesaje a câte 4.000 caractere, ca UI; ultimele opt sunt trimise modelului.
- Ruff, compilarea Python și git diff --check au trecut. Acest task nu a stagiat fișiere și nu a făcut commit, conform coordonării indexului comun.

## Limite care rămân

1. Emiterea tokenului nu este o probă cu microfon și difuzor. Vocea reală în browser și pronunția RO/EN cer verificare separată de root. Ținta vocală p95 sub trei secunde nu este demonstrată.
2. WhatsApp este dezactivat și nu are transport de trimitere. Adaptorul procesează text și note vocale semnate, cu identitate preasociată administrativ, și păstrează răspunsurile local cu outbound_status=not_sent. Notele vocale folosesc STT real când serviciul este disponibil; testele media/STT din suită sunt simulate, nu conversații WhatsApp reale.
3. Lipsesc pentru conectarea reală un număr Business/Meta autorizat, ID-ul acestuia, acces Cloud API la media, secret Meta de semnare, tokenul de verificare webhook, asocierea prevalidată a expeditorului și o adresă HTTPS accesibilă Meta. Nu se importă sau reasociază numere fără autorizare separată. Numărul existent din configurarea demo nu se prezintă ca număr conectat.
4. Niciun apel, email, mesaj WhatsApp sau marcaj de citire nu a fost trimis. Uneltele client ale agenților browser nu înlocuiesc automat adaptorul WhatsApp server-to-server.

## Comenzi și integrare

```sh
.venv/bin/python scripts/daybreak_channels.py preflight
.venv/bin/python scripts/daybreak_channels.py provision
.venv/bin/python scripts/daybreak_channels.py verify
```

Root montează cyberpunks.channels.router.router, prefix /api/conversation, care include /chat, /voice-session și /whatsapp/webhook. Root gestionează excepția exactă de autentificare pentru webhookul Meta; adaptorul verifică semnătura și rămâne dezactivat implicit. SDK-ul browser primește conversation_token și folosește connectionType=webrtc. Specificația completă și lista variabilelor private sunt în CHANNELS.md.

Surse oficiale: https://developers.openai.com/codex/noninteractive , https://developers.openai.com/codex/auth , https://developers.openai.com/codex/sdk , https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools , https://elevenlabs.io/docs/eleven-agents/customization/authentication , https://elevenlabs.io/docs/eleven-agents/whatsapp . Schema live ElevenLabs și schema Codex au fost confruntate cu implementarea.

## Fișiere deținute de acest task

- src/cyberpunks/channels/__init__.py
- src/cyberpunks/channels/models.py
- src/cyberpunks/channels/codex.py
- src/cyberpunks/channels/conversation.py
- src/cyberpunks/channels/limits.py
- src/cyberpunks/channels/elevenlabs.py
- src/cyberpunks/channels/router.py
- src/cyberpunks/channels/whatsapp.py
- tests/channels/conftest.py
- tests/channels/test_api.py
- tests/channels/test_provider.py
- tests/channels/test_elevenlabs.py
- tests/channels/test_whatsapp.py
- scripts/daybreak_channels.py
- docs/operations/CHANNELS.md
- docs/operations/CHANNEL-PREFLIGHT.md

Fișiere runtime ignorate: outputs/runtime/channels.env pentru cheia privată, outputs/runtime/channels.json pentru ID-urile nonsecrete și outputs/runtime/channels/ pentru schemele consultate. Nu s-a modificat outputs/runtime/daybreak.env, runtime.py, api/app.py, jurnalul sau indexul comun.
