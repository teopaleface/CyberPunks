"""Fixed, self-contained report pages. No external assets or executable content."""

from html import escape


def render_report(data):
    def esc(value):
        return escape(str(value), quote=True)

    labels = {
        "work_item_id": "Lucrare",
        "recommendation": "Recomandare",
        "reason": "Motiv",
        "eta": "Ora planificată",
        "duration_min": "Durată, minute",
        "seq": "Oprire",
        "travel_km": "Distanță, km",
        "case_id": "Sesizare",
        "status": "Stare",
        "next_step": "Pasul următor",
    }
    rows = data["rows"]
    pages = []
    for start in range(0, max(1, len(rows)), 3):
        cards = "".join(
            "<article>"
            + "".join(f"<p><b>{esc(labels.get(k, k))}</b><br>{esc(v)}</p>" for k, v in row.items())
            + "</article>"
            for row in rows[start : start + 3]
        )
        meta = " | ".join(esc(data[k]) for k in ("historical_date", "generated_at", "plan_version", "state"))
        pages.append(
            '<!doctype html><html lang="ro"><head><meta charset="utf-8">'
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "<style>*{box-sizing:border-box}body{margin:0;padding:20px;width:360px;background:#f5f5f5;"
            "color:#111;font:16px Arial;overflow-wrap:anywhere}header{border-top:8px solid #f9cf12}"
            "article{background:white;padding:12px;margin:12px 0;border-radius:12px}"
            "small{font-size:13px}p{line-height:1.5}h1{font-size:24px}</style></head><body>"
            f"<header><small>PPC · Daybreak</small><h1>{esc(data['title'])}</h1></header>"
            f"<p>{meta}</p><p>{'Include date sintetice' if data['synthetic'] else 'Date istorice'}</p>{cards}"
            f"<footer>Pagina {len(pages) + 1} · Confirmarea se face în aplicația autentificată.</footer></body></html>"
        )
    return pages
