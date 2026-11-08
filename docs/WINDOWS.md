# Pornire locală pe Windows

Folosește PowerShell, Git, uv și Bun 1.3.11. Nu sunt necesare `make`, Bash sau activarea manuală a mediului Python. `uv sync` instalează Python 3.12 și dependențele proiectului. Instalează instrumentele din sursele lor oficiale înainte de pașii de mai jos.

## Consola și cele trei conturi, fără servicii externe

Din rădăcina clonei:

```powershell
uv sync --locked
bun install --cwd web --frozen-lockfile
uv run python scripts/daybreak_runtime.py prepare
uv run python scripts/daybreak_runtime.py start
```

Deschide http://127.0.0.1:3870. În alt PowerShell, din aceeași clonă, creează conturile sintetice locale:

```powershell
uv run python scripts/daybreak_runtime.py accounts
uv run python scripts/daybreak_runtime.py check
```

Datele conturilor sunt numai în `outputs/runtime/daybreak.env`, fișier ignorat de Git. Citește-le local, fără să le trimiți în chat sau să le comiți. Nu sunt conturile și parolele lui Teo de pe live. Autentificarea și operațiile locale folosesc porturile 3870 și 8720. Ctrl-C în primul terminal oprește procesele pornite de această comandă; porturile ocupate sunt refuzate, fără oprirea altor servere.

La o clonă nouă se copiază instantaneul complet din `outputs/demo`, împreună cu intrările complete din `data/local-runtime`. Planul operațional se recalculează local din acele predicții, fără reantrenare sau descărcări. Datele tehnice își păstrează proveniența publică/sintetică și data istorică. Nu se copiază chei, setări WhatsApp, automatizări sau conturi live. Dacă există deja toate ieșirile modelelor local, se copiază acelea. `prepare` păstrează rularea existentă; `prepare --new-run` creează alta fără ștergerea celei vechi.

Nu este necesară reantrenarea modelelor pentru navigare și operații pe planul salvat. Recalcularea cu modelele locale este separată:

```powershell
uv run python scripts/daybreak_runtime.py infer --scenario demo-vara
```

## Conversație, voce și WhatsApp

Conversația text cere instalarea Codex CLI pe calculatorul colegului și autentificarea lui proprie cu ChatGPT. Nu copiați `auth.json` de la Teo. Pe Windows este tratat și executabilul instalat prin npm, fără lansarea unei comenzi arbitrare în shell. Disponibilitatea modelului și a abonamentului se verifică separat; testele automate folosesc răspunsuri simulate, fără consumarea unui cont real.

Vocea, apelurile și WhatsApp cer propriile acreditări și configurări externe. Nu pornesc automat cu aplicația locală. Verificările actuale ale fișierelor private pentru aceste integrări sunt bazate pe permisiuni Unix. Pentru întregul flux cu aceste canale, folosiți WSL2 cu Ubuntu, clonați proiectul în directorul Linux, instalați acolo uv, Bun și Codex și urmați [ghidul operațional](operations/RUNBOOK.md). Nu reutilizați mediul `.venv` sau `node_modules` din Windows în WSL. Nu activați callbackuri, tuneluri sau trimiterea mesajelor doar pentru testarea consolei.

## Verificare și limite

```powershell
uv run pytest tests/test_local_platform.py tests/operations tests/runtime tests/channels/test_provider.py
bun run --cwd web build
```

Într-o clonă curată, testele operaționale folosesc instantaneul complet:

```powershell
$env:DAYBREAK_OPERATIONS_TEST_DATA = "outputs/demo"
uv run pytest tests/test_local_platform.py tests/operations tests/runtime tests/channels/test_provider.py
```

Fluxul GitHub Actions `Local Windows and Linux` verifică dependențele blocate, blocarea concurentă a fișierelor, oprirea proceselor proprii, operațiile, pregătirea datelor și build-ul web pe ambele sisteme. Adăugarea fluxului nu dovedește o execuție Windows reușită; rezultatul lui trebuie verificat. Verificările locale pe macOS nu confirmă microfonul, apelurile, Codex autentificat sau afișarea pe PC-ul colegului.
