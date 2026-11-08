"""Human-facing PDF copy and layout, derived only from verified report fields."""

import re
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from .report_templates import render_report

MONTHS = (
    "ianuarie",
    "februarie",
    "martie",
    "aprilie",
    "mai",
    "iunie",
    "iulie",
    "august",
    "septembrie",
    "octombrie",
    "noiembrie",
    "decembrie",
)


def report_filename(data):
    day = datetime.fromisoformat(data["historical_date"])
    kind = {"technician": "Traseu", "dispatcher": "Decizii", "customer": "Sesizare"}[data["kind"]]
    return f"Daybreak-{kind}-{day.day}-{MONTHS[day.month - 1]}-{day.year}.pdf"


def reason_for_visit(value):
    text = str(value).strip()
    if text.startswith("Risc pentru siguranța oamenilor") and "bilanț" in text.lower() and "post" in text.lower():
        return "Prioritate de siguranță. Bilanțul postului semnalează pierderi care trebuie verificate în teren."
    if re.match(r"^\d+% din ultimele 4 săptămâni fără date;", text):
        text = text.split("Scor")[0].strip().rstrip("; .")
        text = re.sub(
            r"^(\d+)% din ultimele 4 săptămâni fără date;", r"Date lipsă în \1% din ultimele patru săptămâni;", text
        )
        text = text.replace("cel mai lung gol:", "cea mai lungă pauză:")
        text = re.sub(r"(\d+) zile fără date", r"\1 zile", text)
        text = text.replace("salturi imposibile", "variații neobișnuite")
        text = text.replace("; cea mai lungă", ". Cea mai lungă")
        return text + "."
    return text


def pdf_pages(data):
    if data["kind"] != "technician":
        return render_report(data)
    esc = lambda value: escape(str(value), quote=True)
    day = datetime.fromisoformat(data["historical_date"])
    date = f"{day.day} {MONTHS[day.month - 1]} {day.year}"
    generated = datetime.fromisoformat(data["generated_at"]).astimezone(ZoneInfo("Europe/Bucharest"))
    rows = data["rows"]
    total = sum(float(row.get("duration_min", 0)) for row in rows)

    def duration(value):
        n = round(float(value))
        return f"{n // 60} h {n % 60:02d} min" if n >= 60 else f"{n} min"

    cards = []
    for i, row in enumerate(rows):
        title = str(row.get("title") or "Intervenție programată")
        if title.startswith("MTR-"):
            title = "Contor " + title
        elif title.startswith("PT-"):
            title = "Post de transformare " + title
        eta = datetime.fromisoformat(row["eta"]).strftime("%H:%M") if row.get("eta") else "Oră neprecizată"
        distance = (
            f"{float(row['travel_km']):.2f}".rstrip("0").rstrip(".").replace(".", ",") + " km"
            if row.get("travel_km") is not None
            else "neprecizată"
        )
        cards.append(
            f"<article><p><small>OPRIREA {i + 1:02d}</small><br><b>{esc(eta)} · {esc(title)}</b></p>"
            f"<p>La intervenție: <b>{esc(duration(row.get('duration_min', 0)))}</b> &nbsp; · &nbsp; Deplasare până aici: <b>{esc(distance)}</b></p>"
            f"<p>{esc(reason_for_visit(row.get('reason', '')))}</p></article>"
        )
    state = "Traseu aprobat" if data["state"] == "approved" else "Traseu propus · Așteaptă aprobarea dispecerului"
    note = "Scenariu istoric, cu date sintetice." if data["synthetic"] else "Scenariu istoric."
    return [
        '<!doctype html><html lang="ro"><head><meta charset="utf-8">'
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        "<style>html body{font:14px/1.45 Arial!important;background:white!important;color:#172026!important}"
        "header{border-top:5px solid #f5c900;padding:12px 0 12px!important;border-bottom:1px solid #dce0e2}"
        "header h1{font-size:28px!important;letter-spacing:-1px;margin:8px 0!important}"
        "header p{font-size:14px!important;margin:8px 0!important}small{font-size:11px;color:#59636b}"
        "section article{background:white;border:1px solid #dce0e2;border-left:4px solid #f5c900;border-radius:8px;"
        "padding:8px 12px!important;margin:9px 0!important;break-inside:avoid}"
        "section article p{font-size:13px;line-height:1.45!important;margin:8px 0!important}"
        "section article p:first-child b{font-size:17px}section article p:nth-child(2){color:#59636b}"
        "</style></head><body><header><small>DAYBREAK / FIȘĂ DE TEREN</small><h1>Fișa de traseu</h1>"
        f"<p>{esc(date)} &nbsp; · &nbsp; {esc(state)}</p><p><b>{len(rows)} opriri</b> &nbsp; · &nbsp; Timp la intervenții: <b>{esc(duration(total))}</b></p>"
        f"<small>{esc(note)} Orele sunt planificate, în ora României.<br>Pregătit la {esc(generated.strftime('%d.%m.%Y, %H:%M'))}.</small></header>"
        + "".join(cards)
        + "</body></html>"
    ]
