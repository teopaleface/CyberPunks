"""Ordinele de lucru în PDF, câte unul pe echipă. Text fix în română, date din plan; fără servicii externe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import Align

from cyberpunks.common.contracts import Decision, Plan, Route, Stop, WorkItem
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.settings import TZ, Crew, Settings
from cyberpunks.planner.texts import ACTION_RO, SKILL_RO, SOURCE_RO, hhmm, num, pct, zi

FONTS = Path(__file__).parent / "assets" / "fonts"
FAMILY = "NotoSans"
BANNER = "DEMO — date sintetice, nu este un document oficial Rețele Electrice"
FOOTER_NOTE = "Generat automat; fiecare oprire duce la predicția modelului în jurnalul deciziilor (audit.jsonl)."

NAVY = (0, 48, 87)
GREY = (110, 110, 110)
LIGHT = (234, 240, 246)
AMBER = (255, 225, 140)
RED = (176, 0, 32)
RED_BG = (253, 232, 232)
CONF_RO = {"high": "mare", "medium": "medie", "low": "mică"}
BLANK = "____________"


def _t(dt: datetime) -> datetime:
    return dt.astimezone(TZ)


def _kind_label(wi: WorkItem) -> str:
    a = wi.recommended_action.value
    if wi.source.value == "A":
        return "Verificare contor"
    if wi.source.value == "B":
        return "Echipă trimisă din timp (furtună)"
    if a == "adjust_tap":
        return "Schimbare priză transformator"
    if a == "measurement_campaign":
        return "Montare analizor de calitate"
    return ACTION_RO.get(a, a).capitalize()


class _Pdf(FPDF):
    def __init__(self, plan: Plan, number: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.plan = plan
        self.number = number
        self.add_font(FAMILY, "", str(FONTS / "NotoSans-Regular.ttf"))
        self.add_font(FAMILY, "B", str(FONTS / "NotoSans-Bold.ttf"))
        self.set_margins(14, 17, 14)
        self.set_auto_page_break(True, margin=22)
        self.set_title(f"Ordin de lucru {number}")
        self.set_author("Tura de mâine (agent de planificare)")
        self.alias_nb_pages("{nb}")
        self.set_font(FAMILY, "", 9.5)

    def header(self) -> None:
        self.set_fill_color(*AMBER)
        self.set_text_color(60, 40, 0)
        self.set_font(FAMILY, "B", 8.5)
        self.set_xy(14, 6)
        self.cell(self.epw, 6.5, BANNER, fill=True, align=Align.C)
        self.set_text_color(0, 0, 0)
        self.set_font(FAMILY, "", 9.5)
        self.set_xy(14, 17)

    def footer(self) -> None:
        self.set_draw_color(*GREY)
        self.set_line_width(0.2)
        self.line(14, self.h - 18, self.w - 14, self.h - 18)
        self.set_text_color(*GREY)
        self.set_font(FAMILY, "", 7.5)
        self.set_xy(14, self.h - 17)
        self.cell(40, 4, f"Pagina {self.page_no()} din {{nb}}")
        self.cell(
            self.epw - 40,
            4,
            f"{self.number} · plan {self.plan.plan_id} · planificator {self.plan.planner_version}",
            align=Align.R,
        )
        self.set_xy(14, self.h - 12.5)
        self.cell(self.epw, 4, FOOTER_NOTE)
        self.set_text_color(0, 0, 0)

    # -- ajutoare de desen ---------------------------------------------------------------------

    def kv(self, label: str, value: str, lw: float = 30, size: float = 9.5) -> None:
        self.set_font(FAMILY, "B", size)
        self.cell(lw, 4.8, label, new_x="RIGHT", new_y="TOP")
        self.set_font(FAMILY, "", size)
        self.multi_cell(0, 4.8, value, new_x="LMARGIN", new_y="NEXT", align=Align.L)

    def section(self, title: str) -> None:
        self.ln(1.2)
        self.set_font(FAMILY, "B", 9.5)
        self.set_text_color(*NAVY)
        self.cell(0, 5, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.set_font(FAMILY, "", 9.5)

    def bullets(self, lines: list[str]) -> None:
        for ln in lines:
            self.set_x(self.l_margin + 2)
            self.cell(4, 4.8, "•", new_x="RIGHT", new_y="TOP")
            self.multi_cell(0, 4.8, ln, new_x="LMARGIN", new_y="NEXT", align=Align.L)

    def boxes(self, label: str, options: list[str], lw: float = 30) -> None:
        """Rând cu casete goale (dreptunghiuri desenate), cu trecere pe rând nou dacă nu încape."""
        self.set_font(FAMILY, "", 9.5)
        x0, y = self.l_margin, self.get_y()
        self.set_xy(x0, y)
        self.set_font(FAMILY, "B", 9.5)
        self.cell(lw, 5.2, label, new_x="RIGHT", new_y="TOP")
        self.set_font(FAMILY, "", 9.5)
        x = x0 + lw
        right = self.w - self.r_margin
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.25)
        for opt in options:
            w = 4.5 + self.get_string_width(opt) + 4
            if x + w > right:
                x, y = x0 + lw, y + 5.2
            self.rect(x, y + 0.9, 3.2, 3.2)
            self.set_xy(x + 4.5, y)
            self.cell(w - 4.5, 5.2, opt)
            x += w
        self.set_xy(x0, y + 5.8)

    def blank_lines(self, n: int, h: float = 6.5) -> None:
        self.set_draw_color(150, 150, 150)
        self.set_line_width(0.15)
        for _ in range(n):
            self.ln(h)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)


def _steps(wi: WorkItem) -> list[str]:
    src, act = wi.source.value, wi.recommended_action.value
    if src == "A":
        return [
            "Citiți indexul contorului și verificați sigiliile.",
            "Căutați semne de bypass, racord direct sau capac deschis.",
            (
                "Faceți fotografii (index, sigilii, bornier). Dacă clientul este absent, fotografiile sunt obligatorii "
                "(Ord. ANRE 121/2015, art. 34)."
            ),
            "Nu atingeți părți aflate sub tensiune.",
        ]
    if src == "B":
        tw = wi.time_window
        win = f"{hhmm(_t(tw.start))}–{hhmm(_t(tw.end))}" if tw else "indicată de dispecer"
        return [
            f"Fiți în zonă înainte de fereastra de risc ({win}).",
            "Rămâneți în zonă până când alerta este ridicată de dispecer.",
            "Materialele pentru linii aeriene sunt încărcate în vehicul (verificați la plecare).",
        ]
    if act == "adjust_tap":
        return [
            "Întrerupere planificată: confirmați cu dispeceratul ora și clienții anunțați.",
            "Lucrați după foaia de manevră; scoateți postul de sub tensiune.",
            "Schimbați priza transformatorului la valoarea indicată de dispecer.",
            "Măsurați tensiunile pe faze înainte și după schimbare și notați-le mai jos.",
        ]
    return [
        "Montați un analizor de calitate a energiei la postul de transformare, pe partea de joasă tensiune.",
        "Lăsați analizorul montat cel puțin 7 zile; notați data montării și numărul aparatului.",
    ]


def _safety_form(wi: WorkItem) -> str:
    if wi.source.value == "A":
        return "Dispoziție verbală (DV) sau atribuții de serviciu (AS); fără lucru sub tensiune."
    if wi.source.value == "C" and wi.recommended_action.value == "adjust_tap":
        return "Autorizație de lucru (AL) necesară; foaie de manevră nr. ______; întrerupere planificată anunțată."
    return "Autorizație de lucru (AL) la intervenție."


def _stop_block(pdf: _Pdf, stop: Stop, wi: WorkItem | None, dec: Decision | None) -> None:
    eta = hhmm(_t(stop.eta))
    if wi is None:
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(FAMILY, "B", 10.5)
        pdf.cell(
            0, 7, f"  Oprirea {stop.seq} · ETA {eta} · {stop.work_item_id}", fill=True, new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(FAMILY, "", 9.5)
        pdf.multi_cell(
            0,
            5,
            "Detaliile lucrării lipsesc din datele de intrare; cereți-le dispeceratului.",
            new_x="LMARGIN",
            new_y="NEXT",
            align=Align.L,
        )
        return
    src = wi.source.value
    loc = wi.location

    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FAMILY, "B", 10.5)
    pdf.cell(
        pdf.epw * 0.72,
        7,
        f"  Oprirea {stop.seq} · ETA {eta} · {_kind_label(wi)}",
        fill=True,
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.set_font(FAMILY, "", 9)
    pdf.cell(0, 7, f"{wi.work_item_id}  ", fill=True, align=Align.R, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1.5)

    place = loc.label or wi.asset_id
    pdf.kv("Loc:", f"{place} · zona {loc.zone_id}" + (f" · județ {loc.county}" if loc.county else ""))
    pdf.kv(
        "Coordonate:",
        f"{loc.lat:.5f}, {loc.lon:.5f} · activ {wi.asset_id} · durată {stop.duration_min} min · {num(stop.travel_km, 1)} km de la oprirea anterioară",
    )

    if wi.impact.safety_flag:
        pdf.ln(0.8)
        pdf.set_fill_color(*RED_BG)
        pdf.set_draw_color(*RED)
        pdf.set_line_width(0.5)
        pdf.set_text_color(*RED)
        pdf.set_font(FAMILY, "B", 9.5)
        pdf.multi_cell(
            0,
            5,
            "ATENȚIE, RISC PENTRU OAMENI: lucrarea este marcată cu risc de siguranță (de exemplu șuntare, risc de incendiu). "
            "Nu începeți fără verificarea instalației și a echipamentului de protecție.",
            border=1,
            fill=True,
            padding=1.5,
            new_x="LMARGIN",
            new_y="NEXT",
            align=Align.L,
        )
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(FAMILY, "", 9.5)
        pdf.ln(0.8)

    pdf.section("De ce")
    factors = sorted(wi.explanation.top_factors, key=lambda f: abs(f.contribution), reverse=True)[:3]
    pdf.bullets([f.label_ro for f in factors])
    pr = wi.prediction
    pdf.kv("Scor model:", f"{pct(pr.score)} · încredere {CONF_RO.get(pr.confidence.value, pr.confidence.value)}")
    pdf.kv("Pe scurt:", wi.explanation.summary_ro)

    pdf.section("Ce faceți")
    pdf.bullets(_steps(wi))

    pdf.section("Siguranță")
    pdf.kv("Formă de lucru:", _safety_form(wi), lw=30)
    pdf.boxes("Verificări:", ["Separare electrică", "Legare la pământ și în scurtcircuit", "EIP verificat"], lw=30)

    pdf.section("De completat pe teren")
    if src == "A":
        pdf.kv("Index:", "__________ kWh        Nr. fotografii: _____", lw=30)
        pdf.boxes("Sigilii:", ["intacte", "rupte", "lipsă"], lw=30)
        pdf.boxes("Constatări:", ["capac deschis", "șunt", "racord direct", "nimic"], lw=30)
    elif src == "C":
        pdf.kv("Tensiuni:", "L1 ________ V     L2 ________ V     L3 ________ V", lw=30)
        if wi.recommended_action.value == "adjust_tap":
            pdf.kv("Priză:", "înainte ________      după ________", lw=30)
        else:
            pdf.kv("Analizor:", "nr. aparat ____________      montat la data ____________", lw=30)
    pdf.boxes("Rezultat:", ["rezolvat", "reprogramat", "escaladat"], lw=30)
    pdf.kv("Ora:", "început ___:___        sfârșit ___:___", lw=30)
    pdf.kv("Observații:", "", lw=30)
    pdf.blank_lines(2, 6)

    pdf.section("Semnături")
    right = {"A": "Client (sau: absent / refuză): ____________", "C": "Admitent: ____________"}.get(src)
    left = "Șef de lucrare: ____________    Executanți: ____________"
    if right:
        pdf.multi_cell(0, 5.5, left, new_x="LMARGIN", new_y="NEXT", align=Align.L)
        pdf.multi_cell(0, 5.5, right, new_x="LMARGIN", new_y="NEXT", align=Align.L)
    else:
        pdf.multi_cell(0, 5.5, left, new_x="LMARGIN", new_y="NEXT", align=Align.L)

    pdf.set_font(FAMILY, "", 7)
    pdf.set_text_color(*GREY)
    trace = [
        f"regulă {dec.rule_id}" if dec else None,
        f"predicție {pr.prediction_id}",
        f"model {pr.model_version}",
        f"audit {dec.audit_id}" if dec else None,
    ]
    pdf.ln(0.8)
    pdf.multi_cell(
        0, 3.4, "Trasabilitate: " + " · ".join(t for t in trace if t), new_x="LMARGIN", new_y="NEXT", align=Align.L
    )
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(FAMILY, "", 9.5)


def _render(
    plan: Plan,
    route: Route,
    crew: Crew | None,
    items: dict[str, WorkItem],
    decs: dict[str, Decision],
    settings: Settings,
) -> bytes:
    number = f"OL-{plan.plan_date:%Y%m%d}-{route.crew_id}"
    pdf = _Pdf(plan, number)
    pdf.add_page()

    pdf.set_font(FAMILY, "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(pdf.epw * 0.5, 10, "Ordin de lucru", new_x="RIGHT", new_y="TOP")
    pdf.set_font(FAMILY, "B", 12)
    pdf.cell(0, 10, f"{number}  ·  {zi(plan.plan_date)}", align=Align.R, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.6)
    pdf.line(14, pdf.get_y() + 0.5, pdf.w - 14, pdf.get_y() + 0.5)
    pdf.ln(3)

    depot = settings.depots.get(route.depot_id)
    skills = ", ".join(SKILL_RO.get(s, s) for s in sorted(crew.skills)) if crew else "—"
    pdf.kv("Echipa:", f"{route.crew_id} · depou {depot.label_ro if depot else route.depot_id}")
    pdf.kv("Competențe:", f"{skills} · {crew.size if crew else '—'} persoane")
    pdf.kv("Tura:", f"{settings.shift_start:%H:%M}–{settings.shift_end:%H:%M}")
    pdf.kv("Emitent:", "propus de agentul «Tura de mâine», aprobat de dispecer: ____________")
    pdf.kv("Șef de lucrare:", f"{BLANK}     grupa: ___")
    pdf.kv("Executanți:", "")
    pdf.blank_lines(2, 6)
    pdf.set_fill_color(*LIGHT)
    pdf.set_font(FAMILY, "B", 9.5)
    pdf.cell(
        0,
        7,
        f"  {len(route.stops)} {'oprire' if len(route.stops) == 1 else 'opriri'} · {num(route.total_km, 1)} km · {route.total_travel_min} min drum · "
        f"{route.total_work_min} min lucru",
        fill=True,
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font(FAMILY, "", 9.5)
    pdf.ln(3)

    # Itinerar
    pdf.set_font(FAMILY, "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Itinerar", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(FAMILY, "", 9)
    with pdf.table(
        col_widths=(9, 15, 56, 62, 15, 25),
        text_align=("CENTER", "CENTER", "LEFT", "LEFT", "RIGHT", "RIGHT"),
        line_height=5.2,
        headings_style=_heading_style(),
        borders_layout="HORIZONTAL_LINES",
        padding=(0.8, 1.2),
    ) as table:
        row = table.row()
        for h in ("Nr.", "ETA", "Tip", "Loc", "Min", "Km"):
            row.cell(h)
        for st in route.stops:
            wi = items.get(st.work_item_id)
            row = table.row()
            row.cell(str(st.seq))
            row.cell(hhmm(_t(st.eta)))
            row.cell(_kind_label(wi) if wi else "—")
            row.cell((wi.location.label or wi.asset_id) if wi else st.work_item_id)
            row.cell(str(st.duration_min))
            row.cell(num(st.travel_km, 1))
    pdf.ln(2)
    pdf.set_font(FAMILY, "", 8)
    pdf.set_text_color(*GREY)
    srcs = sorted({SOURCE_RO[items[s.work_item_id].source.value] for s in route.stops if s.work_item_id in items})
    note = "Km = de la oprirea anterioară (prima oprire: de la depou)."
    if srcs:
        note += " Sursa lucrărilor: " + ", ".join(srcs) + "."
    pdf.cell(0, 4, note, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    pdf.ln(4)
    for st in route.stops:
        wi, dec = items.get(st.work_item_id), decs.get(st.work_item_id)
        y0 = pdf.get_y()
        with pdf.offset_rendering() as probe:
            _stop_block(pdf, st, wi, dec)
        pdf.set_y(y0)
        if probe.page_break_triggered:
            pdf.add_page()
        _stop_block(pdf, st, wi, dec)
        pdf.ln(5)
    return bytes(pdf.output())


def _heading_style():
    from fpdf.fonts import FontFace

    return FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=NAVY)


def write_work_orders(plan: Plan, items: list[Item], plan_dir: Path, settings: Settings) -> list[Path]:
    """Writes plan_dir/work_orders/<crew_id>.pdf for every route in plan.routes; deletes stale PDFs of crews no longer in the plan; returns the written paths."""
    out = Path(plan_dir) / "work_orders"
    out.mkdir(parents=True, exist_ok=True)
    by_id = {i.id: i.wi for i in items}
    decs = {d.work_item_id: d for d in plan.decisions}
    crews = {c.crew_id: c for c in settings.crews}
    written: list[Path] = []
    for route in plan.routes:
        path = out / f"{route.crew_id}.pdf"
        path.write_bytes(_render(plan, route, crews.get(route.crew_id), by_id, decs, settings))
        written.append(path)
    keep = {p.name for p in written}
    for old in out.glob("*.pdf"):
        if old.name not in keep:
            old.unlink()
    return written
