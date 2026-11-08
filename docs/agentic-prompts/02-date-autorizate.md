# 02 Date autorizate și proveniență

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Livrează o citire completă și coerentă a datelor permise actorului, pentru analiză și rapoarte, prin interfața 01.

## Fișiere proprii

- src/cyberpunks/agentic/snapshots.py
- tests/agentic/test_snapshots.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- src/cyberpunks/operations/service.py
- src/cyberpunks/operations/auth.py
- src/cyberpunks/operations/planner.py
- src/cyberpunks/channels/conversation.py

## Cerințe

1. Construiește AuthorizedSnapshot numai din contextul complet furnizat de operațiile autentificate. Păstrează restricțiile clientului și tehnicianului și permisiunile dispecerului. Nu citi din scoped_projection și nu extinde drepturile când o selecție nu se găsește.

Sursa OperationsService.context conține deja toate lucrările autorizate. Refolosește această citire și fă selecția explicită human_review pentru coada de revizuire. Nu construi încă un încărcător sau API paginat dacă nu este necesar. Dacă parcurgi lista în blocuri, dovada acoperirii se referă la aceeași sursă completă. Traseul complet al tehnicianului trebuie verificat ca aprobat; simpla sa prezență în context nu ajunge.

2. Leagă snapshotul de organizație, utilizator, apartenență, scenariu, versiunea operațională completă, versiunile cazurilor și predicțiilor și data istorică. Definește selecția exactă a cozii fără a confunda limita revizuirii umane cu limita de citire.

3. Asigură ordinea stabilă și acoperirea tuturor paginilor, inclusiv cazuri fără predicții. O schimbare de versiune sau revocarea apartenenței în timpul citirii produce refuz ori restart controlat, nu un amestec de stări.

4. Oferă verificarea curentă a domeniului și versiunii înaintea utilizării rezultatului. Nu apela metoda command ca observație pasivă, deoarece poate reconcilia. Nu dubla calculul autoritar al versiunii dacă există deja.

## Verificare și predare

Pe copia completă verifică egalitatea identificatorilor cu sursa autorizată, trei roluri, altă organizație/scenariu, revocare, modificarea datelor între pagini, date istorice și lipsa efectelor operaționale. Predă punctele de conectare pentru 00.
