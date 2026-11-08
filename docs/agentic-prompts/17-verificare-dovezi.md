# 17 Verificarea dovezilor și cifrelor

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Verifică afirmațiile tehnice și valorile derivate printr-o singură interfață folosită de coordonator și rapoarte.

## Fișiere proprii

- src/cyberpunks/agentic/evidence.py
- tests/agentic/test_evidence.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/channels/conversation.py
- src/cyberpunks/operations/service.py
- src/cyberpunks/common/contracts.py

## Cerințe

1. Implementează EvidenceRef și verificarea după contractul 01. Compară valorile cu snapshotul și rezultatele calculate, păstrând scopul și versiunea. O cifră prezentă întâmplător în alt câmp nu dovedește afirmația.

2. Păstrează refuzul evaluărilor indisponibile și separarea probabilității problemei de incertitudinea cauzei. Conversia în procente urmează politica exactă existentă; nu relaxa verificarea globală pentru noul flux.

3. Nu importa circular channels/conversation.py și nu crea un verificator paralel mai permisiv. Predă lui 00 conectarea validării existente și explică exact ce verifică automat și ce nu poate garanta semantic.

4. Verifică totalurile și proveniența calculelor înainte de text/voce/HTML/PNG. Raportarea unei operații are nevoie de efect observat, nu de istoric, intenție sau numai starea taskului.

## Verificare și predare

Probe pentru cifră inventată, același număr în context greșit, pointer străin, rezultat de calcul alterat, versiune schimbată, score indisponibil și conversie exactă în procente. Pe sursa completă, toate totalurile din QueueAnalysis trebuie să se potrivească rezultatelor și identificatorilor.
