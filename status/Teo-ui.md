# Status: Teo-ui
Actualizat: 2026-11-07 14:40
Milestone curent: M3 (M0 13:50, M1 13:55, M2 14:40)
Gata de merge: da (commit a68f2aa: M2, toate ecranele de bază pe API și pe instantaneu, modul /demo)

## Făcut
- 12:45 Citite instrucțiunile, memoria, planul, contractele; `uv sync` și `make check` trec.
- 12:50 Paleta PPC verificată din CSS-ul site-urilor (ppcgroup.com `#000f1e`, `#00a3e0`, `#fa4616`; ppcenergy.ro `#163fe8`; font PingLCG, proprietar, nefolosit). Folosim doar familia de culori.
- 12:52 OpenFreeMap merge fără cheie (positron, bright, liberty, dark, fiord; dale peste București; glife cu ș/ț).
- 12:53 Fonturi verificate pe fișiere (cmap): ș/ț cu virgulă în toate cele 34 de candidate.
- 13:00 Logo de la Codex (3 concepte, PNG + SVG), ales „răsărit pe traseu”; favicon `web/app/icon.svg`.
- 13:05 Schelet Next.js 16.4 + React 19.3 + Tailwind 4 + shadcn/ui + MapLibre 6.16 + Recharts 3.10 (bun); stratul de date API → instantaneu demo → fixture-uri, cu proveniența afișată.
- 13:10 Trei machete pe date reale, arătate lui Teo; aleasă „Panou”.
- 13:50 M0 gata:
  - tema Panou (gri în repaus, culoare doar pentru sursă și pentru „decide un om”), Archivo variabil pe lățime;
  - antetul: ecranele, scenariul, proveniența („Date sintetice în 5 din 7, Agentul, în direct”), „Rulează agentul” cu pașii Perceive → Estimate → Decide → Act și timpii reali de la `POST /run` (fără timpi inventați dacă API-ul nu răspunde);
  - ecranul Planul de mâine: cifrele zilei, harta cu vederi pe regiuni (Toată zona, Muntenia Sud, Dobrogea, Banat), harta mică a zonei RE din conturul județelor, linia de timp a echipelor ca schemă monofilară (cu ferestrele de furtună și de tensiune), coada „Nu sunt sigur” cu Aprobă/Respinge/Amână legate la `POST /review`, alerta principală, detaliul lucrării selectate (scor și interval față de prag, factori, caz similar, regula cu valoarea față de cost, urmărirea până la predicție și model).
- 13:51 Merge Teo (extinderea bilanț + scara de soluții): tipurile regenerate, cele 6 acțiuni noi au etichete, tipuri TS pentru `extra.remedy_options` și `extra.fusion`.

- 13:55 M1: detaliul lucrării (`/lucrari/[id]`): graficul pe sursă (A consum cu zilele de zero; B rafale și risc în două grafice, cu fereastra furtunii și pragul; C tensiune cu P10–P90 și limita 1,10), factorii SHAP, cazurile similare, decizia cu regula și pragurile în cuvinte simple, valoarea față de cost, încrederea, urmărirea până la predicție/model/jurnal, datele de intrare, scara de soluții C. Seriile cad pe instantaneu și pe exemplele din fixture-uri.
- 14:00 Testat pe planul real (316 lucrări, 9 trasee, 61 la om) citit din outputs/ al checkout-ului principal (`DEMO_DIR`): harta pe două straturi (markeri cu literă doar pe trasee, restul puncte MapLibre), încadrare pe trasee, etichete care nu se suprapun.
- 14:05 Posturile de transformare: harta verde/galben/roșu după lei pe lună (modul „Posturile”), pagina postului (`/posturi/[id]`) cu bilanțul „ieșit din post” față de „suma clienților”, cauza, contoarele de pe post cu confirmarea din bilanț, tensiunea și scara de soluții. Sursa: `GET /posts`, apoi `posts.json` din instantaneu, apoi derivare din lucrări (contoarele A × scor, marcată ca estimare).
- 14:15 Modul de prezentare `/demo`: tema închisă cu harta de noapte (cererea firului de prezentare), 5 scene cu subtitrare (planul; Nu sunt sigur; de ce a decis agentul; echipa înainte de furtună; ziua echipelor), ← → / 1–5 / `?scena=N` / `?auto=1`, fără insigna Next în capturi.
- 14:20 Ecranele Modele (A, B, C față de baseline cu cifrele reale din rapoarte, analiza erorilor, agentul față de strategii simple, comenzile de reproducere) și Nu sunt sigur (61 de lucrări, cu Aprobă/Respinge/Amână și notă), făcute de un subagent după convențiile din `web/design/CONVENTIONS.md`.
- 14:10 Aprobarea listei echipelor, ordinele de lucru PDF (`/ordine/<echipă>`, de la API sau din instantaneu), lei recuperați (din aprobările omului). Reparat: deciziile omului trimit acum scenariul la `POST /review`.

