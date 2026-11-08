# Agent conversațional pentru trei tipuri de cont

## Cererea lui Teo

Consemnat pe 7 noiembrie 2026, la 22:43, București. Teo a cerut un plan complet pentru agentul conversațional Daybreak, cu toate cele trei perspective discutate: tehnician, dispecer și client. Vrea testarea din trei tipuri de cont, nu doar o conversație demonstrativă într-un singur cont.

Teo a precizat că sunt permise Codex CLI și alte LLM-uri dacă sistemul folosește modelul ML propriu, rulat local. Vocea prin ElevenLabs este direcția explorată. Solicitarea din această etapă este realizarea planului; implementarea și activarea unor servicii externe nu au fost cerute în acest mesaj.

## Planul rezultat

Documentul complet: [Plan pentru agentul cu trei conturi](../docs/PLAN-AGENT-CONVERSATIONAL.md).

- Catalog de 68 de cazuri pe roluri și 12 situații comune, cu 16 cazuri principale P0 pentru prima versiune.
- Același caz și aceeași stare operațională pentru cele trei roluri, cu drepturi verificate pe server.
- Operatorul de relații cu clienții este propus ca vedere restrânsă a dispecerului, fără al patrulea tip de cont.
- Propunere tehnică: voce în browser, trei configurații conversaționale, acțiuni comune pentru text/voce/butoane și modele locale. Configurațiile și infrastructura sunt propuneri, nu funcții livrate.
- Confirmarea constatării nu înseamnă repararea problemei. Fără acces nu înseamnă defect absent și nu devine automat etichetă negativă pentru antrenare.
- Planul include etape, buget orientativ, 40 de probe de verificare și demo cu trei sesiuni independente.

## Situație înainte de implementare

Conturile existente nu au încă rolurile operaționale și legăturile autorizate cont-punct sau cont-echipă. Câmpul de profil team este editabil și nu trebuie folosit drept permisiune. Aprobările personale din KV sunt distincte de aprobările reale ale planificatorului.

API-ul existent poate înregistra constatări și aprobări, dar aceste operații nu sunt încă legate de cele trei roluri. Configurația Cloudflare folosește planul salvat, fără serviciul Python local. Integrarea ElevenLabs, accesul efectiv la cont și minutele disponibile nu au fost testate.

## Limitele etapei de plan

Au fost redactate și verificate documentele. Nu au fost create conturi, schimbate secrete, pornite apeluri, publicată aplicația sau implementate noile funcții. Datele și identitățile de test din plan sunt propuse și etichetate ca sintetice. Interfața rămâne în engleză, conform deciziei deja luate de Teo.

## Implementare și probe, 7-8 noiembrie

Teo a aprobat ulterior implementarea în paralel, Codex pe abonamentul existent, trei conturi, vocea din site și WhatsApp cu text și note vocale. Implementarea locală este separată de site-ul public: workspace pe 3870, API privat pe 8720, intrare exclusiv Meta pe 8721. Datele sunt o copie completă izolată, cu 689 de lucrări și predicții reale ale modelelor locale. Conturile, legăturile și sesizările demonstrative sunt sintetice. Scenariul istoric este 8 iulie 2025.

Cele trei conturi au drepturi verificate pe server. Probele reale au parcurs sesizare confirmată de client, aprobare prin planificator, constatare a tehnicianului și stare comună, fără declararea reparației. Conversația Codex a fost verificată pe toate rolurile. Există propuneri confirmate explicit, versiuni, deduplicare și recuperarea autorizată a comenzilor. Propunerile pornite în WhatsApp se pot găsi în Draft requests sau deschide printr-un link care păstrează identificatorul prin autentificare. Clientul vede rezultatul constatării, fără identificatori interni ai verdictului.

Cheia ElevenLabs existentă a fost găsită în configurația privată existentă. Teo a autorizat adăugarea unui singur IP; lista și accesul API au fost verificate separat după salvare. Trei agenți privați au fost creați și verificați. Două probe au parcurs ASR, agentul vocal, unealta din client, Codex și răspunsul audio real. Proba finală a păstrat textul API identic; a durat 13,15 secunde pentru conversație și 15,44 secunde până la primul audio după întrebare. Pronunția exactă, microfonul și difuzorul fizic rămân neverificate.

