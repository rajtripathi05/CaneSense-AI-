"""PDF / CSV / Excel report generation from the *currently selected* recommendation table."""
from __future__ import annotations
import io
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether)
from . import engine
from .config import APP_NAME, DESCRIPTOR
from .theme import C

DISCLAIMER = ("All farms, plots, readings and recommendations in this report are SYNTHETIC and generated for demonstration. "
              "The model is trained on synthetic labels and has not been validated on real sugarcane farms. "
              "Outputs are decision-support suggestions, not agronomic or engineering advice.")
FOREST, LEAF, LIME = colors.HexColor(C["forest"]), colors.HexColor(C["leaf"]), colors.HexColor(C["lime"])
RISK_RGB = {"High": colors.HexColor(C["red"]), "Medium": colors.HexColor(C["amber"]), "Low": colors.HexColor(C["leaf"])}

COLS = {"plot_id": "Plot", "village": "Village", "crop_stage": "Crop stage", "area_ha": "Area (ha)", "soil_moisture": "Moisture (%)", "moisture_mean_period": "Mean moisture, period (%)",
        "urgency": "Urgency", "p_high": "P(high)", "action": "Recommended action", "depth_mm": "Depth (mm)", "volume_m3": "Water (m³)",
        "duration_h": "Duration (h)", "irrigation_type": "System", "sensor_status": "Sensor", "data_quality": "Data quality"}


def export_table(df: pd.DataFrame) -> pd.DataFrame:
    t = df.sort_values("rank")[[c for c in COLS if c in df.columns]].rename(columns=COLS).copy()
    t["P(high)"] = (t["P(high)"] * 100).round(0)
    return t.reset_index(drop=True)


def meta_lines(scope: dict, generated: datetime) -> list[tuple[str, str]]:
    return [("Generated", generated.strftime("%d %b %Y %H:%M")), ("Scenario", scope.get("scenario", "Normal Conditions")),
            ("Villages", scope.get("villages", "All")), ("Risk levels", scope.get("risks", "All")),
            ("Records", str(scope.get("records", ""))), ("Data window", scope.get("period", "Latest synthetic snapshot"))]


def to_csv(df: pd.DataFrame, scope: dict, generated: datetime) -> bytes:
    head = "".join(f"# {k}: {v}\n" for k, v in meta_lines(scope, generated)) + "# SYNTHETIC DATA - demonstration only\n"
    return (head + export_table(df).to_csv(index=False)).encode("utf-8")


def to_excel(df: pd.DataFrame, scope: dict, generated: datetime) -> bytes:
    buf = io.BytesIO()
    t = export_table(df)
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        wb = xw.book
        hfmt = wb.add_format({"bold": True, "bg_color": C["forest"], "font_color": "#FFFFFF", "border": 1, "text_wrap": True, "valign": "vcenter"})
        title = wb.add_format({"bold": True, "font_size": 16, "font_color": C["forest"]})
        s = wb.add_worksheet("Summary")
        xw.sheets["Summary"] = s
        s.write("A1", f"{APP_NAME} · {DESCRIPTOR}", title)
        for i, (k, v) in enumerate(meta_lines(scope, generated), start=3):
            s.write(i, 0, k, wb.add_format({"bold": True}))
            s.write(i, 1, v)
        k = engine.kpis(df)
        rows = [("Plots in scope", k["plots"]), ("Plots requiring irrigation", k["need_irrigation"]), ("High-urgency plots", k["high_risk"]),
                ("Estimated water demand (m³)", round(k["demand_m3"])), ("Sensors online", f"{k['sensors_online']} of {k['plots']}")]
        for i, (a, b) in enumerate(rows, start=11):
            s.write(i, 0, a, wb.add_format({"bold": True}))
            s.write(i, 1, b)
        s.write(18, 0, DISCLAIMER, wb.add_format({"text_wrap": True, "italic": True}))
        s.set_column(0, 0, 32)
        s.set_column(1, 1, 40)
        s.set_row(18, 60)
        t.to_excel(xw, sheet_name="Plots", index=False, startrow=0)
        w = xw.sheets["Plots"]
        for j, c in enumerate(t.columns):
            w.write(0, j, c, hfmt)
            w.set_column(j, j, max(11, min(34, int(t[c].astype(str).str.len().max()) + 2)))
        w.autofilter(0, 0, len(t), len(t.columns) - 1)
        w.freeze_panes(1, 1)
        for lvl, colr in (("High", C["red_soft"]), ("Medium", C["amber_soft"]), ("Low", C["green_soft"])):
            w.conditional_format(1, t.columns.get_loc("Urgency"), len(t), t.columns.get_loc("Urgency"),
                                 {"type": "cell", "criteria": "==", "value": f'"{lvl}"', "format": wb.add_format({"bg_color": colr})})
        act = t[t["Recommended action"] != engine.A_MONITOR][["Plot", "Village", "Urgency", "Recommended action", "Water (m³)", "Duration (h)"]]
        act.to_excel(xw, sheet_name="Actions", index=False)
        for j, c in enumerate(act.columns):
            xw.sheets["Actions"].write(0, j, c, hfmt)
            xw.sheets["Actions"].set_column(j, j, 30 if c == "Recommended action" else 14)
    return buf.getvalue()


