# Model card: `a-lgbm`, contoare defecte sau manipulate (firul A, Daybreak)

Generat de `uv run python -m cyberpunks.a_contoare.report` din `reports/A/metrics_full.json` (2026-11-07T16:13:05+02:00). Formatul urmează Mitchell et al. 2019, "Model Cards for Model Reporting".

## Pe scurt

- **Ce face:** dă fiecărui contor inteligent o probabilitate calibrată că e defect sau manipulat, plus tipul probabil (defect / manipulare), intervalul de încredere, factorii care au contat și cazuri similare.
- **Pentru cine:** dispecerul și planificatorul echipelor de contorizare Rețele Electrice. Recomandă: verificare la fața locului, citire la distanță, urmărire sau decizia unui om.
- **Ce NU face:** nu acuză pe nimeni de furt, nu taie curentul, nu recalculează facturi. Orice vizită o decide planificatorul (cost și capacitate), iar cazurile nesigure le decide un om.

## Detalii

- Versiuni: `a-lgbm@72c4d15` (agentul) și `a-lgbm-sgcc@72c4d15` (reperul pe etichete reale).
- Tip: LightGBM (arbori de decizie cu gradient), 3 clase (normal / defect / manipulare), ponderi pe clase, oprire timpurie pe gospodării separate; calibrare Venn-ABERS (pe grilă, abatere măsurată față de calculul exact); "nu sunt sigur" prin conformal Mondrian pe scorul brut (alpha 1% normal, 30% problemă).
- Intrare: consumul unui contor pe 180 de zile (citiri la 30 de minute) și mediana vecinilor de pe același post; 40 de features, fiecare cu motivul scris (`features.py`, `FEATURE_INFO`).
- Rulează local, pe 4 nuclee, fără niciun API extern. Scorarea a 15.850 de contoare durează ~10 secunde.
- Autori: echipa CyberPunks, SmartHack XI 2026 (tema PPC). Cod: `src/cyberpunks/a_contoare/`.

## Utilizare corectă

- Prioritizarea verificărilor când echipele sunt puține: K = 1% din contoare, cam o săptămână de vizite pentru 3 echipe la 10.000 de contoare.
- Contoarele defecte (oprite, blocate, fără comunicație, cu salturi, cu citiri negative) înaintea furtului: PPC are deja în producție detecția de fraudă (Energy Anomaly Detection) și a anunțat ca pas următor monitorizarea predictivă a contoarelor defecte.
- Decizia finală o ia planificatorul (cost și capacitate) sau un om (cazurile nesigure). Fiecare decizie duce înapoi la `prediction_id` și `model_version` (jurnalul planificatorului).

## Utilizări greșite (de evitat)

- Acuzații automate de furt, debranșări sau recalculări de facturi pe baza scorului. Constatarea o face echipa la fața locului.
- Profilarea consumatorilor mici: consumul mic poate însemna o locuință goală sau sărăcie energetică. Agentul trimite la om furtul suspectat din chintila de jos a consumului.
- Folosirea pe alte rețele sau țări fără recalibrare. Prevalența și obiceiurile de consum diferă.

## Date

- **Antrenare și test, defecte și furt (sintetic):** consum real din Londra (Low Carbon London, UK Power Networks, CC BY 4.0), 1.414 gospodării, peste care injectăm 7 defecte, 8 tipuri de furt și 2 schimbări normale (concediu, schimbarea ocupanților). Etichetele vin din construcție. Rotunjim la rezoluția contorului după injecție.
- **Reper pe furt real:** SGCC (State Grid Corporation of China, Zheng et al. 2018), 42.372 de clienți, 3.615 cu furt. Fără licență explicită: îl folosim doar pentru cercetare, fără să-l redistribuim.
- **Împărțirea:** Londra pe gospodării (60/20/20) și pe timp (test după antrenare); SGCC pe clienți (60/20/20), stratificat. Features alese pe o validare din setul de antrenare (gospodării ținute deoparte); calibrarea și pragurile conformal, doar pe setul de calibrare; testul, privit o singură dată pe versiune.
- **Demo:** 15.850 de contoare SINTETICE pe cele 300 de posturi din registrul comun (58,81% din clienți, gradul de integrare din Muntenia), cu profile reale ale gospodăriilor de test.

## Rezultate (K = 1% din contoarele din test)

