# 04 Sarcini persistente

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Persistă progresul și rezultatul unei sarcini private și permite reluare controlată după întrerupere.

## Fișiere proprii

- src/cyberpunks/agentic/task_store.py
- tests/agentic/test_task_store.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/operations/database.py
- src/cyberpunks/operations/service.py
- src/cyberpunks/channels/whatsapp_queue.py
- src/cyberpunks/channels/whatsapp_store.py

## Cerințe

1. Implementează interfața 01 cu tranzacții, tranziții valide și claim/lease limitat pentru a evita procesarea simultană. Coordonatorul injectează calea bazei izolate; modulul nu deschide implicit baza runtime activă și nu pornește worker.

2. Leagă fiecare sarcină de emitent, organizație, scenariu, apartenență și versiune. Citirea cere un actor curent verificat; datele salvate nu îi reactivează drepturile vechi. Proiecția publică elimină contextul brut și semnăturile interne.

3. Persistă rezultatele etapelor, dovezile, referințele propunerilor și identificatorii artefactelor. O analiză finalizată și o operație executată sunt stări distincte. Stabilește expirarea, anularea și reluarea conform contractului.

4. Recuperarea sarcinii nu confirmă operații și nu retrimite mesaje cu rezultat necunoscut. Refolosește identificatorii durabili ai operațiilor și registrului de livrare, fără o a doua sursă pentru efectul real.

Reluarea cere o identitate reverificată în cererea curentă. Dacă aceasta nu este disponibilă după restart, sarcina așteaptă reluarea autentificată. Nu ține tranzacții sau lease-uri fără termen în timpul apelurilor modelului ori transportului.

## Verificare și predare

Testează restartul unui obiect de store, concurență, claim expirat, retry identic/diferit, tranziții invalide, anulare, alt actor/organizație și revocare. Probe numai în baze temporare. Predă schema de migrare/conectare pentru 00, fără a o aplica runtimeului.

