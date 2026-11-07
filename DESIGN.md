# Branch-ul `design`

Ramura `design` poate folosi o copie ușoară pentru lucrul la interfață (`web/`). Modelele antrenate (`models/release/`) și mostrele de date (`data/samples/`) se păstrează în `Teo` și `main`, chiar dacă lipsesc din copia de design. Interfața citește planul gata făcut din `outputs/demo/`.

## Cum îl iei (doar branch-ul ăsta, fără istoricul greu al celorlalte)

```bash
git clone --single-branch --branch design --depth 1 https://github.com/teopaleface/CyberPunks.git
cd CyberPunks/web
bun install        # sau npm install
bun run dev        # http://localhost:3710
```

Fără API, consola citește automat instantaneul `outputs/demo/` (planul real al agentului pentru 8 iulie 2025). Detalii: `web/README.md`.

## Reguli

- Lucrezi doar în `web/`. Nu adăuga fișiere mari: imaginile și fonturile sub 1 MB fiecare, fără video, fără modele 3D în git.
- Faci commit și push pe `design`. Orchestratorul aduce în `Teo` doar schimbările din `web/` (modelele și datele lipsesc intenționat aici și nu trebuie șterse din `Teo`).
- Numele produsului e Daybreak. Interfața este în engleză și păstrează comutatorul Light/Dark. Culorile surselor A (albastru), B (mov-prună), C (chihlimbar) sunt verificate pentru daltonism; schimbă-le doar împreună cu firul de interfață.
