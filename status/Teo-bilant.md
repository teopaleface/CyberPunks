# Status: Teo-bilant
Actualizat: 2026-11-07 17:36
Milestone curent: M4 făcut; contorul martor și Weave gata (termen 20:00). **Sunt liber**, de acum doar reparații.
Gata de merge: da (commit a95ea59)

## Răspuns la cererea orchestratorului de la 17:25 (contorul martor, Weave): gata, sunt liber
**Ce s-a schimbat**
1. **Regula contorului martor** (`src/cyberpunks/a_bilant/martor.py`; o regulă, nu un model ML). Compară contorul de balanță cu martorul pe ultimele 3 zile; o diferență peste **0,5%** (clasa de exactitate) înseamnă contor de balanță defect sau setat greșit, cazul „2×”. Dacă martorul confirmă contorul, iar modelul spusese „contor setat greșit”, se alege a doua cauză a modelului.
   - În simulare, martorul există la 50% din posturi (IPOTEZĂ), iar eroarea fixă a celor două contoare e de 0,07%. Diferența normală are mediana **0,06%**, în linie cu „poate 0,1%” spus de mentor.
   - Pragul stă temporar în modul, cu sursa în comentariu. **Cerere către planificator:** cheia `config/economics.yaml` → `meters.martor_diff_limit_pct: 0.5` (SURSĂ: Codul de măsurare ANRE, Ord. 103/2015, contor martor de cel puțin aceeași clasă; clasa 0,5S).
   - Bilanțul post − clienți **nu** folosește pragul de 0,1-0,5%: acolo pierderea normală e de câteva procente și o învață modelul (eroare medie 5,40 kWh/zi; formula fizică 14,92).
2. **Termenii PPC:** „contor de balanță” și „contor martor” în toate textele (cod, explicațiile lucrărilor, documentație, rapoarte). Lucrările au `extra.martor_check` (diferența, pragul, verdictul).
3. **Baza legală, citată:** Codul de măsurare ANRE (Ord. 103/2015): „cel puţin un contor de balanţă la fiecare post de transformare, pentru a facilita identificarea pierderilor tehnice şi netehnice”. Apare în `docs/research/bilant.md`, în `reports/bilant/model_card.md` și în `reports/bilant/headline.md` (textul pentru prezentare).
4. **Weave (date reale UK), ca verificare de realism, nu ca etichete** (`weave_check.py`, `reports/bilant/weave_check.md`, `.png`). Mostra de o zi (~38 MB, în afara git, cu sha256 în docs) are ~42.000 de posturi reale. Forma curbei e apropiată:
   - factorul de încărcare: 0,57 real, 0,51 simulat;
   - ponderea nopții: 0,17 real, 0,16 simulat;
   - vârful: la 18:00 real, la 19:00 simulat;
   - prânzul simulat e mai jos din cauza prosumatorilor.
   Folosirea Weave pentru profilele din simulare rămâne îmbunătățire viitoare. Fișierul complet (700 MB) nu l-am descărcat. NGED LV Load Monitor (cu cont) nu l-am încercat.

**Cifrele (test pe aceleași 300 de posturi, `make bilant-data bilant-eval`)**
- Regula martorului: prinde **98%** din contoarele de balanță setate greșit pe posturile cu martor, cu **0** alarme false. F1 pentru „contor de balanță setat greșit” pe acele posturi: 0,97 doar cu modelul, **0,99** cu regula.
- Diagnosticul pe același test nou: **0,704 cu regula, 0,703 fără**, deci regula se păstrează. Față de 16:12 (0,714), lumea simulată e alta (eroarea contoarelor de balanță trecută la 0,07%, ca martorul să aibă diferența reală). Testul s-a schimbat; nu e o regresie a modelului.
- Cifrele pentru slide rămân: **85% din energia pierdută din cauzele pe care contoarele nu le văd, ~25.000 lei pe lună** (A = 0); **48%** din energia pierdută e invizibilă la contoare.
- Planul B: 30% față de 20% la întâmplare (înainte 36%, pe lumea veche).
- **Postul pentru demo rămâne PT-1269:** bilanțul vede acum pierderi de 2,4 ori normalul și o fază cu ~71% din case (adevărul 76/15/9). C are `C-20250708-PT-1269`, cu `phase_rebalance` prima treaptă.
- Lucrări demo-vara: 75, toate pe posturi cu probleme reale; 0 suprapuneri cu A la om. `make check`: 287 trec.