def _charts(df: pd.DataFrame) -> io.BytesIO:
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.5), dpi=170)
    t = df.groupby(["village", "urgency"]).size().unstack(fill_value=0).reindex(columns=["High", "Medium", "Low"], fill_value=0)
    left = None
    for lvl in ["High", "Medium", "Low"]:
        ax[0].barh(t.index, t[lvl], left=left, color=C[{"High": "red", "Medium": "amber", "Low": "leaf"}[lvl]], label=lvl)
        left = t[lvl] if left is None else left + t[lvl]
    ax[0].invert_yaxis(); ax[0].set_title("Urgency by village (plots)", fontsize=8, loc="left"); ax[0].tick_params(labelsize=7)
    ax[0].legend(fontsize=6, frameon=False, loc="lower right")
    v = df.sort_values("volume_m3", ascending=False).head(8)
    ax[1].barh(v.plot_id.str[-3:], v.volume_m3, color=C["blue"])
    ax[1].invert_yaxis(); ax[1].set_title("Top water demand (m³)", fontsize=8, loc="left"); ax[1].tick_params(labelsize=7)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    b = io.BytesIO(); fig.savefig(b, format="png"); plt.close(fig); b.seek(0)
    return b


class _Numbered(rl_canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.setFont("Helvetica", 7.5); self.setFillColor(colors.HexColor("#66736C"))
            self.drawRightString(A4[0] - 16 * mm, 9 * mm, f"Page {self._pageNumber} of {n}")
            super().showPage()
        super().save()


def _mark(c, x, y, s):
    c.setFillColor(FOREST); c.roundRect(x, y, s, s, s * .23, fill=1, stroke=0)
    c.setFillColor(LIME); c.circle(x + s / 2, y + s * .4, s * .22, fill=1, stroke=0)
    p = c.beginPath(); p.moveTo(x + s / 2, y + s * .84); p.lineTo(x + s * .3, y + s * .5); p.lineTo(x + s * .7, y + s * .5); p.close()
    c.drawPath(p, fill=1, stroke=0)


def to_pdf(df: pd.DataFrame, scope: dict, generated: datetime, academic: dict | None = None, extra_footer: str = "") -> bytes:
    buf = io.BytesIO()
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Heading2"], textColor=FOREST, fontSize=12, spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=8.5, leading=11.5)
    small = ParagraphStyle("s", parent=body, fontSize=7, leading=9, textColor=colors.HexColor("#66736C"))
    cell = ParagraphStyle("c", parent=body, fontSize=7, leading=8.5)

    def page(c, d):
        c.saveState()
        c.setFillColor(FOREST); c.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)
        _mark(c, 14 * mm, A4[1] - 13.5 * mm, 11 * mm)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12); c.drawString(28 * mm, A4[1] - 9.5 * mm, APP_NAME)
        c.setFont("Helvetica", 7.5); c.setFillColor(LIME); c.drawString(28 * mm, A4[1] - 13.2 * mm, DESCRIPTOR.upper())
        c.setFillColor(colors.white); c.drawRightString(A4[0] - 14 * mm, A4[1] - 10 * mm, "Irrigation Operations Report")
        c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#66736C"))
        c.drawString(16 * mm, 9 * mm, f"Synthetic data - demonstration only  |  Generated {generated:%d %b %Y %H:%M}" + (f"  |  {extra_footer}" if extra_footer else ""))
        c.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=22 * mm, bottomMargin=16 * mm,
                          title=f"{APP_NAME} Irrigation Operations Report", author=APP_NAME)
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=page)])
    k = engine.kpis(df)
    s = [Paragraph("Irrigation Operations Report", ParagraphStyle("t", parent=ss["Title"], textColor=FOREST, fontSize=20, alignment=0, spaceAfter=2)),
         Paragraph(f"Scenario: <b>{scope.get('scenario', 'Normal Conditions')}</b> &nbsp;|&nbsp; Villages: {scope.get('villages', 'All')} &nbsp;|&nbsp; "
                   f"Risk: {scope.get('risks', 'All')} &nbsp;|&nbsp; {scope.get('period', 'Latest synthetic snapshot')}", small), Spacer(1, 6)]
    if academic:
        s.insert(2, Paragraph(f"Academic project: {academic['project']} - {academic['name']} ({academic['roll']}, {academic['batch']}); "
                              f"Faculty: {academic['professor']}.", small))
    tiles = [[Paragraph(f"<font size=15><b>{v}</b></font><br/><font size=7 color='#66736C'>{lab}</font>", body) for v, lab in [
        (k["plots"], "PLOTS IN SCOPE"), (k["need_irrigation"], "NEED IRRIGATION"), (k["high_risk"], "HIGH-URGENCY"),
        (f"{k['demand_m3']:,.0f}", "WATER DEMAND (m³)"), (f"{k['sensors_online']}/{k['plots']}", "SENSORS ONLINE")]]]
    tt = Table(tiles, colWidths=[doc.width / 5] * 5)
    tt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .6, colors.HexColor(C["line"])), ("INNERGRID", (0, 0), (-1, -1), .6, colors.HexColor(C["line"])),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF9F3")), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s += [tt, Paragraph("Farm summary and risk overview", h)]
    cnt = df.action.value_counts()
    s.append(Paragraph(f"{k['plots']} plots across {k['farms']} villages ({k['area_ha']:.1f} ha) are in scope. "
                       f"<b>{k['high_risk']}</b> are high urgency, <b>{k['medium_risk']}</b> medium and <b>{k['low_risk']}</b> low. "
                       f"{k['need_irrigation']} plots have an irrigation action (including {k['rain_adjust']} rainfall adjustment and {k['restricted']} deferred by the water budget); "
                       f"{k['review']} need a sensor review. Estimated demand is <b>{k['demand_m3']:,.0f} m³</b>, of which {k['allocated_m3']:,.0f} m³ fits the daily budget.", body))
    s += [Spacer(1, 4), Image(_charts(df), width=doc.width, height=doc.width * 2.5 / 7.4), Paragraph("Recommended actions", h)]
    ar = [["Action", "Plots"]] + [[a, int(cnt.get(a, 0))] for a in engine.ACTIONS if cnt.get(a, 0)]
    at = Table(ar, colWidths=[doc.width * .75, doc.width * .25])
    at.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), FOREST), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor(C["line"]))]))
    s += [at, Paragraph("Plot detail", h)]
    t = df.sort_values("rank")
    rows = [["Plot", "Village", "Moist. %", "Urgency", "Recommended action", "Water m³", "Hours"]]
    for _, r in t.iterrows():
        rows.append([r.plot_id, Paragraph(r.village, cell), "n/a" if pd.isna(r.soil_moisture) else f"{r.soil_moisture:.1f}", r.urgency,
                     Paragraph(r.action, cell), f"{r.volume_m3:,.0f}" if r.volume_m3 else "-", f"{r.duration_h:.1f}" if r.duration_h else "-"])
    pt = Table(rows, repeatRows=1, colWidths=[doc.width * f for f in (.11, .19, .10, .10, .30, .11, .09)])
    st = [("BACKGROUND", (0, 0), (-1, 0), FOREST), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 7.2),
          ("ALIGN", (2, 0), (2, -1), "RIGHT"), ("ALIGN", (5, 0), (6, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("GRID", (0, 0), (-1, -1), .3, colors.HexColor(C["line"])), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F7F1")])]
    for i, (_, r) in enumerate(t.iterrows(), start=1):
        st += [("TEXTCOLOR", (3, i), (3, i), RISK_RGB[r.urgency]), ("FONTNAME", (3, i), (3, i), "Helvetica-Bold")]
    pt.setStyle(TableStyle(st))
    s += [pt, Spacer(1, 8), KeepTogether([Paragraph("Data notes and disclaimer", h), Paragraph(DISCLAIMER, body),
          Paragraph("Urgency is a model estimate; the action, quantity and duration come from a separate transparent rule engine "
                    "(see Methodology). Water depth is capped at 75 mm per event and adjusted for forecast rain and system efficiency.", small)])]
    doc.build(s, canvasmaker=_Numbered)
    return buf.getvalue()
