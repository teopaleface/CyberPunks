# 13 Probe de securitate și reluare

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Verifică independent că integrarea păstrează autorizarea, confirmarea și execuția fără dubluri.

## Fișiere proprii

- tests/agentic/test_security_regressions.py
- tests/agentic/test_recovery_regressions.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- tests/operations/test_operations.py
- tests/operations/test_recovery.py
- tests/channels/test_whatsapp_delivery.py
- tests/channels/test_voice_call_probe.py
- docs/PLAN-AGENTIC.md

## Cerințe

1. Poți pregăti probele după contractul 01, apoi le execuți după integrarea modulelor. Folosește interfețele reale ale modulelor, fixture-ul complet și planificatorul real în copia izolată. Nu modifica implementarea pentru a-ți face probele să treacă.

2. Acoperă schimbarea rolului prin text, accesul pe UUID străin, revocarea în mijlocul unei sarcini, schimbarea planului între citire/pregătire/confirmare și lipsa drepturilor la reluare. Verifică ce informație ajunge efectiv în context, răspuns, HTML și PNG.

3. Verifică explicit că citirea/statusul nu poate reconcilia ori confirma comenzi. Simulează întreruperea după efect și înaintea răspunsului, două confirmări simultane și restart: un singur efect și aceeași comandă durabilă.

4. Pentru livrare, probează ordinea inversată a callbackurilor, pagini multiple, rezultat necunoscut și revocare înainte de POST. Pentru analiză, probează omisiuni după primele opt, schimbarea versiunii și limită de revizuire umană care nu trunchiază analiza.

## Verificare și predare

Predă pentru fiecare defect pașii de reproducere, efectul, fișierul și gravitatea. Rulează probele noi și regresiile relevante existente după integrare, fără a cheltui credite ori a contacta furnizori. O probă blocată pe modul lipsă rămâne netestată, nu skipped-success.
