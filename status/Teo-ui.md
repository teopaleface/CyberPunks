# Status: Teo-ui
Actualizat: 2026-11-07 13:52
Milestone curent: M1 (M0 terminat la 13:50)
Gata de merge: da (commit d18f547, M0: temă, logo, antet, ecranul Planul de mâine pe API și pe fixture-uri)

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

## Urmează
- M1 (17:30): detaliul lucrării (`/lucrari/[id]`) cu graficul potrivit sursei (consum cu zilele de zero; rafale și risc cu fereastra furtunii; tensiune cu P10–P90 și limita 1,10), apoi „Nu sunt sigur” pe pagina ei, alerte și mesaje, jurnal, modele.
- După M1: harta posturilor (verde / galben / roșu după lei pierduți pe lună), pagina postului (ieșit din post față de suma clienților, cauza, confirmarea contorului), scara de soluții C cu treapta aleasă și motivul, mesajul de grup ca previzualizare, ofertele de baterii, contorul de lei recuperați, lista echipelor cu aprobare.
- Până la 01:00: `/demo` pentru înregistrări, cu varianta întunecată cerută de firul de prezentare.

## Blocaje
- niciunul

## Cereri către orchestrator
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
- 12:48 Faza 0 cu subagenți în paralel (schelet, logo, 3 machete).
- 12:50 Trimiterea la PPC rămâne discretă: familia bleumarin + albastru + o culoare caldă, fără valorile lor exacte și fără fontul PingLCG.
- 12:54 Logoul: Codex desenează doar semnul; numele îl scriem cu fontul interfeței (diacritice sigure).
- 13:00 Culorile surselor validate pentru daltonism: deschis A `#2C6FD9`, B `#A23C9E`, C `#D99100`; închis A `#3B82F0`, B `#B84FC0`, C `#C4880A`. Violetul inițial pentru B pica (ΔE 0,9 față de albastru la deuteranopie).
- 13:14 Direcția Panou (HMI de dispecerat, temă deschisă): limba dispecerilor, lizibilă pe proiector; de la „Noaptea” iau ferestrele de timp, de la „Mersul” orele mari.
- 13:35 Harta are vederi pe regiuni, pentru că scenariul demo (8 iulie 2025) are lucrări B în Banat, departe de București; implicit arată regiunea cu cele mai multe opriri.
- 13:40 Orele de plecare și de întoarcere: din `depart_at`/`return_at` când există, altfel estimate din km (marcate „cca”).
- 13:45 Worker-ul MapLibre se servește static din `web/public/maplibre/` (copiat la `dev`/`build`, nu stă în git), pentru că bundler-ul Next nu-i rezolvă calea.
