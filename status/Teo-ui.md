# Status: Teo-ui
Actualizat: 2026-11-07 19:10
Milestone curent: designul „Noapte” cerut de Teo la 18:55 (14 imagini), aplicat pe toate ecranele; lucru în curs
Gata de merge: nu încă (redesign în lucru; ultima versiune bună: 63fac7a)

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

- 14:58 Consola se adaptează la proiectoare și laptopuri de 1280–1600 px (antet, cifre, hartă, linia de timp), verificat cu capturi la 1280×800, 1440×900, 1920×1080.
- 15:00 Scara de soluții arată combinația aleasă de agent (`GET /remedies` sau `plans/<s>/remedies.json`): treptele alese, P90 înainte/după, de ce nu ajunge ceva mai ieftin. Ofertele de baterii pentru PPC Energie pe „Alerte și mesaje” (clienți, kWh, efect, venit, recuperare).
- 15:08 Review independent Codex: 18 probleme, toate reparate (validare completă a lucrărilor, surse coerente când API-ul cade la mijloc, ruta PDF sigură, orele după miezul nopții, cache-ul detaliilor legat de plan, eroare cu Reîncearcă, contrast în tema închisă, scenariul păstrat în meniu, stare goală pentru scenariu fără plan, scenele /demo cu regiunea lor). Lista posturilor `/posturi` ca alternativă la hartă. 25 de teste, test de fum pe 14 ecrane.

- 16:05 Merge Teo (C, bilanț, planificator finale).
- 16:15 Numele produsului e **Daybreak** peste tot în `web/` (titlul paginii, antetul, scheletele de încărcare, `/demo`, README, convenții). Antetul arată doar cuvântul „Daybreak”, cu fontul interfeței, fără semn grafic. Logourile cu soarele, respinse, au ieșit din `web/public/` în `web/design/brand-respins/` (istoric, nefolosite); favicon-ul cu soarele e șters.
- 16:15 Plasa pentru procente: orice procent peste 999% se afișează „de peste 10 ori” („a crescut cu 18273047%” devine „a crescut de peste 10 ori”), în factori, rezumate și adnotări. În datele live de acum nu mai apare niciunul (verificat pe 689 de lucrări).
- 16:20 Graficul bilanțului pe pagina postului, pe formatul real al seriilor (zilnic, valori și sub zero): „ieșit din post” față de „suma clienților”, banda pierderii normale (`low`–`high`), lipsa peste normal colorată exact de unde linia trece de bandă, surplusul sub normal (`surplus_sub_normal`), adnotarea „Lipsa crește de aici”, o notă pentru valorile sub zero. Verificat cu seriile reale ale firului bilanț (copie temporară în /tmp, ștearsă).
- 16:20 Reparat: posturile roșii apăreau gri pe hartă (API-ul scrie „rosu”, fără diacritică). Cauza din bilanț apare în cuvinte, nu cod. Pragurile de culoare se citesc din `config/planner.yaml` (200 și 600 lei); legenda spunea 150.
- 16:25 Alerta principală arată, lângă textul planificatorului, ce a decis agentul pentru lucrările ei, numărat din decizii („11 în trasee, 182 verificate de la distanță”). La fel pe „Alerte și mesaje”.
- 16:25 `make web-demo`: build de producție (~10 s, fără avertismente) și consola pe 3710; testul de fum trece 14/14, paginile se încarcă de 2–3 ori mai repede decât în modul de dezvoltare.
- 16:40 Verificat la 1920×1080 pe planul real de la API: posturile (harta, lista, pagina), scara de soluții, ofertele de baterii (8 posturi), coada „Nu sunt sigur” (25), aprobarea listei (butonul nu a fost apăsat pe API-ul comun). Reparat pe parcurs: 269 de erori React pe „Alerte” (planificatorul pune aceeași lucrare de două ori în `alerts[].work_item_ids`; titlul „194 cazuri” număra dublurile, acum 103), lista posturilor fără lipsa pe zi, jurnalul cu termeni în engleză („Fusion”, „a score”) și „true” în loc de „da”.
- 16:50 `/demo` pentru filmare: harta lasă loc subtitrării (în scena 4 traseul Reșița–Oravița era sub ea), încadrarea cuprinde lucrarea scenei (scena 2: cazul din Ineu ieșea pe margine), linia de timp derulează la echipa lucrării (scena 4: E-RS-1 pleacă la 12:47 și ajunge la 14:00, furtuna e la 15:00), axa orelor rămâne sus. Consola fără erori pe toate ecranele.
- 17:00 Review final: `web-design-guidelines` pe toate ecranele (3 subagenți, 93 de observații: 1 gravă, 13 medii, restul mici) și `impeccable` (detectorul: 0 probleme; review vizual la 1920 și 1440). Reparate: cea gravă și 12 din 13 medii, plus majoritatea celor mici (detaliile în commit-ul 42a71fd). Filtrele jurnalului stau acum în adresă (`?cine=`, `?sursa=`, `?decizia=`, `?cauta=`).
- 17:03 Capturi pentru slideuri în `web/design/captures/` (12, la 1920×1080, toate din planul `PLAN-demo-vara-20250708-170128-31d6`), cu README.

