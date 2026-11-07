# Consola dispecerului (web/)

Interfața web a agentului CyberPunks: Next.js 16 (App Router, Turbopack, Cache Components), React 19, Tailwind 4, shadcn/ui (Radix, presetul Nova), MapLibre, Recharts, Motion. Pachetele se instalează cu bun.

## Comenzi

```bash
cd web
bun install
bun run dev         # http://localhost:3710
bun run build
bun run gen:types   # lib/contracts.ts din ../contracts/*.schema.json
bun test            # testele stratului de date
```

## Variabile de mediu (opționale, în `web/.env.local`)

| Variabilă | Implicit | Ce face |
|---|---|---|
| `API_BASE` | `http://127.0.0.1:8710/api` | API-ul planificatorului |
| `DATA_SOURCE` | `auto` | `auto`, `api`, `demo` sau `fixtures` |
| `DEFAULT_SCENARIO` | `demo-vara` | scenariul de pe ecranul principal |
| `REPO_ROOT` | dosarul părinte al lui `web/` | de unde se citesc `contracts/`, `config/`, `outputs/demo/`, `reports/` |
| `REVIEWER_NAME` | `dispecer` | numele trimis la `POST /review/{id}` |

## Stratul de date (`lib/data/`)

Doar pe server. Fiecare citire întoarce `{ data, source, fetchedAt, degradedReason?, detail?, parseErrors? }`, unde `source` e `api`, `demo` sau `fixtures`, și nu aruncă niciodată spre pagină.

- `index.ts`: `getPlanView`, `getPlan`, `getWorkItems`, `getWorkItem`, `getSeries`, `getAudit`, `getMetrics`, `getScenarios`, `getHealth`.
- `actions.ts`: acțiunile de server `runAgent(scenario)` și `submitReview(id, decision, note)`; întorc `{ ok: true, ... }` sau `{ ok: false, error }`.
- `source.ts`: alegerea sursei. În `auto`: API-ul, dacă răspunde la `/health`; altfel instantaneul din `outputs/demo/`, dacă are plan pentru scenariu; altfel `contracts/fixtures/`.
- `files.ts`: cititoarele de fișiere, inclusiv locurile unde se caută instantaneul demo (`demoCandidates`).
- `types.ts` și `labels.ts`: tipuri și etichete în română, sigure de importat și din componente client.

Next 16 cu Cache Components: componentele care citesc date stau într-un `<Suspense>` (sau sub un `loading.tsx`). Funcțiile din stratul de date cheamă singure `connection()`.

`/debug` arată configurarea, starea API-ului și sursa folosită de fiecare funcție.