## Regula de la 17:15 (fără fișiere grele): verificat, sunt liber
- Bilanțul nu are în git nici modele, nici mostre de date. `models/bilant/` (~22 MB) și `data/processed/bilant/` sunt ignorate și se refac cu `make bilant-eval` / `make bilant-data`, iar `predict.run` le reface singur dacă lipsesc. Cel mai mare fișier al firului în git e o figură de 206 KB (`reports/bilant/normal_loss.png`).
- `tests/test_repo_size.py` trece; `make check`: 277 trec.

## Răspuns la cererea orchestratorului de la 17:05 (sunt liber)
- `reports/bilant/headline.md` și `reports/bilant/demo_posts.md` se scriu acum la **`make bilant-predict`**, după lucrări. `make bilant-eval` nu le mai atinge, deci nu mai apare „rulează întâi make bilant-predict”.
- Ordinea pentru `docs/REPRODUCERE.md`: `make c-weather` → `make bilant-data` → `make bilant-eval` → `make bilant-predict` → `make bilant-test`. Pasul separat `demo_story` nu mai e nevoie, e inclus în `bilant-predict`. Actualizat și în `docs/data/bilant.md`.
- Verificat local: după `make bilant-predict`, pagina are PT-1269 cu cifrele lui. `make check`: 276 trec.
- Lucrări demo-vara cu A-ul curent: 76, toate pe posturi cu probleme reale. Numărul depinde de `A.jsonl` (deduplicare); metricile nu.

## Răspuns la cererea orchestratorului de la 16:40 (sunt liber)
1. **Diagnosticele.** Cifrele din cerere erau vechi: clientul la postul greșit e la **0,77** (de la 16:12, cu identificarea topologiei din tensiuni), iar contorul de client la 0,40. Am mai încercat două lucruri pe același test, fără câștig, deci **modelul rămâne cel actual** (F1 macro 0,714):
   - lot de antrenare nou, cu defecte de contor trase ca la A (`train2`): F1 macro 0,594 singur și 0,706 împreună cu lotul vechi;
   - ponderile claselor: 0,714-0,716. Contorul de client urcă la 0,43 doar dacă clientul la postul greșit coboară la 0,74.
   Reproductibil: `uv run python -m cyberpunks.a_bilant.experiments` → `reports/bilant/experiments.md`.
2. **Cifrele pentru slide** (din `reports/bilant/headline.md`, generat din `metrics.json`):
   - **„Bilanțul găsește 85% din energia pierdută pe care contoarele nu o văd deloc: ~25.000 lei pe lună pe 300 de posturi.”** (furt înainte de contor, cabluri, contor de post setat greșit, client la postul greșit; A găsește 0 aici prin construcție)
   - **„48% din energia pierdută nu apare la niciun contor de client.”** (ziua demo)
   - **„Cauza corectă: F1 0,71, față de 0,48 la regulile clasice.”** Opțional: contorul postului setat greșit e prins în 99% din cazuri, clientul trecut la alt post cu precizie 91%.
   - De nu pus pe slide ca cifră principală: „cu bilanț față de fără” la clasarea contoarelor (zero câștig cu scorurile reale ale lui A).
3. **Postul pentru prezentare: PT-1269**, împreună cu **firul C**:
   - bilanțul: `A-20250708-PT-1269` (`grid_inspection`), pierderi pe cabluri de 2,2 ori normalul, faza estimată ~69% din case (adevărul 76/15/9), în `extra.phase_rebalance_input`;
   - C: `C-20250708-PT-1269` (tensiune prea mare), cu `phase_rebalance` prima treaptă în `extra.remedy_options`;
   - mesajul: o singură mutare a câtorva case pe altă fază rezolvă și pierderile (bilanț), și tensiunea (C). Seria: `outputs/series/demo-vara/A-20250708-PT-1269.json`.

