# Workshopul R Systems "It's 3 AM. Prod is on fire."

Din prezentarea `RSystems_Its-3AM-Prod-Is-on-Fire.pptx` (33 de slideuri, marcată "Public"), SmartHack 2026, R Systems Track. Autor: Matei Bejan, AI Subject Matter Expert și EU AI Team Lead la R Systems. Subiect: RAG practic, de la LLM-uri la grafuri de cunoștințe. Textul complet, cu notițele vorbitorului, e în `materiale/` (local).

R Systems e celălalt partener MAIN. Tema lor pare să fie o unealtă de securitate care scanează și explică rezultatele (din notițe: "findings, severities and scores from code; explanations from the model, grounded in the scan and checked" și "the brief asks for exactly that (hostile input)"). Noi suntem pe tema PPC, dar lecțiile se aplică.

## Lecțiile care ne ajută

- **Codul decide, modelul formulează.** Dacă un răspuns greșit ar fi un bug, decizia stă în cod (praguri, reguli, calcule). Dacă un răspuns stângaci ar fi doar o problemă de stil, îl lasă pe LLM. Se potrivește exact cu cerința PPC: LLM-ul doar orchestrează sau face interfața, decizia vine din modelul nostru și din reguli.
- **Halucinațiile nu dispar din prompt.** Le prinde sistemul din jurul modelului: date reale înainte (grounding), format fix la ieșire (JSON cu valori permise), verificare în cod după (nume, cifre, citări). Dacă verificarea pică, regenerează sau folosește un text-șablon.
- **Exemplul lor:** asistentul telecom a inventat un mesaj, "Security-Setup". L-a prins o verificare în cod care compara fiecare nume din răspuns cu documentele sursă.
- **Contextul e un buget, nu o memorie.** Selectezi ce pui în prompt, nu torni tot.
- **Nu orice injecție e prompt injection.** Textul venit de la utilizator sau din fișiere scanate trebuie escapat înainte să ajungă în SQL, shell, HTML sau prompt. În proiectul lor, un ghilimele plus `*:*` au întors toate tichetele din graf.
- **Citatul de final (IBM, 1979):** "A computer can never be held accountable, therefore a computer must never make a management decision." Modelul propune, codul verifică, omul decide. Bun pentru partea de etică din prezentarea noastră.

## Cifre din cazurile lor (dacă ne trebuie ca exemplu)

- Support desk: 28.587 de tichete (16.338 în engleză, 12.249 în germană). Căutarea unui tichet greu a scăzut de la 10-15 minute (GPT generic) la 3-5 minute (unelte specializate) și la 10-20 de secunde (graf de cunoștințe plus unelte).
- Asistent telecom: peste 600 de specificații 3GPP pe versiune. Qwen3-14B local, cuantizat pe 4 biți, pe un GPU de laptop de 16 GB, 5-10 minute pe răspuns. Căutare hibridă FAISS plus BM25, graf de referințe în Neo4j, reranker.
