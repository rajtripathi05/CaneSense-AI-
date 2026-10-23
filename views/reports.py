import time
from datetime import datetime

import streamlit as st

from canesense import panels, reports, state, ui
from canesense.config import STUDENT

ss = st.session_state
df, hist = state.frame(), state.history()
ui.shell("Reports & Exports", "PDF, CSV and Excel built from exactly the records you select")

l, r = st.columns([2, 3])
with l:
    st.markdown("**Report scope**")
    villages = st.multiselect("Villages", sorted(df.village.unique()), key="rp_v", placeholder="All villages")
    risks = st.multiselect("Urgency levels", ["High", "Medium", "Low"], key="rp_r", placeholder="All levels")
    f0 = panels.apply_filters(df, village=villages, risk=risks)
    plots = st.multiselect("Specific plots (optional)", list(f0.plot_id), key="rp_p", placeholder="All plots in the filters above")
    period = st.select_slider("Reporting period (moisture history)", options=[7, 14, 21], value=21, format_func=lambda d: f"Last {d} days", key="rp_period")
    academic = st.checkbox("Include academic project details (for submission copies)", value=False, key="rp_acad",
                           help="Adds the student/project line to the PDF header. Leave off for ordinary farm-operations reports.")
sel = f0[f0.plot_id.isin(plots)] if plots else f0
scope = dict(scenario=ss.scenario, villages=", ".join(villages) or "All", risks=", ".join(risks) or "All",
             period=f"Last {period} days", records=len(sel))
sig = (tuple(sel.plot_id), ss.scenario, period, academic, state.overrides_key())

if len(sel):
    h = hist[hist.date > hist.date.max() - __import__("pandas").Timedelta(days=period)]
    sel = sel.merge(h.groupby("plot_id").soil_moisture.mean().round(1).rename("moisture_mean_period"), on="plot_id", how="left")

with r:
    st.markdown("**Preview of selected records**")
    if sel.empty:
        ui.empty("No records selected", "Your scope matches no plots. Remove a filter or choose different villages / urgency levels.")
    else:
        k = state.service.summary(sel)
        ui.md(f"<div class='cs-delta'><div><span>Records</span><b>{k['plots']}</b></div><div><span>High urgency</span><b>{k['high_risk']}</b></div>"
              f"<div><span>Need irrigation</span><b>{k['need_irrigation']}</b></div><div><span>Water demand</span><b>{k['demand_m3']:,.0f} m³</b></div>"
              f"</div>")
        st.dataframe(reports.export_table(sel).head(8)[["Plot", "Village", "Moisture (%)", "Urgency", "Recommended action", "Water (m³)"]], hide_index=True, width="stretch", height=300)
        st.caption(f"Showing 8 of {len(sel)} records · scenario: {ss.scenario} · {scope['period']}")

ui.section("Generate and download")
rep = ss.report
fresh = bool(rep) and rep["sig"] == sig
b1, b2, b3, b4 = st.columns([1.3, 1, 1, 2.2])
if b1.button("Generate PDF report", type="primary", icon=":material/picture_as_pdf:", disabled=sel.empty, width="stretch",
             help="Select at least one record." if sel.empty else None):
    bar = st.progress(0, text="Preparing records…")
    for pct, txt in [(25, "Rendering charts…"), (55, "Building tables…")]:
        time.sleep(0.2)
        bar.progress(pct, text=txt)
    gen = datetime.now()
    try:
        pdf = reports.to_pdf(sel, scope, gen, academic=STUDENT if academic else None)
        ss.report = dict(pdf=pdf, ts=gen, sig=sig, n=len(sel))
        bar.progress(100, text="Report ready")
        st.rerun()
    except Exception as e:
        bar.empty()
        st.error(f"The PDF could not be generated ({type(e).__name__}). Your CSV and Excel exports are still available.")
rep = ss.report
fresh = bool(rep) and rep["sig"] == sig
now = datetime.now()
if rep:
    b2.download_button("Download PDF", rep["pdf"], file_name=f"canesense_report_{rep['ts']:%Y%m%d_%H%M}.pdf", mime="application/pdf",
                       icon=":material/download:", width="stretch", disabled=not fresh,
                       help=None if fresh else "Scope changed since this PDF was generated - generate it again.")
else:
    b2.button("Download PDF", disabled=True, icon=":material/download:", width="stretch", help="Generate the PDF first.")
if len(sel):
    b3.download_button("CSV", reports.to_csv(sel, scope, now), file_name=f"canesense_plots_{now:%Y%m%d_%H%M}.csv", mime="text/csv", icon=":material/table:", width="stretch")
    b4.download_button("Excel workbook", reports.to_excel(sel, scope, now), file_name=f"canesense_plots_{now:%Y%m%d_%H%M}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/grid_on:", width="content")
else:
    b3.button("CSV", disabled=True, width="stretch", help="No records selected.")
    b4.button("Excel workbook", disabled=True, help="No records selected.")

if rep:
    kind = "ok" if fresh else "warn"
    ui.md(ui.chip(f"PDF {'ready' if fresh else 'out of date'} · generated {rep['ts']:%d %b %Y %H:%M:%S} · {rep['n']} records", kind, "check" if fresh else "alert"))
else:
    ui.md(ui.chip("PDF not generated yet", "neutral", "clock"))
st.caption("Reports contain synthetic data only and are decision-support material, not agronomic advice.")
