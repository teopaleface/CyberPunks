# 01 Contracte și date de test

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Îngheață interfețele pentru celelalte joburi, cu modificări exclusiv aditive față de conversația și operațiile existente.

## Fișiere proprii

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

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/operations/models.py
- src/cyberpunks/channels/models.py
- src/cyberpunks/channels/conversation.py
- tests/channels/conftest.py
- tests/operations/conftest.py

## Cerințe

1. Transformă cerințele din INTERFACES.md în modele Pydantic stricte, schema JSON și tipuri TypeScript compatibile. Refolosește Actor și acțiunile existente. Fixează scopurile, stările, tranzițiile, erorile, limitele, anularea și proiecția publică. Nu adăuga unelte generale, SQL, HTML sau destinatari arbitrari în intrările LLM.

2. Definește interfețe mici pentru citire autorizată, analiză, persistență, planificarea pasului conversațional, pregătire de operație, observație pasivă a efectului, raport și livrare. Confirmarea și recuperarea existentă nu sunt unelte de citire. Propune exact ruta și răspunsul aditiv pentru taskuri și rapoarte, inclusiv statusul fără efecte.

3. Fixează acoperirea cozii prin identificatori așteptați/citiți/analizați, versiuni și erori. Fixează referințele la dovezi calculate și identificatorul stabil al fiecărei pagini PNG. Asigură compatibilitatea text/voce/HTML/PNG din aceeași structură.

4. Pregătește fixture-ul comun pe copia completă izolată primită de la 00. Verifică lista, hash-urile și versiunile față de sursa completă; pragul de 600 nu este suficient. Exemplarele sanitizate pentru UI sunt marcate ca exemple de contract și nu devin sursă pentru analiza completă.

## Verificare și predare

Testează respingerea câmpurilor autoritare, variante invalide, round-trip Python/JSON/TypeScript și izolarea datelor publice. Predă schema agentic-v1 și exemplele necesare celorlalți; numai după acceptarea 00 contractul este înghețat.
