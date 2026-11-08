# 15 Revizie după standarde

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Revizuiește read-only implementarea integrată față de regulile repo-ului și disciplina modulelor.

## Fișiere proprii

Acest job este read-only și nu deține fișiere pentru editare.

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- AGENTS.md
- web/AGENTS.md
- docs/agentic-prompts/COMMON.md
- docs/agentic-prompts/INTERFACES.md

## Cerințe

1. Primești de la 00 punctul fix de bază și capul exact sau un diff stabil. Verifică numai schimbările acelui punct. Nu folosi un worktree care conține altă versiune și nu începe review-ul pe fișiere aflate încă în editare.

2. Verifică păstrarea muncii concurente, fișierele deținute, reutilizarea autentificării/confirmării, contractele, dependențele și compatibilitatea traseelor existente. Identifică duplicate de logică autoritară sau efecte ascunse sub nume de citire.

3. Citește probele relevante și verifică dacă susțin comportamentul livrat. Nu deduce validare live din teste simulate sau build. Nu edita cod și nu lansa alți agenți.

4. Returnează doar defecte concrete cu prioritate, fișier/linie, declanșator și impact. Separă cerințele blocante de sugestiile opționale. Dacă nu găsești defecte, spune ce ai verificat și care probe nu au putut fi inspectate.

## Verificare și predare

Raport în mesaj pe punctul fix indicat, fără fișiere noi, schimbări Git, procese sau servicii externe. Pentru runda nouă, 00 îți trimite din nou brief-ul și istoricul observațiilor printr-o nouă delegare.

