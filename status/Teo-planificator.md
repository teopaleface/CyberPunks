# Status: Teo-planificator
Actualizat: 2026-11-07 15:56
Milestone curent: M3 gata pe ieșirile finale; M4 în lucru (documentație, ultima revizuire independentă)
Gata de merge: da (commit 15ee1d9, plus acest status)

## Pornirea demo-ului, dintr-un singur loc (checkout-ul principal)
- **`make demo`**: rulează planul real pentru `demo-vara` (modelele A, B, C rulează efectiv, ieșirea bilanțului pentru aceeași zi se refolosește), apoi pornește în paralel API-ul pe http://127.0.0.1:8710/api și consola pe http://localhost:3710. Ctrl-C le oprește pe amândouă. Merg toate: butonul „Rulează agentul” (~26 s: Estimate 14 s, Decide 10 s, Act 1 s), aprobarea planului, coada „nu sunt sigur” cu replanificare, verdictele.
- **`make demo-offline`**: fără modele, API-ul servește instantaneul din git (`outputs/demo/`, planul real de la 15:35 pe ieșirile finale) și pornește consola. Doar citire: „Rulează agentul” și aprobările cer `make demo`.
- Separat: `make api` (ultima rulare locală, altfel instantaneul), `make api-demo` (doar instantaneul), `make web` (consola).
- Gata și folosite de interfață: `POST /api/plan/approve` (`AuditRecord`, `actor: human`, `action: plan_approved`, 409 dacă planul s-a schimbat) și `GET /api/plan/approval`; `GET /api/posts` (300 de posturi, culoare după lei pierduți pe lună din bilanț) și `GET /api/posts/{post_id}`; `posts.json` e și în instantaneu.

## Răspuns la cererile orchestratorului de la 15:15 și 15:50
- **1. Instantaneul pe ieșirile finale** (A 524, bilanț 98, B 26, C 41): 32 de lucrări în traseele a 8 echipe, 224 km, 25 la dispecer (8 zone de furtună cu cerere de întăriri, 17 cazuri de siguranță de decis azi), 13 posturi cu scara C, 28 de contoare confirmate de bilanț. Commit 654c644.
- **2. Scara C pe lucrările reale**: 13 decizii `R-REMEDY-LADDER`, toate fezabile sub 1,10 pu, cu treptele cu echipă programate după preavizul ANRE (10.07.2025) și mesajele pentru până atunci. Explicația spune cifra pentru fiecare treaptă mai ieftină, de exemplu: „cu mesajele către clienții Ore Smart singure (3 lei, la 10% participare), tensiunea ajunge doar la 1,175 pu; cu oferta de baterii singură (24 lei), tensiunea ajunge doar la 1,162 pu”. Mesajul de grup al lui C (`message_preview_ro`) intră în `notifications` (audiență `prosumatori`, `demo_only`), iar ofertele de baterii apar ca notificări și ca listă pentru PPC Energie în raportul zilei (8 posturi). Fuziunea cu bilanțul: 522 de rânduri `R-FUSION-BILANT` în jurnal, 40 de contoare cu scorul urcat; „confirmat de bilanț” apare în motiv doar unde bilanțul chiar confirmă.
- **3. Scenariul `maine`** (8 noiembrie 2026, prognoza reală), cap-coadă în 27 s: A 563, B 26, C 33 de lucrări; 29 în trasee, 25 la dispecer. Alertă nouă „Contextul zilei” (și în raport), de exemplu: „Tensiune: 33 posturi cu risc din 300 (soare pe panou până la 730 W/m² la prânz, 8 °C). În noiembrie sezonul fotovoltaic e la final; mai sunt ~10 zile de soare puternic până la primăvară: o echipă pentru priză sau faze nu se mai plătește, deci agentul trimite 4 mesaje către prosumatori, pune 29 posturi la urmărire și 0 echipe.” și „Furtună: vreme liniștită în cele 26 de zone; cel mai mare risc de avarii e 6%”.
- **Cererile B 9 și 10**: `storm.customers_helped_per_crew_shift: 500` în `config/economics.yaml` (CALCUL din furtuna din Timiș, 7-9 iulie 2025: ~40.000 de consumatori și 80 de echipe pe teren); plafonul: o echipă pe zonă (`storm.max_crews_per_zone: 1`), cel mult 3 echipe trimise din timp pe regiune (`storm.max_crews_per_region: 3`), în `config/planner.yaml`. Regula nouă `R-B-BELOW-THRESHOLD`: nu se mută echipe sub pragul modelului B (`extra.decision_threshold`, 16%), oricât de mare e zona; pe `demo-vara` nu mai pleacă echipe la Constanța (9%), Bolintin și Buftea (6%), iar pe `maine` niciuna.
- Coada dispecerului pune acum întâi zonele de furtună care cer întăriri (urgente, vin după-amiază), apoi siguranța, apoi valoarea.