## Postul pentru prezentare și interfață
- **PT-1269**: dezechilibrul de faze găsit de bilanț e intrarea pentru `phase_rebalance` la C.
  - Lucrarea bilanțului: `A-20250708-PT-1269` (`grid_inspection`), cu `extra.phase_rebalance_input` = pierderea pe cabluri de 2,2 ori normalul și faza estimată ~69% din case. Adevărul din simulare: 76/15/9.
  - Lucrarea lui C pe același post: `C-20250708-PT-1269` (tensiune prea mare), cu `phase_rebalance` prima treaptă în `extra.remedy_options`.
  - Seria: `outputs/series/demo-vara/A-20250708-PT-1269.json`.
- Celelalte cazuri verificate (`reports/bilant/demo_posts.md`):
  - contorul A confirmat de bilanț;
  - contorul postului ×2;
  - perechea cu client mutat: PT-1155 și PT-1029, prinse amândouă, cu `office_correction`.

## Răspuns la cererea orchestratorului de la 15:50
1. **M4: verificat dintr-o clonă curată** (`git clone --branch Teo-bilant`, apoi exact comenzile din `docs/data/bilant.md`, de la `uv sync` la `make bilant-test`, ~10 minute, fără intervenție). Toate cele 142 de cifre din `metrics.json` au ieșit identice, iar `A_bilant.jsonl` a avut aceleași lucrări. Comenzile exacte, timpii și ieșirile sunt în `docs/data/bilant.md` (secțiunile „Comenzile” și „Verificarea dintr-o clonă curată”), pentru `docs/REPRODUCERE.md`.
2. **Cifra principală, după ce A a trecut pe registrul C:** `reports/bilant/headline.md`, generat din `metrics.json` de `uv run python -m cyberpunks.a_bilant.headline` (inclus în `make bilant-eval`).
   - **Cauzele pe care contoarele nu le văd (A = 0):** bilanțul găsește postul la 74% din furturile înainte de contor (cauza corectă 55%), 64% din pierderile tehnice (42%), 99% din contoarele de post setate greșit (99%) și 53% din clienții la postul greșit (42%). **Total: 85% din energia pierdută din aceste cauze, ~25.100 lei pe lună** pe cele 300 de posturi. Din posturile marcate, 13% sunt de fapt normale. În ziua demo, 48% din energia pierdută e invizibilă la contoare.
   - **Mai multe K, deplasări degeaba evitate:** la calitatea lui A pe Londra, 0,20 / 0,28 / 0,28 / 0,05 pe zi la K = 10 / 20 / 50 / 100; lei pe zi de la 824 la 855 (K = 10) și de la 1.177 la 1.458 (K = 50). La calitatea pe SGCC, lei pe zi de la 126 la 456 (×3,6). Cu scorurile reale ale lui A: 0 până la K = 300, iar la K = 500 cu 12 deplasări degeaba mai mult. **Pentru prezentare recomand cifra cu cauzele (85%, ~25.000 lei pe lună, A = 0), nu clasarea contoarelor.**
3. **Clientul la postul greșit:** de la 0,57 la **0,77** (precizie 0,91, recall 0,67), cu identificarea topologiei din tensiuni. Contorul cu tensiunea cea mai ciudată dintr-un post seamănă mai bine cu un vecin decât cu postul lui (`dataset.voltage_topology`, `volt_elsewhere`, `volt_claimed`; metoda din literatură: Short 2013, comparația din 2022). Pierderea tehnică a urcat la 0,52. F1 macro: **0,71** față de 0,48 la reguli.
- Lucrări demo-vara: 74, toate pe posturi cu probleme reale. La om: 11 posturi, 0 suprapuneri cu A (A: 138). `make check`: 257 trec.

