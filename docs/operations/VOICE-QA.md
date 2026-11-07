# Probă vocală reală, cu intrare sintetică

## Stare pentru coordonare

Ambele sesiuni autorizate s-au încheiat. A doua a pornit numai după anunțul
explicit al root că API-ul de pe 8720 a fost repornit cu codul curent și că
aplicația de pe 3870 era pregătită. Nu există sesiune activă din această probă.
Bugetul de două sesiuni este consumat; nu se mai pornesc sesiuni.
Starea locală sigură este `/tmp/daybreak-voice-qa/probe-status.json`.

## A doua probă, după restart, rezultat final

Sesiune din 7 noiembrie 2026, ora 23:42:35 București. Traseul real ASR,
coordonator ElevenLabs, unealtă client, Codex prin abonamentul ChatGPT și
audio a funcționat. Textul final al API-ului și textul emis de ElevenLabs sunt
identice literal, inclusiv punctuația:

> Ce caz vrei să verific? Alege-l în aplicație.

Sunt două propoziții, opt cuvinte. Contul are două cazuri sintetice, ambele
`verification_after_visit`, fără un caz selectat. Proveniența reală are
`status_from_server_template=true`; răspunsul cere alegerea cazului și nu
pretinde că vreun caz este reparat sau închis. Proba confirmă această ramură de
clarificare a regulii de statut. Nu verifică vocal fiecare stare individuală.

- Intrarea sintetică, transcrierea ASR ElevenLabs și mesajul uneltei sunt
  identice cu prima întrebare: "Salut! Ce informații vezi despre sesizările mele?"
- Un singur apel `daybreak_turn`, executat prin sesiunea customer reală a
  aplicației Next. `provider=codex-cli-chatgpt`, `authentication=chatgpt`,
  `model=gpt-6.1-sol`, `tools_enabled=false`, `evidence_values_checked=true`.
  API-ul aplică regula de statut după întoarcerea modelului. Textul de mai sus
  este rezultatul final al API-ului, nu o dovadă că modelul a produs singur
  exact acea formulare.
- Chatul real a durat 13,153 s. De la sfârșitul intrării PCM, la trecerea la
  tăcere, până la primul audio al răspunsului au trecut 15,438 s. ASR a venit
  după 1,085 s, iar primul audio după 1,198 s de la rezultatul uneltei.
  Sesiunea de transport a durat 28,593 s. Sunt măsurări individuale, fără p95.
  Ținta sub trei secunde nu este îndeplinită de această probă.
- Nu există dată, număr sau afirmație de statut în răspunsul final. Nu s-a
  observat schimbare materială a vreunui număr sau statut între API și agent.
  Nu s-a aplicat o regulă generală care să transforme diferențele numerice în
  rezultate trecute.
- `proposal=null`, `write_executed=false`, zero cereri de confirmare. Hashurile
  contextului autorizat înainte și după sunt identice, inclusiv plan, cazuri,
  puncte și lucrări. Conturile și asocierile nu au fost modificate de probă.
- ffprobe confirmă intrarea MP3 mono 44,1 kHz de 3,250794 s, intrarea PCM/WAV
  mono 16 kHz/16 biți de 3,250813 s și ieșirea WAV mono PCM signed little
  endian 16 kHz/16 biți de 2,950063 s. Salutul separat are 1,891 s.

Whisper local confirmă integral întrebarea și prima propoziție a răspunsului.
Pentru ultima propoziție, atât prima transcriere în română, cât și reverificarea
cu detectare automată a limbii redau "Alegere în aplicație." în locul textului
furnizorului "Alege-l în aplicație.". Fișierele și ambele transcrieri sunt
păstrate fără corectare. Nu avem o unealtă de ascultare în această sesiune,
deci identitatea acustică a acelei formulări rămâne neconfirmată. Rezultatul
trecut pentru identitatea textului furnizorului nu este un rezultat trecut
pentru fiecare cuvânt auzit.

Prima încercare de reverificare Whisper cu beam 10 a eșuat local cu exit 134
și `GGML_ASSERT([rsets->data count] == 0)` în backendul Metal, după mesajul
`failed to process audio`. Reverificarea a fost executată apoi pe CPU, cu
parametrii standard de căutare, și s-a încheiat. Acest incident local nu a
deschis altă sesiune ElevenLabs și nu a modificat înregistrarea.

Fișierele exacte finale sunt în
`/tmp/daybreak-voice-qa/session-20261107-234235-670362/`:

- `synthetic-user-input.mp3`, intrarea TTS exactă.
- `synthetic-user-input.pcm` și `synthetic-user-input.wav`, intrarea transmisă.
- `agent-greeting.wav`, salutul separat.
- `agent-response.wav`, răspunsul audio real integral.
- `report.json`, textul API, textul agentului, intrarea ASR, proveniență,
  snapshotul stărilor sintetice, timpi, hashuri și metadate.
- `local-whisper-input.txt` și `.json`, transcrierea locală a intrării.
- `local-whisper-response.txt` și `.json`, prima transcriere a răspunsului.
- `local-whisper-response-recheck.txt` și `.json`, reverificarea locală.
- `artifact-manifest.json`, dimensiunile și SHA-256 ale dovezilor.

Pachetul cu toate aceste fișiere este
`/tmp/daybreak-voice-qa/final-session-evidence.zip`.
Nu s-a verificat microfonul, difuzorul fizic sau traseul browser/WebRTC.
Nicio înregistrare nu a fost încărcată pentru transcrierea locală.

