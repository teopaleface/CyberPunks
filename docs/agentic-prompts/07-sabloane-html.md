# 07 Șabloanele HTML

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se trimite după conținutul integral din COMMON.md. Se aplică interfața agentic-v1 înghețată de 01.

## Rezultat cerut

Creează trei rapoarte lizibile pe telefon, din șabloane fixe în stilul PPC existent.

## Fișiere proprii

- src/cyberpunks/agentic/report_templates.py
- src/cyberpunks/agentic/templates/**
- tests/agentic/test_report_templates.py

Toate celelalte fișiere sunt doar pentru citire. Modificările necesare în fișierele integratorului se predau în mesaj.

## Context de citit la nevoie

- web/components/workspace/workspace.css
- web/components/workspace/proposal-form.css
- docs/PLAN-AGENTIC.md

## Cerințe

1. Consumă exclusiv ReportData din 01. Implementează variantele pentru traseu, coada dispecerului și starea clientului. Refolosește culorile și ordinea vizuală ale consolei existente, fără un produs sau branding separat.

2. HTML-ul și stilurile sunt locale și determinate de template. Escapează textele. Nu accepta HTML, scripturi, imagini remote, adrese sau CSS liber din conversație. Oferă text accesibil separat.

3. Proiectează pentru citire la 360 px. Pentru liste lungi produce pagini sau blocuri paginate fără pierderea vreunui caz. Pune data scenariului, generarea, versiunea, starea și eticheta sintetic/istoric unde este necesar. Nu desena un buton care sugerează confirmare funcțională în PNG.

4. Poți porni cu exemplele de contract sanitizate din 01; după 06 integrează date reale autorizate din copia completă. Nu folosi mockupurile istorice drept valori operaționale.

## Verificare și predare

Testează escaping, conținut lung, diacritice, date lipsă și acoperirea listei între pagini. Inspectează randările la 360 și 728 px cu unealta disponibilă pentru HTML local. Predă HTML-ul exact și imaginile de verificare în mesaj sau prin link accesibil, cu starea datelor declarată.

