# Status: Teo-landing
Actualizat: 2026-11-07 18:25
Milestone curent: M1 (22:00) gata devreme: toate secțiunile pe date reale, în engleză, stil Apple (cererea lui Teo, 17:55), animațiile de bază. Urmează M2 (03:00): review web-design-guidelines, contrast, reduced motion.
Gata de merge: da (commit f3771f1)

## Făcut
- 17:16 Citite instrucțiunile, memoria, statusurile, rapoartele, cadrele filmului.
- 17:25 Research pe cele 10 site-uri plus ppcenergy.ro: `docs/research/landing.md` (ce iau din fiecare și de ce, licențele, fontul, paleta, actualizarea de la 17:55).
- 17:45 Prima variantă a hero-ului (în română), arătată lui Teo.
- 17:55 Teo: „trebuie în engleză, mai wow, mai premium, mai minimalist, mai stil Apple”. Refăcut tot:
  - hero centrat: „Daybreak”, „Tomorrow’s crews, planned tonight.” (titlul din film), o propoziție, „Watch the demo” și „Read the code”; dedesubt harta României din puncte, înclinată ca un peisaj, cu lucrările reale ale zilei demo ca lumini și răsăritul în culorile PPC în spatele orizontului;
  - fontul sistemului (SF Pro pe Mac), Inter pe celelalte sisteme; bara de sus translucidă, ca la Apple;
  - Problem: frază mare care se aprinde la derulare, 4 cifre publice cu note de subsol (3,18M clienți RE, 385.791 prosumatori, 8,66% pierderi în Muntenia, ≈85% din compensațiile automate), citatul PPC „0.87”, „Daybreak does.”;
  - How it works: harta Bucureștiului și Ilfovului fixă, cei 4 pași o schimbă la derulare (lucrările apar, primesc scoruri, cele mai multe merg la verificare de la distanță, cercuri portocalii pentru om, traseele se desenează);
  - Models (bento): contoare, bilanț pe post, furtună, tensiune, fiecare cu cifra față de cel mai puternic reper simplu, citită la build din `reports/*/metrics.json`, și eticheta datelor (sintetic sau real);
  - Cheapest fix first: scara de soluții pe postul PT-1269 (271 V → 252 V, limita 253 V), cu costul fiecărui pas și ce s-a ales;
  - Not sure? It asks you.: cazul real cu încredere mică (Ineu, furtună, 58%), butonul „Hold to approve” (ține apăsat 1,2 s, apoi Undo), coada zilei (25 de cazuri: 17 abțineri, 7 peste plafonul regiunii, 1 încredere mică);
  - Every decision has a reason.: contorul MTR-011921 urmărit de la predicție la factorii SHAP, regula valoare față de cost (695 față de 293 lei), echipa, ora, jurnalul;
  - Results: „+49%” (din `reports/planner/agent_eval.json`), comparația cu cele 4 strategii simple, comenzile care refac fiecare cifră;
  - Demo (consola pe 3710, `/demo`, locul filmului de 30 s), echipa, notele cu sursele, „Not an official PPC product.”
- 18:12 Interacțiunile (textul care se aprinde, pașii hărții, butonul de aprobare) sunt într-un script inline, fără React: merg și deschise direct de pe disc (`landing/out/index.html`), pe serverul static și în dezvoltare. Verificat în toate trei.
- 18:15 Mobil verificat (390×844): harta din How it works stă fixă sus, pașii trec sub ea; fără depășiri pe lățime.
- 18:20 `git merge Teo` (planul demo nou, bilanțul nou): pagina preia singură cifrele noi; exemplele alese există în continuare.
- Capturi: `landing/design/captures/` (hero 1920 și mobil, How it works, modele, scara, omul în buclă, explicația, rezultatele).

## Urmează
- Review `web-design-guidelines` pe fișierele mele și reparațiile; contrast verificat pe toate textele; `prefers-reduced-motion` și `prefers-reduced-transparency`.
- Verificarea surselor pentru cifrele publice (ANRE, planurile RER) direct în documentele primare, unde se poate.
- Locul filmului: legătura când firul de prezentare are exportul (nu intră în repo).
- 08:00: capturi finale pentru prezentare, cererea pentru legătura din README.

## Blocaje
- niciunul