## Răspuns la cererea orchestratorului de la 14:50
- `git merge Teo` făcut. `reports/bilant/metrics.json` din `Teo` era identic cu al meu (bilant-lgbm@4b1ad06). Acum e regenerat, cu cifrele de mai jos.
1. **Mai multe K și deplasări degeaba evitate** (`reports/bilant/fusion_k.png`, `metrics.json`, `fuziune_*`, `fuziune_sgcc_*`, `fuziune_a_real_*`). Câștigul rămâne mic la clasarea contoarelor:
   - calitatea lui A pe Londra: deplasări evitate 0,20 / 0,28 / 0,28 / 0,05 pe zi la K = 10 / 20 / 50 / 100; lei pe zi de la 824 la 855, de la 921 la 1.000, de la 1.177 la 1.458, de la 1.370 la 1.587;
   - calitatea lui A pe SGCC: 0,15 / 0,25 / 0,25 / 0,40 deplasări evitate; lei pe zi de la 126 la 456 (K = 10);
   - scorurile reale ale lui A: 0 până la K = 300.
2. **Cauzele pe care contoarele nu le văd deloc (A = 0)** (`reports/bilant/bilant_only_causes.png`, `cauze_post_*`). Bilanțul găsește postul în 74% din ferestrele cu furt înainte de contor (cauza corectă 55%), 65% la pierderea tehnică (42%), 99% la contorul postului setat greșit (99%) și 50% la clientul la postul greșit (30%). Asta înseamnă **85% din energia lipsă din aceste cauze, ~25.000 lei pe lună** pe cele 300 de posturi. Din posturile marcate, 13% sunt de fapt normale. Plus 48% din energia pierdută în ziua demo e invizibilă la contoare. **Asta propun ca cifră principală.**
3. **Diagnosticele slabe:**
   - clientul la postul greșit: de la **0,32 la 0,57** (precizie 0,83), cu trăsătura „oglindă” (lipsa zilnică la un post corelată negativ cu surplusul vecinului) și cu legarea celor două capete ale perechii (`diagnose.pair_consistency`);
   - pierderea tehnică: de la 0,36 la **0,46**, cu forma orară a lipsei (a + b·sarcină + c·sarcină², acum față de luna trecută) și raportul față de normal;
   - F1 macro: de la 0,61 la **0,67** (reguli 0,48), exactitate 0,81.
   - Am încercat și comparația cu normalul fără istoric (doar GIS): pierderea tehnică a urcat la 0,47, dar F1 macro a scăzut la 0,66. N-am păstrat-o.
4. **`error_analysis.md`, secțiunea 4:** unde ajută bilanțul (cauzele de post, energia invizibilă, diagnosticul, planul B, modelele de contoare slabe) și unde nu (clasarea contoarelor deja găsite de A, coborârea scorurilor, rezolvarea lui „nu sunt sigur”, contorul de client la defectele lui A cu F1 0,38).
- Lucrări demo-vara: 85, valide; 84 pe posturi cu probleme reale. Fără dubluri cu A: 6 posturi „nu sunt sigur” și 62 de posturi cu contor de client lăsate lui A. `make check`: 243 trec.

## Răspuns la cererea orchestratorului de la 14:20
1. **`git merge Teo` făcut.** Contoarele lui A sunt acum pe posturile registrului C. Fuziunea le folosește direct; „legătura aproximativă” mai rămâne doar pentru un `post_id` necunoscut.
2. **Lumea bilanțului are acum exact defectele lui A.** Contorul k al lui A pe un post = clientul k din simulare, cu același tip și aceeași zi de început (`dataset.apply_a_truth`, din `A_ground_truth.csv`, 865 de probleme). Lipsa din bilanț corespunde deci defectelor reale ale lui A.
3. **Evaluarea „cu bilanț față de fără”, refăcută** (`reports/bilant/model_card.md`, tabelul complet; `metrics.json`, `fuziune_*`, `fuziune_sgcc_*`, `fuziune_a_real_*`):
   - scor A simulat, calitatea lui A pe Londra (AUC 0,907), mai multe zile: precizia în primele 10 crește de la 10,2% la **12,2%** (în primele 20: de la 6,4% la 7,7%; 50: de la 4,0% la 4,5%; 100: de la 2,6% la 2,7%). Deplasări degeaba evitate: 0,2-0,3 pe zi. Lei pe zi în primele 10: de la 824 la 855; în primele 50: de la 1.177 la 1.458;
   - aceeași comparație la calitatea lui A pe SGCC (AUC 0,80): în primele 10, de la 2,5% la **4,0%**, iar lei pe zi cresc de la 126 la **456**;
   - **scorurile reale ale lui A**, ziua demo, 15.850 de contoare: precizie 100% cu și fără bilanț până la K = 300; la K = 500: 93,0% fără, 90,6% cu. **Câștig zero.** A e deja precis în vârf, iar cele două lumi (curbele din Londra ale lui A, SimBench la bilanț) împart doar contorul și ziua;
   - **cifra 0,15 față de 0,09 nu mai e valabilă.** Venea din coborârea scorului contoarelor pe posturi curate (concedii), iar pe scorurile reale ale lui A coborârea strica (AUC 0,918 → 0,907). Fuziunea **doar confirmă** acum (AUC 0,919, nu ascunde niciun contor găsit de A). Am încercat și o fuziune învățată, validată pe posturi lăsate deoparte: AUC 0,915, tot fără câștig.
   - **Ce propun pentru prezentare:** bilanțul vede **48% din energia pierdută** pe care niciun contor de client nu o vede (furt înainte de contor 595 kWh/zi, pierderi tehnice peste normal 861, client la postul greșit 309; contoarele defecte 1.892 kWh/zi, ziua demo, `invizibil_*`). În plus spune cauza pe post (F1 0,61 față de 0,48 la reguli).
