# Implementarea: A, B și C în paralel, cu orchestrator

Decizia lui Teo (7 nov. 2026, 12:30): facem în paralel A (contoare), B (furtună) și C (prosumatori), ca un singur produs, "Tura de mâine" (nume de lucru): agentul care decide unde merg mâine echipele de teren Rețele Electrice. Conversația laterală din T3 în care s-a făcut research-ul e orchestratorul: urmărește celelalte fire, rulează testele, face merge-urile.

- Planul complet: `docs/PLAN.md`. Contractele: `docs/CONTRACTS.md` și `src/cyberpunks/common/contracts.py`.
- Instrucțiunile fiecărui fir: `prompts/` (`_comun.md` plus câte un fișier pe fir).
- Stările firelor: `status/<branch>.md`.
- Proiectul T3: "CyberPunks" (`/Users/teo/Projects/CyberPunks`), creat pe 7 nov. 2026.

## Firele (top-level în T3, fiecare în worktree-ul lui, din branch-ul Teo)

| Fir | Branch | Rol |
|---|---|---|
| A | Teo-A-contoare | contoare defecte sau manipulate |
| B | Teo-B-furtuna | risc de avarii la furtună, echipe trimise din timp |
| C | Teo-C-prosumatori | tensiune prea mare din cauza prosumatorilor |
| Planificator | Teo-planificator | agentul: decizii, trasee OR-Tools, acțiuni, jurnal, API pe portul 8710 |
| Interfață | Teo-ui | consola dispecerului, Next.js, portul 3710 |
| Bilanț pe post | Teo-bilant | pierderi pe post, diagnosticul cauzei, fuziunea cu A (adăugat la 14:05, vezi 11-bilant-pe-post.md) |
| Prezentare | Teo-prezentare | video de 30 s cu HyperFrames în stil Apple, slideuri, scriptul demo-ului |

## Thread-urile pornite (7 nov., 12:44) și worktree-urile lor

Worktree-urile sunt în `/Users/teo/.t3/worktrees/CyberPunks/<branch>`.

- A: `mcp:67703da0-af20-4c1c-a2bb-e07fc00ea882`
- B: `mcp:42039004-e535-4894-814b-7dfcc519d440`
- C: `mcp:1db1c118-f897-495d-bf45-dcd91a9d84bf`
- Planificator: `mcp:8a721147-9253-4a31-a5c5-45843bf660ae`
- Interfață: `mcp:258543d3-0b7d-4643-bfb8-99aa0e4bc313`
- Prezentare: `mcp:1b443203-dc89-437d-bf33-01ad5692d571`
- Bilanț pe post (pornit la 14:05): `mcp:509cafcf-5f9a-4ee8-9ab0-68cb1bfbb85a`, worktree `/Users/teo/.t3/worktrees/CyberPunks/Teo-bilant`

Orchestratorul rulează automat la fiecare 30 de minute, prin programarea T3 "Orchestrator CyberPunks (la 30 de minute)" (`scheduled-task:command:mcp:2b4adb6a-3dd4-464e-9117-b6bdd3211bf4:schedule-task:cyberpunks-orchestrator-tick-v1`), legată de conversația laterală. Se oprește după demo (duminică, 13:30). Mac-ul e ținut treaz cu `caffeinate -dimsu -t 93600` (26 de ore, pornit la 12:46).

## Alegeri tehnice (orchestrator, 7 nov.)

- Python 3.12 prin uv. Verificat că se instalează și se importă: lightgbm 4.7.0, shap 0.54.1, ortools 9.15, pandapower 3.5.6, simbench 1.6.3, scikit-learn 1.9.1, pandas 2.3.3, numpy 2.4.6, fastapi, fpdf2.
- Contractele în pydantic v2; schemele JSON se generează din ele. Validatorul respinge coordonatele din afara României și probabilitățile imposibile (intrări greșite).
- Zona demo: București-Ilfov pentru A și C, județele Rețele Electrice din Muntenia Sud, Dobrogea și Banat pentru B. Bazele operative și echipele sunt simulate (`config/area.yaml`, `config/crews.yaml`).
- Scenarii: `demo-vara` (o zi reală de vară cu furtuni, data o alege firul B) și `maine` (prognoza reală).
- Stilul video-ului: articolul lui leo (@leomeethewoo) "Make your product videos look expensive (Apple Framework)", 25 sep. 2026.