- 17:25 Rezerva reverificată după schimbările de azi, pe build-ul de producție: API oprit → „Ultimul plan salvat”, 14/14 ecrane; doar fixture-uri → „Date de test”, 14/14. Scenariul „Mâine, cu prognoza reală” merge pe API (636 de lucrări, 23 în trasee), fără erori în consolă.
- 18:10 Reparațiile din QA-ul cap-coadă (17:55): graficul B fără panoul gol de risc și cu pragurile de 45 și 75 km/h desenate; scara de soluții pornește din `extra.ladder_base_p90_pu` (1,177 la PT-1269); antetul lucrării C arată combinația aleasă; `/modele` urmează `primary_metric` din raport, cu explicația potrivită pentru contoare și rândul SGCC (0,80 față de 0,11); harta cu nume în română sau cu litere latine (fără БЕОГРАД); scorurile de 1,00 apar „peste 0,99”, iar „probabilitatea 100%” apare „peste 99%”; eticheta scenariului nu mai e tăiată.
- 18:15 Teo a ales Varianta 1 a primului ecran („briefingul dimineții”), cu echipele într-o fereastră separată, ca să respire.
- 18:35 Simplificarea, aplicată:
  - primul ecran: fraza zilei („Mâine: 20 de lucrări pentru 8 echipe. 25 de cazuri așteaptă decizia ta.”), o singură acțiune, trei cifre, următorul caz de decis, echipele pe scurt (lista în fereastră), o hartă mică doar cu traseele; „Detaliile zilei” într-un panou lateral;
  - ecranul vechi, întreg (harta mare, linia de timp, detaliile lucrării), la `/harta`; adresele vechi (`/?lucrare=`, `/?harta=posturi`) duc acolo;
  - navigarea: Planul de mâine, De decis, Posturi, iar Alerte, Jurnal și Modele în „Mai mult”;
  - De decis, lucrarea și postul: verdictul într-o frază, apoi graficul; tot ce e tehnic (factori, regula, pragurile, scara de soluții, ID-urile modelului) în secțiuni care se deschid la cerere;
  - numere omenești („circa 5.000 de lei”, „încredere mică”), două greutăți de font, mai mult spațiu, o singură culoare de accent pentru acțiunea principală.
- 18:40 `/demo`: scenele 1 și 2 pe noul prim ecran, în tema închisă; scenele 3–5 pe harta mare; subtitrarea scenei pe o bandă opacă a ei, nu peste hartă.
- 18:50 Posturi, simplificat la fel: o frază („22 de posturi pierd mult: peste 600 de lei pe lună.”), lista cu cele mai mari pierderi, în lei rotunjiți, tabelul complet cu cifrele exacte la cerere.
- 18:45 Review `web-design-guidelines` pe ecranele noi (0 grave, 8 medii, toate reparate), testul de fum 15/15 (cu `/harta`), 50 de teste, consola fără erori; capturile noi pentru slideuri (15) în `web/design/captures/`.
- 18:55 Teo a trimis 14 imagini de design („Noapte”: fundal bleumarin închis, meniu în stânga, carduri, pastile, indicatori semicirculari) și a cerut consola „identic așa”. Decizie: aspectul din imagini, datele reale din API (imaginile au cifre inventate de generator, de ex. „1.284 posturi”, „PT-1223 Domnești”, rânduri de jurnal; nu le copiem).
- 19:01 Fundația: tema închisă (culori luate cu pipeta din imagini), fontul Inter, meniul din stânga cu cele opt ecrane, filele Consola / Rezultate / Rulează / Vezi demo, căutarea (⌘K), pe telefon bara de jos; piesele comune în `web/components/ds/`. Șase subagenți refac în paralel ecranele (planul, Nu sunt sigur + Rulare agent, posturile, lucrările A/B/C, jurnal + alerte + modele, ordinul de lucru + prezentarea).

