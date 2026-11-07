# Workshopul PPC "AI Awareness Briefing / Meet PPC"

Din prezentarea `PPC_AI_awareness.pptx` (33 de slideuri), primită la SmartHack XI 2026. Fișierul și textul complet sunt în `materiale/` (local). Unele slideuri sunt marcate "Internal" sau "Internal Confidential", de aceea originalul nu intră în git.

## Cifrele PPC România, cum le spun ei

- PPC Renewables Romania: peste 1,6 GW instalați, "cel mai mare producător privat de energie regenerabilă din România".
- Rețele Electrice Romania: circa 136.000 km de linii în Muntenia, Banat și Dobrogea ("de 3,4 ori în jurul Pământului"), 293 de stații de transformare, peste 26.000 de posturi de transformare.
- PPC Energy: circa 3 milioane de clienți, circa 80 de magazine, servicii digitale.
- PPC Blue Romania: peste 1.100 de puncte de încărcare, mai mult de jumătate rapide sau ultra-rapide. Presa spunea peste 1.400; folosim cifra lor, 1.100+.
- Peste 2 milioane de contoare inteligente, fiecare trimite 96 de citiri pe zi (una la 15 minute), adică circa 192 de milioane de rânduri pe zi.
- Producția eoliană urmează vremea, iar PPC o prognozează pe intervale de 15 minute pentru ziua următoare.
- Energia se cumpără înainte să fie consumată, deci fiecare eroare de prognoză costă bani.
- Datele de consum ajung la furnizori în minute, nu în zile, datorită platformei lor de date. Ei spun că e o premieră în distribuția din România.

## Platforma de date a contoarelor (construită intern de PPC Digital Solutions)

- Colectare: contoare inteligente și concentratoare în teren.
- Preluare: Apache NiFi (flux continuu) și Airflow (loturi).
- Stocare: data lake pe Amazon S3, straturile Bronze și Silver.
- Procesare: Spark / PySpark pe AWS EMR.
- Rezultate: dashboarduri în Redshift și fluxuri Kafka pentru furnizori.
- **Ce urmează, spus de ei: AI.** Detectarea anomaliilor în comportamentul contoarelor, monitorizare predictivă a contoarelor defecte, dashboarduri asistate de AI.

## Portofoliul AI al PPC România (9 proiecte)

PROD = în producție, DEV = în dezvoltare.

| # | Proiect | Stare | Ce face | La ce folosește |
|---|---|---|---|---|
| 01 | Smart Sentry | PROD | ML pentru predicția defectelor, analiza tendințelor, detectarea anomaliilor (uzura cutiei de viteze la turbine, degradarea panourilor solare) | Mentenanță proactivă, semnalarea automată a comportamentului neașteptat |
| 02 | Energy Anomaly Detection | PROD | Găsește tipare de consum neregulate sau suspecte, din istoric și abateri de comportament | Estimează energia recuperabilă și consumul fraudulos, raportare |
| 03 | LegalRoute | PROD | OCR plus LLM extrag și clasifică informații din documente scanate (juridice) | Trimite documentul direct la persoana potrivită din firmă, fără citire și redirecționare manuală |
| 04 | Inverter Smart Extractor | PROD | Extrage automat date din PDF-uri nestructurate în tabele standard | Mai puțină muncă manuală, date gata de analiză |
| 05 | Short Term Energy Demand Forecast | PROD | Prognoza consumului la 15 minute pentru ziua următoare, din istoric și tot mai multe variabile | Mai puțin risc de a cumpăra prea mult sau prea puțin, decizii de trading mai bune, costuri mai mici |
| 06 | AI Claims Agent | DEV | Agent vocal care sună clienții cu facturi restante, le amintește să plătească, află de ce nu plătesc și, după regulile interne, propune eșalonări | Mai puțină muncă manuală, recuperare mai rapidă, tratament consecvent |
| 07 | ReClassAI | PROD | NLP care reclasifică reclamațiile de pe site-ul Rețele Electrice când clientul a ales categoria greșită | Mai puține verificări manuale, răspuns mai rapid la reparațiile critice, respectarea termenelor (SLA) |
| 08 | Short Term Energy Production Forecast | DEV | Prognoza producției parcurilor eoliene, la nivel de parc, la 15 minute pentru ziua următoare | Mai puține costuri de dezechilibru, trading mai bun |
| 09 | AgentHub | DEV | Platformă centrală pentru toți agenții AI din PPC, cu chatbot intern pe documentele departamentelor | Un singur loc unde fiecare angajat lucrează cu agenți, cu fiecare interacțiune urmărită și stocată sigur |

Ce înseamnă pentru noi: dacă facem ceva ce au deja în producție (prognoza consumului, frauda, reclasificarea reclamațiilor), juriul ne compară cu soluția lor. Mai bine luăm ce au spus că urmează (contoare defecte) sau un pas pe care ei nu-l acoperă (decizia și acțiunea de după model).

## Partea de guvernanță AI (slideurile 10-32)

- Se bazează pe NIST AI RMF 1.0, NIST AI 600-1 (profilul pentru AI generativ), EU AI Act, ghidurile EDPS.
- EU AI Act: sistemele AI pentru infrastructură critică (utilități, transport) sunt "high risk", cu obligații de la august 2026: date de calitate și teste de bias, supraveghere umană obligatorie, jurnal automat al activității, documentație tehnică, audituri. Amenzi până la 15 mil. € sau 3% din cifra de afaceri pentru neconformare.
- Chatboții trebuie să spună utilizatorului că vorbește cu un AI.
- Reguli de folosire sigură: verifici ce produce AI, scoți datele personale înainte de prompt, ceri surse, etichetezi conținutul generat, păstrezi omul în buclă pentru deciziile cu impact.
- Riscuri LLM: inventează lucruri, bias, context limitat, prompt injection, scurgeri de date, încredere oarbă în răspuns.
- Exemple de incidente prezentate: Samsung (cod scurs în ChatGPT, 2023), Claude Code care a șters o bază de date de producție (martie 2025), loguri DeepSeek expuse (ian. 2025), EchoLeak în M365 Copilot (iun. 2025), vulnerabilitate Cursor CVE-2025-54135, avocații din Mata v. Avianca (2023).

Ce înseamnă pentru noi (criteriile de etică și explicabilitate): agentul nostru ar trebui să aibă om în buclă pentru deciziile cu impact, jurnal pentru fiecare decizie, explicație, date pseudonimizate și o notă scurtă despre clasificarea după EU AI Act. Asta arată juriului că am înțeles ce le-au prezentat.