## Cereri noi către orchestrator (te rog transmite)
- **Bilanț, scenariul `maine`**: `cyberpunks.a_bilant.predict.run("maine", "2026-11-08")` cade cu `LightGBMError: The number of features in data (34) is not the same as it was in training data (25)`. Planul merge fără bilanț (sursa e opțională), dar harta posturilor de mâine nu are lei pierduți.
- **C**: `message_preview_ro` spune „dacă 1 din 5 vecini” (20%), iar treapta are `participation_rate: 0.1`; textul ar trebui să folosească aceeași rată.
- **A**: semnalul de siguranță a crescut din nou: pe ieșirea finală, 112 cazuri cu scor ≥ 0,7 marcate cu risc pentru oameni; 91 nu încap în turele de mâine. Propunerea rămâne: `safety_flag` doar pentru dovezi puternice de șuntare.

## Răspuns la cererile orchestratorului de la 14:20
- `git merge Teo` făcut. Planul rulează pe ieșirile din `Teo` (A 391, bilanț 98, B 26, C 41): 40 de lucrări în traseele a 9 echipe, 430 km, 370 de verificări de la distanță și corecții în birou, **25 la om**, 18 mesaje, OR-Tools în 10 s.
- **1. Interfața**
  - `POST /api/plan/approve` `{scenario, plan_id, approver, note}` → `AuditRecord` cu `actor: human`, `action: plan_approved`; 409 dacă `plan_id` nu mai e planul curent (s-a replanificat între timp). `GET /api/plan/approval?scenario=` → `{approved, plan_id, approver, ts, stale}`.
  - `GET /api/posts` există (de la 13:46); acum citește și `extra.lei_per_month` al bilanțului: pe 8 iulie, 22 de posturi roșii, 41 galbene, 237 verzi, toate în registrul C. `posts.json` se scrie la fiecare rulare în `outputs/plans/<s>/` și e în instantaneu (`outputs/demo/plans/demo-vara/posts.json`).
  - Pornirea pentru demo (înlocuită de `make demo`, mai sus):
    - Recomandat, din checkout-ul principal (are datele și modelele): `uv run cyberpunks run --scenario demo-vara` apoi `make api`. API-ul servește ultima rulare (`GET /api/health` → `mode: live`).
    - Fără să ruleze modelele: `CYBERPUNKS_API_SOURCE=demo make api`. API-ul servește instantaneul din git, `outputs/demo/` (planul real din 8 iulie 2025, refăcut la 14:33), chiar dacă există o rulare locală mai veche (`mode: demo`). Butonul „Rulează agentul” cere modul live.
    - API-ul din worktree-ul meu servește acum planul real (rulat la 14:33); exemplele cu 7 lucrări erau de la un test mai vechi.