## Cereri către orchestrator
- (18:25) **Limba s-a schimbat**: Teo a cerut la 17:55 ca landing-ul să fie **în engleză** (tot textul), ca filmul. Titlurile sunt cele din film unde se potrivesc („Tomorrow’s crews, planned tonight.”, „Fallen poles. Stolen power. Too much sun.”, „Not sure? It asks you.”, „+49% more value. Same crews.”).
- (18:25) JURNAL, pentru `memory/journal.md` (eu nu scriu în `memory/`): „17:55 Teo, despre landing: totul în engleză, mai wow, mai premium, mai minimalist, stil Apple. Refăcut: hero centrat cu harta României din puncte înclinată ca un peisaj în zori, fontul sistemului (SF Pro), secțiuni cu o idee fiecare, povestea pe derulare, cifrele modelelor doar din reports/. Port 3730.”
- (18:25) Pentru README, când vreți: o legătură la landing, de exemplu „Pagina de prezentare: `cd landing && bun install && bun run build`, apoi `open landing/out/index.html` (merge și fără server)”. Nu am publicat nimic online.
- (17:20) Portul 3730, ca ați cerut.

## Cum se rulează (comenzile exacte)
- Dezvoltare: `cd landing && bun install && bun dev` → http://localhost:3730
- Export static: `cd landing && bun run build` → `landing/out/`; se deschide direct: `open landing/out/index.html` (fără server, cu toate interacțiunile)
- Exportul pe server: `cd landing && bun run preview` → http://localhost:3730
- `cd landing && bun run lint && bun run typecheck`
- Portul: **3730** (3720 e al previzualizării video).

## Cifre (doar din scripturi, cu comanda)
- Modelele: citite la build din `reports/<A|B|C|bilant>/metrics.json`; agentul din `reports/planner/agent_eval.json` (`uv run python -m cyberpunks.planner.evaluate --days 30 --seed 7 --meters 120`). Pe pagină, fiecare model e comparat cu **cel mai puternic** reper simplu din raport:
  - A, probleme subtile (Londra): precizia@K 62,5% față de 7,0% (regula simplă; regula VEE completă are 1,6%); SGCC: 80% față de 16% (Isolation Forest; VEE 11%). Precizia@K de 1,00 nu apare.
  - Bilanț: pierderea normală, eroare 5,4 față de 14,9 kWh/zi (formula fizică); diagnosticul cauzei F1 0,70 față de 0,48.
  - B: PR-AUC 0,278 față de 0,182 (regula pe rafale; climatologia are 0,151).
  - C: eroarea tensiunii 0,0054 față de 0,0228 pu; de circa 1.400 de ori mai rapid decât calculul de rețea complet.
  - Agentul: +49% valoare netă pe zi față de „primul venit, primul servit”, 352 față de 515 km pe zi (lume sintetică, 30 de zile).
- Planul demo (hero, How it works, cazurile): `outputs/demo/plans/demo-vara/` (instantaneul planificatorului).
- Cifrele publice (secțiunea Problem) au sursa și data în notele de subsol ale paginii.

## Decizii (cu ora)
- 17:18 Port 3730 (cererea orchestratorului).
- 17:19 Capturile site-urilor de referință: `agent-browser` headless, doar vizualizare (Jev nu salvează capturi).
- 17:19 Nimic peste 5 MB în git: `landing/node_modules`, `.next`, `out` ignorate; capturile în WebP (27-135 KB).
- 17:55 Teo: totul în engleză, stil Apple. Fontul sistemului (SF Pro pe Mac) cu Inter în rest, în locul lui Figtree; paleta PPC rămâne.
- 18:00 Hero: harta înclinată în 3D doar cu CSS, răsăritul PPC în spatele orizontului; o singură secvență la încărcare.
- 18:05 La modele, comparația e cu cel mai puternic reper simplu din fiecare raport, nu cu cel mai slab (la A, cifrele din fișier diferă de cele vechi din mesajul orchestratorului).
- 18:06 Textele cazurilor reale sunt compuse în engleză din câmpurile structurate (scor, fereastră, factori), nu traduse din textele românești ale planificatorului.
- 18:08 Am scos „la 15 minute” din texte: datele demo ale contoarelor sunt la 30 de minute (Londra).
- 18:12 Interacțiunile într-un script inline, fără hidratare: Next nu se poate hidrata de pe disc (file://), iar scriptul merge peste tot. `relativize.ts` rescrie doar src/href și url().
