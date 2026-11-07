# Tema PPC: "24h to Power PPC"

Transcrisă din pozele cu slideurile prezentate la deschidere și din documentul oficial `Smarthack_XI_2026_Tema_PPC.pdf` (3 pagini, primit pe 7 nov. 2026, în jur de 12:05). Originalele sunt în `materiale/` (local, nu intră în git). Unde PDF-ul și slideurile diferă, PDF-ul are prioritate.

## Tema

"24h to Power PPC. AI in energy, from data to action."

> Now that you know who PPC is, it's your turn: build an AI agent that, based on an ML model you train, makes decisions and takes action on a real energy problem.

Pe românește: un agent AI care ia decizii și face acțiuni pe o problemă reală de energie, sprijinindu-se pe un model ML antrenat de noi.

Agentul are patru pași:

| Pas | Ce scrie pe slide | Ce înseamnă pentru noi |
|---|---|---|
| Perceive | reads the environment through data: time series, alarms, text, images | Citește date: serii de timp, alarme, text, imagini |
| Estimate | your ML models estimate risk, urgency, forecasts | Modelul nostru estimează risc, urgență sau prognoze |
| Decide | thresholds chosen for a reason, real constraints, confidence level | Praguri justificate, constrângeri reale (oameni, bani, capacitate), nivel de încredere |
| Act | prioritizes, alerts, schedules, reports | Prioritizează, alertează, programează, face rapoarte |

"Pick your challenge from any of the companies": PPC Renewables, Rețele Electrice, PPC Energy, PPC Blue. Alegem problema de la oricare dintre cele patru firme.

## Cerințe obligatorii ("What you need")

1. **Your own ML model.** Cel puțin un model ML antrenat sau fine-tuned de echipă, evaluat pe un set de test separat și comparat cu o metodă simplă de referință (baseline). Codul de antrenare stă în repo. Modelul rulează în codul nostru, nu printr-un API extern.
2. **An LLM is not enough.** Un LLM poate orchestra agentul sau face interfața, dar agentul trebuie să se bazeze pe modelul nostru.
3. **Actions, not just chat.** Agentul trebuie să facă acțiuni: prioritizează, recomandă, generează, alertează sau planifică.
4. **Public or synthetic data.** Doar date publice sau sintetice, cu sursele citate.

## Jurizare: grilă de 100 de puncte

"The best idea for PPC, implemented best, wins. One without the other is not enough."

| Criteriu | Puncte | Ce verifică |
|---|---|---|
| Idea and relevance for PPC | 25 | O problemă reală, bine formulată, credibilă pentru colegii de la PPC |
| ML quality | 25 | Date, model, set de test separat, baseline, analiza erorilor |
| The agent | 25 | Flux automat de la date la acțiune, decizii justificate |
| Robustness | 10 | Date lipsă, cazuri rare, incertitudine |
| Explainability | 10 | De ce a luat agentul decizia |
| Demo and repository | 5 | Prezentare clară, README cu pași care se pot reproduce |

## Ce predăm și când

- Repo GitHub: proiectul care merge, plus materialele de prezentare.
- Termen: duminică, 8 nov. 2026, ora 12:00 ("time is up").
- Demo live de la ora 13:00: 5 minute de demo, în ce format vrem, apoi 2 minute de întrebări tehnice.
- Atenție: regulamentul ASMI spunea 10 minute de prezentare. PPC spune 5 + 2. Ne pregătim pentru 5 minute.

## Ce aduce în plus documentul oficial (PDF)

### Reguli noi sau mai stricte

- **Repo-ul trebuie să fie public**, pe GitHub, iar commit-urile trebuie făcute pe parcursul celor 24 de ore. Istoricul de commit-uri se notează la "Demo și repository". Concluzie: facem commit-uri mici și dese și facem repo-ul public înainte de predare.
- Datele pot fi publice, sintetice **sau colectate și adnotate de echipă**, cu sursele menționate.
- La robustețe se adaugă **datele de intrare greșite** (pe lângă date lipsă, cazuri rare și incertitudine). "Un agent bun știe să spună «nu sunt sigur» și să trimită cazul la un om."
- Reproductibilitate: oricine din juriu poate rula proiectul după README, iar rezultatele din prezentare se pot obține din nou cu scriptul nostru de evaluare.
- Explicabilitate: de exemplu prin importanța features-urilor sau prin cazuri similare din istoric.
- Livrabile: proiectul funcțional în repo public, plus materialele de prezentare (slideuri, notebook sau altele), și un demo live urmat de întrebări tehnice. PDF-ul nu dă durata demo-ului; slideul spunea 5 minute plus 2 de întrebări.
- "Demo și repository" (5 puncte) cere explicit: prezentare clară, README reproductibil, **cod curat, istoric de commit-uri**.

### Ce înseamnă "proiect complet", după PPC

