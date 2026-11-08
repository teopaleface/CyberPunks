# 05 Integrare și verificare finală

Citește AGENTS.md, memory/INDEX.md și docs/PLAN-AGENTIC.md. Păstrează lucrul concurent și ramura Teo. Editează numai fișierele rezervate în manifestul compact. Lucrează pe copia completă izolată, fără secrete sau setări de trimitere; datele adăugate sunt sintetice. Nu reporni servicii, nu modifica conturi și nu trimite mesaje sau apeluri externe. Coordonatorul gestionează Git și integrarea. Predă fișierele, probele exacte și ce rămâne netestat.

Modelele proprii și regulile existente susțin deciziile. Numai Confirm din aplicația autentificată execută schimbări operaționale. Drepturile și versiunile se reverifică la utilizare. Constatarea nu declară reparația. O citire de comandă care poate reconcilia nu este un instrument pasiv.

## Sarcina

Tu ești coordonatorul principal. Înaintea delegării verifică starea Git și sursa completă read-only, pregătește copia izolată și fixează contractele mici pentru snapshot, analiză, task, raport și efect. Reutilizează modelele existente; nu porni un agent separat doar pentru contracte.

După contracte lansează 01, 02 și 03 în paralel, cu deținerea fișierelor din manifest. Când se eliberează primul loc pornește 04. Folosește subagenți ai firului, maximum trei simultan. Descoperă furnizorul/modelul și opțiunile curente prin orchestrator_capabilities; dacă sunt opțiuni moștenite, folosește delegate_task cu target.options. Păstrează taskId și chei stabile per rundă. Nu crea conversații top-level.

Conectează modulele pe parcurs în fișierele centrale rezervate ție. Verifică devreme analiza completă și o operație confirmată prin planificatorul real. Actualizează controlat allowlistul JSON și registrul de livrare pentru pagini multiple. Buildurile sunt separate de frontendul demo. Fă commituri selective, fără lucrul vecinilor.

După integrare verifică circuitul client-dispecer-tehnician, versiuni vechi, revocare, reluare și lipsa dublurilor. Fă revizia standardelor și a cerințelor în acest job, fără alte prompturi permanente. Separă probele simulate, locale, API și telefonul fizic. Probele externe și deploy-ul se fac numai în scope autorizat explicit. Închide delegările după predare, actualizează memoria și raportează rezultatul efectiv. Nu lansa implementarea doar pentru că acest pachet a fost pregătit.

## Fișiere rezervate

- src/cyberpunks/channels/conversation.py
- src/cyberpunks/channels/models.py
- src/cyberpunks/channels/codex.py
- src/cyberpunks/channels/router.py
- src/cyberpunks/channels/whatsapp.py
- src/cyberpunks/channels/whatsapp_worker.py
- src/cyberpunks/channels/whatsapp_transport.py
- src/cyberpunks/channels/whatsapp_store.py
- src/cyberpunks/channels/whatsapp_calls.py
- src/cyberpunks/channels/elevenlabs.py
- src/cyberpunks/operations/service.py
- src/cyberpunks/operations/router.py
- src/cyberpunks/operations/database.py
- src/cyberpunks/operations/planner.py
- src/cyberpunks/runtime.py
- src/cyberpunks/api/app.py
- web/components/workspace/workspace.tsx
- web/components/workspace/main-conversation.tsx
- web/components/workspace/voice.tsx
- web/components/workspace/workspace.css
- web/lib/operations/client.ts
- web/lib/operations/types.ts
- web/lib/operations/gateway.ts
- web/app/api/conversation/[...path]/route.ts
- web/app/api/operations/[...path]/route.ts
- pyproject.toml
- uv.lock
- web/package.json
- web/bun.lock
- docs/operations/BACKEND.md
- docs/operations/CHANNELS.md
- docs/operations/RUNBOOK.md
- memory/INDEX.md
- memory/journal.md
- memory/15-agent-decizii-si-canale.md
- src/cyberpunks/agentic/__init__.py
- src/cyberpunks/agentic/contracts.py
- src/cyberpunks/agentic/ports.py
- contracts/agentic/v1.schema.json
- contracts/agentic/examples/**
- web/lib/agentic/contracts.ts
- tests/agentic/__init__.py
- tests/agentic/conftest.py
- tests/agentic/test_contracts.py
- docs/agentic-prompts/INTERFACES.md
- tests/agentic/test_security_regressions.py
- tests/agentic/test_recovery_regressions.py
- tests/agentic/test_acceptance.py
- scripts/daybreak_agentic_acceptance.py
- docs/operations/AGENTIC-ACCEPTANCE.md