Teo a creat numărul de test Meta +1 555 154 5755 și a confirmat parola Facebook în Helium pentru accesul privat la App Secret. Callbackul HTTPS și asocierea aplicației Meta au fost salvate și recitite. Două răspunsuri reale Codex au fost livrate și citite în WhatsApp, către singurul expeditor verificat, asociat tehnicianului sintetic. O întrebare intermediară despre motivul opririi a fost refuzată de verificarea datelor; retrimiterea a trecut. Codul are acum un răspuns sigur după eșecurile conversaționale, fără afirmații neverificate. Această ramură de eroare este testată simulat.

Notele vocale sunt implementate și testate cu furnizori simulați, inclusiv răspuns OGG/Opus și păstrarea textului dacă audio eșuează. Teo a precizat că nu poate înregistra acum; nu s-a verificat o notă vocală reală prin Meta. Nu îi cerem repetat înregistrarea. Audio este activat numai pentru expeditorul verificat care a cerut această funcție.

Tunelul și tokenul Meta sunt temporare. Procesele locale trebuie să rămână pornite; site-ul nu a fost publicat. P1/P2 din catalog nu sunt toate implementate. Pornire, verificări și limite: [RUNBOOK](../docs/operations/RUNBOOK.md). Secretele și identificatorii personali ai expeditorului rămân numai în fișiere private ignorate de Git, fără valori în memorie.

## Conturi nominale, 8 noiembrie

Teo a cerut explicit aceleași trei conturi local și pe live: dispecer@daybreak.ro, tehnician@daybreak.ro și client@daybreak.ro, cu parola comună stabilită de el, păstrată numai privat. Conturile au fost configurate cu rolurile corespunzătoare, păstrând identificatorii și asocierea WhatsApp. Formularul a fost corectat pentru autentificarea cu parola existentă, păstrând minimul obișnuit la creare/resetare. Toate cele șase autentificări din formular, trei roluri în două medii, au trecut. Publicare din copie izolată a sursei comise, versiunea 2c071473-84fb-4923-a5e7-2135d343fad1. Serviciul operațional rămâne local.

## Corecție cerută: integrare în consola veche

Teo a respins explicit pagina separată de workspace. Agentul trebuie să fie funcțional în interfața veche, cu navigarea, componentele și paleta PPC ale restului site-ului. Implementarea locală folosește /app și AppShell pentru toate rolurile; dispecerul păstrează planul vechi, iar datele celorlalte roluri sunt filtrate. Agentul este un panou contextual comun, cu text, voce și confirmări. /workspace rămâne numai redirecționare compatibilă, fără produs separat. Butoanele existente de aprobare/revizuire deschid formularele agentului. Verificate toate rolurile pe desktop/mobil, conversație Codex reală și confirmarea unei sesizări. Nu reintroduceți o pagină cu branding separat pentru această funcție.

## Corecție cerută: dashboard principal

Teo a respins și lista de fișe cu agent într-un sertar lateral. Cerința curentă este un dashboard principal la /app: rezumat scurt, un caz sau o vizită relevantă, liste compacte și agent vizibil în pagină. Fără buton plutitor sau fereastră peste conținut. Clientul, tehnicianul și dispecerul păstrează datele și acțiunile permise rolului; navigarea, tema și paleta PPC rămân comune consolei existente. Formularele și propunerile se deschid în zona agentului, iar numai Confirm execută o acțiune. Această cerință înlocuiește alegerea anterioară a panoului contextual.

## Voce pentru prezentare și verificare API, 8 noiembrie

La cererea lui Teo, cele trei configurații existente ElevenLabs au fost actualizate prin API și recitite: filtrarea vocilor din fundal activă, turn_v3 în modul eager, timeout de tăcere 5 secunde, Eleven v4 Turbo cu expressive mode și salut în română. Agentul spune o confirmare scurtă înainte să ceară datele; întreruperile sunt blocate pe durata cererii și a răspunsului aferent. Autentificarea, rolurile, unealta unică și politica de confidențialitate au fost păstrate. Limita este 600 secunde și 30 sesiuni pe zi pentru fiecare rol, cu o singură sesiune simultană. Nu au fost pornite conversații ElevenLabs noi în această etapă.

