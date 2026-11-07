# Fișa modelului: bilanț pe post (`bilant-lgbm`)

**Simulare pe date publice, gândită pentru datele PPC.** Toate cifrele de aici vin din `make bilant-data bilant-eval` (`reports/bilant/metrics.json`). Datele de test sunt 100% sintetice.

## Ce face

Pentru fiecare post de transformare și fiecare zi:

1. **Bilanțul**: lipsa = energia ieșită din post (contorul de bilanț) − suma contoarelor clienților din bază, în kWh și lei.
2. **Pierderea normală** (modelul 1): cât ar trebui să lipsească azi la acest post, cu interval P10-P90.
3. **Diagnosticul** (modelul 2): de ce lipsește mai mult. Șase clase: normal, contor de client, furt înainte de contor, pierdere tehnică, client la postul greșit, contorul postului setat greșit.
4. **Lucrarea**: valoarea = probabilitatea × energia lipsă × prețul. Acțiunile, de la ieftin la scump: întâi citire la distanță, apoi verificare, echipă de rețea, corecție în birou fără deplasare, urmărire, decizie umană.
5. **Fuziunea cu A**: confirmă sau infirmă contoarele marcate de modelul A, după cât lipsește la postul lor.

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
| Pierderea normală, MAE (kWh/zi) | **5,30** (14% din 37,0) | formula fizică I²R 14,91; procent fix 20,59 |
| Același, fără istoricul postului | 12,56 | - |
| Acoperirea intervalului P10-P90 | 88,1% | formula fizică 86,6% (interval de ~10 ori mai larg) |
| Diagnosticul, F1 macro | **0,71** | tabelul de reguli din concept 0,48 |
| Diagnosticul, exactitate | 0,83 | 0,78 |
| Primele 10 posturi pe zi prind din energia lipsă | 85% | 80% |
| **Energia pierdută pe care niciun contor de client nu o vede** (furt înainte de contor, pierderi tehnice peste normal, client la postul greșit), ziua demo | **48%** | o vede doar bilanțul |
| Planul B: energia lipsă găsită cu contoare la 20% din posturi | **36%** | la întâmplare 20%; posturile mari întâi 23% |

F1 pe clase (model / reguli): contor de post setat greșit 0,99 / 0,87, normal 0,91 / 0,90, client la postul greșit 0,77 / 0,34, furt înainte de contor 0,70 / 0,35, pierdere tehnică 0,52 / 0,28, contor de client 0,40 / 0,16. Clientul la postul greșit a urcat de la 0,32 la 0,77 în trei pași: trăsătura „oglindă” (lipsa zilnică la un post corelată negativ cu surplusul vecinului), legarea celor două capete ale perechii (`diagnose.pair_consistency`) și identificarea topologiei din tensiuni (contorul cu tensiunea cea mai ciudată seamănă mai bine cu un vecin decât cu postul lui; `dataset.voltage_topology`).

### Ce vede doar bilanțul (A are 0 prin construcție)

| Cauza | Postul găsit | și cauza corectă | Energia lipsă găsită |
|---|---|---|---|
| furt înainte de contor | 74% | 55% | 86% |
| pierdere tehnică (cabluri, faze) | 64% | 42% | 95% |
| contorul postului setat greșit | 99% | 99% | (lipsă doar pe hârtie) |
| client la postul greșit | 53% | 42% | 72% |
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

## Incertitudine și „nu sunt sigur”

Modelul se abține și trimite la om (`human_review`) când:
- cauza cea mai probabilă are sub 50%;
- primele două cauze sunt la mai puțin de 15 puncte;
- intervalul pierderii normale e de peste 3 ori mai larg decât lipsa.

Se abține în 12,7% din ferestre; detaliile sunt în `reports/bilant/error_analysis.md`. Posturile fără contor de bilanț nu primesc lucrare de pierderi: trec pe planul B.

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
