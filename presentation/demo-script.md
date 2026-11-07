# Scriptul demo-ului live: 5 minute + 2 minute de întrebări

Varianta 1 (schiță, 7 nov., 13:40). Se rafinează după ce există consola cu date reale și cifrele din `reports/`. Cine vorbește: Teo (T) conduce; colegii (Tudor, Eden) iau câte o parte, de stabilit cu Teo. Ecranul: laptopul pe proiector, 1920×1080, consola în modul `/demo`, slideurile în alt tab.

## Înainte de demo (cu 15 minute înainte)

- API-ul pornit (`make api`, portul 8710) și consola (`make web`, portul 3710), scenariul `demo-vara` (8 iulie 2025) încărcat și rulat o dată.
- Tab 1: filmul de 30 s (`presentation/exports/tura-de-maine-30s.mp4`), pe ecran complet, cu sunet.
- Tab 2: consola, pe "Planul de mâine". Tab 3: slideurile (PDF). Tab 4: înregistrarea de rezervă (`presentation/exports/demo-rezerva.mp4`).
- Sunetul laptopului verificat pe sala lor. Notificările oprite. Bateria la priză.

## Cronometrul

| Când | Cine | Ce se arată | Ce se spune (pe scurt) |
|---|---|---|---|
| 0:00-0:30 | T | Filmul de 30 s | Nimic peste film. |
| 0:30-1:00 | T | Slide 2 (problema) | "PPC ne-a spus la workshop: 2 milioane de contoare, 192 de milioane de citiri pe zi. Și în temă: un scor de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață. Noi am construit pasul ăsta." |
| 1:00-1:20 | T | Slide 3 (8 iulie 2025) | "Am ales o zi reală: vijelie cu cod roșu în Banat, caniculă la București, contoare suspecte. Aceleași echipe pentru toate." |
| 1:20-2:20 | T | Consola: butonul "Rulează agentul", pașii Perceive, Estimate, Decide, Act cu timpii reali, apoi planul pe hartă | "Agentul citește datele, cele trei modele ale noastre estimează, stratul de decizie din cod alege, iar agentul face planul: trasee, ordine de lucru, alerte." |
| 2:20-3:00 | T | Detaliul unei lucrări A: factorii, cazul similar, regula și pragul, ID-ul predicției; apoi bilanțul postului | "De ce merge echipa aici: nouă zile cu consum zero, iar bilanțul postului confirmă că lipsește energie. Deci nu e o deplasare degeaba." |
| 3:00-3:30 | T | Un post C cu scara de soluții | "Aici tensiunea trece de 1,10. Agentul alege cea mai ieftină soluție care chiar ajunge: mută trei case pe altă fază. Aceeași cauză a găsit-o și bilanțul." |
| 3:30-4:00 | T | Coada "Nu sunt sigur": aprobă o lucrare, planul se refăce | "Când modelul nu e sigur, nu decide singur. Dispecerul aprobă, și decizia lui intră în jurnal." |
| 4:00-4:40 | T | Slide 5 sau 8 (cifrele față de baseline) | Cifrele din `reports/`, citite exact de pe slide, și comanda din README care le refăce. |
| 4:40-5:00 | T | Slide 11 (ce trebuie confirmat cu PPC), apoi titlul | "Ce avem nevoie de la voi ca să meargă pe date reale: contoarele de bilanț și lista client → post. Mulțumim." |

## Planul B

- Pică API-ul: consola citește singură instantaneul din `outputs/demo/` (rezerva e construită de firul UI); spunem "rulăm pe instantaneul salvat al aceleiași zile".
- Pică toată consola sau laptopul: tab 4, înregistrarea de rezervă de 4-5 minute, iar Teo vorbește peste ea după același tabel.
- Pică sunetul la film: filmul merge și fără sunet (textul poartă povestea).
- Rămânem fără timp: sărim peste 3:00-3:30 (scara de soluții) și o păstrăm pentru întrebări.

## Întrebări probabile (2 minute): răspunsuri scurte

- "Cum ați separat setul de test?" A: (din `reports/A/metrics.json`, câmpul `split`); B: ani nevăzuți și state nevăzute; C: rețele nevăzute.
- "Datele sunt reale?" Vremea și ziua sunt reale; contoarele și rețelele sunt publice (SGCC, Londra, SimBench) sau sintetice, etichetate peste tot.
- "Ce face LLM-ul?" Nimic din decizie: deciziile vin din modele și din reguli scrise în cod; textele vin din șabloane cu cifrele verificate în cod.
- "Ce se întâmplă când modelul greșește?" Pragurile sunt alese pe cost, incertitudinea mare merge la om, iar verdictul echipei după vizită devine etichetă nouă.
- "Cât costă să rulați asta?" Rulează local, fără API plătit; pe platforma lor ar intra în Spark pe EMR, lângă calculul zilnic existent.
- "Ce vă trebuie de la PPC?" Contoarele de bilanț, lista client → post, istoricul de avarii și de intervenții pentru calibrare.
