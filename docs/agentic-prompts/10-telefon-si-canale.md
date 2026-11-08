# 10 Telefonul și continuarea între canale

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Leagă apelul și mesajele de aceeași sarcină autorizată, cu răspuns vocal scurt și continuare controlată în aplicație sau WhatsApp.

## Fișiere proprii

- src/cyberpunks/agentic/channel_bridge.py
- tests/agentic/test_channel_bridge.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/channels/whatsapp_calls.py
- src/cyberpunks/channels/whatsapp.py
- src/cyberpunks/channels/elevenlabs.py
- src/cyberpunks/channels/whatsapp_config.py
- tests/channels/test_voice_call_probe.py

## Cerințe

1. Implementează adaptorul după 01, pentru identitatea injectată și verificată de canal. Prima versiune folosește asocierea de tehnician existentă. Un rol declarat verbal sau un număr cerut în conversație nu schimbă actorul.

2. Pentru întrebarea despre traseu cere ruta aprobată a echipei și întoarce numai textul verificat. Pentru analiza mai lungă păstrează un task durabil și spune cum se continuă, fără un răspuns terminat la simplul „verific”.

3. La cererea unui raport în WhatsApp, solicită livrarea numai dacă există permisiune și fereastră de mesagerie validă. Altfel pregătește raportul în aplicație și explică necesitatea unui mesaj de la utilizator. Reia aceeași sarcină prin referință autorizată, fără a copia global transcrierile.

4. Un da rostit nu confirmă. Propunerile se deschid în aplicația autentificată; linkul nu conține tokenuri de confirmare și nu acordă acces. Eșecul vocii păstrează textul și starea reală a taskului.

## Verificare și predare

Testează două ture cu aceeași identitate, schimbarea identității, expirare, revocare, referință străină, mesaj citat, da ambiguu, apel fără fereastră și predare după restart. Nu crea agenți ElevenLabs, nu modifica SIP/tuneluri/asocieri și nu iniția apeluri ori mesaje. Predă pentru 00 modificările punctuale din canalele existente.
