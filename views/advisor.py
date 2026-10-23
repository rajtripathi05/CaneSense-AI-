import json

import streamlit as st

from canesense import charts, engine, panels, service, state, ui
from canesense.config import MODEL_DIR
from canesense.data import RANGES, STAGES, IRRIGATION, SOIL_WHC, validate_frame
from canesense.model import predict

df, hist = state.frame(), state.history()
ui.shell("AI Irrigation Advisor", "Model-predicted urgency + transparent rule engine = actionable recommendations")
metrics = json.loads((MODEL_DIR / "metrics.json").read_text()) if (MODEL_DIR / "metrics.json").exists() else {}
if metrics:
    st.caption(f"Model: RandomForest classifier · macro-F1 {metrics['f1_macro']:.2f} on a held-out synthetic test split ({metrics['n_test']:,} rows). "
               "These scores measure recovery of a synthetic rule, not accuracy on real farms.")

top = df.sort_values("rank").head(6)
ui.section("Top recommendations", "Ranked by model-estimated urgency, soil-moisture deficit and plot size")
cols = st.columns(3)
for i, (_, r) in enumerate(top.iterrows()):
    with cols[i % 3]:
        ui.md(ui.reco_card(r, compact=True))
        if st.button("Inspect", key=f"adv_in_{r.plot_id}", icon=":material/search:"):
            state.select_plot(r.plot_id)

ui.section("Inspect a plot")
ids = list(df.sort_values("rank").plot_id)
ss = st.session_state
if ss.selected_plot in ids and ss.get("adv_last") != ss.selected_plot:
    ss.adv_pick = ss.selected_plot          # selection made elsewhere (map, table, Inspect button)
elif ss.get("adv_pick") not in ids:
    ss.adv_pick = ids[0]
pid = st.selectbox("Plot", ids, key="adv_pick")
state.select_plot(pid)
ss.adv_last = pid
row = df[df.plot_id == pid].iloc[0]
l, r_ = st.columns([3, 2])
with l:
    ui.md(ui.reco_card(row))
with r_:
    st.markdown("**How the recommendation is built**")
    st.markdown(
        "1. The **ML model** estimates urgency (Low / Medium / High) from 10 inputs.\n"
        "2. The **rule engine** picks the action: sensor review → monitor → rainfall adjustment → irrigate.\n"
        "3. **Water depth** = deficit to (trigger + 6 pts) × root-zone depth, capped at 75 mm, minus 70% of forecast rain, divided by system efficiency.\n"
        "4. **Duration** = depth ÷ application rate of the plot's system.\n"
        "5. The **daily water budget** is allocated by priority; plots that do not fit are marked *Restricted water availability*.")
    st.plotly_chart(charts.prob_bar(row), width="stretch", key="adv_prob", config={"displayModeBar": False})
    st.caption("Review guidance: confirm the sensor reading in the field, check pump availability, and treat the figures as a starting point.")

with st.expander("Try a custom reading (what-if)"):
    with st.form("whatif"):
        a, b, c = st.columns(3)
        m = a.number_input("Soil moisture (%)", value=float(row.soil_moisture) if row.soil_moisture == row.soil_moisture else 25.0, step=0.5)
        st_ = b.number_input("Soil temperature (°C)", value=float(row.soil_temp), step=0.5)
        at = c.number_input("Air temperature (°C)", value=float(row.air_temp), step=0.5)
        hu = a.number_input("Humidity (%)", value=float(row.humidity), step=1.0)
        r24 = b.number_input("Rain last 24 h (mm)", value=float(row.rain_24h), step=1.0)
        f48 = c.number_input("Forecast rain 48 h (mm)", value=float(row.forecast_rain_48h), step=1.0)
        et = a.number_input("ET0 (mm/day)", value=float(row.et0), step=0.1)
        ds = b.number_input("Days since irrigation", value=int(row.days_since_irrigation), step=1)
        stg = c.selectbox("Crop stage", STAGES, index=STAGES.index(row.crop_stage))
        go = st.form_submit_button("Predict", type="primary")
    if go:
        t = df[df.plot_id == pid].copy()
        for k, v in dict(soil_moisture=m, soil_temp=st_, air_temp=at, humidity=hu, rain_24h=r24, forecast_rain_48h=f48, et0=et,
                         days_since_irrigation=ds, crop_stage=stg).items():
            t[k] = v
        problems = validate_frame(t)
        if problems:
            for p in problems:
                st.error(f"Please check your input - {p}")
        else:
            clf, _ = service.model_bundle()
            base_cols = [c for c in t.columns if c not in ("p_low", "p_medium", "p_high", "urgency", "confidence", "imputed", "action", "depth_mm",
                                                           "volume_m3", "duration_h", "factors", "priority", "explanation", "data_quality", "allocated_m3", "rank",
                                                           "stage_threshold", "soil_whc")]
            res = engine.recommend(predict(clf, t[base_cols]))
            ui.md(ui.reco_card(res.iloc[0]))
            st.caption("Custom what-if only: it does not change the dashboard.")
