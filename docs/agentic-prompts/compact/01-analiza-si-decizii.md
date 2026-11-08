# 01 Analiza cozii și deciziile agentului

Citește AGENTS.md, memory/INDEX.md și docs/PLAN-AGENTIC.md. Păstrează lucrul concurent și ramura Teo. Editează numai fișierele rezervate în manifestul compact. Lucrează pe copia completă izolată, fără secrete sau setări de trimitere; datele adăugate sunt sintetice. Nu reporni servicii, nu modifica conturi și nu trimite mesaje sau apeluri externe. Coordonatorul gestionează Git și integrarea. Predă fișierele, probele exacte și ce rămâne netestat.

Modelele proprii și regulile existente susțin deciziile. Numai Confirm din aplicația autentificată execută schimbări operaționale. Drepturile și versiunile se reverifică la utilizare. Constatarea nu declară reparația. O citire de comandă care poate reconcilia nu este un instrument pasiv.

## Sarcina

Folosește contractul stabilit inițial de coordonator. Reutilizează OperationsService.context, care conține deja toate lucrările autorizate; selectează explicit coada human_review, fără limita conversațională de șase sau opt. Produce exact un rezultat pentru fiecare identificator, inclusiv abținere pentru evaluări invalide. Numărul 25 nu este o limită de citire.

Coordonează maximum șase pași LLM, cu bugete care încap în cererile canalelor și progres persistent prin interfața sarcinii 02. Verifică dovezile și cifrele din snapshot, inclusiv valorile derivate și versiunea. Pregătirea și observația efectului consumă adaptorul 02; nu expune confirmarea modelului. Nu reaplica reguli de capacitate pe un subset ca și cum ar fi întregul plan.

Testează acoperirea exactă pe datele complete, cazuri după primele opt, lipsuri, dubluri, versiune schimbată, revocare și afirmații fără dovezi. Analiza nu modifică planul. Predă punctele de conectare în conversația existentă coordonatorului.

## Fișiere rezervate

- src/cyberpunks/agentic/snapshots.py
- tests/agentic/test_snapshots.py
- src/cyberpunks/agentic/queue_analysis.py
- tests/agentic/test_queue_analysis.py
- src/cyberpunks/agentic/coordinator.py
- tests/agentic/test_coordinator.py
- src/cyberpunks/agentic/evidence.py
- tests/agentic/test_evidence.py