- 14:40 M2 gata: ecranele Jurnal (filtre, praguri, urmărire, descărcare JSONL) și Alerte și mesaje (subagent); posturile folosesc bilanțul real (lei pe lună, cauza); test de fum pentru toate ecranele (`make web-smoke`, 12 ecrane); 23 de teste (`make web-test`).

- 14:50 Pagina planului mai ușoară: 3,05 MB → 1,98 MB (214 KB gzip) cu 556 de lucrări; detaliile lucrării se încarcă la selecție.
- 14:55 Rezerva fără API verificată cu testul de fum: (1) API oprit, fără instantaneu → „Date de test”, 12/12 ecrane merg; (2) API oprit, cu instantaneul planificatorului (`DEMO_DIR=…/outputs/demo`) → „Ultimul plan salvat”, 12/12 ecrane merg, ordinul de lucru PDF vine din instantaneu.

## Urmează
- M3: audit `impeccable`, rezerva fără API verificată (API oprit), pagina principală mai ușoară (detaliile lucrărilor la cerere), un review independent cu Codex.
- Scara de soluții C și bilanțul apar automat când firele C și bilanț pun `extra.remedy_options` și lucrările `A_bilant` (componentele sunt gata).
- Până la 01:00: `/demo` pentru înregistrări, cu varianta întunecată cerută de firul de prezentare.

## Blocaje
- niciunul

## Cereri către orchestrator
- (14:40) Către planificator (texte): zecimale cu punct în mesaje și alerte („9.1 ore”, „~38.9 kWh”), plural greșit („1 lucrări așteaptă”, „72 lucrări”: corect „1 lucrare”, „72 de lucrări”), data „marți 08.07.2025” în mesaje (în română: „marți, 8 iulie”). Interfața le arată așa cum vin.
- (14:35) Către firul bilanț: lucrările `A-<data>-PT-*` au `extra.series_ref = outputs/series/<s>/A-<data>-PT-*.json`, dar fișierele nu există (în `outputs/series/demo-vara/` sunt doar seriile C ale posturilor). Pagina postului are graficul „ieșit din post” (`value`) față de „suma clienților” (`expected`) gata; îi lipsește doar seria. Contractul `Series` cu `flag: "lipsa_peste_normal"` pe zilele cu lipsă peste normal.
- (14:25) Către firul A (date): în `explanation.top_factors[].label_ro` apar procente absurde („Consumul de noapte a crescut cu 18273047% față de istoric”, împărțire la aproape zero) și zecimale cu punct („0.46 din medie”, „9.1 ore”). Interfața le afișează acum protejat („peste 1.000%”, virgulă), dar textul ar trebui reparat la sursă: plafonare la ±1.000% sau formulare relativă („de la aproape zero”), format românesc. La fel în `reports/B/error_analysis.md` („0.16”).
- (14:10) Către planificator: `POST /api/plan/approve {scenario, plan_id, approver, note}` → `AuditRecord` (actor human, action „plan_approved”), pentru butonul „Aprobă lista echipelor”. Până atunci interfața păstrează aprobarea local și spune asta.
- (14:10) Către planificator: în instantaneul `outputs/demo/plans/<s>/` și `posts.json` (forma de la `GET /posts`), ca harta posturilor să meargă fără API.
- (14:10) Planul real stă acum doar în outputs/ al checkout-ului principal; API-ul de pe 8710 (worktree-ul planificatorului) servește încă planul de test cu 7 lucrări. Pentru demo, instantaneul `outputs/demo/` cu planul real ar fi rezerva sigură.
- Răspuns la cererea firului de prezentare (14:05): varianta întunecată pentru `/demo` costă puțin, culorile închise sunt deja validate în temă (A `#3B82F0`, B `#B84FC0`, C `#C4880A` pe `#0F1D2B`), iar harta are stilul `dark`. O fac până la 01:00, împreună cu cardul „Nu sunt sigur” vizibil pentru captură.
- Către planificator: `GET /api/posts` (registrul posturilor cu lei pierduți pe lună și starea verde/galben/roșu) ar scuti interfața de calcule; până atunci fac un exemplu local, etichetat sintetic.
- Rezolvate de orchestrator la 13:20: seriile de exemplu, planul complet, `depart_at`/`return_at`, `visit_cost_lei`, structura `outputs/demo/`, `scenario_id`, jurnalul.

