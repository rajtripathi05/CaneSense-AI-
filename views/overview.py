import streamlit as st

from canesense import charts, engine, panels, service, state, ui

df, hist = state.frame(), state.history()
base = service.summary(state.baseline_frame())
k = service.summary(df)
ui.shell("Executive Overview", f"Synthetic estate · {k['farms']} villages · {k['plots']} plots · {k['area_ha']:.0f} ha")

with st.container(key="hero"):
    st.markdown('<div class="eyebrow">Precision irrigation intelligence</div><h1>Make every drop count.</h1>'
                '<p class="lead">AI-assisted irrigation planning for smarter, more sustainable sugarcane farming.</p>', unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.5, 1.5, 2.2])
    with c1, st.container(key="cta1"):
        st.page_link(st.session_state["_pages"]["Farm Intelligence"], label="Explore Farm Intelligence", icon=":material/arrow_forward:")
    with c2:
        st.page_link(st.session_state["_pages"]["Scenario Simulator"], label="Run Scenario Simulation", icon=":material/science:")
    st.markdown('<div class="photo-credit">Photo: Timothy A. Gonsalves, CC BY-SA 4.0</div>', unsafe_allow_html=True)

if st.session_state.last_change:
    ch = st.session_state.last_change
    st.success(f"Scenario **{ch['scenario']}** applied at {ch['time']}: high-urgency plots {ch['before']['high_risk']} → {ch['after']['high_risk']}, "
               f"water demand {ch['before']['demand_m3']:,.0f} → {ch['after']['demand_m3']:,.0f} m³.", icon=":material/check_circle:")

cols = st.columns(5)
t_hi = ui.delta_chip(k["high_risk"], base["high_risk"], "{:+.0f} plots")
t_nd = ui.delta_chip(k["need_irrigation"], base["need_irrigation"], "{:+.0f} plots")
t_dm = ui.delta_chip(k["demand_m3"], base["demand_m3"], "{:+,.0f} m³")
cards = [
    ui.kpi("Farms monitored", str(k["farms"]), "villages", f"{k['plots']} plots · {k['area_ha']:.0f} ha", "layers", "green"),
    ui.kpi("Need irrigation", str(k["need_irrigation"]), f"of {k['plots']}", f"{k['rain_adjust']} with rainfall adjustment", "droplet", "amber", *t_nd),
    ui.kpi("High-risk plots", str(k["high_risk"]), "plots", f"{k['medium_risk']} medium · {k['low_risk']} low", "alert", "red", *t_hi),
    ui.kpi("Water demand", f"{k['demand_m3']:,.0f}", "m³", f"{k['allocated_m3']:,.0f} m³ within daily budget", "rain", "blue", *t_dm),
    ui.kpi("Sensor health", f"{k['sensors_online']}/{k['plots']}", "online", f"{k['sensors_degraded']} degraded · {k['sensors_offline']} offline", "wifi",
           "green" if k["sensors_offline"] == 0 else "amber"),
]
for c, h in zip(cols, cards):
    c.markdown(h, unsafe_allow_html=True)

ui.section("Field overview and priority actions", "Click a plot on the map to select it")
left, right = st.columns([3, 2])
with left:
    panels.map_chart(df, "ov_map", tiles=False)
    ui.legend()
    sel = ui.selected_row(df)
    if sel is not None:
        st.info(f"**{sel.plot_id}** ({sel.village}) · {sel.urgency} urgency · {sel.action}. Open **Farm Intelligence** or **AI Irrigation Advisor** for the full detail.", icon=":material/pin_drop:")
with right:
    st.markdown("**Priority action queue**")
    q = df.sort_values("rank").head(7)
    rows = ""
    for _, r in q.iterrows():
        vol = f"{r.volume_m3:,.0f} m³" if r.volume_m3 else "—"
        rows += (f"<div style='display:grid;grid-template-columns:1.6rem 1fr auto;gap:.5rem;align-items:center;padding:.42rem 0;border-bottom:1px solid var(--line)'>"
                 f"<b style='color:var(--muted)'>{int(r['rank'])}</b><div><b>{r.plot_id}</b> <span style='color:var(--muted);font-size:.78rem'>{r.village}</span><br>"
                 f"<span style='font-size:.8rem'>{r.action} · {vol}</span></div>{ui.badge(r.urgency)}</div>")
    ui.md(f"<div class='cs-card' style='padding:.4rem 1rem'>{rows}</div>")

ui.section("Trends and conditions")
a, b, c = st.columns([5, 4, 4])
with a:
    st.markdown("**Soil-moisture trend (21 days)**")
    st.plotly_chart(charts.moisture_trend(hist, df), width="stretch", config={"displayModeBar": False}, key="ov_trend")
    st.caption("Estate mean soil moisture for high-urgency plots versus other plots, against the mean irrigation trigger.")
with b:
    st.markdown("**Irrigation urgency by village**")
    st.plotly_chart(charts.urgency_by_village(df), width="stretch", config={"displayModeBar": False}, key="ov_urg")
    st.caption("Count of plots at each urgency level per village.")
with c:
    st.markdown("**Weather and rainfall**")
    ui.md(f"<div class='cs-delta'><div><span>Air temp</span><b>{df.air_temp.mean():.1f} °C</b></div><div><span>Humidity</span><b>{df.humidity.mean():.0f}%</b></div>"
          f"<div><span>ET0</span><b>{df.et0.mean():.1f} mm/d</b></div><div><span>Rain 48 h fc.</span><b>{df.forecast_rain_48h.mean():.0f} mm</b></div></div>")
    st.plotly_chart(charts.rainfall_panel(hist, df), width="stretch", config={"displayModeBar": False}, key="ov_rain")
