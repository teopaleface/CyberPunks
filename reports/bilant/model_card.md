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

| Ce | Modelul nostru | Metoda simplă |
|---|---|---|
| Pierderea normală, MAE (kWh/zi) | **5,05** (14,7% din 34,4) | formula fizică I²R 14,60; procent fix 19,08 |
| Același, fără istoricul postului | 12,02 | - |
| Acoperirea intervalului P10-P90 | 88,6% | formula fizică 84,9% (interval de 10 ori mai larg) |
| Diagnosticul, F1 macro | **0,61** | tabelul de reguli din concept 0,46 |
| Diagnosticul, exactitate | 0,71 | 0,62 |
| Primele 10 posturi pe zi prind din energia lipsă | 74% | 69% |
| **Cu bilanț față de fără**: precizia în primele 10 contoare pe zi | **15,0%** | scorul A singur 9,2% |
| Lei recuperați pe zi, primele 10 | **874** | 424 |
| Deplasări degeaba pe zi, primele 10 | 8,5 | 9,1 |
| Planul B: energia lipsă găsită cu contoare la 20% din posturi | **32%** | la întâmplare 20%; posturile mari întâi 22% |

F1 pe clase: contor de post setat greșit 0,99, normal 0,83, contor de client 0,58, furt înainte de contor 0,56, pierdere tehnică 0,36, client la postul greșit 0,32.

## Incertitudine și „nu sunt sigur”

Modelul se abține și trimite la om (`human_review`) când:
- cauza cea mai probabilă are sub 50%;
- primele două cauze sunt la mai puțin de 15 puncte;
- intervalul pierderii normale e de peste 3 ori mai larg decât lipsa.

Se abține în 18,8% din ferestre. Acolo ar fi avut dreptate doar în 45% din cazuri, față de 77% în rest. Posturile fără contor de bilanț nu primesc lucrare de pierderi: trec pe planul B.

## Limite cunoscute

- **Totul e simulat.** Pierderile din SimBench sunt calibrate cu un factor ales de noi (×2,5 ± 35%), ca să ajungă la nivelul reperelor RER. Pe date reale, primul pas e reantrenarea pe lipsa măsurată.
- **Scorurile A din cifra „cu bilanț față de fără” sunt simulate** (un clasificator de calitatea lui A: ROC-AUC 0,907, cât raportează A pe Londra). Contoarele reale ale lui A nu sunt încă în aceeași lume cu bilanțul. Cât timp contoarele A nu sunt legate de posturile registrului C, `fuse` nu le schimbă scorul.
- Precizia absolută din fuziune e mică pentru că problemele noi sunt rare: ~11 contoare pe zi din ~27.000. Câștigul relativ e cifra care contează.
- Problemele mici (sub 2 kWh/zi) se confundă cu zgomotul pierderii normale. Problemele foarte vechi (peste 90 de zile) intră treptat în istoricul postului. Istoricul ar trebui învățat doar din perioade verificate.
- Clientul la postul greșit e clasa cea mai slabă. Semnalul (vecinul cu surplus egal) se pierde când vecinul are și el o problemă.
- Fazele nu se măsoară direct: dezechilibrul e estimat din pierderi (`extra.phase_rebalance_input`).

## Bucla de învățare

Verdictul echipei după vizită (review-ul din API, `note: "verdict:<clasă>"`) devine eticheta ferestrei acelui post. Cântărește de 5 ori mai mult la reantrenare (`feedback.py`, `diagnose.fit` cu `weight`). Un `reject` fără verdict înseamnă deplasare degeaba și se citește ca `normal`.

## Utilizare responsabilă

- Omul aprobă lista zilnică (planificatorul, review-ul din API). Fiecare decizie e în jurnal, cu `prediction_id` și versiunea modelului.
- Un post marcat nu înseamnă că un client a furat. Diagnosticul spune unde se pierde energia; constatarea o face echipa, după procedura legală.
- EU AI Act: infrastructură critică, deci risc ridicat. Avem supraveghere umană, jurnal automat, documentație, praguri de abținere.