## Urmează
- Până la 20:00: captura paginii unui post cu graficul bilanțului, dacă seriile ajung în API sau în instantaneu; altfel nimic nou, doar ce găsește testarea.
- După 20:00: doar bug-uri. Schimbările de design de pe `design` le aduc în `Teo-ui` doar din `web/` (`git diff <bază>..origin/design -- web | git apply -3`), nu prin merge: `design` șterge datele și modelele. De acolo ajung în `Teo` prin merge-ul orchestratorului (eu nu fac push pe `Teo`). Acum `design` nu are schimbări în `web/`.

## Blocaje
- niciunul

## Cereri către orchestrator
- (18:45) Raportul nou al lui A (`primary_metric: subtle_precision_at_k`, 0,625 față de 0,07) e în `Teo`, dar API-ul de pe 8710 servește încă raportul vechi (precizia@K 1,00) și la fel instantaneul `outputs/demo/reports/`. Consola urmează automat `primary_metric`; trebuie doar ca API-ul (checkout-ul planificatorului) să ia `Teo` și `make demo-snapshot` să refacă instantaneul.
- (18:45) Seriile bilanțului: lucrarea `A-20250708-PT-1269` are `extra.series_ref = outputs/series/demo-vara/A-20250708-PT-1269.json`; fișierul există doar în `/tmp/bilant_clean/outputs/series/demo-vara/` (78 de fișiere), nu și în checkout-ul principal sau în cel din care rulează API-ul. Consola le găsește singură dacă stau în `outputs/series/demo-vara/` al checkout-ului (verificat: graficul apare pe `/posturi/PT-1269`). Propunere: `make bilant-predict` în checkout-ul API-ului, apoi `make demo-snapshot`.
- (17:05) Către planificator: în `alerts[].work_item_ids` aceeași lucrare apare de două ori (alerta „cazuri cu risc de siguranță”: 194 de intrări, 103 lucrări distincte), iar titlul și „și încă N” din text numără dublurile. Interfața le scoate și corectează numărul din titlu; textul („și încă 188”) rămâne cum vine. Tot acolo: „Întăriri necesare: 1 cazuri de siguranță” (plural).
- (16:30) **Seriile bilanțului lipsesc în continuare** din API și din instantaneu. Lucrările `A-20250708-PT-*` au `extra.series_ref = outputs/series/demo-vara/A-20250708-PT-*.json`, dar `GET /api/series/A-20250708-PT-1269` dă 404 și `outputs/demo/series/demo-vara/` are doar seriile A (contoare), B și C. În worktree-ul Teo-bilant există acum doar `outputs/series/maine/A-20261108-PT-*.json` (98); cele pentru demo-vara nu mai sunt. Propunere: `make bilant-predict` în checkout-ul din care rulează API-ul, apoi `make demo-snapshot`. Graficul e gata și verificat pe formatul real; consola caută seria în API, în `outputs/demo/series/<s>/` și în `outputs/series/<s>/`.
- (16:30) Către planificator, text fals în alerta principală: „193 cazuri cu risc de siguranță: Intră primele în trasee, oricare ar fi costul”, dar din cele 193 doar 11 sunt în trasee, 182 merg la verificare de la distanță (`R-SAFETY-OVER-CAP`). În listă, numele se repetă („PT-1293, Sector 3 (sintetic), PT-1293, Sector 3 (sintetic)”: postul și contorul de pe el). Interfața arată acum, lângă text, numărătoarea reală din decizii, dar textul ar trebui reparat la sursă (de exemplu „11 intră în trasee azi; 182 se verifică întâi de la distanță, echipele sunt pline”).
- (16:30) Către firul bilanț (texte): lipse negative (A-20250708-PT-1282: „La post lipsesc ~-47.1 kWh/zi peste pierderea normală (-2.3% din energie)”; A-20250708-PT-1182: „Postul vecin are surplus de ~-5.5 kWh/zi (potrivire -15%)”; A-20250708-PT-1005: „Lipsa de ~-448 kWh/zi e doar pe hârtie”) și zecimale cu punct în rezumat (PT-1005: „de 1.70 ori”). Când valoarea e negativă, formularea ar trebui să fie de surplus, nu de lipsă.
- (16:30) Pentru demo, consola în modul de producție e mai rapidă și fără uneltele de dezvoltare: `make web-demo`. Ținta `demo` din secțiunea planificatorului pornește `make web` (dezvoltare); dacă vreți, `$(MAKE) -j2 api web-demo`.
- Rezolvate: `posts.json` în instantaneu (da), `POST /api/plan/approve` (există, consola îl folosește), instantaneul `outputs/demo/` în git (da), procentele absurde ale lui A (reparate la sursă; plasa din interfață rămâne).
- (15:10) Pentru demo: consola merge cu API-ul (8710) sau, dacă pică, cu instantaneul `outputs/demo/` din git. Instantaneul planificatorului din checkout-ul principal (`outputs/demo/plans/demo-vara/…`, `series/`, `reports/`, `remedies.json`) e exact ce citește interfața; intră în git la merge?
- (14:40) Către planificator (texte): zecimale cu punct în mesaje și alerte („9.1 ore”, „~38.9 kWh”), plural greșit („1 lucrări așteaptă”, „72 lucrări”: corect „1 lucrare”, „72 de lucrări”), data „marți 08.07.2025” în mesaje (în română: „marți, 8 iulie”). Interfața le arată așa cum vin.
- (14:35) Către firul bilanț: lucrările `A-<data>-PT-*` au `extra.series_ref = outputs/series/<s>/A-<data>-PT-*.json`, dar fișierele nu există (în `outputs/series/demo-vara/` sunt doar seriile C ale posturilor). Pagina postului are graficul „ieșit din post” (`value`) față de „suma clienților” (`expected`) gata; îi lipsește doar seria. Contractul `Series` cu `flag: "lipsa_peste_normal"` pe zilele cu lipsă peste normal.
- (14:25) Către firul A (date): în `explanation.top_factors[].label_ro` apar procente absurde („Consumul de noapte a crescut cu 18273047% față de istoric”, împărțire la aproape zero) și zecimale cu punct („0.46 din medie”, „9.1 ore”). Interfața le afișează acum protejat („peste 1.000%”, virgulă), dar textul ar trebui reparat la sursă: plafonare la ±1.000% sau formulare relativă („de la aproape zero”), format românesc. La fel în `reports/B/error_analysis.md` („0.16”).
- (14:10) Către planificator: `POST /api/plan/approve {scenario, plan_id, approver, note}` → `AuditRecord` (actor human, action „plan_approved”), pentru butonul „Aprobă lista echipelor”. Până atunci interfața păstrează aprobarea local și spune asta.
- (14:10) Către planificator: în instantaneul `outputs/demo/plans/<s>/` și `posts.json` (forma de la `GET /posts`), ca harta posturilor să meargă fără API.
- (14:10) Planul real stă acum doar în outputs/ al checkout-ului principal; API-ul de pe 8710 (worktree-ul planificatorului) servește încă planul de test cu 7 lucrări. Pentru demo, instantaneul `outputs/demo/` cu planul real ar fi rezerva sigură.
- Răspuns la cererea firului de prezentare (14:05): varianta întunecată pentru `/demo` costă puțin, culorile închise sunt deja validate în temă (A `#3B82F0`, B `#B84FC0`, C `#C4880A` pe `#0F1D2B`), iar harta are stilul `dark`. O fac până la 01:00, împreună cu cardul „Nu sunt sigur” vizibil pentru captură.
- Către planificator: `GET /api/posts` (registrul posturilor cu lei pierduți pe lună și starea verde/galben/roșu) ar scuti interfața de calcule; până atunci fac un exemplu local, etichetat sintetic.
- Rezolvate de orchestrator la 13:20: seriile de exemplu, planul complet, `depart_at`/`return_at`, `visit_cost_lei`, structura `outputs/demo/`, `scenario_id`, jurnalul.

