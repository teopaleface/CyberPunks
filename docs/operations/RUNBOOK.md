# Cele trei conturi, vocea și WhatsApp

Implementarea locală acoperă clientul, tehnicianul și dispecerul din planul conversațional. Catalogul complet are 80 de cazuri și situații; extensiile P1/P2 din plan nu sunt toate implementate. Interfața este în engleză, iar conversația răspunde în română sau engleză.

## Pornire

```sh
python3 scripts/daybreak_runtime.py check
python3 scripts/daybreak_runtime.py start
# În alt terminal, doar pentru conturile sintetice locale:
python3 scripts/daybreak_runtime.py accounts
```

Aplicația este la `http://127.0.0.1:3870/app`, API-ul privat pe 8720. Procesele vechi de pe 3710 și 8710 sunt separate. Comanda accounts păstrează identificatorii și parolele existente; upgrade-ul verificat al dispecerului sintetic acordă numai recuperarea comenzilor. Nu se folosește prepare --new-run peste o demonstrație activă, deoarece creează alte identități și necesită refacerea asocierilor.

Credențialele celor trei conturi sunt generate și păstrate numai în fișierul privat ignorat `outputs/runtime/daybreak.env`. Nu copiați fișierul în chat, prezentare sau Git. Celelalte configurări private sunt în același director, cu acces numai pentru utilizator. Nu se cere o cheie OpenAI nouă.

Datele operaționale provin dintr-o copie completă izolată, cu 689 de lucrări și rulări reale ale modelelor locale. Identitățile, punctul clientului și sesizările de acceptanță sunt sintetice. Scenariul este istoric, 8 iulie 2025. Nu reprezintă măsurători curente.

## Ce se testează

Clientul pregătește și confirmă o sesizare pentru punctul propriu. Dispecerul vede aceeași sesizare și aprobă intervenția prin planificatorul real. Tehnicianul înregistrează constatarea pentru lucrarea atribuită, iar clientul vede rezultatul constatării și pasul următor. Confirmarea problemei nu declară reparația sau închiderea.

Textul și vocea pregătesc aceleași propuneri. Numai Confirm din aplicația autentificată execută operația. Versiunile schimbate sunt refuzate, repetările păstrează o singură comandă, iar dispecerul autorizat poate recupera sau anula controlat comenzile întrerupte. Contul și obiectele sunt verificate pe server.

Codex CLI folosește autentificarea ChatGPT existentă. Modelul de conversație formulează intenții; predicțiile tehnice și planul provin din modelele locale ale echipei. Procesul conversației nu are unelte de shell, acces la secrete, confirmări automate sau publicare.

```sh
python3 scripts/daybreak_acceptance.py --chat
uv run pytest tests/operations tests/channels tests/runtime
```

Acceptanța cu --chat folosește serviciul Codex real și scrie numai sesizări sintetice etichetate în copia izolată. Raportul fără parole și cookie-uri este `outputs/runtime/acceptance.json`. Testele automate folosesc și furnizori simulați, etichetați; acestea nu înlocuiesc verificarea serviciilor externe.

Verificarea finală a integrării a trecut 170 de teste Python pentru operațiuni, canale și runtime, plus 170 de teste web cu probele gateway locale activate. Typecheck, lint și buildurile izolate au trecut. Verificarea în Helium a acoperit trei sesiuni la 1440×1100 și 390×844, fără alerte sau depășiri orizontale. Proba separată a propunerii a păstrat legătura prin login și a deschis cardul fără să creeze cazul.

## Voce în browser

Trei agenți ElevenLabs privați, unul pentru fiecare rol, sunt creați și verificați. Utilizatorul acceptă trimiterea conversației demonstrative la ElevenLabs și pornește Talk to Daybreak. Agentul așteaptă rezultatul verificat al conversației înainte să îl rostească.

Două probe au parcurs serviciile reale ASR, agent, unealta din client, Codex și audio. Proba finală a păstrat identic textul întors de API. Au fost măsurate 13,15 secunde pentru conversație și 15,44 secunde de la sfârșitul întrebării până la primul audio. Această pauză rămâne o limită. Microfonul și difuzorul fizic nu au fost verificate. Detalii și fișiere exacte: [VOICE-QA.md](VOICE-QA.md).