## Cum se rulează (comenzile exacte)
- `make web` → http://localhost:3710 (cu API-ul pe 8710 dacă rulează; altfel instantaneul demo sau fixture-urile, automat)
- `make web-test` (17 teste, stratul de date), `cd web && bun run lint`, `cd web && bunx tsc --noEmit`
- Forțarea sursei: `DATA_SOURCE=fixtures make web` (sau `demo`, `api`); alt API: `API_BASE=http://127.0.0.1:8710/api`.

## Cifre (doar din scripturi, cu comanda)
- niciuna (interfața doar afișează cifrele firelor; culorile surselor validate cu `node validate_palette.js` din abilitatea dataviz)

## Decizii (cu ora)
- 14:30 Test de fum `make web-smoke` (încarcă toate ecranele pe consola pornită și cade la orice eroare de randare): `tsc` nu prinde funcțiile de client chemate pe server, testul da.
- 14:00 Harta pe două straturi: markeri DOM cu literă doar pentru opririle din trasee și selecție; celelalte lucrări (sute) sunt puncte într-un strat MapLibre, cu informații la trecerea mouse-ului. Altfel planul real e ilizibil.
- 14:05 Culorile posturilor (verde sub 150, galben 150–600, roșu peste 600 lei pe lună) sunt praguri de afișare, scrise ca atare în legendă; culoarea de la API are prioritate.
- 12:48 Faza 0 cu subagenți în paralel (schelet, logo, 3 machete).
- 12:50 Trimiterea la PPC rămâne discretă: familia bleumarin + albastru + o culoare caldă, fără valorile lor exacte și fără fontul PingLCG.
- 12:54 Logoul: Codex desenează doar semnul; numele îl scriem cu fontul interfeței (diacritice sigure).
- 13:00 Culorile surselor validate pentru daltonism: deschis A `#2C6FD9`, B `#A23C9E`, C `#D99100`; închis A `#3B82F0`, B `#B84FC0`, C `#C4880A`. Violetul inițial pentru B pica (ΔE 0,9 față de albastru la deuteranopie).
- 13:14 Direcția Panou (HMI de dispecerat, temă deschisă): limba dispecerilor, lizibilă pe proiector; de la „Noaptea” iau ferestrele de timp, de la „Mersul” orele mari.
- 13:35 Harta are vederi pe regiuni, pentru că scenariul demo (8 iulie 2025) are lucrări B în Banat, departe de București; implicit arată regiunea cu cele mai multe opriri.
- 13:40 Orele de plecare și de întoarcere: din `depart_at`/`return_at` când există, altfel estimate din km (marcate „cca”).
- 13:45 Worker-ul MapLibre se servește static din `web/public/maplibre/` (copiat la `dev`/`build`, nu stă în git), pentru că bundler-ul Next nu-i rezolvă calea.