- **2. C**: scara pornește de la `extra.ladder_base_p90_pu` (P90-ul modelului plus dezechilibrul pe faze), dacă există; altfel de la `prediction.point_interval[1]`. Test: `test_ladder_starts_from_phase_adjusted_p90`. De la P90-ul cu dezechilibru, unele combinații care păreau suficiente nu mai ajung, iar cazul merge la om.
- **3. Bilanț**: `grid_inspection` → echipa de rețea (`R-BILANT-GRID`, 486 lei, tariful RER ca PROXY); `office_correction` → coada biroului de date (`R-BILANT-OFFICE`, 15 lei). `phase_rebalance_input` e folosit de C la treapta `phase_rebalance`; planificatorul citește direct treptele lui C.
- **4. Coada „nu sunt sigur”: de la 179 la 25.** Ce era în cele 179: 117 abțineri A, 37 de cazuri de siguranță care nu încăpeau în echipe, 12 abțineri de bilanț, 11 zone de furtună peste plafon, 2 B. Doar 8 posturi apăreau și din A, și din bilanț, deci dublarea nu era cauza. Cauza: orice abținere mergea la om, oricât de mică era valoarea. Ce am schimbat:
  - abținerile din cauza datelor (unitate sau multiplicator greșit, `extra.selection = "data"`) merg la biroul de date (`R-ABSTAIN-DATA`, 31 de cazuri);
  - abținerile cu valoare sub 150 lei rămân la urmărire (`R-ABSTAIN-WATCH`, 28);
  - cazurile de siguranță care nu încap primesc o citire la distanță acum și o singură alertă critică de întăriri (`R-SAFETY-NO-CREW`, 24), nu câte o decizie fiecare;
  - coada are o capacitate de 25 de cazuri pe zi (IPOTEZĂ: ~10 minute de dispecer pe caz), în ordinea: siguranță cu semnal puternic, întăriri pentru furtună, valoare; restul revine în planul următor (`R-HUMAN-QUEUE-FULL`, 58).
  - Rezultat, 25 de cazuri care cer un om: 12 cazuri de siguranță cu semnal puternic, de decis azi; 11 zone de furtună cu cod roșu pentru care trebuie aprobate întăriri; 2 cazuri nesigure de furtună.

## Timpii pentru demo (istoric, 14:41)
- Rularea completă din checkout-ul principal (`run.json` de la 14:20): Estimate 240 s, din care bilanțul 228 s (A 9 s, B 0,3 s, C 3 s); Decide 10 s; Act 2 s. Peste limita de 120 s a interfeței.
- De la 14:41, în modul `auto`, ieșirea bilanțului pentru aceeași zi, din ultimele 12 ore, se refolosește (`config/planner.yaml`, `estimate.reuse_fresh_output: [A_bilant]`); nota apare în plan și în `GET /api/run-info`. Rularea completă ar trebui să scadă la ~25 s (A, B, C rulează efectiv).
- Pentru demo: rulați o dată `uv run cyberpunks run --scenario demo-vara` înainte (ca bilanțul să aibă ieșirea zilei), apoi butonul din interfață merge repede.
- Un model care se oprește cu `SystemExit` (B face asta la un scenariu necunoscut) nu mai oprește planul.

## Cereri către orchestrator (te rog transmite)
- **Bilanț**: `cyberpunks.a_bilant.predict.run` durează 228 s; o ieșire în cache pe (scenariu, dată) sau un calcul mai rapid ar face rularea completă reproductibilă în timpul demo-ului.
- **A, `safety_flag` prea larg**: 89 din 391 de lucrări (23%), toate cu eticheta `tamper`, de la scorul 0,52; doar 50 sunt probleme reale (56%), după `A_ground_truth.csv`. Propunere: `safety_flag` doar pentru dovezi puternice de șuntare (de exemplu `tamper` cu scor ≥ 0,8 și semnătura de bypass). Între timp, planificatorul face siguranța obligatorie doar de la scorul 0,7 (`config/planner.yaml`, `global.safety_min_score`); sub prag, prioritatea e doar triplată.
- **A, textul de abținere**: „pragul pentru normal (0.30) și cel pentru problemă (0.12)” are pragurile inversate.
- **Contracte (orchestrator)**: `TimeWindow` aruncă `TypeError` (nu `ValidationError`) când o oră are fus orar și cealaltă nu; numerele infinite (`1e309`) trec de contract. Planificatorul le prinde și le pune în carantină, dar ar fi bine ca validatorul să le respingă direct (de exemplu `allow_inf_nan=False` și ore obligatoriu cu fus orar).

