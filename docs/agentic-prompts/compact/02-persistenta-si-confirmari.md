# 02 Sarcini persistente, confirmări și recuperare

Citește AGENTS.md, memory/INDEX.md și docs/PLAN-AGENTIC.md. Păstrează lucrul concurent și ramura Teo. Editează numai fișierele rezervate în manifestul compact. Lucrează pe copia completă izolată, fără secrete sau setări de trimitere; datele adăugate sunt sintetice. Nu reporni servicii, nu modifica conturi și nu trimite mesaje sau apeluri externe. Coordonatorul gestionează Git și integrarea. Predă fișierele, probele exacte și ce rămâne netestat.

Modelele proprii și regulile existente susțin deciziile. Numai Confirm din aplicația autentificată execută schimbări operaționale. Drepturile și versiunile se reverifică la utilizare. Constatarea nu declară reparația. O citire de comandă care poate reconcilia nu este un instrument pasiv.

## Sarcina

Implementează starea durabilă a sarcinilor și legătura cu propunerile/comenzile existente. Folosește tranzacții scurte, claim limitat, retry fără dubluri și recuperare după restart. Actorul salvat nu reactivează drepturile: reluarea cere autentificare actuală. Nu ține tranzacții în timpul apelurilor LLM sau HTTP.

Reutilizează prepare și confirmarea existentă; nu crea încă un mecanism de execuție. Oferă observație pasivă, distinctă de recuperarea autorizată. Pregătirea nu execută, iar după confirmare rezultatul real se recitește. O revizuire poate invalida planul și alte propuneri.

Testează concurență, restart, expirare, anulare, rol revocat, versiuni vechi și întrerupere după efect înainte de răspuns. Aceeași comandă produce un singur efect. Modificările necesare în serviciul existent se predau coordonatorului.

## Fișiere rezervate

- src/cyberpunks/agentic/task_store.py
- tests/agentic/test_task_store.py
- src/cyberpunks/agentic/effects.py
- tests/agentic/test_effects.py
