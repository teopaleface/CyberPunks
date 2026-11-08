# Firul Interfață: consola dispecerului

Branch: `Teo-ui`. Status: `status/Teo-ui.md`.

## Ce deții

`web/` (tot), secțiunea Interfață din `Makefile`, `status/Teo-ui.md`.

## Obiectiv

O consolă pentru dispecerul Rețele Electrice care arată planul de mâine și explică fiecare decizie. Trebuie să arate premium: e prima impresie a juriului și apare în video. Calitatea vizuală contează cât funcționalitatea.

## Faza 0 (cel mult 45 de minute, subagenți în paralel)

- Direcția vizuală, cu abilitatea `frontend-design`: 2-3 variante cu conținut real (din `contracts/fixtures/plan_example.json` și `work_items_*.jsonl`), arătate lui Teo cu `html_preview` și `html_render`. Alege una și notează de ce în status.
- Paleta: o trimitere discretă la PPC (verifică culorile de pe ppcenergy.ro și ppcgroup.com), fără să pară produs oficial PPC. Cel mult 3 culori principale. Font cu diacritice românești (ș, ț), verificat.
- Generează cu Codex (modelul de imagine "image 2.6") un logo pentru "Daybreak" și, dacă ajută, 1-2 ilustrații, prin `delegate_task` către `codex`, cu calea de salvare în `web/public/brand/`.
- Verifică că hărțile OpenFreeMap merg fără cheie (stilul și tile-urile) sau alege altă sursă de hărți fără cheie.

## Ce construiești

- Stack: Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + MapLibre GL + grafice (Recharts sau visx). Manager: bun sau npm. Port 3710 (`make web`, adaugă ținta în secțiunea ta din Makefile). API-ul e la http://127.0.0.1:8710/api (firul planificator, contractul în `docs/CONTRACTS.md`). Până e gata și ca rezervă permanentă, citește `outputs/demo/` sau `contracts/fixtures/` (o variabilă de mediu alege sursa; interfața nu are voie să cadă dacă API-ul nu răspunde).
- Ecrane:
  1. Planul de mâine: hartă cu traseele echipelor și lucrările colorate pe sursă (A contoare, B furtună, C tensiune), listă ordonată pe echipe, cifrele zilei (lucrări, valoare așteptată, km, câte merg la om).
  2. Rulează agentul: buton care pornește `POST /api/run` și arată pașii Perceive → Estimate → Decide → Act cu timpii reali.
  3. Detaliul unei lucrări: graficul potrivit sursei din `GET /api/series/{id}` (consum cu anomalii; vânt și risc; tensiune cu intervalul și limita 1,10), factorii în cuvinte simple, cazuri similare, încrederea, pragul și regula care au decis, ID-ul predicției și versiunea modelului (urmărirea până la model).
  4. "Nu sunt sigur": coada pentru om, cu aprobă, respinge, amână (`POST /api/review/{id}`), iar planul se actualizează.
  5. Alerte și notificări (textele către prosumatori, marcate "demo, nu s-a trimis").
  6. Jurnalul deciziilor.
  7. Modelele: metricile față de baseline pentru A, B, C (`GET /api/metrics`), analiza erorilor pe scurt, etichetele "date sintetice" și "validat pe date externe".
  8. Scenarii: "Mâine, cu prognoza reală" și "Zi de vară cu furtuni".
- Texte în română, cu diacritice. Etichete de transparență vizibile: "Date sintetice", "Model validat pe date externe".
- Calitate: contrast și navigare din tastatură, stări de încărcare și de eroare, fără elemente care sar la încărcare, animații discrete (`emil-design-eng`), arată bine pe proiector la 1920×1080.
- QA: pornești dev server-ul și verifici cu `agent-browser` sau cu previzualizarea T3, cu capturi. Înainte de "gata": review cu `web-design-guidelines` și `impeccable`, apoi repari ce găsesc. Aplică `vercel-react-best-practices`.
- Pentru video și demo: până la ora 01:00, o rută sau un mod de prezentare (`/demo`), curat, pe care firul de prezentare îl poate înregistra.

## Milestones (ora României)

- 14:30 M0: direcția vizuală aleasă (arătată lui Teo), logo, proiectul Next.js pornit.
- 17:30 M1: ecranul 1 și detaliul lucrării pe fixture-uri.
- 21:30 M2: legat la API, toate ecranele de bază, "Rulează agentul".
- 01:00 modul de prezentare pentru înregistrări.
- 03:00 M3: review-uri de design reparate, stări de eroare, rezerva fără API.
- 08:00 M4: lustruire finală pe date reale, capturi pentru slideuri.
