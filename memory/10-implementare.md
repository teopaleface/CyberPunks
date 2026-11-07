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
| Prezentare | Teo-prezentare | video de 30 s cu HyperFrames în stil Apple, slideuri, scriptul demo-ului |

## Alegeri tehnice (orchestrator, 7 nov.)

- Python 3.12 prin uv. Verificat că se instalează și se importă: lightgbm 4.7.0, shap 0.54.1, ortools 9.15, pandapower 3.5.6, simbench 1.6.3, scikit-learn 1.9.1, pandas 2.3.3, numpy 2.4.6, fastapi, fpdf2.
- Contractele în pydantic v2; schemele JSON se generează din ele. Validatorul respinge coordonatele din afara României și probabilitățile imposibile (intrări greșite).
- Zona demo: București-Ilfov pentru A și C, județele Rețele Electrice din Muntenia Sud, Dobrogea și Banat pentru B. Bazele operative și echipele sunt simulate (`config/area.yaml`, `config/crews.yaml`).
- Scenarii: `demo-vara` (o zi reală de vară cu furtuni, data o alege firul B) și `maine` (prognoza reală).
- Stilul video-ului: articolul lui leo (@leomeethewoo) "Make your product videos look expensive (Apple Framework)", 25 sep. 2026.
