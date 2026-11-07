# Planul de implementare

Echipa CyberPunks, SmartHack XI 2026, tema PPC "24h to Power PPC". Scris de orchestrator pe 7 nov. 2026, ora 13:00. Tema completă: `memory/07-tema-ppc.md`. Formatele de date: `docs/CONTRACTS.md`.

## Produsul într-o frază

"Tura de mâine" (nume de lucru): un agent AI care decide unde merg mâine echipele de teren Rețele Electrice, pe baza a trei modele ML antrenate de noi, și explică fiecare decizie.

PDF-ul PPC spune: "Un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață." Produsul nostru face exact pasul ăsta.

## Trei surse de lucrări, aceleași echipe

| Sursă | Problema | Model (antrenat de noi) | Lucrarea pentru echipe |
|---|---|---|---|
| A. Contoare | Contoare defecte sau manipulate, din peste 2 mil. de contoare care trimit la 15 minute | Clasificare pe date dezechilibrate, cu etichete puține (SGCC plus contoare din Londra cu defecte injectate) | Verificare la fața locului, citire la distanță, urmărire, decizie la om |
| B. Furtună | Unde vor fi avarii în următoarele 24 de ore, din vreme | Probabilitate și cuantile de clienți afectați (EAGLE-I plus vreme istorică Open-Meteo), aplicat pe județele Rețele Electrice | Echipă trimisă din timp în zonă, alertă la dispecerat |
| C. Prosumatori | Posturi unde tensiunea trece de 1,10 pu la prânz din cauza panourilor | Model surogat pentru circulația de puteri (SimBench plus pandapower), testat pe rețele nevăzute | Schimbarea prizei transformatorului, campanie de măsurători, mesaj către prosumatori (PPC Energy) |

Planificatorul primește lucrările din toate trei, aplică praguri justificate de cost și de încredere, trimite la om ce nu e sigur, împarte echipele limitate (abilități, ture, depouri) și produce trasee, ordine de lucru, alerte, notificări și un jurnal în care fiecare decizie duce la predicția care a produs-o.

## Fluxul (Perceive, Estimate, Decide, Act)

```
 Perceive                 Estimate (modelele noastre)        Decide (cod, nu LLM)              Act
 ─────────                ───────────────────────────        ────────────────────              ───
 consum contoare  ──────▶ A: P(defect / manipulare), kWh ─┐
 vreme (prognoză) ──────▶ B: P(avarii), clienți P50/P90  ─┼─▶ validare (carantină) ──▶ praguri ──▶ trasee OR-Tools
 radiație, rețele ──────▶ C: tensiune max P10/P50/P90    ─┘   "nu sunt sigur" → om      cost/valoare  ordine de lucru PDF
                                                               capacitate echipe                     alerte, notificări
                                                                                                      jurnal (audit)
                                       interfața dispecerului ◀── API (FastAPI) ◀──────────────────────┘
```

## Firele de lucru

Toate pornesc din branch-ul `Teo`, fiecare în worktree-ul lui. Orchestratorul (conversația care coordonează) face merge în `Teo`.

| Fir | Branch | Ce deține (scrie doar aici) | Ce livrează |
|---|---|---|---|
| A contoare | `Teo-A-contoare` | `src/cyberpunks/a_contoare/`, `tests/a/`, `reports/A/`, `docs/data/A.md`, `docs/research/A.md`, `data/samples/A/` | `outputs/work_items/<scenariu>/A.jsonl`, serii, `reports/A/metrics.json`, model card |
| B furtună | `Teo-B-furtuna` | `src/cyberpunks/b_furtuna/`, `tests/b/`, `reports/B/`, `docs/data/B.md`, `docs/research/B.md`, `data/samples/B/` | `B.jsonl`, serii, metrici, data reală a scenariului `demo-vara` |
| C prosumatori | `Teo-C-prosumatori` | `src/cyberpunks/c_prosumatori/`, `tests/c/`, `reports/C/`, `docs/data/C.md`, `docs/research/C.md`, `data/samples/C/` | `C.jsonl`, serii, metrici, raport de investiții, răspuns la cereri de racordare |
| Planificator | `Teo-planificator` | `src/cyberpunks/planner/`, `src/cyberpunks/api/`, `src/cyberpunks/cli.py`, `config/`, `tests/planner/`, `reports/planner/`, `docs/research/planificator.md`, `outputs/demo/` | `cyberpunks run`, plan, jurnal, ordine de lucru, alerte, notificări, API pe portul 8710, evaluarea agentului |
| Interfață | `Teo-ui` | `web/` | Consola dispecerului pe portul 3710 |
| Prezentare | `Teo-prezentare` | `presentation/` | Video de 30 s (HyperFrames), slideuri, scriptul demo-ului, înregistrarea de rezervă |
| Orchestrator | `Teo` (checkout-ul principal) | `src/cyberpunks/common/`, `contracts/`, `docs/PLAN.md`, `docs/CONTRACTS.md`, `README.md`, `pyproject.toml` și `uv.lock` (la merge), antetul `Makefile`, `memory/`, `status/orchestrator.md` | Integrare, teste, merge, rapoarte către Teo |