WhatsApp direct Meta folosește acum Scribe v2 și Eleven v4 pentru note vocale. O probă audio sintetică prin API a trecut sinteza și retranscrierea. Codex păstrează abonamentul existent, cu Fast și răspuns scurt; întrebările despre următoarea oprire primesc detaliile opririi aprobate, păstrând traseul și agregatele întregii surse autorizate. Corectată și normalizarea prefixului scoped_context din dovezi, fără slăbirea verificării valorilor sau a predicțiilor indisponibile. Proba comparabilă: 13,60 secunde înainte, 11,82 după; API-ul local repornit a răspuns corect în 12,00 secunde. Acestea sunt probe individuale, nu o garanție de latență.

Interfața vocală locală are control de microfon, stare de pregătire și transmite coordonatorului doar răspunsul verificat. Typecheck, lint și probele locale relevante trec; microfonul fizic, boxele, zgomotul sălii și conversația live completă după aceste modificări rămân neverificate. Fără deploy.

Blocaj actual WhatsApp: tokenul temporar Meta a expirat pe 8 noiembrie la 01:00 București. Debug Token confirmă is_valid=false, accesul la număr și schimbul de token răspund cu 190/463. Subscrierea rămâne activă și callbackul public răspunde corect la verificare. Nu au fost trimise mesaje de test. Comanda refresh-token din daybreak_whatsapp_setup.py cere tokenul ascuns, verifică aplicația, dreptul de mesagerie și numărul înainte de salvarea privată; serviciul recitește tokenul fără restart. Teo va testa o singură notă vocală după înlocuire.

## Clarificarea finală: agentul este pagina principală

Teo a precizat că dashboardul principal trebuie să conțină numai agentul, cu o conversație mare și simplă, asemănătoare ChatGPT. Istoricul poate rămâne discret în stânga, iar textul și vocea sunt în același loc. Cazurile și confirmările apar la nevoie în conversație. Nu se păstrează rezumatul cu cifre și tabele lângă un card de chat. A cerut o generare vizuală înaintea noii implementări; macheta este o propunere, nu interfață deja modificată. Această clarificare înlocuiește structura cu rezumat, card principal și asistent inline.

## Acces Meta refăcut, 8 noiembrie

Blocajul tokenului expirat este rezolvat. La cererea lui Teo, tokenul a fost regenerat în sesiunea Helium existentă, pentru aceeași aplicație și același număr de test. Apoi schimbul API către token cu durată lungă a reușit. Debug Token confirmă is_valid=true, tip USER, drepturile whatsapp_business_management și whatsapp_business_messaging și expirarea pe 6 ianuarie 2027, la 23:15:30 București. Tokenul propriu-zis este numai în fișierul privat ignorat, cu permisiuni 0600.

Verificare independentă după salvare: tokenul recitit este valid, API-ul confirmă numărul existent, subscrierea este activă și neschimbată, iar callbackul public trece challenge-ul. Nu s-au trimis mesaje și nu s-a pornit niciun apel. Serviciul recitește tokenul fără restart; runtime-ul aplicației a rămas stabil pentru QA-ul paralel. Teo poate trimite acum singura notă vocală de test. O notă vocală nu verifică zgomotul și detectarea finalului de vorbire din conversația live.

Pentru refaceri viitoare: în interfața Meta actuală, Use cases → Connect on WhatsApp → Basic setup → Step 1. Try it out → Generate token. După obținerea unui token valid, schimbul API poate prelungi valabilitatea; tokenul deja expirat a fost refuzat anterior cu 190/463. Jev trebuie să urmărească fereastra OAuth proprie și să revină în tabul aplicației după închiderea ei; snapshot-ul popupului cere activarea acelui target. Nu modificați profilul Helium sau celelalte taburi.

## Apeluri WhatsApp configurate, 8 noiembrie

