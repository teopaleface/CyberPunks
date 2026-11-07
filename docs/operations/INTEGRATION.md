# Integrarea locală a celor trei conturi

Implementare autorizată de Teo după aprobarea planului. Acest contract coordonează domeniile lucrate în paralel. Interfața este în engleză.

## Procese și date

- Procesele deja existente pe 3710 și 8710 rămân neatinse.
- Noul API local folosește 127.0.0.1:8720, modulul cyberpunks.runtime.
- Noua interfață folosește 127.0.0.1:3870, cu API_BASE=http://127.0.0.1:8720/api.
- Fișierul privat de pornire este outputs/runtime/daybreak.env, ignorat de Git, cu permisiuni numai pentru utilizator.
- DAYBREAK_OPERATIONS_OUTPUTS indică un director data într-o rulare nouă din outputs/operations-runtime/runs, o copie completă și proaspătă a datelor scenariului. Predicțiile noi și aprobările demo se fac în această copie, fără modificarea planurilor active ale altor fire.
- DAYBREAK_OPERATIONS_DB indică registrul SQLite separat al demonstrației.
- Backendul operațional folosește Store(outputs=Path(DAYBREAK_OPERATIONS_OUTPUTS)); adaptorul la planificator folosește aceeași rădăcină pentru toate efectele.
- Nu se modifică modelele antrenate, seturile de test sau rapoartele lor de performanță.

## Identitate și cereri

Serverul web verifică sesiunea, originea scrierilor și apartenența din cont. El transmite Bearer DAYBREAK_INTERNAL_TOKEN și antetul X-Daybreak-Actor, cu JSON pentru user_id, role, organization_id, crew_id, connection_ids și permissions. Browserul și LLM-ul nu aleg acest antet.

Rolurile de server sunt customer, technician și dispatcher. Organizația demonstrației este daybreak-demo. Backendul stabilește legăturile sintetice la puncte, posturi și echipe din datele complete și le expune pentru provisionarea locală autorizată.

Orice cale veche care modifică planul folosește aceleași drepturi. Alegerea personală din KV nu este o aprobare operațională.

## Operații

Routerul cyberpunks.operations.router exportă router, cu prefix /api/operations. Serviciul cyberpunks.operations.service exportă get_service și OperationsService cu context(actor, scenario), prepare(actor, action, data, scenario), confirm(actor, proposal_id), command(actor, command_id). Actor este în cyberpunks.operations.models.

- GET /api/operations/context returnează actor, scenario, plan, connections, work_items și cases, toate filtrate.
- POST /api/operations/proposals primește action, data și scenario.
- Acțiunile sunt create_case, record_verdict, review_work_item, approve_plan, set_availability și request_human.
- POST /api/operations/proposals/{id}/confirm execută propunerea confirmată și returnează comanda și rezultatul.
- GET /api/operations/commands/{id} permite recuperarea rezultatului după întrerupere.

Modificările suplimentare ale contractului se scriu aici înainte de integrare. Nicio acțiune pregătită de conversație nu se confirmă automat.

## Conversație

Routerul cyberpunks.channels.router exportă router cu prefix /api/conversation.

- POST /api/conversation/chat primește message, history cu role/content, scenario și selecția opțională. Returnează reply, provider și o eventuală proposal.
- POST /api/conversation/voice-session creează o sesiune temporară a agentului ElevenLabs pentru rolul real.
- Funcția din browser daybreak_turn(message) folosește aceeași rută de chat. Agentul vocal așteaptă rezultatul și rostește răspunsul verificat.
- Configurația locală nonsecretă a canalelor este outputs/runtime/channels.json. Cheile nu intră în JSON-ul de răspuns sau în Git.

## Dovezi cerute

Testele principale sunt la API-ul operațional și în trei sesiuni independente de browser. Se testează separat Codex real, ElevenLabs real și vocea cu microfon. Probele simulate se etichetează și nu înlocuiesc serviciul real. WhatsApp rămâne inactiv până la verificarea numărului, identității și integrării; nu se trimit mesaje sau apeluri către alte persoane în test.

## Protecția tranziției

Noul runtime refuză scrierile prin vechile rute API, care nu au registrul comun de comenzi. Citirile consolei rămân disponibile serverului autentificat. Schimbările operaționale trec prin pregătirea și confirmarea propunerilor din workspace. Procesul API vechi rămâne neschimbat.
