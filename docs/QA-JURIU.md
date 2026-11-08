# Întrebările tehnice ale juriului PPC: răspunsuri scurte

Pentru cele 2 minute de întrebări de după demo. Fiecare răspuns are 2-3 propoziții, cu cifra și fișierul din care vine. Cifrele sunt luate din `reports/` și `status/` de pe ramura `Teo` (7 nov. 2026, 16:45); regulile și costurile vin din `config/`. Răspunde cine deține subiectul: A (contoare), B (furtună), C (prosumatori), bilanțul, agentul (planificatorul).

Reguli pentru răspuns: prima propoziție e răspunsul, a doua e cifra, iar a treia, doar dacă e nevoie, e limita. Dacă nu știm, spunem asta și arătăm ce ar trebui confirmat cu PPC (întrebarea 28).

## Datele

**1. De ce date din China (SGCC) și din Londra pentru contoare, și nu date PPC?**
Nu există un set public cu contoare defecte etichetate din România. SGCC are etichete reale de furt pentru 42.372 de clienți (3.615 cu furt). Londra are consum real la 30 de minute de la 1.414 gospodării, peste care am injectat 7 tipuri de defecte și 8 tipuri de furt. Etichetele din Londra sunt construite de noi, deci 60,6% din testul lui A e sintetic. Sursa: `reports/A/model_card.md` (Date), `reports/A/metrics.json` (`synthetic_share` 0,6059).

**2. De ce date din SUA pentru furtuni?**
EAGLE-I (ORNL) e setul public cu clienții fără curent pe zonă, la 15 minute, pe mai mulți ani (licență CC BY 4.0). Pentru România nu există un istoric public de avarii. Am luat 80 de comitate din 8 state cu climă continentală: 58.480 de zile-comitat la antrenare și 29.200 la test, cu vremea Open-Meteo, aceeași sursă meteo pe care o folosim în România. Sursa: `reports/B/metrics.json` (`dataset`), `status/Teo-B-furtuna.md` (Cifre).

**3. De ce SimBench pentru tensiunea din posturi?**
Rețelele de joasă tensiune ale Rețele Electrice nu sunt publice. SimBench dă topologii și profile reale (licență ODbL), pe care am construit 480 de posturi sintetice, cu tensiunea calculată cu pandapower. Etichetele vin din fizică: diferența maximă față de pandapower e 5,2e-08 pu. Sursa: `reports/C/model_card.md` (Datele), `reports/C/powerflow_bench.json`.

**4. Ce e real și ce e sintetic?**
- B nu are nimic sintetic (`synthetic_share` 0,0).
- A e 60,6% sintetic (Londra cu defecte injectate).
- C și bilanțul sunt 100% sintetice (SimBench plus simulare).
- În demo, contoarele, posturile, echipele și bazele sunt sintetice, așezate pe hartă reală. Vremea din 8 iulie 2025 și prognoza pentru mâine sunt reale.
Sursa: `reports/*/metrics.json` (`synthetic_share`), `config/crews.yaml` (echipe SIMULATE).

## Împărțirea pe antrenare și test

**5. Cum ați evitat să „vedeți viitorul”?**
Fiecare model e testat pe ce n-a văzut:
- B: antrenare pe 2023-2024 și test pe 2025, adică 29.200 de zile-comitat, plus 8 state ținute pe rând deoparte.
- A: gospodării nevăzute și perioadă ulterioară la Londra, clienți nevăzuți la SGCC.
- C: rețele nevăzute (câte o topologie lăsată deoparte) și luni nevăzute, adică 324.000 de zile-post din 2025.
Sursa: câmpul `split` din `reports/B/metrics.json`, `reports/A/metrics.json` și `reports/C/metrics.json`.

**6. Ați ales parametrii uitându-vă la test?**
Nu. B i-a ales doar pe scorurile out-of-fold din anii de antrenare, din 24 de configurații. A și-a ales variabilele pe validare și a privit testul o singură dată pe versiune. Sursa: `reports/B/tuning.json`, `reports/A/feature_selection.json`, `reports/A/model_card.md` (Date).

## Metodele simple de comparație

**7. B: față de ce comparați și cu cât bateți?**
Pe 2025, PR-AUC-ul modelului e 0,278, față de 0,182 la regula pe rafală și 0,151 la climatologia pe comitat și lună. Brier e 0,0841 față de 0,0914. Pe state nevăzute, modelul bate ambele metode simple în 8 din 8 state (PR-AUC mediu 0,259 față de 0,188 și 0,122). Sursa: `reports/B/metrics.json`, `reports/B/metrics_detail.json` (`loso_summary`).

