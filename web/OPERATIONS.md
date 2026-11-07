# Workspace operațional local

Interfața `/workspace` folosește rolul și apartenența salvată în cont. `/app` trimite spre această pagină. Dispecerul autorizat păstrează consola detaliată la `/app?console=1`.

## Pornire și conturi

Procesul root deține pornirea pe 8720/3870 și mediul privat. Din rădăcina repo-ului, după pornire: `python3 scripts/daybreak_runtime.py accounts`.

Provisionarea cere modul development, `DAYBREAK_ENABLE_DEMO_PROVISIONING=1`, origine și adresă locală, plus tokenul intern. Folosește cele trei parole și emailuri furnizate separat în mediul privat. Interoghează asocierea deterministă a backendului. Creează numai conturile sintetice noi; la repetare verifică parola, marcajul sintetic și apartenența fiecărui cont, fără rescriere. Un cont existent diferit produce conflict.

`DAYBREAK_COOKIE_NAME` separă cookie-ul de aplicația veche. `DAYBREAK_NEXT_DIST` separă compilarea. Directorul `.next-operations-check` folosit pentru verificarea buildului este ignorat. Nu se stochează parole sau tokenuri în acest document.

## Acces și operații

Gateway-ul acceptă numai rutele necesare pentru context, propuneri, confirmări, comenzi, chat și sesiuni vocale. Nu transmite cookie-ul, actorul sau autorizarea trimisă de browser. Construiește actorul din contul verificat și folosește tokenul intern pe loopback. Originea este verificată inclusiv la citirile operaționale. În Next dev, autoritatea cererii vine din Host, deoarece request.url poate fi normalizat la localhost; X-Forwarded-Host nu acordă acces.

Înregistrarea publică produce numai client fără punct autorizat. Câmpul team din profil nu acordă rol sau echipă. Citirile consolei, exportul jurnalului și ordinele sunt restrânse la dispecerul organizației sintetice cu view_console. Celelalte roluri folosesc proiecțiile filtrate ale backendului. Căile vechi de aprobare personală și acțiunile vechi refuză scrierea și indică workspace-ul. Nu există succes prin cookie.

Interfața are aceeași conversație pentru toate rolurile, carduri în domeniul contului, formulare și Confirm/Edit/Cancel, comenzi recuperabile și recitire la două secunde. Scenariul P0 este demo-vara, istoric, etichetat sintetic. Tehnicianul vede traseul propriu și distincția propus/aprobat; explicațiile folosesc predicția și factorii returnați de server.

