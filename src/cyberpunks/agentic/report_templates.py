"""Fixed report pages with readable labels, private provenance and escaped text."""

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo


def render_report(data):
    def esc(value):
        return escape(str(value), quote=True)

    labels = {
        "title": "Locul intervenției",
        "recommendation": "Recomandare",
        "reason": "Motiv",
        "eta": "Ora planificată",
        "duration_min": "Durată, minute",
        "seq": "Oprire",
        "travel_km": "Distanță, km",
        "status": "Stare",
        "next_step": "Pasul următor",
    }
    actions = {
        "abstain": "Cere date suplimentare înainte de decizie.",
        "human_review": "Revizuire de către dispecer înainte de programare.",
        "request_additional_crews": "Cere întăriri. Capacitatea regională este ocupată.",
        "inspect_on_site": "Propune o inspecție pentru stabilirea cauzei.",
        "preposition_crew": "Propune poziționarea unei echipe înaintea evenimentului.",
        "measurement_campaign": "Propune măsurători suplimentare în teren.",
    }
    rows = data["rows"]
    page_count = max(1, (len(rows) + 2) // 3)
    stamp = datetime.fromisoformat(data["generated_at"]).astimezone(ZoneInfo("Europe/Bucharest"))
    state = "Traseu aprobat" if data["state"] == "approved" else "Propunere, neaplicată"
    metadata = f"Scenariu istoric: {esc(data['historical_date'])}<br>Generat: {esc(stamp.strftime('%d.%m.%Y %H:%M'))}, București"
    pages = []
    for start in range(0, max(1, len(rows)), 3):
        cards = []
        for row in rows[start : start + 3]:
            parts = []
            for key, value in row.items():
                if key in {"work_item_id", "case_id"}:
                    continue
                shown = actions.get(str(value), value) if key == "recommendation" else value
                parts.append(f"<p><b>{esc(labels.get(key, key))}</b><br>{esc(shown)}</p>")
            reference = row.get("work_item_id") or row.get("case_id")
            if reference:
                parts.append(f"<small>Referință: {esc(reference)}</small>")
            cards.append("<article>" + "".join(parts) + "</article>")
        pages.append(
            '<!doctype html><html lang="ro"><head><meta charset="utf-8">'
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "<style>*{box-sizing:border-box}body{margin:0;padding:20px;width:360px;background:#f5f5f5;"
            "color:#111;font:16px Arial;overflow-wrap:anywhere}header{border-top:8px solid #f9cf12}"
            "article{background:white;padding:16px;margin:14px 0;border-radius:12px}"
            "small,footer{font-size:12px;line-height:1.5;color:#555}p{line-height:1.5}h1{font-size:24px}"
            "header>p{font-size:13px}article>p:first-child{margin-top:0}</style></head><body>"
            f"<header><small>PPC · Daybreak</small><h1>{esc(data['title'])}</h1>"
            f"<p>{metadata}</p><p><b>{esc(state)}</b><br>{'Include date sintetice' if data['synthetic'] else 'Date istorice'}</p></header>"
            + "".join(cards)
            + f"<footer>Pagina {len(pages) + 1} din {page_count}. Confirmarea se face în aplicația autentificată.</footer></body></html>"
        )
    return pages
