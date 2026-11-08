# 03 Analiza întregii cozi

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Produce o recomandare explicabilă pentru fiecare caz din coada autorizată, cu dovada acoperirii complete și fără modificarea planului.

## Fișiere proprii

- src/cyberpunks/agentic/queue_analysis.py
- tests/agentic/test_queue_analysis.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/planner/decide.py
- src/cyberpunks/common/contracts.py
- src/cyberpunks/operations/planner.py

## Cerințe

1. Consumă snapshotul complet din 02, prin contractul 01. Calculează recomandările în cod folosind predicțiile, regulile și constrângerile existente. Separă decizia actuală, recomandarea propusă și efectul încă neexecutat. Nu reantrena modelele și nu inventa o nouă formulă de prioritizare.

Regulile dependente de capacitatea globală nu se reaplică pe un subset ca și cum ar fi întregul plan. Reflecți decizia și constrângerile planificatorului real; o analiză human_review nu devine automat o listă approve. Livrezi dovezile împreună cu rezultatul; 17 le verifică la consumarea de către coordonator și rapoarte. Nu importa verificatorul înapoi în modulul de analiză.

2. Pentru fiecare caz păstrează motivul, predicția și versiunea, regula, impactul verificat, incertitudinea, blocajul și următorul pas. Fără evaluare validă, întoarce abținere și datele necesare ori revizuire umană.

3. Verifică egalitatea mulțimilor sursă/citit/rezultat, dubluri și erori. Nu marca o analiză completă când lipsește o pagină. Numărul 25 este un caz de verificare, nu hard limit; tratează și cozi mai mari.

4. Păstrează semnalul de siguranță și limita de echipe. Recomandarea approve nu declară că lucrarea încape în traseu. Nu aplica revizuiri, aprobări, replanificări, trimiteri sau etichete ML.

## Verificare și predare

Probe pe întreaga copie, cu numărul real de cazuri; regresii pentru mai mult de opt și pentru 25 de cazuri controlate în copia completă, etichetate sintetic. Testează lipsuri, dubluri, pagină omisă, predicție invalidă, cauze apropiate și capacitate insuficientă. Compară planul înainte/după: analiza nu îl schimbă.
