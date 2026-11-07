# Status: Teo-bilant
Actualizat: 2026-11-07 14:38
Milestone curent: M3 făcut (robustețe, analiza erorilor, planul B), M4 aproape (docs, fișa modelului)
Gata de merge: da (commit 35eb179)

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
1. **Prezentarea:** cifra pentru bilanț e „vede 48% din energia pierdută pe care contoarele nu o văd” plus planul B (36% față de 20%). Cifra „cu bilanț față de fără” doar ca sensibilitate: câștig când modelul de contoare e mai slab (SGCC: lei în primele 10 de 3,6 ori), zero cu scorurile actuale ale lui A. Vă rog transmiteți firului de prezentare.
2. **Planificatorul:** ordinea contează pentru deduplicare. `cyberpunks.a_contoare.predict` trebuie să ruleze înaintea `cyberpunks.a_bilant.predict` (bilanțul citește `A.jsonl` ca să nu dubleze). Apoi `fuse`.
3. **C:** `extra.phase_rebalance_input` pe lucrările `pierdere_tehnica` (PT-1269: pierderi de 2,2 ori normalul, faza estimată ~68%, adevărul 76/15/9).
4. **`memory/journal.md`:** „14:37 bilanț: fuziunea doar confirmă (pe scorurile reale ale lui A, coborârea strica clasamentul); cifra 0,15/0,09 retrasă; cifra pentru prezentare: 48% din energia pierdută e invizibilă la contoare.”

## Cum se rulează (comenzile exacte)
- `make c-weather` (o dată), `make bilant-data` (~1 min), `make bilant-eval` (~5 min: modele, metrici, planul B, analiza erorilor), `make bilant-predict`, `uv run python -m cyberpunks.a_bilant.demo_story`, `make bilant-test`.
- Lotul hărții citește `outputs/work_items/demo-vara/A_ground_truth.csv`; dacă lipsește, rulează singur `a_contoare.predict`.

## Cifre (doar din scripturi, cu comanda `make bilant-data bilant-eval`)
SIMULARE pe date publice. Test: cele 300 de posturi ale registrului C (rețele nevăzute).
- Pierderea normală: MAE 5,30 kWh/zi (formula fizică 14,91; procent fix 20,59); fără istoric 12,56; acoperirea P10-P90 88,1%; mediana pierderii 3,8% din energia care trece prin post.
- Diagnosticul: F1 macro 0,61 față de 0,48 la reguli; furt înainte de contor 0,66 față de 0,35; contor de post ×2 0,99; se abține în 15,1% din ferestre.
- Energia invizibilă la contoare: 48%. Planul B: 36% față de 20%. Fuziunea: tabelul de mai sus.

## Decizii (cu ora)
- 13:35-14:04: vezi istoricul (registrul C, calibrarea ×2,5, două modele normale, creșterea lipsei în fuziune, contorul ×2 valorează 2 deplasări, întâi citire la distanță).
- 14:25: defectele lui A intră în lumea bilanțului (contorul k = clientul k), ca fuziunea să fie testată pe aceleași probleme.
- 14:30: fuziunea doar confirmă; testul pe mai multe zile trece pe lotul train (lotul hărții are acum defectele lui A, apărute doar în ultimele 60 de zile).
- 14:35: rezolvarea automată a lui „nu sunt sigur” e oprită (0 din 5 corecte pe demo).
- 14:35: bilanțul lasă lui A posturile unde A are deja lucrare la om sau pe contor.