## Făcut (pe scurt, cu ora)
- 12:53 API-ul; 12:58 M0 (cercetarea, `config/economics.yaml` cu surse); 13:11 M1 (agentul cap-coadă).
- 13:31 Evaluarea agentului și măsurarea solverului; 13:44 extinderea (bilanț, fuziune, scara C, lista după lei pe oră); 13:46 API pentru extindere.
- 13:57 Prima revizuire independentă (Codex): 12 probleme reparate, 11 teste. 14:22 A doua revizuire: 11 probleme reparate, 10 teste (ordinul de lucru arată acțiunea aleasă de agent, orele din anunțul de întrerupere vin din traseu, scenariile de participare nu se adună, replanificarea refolosește fuziunea, intrările cu fus orar amestecat sau infinite intră în carantină).
- 14:05 Ordinul de lucru PDF are prima pagină cu pornirea turei. 14:12 Graficul evaluării (`reports/planner/agent_eval.png`). 14:14 Preavizul ANRE sare peste sărbătorile legale.
- 14:15 A doua evaluare: ziua demo, cu lucrările reale A și adevărul injectat (`A_ground_truth.csv`), în `reports/planner/agent_eval.md`.
- 14:33 Coada omului, aprobarea planului, harta cu bilanțul, instantaneul demo pe ultimul rulaj. 238 de teste trec.
- 14:49 A treia revizuire independentă (Codex): 6 probleme reparate, 6 teste (combinațiile de trepte C păstrează toate treptele cu echipă în ordinul de lucru; fără citire la distanță pentru contoarele care nu se citesc de la distanță; un fișier stricat nu oprește pasul Estimate; ablațiile pornesc de la aceleași setări; graficul arată și valori negative). În total, 29 de probleme găsite de revizuiri și reparate. 245 de teste trec.

## Pentru README-ul principal (text propus, orchestratorul îl poate copia)
> **Agentul (planificatorul).** `uv run cyberpunks run --scenario demo-vara` trece automat prin cei patru pași: *Perceive* (configurația, scenariul, ce date și modele există), *Estimate* (modelele A, bilanț, B, C), *Decide* (validare și carantină, reguli cu nume și praguri justificate de cost, trasee OR-Tools cu ferestre de timp, abilități și baze multiple, cu rezervă greedy) și *Act* (planul, jurnalul de decizii, alertele, mesajele demo, ordinele de lucru PDF pe echipă, raportul zilei). Fiecare decizie are o regulă (`rule_id`), pragurile folosite, motivul în română și o linie în jurnal cu ID-ul predicției, versiunea modelului și amprenta intrării. Ce nu e sigur merge la dispecer, într-o coadă de cel mult 25 de cazuri pe zi; dispecerul aprobă, respinge sau amână, iar planul se recalculează. Pragurile: `config/planner.yaml`; costurile, cu sursa fiecăruia: `config/economics.yaml`; cercetarea: `docs/research/planificator.md`.
>
> **Evaluarea agentului.** `make agent-eval` (~2 min) compară agentul cu strategii simple (top-K după scor, primul venit, aleator, o singură sursă) pe aceleași echipe și restricții: pe 30 de zile sintetice, +49% valoare netă față de cea mai bună strategie simplă, cu mai puțini km și mai puține urgențe ratate; pe ziua demo, cu lucrările reale A și adevărul injectat, agentul vizitează 29 din 50 de cazuri reale de siguranță, față de 2 la ordinea pe valoare. Metoda și limitele: `reports/planner/README.md`; tabelele: `reports/planner/agent_eval.md`.
>
> **API.** `make api` pornește API-ul pe http://127.0.0.1:8710/api (documentație la `/docs`); `CYBERPUNKS_API_SOURCE=demo make api` servește instantaneul din git (`outputs/demo/`), fără să ruleze modelele.

## Pentru firul Interfață (toate rutele, cu `?scenario=`)
- Din contract: `/health` (cu `plan_id`, `mode`), `/scenarios`, `POST /run`, `/plan`, `/work-items`, `/work-items/{id}` (cu `decision` și `action`), `/series/{id}`, `/audit`, `POST /review/{id}`, `/metrics`, `/work-orders/{crew}.pdf`.
- În plus: `/quarantine`, `/alerts`, `/notifications`, `/report`, `/run-info` (timpii pe pași, sursele, solverul), `/rules`, `/remedies` (scara C), `/posts`, `/posts/{post_id}`, `POST /routes/{crew}/approve`, `/approvals` (cu `stale`), `POST /verdict/{id}`, `/labels`, `POST /plan/approve`, `/plan/approval`.
- Ordinea deciziilor în plan: întâi verificările de la distanță și corecțiile din birou, apoi lista pe echipe (`rank` după `threshold.lei_per_work_hour`), apoi restul.

