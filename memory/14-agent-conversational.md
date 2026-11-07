# Agent conversațional pentru trei tipuri de cont

## Cererea lui Teo

Consemnat pe 7 noiembrie 2026, la 22:43, București. Teo a cerut un plan complet pentru agentul conversațional Daybreak, cu toate cele trei perspective discutate: tehnician, dispecer și client. Vrea testarea din trei tipuri de cont, nu doar o conversație demonstrativă într-un singur cont.

Teo a precizat că sunt permise Codex CLI și alte LLM-uri dacă sistemul folosește modelul ML propriu, rulat local. Vocea prin ElevenLabs este direcția explorată. Solicitarea din această etapă este realizarea planului; implementarea și activarea unor servicii externe nu au fost cerute în acest mesaj.

## Planul rezultat

Documentul complet: [Plan pentru agentul cu trei conturi](../docs/PLAN-AGENT-CONVERSATIONAL.md).

- Catalog de 68 de cazuri pe roluri și 12 situații comune, cu 16 cazuri principale P0 pentru prima versiune.
- Același caz și aceeași stare operațională pentru cele trei roluri, cu drepturi verificate pe server.
- Operatorul de relații cu clienții este propus ca vedere restrânsă a dispecerului, fără al patrulea tip de cont.
- Propunere tehnică: voce în browser, trei configurații conversaționale, acțiuni comune pentru text/voce/butoane și modele locale. Configurațiile și infrastructura sunt propuneri, nu funcții livrate.
- Confirmarea constatării nu înseamnă repararea problemei. Fără acces nu înseamnă defect absent și nu devine automat etichetă negativă pentru antrenare.
- Planul include etape, buget orientativ, 40 de probe de verificare și demo cu trei sesiuni independente.

## Situație verificată în cod

Conturile existente nu au încă rolurile operaționale și legăturile autorizate cont-punct sau cont-echipă. Câmpul de profil team este editabil și nu trebuie folosit drept permisiune. Aprobările personale din KV sunt distincte de aprobările reale ale planificatorului.

API-ul existent poate înregistra constatări și aprobări, dar aceste operații nu sunt încă legate de cele trei roluri. Configurația Cloudflare folosește planul salvat, fără serviciul Python local. Integrarea ElevenLabs, accesul efectiv la cont și minutele disponibile nu au fost testate.

## Limitele acestei etape

Au fost redactate și verificate documentele. Nu au fost create conturi, schimbate secrete, pornite apeluri, publicată aplicația sau implementate noile funcții. Datele și identitățile de test din plan sunt propuse și etichetate ca sintetice. Interfața rămâne în engleză, conform deciziei deja luate de Teo.
