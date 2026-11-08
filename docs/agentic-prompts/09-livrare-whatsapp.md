# 09 Livrarea imaginii pe WhatsApp

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Adaugă suportul logic pentru răspuns cu imagini, folosind registrul de livrare existent și fără trimiteri reale în acest job.

## Fișiere proprii

- src/cyberpunks/agentic/image_delivery.py
- tests/agentic/test_image_delivery.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/channels/whatsapp_transport.py
- src/cyberpunks/channels/whatsapp_store.py
- src/cyberpunks/channels/whatsapp_worker.py
- src/cyberpunks/channels/whatsapp_config.py
- tests/channels/test_whatsapp_delivery.py

## Cerințe

1. Implementează adaptorul după contractul 01, cu client HTTP și registru injectate. Uploadul și mesajul folosesc media API Meta; nu publica un link deschis către fișier și nu importa numărul în alt furnizor.

2. Folosește numai destinatarul deja asociat emitentului. Verifică din nou identitatea, drepturile, opțiunile și fereastra de mesagerie înaintea uploadului și fiecărui POST ireversibil. Apelul singur nu deschide fereastra. Nu permite număr sau URL arbitrar de la LLM.

3. Gestionează pagini PNG multiple cu identificatori stabili per pagină și hash-ul octeților persistați. Registrul actual pe eveniment/tip trebuie extins de 00; predă modificarea precisă, nu construi un registru concurent. Acceptat, livrat și citit sunt stări diferite.

4. Timeoutul sau răspunsul necunoscut nu produce retrimitere automată. Callbackurile și restartul nu dublează textul, audio sau paginile. Dacă imaginea eșuează, textul verificat rămâne disponibil fără reluarea analizei.

## Verificare și predare

Cu transport simulat testează upload eșuat, 429, timeout necunoscut, callback înainte/după răspuns, trei pagini, retry, restart, rol revocat, fereastră închisă și păstrarea textului. Nu citi tokenuri și nu trimite mesaje. Predă punctele exacte de extindere a transportului/registrului către 00.

