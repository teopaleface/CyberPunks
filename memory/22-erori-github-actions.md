# Verificări CI Windows și Linux

Rularea https://github.com/teopaleface/CyberPunks/actions/runs/42459942911 pe main:

- Windows: 111 teste trecute, 6 omise, unul eșuat la verificarea POSIX 0600. Verificarea biților POSIX se aplică doar pe POSIX. Această schimbare nu constituie o verificare ACL Windows.
- Ubuntu: build-ul și testele au trecut, dar cache prune uv a expirat după 300 s. Smoke check-ul omora forțat launcherul, deși serviciile sunt pornite în sesiuni separate. Astfel, handlerul launcherului nu mai putea închide serviciul uv. Corecția permite oprirea normală, apoi forțează după 20 s dacă launcherul nu răspunde.
- Testul de regresie pornește un launcher cu serviciu în sesiune separată și verifică că oprirea execută handlerul și închide serviciul.

Verificare locală: 7 teste au trecut (`test_local_setup`, `test_local_start_cleanup`, `test_local_platform`), inclusiv regresia pentru serviciul separat; Ruff și git diff --check au trecut. Validarea Windows și Ubuntu rămâne în GitHub Actions.
