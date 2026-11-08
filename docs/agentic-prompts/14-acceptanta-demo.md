# 14 Acceptanță și demo

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Dovedește circuitul complet pe cele trei conturi și pregătește scenariul de cinci minute, fără a confunda simulările cu probele de telefon.

## Fișiere proprii

- tests/agentic/test_acceptance.py
- scripts/daybreak_agentic_acceptance.py
- docs/operations/AGENTIC-ACCEPTANCE.md

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- docs/PLAN-AGENTIC.md
- docs/operations/RUNBOOK.md
- web/design/CONSOLE-RECOVERY.md
- tests/channels/conftest.py

## Cerințe

1. Pregătește scenariul după 01; execută-l după integrarea 00 și 02–13. Folosește copia completă coerentă și conturi sintetice, verificând sursa prin identificatori/versiuni. Nu înlocui întregul sistem cu 25 de obiecte fabricate.

2. Parcurge cererea clientului, analiza întregii cozi, revizuirea confirmată de dispecer, planul aprobat, traseul tehnicianului și constatarea confirmată. Verifică starea comună și limitele proiecției clientului, inclusiv că reparația nu este declarată.

3. Scriptul de acceptanță este sigur implicit și folosește numai sandboxul local fără transport extern. Probează și o conversație cu două ture și funcții reale locale. Un mod extern trebuie delimitat și rulat doar de 00 în etapa autorizată; nu păstra chei, cookie-uri sau date personale în script ori raport.

4. Documentează pașii demo, condițiile de pornire și dovezile reale obținute. Pentru apel fizic, imagine primită, zgomotul sălii și timpi manual versus agent folosește starea neverificat până când există proba respectivă. Nu cere repetat înregistrări sau intervenții de la Teo.

## Verificare și predare

Rulează acceptanța locală integrată și proba de regresie pe date complete. Browserul folosește fluxul local de QA autorizat, trei sesiuni independente și build separat; nu pornește alte profile Helium și nu schimbă serviciile. Predă criteriile trecute și exact ce rămâne pentru telefon/furnizori. Raportul nu conține artefacte imaginare sau cifre din mockup.