## Prima probă, înainte de restart

API-ul încă folosea codul încărcat la 23:10. Root a precizat că ultimele
reguli de statut/reparație și promptul scurt nu erau încă încărcate. Rezultatul
de mai jos dovedește traseul vocal real, nu validarea acestor ultime schimbări.

- Cont sintetic autentificat customer, două sesizări autorizate, un punct asociat,
  fără lucrări interne vizibile.
- Intrare ElevenLabs TTS cu vocea stock existentă, apoi PCM mono 16 kHz/16 biți,
  transmis în pachete de 100 ms, în timp real, urmat de tăcere.
- Întrebarea sintetică și transcrierea ASR reală sunt identice:
  "Salut! Ce informații vezi despre sesizările mele?"
- Agent privat verificat prin GET, conectat prin URL WebSocket semnat păstrat
  exclusiv în memorie. Metadata confirmă PCM 16 kHz la intrare și ieșire.
- Un singur apel real `daybreak_turn`, cu întrebarea integrală. Proba l-a
  executat prin sesiunea HTTP customer în aplicația Next de pe 3870, cu backend
  privat pe 8720. Rezultatul identifică `codex-cli-chatgpt`, autentificare
  `chatgpt`, model `gpt-6.1-sol`, fără unelte Codex și cu dovezi verificate.
- Rezultatul real a fost transmis agentului ca JSON în `client_tool_result`.
  Agentul a produs răspuns text și audio PCM real. Nu s-a sintetizat separat un
  răspuns pregătit pentru a înlocui conversația.
- Fără propunere, `write_executed=false`, zero cereri de confirmare.
  Hashul planului, cazurilor, punctelor și lucrărilor autorizate este identic
  înainte și după conversație. Nu s-au trimis mesaje sau notificări.
- Codex a răspuns în 14,649 s. De la trimiterea ultimului pachet audio de intrare
  la primul audio al răspunsului au trecut 16,937 s. Primul audio a venit la
  0,911 s după întoarcerea rezultatului uneltei. Sesiunea a durat 32,557 s.
  Acestea sunt măsurări ale unei singure probe, fără p95 și fără verificarea
  țintei sub trei secunde. Ultimul pachet conține aproximativ 94 ms de audio.
- Răspunsul nu este identic literal cu cel al uneltei. Agentul a eliminat
  pauza de paragraf și a transformat `8 iulie 2025` în
  `opt iulie două mii douăzeci și cinci`. Celelalte cuvinte sunt identice.
  Raportul marchează corect verificarea de identitate strictă drept eșuată.
  Data verbalizată reprezintă aceeași dată verificată în plan, 2025-07-08;
  această diferență și eliminarea spațiilor de paragraf sunt nemateriale.
  Rezultatul strict rămâne eșuat, distinct de această apreciere semantică.
- Captura finală are 26,85425 s, PCM signed little endian, mono 16 kHz,
  16 biți. Intrarea MP3 are 3,993832 s, mono 44,1 kHz.

Fișierele exacte sunt în
`/tmp/daybreak-voice-qa/session-20261107-233656-591047/`:

- `synthetic-user-input.mp3`, intrarea TTS exactă.
- `synthetic-user-input.pcm`, octeții de intrare trimiși prin WebSocket.
- `synthetic-user-input.wav`, aceeași intrare PCM într-un container WAV.
- `agent-greeting.wav`, salutul real, separat de răspuns.
- `agent-response.wav`, întregul răspuns audio primit după rezultatul uneltei.
- `report.json`, transcriere, mesajul uneltei, răspuns Codex, textul agentului,
  timpi, proveniență și metadate ffprobe. Fără chei, cookies, tokenuri sau URL semnat.
- `local-whisper-input.txt` și `.json`, transcrierea independentă locală a intrării.
- `local-whisper-response.txt` și `.json`, transcrierea independentă locală a ieșirii.

Whisper local, modelul `ggml-large-v3-turbo-q5_0.bin`, confirmă conținutul
întrebării și al răspunsului din fișierele audio. Transcrierea independentă redă
`demo-vara` ca `de Movara`, deci pronunția numelui rămâne incertă. Transcrierea
automată nu înlocuiește ascultarea. Nu s-a ascultat audio pe difuzor și nu s-au
verificat microfonul, WebRTC sau browserul fizic. Fișierele nu au fost încărcate
pentru această verificare locală.

Timpul estimat de la sfârșitul nominal al sunetului de intrare până la primul
audio de ieșire este 16,845 s. Valoarea de 16,937 s de mai sus măsoară de la
trimiterea ultimului pachet. Răspunsul audio a sosit mai repede decât viteza de
redare; captura WAV păstrează toate cele 26,85425 s chiar dacă sesiunea de
transport s-a închis mai devreme decât s-ar fi terminat redarea în timp real.

## Protocol

Proba folosește `scripts/daybreak_voice_probe.py`, maximum o sesiune per
invocare și două sesiuni pentru acest lot. O sesiune se oprește în cel mult
120 s. Nu schimbă agenți cloud și nu confirmă operații.

Surse oficiale verificate:
[Evenimente WebSocket](https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket),
[URL semnat](https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-signed-url).

Nu s-a făcut stage sau commit. Domeniile celorlalți agenți rămân neatinse.
Ruff, compilarea Python și `git diff --check` au trecut pentru fișierele probei.
