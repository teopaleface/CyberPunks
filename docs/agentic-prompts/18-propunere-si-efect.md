# 18 Legătura dintre propunere și efect

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Pregătește operația exactă cerută și observă efectul confirmat, păstrând un singur mecanism de execuție și recuperare.

## Fișiere proprii

- src/cyberpunks/agentic/effects.py
- tests/agentic/test_effects.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/operations/service.py
- src/cyberpunks/operations/planner.py
- tests/operations/test_operations.py
- tests/operations/test_recovery.py

## Cerințe

1. Folosește OperationsService.prepare și modelele existente, cu versiunile cazului și planului analizat. Corecțiile păstrează motivul și originalul. Nu scrie direct în planificator sau în registrul comenzilor.

2. Interfața oferită coordonatorului nu are confirmare. După Confirm din aplicație, folosește observația pasivă din contractul 01 și recitește contextul autorizat. Metoda command existentă poate reconcilia; nu o apela tacit ca pe o citire fără efecte.

3. Dacă lipsește o observație pasivă în serviciul existent, predă lui 00 modificarea exactă necesară, cu testele aferente adaptorului, fără să editezi fișierul central. Recuperarea rămâne pe calea explicit autorizată existentă.

4. Distinge cererea approve de rezultatul efectiv, capacitatea insuficientă, invalidarea planului și aprobarea separată a planului. Reluarea taskului nu pregătește în avans operații pentru toate cazurile și nu confirmă din nou.

## Verificare și predare

Pe copia completă verifică propunere fără efect, refuz la versiune veche, confirmare prin calea existentă cu un singur efect, observație repetată fără mutații și întrerupere după efect. Probează și no_access/confirmed fără declararea reparației. Predă legătura precisă necesară în 00.