**8. A: față de ce comparați?**
Pe etichetele reale (SGCC), precizia@K e 0,80, față de 0,035 pentru regula „zero 7 zile sau scădere de 50%”, 0,106 pentru VEE și 0,165 pentru IsolationForest. PR-AUC e 0,399, față de 0,08-0,11 la metodele simple. Sursa: `reports/A/metrics.json`, `reports/A/model_card.md`.

**9. C: față de ce comparați?**
Eroarea medie a tensiunii maxime e 0,0054 pu, față de 0,0228 pu la o regresie pe soare × kW/kVA. Pentru depășirea de 1,10 pu, PR-AUC e 0,951 față de 0,427, iar recall-ul e 86,5% față de 25,6%. Sursa: `reports/C/metrics.json` (`mae_vmax_pu`, `pr_auc_exceed`, `recall_exceed`).

**10. Bilanț: față de ce comparați?**
Pierderea normală a postului are eroarea medie de 5,30 kWh pe zi, față de 14,91 la formula fizică I²R și 20,59 la un procent fix. Diagnosticul cauzei are F1 macro 0,71, față de 0,48 la reguli. Sursa: `reports/bilant/metrics.json` (`normal_mae_kwh_day`, `diagnoza_macro_f1`).

## Precizia@K de 1,00 a lui A

**11. Precizia@K de 1,00 nu e prea frumoasă ca să fie adevărată?**
E pe setul din Londra cu defecte injectate, la K = 130 (1% din contoare). Primele 130 sunt defecte evidente: 46 de contoare blocate, 34 oprite, 28 cu citiri negative. Cifra care arată ce adaugă modelul e precizia pe problemele subtile: 0,62, față de 0,02 la VEE. Pe etichetele reale (SGCC) precizia e 0,80, iar dacă K crește la toate cele 597 de probleme, scade la 0,66. Sursa: `reports/A/error_analysis.md` (secțiunea 2), `reports/A/metrics.json`.

## Transferul din SUA în România

**12. Cum aplicați în Banat un model antrenat în SUA?**
Am împărțit județele în 26 de zone de mărimea unui comitat american. Modelul folosește doar variabile care nu depind de țară (rafală, ploaie, zăpadă, polei, sezon, mărimea și densitatea zonei) și aceeași sursă meteo. Testul pe state nevăzute imită situația României: PR-AUC 0,259, iar modelul bate metodele simple în 8 din 8 state. Fiecare lucrare spune „validat pe date externe; de calibrat pe istoricul Rețele Electrice”. Sursa: `reports/B/model_card.md`, `reports/B/metrics_detail.json`.

**13. Ce dovadă aveți că merge în România?**
Am verificat trei furtuni reale din presă:
- 8 iulie 2025, cod roșu în Banat: riscul mediu e 0,31 în Banat față de 0,07 în rest, cu echipă recomandată în 22 de zone-zi din Banat și în niciuna din rest.
- 17 iulie 2025, Slobozia: zona iese pe locul 1 din 26, la egalitate cu Oravița (P = 0,36).
- 26 noiembrie 2023, viscol în Dobrogea: riscul mediu e 0,87 în Dobrogea față de 0,09 în rest, iar toate cele 10 zone din Dobrogea primesc echipă.
Fără istoricul RER, verificarea e calitativă. Sursa: `reports/B/backtest_romania.md`.

**14. De ce ați scos temperatura din model?**
Cu temperatura, modelul trimitea echipe în zonele cu caniculă din Ialomița chiar în ziua furtunii din Banat, iar verile românești sunt mai calde decât ce a văzut modelul în SUA. Pe testul din SUA, renunțarea costă 1,9% din PR-AUC (0,278 față de 0,283). Sursa: `reports/B/experiments.json` (`cu_temperaturi`), `status/Teo-B-furtuna.md` (Decizii).

**15. Prognozele subestimează vijeliile. Cum tratați asta?**
Da, le subestimează: pe 8 iulie 2025, arhiva dă rafale de 40-85 km/h, iar măsurătorile au fost de 90-120 km/h. Modelul e antrenat pe aceeași vreme netezită, deci ordonează corect zonele. Incertitudinea vine din 40 de membri ICON-EPS pentru mâine și din 3 modele meteo pentru zilele trecute; când nu se pun de acord, decide omul. Sursa: `reports/B/backtest_romania.md` (Verdict), `reports/B/model_card.md`.