Fiecare fir are și fișierul lui de stare, `status/<branch>.md`, și secțiunea lui din `Makefile`.

## Calendar (ora României)

| Când | Ce |
|---|---|
| Sâmbătă 13:15 | Pornesc firele |
| 14:30 | M0: cercetare scurtă scrisă în `docs/research/`, date descărcate sau generator gata, status completat |
| 15:00 | Firul B anunță data reală pentru scenariul `demo-vara` |
| 16:00 | Planificatorul servește fixture-urile prin API, ca interfața să lucreze pe date |
| 17:30 | M1: primul cap-coadă pe fiecare fir (baseline, primul model, lucrări valide; plan din fixture-uri; interfața arată planul) |
| 21:30 | M2: modelele bat baseline-ul pe test separat; OR-Tools, ordine de lucru, alerte, jurnal; interfața legată la API; storyboard video |
| 22:00 | Integrarea 1: totul pe `Teo`, `uv run cyberpunks run --scenario demo-vara` merge cap-coadă |
| Duminică 01:00 | Interfața are modul de prezentare pentru înregistrări |
| 03:00 | M3: robustețe, explicabilitate, analiza erorilor, evaluarea agentului, interfața completă, video v1 |
| 08:00 | M4: model cards, README reproductibil, test dintr-o clonă curată, slideuri, video final, înregistrarea de rezervă |
| 10:30 | Înghețarea codului: doar reparații |
| 11:00 | Orchestratorul: test final dintr-o clonă curată, merge final pe `Teo`. Teo decide merge în `main`, curățarea istoricului și repo-ul public |
| 12:00 | Predare. Demo live de la 13:00: 5 minute plus 2 minute de întrebări |

## Reguli comune

- Fiecare fir scrie doar în directoarele lui. Cererile pentru fișiere comune merg în `status/<branch>.md`, la "Cereri către orchestrator".
- Python 3.12 prin uv (`uv sync`, `uv run`). Dependențe noi prin `uv add`, anunțate în status.
- Commit-uri mici și dese, împinse pe `origin/<branch>`. La fiecare milestone: `git merge Teo` în branch-ul propriu, `make check`, push, "Gata de merge: da (commit ...)" în status.
- Interzis: force-push, rescrierea istoricului, ștergerea branch-urilor, push pe `main` sau `Teo`, schimbarea vizibilității repo-ului, secrete sau date mari în git.
- Nicio cifră inventată: fiecare metrică vine dintr-un script care se poate rula din nou. Ipotezele economice stau în `config/economics.yaml`, cu sursă sau cu eticheta "IPOTEZĂ".
- Datele și activele sintetice sunt etichetate ca sintetice în date, în interfață și în prezentare.
- Mașina e împărțită de 6 fire: antrenările lungi folosesc cel mult 4 nuclee.

## Integrarea

1. Orchestratorul citește la fiecare 30 de minute stările (`git show <branch>:status/<branch>.md`) și firele.
2. Ce e marcat "Gata de merge" intră în `Teo` cu `git merge --no-ff`, apoi `make check` și testul cap-coadă. Dacă pică, orchestratorul repară integrarea sau scrie firului ce trebuie schimbat.
3. După merge, orchestratorul împinge `Teo` și anunță firele să facă `git merge Teo`.
4. Schimbările de contract le face doar orchestratorul, cu notificare către toate firele.

## Ce înseamnă "gata" (legat de grila PPC)

- Idee și relevanță (25): problema spusă cu cifrele PPC, în produs și în prezentare.
- Calitate ML (25): pentru fiecare model, `reports/<X>/metrics.json` valid (model față de baseline pe test separat), `error_analysis.md`, `model_card.md`, comandă de reproducere.
- Agent (25): `uv run cyberpunks run --scenario demo-vara` merge automat de la date la acțiuni; praguri cu `rule_id`; evaluarea agentului față de strategii simple în `reports/planner/`.
- Robustețe (10): teste pentru intrări greșite, date lipsă, surse lipsă, "nu sunt sigur" trimis la om.
- Explicabilitate (10): factori și cazuri similare pentru fiecare lucrare, urmărire până la predicție în jurnal și în interfață.
- Demo și repo (5): README cu pași care merg dintr-o clonă curată, cod curat, istoric de commit-uri, video, slideuri.
