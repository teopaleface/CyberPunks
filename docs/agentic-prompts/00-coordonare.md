# 00 Coordonare și integrare

Arhivat. Acest prompt din împărțirea inițială nu se mai execută separat. Folosește pachetul compact din README.md.

Acest prompt se rulează când Teo cere începerea implementării. În etapa pregătirii prompturilor rămâne un livrabil. Obiectivul este prima versiune din `docs/PLAN-AGENTIC.md`, implementată în paralel, cu analiza completă a cozii, operații confirmate și rapoarte pe canalele permise.

## Preflight și prima predare

Citește instrucțiunile comune și manifestul. Verifică ramura `Teo`, starea Git, ceilalți agenți și deținătorii fișierelor, sursa operațională completă și procesele deja active, fără a le modifica. Pregătește copia izolată completă fără secrete sau setări de trimitere. Verifică faptul că această copie poate reproduce planul. Păstrează snapshotul și versiunile sale coerente; nu copia baze active printr-o simplă copiere care poate pierde tranzacții.

Sursa proaspătă trebuie să provină din starea efectiv folosită pentru demo sau din datele live accesibile read-only. Dacă nu este accesibilă o sursă completă actuală, consemnează blocajul și continuă numai contractele și modulele care nu pretind acceptanță pe date reale. Nu redenumi un set vechi drept copie proaspătă.

Lansează 01. Verifică după predare schema comună, compatibilitatea vechiului turn conversațional și datele complete pentru probe. Publică în contextul fiecărui job versiunea contractului și calea izolată a datelor. Abia apoi pornesc implementările independente.

## Delegare

Folosește subagenți ai acestui fir, nu conversații top-level. Citește catalogul live prin `orchestrator_capabilities`. Păstrează furnizorul, modelul și opțiunile moștenite dacă Teo nu cere altceva. Când există opțiuni moștenite, delegă prin `delegate_task` și transmite-le în `target.options`, verificând răspunsul. Folosește un `clientRequestId` distinct și stabil per sarcină și rundă. Păstrează fiecare `taskId`.

Fiecare prompt efectiv este `COMMON.md` urmat de fișierul sarcinii și de datele necesare ale predării precedente. Limita curentă este trei subagenți simultan, pe lângă tine. Lansezi imediat următoarea sarcină pregătită când se eliberează un loc. 02 și 04 au prioritate, al treilea loc poate începe 07. Apoi urmezi dependențele și ordinea din README. Nu dublezi joburi active și nu pornești agenți care doar așteaptă un fișier încă nepredat.

În checkout comun, deținerea este strictă. Contractele înghețate permit implementare cu dependențe simulate, iar integrarea așteaptă implementările reale. Pentru checkout separat, folosește `isolation:worktree` numai după ce commitul de bază include planul și contractul. Transmite explicit materialul lipsă; editările necomise nu sunt copiate automat. Nu schimbi branchul checkoutului comun și nu muți alt fir.

## Fișierele pe care numai tu le conectezi

Tu deții modificările în fișierele existente `channels/conversation.py`, `channels/models.py`, `channels/codex.py`, `channels/router.py`, `channels/whatsapp.py`, `channels/whatsapp_worker.py`, `channels/whatsapp_transport.py`, `channels/whatsapp_store.py`, `channels/whatsapp_calls.py`, `channels/elevenlabs.py`, montarea API-ului și fișierele existente de operații. Copiii propun exact punctele de conectare, dar nu le editează.

Tu conectezi noile carduri și noul client în `web/components/workspace/workspace.tsx`, `main-conversation.tsx`, `voice.tsx` și clientul/proxy-urile existente. Tu deții orice schimbare necesară în dependențe și lockfiles. Alegi un renderer disponibil după verificare, cu o singură decizie de dependență, fără instalări concurente.

Nu aplica lista de mai sus ca autorizație de rescriere. Fă numai legăturile necesare și păstrează autentificarea, confirmarea, istoricul, fotografiile și corecțiile existente. Un conflict cu un agent din afara acestei execuții se rezolvă prin delimitare, nu prin suprascriere.

## Integrare continuă

Integrează mai întâi 02, 03, 04, 17, 18 și 05 și verifică o analiză completă. Montează 12, conectează 11 și verifică pregătirea și confirmarea unei operații reale în copia izolată. Adaugă 06–08, apoi 09–10. Codul conversației rămâne izolat de shell; accesul la funcțiile agentice trece prin aplicație și schema înghețată.

Operațiile existente de Confirm rămân singura cale de execuție cu impact. Sarcina urmărește comanda și recitește rezultatul. Un răspuns care spune „aplicat” fără efect real este defect blocant. Contractul vechi funcționează și fără date agentice.

Coordonează probele 13–14 pe o copie completă și un build separat de frontendul demo, după integrarea modulelor folosite, inclusiv 17 și 18. Înregistrează distinct ce este simulat, local integrat, verificat în browser sau pe telefon. Nu iniția apeluri, mesaje, configurări, modificări de cont ori deploy fără autorizarea existentă explicită pentru acel pas. Dacă etapa de implementare nu include aceste acțiuni, finalizează probele locale și numește exact proba externă rămasă.

## Revizie și încheiere

Fă commituri mici numai cu fișierele sau hunks-urile proprii verificate; păstrează lucrul necomis și indexul altora. Fixează un punct de revizie reproductibil. Lansează 15 și 16 simultan pe același punct. Pentru fiecare rundă nouă de revizie, apelează din nou `delegate_task`, cu brief-ul inițial, observațiile, remedierile și obiecțiile nerezolvate. Nu continua runda prin `t3_thread_send` pe firul copil.

Remediază defectele blocante, repetă doar probele afectate și reverifică integrarea necesară. Citește rezultatele sarcinilor și închide delegările după predare cu `task_cancel`, inclusiv pentru a elibera livrarea automată. Fără bucle dese de polling; consultă statusul când rezultatul este necesar și continuă munca independentă între notificări.

Actualizează central memoria proiectului și jurnalul cu ora București, fără secrete. Predă în română rezultatul efectiv, probele și limitele. Prima versiune nu se extinde tacit la aprobări în grup, numere noi, confirmări WhatsApp, simulări de capacitate sau telefonie obișnuită.
