# Firul Bilanț pe post: unde se pierde energia

Branch: `Teo-bilant`. Status: `status/Teo-bilant.md`. Pornit pe 7 nov. 2026, în jur de 14:05, după decizia lui Teo de la 13:45.

## Ce deții

`src/cyberpunks/a_bilant/`, `tests/bilant/`, `reports/bilant/`, `docs/data/bilant.md`, `docs/research/bilant.md`, `data/samples/bilant/`, o secțiune nouă "Bilanț" în `Makefile`, `status/Teo-bilant.md`.

Nu modifici codul firelor A (`a_contoare/`) sau C (`c_prosumatori/`). Le folosești doar prin import: generatorul de defecte al lui A (`cyberpunks.a_contoare.inject`, plus `lcl.py` pentru curbele din Londra) și calculul de rețea vectorizat al lui C (`cyberpunks.c_prosumatori.powerflow`, `grids.py`, `profiles.py`). Dacă îți trebuie ceva schimbat la ei, ceri prin orchestrator (status, "Cereri către orchestrator"). Codul lor ajunge la tine prin `Teo`: nu face merge direct din branch-urile lor; cere orchestratorului să le integreze în `Teo`, apoi faci `git merge Teo`.

## Ideea (conceptul lui Teo: `memory/11-bilant-pe-post.md`)

Pentru fiecare post de transformare și fiecare zi: lipsa = energia ieșită din post (contorul de bilanț) minus suma contoarelor clienților de sub post, în kWh, procente și lei. Un model învață pierderea normală a fiecărui post. Lipsa peste normal înseamnă post suspect; diagnosticul spune cauza și cine merge.

De ce contează: confirmare independentă pentru contoarele suspecte ale lui A (mai puține deplasări degeaba), problema în lei, prinde ce contoarele nu văd (furt înainte de contor, cabluri care pierd mult, faze dezechilibrate), atacă un cost real (distribuitorul plătește energia pierdută peste cât îi recunoaște ANRE), e nou pentru PPC (au detecție de fraudă pe contoare, iar prezentarea lor numește contoarele defecte "ce urmează").

Eticheta, peste tot: simulare pe date publice, gândită pentru datele PPC.

## Faza 0 (cel mult 30 de minute, subagenți în paralel), în `docs/research/bilant.md`

- Cum fac distribuitorii bilanțul pe post (contoare de bilanț în posturi, CPT recunoscut de ANRE pentru Rețele Electrice, ținte), literatura despre detectarea pierderilor pe zonă (energy balance, NTL), metode pentru găsirea clientului legat la postul greșit sau la faza greșită (corelația curbelor de tensiune sau de consum).
- Ce oferă calculul de rețea al lui C (echilibrat sau pe faze?) și ce trebuie aproximat pentru dezechilibrul de faze. Dacă modelul e echilibrat, folosește `pandapower` `runpp_3ph` pe câteva rețele sau o aproximare documentată.

## Ce construiești