Acoperă fiecare pas, de la datele brute la acțiunea finală, automat, fără intervenție manuală între pași:
- Date pregătite de echipă: surse alese și justificate, date curățate, combinate, adnotate sau generate sintetic în mod realist, features construite cu un motiv clar.
- Model antrenat și evaluat corect: set de test separat, comparația cu baseline-ul, analiza erorilor (unde greșește, pe ce cazuri și ce am încercat ca să corectăm).
- Strat de decizie justificat: praguri alese cu motiv, constrângeri reale ("câte cazuri poate verifica o echipă pe zi"), nivelul de încredere al modelului.
- Acțiuni concrete: listă de priorități, alertă, raport sau intervenție programată.
- Situații dificile: date lipsă, cazuri rare, intrări greșite, incertitudine.
- Explicabilitate și reproductibilitate (mai sus).

### Ce fel de agent au în minte (citate și parafraze din PDF)

- Datele pe care le folosesc colegii PPC: serii de timp (contoare inteligente, producție din parcuri, SCADA de la turbine și invertoare, prețuri de piață), date externe (meteo, calendar și sărbători, evenimente locale), date operaționale (alarme din rețea, istoric de intervenții și defecte, rapoarte de teren, sesiuni de încărcare), date despre clienți (contracte, facturi, plăți, reclamații în text liber), imagini și date spațiale (fotografii și imagini termice de la drone, hărți ale rețelei, locațiile stațiilor).
- Deciziile zilnice: "ce alarmă e reală, ce echipamente riscă să se defecteze, ce clienți trebuie verificați și ce solicitări se tratează primele".
- Tipurile de probleme ML: regresie și prognoză pe serii de timp, detecție de anomalii cu etichete puține, clasificare pe date dezechilibrate, clusterizare și ranking sub constrângeri de capacitate.
- "Un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață, iar o prognoză de consum nu reechilibrează rețeaua." Valoarea apare când predicția devine decizie și decizia devine acțiune.
- Agentul poate combina mai multe modele. Exemplul lor: un model clasifică solicitarea clientului după subiect (factură, avarie, contract), un al doilea estimează urgența, ca să decidă ce caz se tratează primul. Poate lega acțiuni: listă de priorități, alertă la echipa potrivită, programarea intervenției, raport.
- "Fiecare decizie poate fi urmărită până la predicția modelului care a produs-o." Concluzie: jurnal de decizii cu ID-ul predicției, versiunea modelului și pragul folosit.
- Grila e aceeași ca pe slide (25/25/10/25/10/5). "Cine câștigă: echipa care are cea mai bună idee pentru PPC și o implementează cel mai bine. Una fără cealaltă nu e suficientă."

## Al doilea set de criterii (slide în română, sursă neclară)

Slide separat, cu fundal albastru închis, alt stil decât slideurile PPC. Nu apare în niciuna dintre cele două prezentări primite. Probabil sunt criteriile generale ASMI sau ale premiilor speciale.

- Inovație și creativitate: ce elemente originale aduce?
- Utilitate practică: este ușor de folosit și relevant pentru utilizatori?
- Etică și responsabilitate: cum sunt protejate datele și explicate deciziile AI?
- Sustenabilitate: costuri de întreținere, de infrastructură și de scalabilitate.

## Ce rezultă pentru proiect (checklist)

- [ ] O problemă luată dintr-o firmă PPC anume, spusă cu cifrele lor (din `08-ppc-workshop-ai.md`).
- [ ] Set de date public citat, sau date sintetice generate de noi, cu generatorul în repo și explicat.
- [ ] Împărțire train / test separată (pe timp, dacă sunt serii de timp, ca să nu "vadă viitorul").
- [ ] Un baseline simplu (regulă, medie, persistență) și modelul nostru, cu aceleași metrici pe același test.
- [ ] Analiza erorilor: unde greșește modelul și de ce.
- [ ] Agent care trece automat prin Perceive, Estimate, Decide, Act, fără om la fiecare pas.
- [ ] Praguri alese cu motiv (cost, capacitate) și nivel de încredere la fiecare decizie.
- [ ] Comportament la date lipsă, cazuri rare și încredere mică (de exemplu, trimite la om).
- [ ] Explicație pentru fiecare decizie (ce a contat și cât).
- [ ] Protecția datelor (ID-uri pseudonimizate, nimic personal) și om în buclă pentru deciziile cu impact.
- [ ] Costuri de rulare mici: modelul rulează local, fără API plătit.
- [ ] README cu pași de instalare și rulare care merg de la zero, plus un script de evaluare care refăce cifrele din prezentare.
- [ ] Commit-uri mici și dese pe tot parcursul celor 24 de ore.
- [ ] Repo public înainte de predare (vezi `06-intrebari-deschise.md` despre ce scoatem înainte).
- [ ] Intrări greșite tratate (valori imposibile, format greșit) și "nu sunt sigur" trimis la om.
- [ ] Jurnal de decizii: fiecare acțiune duce la predicția, modelul și pragul care au produs-o.
- [ ] Prezentare de 5 minute, urcată în repo înainte de 12:00.