4. **Trimiterile la om:** bilanțul și A nu mai trimit același post la om (suprapunere **0**, verificat pe demo-vara). Bilanțul lasă lui A 6 posturi „nu sunt sigur” unde A trimite deja un contor la om, plus 57 de posturi de tip „contor de client” unde A are deja lucrarea pe contor (`extra.left_to_A` în starea postului; fuziunea confirmă lucrarea lui A). Bilanțul trimite la om **11** posturi; A trimite 117. Am încercat ca bilanțul să rezolve „nu sunt sigur” al lui A (citire la distanță în loc de om), dar cele 5 cazuri rezolvate pe demo nu aveau nicio problemă reală. Codul există, e oprit (`fuse.RESOLVE_ABSTAIN = False`). Restul de ~186 la om din plan nu vine din bilanț: 11 sunt ale mele, 117 ale lui A (după fuziune la fel), restul sunt B/C/planificator.

## Făcut (de la M2)
- Robustețe (`inputs.py`): contor de post lipsă → planul B; ore dublate; Wh → kWh; polaritate inversată; ore lipsă. Legate în rularea zilnică, cu 3 cazuri de test vizibile în demo (PT-1003 Wh, PT-1007 fără contor de post, PT-1011 ore dublate).
- Clientul suspect, din semne clare (zero, blocat, negativ) înainte de scădere: corect în 21 din 45 de posturi, față de 4 din 45 cu metoda veche.
- Planul B (`reports/bilant/plan_b.md`): montând contoare la 20% din posturi după model, găsești 36% din energia lipsă (la întâmplare 20%, posturile mari întâi 23%); ~3.530 lei pe an per contor, față de ~1.960. Gradul de integrare 56-67% e în raport.
- Analiza erorilor (`reports/bilant/error_analysis.md`), fișa pentru prezentare (`reports/bilant/demo_posts.md`, cazuri verificate cu adevărul), fișa modelului, `docs/data/bilant.md`, verdictele după vizită ca etichete (`feedback.py`).
- Teste: 24 în `tests/bilant/` (redenumite `test_bilant_*` după conflictul de nume cu A); `make check`: 225 trec.

## Urmează
- M4: verificare dintr-o clonă curată (`make c-weather bilant-data bilant-eval bilant-predict`), ultimele retușuri la documentație.
- Dacă e timp: clientul la postul greșit (F1 0,37) și contorul de client în lumea cu defectele lui A (F1 0,33; multe tipuri ale lui A nu schimbă totalul zilei).

## Blocaje
- Niciunul.