## Intervalele de încredere

**16. Cât de sigure sunt intervalele?**
- B: intervalul P10-P90 cuprinde 80,8% din vârfurile reale din 2025, față de ținta de 80% (72,2% fără calibrarea conformală).
- C: 82,1% pe rețele nevăzute, între 75,8% (semiurb5) și 87,1% (rural2), cu un interval de 4 ori mai îngust decât al metodei simple (0,018 pu).
Sursa: `reports/B/metrics.json` (`coverage_p10_p90`), `reports/C/metrics_detail.json` (`by_topology`).

**17. Când spune modelul „nu sunt sigur”?**
- B, când: lipsește vremea; vremea iese din ce a văzut modelul; zona e mai mare decât orice comitat din antrenare și vremea e periculoasă; modelele meteo nu se pun de acord și intervalul (de cel puțin 0,35) trece peste prag.
- A, când are sub 60 de zile de citiri din 180.
- Agentul, când intervalul trece de 0,5 sau datele lipsă trec de 40%. Coada omului are cel mult 25 de cazuri pe zi.
Sursa: `reports/B/model_card.md`, `reports/A/error_analysis.md` (secțiunea 6), `config/planner.yaml`.

## Agentul

**18. Cum decide agentul?**
Prin reguli în cod, nu printr-un LLM: fiecare lucrare primește o decizie cu `rule_id`, pragurile folosite și motivul în română. Trimite o echipă doar dacă valoarea așteptată depășește costul (tura de furtună 2.700 lei, vizita la contor 250 lei) și doar peste pragurile minime: scor ≥ 0,5 pentru vizita la contor, risc ≥ 0,15 pentru furtună. Capacitatea e limitată (11 echipe simulate, cel mult 3 pe regiune la furtună), iar traseele vin din OR-Tools. Sursa: `config/planner.yaml`, `config/economics.yaml`, `status/Teo-planificator.md`.

**19. E mai bun decât o regulă simplă?**
Pe o lume sintetică de 30 de zile, agentul aduce 35.061 lei pe zi valoare netă, față de 23.552 lei la „primul venit” și 23.255 la „top-K”, adică +49%. Face 352 km pe zi, față de 515. Avantajul rămâne între +48% și +77% când variem costurile ipotetice. Sursa: `reports/planner/agent_eval.md`.

**20. Cum ajungeți de la o decizie la predicția care a produs-o?**
Fiecare decizie are o linie în `audit.jsonl`, cu `prediction_id`, `model_version`, `rule_id`, pragurile și amprenta intrărilor. Decizia omului intră în același jurnal, cu `actor: human`, iar aprobarea unui plan schimbat între timp e refuzată. Sursa: `docs/CONTRACTS.md`, `status/Teo-planificator.md`.

**21. Ce se întâmplă dacă pică o sursă de date sau internetul?**
B folosește ultima prognoză salvată și scrie asta în lucrare. Dacă nu există nicio copie, scrie totuși cele 26 de lucrări, toate trimise la om, cu motivul „vremea indisponibilă”. Planificatorul marchează sursa „missing” sau „degraded” și lucrează cu celelalte. Sursa: `status/Teo-B-furtuna.md` (Făcut), `docs/CONTRACTS.md`.

**22. De ce ar avea un dispecer încredere?**
Fiecare lucrare explică decizia: factorii în cuvinte simple (de exemplu „rafale de 72 km/h în ziua de dinainte, 15 mm de ploaie în 48 de ore”), trei zile istorice asemănătoare cu ce s-a întâmplat atunci și, la C, de ce nu s-a ales o soluție mai ieftină. Cifrele din frază sunt calculate în cod, nu generate de un LLM. Sursa: `reports/B/model_card.md`, `reports/C/model_card.md` (Explicabilitatea).

## Bilanțul

**23. Ce e bilanțul și de ce câștigul lui e mic?**
Bilanțul compară energia ieșită din post cu suma contoarelor clienților și explică diferența, pe 6 cauze. Pus peste A, câștigul e mic, din două motive: A e deja precis în vârf (precizie 1,0 cu și fără bilanț până la K = 300), iar pierderea unui singur contor, de câțiva kWh pe zi, se pierde în zgomotul postului. Valoarea lui e în ce nu văd contoarele: 48% din energia pierdută în ziua demo, din care găsește 85%. Sursa: `reports/bilant/model_card.md`, `reports/bilant/error_analysis.md` (secțiunea 3), `reports/bilant/metrics.json`.

