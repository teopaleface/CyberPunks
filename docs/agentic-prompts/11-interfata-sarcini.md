# 11 Interfața sarcinilor în conversație

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Arată progresul, recomandările și rapoartele în conversația principală existentă, pentru cele trei roluri.

## Fișiere proprii

- web/components/agentic/**
- web/lib/agentic/use-task.ts
- web/lib/agentic/use-task.test.tsx

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- web/AGENTS.md
- web/components/workspace/workspace.tsx
- web/components/workspace/main-conversation.tsx
- web/components/workspace/proposal-form.tsx
- web/components/workspace/workspace.css
- web/lib/operations/client.ts

## Cerințe

1. Creează componente noi consumate prin proprietăți și callbacks tipizate din 01. Nu modifica Workspace, istoricul, formularele sau navigația existentă; 00 face legăturile. Citește ghidul Next relevant instalat înainte de cod.

2. Arată starea taskului, acoperirea analizei și fiecare recomandare, cu motiv și blocaj. Lista lungă poate fi compactă, dar toate cazurile rămân accesibile. Rezultatul parțial nu primește eticheta complet.

3. Separă clar propunerea, aprobarea și efectul recitit. Butonul de revizuire deschide formularul existent; componentele noi nu confirmă automat. Arată planul vechi, expirarea sau necesitatea altei aprobări.

4. Hook-ul folosește clientul 12, oprește citirea la demontare/schimbarea contului și are polling limitat/backoff. Schimbarea rolului, scenariului sau sesiunii șterge starea privată. Păstrează engleza interfeței, conversația în limba utilizatorului, Light/Dark și designul PPC.

## Verificare și predare

Probe de componente și hook pentru progres, 25 de rezultate, eroare, versiune veche, sesiune expirată și schimbarea contului. Verifică tastatură și ecran de 360 px în build izolat, fără a modifica portul sau cache-ul demo. Predă componentele și callbacks-urile exacte către 00; o probă cu client simulat nu dovedește integrarea HTTP.
