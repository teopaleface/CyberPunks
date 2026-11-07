# Fișa modelului: bilanț pe post (`bilant-lgbm`)

**Simulare pe date publice, gândită pentru datele PPC.** Toate cifrele de aici vin din `make bilant-data bilant-eval` (`reports/bilant/metrics.json`). Datele de test sunt 100% sintetice.

## Baza legală

Codul de măsurare a energiei electrice (ANRE, Ord. 103/2015, copie: https://reteleelectrice.ro/wp-content/uploads/cod-masurare-2015.pdf): „Sistemele de măsurare inteligentă trebuie să permită integrarea a cel puţin un contor de balanţă la fiecare post de transformare, pentru a facilita identificarea pierderilor tehnice şi netehnice.” Același cod definește contorul martor: „contor de energie electrică având rolul de a măsura energia electrică în paralel cu contorul de decontare”, cu cel puțin aceeași clasă de exactitate, pe aceleași circuite.

## Ce face

Pentru fiecare post de transformare și fiecare zi:

1. **Bilanțul**: lipsa = energia ieșită din post (contorul de balanță) − suma contoarelor clienților din bază, în kWh și lei.
2. **Pierderea normală** (modelul 1): cât ar trebui să lipsească azi la acest post, cu interval P10-P90.
3. **Diagnosticul** (modelul 2): de ce lipsește mai mult. Șase clase: normal, contor de client, furt înainte de contor, pierdere tehnică, client la postul greșit, contorul postului setat greșit.
4. **Lucrarea**: valoarea = probabilitatea × energia lipsă × prețul. Acțiunile, de la ieftin la scump: întâi citire la distanță, apoi verificare, echipă de rețea, corecție în birou fără deplasare, urmărire, decizie umană.
5. **Regula contorului martor** (unde postul are martor): dacă contorul de balanță și martorul diferă cu peste 0,5% (clasa de exactitate), contorul de balanță e defect sau setat greșit. E o regulă, nu un model. Mentorul PPC: diferența normală e ~0,1%. Atenție: pragul de 0,5% nu se folosește la bilanțul post − clienți, unde pierderea normală e de câteva procente.
6. **Fuziunea cu A**: confirmă sau infirmă contoarele marcate de modelul A, după cât lipsește la postul lor.

Deciziile le iau modelele noastre și regulile scrise în cod. LLM-ul nu decide nimic aici.

## Modelele

| | Modelul 1: pierderea normală | Modelul 2: diagnosticul |
|---|---|---|
| Algoritm | LightGBM, regresie cuantilă P10/P50/P90, interval calibrat (conformal pe 20% din posturile de antrenare) | LightGBM multiclasă, clase echilibrate |
| Trăsături | Σ\|P\|, Σ P², energia injectată, formula fizică ΣP²·R/U², cablurile din GIS, temperatura, radiația, istoricul robust al postului (cuantilele 20 și 50 ale raportului, 120 de zile, oprit cu 14 zile înainte) | 25 de trăsături pe fereastra de 14 zile (`windows.WIN_FEATURES`) |
| Variante | cu istoric; fără istoric (post nou) | - |
| Antrenare | 300 de posturi sintetice (`train`), zilele fără probleme | ferestrele lotului `train`, cu pierderea normală prezisă fără ca postul să fi fost văzut (3 grupe) |
| Test | cele 300 de posturi ale hărții (registrul C), rețele nevăzute | idem, 13.200 de ferestre |

## Rezultatele (test, rețele nevăzute)

Pe lotul hărții, defectele de contor sunt exact cele ale firului A (`A_ground_truth.csv`, 865 de contoare). Contorul k al lui A pe un post e clientul k din lumea bilanțului.

| Ce | Modelul nostru | Metoda simplă |
|---|---|---|
| Pierderea normală, MAE (kWh/zi) | **5,40** (15% din 37,0) | formula fizică I²R 14,92; procent fix 20,62 |
| Același, fără istoricul postului | 12,49 | - |
| Acoperirea intervalului P10-P90 | 88,1% | formula fizică 86,6% (interval de ~10 ori mai larg) |
| Diagnosticul v2, F1 macro (model + regula martorului) | **0,75** | v1 (rezerva) 0,70; tabelul de reguli din concept 0,48 |
| Diagnosticul v2, exactitate | 0,86 | v1 0,82; reguli 0,78 |
| Regula contorului martor (posturile cu martor): contoare de balanță setate greșit prinse | **98%**, 0 alarme false | doar modelul: F1 0,97; cu regula 0,99 |
| Primele 10 posturi pe zi prind din energia lipsă | 85% | 80% |
| **Energia pierdută pe care niciun contor de client nu o vede** (furt înainte de contor, pierderi tehnice peste normal, client la postul greșit), ziua demo | **48%** | o vede doar bilanțul |
| Planul B: energia lipsă găsită cu contoare de balanță la 20% din posturi | **30%** | la întâmplare 20%; posturile mari întâi 23% |

F1 pe clase (model / reguli): contor de balanță setat greșit 0,99 / 0,87, normal 0,91 / 0,90, client la postul greșit 0,76 / 0,34, furt înainte de contor 0,67 / 0,35, pierdere tehnică 0,51 / 0,28, contor de client 0,38 / 0,16. Față de versiunea de la 16:12 (0,71), lumea simulată s-a schimbat: eroarea contoarelor de balanță e acum 0,07% (diferența normală martor − contor ~0,1%, cât a spus mentorul PPC), deci testul e altul. Pe același test nou, modelul fără regula martorului dă 0,703, iar cu regulă 0,704. Clientul la postul greșit a urcat de la 0,32 la ~0,77 în trei pași: trăsătura „oglindă” (lipsa zilnică la un post corelată negativ cu surplusul vecinului), legarea celor două capete ale perechii (`diagnose.pair_consistency`) și identificarea topologiei din tensiuni (contorul cu tensiunea cea mai ciudată seamănă mai bine cu un vecin decât cu postul lui; `dataset.voltage_topology`).

### Ce vede doar bilanțul (A are 0 prin construcție)

| Cauza | Postul găsit | și cauza corectă | Energia lipsă găsită |
|---|---|---|---|
| furt înainte de contor | 74% | 54% | 85% |
| pierdere tehnică (cabluri, faze) | 64% | 43% | 94% |
| contorul de balanță setat greșit | 99% | 98% | (lipsă doar pe hârtie) |
| client la postul greșit | 54% | 41% | 72% |
| **total** | | | **85%, ~25.000 lei pe lună** pe cele 300 de posturi |

Din posturile marcate, 13% sunt de fapt normale. Figura: `reports/bilant/bilant_only_causes.png`.

### Cu bilanț față de fără (verificări de contoare)

Regula din producție: bilanțul doar confirmă, nu coboară niciodată un contor găsit de A.

| Test | K contoare pe zi | Precizia fără → cu bilanț | Deplasări degeaba evitate pe zi | Lei recuperați pe zi fără → cu |
|---|---|---|---|---|
| Mai multe zile, scor A simulat la calitatea lui A pe Londra (ROC-AUC 0,907) | 10 | 10,2% → **12,2%** | 0,20 | 824 → 855 |
| | 20 | 6,4% → 7,7% | 0,28 | 921 → 1.000 |
| | 50 | 4,0% → 4,5% | 0,28 | 1.177 → 1.458 |
| | 100 | 2,6% → 2,7% | 0,05 | 1.370 → 1.587 |
| Idem, la calitatea lui A pe SGCC, date reale de furt (ROC-AUC 0,80) | 10 | 2,5% → **4,0%** | 0,15 | 126 → **456** |
| | 20 | 1,4% → 2,6% | 0,25 | 126 → 502 |
| | 100 | 0,7% → 1,1% | 0,40 | 539 → 740 |
| Ziua demo, scorurile **reale** ale lui A (15.850 de contoare) | 10-300 | 100% → 100% | 0 | - |
| | 500 | 93,0% → 90,6% | -12 | - |

Concluzia cinstită: cu scorurile reale ale lui A nu există câștig la clasare. A e deja precis în vârful listei, iar cele două lumi simulate (curbele din Londra ale lui A, curbele SimBench ale bilanțului) împart doar contorul cu problemă și ziua apariției. Câștigul apare când modelul de contoare e mai slab (de exemplu, la calitatea SGCC, lei recuperați în primele 10 cresc de 3,6 ori). Valoarea principală a bilanțului e alta: vede 48% din energia pierdută, pe care contoarele n-o văd deloc, și spune cauza la nivel de post.

## Varianta v2 (7 nov., 22:10-22:35)

Regula: v2 se păstrează doar dacă bate v1 pe același test (cele 300 de posturi ale hărții). v1 rămâne rezervă: `models/bilant/diagnose.*`, `fuse.V1_PARAMS`.

- **Diagnosticul v2:** ~3.000 de posturi de antrenare (lotul `trainL`, față de 300), 7 trăsături noi (clienți cu consumul înjumătățit, cât explică primii 3, contoare noi cu zero / blocate / cu semn schimbat pe 7 zile, raportul față de normalul din GIS) și setări LightGBM căutate cu Optuna (40 de încercări, validare pe 20% din cartierele `trainL`). Pe test, F1 macro: v1 0,704 → doar mai multe posturi 0,717 → plus trăsături 0,735 → plus căutare **0,754**. Pe clase: contor de client 0,38 → 0,47, furt înainte de contor 0,67 → 0,77, client la postul greșit 0,76 → 0,87, pierdere tehnică 0,51 → 0,49 (ușor mai jos). Detalii: `reports/bilant/v2_comparison.json`.
- **Fuziunea v2:** aceeași regulă (doar confirmă), cu parametrii căutați automat (Optuna, 60 de încercări) pe un lot separat de ~3.000 de posturi cu defectele de contor ca la A (`trainLA`). Pe harta de test, scoruri A simulate: precizia în primele 10 contoare pe zi 80% doar cu A, 78% cu v1, **90% cu v2**; în primele 100: 31% → 33%; deplasări degeaba evitate pe zi față de A: 1,0 / 0,8 / 1,0 / 2,0 la K = 10 / 20 / 50 / 100; lei pe zi în primele 10: 4.966 → 8.278. Cu scorurile reale ale lui A: AUC 0,917 → 0,919 (v1: 0,916), deci v2 nu strică. Fuziunea învățată (LightGBM) a fost respinsă: câștigul ei pe simulare venea din construcția scorului A simulat, iar pe scorurile reale cădea la AUC 0,85 (`reports/bilant/fusion_v2_comparison_trainLA.json`).

## Incertitudine și „nu sunt sigur”

Modelul se abține și trimite la om (`human_review`) când:
- cauza cea mai probabilă are sub 50%;
- primele două cauze sunt la mai puțin de 15 puncte;
- intervalul pierderii normale e de peste 3 ori mai larg decât lipsa.

Se abține în 12,7% din ferestre; detaliile sunt în `reports/bilant/error_analysis.md`. Posturile fără contor de balanță nu primesc lucrare de pierderi: trec pe planul B.

## Limite cunoscute

- **Totul e simulat.** Pierderile din SimBench sunt calibrate cu un factor ales de noi (×2,5 ± 35%), ca să ajungă la nivelul reperelor RER. Pe date reale, primul pas e reantrenarea pe lipsa măsurată.
- În testul pe mai multe zile, scorurile A sunt simulate. Cu scorurile reale (ziua demo), fuziunea nu câștigă nimic la clasare (tabelul de mai sus).
- Precizia absolută din testul simulat e mică pentru că problemele noi sunt rare: ~10 contoare pe zi din ~24.000.
- „Nu sunt sigur” al lui A nu se rezolvă automat cu bilanțul. Am încercat; pe ziua demo, cele 5 cazuri rezolvate nu aveau nicio problemă reală. Codul există, dar e oprit (`fuse.RESOLVE_ABSTAIN`).
- Problemele mici (sub 2 kWh/zi) se confundă cu zgomotul pierderii normale. Problemele foarte vechi (peste 90 de zile) intră treptat în istoricul postului. Istoricul ar trebui învățat doar din perioade verificate.
- Clientul la postul greșit: recall 67%, precizie 91%. Tensiunea e simulată din calculul de rețea; pe date reale, contoarele trebuie să trimită tensiunea (multe o fac, la 15 minute). Pierderea tehnică veche (peste 60 de zile) sau mică (sub 10 kWh/zi) scapă des, pentru că istoricul postului o învață ca normală.
- Fazele nu se măsoară direct: dezechilibrul e estimat din pierderi (`extra.phase_rebalance_input`).

## Bucla de învățare

Verdictul echipei după vizită (review-ul din API, `note: "verdict:<clasă>"`) devine eticheta ferestrei acelui post. Cântărește de 5 ori mai mult la reantrenare (`feedback.py`, `diagnose.fit` cu `weight`). Un `reject` fără verdict înseamnă deplasare degeaba și se citește ca `normal`.

## Utilizare responsabilă

- Omul aprobă lista zilnică (planificatorul, review-ul din API). Fiecare decizie e în jurnal, cu `prediction_id` și versiunea modelului.
- Un post marcat nu înseamnă că un client a furat. Diagnosticul spune unde se pierde energia; constatarea o face echipa, după procedura legală.
- EU AI Act: infrastructură critică, deci risc ridicat. Avem supraveghere umană, jurnal automat, documentație, praguri de abținere.
