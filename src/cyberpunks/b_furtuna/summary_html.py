"""Pagina de rezumat B (pentru Teo și pentru prezentare), din fișierele de metrici și figurile din reports/B.

    uv run python -m cyberpunks.b_furtuna.summary_html
Scrie `outputs/B/summary.html` (în afara git): o pagină autonomă, cu imaginile incluse.
"""

from __future__ import annotations

import base64
import html
import json

from cyberpunks.common.paths import OUTPUTS, REPORTS

OUT = OUTPUTS / "B" / "summary.html"


def _img(name: str, alt: str) -> str:
    path = REPORTS / "B" / name
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'<figure><img alt="{html.escape(alt)}" src="data:image/png;base64,{b64}"><figcaption>{html.escape(alt)}</figcaption></figure>'


def _f(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _p(x: float) -> str:
    return f"{100 * x:.0f}%"


def build() -> str:
    m = json.loads((REPORTS / "B" / "metrics.json").read_text(encoding="utf-8"))
    d = json.loads((REPORTS / "B" / "metrics_detail.json").read_text(encoding="utf-8"))
    mm, main = m["metrics"], d["main"]
    lo = d.get("loso_summary") or {}
    cap = d.get("capacity", {}).get("results", {})
    k = d.get("capacity", {}).get("k_crews_per_day")
    ti = d["train_info"]
    rows = [
        ("Model (LightGBM calibrat)", mm["pr_auc"], mm["brier"], mm.get("recall_severe_at_thr", float("nan"))),
        ("Climatologie comitat × lună", m["baseline_metrics"]["pr_auc"], m["baseline_metrics"]["brier"],
         m["baseline_metrics"]["recall_severe_at_thr"]),
        ("Climatologie pe lună", main["clim_month"]["pr_auc"], main["clim_month"]["brier"],
         main["clim_month"]["recall_severe_at_thr"]),
        ("Regula pe rafală", main["gust_rule"]["pr_auc"], main["gust_rule"]["brier"], main["gust_rule"]["recall_severe_at_thr"]),
    ]
    trs = "".join(
        f"<tr{' class=hl' if i == 0 else ''}><th scope=row>{html.escape(n)}</th><td>{_f(a)}</td><td>{_f(b, 4)}</td><td>{_p(c)}</td></tr>"
        for i, (n, a, b, c) in enumerate(rows)
    )
    tiles = [
        (_f(mm["pr_auc"]), f"PR-AUC pe {2025}, an nevăzut (climatologia: {_f(m['baseline_metrics']['pr_auc'])})"),
        (_f(lo.get("model_pr_auc_mean", float("nan"))), f"PR-AUC pe state nevăzute (climatologia: {_f(lo.get('clim_month_pr_auc_mean', float('nan')))})"),
        (_p(mm["coverage_p10_p90"]), "din avarii cad în intervalul P10-P90 (ținta 80%)"),
    ]
    if cap:
        tiles.append((_p(cap["model"]["customers_covered_share"]),
                      f"din clienții afectați acoperiți cu {k} echipe pe zi (la întâmplare: {_p(cap['aleator']['customers_covered_share'])})"))
    tiles_html = "".join(f"<div class=tile><div class=big>{v}</div><div class=lbl>{html.escape(t)}</div></div>" for v, t in tiles)
    return f"""<!doctype html><html lang=ro><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>B: risc de avarii la furtună</title>
<style>
.viz-root{{color-scheme:light;--s:#fcfcfb;--t1:#0b0b0b;--t2:#52514e;--g:#e4e3df;--b:#2a78d6}}
body{{margin:0;background:#fcfcfb;color:#0b0b0b;font:15px/1.5 -apple-system,system-ui,Segoe UI,Roboto,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:28px 22px 48px}}
h1{{font-size:24px;margin:0 0 4px}} .sub{{color:#52514e;margin:0 0 22px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:0 0 26px}}
.tile{{border:1px solid #e4e3df;border-radius:10px;padding:14px 16px;background:#fff}}
.big{{font-size:30px;font-weight:650;color:#2a78d6;font-variant-numeric:tabular-nums}} .lbl{{color:#52514e;font-size:13px}}
table{{border-collapse:collapse;width:100%;margin:6px 0 26px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #e4e3df}} td{{text-align:right}}
thead th{{color:#52514e;font-weight:600;font-size:13px}} tr.hl th,tr.hl td{{font-weight:650}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}}
figure{{margin:0}} img{{width:100%;height:auto;border:1px solid #e4e3df;border-radius:8px;background:#fcfcfb}}
figcaption{{color:#52514e;font-size:13px;margin-top:4px}} .note{{color:#52514e;font-size:13px}}
</style></head><body class=viz-root><main>
<h1>Riscul de avarii la furtună (firul B)</h1>
<p class=sub>Model <code>{html.escape(m['model_version'])}</code>, antrenat pe {ti['counties']} comitate din SUA ({', '.join(ti['states'])}),
anii {ti['years'][0]}-{ti['years'][-1]}; test pe 2025. Toate cifrele vin din <code>reports/B/metrics.json</code>.</p>
<div class=tiles>{tiles_html}</div>
<table><caption class=note style="text-align:left;caption-side:top">Test pe 2025 ({m['test_size']:,} zile-comitat, prevalență {_p(mm['prevalence'])})</caption>
<thead><tr><th scope=col>Metoda</th><th scope=col>PR-AUC (mai mare e mai bine)</th><th scope=col>Brier (mai mic e mai bine)</th><th scope=col>Recall avarii severe la prag</th></tr></thead>
<tbody>{trs}</tbody></table>
<div class=grid>
{_img('fig_backtest_zones.png', 'Backtest România: riscul pe zone, 6-10 iulie 2025 (furtuna din Banat, cod roșu pe 8 iulie)')}
{_img('fig_gust_bins.png', 'Avariile cresc cu rafala: frecvența reală față de probabilitatea prezisă')}
{_img('fig_pr_curves.png', 'Precizie-recall pe 2025: modelul față de baseline-uri')}
{_img('fig_shap_importance.png', 'Ce contează pentru risc (SHAP)')}
</div>
<p class=note>Validat pe date externe (SUA, EAGLE-I); de calibrat pe istoricul de avarii Rețele Electrice.</p>
</main></body></html>""".replace(f"{m['test_size']:,}", f"{m['test_size']:,}".replace(",", "."))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