## WhatsApp

Numărul de test Meta ales de Teo este `+1 555 154 5755`. Integrarea folosește direct API-ul Meta și ElevenLabs pentru transcriere și sinteză; numărul nu este importat în integrarea WhatsApp nativă ElevenLabs. Un singur expeditor verificat este asociat contului sintetic de tehnician. Nu se acceptă schimbarea rolului prin conversație.

Callbackul HTTPS și asocierea aplicației Meta au fost salvate și recitite prin API. Un mesaj real primit de la Teo a produs un răspuns Codex, iar Meta a confirmat livrarea lui. Mesajele sunt salvate înaintea confirmării HTTP și procesate separat. Un rezultat de trimitere necunoscut nu este retrimis automat.

Notele vocale sunt implementate, cu răspuns text și opțional OGG/Opus pentru expeditorul care a cerut audio. Un eșec audio păstrează textul. Teo nu poate înregistra momentan, deci primirea unei note vocale reale prin Meta rămâne neverificată. Probele vocale reale din browser și testele simulate ale transportului sunt dovezi separate.

```sh
uv run python scripts/daybreak_whatsapp_setup.py check
uv run python scripts/daybreak_whatsapp_setup.py serve
# În alt terminal:
cloudflared tunnel --url http://127.0.0.1:8721 --no-autoupdate
# Conectarea explicită, după obținerea URL-ului HTTPS temporar:
uv run python scripts/daybreak_whatsapp_setup.py connect --callback https://GAZDA.trycloudflare.com/api/conversation/whatsapp/webhook
uv run python scripts/daybreak_channels.py whatsapp-status
```

Serve pornește numai intrarea Meta pe 8721 și un singur proces pentru răspunsuri. Nu expune workspace-ul, conturile, consola sau documentația API. Nu porniți încă un proces de răspuns peste acesta. Endpointul public acceptă numai verificarea Meta și evenimente cu semnătură validă, expeditor și număr autorizate.

Tunelul este temporar și depinde de procesele locale. URL-ul se poate schimba după restart, iar tokenul temporar Meta poate expira. Nu este o publicare permanentă. Nu este configurată o adresă publică a site-ului; propunerile se găsesc în Draft requests din aplicația locală autentificată, iar Open recitește obiectul propriu fără să îl confirme. Pentru o viitoare adresă publică verificată, mesajul include identificatorul propunerii în legătura către aplicație, păstrată și prin login.

