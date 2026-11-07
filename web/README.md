# Tura de mâine: consola dispecerului (`web/`)

Consola în care dispecerul Rețele Electrice vede planul de mâine făcut de agent, înțelege fiecare decizie și decide ce agentul n-a putut decide singur. Proiectată pentru proiector 1920×1080, în română.

Stack: Next.js 16 (App Router, Turbopack, Cache Components), React 19, Tailwind 4, shadcn/ui, MapLibre GL 6 cu hărți OpenFreeMap (fără cheie), Recharts 3. Pachetele se instalează cu bun (merge și `npm install`).

## Pornire

```bash
make web            # din rădăcina repo-ului: instalează și pornește pe http://localhost:3710
# sau
cd web && bun install && bun run dev
```

Consola merge și fără API: dacă `http://127.0.0.1:8710/api` nu răspunde, citește instantaneul `outputs/demo/`, iar dacă nici acela nu există, exemplele din `contracts/fixtures/`. Antetul spune mereu de unde vin datele („Agentul, în direct”, „Ultimul plan salvat”, „Date de test”).

Alte comenzi: `bun run build` (build de producție), `bun test` (stratul de date), `bun run lint`, `bunx tsc --noEmit`, `bun run gen:types` (tipurile din `../contracts/*.schema.json`).

## Ecranele

| Adresă | Ce arată |
|---|---|
| `/` | Planul de mâine: cifrele zilei, harta pe regiuni (lucrările sau posturile de transformare), linia de timp a echipelor ca schemă monofilară, coada „Nu sunt sigur”, alerta principală, detaliul lucrării selectate, aprobarea listei echipelor, ordinele de lucru PDF |
| `/lucrari/<id>` | Detaliul unei lucrări: graficul potrivit sursei, factorii (SHAP), cazurile asemănătoare, decizia cu regula și pragurile, încrederea, urmărirea până la predicție și versiunea modelului, datele de intrare, scara de soluții pentru tensiune |
| `/posturi/<id>` | Pagina unui post: energia ieșită față de suma clienților (bilanțul), cauza probabilă, contoarele semnalate, tensiunea |
| `/coada` | „Nu sunt sigur”: tot ce așteaptă un om, cu Aprobă, Respinge, Amână |
| `/alerte` | Alertele pentru dispecerat și echipe; mesajele către clienți (demo, nu se trimite nimic) |
| `/jurnal` | Jurnalul deciziilor, agent și om, cu predicția, modelul, regula și pragurile |
| `/modele` | Modelele A, B, C față de baseline pe setul de test, evaluarea agentului față de strategii simple |
| `/demo` | Modul de prezentare pentru înregistrări: tema închisă, 5 scene (← →, cifrele 1–5, `?scena=2`, `?auto=1`) |
| `/ordine/<echipă>` | Ordinul de lucru al echipei (PDF), de la API sau din instantaneu |
| `/debug` | Configurarea, starea API-ului și sursa fiecărei citiri |

Scenariul se alege din antet (se ține minte într-un cookie) sau din adresă: `?scenariu=maine`.

## Variabile de mediu (opționale, în `web/.env.local`)

| Variabilă | Implicit | Ce face |
|---|---|---|
| `API_BASE` | `http://127.0.0.1:8710/api` | API-ul planificatorului |
| `DATA_SOURCE` | `auto` | `auto`, `api`, `demo` sau `fixtures` |
| `DEMO_DIR` | `outputs/demo` | unde e instantaneul demo (aceeași structură ca `outputs/`) |
| `DEFAULT_SCENARIO` | `demo-vara` | scenariul implicit |
| `REPO_ROOT` | dosarul părinte al lui `web/` | de unde se citesc `contracts/`, `config/`, `reports/` |
| `REVIEWER_NAME` | `dispecer` | numele trimis la `POST /review/{id}` |

## Transparență

- „Date sintetice”: contoarele, posturile, bazele și echipele sunt sintetice, puse pe harta reală (pătratul hașurat din antet și de la fiecare lucrare).
- „Model validat pe date externe”: apare la lucrările și modelele antrenate pe seturi publice (SGCC, Londra, EAGLE-I, SimBench).
- Bilanțul pe post: „Simulare pe date publice, gândită pentru datele PPC”.
- Mesajele către clienți sunt doar previzualizări: „demo, nu s-a trimis”.
- Culorile surselor (A albastru, B mov-prună, C chihlimbar) sunt verificate pentru daltonism; markerii poartă și litera sursei.

## Organizarea codului

- `lib/data/`: stratul de date, doar pe server. Fiecare citire întoarce `{ data, source, degradedReason }` și nu aruncă spre pagină. Acțiunile de server: `runAgent`, `submitReview`, `approvePlan`.
- `components/shell/`: antetul (ecrane, scenariu, proveniență, „Rulează agentul” cu timpii reali ai pașilor Perceive, Estimate, Decide, Act).
- `components/plan/`: harta (MapLibre: markeri cu literă pentru opririle din trasee, puncte pentru restul), linia de timp a echipelor, coloana din dreapta.
- `components/detail/`: graficele pe sursă, scara de soluții, butoanele omului.
- `design/`: brieful și machetele direcțiilor vizuale, convențiile (`design/CONVENTIONS.md`).
- Worker-ul MapLibre se copiază din `node_modules` în `public/maplibre/` la `dev` și `build` (`scripts/copy-maplibre-worker.ts`).