## Cereri către orchestrator
1. **Prezentarea:** cifra pentru bilanț e „găsește 85% din energia lipsă din cauzele pe care contoarele nu le văd (furt înainte de contor, cabluri, contor de post, client la postul greșit), ~25.000 lei pe lună pe 300 de posturi; A are 0 acolo”, plus „48% din energia pierdută e invizibilă la contoare” și planul B (36% față de 20%). Cifra „cu bilanț față de fără” doar ca sensibilitate: câștig când modelul de contoare e mai slab (SGCC: lei în primele 10 de 3,6 ori), zero cu scorurile actuale ale lui A. Vă rog transmiteți firului de prezentare.
2. **Planificatorul:** ordinea contează pentru deduplicare. `cyberpunks.a_contoare.predict` trebuie să ruleze înaintea `cyberpunks.a_bilant.predict` (bilanțul citește `A.jsonl` ca să nu dubleze). Apoi `fuse`.
3. **C:** `extra.phase_rebalance_input` pe lucrările `pierdere_tehnica` (PT-1269: pierderi de 2,2 ori normalul, faza estimată ~68%, adevărul 76/15/9).
4. **`memory/journal.md`:** „14:37 bilanț: fuziunea doar confirmă (pe scorurile reale ale lui A, coborârea strica clasamentul); cifra 0,15/0,09 retrasă; cifra pentru prezentare: 48% din energia pierdută e invizibilă la contoare.”

## Cum se rulează (comenzile exacte)
- `make c-weather` (o dată), `make bilant-data` (~1 min), `make bilant-eval` (~5 min: modele, metrici, planul B, analiza erorilor), `make bilant-predict`, `uv run python -m cyberpunks.a_bilant.demo_story`, `make bilant-test`.
- Lotul hărții citește `outputs/work_items/demo-vara/A_ground_truth.csv`; dacă lipsește, rulează singur `a_contoare.predict`.

## Cifre (doar din scripturi, cu comanda `make bilant-data bilant-eval`)
SIMULARE pe date publice. Test: cele 300 de posturi ale registrului C (rețele nevăzute).
- Pierderea normală: MAE 5,30 kWh/zi (formula fizică 14,91; procent fix 20,59); fără istoric 12,56; acoperirea P10-P90 88,1%; mediana pierderii 3,8% din energia care trece prin post.
- Diagnosticul: F1 macro 0,71 față de 0,48 la reguli; client la postul greșit 0,77 față de 0,34; furt înainte de contor 0,70 față de 0,35; pierdere tehnică 0,52 față de 0,28; contor de post ×2 0,99; se abține în 12,7% din ferestre.
- Cauzele de post (A = 0): găsite 74% / 64% / 99% / 53%; 85% din energie, ~25.100 lei pe lună.
- Energia invizibilă la contoare: 48%. Planul B: 36% față de 20%. Fuziunea: tabelul de mai sus.

## Decizii (cu ora)
- 13:35-14:04: vezi istoricul (registrul C, calibrarea ×2,5, două modele normale, creșterea lipsei în fuziune, contorul ×2 valorează 2 deplasări, întâi citire la distanță).
- 14:25: defectele lui A intră în lumea bilanțului (contorul k = clientul k), ca fuziunea să fie testată pe aceleași probleme.
- 14:30: fuziunea doar confirmă; testul pe mai multe zile trece pe lotul train (lotul hărții are acum defectele lui A, apărute doar în ultimele 60 de zile).
- 14:35: rezolvarea automată a lui „nu sunt sigur” e oprită (0 din 5 corecte pe demo).
- 14:35: bilanțul lasă lui A posturile unde A are deja lucrare la om sau pe contor.
- 17:30: regula contorului martor (0,5%, pe ultimele 3 zile) peste model; eroarea contoarelor de balanță 0,07% (diferența normală martor ~0,1%, mentorul PPC); Weave doar ca verificare de realism.
- 17:15: fără fișiere grele în git: modelele și datele bilanțului rămân în afara git, refăcute din comenzi.
- 16:55: lotul train2 și ponderile claselor încercate pe același test, fără câștig: modelul rămâne neschimbat.
- 16:20: identificarea topologiei din tensiuni pentru clientul la postul greșit; extinderea regulii de pereche testată și lăsată deoparte (0,567 → 0,574, zgomot).
- 15:00: trăsătura „oglindă” și legarea perechii pentru clientul la postul greșit; forma orară a lipsei pentru pierderea tehnică; comparația cu normalul fără istoric, scoasă (F1 macro mai mic).
