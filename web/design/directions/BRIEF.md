# Brief comun: machete de direcție vizuală pentru „Tura de mâine”

Scris de firul Interfață (Teo-ui), 7 nov. 2026, 13:00. Trei direcții, același ecran, același conținut, ca Teo să compare doar limbajul vizual.

## Produsul și publicul

- „Tura de mâine”: consola dispecerului Rețele Electrice (distribuitorul PPC în Muntenia Sud, Dobrogea, Banat). Un agent AI decide unde merg mâine echipele de teren, pe baza a trei modele ML: A contoare defecte sau manipulate, B risc de avarii la furtună, C tensiune prea mare din cauza prosumatorilor (panouri solare).
- Publicul: dispecerul care pregătește tura de mâine și juriul PPC (oameni de date, AI și rețea), care vede ecranul pe un proiector 1920×1080 într-un demo de 5 minute și într-un video.
- Treaba principală a ecranului: în 5 secunde se vede unde merg echipele mâine, de ce, și ce n-a putut decide agentul singur („Nu sunt sigur”, decide un om).

## Ecranul de construit: „Planul de mâine”, static, 1920×1080

Un singur fișier HTML: `web/design/directions/<slug>.html`, care încarcă `./data.js` (`window.TURA`, date reale din `contracts/fixtures/`, sintetice), Google Fonts, MapLibre GL JS 5 de pe unpkg (`https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js` și `.css`). Pagina fixă 1920×1080 (`body` 1920×1080, fără scroll).

Conținut obligatoriu (toate cifrele vin din `window.TURA`; nu inventa altele):
1. Antet: semnul produsului (logoul se face în paralel; pune un semn geometric simplu de 20-24 px, de exemplu un semicerc de soare pe o linie) și numele „Tura de mâine”; data „Luni, 9 noiembrie 2026”; tura 08:00–16:00 (`TURA.shift`); proveniența datelor, vizibilă: „Date sintetice (exemple de test)”; butonul principal „Rulează agentul”.
2. Cifrele zilei (din `plan.summary`): 8 lucrări intrate, 7 valide, 1 în carantină; 3 alocate echipelor; 1 la om; 1 notificare; valoare așteptată 2.741 lei (2741,2); 31,4 km; 2 echipe folosite din 8 (`TURA.crews`).
3. Harta (MapLibre + OpenFreeMap, fără cheie): baze operative (`TURA.depots`), traseele din `plan.routes` (bază → opriri în ordinea `seq` → bază), toate lucrările din `TURA.work_items` colorate pe sursă (A, B, C), lucrarea trimisă la om (`A-20261109-MTR-027710`) marcată distinct, lucrările fără decizie (`B-20261109-IF-SNAGOV`, `C-20261109-PT-0877`) marcate ca „neplanificate”. `B-20261109-CT-MEDGIDIA` e în Constanța, departe de București: arat-o într-un mic locator al zonei Rețele Electrice (Muntenia Sud, Dobrogea, Banat) sau ca indicator la marginea hărții. Încadrează harta pe București-Ilfov plus Snagov.
   - Stiluri OpenFreeMap verificate (merg fără cheie): `https://tiles.openfreemap.org/styles/positron` (deschis), `.../bright`, `.../liberty`, `.../dark`, `.../fiord` (închise). După `load`, pune etichetele pe numele local: pentru fiecare strat `symbol` cu `text-field`, `map.setLayoutProperty(id, 'text-field', ['get', 'name'])` (altfel apare „Bucharest” în loc de „București”). Poți recolora straturile (`setPaintProperty`) ca harta să intre în paletă. Păstrează atribuirea OpenFreeMap/OpenStreetMap vizibilă, compactă.
   - Traseele: planificatorul nu dă geometria drumului, doar ordinea și km. Desenează segmentele ca arce ușor curbate (Bézier eșantionat), ca să fie clar că arată ordinea, nu drumul exact.
