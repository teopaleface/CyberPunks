# 05 Coordonatorul agentic

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Duce o cerere prin mai mulți pași autorizați și verifică rezultatul, cu maximum șase pași conversaționali și limite de durată.

## Fișiere proprii

- src/cyberpunks/agentic/coordinator.py
- tests/agentic/test_coordinator.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/channels/conversation.py
- src/cyberpunks/channels/models.py
- src/cyberpunks/channels/codex.py
- src/cyberpunks/operations/service.py

## Cerințe

1. Implementează coordonatorul după interfețele 01, cu citirea 02, analiza 03 și persistența 04 injectate. Poate cere date, explicații, rapoarte și pregătirea uneia dintre acțiunile existente. Cele 25 de cazuri se procesează prin analiză, fără 25 de ture LLM succesive.

Verificarea dovezilor vine din 17, iar pregătirea și observația efectului din 18. Nu le reimplementezi în bucla de coordonare. Pentru prima versiune, reluarea după restart se face cu autentificare curentă; simplul actor salvat nu autorizează procesare autonomă. Împarte progresul în cereri limitate care încap în termenele proxy-ului și uneltei vocale, păstrând o stare durabilă.

2. Autorizează fiecare cerere de funcție și verifică domeniul și versiunile după așteptări. Propunerile rămân în awaiting_confirmation; confirmarea și recuperarea comenzii nu sunt unelte ale LLM-ului. După Confirm, observă efectul prin interfața pasivă și reface citirea autorizată.

3. Întrebările simple despre traseul aprobat au cale scurtă. Nu porni modelele lente inutil. Timpul epuizat, o dependență indisponibilă sau o nepotrivire a dovezilor produc stare explicită, nu succes inventat.

4. Procesul LLM rămâne izolat. Folosește interfața de planificare din 01; descrie pentru 00 schimbarea exactă necesară în schema furnizorului existent. Păstrează reply/proposal și proveniența compatibile. Nu modifica fișierele channels existente.

## Verificare și predare

Cu furnizor explicit simulat verifică două sau mai multe etape reale de funcție, limita de șase, date lipsă, tool nepermis, injecții, plan schimbat, revocare, restart și observație fără efect. După dependențe, probează pe copia completă pregătire + confirmare prin API-ul existent + recitire, fără confirmare din agent.
