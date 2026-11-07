# Tema PPC: "24h to Power PPC"

Transcrisă din pozele cu slideurile prezentate la deschidere, 7 nov. 2026. Pozele originale sunt în `materiale/poze-slideuri/` (local, nu intră în git).

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
- [ ] README cu pași de instalare și rulare care merg de la zero.
- [ ] Prezentare de 5 minute, urcată în repo înainte de 12:00.