## Pornirea consolei pentru testare
1. Prima dată: `make web-install` (instalează pachetele consolei cu bun).
2. Cu agentul în direct: `make api` într-un terminal și `make web-demo` în altul, apoi http://localhost:3710 (planul) și http://localhost:3710/demo (prezentarea, tema închisă).
3. Fără modele și fără API: `make web`; consola citește singură planul salvat din `outputs/demo/` și scrie sus „Ultimul plan salvat”.
4. Verificări: `make web-test` (38 de teste) și, cu consola pornită, `make web-smoke` (14 ecrane).

## Cum se rulează (comenzile exacte)
- **Pentru demo:** `make api` (sau `make api-demo` fără modele) într-un terminal, apoi `make web-demo` în altul → http://localhost:3710 (planul), http://localhost:3710/demo (prezentarea în tema închisă: ← → sau 1–5 schimbă scena, `?scena=N`, `?auto=1`). Fără API, consola merge singură pe instantaneul `outputs/demo/` din git.
- La dezvoltare: `make web` → http://localhost:3710 (cu API-ul pe 8710 dacă rulează; altfel instantaneul demo sau fixture-urile, automat)
- `make web-test` (35 de teste), `make web-smoke` (14 ecrane, pe consola pornită), `cd web && bun run lint`, `cd web && bunx tsc --noEmit`
- Forțarea sursei: `DATA_SOURCE=fixtures make web` (sau `demo`, `api`); alt API: `API_BASE=http://127.0.0.1:8710/api`.

