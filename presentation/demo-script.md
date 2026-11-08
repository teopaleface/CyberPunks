# Scriptul demo-ului live: 5 minute + 2 minute de întrebări

Varianta finală, 8 nov. 2026, 08:30. Produsul: **Daybreak**. Prezintă Teo (T); colegii (Tudor, Eden) răspund la întrebările pe partea lor. Ecranul: laptopul pe proiector, 1920×1080.

## Fișierele (toate pe laptopul lui Teo)

| Ce | Unde |
|---|---|
| Filmul pentru sală (52,9 s, cu „POWER”, doar local) | `presentation/exports/local/daybreak-film-power.mp4` |
| Filmul versionat (fără „POWER”, vocea și efectele; e cel predat) | `presentation/exports/daybreak-film.mp4` |
| Slideurile (16 pagini: 1-11 principale, 12-16 anexă) | `presentation/exports/daybreak-slides.pdf` |
| Înregistrarea de rezervă a consolei (fără sunet) | `presentation/exports/local/daybreak-demo-rezerva.mp4` |

## Înainte de demo (cu 15 minute înainte)

- API-ul pornit (`make api`, portul 8710) și consola (`make web`, portul 3710), scenariul `demo-vara` (marți, 8 iulie 2025) încărcat și rulat o dată.
- Tab 1: filmul pentru sală, pe ecran complet, cu sunet (verificat volumul pe boxele sălii). Tab 2: consola, pe planul de mâine. Tab 3: slideurile (PDF). Tab 4: înregistrarea de rezervă.
- Notificările oprite, laptopul la priză, ecranul nu intră în repaus.

## Cronometrul

| Când | Ce se arată | Ce se spune (pe scurt) |
|---|---|---|
| 0:00-0:55 | Filmul (52,9 s) | Nimic peste film: are voce și text pe ecran. |
| 0:55-1:25 | Slide 2 (192 de milioane de citiri pe zi) | „PPC are peste 2 milioane de contoare și 192 de milioane de citiri pe zi. Dar un scor de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață. Daybreak face pasul ăsta.” |
| 1:25-1:45 | Slide 4 (8 iulie 2025) | „Am luat o zi reală: vijelie cu cod roșu în Banat, soare puternic la prânz, contoare suspecte. Aceleași echipe pentru toate.” |
| 1:45-2:45 | Consola: butonul care rulează agentul, apoi planul pe hartă | „Daybreak citește datele, cele trei modele ale noastre estimează, regulile din cod aleg, iar la final iese planul: traseul și ordinea lucrărilor pentru fiecare echipă, alertele, mesajele.” |
| 2:45-3:25 | Detaliul unei lucrări la un contor: factorii, cazul asemănător, regula și pragul | „De ce merge echipa aici: factorii în cuvinte simple, un caz asemănător din istoric și regula care a decis. Nu e o cutie neagră.” |
| 3:25-3:55 | Coada „Nu sunt sigur”: aprobă o lucrare | „Când nu e sigur, Daybreak nu decide singur. Dispecerul aprobă sau respinge, iar decizia lui intră în jurnal.” |
| 3:55-4:35 | Slide 9 (+49%), apoi slide 6 (modelele față de metoda simplă) | Cifrele citite exact de pe slide: „În 30 de zile simulate, cu aceleași echipe: 49% mai multă valoare, 31,6% mai puțini kilometri, 37% vizite degeaba față de 63%.” |
| 4:35-5:00 | Slide 12 (ce vrem să confirmăm cu PPC), apoi titlul | „Ca să meargă pe date reale ne trebuie contoarele de bilanț din posturi și lista client → post. Mulțumim.” |

## Cifrele (aceleași ca pe slideuri, din `reports/`)

- Agentul, 30 de zile simulate, date sintetice, față de „primul venit, primul servit” (cea mai bună strategie simplă): +49% valoare netă; 10.565 km față de 15.439 (-31,6%); 37% vizite degeaba față de 63%; 46 de cazuri trimise la om. Sursa: `reports/planner/agent_eval.json`.
- A (contoare): pe problemele subtile 0,62 față de 0,02 la regula simplă VEE; pe SGCC, cu etichete reale, 0,80 față de 0,11. NU spunem 1,00 (vine din defectele evidente de pe Londra).
- B (furtună): PR-AUC 0,28 față de 0,15 la climatologie.
- C (tensiune): eroarea la tensiunea maximă 0,0054 pu față de 0,0227; găsește 87% din depășiri față de 26%.
- Bilanțul pe post: F1 la diagnosticul cauzei 0,71 față de 0,48.
- Atenție: filmul spune „556 problems” (consola de ieri); planul de azi pentru 8 iulie are alt număr de lucrări. Live spunem doar ce e pe ecran („sute de lucrări”).

## Planul B

- Pică API-ul: consola merge pe instantaneul salvat din `outputs/demo/`; spunem „rulăm pe instantaneul salvat al aceleiași zile”.
- Pică toată consola: tab 4, înregistrarea de rezervă, iar Teo vorbește peste ea după același tabel (de la 1:45).
- Pică sunetul: filmul are text pe ecran; mergem mai departe.
- Pică filmul pentru sală: varianta versionată `presentation/exports/daybreak-film.mp4` (aceeași imagine, fără muzică).
- Rămânem fără timp: sărim peste detaliul lucrării (2:45-3:25) și îl păstrăm pentru întrebări.

## Întrebări probabile (2 minute): răspunsuri scurte

- „Cum ați separat setul de test?” A: date nevăzute la antrenare (vezi `reports/A/metrics.json`); B: ani și zone nevăzute; C: rețele nevăzute. Comanda care reface fiecare cifră e în slide 15 și în README.
- „Datele sunt reale?” Ziua și vremea sunt reale (8 iulie 2025). Contoarele și rețelele vin din seturi publice (SGCC, Londra, SimBench) sau sunt sintetice, etichetate peste tot. Evaluarea agentului e o simulare de 30 de zile.
- „Ce face AI-ul generativ?” Nimic din decizie: deciziile vin din modele și din reguli scrise în cod; textele vin din șabloane cu cifrele verificate în cod. Vocea și imaginile din film sunt generate (etichetat).
- „Ce se întâmplă când modelul greșește?” Pragurile sunt alese pe cost, incertitudinea mare merge la dispecer, iar verdictul echipei după vizită devine etichetă nouă.
- „Cât costă să rulați asta?” Rulează local (LightGBM, OR-Tools), fără API plătit; pe platforma PPC ar intra lângă calculul zilnic existent.
- „Ce vă trebuie de la PPC?” Contoarele de bilanț, lista client → post, istoricul de avarii și de intervenții pentru calibrare.
