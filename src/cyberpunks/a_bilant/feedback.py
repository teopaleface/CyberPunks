"""Verdictul echipei după vizită devine etichetă nouă pentru diagnostic (bucla de învățare).

Omul răspunde prin review-ul existent din API (`POST /review/{id}`), care scrie în `outputs/plans/<s>/audit.jsonl`
o linie cu `actor: human`. Convenția pentru bilanț: în `note`, `verdict:<clasă>` (o clasă din `problems.CLASSES`),
de exemplu `verdict:furt_inainte_contor` sau `verdict:normal` (deplasare degeaba). `reject` fără verdict înseamnă
„problema nu s-a confirmat” și se citește ca `normal`.

La reantrenare (`collect` → `windows_with_verdicts`): fereastra postului din ziua lucrării primește eticheta
verdictului în locul celei simulate și o pondere mai mare (`VERDICT_WEIGHT`), pentru că e o observație reală. Pe date
PPC, verdictele devin cu timpul principala sursă de etichete, iar simularea rămâne doar pentru clasele rare.
"""

from __future__ import annotations

import json
import re

import pandas as pd

from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.common.paths import plan_dir

VERDICT_WEIGHT = 5.0
_RX = re.compile(r"verdict:\s*([a-z_]+)")


def collect(scenario: str) -> pd.DataFrame:
    """Verdictele umane pentru lucrările de bilanț (A-<data>-PT-...), din jurnalul planului."""
    p = plan_dir(scenario) / "audit.jsonl"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            wid = r.get("work_item_id") or ""
            if r.get("actor") != "human" or not re.match(r"^A-\d{8}-PT-", wid):
                continue
            note = (r.get("note") or "").lower()
            m = _RX.search(note)
            if m and m.group(1) in CLASSES:
                verdict = m.group(1)
            elif "reject" in (r.get("action") or "").lower():
                verdict = "normal"
            else:
                continue
            rows.append({"work_item_id": wid, "post_id": wid[11:], "date": pd.Timestamp(wid[2:10]), "verdict": verdict, "prediction_id": r.get("prediction_id"), "ts": r.get("ts")})
    return pd.DataFrame(rows, columns=["work_item_id", "post_id", "date", "verdict", "prediction_id", "ts"]).drop_duplicates("work_item_id", keep="last")


def windows_with_verdicts(win: pd.DataFrame, verdicts: pd.DataFrame) -> pd.DataFrame:
    """Înlocuiește eticheta ferestrelor (post, zi) cu verdictul și adaugă coloana `weight` pentru antrenare."""
    w = win.copy()
    w["weight"] = 1.0
    if verdicts.empty:
        return w
    key = verdicts.set_index(["post_id", "date"])["verdict"]
    idx = pd.MultiIndex.from_arrays([w["post_id"], pd.to_datetime(w["date"])])
    hit = idx.isin(key.index)
    w.loc[hit, "true_class"] = key.reindex(idx[hit]).to_numpy()
    w.loc[hit, "weight"] = VERDICT_WEIGHT
    return w