| Set de test | Model | Regula simplă | Regula VEE completă | IsolationForest |
|---|---|---|---|---|
| SGCC, furt real (8.475 de clienți): precizia@K | 0,80 | 0,04 | 0,11 | 0,16 |
| SGCC: PR-AUC / ROC-AUC | 0,40 / 0,82 | 0,08 / 0,50 | 0,10 / 0,56 | 0,11 / 0,59 |
| Londra, sintetic (13.028 de eșantioane): precizia@K | 1,00 | 0,46 | 0,53 | 0,06 |
| Londra: PR-AUC / ROC-AUC | 0,68 / 0,91 | 0,19 / 0,70 | 0,26 / 0,80 | 0,18 / 0,78 |
| Londra, doar problemele subtile: precizia@K | 0,62 | 0,07 | 0,02 | 0,04 |

- Calibrare (Londra, test): Brier 0,023, ECE 0,004. Conformal (acoperirea empirică a mulțimii, pe test): 99% la normale (țintă 99%), 69% la probleme (țintă 70%). Ca decizii: 59% din probleme recunoscute sigur, precizia deciziilor "problemă" 74%, 1% din contoarele normale declarate "problemă", 2% "nu sunt sigur".
- Scurgeri: nicio gospodărie sau client în două seturi; referința vecinilor SGCC doar din antrenare; cu etichete amestecate, PR-AUC pe test cade la prevalență (0,047 pe Londra, 0,105 pe SGCC). Testul cu etichete amestecate e o verificare de bun-simț, nu o dovadă (error_analysis.md, secțiunea 1).
- Precizia@K = 1,00 pe Londra vine din defectele evidente care umplu vârful listei. La K = numărul de probleme, precizia e 0,66. Detalii în `error_analysis.md`, secțiunea 2.
- Figuri: `reports/A/figures/headline_precision.png`, `ranking_at_k.png`, `false_alarms_by_consumption.png`, `calibration.png`, `detection_by_kind.png`.
- Date lipsă (populația demo): PR-AUC 0,69 -> 0,59 -> 0,56 la 0 / 30 / 50% zile lipsă. Peste 2/3 lipsă, agentul se abține și trimite la om.
- Fuziunea cu bilanțul pe post (verificată pe testul A, bilanț cu sigma 2%): precizia@10 1,00 -> 1,00, PR-AUC 0,718 -> 0,721. Confirmă mai ales defectele cu pierdere mare de energie, rar furtul, niciodată tiparele fără pierdere de energie (`error_analysis.md`, secțiunea 9).

## Limite

- Etichetele de defect și de furt din Londra sunt sintetice. Un furt real poate arăta altfel decât atacurile din literatură (h1-h6) și variantele noastre.
- Slab la ceasul decalat, la sub-înregistrarea lentă și la bypass-ul parțial instalat treptat (`error_analysis.md`, secțiunea 3).
- Prevalența din test și din demo (3% defecte, 2% furturi) e o ipoteză. Precizia depinde de ea.
- Pe SGCC, împărțirea pe timp dă rezultate mai slabe (ROC-AUC ~0,71): golurile de colectare din 2015 dispar în 2016, iar eticheta nu are dată.

## Etică, date personale, EU AI Act

- Fără date personale: ID-uri de contor sintetice, nicio adresă, niciun nume. Topologia e sintetică, pe poziții plauzibile din OpenStreetMap.
- Om în buclă: cazurile nesigure (zona gri conformal, istoric scurt, date insuficiente) și furtul suspectat la consum mic merg la un om, cu motivul scris.
- Alarmele false se verifică pe chintile de consum la fiecare evaluare (`error_analysis.md`, secțiunea 5).
- EU AI Act: tratăm sistemul ca pe unul cu impact (utilități, infrastructură critică). De aceea are supraveghere umană, jurnal automat al deciziilor (planificatorul), documentație (acest card, `docs/data/A.md`) și explicații pentru fiecare lucrare. Clasificarea juridică exactă nu am verificat-o.

## Reproducere

```bash
make a-all        # descărcare, features, antrenare, evaluare, robustețe, lucrări (~6 min)
make a-evaluate   # doar evaluarea (reports/A/metrics.json, metrics_full.json, figuri)
uv run python -m cyberpunks.a_contoare.report   # acest card și error_analysis.md, din cifrele de mai sus
```
