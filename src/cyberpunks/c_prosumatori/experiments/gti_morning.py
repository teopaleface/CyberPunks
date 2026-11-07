"""Experiment: radiația de dimineață (6-11) ca trăsătură, pentru posturile cu baterii. Nu atinge metrics.json.

    uv run python -m cyberpunks.c_prosumatori.experiments.gti_morning     # reports/C/experiment_gti_morning.json
"""
import json

import pandas as pd

from cyberpunks.c_prosumatori import evaluate as E
from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import train as T
from cyberpunks.c_prosumatori import weather
from cyberpunks.common.paths import REPORTS

df = T.load_daily("train")
hw = F.hourly_weather(weather.archive())
morning = hw[(hw.hour >= 6) & (hw.hour < 11)].groupby("date")["gti"].sum() / 1000
df["gti_morning"] = df["date"].map(morning)
F.DAILY_FEATURES.append("gti_morning")
T.load_daily = lambda pool="train", refresh=False: df  # evaluarea folosește tabelul cu trăsătura nouă
captured = {}
_orig = E.summarize
def _cap(res, seconds):
    captured["res"] = res
    return _orig(res, seconds)
E.summarize = _cap
det = E.evaluate(save=False)
r = captured["res"]
bat = pd.cut(r.battery_pv_share, [-0.01, 0.0, 0.25, 0.5, 1.0], labels=["fara", "sub25", "25-50", "peste50"])
by_bat = r.assign(ae=(r.m_q50 - r.vmax_day).abs()).groupby(bat, observed=True)["ae"].mean().round(5).to_dict()
res = {"model": {k: det["model"][k] for k in ("mae_vmax_pu", "coverage_p10_p90", "pr_auc_exceed", "recall_exceed", "brier")},
       "by_topology_mae": {t: v["model"]["mae_vmax_pu"] for t, v in det["by_topology"].items()},
       "mae_by_battery_share": {str(k): v for k, v in by_bat.items()}}
(REPORTS / "C" / "experiment_gti_morning.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=1))