## Urmează (M3)
- Instantaneul final când A, B, C și bilanțul își fixează versiunile.
- O a treia rundă scurtă de revizuire înainte de înghețare, timpii pentru demo, scenariul `maine`.

## Blocaje
- Niciunul.

## Cum se rulează (comenzile exacte)
- `uv sync && make check`
- `uv run cyberpunks run --scenario demo-vara` (sau `--mode existing`, `--mode fixtures`, `--date YYYY-MM-DD`)
- `make api` (sau `CYBERPUNKS_API_SOURCE=demo make api`) → http://127.0.0.1:8710/api/health, documentația la `/docs`
- `make agent-eval` (~2 min), `make solver-bench` (~6 min), `make demo-snapshot`

## Cifre (doar din scripturi, cu comanda)
- `make agent-eval`, 30 de zile SINTETICE: valoare netă pe zi, agentul 35.061 lei, cea mai bună strategie simplă 23.552 (+49%); km pe zi 352 față de 511 la top-K; urgențe ratate 19,6% față de 26,8%. Robust la un model supra-încrezător și la ipotezele fără sursă (+48% … +77%). Tabelele: `reports/planner/agent_eval.md`, graficul: `reports/planner/agent_eval.png`.
- `make solver-bench`: OR-Tools aduce cu 3-19% mai multă valoare netă decât greedy pe 100-300 de lucrări, în 1,4-9 s.
- Ziua demo, 8 iulie 2025, doar contoarele (lucrările reale A, 391, din care 274 probleme reale după `A_ground_truth.csv`; valoarea capturată e valoarea reală): agentul face 33 de vizite, toate pe probleme reale, și vizitează 29 din cele 50 de cazuri reale de siguranță, dar câștigă doar 2.529 lei net, pentru că siguranța e obligatorie și valorează puțin în lei. Fără siguranța obligatorie: 25.394 lei și 14 cazuri de siguranță. Ordinea pe valoare a lui A („primul venit”): 28.825 lei și 2 cazuri. Top-K după scor: 6.179 lei și 2 cazuri. E un compromis de politică (`global.safety_mandatory` în `config/planner.yaml`); pentru prezentare, cifra cinstită e „29 din 50 de cazuri de siguranță față de 2”, nu valoarea netă.

## Decizii (cu ora)
- 12:53 API-ul citește: ultima rulare (`outputs/`), instantaneul `outputs/demo/`, apoi `contracts/fixtures/`; `CYBERPUNKS_API_SOURCE` poate fixa sursa (14:30).
- 12:58 Costuri: vizita 250 lei (tarif RER 2026, PROXY), energia pierdută 0,70 lei/kWh (PZU 2026), tura de furtună 2.700 lei (CALCUL).
- 13:05 Echipa de furtună rămâne în zonă (nodul B e ultimul din traseu); ajunge la ora limită, cel târziu la sfârșitul turei (13:52).
- 13:18 Premiul din trasee = valoarea așteptată − costul acțiunii; încrederea medie cere o marjă de 25%.
- 13:23 La B, `safety_flag` (rafale) e avertisment pentru echipă. 13:31 Pragul etic la contoare: scor ≥ 0,5 pentru o vizită la ușa unui client.
- 13:52 Zonele de furtună peste plafonul regional merg la dispecer, cu alerta „Întăriri necesare”.
- 14:00 Aprobarea omului confirmă decizia agentului, cu acțiunea ei.
- 14:15 Pe ziua demo, agentul trimite întâi cazurile cu risc pentru oameni, chiar dacă valorează puțin în lei; ablația din raport arată cât costă regula.
- 14:28 Coada omului: capacitate de 25 pe zi; abținerile din cauza datelor merg la biroul de date, cele cu valoare mică la urmărire; siguranța obligatorie doar de la scorul 0,7.
