"""Run after extract-daybreak.py: replaces the brainstorm letters A/B/C in display strings with the source names. Usage: python -I scripts/clean-letters.py src/data/daybreak.json"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))

NAME = {"A": "contoare", "B": "furtună", "C": "tensiune"}
REPL = [
    (r"surse A=ok/model, A_bilant=ok/model, B=ok/model, C=ok/model", "surse contoare=ok/model, bilanț=ok/model, furtună=ok/model, tensiune=ok/model"),
    (r"\bA_bilant\b", "bilanț"),
    (r"\b(modelul|modelului|firul|firului|sursa|sursei|registrul|registrului|scorurile|scorul|raportat de)\s+([ABC])\b",
     lambda m: f"{m.group(1)} de {NAME[m.group(2)]}" if m.group(1) in ("modelul", "modelului", "firul", "firului", "registrul", "registrului", "scorurile", "scorul")
     else f"{m.group(1)} modelul de {NAME[m.group(2)]}" if m.group(1) == "raportat de" else f"{m.group(1)} {NAME[m.group(2)]}"),
]
REPL += [(r"bfirul de ", "modulul de "), (r"bfirului de ", "modulului de ")]
LEFT = re.compile(r"(?<![\w\-./])[ABC](?![\w\-./])")
changed = 0
left = []


def fix(s, path):
    global changed
    out = s
    for a, b in REPL:
        out = re.sub(a, b, out)
    if out != s:
        changed += 1
    if LEFT.search(out):
        left.append((path, out[:200]))
    return out


SKIP_KEYS = {"source", "id", "allItems", "sources", "perSource", "models", "modelCards"}


def walk(x, path=""):
    if isinstance(x, dict):
        return {k: (v if (k in SKIP_KEYS and not isinstance(v, (str,)) and k != "modelCards") and k in ("allItems", "perSource", "models") else walk(v, f"{path}.{k}")) for k, v in x.items()}
    if isinstance(x, list):
        return [walk(v, f"{path}[]") for v in x]
    if isinstance(x, str):
        return fix(x, path)
    return x


d = walk(d)
p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("changed", changed)
for a, b in left[:40]:
    print("LEFT", a, "|", b)