La cererea explicită a lui Teo, apelurile primite sunt activate pe numărul Meta de test existent. Meta a confirmat prin API atât calling=ENABLED și vizibilitatea butonului DEFAULT, cât și ruta SIP criptată spre ElevenLabs. Importul WhatsApp nativ ElevenLabs este exclus pentru WABA de dezvoltator; folosim SIP și păstrăm separat integrarea existentă de mesaje/note vocale.

Există un agent privat suplimentar pentru apeluri și un serviciu restrâns pe 8722, cu tunel HTTPS propriu. Apelurile și accesul la date sunt limitate la apelantul verificat existent, în rolul său de tehnician. Identitatea este injectată din variabilele de sistem ElevenLabs, verificată pe server și recitită din asocierile existente la fiecare tură. Nicio confirmare de operație nu se execută în apel. SIP și audio sunt criptate, parola SIP și acreditările HTTP sunt numai în configurarea privată ignorată. Înregistrarea audio și jurnalele SIP sunt dezactivate; nu există rută de apeluri inițiate de agent.

Setările sunt recitite independent la Meta și ElevenLabs; TLS SIP este verificat. Serviciul public a refuzat accesul fără acreditare cu 401 și a răspuns prin Codex real în 11,23 secunde, folosind datele autorizate. 184 teste Python trec. Nu a fost pornit automat niciun apel și nu s-au trimis mesaje. Teo a primit solicitarea pentru un singur apel de probă; conversația audio completă și sala zgomotoasă rămân neverificate până la acea probă. Procesele noi de pe 8722 și tunelul trebuie să rămână pornite, iar runtime-ul consolei și al mesajelor a rămas neschimbat. Ghid în docs/operations/RUNBOOK.md, secțiunea Apeluri WhatsApp primite.

### Separarea supravegherii runtime

În timpul QA-ului UI ulterior, oprirea frontendului a făcut ca procesul comun pornit de daybreak_runtime.start să oprească și API-ul 8720. Procesele aveau grupuri diferite, dar aceeași supraveghere, iar aceasta apela stop pentru toate componentele când una ieșea. API-ul a fost repornit separat, cu același mediu privat; frontendul a pornit separat cu propriul director Next. Verificările ulterioare au confirmat un singur API pe 8720 și serviciul de apeluri pe 8722, ambele cu HTTP 200. Nu s-au modificat fișiere de configurare sau date în această recuperare. Pentru un restart numai de frontend, verificați întregul lanț de părinți și supravegherea, nu doar grupul de procese sau PID-ul next-server.

## Agent principal și recuperarea întregii console

Teo a cerut explicit recuperarea designului celor 14 vederi originale și folosirea lui unde este potrivit fiecărui cont. Cerințele se completează: /app rămâne numai conversația principală, iar operațiunile sunt pagini distincte în același meniu. Planul dispecerului este la /planificare; harta, coada, substațiile, lucrările A/B/C, istoricul, modelele, ordinele și prezentarea sunt păstrate. Clientul are cazuri, conexiuni și activitate proprii. Tehnicianul are traseul cu hartă, lucrările și cazurile echipei, dovezi și constatări. Accesul este verificat pe server și în contextul API; nu se relaxează protecția consolei globale.

Implementat și verificat local pe datele complete: 223 teste web, typecheck, lint și build izolat. Toate vederile dispecerului și paginile pe roluri au fost deschise în Helium; conversația reală, istoricul, mobilul și transferul unei revizuiri fără salvare automată au trecut. Corectată și aprobarea falsă bazată pe cookie din hartă. Datele din machetele istorice nu sunt sursă pentru valorile afișate. Fără deploy sau retestarea hardware-ului audio. Inventar în web/design/CONSOLE-RECOVERY.md.

## Prima probă WhatsApp pe telefon confirmată

Teo a confirmat explicit că agentul răspunde la apel și îl aude. ElevenLabs confirmă un apel SIP încheiat cu succes, 23 de secunde și cinci mesaje în conversație. Aceasta verifică legătura vocală reală de pe telefon. Răspunsurile observate au fost salutul, confirmarea de verificare și întrebarea de prezență; nu a fost confirmat un răspuns operațional pe datele Daybreak în acest apel. Proba în zgomotul sălii rămâne separată și neverificată. Înregistrarea audio nu a fost activată.