## Etica

**24. Nu riscați să trimiteți controale la oameni săraci?**
Un consum mic poate însemna sărăcie sau casă goală, nu furt. De aceea furtul suspectat la consum mic merge la om, nu direct la vizită, iar o vizită cere scor ≥ 0,5. Pe SGCC, regula simplă ar trimite echipa la 19,4% din consumatorii foarte mici, iar modelul la 0,4%. Sursa: `reports/A/model_card.md`, `status/Teo-A-contoare.md` (Cifre), `config/planner.yaml` (`meters.visit_min_score`).

**25. Ce înseamnă EU AI Act pentru voi?**
Sistemele AI pentru infrastructură critică sunt de risc ridicat. Răspunsul nostru: omul aprobă planul, fiecare decizie e în jurnal, iar documentația e în model card-uri. Încadrarea juridică exactă n-am verificat-o cu un jurist; A o spune explicit. Sursa: `reports/B/model_card.md` (Responsabilitate), `reports/C/model_card.md`, `reports/A/model_card.md` (Etică).

**26. Ce date personale folosiți?**
Niciuna. ID-urile contoarelor și posturilor sunt sintetice, fără nume sau adrese, iar mesajele către clienți sunt de grup, pe post. Sursa: `reports/A/model_card.md`, `reports/C/model_card.md`, `docs/data/C.md`.

## Costuri și scalare

**27. Cât costă și cum ar rula pe platforma PPC (S3, Spark, NiFi)?**
Totul rulează local, fără API plătit: un plan complet durează circa 26 de secunde, iar C calculează 300 de posturi pe o zi în 0,05 secunde, față de 66,6 secunde cu pandapower. Modelele sunt LightGBM pe procesor, deci se pot rula ca job-uri pe date deja preluate în data lake. Integrarea efectivă cu S3, Spark sau NiFi nu e construită (vezi „Puncte slabe”). Sursa: `status/Teo-planificator.md`, `reports/C/metrics.json`.

**28. Ce trebuie confirmat cu PPC înainte de producție?**
- Pentru B: istoricul de avarii pe zone, ca să calibrăm transferul din SUA.
- Pentru A: contoare defecte etichetate și prevalența reală (acum ipoteză: 3% defecte, 2% furt).
- Pentru C: topologia din GIS și priza fiecărui post.
- Pentru bilanț: câte posturi au contor de bilanț.
- Pentru agent: echipele, turele și costurile reale, care acum sunt simulate sau ipoteze.
Sursa: `reports/A/model_card.md` (Limite), `reports/C/error_analysis.md` (secțiunea 6), `config/crews.yaml`, `config/economics.yaml`.

**29. De ce nu lăsați un LLM să decidă?**
Tema cere ca deciziile să vină din modelele noastre și din reguli scrise în cod. Un LLM nu dă probabilități calibrate și nu lasă un jurnal verificabil. La noi, frazele explicațiilor sunt șabloane completate cu cifre din cod. Sursa: `reports/B/model_card.md`, `reports/C/model_card.md`.

**30. Cum ați ales pragurile?**
- Pragul de furtună al lui B, 0,16, e cel mai bun F1 pe scorurile out-of-fold din anii de antrenare.
- Agentul trimite echipe doar peste risc 0,15 și doar dacă valoarea netă e pozitivă.
- Pragul de 0,5 pentru vizita la contor e un prag etic.
- O echipă ajută cel mult 500 de clienți într-o tură, calculat din furtuna din Timiș: circa 40.000 de consumatori și 80 de echipe.
Sursa: `reports/B/metrics.json` (`decision_threshold`), `config/planner.yaml`, `config/economics.yaml` (`customers_helped_per_crew_shift`).

## Întrebări despre demo

**31. În fereastra furtunii (15:00-21:00), vântul din grafic scade. De ce trimiteți echipa?**
Graficul arată arhiva Open-Meteo, care netezește vijeliile: la Timișoara dă cel mult 50 km/h la 14:00 și 37 km/h la 15:00. Furtuna reală a avut rafale măsurate de 90-120 km/h (Transelectrica), iar ANM a dat cod roșu de vijelii exact pentru 15:00-21:00. Cu o seară înainte, prognoza ICON dădea 68-72 km/h la Reșița, Caransebeș și Deva, iar ECMWF arăta aer foarte instabil la Timișoara (CAPE de 1.960 J/kg). Riscul modelului din grafic urcă exact la 15:00, odată cu ploaia de furtună: de la 0,19 la 0,36, apoi la 0,43. Orele sunt ora României (+03:00): vremea e cerută cu fusul Europe/Bucharest. Sursa: seria `B-20250708-TM-TIMISOARA` (`expected` = riscul zilei, cu vremea de până la acea oră), `reports/B/backtest_romania.md`, `docs/research/B.md` (secțiunea 3).

