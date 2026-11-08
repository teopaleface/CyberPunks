# 04 Interfața și legătura cu telefonul

Citește AGENTS.md, memory/INDEX.md și docs/PLAN-AGENTIC.md. Păstrează lucrul concurent și ramura Teo. Editează numai fișierele rezervate în manifestul compact. Lucrează pe copia completă izolată, fără secrete sau setări de trimitere; datele adăugate sunt sintetice. Nu reporni servicii, nu modifica conturi și nu trimite mesaje sau apeluri externe. Coordonatorul gestionează Git și integrarea. Predă fișierele, probele exacte și ce rămâne netestat.

Modelele proprii și regulile existente susțin deciziile. Numai Confirm din aplicația autentificată execută schimbări operaționale. Drepturile și versiunile se reverifică la utilizare. Constatarea nu declară reparația. O citire de comandă care poate reconcilia nu este un instrument pasiv.

## Sarcina

Creează cardurile de progres și rezultate în conversația principală, clientul și routerul autentificat și continuarea între canale. Citește web/AGENTS.md și ghidul Next instalat. Folosește contractele comune și dependențe simulate până la predarea modulelor reale.

Arată toate rezultatele și acoperirea, stările parțiale, propunerile și efectele reale separat. Revizuirea deschide formularul existent; nu confirmă automat. Oprește cererile vechi la schimbarea contului/scenariului. Păstrează engleza interfeței și Light/Dark. GET nu pornește sarcini și nu reconciliază comenzi. Pentru PNG folosește gateway privat separat de proxy-ul JSON.

Apelul existent oferă traseul aprobat și continuare autorizată pentru sarcini lungi. Prima asociere telefonică rămâne tehnicianul; nu schimba rolul prin conversație. Un da nu confirmă. Nu modifica SIP, agenți vocali, tuneluri sau asocieri.

Testează trei roluri local, acces străin, revocare, sesiune expirată, două ture, plan neaprobat, continuitatea sarcinii și ecran de 360 px. Conectarea în Workspace și canalele existente aparține coordonatorului.

## Fișiere rezervate

- src/cyberpunks/agentic/channel_bridge.py
- tests/agentic/test_channel_bridge.py
- web/components/agentic/**
- web/lib/agentic/use-task.ts
- web/lib/agentic/use-task.test.tsx
- src/cyberpunks/agentic/router.py
- tests/agentic/test_router.py
- web/lib/agentic/client.ts
- web/lib/agentic/client.test.ts
- web/lib/agentic/report-gateway.ts
- web/lib/agentic/report-gateway.test.ts
- web/app/api/agentic/reports/[reportId]/pages/[page]/route.ts