SDK-ul instalat este @elevenlabs/react 1.21.1. Implementarea folosește ConversationProvider, cârligele de control/stare și unealta daybreak_turn, după [documentația oficială React](https://elevenlabs.io/docs/eleven-agents/libraries/react) și [contractul uneltelor client](https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools). Unealta trimite la același chat și întoarce răspunsul efectiv. Serverul canalelor verifică agentul privat și faptul că așteaptă unealta. Confirmarea scrierii rămâne buton în interfață. Consimțământul precede microfonul, End și logout opresc sesiunea, durata are limită, iar textul rămâne disponibil.

## Verificări efectuate în acest task

- `bun test`: 115 teste trecute, zero eșecuri. Testele runtime sunt oprite implicit și au fost rulate separat, cu mediul privat încărcat.
- `bun test lib/operations/gateway.test.ts`: 34 teste pentru acces, origini, actor, loopback, lipsa tokenului, pregătire fără confirmare, retry și erori sigure.
- `DAYBREAK_TEST_ORIGIN=http://127.0.0.1:3870 bun test lib/operations/runtime.test.ts`: șase teste trecute pe serverele locale, cu cele trei parole citite din mediul privat de pornire. Acoperă sesiuni independente, domeniul datelor, promovare refuzată, exporturi și aprobări vechi, origine și revocarea unui singur cookie.
- `bun x tsc --noEmit` și `bun run lint`: trecute. Buildul a trecut izolat cu `DAYBREAK_NEXT_DIST=.next-operations-check bun x next build`.
- Verificarea vizuală a folosit Helium prin CDP, după două timeouturi ale snapshotului T3. Script local: `/tmp/daybreak-workspace-readonly-qa.mjs`. A creat trei contexte de browser independente, apoi le-a închis. A autentificat separat conturile sintetice și a inspectat fiecare workspace la 1440×1100 și 390×844. Zero alerte de eroare și zero depășiri orizontale. Client: zero lucrări interne. Tehnician: două lucrări în echipa lui. Dispecer: toate cele 689 lucrări ale planului local.
- Raportul este `/tmp/daybreak-workspace-readonly-qa.json`, capturile sunt `/tmp/daybreak-workspace-{customer,technician,dispatcher}-{desktop,mobile}.png`. Conțin numai identitatea sintetică publică și datele autorizate, fără parole sau cookie-uri. Dovezile preced restartul root pentru noua asociere deterministă; nu probează starea acelui nou set.

Nu au fost executate în acest task conversația vocală reală cu microfon/difuzor sau scenariul operațional complet cu scrieri succesive ale tuturor rolurilor. Root face integrarea acestor probe. Capturile nu probează vocea. Nu s-au publicat schimbări și nu s-au trimis apeluri, emailuri ori mesaje WhatsApp.

## Fișierele acestui task

Fișiere noi, deținute integral:

- `web/OPERATIONS.md`
- `web/lib/operations/client.ts`
- `web/lib/operations/gateway.ts`
- `web/lib/operations/gateway.test.ts`
- `web/lib/operations/policy.ts`
- `web/lib/operations/runtime.test.ts`
- `web/lib/operations/types.ts`
- `web/lib/server/operations.ts`
- `web/app/api/operations/[...path]/route.ts`
- `web/app/api/conversation/[...path]/route.ts`
- `web/app/api/dev/provision-demo/route.ts`
- `web/app/workspace/page.tsx`
- `web/components/workspace/workspace.tsx`
- `web/components/workspace/workspace.css`
- `web/components/workspace/proposal-form.tsx`
- `web/components/workspace/voice.tsx`
- `web/scripts/provision-demo.ts`

Modificări proprii în fișiere existente:

- `web/.gitignore`: directoarele locale de compilare.
- `web/eslint.config.mjs`: ignorarea directoarelor locale generate.
- `web/next.config.ts`: distDir configurabil.
- `web/tsconfig.json`: includerea tipurilor generate de .next-operations; fără tipurile .next-operations-check.
- `web/package.json`, `web/bun.lock`: dependența ElevenLabs.
- `web/lib/server/accounts.ts`: apartenență, cookie configurabil, client fără legături la înregistrare, provisionare aditivă/repetabilă.
- `web/lib/data/api.ts`: autorizarea internă pentru API-ul privat.
- `web/lib/data/actions.ts`: refuzul scrierilor vechi și protecția citirii detaliului.
- `web/app/api/cont/route.ts`, `web/app/api/cont/intrare/route.ts`, `web/app/api/cont/inregistrare/route.ts`, `web/app/api/cont/iesire/route.ts`, `web/app/api/cont/parola/route.ts`: origine, profil limitat, apartenență în răspunsurile sigure.
- `web/app/api/aprobari/route.ts`: retragerea aprobărilor personale vechi, cu acces verificat.
- `web/app/jurnal/descarca/route.ts`, `web/app/ordine/[crew]/route.ts`: protecție la citire; ordinul folosește și tokenul intern.
- `web/app/app/page.tsx`: intrare în workspace și protecția consolei.
- `web/app/alerte/page.tsx`, `web/app/coada/page.tsx`, `web/app/debug/page.tsx`, `web/app/demo/page.tsx`, `web/app/harta/page.tsx`, `web/app/jurnal/page.tsx`, `web/app/lucrari/page.tsx`, `web/app/lucrari/[id]/page.tsx`, `web/app/modele/page.tsx`, `web/app/posturi/page.tsx`, `web/app/posturi/[id]/page.tsx`, `web/app/rulare/page.tsx`: numai importul requireConsole și apelul său înaintea citirilor private.
- `web/site/src/pages/sign-in.tsx`: numai textele despre workspace și legătura publică spre /agent. Modificările de temă din acest fișier aparțin celuilalt task.

Nu aparțin acestui task modificările de temă, contrast, metrici/confidence, datele modelelor, layoutul global, scripturile de generare landing sau alte fișiere Python. Unele pagini protejate au și modificări paralele; lista de mai sus revendică numai verificarea accesului. Nu am făcut stage sau commit, la cererea root.

## Corecția recuperării comenzilor

Workspace-ul afișează `context.pending_commands` după recitire sau redeschidere. Lista nu execută GET pe fiecare comandă și nu anulează nimic automat. Acțiunea oferită depinde de `can_recover`, `recovery_action` și permisiunile curente din contextul verificat. `retrieve` oferă recuperarea explicită prin GET. `cancel` cere motiv, revizuire și butonul separat Confirm cancellation; abia acel buton trimite POST-ul cu `decision: cancel` și motiv. `manual_review` și `requires_dispatcher` explică blocajul și nu oferă un buton care să execute operații. Backendul verifică din nou starea efectului și apartenența înaintea acțiunii.

Gateway-ul permite exclusiv `POST /api/operations/commands/{id}/recover`, cu dispecer verificat și `recover_commands`. Acceptă numai `decision: cancel` și un motiv de 3-2000 de caractere; nu există endpoint generic pentru schimbarea drepturilor. Pollingul contextului rămâne la două secunde, dar recuperarea comenzilor este explicită.

Comanda administrativă este aceeași, rulată de root: `python3 scripts/daybreak_runtime.py accounts`. Ruta locală existentă păstrează toate verificările de development, flag, loopback, origine și bearer intern. Pentru conturi existente verifică toate cele trei emailuri, marcajele sintetice, parolele și apartenențele așteptate înaintea oricărei scrieri. Singura diferență acceptată este lipsa `recover_commands` din vechiul dispecer sintetic `daybreak-demo`, fără echipă sau puncte proprii și cu setul anterior exact de permisiuni. Numai acea permisiune se adaugă. ID-ul, emailul, hash-ul și salt-ul parolei, data creării, profilul și celelalte două conturi rămân neschimbate. Rezultatul include `membership_upgrade.added_permissions` numai la aplicare. Repetarea nu scrie din nou.

Auditul este stocat atomic în aceeași înregistrare KV cu permisiunea: `capability_grants` include permisiunea, ora, sursa `local_demo_provisioning` și verificarea credențialelor, fără parole. Conturile noi de dispecer sintetic primesc permisiunea în setul fix de la server. Conturile generale sau de producție nu sunt eligibile pentru upgrade. Profilul public nu poate edita aceste câmpuri. Nu am executat upgrade-ul pe conturile runtime; root îl aplică și verifică fluxul complet.

Fișierele acestei corecții, fără staging sau commit:

- Noi: `web/components/workspace/pending-commands.tsx`, `web/lib/operations/recovery.ts`, `web/lib/operations/recovery.test.tsx`, `web/lib/operations/demo-permissions.ts`, `web/lib/operations/demo-provisioning.test.ts`, `web/lib/operations/demo-admin-gate.test.ts`.
- Modificate: `web/components/workspace/workspace.tsx`, `web/lib/operations/types.ts`, `web/lib/operations/gateway.ts`, `web/lib/operations/gateway.test.ts`, `web/lib/server/accounts.ts`, `web/app/api/dev/provision-demo/route.ts`, `web/OPERATIONS.md`.
- Modificările paralele de culoare din `web/app/coada/page.tsx` nu aparțin acestei corecții și nu au fost atinse.

Testele noi verifică redescoperirea comenzilor la randare, lipsa efectelor la randare, refuzurile pe stările manuale sau drepturi insuficiente, ruta și corpul exact al anulării, verificările de acces ale administrării locale și acordarea controlată în stocare cu PBKDF2 real. Proba din stocare verifică păstrarea conturilor și identificatorilor, auditul, repetarea fără scriere și refuzul conturilor nesintetice, rolurilor/organizațiilor/apartenențelor diferite sau parolelor greșite. Nu înlocuiește proba root pe conturile și comenzile runtime.

Verificarea acestei corecții: `bun test` a trecut 142 de teste, cu șapte probe runtime oprite implicit și zero eșecuri. `bun x tsc --noEmit`, `bun run lint`, `DAYBREAK_NEXT_DIST=.next-operations-web-review bun x next build` și `git diff --check` au trecut. Directorul de build rămâne ignorat; includerile temporare ale tipurilor sale au fost eliminate din tsconfig. Testele au folosit numai stocări de test în memorie și parole sintetice generate pentru fiecare probă, fără acces la conturile runtime.

## Propuneri pornite din WhatsApp: acces din workspace

Calea `/workspace?proposal=<UUID>` păstrează identificatorul valid prin redirecționarea la `/intra?proposal=<UUID>` și prin schimbarea modului de autentificare. După login se încarcă pagina workspace prin navigare locală completă. Nu acceptă un URL de revenire liber; `next`, `returnTo`, scheme externe, ID-uri ambigue sau căi injectate nu stabilesc destinația.

Gateway-ul permite noul `GET /api/operations/proposals/{UUID}` numai pentru un ID UUID strict. Backendul verifică proprietarul și valabilitatea. Clientul initializează cardul existent cu exact obiectul întors de GET, fără regenerare sau confirmare automată. Confirm/Edit/Cancel folosesc comportamentul explicit existent. Erorile 403/404/409 și indisponibilitatea au texte sigure, fără obiecte sau semnături private.

Contextul poate include `pending_proposals`, cel mult zece ciorne proprii, valide, curente și neconfirmate. Interfața acceptă sumarul public cu `proposal_id`, `action`, `summary`, `expires_at` și metadate opționale. Secțiunea Draft requests nu face alte citiri sau scrieri la randare/polling. Numai Open for review citește propunerea completă prin GET-ul verificat și deschide cardul existent. Astfel, tehnicianul poate deschide workspace-ul pe laptop după conversația WhatsApp chiar fără un link public.

`PUBLIC_APP_ORIGIN` nu a fost configurat aici și nu s-a publicat site-ul. O cale locală nu este prezentată drept link accesibil de pe telefon. Generarea unui link WhatsApp public rămâne condiționată de configurarea și verificarea ulterioară a originii publice de către root. Nu au fost modificate conturi, credențiale, runtime sau configurări.

Fișierele acestei completări P1:

- Noi: `web/lib/operations/proposal-link.ts`, `web/lib/operations/linked-proposal.ts`, `web/lib/operations/proposal-link.test.ts`, `web/components/workspace/draft-requests.tsx`, `web/lib/operations/draft-requests.test.tsx`.
- Modificate: `web/app/workspace/page.tsx`, `web/components/workspace/workspace.tsx`, `web/site/src/pages/sign-in.tsx`, `web/lib/operations/gateway.ts`, `web/lib/operations/gateway.test.ts`, `web/lib/operations/types.ts`, `web/OPERATIONS.md`.
- Funcția findingText și folosirile ei adăugate de root sunt păstrate. Nu au fost atinse culorile din coada.

Verificări: `bun test` a trecut 164 de probe, cu șapte probe runtime oprite implicit și zero eșecuri. Typecheck și lint pentru web au trecut; buildul Next izolat în `.next-operations-link-review` a trecut. Site-ul de autentificare a trecut `bun run build`; lintul lui nu are erori, dar raportează avertismente existente despre Fast Refresh și efecte React. `bun scripts/build-landing.ts` a reconstruit bundle-ul local de autentificare, fără modificări ale datelor urmărite de git. Testele acoperă păstrarea ID-ului prin login, refuzul redirecționărilor externe, identitatea exactă a obiectului citit, GET fără confirmare, refuzurile sigure și lista inertă de ciorne. Fluxul WhatsApp real până la butonul Confirm rămâne de verificat de root cu backendul integrat.