**32. Ați încercat și date europene? De ce nu folosiți un model antrenat în Europa?**
Da: am antrenat a doua variantă pe avariile reale de joasă tensiune din nordul Scoției (SSEN, 2016-2025), unde fiecare avarie are cauza scrisă, și am testat-o pe anii nevăzuți 2024-2025. În Scoția, varianta europeană are PR-AUC 0,296, iar modelul nostru pe SUA, care n-a văzut niciodată date europene, are 0,277; amândouă bat climatologia locală (0,161). Invers, pe SUA modelul european scade la 0,159, față de 0,278. Pe furtuna de vară din Banat dă doar 0,09, pentru că a învățat mai ales furtunile de iarnă dinspre ocean, deci agentul rămâne pe modelul pe SUA. Sursa: `reports/B/metrics_ssen.json`, `reports/B/metrics_ssen_detail.json` (`decision_ro`), `reports/B/model_card.md`.

**33. Cum verificați mărimea avariilor în România, fără istoricul Rețele Electrice?**
Cu cifrele oficiale anuale, nu pe furtună. Rețele Electrice Banat a raportat pentru 2025 un SAIDI din condiții meteorologice deosebite de 92,87 de minute pe utilizator în mediul rural și de 16,94 în mediul urban, la joasă tensiune. Furtuna din 7-9 iulie 2025 a afectat circa 40.000 de consumatori (4,1% din clienții din Banat); la o întrerupere medie de 8 ore (ipoteză), asta înseamnă circa 20 de minute de SAIDI, același ordin de mărime. Sursa: `reports/B/backtest_romania.md` (Ordin de mărime), `docs/research/B.md` (secțiunea 5).

## Puncte slabe (de reparat sau de pregătit răspunsul)

1. **Platforma PPC (S3, Spark, NiFi):** niciun fișier nu descrie cum ar rula modelele pe ea, cât ar costa în cloud sau cât ar dura pe peste 2 mil. de contoare.
2. **Agentul pe ziua demo:** valoarea netă a agentului (2.529 lei) e mult sub cea a strategiei „primul venit” (28.825 lei), din cauza cazurilor de siguranță obligatorii. Răspunsul recomandat de planificator: agentul vizitează 29 din 50 de cazuri de siguranță, „primul venit” doar 2 (`status/Teo-planificator.md`, Cifre).
3. **A:**
   - Precizia@K de 1,00 e pe date sintetice.
   - Pe SGCC, cu împărțirea pe timp, precizia scade la 0,40 (`reports/A/robustness.json`, `sgcc_time_split`).
   - Fișierele dau cifre ușor diferite: 0,80 față de 0,812 și 0,64 față de 0,66. Trebuie aliniate.
   - `test_size` 21.503 înseamnă 13.028 eșantioane din Londra plus 8.475 din SGCC; de explicat dacă se întreabă.
4. **B:**
   - 61% din evenimente apar în zile fără semnal meteo puternic.
   - La zăpada fără vânt, modelul prinde doar 12% din avarii.
   - Testul folosește vremea reconstituită, nu prognoza din ziua de dinainte, deci cifrele sunt o limită de sus (`reports/B/error_analysis.md`, `reports/B/model_card.md`).
5. **Bilanțul:**
   - E 100% simulat.
   - Peste scorurile reale ale lui A câștigul e nul.
   - În `reports/bilant/demo_posts.md` (secțiunea 3) apare textul „…: False”, care pare o eroare de formulare.
6. **C:** e 100% sintetic, pe rețele germane, cu rezoluție orară (normele cer medii pe 10 minute). Acoperirea intervalului scade la 75,8% pe semiurb5 (`reports/C/model_card.md`, Limite).
7. **Evaluarea agentului:** e făcută pe o lume sintetică. Câștigul de timp la restabilire (2,5 h), costul pe client-oră (12 lei) și cei 500 de clienți pe echipă sunt IPOTEZE (`reports/planner/README.md`, Limite).
8. **Etica:** sărăcia energetică e analizată doar la A, nu și la B sau C (de exemplu, cine primește mesajele de la C).
9. **Încadrarea după EU AI Act:** n-a verificat-o un jurist.
