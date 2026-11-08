# 03 Rapoarte vizuale și WhatsApp

Citește AGENTS.md, memory/INDEX.md și docs/PLAN-AGENTIC.md. Păstrează lucrul concurent și ramura Teo. Editează numai fișierele rezervate în manifestul compact. Lucrează pe copia completă izolată, fără secrete sau setări de trimitere; datele adăugate sunt sintetice. Nu reporni servicii, nu modifica conturi și nu trimite mesaje sau apeluri externe. Coordonatorul gestionează Git și integrarea. Predă fișierele, probele exacte și ce rămâne netestat.

Modelele proprii și regulile existente susțin deciziile. Numai Confirm din aplicația autentificată execută schimbări operaționale. Drepturile și versiunile se reverifică la utilizare. Constatarea nu declară reparația. O citire de comandă care poate reconcilia nu este un instrument pasiv.

## Sarcina

Construiește rapoarte pentru dispecer, tehnician și client din structura verificată comună. Pentru început lucrează cu exemplele sanitizate ale contractului; integrarea folosește sursa completă. Filtrează câmpurile după rol și păstrează data istorică, generarea, versiunea și starea propus/aprobat.

Generează HTML din șabloane fixe în designul PPC existent, apoi PNG paginat și text accesibil. Escapează textele și blochează scripturi, rețea și căi arbitrare. Verifică lizibilitatea la 360 px. Persista octeții exacți și hash-ul fiecărei pagini înainte de livrare.

Transportul folosește registrul Meta existent, extins prin coordonator pentru identificatori separați per pagină. Verifică destinatarul și fereastra înaintea trimiterii; apelul singur nu deschide fereastra. Timeoutul necunoscut nu provoacă retrimitere. Testele transportului sunt simulate, fără tokenuri. Predă imaginile exacte inspectate și extensiile necesare în transportul existent. Dacă timpul scade, păstrează raportul textual și amână PNG-ul.

## Fișiere rezervate

- src/cyberpunks/agentic/report_data.py
- tests/agentic/test_report_data.py
- src/cyberpunks/agentic/report_templates.py
- src/cyberpunks/agentic/templates/**
- tests/agentic/test_report_templates.py
- src/cyberpunks/agentic/png_renderer.py
- tests/agentic/test_png_renderer.py
- src/cyberpunks/agentic/image_delivery.py
- tests/agentic/test_image_delivery.py