Configurarea callbackului folosește [API-ul oficial Meta pentru subscriptions](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/application.py) și [subscrierea WABA documentată de Meta](https://www.postman.com/meta/whatsapp-business-platform/request/26gui66/subscribe-to-a-waba). Scriptul păstrează callbackurile străine și nu activează trimiterea până când recitirea confirmă callbackul, câmpurile și aplicația asociată. Nu trimite mesaje de probă automat.

## Conturile existente pe live în demo-ul local

`python3 scripts/daybreak_sync_live_accounts.py` citește numai înregistrările conturilor și indexurile lor de email din KV-ul live și le copiază în KV-ul local. Păstrează parola derivată, identificatorul și apartenența; nu copiază sesiuni sau aprobări și nu scrie pe live. Refuză coliziunile cu un alt cont local, păstrează o copie privată de siguranță și recitește fiecare valoare după import. La prima copiere a existat un singur cont live, fără apartenență operațională. Drepturile locale se atribuie separat, explicit.

La cererea ulterioară a lui Teo, conturile demonstrative sunt dispecer@daybreak.ro, tehnician@daybreak.ro și client@daybreak.ro, cu rolurile corespunzătoare, local și pe live. Parola cerută este păstrată numai în configurarea privată. Identificatorii existenți sunt păstrați, inclusiv asocierea WhatsApp a tehnicianului. Autentificarea existentă acceptă parola contului; crearea și resetarea obișnuită păstrează minimul de șase caractere. Provisionarea administrativă permite minimum patru caractere și o parolă comună numai pentru cele trei adrese și roluri exacte. Formularul a fost verificat cu toate cele trei roluri în ambele medii. Versiunea publicată din sursa comisă este 2c071473-84fb-4923-a5e7-2135d343fad1. Serviciul operațional Python continuă să ruleze local.

## Agentul în consola existentă

La cererea lui Teo, integrarea separată /workspace a fost înlocuită cu agentul din consola existentă. /app deschide planul original pentru dispecer, iar tehnicianul și clientul folosesc același AppShell cu datele autorizate. /workspace este numai o redirecționare de compatibilitate, inclusiv pentru propuneri. Navigarea, Wordmark, componentele DS, temele și culorile semantice PPC sunt comune site-ului.

Dashboardul /app include direct asistentul, alături de rezumat și cazul sau vizita relevantă. Nu există buton plutitor sau sertar peste ecran. Textul este modul implicit; vocea are o filă separată. Paginile de detaliu transmit lucrarea deschisă printr-o cerere temporară, limitată la contul și scenariul curent, apoi deschid dashboardul. Butoanele de aprobare și revizuire deschid acolo formularul, fără scriere sau succes local fictiv. Aprobarea nu se deduce din cookie-uri. Contextul, rolul și scenariul sunt reverificate; după confirmare se actualizează consola.

Verificare locală a dashboardului: trei conturi la 1440×1100, 1024×900 și 390×844, fără alerte sau depășiri orizontale; schimbarea temei; revizuire din detaliul lucrării în asistentul inline, fără efect automat; pregătire și anulare de propunere fără caz nou sau schimbarea versiunii planului; răspuns Codex real fără operație executată. 209 teste web, build Next izolat, typecheck și lint trec. Confirmarea efectivă fusese verificată în integrarea anterioară. Microfonul și difuzorul fizic nu au fost retestate în această etapă. Această corecție UI este verificată local, fără deploy.

## Actualizare vocală pentru prezentare

`python3 scripts/daybreak_channels.py tune-presentation` actualizează numai cei trei agenți existenți, verifică dependențele uneltelor, păstrează o copie privată a configurației anterioare și recitește rezultatul. Activează filtrarea vocilor din fundal, v4 Turbo, eager și confirmarea scurtă înaintea cererii. Limita este 10 minute și 30 sesiuni pe zi pentru fiecare rol. Nu pornește conversații și nu trimite mesaje. Notele vocale WhatsApp folosesc Scribe v2 și Eleven v4.

Dacă Meta întoarce 190/463, tokenul temporar a expirat. Generează un token nou în aplicația Meta existentă, apoi rulează `python3 scripts/daybreak_whatsapp_setup.py refresh-token`. Introducerea este ascunsă, iar tokenul se salvează numai după verificarea aplicației, a dreptului de mesagerie și a numărului. Nu îl pune în chat sau în argumentele comenzii. Serviciul îl preia fără restart. Starea confirmată pe 8 noiembrie la 01:54: token expirat, callback activ și verificat, fără probă WhatsApp nouă.

Răspunsul conversațional local măsurat după actualizare este circa 12 secunde; viteza și zgomotul din sala reală rămân de verificat. O notă vocală WhatsApp nu testează detectarea sfârșitului de vorbire din conversația live.

### Token Meta reînnoit și verificat

Pe 8 noiembrie, tokenul temporar expirat a fost regenerat în aplicația Meta existentă și schimbat prin API cu unul cu durată lungă. Expirare confirmată prin Debug Token: 6 ianuarie 2027, 23:15:30 București. Tokenul privat recitit are dreptul de mesagerie, API-ul confirmă numărul existent, subscrierea este activă și challenge-ul public trece. Nu este necesar restartul serviciului; testul WhatsApp al lui Teo poate începe. Nu s-au trimis mesaje de test în această verificare.

## Apeluri WhatsApp primite

Apelurile către același număr Meta de test sunt conectate direct prin SIP la un agent ElevenLabs separat pentru apeluri. Mesajele și notele vocale rămân în integrarea Meta existentă. Nu este un import WhatsApp nativ ElevenLabs: acel import nu acceptă WABA creat sub aplicația de dezvoltator.

Numărul are calling=ENABLED, call_icon_visibility=DEFAULT, SIP către sip.rtc.elevenlabs.io:5061, semnalizare TLS, autentificare digest cu parola generată de Meta și audio SRTP cu SDES. Codecurile PCMA/PCMU sunt activate pentru compatibilitatea cu ElevenLabs. Agentul folosește v4 Turbo, filtrarea fundalului și limita de 10 minute. Jurnalele SIP și înregistrarea audio sunt dezactivate. Apelurile sunt limitate la numărul deja verificat al lui Teo și la rolul său de tehnician; nu există rută pentru apeluri inițiate de agent.

Agentul apelează un serviciu restrâns pe 127.0.0.1:8722, expus prin propriul tunel HTTPS temporar. Serviciul cere o acreditare separată, verifică apelantul cu asocierea WhatsApp existentă și folosește ConversationService pe datele complete izolate și modelele locale. Apelantul și identificatorul conversației sunt injectate de ElevenLabs din variabilele de sistem, nu alese de LLM. Istoricul este păstrat numai în memoria procesului și limitat la 12 mesaje și 11 minute. Confirmarea operațiilor rămâne exclusiv în aplicație.

Pornire și verificare fără apeluri automate:

```sh
.venv/bin/python scripts/daybreak_whatsapp_calls.py prepare
.venv/bin/python -m uvicorn cyberpunks.channels.whatsapp_calls:create_app --factory --host 127.0.0.1 --port 8722 --no-access-log
# Alt terminal, numai serviciul restrâns:
cloudflared tunnel --url http://127.0.0.1:8722 --no-autoupdate
# După obținerea originii HTTPS a acestui tunel:
.venv/bin/python scripts/daybreak_whatsapp_calls.py configure --public-origin https://GAZDA.trycloudflare.com
.venv/bin/python scripts/daybreak_whatsapp_calls.py verify
.venv/bin/python scripts/daybreak_whatsapp_calls.py show-call-button
```

Secretele SIP, acreditarea serviciului, originea temporară și identificatorii resurselor sunt numai în outputs/runtime/whatsapp-calling.json, cu permisiuni 0600 și ignorat de Git. Nu afișați sau copiați conținutul. Scriptul păstrează separat resursele noi, refuză numere existente străine și nu repetă creări cu rezultat necunoscut. Nu oprește și nu repornește runtime-ul consolei sau workerul de mesaje.

Verificare din 8 noiembrie: setările Meta și ElevenLabs recitite, certificat TLS SIP verificat, cerere neautentificată respinsă cu 401, cerere autorizată prin tunel cu răspuns Codex real în 11,23 secunde. Cele 184 teste Python pentru canale, runtime și operațiuni trec. Apelul complet de pe telefon și zgomotul din sală rămân probe separate. Teo a primit solicitarea de a suna o singură dată. Calculatorul și tunelul serviciului trebuie să rămână pornite pentru răspunsurile cu date Daybreak.

Surse: [Meta SIP](https://developers.facebook.com/documentation/business-messaging/whatsapp/calling/sip/), [Meta call settings](https://developers.facebook.com/documentation/business-messaging/whatsapp/calling/call-settings/), [ElevenLabs SIP](https://elevenlabs.io/docs/eleven-agents/phone-numbers/sip-trunking), [variabile de sistem](https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables).

### Restart numai de frontend

`daybreak_runtime.py start` supraveghează API-ul și frontendul împreună și le oprește pe ambele dacă unul se închide. Grupurile de procese diferite nu le fac independente. Pentru QA cu restart numai de frontend, porniți API-ul și frontendul ca procese independente, cu mediul întors de `daybreak_runtime.environment()`, fără rescrierea fișierelor private. Înainte de orice pornire verificați listenerul portului, ca să nu dublați API-ul. Pe 8 noiembrie s-a verificat recuperarea separată a API-ului 8720 după acest comportament; workerul Meta și serviciul de apeluri 8722 au rămas active.