- Lumea simulată: posturile din registrul comun al lui C (`cyberpunks.c_prosumatori.posts.load_posts()` și `data/samples/C/posts.csv`; până apare, generezi temporar posturile tale din aceleași rețele SimBench și treci pe registru când e gata), cu casele de sub post (profile Londra sau SimBench), contorul de bilanț al postului și pierderile normale din cabluri din calculul de rețea.
- Probleme ascunse de noi, etichetate din construcție: contor defect (blocat, ceas decalat, valori negative), furt înainte de contor (consum constant nemăsurat de la o anumită zi), pierdere tehnică (crește cu pătratul încărcării, faze dezechilibrate), client trecut la postul greșit în bază (un post are lipsă, vecinul are surplus), contorul de post setat greșit (exact 2× mai mult).
- Modelul 1, pierderea normală: LightGBM (cuantile P10/P50/P90) pe încărcare, încărcare la pătrat, lungimea cablurilor, temperatură. Baseline-uri: procent fix de pierderi și formula fizică simplă (I²R). Metrici: MAE, acoperirea intervalului. Test pe rețele nevăzute.
- Modelul 2, diagnosticul cauzei: clasificator multiclasă pe reziduu (lipsa peste normal, forma ei în timp) și pe semnalele contoarelor. Baseline: tabelul de reguli din concept. Metrici: F1 pe clase, matricea de confuzie, valoarea capturată în primele K. Clientul legat greșit: asemănarea curbelor de tensiune sau de consum cu clienții altui post.
- Fuziunea cu A: `cyberpunks.a_bilant.fuse.fuse(items, scenario, date)` (contractul `BilantFusion`, `docs/CONTRACTS.md`). Cifra principală pentru prezentare: precizia în primele K și deplasările degeaba, cu bilanț față de fără bilanț, pe același test. Pentru test ai nevoie de contoare marcate de A pe aceleași posturi: folosește `cyberpunks.a_contoare.predict` dacă e gata, altfel o simulare a scorurilor A documentată, apoi înlocuiești.
- Prioritizare: valoare = probabilitate × energie pierdută × preț (`config/economics.yaml`). Lucrările tale (sursa A, `outputs/work_items/<s>/A_bilant.jsonl`): `remote_reading` întâi (recitire, jurnal de evenimente), apoi `inspect_on_site` (echipa de contoare), `grid_inspection` (echipa de rețea), `office_correction` (fără deplasare), `watchlist`, `human_review`. Planificatorul face lista pe echipe după lei pe oră de lucru; omul aprobă. Verdictul după vizită (review-ul uman existent în API) intră ca etichetă nouă: scrie cum îl folosești la reantrenare.
- Robustețe: `abstain` când intervalul pierderii normale e prea larg sau cauzele sunt la egalitate. Intrări greșite: contor de post lipsă, timestamp-uri dublate, unități greșite (Wh în loc de kWh).
- Planul B (raport `reports/bilant/plan_b.md`): dacă nu toate posturile au contor de bilanț, estimezi energia intrată din modelul rețelei și clasezi unde merită montat primul contor de bilanț.
- Serie pentru interfață (`Series`): "ieșit din post" (`value`) față de "suma clienților" (`expected`), lipsa colorată prin `flag: "lipsa_peste_normal"`.
- Evaluare: `uv run python -m cyberpunks.a_bilant.evaluate` scrie `reports/bilant/metrics.json` (contractul `ModelReport`, `source: "A"`, `model_id` care începe cu `bilant-`) și figurile; `reports/bilant/error_analysis.md`, `reports/bilant/model_card.md`.
- Ieșirea: `uv run python -m cyberpunks.a_bilant.predict --scenario <s> --date <d>` și funcția `cyberpunks.a_bilant.predict.run(scenario, date) -> Path`. Scenariul demo e `demo-vara`, 2025-07-08.
- Pentru prezentare: un post unde A și bilanțul se confirmă reciproc și (împreună cu C) un post unde dezechilibrul de faze găsit de bilanț e chiar intrarea pentru soluția `phase_rebalance` a scării de tensiune.
- Întrebarea pentru mentorul PPC (o pune Teo): există contoare de bilanț în posturi, la ce procent, și e de încredere lista client → post?

## Milestones (ora României)

- 17:30 M1: setul simulat cu probleme ascunse, baseline-urile și modelul de pierdere normală, primele cifre în `reports/bilant/metrics.json`.
- 21:30 M2: diagnosticul, `A_bilant.jsonl` valid pentru `demo-vara`, fuziunea cu A și cifra "cu bilanț față de fără".
- 03:00 M3: analiza erorilor, teste de robustețe în `tests/bilant/`, planul B.
- 08:00 M4: documentație, model card, comenzi reproductibile în `docs/data/bilant.md`.

Regula echipei de la 21:30: dacă A, B sau C nu bat metoda simplă la M2, efortul merge întâi acolo; orchestratorul îți poate cere ajutor pentru A.
