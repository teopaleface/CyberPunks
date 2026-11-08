# 12 Accesul HTTP autentificat

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Expune taskurile și rapoartele prin autentificarea existentă, cu o schemă stabilă și fără endpoint nou de confirmare.

## Fișiere proprii

- src/cyberpunks/agentic/router.py
- tests/agentic/test_router.py
- web/lib/agentic/client.ts
- web/lib/agentic/client.test.ts
- web/lib/agentic/report-gateway.ts
- web/lib/agentic/report-gateway.test.ts
- web/app/api/agentic/reports/[reportId]/pages/[page]/route.ts

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/channels/router.py
- src/cyberpunks/operations/auth.py
- web/app/api/conversation/[...path]/route.ts
- web/lib/operations/gateway.ts
- web/lib/operations/client.ts
- web/lib/operations/photo-gateway.ts

## Cerințe

1. Implementează routerul și clientul după rutele și tipurile înghețate de 01. Identitatea vine din dependența de autentificare a serverului; reutilizează gateway-ul existent prin montarea pe care o face 00. Nu accepta actor, rol, număr ori permisiuni în corp.

2. Pornirea taskului este POST limitat; GET citește numai starea sau artefactul propriu și nu rulează taskuri, confirmări ori reconciliere. Continuarea explicită, dacă interfața o cere, rămâne POST și este autorizată separat.

3. Verifică proprietarul, domeniul actual, expirarea și versiunea la fiecare acces. UUID-ul singur nu acordă acces. Rapoartele sunt private, no-store și fără redirect către o resursă externă. Erorile sunt sigure și nu includ excepții brute sau context.

4. Clientul web propagă sesiunea și semnalele de anulare conform convențiilor existente. Nu adăuga un mecanism nou de login sau confirmare; nu schimba vechile proxy-uri. Predă montarea și eventualele căi allowlist pentru 00.

Proxy-ul conversației existent tratează JSON și are o listă explicită de căi. Pentru imagine implementează gateway-ul privat și ruta proprie din lista ta, reutilizând autentificarea existentă după modelul photo-gateway. Verifică octeții PNG, Content-Type și anteturile; nu elimina filtrarea vechiului gateway și nu transforma octeții în răspuns JSON. Limitarea timpului fiecărei cereri trebuie să permită progres durabil în locul a șase ture LLM blocate într-o singură cerere.

## Verificare și predare

Probe HTTP cu dependențe injectate pentru cele trei roluri, lipsa autentificării, alt actor/organizație/scenariu, câmpuri suplimentare, raport străin, index de pagină invalid, expirare, revocare și GET fără efect. Testează erorile de sesiune și payloadurile clientului. Nu monta routerul în serverul live.

