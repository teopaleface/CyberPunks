# Status: Teo-planificator
Actualizat: 2026-11-07 14:37
Milestone curent: M2 gata pe ieșirile reale din `Teo`; M3 în lucru (robustețe, revizuiri, instantaneu, documentație)
Gata de merge: da (commit 4f9fcba, plus acest status)

## Răspuns la cererile orchestratorului de la 14:20
- `git merge Teo` făcut. Planul rulează pe ieșirile din `Teo` (A 391, bilanț 98, B 26, C 41): 40 de lucrări în traseele a 9 echipe, 430 km, 370 de verificări de la distanță și corecții în birou, **25 la om**, 18 mesaje, OR-Tools în 10 s.
- **1. Interfața**
  - `POST /api/plan/approve` `{scenario, plan_id, approver, note}` → `AuditRecord` cu `actor: human`, `action: plan_approved`; 409 dacă `plan_id` nu mai e planul curent (s-a replanificat între timp). `GET /api/plan/approval?scenario=` → `{approved, plan_id, approver, ts, stale}`.
  - `GET /api/posts` există (de la 13:46); acum citește și `extra.lei_per_month` al bilanțului: pe 8 iulie, 22 de posturi roșii, 41 galbene, 237 verzi, toate în registrul C. `posts.json` se scrie la fiecare rulare în `outputs/plans/<s>/` și e în instantaneu (`outputs/demo/plans/demo-vara/posts.json`).
  - **Pornirea pentru demo** (planul real, nu exemplele):
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

## Cereri către orchestrator (te rog transmite)
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

## Pentru firul Interfață (toate rutele, cu `?scenario=`)
- Din contract: `/health` (cu `plan_id`, `mode`), `/scenarios`, `POST /run`, `/plan`, `/work-items`, `/work-items/{id}` (cu `decision` și `action`), `/series/{id}`, `/audit`, `POST /review/{id}`, `/metrics`, `/work-orders/{crew}.pdf`.
- În plus: `/quarantine`, `/alerts`, `/notifications`, `/report`, `/run-info` (timpii pe pași, sursele, solverul), `/rules`, `/remedies` (scara C), `/posts`, `/posts/{post_id}`, `POST /routes/{crew}/approve`, `/approvals` (cu `stale`), `POST /verdict/{id}`, `/labels`, `POST /plan/approve`, `/plan/approval`.
- Ordinea deciziilor în plan: întâi verificările de la distanță și corecțiile din birou, apoi lista pe echipe (`rank` după `threshold.lei_per_work_hour`), apoi restul.

## Urmează (M3)
- Evaluarea refăcută pe ieșirile noi (rulează acum), apoi instantaneul final când A, B, C și bilanțul își fixează versiunile.
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
- Ziua demo (cifrele noi vin după evaluarea care rulează acum).

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