## Cifre (doar din scripturi, cu comanda)
- niciuna (interfața doar afișează cifrele firelor; culorile surselor validate cu `node validate_palette.js` din abilitatea dataviz)

## Decizii (cu ora)
- 18:15 Primul ecran: Varianta 1 (alegerea lui Teo); echipele au doar un rezumat pe ecran, lista întreagă e într-o fereastră. Ecranul vechi rămâne întreg la `/harta`, ca nicio informație să nu se piardă.
- 18:40 În `/demo`, poveștile cu hartă (de ce a decis, furtuna, ziua echipelor) rămân pe harta mare; primele două scene arată primul ecran simplu.
- 17:00 Din review: Aprobă, Respinge și Amână rămân fără fereastră de confirmare. Decizia nu șterge nimic: intră în jurnal cu actorul „om”, iar planul următor o reevaluează; o confirmare la fiecare caz ar încetini dispecerul (și demo-ul).
- 16:50 În `/demo`, scena își alege încadrarea: harta lasă loc subtitrării, iar linia de timp arată echipa lucrării din scenă.
- 16:15 Daybreak (decizia lui Teo, 15:30): antetul are doar cuvântul, cu fontul interfeței, până la identitatea aleasă separat; culorile surselor A, B, C rămân. Logourile respinse ies din `public/`, ca nimeni să nu le folosească din greșeală în slideuri.
- 16:25 Când textul unei alerte și deciziile nu se potrivesc, interfața arată deciziile (numărate), lângă text, fără să rescrie textul planificatorului.
- 16:20 Pragurile de culoare ale posturilor vin din `config/planner.yaml`, aceleași cu ale planificatorului; culoarea primită de la API are prioritate, normalizată („rosu” → „roșu”).
- 14:30 Test de fum `make web-smoke` (încarcă toate ecranele pe consola pornită și cade la orice eroare de randare): `tsc` nu prinde funcțiile de client chemate pe server, testul da.
- 14:00 Harta pe două straturi: markeri DOM cu literă doar pentru opririle din trasee și selecție; celelalte lucrări (sute) sunt puncte într-un strat MapLibre, cu informații la trecerea mouse-ului. Altfel planul real e ilizibil.
- 12:48 Faza 0 cu subagenți în paralel (schelet, logo, 3 machete).
- 12:50 Trimiterea la PPC rămâne discretă: familia bleumarin + albastru + o culoare caldă, fără valorile lor exacte și fără fontul PingLCG.
- 12:54 Logoul: Codex desenează doar semnul; numele îl scriem cu fontul interfeței (diacritice sigure).
- 13:00 Culorile surselor validate pentru daltonism: deschis A `#2C6FD9`, B `#A23C9E`, C `#D99100`; închis A `#3B82F0`, B `#B84FC0`, C `#C4880A`. Violetul inițial pentru B pica (ΔE 0,9 față de albastru la deuteranopie).
- 13:14 Direcția Panou (HMI de dispecerat, temă deschisă): limba dispecerilor, lizibilă pe proiector; de la „Noaptea” iau ferestrele de timp, de la „Mersul” orele mari.
- 13:35 Harta are vederi pe regiuni, pentru că scenariul demo (8 iulie 2025) are lucrări B în Banat, departe de București; implicit arată regiunea cu cele mai multe opriri.
- 13:40 Orele de plecare și de întoarcere: din `depart_at`/`return_at` când există, altfel estimate din km (marcate „cca”).
- 13:45 Worker-ul MapLibre se servește static din `web/public/maplibre/` (copiat la `dev`/`build`, nu stă în git), pentru că bundler-ul Next nu-i rezolvă calea.
