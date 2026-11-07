"""Evaluarea bilanțului pe post: scrie `reports/bilant/metrics.json` (contractul ModelReport) și figurile.

    uv run python -m cyberpunks.a_bilant.dataset      # o dată: lotul simulat (~1 minut, 4 procese)
    uv run python -m cyberpunks.a_bilant.evaluate

Testul: zilele curate ale celor 300 de posturi din registrul C (rețele nevăzute la antrenare). Totul e SIMULARE pe
date publice, gândită pentru datele PPC.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import fusion_eval as FE
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant.fuse import combine_arrays
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.common.config import load as load_config
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "bilant"
DATASET = [
    "SimBench 1-LV-* (rețele de joasă tensiune și profile de consum, ODbL), variante SINTETICE construite de firul C",
    "Open-Meteo archive (CC BY 4.0), București-Ilfov, orar, 2024-07-01 - 2025-07-08",
    "Registrul de posturi al firului C (poziții OpenStreetMap, ODbL; rețelele din spate sintetice)",
    "Probleme ascunse de noi (contoare, furt înainte de contor, pierderi tehnice, client la postul greșit, contor de post setat greșit): SINTETIC",
]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "nogit"


def eval_normal(tr: pd.DataFrame, te: pd.DataFrame) -> tuple[dict, dict, dict[str, N.NormalModel], pd.DataFrame]:
    trc = tr[tr["clean"] & (tr["hist_days"] > 0)]
    tec = te[te["clean"] & (te["hist_days"] > 0)].copy()
    y = tec["short_kwh"].to_numpy()
    models = N.fit_pair(trc)
    model = models["warm"]
    pred = model.predict(tec)
    m = N.interval_metrics(y, pred)
    base_fix = N.interval_metrics(y, N.FixedPercent.fit(trc).predict(tec))
    base_phys = N.interval_metrics(y, N.PhysicsI2R.fit(trc).predict(tec))
    # fără istoricul postului (post nou, fără zile curate): aceleași trăsături, istoricul golit
    m_cold = N.interval_metrics(y, models["cold"].predict(N.drop_history(tec)))
    tec[["p10", "p50", "p90"]] = pred.to_numpy()
    metrics = {f"normal_{k}": v for k, v in m.items()}
    metrics.update({f"normal_fara_istoric_{k}": v for k, v in m_cold.items() if k in ("mae_kwh_day", "coverage_p10_p90")})
    metrics.update({f"procent_fix_{k}": v for k, v in base_fix.items() if k in ("mae_kwh_day", "coverage_p10_p90", "interval_width_kwh_day")})
    metrics["normal_test_days"] = float(len(tec))
    metrics["normal_test_posts"] = float(tec["post_id"].nunique())
    metrics["normal_mean_loss_kwh_day"] = float(np.mean(y))
    metrics["normal_median_loss_pct_throughput"] = float(np.median(y / tec["abs_kwh"].clip(lower=1e-3)) * 100)
    baseline = {f"normal_{k}": v for k, v in base_phys.items()}
    return metrics, baseline, models, tec


def fig_normal(tec: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    s = tec.sample(min(4000, len(tec)), random_state=0)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    ax[0].scatter(s["p50"], s["short_kwh"], s=3, alpha=0.3, color="#2b6cb0")
    lim = float(np.quantile(s["short_kwh"], 0.995))
    ax[0].plot([0, lim], [0, lim], color="#444", lw=1)
    ax[0].set_xlim(0, lim)
    ax[0].set_ylim(0, lim)
    ax[0].set_xlabel("pierderea normală estimată P50 (kWh/zi)")
    ax[0].set_ylabel("lipsa reală la post (kWh/zi)")
    ax[0].set_title("Rețele nevăzute, zile fără probleme")
    pid = tec.groupby("post_id")["short_kwh"].mean().sort_values().index[len(tec["post_id"].unique()) // 2]
    g = tec[tec["post_id"] == pid].sort_values("day")
    ax[1].fill_between(g["date"], g["p10"], g["p90"], color="#90cdf4", alpha=0.6, label="interval P10-P90")
    ax[1].plot(g["date"], g["p50"], color="#2b6cb0", lw=1, label="normal P50")
    ax[1].plot(g["date"], g["short_kwh"], color="#c53030", lw=0.8, label="lipsa reală")
    ax[1].set_title(f"{pid}: pierderea normală pe zi")
    ax[1].set_ylabel("kWh/zi")
    ax[1].legend(fontsize=8)
    fig.suptitle("Bilanț pe post, modelul pierderii normale (SIMULARE pe date publice)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "normal_loss.png", dpi=130)
    plt.close(fig)


def value_at_k(win: pd.DataFrame, score: np.ndarray, k: int = 10) -> float:
    """Ce parte din excesul real (kWh) al zilei e în primele k posturi după scor (media pe zilele de evaluare)."""
    vals = []
    for _, g in win.assign(_s=score).groupby("day"):
        tot = g["true_excess_kwh"].abs().sum()
        if tot <= 0:
            continue
        vals.append(g.nlargest(k, "_s")["true_excess_kwh"].abs().sum() / tot)
    return float(np.mean(vals))


def eval_diagnosis(wtr: pd.DataFrame, wte: pd.DataFrame) -> tuple[dict, dict, G.Diagnoser, pd.DataFrame]:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

    diag = G.fit(wtr)
    proba = diag.proba(wte)
    dec0 = G.pair_consistency(wte, G.decide(proba, wte))
    dec = G.apply_martor_rule(wte, dec0)
    y = wte["true_class"].to_numpy()
    lab = dec["label"].to_numpy()
    lab0 = dec0["label"].to_numpy()
    rl = G.rules(wte).to_numpy()
    m = {
        "diagnoza_macro_f1": float(f1_score(y, lab, average="macro")),
        "diagnoza_accuracy": float(accuracy_score(y, lab)),
        "diagnoza_abstain_rate": float(dec["abstain"].mean()),
        "diagnoza_macro_f1_fara_abtineri": float(f1_score(y[~dec["abstain"]], lab[~dec["abstain"]], average="macro")),
        "diagnoza_value_at_10_posts": value_at_k(wte, (dec["p_problem"] * wte["r_mean_kwh"].abs()).to_numpy()),
    }
    b = {
        "diagnoza_macro_f1": float(f1_score(y, rl, average="macro")),
        "diagnoza_accuracy": float(accuracy_score(y, rl)),
        "diagnoza_value_at_10_posts": value_at_k(wte, np.where(rl != "normal", wte["r_mean_kwh"].abs(), 0.0)),
    }
    for c, f in zip(CLASSES, f1_score(y, lab, average=None, labels=list(CLASSES)), strict=True):
        m[f"diagnoza_f1_{c}"] = float(f)
    # regula contorului martor (doar posturile care au martor): cu regula față de doar modelul
    hm = np.isfinite(wte["martor_diff"].to_numpy())
    cfg = y == "contor_bilant_setat"
    over = dec["martor_rule"].to_numpy() == "diferenta_peste_clasa"
    m["martor_windows"] = float(hm.sum())
    m["martor_rule_recall_contor_post"] = float((over & cfg & hm).sum() / max((cfg & hm).sum(), 1))
    m["martor_rule_false_alarms"] = float((over & ~cfg).sum())
    m["martor_model_only_f1_contor_post"] = float(f1_score(y[hm], lab0[hm], average=None, labels=["contor_bilant_setat"])[0])
    m["martor_with_rule_f1_contor_post"] = float(f1_score(y[hm], lab[hm], average=None, labels=["contor_bilant_setat"])[0])
    m["diagnoza_macro_f1_fara_martor"] = float(f1_score(y, lab0, average="macro"))
    m["martor_normal_diff_median_pct"] = float(np.nanmedian(wte.loc[hm & (y == "normal"), "martor_diff"]) * 100) if (hm & (y == "normal")).any() else float("nan")
    for c, f in zip(CLASSES, f1_score(y, rl, average=None, labels=list(CLASSES)), strict=True):
        b[f"diagnoza_f1_{c}"] = float(f)
    cm = pd.DataFrame(confusion_matrix(y, lab, labels=list(CLASSES)), index=list(CLASSES), columns=list(CLASSES))
    return m, b, diag, cm


def fig_confusion(cm: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    short = ["normal", "contor client", "furt înainte", "tehnică", "post greșit", "contor post"]
    norm = cm.div(cm.sum(1).clip(lower=1), axis=0)
    fig, ax = plt.subplots(figsize=(7, 5.6))
    ax.imshow(norm.to_numpy(), cmap="Blues", vmin=0, vmax=1)
    for i in range(len(cm)):
        for j in range(len(cm)):
            ax.text(j, i, f"{int(cm.iat[i, j])}", ha="center", va="center", fontsize=8, color="white" if norm.iat[i, j] > 0.5 else "#222")
    ax.set_xticks(range(len(cm)), short, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(cm)), short, fontsize=8)
    ax.set_xlabel("diagnosticul modelului")
    ax.set_ylabel("cauza reală (din construcție)")
    ax.set_title("Diagnosticul cauzei pe rețele nevăzute (SIMULARE)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "diagnosis_confusion.png", dpi=130)
    plt.close(fig)
    cm.to_csv(OUT / "diagnosis_confusion.csv")


def fig_fusion(with_b: dict, without: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ks = list(FE.KS)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(len(ks))
    ax[0].bar(x - 0.2, [without[f"precision_at_{k}"] * 100 for k in ks], 0.4, label="doar scorul contorului (A)", color="#a0aec0")
    ax[0].bar(x + 0.2, [with_b[f"precision_at_{k}"] * 100 for k in ks], 0.4, label="A + bilanțul postului", color="#2b6cb0")
    ax[0].set_xticks(x, [f"primele {k}" for k in ks])
    ax[0].set_ylabel("% contoare verificate cu problemă reală")
    ax[0].legend(fontsize=8)
    ax[1].bar(x - 0.2, [without[f"value_lei_per_day_at_{k}"] for k in ks], 0.4, color="#a0aec0")
    ax[1].bar(x + 0.2, [with_b[f"value_lei_per_day_at_{k}"] for k in ks], 0.4, color="#2b6cb0")
    ax[1].set_xticks(x, [f"primele {k}" for k in ks])
    ax[1].set_ylabel("lei recuperați pe zi de verificări")
    fig.suptitle("Cu bilanț față de fără, pe aceleași contoare și zile (SIMULARE; scoruri A simulate)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fusion_with_vs_without.png", dpi=130)
    plt.close(fig)


def fig_post_causes(pc: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = {"furt_inainte_contor": "furt înainte\nde contor", "pierdere_tehnica": "pierdere tehnică\n(cabluri, faze)", "contor_bilant_setat": "contorul postului\nsetat greșit", "client_post_gresit": "client la\npostul greșit"}
    cs = [c for c in FE.POST_CAUSES if f"{c}_found" in pc]
    x = np.arange(len(cs))
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(x - 0.27, [0] * len(cs), 0.27, color="#a0aec0", label="doar contoarele (A): nu le vede")
    ax.bar(x, [pc[f"{c}_found"] * 100 for c in cs], 0.27, color="#2b6cb0", label="bilanțul: post găsit")
    ax.bar(x + 0.27, [pc[f"{c}_right_cause"] * 100 for c in cs], 0.27, color="#2c5282", alpha=0.6, label="bilanțul: și cauza corectă")
    for i, c in enumerate(cs):
        ax.text(i - 0.27, 2, "0", ha="center", fontsize=8)
    ax.set_xticks(x, [names[c] for c in cs], fontsize=8)
    ax.set_ylabel("% din ferestrele cu această problemă")
    ax.set_ylim(0, 105)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Ce vede doar bilanțul: cauze pe care contoarele clienților nu le arată (SIMULARE)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "bilant_only_causes.png", dpi=130)
    plt.close(fig)


def fig_fusion_k(fw: dict, fwo: dict, fs: dict, fso: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ks = list(FE.KS)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for w, wo, lab, col in ((fw, fwo, "A de calitatea pe Londra (AUC 0,91)", "#2b6cb0"), (fs, fso, "A de calitatea pe SGCC (AUC 0,80)", "#dd6b20")):
        ax[0].plot(ks, [wo[f"value_lei_per_day_at_{k}"] for k in ks], "--", color=col, alpha=0.6, label=f"fără bilanț, {lab}")
        ax[0].plot(ks, [w[f"value_lei_per_day_at_{k}"] for k in ks], "-o", color=col, label=f"cu bilanț, {lab}")
        ax[1].bar(np.arange(len(ks)) + (0.2 if col == "#dd6b20" else -0.2), [w[f"wasted_trips_avoided_per_day_at_{k}"] for k in ks], 0.4, color=col, label=lab)
    ax[0].set_xlabel("contoare verificate pe zi (K)")
    ax[0].set_ylabel("lei recuperați pe zi")
    ax[0].legend(fontsize=7)
    ax[1].set_xticks(range(len(ks)), [str(k) for k in ks])
    ax[1].set_xlabel("contoare verificate pe zi (K)")
    ax[1].set_ylabel("deplasări degeaba evitate pe zi")
    ax[1].legend(fontsize=7)
    fig.suptitle("Cu bilanț față de fără, pe mai multe K (SIMULARE; scoruri A simulate)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fusion_k.png", dpi=130)
    plt.close(fig)


def main() -> None:
    tr = F.load_pool("train")
    te = F.load_pool("pop")
    metrics, baseline, models, tec = eval_normal(tr, te)
    models["warm"].save("normal")
    models["cold"].save("normal_cold")
    fig_normal(tec)
    sha = git_sha()

    # diagnosticul: ferestre de 14 zile; pe antrenare cu pierderea normală prezisă fără ca postul să fi fost văzut
    wtr = W.build_windows(tr, W.oof_normal(tr), "train")
    wte = W.build_windows(te, W.predict_normal(models, te), "pop")
    from cyberpunks.common.paths import DATA_PROCESSED

    wtr.to_parquet(DATA_PROCESSED / "bilant" / "windows_train.parquet")
    md, bd, diag, cm = eval_diagnosis(wtr, wte)
    proba = diag.proba(wte)
    dec_te = G.apply_martor_rule(wte, G.pair_consistency(wte, G.decide(proba, wte)))
    wdec = wte.join(dec_te).join(proba.add_prefix("p_")).assign(rule=G.rules(wte))
    wdec.to_parquet(DATA_PROCESSED / "bilant" / "windows_pop.parquet")
    tec.to_parquet(DATA_PROCESSED / "bilant" / "normal_test_pop.parquet")
    diag.save()
    fig_confusion(cm)
    metrics.update(md)
    baseline.update(bd)
    metrics["diagnoza_test_windows"] = float(len(wte))

    # fuziunea cu A: incertitudinea creșterii lipsei, măsurată pe ferestrele normale de antrenare
    nrm = wtr[wtr["true_class"] == "normal"]
    sig = {"delta": float(np.std(nrm["delta_kwh"] / (nrm["width_kwh"] / 2.56))), "level": float(np.std(nrm["r_mean_kwh"] / (nrm["width_kwh"] / 2.56)))}
    (N.MODEL_DIR / "fusion_sigma.json").write_text(json.dumps(sig))
    (N.MODEL_DIR / "version.json").write_text(json.dumps({"version": f"bilant-diagnoza-lgbm@{sha}"}))
    eco = load_config("economics")
    price = float(eco["energy"]["loss_cost_lei_per_kwh"])
    horizon = int(eco["meters"]["detection_horizon_days"])
    # (a) mai multe zile, scoruri A simulate, pe lotul train (problemele de contor apar pe tot anul; pierderea normală
    # prezisă fără ca postul să fi fost văzut). Lotul pop are acum defectele reale ale lui A, apărute în ultimele 60 de zile.
    t = FE.meter_table("train", wtr, sig["delta"])
    fw, fwo = FE.evaluate(t, price, horizon)
    fs, fso = FE.evaluate(t, price, horizon, target_auc=FE.A_SGCC_AUC)
    fig_fusion(fw, fwo)
    a_sc, _, _ = FE.simulate_a_scores(t)
    t.assign(a=a_sc, fused=combine_arrays(a_sc, t["excess"].to_numpy(), t["sigma"].to_numpy(), np.maximum(t["drop"].to_numpy(), 0.0))).to_parquet(DATA_PROCESSED / "bilant" / "fusion_meters_train.parquet")
    metrics.update({f"fuziune_sgcc_{k}": v for k, v in fs.items() if not k.startswith("info_")})
    baseline.update({f"fuziune_sgcc_{k}": v for k, v in fso.items()})
    # (b) ziua demo, scorurile REALE ale lui A pe cele ~15.850 de contoare
    real = FE.evaluate_real_a(wte, sig["delta"], price, horizon)
    metrics.update({f"fuziune_a_real_{k}": v for k, v in real.items()})
    # (c) energia pe care contoarele nu o văd (doar bilanțul o vede), ziua demo
    metrics.update({f"invizibil_{k}": v for k, v in FE.invisible_energy(te, int(te["day"].max())).items()})
    # (d) cauzele de post: ce găsește bilanțul acolo unde A are 0 prin construcție
    pc = FE.post_causes(wdec, price)
    metrics.update({f"cauze_post_{k}": v for k, v in pc.items()})
    baseline.update({f"cauze_post_{k}": 0.0 for k in pc if k.endswith(("_found", "_right_cause", "_share")) and "false_alarm" not in k})
    fig_post_causes(pc)
    fig_fusion_k(fw, fwo, fs, fso)
    metrics.update({f"fuziune_{k}": v for k, v in fw.items()})
    baseline.update({f"fuziune_{k}": v for k, v in fwo.items()})
    report = ModelReport(
        source="A",
        model_id="bilant-lgbm",
        model_version=f"bilant-lgbm@{sha}",
        task="bilanț pe post: pierderea normală (regresie cuantilă P10/P50/P90), diagnosticul cauzei (clasificare în 6 clase), fuziunea cu scorul contoarelor A (clasament în primele K)",
        dataset=DATASET,
        split="antrenare: 300 de posturi sintetice noi (lotul train); test: cele 300 de posturi din registrul C (rețele nevăzute). Pierderea normală: zilele fără probleme, cu cel puțin 21 de zile de istoric (test_size). Diagnosticul: ferestre de 14 zile, la 7 zile. Fuziunea: contoarele lotului de test, problemele apărute în ultimele 2-12 zile, K contoare verificate pe zi; scorurile A sunt simulate la ROC-AUC 0,907 (cel raportat de A)",
        test_size=int(metrics["normal_test_days"]),
        primary_metric="fuziune_precision_at_10",
        metrics={k: round(float(v), 4) for k, v in metrics.items()},
        baseline_id="fuziune_*: doar scorul A, fără bilanț; normal_*: formula fizică I²R (a·ΣP²·R/U² + b·nr. contoare); diagnoza_*: tabelul de reguli din concept; procent_fix_*: în metrics, al doilea reper pentru normal",
        baseline_metrics={k: round(float(v), 4) for k, v in baseline.items()},
        synthetic_share=1.0,
        created_at=datetime.now(ZoneInfo("Europe/Bucharest")).replace(microsecond=0),
        reproduce_cmd="uv run python -m cyberpunks.a_bilant.dataset && uv run python -m cyberpunks.a_bilant.evaluate",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: round(v, 3) for k, v in report.metrics.items()}, indent=1, ensure_ascii=False))
    print("baseline", json.dumps({k: round(v, 3) for k, v in report.baseline_metrics.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
