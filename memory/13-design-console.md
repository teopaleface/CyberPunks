# Audit și aliniere vizuală a consolei

7 noiembrie 2026, 22:04, București.

Teo a cerut concentrarea pe design și un audit al landingului și consolei. Landingul îi place. Consola i se pare greu de citit și de înțeles, cu alte fonturi și culori. A autorizat mai mulți subagenți pentru rezolvare.

Reperul este landingul integrat din `web/site`, servit la `/`, nu aplicația veche separată din `landing/`. Consola este la `/app`.

Modificări locale: negru, alb și galben pentru acțiuni; Geist pentru text și carduri, Unbounded pentru titluri; trei cifre principale, planul și cazul de decis separate, restul la cerere. Navigare grupată, „De verificat” în loc de „Nu sunt sigur”, meniu complet pe telefon. Pe telefon, următorul caz de decis apare înaintea cifrelor.

Auditul și limitele verificării sunt în `web/design/AUDIT-UI-UX.md`. Nu s-a făcut deploy. Conflictul anterior din `memory/journal.md` a fost integrat de alt fir în timpul lucrului, în commitul a1862c1. Acest task nu a modificat conturile/API.
