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

## Situație înainte de implementare

Conturile existente nu au încă rolurile operaționale și legăturile autorizate cont-punct sau cont-echipă. Câmpul de profil team este editabil și nu trebuie folosit drept permisiune. Aprobările personale din KV sunt distincte de aprobările reale ale planificatorului.

API-ul existent poate înregistra constatări și aprobări, dar aceste operații nu sunt încă legate de cele trei roluri. Configurația Cloudflare folosește planul salvat, fără serviciul Python local. Integrarea ElevenLabs, accesul efectiv la cont și minutele disponibile nu au fost testate.

## Limitele etapei de plan

Au fost redactate și verificate documentele. Nu au fost create conturi, schimbate secrete, pornite apeluri, publicată aplicația sau implementate noile funcții. Datele și identitățile de test din plan sunt propuse și etichetate ca sintetice. Interfața rămâne în engleză, conform deciziei deja luate de Teo.

## Implementare și probe, 7-8 noiembrie

Teo a aprobat ulterior implementarea în paralel, Codex pe abonamentul existent, trei conturi, vocea din site și WhatsApp cu text și note vocale. Implementarea locală este separată de site-ul public: workspace pe 3870, API privat pe 8720, intrare exclusiv Meta pe 8721. Datele sunt o copie completă izolată, cu 689 de lucrări și predicții reale ale modelelor locale. Conturile, legăturile și sesizările demonstrative sunt sintetice. Scenariul istoric este 8 iulie 2025.

Cele trei conturi au drepturi verificate pe server. Probele reale au parcurs sesizare confirmată de client, aprobare prin planificator, constatare a tehnicianului și stare comună, fără declararea reparației. Conversația Codex a fost verificată pe toate rolurile. Există propuneri confirmate explicit, versiuni, deduplicare și recuperarea autorizată a comenzilor. Propunerile pornite în WhatsApp se pot găsi în Draft requests sau deschide printr-un link care păstrează identificatorul prin autentificare. Clientul vede rezultatul constatării, fără identificatori interni ai verdictului.

Cheia ElevenLabs existentă a fost găsită în configurația privată existentă. Teo a autorizat adăugarea unui singur IP; lista și accesul API au fost verificate separat după salvare. Trei agenți privați au fost creați și verificați. Două probe au parcurs ASR, agentul vocal, unealta din client, Codex și răspunsul audio real. Proba finală a păstrat textul API identic; a durat 13,15 secunde pentru conversație și 15,44 secunde până la primul audio după întrebare. Pronunția exactă, microfonul și difuzorul fizic rămân neverificate.

Teo a creat numărul de test Meta +1 555 154 5755 și a confirmat parola Facebook în Helium pentru accesul privat la App Secret. Callbackul HTTPS și asocierea aplicației Meta au fost salvate și recitite. Două răspunsuri reale Codex au fost livrate și citite în WhatsApp, către singurul expeditor verificat, asociat tehnicianului sintetic. O întrebare intermediară despre motivul opririi a fost refuzată de verificarea datelor; retrimiterea a trecut. Codul are acum un răspuns sigur după eșecurile conversaționale, fără afirmații neverificate. Această ramură de eroare este testată simulat.

Notele vocale sunt implementate și testate cu furnizori simulați, inclusiv răspuns OGG/Opus și păstrarea textului dacă audio eșuează. Teo a precizat că nu poate înregistra acum; nu s-a verificat o notă vocală reală prin Meta. Nu îi cerem repetat înregistrarea. Audio este activat numai pentru expeditorul verificat care a cerut această funcție.

Tunelul și tokenul Meta sunt temporare. Procesele locale trebuie să rămână pornite; site-ul nu a fost publicat. P1/P2 din catalog nu sunt toate implementate. Pornire, verificări și limite: [RUNBOOK](../docs/operations/RUNBOOK.md). Secretele și identificatorii personali ai expeditorului rămân numai în fișiere private ignorate de Git, fără valori în memorie.

## Conturi nominale, 8 noiembrie

Teo a cerut explicit aceleași trei conturi local și pe live: dispecer@daybreak.ro, tehnician@daybreak.ro și client@daybreak.ro, cu parola comună stabilită de el, păstrată numai privat. Conturile au fost configurate cu rolurile corespunzătoare, păstrând identificatorii și asocierea WhatsApp. Formularul a fost corectat pentru autentificarea cu parola existentă, păstrând minimul obișnuit la creare/resetare. Toate cele șase autentificări din formular, trei roluri în două medii, au trecut. Publicare din copie izolată a sursei comise, versiunea 2c071473-84fb-4923-a5e7-2135d343fad1. Serviciul operațional rămâne local.
