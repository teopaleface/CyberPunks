# Cele trei conturi, vocea și WhatsApp

Implementarea locală acoperă clientul, tehnicianul și dispecerul din planul conversațional. Catalogul complet are 80 de cazuri și situații; extensiile P1/P2 din plan nu sunt toate implementate. Interfața este în engleză, iar conversația răspunde în română sau engleză.

## Pornire

```sh
python3 scripts/daybreak_runtime.py check
python3 scripts/daybreak_runtime.py start
# În alt terminal, doar pentru conturile sintetice locale:
python3 scripts/daybreak_runtime.py accounts
```

Aplicația este la `http://127.0.0.1:3870/workspace`, API-ul privat pe 8720. Procesele vechi de pe 3710 și 8710 sunt separate. Comanda accounts păstrează identificatorii și parolele existente; upgrade-ul verificat al dispecerului sintetic acordă numai recuperarea comenzilor. Nu se folosește prepare --new-run peste o demonstrație activă, deoarece creează alte identități și necesită refacerea asocierilor.

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