4. Echipele: `E-BV-2` (2 opriri: 08:25 contor MTR-004217, 40 min, 6,1 km; 09:50 contor MTR-019833, 40 min, 11,8 km; total 29,0 km, 80 min lucru, 95 min drum) și `E-BV-3` (11:00 PT-1432, 120 min, 2,4 km, cere întrerupere planificată; total 4,8 km). Din cifrele planului reies: E-BV-2 pleacă 08:00, oprirea 1 08:25–09:05, oprirea 2 09:50–10:30, revine ~10:55; E-BV-3 pleacă ~10:53, lucrează 11:00–13:00, revine ~13:07. Celelalte 6 echipe n-au lucrări: arată-le compact („6 echipe libere”).
5. „Nu sunt sigur” (coada pentru om): `A-20261109-MTR-027710`, motivul „doar 11 zile de istoric după montare”, scor 0,52 (interval 0,34–0,60), încredere scăzută; acțiuni: Aprobă, Respinge, Amână.
6. Alerta: „Risc de avarii în zona Medgidia”, avertisment: „Rafale de 85 km/h între 12:00 și 20:00. Recomand o echipă în zonă de la 11:00.”
7. Carantina: 1 lucrare respinsă la intrare, `A-20261109-MTR-BAD`: latitudine 51,5 (în afara României) și scor 1,4 (imposibil).
8. Detaliul lucrării selectate (panou sau suprapunere): `A-20261109-MTR-004217`, contor din București, sectorul 6, suspect de manipulare (`tamper`), scor 0,87 (0,69–0,95), încredere mare, semnal de siguranță; factorii cu contribuția lor ca bare: „9 zile la rând cu consum zero” +0,31, „cu 72% sub vecinii de pe același post” +0,22; caz similar SGCC-0193, furt confirmat, similaritate 0,91; regula `R-VALUE-OVER-COST`: valoarea așteptată 1.239,75 lei depășește costul vizitei (180 lei, ipoteză din `config/economics.yaml`); urmărirea: ID-ul predicției 69136ff3…, modelul `a-lgbm@fixture`.

Codurile surselor, aceleași în toate direcțiile: A = Contoare, B = Furtună, C = Tensiune. Culoarea nu e singurul indiciu: markerii poartă litera sursei.

## Scriere

- Română, cu diacritice corecte (ș, ț cu virgulă). Cuvinte simple, din perspectiva dispecerului. Numere în format românesc: 2.741 lei, 0,87, 31,4 km, ore 24h (08:25).
- Butoanele spun exact ce fac („Rulează agentul”, „Aprobă”). Fără texte de umplutură, fără lorem ipsum.

## Ce evităm (semnele unui design generat automat)

Etichete cu majuscule peste tot; eticheta mică deasupra fiecărui titlu; șiruri de meta legate cu puncte la mijloc („A · B · C”); etichete „CUVÂNT — fragment”; font monospace pentru etichetele mici de date; „→” lipit de butoane; carduri rotunjite identice, cu aceeași umbră gri; degradeuri decorative; un singur cuvânt colorat în titlu; numerotare decorativă (01/02/03) pe conținut care nu e o secvență.

## Calitate

- Contrast AA (text ≥ 4,5:1, text mare și elemente grafice ≥ 3:1). Lizibil pe proiector: text de bază ≥ 15 px, etichete ≥ 13 px. Cifre tabulare (`font-variant-numeric: tabular-nums`).
- Stiluri `:focus-visible` vizibile pe butoane (chiar dacă macheta e statică).
- O singură idee memorabilă pe ecran; restul liniștit și disciplinat.

## Captură și verificare (obligatoriu)

- Pagina setează `window.__ready = true` după `document.fonts.ready` și după evenimentul `idle` al hărții.
- Captura, cu sesiunea ta de browser (QA local):
  ```bash
  export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix dir-<slug>)"
  agent-browser set viewport 1920 1080
  agent-browser open file:///Users/teo/.t3/worktrees/CyberPunks/Teo-ui/web/design/directions/<slug>.html
  agent-browser wait --fn "window.__ready === true"
  agent-browser screenshot /Users/teo/.t3/worktrees/CyberPunks/Teo-ui/web/design/directions/<slug>.jpg (după captură, salvată ca JPG)
  ```
  Uită-te la captură (citește PNG-ul), repară ce nu merge (text tăiat, suprapuneri, diacritice, contrast), refă captura. La final `agent-browser close`.
- Scrii doar în `web/design/directions/` (fișierele tale: `<slug>.html`, `<slug>.jpg (după captură, salvată ca JPG)`). Fără `git commit`, `git push`, `git stash`. Alt agent construiește în paralel aplicația Next.js în `web/`: nu atinge nimic altceva.
